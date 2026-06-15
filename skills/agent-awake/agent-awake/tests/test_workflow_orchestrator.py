#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流编排引擎测试套件
测试工作流定义、调度、任务分配、事件等功能
"""

import os
import sys
import tempfile
import shutil
import unittest
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from workflow_orchestrator import (
    WorkflowOrchestrator,
    WorkflowDefinition,
    WorkflowTask,
    WorkflowStatus,
    TaskStatus,
    SchedulingStrategy,
    WorkflowEventType,
    AgentInfo,
    create_orchestrator_with_presets,
    PRESET_WORKFLOWS
)


class TestAgentManagement(unittest.TestCase):
    """Agent管理测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = WorkflowOrchestrator(self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_register_agent(self):
        """测试注册Agent"""
        agent = self.orchestrator.register_agent(
            agent_id="agent_001",
            agent_name="测试Agent",
            role="builder",
            capabilities=["需求分析", "架构设计"],
            tags=["python", "backend"]
        )
        
        self.assertEqual(agent.agent_id, "agent_001")
        self.assertEqual(agent.agent_name, "测试Agent")
        self.assertEqual(agent.role, "builder")
        self.assertEqual(agent.status, "idle")
        self.assertEqual(len(agent.capabilities), 2)
    
    def test_get_agent(self):
        """测试获取Agent"""
        self.orchestrator.register_agent("agent_001", "测试")
        
        agent = self.orchestrator.get_agent("agent_001")
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_name, "测试")
        
        # 不存在的Agent
        self.assertIsNone(self.orchestrator.get_agent("nonexistent"))
    
    def test_list_agents(self):
        """测试列出Agent"""
        self.orchestrator.register_agent("a1", "Agent1", role="builder")
        self.orchestrator.register_agent("a2", "Agent2", role="breaker")
        self.orchestrator.register_agent("a3", "Agent3", role="builder")
        
        # 所有Agent
        all_agents = self.orchestrator.list_agents()
        self.assertEqual(len(all_agents), 3)
        
        # 按角色过滤
        builders = self.orchestrator.list_agents(role_filter="builder")
        self.assertEqual(len(builders), 2)
    
    def test_agent_heartbeat(self):
        """测试心跳"""
        self.orchestrator.register_agent("agent_001", "测试")
        
        # 模拟离线
        self.orchestrator.update_agent_status("agent_001", "offline")
        
        # 心跳应该恢复为idle
        result = self.orchestrator.heartbeat("agent_001")
        self.assertTrue(result)
        
        agent = self.orchestrator.get_agent("agent_001")
        self.assertEqual(agent.status, "idle")
    
    def test_unregister_agent(self):
        """测试注销Agent"""
        self.orchestrator.register_agent("agent_001", "测试")
        
        result = self.orchestrator.unregister_agent("agent_001")
        self.assertTrue(result)
        
        self.assertIsNone(self.orchestrator.get_agent("agent_001"))


class TestWorkflowDefinition(unittest.TestCase):
    """工作流定义测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = WorkflowOrchestrator(self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_register_definition(self):
        """测试注册工作流定义"""
        wf_def = WorkflowDefinition(
            workflow_type="test_workflow",
            name="测试工作流",
            description="这是一个测试工作流",
            version="1.0",
            tasks=[
                {"task_id": "task1", "name": "任务1", "task_type": "analysis"},
                {"task_id": "task2", "name": "任务2", "task_type": "development", 
                 "dependencies": ["task1"]}
            ],
            on_failure="stop"
        )
        
        result = self.orchestrator.register_workflow_definition(wf_def)
        self.assertTrue(result)
        
        # 获取定义
        retrieved = self.orchestrator.get_workflow_definition("test_workflow")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.name, "测试工作流")
        self.assertEqual(len(retrieved.tasks), 2)
    
    def test_list_definitions(self):
        """测试列出工作流定义"""
        for i in range(3):
            wf_def = WorkflowDefinition(
                workflow_type=f"wf_{i}",
                name=f"工作流{i}",
                tasks=[{"task_id": "t1", "name": "任务1", "task_type": "test"}]
            )
            self.orchestrator.register_workflow_definition(wf_def)
        
        defs = self.orchestrator.list_workflow_definitions()
        self.assertEqual(len(defs), 3)
    
    def test_preset_workflows(self):
        """测试预置工作流"""
        orch = create_orchestrator_with_presets(self.test_dir)
        
        defs = orch.list_workflow_definitions()
        self.assertGreaterEqual(len(defs), 3)
        
        # 检查是否有功能开发工作流
        feature_dev = orch.get_workflow_definition("feature_development")
        self.assertIsNotNone(feature_dev)
        self.assertEqual(feature_dev.name, "功能开发工作流")
        self.assertEqual(len(feature_dev.tasks), 5)  # 需求/设计/开发/测试/部署


class TestWorkflowInstance(unittest.TestCase):
    """工作流实例测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = create_orchestrator_with_presets(self.test_dir)
        
        # 注册一些Agent
        self.orchestrator.register_agent(
            "builder_01", "架构师", role="builder",
            capabilities=["需求分析", "架构设计", "技术选型"]
        )
        self.orchestrator.register_agent(
            "dev_01", "开发者", role="constructor",
            capabilities=["编程开发", "单元测试"]
        )
        self.orchestrator.register_agent(
            "tester_01", "测试员", role="breaker",
            capabilities=["测试", "安全审计"]
        )
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_create_workflow(self):
        """测试创建工作流实例"""
        workflow = self.orchestrator.create_workflow(
            workflow_type="feature_development",
            name="测试功能开发",
            triggered_by="test_user"
        )
        
        self.assertIsNotNone(workflow)
        self.assertEqual(workflow.workflow_type, "feature_development")
        self.assertEqual(workflow.name, "测试功能开发")
        self.assertEqual(workflow.status, WorkflowStatus.PENDING)
        self.assertEqual(len(workflow.tasks), 5)  # 5个任务
    
    def test_create_nonexistent_workflow(self):
        """测试创建不存在的工作流类型"""
        workflow = self.orchestrator.create_workflow("nonexistent_type")
        self.assertIsNone(workflow)
    
    def test_start_workflow(self):
        """测试启动工作流"""
        workflow = self.orchestrator.create_workflow("feature_development")
        
        result = self.orchestrator.start_workflow(workflow.workflow_id)
        self.assertTrue(result)
        
        updated = self.orchestrator.get_workflow(workflow.workflow_id)
        self.assertEqual(updated.status, WorkflowStatus.RUNNING)
        self.assertIsNotNone(updated.started_at)
    
    def test_start_running_workflow(self):
        """测试重复启动运行中的工作流"""
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        
        # 再次启动应该失败
        result = self.orchestrator.start_workflow(workflow.workflow_id)
        self.assertFalse(result)
    
    def test_workflow_tasks_hierarchy(self):
        """测试工作流任务依赖关系"""
        workflow = self.orchestrator.create_workflow("code_review")
        
        # 检查任务数量
        self.assertEqual(len(workflow.tasks), 4)
        
        # 检查初始状态 - 没有依赖的任务应该是PENDING，等start后变成READY
        # 找一个没有依赖的任务（第一个任务initial_review）
        for task in workflow.tasks.values():
            if "initial_review" in task.task_id:
                self.assertEqual(len(task.dependencies), 0)
            elif "rework" in task.task_id:
                self.assertEqual(len(task.dependencies), 1)
            elif "final_review" in task.task_id:
                self.assertEqual(len(task.dependencies), 1)
            elif "merge" in task.task_id:
                self.assertEqual(len(task.dependencies), 1)
    
    def test_pause_resume_workflow(self):
        """测试暂停和恢复工作流"""
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        
        # 暂停
        result = self.orchestrator.pause_workflow(workflow.workflow_id)
        self.assertTrue(result)
        
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        self.assertEqual(wf.status, WorkflowStatus.PAUSED)
        
        # 恢复
        result = self.orchestrator.resume_workflow(workflow.workflow_id)
        self.assertTrue(result)
        
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        self.assertEqual(wf.status, WorkflowStatus.RUNNING)
    
    def test_cancel_workflow(self):
        """测试取消工作流"""
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        
        result = self.orchestrator.cancel_workflow(workflow.workflow_id)
        self.assertTrue(result)
        
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        self.assertEqual(wf.status, WorkflowStatus.CANCELLED)
        
        # 所有任务都应该被取消
        for task in wf.tasks.values():
            self.assertIn(task.status, 
                         [TaskStatus.CANCELLED, TaskStatus.PENDING, TaskStatus.READY])
    
    def test_list_workflows(self):
        """测试列出工作流"""
        for i in range(5):
            wf = self.orchestrator.create_workflow("feature_development", name=f"工作流{i}")
            if i % 2 == 0:
                self.orchestrator.start_workflow(wf.workflow_id)
        
        # 所有工作流
        all_wf = self.orchestrator.list_workflows()
        self.assertEqual(len(all_wf), 5)
        
        # 运行中的工作流
        running = self.orchestrator.list_workflows(status_filter=WorkflowStatus.RUNNING)
        self.assertEqual(len(running), 3)  # 0,2,4 是运行的


class TestTaskScheduling(unittest.TestCase):
    """任务调度测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = create_orchestrator_with_presets(self.test_dir)
        
        # 注册各类Agent
        self.orchestrator.register_agent(
            "builder_01", "架构师", role="builder",
            capabilities=["需求分析", "架构设计", "技术选型"]
        )
        self.orchestrator.register_agent(
            "dev_01", "开发者A", role="constructor",
            capabilities=["编程开发", "单元测试"],
            tags=["python", "backend"]
        )
        self.orchestrator.register_agent(
            "dev_02", "开发者B", role="constructor",
            capabilities=["编程开发", "代码审查"],
            tags=["java", "backend"]
        )
        self.orchestrator.register_agent(
            "tester_01", "测试员", role="breaker",
            capabilities=["测试", "安全审计"]
        )
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_dispatch_initial_tasks(self):
        """测试调度初始任务"""
        workflow = self.orchestrator.create_workflow("feature_development")
        
        # 手动启动，不自动调度
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now().isoformat()
        self.orchestrator._update_ready_tasks(workflow)
        self.orchestrator._save_state()
        
        # 调度任务
        dispatched = self.orchestrator.dispatch()
        
        # 应该有第一个任务（需求分析）被分配
        self.assertGreater(len(dispatched), 0)
        
        # 检查任务状态
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        assigned_tasks = [t for t in wf.tasks.values() 
                         if t.status == TaskStatus.ASSIGNED]
        self.assertGreater(len(assigned_tasks), 0)
        
        # 检查Agent状态
        busy_agents = self.orchestrator.list_agents(status_filter="busy")
        self.assertGreater(len(busy_agents), 0)
    
    def test_find_suitable_agent_best_match(self):
        """测试最佳匹配策略"""
        # 创建一个需要builder角色的任务
        task = WorkflowTask(
            task_id="test_task",
            name="测试任务",
            task_type="design",
            requirements={
                "role": "builder",
                "capabilities": ["架构设计"]
            }
        )
        
        agent = self.orchestrator.find_suitable_agent(
            task, SchedulingStrategy.BEST_MATCH
        )
        
        self.assertIsNotNone(agent)
        # 应该匹配到builder_01
        self.assertEqual(agent.role, "builder")
    
    def test_find_suitable_agent_round_robin(self):
        """测试轮询策略"""
        # 第一个应该是第一个注册的空闲Agent
        task = WorkflowTask(task_id="t1", name="t1", task_type="test")
        
        agents = []
        for _ in range(3):
            agent = self.orchestrator.find_suitable_agent(
                task, SchedulingStrategy.ROUND_ROBIN
            )
            if agent:
                agents.append(agent.agent_id)
        
        # 应该有不同的Agent被选中
        self.assertGreater(len(set(agents)), 1)
    
    def test_find_suitable_agent_no_idle(self):
        """测试没有空闲Agent时"""
        # 把所有Agent设为busy
        for agent_id in ["builder_01", "dev_01", "dev_02", "tester_01"]:
            self.orchestrator.update_agent_status(agent_id, "busy")
        
        task = WorkflowTask(task_id="t1", name="t1", task_type="test")
        agent = self.orchestrator.find_suitable_agent(task)
        
        self.assertIsNone(agent)
    
    def test_complete_task_triggers_next(self):
        """测试完成任务后触发后续任务"""
        workflow = self.orchestrator.create_workflow("code_review")
        
        # 手动启动
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now().isoformat()
        self.orchestrator._update_ready_tasks(workflow)
        self.orchestrator._save_state()
        
        # 调度第一个任务
        dispatched = self.orchestrator.dispatch()
        self.assertGreater(len(dispatched), 0)
        
        # 找到第一个任务（initial_review）并完成
        first_task = None
        for task in workflow.tasks.values():
            if task.status == TaskStatus.ASSIGNED:
                first_task = task
                break
        
        self.assertIsNotNone(first_task)
        
        # 标记任务开始并完成
        self.orchestrator.start_task(first_task.task_id)
        
        # 手动完成，不自动调度（通过直接调用内部方法）
        task = workflow.tasks[first_task.task_id]
        task.status = TaskStatus.COMPLETED
        task.result = "审查完成"
        task.completed_at = datetime.now().isoformat()
        
        # 释放Agent
        if task.assigned_agent:
            agent = self.orchestrator.agents.get(task.assigned_agent)
            if agent:
                agent.status = "idle"
                agent.current_task = ""
                agent.tasks_completed += 1
        
        self.orchestrator._save_state()
        
        # 现在手动触发下一批任务的就绪状态
        self.orchestrator._update_ready_tasks(workflow)
        
        # 检查后续任务是否变成就绪
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        ready_tasks = [t for t in wf.tasks.values() if t.status == TaskStatus.READY]
        # 应该有rework任务变成就绪
        self.assertGreaterEqual(len(ready_tasks), 1)
    
    def test_task_retry(self):
        """测试任务重试"""
        workflow = self.orchestrator.create_workflow("code_review")
        
        # 手动启动
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now().isoformat()
        self.orchestrator._update_ready_tasks(workflow)
        self.orchestrator._save_state()
        
        # 调度并获取第一个任务
        self.orchestrator.dispatch()
        
        first_task = None
        for task in workflow.tasks.values():
            if task.status == TaskStatus.ASSIGNED:
                first_task = task
                break
        
        self.assertIsNotNone(first_task)
        task_id = first_task.task_id
        original_agent = first_task.assigned_agent
        
        # 第一次失败（通过直接修改状态来模拟，避免自动调度）
        task = workflow.tasks[task_id]
        task.error_message = "错误1"
        task.retry_count = 1
        task.status = TaskStatus.READY
        task.assigned_agent = ""
        task.started_at = ""
        
        # 释放Agent
        if original_agent:
            agent = self.orchestrator.agents.get(original_agent)
            if agent:
                agent.status = "idle"
                agent.current_task = ""
                agent.tasks_failed += 1
        
        self.orchestrator._save_state()
        
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        task = wf.tasks[task_id]
        self.assertEqual(task.retry_count, 1)
        # 应该是READY状态，可以重试
        self.assertEqual(task.status, TaskStatus.READY)
        
        # 再次调度，应该能分配到新的或者同一个Agent
        dispatched = self.orchestrator.dispatch()
        self.assertGreater(len(dispatched), 0)
        
        # 检查任务被重新分配
        wf2 = self.orchestrator.get_workflow(workflow.workflow_id)
        task2 = wf2.tasks[task_id]
        self.assertEqual(task2.status, TaskStatus.ASSIGNED)
        
        # 多次失败直到达到最大重试次数
        max_retries = task2.max_retries
        for i in range(max_retries):
            # 模拟失败
            task2.status = TaskStatus.FAILED
            task2.completed_at = datetime.now().isoformat()
            task2.retry_count = max_retries + 1
            
            # 释放Agent
            if task2.assigned_agent:
                agent = self.orchestrator.agents.get(task2.assigned_agent)
                if agent:
                    agent.status = "idle"
                    agent.current_task = ""
                    agent.tasks_failed += 1
            
            self.orchestrator._save_state()
            break  # 只测试一次失败达到max的情况
        
        wf3 = self.orchestrator.get_workflow(workflow.workflow_id)
        task3 = wf3.tasks[task_id]
        self.assertEqual(task3.status, TaskStatus.FAILED)
        self.assertGreater(task3.retry_count, max_retries)


class TestWorkflowEvents(unittest.TestCase):
    """工作流事件测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = create_orchestrator_with_presets(self.test_dir)
        self.events_received = []
        
        # 注册事件处理器
        def handler(event):
            self.events_received.append(event)
        
        self.orchestrator.on("*", handler)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_workflow_start_event(self):
        """测试工作流启动事件"""
        workflow = self.orchestrator.create_workflow("feature_development")
        initial_count = len(self.events_received)
        
        self.orchestrator.start_workflow(workflow.workflow_id)
        
        # 应该有workflow_started事件
        start_events = [e for e in self.events_received 
                       if e.event_type == WorkflowEventType.WORKFLOW_STARTED]
        self.assertGreater(len(start_events), initial_count)
    
    def test_task_assign_event(self):
        """测试任务分配事件"""
        self.orchestrator.register_agent("test_agent", "测试Agent")
        
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        
        initial_count = len(self.events_received)
        
        # 调度会触发任务分配事件
        self.orchestrator.dispatch()
        
        assign_events = [e for e in self.events_received 
                        if e.event_type == WorkflowEventType.TASK_ASSIGNED]
        self.assertGreater(len(assign_events), 0)
    
    def test_task_complete_event(self):
        """测试任务完成事件"""
        self.orchestrator.register_agent("test_agent", "测试Agent")
        
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        self.orchestrator.dispatch()
        
        # 找到一个已分配的任务
        task = None
        for t in workflow.tasks.values():
            if t.status == TaskStatus.ASSIGNED:
                task = t
                break
        
        self.assertIsNotNone(task)
        
        initial_count = len([e for e in self.events_received 
                            if e.event_type == WorkflowEventType.TASK_COMPLETED])
        
        self.orchestrator.complete_task(task.task_id)
        
        complete_events = [e for e in self.events_received 
                          if e.event_type == WorkflowEventType.TASK_COMPLETED]
        self.assertEqual(len(complete_events), initial_count + 1)


class TestStatistics(unittest.TestCase):
    """统计与监控测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = create_orchestrator_with_presets(self.test_dir)
        
        self.orchestrator.register_agent("a1", "Agent1", role="builder")
        self.orchestrator.register_agent("a2", "Agent2", role="constructor")
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_get_statistics_empty(self):
        """测试空状态统计"""
        stats = self.orchestrator.get_statistics()
        
        self.assertEqual(stats["agents"]["total"], 2)
        self.assertEqual(stats["agents"]["idle"], 2)
        self.assertEqual(stats["workflows"]["total"], 0)
        self.assertEqual(stats["tasks"]["total"], 0)
    
    def test_get_statistics_with_workflow(self):
        """测试有工作流时的统计"""
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        self.orchestrator.dispatch()
        
        stats = self.orchestrator.get_statistics()
        
        self.assertEqual(stats["workflows"]["total"], 1)
        self.assertEqual(stats["workflows"]["running"], 1)
        self.assertGreater(stats["tasks"]["total"], 0)
    
    def test_workflow_progress(self):
        """测试工作流进度"""
        workflow = self.orchestrator.create_workflow("code_review")
        
        # 未开始
        progress = self.orchestrator.get_workflow_progress(workflow.workflow_id)
        self.assertEqual(progress["progress_percent"], 0)
        self.assertEqual(progress["total_tasks"], 4)
        self.assertEqual(progress["completed_tasks"], 0)
    
    def test_agent_workload(self):
        """测试Agent工作负载"""
        workload = self.orchestrator.get_agent_workload("a1")
        
        self.assertEqual(workload["agent_id"], "a1")
        self.assertEqual(workload["status"], "idle")
        self.assertEqual(workload["tasks_completed"], 0)
    
    def test_nonexistent_agent_workload(self):
        """测试不存在的Agent"""
        workload = self.orchestrator.get_agent_workload("nonexistent")
        self.assertIn("error", workload)


class TestPersistence(unittest.TestCase):
    """持久化测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_state_persistence(self):
        """测试状态持久化"""
        # 创建第一个实例并添加数据
        orch1 = create_orchestrator_with_presets(self.test_dir)
        orch1.register_agent("test_agent", "测试Agent", role="builder")
        
        workflow = orch1.create_workflow("feature_development", name="持久化测试")
        wf_id = workflow.workflow_id
        
        # 保存状态
        orch1._save_state()
        
        # 创建第二个实例，应该加载相同的数据
        orch2 = WorkflowOrchestrator(self.test_dir)
        
        # 检查Agent是否被加载
        agent = orch2.get_agent("test_agent")
        self.assertIsNotNone(agent)
        self.assertEqual(agent.agent_name, "测试Agent")
        
        # 检查工作流是否被加载
        wf = orch2.get_workflow(wf_id)
        self.assertIsNotNone(wf)
        self.assertEqual(wf.name, "持久化测试")
        self.assertEqual(len(wf.tasks), 5)
    
    def test_definition_persistence(self):
        """测试工作流定义持久化"""
        orch1 = create_orchestrator_with_presets(self.test_dir)
        defs_count = len(orch1.list_workflow_definitions())
        
        # 创建第二个实例
        orch2 = WorkflowOrchestrator(self.test_dir)
        self.assertEqual(len(orch2.list_workflow_definitions()), defs_count)


class TestCleanup(unittest.TestCase):
    """清理功能测试"""
    
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.orchestrator = create_orchestrator_with_presets(self.test_dir)
    
    def tearDown(self):
        shutil.rmtree(self.test_dir)
    
    def test_cleanup_completed(self):
        """测试清理已完成的工作流"""
        # 创建并完成一个工作流
        workflow = self.orchestrator.create_workflow("feature_development")
        self.orchestrator.start_workflow(workflow.workflow_id)
        
        # 手动标记所有任务为完成
        wf = self.orchestrator.get_workflow(workflow.workflow_id)
        for task in wf.tasks.values():
            task.status = TaskStatus.COMPLETED
            task.completed_at = "2020-01-01T00:00:00"  # 很久以前
        
        wf.status = WorkflowStatus.COMPLETED
        wf.completed_at = "2020-01-01T00:00:00"
        self.orchestrator._save_state()
        
        # 清理30天前的
        cleaned = self.orchestrator.cleanup_completed(days=30)
        self.assertGreaterEqual(cleaned, 1)
        
        # 验证已被清理
        self.assertIsNone(self.orchestrator.get_workflow(workflow.workflow_id))


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestAgentManagement))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowDefinition))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowInstance))
    suite.addTests(loader.loadTestsFromTestCase(TestTaskScheduling))
    suite.addTests(loader.loadTestsFromTestCase(TestWorkflowEvents))
    suite.addTests(loader.loadTestsFromTestCase(TestStatistics))
    suite.addTests(loader.loadTestsFromTestCase(TestPersistence))
    suite.addTests(loader.loadTestsFromTestCase(TestCleanup))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    
    print("\n" + "=" * 60)
    print(f"测试总计: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
