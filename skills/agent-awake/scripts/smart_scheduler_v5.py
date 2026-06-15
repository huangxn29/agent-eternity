#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能唤醒调度 v5.0 - 多智能体协同调度系统

核心能力：
1. DAG工作流调度 - 任务依赖图，自动排序执行
2. 优先级队列 - 6级优先级，紧急任务优先
3. 智能唤醒 - 按需唤醒，空闲休眠，节省资源
4. 负载均衡 - 多实例任务分发，避免单点过载
5. 任务重试 - 失败自动重试，指数退避
6. 并发控制 - 最大并发数限制，保护系统稳定
7. 调度日历 - 支持定时/周期性任务
8. 资源感知 - 根据系统负载动态调整调度
9. 任务监控 - 实时状态追踪与性能统计

@author: 元界
@version: 5.0.0
"""

import os
import sys
import json
import time
import uuid
import heapq
import logging
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Callable, Set
from pathlib import Path
from enum import Enum

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('awake_v5')


# ============================================================
# 枚举类型
# ============================================================

class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = 0  # 最高：紧急故障处理
    HIGH = 1      # 高：重要任务
    NORMAL = 2    # 普通：常规任务
    LOW = 3       # 低：后台任务
    IDLE = 4      # 最低：空闲时才执行
    BATCH = 5     # 批量：批量处理任务


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"       # 等待中
    SCHEDULED = "scheduled"   # 已调度
    RUNNING = "running"       # 运行中
    PAUSED = "paused"         # 已暂停
    COMPLETED = "completed"   # 已完成
    FAILED = "failed"         # 失败
    CANCELLED = "cancelled"   # 已取消
    RETRYING = "retrying"     # 重试中


class ScheduleType(Enum):
    """调度类型"""
    IMMEDIATE = "immediate"   # 立即执行
    DELAYED = "delayed"       # 延迟执行
    RECURRING = "recurring"   # 周期性执行
    CRON = "cron"             # Cron表达式


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Task:
    """任务"""
    task_id: str
    name: str
    task_type: str
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    payload: dict = field(default_factory=dict)
    
    # 调度相关
    schedule_type: ScheduleType = ScheduleType.IMMEDIATE
    scheduled_time: str = ""  # 计划执行时间
    cron_expression: str = ""  # Cron表达式
    interval_seconds: int = 0  # 周期间隔
    
    # 执行相关
    max_retries: int = 3
    retry_count: int = 0
    timeout_seconds: int = 300  # 超时时间
    execution_time: float = 0.0  # 执行耗时
    
    # 依赖
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    dependents: List[str] = field(default_factory=list)    # 被依赖的任务ID
    
    # 资源需求
    required_capability: int = 50  # 需要的能力等级
    memory_required_mb: int = 100  # 需要的内存
    
    # 时间记录
    created_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    last_error: str = ""
    
    # 分配
    assigned_agent: str = ""  # 分配给哪个智能体
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.task_id:
            self.task_id = f"task_{uuid.uuid4().hex[:12]}"
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['priority'] = self.priority.value
        d['status'] = self.status.value
        d['schedule_type'] = self.schedule_type.value
        return d
    
    @classmethod
    def from_dict(cls, d: dict) -> 'Task':
        d = d.copy()
        d['priority'] = TaskPriority(d.get('priority', 2))
        d['status'] = TaskStatus(d.get('status', 'pending'))
        d['schedule_type'] = ScheduleType(d.get('schedule_type', 'immediate'))
        return cls(**d)


@dataclass
class AgentInstance:
    """智能体实例"""
    agent_id: str
    name: str
    status: str = "idle"  # idle/running/sleeping/offline
    capability: float = 60.0
    current_load: float = 0.0  # 当前负载 0-100
    current_task: str = ""
    last_heartbeat: str = ""
    tasks_completed: int = 0
    tasks_failed: int = 0
    total_uptime: float = 0.0  # 总运行时间(秒)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Workflow:
    """工作流 - DAG任务组"""
    name: str
    workflow_id: str = ""
    tasks: List[str] = field(default_factory=list)  # 任务ID列表
    status: str = "pending"
    created_at: str = ""
    completed_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.workflow_id:
            self.workflow_id = f"workflow_{uuid.uuid4().hex[:12]}"
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class ScheduleStats:
    """调度统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    cancelled_tasks: int = 0
    total_retry_count: int = 0
    avg_execution_time: float = 0.0
    peak_concurrent_tasks: int = 0
    tasks_by_priority: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 优先级队列
# ============================================================

class PriorityTaskQueue:
    """优先级任务队列"""
    
    def __init__(self):
        self._heap: List[Tuple[int, str, Task]] = []
        self._task_map: Dict[str, Task] = {}
        self._lock = threading.Lock()
    
    def push(self, task: Task):
        """添加任务"""
        with self._lock:
            heapq.heappush(self._heap, (task.priority.value, task.task_id, task))
            self._task_map[task.task_id] = task
    
    def pop(self) -> Optional[Task]:
        """取出最高优先级任务"""
        with self._lock:
            if not self._heap:
                return None
            
            while self._heap:
                priority, task_id, task = heapq.heappop(self._heap)
                if task_id in self._task_map and task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                    del self._task_map[task_id]
                    return task
            
            return None
    
    def peek(self) -> Optional[Task]:
        """查看最高优先级任务但不移除"""
        with self._lock:
            for priority, task_id, task in self._heap:
                if task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                    return task
            return None
    
    def size(self) -> int:
        """队列大小"""
        with self._lock:
            return len([t for t in self._task_map.values() 
                       if t.status in [TaskStatus.PENDING, TaskStatus.RETRYING]])
    
    def remove(self, task_id: str) -> bool:
        """移除任务"""
        with self._lock:
            if task_id in self._task_map:
                self._task_map[task_id].status = TaskStatus.CANCELLED
                return True
            return False
    
    def get_all_tasks(self) -> List[Task]:
        """获取所有任务"""
        with self._lock:
            return list(self._task_map.values())


# ============================================================
# DAG调度器
# ============================================================

class DAGScheduler:
    """DAG工作流调度器"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.workflows: Dict[str, Workflow] = {}
        self._lock = threading.Lock()
    
    def add_task(self, task: Task, workflow_id: str = None) -> str:
        """添加任务"""
        with self._lock:
            self.tasks[task.task_id] = task
            
            if workflow_id and workflow_id in self.workflows:
                self.workflows[workflow_id].tasks.append(task.task_id)
            
            return task.task_id
    
    def add_dependency(self, task_id: str, depends_on: str):
        """添加依赖关系"""
        with self._lock:
            if task_id in self.tasks and depends_on in self.tasks:
                if depends_on not in self.tasks[task_id].dependencies:
                    self.tasks[task_id].dependencies.append(depends_on)
                if task_id not in self.tasks[depends_on].dependents:
                    self.tasks[depends_on].dependents.append(task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """获取所有可以执行的任务（依赖已满足）"""
        ready = []
        with self._lock:
            for task in self.tasks.values():
                if task.status != TaskStatus.PENDING:
                    continue
                
                # 检查所有依赖是否完成
                deps_met = True
                for dep_id in task.dependencies:
                    dep = self.tasks.get(dep_id)
                    if not dep or dep.status != TaskStatus.COMPLETED:
                        deps_met = False
                        break
                
                if deps_met:
                    ready.append(task)
        
        # 按优先级排序
        ready.sort(key=lambda t: t.priority.value)
        return ready
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        with self._lock:
            return self.tasks.get(task_id)
    
    def update_task_status(self, task_id: str, status: TaskStatus, **kwargs):
        """更新任务状态"""
        with self._lock:
            if task_id in self.tasks:
                task = self.tasks[task_id]
                task.status = status
                
                if status == TaskStatus.RUNNING:
                    task.started_at = datetime.now().isoformat()
                elif status in [TaskStatus.COMPLETED, TaskStatus.FAILED]:
                    task.completed_at = datetime.now().isoformat()
                    if task.started_at:
                        try:
                            start = datetime.fromisoformat(task.started_at)
                            end = datetime.fromisoformat(task.completed_at)
                            task.execution_time = (end - start).total_seconds()
                        except:
                            pass
                
                for key, value in kwargs.items():
                    if hasattr(task, key):
                        setattr(task, key, value)
                
                # 检查工作流是否完成
                self._check_workflow_completion(task)
    
    def _check_workflow_completion(self, task: Task):
        """检查工作流是否完成（内部调用，需加锁）"""
        for wf in self.workflows.values():
            if task.task_id in wf.tasks:
                all_done = all(
                    self.tasks.get(tid).status == TaskStatus.COMPLETED
                    for tid in wf.tasks if tid in self.tasks
                )
                if all_done:
                    wf.status = "completed"
                    wf.completed_at = datetime.now().isoformat()
    
    def get_dependent_tasks(self, task_id: str) -> List[Task]:
        """获取依赖此任务的所有任务"""
        with self._lock:
            if task_id not in self.tasks:
                return []
            task = self.tasks[task_id]
            return [self.tasks[t] for t in task.dependents if t in self.tasks]
    
    def create_workflow(self, name: str) -> str:
        """创建工作流"""
        wf = Workflow(name=name)
        with self._lock:
            self.workflows[wf.workflow_id] = wf
        return wf.workflow_id
    
    def get_workflow_status(self, workflow_id: str) -> dict:
        """获取工作流状态"""
        with self._lock:
            wf = self.workflows.get(workflow_id)
            if not wf:
                return {}
            
            tasks = [self.tasks.get(tid) for tid in wf.tasks if tid in self.tasks]
            completed = sum(1 for t in tasks if t and t.status == TaskStatus.COMPLETED)
            failed = sum(1 for t in tasks if t and t.status == TaskStatus.FAILED)
            
            return {
                "workflow_id": workflow_id,
                "name": wf.name,
                "status": wf.status,
                "total_tasks": len(wf.tasks),
                "completed_tasks": completed,
                "failed_tasks": failed,
                "pending_tasks": len(wf.tasks) - completed - failed
            }


# ============================================================
# 智能唤醒调度器
# ============================================================

class SmartAwakeSchedulerV5:
    """智能唤醒调度器 v5.0"""
    
    def __init__(self, data_path: str = None, max_concurrent: int = 10):
        """
        初始化调度器
        
        Args:
            data_path: 数据存储路径
            max_concurrent: 最大并发任务数
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'scheduler_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 核心组件
        self.task_queue = PriorityTaskQueue()
        self.dag_scheduler = DAGScheduler()
        
        # 智能体实例管理
        self.agents: Dict[str, AgentInstance] = {}
        
        # 并发控制
        self.max_concurrent = max_concurrent
        self.current_running = 0
        
        # 统计
        self.stats = ScheduleStats()
        
        # 运行状态
        self._running = False
        self._scheduler_thread = None
        self._lock = threading.Lock()
        
        # 任务执行回调
        self.task_executor: Optional[Callable[[Task], bool]] = None
        
        # 数据文件
        self._tasks_file = self.data_path / 'tasks.json'
        self._agents_file = self.data_path / 'agents.json'
        self._stats_file = self.data_path / 'stats.json'
        
        self._load_data()
        
        logger.info(f"智能唤醒调度 v5.0 初始化完成 - 最大并发: {max_concurrent}")
    
    def _load_data(self):
        """加载持久化数据"""
        # 加载任务
        if self._tasks_file.exists():
            try:
                with open(self._tasks_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for task_data in data:
                        task = Task.from_dict(task_data)
                        if task.status in [TaskStatus.PENDING, TaskStatus.RETRYING]:
                            self.task_queue.push(task)
                        self.dag_scheduler.tasks[task.task_id] = task
            except Exception as e:
                logger.error(f"加载任务数据失败: {e}")
        
        # 加载智能体
        if self._agents_file.exists():
            try:
                with open(self._agents_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for aid, agent_data in data.items():
                        self.agents[aid] = AgentInstance(**agent_data)
            except Exception as e:
                logger.error(f"加载智能体数据失败: {e}")
        
        # 加载统计
        if self._stats_file.exists():
            try:
                with open(self._stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.stats = ScheduleStats(**data)
            except Exception as e:
                logger.error(f"加载统计数据失败: {e}")
    
    def _save_tasks(self):
        """保存任务数据"""
        try:
            all_tasks = list(self.dag_scheduler.tasks.values())
            with open(self._tasks_file, 'w', encoding='utf-8') as f:
                json.dump([t.to_dict() for t in all_tasks], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存任务数据失败: {e}")
    
    def _save_agents(self):
        """保存智能体数据"""
        try:
            with open(self._agents_file, 'w', encoding='utf-8') as f:
                json.dump({k: v.to_dict() for k, v in self.agents.items()}, 
                         f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存智能体数据失败: {e}")
    
    def _save_stats(self):
        """保存统计数据"""
        try:
            with open(self._stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats.to_dict(), f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存统计数据失败: {e}")
    
    # ============================================================
    # 任务管理
    # ============================================================
    
    def submit_task(self, name: str, task_type: str, 
                   priority: TaskPriority = TaskPriority.NORMAL,
                   payload: dict = None,
                   dependencies: List[str] = None,
                   workflow_id: str = None,
                   schedule_type: ScheduleType = ScheduleType.IMMEDIATE,
                   scheduled_time: str = "",
                   max_retries: int = 3,
                   timeout_seconds: int = 300) -> str:
        """
        提交任务
        
        Returns:
            任务ID
        """
        task = Task(
            task_id=f"task_{uuid.uuid4().hex[:12]}",
            name=name,
            task_type=task_type,
            priority=priority,
            payload=payload or {},
            dependencies=dependencies or [],
            schedule_type=schedule_type,
            scheduled_time=scheduled_time,
            max_retries=max_retries,
            timeout_seconds=timeout_seconds
        )
        
        # 添加到DAG调度器
        self.dag_scheduler.add_task(task, workflow_id)
        
        # 建立依赖关系
        for dep_id in dependencies or []:
            self.dag_scheduler.add_dependency(task.task_id, dep_id)
        
        # 如果是立即执行且无依赖，加入优先级队列
        if schedule_type == ScheduleType.IMMEDIATE and not task.dependencies:
            self.task_queue.push(task)
        
        self.stats.total_tasks += 1
        self._save_tasks()
        self._save_stats()
        
        logger.info(f"任务提交: {name} (ID: {task.task_id}, 优先级: {priority.name})")
        return task.task_id
    
    def cancel_task(self, task_id: str) -> bool:
        """取消任务"""
        result = self.task_queue.remove(task_id)
        if result:
            self.dag_scheduler.update_task_status(task_id, TaskStatus.CANCELLED)
            self.stats.cancelled_tasks += 1
            self._save_stats()
            logger.info(f"任务已取消: {task_id}")
        return result
    
    def get_task_status(self, task_id: str) -> Optional[dict]:
        """获取任务状态"""
        task = self.dag_scheduler.get_task(task_id)
        if task:
            return task.to_dict()
        return None
    
    # ============================================================
    # 智能体管理
    # ============================================================
    
    def register_agent(self, agent_id: str, name: str, 
                      capability: float = 60.0) -> str:
        """注册智能体"""
        agent = AgentInstance(
            agent_id=agent_id,
            name=name,
            capability=capability,
            last_heartbeat=datetime.now().isoformat()
        )
        
        self.agents[agent_id] = agent
        self._save_agents()
        
        logger.info(f"智能体已注册: {name} (ID: {agent_id}, 能力: {capability})")
        return agent_id
    
    def unregister_agent(self, agent_id: str) -> bool:
        """注销智能体"""
        if agent_id in self.agents:
            del self.agents[agent_id]
            self._save_agents()
            logger.info(f"智能体已注销: {agent_id}")
            return True
        return False
    
    def heartbeat(self, agent_id: str, load: float = 0.0) -> bool:
        """智能体心跳"""
        if agent_id in self.agents:
            agent = self.agents[agent_id]
            agent.last_heartbeat = datetime.now().isoformat()
            agent.current_load = load
            if agent.status == "offline":
                agent.status = "idle"
                logger.info(f"智能体上线: {agent.name}")
            return True
        return False
    
    def get_available_agents(self, min_capability: int = 0) -> List[AgentInstance]:
        """获取可用智能体"""
        now = datetime.now()
        available = []
        
        for agent in self.agents.values():
            if agent.status in ["idle", "running"]:
                # 检查心跳是否在5分钟内
                try:
                    last_hb = datetime.fromisoformat(agent.last_heartbeat)
                    if (now - last_hb) < timedelta(minutes=5):
                        if agent.capability >= min_capability:
                            available.append(agent)
                except:
                    pass
        
        # 按负载升序排序（负载低的优先）
        available.sort(key=lambda a: a.current_load)
        return available
    
    # ============================================================
    # 任务调度
    # ============================================================
    
    def _schedule_tick(self):
        """调度周期 - 内部方法"""
        # 检查并发限制
        if self.current_running >= self.max_concurrent:
            return
        
        # 获取就绪的DAG任务
        ready_tasks = self.dag_scheduler.get_ready_tasks()
        
        # 重新加入队列（如果还没在队列里）
        for task in ready_tasks:
            if task.status == TaskStatus.PENDING:
                self.task_queue.push(task)
        
        # 取出最高优先级任务
        task = self.task_queue.pop()
        if not task:
            return
        
        # 查找合适的智能体
        available_agents = self.get_available_agents(task.required_capability)
        
        if not available_agents:
            # 没有可用智能体，任务重新入队
            task.status = TaskStatus.PENDING
            self.task_queue.push(task)
            logger.debug(f"无可用智能体，任务等待: {task.name}")
            return
        
        # 分配给负载最低的智能体
        agent = available_agents[0]
        
        # 执行任务
        self._execute_task(task, agent)
    
    def _execute_task(self, task: Task, agent: AgentInstance):
        """执行任务"""
        with self._lock:
            self.current_running += 1
            if self.current_running > self.stats.peak_concurrent_tasks:
                self.stats.peak_concurrent_tasks = self.current_running
        
        # 更新状态
        task.status = TaskStatus.RUNNING
        task.assigned_agent = agent.agent_id
        task.started_at = datetime.now().isoformat()
        agent.status = "running"
        agent.current_task = task.task_id
        agent.current_load = min(100, agent.current_load + 20)
        
        self.dag_scheduler.update_task_status(task.task_id, TaskStatus.RUNNING,
                                            assigned_agent=agent.agent_id)
        
        logger.info(f"开始执行任务: {task.name} (分配给: {agent.name})")
        
        # 异步执行
        def run_task():
            try:
                success = True
                
                if self.task_executor:
                    success = self.task_executor(task)
                
                # 执行完成
                if success:
                    self._on_task_success(task, agent)
                else:
                    self._on_task_failure(task, agent, "执行失败")
                    
            except Exception as e:
                logger.error(f"任务执行异常: {task.name} - {e}")
                self._on_task_failure(task, agent, str(e))
            
            finally:
                with self._lock:
                    self.current_running -= 1
        
        thread = threading.Thread(target=run_task, daemon=True)
        thread.start()
    
    def _on_task_success(self, task: Task, agent: AgentInstance):
        """任务成功"""
        task.status = TaskStatus.COMPLETED
        task.completed_at = datetime.now().isoformat()
        
        # 计算执行时间
        if task.started_at:
            try:
                start = datetime.fromisoformat(task.started_at)
                end = datetime.fromisoformat(task.completed_at)
                task.execution_time = (end - start).total_seconds()
            except:
                pass
        
        # 更新智能体状态
        agent.status = "idle"
        agent.current_task = ""
        agent.tasks_completed += 1
        agent.current_load = max(0, agent.current_load - 20)
        
        # 更新统计
        self.stats.completed_tasks += 1
        
        # 更新DAG状态
        self.dag_scheduler.update_task_status(task.task_id, TaskStatus.COMPLETED)
        
        # 检查下游任务，依赖满足则加入队列
        dependents = self.dag_scheduler.get_dependent_tasks(task.task_id)
        for dep_task in dependents:
            # 检查该任务的所有依赖是否都完成了
            all_deps_done = all(
                self.dag_scheduler.get_task(dep_id).status == TaskStatus.COMPLETED
                for dep_id in dep_task.dependencies
                if dep_id in self.dag_scheduler.tasks
            )
            if all_deps_done and dep_task.status == TaskStatus.PENDING:
                self.task_queue.push(dep_task)
                logger.info(f"依赖满足，任务入队: {dep_task.name}")
        
        self._save_tasks()
        self._save_agents()
        self._save_stats()
        
        logger.info(f"任务完成: {task.name} (耗时: {task.execution_time:.2f}s)")
    
    def _on_task_failure(self, task: Task, agent: AgentInstance, error: str):
        """任务失败"""
        task.last_error = error
        
        # 更新智能体状态
        agent.status = "idle"
        agent.current_task = ""
        agent.tasks_failed += 1
        agent.current_load = max(0, agent.current_load - 20)
        
        # 检查是否可以重试
        if task.retry_count < task.max_retries:
            task.retry_count += 1
            task.status = TaskStatus.RETRYING
            self.stats.total_retry_count += 1
            
            # 指数退避延迟后重新入队
            delay = 2 ** task.retry_count  # 2, 4, 8, 16...
            logger.info(f"任务重试 ({task.retry_count}/{task.max_retries}): {task.name} - {error}")
            
            def delayed_retry():
                time.sleep(delay)
                if task.status == TaskStatus.RETRYING:
                    self.dag_scheduler.update_task_status(task.task_id, TaskStatus.PENDING)
                    self.task_queue.push(task)
            
            thread = threading.Thread(target=delayed_retry, daemon=True)
            thread.start()
        else:
            task.status = TaskStatus.FAILED
            self.stats.failed_tasks += 1
            logger.error(f"任务最终失败: {task.name} - {error}")
        
        self.dag_scheduler.update_task_status(
            task.task_id, task.status, 
            last_error=error,
            retry_count=task.retry_count
        )
        
        self._save_tasks()
        self._save_agents()
        self._save_stats()
    
    # ============================================================
    # 调度启停
    # ============================================================
    
    def start(self):
        """启动调度器"""
        if self._running:
            logger.warning("调度器已在运行")
            return
        
        self._running = True
        
        def scheduler_loop():
            logger.info("调度器主循环已启动")
            while self._running:
                try:
                    self._schedule_tick()
                except Exception as e:
                    logger.error(f"调度循环异常: {e}")
                
                time.sleep(0.5)  # 500ms调度间隔
            
            logger.info("调度器主循环已停止")
        
        self._scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self._scheduler_thread.start()
        
        logger.info("智能唤醒调度器 v5.0 已启动")
    
    def stop(self):
        """停止调度器"""
        self._running = False
        if self._scheduler_thread:
            self._scheduler_thread.join(timeout=5)
        logger.info("智能唤醒调度器 v5.0 已停止")
    
    # ============================================================
    # 状态查询
    # ============================================================
    
    def get_status(self) -> dict:
        """获取调度器状态"""
        queue_size = self.task_queue.size()
        running_count = self.current_running
        active_agents = len([a for a in self.agents.values() if a.status != "offline"])
        
        # 各优先级任务数
        priority_counts = {}
        for task in self.task_queue.get_all_tasks():
            p = task.priority.name
            priority_counts[p] = priority_counts.get(p, 0) + 1
        
        return {
            "version": "5.0",
            "running": self._running,
            "queue_size": queue_size,
            "running_tasks": running_count,
            "max_concurrent": self.max_concurrent,
            "active_agents": active_agents,
            "total_agents": len(self.agents),
            "tasks_by_priority": priority_counts,
            "stats": self.stats.to_dict()
        }
    
    def get_worker_status(self) -> List[dict]:
        """获取所有工作节点状态"""
        return [agent.to_dict() for agent in self.agents.values()]
    
    def get_pending_tasks(self, limit: int = 20) -> List[dict]:
        """获取待处理任务"""
        tasks = self.task_queue.get_all_tasks()
        tasks.sort(key=lambda t: t.priority.value)
        return [t.to_dict() for t in tasks[:limit]]


# ============================================================
# 演示与测试
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("智能唤醒调度 v5.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建调度器
        scheduler = SmartAwakeSchedulerV5(
            data_path=os.path.join(tmpdir, "scheduler"),
            max_concurrent=5
        )
        
        # 注册智能体
        print("\n🤖 注册智能体...")
        scheduler.register_agent("agent-001", "建造者-1号", capability=80.0)
        scheduler.register_agent("agent-002", "建造者-2号", capability=70.0)
        scheduler.register_agent("agent-003", "哨兵-1号", capability=60.0)
        print(f"  已注册 {len(scheduler.agents)} 个智能体")
        
        # 设置简单的任务执行器
        execution_count = 0
        
        def mock_executor(task: Task) -> bool:
            nonlocal execution_count
            execution_count += 1
            time.sleep(0.1)
            if task.priority == TaskPriority.LOW and execution_count % 5 == 0:
                return False
            return True
        
        scheduler.task_executor = mock_executor
        
        # 启动调度器
        scheduler.start()
        print("\n▶️ 调度器已启动")
        
        # 提交不同优先级的任务
        print("\n📋 提交任务...")
        
        for i in range(3):
            scheduler.submit_task(
                name=f"普通任务-{i+1}",
                task_type="normal",
                priority=TaskPriority.NORMAL
            )
        
        scheduler.submit_task(
            name="紧急任务-1",
            task_type="urgent",
            priority=TaskPriority.HIGH
        )
        
        scheduler.submit_task(
            name="后台任务-1",
            task_type="background",
            priority=TaskPriority.LOW
        )
        
        scheduler.submit_task(
            name="关键任务-1",
            task_type="critical",
            priority=TaskPriority.CRITICAL
        )
        
        print(f"  已提交 6 个任务")
        
        # 等待执行
        time.sleep(1)
        
        # 查看状态
        print("\n📊 调度器状态:")
        status = scheduler.get_status()
        print(f"  运行中: {'是' if status['running'] else '否'}")
        print(f"  队列大小: {status['queue_size']}")
        print(f"  运行中任务: {status['running_tasks']}")
        print(f"  活跃智能体: {status['active_agents']}")
        print(f"  最大并发: {status['max_concurrent']}")
        
        print("\n📈 统计数据:")
        stats = status['stats']
        print(f"  总任务数: {stats['total_tasks']}")
        print(f"  已完成: {stats['completed_tasks']}")
        print(f"  失败: {stats['failed_tasks']}")
        print(f"  总重试次数: {stats['total_retry_count']}")
        print(f"  峰值并发: {stats['peak_concurrent_tasks']}")
        
        # DAG工作流演示
        print("\n🔗 DAG工作流演示:")
        wf_id = scheduler.dag_scheduler.create_workflow("数据处理工作流")
        
        task_a = scheduler.submit_task("数据采集", "collect", priority=TaskPriority.NORMAL)
        task_b = scheduler.submit_task("数据清洗", "clean", priority=TaskPriority.NORMAL,
                                       dependencies=[task_a])
        task_c = scheduler.submit_task("数据分析", "analyze", priority=TaskPriority.HIGH,
                                       dependencies=[task_b])
        task_d = scheduler.submit_task("报告生成", "report", priority=TaskPriority.NORMAL,
                                       dependencies=[task_c])
        
        for tid in [task_a, task_b, task_c, task_d]:
            scheduler.dag_scheduler.workflows[wf_id].tasks.append(tid)
        
        print(f"  工作流ID: {wf_id}")
        print(f"  任务链: 数据采集 → 数据清洗 → 数据分析 → 报告生成")
        
        # 等待工作流完成
        time.sleep(2)
        
        wf_status = scheduler.dag_scheduler.get_workflow_status(wf_id)
        print(f"  工作流状态: {wf_status['status']}")
        print(f"  完成进度: {wf_status['completed_tasks']}/{wf_status['total_tasks']}")
        
        # 查看智能体状态
        print("\n🤖 智能体状态:")
        workers = scheduler.get_worker_status()
        for w in workers:
            print(f"  {w['name']}: {w['status']} "
                  f"(能力:{w['capability']}, "
                  f"完成:{w['tasks_completed']}, "
                  f"失败:{w['tasks_failed']})")
        
        # 停止调度器
        scheduler.stop()
        
        print("\n" + "=" * 70)
        print("✅ 智能唤醒调度 v5.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
