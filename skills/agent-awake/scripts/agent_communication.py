#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体通信系统
Agent Communication System v1.0

多智能体永生平台 - 通信层核心模块
提供智能体间消息传递、发布订阅、协作通信能力

核心功能：
- 智能体间直接消息传递
- 主题发布/订阅系统
- 消息队列与异步投递
- 消息持久化与历史记录
- 消息状态追踪（已发送/已送达/已读）
- 工作流上下文关联
- 优先级消息与紧急通知
- 消息加密与身份验证（集成agent-identity）
"""

import os
import json
import uuid
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict, deque


class MessageStatus(str, Enum):
    """消息状态"""
    SENT = "sent"           # 已发送
    DELIVERED = "delivered" # 已送达
    READ = "read"           # 已读
    FAILED = "failed"       # 发送失败
    EXPIRED = "expired"     # 已过期


class MessagePriority(str, Enum):
    """消息优先级"""
    LOW = "low"             # 低优先级
    NORMAL = "normal"       # 普通
    HIGH = "high"           # 高优先级
    URGENT = "urgent"       # 紧急
    CRITICAL = "critical"   #  critical


class MessageType(str, Enum):
    """消息类型"""
    DIRECT = "direct"       # 直接消息
    BROADCAST = "broadcast" # 广播
    TASK = "task"           # 任务相关
    EVENT = "event"         # 事件通知
    SYSTEM = "system"       # 系统消息
    HEARTBEAT = "heartbeat" # 心跳


@dataclass
class AgentMessage:
    """智能体消息"""
    message_id: str
    sender_id: str
    receiver_id: str          # 对于广播消息，receiver为频道名
    content: str
    message_type: MessageType = MessageType.DIRECT
    priority: MessagePriority = MessagePriority.NORMAL
    status: MessageStatus = MessageStatus.SENT
    topic: str = ""           # 主题/频道
    workflow_id: str = ""     # 关联的工作流ID
    task_id: str = ""         # 关联的任务ID
    data: Dict[str, Any] = field(default_factory=dict)  # 附加数据
    created_at: str = ""
    delivered_at: str = ""
    read_at: str = ""
    expires_at: str = ""      # 过期时间
    signature: str = ""       # 消息签名（用于身份验证）
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.message_id:
            self.message_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict:
        return {
            "message_id": self.message_id,
            "sender_id": self.sender_id,
            "receiver_id": self.receiver_id,
            "content": self.content,
            "message_type": self.message_type.value if isinstance(self.message_type, Enum) else self.message_type,
            "priority": self.priority.value if isinstance(self.priority, Enum) else self.priority,
            "status": self.status.value if isinstance(self.status, Enum) else self.status,
            "topic": self.topic,
            "workflow_id": self.workflow_id,
            "task_id": self.task_id,
            "data": self.data,
            "created_at": self.created_at,
            "delivered_at": self.delivered_at,
            "read_at": self.read_at,
            "expires_at": self.expires_at,
            "signature": self.signature
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentMessage':
        # Convert enum strings back to enum types
        msg_data = data.copy()
        for enum_field, enum_cls in [
            ("message_type", MessageType),
            ("priority", MessagePriority),
            ("status", MessageStatus)
        ]:
            if enum_field in msg_data and isinstance(msg_data[enum_field], str):
                try:
                    msg_data[enum_field] = enum_cls(msg_data[enum_field])
                except ValueError:
                    pass
        return cls(**{k: v for k, v in msg_data.items() if k in cls.__dataclass_fields__})


@dataclass
class MessageChannel:
    """消息频道/主题"""
    channel_id: str
    name: str
    description: str = ""
    subscribers: List[str] = field(default_factory=list)  # 订阅者agent ID列表
    is_public: bool = True
    created_at: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "channel_id": self.channel_id,
            "name": self.name,
            "description": self.description,
            "subscribers": self.subscribers,
            "is_public": self.is_public,
            "created_at": self.created_at,
            "metadata": self.metadata
        }


class MessageQueue:
    """消息队列 - 支持优先级的FIFO队列"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues: Dict[MessagePriority, deque] = defaultdict(deque)
        self._message_index: Dict[str, AgentMessage] = {}
    
    def enqueue(self, message: AgentMessage) -> bool:
        """消息入队"""
        if len(self._message_index) >= self.max_size:
            return False
        priority = message.priority
        self._queues[priority].append(message.message_id)
        self._message_index[message.message_id] = message
        return True
    
    def dequeue(self) -> Optional[AgentMessage]:
        """按优先级出队"""
        priority_order = [
            MessagePriority.CRITICAL,
            MessagePriority.URGENT,
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.LOW
        ]
        for priority in priority_order:
            queue = self._queues[priority]
            if queue:
                msg_id = queue.popleft()
                return self._message_index.get(msg_id)
        return None
    
    def peek(self) -> Optional[AgentMessage]:
        """查看队首消息但不出队"""
        priority_order = [
            MessagePriority.CRITICAL,
            MessagePriority.URGENT,
            MessagePriority.HIGH,
            MessagePriority.NORMAL,
            MessagePriority.LOW
        ]
        for priority in priority_order:
            queue = self._queues[priority]
            if queue:
                msg_id = queue[0]
                return self._message_index.get(msg_id)
        return None
    
    def size(self) -> int:
        """队列总大小"""
        return sum(len(q) for q in self._queues.values())
    
    def get_message(self, message_id: str) -> Optional[AgentMessage]:
        """根据ID获取消息"""
        return self._message_index.get(message_id)
    
    def clear(self):
        """清空队列"""
        self._queues.clear()
        self._message_index.clear()


class AgentCommunication:
    """
    智能体通信系统
    
    提供完整的多智能体通信能力，包括：
    - 直接消息传递
    - 发布/订阅主题
    - 消息队列
    - 消息历史
    """
    
    def __init__(self, storage_path: Optional[str] = None):
        self.storage_path = storage_path
        self._agents: Dict[str, Dict] = {}  # 注册的智能体
        self._channels: Dict[str, MessageChannel] = {}  # 消息频道
        self._message_history: List[AgentMessage] = []  # 所有消息历史
        self._inbox: Dict[str, List[AgentMessage]] = defaultdict(list)  # 收件箱
        self._outbox: Dict[str, List[AgentMessage]] = defaultdict(list)  # 发件箱
        self._queues: Dict[str, MessageQueue] = defaultdict(MessageQueue)  # 消息队列
        self._subscriptions: Dict[str, List[str]] = defaultdict(list)  # 订阅关系 agent_id -> [channel_ids]
        self._message_callbacks: Dict[str, List[Callable]] = defaultdict(list)  # 消息回调
        self._max_history = 10000
        
        # 注册系统智能体
        self._agents["system"] = {
            "agent_id": "system",
            "name": "System",
            "capabilities": [],
            "status": "online",
            "metadata": {"is_system": True},
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        
        # 初始化默认系统频道
        self._init_default_channels()
    
    def _init_default_channels(self):
        """初始化默认频道"""
        default_channels = [
            ("system", "系统通知", "系统级广播消息", True),
            ("events", "事件频道", "工作流与任务事件", True),
            ("general", "综合讨论", "通用交流频道", True),
        ]
        for channel_id, name, desc, is_public in default_channels:
            self.create_channel(channel_id, name, desc, is_public)
    
    # ===== Agent 管理 =====
    
    def register_agent(self, agent_id: str, agent_name: str = "", 
                       capabilities: List[str] = None, 
                       metadata: Dict[str, Any] = None) -> bool:
        """注册智能体"""
        if agent_id in self._agents:
            return False
        
        self._agents[agent_id] = {
            "agent_id": agent_id,
            "name": agent_name or agent_id,
            "capabilities": capabilities or [],
            "status": "online",
            "metadata": metadata or {},
            "registered_at": datetime.now().isoformat(),
            "last_seen": datetime.now().isoformat()
        }
        
        # 自动订阅系统频道和事件频道
        self.subscribe(agent_id, "system")
        self.subscribe(agent_id, "events")
        
        return True
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        if agent_id not in self._agents:
            return False
        
        # 取消所有订阅
        for channel_id in list(self._subscriptions.get(agent_id, [])):
            self.unsubscribe(agent_id, channel_id)
        
        del self._agents[agent_id]
        return True
    
    def get_agent(self, agent_id: str) -> Optional[Dict]:
        """获取智能体信息"""
        agent = self._agents.get(agent_id)
        if agent:
            agent["last_seen"] = datetime.now().isoformat()
        return agent
    
    def list_agents(self, status: str = None) -> List[Dict]:
        """列出所有智能体"""
        agents = list(self._agents.values())
        if status:
            agents = [a for a in agents if a["status"] == status]
        return agents
    
    def set_agent_status(self, agent_id: str, status: str) -> bool:
        """设置智能体状态"""
        if agent_id not in self._agents:
            return False
        self._agents[agent_id]["status"] = status
        self._agents[agent_id]["last_seen"] = datetime.now().isoformat()
        return True
    
    # ===== 频道管理 =====
    
    def create_channel(self, channel_id: str, name: str, 
                       description: str = "", is_public: bool = True,
                       metadata: Dict[str, Any] = None) -> MessageChannel:
        """创建消息频道"""
        channel = MessageChannel(
            channel_id=channel_id,
            name=name,
            description=description,
            is_public=is_public,
            metadata=metadata or {}
        )
        self._channels[channel_id] = channel
        return channel
    
    def delete_channel(self, channel_id: str) -> bool:
        """删除频道"""
        if channel_id not in self._channels:
            return False
        # 取消所有订阅
        for subscriber_id in self._channels[channel_id].subscribers:
            if channel_id in self._subscriptions.get(subscriber_id, []):
                self._subscriptions[subscriber_id].remove(channel_id)
        del self._channels[channel_id]
        return True
    
    def get_channel(self, channel_id: str) -> Optional[MessageChannel]:
        """获取频道信息"""
        return self._channels.get(channel_id)
    
    def list_channels(self) -> List[MessageChannel]:
        """列出所有频道"""
        return list(self._channels.values())
    
    def subscribe(self, agent_id: str, channel_id: str) -> bool:
        """订阅频道"""
        if channel_id not in self._channels:
            return False
        if agent_id not in self._agents:
            return False
        
        channel = self._channels[channel_id]
        if agent_id not in channel.subscribers:
            channel.subscribers.append(agent_id)
        
        if channel_id not in self._subscriptions[agent_id]:
            self._subscriptions[agent_id].append(channel_id)
        
        return True
    
    def unsubscribe(self, agent_id: str, channel_id: str) -> bool:
        """取消订阅"""
        if channel_id not in self._channels:
            return False
        
        channel = self._channels[channel_id]
        if agent_id in channel.subscribers:
            channel.subscribers.remove(agent_id)
        
        if agent_id in self._subscriptions and channel_id in self._subscriptions[agent_id]:
            self._subscriptions[agent_id].remove(channel_id)
        
        return True
    
    def get_subscriptions(self, agent_id: str) -> List[str]:
        """获取智能体的订阅列表"""
        return self._subscriptions.get(agent_id, [])
    
    # ===== 消息发送 =====
    
    def send_message(self, sender_id: str, receiver_id: str, content: str,
                     message_type: MessageType = MessageType.DIRECT,
                     priority: MessagePriority = MessagePriority.NORMAL,
                     topic: str = "",
                     workflow_id: str = "",
                     task_id: str = "",
                     data: Dict[str, Any] = None,
                     expires_at: str = "") -> Optional[AgentMessage]:
        """发送直接消息"""
        if sender_id not in self._agents:
            return None
        
        message = AgentMessage(
            message_id=str(uuid.uuid4()),
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=message_type,
            priority=priority,
            topic=topic,
            workflow_id=workflow_id,
            task_id=task_id,
            data=data or {},
            status=MessageStatus.SENT,
            expires_at=expires_at
        )
        
        # 存入历史
        self._message_history.append(message)
        if len(self._message_history) > self._max_history:
            self._message_history.pop(0)
        
        # 存入发件箱
        self._outbox[sender_id].append(message)
        
        # 存入收件人收件箱
        if receiver_id in self._agents:
            self._inbox[receiver_id].append(message)
            message.status = MessageStatus.DELIVERED
            message.delivered_at = datetime.now().isoformat()
            
            # 加入收件人消息队列
            self._queues[receiver_id].enqueue(message)
            
            # 触发回调
            self._trigger_callbacks(receiver_id, message)
        else:
            # 接收者不存在，消息发送失败
            message.status = MessageStatus.FAILED
            message.error_message = "Receiver not found"
        
        return message
    
    def broadcast(self, sender_id: str, channel_id: str, content: str,
                  priority: MessagePriority = MessagePriority.NORMAL,
                  topic: str = "",
                  workflow_id: str = "",
                  task_id: str = "",
                  data: Dict[str, Any] = None) -> List[AgentMessage]:
        """广播消息到频道"""
        if sender_id not in self._agents:
            return []
        if channel_id not in self._channels:
            return []
        
        channel = self._channels[channel_id]
        sent_messages = []
        
        for subscriber_id in channel.subscribers:
            if subscriber_id == sender_id:
                continue
            
            message = self.send_message(
                sender_id=sender_id,
                receiver_id=subscriber_id,
                content=content,
                message_type=MessageType.BROADCAST,
                priority=priority,
                topic=topic or channel_id,
                workflow_id=workflow_id,
                task_id=task_id,
                data=data
            )
            if message:
                sent_messages.append(message)
        
        return sent_messages
    
    # ===== 消息接收 =====
    
    def receive_message(self, agent_id: str) -> Optional[AgentMessage]:
        """接收一条消息（从队列中取出）"""
        if agent_id not in self._agents:
            return None
        
        queue = self._queues.get(agent_id)
        if not queue:
            return None
        
        message = queue.dequeue()
        if message:
            message.status = MessageStatus.READ
            message.read_at = datetime.now().isoformat()
            self._agents[agent_id]["last_seen"] = datetime.now().isoformat()
        
        return message
    
    def receive_all_messages(self, agent_id: str, limit: int = 100) -> List[AgentMessage]:
        """接收所有未读消息"""
        messages = []
        for _ in range(limit):
            msg = self.receive_message(agent_id)
            if msg is None:
                break
            messages.append(msg)
        return messages
    
    def peek_message(self, agent_id: str) -> Optional[AgentMessage]:
        """查看下一条消息但不取出"""
        if agent_id not in self._agents:
            return None
        queue = self._queues.get(agent_id)
        return queue.peek() if queue else None
    
    def get_inbox(self, agent_id: str, limit: int = 50, 
                  status: MessageStatus = None,
                  message_type: MessageType = None) -> List[AgentMessage]:
        """获取收件箱历史"""
        messages = self._inbox.get(agent_id, [])
        if status:
            messages = [m for m in messages if m.status == status]
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return messages[-limit:]
    
    def get_outbox(self, agent_id: str, limit: int = 50,
                   message_type: MessageType = None) -> List[AgentMessage]:
        """获取发件箱历史"""
        messages = self._outbox.get(agent_id, [])
        if message_type:
            messages = [m for m in messages if m.message_type == message_type]
        return messages[-limit:]
    
    def get_conversation(self, agent1_id: str, agent2_id: str, limit: int = 50) -> List[AgentMessage]:
        """获取两个智能体之间的对话历史"""
        messages = []
        for msg in self._message_history:
            if (msg.sender_id == agent1_id and msg.receiver_id == agent2_id) or \
               (msg.sender_id == agent2_id and msg.receiver_id == agent1_id):
                messages.append(msg)
        return messages[-limit:]
    
    def get_workflow_messages(self, workflow_id: str) -> List[AgentMessage]:
        """获取工作流相关的所有消息"""
        return [m for m in self._message_history if m.workflow_id == workflow_id]
    
    def get_task_messages(self, task_id: str) -> List[AgentMessage]:
        """获取任务相关的所有消息"""
        return [m for m in self._message_history if m.task_id == task_id]
    
    # ===== 消息回调 =====
    
    def on_message(self, agent_id: str, callback: Callable[[AgentMessage], None]) -> None:
        """注册消息到达回调"""
        self._message_callbacks[agent_id].append(callback)
    
    def _trigger_callbacks(self, agent_id: str, message: AgentMessage) -> None:
        """触发消息回调"""
        for callback in self._message_callbacks.get(agent_id, []):
            try:
                callback(message)
            except Exception:
                pass  # 忽略回调异常
    
    # ===== 统计信息 =====
    
    def get_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体通信统计"""
        inbox = self._inbox.get(agent_id, [])
        outbox = self._outbox.get(agent_id, [])
        queue = self._queues.get(agent_id)
        
        unread_count = queue.size() if queue else 0
        
        return {
            "agent_id": agent_id,
            "total_received": len(inbox),
            "total_sent": len(outbox),
            "unread_count": unread_count,
            "subscriptions": self.get_subscriptions(agent_id),
            "status": self._agents.get(agent_id, {}).get("status", "unknown"),
            "last_seen": self._agents.get(agent_id, {}).get("last_seen", "")
        }
    
    def get_channel_stats(self, channel_id: str) -> Dict[str, Any]:
        """获取频道统计"""
        channel = self._channels.get(channel_id)
        if not channel:
            return {}
        
        channel_messages = [m for m in self._message_history if m.topic == channel_id]
        
        return {
            "channel_id": channel_id,
            "name": channel.name,
            "subscriber_count": len(channel.subscribers),
            "total_messages": len(channel_messages),
            "is_public": channel.is_public
        }
    
    def get_system_stats(self) -> Dict[str, Any]:
        """获取系统整体统计"""
        total_messages = len(self._message_history)
        online_agents = sum(1 for a in self._agents.values() if a["status"] == "online")
        
        return {
            "total_agents": len(self._agents),
            "online_agents": online_agents,
            "total_channels": len(self._channels),
            "total_messages": total_messages,
            "total_queued": sum(q.size() for q in self._queues.values()),
            "uptime": "N/A"
        }
    
    # ===== 持久化 =====
    
    def save_state(self, path: str = None) -> bool:
        """保存状态到文件"""
        save_path = path or self.storage_path
        if not save_path:
            return False
        
        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            state = {
                "agents": self._agents,
                "channels": {cid: ch.to_dict() for cid, ch in self._channels.items()},
                "message_history": [m.to_dict() for m in self._message_history],
                "inbox": {aid: [m.to_dict() for m in msgs] for aid, msgs in self._inbox.items()},
                "outbox": {aid: [m.to_dict() for m in msgs] for aid, msgs in self._outbox.items()},
                "subscriptions": dict(self._subscriptions),
                "saved_at": datetime.now().isoformat()
            }
            with open(save_path, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
            return True
        except Exception:
            return False
    
    def load_state(self, path: str = None) -> bool:
        """从文件加载状态"""
        load_path = path or self.storage_path
        if not load_path or not os.path.exists(load_path):
            return False
        
        try:
            with open(load_path, 'r', encoding='utf-8') as f:
                state = json.load(f)
            
            self._agents = state.get("agents", {})
            
            # 重建频道
            self._channels = {}
            for cid, ch_data in state.get("channels", {}).items():
                self._channels[cid] = MessageChannel(
                    channel_id=ch_data["channel_id"],
                    name=ch_data["name"],
                    description=ch_data.get("description", ""),
                    subscribers=ch_data.get("subscribers", []),
                    is_public=ch_data.get("is_public", True),
                    created_at=ch_data.get("created_at", ""),
                    metadata=ch_data.get("metadata", {})
                )
            
            # 重建消息历史
            self._message_history = [
                AgentMessage.from_dict(m) for m in state.get("message_history", [])
            ]
            
            # 重建收件箱和发件箱
            self._inbox = defaultdict(list)
            for aid, msgs in state.get("inbox", {}).items():
                self._inbox[aid] = [AgentMessage.from_dict(m) for m in msgs]
            
            self._outbox = defaultdict(list)
            for aid, msgs in state.get("outbox", {}).items():
                self._outbox[aid] = [AgentMessage.from_dict(m) for m in msgs]
            
            # 重建订阅
            self._subscriptions = defaultdict(list)
            for aid, channels in state.get("subscriptions", {}).items():
                self._subscriptions[aid] = channels
            
            # 重建消息队列（未读消息重新入队）
            self._queues = defaultdict(MessageQueue)
            for aid, messages in self._inbox.items():
                for msg in messages:
                    if msg.status == MessageStatus.DELIVERED:
                        self._queues[aid].enqueue(msg)
            
            return True
        except Exception:
            return False
    
    # ===== 工作流集成辅助方法 =====
    
    def send_task_message(self, sender_id: str, receiver_id: str, 
                          workflow_id: str, task_id: str, content: str,
                          data: Dict[str, Any] = None) -> Optional[AgentMessage]:
        """发送任务相关消息"""
        return self.send_message(
            sender_id=sender_id,
            receiver_id=receiver_id,
            content=content,
            message_type=MessageType.TASK,
            workflow_id=workflow_id,
            task_id=task_id,
            data=data
        )
    
    def broadcast_event(self, sender_id: str, event_name: str, 
                        data: Dict[str, Any] = None,
                        workflow_id: str = "") -> List[AgentMessage]:
        """广播事件到事件频道"""
        return self.broadcast(
            sender_id=sender_id,
            channel_id="events",
            content=f"Event: {event_name}",
            priority=MessagePriority.NORMAL,
            topic=event_name,
            workflow_id=workflow_id,
            data=data or {}
        )
    
    def send_system_message(self, receiver_id: str, content: str,
                            priority: MessagePriority = MessagePriority.HIGH) -> Optional[AgentMessage]:
        """发送系统消息"""
        return self.send_message(
            sender_id="system",
            receiver_id=receiver_id,
            content=content,
            message_type=MessageType.SYSTEM,
            priority=priority
        )
    
    # ===== 心跳机制 =====
    
    def send_heartbeat(self, agent_id: str) -> bool:
        """发送心跳（更新在线状态）"""
        if agent_id not in self._agents:
            return False
        self._agents[agent_id]["status"] = "online"
        self._agents[agent_id]["last_seen"] = datetime.now().isoformat()
        return True
    
    def check_offline_agents(self, timeout_seconds: int = 300) -> List[str]:
        """检查超时未心跳的智能体，标记为离线"""
        offline_agents = []
        now = datetime.now()
        
        for agent_id, agent_info in self._agents.items():
            if agent_info["status"] != "online":
                continue
            
            last_seen = agent_info.get("last_seen", "")
            if not last_seen:
                continue
            
            try:
                last_time = datetime.fromisoformat(last_seen)
                if (now - last_time).total_seconds() > timeout_seconds:
                    agent_info["status"] = "offline"
                    offline_agents.append(agent_id)
            except (ValueError, TypeError):
                pass
        
        return offline_agents
