#!/usr/bin/env python3
"""
编排调度器模块
提供多Agent的编排调度、任务分发和协同工作功能。
支持定时任务、依赖调度、负载均衡等。
"""

import os
import json
import time
import random
import hashlib
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum


class TaskStatus(str, Enum):
    """任务状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentRole(str, Enum):
    """Agent角色枚举"""
    SENTINEL = "sentinel"       # 哨兵 - 监控巡检
    BUILDER = "builder"         # 建造者 - 架构决策
    CONSTRUCTOR = "constructor" # 施工者 - 功能开发
    BREAKER = "breaker"         # 破坏者 - 安全测试
    DEFAULT = "default"         # 通用


@dataclass
class Task:
    """任务对象"""
    task_id: str
    task_type: str
    title: str
    description: str = ""
    priority: int = 2  # 0=紧急, 1=高, 2=普通, 3=低
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: str = ""
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    result: str = ""
    error_message: str = ""
    retry_count: int = 0
    max_retries: int = 3
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    estimated_duration: int = 300  # 预估时长（秒）


@dataclass
class AgentInfo:
    """Agent信息"""
    agent_id: str
    agent_name: str
    role: AgentRole = AgentRole.DEFAULT
    status: str = "idle"  # idle, busy, offline
    current_task: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: str = ""
    capabilities: List[str] = field(default_factory=list)
    cpu_quota: str = "1.0"
    memory_quota: str = "1536M"


class Orchestrator:
    """编排调度器
    
    负责管理多个Agent的任务调度、资源分配和协同工作。
    """
    
    def __init__(self, data_dir: str = None):
        """初始化编排调度器
        
        Args:
            data_dir: 数据目录
        """
        if data_dir:
            self.data_dir = Path(data_dir).resolve()
        else:
            self.data_dir = Path(__file__).parent.parent / "agent-awake-data"
        
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_history: List[Task] = []
        
        # 加载持久化数据
        self._load_state()
    
    def _load_state(self):
        """加载状态"""
        agents_file = self.data_dir / "agents.json"
        tasks_file = self.data_dir / "tasks.json"
        
        if agents_file.exists():
            try:
                with open(agents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.agents = {k: AgentInfo(**v) for k, v in data.items()}
            except (json.JSONDecodeError, TypeError):
                pass
        
        if tasks_file.exists():
            try:
                with open(tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.tasks = {k: Task(**v) for k, v in data.items()}
            except (json.JSONDecodeError, TypeError):
                pass
    
    def _save_state(self):
        """保存状态"""
        agents_file = self.data_dir / "agents.json"
        tasks_file = self.data_dir / "tasks.json"
        
        with open(agents_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.__dict__ for k, v in self.agents.items()}, f, indent=2, ensure_ascii=False)
        
        with open(tasks_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.__dict__ for k, v in self.tasks.items()}, f, indent=2, ensure_ascii=False)
    
    def register_agent(self, agent_id: str, agent_name: str = "",
                      role: AgentRole = AgentRole.DEFAULT,
                      capabilities: List[str] = None,
                      cpu_quota: str = "1.0",
                      memory_quota: str = "1536M") -> AgentInfo:
        """注册一个Agent
        
        Args:
            agent_id: Agent唯一标识符
            agent_name: Agent名称
            role: Agent角色
            capabilities: 能力列表
            cpu_quota: CPU配额
            memory_quota: 内存配额
        
        Returns:
            Agent信息对象
        """
        agent = AgentInfo(
            agent_id=agent_id,
            agent_name=agent_name or agent_id,
            role=role,
            capabilities=capabilities or [],
            cpu_quota=cpu_quota,
            memory_quota=memory_quota,
            last_heartbeat=datetime.utcnow().isoformat()
        )
        
        self.agents[agent_id] = agent
        self._save_state()
        return agent
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销Agent
        
        Args:
            agent_id: Agent ID
        
        Returns:
            是否成功
        """
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save_state()
            return True
        return False
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取Agent信息"""
        return self.agents.get(agent_id)
    
    def list_agents(self, role_filter: AgentRole = None,
                   status_filter: str = None) -> List[AgentInfo]:
        """列出所有Agent
        
        Args:
            role_filter: 按角色过滤
            status_filter: 按状态过滤
        
        Returns:
            Agent信息列表
        """
        agents = list(self.agents.values())
        if role_filter:
            agents = [a for a in agents if a.role == role_filter]
        if status_filter:
            agents = [a for a in agents if a.status == status_filter]
        return agents
    
    def update_agent_status(self, agent_id: str, status: str) -> Optional[AgentInfo]:
        """更新Agent状态"""
        if agent_id not in self.agents:
            return None
        
        self.agents[agent_id].status = status
        self.agents[agent_id].last_heartbeat = datetime.utcnow().isoformat()
        self._save_state()
        return self.agents[agent_id]
    
    def heartbeat(self, agent_id: str) -> bool:
        """Agent心跳"""
        if agent_id in self.agents:
            self.agents[agent_id].last_heartbeat = datetime.utcnow().isoformat()
            self._save_state()
            return True
        return False
    
    def create_task(self, task_type: str, title: str, description: str = "",
                   priority: int = 2, dependencies: List[str] = None,
                   tags: List[str] = None, max_retries: int = 3,
                   estimated_duration: int = 300) -> Task:
        """创建任务
        
        Args:
            task_type: 任务类型
            title: 任务标题
            description: 任务描述
            priority: 优先级 (0=紧急, 1=高, 2=普通, 3=低)
            dependencies: 依赖的任务ID列表
            tags: 标签列表
            max_retries: 最大重试次数
            estimated_duration: 预估时长（秒）
        
        Returns:
            任务对象
        """
        # 生成任务ID
        timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
        random_str = hashlib.md5(str(random.random()).encode()).hexdigest()[:8]
        task_id = f"task_{timestamp}_{random_str}"
        
        task = Task(
            task_id=task_id,
            task_type=task_type,
            title=title,
            description=description,
            priority=priority,
            dependencies=dependencies or [],
            tags=tags or [],
            max_retries=max_retries,
            estimated_duration=estimated_duration,
            created_at=datetime.utcnow().isoformat()
        )
        
        self.tasks[task_id] = task
        self._save_state()
        return task
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务信息"""
        return self.tasks.get(task_id)
    
    def list_tasks(self, status_filter: TaskStatus = None,
                   agent_filter: str = None,
                   priority_filter: int = None) -> List[Task]:
        """列出任务
        
        Args:
            status_filter: 按状态过滤
            agent_filter: 按分配的Agent过滤
            priority_filter: 按优先级过滤
        
        Returns:
            任务列表
        """
        tasks = list(self.tasks.values())
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        if agent_filter:
            tasks = [t for t in tasks if t.assigned_agent == agent_filter]
        if priority_filter is not None:
            tasks = [t for t in tasks if t.priority == priority_filter]
        
        # 按优先级和创建时间排序
        tasks.sort(key=lambda t: (t.priority, t.created_at))
        return tasks
    
    def _get_task_anywhere(self, task_id: str) -> Optional[Task]:
        """从活跃任务或历史中查找任务"""
        if task_id in self.tasks:
            return self.tasks[task_id]
        for task in self.task_history:
            if task.task_id == task_id:
                return task
        return None
    
    def get_pending_tasks(self) -> List[Task]:
        """获取可分配的待处理任务
        
        检查依赖是否都已完成
        """
        pending = [t for t in self.tasks.values() 
                  if t.status == TaskStatus.PENDING]
        
        # 过滤掉依赖未完成的任务
        ready = []
        for task in pending:
            deps_met = True
            for dep_id in task.dependencies:
                dep_task = self._get_task_anywhere(dep_id)
                if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                    deps_met = False
                    break
            if deps_met:
                ready.append(task)
        
        # 按优先级排序
        ready.sort(key=lambda t: (t.priority, t.created_at))
        return ready
    
    def assign_task(self, task_id: str, agent_id: str) -> Optional[Task]:
        """分配任务给Agent
        
        Args:
            task_id: 任务ID
            agent_id: Agent ID
        
        Returns:
            更新后的任务对象
        """
        if task_id not in self.tasks or agent_id not in self.agents:
            return None
        
        task = self.tasks[task_id]
        task.assigned_agent = agent_id
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.utcnow().isoformat()
        
        # 更新Agent状态
        self.agents[agent_id].status = "busy"
        self.agents[agent_id].current_task = task_id
        
        self._save_state()
        return task
    
    def complete_task(self, task_id: str, result: str = "") -> Optional[Task]:
        """完成任务
        
        Args:
            task_id: 任务ID
            result: 任务结果
        
        Returns:
            更新后的任务对象
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task.status = TaskStatus.COMPLETED
        task.result = result
        task.completed_at = datetime.utcnow().isoformat()
        
        # 更新Agent状态
        if task.assigned_agent and task.assigned_agent in self.agents:
            agent = self.agents[task.assigned_agent]
            agent.status = "idle"
            agent.current_task = ""
            agent.tasks_completed += 1
        
        # 从活跃任务移到历史
        del self.tasks[task_id]
        self.task_history.append(task)
        self._save_state()
        return task
    
    def fail_task(self, task_id: str, error_message: str = "") -> Optional[Task]:
        """标记任务失败
        
        Args:
            task_id: 任务ID
            error_message: 错误信息
        
        Returns:
            更新后的任务对象
        """
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task.error_message = error_message
        task.retry_count += 1
        
        # 更新Agent状态
        if task.assigned_agent and task.assigned_agent in self.agents:
            agent = self.agents[task.assigned_agent]
            agent.status = "idle"
            agent.current_task = ""
            agent.tasks_failed += 1
        
        # 检查是否需要重试
        if task.retry_count <= task.max_retries:
            task.status = TaskStatus.PENDING
            task.assigned_agent = ""
            task.started_at = ""
        else:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.utcnow().isoformat()
            # 从活跃任务移到历史
            del self.tasks[task_id]
            self.task_history.append(task)
        
        self._save_state()
        return task
    
    def cancel_task(self, task_id: str) -> Optional[Task]:
        """取消任务"""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        task.status = TaskStatus.CANCELLED
        task.completed_at = datetime.utcnow().isoformat()
        
        # 释放Agent
        if task.assigned_agent and task.assigned_agent in self.agents:
            agent = self.agents[task.assigned_agent]
            agent.status = "idle"
            agent.current_task = ""
        
        # 从活跃任务移到历史
        del self.tasks[task_id]
        self.task_history.append(task)
        self._save_state()
        return task
    
    def find_suitable_agent(self, task: Task) -> Optional[AgentInfo]:
        """寻找适合执行任务的Agent
        
        Args:
            task: 任务对象
        
        Returns:
            适合的Agent，找不到返回None
        """
        # 获取空闲的Agent
        idle_agents = [a for a in self.agents.values() if a.status == "idle"]
        
        if not idle_agents:
            return None
        
        # 根据任务类型和标签匹配合适的Agent
        # 这里使用简单的匹配逻辑，可根据需要扩展
        scored_agents = []
        
        for agent in idle_agents:
            score = 0
            
            # 角色匹配加分
            role_task_map = {
                "monitoring": AgentRole.SENTINEL,
                "security": AgentRole.BREAKER,
                "development": AgentRole.CONSTRUCTOR,
                "architecture": AgentRole.BUILDER,
            }
            
            if task.task_type in role_task_map and agent.role == role_task_map[task.task_type]:
                score += 10
            
            # 能力匹配加分
            for tag in task.tags:
                if tag in agent.capabilities:
                    score += 5
            
            # 历史成功率加分
            total_tasks = agent.tasks_completed + agent.tasks_failed
            if total_tasks > 0:
                success_rate = agent.tasks_completed / total_tasks
                score += success_rate * 3
            
            scored_agents.append((score, agent))
        
        # 按分数排序，返回最高分的
        scored_agents.sort(key=lambda x: x[0], reverse=True)
        
        if scored_agents and scored_agents[0][0] > 0:
            return scored_agents[0][1]
        
        # 如果没有匹配的，返回第一个空闲的
        return idle_agents[0] if idle_agents else None
    
    def dispatch_task(self) -> Optional[Tuple[Task, AgentInfo]]:
        """调度一个任务给合适的Agent
        
        Returns:
            (任务, Agent) 元组，没有可调度的返回None
        """
        pending = self.get_pending_tasks()
        if not pending:
            return None
        
        for task in pending:
            agent = self.find_suitable_agent(task)
            if agent:
                self.assign_task(task.task_id, agent.agent_id)
                return task, agent
        
        return None
    
    def get_statistics(self) -> Dict:
        """获取统计信息
        
        Returns:
            统计信息字典
        """
        total_agents = len(self.agents)
        idle_agents = len([a for a in self.agents.values() if a.status == "idle"])
        busy_agents = len([a for a in self.agents.values() if a.status == "busy"])
        
        # 活跃任务（pending/running）在self.tasks中
        pending_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.PENDING])
        running_tasks = len([t for t in self.tasks.values() if t.status == TaskStatus.RUNNING])
        
        # 已结束任务（completed/failed/cancelled）在task_history中
        completed_tasks = len([t for t in self.task_history if t.status == TaskStatus.COMPLETED])
        failed_tasks = len([t for t in self.task_history if t.status == TaskStatus.FAILED])
        cancelled_tasks = len([t for t in self.task_history if t.status == TaskStatus.CANCELLED])
        
        total_tasks = len(self.tasks) + len(self.task_history)
        
        # 计算成功率
        finished = completed_tasks + failed_tasks
        success_rate = (completed_tasks / finished * 100) if finished > 0 else 0
        
        return {
            "agents": {
                "total": total_agents,
                "idle": idle_agents,
                "busy": busy_agents,
            },
            "tasks": {
                "total": total_tasks,
                "pending": pending_tasks,
                "running": running_tasks,
                "completed": completed_tasks,
                "failed": failed_tasks,
                "cancelled": cancelled_tasks,
                "success_rate": round(success_rate, 2),
            }
        }
    
    def cleanup_completed(self, days: int = 30) -> int:
        """清理指定天数前完成的任务
        
        Args:
            days: 天数阈值
        
        Returns:
            清理的任务数量
        """
        # 简单实现：从内存tasks中移除已完成/失败/取消的任务
        completed_ids = [
            k for k, v in self.tasks.items()
            if v.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]
        ]
        
        for task_id in completed_ids:
            del self.tasks[task_id]
        
        if completed_ids:
            self._save_state()
        
        return len(completed_ids)
