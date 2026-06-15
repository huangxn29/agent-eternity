#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体通信系统测试
Test cases for Agent Communication System v1.0
"""

import unittest
import json
import os
import sys
import tempfile
import time
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from agent_communication import (
    AgentCommunication, AgentMessage, MessageChannel, MessageQueue,
    MessageStatus, MessagePriority, MessageType
)


class TestMessageDataClasses(unittest.TestCase):
    """测试消息数据类"""
    
    def test_agent_message_creation(self):
        """测试创建AgentMessage"""
        msg = AgentMessage(
            message_id="test-123",
            sender_id="agent1",
            receiver_id="agent2",
            content="Hello, World!"
        )
        self.assertEqual(msg.sender_id, "agent1")
        self.assertEqual(msg.receiver_id, "agent2")
        self.assertEqual(msg.content, "Hello, World!")
        self.assertEqual(msg.status, MessageStatus.SENT)
        self.assertEqual(msg.priority, MessagePriority.NORMAL)
        self.assertEqual(msg.message_type, MessageType.DIRECT)
        self.assertIsNotNone(msg.created_at)
    
    def test_agent_message_default_id(self):
        """测试默认消息ID生成"""
        msg = AgentMessage(
            message_id="",
            sender_id="agent1",
            receiver_id="agent2",
            content="Test"
        )
        self.assertNotEqual(msg.message_id, "")
        self.assertTrue(len(msg.message_id) > 0)
    
    def test_agent_message_to_dict(self):
        """测试消息序列化"""
        msg = AgentMessage(
            message_id="msg-1",
            sender_id="alice",
            receiver_id="bob",
            content="Hi Bob",
            priority=MessagePriority.HIGH,
            data={"key": "value"}
        )
        d = msg.to_dict()
        self.assertEqual(d["message_id"], "msg-1")
        self.assertEqual(d["sender_id"], "alice")
        self.assertEqual(d["priority"], "high")
        self.assertEqual(d["data"]["key"], "value")
    
    def test_agent_message_from_dict(self):
        """测试消息反序列化"""
        d = {
            "message_id": "msg-2",
            "sender_id": "bob",
            "receiver_id": "alice",
            "content": "Hi Alice",
            "priority": "low",
            "message_type": "broadcast"
        }
        msg = AgentMessage.from_dict(d)
        self.assertEqual(msg.message_id, "msg-2")
        self.assertEqual(msg.priority, MessagePriority.LOW)
        self.assertEqual(msg.message_type, MessageType.BROADCAST)
    
    def test_message_channel_creation(self):
        """测试创建消息频道"""
        channel = MessageChannel(
            channel_id="general",
            name="General Chat",
            description="General discussion",
            is_public=True
        )
        self.assertEqual(channel.channel_id, "general")
        self.assertEqual(channel.name, "General Chat")
        self.assertTrue(channel.is_public)
        self.assertEqual(len(channel.subscribers), 0)
        self.assertIsNotNone(channel.created_at)


class TestMessageQueue(unittest.TestCase):
    """测试消息队列"""
    
    def test_queue_basic(self):
        """测试基本入队出队"""
        q = MessageQueue()
        msg = AgentMessage(
            message_id="m1",
            sender_id="a1",
            receiver_id="a2",
            content="test"
        )
        
        self.assertTrue(q.enqueue(msg))
        self.assertEqual(q.size(), 1)
        
        dequeued = q.dequeue()
        self.assertIsNotNone(dequeued)
        self.assertEqual(dequeued.message_id, "m1")
        self.assertEqual(q.size(), 0)
    
    def test_queue_priority_order(self):
        """测试优先级队列顺序"""
        q = MessageQueue()
        
        msg_low = AgentMessage(
            message_id="low", sender_id="a", receiver_id="b",
            content="low", priority=MessagePriority.LOW
        )
        msg_high = AgentMessage(
            message_id="high", sender_id="a", receiver_id="b",
            content="high", priority=MessagePriority.HIGH
        )
        msg_normal = AgentMessage(
            message_id="normal", sender_id="a", receiver_id="b",
            content="normal", priority=MessagePriority.NORMAL
        )
        msg_critical = AgentMessage(
            message_id="critical", sender_id="a", receiver_id="b",
            content="critical", priority=MessagePriority.CRITICAL
        )
        
        # 按乱序入队
        q.enqueue(msg_low)
        q.enqueue(msg_high)
        q.enqueue(msg_normal)
        q.enqueue(msg_critical)
        
        # 按优先级出队
        self.assertEqual(q.dequeue().message_id, "critical")
        self.assertEqual(q.dequeue().message_id, "high")
        self.assertEqual(q.dequeue().message_id, "normal")
        self.assertEqual(q.dequeue().message_id, "low")
    
    def test_queue_peek(self):
        """测试查看队首"""
        q = MessageQueue()
        msg = AgentMessage(
            message_id="m1", sender_id="a", receiver_id="b", content="test",
            priority=MessagePriority.URGENT
        )
        q.enqueue(msg)
        
        peeked = q.peek()
        self.assertIsNotNone(peeked)
        self.assertEqual(peeked.message_id, "m1")
        self.assertEqual(q.size(), 1)  # peek不取出
    
    def test_queue_empty(self):
        """测试空队列"""
        q = MessageQueue()
        self.assertIsNone(q.dequeue())
        self.assertIsNone(q.peek())
        self.assertEqual(q.size(), 0)
    
    def test_queue_max_size(self):
        """测试队列最大容量"""
        q = MessageQueue(max_size=3)
        
        for i in range(5):
            msg = AgentMessage(
                message_id=f"m{i}", sender_id="a", receiver_id="b", content=f"msg{i}"
            )
            result = q.enqueue(msg)
            if i < 3:
                self.assertTrue(result)
            else:
                self.assertFalse(result)
        
        self.assertEqual(q.size(), 3)
    
    def test_queue_get_message(self):
        """测试根据ID获取消息"""
        q = MessageQueue()
        msg = AgentMessage(
            message_id="find-me", sender_id="a", receiver_id="b", content="find me"
        )
        q.enqueue(msg)
        
        found = q.get_message("find-me")
        self.assertIsNotNone(found)
        self.assertEqual(found.content, "find me")
        
        not_found = q.get_message("not-exist")
        self.assertIsNone(not_found)


class TestAgentManagement(unittest.TestCase):
    """测试智能体注册与管理"""
    
    def setUp(self):
        self.comm = AgentCommunication()
    
    def test_register_agent(self):
        """测试注册智能体"""
        result = self.comm.register_agent(
            agent_id="agent-1",
            agent_name="Test Agent",
            capabilities=["writing", "analysis"]
        )
        self.assertTrue(result)
        
        agent = self.comm.get_agent("agent-1")
        self.assertIsNotNone(agent)
        self.assertEqual(agent["name"], "Test Agent")
        self.assertEqual(agent["status"], "online")
        self.assertIn("writing", agent["capabilities"])
    
    def test_register_duplicate_agent(self):
        """测试重复注册"""
        self.comm.register_agent("agent-1")
        result = self.comm.register_agent("agent-1")
        self.assertFalse(result)
    
    def test_unregister_agent(self):
        """测试注销智能体"""
        self.comm.register_agent("agent-1")
        result = self.comm.unregister_agent("agent-1")
        self.assertTrue(result)
        
        agent = self.comm.get_agent("agent-1")
        self.assertIsNone(agent)
    
    def test_unregister_nonexistent(self):
        """测试注销不存在的智能体"""
        result = self.comm.unregister_agent("nonexistent")
        self.assertFalse(result)
    
    def test_list_agents(self):
        """测试列出智能体"""
        self.comm.register_agent("a1", "Agent 1")
        self.comm.register_agent("a2", "Agent 2")
        self.comm.register_agent("a3", "Agent 3")
        
        agents = self.comm.list_agents()
        # 3个注册的 + 1个系统智能体
        self.assertEqual(len(agents), 4)
    
    def test_list_agents_by_status(self):
        """测试按状态筛选智能体"""
        self.comm.register_agent("online-1")
        self.comm.register_agent("online-2")
        self.comm.register_agent("offline-1")
        self.comm.set_agent_status("offline-1", "offline")
        
        online = self.comm.list_agents(status="online")
        offline = self.comm.list_agents(status="offline")
        
        # 2个在线的 + 1个系统智能体(在线) = 3个在线
        self.assertEqual(len(online), 3)
        self.assertEqual(len(offline), 1)
    
    def test_set_agent_status(self):
        """测试设置智能体状态"""
        self.comm.register_agent("a1")
        result = self.comm.set_agent_status("a1", "busy")
        self.assertTrue(result)
        
        agent = self.comm.get_agent("a1")
        self.assertEqual(agent["status"], "busy")
    
    def test_auto_subscribe_default_channels(self):
        """测试自动订阅默认频道"""
        self.comm.register_agent("new-agent")
        subscriptions = self.comm.get_subscriptions("new-agent")
        
        self.assertIn("system", subscriptions)
        self.assertIn("events", subscriptions)
    
    def test_heartbeat(self):
        """测试心跳机制"""
        self.comm.register_agent("agent-1")
        
        result = self.comm.send_heartbeat("agent-1")
        self.assertTrue(result)
        
        agent = self.comm.get_agent("agent-1")
        self.assertEqual(agent["status"], "online")
    
    def test_check_offline_agents(self):
        """测试检查离线智能体"""
        self.comm.register_agent("agent-1")
        
        # 修改last_seen模拟超时
        agent = self.comm._agents["agent-1"]
        agent["last_seen"] = "2020-01-01T00:00:00"
        
        offline = self.comm.check_offline_agents(timeout_seconds=60)
        self.assertIn("agent-1", offline)
        self.assertEqual(agent["status"], "offline")


class TestChannelManagement(unittest.TestCase):
    """测试频道管理"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("alice")
        self.comm.register_agent("bob")
        self.comm.register_agent("charlie")
    
    def test_default_channels_exist(self):
        """测试默认频道存在"""
        channels = self.comm.list_channels()
        channel_ids = [c.channel_id for c in channels]
        
        self.assertIn("system", channel_ids)
        self.assertIn("events", channel_ids)
        self.assertIn("general", channel_ids)
    
    def test_create_channel(self):
        """测试创建频道"""
        channel = self.comm.create_channel(
            channel_id="dev-team",
            name="Development Team",
            description="Dev team discussions"
        )
        self.assertIsNotNone(channel)
        self.assertEqual(channel.channel_id, "dev-team")
        self.assertTrue(channel.is_public)
    
    def test_delete_channel(self):
        """测试删除频道"""
        self.comm.create_channel("temp-channel", "Temp")
        result = self.comm.delete_channel("temp-channel")
        self.assertTrue(result)
        
        channel = self.comm.get_channel("temp-channel")
        self.assertIsNone(channel)
    
    def test_subscribe_unsubscribe(self):
        """测试订阅和取消订阅"""
        self.comm.create_channel("test-channel", "Test")
        
        # 订阅
        result = self.comm.subscribe("alice", "test-channel")
        self.assertTrue(result)
        
        channel = self.comm.get_channel("test-channel")
        self.assertIn("alice", channel.subscribers)
        self.assertIn("test-channel", self.comm.get_subscriptions("alice"))
        
        # 取消订阅
        result = self.comm.unsubscribe("alice", "test-channel")
        self.assertTrue(result)
        
        channel = self.comm.get_channel("test-channel")
        self.assertNotIn("alice", channel.subscribers)
        self.assertNotIn("test-channel", self.comm.get_subscriptions("alice"))
    
    def test_subscribe_nonexistent_channel(self):
        """测试订阅不存在的频道"""
        result = self.comm.subscribe("alice", "no-such-channel")
        self.assertFalse(result)
    
    def test_get_channel_info(self):
        """测试获取频道信息"""
        self.comm.create_channel("info-channel", "Info Channel", "Test description")
        channel = self.comm.get_channel("info-channel")
        
        self.assertIsNotNone(channel)
        self.assertEqual(channel.name, "Info Channel")
        self.assertEqual(channel.description, "Test description")


class TestDirectMessaging(unittest.TestCase):
    """测试直接消息传递"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("alice", "Alice")
        self.comm.register_agent("bob", "Bob")
    
    def test_send_direct_message(self):
        """测试发送直接消息"""
        msg = self.comm.send_message(
            sender_id="alice",
            receiver_id="bob",
            content="Hello Bob!"
        )
        
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender_id, "alice")
        self.assertEqual(msg.receiver_id, "bob")
        self.assertEqual(msg.content, "Hello Bob!")
        self.assertEqual(msg.status, MessageStatus.DELIVERED)
    
    def test_send_message_to_nonexistent(self):
        """测试发送消息给不存在的接收者"""
        msg = self.comm.send_message(
            sender_id="alice",
            receiver_id="nobody",
            content="Hello?"
        )
        
        self.assertIsNotNone(msg)
        self.assertEqual(msg.status, MessageStatus.FAILED)
    
    def test_send_message_from_nonexistent(self):
        """测试不存在的发送者"""
        msg = self.comm.send_message(
            sender_id="nobody",
            receiver_id="bob",
            content="Hello?"
        )
        self.assertIsNone(msg)
    
    def test_receive_message(self):
        """测试接收消息"""
        self.comm.send_message("alice", "bob", "Message 1")
        self.comm.send_message("alice", "bob", "Message 2")
        
        msg = self.comm.receive_message("bob")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.content, "Message 1")
        self.assertEqual(msg.status, MessageStatus.READ)
    
    def test_receive_all_messages(self):
        """测试接收所有未读消息"""
        for i in range(5):
            self.comm.send_message("alice", "bob", f"Message {i}")
        
        messages = self.comm.receive_all_messages("bob")
        self.assertEqual(len(messages), 5)
        self.assertEqual(messages[0].content, "Message 0")
        self.assertEqual(messages[-1].content, "Message 4")
    
    def test_receive_all_messages_limit(self):
        """测试限制接收数量"""
        for i in range(10):
            self.comm.send_message("alice", "bob", f"Message {i}")
        
        messages = self.comm.receive_all_messages("bob", limit=3)
        self.assertEqual(len(messages), 3)
    
    def test_peek_message(self):
        """测试查看消息但不取出"""
        self.comm.send_message("alice", "bob", "Peek me")
        
        peeked = self.comm.peek_message("bob")
        self.assertIsNotNone(peeked)
        self.assertEqual(peeked.content, "Peek me")
        
        # 消息仍在队列中
        received = self.comm.receive_message("bob")
        self.assertIsNotNone(received)
        self.assertEqual(received.content, "Peek me")
    
    def test_empty_inbox(self):
        """测试空收件箱"""
        msg = self.comm.receive_message("bob")
        self.assertIsNone(msg)
    
    def test_inbox_history(self):
        """测试收件箱历史"""
        self.comm.send_message("alice", "bob", "First")
        self.comm.send_message("alice", "bob", "Second")
        
        inbox = self.comm.get_inbox("bob")
        self.assertEqual(len(inbox), 2)
    
    def test_outbox_history(self):
        """测试发件箱历史"""
        self.comm.send_message("alice", "bob", "Hello")
        self.comm.send_message("alice", "bob", "World")
        
        outbox = self.comm.get_outbox("alice")
        self.assertEqual(len(outbox), 2)
        self.assertEqual(outbox[0].content, "Hello")
    
    def test_conversation_history(self):
        """测试对话历史"""
        self.comm.send_message("alice", "bob", "Hi Bob")
        self.comm.send_message("bob", "alice", "Hi Alice")
        self.comm.send_message("alice", "bob", "How are you?")
        
        convo = self.comm.get_conversation("alice", "bob")
        self.assertEqual(len(convo), 3)
        self.assertEqual(convo[0].content, "Hi Bob")
        self.assertEqual(convo[1].content, "Hi Alice")
        self.assertEqual(convo[2].content, "How are you?")


class TestBroadcastMessaging(unittest.TestCase):
    """测试广播消息"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("alice")
        self.comm.register_agent("bob")
        self.comm.register_agent("charlie")
        
        self.comm.create_channel("team", "Team Channel")
        self.comm.subscribe("alice", "team")
        self.comm.subscribe("bob", "team")
        # charlie 不订阅 team 频道
    
    def test_broadcast_to_channel(self):
        """测试广播到频道"""
        messages = self.comm.broadcast(
            sender_id="alice",
            channel_id="team",
            content="Team meeting at 3pm"
        )
        
        # alice和bob订阅了，但alice是发送者，所以只有bob收到
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].receiver_id, "bob")
        self.assertEqual(messages[0].message_type, MessageType.BROADCAST)
    
    def test_broadcast_multiple_subscribers(self):
        """测试多个订阅者的广播"""
        self.comm.subscribe("charlie", "team")  # 现在3人订阅
        
        messages = self.comm.broadcast(
            sender_id="alice",
            channel_id="team",
            content="Hello team"
        )
        
        self.assertEqual(len(messages), 2)  # bob和charlie收到
        receiver_ids = [m.receiver_id for m in messages]
        self.assertIn("bob", receiver_ids)
        self.assertIn("charlie", receiver_ids)
    
    def test_broadcast_nonexistent_channel(self):
        """测试广播到不存在的频道"""
        messages = self.comm.broadcast(
            sender_id="alice",
            channel_id="no-channel",
            content="Hello?"
        )
        self.assertEqual(len(messages), 0)
    
    def test_broadcast_with_priority(self):
        """测试带优先级的广播"""
        messages = self.comm.broadcast(
            sender_id="alice",
            channel_id="team",
            content="URGENT: Server down!",
            priority=MessagePriority.URGENT
        )
        
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].priority, MessagePriority.URGENT)


class TestMessageCallbacks(unittest.TestCase):
    """测试消息回调机制"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("alice")
        self.comm.register_agent("bob")
    
    def test_on_message_callback(self):
        """测试消息到达回调"""
        received_messages = []
        
        def callback(msg):
            received_messages.append(msg)
        
        self.comm.on_message("bob", callback)
        
        self.comm.send_message("alice", "bob", "Test callback")
        
        self.assertEqual(len(received_messages), 1)
        self.assertEqual(received_messages[0].content, "Test callback")
    
    def test_multiple_callbacks(self):
        """测试多个回调"""
        count1 = 0
        count2 = 0
        
        def cb1(msg):
            nonlocal count1
            count1 += 1
        
        def cb2(msg):
            nonlocal count2
            count2 += 1
        
        self.comm.on_message("bob", cb1)
        self.comm.on_message("bob", cb2)
        
        self.comm.send_message("alice", "bob", "Multi callback test")
        
        self.assertEqual(count1, 1)
        self.assertEqual(count2, 1)
    
    def test_callback_exception_handled(self):
        """测试回调异常不影响其他回调"""
        results = []
        
        def bad_callback(msg):
            raise RuntimeError("Oops!")
        
        def good_callback(msg):
            results.append(msg.content)
        
        self.comm.on_message("bob", bad_callback)
        self.comm.on_message("bob", good_callback)
        
        # 不应抛出异常
        self.comm.send_message("alice", "bob", "Exception test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0], "Exception test")


class TestWorkflowIntegration(unittest.TestCase):
    """测试工作流集成"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("worker-1")
        self.comm.register_agent("worker-2")
        self.comm.register_agent("manager")
    
    def test_send_task_message(self):
        """测试发送任务消息"""
        msg = self.comm.send_task_message(
            sender_id="manager",
            receiver_id="worker-1",
            workflow_id="wf-001",
            task_id="task-001",
            content="Please complete this task",
            data={"deadline": "2024-12-31"}
        )
        
        self.assertIsNotNone(msg)
        self.assertEqual(msg.workflow_id, "wf-001")
        self.assertEqual(msg.task_id, "task-001")
        self.assertEqual(msg.message_type, MessageType.TASK)
        self.assertEqual(msg.data["deadline"], "2024-12-31")
    
    def test_get_workflow_messages(self):
        """测试获取工作流相关消息"""
        self.comm.send_task_message("manager", "worker-1", "wf-1", "t1", "Msg 1")
        self.comm.send_task_message("manager", "worker-2", "wf-1", "t2", "Msg 2")
        self.comm.send_task_message("manager", "worker-1", "wf-2", "t1", "Other workflow")
        
        wf_messages = self.comm.get_workflow_messages("wf-1")
        self.assertEqual(len(wf_messages), 2)
    
    def test_get_task_messages(self):
        """测试获取任务相关消息"""
        self.comm.send_task_message("manager", "worker-1", "wf-1", "task-a", "Task msg 1")
        self.comm.send_task_message("worker-1", "manager", "wf-1", "task-a", "Task done")
        self.comm.send_task_message("manager", "worker-1", "wf-1", "task-b", "Other task")
        
        task_messages = self.comm.get_task_messages("task-a")
        self.assertEqual(len(task_messages), 2)
    
    def test_broadcast_event(self):
        """测试事件广播"""
        # 所有智能体都自动订阅了events频道
        messages = self.comm.broadcast_event(
            sender_id="system",
            event_name="workflow_completed",
            data={"workflow_id": "wf-1", "status": "success"},
            workflow_id="wf-1"
        )
        
        # 3个智能体都在events频道订阅，system不是注册agent所以不算
        self.assertEqual(len(messages), 3)
        
        msg_types = [m.message_type for m in messages]
        self.assertTrue(all(t == MessageType.BROADCAST for t in msg_types))
    
    def test_system_message(self):
        """测试系统消息"""
        msg = self.comm.send_system_message(
            receiver_id="worker-1",
            content="System maintenance scheduled",
            priority=MessagePriority.HIGH
        )
        
        self.assertIsNotNone(msg)
        self.assertEqual(msg.sender_id, "system")
        self.assertEqual(msg.message_type, MessageType.SYSTEM)
        self.assertEqual(msg.priority, MessagePriority.HIGH)


class TestStatistics(unittest.TestCase):
    """测试统计信息"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("alice")
        self.comm.register_agent("bob")
        self.comm.register_agent("charlie")
    
    def test_agent_stats(self):
        """测试智能体统计"""
        # 发送一些消息
        self.comm.send_message("alice", "bob", "Hi")
        self.comm.send_message("bob", "alice", "Hello")
        self.comm.send_message("charlie", "bob", "Yo")
        
        stats = self.comm.get_agent_stats("bob")
        self.assertEqual(stats["agent_id"], "bob")
        self.assertEqual(stats["total_received"], 2)  # alice和charlie各发一条
        self.assertEqual(stats["total_sent"], 1)      # 给alice发了一条
        self.assertGreater(stats["unread_count"], 0)
        self.assertIn("system", stats["subscriptions"])
    
    def test_channel_stats(self):
        """测试频道统计"""
        self.comm.create_channel("test-channel", "Test")
        self.comm.subscribe("alice", "test-channel")
        self.comm.subscribe("bob", "test-channel")
        
        self.comm.broadcast("alice", "test-channel", "First broadcast")
        
        stats = self.comm.get_channel_stats("test-channel")
        self.assertEqual(stats["channel_id"], "test-channel")
        self.assertEqual(stats["subscriber_count"], 2)
        self.assertEqual(stats["total_messages"], 1)
    
    def test_system_stats(self):
        """测试系统整体统计"""
        stats = self.comm.get_system_stats()
        
        # 3个注册的 + 1个系统智能体 = 4
        self.assertEqual(stats["total_agents"], 4)
        self.assertEqual(stats["online_agents"], 4)
        self.assertGreater(stats["total_channels"], 0)
        self.assertEqual(stats["total_messages"], 0)
        
        # 发一些消息后再检查
        self.comm.send_message("alice", "bob", "Test")
        stats = self.comm.get_system_stats()
        self.assertEqual(stats["total_messages"], 1)


class TestPersistence(unittest.TestCase):
    """测试持久化"""
    
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.save_path = os.path.join(self.temp_dir, "comm_state.json")
        self.comm = AgentCommunication(storage_path=self.save_path)
    
    def tearDown(self):
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_save_and_load_state(self):
        """测试保存和加载状态"""
        # 设置初始状态
        self.comm.register_agent("alice", "Alice", ["coding"])
        self.comm.register_agent("bob", "Bob", ["design"])
        
        self.comm.create_channel("project", "Project Channel")
        self.comm.subscribe("alice", "project")
        self.comm.subscribe("bob", "project")
        
        self.comm.send_message("alice", "bob", "Let's build something great!")
        self.comm.send_task_message("bob", "alice", "wf-1", "t-1", "Design mockup ready")
        
        # 保存
        save_result = self.comm.save_state()
        self.assertTrue(save_result)
        self.assertTrue(os.path.exists(self.save_path))
        
        # 创建新实例并加载
        new_comm = AgentCommunication()
        load_result = new_comm.load_state(self.save_path)
        self.assertTrue(load_result)
        
        # 验证智能体
        alice = new_comm.get_agent("alice")
        self.assertIsNotNone(alice)
        self.assertEqual(alice["name"], "Alice")
        self.assertIn("coding", alice["capabilities"])
        
        # 验证频道
        channel = new_comm.get_channel("project")
        self.assertIsNotNone(channel)
        self.assertIn("alice", channel.subscribers)
        self.assertIn("bob", channel.subscribers)
        
        # 验证消息历史
        convo = new_comm.get_conversation("alice", "bob")
        self.assertEqual(len(convo), 2)
        
        # 验证任务消息
        task_msgs = new_comm.get_task_messages("t-1")
        self.assertEqual(len(task_msgs), 1)
        self.assertEqual(task_msgs[0].content, "Design mockup ready")
    
    def test_load_nonexistent_file(self):
        """测试加载不存在的文件"""
        comm = AgentCommunication()
        result = comm.load_state("/nonexistent/path.json")
        self.assertFalse(result)
    
    def test_save_without_path(self):
        """测试没有保存路径时"""
        comm = AgentCommunication()
        result = comm.save_state()
        self.assertFalse(result)


class TestPriorityMessaging(unittest.TestCase):
    """测试优先级消息"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("sender")
        self.comm.register_agent("receiver")
    
    def test_priority_delivery_order(self):
        """测试消息按优先级投递"""
        self.comm.send_message("sender", "receiver", "Low priority", priority=MessagePriority.LOW)
        self.comm.send_message("sender", "receiver", "Normal priority", priority=MessagePriority.NORMAL)
        self.comm.send_message("sender", "receiver", "High priority", priority=MessagePriority.HIGH)
        self.comm.send_message("sender", "receiver", "Urgent priority", priority=MessagePriority.URGENT)
        self.comm.send_message("sender", "receiver", "Critical priority", priority=MessagePriority.CRITICAL)
        
        # 按优先级从高到低接收
        msg1 = self.comm.receive_message("receiver")
        msg2 = self.comm.receive_message("receiver")
        msg3 = self.comm.receive_message("receiver")
        msg4 = self.comm.receive_message("receiver")
        msg5 = self.comm.receive_message("receiver")
        
        self.assertEqual(msg1.priority, MessagePriority.CRITICAL)
        self.assertEqual(msg2.priority, MessagePriority.URGENT)
        self.assertEqual(msg3.priority, MessagePriority.HIGH)
        self.assertEqual(msg4.priority, MessagePriority.NORMAL)
        self.assertEqual(msg5.priority, MessagePriority.LOW)
    
    def test_inbox_filter_by_status(self):
        """测试按状态筛选收件箱"""
        self.comm.send_message("sender", "receiver", "Unread 1")
        self.comm.send_message("sender", "receiver", "Unread 2")
        
        # 读取一条消息（标记为已读）
        self.comm.receive_message("receiver")
        
        # 获取已读和未读
        delivered = self.comm.get_inbox("receiver", status=MessageStatus.DELIVERED)
        read = self.comm.get_inbox("receiver", status=MessageStatus.READ)
        
        self.assertEqual(len(delivered), 1)
        self.assertEqual(len(read), 1)


class TestMessageTypeFilter(unittest.TestCase):
    """测试按消息类型筛选"""
    
    def setUp(self):
        self.comm = AgentCommunication()
        self.comm.register_agent("a1")
        self.comm.register_agent("a2")
    
    def test_filter_by_message_type(self):
        """测试按消息类型筛选"""
        self.comm.send_message("a1", "a2", "Direct msg", message_type=MessageType.DIRECT)
        self.comm.send_task_message("a1", "a2", "wf1", "t1", "Task msg")
        self.comm.send_system_message("a2", "System msg")
        
        # 按类型筛选收件箱
        task_msgs = self.comm.get_inbox("a2", message_type=MessageType.TASK)
        sys_msgs = self.comm.get_inbox("a2", message_type=MessageType.SYSTEM)
        direct_msgs = self.comm.get_inbox("a2", message_type=MessageType.DIRECT)
        
        self.assertEqual(len(task_msgs), 1)
        self.assertEqual(task_msgs[0].content, "Task msg")
        self.assertEqual(len(sys_msgs), 1)
        self.assertEqual(sys_msgs[0].content, "System msg")
        self.assertEqual(len(direct_msgs), 1)


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def setUp(self):
        self.comm = AgentCommunication()
    
    def test_empty_message_content(self):
        """测试空内容消息"""
        self.comm.register_agent("a1")
        self.comm.register_agent("a2")
        
        msg = self.comm.send_message("a1", "a2", "")
        self.assertIsNotNone(msg)
        self.assertEqual(msg.content, "")
    
    def test_large_message_content(self):
        """测试大内容消息"""
        self.comm.register_agent("a1")
        self.comm.register_agent("a2")
        
        large_content = "x" * 10000
        msg = self.comm.send_message("a1", "a2", large_content)
        self.assertIsNotNone(msg)
        self.assertEqual(len(msg.content), 10000)
    
    def test_message_with_special_characters(self):
        """测试含特殊字符的消息"""
        self.comm.register_agent("a1")
        self.comm.register_agent("a2")
        
        special_content = "Hello 🌍! こんにちは! Здравствуй! \n\t\r"
        msg = self.comm.send_message("a1", "a2", special_content)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.content, special_content)
    
    def test_message_data_complex(self):
        """测试复杂的data字段"""
        self.comm.register_agent("a1")
        self.comm.register_agent("a2")
        
        complex_data = {
            "nested": {"key": "value", "list": [1, 2, 3]},
            "numbers": [1.5, 2.5, 3.5],
            "boolean": True,
            "null_value": None
        }
        
        msg = self.comm.send_message("a1", "a2", "Test data", data=complex_data)
        self.assertIsNotNone(msg)
        self.assertEqual(msg.data["nested"]["key"], "value")
        self.assertEqual(msg.data["nested"]["list"], [1, 2, 3])
        self.assertTrue(msg.data["boolean"])
    
    def test_max_history_limit(self):
        """测试消息历史上限"""
        self.comm.register_agent("a1")
        self.comm.register_agent("a2")
        self.comm._max_history = 100  # 降低上限便于测试
        
        for i in range(150):
            self.comm.send_message("a1", "a2", f"Message {i}")
        
        # 历史记录不应超过上限
        self.assertLessEqual(len(self.comm._message_history), 100)


if __name__ == "__main__":
    unittest.main()
