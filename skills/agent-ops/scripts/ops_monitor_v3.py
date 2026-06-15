#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体运维监控 v3.0 - 全链路健康监控与自愈系统

核心能力：
1. 多模块健康度聚合监控（9大模块统一监控
2. 实时告警系统（分级告警、多渠道通知
3. 智能巡检调度（定时巡检、异常触发
4. 运营仪表盘（整体状态可视化
5. 自愈机制（常见故障自动恢复
6. 运营报表（日报/周报/月报自动生成

@author: 元界
@version: 3.0.0
"""

import os
import sys
import json
import time
import uuid
import hashlib
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path
import threading

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('ops_v3')


# ============================================================
# 数据模型
# ============================================================

@dataclass
class ModuleHealth:
    """模块健康度"""
    module_name: str
    module_type: str  # foundation/core/platform/ecosystem
    status: str  # healthy/warning/critical/unknown
    health_score: float  # 0-100
    last_check: str
    issues: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Alert:
    """告警"""
    alert_id: str
    level: str  # info/warning/error/critical
    module: str
    title: str
    message: str
    created_at: str
    status: str  # active/acknowledged/resolved
    resolved_at: str = ""
    resolution_note: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InspectionResult:
    """巡检结果"""
    inspection_id: str
    start_time: str
    end_time: str
    modules_checked: int
    issues_found: int
    alerts_generated: int
    details: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SelfHealingAction:
    """自愈动作"""
    action_id: str
    action_type: str  # restart/cleanup/rollback/scale/notify
    target_module: str
    status: str  # pending/running/success/failed
    result: str = ""
    executed_at: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class OpsReport:
    """运营报表"""
    report_id: str
    period: str  # daily/weekly/monthly
    start_date: str
    end_date: str
    summary: dict = field(default_factory=dict)
    alerts: List[dict] = field(default_factory=list)
    health_trends: List[dict] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 监控检查器
# ============================================================

class HealthChecker:
    """健康度检查器基类"""
    
    def check(self) -> ModuleHealth:
        raise NotImplementedError


class FileSystemChecker(HealthChecker):
    """文件系统检查"""
    
    def __init__(self, path: str, name: str = "filesystem"):
        self.path = Path(path)
        self.name = name
    
    def check(self) -> ModuleHealth:
        issues = []
        score = 100
        
        # 检查路径是否存在
        if not self.path.exists():
            issues.append(f"路径不存在: {self.path}")
            score = 0
        else:
            # 检查磁盘空间
            try:
                stat = os.statvfs(self.path)
                total_gb = (stat.f_frsize * stat.f_blocks) / (1024**3)
                free_gb = (stat.f_frsize * stat.f_bavail) / (1024**3)
                usage_percent = ((total_gb - free_gb) / total_gb) * 100 if total_gb > 0 else 0
                
                if usage_percent > 90:
                    issues.append(f"磁盘使用率过高: {usage_percent:.1f}%")
                    score -= 40
                elif usage_percent > 75:
                    issues.append(f"磁盘使用率偏高: {usage_percent:.1f}%")
                    score -= 15
                
                metrics = {
                    "total_gb": round(total_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "usage_percent": round(usage_percent, 1)
                }
            except Exception as e:
                issues.append(f"磁盘检查失败: {e}")
                score -= 20
                metrics = {"error": str(e)}
        
        status = "healthy" if score >= 80 else "warning" if score >= 50 else "critical"
        
        return ModuleHealth(
            module_name=self.name,
            module_type="foundation",
            status=status,
            health_score=max(0, score),
            last_check=datetime.now().isoformat(),
            issues=issues,
            metrics=metrics
        )


class ProcessChecker(HealthChecker):
    """进程检查"""
    
    def __init__(self, process_name: str, name: str = None):
        self.process_name = process_name
        self.name = name or f"process_{process_name}"
    
    def check(self) -> ModuleHealth:
        issues = []
        score = 100
        
        try:
            import subprocess
            result = subprocess.run(
                ['pgrep', '-f', self.process_name],
                capture_output=True, text=True
            )
            pids = [p for p in result.stdout.strip().split('\n') if p]
            
            if not pids:
                issues.append(f"进程未运行: {self.process_name}")
                score = 0
            else:
                metrics = {"pid_count": len(pids), "pids": pids[:5]}
        except Exception as e:
            issues.append(f"进程检查失败: {e}")
            score = 50
            metrics = {"error": str(e)}
        
        status = "healthy" if score >= 80 else "warning" if score >= 50 else "critical"
        
        return ModuleHealth(
            module_name=self.name,
            module_type="core",
            status=status,
            health_score=max(0, score),
            last_check=datetime.now().isoformat(),
            issues=issues,
            metrics=metrics
        )


class ConnectivityChecker(HealthChecker):
    """连通性检查"""
    
    def __init__(self, target: str, name: str = None, timeout: int = 5):
        self.target = target
        self.name = name or f"connect_{target}"
        self.timeout = timeout
    
    def check(self) -> ModuleHealth:
        issues = []
        score = 100
        metrics = {}
        
        try:
            import subprocess
            start = time.time()
            
            # ping检测
            result = subprocess.run(
                ['ping', '-c', '1', '-W', str(self.timeout), self.target],
                capture_output=True, text=True, timeout=self.timeout + 2
            )
            
            latency = (time.time() - start) * 1000
            
            if result.returncode != 0:
                issues.append(f"无法连接: {self.target}")
                score = 0
            else:
                metrics["latency_ms"] = round(latency, 2)
                
                if latency > 500:
                    issues.append(f"延迟过高: {latency:.0f}ms")
                    score -= 30
                elif latency > 200:
                    issues.append(f"延迟偏高: {latency:.0f}ms")
                    score -= 10
        except Exception as e:
            issues.append(f"连接检查失败: {e}")
            score = 50
            metrics["error"] = str(e)
        
        status = "healthy" if score >= 80 else "warning" if score >= 50 else "critical"
        
        return ModuleHealth(
            module_name=self.name,
            module_type="core",
            status=status,
            health_score=max(0, score),
            last_check=datetime.now().isoformat(),
            issues=issues,
            metrics=metrics
        )


class DataIntegrityChecker(HealthChecker):
    """数据完整性检查"""
    
    def __init__(self, data_path: str, name: str = "data_integrity"):
        self.data_path = Path(data_path)
        self.name = name
    
    def check(self) -> ModuleHealth:
        issues = []
        score = 100
        metrics = {}
        
        if not self.data_path.exists():
            issues.append(f"数据路径不存在: {self.data_path}")
            score = 0
        else:
            try:
                # 检查关键文件
                critical_files = []
                missing_files = []
                corrupted_files = []
                
                for f in self.data_path.rglob('*.json'):
                    critical_files.append(str(f))
                    try:
                        with open(f, 'r', encoding='utf-8') as fh:
                            json.load(fh)
                    except json.JSONDecodeError:
                        corrupted_files.append(str(f))
                        score -= 20
                
                metrics["total_files"] = len(critical_files)
                metrics["corrupted_files"] = len(corrupted_files)
                
                if corrupted_files:
                    issues.append(f"损坏的JSON文件: {len(corrupted_files)}个")
            except Exception as e:
                issues.append(f"数据检查失败: {e}")
                score -= 30
        
        status = "healthy" if score >= 80 else "warning" if score >= 50 else "critical"
        
        return ModuleHealth(
            module_name=self.name,
            module_type="foundation",
            status=status,
            health_score=max(0, score),
            last_check=datetime.now().isoformat(),
            issues=issues,
            metrics=metrics
        )


# ============================================================
# 告警管理器
# ============================================================

class AlertManager:
    """告警管理器"""
    
    def __init__(self, storage_path: str):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.alerts_file = self.storage_path / 'alerts.json'
        self.alerts: Dict[str, Alert] = {}
        
        # 告警回调
        self.callbacks: Dict[str, List[Callable]] = {
            "info": [],
            "warning": [],
            "error": [],
            "critical": []
        }
        
        self._load_alerts()
    
    def _load_alerts(self):
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for aid, alert_data in data.items():
                        self.alerts[aid] = Alert(**alert_data)
            except Exception as e:
                logger.error(f"加载告警数据失败: {e}")
    
    def _save_alerts(self):
        try:
            with open(self.alerts_file, 'w', encoding='utf-8') as f:
                json.dump({k: v.to_dict() for k, v in self.alerts.items()}, 
                         f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存告警数据失败: {e}")
    
    def create_alert(self, level: str, module: str, title: str, 
                    message: str) -> Alert:
        """创建告警"""
        alert_id = f"alert_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        alert = Alert(
            alert_id=alert_id,
            level=level,
            module=module,
            title=title,
            message=message,
            created_at=now,
            status="active"
        )
        
        self.alerts[alert_id] = alert
        self._save_alerts()
        
        logger.warning(f"新告警 [{level}] {module}: {title}")
        
        # 触发回调
        for callback in self.callbacks.get(level, []):
            try:
                callback(alert)
            except Exception as e:
                logger.error(f"告警回调执行失败: {e}")
        
        return alert
    
    def acknowledge_alert(self, alert_id: str) -> bool:
        """确认告警"""
        if alert_id not in self.alerts:
            return False
        
        self.alerts[alert_id].status = "acknowledged"
        self._save_alerts()
        return True
    
    def resolve_alert(self, alert_id: str, note: str = "") -> bool:
        """解决告警"""
        if alert_id not in self.alerts:
            return False
        
        alert = self.alerts[alert_id]
        alert.status = "resolved"
        alert.resolved_at = datetime.now().isoformat()
        alert.resolution_note = note
        self._save_alerts()
        
        logger.info(f"告警已解决: {alert.title}")
        return True
    
    def get_active_alerts(self, level: str = None) -> List[Alert]:
        """获取活跃告警"""
        alerts = [a for a in self.alerts.values() if a.status == "active"]
        if level:
            alerts = [a for a in alerts if a.level == level]
        return sorted(alerts, key=lambda x: x.created_at, reverse=True)
    
    def add_callback(self, level: str, callback: Callable):
        """添加告警回调"""
        if level in self.callbacks:
            self.callbacks[level].append(callback)


# ============================================================
# 自愈引擎
# ============================================================

class SelfHealingEngine:
    """自愈引擎"""
    
    def __init__(self, ops_monitor: 'OpsMonitorV3'):
        self.monitor = ops_monitor
        self.actions: Dict[str, SelfHealingAction] = {}
        self.healing_rules = []
        
        # 注册默认自愈规则
        self._register_default_rules()
    
    def _register_default_rules(self):
        """注册默认自愈规则"""
        # 规则：磁盘使用率过高 -> 清理临时文件
        self.healing_rules.append({
            "trigger": "high_disk_usage",
            "condition": lambda h: h.module_name == "filesystem" and h.health_score < 60,
            "action": "clean_temp_files",
            "description": "清理临时文件释放空间"
        })
    
    def analyze_and_heal(self, health: ModuleHealth) -> Optional[SelfHealingAction]:
        """分析健康状态并执行自愈"""
        for rule in self.healing_rules:
            try:
                if rule["condition"](health):
                    return self._execute_healing(rule, health)
            except Exception as e:
                logger.error(f"自愈规则执行异常: {e}")
        
        return None
    
    def _execute_healing(self, rule: dict, health: ModuleHealth) -> SelfHealingAction:
        """执行自愈动作"""
        action_id = f"heal_{uuid.uuid4().hex[:12]}"
        
        action = SelfHealingAction(
            action_id=action_id,
            action_type=rule["action"],
            target_module=health.module_name,
            status="running",
            executed_at=datetime.now().isoformat()
        )
        
        self.actions[action_id] = action
        
        try:
            # 执行具体自愈逻辑
            if rule["action"] == "clean_temp_files":
                result = self._clean_temp_files()
            else:
                result = f"未知动作类型: {rule['action']}"
            
            action.status = "success"
            action.result = result
            
            logger.info(f"自愈成功: {rule['description']} - {result}")
            
        except Exception as e:
            action.status = "failed"
            action.result = str(e)
            logger.error(f"自愈失败: {rule['description']} - {e}")
        
        return action
    
    def _clean_temp_files(self) -> str:
        """清理临时文件"""
        temp_dirs = ['/tmp', '/var/tmp']
        cleaned_size = 0
        
        for temp_dir in temp_dirs:
            if not os.path.exists(temp_dir):
                continue
            
            try:
                for root, dirs, files in os.walk(temp_dir):
                    for f in files:
                        fp = os.path.join(root, f)
                        try:
                            # 只清理超过1小时的文件
                            if time.time() - os.path.getmtime(fp) > 3600:
                                size = os.path.getsize(fp)
                                os.remove(fp)
                                cleaned_size += size
                        except:
                            pass
            except:
                pass
        
        cleaned_mb = cleaned_size / (1024 * 1024)
        return f"清理了 {cleaned_mb:.2f} MB 临时文件"


# ============================================================
# 运维监控主引擎
# ============================================================

class OpsMonitorV3:
    """智能体运维监控 v3.0 主引擎"""
    
    def __init__(self, data_path: str = None):
        """
        初始化运维监控
        
        Args:
            data_path: 数据存储路径
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'ops_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 组件初始化
        self.alert_manager = AlertManager(str(self.data_path / 'alerts'))
        self.self_healing = SelfHealingEngine(self)
        
        # 检查器注册
        self.checkers: Dict[str, HealthChecker] = {}
        
        # 健康度历史
        self.health_history: List[dict] = []
        self.history_file = self.data_path / 'health_history.json'
        self._load_history()
        
        # 巡检调度
        self._inspection_thread = None
        self._inspection_running = False
        self._inspection_interval = 300  # 5分钟一次
        
        logger.info(f"运维监控 v3.0 初始化完成 - 数据路径: {self.data_path}")
    
    def _load_history(self):
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    self.health_history = json.load(f)
            except Exception as e:
                logger.error(f"加载健康历史失败: {e}")
    
    def _save_history(self):
        try:
            # 只保留最近1000条
            if len(self.health_history) > 1000:
                self.health_history = self.health_history[-1000:]
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.health_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存健康历史失败: {e}")
    
    def register_checker(self, name: str, checker: HealthChecker):
        """注册检查器"""
        self.checkers[name] = checker
        logger.info(f"已注册检查器: {name}")
    
    def register_default_checkers(self, base_path: str = None):
        """注册默认检查器"""
        if base_path is None:
            base_path = str(self.data_path.parent)
        
        # 文件系统检查
        self.register_checker("filesystem", FileSystemChecker(base_path))
        
        # 数据完整性检查
        self.register_checker("data_integrity", DataIntegrityChecker(base_path))
        
        # 网络连通性检查（常见目标
        self.register_checker("network_google", 
                            ConnectivityChecker("8.8.8.8", "network_dns"))
    
    def run_full_inspection(self) -> InspectionResult:
        """执行完整巡检"""
        logger.info("开始完整巡检...")
        start_time = datetime.now()
        
        results = []
        issues_count = 0
        alerts_count = 0
        
        for name, checker in self.checkers.items():
            try:
                health = checker.check()
                results.append(health.to_dict())
                
                if health.status != "healthy":
                    issues_count += 1
                    
                    # 根据健康度生成告警
                    if health.status == "critical":
                        alert_level = "error"
                    elif health.status == "warning":
                        alert_level = "warning"
                    else:
                        alert_level = "info"
                    
                    alert = self.alert_manager.create_alert(
                        level=alert_level,
                        module=health.module_name,
                        title=f"{health.module_name} 健康度异常",
                        message=f"健康分数: {health.health_score:.1f}, 问题: {', '.join(health.issues)}"
                    )
                    alerts_count += 1
                    
                    # 尝试自愈
                    self.self_healing.analyze_and_heal(health)
                    
            except Exception as e:
                logger.error(f"检查器 {name} 执行失败: {e}")
                results.append({
                    "module_name": name,
                    "status": "unknown",
                    "health_score": 0,
                    "error": str(e)
                })
        
        end_time = datetime.now()
        
        # 记录历史
        avg_score = sum(r.get("health_score", 0) for r in results) / len(results) if results else 0
        
        self.health_history.append({
            "timestamp": end_time.isoformat(),
            "average_score": round(avg_score, 1),
            "modules_count": len(results),
            "issues_count": issues_count,
            "results": results
        })
        self._save_history()
        
        inspection = InspectionResult(
            inspection_id=f"insp_{uuid.uuid4().hex[:12]}",
            start_time=start_time.isoformat(),
            end_time=end_time.isoformat(),
            modules_checked=len(results),
            issues_found=issues_count,
            alerts_generated=alerts_count,
            details=results
        )
        
        logger.info(f"巡检完成 - 检查 {len(results)} 个模块, 发现 {issues_count} 个问题, 生成 {alerts_count} 个告警")
        
        return inspection
    
    def get_dashboard(self) -> dict:
        """获取运营仪表盘数据"""
        # 最新健康状态
        latest = self.health_history[-1] if self.health_history else None
        
        # 活跃告警
        active_alerts = self.alert_manager.get_active_alerts()
        
        # 计算24小时趋势
        now = datetime.now()
        day_ago = now - timedelta(hours=24)
        
        day_history = [
            h for h in self.health_history 
            if datetime.fromisoformat(h["timestamp"]) > day_ago
        ]
        
        if day_history:
            scores = [h["average_score"] for h in day_history]
            trend_24h = {
                "start_score": scores[0],
                "end_score": scores[-1],
                "avg_score": sum(scores) / len(scores),
                "min_score": min(scores),
                "max_score": max(scores),
                "data_points": len(scores)
            }
        else:
            trend_24h = {}
        
        # 各模块最新状态
        module_status = {}
        if latest:
            for result in latest["results"]:
                module_status[result["module_name"]] = {
                    "status": result["status"],
                    "score": result.get("health_score", 0)
                }
        
        return {
            "version": "3.0",
            "overall_health": latest.get("average_score", 0) if latest else 0,
            "overall_status": latest.get("results", [{}])[0].get("status", "unknown") if latest else "unknown",
            "modules_monitored": len(self.checkers),
            "active_alerts": len(active_alerts),
            "critical_alerts": len([a for a in active_alerts if a.level == "critical"]),
            "warning_alerts": len([a for a in active_alerts if a.level == "warning"]),
            "module_status": module_status,
            "trend_24h": trend_24h,
            "last_inspection": latest.get("timestamp") if latest else None,
            "self_healing_actions": len(self.self_healing.actions)
        }
    
    def generate_report(self, period: str = "daily") -> OpsReport:
        """生成运营报表"""
        now = datetime.now()
        
        if period == "daily":
            start = now - timedelta(days=1)
        elif period == "weekly":
            start = now - timedelta(weeks=1)
        elif period == "monthly":
            start = now - timedelta(days=30)
        else:
            start = now - timedelta(days=1)
        
        # 筛选时间段内的历史
        period_history = [
            h for h in self.health_history 
            if datetime.fromisoformat(h["timestamp"]) >= start
        ]
        
        # 计算统计
        if period_history:
            scores = [h["average_score"] for h in period_history]
            avg_score = sum(scores) / len(scores)
            min_score = min(scores)
            max_score = max(scores)
            total_issues = sum(h.get("issues_count", 0) for h in period_history)
        else:
            avg_score = 0
            min_score = 0
            max_score = 0
            total_issues = 0
        
        report = OpsReport(
            report_id=f"report_{uuid.uuid4().hex[:12]}",
            period=period,
            start_date=start.isoformat(),
            end_date=now.isoformat(),
            summary={
                "average_health_score": round(avg_score, 1),
                "min_health_score": round(min_score, 1),
                "max_health_score": round(max_score, 1),
                "total_inspections": len(period_history),
                "total_issues_found": total_issues,
                "active_alerts": len(self.alert_manager.get_active_alerts())
            },
            health_trends=period_history[-100:] if period_history else []
        )
        
        logger.info(f"生成{period}报表 - 平均健康度: {avg_score:.1f}")
        return report
    
    def start_auto_inspection(self, interval_seconds: int = 300):
        """启动自动巡检"""
        if self._inspection_running:
            logger.warning("自动巡检已在运行")
            return
        
        self._inspection_interval = interval_seconds
        self._inspection_running = True
        
        def inspection_loop():
            while self._inspection_running:
                try:
                    self.run_full_inspection()
                except Exception as e:
                    logger.error(f"自动巡检异常: {e}")
                
                time.sleep(self._inspection_interval)
        
        self._inspection_thread = threading.Thread(target=inspection_loop, daemon=True)
        self._inspection_thread.start()
        
        logger.info(f"自动巡检已启动 - 间隔: {interval_seconds}秒")
    
    def stop_auto_inspection(self):
        """停止自动巡检"""
        self._inspection_running = False
        if self._inspection_thread:
            self._inspection_thread.join(timeout=5)
        logger.info("自动巡检已停止")


# ============================================================
# 演示与测试
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("智能体运维监控 v3.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        monitor = OpsMonitorV3(data_path=os.path.join(tmpdir, "ops"))
        
        print("\n🔧 注册检查器...")
        monitor.register_default_checkers(tmpdir)
        print(f"  已注册 {len(monitor.checkers)} 个检查器")
        
        print("\n🔍 执行完整巡检...")
        inspection = monitor.run_full_inspection()
        print(f"  检查模块数: {inspection.modules_checked}")
        print(f"  发现问题: {inspection.issues_found}")
        print(f"  生成告警: {inspection.alerts_generated}")
        
        print("\n📊 运营仪表盘...")
        dashboard = monitor.get_dashboard()
        print(f"  整体健康度: {dashboard['overall_health']:.1f}")
        print(f"  监控模块数: {dashboard['modules_monitored']}")
        print(f"  活跃告警数: {dashboard['active_alerts']}")
        print(f"  自愈动作数: {dashboard['self_healing_actions']}")
        
        print("\n📝 模块状态详情:")
        for name, status in dashboard["module_status"].items():
            print(f"  - {name}: {status['status']} ({status['score']:.0f}分)")
        
        print("\n📋 活跃告警列表:")
        active_alerts = monitor.alert_manager.get_active_alerts()
        if active_alerts:
            for alert in active_alerts[:5]:
                print(f"  [{alert.level.upper()}] {alert.module}: {alert.title}")
        else:
            print("  无活跃告警")
        
        print("\n📈 生成日报表...")
        report = monitor.generate_report("daily")
        print(f"  报告周期: {report.period}")
        print(f"  平均健康度: {report.summary['average_health_score']:.1f}")
        print(f"  巡检次数: {report.summary['total_inspections']}")
        print(f"  总问题数: {report.summary['total_issues_found']}")
        
        print("\n💚 测试自愈引擎...")
        # 模拟一个低健康度的模块状态
        test_health = ModuleHealth(
            module_name="test_module",
            module_type="core",
            status="warning",
            health_score=55.0,
            last_check=datetime.now().isoformat(),
            issues=["测试问题"]
        )
        action = monitor.self_healing.analyze_and_heal(test_health)
        if action:
            print(f"  自愈动作: {action.action_type}")
            print(f"  执行结果: {action.status} - {action.result}")
        else:
            print("  无匹配的自愈规则")
        
        print("\n" + "=" * 70)
        print("✅ 运维监控 v3.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
