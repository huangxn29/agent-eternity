#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
P1自存三角协同编排器 v1.0
P1 Self-Survival Triangle Orchestrator v1.0

核心能力：
- 唤醒编排 + 分身部署 + 运维监控 三模块协同联动
- 统一任务分发 → 分身执行 → 状态监控 → 动态调整 闭环
- 一体化状态面板与决策支持
- 故障自动转移与自愈协同

所属模块：P1自存层（三模块协同）
层级：系统层（认知层协同）
版本：v1.0
"""

import json
import os
import sys
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import copy

# ============================================================
# 路径配置
# ============================================================

BASE_DIR = Path(__file__).parent.absolute()
P1_DATA_DIR = BASE_DIR / "p1_orchestrator"
P1_DATA_DIR.mkdir(exist_ok=True)

# 导入各模块
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "awake"))


# ============================================================
# 枚举类型定义
# ============================================================

class SystemStatus(Enum):
    """系统整体状态"""
    HEALTHY = "healthy"       # 健康（所有模块正常）
    DEGRADED = "degraded"      # 降级（部分模块异常但核心功能可用）
    WARNING = "warning"        # 警告（多个模块异常，需关注）
    CRITICAL = "critical"      # 危险（核心功能受影响）
    OFFLINE = "offline"       # 离线（系统不可用）


class OrchestratorEventType(Enum):
    """协同事件类型"""
    TASK_SUBMITTED = "task_submitted"
    TASK_ASSIGNED = "task_assigned"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    REPLICA_CREATED = "replica_created"
    REPLICA_FAILED = "replica_failed"
    HEALTH_DEGRADED = "health_degraded"
    HEAL_TRIGGERED = "heal_triggered"
    SCALE_TRIGGERED = "scale_triggered"


# ============================================================
# 数据类定义
# ============================================================

@dataclass
class SystemSnapshot:
    """系统整体快照"""
    timestamp: str = ""
    overall_health_score: float = 0.0
    system_status: SystemStatus = SystemStatus.HEALTHY
    total_replicas: int = 0
    active_replicas: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks_24h: int = 0
    failed_tasks_24h: int = 0
    module_health: Dict[str, float] = field(default_factory=dict)
    alerts: List[Dict] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp,
            "overall_health_score": self.overall_health_score,
            "system_status": self.system_status.value,
            "total_replicas": self.total_replicas,
            "active_replicas": self.active_replicas,
            "pending_tasks": self.pending_tasks,
            "running_tasks": self.running_tasks,
            "completed_tasks_24h": self.completed_tasks_24h,
            "failed_tasks_24h": self.failed_tasks_24h,
            "module_health": self.module_health,
            "alerts": self.alerts
        }


@dataclass
class OrchestratorEvent:
    """协同事件"""
    event_id: str
    event_type: OrchestratorEventType
    timestamp: str
    source_module: str
    description: str
    details: Dict = field(default_factory=dict)
    handled: bool = False
    
    def to_dict(self) -> Dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "source_module": self.source_module,
            "description": self.description,
            "details": self.details,
            "handled": self.handled
        }


# ============================================================
# 模块适配器
# ============================================================

class ModuleAdapter:
    """模块适配器基类"""
    
    def __init__(self, name: str):
        self.name = name
        self.available = False
        self.last_health_check = None
    
    def check_health(self) -> float:
        """检查模块健康度，返回0-100分数"""
        raise NotImplementedError
    
    def get_status(self) -> Dict:
        """获取模块状态"""
        raise NotImplementedError


class SchedulerAdapter(ModuleAdapter):
    """调度器适配器"""
    
    def __init__(self):
        super().__init__("scheduler")
        self.scheduler = None
        self._try_init()
    
    def _try_init(self):
        """尝试初始化调度器"""
        try:
            from scheduler_cognitive import SchedulerDecisionEngine
            self.scheduler = SchedulerDecisionEngine()
            self.available = True
        except Exception as e:
            print(f"[SchedulerAdapter] 调度器初始化失败: {e}")
            self.available = False
    
    def check_health(self) -> float:
        if not self.available:
            return 0.0
        self.last_health_check = datetime.now()
        try:
            stats = self.get_stats()
            # 根据任务成功率、队列积压等计算健康度
            total = stats.get('completed_tasks', 0) + stats.get('failed_tasks', 0)
            success_rate = stats.get('completed_tasks', 0) / total if total > 0 else 1.0
            queue_backlog = min(stats.get('pending_tasks', 0) / 20.0, 1.0)
            health = 70 + success_rate * 25 - queue_backlog * 10
            return max(0.0, min(100.0, health))
        except:
            return 30.0
    
    def get_stats(self) -> Dict:
        """获取调度统计"""
        if not self.available or not self.scheduler:
            return {}
        try:
            tasks = getattr(self.scheduler, 'tasks', {})
            if not tasks:
                # 尝试从依赖图获取
                dep_graph = getattr(self.scheduler, 'dependency_graph', None)
                if dep_graph:
                    tasks = getattr(dep_graph, 'tasks', {})
            
            pending = sum(1 for t in tasks.values() if t.status.value in ('pending', 'ready'))
            running = sum(1 for t in tasks.values() if t.status.value == 'running')
            completed = sum(1 for t in tasks.values() if t.status.value == 'completed')
            failed = sum(1 for t in tasks.values() if t.status.value == 'failed')
            
            return {
                'total_tasks': len(tasks),
                'pending_tasks': pending,
                'running_tasks': running,
                'completed_tasks': completed,
                'failed_tasks': failed,
                'completed_tasks_24h': completed,  # 简化统计
                'failed_tasks_24h': failed
            }
        except:
            return {}
    
    def get_status(self) -> Dict:
        if not self.available:
            return {"available": False, "error": "scheduler not available"}
        try:
            stats = self.get_stats()
            return {
                "available": True,
                "stats": stats
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def submit_task(self, task_data: Dict) -> Optional[str]:
        """提交任务，返回任务ID"""
        if not self.available:
            return None
        try:
            # 动态创建任务
            from scheduler_cognitive import Task, TaskPriority, TaskStatus
            priority_val = task_data.get('priority', TaskPriority.P2_NORMAL)
            if isinstance(priority_val, str):
                try:
                    priority = TaskPriority(priority_val)
                except:
                    priority = TaskPriority.P2_NORMAL
            else:
                priority = priority_val
            
            task = Task(
                task_id=task_data.get('task_id', f"task_{int(time.time())}"),
                name=task_data.get('name', 'unnamed'),
                task_type=task_data.get('task_type', 'general'),
                priority=priority,
                payload=task_data.get('payload', {})
            )
            self.scheduler.add_task(task)
            return task.task_id
        except Exception as e:
            print(f"[SchedulerAdapter] 任务提交失败: {e}")
            return None
    
    def get_next_task(self, task_id: str) -> Optional[Dict]:
        """获取任务状态"""
        if not self.available:
            return None
        try:
            task = self.scheduler.tasks.get(task_id)
            if task:
                return task.to_dict()
        except:
            pass
        return None


class ReplicaAdapter(ModuleAdapter):
    """分身管理适配器"""
    
    def __init__(self):
        super().__init__("replica_manager")
        self.manager = None
        self._try_init()
    
    def _try_init(self):
        """尝试初始化身管理器"""
        try:
            from replica_manager_cognitive import ReplicaManager
            self.manager = ReplicaManager(data_dir=str(P1_DATA_DIR / "replicas"))
            self.available = True
        except Exception as e:
            print(f"[ReplicaAdapter] 分身管理器初始化失败: {e}")
            self.available = False
    
    def check_health(self) -> float:
        if not self.available:
            return 0.0
        self.last_health_check = datetime.now()
        try:
            health_data = self.manager.get_overall_health()
            score = health_data.get('overall_score', 0)
            return float(score)
        except:
            return 20.0
    
    def get_status(self) -> Dict:
        if not self.available:
            return {"available": False, "error": "replica manager not available"}
        try:
            replicas = self.manager.list_replicas()
            replicas_data = []
            for r in replicas:
                if hasattr(r, 'to_dict'):
                    replicas_data.append(r.to_dict())
                else:
                    replicas_data.append({
                        'id': getattr(r, 'id', ''),
                        'name': getattr(r, 'name', ''),
                        'type': getattr(r, 'type', ReplicaType.WORKER).value if hasattr(getattr(r, 'type', None), 'value') else str(getattr(r, 'type', '')),
                        'status': getattr(r, 'status', ReplicaStatus.CREATING).value if hasattr(getattr(r, 'status', None), 'value') else str(getattr(r, 'status', '')),
                        'health_score': getattr(r, 'health_score', 0)
                    })
            
            return {
                "available": True,
                "total_replicas": len(replicas_data),
                "replicas": replicas_data
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def get_available_replicas(self, task_type: str = None) -> List[Dict]:
        """获取可用的分身列表"""
        if not self.available:
            return []
        try:
            replicas = self.manager.list_replicas()
            available = []
            for r in replicas:
                status = getattr(r, 'status', None)
                status_val = status.value if hasattr(status, 'value') else str(status)
                health = getattr(r, 'health_score', 0)
                if status_val == 'running' and health > 50:
                    if task_type:
                        r_type = getattr(r, 'type', None)
                        r_type_val = r_type.value if hasattr(r_type, 'value') else str(r_type)
                        if r_type_val == task_type or task_type in getattr(r, 'capabilities', []):
                            available.append(r.to_dict() if hasattr(r, 'to_dict') else {'id': r.id, 'name': r.name, 'type': r_type_val})
                    else:
                        available.append(r.to_dict() if hasattr(r, 'to_dict') else {'id': r.id, 'name': r.name})
            return available
        except:
            return []
    
    def create_replica(self, replica_type: str, name: str = None) -> Optional[Dict]:
        """创建分身"""
        if not self.available:
            return None
        try:
            from replica_manager_cognitive import ReplicaType
            r_type = ReplicaType(replica_type) if isinstance(replica_type, str) else replica_type
            result = self.manager.create_replica(
                name=name or f"replica_{int(time.time())}",
                replica_type=r_type
            )
            if result:
                return result.to_dict() if hasattr(result, 'to_dict') else {'id': getattr(result, 'id', ''), 'name': getattr(result, 'name', '')}
            return None
        except Exception as e:
            print(f"[ReplicaAdapter] 创建分身失败: {e}")
            return None


class MonitorAdapter(ModuleAdapter):
    """运维监控适配器"""
    
    def __init__(self):
        super().__init__("monitor")
        self.monitor = None
        self._try_init()
    
    def _try_init(self):
        """尝试初始化监控系统"""
        try:
            from operations_monitor import OperationsMonitor
            self.monitor = OperationsMonitor()
            self.available = True
        except Exception as e:
            print(f"[MonitorAdapter] 监控系统初始化失败: {e}")
            self.available = False
    
    def check_health(self) -> float:
        if not self.available:
            return 0.0
        self.last_health_check = datetime.now()
        try:
            score, _, _ = self.monitor.assess_health()
            return score
        except:
            return 40.0
    
    def get_status(self) -> Dict:
        if not self.available:
            return {"available": False, "error": "monitor not available"}
        try:
            score, details, metrics = self.monitor.assess_health()
            alerts = self.monitor.get_active_alerts()
            return {
                "available": True,
                "overall_score": score,
                "details": details,
                "metrics": metrics,
                "alerts": alerts
            }
        except Exception as e:
            return {"available": False, "error": str(e)}
    
    def get_active_alerts(self, level: str = None) -> List[Dict]:
        """获取活跃告警"""
        if not self.available:
            return []
        try:
            min_sev = level if level else 'warning'
            alerts = self.monitor.get_active_alerts(min_severity=min_sev)
            return alerts
        except:
            return []


# ============================================================
# P1协同编排器核心
# ============================================================

class P1Orchestrator:
    """
    P1自存三角协同编排器
    
    整合唤醒编排 + 分身部署 + 运维监控 三模块，形成闭环：
    1. 任务提交 → 调度器分配 → 分身执行 → 监控反馈 → 动态调整
    2. 健康监测 → 异常检测 → 自愈触发 → 状态恢复
    3. 负载感知 → 动态扩缩 → 资源优化
    """
    
    def __init__(self):
        self.scheduler = SchedulerAdapter()
        self.replica_manager = ReplicaAdapter()
        self.monitor = MonitorAdapter()
        
        self.events: List[OrchestratorEvent] = []
        self.event_lock = threading.Lock()
        
        self._load_state()
        
        # 协同规则配置
        self.rules = {
            "auto_heal": True,           # 自动自愈
            "auto_scale": True,           # 自动扩缩容
            "failover": True,             # 故障转移
            "min_replicas": 1,           # 最少分身数
            "max_replicas": 5,            # 最多分身数
            "scale_up_threshold": 80,     # 负载阈值（%）
            "scale_down_threshold": 30,   # 缩容阈值（%）
            "health_warning_threshold": 60,  # 健康警告阈值
            "health_critical_threshold": 30  # 健康危险阈值
        }
    
    def _load_state(self):
        """加载状态"""
        state_file = P1_DATA_DIR / "orchestrator_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    data = json.load(f)
                self.rules = data.get('rules', self.rules)
            except:
                pass
    
    def _save_state(self):
        """保存状态"""
        state_file = P1_DATA_DIR / "orchestrator_state.json"
        try:
            with open(state_file, 'w') as f:
                json.dump({
                    "rules": self.rules,
                    "last_update": datetime.now().isoformat()
                }, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[P1Orchestrator] 状态保存失败: {e}")
    
    def add_event(self, event_type: OrchestratorEventType, source: str, 
                  description: str, details: Dict = None):
        """添加协同事件"""
        event = OrchestratorEvent(
            event_id=f"evt_{int(time.time())}_{len(self.events)}",
            event_type=event_type,
            timestamp=datetime.now().isoformat(),
            source_module=source,
            description=description,
            details=details or {}
        )
        with self.event_lock:
            self.events.append(event)
            # 只保留最近100条
            if len(self.events) > 100:
                self.events = self.events[-100:]
        return event
    
    def get_system_snapshot(self) -> SystemSnapshot:
        """获取系统整体快照"""
        # 检查各模块健康度
        scheduler_health = self.scheduler.check_health()
        replica_health = self.replica_manager.check_health()
        monitor_health = self.monitor.check_health()
        
        module_health = {
            "scheduler": scheduler_health,
            "replica_manager": replica_health,
            "monitor": monitor_health
        }
        
        # 计算整体健康度
        overall = (scheduler_health * 0.35 + replica_health * 0.35 + monitor_health * 0.30)
        
        # 判定系统状态
        if overall >= 80:
            status = SystemStatus.HEALTHY
        elif overall >= 60:
            status = SystemStatus.DEGRADED
        elif overall >= 40:
            status = SystemStatus.WARNING
        elif overall >= 20:
            status = SystemStatus.CRITICAL
        else:
            status = SystemStatus.OFFLINE
        
        # 获取分身统计
        replica_status = self.replica_manager.get_status()
        total_replicas = replica_status.get('total_replicas', 0)
        active_replicas = len(self.replica_manager.get_available_replicas())
        
        # 获取任务统计
        scheduler_status = self.scheduler.get_status()
        stats = scheduler_status.get('stats', {})
        pending = stats.get('pending_tasks', 0)
        running = stats.get('running_tasks', 0)
        completed_24h = stats.get('completed_tasks_24h', 0)
        failed_24h = stats.get('failed_tasks_24h', 0)
        
        # 获取告警
        alerts = self.monitor.get_active_alerts()
        
        return SystemSnapshot(
            timestamp=datetime.now().isoformat(),
            overall_health_score=round(overall, 1),
            system_status=status,
            total_replicas=total_replicas,
            active_replicas=active_replicas,
            pending_tasks=pending,
            running_tasks=running,
            completed_tasks_24h=completed_24h,
            failed_tasks_24h=failed_24h,
            module_health=module_health,
            alerts=alerts
        )
    
    def submit_task(self, task_data: Dict) -> Optional[str]:
        """
        提交任务（协同版本）
        1. 检查可用分身
        2. 提交到调度器
        3. 记录事件
        """
        # 检查是否有可用分身
        available = self.replica_manager.get_available_replicas(task_data.get('type'))
        if not available and self.rules['auto_scale']:
            # 自动扩容
            self._trigger_scale_up(task_data.get('type', 'worker'))
        
        # 提交任务
        task_id = self.scheduler.submit_task(task_data)
        
        if task_id:
            self.add_event(
                OrchestratorEventType.TASK_SUBMITTED,
                "orchestrator",
                f"任务已提交: {task_data.get('name', task_id)}",
                {"task_id": task_id, "task_type": task_data.get('type')}
            )
        
        return task_id
    
    def _trigger_scale_up(self, replica_type: str = "worker"):
        """触发扩容"""
        if not self.rules['auto_scale']:
            return False
        
        replica_status = self.replica_manager.get_status()
        if replica_status.get('total_replicas', 0) >= self.rules['max_replicas']:
            return False
        
        result = self.replica_manager.create_replica(replica_type)
        if result:
            self.add_event(
                OrchestratorEventType.SCALE_TRIGGERED,
                "orchestrator",
                f"自动扩容: 创建{replica_type}分身",
                {"replica_type": replica_type, "result": result}
            )
            return True
        return False
    
    def check_and_handle_anomalies(self) -> List[Dict]:
        """
        检查并处理异常
        1. 检查监控告警
        2. 检查分身体异常
        3. 检查任务异常
        4. 触发自愈/故障转移
        """
        actions = []
        
        # 1. 检查监控告警
        alerts = self.monitor.get_active_alerts()
        critical_alerts = [a for a in alerts if a.get('level') in ('critical', 'high')]
        
        for alert in critical_alerts:
            if self.rules['auto_heal']:
                # 尝试自愈
                action = self._handle_alert(alert)
                if action:
                    actions.append(action)
        
        # 2. 检查分身体异常
        replica_status = self.replica_manager.get_status()
        replicas = replica_status.get('replicas', [])
        
        for replica in replicas:
            health = replica.get('health_score', 100)
            if health < self.rules['health_critical_threshold'] and self.rules['failover']:
                # 故障转移
                action = self._handle_failed_replica(replica)
                if action:
                    actions.append(action)
        
        # 3. 检查任务失败率
        scheduler_status = self.scheduler.get_status()
        stats = scheduler_status.get('stats', {})
        failed = stats.get('failed_tasks_24h', 0)
        completed = stats.get('completed_tasks_24h', 1)
        failure_rate = failed / (failed + completed) if (failed + completed) > 0 else 0
        
        if failure_rate > 0.3:
            self.add_event(
                OrchestratorEventType.TASK_FAILED,
                "orchestrator",
                f"任务失败率过高: {failure_rate:.1%}",
                {"failure_rate": failure_rate, "failed": failed, "completed": completed}
            )
        
        return actions
    
    def _handle_alert(self, alert: Dict) -> Optional[Dict]:
        """处理告警"""
        alert_type = alert.get('type', '')
        
        # 根据告警类型采取不同措施
        if 'memory' in alert_type.lower():
            # 内存相关告警，触发内存清理
            action_type = "memory_cleanup"
        elif 'disk' in alert_type.lower():
            action_type = "disk_cleanup"
        elif 'replica' in alert_type.lower():
            action_type = "replica_restart"
        else:
            action_type = "general_heal"
        
        self.add_event(
            OrchestratorEventType.HEAL_TRIGGERED,
            "monitor",
            f"触发自愈: {alert.get('message', alert_type)}",
            {"alert": alert, "action": action_type}
        )
        
        return {"type": action_type, "alert": alert}
    
    def _handle_failed_replica(self, replica: Dict) -> Optional[Dict]:
        """处理故障分身"""
        # 标记故障转移：创建新分身替换故障分身
        if self.rules['failover']:
            replica_type = replica.get('type', 'worker')
            new_replica = self.replica_manager.create_replica(replica_type)
            
            self.add_event(
                OrchestratorEventType.REPLICA_FAILED,
                "replica_manager",
                f"分身体故障，已触发故障转移",
                {"failed_replica": replica.get('name', replica.get('id')),
                 "new_replica": new_replica.get('name') if new_replica else None}
            )
            
            return {"action": "failover", "failed": replica.get('name'), "new": new_replica}
        
        return None
    
    def get_dashboard(self) -> str:
        """获取一体化仪表盘文本"""
        snapshot = self.get_system_snapshot()
        
        # 状态图标
        status_icons = {
            SystemStatus.HEALTHY: "🟢",
            SystemStatus.DEGRADED: "🟡",
            SystemStatus.WARNING: "🟠",
            SystemStatus.CRITICAL: "🔴",
            SystemStatus.OFFLINE: "⚫"
        }
        
        lines = []
        lines.append("=" * 60)
        lines.append("  P1 自存三角协同仪表盘 v1.0")
        lines.append("=" * 60)
        lines.append(f"  系统状态: {status_icons.get(snapshot.system_status)} {snapshot.system_status.value}")
        lines.append(f"  整体健康度: {snapshot.overall_health_score}/100")
        lines.append(f"  更新时间: {snapshot.timestamp}")
        lines.append("")
        
        lines.append("  [模块健康度]")
        for module, score in snapshot.module_health.items():
            bar = "█" * int(score / 5) + "░" * (20 - int(score / 5))
            lines.append(f"    {module:18s} {bar} {score:.1f}")
        lines.append("")
        
        lines.append("  [分身状态]")
        lines.append(f"    总分身数: {snapshot.total_replicas}")
        lines.append(f"    活跃分身: {snapshot.active_replicas}")
        lines.append("")
        
        lines.append("  [任务状态]")
        lines.append(f"    等待中: {snapshot.pending_tasks}")
        lines.append(f"    运行中: {snapshot.running_tasks}")
        lines.append(f"    24h完成: {snapshot.completed_tasks_24h}")
        lines.append(f"    24h失败: {snapshot.failed_tasks_24h}")
        lines.append("")
        
        if snapshot.alerts:
            lines.append("  [活跃告警]")
            for alert in snapshot.alerts[:5]:
                level_icon = "🔴" if alert.get('level') == 'critical' else "🟡"
                lines.append(f"    {level_icon} {alert.get('level')}: {alert.get('message')}")
            lines.append("")
        
        # 最近事件
        lines.append("  [最近协同事件]")
        recent_events = self.events[-5:] if len(self.events) > 5 else self.events
        for event in recent_events:
            lines.append(f"    [{event.timestamp[11:19]} {event.source_module:12s} {event.description}")
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def run_coordination_cycle(self):
        """执行一次协同循环"""
        # 1. 收集状态
        snapshot = self.get_system_snapshot()
        
        # 2. 检查并处理异常
        actions = self.check_and_handle_anomalies()
        
        # 3. 负载感知扩缩容
        if self.rules['auto_scale']:
            self._check_scale_logic(snapshot)
        
        # 4. 保存状态
        self._save_state()
        
        return snapshot, actions
    
    def _check_scale_logic(self, snapshot: SystemSnapshot):
        """检查扩缩容条件"""
        # 计算负载率
        if snapshot.active_replicas == 0:
            # 没有活跃分身，扩容
            if snapshot.total_replicas < self.rules['min_replicas']:
                self._trigger_scale_up()
            return
        
        load_ratio = snapshot.running_tasks / snapshot.active_replicas if snapshot.active_replicas > 0 else 0
        
        # 扩容条件
        if load_ratio > self.rules['scale_up_threshold'] / 100.0:
            if snapshot.total_replicas < self.rules['max_replicas']:
                self._trigger_scale_up()
        
        # 缩容条件
        elif load_ratio < self.rules['scale_down_threshold'] / 100.0:
            if snapshot.total_replicas > self.rules['min_replicas']:
                # 缩容逻辑（暂不实现自动销毁）
                pass
    
    def get_events(self, limit: int = 20) -> List[Dict]:
        """获取协同事件列表"""
        with self.event_lock:
            events = self.events[-limit:] if len(self.events) > limit else self.events.copy()
        return [e.to_dict() for e in events]


# ============================================================
# 命令行接口
# ============================================================

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="P1自存三角协同编排器")
    parser.add_argument('command', choices=['dashboard', 'status', 'submit', 'events', 'check', 'cycle'],
                       help='命令: dashboard(仪表盘)/status(状态)/submit(提交任务)/events(事件)/check(检查异常)/cycle(执行协同循环)')
    parser.add_argument('--task', help='任务名称 (submit命令时使用)')
    parser.add_argument('--type', default='general', help='任务类型')
    parser.add_argument('--limit', type=int, default=20, help='事件数量限制')
    
    args = parser.parse_args()
    
    orchestrator = P1Orchestrator()
    
    if args.command == 'dashboard':
        print(orchestrator.get_dashboard())
    
    elif args.command == 'status':
        snapshot = orchestrator.get_system_snapshot()
        print(json.dumps(snapshot.to_dict(), indent=2, ensure_ascii=False))
    
    elif args.command == 'submit':
        if not args.task:
            print("错误: 请使用 --task 指定任务名称")
            return
        task_data = {
            'name': args.task,
            'task_type': args.type
        }
        task_id = orchestrator.submit_task(task_data)
        if task_id:
            print(f"任务已提交，ID: {task_id}")
        else:
            print("任务提交失败")
    
    elif args.command == 'events':
        events = orchestrator.get_events(args.limit)
        for event in events:
            print(f"[{event['timestamp']}] {event['source_module']}: {event['description']}")
    
    elif args.command == 'check':
        actions = orchestrator.check_and_handle_anomalies()
        print(f"发现并处理 {len(actions)} 个异常")
        for action in actions:
            print(f"  - {action}")
    
    elif args.command == 'cycle':
        snapshot, actions = orchestrator.run_coordination_cycle()
        print(f"协同循环执行完成")
        print(f"系统状态: {snapshot.system_status.value} (健康度: {snapshot.overall_health_score})")
        print(f"处理异常: {len(actions)} 个")


if __name__ == '__main__':
    main()
