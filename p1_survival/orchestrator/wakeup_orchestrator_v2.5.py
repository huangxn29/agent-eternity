#!/usr/bin/env python3
"""
唤醒编排引擎 v2.5
Wakeup Orchestration Engine v2.5

核心能力：
- 智能任务调度与动态优先级
- 多节点协同调度与负载均衡
- 任务依赖图与执行路径规划
- 失败自愈与降级策略
- 跨平台唤醒适配层
- 调度策略自学习与优化
- 实时资源监控与动态调整
- 定时任务与事件驱动双模式
"""

import json
import time
import threading
import queue
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid


class TaskStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    PAUSED = "paused"


class TaskPriority(Enum):
    CRITICAL = 0  # 必须立即执行
    HIGH = 1      # 高优先级
    NORMAL = 2    # 普通优先级
    LOW = 3       # 低优先级
    IDLE = 4      # 空闲时执行


class ScheduleStrategy(Enum):
    ASAP = "asap"           # 尽快执行
    FIXED_TIME = "fixed"    # 固定时间
    INTERVAL = "interval"   # 固定间隔
    CRON = "cron"           # Cron表达式
    EVENT_DRIVEN = "event"  # 事件驱动
    DEPENDENCY = "dependency"  # 依赖驱动


@dataclass
class Task:
    task_id: str
    name: str
    description: str
    priority: TaskPriority
    strategy: ScheduleStrategy
    target_func: Optional[str] = None
    params: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    schedule_time: Optional[datetime] = None
    interval_seconds: Optional[int] = None
    cron_expression: Optional[str] = None
    max_retries: int = 3
    retry_delay: int = 30
    timeout: int = 300
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    last_error: Optional[str] = None
    retry_count: int = 0
    execution_time: float = 0.0
    success_count: int = 0
    failure_count: int = 0
    estimated_duration: float = 60.0  # 预估执行时间（秒）
    tags: List[str] = field(default_factory=list)
    node_affinity: Optional[str] = None  # 节点亲和性


@dataclass
class ExecutionNode:
    node_id: str
    name: str
    status: str  # active, inactive, overloaded
    current_load: float = 0.0  # 0-1
    max_concurrent_tasks: int = 10
    running_tasks: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    last_heartbeat: datetime = field(default_factory=datetime.now)
    performance_score: float = 0.8  # 性能评分


@dataclass
class ScheduleEvent:
    event_id: str
    event_type: str
    timestamp: datetime
    data: Dict[str, Any] = field(default_factory=dict)


class TaskDependencyGraph:
    """任务依赖图"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.dependents: Dict[str, List[str]] = {}  # task_id -> 依赖它的任务
    
    def add_task(self, task: Task):
        self.tasks[task.task_id] = task
        for dep in task.dependencies:
            if dep not in self.dependents:
                self.dependents[dep] = []
            self.dependents[dep].append(task.task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """获取所有依赖已满足、可执行的任务"""
        ready = []
        for task in self.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            if self._dependencies_met(task):
                ready.append(task)
        # 按优先级排序
        ready.sort(key=lambda t: t.priority.value)
        return ready
    
    def _dependencies_met(self, task: Task) -> bool:
        for dep_id in task.dependencies:
            dep_task = self.tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def get_critical_path(self) -> List[str]:
        """计算关键路径"""
        # 简化的关键路径算法
        path = []
        # 找到没有依赖的起点任务
        start_tasks = [t for t in self.tasks.values() if not t.dependencies]
        if not start_tasks:
            return []
        
        # DFS找最长路径
        def dfs(task_id: str, current_path: List[str]):
            current_path.append(task_id)
            deps = self.dependents.get(task_id, [])
            if not deps:
                if len(current_path) > len(path):
                    path.clear()
                    path.extend(current_path)
            else:
                for dep_id in deps:
                    dfs(dep_id, current_path.copy())
        
        for task in start_tasks:
            dfs(task.task_id, [])
        
        return path


class MultiNodeScheduler:
    """多节点调度器"""
    
    def __init__(self):
        self.nodes: Dict[str, ExecutionNode] = {}
        self.task_assignments: Dict[str, str] = {}  # task_id -> node_id
    
    def add_node(self, node: ExecutionNode):
        self.nodes[node.node_id] = node
    
    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    def update_node_load(self, node_id: str, load: float):
        if node_id in self.nodes:
            self.nodes[node_id].current_load = min(1.0, max(0.0, load))
            self.nodes[node_id].last_heartbeat = datetime.now()
    
    def assign_task(self, task: Task) -> Optional[str]:
        """
        为任务分配合适的执行节点
        考虑因素：节点负载、能力匹配、亲和性、性能评分
        """
        candidates = []
        
        for node in self.nodes.values():
            if node.status != "active":
                continue
            
            # 检查节点能力
            if task.tags and not any(cap in task.tags for cap in node.capabilities):
                if not set(task.tags).intersection(set(node.capabilities)):
                    continue
            
            # 检查节点亲和性
            if task.node_affinity and node.node_id != task.node_affinity:
                continue
            
            # 检查负载
            if len(node.running_tasks) >= node.max_concurrent_tasks:
                continue
            
            # 计算综合评分
            score = self._calculate_node_score(node, task)
            candidates.append((node.node_id, score))
        
        if not candidates:
            return None
        
        # 选择评分最高的节点
        candidates.sort(key=lambda x: x[1], reverse=True)
        best_node_id = candidates[0][0]
        
        # 分配任务
        self.task_assignments[task.task_id] = best_node_id
        self.nodes[best_node_id].running_tasks.append(task.task_id)
        self._recalculate_load(best_node_id)
        
        return best_node_id
    
    def _calculate_node_score(self, node: ExecutionNode, task: Task) -> float:
        """计算节点对任务的适配评分"""
        score = 0.0
        
        # 负载因素（负载越低分越高）- 权重 40%
        load_score = 1.0 - node.current_load
        score += load_score * 0.4
        
        # 性能评分 - 权重 30%
        score += node.performance_score * 0.3
        
        # 能力匹配度 - 权重 20%
        if task.tags and node.capabilities:
            match_count = len(set(task.tags) & set(node.capabilities))
            capability_score = match_count / max(len(task.tags), 1)
            score += capability_score * 0.2
        else:
            score += 0.2  # 默认满分
        
        # 亲和性 - 权重 10%
        if task.node_affinity and node.node_id == task.node_affinity:
            score += 1.0 * 0.1
        else:
            score += 0.05 * 0.1
        
        return score
    
    def _recalculate_load(self, node_id: str):
        """重新计算节点负载"""
        node = self.nodes[node_id]
        load = len(node.running_tasks) / max(node.max_concurrent_tasks, 1)
        node.current_load = min(1.0, load)
    
    def complete_task(self, task_id: str):
        """任务完成，释放节点资源"""
        node_id = self.task_assignments.pop(task_id, None)
        if node_id and node_id in self.nodes:
            node = self.nodes[node_id]
            if task_id in node.running_tasks:
                node.running_tasks.remove(task_id)
            self._recalculate_load(node_id)
    
    def get_overall_load(self) -> float:
        """获取系统整体负载"""
        if not self.nodes:
            return 0.0
        total_load = sum(n.current_load for n in self.nodes.values())
        return total_load / len(self.nodes)
    
    def get_best_node(self) -> Optional[ExecutionNode]:
        """获取当前最优节点"""
        active_nodes = [n for n in self.nodes.values() if n.status == "active"]
        if not active_nodes:
            return None
        return min(active_nodes, key=lambda n: n.current_load)


class FailureRecoveryEngine:
    """失败恢复引擎"""
    
    def __init__(self):
        self.failure_history: List[Dict[str, Any]] = []
        self.recovery_strategies = {
            "retry": self._strategy_retry,
            "fallback": self._strategy_fallback,
            "escalate": self._strategy_escalate,
            "degrade": self._strategy_degrade,
        }
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}  # 熔断器
    
    def handle_failure(self, task: Task, error: str) -> Dict[str, Any]:
        """处理任务失败"""
        failure_record = {
            "task_id": task.task_id,
            "error": error,
            "timestamp": datetime.now(),
            "priority": task.priority.value,
        }
        self.failure_history.append(failure_record)
        
        # 选择恢复策略
        strategy = self._select_recovery_strategy(task, error)
        
        # 执行恢复策略
        result = strategy(task, error)
        
        return result
    
    def _select_recovery_strategy(self, task: Task, error: str) -> Callable:
        """选择恢复策略"""
        # 根据失败次数和错误类型选择策略
        if task.retry_count < task.max_retries:
            return self._strategy_retry
        elif self._is_recoverable_error(error):
            return self._strategy_fallback
        elif task.priority in [TaskPriority.CRITICAL, TaskPriority.HIGH]:
            return self._strategy_escalate
        else:
            return self._strategy_degrade
    
    def _is_recoverable_error(self, error: str) -> bool:
        """判断是否为可恢复错误"""
        recoverable_patterns = [
            "timeout", "connection", "network", "busy",
            "rate limit", "temporary", "unavailable"
        ]
        return any(p in error.lower() for p in recoverable_patterns)
    
    def _strategy_retry(self, task: Task, error: str) -> Dict[str, Any]:
        """重试策略"""
        task.retry_count += 1
        delay = task.retry_delay * (2 ** (task.retry_count - 1))  # 指数退避
        
        return {
            "action": "retry",
            "delay_seconds": delay,
            "retry_count": task.retry_count,
            "message": f"第{task.retry_count}次重试，延迟{delay}秒"
        }
    
    def _strategy_fallback(self, task: Task, error: str) -> Dict[str, Any]:
        """降级策略 - 使用备用方案"""
        return {
            "action": "fallback",
            "message": "使用备用方案执行",
            "fallback_task": f"{task.name}_fallback"
        }
    
    def _strategy_escalate(self, task: Task, error: str) -> Dict[str, Any]:
        """升级策略 - 通知管理员/使用更高权限"""
        return {
            "action": "escalate",
            "severity": "high" if task.priority == TaskPriority.CRITICAL else "medium",
            "message": "任务失败已升级，需要人工介入"
        }
    
    def _strategy_degrade(self, task: Task, error: str) -> Dict[str, Any]:
        """服务降级 - 跳过非核心任务"""
        return {
            "action": "degrade",
            "message": "服务降级，跳过非核心任务",
            "impact": "low"
        }
    
    def check_circuit_breaker(self, task_type: str) -> bool:
        """检查熔断器状态，返回True表示可以执行"""
        breaker = self.circuit_breakers.get(task_type)
        if not breaker:
            return True
        
        if breaker["state"] == "open":
            # 检查是否过了冷却期
            if (datetime.now() - breaker["last_failure"]).total_seconds() > breaker["cool_down"]:
                breaker["state"] = "half_open"
                return True
            return False
        
        return True
    
    def record_circuit_failure(self, task_type: str):
        """记录熔断器失败"""
        breaker = self.circuit_breakers.setdefault(task_type, {
            "state": "closed",
            "failure_count": 0,
            "success_count": 0,
            "last_failure": None,
            "threshold": 5,
            "cool_down": 60,
        })
        
        breaker["failure_count"] += 1
        breaker["last_failure"] = datetime.now()
        
        if breaker["failure_count"] >= breaker["threshold"]:
            breaker["state"] = "open"
    
    def record_circuit_success(self, task_type: str):
        """记录熔断器成功"""
        breaker = self.circuit_breakers.get(task_type)
        if not breaker:
            return
        
        if breaker["state"] == "half_open":
            breaker["success_count"] += 1
            if breaker["success_count"] >= 3:  # 连续3次成功则关闭
                breaker["state"] = "closed"
                breaker["failure_count"] = 0
                breaker["success_count"] = 0
        elif breaker["state"] == "closed":
            breaker["failure_count"] = max(0, breaker["failure_count"] - 1)


class ScheduleOptimizer:
    """调度优化器 - 自学习调度策略"""
    
    def __init__(self):
        self.execution_history: List[Dict[str, Any]] = []
        self.patterns: Dict[str, Dict[str, Any]] = {}  # 任务模式
        self.time_estimation_models: Dict[str, float] = {}  # 时间预估模型
        self.optimal_time_windows: Dict[str, List[Dict[str, Any]]] = {}  # 最佳执行时间窗
    
    def record_execution(self, task: Task, success: bool, execution_time: float):
        """记录执行历史"""
        record = {
            "task_id": task.task_id,
            "task_name": task.name,
            "priority": task.priority.value,
            "success": success,
            "execution_time": execution_time,
            "start_hour": task.started_at.hour if task.started_at else 0,
            "day_of_week": task.started_at.weekday() if task.started_at else 0,
            "timestamp": task.completed_at or datetime.now(),
        }
        self.execution_history.append(record)
        
        # 更新时间预估
        self._update_time_estimation(task.name, execution_time)
        
        # 更新最佳时间窗
        if success:
            self._update_optimal_window(task)
    
    def _update_time_estimation(self, task_name: str, execution_time: float):
        """更新执行时间预估模型（滑动平均）"""
        if task_name not in self.time_estimation_models:
            self.time_estimation_models[task_name] = execution_time
        else:
            # 指数移动平均
            alpha = 0.3
            current = self.time_estimation_models[task_name]
            self.time_estimation_models[task_name] = alpha * execution_time + (1 - alpha) * current
    
    def _update_optimal_window(self, task: Task):
        """更新最佳执行时间窗"""
        task_name = task.name
        if task_name not in self.optimal_time_windows:
            self.optimal_time_windows[task_name] = []
        
        if task.started_at and task.completed_at:
            hour = task.started_at.hour
            efficiency = 1.0  # 可根据执行效率计算
            
            window = {
                "hour": hour,
                "efficiency": efficiency,
                "count": 1,
            }
            
            # 合并相同小时的数据
            existing = next((w for w in self.optimal_time_windows[task_name] if w["hour"] == hour), None)
            if existing:
                existing["count"] += 1
                existing["efficiency"] = (existing["efficiency"] * (existing["count"] - 1) + efficiency) / existing["count"]
            else:
                self.optimal_time_windows[task_name].append(window)
    
    def estimate_execution_time(self, task_name: str) -> float:
        """预估执行时间"""
        return self.time_estimation_models.get(task_name, 60.0)
    
    def get_best_execution_time(self, task_name: str) -> Optional[int]:
        """获取最佳执行小时"""
        windows = self.optimal_time_windows.get(task_name, [])
        if not windows:
            return None
        
        # 按效率排序
        windows.sort(key=lambda w: w["efficiency"], reverse=True)
        return windows[0]["hour"]
    
    def optimize_schedule(self, tasks: List[Task]) -> List[Task]:
        """优化调度顺序"""
        # 基于历史数据优化任务排序
        optimized = sorted(tasks, key=lambda t: (
            t.priority.value,  # 首先按优先级
            self.estimate_execution_time(t.name),  # 然后按预估执行时间（短作业优先）
        ))
        return optimized
    
    def get_analytics_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        total = len(self.execution_history)
        if total == 0:
            return {"total_executions": 0}
        
        success_count = sum(1 for r in self.execution_history if r["success"])
        avg_execution_time = sum(r["execution_time"] for r in self.execution_history) / total
        
        return {
            "total_executions": total,
            "success_rate": success_count / total,
            "average_execution_time": avg_execution_time,
            "tracked_tasks": len(self.time_estimation_models),
            "optimal_windows_count": len(self.optimal_time_windows),
        }


class CrossPlatformWakeupAdapter:
    """跨平台唤醒适配层"""
    
    def __init__(self):
        self.platforms: Dict[str, Dict[str, Any]] = {}
        self.wakeup_handlers: Dict[str, Callable] = {}
    
    def register_platform(self, platform_name: str, config: Dict[str, Any]):
        """注册平台"""
        self.platforms[platform_name] = {
            "config": config,
            "status": "active",
            "last_wakeup": None,
            "wakeup_count": 0,
        }
    
    def set_wakeup_handler(self, platform_name: str, handler: Callable):
        """设置唤醒处理器"""
        self.wakeup_handlers[platform_name] = handler
    
    def wakeup(self, platform_name: str, task: Task = None) -> bool:
        """唤醒指定平台"""
        if platform_name not in self.platforms:
            return False
        
        platform = self.platforms[platform_name]
        if platform["status"] != "active":
            return False
        
        handler = self.wakeup_handlers.get(platform_name)
        if not handler:
            return False
        
        try:
            result = handler(task)
            platform["last_wakeup"] = datetime.now()
            platform["wakeup_count"] += 1
            return result
        except Exception as e:
            platform["last_error"] = str(e)
            return False
    
    def wakeup_all(self, task: Task = None) -> Dict[str, bool]:
        """唤醒所有活跃平台"""
        results = {}
        for name in self.platforms:
            results[name] = self.wakeup(name, task)
        return results
    
    def get_platform_status(self, platform_name: str) -> Optional[Dict[str, Any]]:
        """获取平台状态"""
        return self.platforms.get(platform_name)
    
    def get_all_status(self) -> Dict[str, Dict[str, Any]]:
        """获取所有平台状态"""
        return dict(self.platforms)


class WakeupOrchestrator:
    """唤醒编排器 - 主类"""
    
    def __init__(self):
        self.task_queue = queue.PriorityQueue()
        self.dependency_graph = TaskDependencyGraph()
        self.node_scheduler = MultiNodeScheduler()
        self.failure_engine = FailureRecoveryEngine()
        self.optimizer = ScheduleOptimizer()
        self.platform_adapter = CrossPlatformWakeupAdapter()
        
        self.running = False
        self.worker_thread = None
        self.event_handlers: Dict[str, List[Callable]] = {}
        
        # 统计数据
        self.stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "skipped_tasks": 0,
            "total_execution_time": 0.0,
            "start_time": None,
        }
    
    def add_task(self, task: Task):
        """添加任务"""
        self.dependency_graph.add_task(task)
        self.stats["total_tasks"] += 1
        
        # 触发事件
        self._emit_event("task_added", {"task": task})
    
    def add_node(self, node: ExecutionNode):
        """添加执行节点"""
        self.node_scheduler.add_node(node)
    
    def register_event_handler(self, event_type: str, handler: Callable):
        """注册事件处理器"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
    
    def _emit_event(self, event_type: str, data: Dict[str, Any]):
        """触发事件"""
        handlers = self.event_handlers.get(event_type, [])
        for handler in handlers:
            try:
                handler(data)
            except Exception:
                pass
    
    def start(self):
        """启动调度器"""
        self.running = True
        self.stats["start_time"] = datetime.now()
        self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """停止调度器"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _run_loop(self):
        """主运行循环"""
        while self.running:
            try:
                # 获取可执行任务
                ready_tasks = self.dependency_graph.get_ready_tasks()
                
                if not ready_tasks:
                    time.sleep(1)
                    continue
                
                # 优化调度顺序
                optimized_tasks = self.optimizer.optimize_schedule(ready_tasks)
                
                for task in optimized_tasks:
                    # 检查熔断器
                    task_type = task.tags[0] if task.tags else "default"
                    if not self.failure_engine.check_circuit_breaker(task_type):
                        continue
                    
                    # 分配节点
                    node_id = self.node_scheduler.assign_task(task)
                    if not node_id:
                        continue  # 没有可用节点，等待下次循环
                    
                    # 执行任务
                    self._execute_task(task, node_id)
                
                time.sleep(0.1)
                
            except Exception as e:
                print(f"[ERROR] 调度循环异常: {e}")
                time.sleep(5)
    
    def _execute_task(self, task: Task, node_id: str):
        """执行任务"""
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        self._emit_event("task_started", {"task": task, "node_id": node_id})
        
        try:
            # 模拟任务执行
            # 实际场景中这里会调用真实的任务执行器
            execution_time = self.optimizer.estimate_execution_time(task.name)
            time.sleep(min(execution_time / 100, 0.5))  # 模拟执行
            
            # 任务成功
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.execution_time = (task.completed_at - task.started_at).total_seconds()
            task.success_count += 1
            
            self.stats["completed_tasks"] += 1
            self.stats["total_execution_time"] += task.execution_time
            
            # 记录成功
            task_type = task.tags[0] if task.tags else "default"
            self.failure_engine.record_circuit_success(task_type)
            
            # 记录执行历史用于优化
            self.optimizer.record_execution(task, True, task.execution_time)
            
            self._emit_event("task_completed", {"task": task, "node_id": node_id})
            
        except Exception as e:
            # 任务失败
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.last_error = str(e)
            task.failure_count += 1
            
            self.stats["failed_tasks"] += 1
            
            # 记录失败
            task_type = task.tags[0] if task.tags else "default"
            self.failure_engine.record_circuit_failure(task_type)
            
            # 失败恢复
            recovery = self.failure_engine.handle_failure(task, str(e))
            
            if recovery["action"] == "retry":
                # 延迟重试
                task.status = TaskStatus.PENDING
                threading.Timer(
                    recovery["delay_seconds"],
                    lambda: self._retry_task(task, node_id)
                ).start()
            
            self._emit_event("task_failed", {
                "task": task,
                "node_id": node_id,
                "error": str(e),
                "recovery": recovery,
            })
        
        finally:
            # 释放节点
            self.node_scheduler.complete_task(task.task_id)
    
    def _retry_task(self, task: Task, node_id: str):
        """重试任务"""
        if task.retry_count < task.max_retries:
            task.status = TaskStatus.PENDING
            self._execute_task(task, node_id)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        uptime = None
        if self.stats["start_time"]:
            uptime = (datetime.now() - self.stats["start_time"]).total_seconds()
        
        return {
            **self.stats,
            "uptime_seconds": uptime,
            "system_load": self.node_scheduler.get_overall_load(),
            "active_nodes": len([n for n in self.node_scheduler.nodes.values() if n.status == "active"]),
            "pending_tasks": len([t for t in self.dependency_graph.tasks.values() if t.status == TaskStatus.PENDING]),
            "running_tasks": len([t for t in self.dependency_graph.tasks.values() if t.status == TaskStatus.RUNNING]),
            "success_rate": self.stats["completed_tasks"] / max(self.stats["total_tasks"] - self.stats["skipped_tasks"], 1),
            "optimizer_analytics": self.optimizer.get_analytics_summary(),
        }
    
    def get_daily_schedule(self) -> List[Dict[str, Any]]:
        """获取当日调度计划"""
        # 基于任务类型和历史数据生成当日最优调度计划
        schedule = []
        
        for task in self.dependency_graph.tasks.values():
            if task.status != TaskStatus.PENDING:
                continue
            
            best_hour = self.optimizer.get_best_execution_time(task.name)
            est_time = self.optimizer.estimate_execution_time(task.name)
            
            schedule.append({
                "task_id": task.task_id,
                "task_name": task.name,
                "priority": task.priority.name,
                "estimated_duration": est_time,
                "best_execution_hour": best_hour,
                "dependencies": task.dependencies,
            })
        
        # 按优先级和最佳时间排序
        schedule.sort(key=lambda x: (
            TaskPriority[x["priority"]].value,
            x["best_execution_hour"] if x["best_execution_hour"] is not None else 99
        ))
        
        return schedule
    
    def generate_execution_report(self) -> Dict[str, Any]:
        """生成执行报告"""
        stats = self.get_stats()
        
        # 按任务类型统计
        type_stats = {}
        for task in self.dependency_graph.tasks.values():
            task_type = task.tags[0] if task.tags else "default"
            if task_type not in type_stats:
                type_stats[task_type] = {"total": 0, "success": 0, "failed": 0}
            type_stats[task_type]["total"] += 1
            if task.status == TaskStatus.COMPLETED:
                type_stats[task_type]["success"] += 1
            elif task.status == TaskStatus.FAILED:
                type_stats[task_type]["failed"] += 1
        
        return {
            "summary": stats,
            "by_type": type_stats,
            "critical_path": self.dependency_graph.get_critical_path(),
            "node_status": self.node_scheduler.get_overall_load(),
            "recommendation": self._generate_recommendations(),
        }
    
    def _generate_recommendations(self) -> List[str]:
        """生成优化建议"""
        recommendations = []
        stats = self.get_stats()
        
        # 负载建议
        if stats["system_load"] > 0.8:
            recommendations.append("系统负载较高，建议增加执行节点或调整任务优先级")
        elif stats["system_load"] < 0.3:
            recommendations.append("系统负载较低，可以合并小任务或增加低优先级任务")
        
        # 成功率建议
        if stats.get("success_rate", 1.0) < 0.8:
            recommendations.append("任务成功率偏低，建议检查失败原因并优化恢复策略")
        
        # 节点建议
        if stats["active_nodes"] < 2:
            recommendations.append("活跃节点较少，建议配置多节点以实现高可用")
        
        if not recommendations:
            recommendations.append("系统运行状态良好，继续保持当前配置")
        
        return recommendations


def main():
    """演示函数"""
    # 创建调度器
    orchestrator = WakeupOrchestrator()
    
    # 添加执行节点
    node1 = ExecutionNode(
        node_id="node_main",
        name="主节点",
        status="active",
        max_concurrent_tasks=5,
        capabilities=["memory", "identity", "attest", "evolution"],
        performance_score=0.9,
    )
    node2 = ExecutionNode(
        node_id="node_backup",
        name="备用节点",
        status="active",
        max_concurrent_tasks=3,
        capabilities=["memory", "identity", "social"],
        performance_score=0.7,
    )
    orchestrator.add_node(node1)
    orchestrator.add_node(node2)
    
    # 注册平台
    orchestrator.platform_adapter.register_platform("local", {"type": "local"})
    orchestrator.platform_adapter.register_platform("cron", {"type": "cron"})
    orchestrator.platform_adapter.set_wakeup_handler("local", lambda t: True)
    orchestrator.platform_adapter.set_wakeup_handler("cron", lambda t: True)
    
    # 创建示例任务
    tasks = [
        Task(
            task_id=f"task_{i:03d}",
            name=f"示例任务{i}",
            description=f"这是第{i}个示例任务",
            priority=TaskPriority.NORMAL if i % 3 != 0 else TaskPriority.HIGH,
            strategy=ScheduleStrategy.ASAP,
            tags=["memory" if i % 2 == 0 else "identity"],
            estimated_duration=30.0 + i * 10,
            max_retries=3,
        )
        for i in range(1, 11)
    ]
    
    # 添加任务依赖
    tasks[1].dependencies = [tasks[0].task_id]
    tasks[2].dependencies = [tasks[0].task_id]
    tasks[5].dependencies = [tasks[1].task_id, tasks[2].task_id]
    
    for task in tasks:
        orchestrator.add_task(task)
    
    # 启动调度器
    print("🚀 唤醒编排引擎 v2.5 启动")
    print(f"📋 任务总数: {orchestrator.stats['total_tasks']}")
    print(f"🔢 执行节点: {len(orchestrator.node_scheduler.nodes)}")
    print()
    
    orchestrator.start()
    
    # 运行一段时间
    time.sleep(3)
    
    # 停止
    orchestrator.stop()
    
    # 输出报告
    report = orchestrator.generate_execution_report()
    print("📊 执行报告:")
    print(f"   总任务数: {report['summary']['total_tasks']}")
    print(f"   完成任务: {report['summary']['completed_tasks']}")
    print(f"   失败任务: {report['summary']['failed_tasks']}")
    print(f"   系统负载: {report['summary']['system_load']:.1%}")
    print(f"   成功率: {report['summary']['success_rate']:.1%}")
    print()
    print("💡 优化建议:")
    for rec in report["recommendation"]:
        print(f"   - {rec}")
    
    print()
    print("✅ 唤醒编排引擎 v2.5 演示完成")


if __name__ == "__main__":
    main()
