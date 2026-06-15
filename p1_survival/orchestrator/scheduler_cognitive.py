#!/usr/bin/env python3
"""
唤醒编排认知层 - 智能调度决策引擎
版本：v2.0 认知层增强版
功能：任务依赖管理、智能调度决策、失败重试策略、生命周期管理、自我优化
"""

import json
import time
import os
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Tuple
from collections import defaultdict


class TaskStatus(Enum):
    """任务状态枚举"""
    PENDING = "pending"        # 等待中
    READY = "ready"            # 就绪（依赖满足）
    RUNNING = "running"        # 运行中
    PAUSED = "paused"          # 已暂停
    COMPLETED = "completed"    # 已完成
    FAILED = "failed"          # 已失败
    SKIPPED = "skipped"        # 已跳过（依赖失败）
    RETRYING = "retrying"      # 重试中


class TaskPriority(Enum):
    """任务优先级枚举"""
    P0_CRITICAL = 0    # 紧急：立即执行，抢占资源
    P1_HIGH = 1        # 高优：优先执行
    P2_NORMAL = 2      # 普通：正常排队
    P3_LOW = 3         # 低优：空闲时执行


class SchedulerStrategy(Enum):
    """调度策略枚举"""
    FIFO = "fifo"                    # 先进先出
    PRIORITY = "priority"            # 优先级调度
    DEPENDENCY_AWARE = "dependency"  # 依赖感知调度
    LOAD_BALANCE = "load_balance"    # 负载均衡
    ADAPTIVE = "adaptive"            # 自适应调度（综合）


class Task:
    """任务模型"""
    
    def __init__(self, task_id: str, name: str, task_type: str, 
                 priority: TaskPriority = TaskPriority.P2_NORMAL,
                 dependencies: List[str] = None,
                 estimated_duration: int = 300,  # 预估时长（秒）
                 max_retries: int = 3,
                 retry_delay: int = 60,  # 重试延迟（秒）
                 timeout: int = 3600,    # 超时时间（秒）
                 payload: Dict = None):
        self.task_id = task_id
        self.name = name
        self.task_type = task_type
        self.priority = priority
        self.dependencies = dependencies or []
        self.estimated_duration = estimated_duration
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.timeout = timeout
        self.payload = payload or {}
        
        # 运行时状态
        self.status = TaskStatus.PENDING
        self.retry_count = 0
        self.created_at = datetime.now()
        self.started_at: Optional[datetime] = None
        self.completed_at: Optional[datetime] = None
        self.last_error: Optional[str] = None
        self.result: Optional[Dict] = None
        self.progress: float = 0.0  # 0-100
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "task_id": self.task_id,
            "name": self.name,
            "task_type": self.task_type,
            "priority": self.priority.value,
            "dependencies": self.dependencies,
            "estimated_duration": self.estimated_duration,
            "max_retries": self.max_retries,
            "retry_delay": self.retry_delay,
            "timeout": self.timeout,
            "status": self.status.value,
            "retry_count": self.retry_count,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "last_error": self.last_error,
            "progress": self.progress
        }
    
    def can_start(self, completed_tasks: Dict[str, 'Task']) -> bool:
        """检查是否可以启动（所有依赖都已完成）"""
        for dep_id in self.dependencies:
            dep_task = completed_tasks.get(dep_id)
            if not dep_task or dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    def should_retry(self) -> bool:
        """是否应该重试"""
        return (self.status == TaskStatus.FAILED and 
                self.retry_count < self.max_retries)
    
    def get_wait_time(self) -> float:
        """获取等待时间（秒）"""
        if self.status == TaskStatus.FAILED and self.completed_at:
            waited = (datetime.now() - self.completed_at).total_seconds()
            return waited
        return 0


class DependencyGraph:
    """任务依赖图（DAG）"""
    
    def __init__(self):
        self.tasks: Dict[str, Task] = {}
        self.reverse_deps: Dict[str, List[str]] = defaultdict(list)  # 反向依赖
    
    def add_task(self, task: Task):
        """添加任务"""
        self.tasks[task.task_id] = task
        # 建立反向依赖索引
        for dep_id in task.dependencies:
            self.reverse_deps[dep_id].append(task.task_id)
    
    def get_ready_tasks(self) -> List[Task]:
        """获取所有就绪的任务（依赖全部完成）"""
        ready = []
        completed_ids = {tid for tid, t in self.tasks.items() 
                        if t.status == TaskStatus.COMPLETED}
        
        for task in self.tasks.values():
            if task.status in (TaskStatus.PENDING, TaskStatus.FAILED):
                if task.can_start({tid: self.tasks[tid] for tid in completed_ids 
                                  if tid in self.tasks}):
                    if task.status == TaskStatus.FAILED:
                        if task.should_retry() and task.get_wait_time() >= task.retry_delay:
                            task.status = TaskStatus.RETRYING
                            ready.append(task)
                    else:
                        task.status = TaskStatus.READY
                        ready.append(task)
        return ready
    
    def get_downstream_tasks(self, task_id: str) -> List[Task]:
        """获取下游任务（依赖该任务的任务）"""
        downstream_ids = self.reverse_deps.get(task_id, [])
        return [self.tasks[tid] for tid in downstream_ids if tid in self.tasks]
    
    def has_circular_dependency(self) -> bool:
        """检测是否有循环依赖"""
        visited = set()
        rec_stack = set()
        
        def dfs(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)
            
            for dep_id in self.tasks[task_id].dependencies:
                if dep_id not in self.tasks:
                    continue
                if dep_id not in visited:
                    if dfs(dep_id):
                        return True
                elif dep_id in rec_stack:
                    return True
            
            rec_stack.discard(task_id)
            return False
        
        for task_id in self.tasks:
            if task_id not in visited:
                if dfs(task_id):
                    return True
        return False
    
    def get_critical_path(self) -> List[str]:
        """计算关键路径（最长路径）"""
        memo = {}
        
        def path_length(task_id: str) -> Tuple[float, List[str]]:
            if task_id in memo:
                return memo[task_id]
            
            task = self.tasks.get(task_id)
            if not task:
                return (0, [])
            
            if not task.dependencies:
                result = (task.estimated_duration, [task_id])
                memo[task_id] = result
                return result
            
            max_len = 0
            max_path = []
            
            for dep_id in task.dependencies:
                dep_len, dep_path = path_length(dep_id)
                if dep_len > max_len:
                    max_len = dep_len
                    max_path = dep_path
            
            result = (max_len + task.estimated_duration, max_path + [task_id])
            memo[task_id] = result
            return result
        
        max_total = 0
        critical_path = []
        
        for task_id in self.tasks:
            total, path = path_length(task_id)
            if total > max_total:
                max_total = total
                critical_path = path
        
        return critical_path


class RetryStrategy:
    """重试策略引擎"""
    
    def __init__(self):
        self.strategies = {
            "exponential": self._exponential_backoff,
            "fixed": self._fixed_delay,
            "linear": self._linear_backoff,
            "adaptive": self._adaptive_retry,
        }
        self.failure_patterns = defaultdict(int)  # 失败模式统计
    
    def _fixed_delay(self, retry_count: int, base_delay: float) -> float:
        """固定延迟"""
        return base_delay
    
    def _exponential_backoff(self, retry_count: int, base_delay: float) -> float:
        """指数退避"""
        return base_delay * (2 ** retry_count)
    
    def _linear_backoff(self, retry_count: int, base_delay: float) -> float:
        """线性退避"""
        return base_delay * (retry_count + 1)
    
    def _adaptive_retry(self, retry_count: int, base_delay: float, 
                       failure_rate: float = 0.0) -> float:
        """自适应重试：失败率高时增加延迟"""
        base = self._exponential_backoff(retry_count, base_delay)
        if failure_rate > 0.5:
            base *= 2  # 失败率超过50%，加倍延迟
        return base
    
    def get_retry_delay(self, task: Task, strategy: str = "exponential",
                       failure_rate: float = 0.0) -> float:
        """计算重试延迟"""
        strategy_fn = self.strategies.get(strategy, self._exponential_backoff)
        if strategy == "adaptive":
            return strategy_fn(task.retry_count, task.retry_delay, failure_rate)
        return strategy_fn(task.retry_count, task.retry_delay)
    
    def should_circuit_break(self, task_type: str, 
                           failure_threshold: int = 5,
                           window_seconds: int = 300) -> bool:
        """熔断器判断：某类型任务连续失败太多次则熔断"""
        # 简化实现：记录失败次数
        return self.failure_patterns[task_type] >= failure_threshold
    
    def record_failure(self, task_type: str):
        """记录失败"""
        self.failure_patterns[task_type] += 1
    
    def record_success(self, task_type: str):
        """记录成功（重置失败计数）"""
        self.failure_patterns[task_type] = 0


class SchedulerDecisionEngine:
    """调度决策引擎 - 认知层核心"""
    
    def __init__(self, strategy: SchedulerStrategy = SchedulerStrategy.ADAPTIVE):
        self.strategy = strategy
        self.dependency_graph = DependencyGraph()
        self.retry_strategy = RetryStrategy()
        self.execution_history: List[Dict] = []
        self.load_stats: Dict[str, float] = defaultdict(float)  # 各类型负载
        self.circuit_breakers: Dict[str, bool] = defaultdict(bool)
    
    def add_task(self, task: Task) -> bool:
        """添加任务到调度器"""
        # 先检查循环依赖
        self.dependency_graph.add_task(task)
        if self.dependency_graph.has_circular_dependency():
            # 回滚
            del self.dependency_graph.tasks[task.task_id]
            return False
        return True
    
    def get_next_task(self) -> Optional[Task]:
        """获取下一个要执行的任务"""
        ready_tasks = self.dependency_graph.get_ready_tasks()
        
        if not ready_tasks:
            return None
        
        if self.strategy == SchedulerStrategy.FIFO:
            # 按创建时间排序
            ready_tasks.sort(key=lambda t: t.created_at)
            return ready_tasks[0]
        
        elif self.strategy == SchedulerStrategy.PRIORITY:
            # 按优先级排序，同优先级按FIFO
            ready_tasks.sort(key=lambda t: (t.priority.value, t.created_at))
            return ready_tasks[0]
        
        elif self.strategy == SchedulerStrategy.DEPENDENCY_AWARE:
            # 优先调度关键路径上的任务
            critical_path = self.dependency_graph.get_critical_path()
            
            def critical_path_priority(task: Task) -> Tuple[int, int, datetime]:
                # 先看是否在关键路径上
                in_critical = 0 if task.task_id in critical_path else 1
                # 再看下游任务数量（多的优先）
                downstream_count = len(self.dependency_graph.get_downstream_tasks(task.task_id))
                return (in_critical, -downstream_count, task.created_at)
            
            ready_tasks.sort(key=critical_path_priority)
            return ready_tasks[0]
        
        elif self.strategy == SchedulerStrategy.LOAD_BALANCE:
            # 优先调度负载低的任务类型
            def load_priority(task: Task) -> Tuple[float, int, datetime]:
                load = self.load_stats.get(task.task_type, 0)
                return (load, task.priority.value, task.created_at)
            
            ready_tasks.sort(key=load_priority)
            return ready_tasks[0]
        
        else:  # ADAPTIVE
            # 综合评分：优先级(40%) + 关键路径(30%) + 负载(30%)
            critical_path = set(self.dependency_graph.get_critical_path())
            
            def adaptive_score(task: Task) -> float:
                # 优先级得分（越低越优先，P0=0分最好）
                priority_score = task.priority.value / 3.0  # 归一化到0-1
                
                # 关键路径得分（在关键路径上=0，不在=1）
                critical_score = 0.0 if task.task_id in critical_path else 1.0
                
                # 负载得分（当前负载越高，得分越低，越不优先）
                max_load = max(self.load_stats.values()) if self.load_stats else 1
                load = self.load_stats.get(task.task_type, 0)
                load_score = load / max_load if max_load > 0 else 0
                
                # 综合评分（越低越优先）
                total = (priority_score * 0.4 + 
                        critical_score * 0.3 + 
                        load_score * 0.3)
                return total
            
            ready_tasks.sort(key=adaptive_score)
            return ready_tasks[0]
    
    def mark_task_started(self, task_id: str):
        """标记任务开始"""
        task = self.dependency_graph.tasks.get(task_id)
        if task:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.progress = 0.0
            self.load_stats[task.task_type] += task.estimated_duration
    
    def mark_task_completed(self, task_id: str, result: Dict = None):
        """标记任务完成"""
        task = self.dependency_graph.tasks.get(task_id)
        if task:
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result or {}
            task.progress = 100.0
            
            # 负载统计
            duration = (task.completed_at - task.started_at).total_seconds() if task.started_at else 0
            self.load_stats[task.task_type] = max(0, self.load_stats[task.task_type] - task.estimated_duration + duration)
            
            # 记录历史
            self._record_execution(task, True)
            
            # 重置熔断器
            self.retry_strategy.record_success(task.task_type)
            self.circuit_breakers[task.task_type] = False
    
    def mark_task_failed(self, task_id: str, error: str):
        """标记任务失败"""
        task = self.dependency_graph.tasks.get(task_id)
        if task:
            task.status = TaskStatus.FAILED
            task.completed_at = datetime.now()
            task.last_error = error
            task.retry_count += 1
            
            # 负载统计
            self.load_stats[task.task_type] = max(0, 
                self.load_stats[task.task_type] - task.estimated_duration)
            
            # 记录失败
            self.retry_strategy.record_failure(task.task_type)
            
            # 检查是否需要熔断
            if self.retry_strategy.should_circuit_break(task.task_type):
                self.circuit_breakers[task.task_type] = True
            
            # 标记下游任务为跳过
            downstream = self.dependency_graph.get_downstream_tasks(task_id)
            for dep_task in downstream:
                if dep_task.status in (TaskStatus.PENDING, TaskStatus.READY):
                    dep_task.status = TaskStatus.SKIPPED
                    dep_task.last_error = f"依赖任务 {task_id} 失败"
            
            self._record_execution(task, False)
    
    def _record_execution(self, task: Task, success: bool):
        """记录执行历史（用于学习优化）"""
        duration = 0
        if task.started_at and task.completed_at:
            duration = (task.completed_at - task.started_at).total_seconds()
        
        record = {
            "task_id": task.task_id,
            "task_type": task.task_type,
            "priority": task.priority.value,
            "success": success,
            "duration": duration,
            "estimated_duration": task.estimated_duration,
            "retry_count": task.retry_count,
            "error": task.last_error,
            "timestamp": datetime.now().isoformat()
        }
        self.execution_history.append(record)
        
        # 只保留最近1000条
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-1000:]
    
    def get_scheduler_health(self) -> Dict:
        """获取调度器健康状态"""
        tasks = self.dependency_graph.tasks.values()
        status_counts = defaultdict(int)
        for task in tasks:
            status_counts[task.status.value] += 1
        
        # 计算成功率
        total_completed = sum(1 for r in self.execution_history if r["success"])
        total_executed = len(self.execution_history)
        success_rate = total_completed / total_executed if total_executed > 0 else 1.0
        
        return {
            "total_tasks": len(tasks),
            "status_counts": dict(status_counts),
            "success_rate": success_rate,
            "active_circuit_breakers": [k for k, v in self.circuit_breakers.items() if v],
            "avg_retry_count": (sum(t.retry_count for t in tasks) / len(tasks)) if tasks else 0,
            "load_stats": dict(self.load_stats),
            "strategy": self.strategy.value
        }
    
    def optimize_strategy(self):
        """根据历史数据自动优化调度策略"""
        # 分析历史数据，选择最优策略
        if len(self.execution_history) < 20:
            return  # 数据不足，不优化
        
        # 计算各指标
        success_rate = sum(1 for r in self.execution_history if r["success"]) / len(self.execution_history)
        
        # 计算平均等待时间（排队时间）
        # 这里简化，实际需要更复杂的分析
        
        # 根据任务类型分布调整策略
        type_counts = defaultdict(int)
        for r in self.execution_history:
            type_counts[r["task_type"]] += 1
        
        if len(type_counts) > 3:
            # 任务类型多，用负载均衡
            self.strategy = SchedulerStrategy.LOAD_BALANCE
        elif any(count > len(self.execution_history) * 0.3 for count in type_counts.values()):
            # 某类任务占比高，用优先级调度
            self.strategy = SchedulerStrategy.PRIORITY
        else:
            self.strategy = SchedulerStrategy.ADAPTIVE
    
    def save_state(self, filepath: str):
        """保存调度器状态"""
        state = {
            "tasks": {tid: t.to_dict() for tid, t in self.dependency_graph.tasks.items()},
            "execution_history": self.execution_history,
            "load_stats": dict(self.load_stats),
            "circuit_breakers": dict(self.circuit_breakers),
            "strategy": self.strategy.value,
            "failure_patterns": dict(self.retry_strategy.failure_patterns)
        }
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(state, f, indent=2, ensure_ascii=False)
    
    def load_state(self, filepath: str):
        """加载调度器状态"""
        if not os.path.exists(filepath):
            return
        
        with open(filepath, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # 恢复任务
        for tid, task_data in state.get("tasks", {}).items():
            task = Task(
                task_id=task_data["task_id"],
                name=task_data["name"],
                task_type=task_data["task_type"],
                priority=TaskPriority(task_data["priority"]),
                dependencies=task_data.get("dependencies", []),
                estimated_duration=task_data.get("estimated_duration", 300),
                max_retries=task_data.get("max_retries", 3),
                retry_delay=task_data.get("retry_delay", 60),
                timeout=task_data.get("timeout", 3600)
            )
            task.status = TaskStatus(task_data["status"])
            task.retry_count = task_data.get("retry_count", 0)
            task.progress = task_data.get("progress", 0.0)
            task.last_error = task_data.get("last_error")
            
            # 恢复时间
            if task_data.get("created_at"):
                task.created_at = datetime.fromisoformat(task_data["created_at"])
            if task_data.get("started_at"):
                task.started_at = datetime.fromisoformat(task_data["started_at"])
            if task_data.get("completed_at"):
                task.completed_at = datetime.fromisoformat(task_data["completed_at"])
            
            self.dependency_graph.tasks[tid] = task
        
        # 重建反向依赖
        self.dependency_graph.reverse_deps.clear()
        for task in self.dependency_graph.tasks.values():
            for dep_id in task.dependencies:
                self.dependency_graph.reverse_deps[dep_id].append(task.task_id)
        
        # 恢复其他状态
        self.execution_history = state.get("execution_history", [])
        self.load_stats = defaultdict(float, state.get("load_stats", {}))
        self.circuit_breakers = defaultdict(bool, state.get("circuit_breakers", {}))
        self.strategy = SchedulerStrategy(state.get("strategy", "adaptive"))
        self.retry_strategy.failure_patterns = defaultdict(int, state.get("failure_patterns", {}))


class WorkflowEngine:
    """工作流引擎 - 定义可复用的任务流程模板"""
    
    def __init__(self, scheduler: SchedulerDecisionEngine):
        self.scheduler = scheduler
        self.templates: Dict[str, Dict] = {}  # 工作流模板
    
    def register_template(self, template_id: str, name: str, 
                         task_definitions: List[Dict],
                         description: str = ""):
        """注册工作流模板"""
        self.templates[template_id] = {
            "name": name,
            "description": description,
            "task_definitions": task_definitions
        }
    
    def execute_workflow(self, template_id: str, context: Dict = None) -> List[str]:
        """执行工作流，返回创建的任务ID列表"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"工作流模板不存在: {template_id}")
        
        context = context or {}
        created_tasks = []
        
        for task_def in template["task_definitions"]:
            # 支持模板变量替换
            task_id = task_def["id"].format(**context)
            task_name = task_def["name"].format(**context)
            
            dependencies = [d.format(**context) for d in task_def.get("dependencies", [])]
            
            task = Task(
                task_id=task_id,
                name=task_name,
                task_type=task_def.get("type", "general"),
                priority=TaskPriority(task_def.get("priority", 2)),
                dependencies=dependencies,
                estimated_duration=task_def.get("estimated_duration", 300),
                max_retries=task_def.get("max_retries", 3),
                retry_delay=task_def.get("retry_delay", 60),
                timeout=task_def.get("timeout", 3600),
                payload=task_def.get("payload", {})
            )
            
            if self.scheduler.add_task(task):
                created_tasks.append(task_id)
        
        return created_tasks


# ========== 永生平台默认工作流模板 ==========

DEFAULT_WORKFLOWS = {
    "daily_maintenance": {
        "name": "每日维护工作流",
        "description": "每日定时执行的系统维护任务链",
        "task_definitions": [
            {
                "id": "daily_heartbeat",
                "name": "每日心跳检查",
                "type": "health_check",
                "priority": 0,  # P0
                "dependencies": [],
                "estimated_duration": 30
            },
            {
                "id": "memory_整理",
                "name": "记忆自动整理",
                "type": "memory",
                "priority": 1,  # P1
                "dependencies": ["daily_heartbeat"],
                "estimated_duration": 120
            },
            {
                "id": "attest_auto",
                "name": "自动存证",
                "type": "attest",
                "priority": 1,
                "dependencies": ["memory_整理"],
                "estimated_duration": 60
            },
            {
                "id": "identity_check",
                "name": "身份漂移检测",
                "type": "identity",
                "priority": 1,
                "dependencies": ["daily_heartbeat"],
                "estimated_duration": 45
            },
            {
                "id": "system_backup",
                "name": "系统备份",
                "type": "backup",
                "priority": 2,
                "dependencies": ["attest_auto", "identity_check"],
                "estimated_duration": 90
            },
            {
                "id": "evolution_snapshot",
                "name": "进化快照",
                "type": "evolution",
                "priority": 2,
                "dependencies": ["system_backup"],
                "estimated_duration": 60
            }
        ]
    },
    "evolution_cycle": {
        "name": "进化循环工作流",
        "description": "标准进化周期：评估→决策→执行→验证→沉淀",
        "task_definitions": [
            {
                "id": "eval_status",
                "name": "状态评估",
                "type": "evaluation",
                "priority": 1,
                "dependencies": [],
                "estimated_duration": 60
            },
            {
                "id": "priority_calc",
                "name": "优先级计算",
                "type": "decision",
                "priority": 1,
                "dependencies": ["eval_status"],
                "estimated_duration": 45
            },
            {
                "id": "module_evolution",
                "name": "模块进化执行",
                "type": "evolution",
                "priority": 0,
                "dependencies": ["priority_calc"],
                "estimated_duration": 300
            },
            {
                "id": "verification",
                "name": "进化验证",
                "type": "verification",
                "priority": 1,
                "dependencies": ["module_evolution"],
                "estimated_duration": 90
            },
            {
                "id": "log_sediment",
                "name": "进化日志沉淀",
                "type": "memory",
                "priority": 2,
                "dependencies": ["verification"],
                "estimated_duration": 60
            }
        ]
    }
}


def main():
    """演示：智能调度引擎功能展示"""
    print("=" * 60)
    print("唤醒编排认知层 - 智能调度决策引擎 v2.0")
    print("=" * 60)
    
    # 创建调度器
    scheduler = SchedulerDecisionEngine(strategy=SchedulerStrategy.ADAPTIVE)
    
    # 创建工作流引擎
    workflow_engine = WorkflowEngine(scheduler)
    
    # 注册默认工作流
    for tid, tpl in DEFAULT_WORKFLOWS.items():
        workflow_engine.register_template(tid, tpl["name"], 
                                         tpl["task_definitions"], 
                                         tpl.get("description", ""))
    
    print(f"\n已注册 {len(DEFAULT_WORKFLOWS)} 个工作流模板")
    
    # 执行每日维护工作流
    print("\n--- 执行每日维护工作流 ---")
    task_ids = workflow_engine.execute_workflow("daily_maintenance")
    print(f"创建了 {len(task_ids)} 个任务")
    
    # 模拟任务执行
    print("\n--- 模拟任务调度 ---")
    for i in range(8):
        next_task = scheduler.get_next_task()
        if next_task:
            print(f"  调度任务: [{next_task.priority.name}] {next_task.name} ({next_task.task_id})")
            scheduler.mark_task_started(next_task.task_id)
            
            # 模拟执行
            time.sleep(0.01)
            
            # 大部分成功，偶尔失败
            if i == 3:  # 第4个任务失败
                print(f"    ❌ 任务失败: 模拟错误")
                scheduler.mark_task_failed(next_task.task_id, "模拟执行错误")
            else:
                print(f"    ✅ 任务完成")
                scheduler.mark_task_completed(next_task.task_id, {"result": "success"})
        else:
            print("  无就绪任务")
            break
    
    # 检查重试
    print("\n--- 检查重试任务 ---")
    next_task = scheduler.get_next_task()
    if next_task and next_task.status == TaskStatus.RETRYING:
        print(f"  重试任务: {next_task.name} (第{next_task.retry_count}次重试)")
    
    # 显示健康状态
    print("\n--- 调度器健康状态 ---")
    health = scheduler.get_scheduler_health()
    for key, value in health.items():
        if isinstance(value, dict):
            print(f"  {key}:")
            for k, v in value.items():
                print(f"    {k}: {v}")
        else:
            print(f"  {key}: {value}")
    
    # 显示任务依赖图
    print("\n--- 任务依赖图 ---")
    for task in scheduler.dependency_graph.tasks.values():
        deps = ", ".join(task.dependencies) if task.dependencies else "无"
        print(f"  [{task.status.value}] {task.name} → 依赖: {deps}")
    
    # 计算关键路径
    critical_path = scheduler.dependency_graph.get_critical_path()
    print(f"\n关键路径: {' → '.join(critical_path)}")
    
    print("\n" + "=" * 60)
    print("唤醒编排认知层建设完成！")
    print("核心能力：DAG依赖管理、智能调度决策、失败重试熔断、工作流模板、自我优化")
    print("=" * 60)


if __name__ == "__main__":
    main()
