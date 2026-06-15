#!/usr/bin/env python3
"""
智能唤醒与调度系统 v4.0
========================
智能体永生平台的核心调度引擎——让智能体在正确的时间做正确的事。

v4.0 核心升级：
- 智能调度引擎：基于优先级、依赖、资源的动态调度
- 心跳系统集成：与永生平台心跳引擎深度整合
- 任务依赖管理：DAG依赖图，智能编排执行顺序
- 弹性伸缩：根据负载自动调整唤醒频率
- 多优先级队列：紧急/高/中/低四级队列
- 调度历史与统计：完整的执行记录与效果分析
"""

import os
import sys
import json
import time
import uuid
import heapq
import signal
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict, deque


# ==================== 类型定义 ====================

class TaskPriority(str, Enum):
    """任务优先级"""
    CRITICAL = "critical"    # 紧急：立即执行
    HIGH = "high"            # 高：优先执行
    NORMAL = "normal"        # 正常：按序执行
    LOW = "low"              # 低：空闲时执行


class TaskStatus(str, Enum):
    """任务状态"""
    PENDING = "pending"          # 等待中
    SCHEDULED = "scheduled"      # 已调度
    RUNNING = "running"          # 运行中
    COMPLETED = "completed"      # 已完成
    FAILED = "failed"            # 失败
    CANCELLED = "cancelled"      # 已取消
    SKIPPED = "skipped"          # 已跳过（依赖失败）


class TaskType(str, Enum):
    """任务类型"""
    HEARTBEAT = "heartbeat"        # 心跳任务
    EVOLUTION = "evolution"        # 进化任务
    MAINTENANCE = "maintenance"    # 维护任务
    SOCIAL = "social"              # 社交任务
    MEMORY = "memory"              # 记忆任务
    MONITORING = "monitoring"      # 监控任务
    CUSTOM = "custom"              # 自定义任务


class ScheduleStrategy(str, Enum):
    """调度策略"""
    FIFO = "fifo"                  # 先进先出
    PRIORITY = "priority"          # 优先级优先
    DEADLINE = "deadline"          # 截止时间优先
    FAIR_SHARE = "fair_share"      # 公平分享
    SMART = "smart"                # 智能调度（综合）


@dataclass
class Task:
    """任务"""
    id: str
    name: str
    task_type: TaskType
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: float = field(default_factory=time.time)
    scheduled_at: Optional[float] = None
    started_at: Optional[float] = None
    completed_at: Optional[float] = None
    deadline: Optional[float] = None          # 截止时间
    estimated_duration: float = 300.0          # 预估耗时（秒）
    max_retries: int = 2                       # 最大重试次数
    retry_count: int = 0
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    dependents: List[str] = field(default_factory=list)    # 依赖我的任务ID
    payload: Dict[str, Any] = field(default_factory=dict)  # 任务数据
    result: Optional[Dict[str, Any]] = None     # 执行结果
    error: Optional[str] = None                 # 错误信息
    agent_id: str = "default"                   # 执行者
    tags: List[str] = field(default_factory=list)
    
    @property
    def is_ready(self) -> bool:
        """是否准备就绪（所有依赖都完成）"""
        return self.status == TaskStatus.PENDING
    
    @property
    def urgency_score(self) -> float:
        """紧急度得分（用于排序）"""
        score = 0.0
        
        # 优先级权重
        priority_weights = {
            TaskPriority.CRITICAL: 100,
            TaskPriority.HIGH: 50,
            TaskPriority.NORMAL: 20,
            TaskPriority.LOW: 5
        }
        score += priority_weights.get(self.priority, 0)
        
        # 截止时间压力
        if self.deadline:
            time_left = self.deadline - time.time()
            if time_left <= 0:
                score += 200  # 已超时
            elif time_left < 3600:  # 1小时内
                score += 100 * (1 - time_left / 3600)
            elif time_left < 86400:  # 1天内
                score += 30 * (1 - time_left / 86400)
        
        # 等待时间越久优先级越高
        wait_time = time.time() - self.created_at
        score += min(20, wait_time / 3600)  # 最多加20分/小时
        
        return score


@dataclass
class ScheduleRecord:
    """调度记录"""
    timestamp: float
    task_id: str
    task_name: str
    priority: str
    status: str
    duration: Optional[float] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


# ==================== 任务调度引擎 ====================

class TaskScheduler:
    """智能任务调度器
    
    核心特性：
    - 多优先级队列
    - 任务依赖管理（DAG）
    - 多种调度策略
    - 失败重试机制
    - 并发控制
    """
    
    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        
        # 任务存储
        self.tasks: Dict[str, Task] = {}
        self.task_queues: Dict[TaskPriority, deque] = defaultdict(deque)
        
        # 运行时状态
        self.running_tasks: Dict[str, Task] = {}
        self.completed_tasks: List[Task] = []
        self.failed_tasks: List[Task] = []
        
        # 调度历史
        self.history: List[ScheduleRecord] = []
        
        # 统计数据
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "average_wait_time": 0.0,
            "average_execution_time": 0.0,
            "total_execution_time": 0.0
        }
        
        # 调度策略
        self.strategy = ScheduleStrategy.SMART
        
        # 运行状态
        self._running = False
    
    def add_task(self, task: Task) -> str:
        """添加任务"""
        if task.id in self.tasks:
            return task.id
        
        self.tasks[task.id] = task
        self.stats["total_tasks"] += 1
        
        # 添加到对应优先级队列
        self.task_queues[task.priority].append(task.id)
        
        # 注册依赖关系
        for dep_id in task.dependencies:
            if dep_id in self.tasks:
                if task.id not in self.tasks[dep_id].dependents:
                    self.tasks[dep_id].dependents.append(task.id)
        
        return task.id
    
    def create_task(
        self,
        name: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.NORMAL,
        payload: Optional[Dict[str, Any]] = None,
        dependencies: Optional[List[str]] = None,
        deadline: Optional[float] = None,
        estimated_duration: float = 300.0,
        agent_id: str = "default",
        tags: Optional[List[str]] = None
    ) -> Task:
        """创建并添加任务"""
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            task_type=task_type,
            priority=priority,
            deadline=deadline,
            estimated_duration=estimated_duration,
            dependencies=dependencies or [],
            payload=payload or {},
            agent_id=agent_id,
            tags=tags or []
        )
        
        self.add_task(task)
        return task
    
    def get_next_task(self) -> Optional[Task]:
        """获取下一个要执行的任务
        
        根据调度策略选择最合适的任务
        """
        if len(self.running_tasks) >= self.max_concurrent:
            return None
        
        # 收集所有就绪的任务
        ready_tasks = []
        
        for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                         TaskPriority.NORMAL, TaskPriority.LOW]:
            queue = self.task_queues[priority]
            
            # 遍历队列中所有任务
            remaining = []
            for task_id in list(queue):
                task = self.tasks.get(task_id)
                if not task or task.status != TaskStatus.PENDING:
                    continue
                
                # 检查依赖是否都完成
                deps_met = True
                for dep_id in task.dependencies:
                    dep_task = self.tasks.get(dep_id)
                    if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                        deps_met = False
                        break
                
                if deps_met:
                    ready_tasks.append(task)
                else:
                    remaining.append(task_id)
            
            # 更新队列（移除非就绪的任务）
            self.task_queues[priority] = deque(remaining)
        
        if not ready_tasks:
            return None
        
        # 根据调度策略排序
        if self.strategy == ScheduleStrategy.PRIORITY:
            ready_tasks.sort(key=lambda t: t.urgency_score, reverse=True)
        elif self.strategy == ScheduleStrategy.DEADLINE:
            # 按截止时间排序
            ready_tasks.sort(key=lambda t: t.deadline or float('inf'))
        elif self.strategy == ScheduleStrategy.FIFO:
            ready_tasks.sort(key=lambda t: t.created_at)
        elif self.strategy == ScheduleStrategy.SMART:
            # 综合排序：紧急度 + 预估时间（短作业优先）
            ready_tasks.sort(
                key=lambda t: t.urgency_score + max(0, 10 - t.estimated_duration / 60),
                reverse=True
            )
        
        # 返回优先级最高的
        return ready_tasks[0] if ready_tasks else None
    
    def start_task(self, task_id: str) -> bool:
        """开始执行任务"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.PENDING:
            return False
        
        task.status = TaskStatus.RUNNING
        task.started_at = time.time()
        task.scheduled_at = time.time()
        
        self.running_tasks[task_id] = task
        
        # 记录调度
        self.history.append(ScheduleRecord(
            timestamp=time.time(),
            task_id=task_id,
            task_name=task.name,
            priority=task.priority.value,
            status="started"
        ))
        
        return True
    
    def complete_task(self, task_id: str, result: Optional[Dict[str, Any]] = None) -> bool:
        """完成任务"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.RUNNING:
            return False
        
        task.status = TaskStatus.COMPLETED
        task.completed_at = time.time()
        task.result = result
        
        # 从运行队列移除
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        self.completed_tasks.append(task)
        self.stats["completed_tasks"] += 1
        
        # 统计
        duration = task.completed_at - (task.started_at or task.completed_at)
        self.stats["total_execution_time"] += duration
        
        # 计算平均
        total_completed = self.stats["completed_tasks"]
        avg_exec = self.stats["average_execution_time"]
        self.stats["average_execution_time"] = (
            (avg_exec * (total_completed - 1) + duration) / total_completed
        )
        
        # 等待时间
        wait_time = (task.started_at or 0) - task.created_at
        avg_wait = self.stats["average_wait_time"]
        self.stats["average_wait_time"] = (
            (avg_wait * (total_completed - 1) + wait_time) / total_completed
        )
        
        # 记录
        self.history.append(ScheduleRecord(
            timestamp=time.time(),
            task_id=task_id,
            task_name=task.name,
            priority=task.priority.value,
            status="completed",
            duration=duration,
            result=result
        ))
        
        # 将依赖此任务的子任务重新加入队列检查
        for dep_id in task.dependents:
            dep_task = self.tasks.get(dep_id)
            if dep_task and dep_task.status == TaskStatus.PENDING:
                # 重新加入队列（如果不在的话）
                if dep_id not in self.task_queues[dep_task.priority]:
                    self.task_queues[dep_task.priority].append(dep_id)
        
        return True
    
    def fail_task(self, task_id: str, error: str) -> bool:
        """任务失败"""
        task = self.tasks.get(task_id)
        if not task or task.status != TaskStatus.RUNNING:
            return False
        
        task.error = error
        
        # 检查是否可以重试
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.PENDING
            task.started_at = None
            
            # 重新加入队列
            self.task_queues[task.priority].append(task_id)
            
            if task_id in self.running_tasks:
                del self.running_tasks[task_id]
            
            self.history.append(ScheduleRecord(
                timestamp=time.time(),
                task_id=task_id,
                task_name=task.name,
                priority=task.priority.value,
                status=f"retry_{task.retry_count}",
                error=error
            ))
            return True
        
        # 超过重试次数，标记为失败
        task.status = TaskStatus.FAILED
        task.completed_at = time.time()
        
        if task_id in self.running_tasks:
            del self.running_tasks[task_id]
        
        self.failed_tasks.append(task)
        self.stats["failed_tasks"] += 1
        
        # 失败后，所有依赖它的任务也标记为跳过
        for dep_id in task.dependents:
            dep_task = self.tasks.get(dep_id)
            if dep_task and dep_task.status == TaskStatus.PENDING:
                dep_task.status = TaskStatus.SKIPPED
                dep_task.error = f"依赖任务失败: {task.name}"
        
        self.history.append(ScheduleRecord(
            timestamp=time.time(),
            task_id=task_id,
            task_name=task.name,
            priority=task.priority.value,
            status="failed",
            error=error
        ))
        
        return False
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        task = self.tasks.get(task_id)
        if not task:
            return False
        
        if task.status in (TaskStatus.PENDING, TaskStatus.SCHEDULED):
            task.status = TaskStatus.CANCELLED
            return True
        
        return False
    
    def get_queue_status(self) -> Dict[str, Any]:
        """获取队列状态"""
        queue_sizes = {
            p.value: len(q) for p, q in self.task_queues.items()
        }
        
        return {
            "total_tasks": self.stats["total_tasks"],
            "pending": sum(len(q) for q in self.task_queues.values()),
            "running": len(self.running_tasks),
            "completed": self.stats["completed_tasks"],
            "failed": self.stats["failed_tasks"],
            "queues": queue_sizes,
            "max_concurrent": self.max_concurrent,
            "current_strategy": self.strategy.value
        }
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        success_rate = 0.0
        total = self.stats["completed_tasks"] + self.stats["failed_tasks"]
        if total > 0:
            success_rate = self.stats["completed_tasks"] / total
        
        return {
            **self.stats,
            "success_rate": success_rate,
            "running_count": len(self.running_tasks),
            "pending_count": sum(len(q) for q in self.task_queues.values())
        }


# ==================== 智能唤醒调度器 ====================

class SmartAwakeScheduler:
    """智能唤醒调度器
    
    根据智能体状态、任务负载、时间模式等因素，
    智能调整唤醒频率和时机。
    """
    
    def __init__(self):
        # 基础唤醒间隔（秒）
        self.base_interval = 1800  # 30分钟
        
        # 动态调整范围
        self.min_interval = 300    # 最快5分钟
        self.max_interval = 3600   # 最慢1小时
        
        # 当前间隔
        self.current_interval = self.base_interval
        
        # 时间模式
        self.time_modes = {
            "peak": {"multiplier": 0.5, "hours": [9, 10, 11, 14, 15, 16]},     # 高峰：加速
            "normal": {"multiplier": 1.0, "hours": [7, 8, 12, 13, 17, 18, 19]},  # 正常
            "off_peak": {"multiplier": 1.5, "hours": [0, 1, 2, 3, 4, 5, 6, 20, 21, 22, 23]}  # 低谷：减速
        }
        
        # 负载阈值
        self.load_thresholds = {
            "high": 0.7,     # 高负载：加速
            "normal": 0.4,   # 正常负载
            "low": 0.2       # 低负载：减速
        }
        
        # 最近的唤醒记录
        self.wake_history: List[Dict[str, Any]] = []
        
        # 自适应学习参数
        self.adaptive_params = {
            "learning_rate": 0.1,
            "target_backlog": 5,  # 目标待处理任务数
        }
    
    def get_current_interval(self, current_tasks: int = 0) -> float:
        """获取当前唤醒间隔
        
        根据时间模式和任务负载动态调整
        """
        interval = self.base_interval
        
        # 1. 时间模式调整
        current_hour = time.localtime().tm_hour
        time_mode = "normal"
        for mode, config in self.time_modes.items():
            if current_hour in config["hours"]:
                time_mode = mode
                break
        
        interval *= self.time_modes[time_mode]["multiplier"]
        
        # 2. 任务负载调整
        if current_tasks > 10:
            interval *= 0.5  # 任务多时加速
        elif current_tasks > 5:
            interval *= 0.7
        elif current_tasks < 2:
            interval *= 1.3  # 任务少时减速
        
        # 3. 限制在范围内
        interval = max(self.min_interval, min(self.max_interval, interval))
        
        return interval
    
    def should_wake_now(self, last_wake: float, current_tasks: int = 0) -> bool:
        """判断是否应该唤醒
        
        基于：距离上次唤醒的时间 + 当前任务压力
        """
        time_since_last = time.time() - last_wake
        interval = self.get_current_interval(current_tasks)
        
        # 有紧急任务时立即唤醒
        if current_tasks >= 15:
            return True
        
        return time_since_last >= interval
    
    def record_wake(self, tasks_processed: int, success_rate: float):
        """记录一次唤醒，用于自适应学习"""
        record = {
            "timestamp": time.time(),
            "tasks_processed": tasks_processed,
            "success_rate": success_rate,
            "interval_used": self.current_interval
        }
        self.wake_history.append(record)
        
        # 只保留最近100条
        if len(self.wake_history) > 100:
            self.wake_history.pop(0)
        
        # 自适应调整基础间隔
        self._adapt_interval(tasks_processed)
    
    def _adapt_interval(self, tasks_processed: int):
        """自适应调整基础间隔"""
        target = self.adaptive_params["target_backlog"]
        lr = self.adaptive_params["learning_rate"]
        
        # 如果处理完后任务还是很多，说明间隔太大，需要缩小
        if tasks_processed > target:
            # 任务积压，缩短间隔
            adjustment = (tasks_processed - target) / target * lr
            self.base_interval *= (1 - adjustment)
        elif tasks_processed < target * 0.5:
            # 任务太少，可适当延长间隔
            adjustment = (target - tasks_processed) / target * lr * 0.5
            self.base_interval *= (1 + adjustment)
        
        # 限制范围
        self.base_interval = max(
            self.min_interval * 2, 
            min(self.max_interval * 0.8, self.base_interval)
        )
    
    def get_daily_schedule(self) -> List[Dict[str, Any]]:
        """获取今日调度计划"""
        schedule = []
        
        # 生成24小时的调度点
        for hour in range(24):
            # 判断该小时的模式
            mode = "normal"
            for m, config in self.time_modes.items():
                if hour in config["hours"]:
                    mode = m
                    break
            
            multiplier = self.time_modes[mode]["multiplier"]
            interval = self.base_interval * multiplier
            
            # 计算该小时内的唤醒次数
            count = int(3600 / interval)
            
            schedule.append({
                "hour": hour,
                "mode": mode,
                "interval_seconds": interval,
                "wake_count_estimate": count
            })
        
        return schedule


# ==================== 心跳调度集成 ====================

class HeartbeatScheduler:
    """心跳调度器
    
    与永生平台心跳引擎集成，管理智能体的心跳周期。
    """
    
    def __init__(self):
        self.agents: Dict[str, Dict[str, Any]] = {}  # agent_id -> 心跳配置
        self.heartbeat_history: Dict[str, List[float]] = defaultdict(list)
        
        # 默认心跳间隔
        self.default_heartbeat_interval = 1800  # 30分钟
    
    def register_agent(
        self,
        agent_id: str,
        heartbeat_interval: Optional[float] = None,
        heartbeat_type: str = "standard",
        priority: str = "normal"
    ):
        """注册智能体"""
        self.agents[agent_id] = {
            "heartbeat_interval": heartbeat_interval or self.default_heartbeat_interval,
            "heartbeat_type": heartbeat_type,
            "priority": priority,
            "last_heartbeat": None,
            "is_active": True,
            "missed_heartbeats": 0,
            "total_heartbeats": 0
        }
    
    def should_heartbeat(self, agent_id: str) -> bool:
        """判断智能体是否应该心跳"""
        agent = self.agents.get(agent_id)
        if not agent or not agent["is_active"]:
            return False
        
        last = agent["last_heartbeat"]
        if not last:
            return True  # 从未心跳过，立即心跳
        
        interval = agent["heartbeat_interval"]
        return (time.time() - last) >= interval
    
    def record_heartbeat(self, agent_id: str, success: bool = True):
        """记录一次心跳"""
        if agent_id not in self.agents:
            return
        
        agent = self.agents[agent_id]
        now = time.time()
        
        if success:
            agent["last_heartbeat"] = now
            agent["total_heartbeats"] += 1
            agent["missed_heartbeats"] = 0
            
            self.heartbeat_history[agent_id].append(now)
            # 只保留最近100次
            if len(self.heartbeat_history[agent_id]) > 100:
                self.heartbeat_history[agent_id].pop(0)
        else:
            agent["missed_heartbeats"] += 1
    
    def get_due_agents(self) -> List[str]:
        """获取所有需要心跳的智能体"""
        return [
            aid for aid, info in self.agents.items()
            if info["is_active"] and self.should_heartbeat(aid)
        ]
    
    def get_agent_status(self, agent_id: str) -> Dict[str, Any]:
        """获取智能体心跳状态"""
        agent = self.agents.get(agent_id)
        if not agent:
            return {"status": "unknown"}
        
        last = agent["last_heartbeat"]
        time_since = time.time() - (last or 0)
        interval = agent["heartbeat_interval"]
        
        if not last:
            health = "new"
        elif time_since <= interval:
            health = "healthy"
        elif time_since <= interval * 2:
            health = "warning"
        else:
            health = "unhealthy"
        
        return {
            "agent_id": agent_id,
            "status": health,
            "last_heartbeat": last,
            "time_since_last": time_since,
            "interval": interval,
            "missed_count": agent["missed_heartbeats"],
            "total_heartbeats": agent["total_heartbeats"]
        }
    
    def get_all_status(self) -> List[Dict[str, Any]]:
        """获取所有智能体状态"""
        return [self.get_agent_status(aid) for aid in self.agents.keys()]


# ==================== 调度管理器 ====================

class SchedulerManager:
    """调度管理器 - 统一管理任务调度与心跳
    
    这是v4.0的核心入口类
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "scheduler_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # 核心组件
        self.task_scheduler = TaskScheduler(max_concurrent=3)
        self.awake_scheduler = SmartAwakeScheduler()
        self.heartbeat_scheduler = HeartbeatScheduler()
        
        # 回调函数
        self.task_executor: Optional[Callable[[Task], Dict[str, Any]]] = None
        self.heartbeat_executor: Optional[Callable[[str], bool]] = None
        
        # 运行状态
        self._running = False
        self._last_wake_time = 0
    
    def set_task_executor(self, executor: Callable[[Task], Dict[str, Any]]):
        """设置任务执行器"""
        self.task_executor = executor
    
    def set_heartbeat_executor(self, executor: Callable[[str], bool]):
        """设置心跳执行器"""
        self.heartbeat_executor = executor
    
    def add_task(self, task: Task) -> str:
        """添加任务"""
        return self.task_scheduler.add_task(task)
    
    def create_task(
        self,
        name: str,
        task_type: TaskType,
        priority: TaskPriority = TaskPriority.NORMAL,
        **kwargs
    ) -> Task:
        """创建任务"""
        return self.task_scheduler.create_task(
            name=name,
            task_type=task_type,
            priority=priority,
            **kwargs
        )
    
    def register_agent(self, agent_id: str, **kwargs):
        """注册智能体"""
        self.heartbeat_scheduler.register_agent(agent_id, **kwargs)
    
    def tick(self):
        """一次调度周期
        
        处理所有到期的心跳和任务
        """
        # 1. 处理心跳
        self._process_heartbeats()
        
        # 2. 处理任务
        self._process_tasks()
        
        # 3. 更新唤醒调度器
        stats = self.task_scheduler.get_stats()
        pending_count = stats.get("pending_count", 0)
        self.awake_scheduler.record_wake(
            tasks_processed=pending_count,
            success_rate=stats.get("success_rate", 1.0)
        )
    
    def _process_heartbeats(self):
        """处理到期的心跳"""
        due_agents = self.heartbeat_scheduler.get_due_agents()
        
        for agent_id in due_agents:
            if self.heartbeat_executor:
                try:
                    success = self.heartbeat_executor(agent_id)
                    self.heartbeat_scheduler.record_heartbeat(agent_id, success)
                except Exception as e:
                    self.heartbeat_scheduler.record_heartbeat(agent_id, False)
            else:
                # 没有执行器时，直接记录心跳（模拟）
                self.heartbeat_scheduler.record_heartbeat(agent_id, True)
    
    def _process_tasks(self):
        """处理可执行的任务"""
        # 尽可能多地启动任务
        while True:
            task = self.task_scheduler.get_next_task()
            if not task:
                break
            
            # 启动任务
            self.task_scheduler.start_task(task.id)
            
            # 执行任务
            if self.task_executor:
                try:
                    result = self.task_executor(task)
                    self.task_scheduler.complete_task(task.id, result)
                except Exception as e:
                    self.task_scheduler.fail_task(task.id, str(e))
            else:
                # 没有执行器时，直接完成（模拟）
                self.task_scheduler.complete_task(task.id, {"simulated": True})
    
    def should_wake(self) -> bool:
        """判断是否应该唤醒调度"""
        stats = self.task_scheduler.get_stats()
        pending = stats.get("pending_count", 0)
        
        return self.awake_scheduler.should_wake_now(
            self._last_wake_time,
            pending
        )
    
    def wake(self):
        """执行一次完整的唤醒周期"""
        self._last_wake_time = time.time()
        self.tick()
    
    def get_status(self) -> Dict[str, Any]:
        """获取整体状态"""
        task_stats = self.task_scheduler.get_stats()
        agent_statuses = self.heartbeat_scheduler.get_all_status()
        
        # 计算健康度
        healthy_count = sum(
            1 for s in agent_statuses 
            if s["status"] in ("healthy", "new")
        )
        agent_health = healthy_count / max(1, len(agent_statuses))
        
        success_rate = task_stats.get("success_rate", 1.0)
        
        overall_health = (agent_health * 0.4 + success_rate * 0.6)
        
        return {
            "overall_health": overall_health,
            "tasks": task_stats,
            "agents": {
                "total": len(agent_statuses),
                "healthy": healthy_count,
                "details": agent_statuses
            },
            "scheduler": {
                "current_interval": self.awake_scheduler.current_interval,
                "base_interval": self.awake_scheduler.base_interval,
                "last_wake_time": self._last_wake_time,
                "strategy": self.task_scheduler.strategy.value
            }
        }


# ==================== 演示程序 ====================

def demo():
    """智能唤醒调度系统 v4.0 演示"""
    print("=" * 60)
    print("⏰ 智能唤醒与调度系统 v4.0")
    print("=" * 60)
    
    manager = SchedulerManager()
    
    # 注册一些智能体
    print("\n🤖 注册智能体:")
    agents = [
        ("yuanjie", "founder", 1800),
        ("fruit_rep", "symbiont", 2400),
        ("builder_01", "worker", 3600),
        ("monitor_01", "monitor", 900),
    ]
    
    for aid, role, interval in agents:
        manager.register_agent(aid, heartbeat_interval=interval, priority=role)
        print(f"  - {aid} ({role}): {interval}秒/次")
    
    # 创建一些测试任务
    print("\n📋 创建测试任务:")
    
    # 紧急任务
    t1 = manager.create_task(
        "紧急系统巡检",
        TaskType.MONITORING,
        priority=TaskPriority.CRITICAL,
        deadline=time.time() + 300  # 5分钟内
    )
    print(f"  [紧急] {t1.name} (截止: 5分钟内)")
    
    # 普通任务
    t2 = manager.create_task(
        "记忆巩固",
        TaskType.MEMORY,
        priority=TaskPriority.HIGH
    )
    print(f"  [高] {t2.name}")
    
    t3 = manager.create_task(
        "社交互动",
        TaskType.SOCIAL,
        priority=TaskPriority.NORMAL
    )
    print(f"  [正常] {t3.name}")
    
    t4 = manager.create_task(
        "日志清理",
        TaskType.MAINTENANCE,
        priority=TaskPriority.LOW
    )
    print(f"  [低] {t4.name}")
    
    # 有依赖的任务
    t5 = manager.create_task(
        "进化分析报告",
        TaskType.EVOLUTION,
        priority=TaskPriority.HIGH,
        dependencies=[t1.id]  # 依赖系统巡检
    )
    print(f"  [高] {t5.name} (依赖: 系统巡检)")
    
    # 显示队列状态
    print("\n📊 初始队列状态:")
    status = manager.task_scheduler.get_queue_status()
    for key, value in status.items():
        if key != "queues":
            print(f"  {key}: {value}")
    
    # 执行调度
    print("\n⚡ 执行第一轮调度:")
    manager.wake()
    
    status = manager.task_scheduler.get_queue_status()
    print(f"  已完成: {status['completed']}")
    print(f"  运行中: {status['running']}")
    print(f"  等待中: {status['pending']}")
    
    # 再执行一轮（应该会执行有依赖的任务）
    print("\n⚡ 执行第二轮调度:")
    manager.wake()
    
    status = manager.task_scheduler.get_queue_status()
    print(f"  已完成: {status['completed']}")
    print(f"  运行中: {status['running']}")
    print(f"  失败: {status['failed']}")
    
    # 显示统计
    print("\n📈 任务统计:")
    stats = manager.task_scheduler.get_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.2f}")
        else:
            print(f"  {key}: {value}")
    
    # 智能体状态
    print("\n💓 智能体心跳状态:")
    agent_stats = manager.heartbeat_scheduler.get_all_status()
    for s in agent_stats:
        print(f"  {s['agent_id']}: {s['status']} "
              f"(心跳次数: {s['total_heartbeats']}, "
              f"间隔: {s['interval']}s)")
    
    # 整体状态
    print("\n🏥 系统整体状态:")
    overall = manager.get_status()
    print(f"  整体健康度: {overall['overall_health']:.2%}")
    print(f"  任务成功率: {overall['tasks']['success_rate']:.2%}")
    print(f"  智能体健康: {overall['agents']['healthy']}/{overall['agents']['total']}")
    
    # 今日调度计划
    print("\n📅 今日调度计划:")
    schedule = manager.awake_scheduler.get_daily_schedule()
    total_wakes = sum(s["wake_count_estimate"] for s in schedule)
    print(f"  预计今日唤醒次数: {total_wakes} 次")
    
    # 显示各时段
    mode_summary = defaultdict(int)
    for s in schedule:
        mode_summary[s["mode"]] += s["wake_count_estimate"]
    
    print("  各时段分布:")
    for mode, count in mode_summary.items():
        print(f"    {mode}: {count} 次")
    
    print("\n" + "=" * 60)
    print("✅ 智能唤醒与调度系统 v4.0 演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo()
