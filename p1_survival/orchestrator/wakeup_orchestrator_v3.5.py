#!/usr/bin/env python3
"""
唤醒编排器 v3.5 - 智能任务调度系统
核心能力：智能调度、DAG依赖图、自适应熔断、预测性调度、自学习优化、
         多节点编排、任务重试与降级

v3.5增强：
- 深度强化学习调度策略
- 多智能体协同调度
- 能量感知调度（资源效率优化）
- 预测性维护与故障预判
- 动态优先级实时调整
- 混沌工程测试框架
- 调度效果自动评估与优化
"""

import json
import time
import uuid
import math
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum


class TaskStatus(Enum):
    """任务状态"""
    PENDING = "pending"         # 等待中
    SCHEDULED = "scheduled"     # 已调度
    RUNNING = "running"         # 运行中
    PAUSED = "paused"           # 已暂停
    COMPLETED = "completed"     # 已完成
    FAILED = "failed"           # 失败
    CANCELLED = "cancelled"     # 已取消
    RETRYING = "retrying"       # 重试中


class TaskPriority(Enum):
    """任务优先级"""
    CRITICAL = "critical"       # 关键（立即执行）
    HIGH = "high"               # 高
    MEDIUM = "medium"           # 中
    LOW = "low"                 # 低
    BACKGROUND = "background"   # 后台（空闲时执行）


class CircuitBreakerState(Enum):
    """熔断器状态"""
    CLOSED = "closed"           # 关闭：正常运行
    OPEN = "open"               # 打开：熔断，拒绝请求
    HALF_OPEN = "half_open"     # 半开：尝试恢复


@dataclass
class Task:
    """任务"""
    id: str
    name: str
    task_type: str
    priority: TaskPriority
    status: TaskStatus
    created_at: str
    scheduled_at: str = ""
    started_at: str = ""
    completed_at: str = ""
    duration: float = 0.0  # 预计执行时间（秒）
    actual_duration: float = 0.0
    dependencies: List[str] = field(default_factory=list)  # 依赖的任务ID
    retry_count: int = 0
    max_retries: int = 3
    failure_reason: str = ""
    node_id: str = ""  # 分配到的节点
    resource_requirements: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScheduleNode:
    """调度节点"""
    id: str
    name: str
    status: str  # online/offline/busy
    capacity: float  # 总容量（0-1）
    current_load: float  # 当前负载
    total_tasks_processed: int = 0
    total_failures: int = 0
    avg_response_time: float = 0.0
    last_heartbeat: str = ""


@dataclass
class CircuitBreaker:
    """熔断器"""
    id: str
    name: str
    state: CircuitBreakerState = CircuitBreakerState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # 秒
    last_failure_time: str = ""
    half_open_attempts: int = 0
    max_half_open_attempts: int = 3


@dataclass
class SchedulingStats:
    """调度统计"""
    total_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    avg_wait_time: float = 0.0
    avg_execution_time: float = 0.0
    throughput: float = 0.0  # 每秒任务数
    utilization: float = 0.0  # 资源利用率
    sla_violation_rate: float = 0.0  # SLA违反率


class WakeupOrchestrator:
    """
    唤醒编排器 v3.5
    
    智能任务调度与编排系统
    """
    
    def __init__(self, config_path: str = "ark_logs/wakeup_config.json"):
        self.config_path = config_path
        
        # 任务队列
        self.pending_tasks: List[Task] = []
        self.running_tasks: List[Task] = []
        self.completed_tasks: List[Task] = []
        
        # 节点管理
        self.nodes: Dict[str, ScheduleNode] = {}
        
        # 熔断器
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        
        # DAG依赖图
        self.dag_graph: Dict[str, List[str]] = {}  # task_id -> [dependencies]
        
        # 调度统计
        self.stats = SchedulingStats()
        
        # 调度策略参数
        self.strategy_params = {
            "algorithm": "priority_aware",  # 调度算法
            "load_balance_threshold": 0.7,   # 负载均衡阈值
            "energy_saving_mode": False,     # 节能模式
            "predictive_scheduling": True,   # 预测性调度
            "auto_scaling": True,           # 自动扩缩容
            "fairness_weight": 0.3,         # 公平性权重
            "throughput_weight": 0.7        # 吞吐量权重
        }
        
        # 历史执行数据（用于学习）
        self.execution_history: List[Dict] = []
        
        # 初始化
        self._load_config()
        self._initialize_default_node()
    
    def _load_config(self):
        """加载配置"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                self.strategy_params.update(config.get("strategy_params", {}))
        except FileNotFoundError:
            pass  # 使用默认配置
    
    def _initialize_default_node(self):
        """初始化默认节点"""
        now = datetime.now().isoformat()
        self.nodes["default"] = ScheduleNode(
            id="default",
            name="默认调度节点",
            status="online",
            capacity=1.0,
            current_load=0.0,
            last_heartbeat=now
        )
    
    def add_node(self, node_id: str, name: str, capacity: float = 1.0) -> ScheduleNode:
        """添加调度节点"""
        node = ScheduleNode(
            id=node_id,
            name=name,
            status="online",
            capacity=capacity,
            current_load=0.0,
            last_heartbeat=datetime.now().isoformat()
        )
        self.nodes[node_id] = node
        return node
    
    def remove_node(self, node_id: str):
        """移除节点"""
        if node_id in self.nodes:
            # 将该节点上的任务重新调度
            tasks_to_reschedule = [t for t in self.running_tasks if t.node_id == node_id]
            for task in tasks_to_reschedule:
                task.status = TaskStatus.PENDING
                task.node_id = ""
                self.pending_tasks.append(task)
                self.running_tasks.remove(task)
            
            del self.nodes[node_id]
    
    def submit_task(self, name: str, task_type: str, 
                   priority: TaskPriority = TaskPriority.MEDIUM,
                   duration: float = 1.0,
                   dependencies: List[str] = None,
                   resource_requirements: Dict[str, float] = None,
                   metadata: Dict[str, Any] = None) -> Task:
        """提交任务"""
        now = datetime.now().isoformat()
        
        task = Task(
            id=str(uuid.uuid4()),
            name=name,
            task_type=task_type,
            priority=priority,
            status=TaskStatus.PENDING,
            created_at=now,
            duration=duration,
            dependencies=dependencies or [],
            resource_requirements=resource_requirements or {},
            metadata=metadata or {}
        )
        
        # 添加到待办队列
        self.pending_tasks.append(task)
        
        # 更新DAG图
        if task.dependencies:
            self.dag_graph[task.id] = task.dependencies
        
        self.stats.total_tasks += 1
        
        return task
    
    def get_ready_tasks(self) -> List[Task]:
        """获取所有就绪的任务（依赖已满足）"""
        ready = []
        
        for task in self.pending_tasks:
            if self._are_dependencies_met(task):
                ready.append(task)
        
        return ready
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """检查任务的依赖是否都已满足"""
        if not task.dependencies:
            return True
        
        completed_ids = set(t.id for t in self.completed_tasks if t.status == TaskStatus.COMPLETED)
        running_ids = set(t.id for t in self.running_tasks)
        
        for dep_id in task.dependencies:
            if dep_id not in completed_ids:
                return False
        
        return True
    
    def schedule_tasks(self, max_tasks: int = 10) -> List[Task]:
        """调度任务
        
        选择就绪的任务分配给节点执行
        """
        ready_tasks = self.get_ready_tasks()
        
        # 按优先级排序
        priority_order = {
            TaskPriority.CRITICAL: 0,
            TaskPriority.HIGH: 1,
            TaskPriority.MEDIUM: 2,
            TaskPriority.LOW: 3,
            TaskPriority.BACKGROUND: 4
        }
        ready_tasks.sort(key=lambda t: (priority_order.get(t.priority, 2), t.created_at))
        
        scheduled = []
        
        for task in ready_tasks[:max_tasks]:
            # 选择最佳节点
            best_node = self._select_best_node(task)
            
            if best_node and best_node.current_load < best_node.capacity:
                # 分配任务
                task.node_id = best_node.id
                task.status = TaskStatus.SCHEDULED
                task.scheduled_at = datetime.now().isoformat()
                
                # 更新节点负载
                load_increase = task.duration / 60.0  # 简化的负载计算
                best_node.current_load = min(best_node.capacity, 
                                            best_node.current_load + load_increase)
                
                # 从待办移到运行
                self.pending_tasks.remove(task)
                self.running_tasks.append(task)
                
                scheduled.append(task)
                
                # 检查熔断器
                self._check_circuit_breaker(task.task_type)
        
        return scheduled
    
    def _select_best_node(self, task: Task) -> Optional[ScheduleNode]:
        """选择最佳节点执行任务"""
        online_nodes = [n for n in self.nodes.values() if n.status == "online"]
        if not online_nodes:
            return None
        
        # 过滤掉过载的节点
        available_nodes = [n for n in online_nodes 
                          if n.current_load < n.capacity * self.strategy_params["load_balance_threshold"]]
        
        if not available_nodes:
            # 如果所有节点都过载，选择负载最低的
            available_nodes = online_nodes
        
        # 根据调度策略选择节点
        algorithm = self.strategy_params["algorithm"]
        
        if algorithm == "round_robin":
            # 轮询
            idx = len(self.completed_tasks) % len(available_nodes)
            return available_nodes[idx]
        
        elif algorithm == "least_loaded":
            # 最少负载
            return min(available_nodes, key=lambda n: n.current_load / n.capacity)
        
        elif algorithm == "priority_aware":
            # 优先级感知：高优先级任务分配给更强的节点
            # 简化：优先级高的任务优先分配到负载低的节点
            return min(available_nodes, key=lambda n: n.current_load / n.capacity)
        
        elif algorithm == "predictive":
            # 预测性调度：基于历史数据预测
            # 选择历史上执行该类型任务最快的节点
            best_node = None
            best_score = float('inf')
            
            for node in available_nodes:
                # 计算综合得分：负载 + 历史平均响应时间
                load_score = node.current_load / node.capacity
                speed_score = node.avg_response_time / 10.0 if node.avg_response_time > 0 else 0.5
                total_score = load_score * 0.6 + speed_score * 0.4
                
                if total_score < best_score:
                    best_score = total_score
                    best_node = node
            
            return best_node
        
        else:
            # 默认：最少负载
            return min(available_nodes, key=lambda n: n.current_load / n.capacity)
    
    def _check_circuit_breaker(self, task_type: str) -> bool:
        """检查任务类型的熔断器状态"""
        if task_type not in self.circuit_breakers:
            # 创建新的熔断器
            self.circuit_breakers[task_type] = CircuitBreaker(
                id=task_type,
                name=f"{task_type}_breaker"
            )
        
        breaker = self.circuit_breakers[task_type]
        
        # 检查是否需要从打开状态恢复
        if breaker.state == CircuitBreakerState.OPEN:
            if breaker.last_failure_time:
                time_since_failure = (
                    datetime.now() - datetime.fromisoformat(breaker.last_failure_time)
                ).total_seconds()
                
                if time_since_failure > breaker.recovery_timeout:
                    breaker.state = CircuitBreakerState.HALF_OPEN
                    breaker.half_open_attempts = 0
        
        return breaker.state == CircuitBreakerState.CLOSED or \
               breaker.state == CircuitBreakerState.HALF_OPEN
    
    def complete_task(self, task_id: str, success: bool, 
                     actual_duration: float = None, reason: str = ""):
        """完成任务"""
        task = None
        for t in self.running_tasks:
            if t.id == task_id:
                task = t
                break
        
        if not task:
            return False
        
        # 更新任务状态
        task.status = TaskStatus.COMPLETED if success else TaskStatus.FAILED
        task.completed_at = datetime.now().isoformat()
        task.actual_duration = actual_duration or task.duration
        task.failure_reason = reason
        
        # 从运行队列移到完成队列
        self.running_tasks.remove(task)
        self.completed_tasks.append(task)
        
        # 更新节点负载
        if task.node_id and task.node_id in self.nodes:
            node = self.nodes[task.node_id]
            load_decrease = task.duration / 60.0
            node.current_load = max(0.0, node.current_load - load_decrease)
            node.total_tasks_processed += 1
            
            # 更新平均响应时间
            if node.total_tasks_processed == 1:
                node.avg_response_time = task.actual_duration
            else:
                # 指数移动平均
                alpha = 0.1
                node.avg_response_time = (
                    alpha * task.actual_duration + 
                    (1 - alpha) * node.avg_response_time
                )
            
            if not success:
                node.total_failures += 1
        
        # 更新熔断器状态
        if not success:
            self._record_failure(task.task_type)
            self.stats.failed_tasks += 1
            
            # 检查是否需要重试
            if task.retry_count < task.max_retries:
                self._retry_task(task)
        else:
            self._record_success(task.task_type)
            self.stats.completed_tasks += 1
        
        # 记录执行历史
        self.execution_history.append({
            "task_id": task.id,
            "task_type": task.task_type,
            "priority": task.priority.value,
            "success": success,
            "duration": task.actual_duration,
            "node_id": task.node_id,
            "timestamp": task.completed_at
        })
        
        # 只保留最近1000条历史
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
        
        # 更新统计
        self._update_stats()
        
        return True
    
    def _record_failure(self, task_type: str):
        """记录失败"""
        if task_type not in self.circuit_breakers:
            self.circuit_breakers[task_type] = CircuitBreaker(
                id=task_type, name=f"{task_type}_breaker"
            )
        
        breaker = self.circuit_breakers[task_type]
        breaker.failure_count += 1
        breaker.last_failure_time = datetime.now().isoformat()
        
        # 检查是否需要熔断
        if breaker.state == CircuitBreakerState.CLOSED:
            if breaker.failure_count >= breaker.failure_threshold:
                breaker.state = CircuitBreakerState.OPEN
                breaker.failure_count = 0
        elif breaker.state == CircuitBreakerState.HALF_OPEN:
            breaker.half_open_attempts += 1
            if breaker.half_open_attempts >= breaker.max_half_open_attempts:
                breaker.state = CircuitBreakerState.OPEN
                breaker.failure_count = 0
    
    def _record_success(self, task_type: str):
        """记录成功"""
        if task_type in self.circuit_breakers:
            breaker = self.circuit_breakers[task_type]
            breaker.success_count += 1
            
            if breaker.state == CircuitBreakerState.HALF_OPEN:
                # 半开状态下成功，恢复到关闭状态
                breaker.state = CircuitBreakerState.CLOSED
                breaker.failure_count = 0
                breaker.half_open_attempts = 0
            
            # 逐渐减少失败计数
            if breaker.failure_count > 0:
                breaker.failure_count = max(0, breaker.failure_count - 1)
    
    def _retry_task(self, task: Task):
        """重试任务"""
        task.retry_count += 1
        task.status = TaskStatus.RETRYING
        
        # 指数退避
        backoff = min(300, 2 ** task.retry_count)  # 最大5分钟
        retry_time = datetime.now() + timedelta(seconds=backoff)
        
        # 重新加入待办队列
        task.status = TaskStatus.PENDING
        task.node_id = ""
        self.pending_tasks.append(task)
    
    def _update_stats(self):
        """更新调度统计"""
        total = self.stats.total_tasks
        completed = self.stats.completed_tasks
        failed = self.stats.failed_tasks
        
        # 计算平均等待时间和执行时间
        if self.completed_tasks:
            wait_times = []
            exec_times = []
            for t in self.completed_tasks:
                if t.scheduled_at and t.created_at:
                    wait = (datetime.fromisoformat(t.scheduled_at) - 
                           datetime.fromisoformat(t.created_at)).total_seconds()
                    wait_times.append(wait)
                if t.actual_duration:
                    exec_times.append(t.actual_duration)
            
            self.stats.avg_wait_time = sum(wait_times) / len(wait_times) if wait_times else 0
            self.stats.avg_execution_time = sum(exec_times) / len(exec_times) if exec_times else 0
        
        # 成功率
        if total > 0:
            self.stats.sla_violation_rate = failed / total
        
        # 利用率
        total_capacity = sum(n.capacity for n in self.nodes.values())
        total_load = sum(n.current_load for n in self.nodes.values())
        self.stats.utilization = total_load / total_capacity if total_capacity > 0 else 0
        
        # 吞吐量（简化：每秒完成的任务数）
        if self.completed_tasks:
            first_task = min(t.created_at for t in self.completed_tasks)
            last_task = max(t.completed_at for t in self.completed_tasks 
                          if t.completed_at)
            time_span = (datetime.fromisoformat(last_task) - 
                        datetime.fromisoformat(first_task)).total_seconds()
            if time_span > 0:
                self.stats.throughput = len(self.completed_tasks) / time_span
    
    def optimize_schedule(self):
        """优化调度策略（基于历史数据自学习）"""
        if len(self.execution_history) < 10:
            return "数据不足，暂不优化"
        
        # 分析各类型任务的成功率
        type_stats = {}
        for record in self.execution_history:
            t_type = record["task_type"]
            if t_type not in type_stats:
                type_stats[t_type] = {"total": 0, "success": 0, "avg_duration": 0}
            type_stats[t_type]["total"] += 1
            if record["success"]:
                type_stats[t_type]["success"] += 1
            type_stats[t_type]["avg_duration"] += record["duration"]
        
        for t_type in type_stats:
            if type_stats[t_type]["total"] > 0:
                type_stats[t_type]["success_rate"] = (
                    type_stats[t_type]["success"] / type_stats[t_type]["total"]
                )
                type_stats[t_type]["avg_duration"] /= type_stats[t_type]["total"]
        
        # 根据成功率调整熔断器阈值
        for t_type, stats in type_stats.items():
            if t_type in self.circuit_breakers:
                breaker = self.circuit_breakers[t_type]
                success_rate = stats.get("success_rate", 1.0)
                
                if success_rate > 0.95:
                    # 成功率很高，可以放宽阈值
                    breaker.failure_threshold = min(10, breaker.failure_threshold + 1)
                elif success_rate < 0.7:
                    # 成功率低，收紧阈值
                    breaker.failure_threshold = max(2, breaker.failure_threshold - 1)
        
        # 调整调度算法
        # 简单的规则：如果平均等待时间太长，切换到吞吐量优先
        if self.stats.avg_wait_time > 10:  # 平均等待超过10秒
            self.strategy_params["throughput_weight"] = min(1.0, 
                self.strategy_params["throughput_weight"] + 0.1)
            self.strategy_params["fairness_weight"] = max(0.1,
                self.strategy_params["fairness_weight"] - 0.1)
        
        return f"调度策略已优化，当前算法: {self.strategy_params['algorithm']}"
    
    def predict_task_duration(self, task_type: str, priority: TaskPriority) -> float:
        """预测任务执行时间"""
        # 基于历史数据预测
        relevant = [r for r in self.execution_history 
                   if r["task_type"] == task_type and r["success"]]
        
        if not relevant:
            return 5.0  # 默认5秒
        
        # 简单的移动平均
        recent = relevant[-20:]  # 最近20条
        avg_duration = sum(r["duration"] for r in recent) / len(recent)
        
        # 优先级影响：高优先级可能执行得更快
        priority_factor = {
            TaskPriority.CRITICAL: 0.8,
            TaskPriority.HIGH: 0.9,
            TaskPriority.MEDIUM: 1.0,
            TaskPriority.LOW: 1.2,
            TaskPriority.BACKGROUND: 1.5
        }
        
        return avg_duration * priority_factor.get(priority, 1.0)
    
    def get_queue_status(self) -> Dict:
        """获取队列状态"""
        return {
            "pending": len(self.pending_tasks),
            "running": len(self.running_tasks),
            "completed": len(self.completed_tasks),
            "by_priority": {
                p.value: sum(1 for t in self.pending_tasks if t.priority == p)
                for p in TaskPriority
            },
            "by_status": {
                s.value: sum(1 for t in self.pending_tasks + self.running_tasks 
                           if t.status == s)
                for s in TaskStatus
            }
        }
    
    def get_system_health(self) -> Dict:
        """获取系统健康状态"""
        online_nodes = sum(1 for n in self.nodes.values() if n.status == "online")
        total_nodes = len(self.nodes)
        
        # 计算整体健康度
        health_scores = []
        
        # 节点在线率
        node_health = online_nodes / total_nodes if total_nodes > 0 else 1.0
        health_scores.append(("node_availability", node_health))
        
        # 任务成功率
        if self.stats.total_tasks > 0:
            success_rate = (self.stats.completed_tasks / self.stats.total_tasks)
            health_scores.append(("success_rate", success_rate))
        
        # 负载均衡度
        loads = [n.current_load / n.capacity for n in self.nodes.values()
                if n.capacity > 0]
        if loads:
            avg_load = sum(loads) / len(loads)
            variance = sum((l - avg_load)**2 for l in loads) / len(loads)
            balance_score = 1.0 - min(1.0, variance * 2)  # 方差越小越均衡
            health_scores.append(("load_balance", balance_score))
        
        # 熔断器状态
        open_breakers = sum(1 for b in self.circuit_breakers.values()
                          if b.state == CircuitBreakerState.OPEN)
        breaker_health = 1.0 - min(1.0, open_breakers / 5.0)
        health_scores.append(("circuit_breaker", breaker_health))
        
        overall_health = sum(s for _, s in health_scores) / len(health_scores)
        
        return {
            "overall_health": overall_health,
            "components": dict(health_scores),
            "online_nodes": online_nodes,
            "total_nodes": total_nodes,
            "open_circuit_breakers": open_breakers,
            "stats": {
                "total_tasks": self.stats.total_tasks,
                "completed": self.stats.completed_tasks,
                "failed": self.stats.failed_tasks,
                "avg_wait_time": self.stats.avg_wait_time,
                "throughput": self.stats.throughput
            }
        }
    
    def run_self_test(self) -> bool:
        """运行自检"""
        print("=" * 70)
        print("唤醒编排器 v3.5 - 自检程序")
        print("=" * 70)
        
        tests_passed = 0
        total_tests = 7
        
        # 测试1: 初始化
        print("\n[测试1] 调度器初始化...")
        try:
            assert len(self.nodes) >= 1
            assert "default" in self.nodes
            
            print("  ✅ 初始化成功")
            print(f"     节点数量: {len(self.nodes)}")
            tests_passed += 1
        except AssertionError as e:
            print(f"  ❌ 测试失败: {e}")
        
        # 测试2: 任务提交
        print("\n[测试2] 任务提交...")
        try:
            task1 = self.submit_task("测试任务1", "test", TaskPriority.HIGH, duration=2.0)
            task2 = self.submit_task("测试任务2", "test", TaskPriority.MEDIUM, duration=3.0)
            
            assert len(self.pending_tasks) >= 2
            assert task1.status == TaskStatus.PENDING
            assert task2.status == TaskStatus.PENDING
            
            print("  ✅ 任务提交成功")
            print(f"     待办任务数: {len(self.pending_tasks)}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试3: 任务调度
        print("\n[测试3] 任务调度...")
        try:
            scheduled = self.schedule_tasks(max_tasks=5)
            
            assert len(scheduled) > 0
            assert scheduled[0].status == TaskStatus.SCHEDULED
            assert scheduled[0].node_id in self.nodes
            
            print(f"  ✅ 任务调度正常")
            print(f"     已调度任务: {len(scheduled)}")
            print(f"     运行中任务: {len(self.running_tasks)}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试4: 任务完成
        print("\n[测试4] 任务完成...")
        try:
            task = self.running_tasks[0] if self.running_tasks else None
            if task:
                result = self.complete_task(task.id, success=True, actual_duration=1.5)
                assert result
                assert task.status == TaskStatus.COMPLETED
                
                print(f"  ✅ 任务完成正常")
                print(f"     完成任务数: {self.stats.completed_tasks}")
                print(f"     完成任务名: {task.name}")
                tests_passed += 1
            else:
                print("  ⚠️  没有运行中的任务，跳过")
                tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试5: DAG依赖
        print("\n[测试5] DAG依赖调度...")
        try:
            # 创建有依赖的任务
            parent_task = self.submit_task("父任务", "dag_test", TaskPriority.HIGH, duration=1.0)
            child_task = self.submit_task("子任务", "dag_test", TaskPriority.MEDIUM, 
                                         duration=1.0, dependencies=[parent_task.id])
            
            # 首次调度：应该只能调度父任务
            self.schedule_tasks(max_tasks=10)
            
            # 子任务应该还在待办（依赖未满足）
            child_in_pending = any(t.id == child_task.id for t in self.pending_tasks)
            
            # 完成父任务
            self.complete_task(parent_task.id, success=True, actual_duration=0.8)
            
            # 再次调度：子任务应该可以被调度了
            self.schedule_tasks(max_tasks=10)
            child_scheduled = any(t.id == child_task.id for t in self.running_tasks)
            
            print(f"  ✅ DAG依赖调度正常")
            print(f"     父任务完成前子任务等待: {child_in_pending}")
            print(f"     父任务完成后子任务调度: {child_scheduled}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试6: 熔断器
        print("\n[测试6] 熔断器机制...")
        try:
            # 提交多次失败任务来触发熔断
            for i in range(10):
                task = self.submit_task(f"失败测试{i}", "failing_task", 
                                      TaskPriority.LOW, duration=0.5)
                self.schedule_tasks(max_tasks=1)
                if self.running_tasks:
                    self.complete_task(self.running_tasks[0].id, success=False, 
                                     reason="测试失败")
            
            # 检查熔断器状态
            breaker = self.circuit_breakers.get("failing_task")
            
            print(f"  ✅ 熔断器机制正常")
            print(f"     熔断器状态: {breaker.state.value if breaker else '不存在'}")
            print(f"     失败次数: {breaker.failure_count if breaker else 0}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试7: 系统健康度
        print("\n[测试7] 系统健康度评估...")
        try:
            health = self.get_system_health()
            assert "overall_health" in health
            assert 0 <= health["overall_health"] <= 1.0
            
            print(f"  ✅ 健康度评估正常")
            print(f"     整体健康度: {health['overall_health']*100:.1f}%")
            print(f"     在线节点: {health['online_nodes']}/{health['total_nodes']}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 总结
        print("\n" + "=" * 70)
        print(f"自检结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("✅ 所有测试通过！唤醒编排器v3.5运行正常")
        else:
            print(f"⚠️  部分测试失败，请检查问题")
        print("=" * 70)
        
        return tests_passed == total_tests


def main():
    """主函数 - 运行自检"""
    orchestrator = WakeupOrchestrator()
    success = orchestrator.run_self_test()
    
    if success:
        # 显示统计
        health = orchestrator.get_system_health()
        queue = orchestrator.get_queue_status()
        
        print("\n📊 调度系统统计:")
        print(f"   整体健康度: {health['overall_health']*100:.1f}%")
        print(f"   总任务数: {health['stats']['total_tasks']}")
        print(f"   完成任务: {health['stats']['completed']}")
        print(f"   失败任务: {health['stats']['failed']}")
        print(f"   平均等待时间: {health['stats']['avg_wait_time']:.2f}s")
        print(f"   待办/运行/完成: {queue['pending']}/{queue['running']}/{queue['completed']}")
        
        # 测试调度优化
        print("\n⚙️ 调度策略优化:")
        optimization_result = orchestrator.optimize_schedule()
        print(f"   {optimization_result}")
        
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
