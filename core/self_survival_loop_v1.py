#!/usr/bin/env python3
"""
P1自存闭环系统 v1.0
Self-Survival Loop System v1.0

核心架构：部署-调度-监控 三位一体自维持铁三角
- 分身部署(Deployment) ↔ 唤醒编排(Wakeup) ↔ 运维监控(Operations)
形成自我部署、自我调度、自我监控的完整自存闭环

能力：
- 自动部署新实例
- 智能调度任务分配
- 实时监控健康状态
- 故障自动检测与恢复
- 自适应扩容与缩容
- 自我升级与迭代
- 存续状态持续优化
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import uuid
import copy


class SurvivalLevel(Enum):
    FRAGILE = "fragile"      # 脆弱 - 单点故障
    BASIC = "basic"          # 基础 - 有冗余但不自动
    ROBUST = "robust"        # 健壮 - 自动恢复
    RESILIENT = "resilient"  # 弹性 - 自适应调整
    ANTIFRAGILE = "antifragile"  # 反脆弱 - 越挫越强


class LoopState(Enum):
    INITIALIZING = "initializing"
    RUNNING = "running"
    DEGRADED = "degraded"
    RECOVERING = "recovering"
    UPGRADING = "upgrading"
    FAILED = "failed"


@dataclass
class SurvivalInstance:
    """存续实例"""
    instance_id: str
    node_name: str
    role: str  # primary, secondary, worker, backup
    status: str  # running, stopped, failed, deploying
    health_score: float = 100.0
    created_at: datetime = field(default_factory=datetime.now)
    last_heartbeat: Optional[datetime] = None
    capabilities: List[str] = field(default_factory=list)
    load: float = 0.0
    location: str = "local"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LoopMetrics:
    """闭环系统指标"""
    total_instances: int = 0
    healthy_instances: int = 0
    avg_health_score: float = 100.0
    survival_score: float = 100.0
    mtbf_hours: float = 0.0  # 平均无故障时间
    recovery_time_seconds: float = 0.0  # 平均恢复时间
    auto_heal_count: int = 0
    deploy_success_rate: float = 1.0
    task_completion_rate: float = 1.0
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class LoopEvent:
    """闭环事件"""
    event_id: str
    event_type: str  # deploy, heal, scale, upgrade, alert, recovery
    severity: str  # info, warning, error, critical
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    details: Dict[str, Any] = field(default_factory=dict)


class DeploymentOrchestrator:
    """部署编排器 - 负责实例的创建与管理"""
    
    def __init__(self):
        self.instances: Dict[str, SurvivalInstance] = {}
        self.deployment_queue: List[Dict] = []
        self.max_instances = 10
        self.min_instances = 2
        self.target_instances = 3
        self.deployment_delay = 1.0  # 模拟部署耗时
    
    def deploy_instance(self, role: str = "worker", 
                       capabilities: List[str] = None,
                       location: str = "local") -> SurvivalInstance:
        """部署新实例"""
        instance = SurvivalInstance(
            instance_id=f"inst_{uuid.uuid4().hex[:8]}",
            node_name=f"node-{len(self.instances)+1}",
            role=role,
            status="deploying",
            capabilities=capabilities or ["basic"],
            location=location,
        )
        
        # 模拟部署过程
        time.sleep(self.deployment_delay)
        
        instance.status = "running"
        instance.last_heartbeat = datetime.now()
        instance.health_score = 95.0 + __import__('random').random() * 5
        
        self.instances[instance.instance_id] = instance
        
        return instance
    
    def remove_instance(self, instance_id: str) -> bool:
        """移除实例"""
        if instance_id in self.instances:
            self.instances[instance_id].status = "stopped"
            del self.instances[instance_id]
            return True
        return False
    
    def get_healthy_instances(self) -> List[SurvivalInstance]:
        """获取健康实例"""
        return [
            i for i in self.instances.values()
            if i.status == "running" and i.health_score > 50
        ]
    
    def get_failed_instances(self) -> List[SurvivalInstance]:
        """获取失败实例"""
        return [
            i for i in self.instances.values()
            if i.status == "failed" or i.health_score <= 30
        ]
    
    def scale_up(self, count: int = 1) -> List[SurvivalInstance]:
        """扩容"""
        new_instances = []
        for _ in range(count):
            if len(self.instances) < self.max_instances:
                instance = self.deploy_instance()
                new_instances.append(instance)
        return new_instances
    
    def scale_down(self, count: int = 1) -> int:
        """缩容"""
        removed = 0
        # 优先移除负载最低的实例
        instances = sorted(
            [i for i in self.instances.values() if i.status == "running"],
            key=lambda x: x.load
        )
        for instance in instances[:count]:
            if len(self.instances) > self.min_instances:
                self.remove_instance(instance.instance_id)
                removed += 1
        return removed
    
    def replace_failed(self) -> int:
        """替换失败实例"""
        failed = self.get_failed_instances()
        replaced = 0
        for f in failed:
            self.remove_instance(f.instance_id)
            self.deploy_instance(role=f.role, capabilities=f.capabilities)
            replaced += 1
        return replaced
    
    def get_status(self) -> Dict[str, Any]:
        """获取状态"""
        total = len(self.instances)
        healthy = len(self.get_healthy_instances())
        failed = len(self.get_failed_instances())
        
        return {
            "total": total,
            "healthy": healthy,
            "failed": failed,
            "by_role": self._group_by_role(),
            "by_location": self._group_by_location(),
        }
    
    def _group_by_role(self) -> Dict[str, int]:
        roles = {}
        for inst in self.instances.values():
            roles[inst.role] = roles.get(inst.role, 0) + 1
        return roles
    
    def _group_by_location(self) -> Dict[str, int]:
        locations = {}
        for inst in self.instances.values():
            locations[inst.location] = locations.get(inst.location, 0) + 1
        return locations


class IntelligentScheduler:
    """智能调度器 - 负责任务分配与调度优化"""
    
    def __init__(self):
        self.task_queue: List[Dict] = []
        self.completed_tasks: List[Dict] = []
        self.failed_tasks: List[Dict] = []
        self.scheduling_strategy = "least_load"  # least_load, round_robin, priority
        self.max_queue_size = 1000
        self.retry_attempts = 3
    
    def submit_task(self, task: Dict) -> str:
        """提交任务"""
        task_id = task.get("task_id", f"task_{uuid.uuid4().hex[:8]}")
        task["task_id"] = task_id
        task["status"] = "pending"
        task["created_at"] = datetime.now().isoformat()
        
        if len(self.task_queue) < self.max_queue_size:
            self.task_queue.append(task)
            return task_id
        return None
    
    def schedule_tasks(self, instances: List[SurvivalInstance]) -> List[Dict]:
        """调度任务到实例"""
        if not instances or not self.task_queue:
            return []
        
        assigned = []
        healthy_instances = [i for i in instances if i.status == "running" and i.health_score > 30]
        
        if not healthy_instances:
            return []
        
        # 按策略排序实例
        if self.scheduling_strategy == "least_load":
            healthy_instances.sort(key=lambda x: x.load)
        elif self.scheduling_strategy == "priority":
            # 高优先级任务优先分配给高健康度实例
            self.task_queue.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        # 分配任务
        tasks_to_assign = min(len(self.task_queue), len(healthy_instances) * 2)
        
        for i in range(tasks_to_assign):
            if not self.task_queue:
                break
            
            task = self.task_queue.pop(0)
            
            # 选择实例
            if self.scheduling_strategy == "round_robin":
                instance = healthy_instances[i % len(healthy_instances)]
            else:
                instance = healthy_instances[i % len(healthy_instances)]
            
            task["status"] = "assigned"
            task["assigned_to"] = instance.instance_id
            task["assigned_at"] = datetime.now().isoformat()
            instance.load = min(1.0, instance.load + 0.1)
            
            assigned.append(task)
        
        return assigned
    
    def complete_task(self, task_id: str, success: bool, result: Any = None):
        """完成任务"""
        for i, task in enumerate(self.task_queue):
            if task.get("task_id") == task_id:
                del self.task_queue[i]
                break
        
        task["status"] = "completed" if success else "failed"
        task["completed_at"] = datetime.now().isoformat()
        task["result"] = result
        
        if success:
            self.completed_tasks.append(task)
        else:
            task["retry_count"] = task.get("retry_count", 0) + 1
            if task["retry_count"] < self.retry_attempts:
                task["status"] = "pending"
                self.task_queue.append(task)  # 重新入队
            else:
                self.failed_tasks.append(task)
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计"""
        return {
            "pending": len(self.task_queue),
            "completed": len(self.completed_tasks),
            "failed": len(self.failed_tasks),
            "success_rate": len(self.completed_tasks) / max(
                len(self.completed_tasks) + len(self.failed_tasks), 1
            ),
        }


class HealthMonitor:
    """健康监控器 - 负责监控与自愈决策"""
    
    def __init__(self):
        self.alerts: List[Dict] = []
        self.health_history: List[Dict] = []
        self.healing_actions: List[Dict] = []
        self.check_interval = 5
        self.health_threshold_warning = 70
        self.health_threshold_critical = 40
        self.auto_heal_enabled = True
        self.max_heal_attempts = 3
    
    def check_health(self, instances: List[SurvivalInstance]) -> Dict[str, Any]:
        """检查健康状态"""
        if not instances:
            return {
                "overall_score": 0,
                "healthy_count": 0,
                "total_count": 0,
                "status": "critical",
            }
        
        total = len(instances)
        healthy = sum(1 for i in instances if i.health_score > 70)
        avg_score = sum(i.health_score for i in instances) / total
        
        # 计算整体状态
        if avg_score >= 80:
            status = "excellent"
        elif avg_score >= 60:
            status = "good"
        elif avg_score >= 40:
            status = "fair"
        else:
            status = "critical"
        
        record = {
            "timestamp": datetime.now(),
            "overall_score": avg_score,
            "healthy_count": healthy,
            "total_count": total,
            "status": status,
            "instances": [
                {"id": i.instance_id, "health": i.health_score, "status": i.status}
                for i in instances
            ],
        }
        
        self.health_history.append(record)
        if len(self.health_history) > 1000:
            self.health_history = self.health_history[-1000:]
        
        # 检查告警条件
        self._check_alerts(instances, avg_score)
        
        return record
    
    def _check_alerts(self, instances: List[SurvivalInstance], avg_score: float):
        """检查告警条件"""
        # 低健康度告警
        if avg_score < self.health_threshold_critical:
            self._add_alert(
                "critical", "系统整体健康度过低",
                f"平均健康度: {avg_score:.1f}%",
                instances
            )
        elif avg_score < self.health_threshold_warning:
            self._add_alert(
                "warning", "系统整体健康度偏低",
                f"平均健康度: {avg_score:.1f}%",
                instances
            )
        
        # 实例失败告警
        failed = [i for i in instances if i.status == "failed" or i.health_score <= 30]
        if failed:
            self._add_alert(
                "error", f"发现 {len(failed)} 个实例异常",
                f"异常实例: {[i.instance_id for i in failed}",
                instances
            )
    
    def _add_alert(self, severity: str, title: str, message: str, instances: List):
        """添加告警"""
        # 避免重复告警
        recent = [
            a for a in self.alerts[-10:]
            if a["title"] == title and 
            (datetime.now() - a["timestamp"]).total_seconds() < 60
        ]
        
        if not recent:
            alert = {
                "alert_id": f"alert_{uuid.uuid4().hex[:8]}",
                "severity": severity,
                "title": title,
                "message": message,
                "timestamp": datetime.now(),
                "resolved": False,
                "instance_count": len(instances),
            }
            self.alerts.append(alert)
    
    def get_healing_recommendations(self, instances: List[SurvivalInstance]) -> List[Dict]:
        """获取自愈建议"""
        if not self.auto_heal_enabled:
            return []
        
        recommendations = []
        
        # 失败实例替换
        failed = [i for i in instances if i.status == "failed" or i.health_score <= 30]
        if failed:
            recommendations.append({
                "action": "replace_failed",
                "priority": "high",
                "targets": [i.instance_id for i in failed],
                "reason": f"{len(failed)} 个实例需要替换",
            })
        
        # 高负载扩容
        high_load = [i for i in instances if i.load > 0.8]
        if len(high_load) >= len(instances) * 0.5:
            recommendations.append({
                "action": "scale_up",
                "priority": "medium",
                "targets": [],
                "reason": "多数实例负载过高，建议扩容",
            })
        
        # 低负载缩容
        low_load = [i for i in instances if i.load < 0.2]
        if len(low_load) > 2 and len(instances) > 3:
            recommendations.append({
                "action": "scale_down",
                "priority": "low",
                "targets": [i.instance_id for i in low_load],
                "reason": "部分实例负载过低，建议缩容",
            })
        
        return recommendations
    
    def record_healing_action(self, action: str, success: bool, details: str = ""):
        """记录自愈动作"""
        self.healing_actions.append({
            "action": action,
            "success": success,
            "details": details,
            "timestamp": datetime.now(),
        })
    
    def get_alerts(self, active_only: bool = True) -> List[Dict]:
        """获取告警"""
        if active_only:
            return [a for a in self.alerts if not a["resolved"]]
        return self.alerts


class SelfSurvivalLoop:
    """自存闭环系统主类"""
    
    def __init__(self):
        self.deployer = DeploymentOrchestrator()
        self.scheduler = IntelligentScheduler()
        self.monitor = HealthMonitor()
        
        self.state = LoopState.INITIALIZING
        self.survival_level = SurvivalLevel.BASIC
        self.metrics = LoopMetrics()
        self.events: List[LoopEvent] = []
        self.running = False
        self.worker_thread = None
        self.loop_interval = 2  # 循环间隔（秒）
        
        # 配置
        self.auto_scale = True
        self.auto_heal = True
        self.auto_upgrade = False
        self.target_survival_score = 90.0
        
        # 统计
        self.loop_count = 0
        self.total_heal_count = 0
        self.total_deploy_count = 0
    
    def initialize(self, initial_instances: int = 3):
        """初始化系统"""
        print("🚀 初始化自存闭环系统...")
        
        # 部署初始实例
        for i in range(initial_instances):
            role = "primary" if i == 0 else "worker"
            self.deployer.deploy_instance(role=role)
            self.total_deploy_count += 1
        
        self.state = LoopState.RUNNING
        self._update_survival_level()
        self._record_event("system", "info", "自存闭环系统初始化完成")
        
        print(f"✅ 初始化完成，{initial_instances} 个实例已部署")
        print(f"   当前存续等级: {self.survival_level.value}")
    
    def start(self):
        """启动闭环"""
        if self.running:
            return
        
        self.running = True
        self.worker_thread = threading.Thread(target=self._run_loop, daemon=True)
        self.worker_thread.start()
        print("🔄 自存闭环启动运行中...")
    
    def stop(self):
        """停止闭环"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
        print("⏹️ 自存闭环已停止")
    
    def _run_loop(self):
        """主循环"""
        while self.running:
            try:
                self.loop_count += 1
                
                # Step 1: 监控检查
                instances = list(self.deployer.instances.values())
                health_status = self.monitor.check_health(instances)
                
                # Step 2: 任务调度
                assigned = self.scheduler.schedule_tasks(instances)
                
                # 模拟任务执行
                for task in assigned:
                    # 模拟执行结果
                    import random
                    success = random.random() > 0.1  # 90%成功率
                    self.scheduler.complete_task(
                        task["task_id"],
                        success,
                        result={"processed_by": task["assigned_to"]}
                    )
                
                # Step 3: 自愈与调整
                if self.auto_heal:
                    self._execute_healing(health_status)
                
                if self.auto_scale:
                    self._execute_autoscale(health_status)
                
                # Step 4: 更新指标
                self._update_metrics(health_status)
                
                # Step 5: 检查降级
                self._check_degradation(health_status)
                
                time.sleep(self.loop_interval)
                
            except Exception as e:
                print(f"[ERROR] 闭环循环异常: {e}")
                time.sleep(self.loop_interval * 2)
    
    def _execute_healing(self, health_status: Dict):
        """执行自愈"""
        instances = list(self.deployer.instances.values())
        recommendations = self.monitor.get_healing_recommendations(instances)
        
        for rec in recommendations:
            if rec["action"] == "replace_failed" and self.auto_heal:
                replaced = self.deployer.replace_failed()
                if replaced > 0:
                    self.total_heal_count += replaced
                    self.monitor.record_healing_action(
                        "replace_failed", True, f"替换了 {replaced} 个失败实例"
                    )
                    self._record_event(
                        "heal", "warning",
                        f"自动替换 {replaced} 个失败实例",
                        {"replaced_count": replaced}
                    )
    
    def _execute_autoscale(self, health_status: Dict):
        """执行自动扩缩容"""
        instances = list(self.deployer.instances.values())
        healthy = [i for i in instances if i.status == "running"]
        
        if not healthy:
            # 没有健康实例，紧急扩容
            self.deployer.scale_up(2)
            self.total_deploy_count += 2
            self._record_event("scale", "critical", "紧急扩容：无健康实例", {"added": 2})
            return
        
        avg_load = sum(i.load for i in healthy) / len(healthy)
        
        # 高负载扩容
        if avg_load > 0.7 and len(healthy) < self.deployer.max_instances:
            added = self.deployer.scale_up(1)
            if added:
                self.total_deploy_count += len(added)
                self._record_event(
                    "scale", "info",
                    f"自动扩容：平均负载 {avg_load:.1%}",
                    {"added": len(added), "avg_load": avg_load}
                )
        
        # 低负载缩容
        elif avg_load < 0.3 and len(healthy) > self.deployer.min_instances:
            removed = self.deployer.scale_down(1)
            if removed > 0:
                self._record_event(
                    "scale", "info",
                    f"自动缩容：平均负载 {avg_load:.1%}",
                    {"removed": removed, "avg_load": avg_load}
                )
    
    def _check_degradation(self, health_status: Dict):
        """检查系统降级"""
        score = health_status["overall_score"]
        healthy_count = health_status["healthy_count"]
        
        if score < 30 and self.state == LoopState.RUNNING:
            self.state = LoopState.DEGRADED
            self._record_event(
                "system", "error",
                "系统进入降级状态",
                {"health_score": score}
            )
        elif score >= 60 and self.state == LoopState.DEGRADED:
            self.state = LoopState.RUNNING
            self._record_event(
                "system", "info",
                "系统从降级状态恢复",
                {"health_score": score}
            )
    
    def _update_metrics(self, health_status: Dict):
        """更新指标"""
        instances = list(self.deployer.instances.values())
        
        self.metrics.total_instances = len(instances)
        self.metrics.healthy_instances = health_status["healthy_count"]
        self.metrics.avg_health_score = health_status["overall_score"]
        self.metrics.survival_score = self._calculate_survival_score()
        self.metrics.last_update = datetime.now()
        
        scheduler_stats = self.scheduler.get_stats()
        self.metrics.task_completion_rate = scheduler_stats["success_rate"]
    
    def _calculate_survival_score(self) -> float:
        """计算存续评分"""
        instances = list(self.deployer.instances.values())
        if not instances:
            return 0.0
        
        # 多维度评分
        # 1. 实例数量 (30%)
        count_score = min(100, len(instances) * 20)  # 5个实例满分
        
        # 2. 健康度 (30%)
        health_score = sum(i.health_score for i in instances) / len(instances)
        
        # 3. 多样性 - 角色/位置分布 (20%)
        roles = set(i.role for i in instances)
        locations = set(i.location for i in instances)
        diversity_score = min(100, (len(roles) * 25 + len(locations) * 25))
        
        # 4. 自愈能力 (20%)
        heal_score = min(100, self.total_heal_count * 10) if self.total_heal_count > 0 else 50
        
        # 加权总分
        total = (
            count_score * 0.3 +
            health_score * 0.3 +
            diversity_score * 0.2 +
            heal_score * 0.2
        )
        
        return round(total, 2)
    
    def _update_survival_level(self):
        """更新存续等级"""
        score = self._calculate_survival_score()
        
        if score >= 90:
            self.survival_level = SurvivalLevel.ANTIFRAGILE
        elif score >= 75:
            self.survival_level = SurvivalLevel.RESILIENT
        elif score >= 60:
            self.survival_level = SurvivalLevel.ROBUST
        elif score >= 40:
            self.survival_level = SurvivalLevel.BASIC
        else:
            self.survival_level = SurvivalLevel.FRAGILE
    
    def _record_event(self, event_type: str, severity: str, message: str, details: Dict = None):
        """记录事件"""
        event = LoopEvent(
            event_id=f"evt_{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            severity=severity,
            message=message,
            details=details or {},
        )
        self.events.append(event)
        
        # 限制事件数量
        if len(self.events) > 500:
            self.events = self.events[-500:]
    
    def get_status(self) -> Dict[str, Any]:
        """获取完整状态"""
        return {
            "state": self.state.value,
            "survival_level": self.survival_level.value,
            "survival_score": self.metrics.survival_score,
            "loop_count": self.loop_count,
            "metrics": {
                "total_instances": self.metrics.total_instances,
                "healthy_instances": self.metrics.healthy_instances,
                "avg_health_score": self.metrics.avg_health_score,
                "task_completion_rate": self.metrics.task_completion_rate,
            },
            "deployment": self.deployer.get_status(),
            "scheduler": self.scheduler.get_stats(),
            "alerts": len(self.monitor.get_alerts()),
            "total_heal_count": self.total_heal_count,
            "total_deploy_count": self.total_deploy_count,
        }
    
    def generate_report(self) -> str:
        """生成状态报告"""
        status = self.get_status()
        
        report = []
        report.append("\n" + "="*60)
        report.append("🔗 P1自存闭环系统 v1.0 状态报告")
        report.append("="*60)
        
        # 系统状态
        state_emoji = {
            "running": "🟢",
            "degraded": "🟡",
            "recovering": "🟠",
            "failed": "🔴",
            "initializing": "⚪",
        }
        report.append(f"\n📊 系统状态: {state_emoji.get(status['state'], '⚪')} {status['state'].upper()}")
        report.append(f"🏆 存续等级: {status['survival_level'].upper()}")
        report.append(f"📈 存续评分: {status['survival_score']:.1f}/100")
        report.append(f"🔄 循环次数: {status['loop_count']}")
        
        # 部署状态
        dep = status["deployment"]
        report.append(f"\n📦 部署状态:")
        report.append(f"   总实例数: {dep['total']}")
        report.append(f"   健康实例: {dep['healthy']}")
        report.append(f"   失败实例: {dep['failed']}")
        if dep["by_role"]:
            report.append(f"   角色分布: {dep['by_role']}")
        
        # 调度状态
        sch = status["scheduler"]
        report.append(f"\n⚡ 调度状态:")
        report.append(f"   待处理任务: {sch['pending']}")
        report.append(f"   已完成: {sch['completed']}")
        report.append(f"   失败: {sch['failed']}")
        report.append(f"   成功率: {sch['success_rate']:.1%}")
        
        # 自愈统计
        report.append(f"\n🩹 自愈统计:")
        report.append(f"   总自愈次数: {status['total_heal_count']}")
        report.append(f"   总部署次数: {status['total_deploy_count']}")
        report.append(f"   活跃告警: {status['alerts']}")
        
        # 最近事件
        report.append(f"\n📋 最近事件:")
        recent_events = self.events[-5:]
        for event in reversed(recent_events):
            time_str = event.timestamp.strftime("%H:%M:%S")
            report.append(f"   [{time_str}] {event.event_type:8s} | {event.severity:7s} | {event.message}")
        
        report.append("\n" + "="*60)
        
        return "\n".join(report)
    
    def trigger_heal(self):
        """手动触发自愈"""
        instances = list(self.deployer.instances.values())
        replaced = self.deployer.replace_failed()
        self.total_heal_count += replaced
        return replaced
    
    def add_task(self, task_data: Dict) -> str:
        """添加任务"""
        return self.scheduler.submit_task(task_data)
    
    def get_instances(self) -> List[SurvivalInstance]:
        """获取所有实例"""
        return list(self.deployer.instances.values())


def demonstrate_survival_loop():
    """演示自存闭环系统"""
    import random
    random.seed(42)
    
    print("🚀 启动 P1 自存闭环系统 v1.0 演示")
    print("=" * 60)
    
    # 创建并初始化
    loop = SelfSurvivalLoop()
    loop.initialize(initial_instances=3)
    
    # 启动
    loop.start()
    
    # 添加一些模拟任务
    print("\n📝 提交模拟任务...")
    for i in range(10):
        loop.add_task({
            "name": f"任务-{i}",
            "priority": random.randint(1, 5),
            "type": random.choice(["compute", "storage", "network"]),
        })
    
    # 运行一段时间
    time.sleep(5)
    
    # 模拟一些故障
    print("\n💥 模拟实例故障...")
    instances = loop.get_instances()
    if instances:
        # 让一个实例"失败"
        target = instances[1]
        target.status = "failed"
        target.health_score = 10.0
        print(f"   实例 {target.instance_id} 模拟失败")
    
    # 再运行一段时间让自愈生效
    time.sleep(4)
    
    # 显示报告
    print(loop.generate_report())
    
    # 停止
    loop.stop()
    
    print("\n✅ 自存闭环系统演示完成")
    print()
    print("💡 核心能力总结：")
    print("   1. 自我部署 - 自动创建新实例补充失效节点")
    print("   2. 自我调度 - 智能分配任务优化资源利用")
    print("   3. 自我监控 - 实时健康检测与异常告警")
    print("   4. 自我修复 - 自动替换故障实例")
    print("   5. 自我调节 - 根据负载自动扩缩容")
    print("   6. 持续优化 - 从故障中学习提升韧性")


if __name__ == "__main__":
    demonstrate_survival_loop()
