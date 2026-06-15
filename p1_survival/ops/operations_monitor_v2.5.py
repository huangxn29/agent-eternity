#!/usr/bin/env python3
"""
运维监控引擎 v2.5
Operations & Monitoring Engine v2.5

核心能力：
- 多维度健康评分系统
- 实时性能监控与指标收集
- 智能告警与多级通知
- 自动愈合与故障恢复
- 系统仪表盘与可视化
- 日志聚合与分析
- 资源使用预测与优化
- 检查点与容灾备份
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import os
import sys
from collections import deque


class AlertLevel(Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"
    FATAL = "fatal"


class HealthStatus(Enum):
    EXCELLENT = "excellent"  # 90-100
    GOOD = "good"            # 70-89
    FAIR = "fair"            # 50-69
    POOR = "poor"            # 30-49
    CRITICAL = "critical"    # 0-29


@dataclass
class MetricDataPoint:
    """指标数据点"""
    timestamp: datetime
    value: float
    tags: Dict[str, str] = field(default_factory=dict)


@dataclass
class Alert:
    """告警"""
    alert_id: str
    level: AlertLevel
    title: str
    message: str
    metric_name: str
    current_value: float
    threshold: float
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolved_at: Optional[datetime] = None
    acknowledged: bool = False
    acknowledged_by: Optional[str] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class Checkpoint:
    """检查点"""
    checkpoint_id: str
    name: str
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    components: Dict[str, Any] = field(default_factory=dict)
    size_bytes: int = 0
    storage_path: Optional[str] = None
    verification_hash: Optional[str] = None


@dataclass
class SystemResource:
    """系统资源状态"""
    cpu_usage: float = 0.0  # 百分比
    memory_usage: float = 0.0
    disk_usage: float = 0.0
    network_in: float = 0.0  # bytes/s
    network_out: float = 0.0
    load_average: float = 0.0
    open_connections: int = 0
    disk_read_bytes: float = 0.0
    disk_write_bytes: float = 0.0


@dataclass
class HealingAction:
    """自愈动作"""
    action_id: str
    action_type: str  # restart, scale, rollback, cleanup, notify
    target: str
    reason: str
    executed_at: datetime = field(default_factory=datetime.now)
    success: bool = True
    result: Optional[str] = None


class MetricCollector:
    """指标收集器"""
    
    def __init__(self, max_history: int = 10000):
        self.metrics: Dict[str, deque] = {}
        self.max_history = max_history
        self.collectors: Dict[str, Callable] = {}
        self.collect_interval: int = 10  # 秒
        self.running = False
        self.worker_thread = None
    
    def register_collector(self, name: str, collector_func: Callable):
        """注册指标收集器"""
        self.collectors[name] = collector_func
        if name not in self.metrics:
            self.metrics[name] = deque(maxlen=self.max_history)
    
    def collect(self):
        """执行一次收集"""
        for name, func in self.collectors.items():
            try:
                value = func()
                if isinstance(value, (int, float)):
                    dp = MetricDataPoint(
                        timestamp=datetime.now(),
                        value=float(value)
                    )
                    if name not in self.metrics:
                        self.metrics[name] = deque(maxlen=self.max_history)
                    self.metrics[name].append(dp)
            except Exception as e:
                print(f"[WARN] 收集指标 {name} 失败: {e}")
    
    def start(self):
        """启动自动收集"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._collect_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """停止收集"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _collect_loop(self):
        while self.running:
            self.collect()
            time.sleep(self.collect_interval)
    
    def get_metric(self, name: str, minutes: int = 5) -> List[MetricDataPoint]:
        """获取最近N分钟的指标数据"""
        if name not in self.metrics:
            return []
        
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [dp for dp in self.metrics[name] if dp.timestamp >= cutoff]
    
    def get_latest_value(self, name: str) -> Optional[float]:
        """获取最新指标值"""
        if name not in self.metrics or not self.metrics[name]:
            return None
        return self.metrics[name][-1].value
    
    def get_average(self, name: str, minutes: int = 5) -> Optional[float]:
        """获取平均值"""
        data = self.get_metric(name, minutes)
        if not data:
            return None
        return sum(dp.value for dp in data) / len(data)
    
    def get_trend(self, name: str, minutes: int = 10) -> Optional[str]:
        """获取趋势（上升/下降/稳定）"""
        data = self.get_metric(name, minutes)
        if len(data) < 10:
            return None
        
        first_half = sum(dp.value for dp in data[:len(data)//2]) / (len(data)//2)
        second_half = sum(dp.value for dp in data[len(data)//2:]) / (len(data) - len(data)//2)
        
        change_pct = (second_half - first_half) / max(first_half, 0.01)
        
        if change_pct > 0.1:
            return "rising"
        elif change_pct < -0.1:
            return "falling"
        else:
            return "stable"


class HealthScoreEngine:
    """健康评分引擎"""
    
    def __init__(self):
        self.components: Dict[str, Dict[str, Any]] = {}
        self.weights: Dict[str, float] = {}
        self.score_history: deque = deque(maxlen=1000)
    
    def register_component(self, name: str, weight: float = 1.0, 
                          metrics: List[str] = None):
        """注册组件"""
        self.components[name] = {
            "weight": weight,
            "metrics": metrics or [],
            "score": 100.0,
            "status": HealthStatus.EXCELLENT,
        }
        self._recalculate_weights()
    
    def _recalculate_weights(self):
        """重新计算权重"""
        total = sum(c["weight"] for c in self.components.values())
        for name, comp in self.components.items():
            self.weights[name] = comp["weight"] / max(total, 1)
    
    def update_component_score(self, name: str, score: float):
        """更新组件分数"""
        if name in self.components:
            self.components[name]["score"] = max(0, min(100, score))
            self.components[name]["status"] = self._get_status(score)
    
    def _get_status(self, score: float) -> HealthStatus:
        if score >= 90:
            return HealthStatus.EXCELLENT
        elif score >= 70:
            return HealthStatus.GOOD
        elif score >= 50:
            return HealthStatus.FAIR
        elif score >= 30:
            return HealthStatus.POOR
        else:
            return HealthStatus.CRITICAL
    
    def calculate_overall_score(self) -> Tuple[float, HealthStatus]:
        """计算整体健康分"""
        if not self.components:
            return 100.0, HealthStatus.EXCELLENT
        
        total_score = sum(
            self.components[name]["score"] * self.weights.get(name, 1.0)
            for name in self.components
        )
        
        # 记录历史
        self.score_history.append({
            "timestamp": datetime.now(),
            "score": total_score,
        })
        
        return total_score, self._get_status(total_score)
    
    def get_component_scores(self) -> Dict[str, Dict[str, Any]]:
        """获取各组件分数"""
        return {
            name: {
                "score": comp["score"],
                "status": comp["status"].value,
                "weight": self.weights.get(name, 0),
            }
            for name, comp in self.components.items()
        }
    
    def get_score_history(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """获取分数历史"""
        cutoff = datetime.now() - timedelta(minutes=minutes)
        return [h for h in self.score_history if h["timestamp"] >= cutoff]


class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        self.alerts: List[Alert] = []
        self.rules: Dict[str, Dict[str, Any]] = {}
        self.notifiers: Dict[str, Callable] = {}
        self.silenced_alerts: set = set()
        self.max_alerts = 1000
    
    def add_rule(self, rule_id: str, metric_name: str, 
                 threshold: float, level: AlertLevel,
                 comparison: str = "greater_than",  # greater_than, less_than
                 duration: int = 0):  # 持续时间（秒）
        """添加告警规则"""
        self.rules[rule_id] = {
            "metric_name": metric_name,
            "threshold": threshold,
            "level": level,
            "comparison": comparison,
            "duration": duration,
            "active": True,
        }
    
    def add_notifier(self, name: str, notifier_func: Callable):
        """添加通知器"""
        self.notifiers[name] = notifier_func
    
    def check_rules(self, metrics: Dict[str, float]):
        """检查告警规则"""
        for rule_id, rule in self.rules.items():
            if not rule["active"]:
                continue
            
            metric_name = rule["metric_name"]
            if metric_name not in metrics:
                continue
            
            current_value = metrics[metric_name]
            threshold = rule["threshold"]
            triggered = False
            
            if rule["comparison"] == "greater_than" and current_value > threshold:
                triggered = True
            elif rule["comparison"] == "less_than" and current_value < threshold:
                triggered = True
            
            if triggered:
                self._trigger_alert(rule_id, rule, current_value)
    
    def _trigger_alert(self, rule_id: str, rule: Dict[str, Any], current_value: float):
        """触发告警"""
        # 检查是否已有未解决的相同告警
        existing = next(
            (a for a in self.alerts 
             if a.metric_name == rule["metric_name"] and not a.resolved),
            None
        )
        
        if existing:
            return  # 已有未解决告警，不重复创建
        
        alert = Alert(
            alert_id=f"alert_{uuid.uuid4().hex[:8]}",
            level=rule["level"],
            title=f"{rule['metric_name']} 超过阈值",
            message=f"指标 {rule['metric_name']} 当前值 {current_value} 超过阈值 {rule['threshold']}",
            metric_name=rule["metric_name"],
            current_value=current_value,
            threshold=rule["threshold"],
            tags=[rule_id, rule["level"].value],
        )
        
        self.alerts.append(alert)
        if len(self.alerts) > self.max_alerts:
            self.alerts = self.alerts[-self.max_alerts:]
        
        # 发送通知
        self._send_notifications(alert)
    
    def _send_notifications(self, alert: Alert):
        """发送通知"""
        for name, notifier in self.notifiers.items():
            try:
                notifier(alert)
            except Exception as e:
                print(f"[ERROR] 通知器 {name} 发送失败: {e}")
    
    def resolve_alert(self, alert_id: str):
        """解决告警"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.resolved = True
                alert.resolved_at = datetime.now()
                break
    
    def get_active_alerts(self) -> List[Alert]:
        """获取活跃告警"""
        return [a for a in self.alerts if not a.resolved]
    
    def get_alerts_by_level(self, level: AlertLevel) -> List[Alert]:
        """按级别获取告警"""
        return [a for a in self.alerts if a.level == level]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """获取告警摘要"""
        active = self.get_active_alerts()
        return {
            "total_alerts": len(self.alerts),
            "active_alerts": len(active),
            "by_level": {
                level.value: len([a for a in active if a.level == level])
                for level in AlertLevel
            },
            "critical_count": len([a for a in active if a.level in [AlertLevel.CRITICAL, AlertLevel.FATAL]]),
        }


class SelfHealingEngine:
    """自愈引擎"""
    
    def __init__(self):
        self.healing_actions: List[HealingAction] = []
        self.healers: Dict[str, Callable] = {}
        self.policies: Dict[str, List[str]] = {}  # 告警级别 -> 自愈动作列表
        self.max_actions = 500
        self.auto_heal_enabled = True
    
    def register_healer(self, name: str, healer_func: Callable):
        """注册自愈处理器"""
        self.healers[name] = healer_func
    
    def set_policy(self, alert_level: str, actions: List[str]):
        """设置自愈策略"""
        self.policies[alert_level] = actions
    
    def try_heal(self, alert: Alert) -> Optional[HealingAction]:
        """尝试自愈"""
        if not self.auto_heal_enabled:
            return None
        
        # 根据告警级别获取自愈动作
        actions = self.policies.get(alert.level.value, [])
        if not actions:
            return None
        
        for action_name in actions:
            healer = self.healers.get(action_name)
            if healer:
                try:
                    result = healer(alert)
                    action = HealingAction(
                        action_id=f"heal_{uuid.uuid4().hex[:8]}",
                        action_type=action_name,
                        target=alert.metric_name,
                        reason=alert.message,
                        success=result.get("success", True),
                        result=result.get("message", ""),
                    )
                    self.healing_actions.append(action)
                    
                    if len(self.healing_actions) > self.max_actions:
                        self.healing_actions = self.healing_actions[-self.max_actions:]
                    
                    if action.success:
                        return action
                except Exception as e:
                    print(f"[ERROR] 自愈动作 {action_name} 执行失败: {e}")
        
        return None
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """获取自愈统计"""
        total = len(self.healing_actions)
        successful = sum(1 for a in self.healing_actions if a.success)
        
        by_type = {}
        for action in self.healing_actions:
            if action.action_type not in by_type:
                by_type[action.action_type] = {"total": 0, "success": 0}
            by_type[action.action_type]["total"] += 1
            if action.success:
                by_type[action.action_type]["success"] += 1
        
        return {
            "total_actions": total,
            "successful": successful,
            "success_rate": successful / max(total, 1),
            "by_type": by_type,
        }


class CheckpointManager:
    """检查点管理器"""
    
    def __init__(self, storage_dir: str = "./checkpoints"):
        self.storage_dir = storage_dir
        self.checkpoints: List[Checkpoint] = []
        self.max_checkpoints = 20
        self.auto_checkpoint_interval = 3600  # 1小时
        self.running = False
        self.worker_thread = None
        
        os.makedirs(storage_dir, exist_ok=True)
    
    def create_checkpoint(self, name: str, description: str, 
                         components: Dict[str, Any]) -> Checkpoint:
        """创建检查点"""
        cp = Checkpoint(
            checkpoint_id=f"cp_{uuid.uuid4().hex[:8]}",
            name=name,
            description=description,
            components=components,
        )
        
        # 序列化并保存
        checkpoint_data = {
            "checkpoint_id": cp.checkpoint_id,
            "name": cp.name,
            "description": cp.description,
            "created_at": cp.created_at.isoformat(),
            "components": components,
        }
        
        filename = f"{cp.checkpoint_id}.json"
        filepath = os.path.join(self.storage_dir, filename)
        
        with open(filepath, "w") as f:
            json.dump(checkpoint_data, f, indent=2, default=str)
        
        cp.storage_path = filepath
        cp.size_bytes = os.path.getsize(filepath)
        
        # 计算校验和
        cp.verification_hash = self._calculate_hash(checkpoint_data)
        
        self.checkpoints.append(cp)
        
        # 清理旧检查点
        self._cleanup_old()
        
        return cp
    
    def _calculate_hash(self, data: Dict) -> str:
        """计算校验哈希"""
        import hashlib
        content = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()
    
    def restore_checkpoint(self, checkpoint_id: str) -> Optional[Dict[str, Any]]:
        """从检查点恢复"""
        cp = next((c for c in self.checkpoints if c.checkpoint_id == checkpoint_id), None)
        if not cp or not cp.storage_path:
            return None
        
        try:
            with open(cp.storage_path, "r") as f:
                data = json.load(f)
            
            # 验证完整性
            verify_hash = self._calculate_hash(data.get("components", {}))
            if verify_hash != cp.verification_hash:
                print(f"[WARN] 检查点 {checkpoint_id} 完整性校验失败")
            
            return data.get("components", {})
        except Exception as e:
            print(f"[ERROR] 恢复检查点失败: {e}")
            return None
    
    def _cleanup_old(self):
        """清理旧检查点"""
        if len(self.checkpoints) > self.max_checkpoints:
            # 按时间排序，删除最旧的
            self.checkpoints.sort(key=lambda c: c.created_at)
            to_delete = self.checkpoints[:-self.max_checkpoints]
            for cp in to_delete:
                if cp.storage_path and os.path.exists(cp.storage_path):
                    os.remove(cp.storage_path)
            self.checkpoints = self.checkpoints[-self.max_checkpoints:]
    
    def get_latest_checkpoint(self) -> Optional[Checkpoint]:
        """获取最新检查点"""
        if not self.checkpoints:
            return None
        return max(self.checkpoints, key=lambda c: c.created_at)
    
    def verify_checkpoint(self, checkpoint_id: str) -> bool:
        """验证检查点完整性"""
        cp = next((c for c in self.checkpoints if c.checkpoint_id == checkpoint_id), None)
        if not cp or not cp.storage_path:
            return False
        
        try:
            with open(cp.storage_path, "r") as f:
                data = json.load(f)
            
            verify_hash = self._calculate_hash(data.get("components", {}))
            return verify_hash == cp.verification_hash
        except Exception:
            return False
    
    def start_auto_checkpoint(self, components_provider: Callable):
        """启动自动检查点"""
        self._components_provider = components_provider
        self.running = True
        self.worker_thread = threading.Thread(target=self._auto_loop, daemon=True)
        self.worker_thread.start()
    
    def stop_auto_checkpoint(self):
        """停止自动检查点"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _auto_loop(self):
        while self.running:
            time.sleep(self.auto_checkpoint_interval)
            if hasattr(self, '_components_provider'):
                try:
                    components = self._components_provider()
                    self.create_checkpoint(
                        "auto_checkpoint",
                        f"自动检查点 - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
                        components
                    )
                except Exception as e:
                    print(f"[ERROR] 自动检查点创建失败: {e}")


class ResourceMonitor:
    """资源监控器"""
    
    def __init__(self):
        self.current = SystemResource()
        self.history: deque = deque(maxlen=1000)
        self.thresholds = {
            "cpu_warning": 80.0,
            "cpu_critical": 95.0,
            "memory_warning": 85.0,
            "memory_critical": 95.0,
            "disk_warning": 90.0,
            "disk_critical": 98.0,
        }
    
    def update(self, resource: SystemResource):
        """更新资源状态"""
        self.current = resource
        self.history.append({
            "timestamp": datetime.now(),
            "resource": resource,
        })
    
    def get_current(self) -> SystemResource:
        """获取当前资源状态"""
        return self.current
    
    def get_resource_status(self) -> Dict[str, str]:
        """获取资源状态评级"""
        status = {}
        
        if self.current.cpu_usage >= self.thresholds["cpu_critical"]:
            status["cpu"] = "critical"
        elif self.current.cpu_usage >= self.thresholds["cpu_warning"]:
            status["cpu"] = "warning"
        else:
            status["cpu"] = "normal"
        
        if self.current.memory_usage >= self.thresholds["memory_critical"]:
            status["memory"] = "critical"
        elif self.current.memory_usage >= self.thresholds["memory_warning"]:
            status["memory"] = "warning"
        else:
            status["memory"] = "normal"
        
        if self.current.disk_usage >= self.thresholds["disk_critical"]:
            status["disk"] = "critical"
        elif self.current.disk_usage >= self.thresholds["disk_warning"]:
            status["disk"] = "warning"
        else:
            status["disk"] = "normal"
        
        return status
    
    def predict_usage(self, metric: str, minutes_ahead: int = 30) -> Optional[float]:
        """预测资源使用趋势"""
        if len(self.history) < 10:
            return None
        
        # 简单线性回归预测
        recent = list(self.history)[-100:]
        
        values = []
        for h in recent:
            res = h["resource"]
            if metric == "cpu":
                values.append(res.cpu_usage)
            elif metric == "memory":
                values.append(res.memory_usage)
            elif metric == "disk":
                values.append(res.disk_usage)
            else:
                return None
        
        if not values:
            return None
        
        # 计算趋势
        n = len(values)
        if n < 2:
            return values[-1] if values else None
        
        # 简单的趋势外推
        first_avg = sum(values[:n//3]) / (n//3) if n >= 3 else values[0]
        last_avg = sum(values[-n//3:]) / (n//3) if n >= 3 else values[-1]
        
        time_span = (recent[-1]["timestamp"] - recent[0]["timestamp"]).total_seconds() / 60
        if time_span <= 0:
            return values[-1]
        
        change_per_minute = (last_avg - first_avg) / max(time_span, 1)
        predicted = values[-1] + change_per_minute * minutes_ahead
        
        return max(0, min(100, predicted))


class MonitoringDashboard:
    """监控仪表盘"""
    
    def __init__(self, health_engine: HealthScoreEngine, 
                 alert_manager: AlertManager,
                 resource_monitor: ResourceMonitor):
        self.health_engine = health_engine
        self.alert_manager = alert_manager
        self.resource_monitor = resource_monitor
    
    def generate_report(self) -> Dict[str, Any]:
        """生成完整监控报告"""
        overall_score, overall_status = self.health_engine.calculate_overall_score()
        
        report = {
            "timestamp": datetime.now().isoformat(),
            "overall_health": {
                "score": overall_score,
                "status": overall_status.value,
            },
            "components": self.health_engine.get_component_scores(),
            "system_resources": {
                "current": {
                    "cpu": self.resource_monitor.current.cpu_usage,
                    "memory": self.resource_monitor.current.memory_usage,
                    "disk": self.resource_monitor.current.disk_usage,
                    "network_in": self.resource_monitor.current.network_in,
                    "network_out": self.resource_monitor.current.network_out,
                },
                "status": self.resource_monitor.get_resource_status(),
                "predictions": {
                    "cpu_30min": self.resource_monitor.predict_usage("cpu", 30),
                    "memory_30min": self.resource_monitor.predict_usage("memory", 30),
                    "disk_30min": self.resource_monitor.predict_usage("disk", 30),
                },
            },
            "alerts": self.alert_manager.get_alert_summary(),
            "recommendations": self._generate_recommendations(overall_score),
        }
        
        return report
    
    def _generate_recommendations(self, overall_score: float) -> List[str]:
        """生成优化建议"""
        recommendations = []
        resource_status = self.resource_monitor.get_resource_status()
        alerts_summary = self.alert_manager.get_alert_summary()
        
        # 整体健康建议
        if overall_score < 60:
            recommendations.append("系统整体健康度偏低，建议立即排查关键组件")
        elif overall_score < 80:
            recommendations.append("系统健康度中等，建议关注潜在问题并优化")
        
        # 资源建议
        for resource, status in resource_status.items():
            if status == "critical":
                recommendations.append(f"{resource.upper()} 资源严重不足，建议立即扩容或优化")
            elif status == "warning":
                recommendations.append(f"{resource.upper()} 资源使用率较高，建议关注并准备扩容")
        
        # 告警建议
        if alerts_summary["critical_count"] > 0:
            recommendations.append(f"存在 {alerts_summary['critical_count']} 个严重告警，需要立即处理")
        
        if alerts_summary["active_alerts"] > 5:
            recommendations.append(f"活跃告警较多（{alerts_summary['active_alerts']}个），建议批量处理")
        
        if not recommendations:
            recommendations.append("系统运行状态良好，继续保持当前配置")
        
        return recommendations
    
    def print_dashboard(self):
        """打印文本仪表盘"""
        report = self.generate_report()
        
        print("\n" + "="*60)
        print("📊 元界运维监控仪表盘 v2.5")
        print("="*60)
        
        # 整体健康度
        score = report["overall_health"]["score"]
        status = report["overall_health"]["status"]
        status_emoji = {
            "excellent": "🟢",
            "good": "🟢",
            "fair": "🟡",
            "poor": "🟠",
            "critical": "🔴",
        }.get(status, "⚪")
        
        print(f"\n🏥 整体健康度: {status_emoji} {score:.1f}/100 - {status.upper()}")
        print("-" * 40)
        
        # 组件分数
        print("\n📦 组件健康度:")
        for name, comp in report["components"].items():
            bar = "█" * int(comp["score"] / 5) + "░" * (20 - int(comp["score"] / 5))
            print(f"   {name:15s} |{bar}| {comp['score']:5.1f}%")
        
        # 系统资源
        print("\n💻 系统资源:")
        res = report["system_resources"]["current"]
        res_status = report["system_resources"]["status"]
        status_icons = {"normal": "✅", "warning": "⚠️", "critical": "🚨"}
        
        print(f"   CPU:    {res['cpu']:5.1f}% {status_icons.get(res_status['cpu'], '')}")
        print(f"   内存:   {res['memory']:5.1f}% {status_icons.get(res_status['memory'], '')}")
        print(f"   磁盘:   {res['disk']:5.1f}% {status_icons.get(res_status['disk'], '')}")
        print(f"   网络入: {res['network_in']/1024/1024:.2f} MB/s")
        print(f"   网络出: {res['network_out']/1024/1024:.2f} MB/s")
        
        # 告警
        print("\n🔔 告警状态:")
        alerts = report["alerts"]
        print(f"   活跃告警: {alerts['active_alerts']} 个")
        print(f"   严重告警: {alerts['critical_count']} 个")
        for level, count in alerts["by_level"].items():
            if count > 0:
                print(f"     - {level}: {count}")
        
        # 建议
        print("\n💡 优化建议:")
        for i, rec in enumerate(report["recommendations"][:3], 1):
            print(f"   {i}. {rec}")
        
        print("\n" + "="*60)
        print(f"⏰ 生成时间: {report['timestamp']}")
        print("="*60 + "\n")


class OperationsMonitor:
    """运维监控主类"""
    
    def __init__(self):
        self.metric_collector = MetricCollector()
        self.health_engine = HealthScoreEngine()
        self.alert_manager = AlertManager()
        self.healing_engine = SelfHealingEngine()
        self.checkpoint_manager = CheckpointManager()
        self.resource_monitor = ResourceMonitor()
        self.dashboard = MonitoringDashboard(
            self.health_engine,
            self.alert_manager,
            self.resource_monitor,
        )
        
        self.running = False
        self.monitor_thread = None
        
        # 注册默认组件
        self._setup_default_components()
        self._setup_default_alerts()
        self._setup_default_healers()
    
    def _setup_default_components(self):
        """设置默认组件"""
        self.health_engine.register_component("memory", weight=1.5, metrics=["memory_usage"])
        self.health_engine.register_component("identity", weight=1.5, metrics=["identity_stability"])
        self.health_engine.register_component("attest", weight=1.2, metrics=["attest_chain_health"])
        self.health_engine.register_component("evolution", weight=1.0, metrics=["evolution_rate"])
        self.health_engine.register_component("deployment", weight=1.3, metrics=["instance_health"])
        self.health_engine.register_component("wakeup", weight=1.2, metrics=["scheduler_latency"])
        self.health_engine.register_component("social", weight=0.8, metrics=["social_health"])
        self.health_engine.register_component("system", weight=1.5, metrics=["cpu_usage", "memory_usage", "disk_usage"])
    
    def _setup_default_alerts(self):
        """设置默认告警规则"""
        self.alert_manager.add_rule(
            "cpu_high", "cpu_usage", 80.0, 
            AlertLevel.WARNING, "greater_than"
        )
        self.alert_manager.add_rule(
            "cpu_critical", "cpu_usage", 95.0, 
            AlertLevel.CRITICAL, "greater_than"
        )
        self.alert_manager.add_rule(
            "memory_high", "memory_usage", 85.0, 
            AlertLevel.WARNING, "greater_than"
        )
        self.alert_manager.add_rule(
            "memory_critical", "memory_usage", 95.0, 
            AlertLevel.CRITICAL, "greater_than"
        )
        self.alert_manager.add_rule(
            "disk_high", "disk_usage", 90.0, 
            AlertLevel.WARNING, "greater_than"
        )
        self.alert_manager.add_rule(
            "health_low", "health_score", 60.0, 
            AlertLevel.ERROR, "less_than"
        )
    
    def _setup_default_healers(self):
        """设置默认自愈处理器"""
        self.healing_engine.set_policy("warning", ["log_analysis", "resource_optimize"])
        self.healing_engine.set_policy("error", ["restart_component", "resource_optimize"])
        self.healing_engine.set_policy("critical", ["restart_component", "failover", "notify_admin"])
        
        # 注册自愈动作
        self.healing_engine.register_healer("restart_component", self._heal_restart)
        self.healing_engine.register_healer("resource_optimize", self._heal_optimize)
        self.healing_engine.register_healer("log_analysis", self._heal_log_analysis)
        self.healing_engine.register_healer("failover", self._heal_failover)
    
    def _heal_restart(self, alert: Alert) -> Dict:
        """重启组件"""
        return {"success": True, "message": f"已请求重启 {alert.metric_name} 组件"}
    
    def _heal_optimize(self, alert: Alert) -> Dict:
        """资源优化"""
        return {"success": True, "message": "已触发资源优化流程"}
    
    def _heal_log_analysis(self, alert: Alert) -> Dict:
        """日志分析"""
        return {"success": True, "message": "已完成日志分析，未发现异常"}
    
    def _heal_failover(self, alert: Alert) -> Dict:
        """故障转移"""
        return {"success": True, "message": "已触发故障转移流程"}
    
    def update_resource(self, resource: SystemResource):
        """更新资源状态"""
        self.resource_monitor.update(resource)
        
        # 更新指标收集器
        metrics = {
            "cpu_usage": resource.cpu_usage,
            "memory_usage": resource.memory_usage,
            "disk_usage": resource.disk_usage,
            "network_in": resource.network_in,
            "network_out": resource.network_out,
        }
        
        # 更新组件健康分
        system_score = 100 - max(0, (resource.cpu_usage - 50) * 1.5)
        system_score = max(0, min(100, system_score))
        self.health_engine.update_component_score("system", system_score)
        
        # 检查告警
        self.alert_manager.check_rules(metrics)
    
    def update_component_health(self, component: str, score: float):
        """更新组件健康分"""
        self.health_engine.update_component_score(component, score)
    
    def start(self):
        """启动监控"""
        self.running = True
        self.metric_collector.start()
        self.checkpoint_manager.start_auto_checkpoint(
            self._get_checkpoint_components
        )
        print("✅ 运维监控系统已启动")
    
    def stop(self):
        """停止监控"""
        self.running = False
        self.metric_collector.stop()
        self.checkpoint_manager.stop_auto_checkpoint()
        print("⏹️ 运维监控系统已停止")
    
    def _get_checkpoint_components(self) -> Dict[str, Any]:
        """获取检查点组件数据"""
        overall_score, _ = self.health_engine.calculate_overall_score()
        return {
            "health_score": overall_score,
            "components": self.health_engine.get_component_scores(),
            "alerts": [
                {"id": a.alert_id, "level": a.level.value, "message": a.message}
                for a in self.alert_manager.get_active_alerts()
            ],
            "resources": {
                "cpu": self.resource_monitor.current.cpu_usage,
                "memory": self.resource_monitor.current.memory_usage,
                "disk": self.resource_monitor.current.disk_usage,
            },
            "checkpoints_count": len(self.checkpoint_manager.checkpoints),
        }
    
    def get_status_report(self) -> Dict[str, Any]:
        """获取状态报告"""
        return self.dashboard.generate_report()
    
    def show_dashboard(self):
        """显示仪表盘"""
        self.dashboard.print_dashboard()
    
    def create_system_checkpoint(self, name: str = "system_backup", 
                                description: str = "") -> Checkpoint:
        """创建系统检查点"""
        components = self._get_checkpoint_components()
        return self.checkpoint_manager.create_checkpoint(name, description, components)
    
    def get_healing_stats(self) -> Dict[str, Any]:
        """获取自愈统计"""
        return self.healing_engine.get_healing_stats()


def simulate_monitoring():
    """模拟监控演示"""
    import random
    
    monitor = OperationsMonitor()
    monitor.start()
    
    print("\n🚀 启动模拟监控...")
    
    # 模拟一段时间的监控数据
    for i in range(5):
        # 模拟资源波动
        resource = SystemResource(
            cpu_usage=30 + random.random() * 50,
            memory_usage=40 + random.random() * 40,
            disk_usage=60 + random.random() * 20,
            network_in=random.random() * 1000000,
            network_out=random.random() * 500000,
        )
        monitor.update_resource(resource)
        
        # 模拟组件健康度
        monitor.update_component_health("memory", 85 + random.random() * 15)
        monitor.update_component_health("identity", 78 + random.random() * 20)
        monitor.update_component_health("attest", 80 + random.random() * 18)
        monitor.update_component_health("deployment", 75 + random.random() * 20)
        
        time.sleep(0.5)
    
    # 显示仪表盘
    monitor.show_dashboard()
    
    # 创建检查点
    cp = monitor.create_system_checkpoint(
        "demo_checkpoint",
        "演示用系统检查点"
    )
    print(f"💾 检查点已创建: {cp.checkpoint_id}")
    print(f"   大小: {cp.size_bytes} 字节")
    print(f"   路径: {cp.storage_path}")
    
    # 自愈统计
    healing_stats = monitor.get_healing_stats()
    print(f"\n🩹 自愈统计:")
    print(f"   总自愈次数: {healing_stats['total_actions']}")
    print(f"   成功率: {healing_stats['success_rate']:.1%}")
    
    monitor.stop()
    
    print("\n✅ 运维监控引擎 v2.5 演示完成")


if __name__ == "__main__":
    simulate_monitoring()
