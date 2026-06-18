#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
工作流编排引擎
Workflow Orchestration Engine v1.0

多智能体永生平台 - 任务编排层核心模块
提供工作流定义、任务依赖管理、多Agent协同、事件驱动调度

核心功能：
- 工作流定义与执行（DAG有向无环图）
- 多智能体协同任务分配
- 事件驱动的任务状态机
- 任务模板与复用
- 调度策略引擎
- 进度追踪与实时状态
- 失败重试与回滚机制
- 工作流版本管理
"""

import os
import json
import uuid
import time
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import copy


class WorkflowStatus(str, Enum):
    """工作流状态"""
    PENDING = "pending"           # 等待开始
    RUNNING = "running"           # 运行中
    PAUSED = "paused"             # 已暂停
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    CANCELLED = "cancelled"       # 已取消


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"           # 待处理
    READY = "ready"               # 就绪（依赖满足）
    ASSIGNED = "assigned"         # 已分配
    RUNNING = "running"           # 运行中
    WAITING = "waiting"           # 等待外部输入
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    SKIPPED = "skipped"           # 已跳过
    CANCELLED = "cancelled"       # 已取消


class SchedulingStrategy(str, Enum):
    """调度策略"""
    FIRST_AVAILABLE = "first_available"     # 第一个可用的Agent
    BEST_MATCH = "best_match"               # 最佳匹配（能力/角色）
    ROUND_ROBIN = "round_robin"             # 轮询
    LOAD_BALANCED = "load_balanced"         # 负载均衡
    PRIORITY_FIRST = "priority_first"       # 优先级优先


class WorkflowEventType(str, Enum):
    """工作流事件类型"""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_ASSIGNED = "task_assigned"
    AGENT_REGISTERED = "agent_registered"
    AGENT_OFFLINE = "agent_offline"


@dataclass
class WorkflowTask:
    """工作流中的任务节点"""
    task_id: str
    name: str
    task_type: str
    description: str = ""
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str = ""
    dependencies: List[str] = field(default_factory=list)
    dependents: List[str] = field(default_factory=list)
    priority: int = 2
    tags: List[str] = field(default_factory=list)
    requirements: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    estimated_duration: int = 300  # 秒
    timeout: int = 3600  # 超时时间（秒）
    data: Dict[str, Any] = field(default_factory=dict)  # 任务相关数据
    
    def to_dict(self) -> Dict:
        return {
            "task_id": self.task_id,
            "name": self.name,
            "task_type": self.task_type,
            "description": self.description,
            "status": self.status,
            "assigned_agent": self.assigned_agent,
            "dependencies": self.dependencies,
            "dependents": self.dependents,
            "priority": self.priority,
            "tags": self.tags,
            "requirements": self.requirements,
            "result": self.result,
            "error_message": self.error_message,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "estimated_duration": self.estimated_duration,
            "timeout": self.timeout,
            "data": self.data
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkflowTask':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


@dataclass
class WorkflowDefinition:
    """工作流定义（模板）"""
    workflow_type: str
    name: str
    description: str = ""
    version: str = "1.0"
    tasks: List[Dict] = field(default_factory=list)  # 任务定义列表
    variables: Dict[str, Any] = field(default_factory=dict)  # 全局变量
    default_timeout: int = 3600
    on_failure: str = "stop"  # stop, continue, rollback
    
    def to_dict(self) -> Dict:
        return {
            "workflow_type": self.workflow_type,
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "tasks": self.tasks,
            "variables": self.variables,
            "default_timeout": self.default_timeout,
            "on_failure": self.on_failure
        }


@dataclass
class WorkflowInstance:
    """工作流运行实例"""
    workflow_id: str
    workflow_type: str
    name: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    tasks: Dict[str, WorkflowTask] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    trigger: str = "manual"  # manual, scheduled, event
    triggered_by: str = ""
    on_failure: str = "stop"
    
    def to_dict(self) -> Dict:
        return {
            "workflow_id": self.workflow_id,
            "workflow_type": self.workflow_type,
            "name": self.name,
            "status": self.status,
            "tasks": {k: v.to_dict() for k, v in self.tasks.items()},
            "variables": self.variables,
            "created_at": self.created_at,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "trigger": self.trigger,
            "triggered_by": self.triggered_by,
            "on_failure": self.on_failure
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'WorkflowInstance':
        tasks = {}
        if "tasks" in data:
            for k, v in data["tasks"].items():
                tasks[k] = WorkflowTask.from_dict(v)
        
        instance = cls(
            workflow_id=data["workflow_id"],
            workflow_type=data["workflow_type"],
            name=data["name"],
            status=WorkflowStatus(data.get("status", "pending")),
            tasks=tasks,
            variables=data.get("variables", {}),
            created_at=data.get("created_at", ""),
            started_at=data.get("started_at", ""),
            completed_at=data.get("completed_at", ""),
            trigger=data.get("trigger", "manual"),
            triggered_by=data.get("triggered_by", ""),
            on_failure=data.get("on_failure", "stop")
        )
        return instance


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    agent_name: str
    role: str = "default"
    status: str = "idle"  # idle, busy, offline
    current_task: str = ""
    current_workflow: str = ""
    capabilities: List[str] = field(default_factory=list)
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: str = ""
    load_score: float = 0.0  # 负载分数
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "role": self.role,
            "status": self.status,
            "current_task": self.current_task,
            "current_workflow": self.current_workflow,
            "capabilities": self.capabilities,
            "tasks_completed": self.tasks_completed,
            "tasks_failed": self.tasks_failed,
            "last_heartbeat": self.last_heartbeat,
            "load_score": self.load_score,
            "tags": self.tags,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'AgentInfo':
        return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})


class WorkflowEvent:
    """工作流事件"""
    
    def __init__(self, event_type: str, data: Dict[str, Any] = None):
        self.event_id = f"evt_{uuid.uuid4().hex[:12]}"
        self.event_type = event_type
        self.timestamp = datetime.now().isoformat()
        self.data = data or {}
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp,
            "data": self.data
        }


class WorkflowOrchestrator:
    """工作流编排器
    
    多智能体平台级任务编排核心，支持：
    - 工作流定义与版本管理
    - DAG任务依赖调度
    - 多智能体任务分配
    - 事件驱动架构
    - 进度追踪与监控
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "orchestrator_data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 工作流定义
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        
        # 运行实例
        self.workflows: Dict[str, WorkflowInstance] = {}
        self.agents: Dict[str, AgentInfo] = {}
        
        # 事件总线
        self.event_handlers: Dict[str, List[Callable]] = defaultdict(list)
        self.event_history: List[WorkflowEvent] = []
        
        # 调度状态
        self.scheduling_enabled = True
        self.last_dispatch_time = ""
        
        # 轮询指针
        self._round_robin_index = 0
        
        # 加载持久化数据
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        workflows_file = self.data_dir / "workflows.json"
        agents_file = self.data_dir / "agents.json"
        defs_file = self.data_dir / "workflow_definitions.json"
        
        if workflows_file.exists():
            try:
                with open(workflows_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.workflows = {k: WorkflowInstance.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, TypeError):
                pass
        
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.agents = {k: AgentInfo.from_dict(v) for k, v in data.items()}
            except (json.JSONDecodeError, TypeError):
                pass
        
        if defs_file.exists():
            try:
                with open(defs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.workflow_definitions = {
                    k: WorkflowDefinition(**v) for k, v in data.items()
                }
            except (json.JSONDecodeError, TypeError):
                pass
    
    def _save_state(self):
        """保存状态"""
        workflows_file = self.data_dir / "workflows.json"
        agents_file = self.data_dir / "agents.json"
        defs_file = self.data_dir / "workflow_definitions.json"
        
        with open(workflows_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.workflows.items()},
                f, indent=2, ensure_ascii=False
            )
        
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.agents.items()},
                f, indent=2, ensure_ascii=False
            )
        
        with open(defs_file, 'w', encoding='utf-8') as f:
            json.dump(
                {k: v.to_dict() for k, v in self.workflow_definitions.items()},
                f, indent=2, ensure_ascii=False
            )
    
    # ========== 事件系统 ==========
    
    def on(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        self.event_handlers[event_type].append(handler)
    
    def _emit_event(self, event: WorkflowEvent):
        """触发事件"""
        self.event_history.append(event)
        
        # 保留最近1000条事件
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
        
        # 调用处理器
        for handler in self.event_handlers.get(event.event_type, []):
            try:
                handler(event)
            except Exception as e:
                print(f"事件处理器执行失败: {e}")
        
        # 调用通用处理器
        for handler in self.event_handlers.get("*", []):
            try:
                handler(event)
            except Exception as e:
                print(f"事件处理器执行失败: {e}")
    
    # ========== 工作流定义 ==========
    
    def register_workflow_definition(self, wf_def: WorkflowDefinition) -> bool:
        """注册工作流定义
        
        Args:
            wf_def: 工作流定义
        
        Returns:
            是否成功
        """
        self.workflow_definitions[wf_def.workflow_type] = wf_def
        self._save_state()
        return True
    
    def get_workflow_definition(self, workflow_type: str) -> Optional[WorkflowDefinition]:
        """获取工作流定义"""
        return self.workflow_definitions.get(workflow_type)
    
    def list_workflow_definitions(self) -> List[WorkflowDefinition]:
        """列出所有工作流定义"""
        return list(self.workflow_definitions.values())
    
    # ========== Agent管理 ==========
    
    def register_agent(self, agent_id: str, agent_name: str = "",
                      role: str = "default", 
                      capabilities: List[str] = None,
                      tags: List[str] = None) -> AgentInfo:
        """注册Agent
        
        Args:
            agent_id: Agent ID
            agent_name: Agent名称
            role: 角色
            capabilities: 能力列表
            tags: 标签
        
        Returns:
            Agent信息
        """
        agent = AgentInfo(
            agent_id=agent_id,
            agent_name=agent_name or agent_id,
            role=role,
            capabilities=capabilities or [],
            tags=tags or [],
            last_heartbeat=datetime.now().isoformat()
        )
        
        self.agents[agent_id] = agent
        self._save_state()
        
        self._emit_event(WorkflowEvent(
            WorkflowEventType.AGENT_REGISTERED,
            {"agent_id": agent_id, "agent_name": agent_name}
        ))
        
        return agent
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save_state()
            
            self._emit_event(WorkflowEvent(
                WorkflowEventType.AGENT_OFFLINE,
                {"agent_id": agent_id}
            ))
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取Agent信息"""
        return self.agents.get(agent_id)
    
    def list_agents(self, status_filter: str = None,
                   role_filter: str = None) -> List[AgentInfo]:
        """列出Agent"""
        agents = list(self.agents.values())
        
        if status_filter:
            agents = [a for a in agents if a.status == status_filter]
        if role_filter:
            agents = [a for a in agents if a.role == role_filter]
        
        return agents
    
    def update_agent_status(self, agent_id: str, status: str) -> Optional[AgentInfo]:
        """更新Agent状态"""
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        
        agent.status = status
        agent.last_heartbeat = datetime.now().isoformat()
        self._save_state()
        return agent
    
    def heartbeat(self, agent_id: str) -> bool:
        """Agent心跳"""
        agent = self.agents.get(agent_id)
        if not agent:
            return False
        
        agent.last_heartbeat = datetime.now().isoformat()
        
        # 如果是offline状态，自动恢复为idle
        if agent.status == "offline":
            agent.status = "idle"
        
        self._save_state()
        return True
    
    # ========== 工作流实例管理 ==========
    
    def create_workflow(self, workflow_type: str, 
                       name: str = None,
                       variables: Dict[str, Any] = None,
                       trigger: str = "manual",
                       triggered_by: str = "") -> Optional[WorkflowInstance]:
        """从定义创建工作流实例
        
        Args:
            workflow_type: 工作流类型
            name: 工作流名称（可选，默认使用定义中的名称）
            variables: 变量覆盖
            trigger: 触发方式
            triggered_by: 触发者
        
        Returns:
            工作流实例
        """
        wf_def = self.workflow_definitions.get(workflow_type)
        if not wf_def:
            return None
        
        # 生成工作流ID
        workflow_id = f"wf_{datetime.now().strftime('%Y%m%d%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # 构建任务
        tasks = {}
        for task_def in wf_def.tasks:
            task_id = f"{workflow_id}_{task_def['task_id']}"
            task = WorkflowTask(
                task_id=task_id,
                name=task_def.get("name", task_def["task_id"]),
                task_type=task_def.get("task_type", "general"),
                description=task_def.get("description", ""),
                dependencies=[f"{workflow_id}_{d}" for d in task_def.get("dependencies", [])],
                priority=task_def.get("priority", 2),
                tags=task_def.get("tags", []),
                requirements=task_def.get("requirements", {}),
                max_retries=task_def.get("max_retries", 3),
                estimated_duration=task_def.get("estimated_duration", 300),
                timeout=task_def.get("timeout", wf_def.default_timeout),
                data=task_def.get("data", {}),
                created_at=datetime.now().isoformat()
            )
            tasks[task_id] = task
        
        # 构建依赖关系（反向）
        for task_id, task in tasks.items():
            for dep_id in task.dependencies:
                if dep_id in tasks:
                    if task_id not in tasks[dep_id].dependents:
                        tasks[dep_id].dependents.append(task_id)
        
        # 合并变量
        merged_vars = {**wf_def.variables, **(variables or {})}
        
        # 创建实例
        workflow = WorkflowInstance(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            name=name or wf_def.name,
            status=WorkflowStatus.PENDING,
            tasks=tasks,
            variables=merged_vars,
            created_at=datetime.now().isoformat(),
            trigger=trigger,
            triggered_by=triggered_by,
            on_failure=wf_def.on_failure
        )
        
        self.workflows[workflow_id] = workflow
        self._save_state()
        
        return workflow
    
    def start_workflow(self, workflow_id: str) -> bool:
        """启动工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        if workflow.status != WorkflowStatus.PENDING:
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now().isoformat()
        
        # 更新初始就绪任务
        self._update_ready_tasks(workflow)
        
        self._save_state()
        
        self._emit_event(WorkflowEvent(
            WorkflowEventType.WORKFLOW_STARTED,
            {"workflow_id": workflow_id, "name": workflow.name}
        ))
        
        # 立即尝试调度
        self.dispatch()
        
        return True
    
    def _update_ready_tasks(self, workflow: WorkflowInstance):
        """更新工作流中的就绪任务"""
        for task_id, task in workflow.tasks.items():
            if task.status == TaskStatus.PENDING:
                # 检查依赖是否都已完成
                deps_met = True
                for dep_id in task.dependencies:
                    dep_task = workflow.tasks.get(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        # 如果依赖被跳过了，也算满足（跳过条件）
                        if dep_task and dep_task.status == TaskStatus.SKIPPED:
                            continue
                        deps_met = False
                        break
                
                if deps_met:
                    task.status = TaskStatus.READY
    
    def get_workflow(self, workflow_id: str) -> Optional[WorkflowInstance]:
        """获取工作流实例"""
        return self.workflows.get(workflow_id)
    
    def list_workflows(self, status_filter: WorkflowStatus = None,
                      limit: int = 50, offset: int = 0) -> List[WorkflowInstance]:
        """列出工作流"""
        workflows = list(self.workflows.values())
        
        if status_filter:
            workflows = [w for w in workflows if w.status == status_filter]
        
        # 按创建时间倒序
        workflows.sort(key=lambda w: w.created_at, reverse=True)
        
        return workflows[offset:offset+limit]
    
    def pause_workflow(self, workflow_id: str) -> bool:
        """暂停工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.RUNNING:
            return False
        
        workflow.status = WorkflowStatus.PAUSED
        self._save_state()
        return True
    
    def resume_workflow(self, workflow_id: str) -> bool:
        """恢复工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow or workflow.status != WorkflowStatus.PAUSED:
            return False
        
        workflow.status = WorkflowStatus.RUNNING
        self._save_state()
        self.dispatch()  # 恢复后立即调度
        return True
    
    def cancel_workflow(self, workflow_id: str) -> bool:
        """取消工作流"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return False
        
        if workflow.status in [WorkflowStatus.COMPLETED, 
                               WorkflowStatus.FAILED,
                               WorkflowStatus.CANCELLED]:
            return False
        
        workflow.status = WorkflowStatus.CANCELLED
        workflow.completed_at = datetime.now().isoformat()
        
        # 取消所有运行中的任务
        for task in workflow.tasks.values():
            if task.status in [TaskStatus.RUNNING, TaskStatus.ASSIGNED, 
                               TaskStatus.READY, TaskStatus.PENDING]:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                
                # 释放Agent
                if task.assigned_agent:
                    agent = self.agents.get(task.assigned_agent)
                    if agent:
                        agent.status = "idle"
                        agent.current_task = ""
                        agent.current_workflow = ""
        
        self._save_state()
        return True
    
    # ========== 任务调度 ==========
    
    def find_suitable_agent(self, task: WorkflowTask,
                           strategy: SchedulingStrategy = SchedulingStrategy.BEST_MATCH
                           ) -> Optional[AgentInfo]:
        """寻找适合执行任务的Agent
        
        Args:
            task: 任务
            strategy: 调度策略
        
        Returns:
            合适的Agent
        """
        # 获取空闲Agent
        idle_agents = [a for a in self.agents.values() if a.status == "idle"]
        
        if not idle_agents:
            return None
        
        if strategy == SchedulingStrategy.FIRST_AVAILABLE:
            return idle_agents[0]
        
        elif strategy == SchedulingStrategy.ROUND_ROBIN:
            if self._round_robin_index >= len(idle_agents):
                self._round_robin_index = 0
            agent = idle_agents[self._round_robin_index]
            self._round_robin_index += 1
            return agent
        
        elif strategy == SchedulingStrategy.LOAD_BALANCED:
            # 选择负载最低的
            idle_agents.sort(key=lambda a: a.load_score)
            return idle_agents[0]
        
        elif strategy == SchedulingStrategy.BEST_MATCH:
            # 最佳匹配算法
            scored_agents = []
            
            for agent in idle_agents:
                score = 0
                
                # 角色匹配
                if task.requirements.get("role") and agent.role == task.requirements["role"]:
                    score += 30
                
                # 能力匹配
                required_caps = set(task.requirements.get("capabilities", []))
                agent_caps = set(agent.capabilities)
                if required_caps:
                    match_ratio = len(required_caps & agent_caps) / len(required_caps)
                    score += match_ratio * 40
                
                # 标签匹配
                required_tags = set(task.tags)
                agent_tags = set(agent.tags)
                if required_tags and agent_tags:
                    tag_match = len(required_tags & agent_tags) / len(required_tags)
                    score += tag_match * 20
                
                # 历史成功率
                total = agent.tasks_completed + agent.tasks_failed
                if total > 0:
                    success_rate = agent.tasks_completed / total
                    score += success_rate * 10
                
                # 负载减分
                score -= agent.load_score * 5
                
                scored_agents.append((score, agent))
            
            scored_agents.sort(key=lambda x: x[0], reverse=True)
            
            if scored_agents:
                return scored_agents[0][1]
            return None
        
        elif strategy == SchedulingStrategy.PRIORITY_FIRST:
            # 优先级优先：高优先级任务分配给最好的Agent
            return self.find_suitable_agent(task, SchedulingStrategy.BEST_MATCH)
        
        # 默认返回第一个
        return idle_agents[0]
    
    def dispatch(self) -> List[Tuple[WorkflowInstance, WorkflowTask, AgentInfo]]:
        """调度所有可执行的任务
        
        Returns:
            本次调度的 (工作流, 任务, Agent) 列表
        """
        if not self.scheduling_enabled:
            return []
        
        dispatched = []
        
        # 遍历所有运行中的工作流
        for workflow in self.workflows.values():
            if workflow.status != WorkflowStatus.RUNNING:
                continue
            
            # 更新就绪任务
            self._update_ready_tasks(workflow)
            
            # 获取所有就绪任务
            ready_tasks = [
                t for t in workflow.tasks.values()
                if t.status == TaskStatus.READY
            ]
            
            # 按优先级排序
            ready_tasks.sort(key=lambda t: (t.priority, t.created_at))
            
            for task in ready_tasks:
                # 选择调度策略
                strategy = SchedulingStrategy(
                    workflow.variables.get("scheduling_strategy", "best_match")
                )
                
                # 寻找合适的Agent
                agent = self.find_suitable_agent(task, strategy)
                if agent:
                    self._assign_task(workflow, task, agent)
                    dispatched.append((workflow, task, agent))
        
        self.last_dispatch_time = datetime.now().isoformat()
        
        if dispatched:
            self._save_state()
        
        return dispatched
    
    def _assign_task(self, workflow: WorkflowInstance, task: WorkflowTask,
                    agent: AgentInfo):
        """分配任务给Agent"""
        task.status = TaskStatus.ASSIGNED
        task.assigned_agent = agent.agent_id
        
        agent.status = "busy"
        agent.current_task = task.task_id
        agent.current_workflow = workflow.workflow_id
        agent.load_score += 1.0  # 增加负载
        
        self._emit_event(WorkflowEvent(
            WorkflowEventType.TASK_ASSIGNED,
            {
                "workflow_id": workflow.workflow_id,
                "task_id": task.task_id,
                "agent_id": agent.agent_id
            }
        ))
    
    # ========== 任务执行回调 ==========
    
    def start_task(self, task_id: str) -> bool:
        """标记任务开始执行"""
        # 找到所属的工作流
        for workflow in self.workflows.values():
            if task_id in workflow.tasks:
                task = workflow.tasks[task_id]
                if task.status in [TaskStatus.READY, TaskStatus.ASSIGNED]:
                    task.status = TaskStatus.RUNNING
                    task.started_at = datetime.now().isoformat()
                    
                    self._emit_event(WorkflowEvent(
                        WorkflowEventType.TASK_STARTED,
                        {
                            "workflow_id": workflow.workflow_id,
                            "task_id": task_id
                        }
                    ))
                    
                    self._save_state()
                    return True
                break
        return False
    
    def complete_task(self, task_id: str, result: Any = None) -> bool:
        """标记任务完成
        
        Args:
            task_id: 任务ID
            result: 任务结果
        
        Returns:
            是否成功
        """
        for workflow in self.workflows.values():
            if task_id in workflow.tasks:
                task = workflow.tasks[task_id]
                
                if task.status in [TaskStatus.RUNNING, TaskStatus.WAITING, 
                                   TaskStatus.ASSIGNED]:
                    task.status = TaskStatus.COMPLETED
                    task.result = result
                    task.completed_at = datetime.now().isoformat()
                    
                    # 释放Agent
                    if task.assigned_agent:
                        agent = self.agents.get(task.assigned_agent)
                        if agent:
                            agent.status = "idle"
                            agent.current_task = ""
                            agent.current_workflow = ""
                            agent.tasks_completed += 1
                            agent.load_score = max(0, agent.load_score - 0.5)
                    
                    self._emit_event(WorkflowEvent(
                        WorkflowEventType.TASK_COMPLETED,
                        {
                            "workflow_id": workflow.workflow_id,
                            "task_id": task_id
                        }
                    ))
                    
                    # 检查工作流是否完成
                    self._check_workflow_completion(workflow)
                    
                    # 继续调度
                    self.dispatch()
                    
                    self._save_state()
                    return True
                break
        return False
    
    def fail_task(self, task_id: str, error_message: str = "") -> bool:
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        
        Returns:
            是否成功
        """
        for workflow in self.workflows.values():
            if task_id in workflow.tasks:
                task = workflow.tasks[task_id]
                
                if task.status in [TaskStatus.RUNNING, TaskStatus.ASSIGNED]:
                    task.error_message = error_message
                    task.retry_count += 1
                    
                    # 释放Agent
                    if task.assigned_agent:
                        agent = self.agents.get(task.assigned_agent)
                        if agent:
                            agent.status = "idle"
                            agent.current_task = ""
                            agent.current_workflow = ""
                            agent.tasks_failed += 1
                    
                    # 检查是否可以重试
                    if task.retry_count <= task.max_retries:
                        task.status = TaskStatus.READY
                        task.assigned_agent = ""
                        task.started_at = ""
                    else:
                        task.status = TaskStatus.FAILED
                        task.completed_at = datetime.now().isoformat()
                        
                        # 任务失败事件
                        self._emit_event(WorkflowEvent(
                            WorkflowEventType.TASK_FAILED,
                            {
                                "workflow_id": workflow.workflow_id,
                                "task_id": task_id,
                                "error": error_message
                            }
                        ))
                        
                        # 处理工作流失败策略
                        if workflow.on_failure == "stop":
                            self._fail_workflow(workflow, f"任务 {task.name} 失败: {error_message}")
                        elif workflow.on_failure == "continue":
                            # 跳过失败的任务，继续其他分支
                            self._skip_dependent_tasks(workflow, task)
                    
                    self._save_state()
                    self.dispatch()
                    return True
                break
        return False
    
    def _skip_dependent_tasks(self, workflow: WorkflowInstance, failed_task: WorkflowTask):
        """跳过所有依赖失败任务的任务"""
        for dep_id in failed_task.dependents:
            if dep_id in workflow.tasks:
                dep_task = workflow.tasks[dep_id]
                if dep_task.status in [TaskStatus.PENDING, TaskStatus.READY]:
                    dep_task.status = TaskStatus.SKIPPED
                    dep_task.completed_at = datetime.now().isoformat()
                    self._skip_dependent_tasks(workflow, dep_task)
    
    def _fail_workflow(self, workflow: WorkflowInstance, reason: str):
        """标记工作流失败"""
        workflow.status = WorkflowStatus.FAILED
        workflow.completed_at = datetime.now().isoformat()
        
        # 取消所有未完成的任务
        for task in workflow.tasks.values():
            if task.status in [TaskStatus.RUNNING, TaskStatus.ASSIGNED,
                               TaskStatus.READY, TaskStatus.PENDING, 
                               TaskStatus.WAITING]:
                task.status = TaskStatus.CANCELLED
                task.completed_at = datetime.now().isoformat()
                
                # 释放Agent
                if task.assigned_agent:
                    agent = self.agents.get(task.assigned_agent)
                    if agent:
                        agent.status = "idle"
                        agent.current_task = ""
                        agent.current_workflow = ""
        
        self._emit_event(WorkflowEvent(
            WorkflowEventType.WORKFLOW_FAILED,
            {
                "workflow_id": workflow.workflow_id,
                "reason": reason
            }
        ))
    
    def _check_workflow_completion(self, workflow: WorkflowInstance):
        """检查工作流是否完成"""
        if workflow.status != WorkflowStatus.RUNNING:
            return
        
        all_done = True
        has_failure = False
        
        for task in workflow.tasks.values():
            if task.status in [TaskStatus.PENDING, TaskStatus.READY,
                               TaskStatus.ASSIGNED, TaskStatus.RUNNING,
                               TaskStatus.WAITING]:
                all_done = False
                break
            elif task.status == TaskStatus.FAILED:
                has_failure = True
        
        if all_done:
            if has_failure and workflow.on_failure == "stop":
                # 已经在fail_task中处理了
                pass
            else:
                workflow.status = WorkflowStatus.COMPLETED
                workflow.completed_at = datetime.now().isoformat()
                
                self._emit_event(WorkflowEvent(
                    WorkflowEventType.WORKFLOW_COMPLETED,
                    {
                        "workflow_id": workflow.workflow_id,
                        "name": workflow.name
                    }
                ))
    
    # ========== 统计与监控 ==========
    
    def get_statistics(self) -> Dict:
        """获取统计信息"""
        total_workflows = len(self.workflows)
        running_workflows = sum(
            1 for w in self.workflows.values() if w.status == WorkflowStatus.RUNNING
        )
        completed_workflows = sum(
            1 for w in self.workflows.values() if w.status == WorkflowStatus.COMPLETED
        )
        failed_workflows = sum(
            1 for w in self.workflows.values() if w.status == WorkflowStatus.FAILED
        )
        
        total_agents = len(self.agents)
        idle_agents = sum(1 for a in self.agents.values() if a.status == "idle")
        busy_agents = sum(1 for a in self.agents.values() if a.status == "busy")
        offline_agents = sum(1 for a in self.agents.values() if a.status == "offline")
        
        # 统计任务
        total_tasks = 0
        completed_tasks = 0
        failed_tasks = 0
        running_tasks = 0
        
        for workflow in self.workflows.values():
            for task in workflow.tasks.values():
                total_tasks += 1
                if task.status == TaskStatus.COMPLETED:
                    completed_tasks += 1
                elif task.status == TaskStatus.FAILED:
                    failed_tasks += 1
                elif task.status == TaskStatus.RUNNING:
                    running_tasks += 1
        
        # 计算成功率
        finished = completed_tasks + failed_tasks
        success_rate = (completed_tasks / finished * 100) if finished > 0 else 0
        
        return {
            "workflows": {
                "total": total_workflows,
                "running": running_workflows,
                "completed": completed_workflows,
                "failed": failed_workflows,
            },
            "agents": {
                "total": total_agents,
                "idle": idle_agents,
                "busy": busy_agents,
                "offline": offline_agents,
            },
            "tasks": {
                "total": total_tasks,
                "running": running_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "success_rate": round(success_rate, 2),
            },
            "scheduling": {
                "enabled": self.scheduling_enabled,
                "last_dispatch": self.last_dispatch_time,
            }
        }
    
    def get_workflow_progress(self, workflow_id: str) -> Dict:
        """获取工作流进度"""
        workflow = self.workflows.get(workflow_id)
        if not workflow:
            return {"error": "工作流不存在"}
        
        total = len(workflow.tasks)
        completed = sum(1 for t in workflow.tasks.values() 
                       if t.status == TaskStatus.COMPLETED)
        failed = sum(1 for t in workflow.tasks.values() 
                    if t.status == TaskStatus.FAILED)
        running = sum(1 for t in workflow.tasks.values() 
                     if t.status == TaskStatus.RUNNING)
        
        progress = (completed / total * 100) if total > 0 else 0
        
        # 计算持续时间
        duration = 0
        if workflow.started_at:
            end_time = (workflow.completed_at 
                       if workflow.completed_at 
                       else datetime.now().isoformat())
            try:
                start = datetime.fromisoformat(workflow.started_at)
                end = datetime.fromisoformat(end_time)
                duration = int((end - start).total_seconds())
            except:
                pass
        
        return {
            "workflow_id": workflow_id,
            "name": workflow.name,
            "status": workflow.status,
            "progress_percent": round(progress, 1),
            "total_tasks": total,
            "completed_tasks": completed,
            "failed_tasks": failed,
            "running_tasks": running,
            "pending_tasks": total - completed - failed - running,
            "duration_seconds": duration,
            "started_at": workflow.started_at,
            "completed_at": workflow.completed_at
        }
    
    def get_agent_workload(self, agent_id: str) -> Dict:
        """获取Agent工作负载"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"error": "Agent不存在"}
        
        # 获取该Agent相关的任务
        agent_tasks = []
        for workflow in self.workflows.values():
            for task in workflow.tasks.values():
                if task.assigned_agent == agent_id:
                    agent_tasks.append({
                        "task_id": task.task_id,
                        "workflow_id": workflow.workflow_id,
                        "name": task.name,
                        "status": task.status
                    })
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.agent_name,
            "status": agent.status,
            "load_score": agent.load_score,
            "tasks_completed": agent.tasks_completed,
            "tasks_failed": agent.tasks_failed,
            "current_task": agent.current_task,
            "current_workflow": agent.current_workflow,
            "recent_tasks": agent_tasks[-10:],
            "last_heartbeat": agent.last_heartbeat
        }
    
    # ========== 清理 ==========
    
    def cleanup_completed(self, days: int = 30) -> int:
        """清理指定天数前完成的工作流"""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()
        
        to_remove = []
        for wf_id, workflow in self.workflows.items():
            if (workflow.status in [WorkflowStatus.COMPLETED, 
                                    WorkflowStatus.FAILED,
                                    WorkflowStatus.CANCELLED]
                and workflow.completed_at
                and workflow.completed_at < cutoff):
                to_remove.append(wf_id)
        
        for wf_id in to_remove:
            del self.workflows[wf_id]
        
        if to_remove:
            self._save_state()
        
        return len(to_remove)


# ========== 预置工作流模板 ==========

PRESET_WORKFLOWS = {
    "feature_development": {
        "name": "功能开发工作流",
        "description": "多Agent协作完成新功能开发：需求分析→设计→开发→测试→部署",
        "version": "1.0",
        "tasks": [
            {
                "task_id": "requirements",
                "name": "需求分析",
                "task_type": "analysis",
                "description": "分析需求，输出需求文档",
                "requirements": {"role": "builder", "capabilities": ["需求分析", "文档编写"]},
                "priority": 1,
                "estimated_duration": 1800
            },
            {
                "task_id": "design",
                "name": "架构设计",
                "task_type": "design",
                "description": "技术方案设计与架构设计",
                "dependencies": ["requirements"],
                "requirements": {"role": "builder", "capabilities": ["架构设计", "技术选型"]},
                "priority": 1,
                "estimated_duration": 2400
            },
            {
                "task_id": "development",
                "name": "功能开发",
                "task_type": "development",
                "description": "代码实现与单元测试",
                "dependencies": ["design"],
                "requirements": {"role": "constructor", "capabilities": ["编程开发", "单元测试"]},
                "priority": 2,
                "estimated_duration": 3600
            },
            {
                "task_id": "testing",
                "name": "测试验证",
                "task_type": "testing",
                "description": "功能测试、集成测试、安全测试",
                "dependencies": ["development"],
                "requirements": {"role": "breaker", "capabilities": ["测试", "安全审计"]},
                "priority": 2,
                "estimated_duration": 2400
            },
            {
                "task_id": "deployment",
                "name": "部署上线",
                "task_type": "deployment",
                "description": "部署到生产环境并验证",
                "dependencies": ["testing"],
                "requirements": {"capabilities": ["部署", "运维"]},
                "priority": 2,
                "estimated_duration": 1200
            }
        ],
        "on_failure": "stop",
        "default_timeout": 7200
    },
    
    "code_review": {
        "name": "代码审查工作流",
        "description": "双人代码审查：初审→复审→合并",
        "version": "1.0",
        "tasks": [
            {
                "task_id": "initial_review",
                "name": "初审",
                "task_type": "review",
                "description": "第一轮代码审查，检查代码质量、规范、潜在bug",
                "requirements": {"capabilities": ["代码审查", "质量保证"]},
                "priority": 2,
                "estimated_duration": 1800
            },
            {
                "task_id": "rework",
                "name": "修改优化",
                "task_type": "development",
                "description": "根据审查意见修改代码",
                "dependencies": ["initial_review"],
                "requirements": {"capabilities": ["编程开发"]},
                "priority": 2,
                "estimated_duration": 2400
            },
            {
                "task_id": "final_review",
                "name": "复审",
                "task_type": "review",
                "description": "第二轮代码审查，确认问题已修复",
                "dependencies": ["rework"],
                "requirements": {"capabilities": ["代码审查"]},
                "priority": 2,
                "estimated_duration": 900
            },
            {
                "task_id": "merge",
                "name": "合并",
                "task_type": "integration",
                "description": "将通过审查的代码合并到主分支",
                "dependencies": ["final_review"],
                "requirements": {"capabilities": ["版本控制", "集成"]},
                "priority": 1,
                "estimated_duration": 600
            }
        ],
        "on_failure": "stop",
        "default_timeout": 3600
    },
    
    "incident_response": {
        "name": "应急响应工作流",
        "description": "故障应急响应：检测→定位→修复→验证→复盘",
        "version": "1.0",
        "tasks": [
            {
                "task_id": "detection",
                "name": "故障检测",
                "task_type": "monitoring",
                "description": "检测和确认故障现象",
                "requirements": {"role": "sentinel", "capabilities": ["监控", "告警"]},
                "priority": 0,
                "estimated_duration": 300
            },
            {
                "task_id": "diagnosis",
                "name": "故障定位",
                "task_type": "analysis",
                "description": "分析故障根因",
                "dependencies": ["detection"],
                "requirements": {"capabilities": ["问题诊断", "日志分析"]},
                "priority": 0,
                "estimated_duration": 900
            },
            {
                "task_id": "fix",
                "name": "修复实施",
                "task_type": "remediation",
                "description": "实施修复方案",
                "dependencies": ["diagnosis"],
                "requirements": {"capabilities": ["故障修复", "运维"]},
                "priority": 0,
                "estimated_duration": 1200
            },
            {
                "task_id": "verification",
                "name": "验证确认",
                "task_type": "testing",
                "description": "验证故障是否已修复",
                "dependencies": ["fix"],
                "requirements": {"capabilities": ["测试验证"]},
                "priority": 0,
                "estimated_duration": 600
            },
            {
                "task_id": "retrospective",
                "name": "复盘总结",
                "task_type": "documentation",
                "description": "故障复盘与改进措施",
                "dependencies": ["verification"],
                "requirements": {"capabilities": ["文档编写", "总结分析"]},
                "priority": 2,
                "estimated_duration": 1800
            }
        ],
        "on_failure": "stop",
        "default_timeout": 3600
    }
}


def create_orchestrator_with_presets(data_dir: str = None) -> WorkflowOrchestrator:
    """创建编排器并加载预置工作流
    
    Args:
        data_dir: 数据目录
    
    Returns:
        编排器实例
    """
    orchestrator = WorkflowOrchestrator(data_dir)
    
    # 注册预置工作流
    for wf_type, wf_data in PRESET_WORKFLOWS.items():
        wf_def = WorkflowDefinition(
            workflow_type=wf_type,
            name=wf_data["name"],
            description=wf_data.get("description", ""),
            version=wf_data.get("version", "1.0"),
            tasks=wf_data.get("tasks", []),
            variables=wf_data.get("variables", {}),
            default_timeout=wf_data.get("default_timeout", 3600),
            on_failure=wf_data.get("on_failure", "stop")
        )
        orchestrator.register_workflow_definition(wf_def)
    
    return orchestrator
