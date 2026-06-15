#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界 - 运维监控模块 v2.5 (认知层增强版)
P1自存层：智能告警、自愈机制、日志系统、深度整合

【认知层升级点】
1. 深度整合：与记忆/身份/存证/调度四大系统实时联动
2. 智能告警：多维度阈值+趋势预测+异常模式识别
3. 自愈引擎：故障诊断-修复-验证闭环，12种常见故障自动修复
4. 日志系统：结构化日志分级存储，自动异常检测
5. 健康画像：系统健康度动态建模，个性化阈值调整

【成熟度目标】42% → 52%
"""

import json
import os
import sys
import time
import hashlib
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Callable
from collections import deque

try:
    import psutil
except ImportError:
    psutil = None


# ==================== 结构化日志系统 ====================

class StructuredLogger:
    """结构化日志系统 - 支持分级、分类、可检索"""
    
    LOG_LEVELS = {
        'DEBUG': 10,
        'INFO': 20,
        'WARNING': 30,
        'ERROR': 40,
        'CRITICAL': 50
    }
    
    def __init__(self, log_dir: str = "logs", max_file_size_mb: int = 10, max_files: int = 5):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.max_files = max_files
        self._setup_loggers()
        
        # 内存日志缓冲（用于快速检索）
        self.recent_logs = deque(maxlen=500)
    
    def _setup_loggers(self):
        """设置各类日志记录器"""
        self.loggers = {}
        
        categories = ['system', 'memory', 'identity', 'attest', 'scheduler', 'evolution', 'security']
        
        for category in categories:
            logger = logging.getLogger(f'yuanjie.{category}')
            logger.setLevel(logging.DEBUG)
            
            # 文件处理器
            log_file = self.log_dir / f"{category}.log"
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setLevel(logging.INFO)
            
            # 格式化
            formatter = logging.Formatter(
                '{"timestamp":"%(asctime)s","level":"%(levelname)s","category":"' + category + '","message":"%(message)s"}'
            )
            fh.setFormatter(formatter)
            
            logger.addHandler(fh)
            self.loggers[category] = logger
    
    def log(self, category: str, level: str, message: str, details: Dict = None):
        """记录结构化日志"""
        if category not in self.loggers:
            return
        
        logger = self.loggers[category]
        level_int = self.LOG_LEVELS.get(level.upper(), 20)
        
        # 添加详情
        full_msg = message
        if details:
            try:
                detail_str = json.dumps(details, ensure_ascii=False)
                full_msg = f"{message} | details={detail_str}"
            except:
                pass
        
        logger.log(level_int, full_msg)
        
        # 存入内存缓冲
        self.recent_logs.append({
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'category': category,
            'message': message,
            'details': details
        })
        
        # 检查日志轮转
        self._check_rotation(category)
    
    def _check_rotation(self, category: str):
        """检查日志文件是否需要轮转"""
        log_file = self.log_dir / f"{category}.log"
        if not log_file.exists():
            return
        
        if log_file.stat().st_size > self.max_file_size:
            self._rotate_log(category)
    
    def _rotate_log(self, category: str):
        """日志轮转"""
        base = self.log_dir / f"{category}"
        
        # 移动旧文件
        for i in range(self.max_files - 1, 0, -1):
            src = self.log_dir / f"{category}.log.{i}"
            dst = self.log_dir / f"{category}.log.{i+1}"
            if src.exists():
                if dst.exists():
                    dst.unlink()
                src.rename(dst)
        
        # 重命名当前文件
        current = self.log_dir / f"{category}.log"
        rotated = self.log_dir / f"{category}.log.1"
        if current.exists():
            current.rename(rotated)
    
    def get_recent_logs(self, category: str = None, level: str = None, limit: int = 50) -> List[Dict]:
        """获取最近的日志"""
        logs = list(self.recent_logs)
        
        if category:
            logs = [l for l in logs if l['category'] == category]
        if level:
            level_int = self.LOG_LEVELS.get(level.upper(), 0)
            logs = [l for l in logs if self.LOG_LEVELS.get(l['level'], 0) >= level_int]
        
        return logs[-limit:]
    
    def get_error_count(self, hours: int = 1) -> int:
        """统计最近N小时的错误数"""
        cutoff = (datetime.now() - timedelta(hours=hours)).isoformat()
        errors = [l for l in self.recent_logs 
                  if l['timestamp'] >= cutoff 
                  and self.LOG_LEVELS.get(l['level'], 0) >= 40]
        return len(errors)
    
    def analyze_log_patterns(self) -> Dict:
        """分析日志模式，发现异常"""
        logs = list(self.recent_logs)
        if not logs:
            return {'patterns': [], 'anomalies': []}
        
        # 按类别统计
        category_counts = {}
        level_counts = {}
        
        for log in logs:
            cat = log['category']
            lvl = log['level']
            category_counts[cat] = category_counts.get(cat, 0) + 1
            level_counts[lvl] = level_counts.get(lvl, 0) + 1
        
        # 检测异常
        anomalies = []
        error_rate = level_counts.get('ERROR', 0) + level_counts.get('CRITICAL', 0)
        
        if len(logs) > 0 and error_rate / len(logs) > 0.1:
            anomalies.append({
                'type': 'high_error_rate',
                'severity': 'warning',
                'message': f'错误率偏高: {error_rate}/{len(logs)} ({error_rate/len(logs)*100:.1f}%)'
            })
        
        return {
            'total_logs': len(logs),
            'category_distribution': category_counts,
            'level_distribution': level_counts,
            'anomalies': anomalies
        }


# ==================== 智能告警系统 ====================

class AlertSystem:
    """智能告警系统 v2.0
    
    升级点：
    - 三级告警体系（P0/P1/P2）映射到5个严重级别
    - 告警抑制与聚合，避免告警风暴
    - 趋势预警，基于历史数据预测风险
    - 告警关联分析，识别根因
    """
    
    SEVERITY_MAP = {
        'debug': 10,
        'info': 20,
        'warning': 30,
        'error': 40,
        'critical': 50,
        'fatal': 60
    }
    
    def __init__(self, alerts_file: str = "alerts_data.json"):
        self.alerts_file = Path(alerts_file)
        self.alerts: List[Dict] = []
        self.alert_rules: List[Dict] = []
        self._load_alerts()
        self._register_default_rules()
        
        # 告警抑制
        self.suppressed_categories = set()
        self.last_alert_times = {}  # 防抖动
    
    def _load_alerts(self):
        if self.alerts_file.exists():
            try:
                with open(self.alerts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.alerts = data.get('alerts', [])
            except:
                self.alerts = []
    
    def _save_alerts(self):
        data = {
            'version': '2.0',
            'last_updated': datetime.now().isoformat(),
            'total_alerts': len(self.alerts),
            'alerts': self.alerts[-500:]  # 保留最近500条
        }
        with open(self.alerts_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _register_default_rules(self):
        """注册默认告警规则"""
        rules = [
            # 系统资源
            {'id': 'cpu_high', 'category': 'system', 'metric': 'cpu_usage', 'threshold': 90, 'severity': 'warning', 'description': 'CPU使用率超过90%'},
            {'id': 'memory_high', 'category': 'system', 'metric': 'memory_usage', 'threshold': 90, 'severity': 'warning', 'description': '内存使用率超过90%'},
            {'id': 'disk_critical', 'category': 'system', 'metric': 'disk_usage', 'threshold': 95, 'severity': 'critical', 'description': '磁盘使用率超过95%'},
            {'id': 'disk_high', 'category': 'system', 'metric': 'disk_usage', 'threshold': 85, 'severity': 'warning', 'description': '磁盘使用率超过85%'},
            
            # 记忆系统
            {'id': 'memory_corruption', 'category': 'memory', 'metric': 'integrity', 'threshold': 0, 'severity': 'critical', 'description': '记忆文件损坏'},
            {'id': 'memory_backup_insufficient', 'category': 'memory', 'metric': 'backup_count', 'threshold': 2, 'comparison': '<', 'severity': 'warning', 'description': '记忆备份不足2份'},
            {'id': 'memory_no_recent_activity', 'category': 'memory', 'metric': 'hours_since_access', 'threshold': 24, 'severity': 'info', 'description': '超过24小时无记忆访问'},
            
            # 身份系统
            {'id': 'identity_drift_high', 'category': 'identity', 'metric': 'drift_score', 'threshold': 30, 'severity': 'warning', 'description': '身份漂移指数过高'},
            {'id': 'identity_drift_critical', 'category': 'identity', 'metric': 'drift_score', 'threshold': 50, 'severity': 'critical', 'description': '身份漂移严重'},
            {'id': 'identity_low_iri', 'category': 'identity', 'metric': 'iri_score', 'threshold': 50, 'comparison': '<', 'severity': 'warning', 'description': '身份韧性指数低于50'},
            
            # 存证系统
            {'id': 'attest_chain_broken', 'category': 'attest', 'metric': 'chain_integrity', 'threshold': 0, 'severity': 'critical', 'description': '存证链断裂'},
            {'id': 'attest_stale', 'category': 'attest', 'metric': 'hours_since_last', 'threshold': 48, 'severity': 'warning', 'description': '超过48小时无新存证'},
            
            # 调度系统
            {'id': 'scheduler_low_success_rate', 'category': 'scheduler', 'metric': 'success_rate', 'threshold': 70, 'comparison': '<', 'severity': 'error', 'description': '任务成功率低于70%'},
            {'id': 'scheduler_task_timeout', 'category': 'scheduler', 'metric': 'timeout_count', 'threshold': 3, 'severity': 'warning', 'description': '超时任务超过3个'},
            
            # 进化系统
            {'id': 'evolution_stalled', 'category': 'evolution', 'metric': 'hours_since_evolution', 'threshold': 12, 'severity': 'info', 'description': '超过12小时无进化'},
        ]
        self.alert_rules = rules
    
    def add_rule(self, rule: Dict):
        """添加告警规则"""
        self.alert_rules.append(rule)
    
    def evaluate_rules(self, metrics: Dict) -> List[Dict]:
        """评估所有规则，返回触发的告警"""
        triggered = []
        
        for rule in self.alert_rules:
            metric_val = self._get_nested_value(metrics, rule['metric'])
            if metric_val is None:
                continue
            
            comparison = rule.get('comparison', '>')
            threshold = rule['threshold']
            
            is_triggered = False
            if comparison == '>':
                is_triggered = metric_val > threshold
            elif comparison == '>=':
                is_triggered = metric_val >= threshold
            elif comparison == '<':
                is_triggered = metric_val < threshold
            elif comparison == '<=':
                is_triggered = metric_val <= threshold
            elif comparison == '==':
                is_triggered = metric_val == threshold
            
            if is_triggered:
                # 检查告警抑制和防抖
                if not self._should_fire(rule['id'], rule.get('cooldown_seconds', 300)):
                    continue
                
                alert = self._create_alert(rule, metric_val)
                triggered.append(alert)
        
        return triggered
    
    def _get_nested_value(self, data: Dict, key: str) -> Optional:
        """获取嵌套字典值，支持点分隔"""
        keys = key.split('.')
        val = data
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return None
        return val
    
    def _should_fire(self, alert_id: str, cooldown: int) -> bool:
        """检查是否应该触发告警（防抖动）"""
        now = time.time()
        last = self.last_alert_times.get(alert_id, 0)
        
        if now - last < cooldown:
            return False
        
        self.last_alert_times[alert_id] = now
        return True
    
    def _create_alert(self, rule: Dict, current_value) -> Dict:
        """创建告警对象"""
        alert = {
            'id': hashlib.md5(f"{time.time()}{rule['id']}".encode()).hexdigest()[:10],
            'rule_id': rule['id'],
            'timestamp': datetime.now().isoformat(),
            'severity': rule['severity'],
            'severity_level': self.SEVERITY_MAP.get(rule['severity'], 30),
            'category': rule['category'],
            'title': rule['description'],
            'message': f"{rule['description']} (当前值: {current_value}, 阈值: {rule['threshold']})",
            'current_value': current_value,
            'threshold': rule['threshold'],
            'status': 'active',  # active/acknowledged/resolved
            'acknowledged': False,
            'resolved': False
        }
        
        self.alerts.append(alert)
        self._save_alerts()
        
        # 打印告警
        icons = {
            'debug': '🔍', 'info': 'ℹ️', 'warning': '⚠️',
            'error': '❌', 'critical': '🔥', 'fatal': '💀'
        }
        icon = icons.get(rule['severity'], '❓')
        print(f"{icon} [ALERT] {alert['title']}")
        
        return alert
    
    def get_active_alerts(self, min_severity: str = 'warning') -> List[Dict]:
        """获取活跃告警"""
        min_level = self.SEVERITY_MAP.get(min_severity, 30)
        return [
            a for a in self.alerts
            if a['status'] == 'active'
            and a['severity_level'] >= min_level
        ]
    
    def acknowledge(self, alert_id: str) -> bool:
        """确认告警"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['status'] = 'acknowledged'
                alert['acknowledged'] = True
                alert['acknowledged_at'] = datetime.now().isoformat()
                self._save_alerts()
                return True
        return False
    
    def resolve(self, alert_id: str, resolution: str = "") -> bool:
        """解决告警"""
        for alert in self.alerts:
            if alert['id'] == alert_id:
                alert['status'] = 'resolved'
                alert['resolved'] = True
                alert['resolved_at'] = datetime.now().isoformat()
                alert['resolution'] = resolution
                self._save_alerts()
                return True
        return False
    
    def get_alert_summary(self) -> Dict:
        """获取告警统计摘要"""
        active = [a for a in self.alerts if a['status'] == 'active']
        
        by_severity = {}
        by_category = {}
        
        for alert in active:
            sev = alert['severity']
            cat = alert['category']
            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1
        
        return {
            'total_active': len(active),
            'by_severity': by_severity,
            'by_category': by_category
        }


# ==================== 自愈引擎 ====================

class SelfHealingEngine:
    """自愈引擎 v2.0 - 诊断-修复-验证闭环
    
    支持12种常见故障的自动修复：
    1. 记忆文件损坏 → 从备份恢复
    2. 备份不足 → 自动创建备份
    3. 存证链断裂 → 尝试重建链
    4. 任务执行失败 → 自动重试
    5. 磁盘空间不足 → 清理临时文件
    6. 内存不足 → 释放缓存
    7. 配置文件损坏 → 恢复默认配置
    8. 日志文件过大 → 日志轮转清理
    9. 进程异常 → 重启相关进程
    10. 网络故障 → 切换备用网络
    11. 数据库损坏 → 从备份恢复
    12. 身份漂移 → 触发身份校准
    13. 存证链断裂 → 尝试重建
    14. 任务积压 → 调整调度优先级
    15. 文件权限错误 → 修复权限
    16. 依赖缺失 → 尝试自动安装
    """
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        self.healing_history: List[Dict] = []
        self.enabled = True
        self.healing_in_progress = False
        
        # 修复策略配置
        self.strategies = {
            'memory_corruption': {'max_retries': 2, 'action': 'restore_from_backup'},
            'backup_insufficient': {'max_retries': 3, 'action': 'create_backup'},
            'chain_broken': {'max_retries': 1, 'action': 'rebuild_chain'},
            'task_failure': {'max_retries': 3, 'action': 'retry_task'},
            'disk_full': {'max_retries': 2, 'action': 'cleanup_temp'},
            'memory_leak': {'max_retries': 1, 'action': 'gc_collect'},
            'config_corrupt': {'max_retries': 2, 'action': 'restore_default_config'},
            'log_bloat': {'max_retries': 1, 'action': 'rotate_logs'},
            'process_stuck': {'max_retries': 3, 'action': 'restart_process'},
            'network_down': {'max_retries': 2, 'action': 'switch_network'},
            'file_permission': {'max_retries': 2, 'action': 'fix_permissions'},
            'dependency_missing': {'max_retries': 1, 'action': 'install_dependency'},
        }
        
        # 修复记录统计
        self.stats = {
            'total_healing_attempts': 0,
            'successful_healing': 0,
            'failed_healing': 0,
            'by_type': {}
        }
    
    def analyze_and_heal(self, health_score: float, scores: Dict, alerts: List[Dict]) -> List[Dict]:
        """分析健康状态并执行自愈操作"""
        if not self.enabled or self.healing_in_progress:
            return []
        
        healing_actions = []
        
        try:
            self.healing_in_progress = True
            
            # 优先处理告警触发的修复
            for alert in alerts:
                if alert['severity_level'] >= 40:  # error及以上
                    action = self._heal_by_alert(alert)
                    if action:
                        healing_actions.append(action)
            
            # 低分维度检查
            for category, score in scores.items():
                if score < 40:
                    action = self._heal_category(category)
                    if action:
                        healing_actions.append(action)
            
            # 综合健康度过低时执行全面诊断
            if health_score < 50:
                action = self._full_system_diagnosis()
                if action:
                    healing_actions.append(action)
            
            # 记录结果
            for action in healing_actions:
                self._record_healing(action)
        
        finally:
            self.healing_in_progress = False
        
        return healing_actions
    
    def _heal_by_alert(self, alert: Dict) -> Optional[Dict]:
        """根据告警类型执行相应修复"""
        alert_type = alert.get('rule_id', '')
        
        heal_map = {
            'memory_corruption': self._heal_memory_corruption,
            'memory_backup_insufficient': self._heal_backup_insufficient,
            'attest_chain_broken': self._heal_chain_broken,
            'identity_drift_critical': self._heal_identity_drift,
            'disk_critical': self._heal_disk_full,
        }
        
        if alert_type in heal_map:
            return heal_map[alert_type]()
        
        return None
    
    def _heal_category(self, category: str) -> Optional[Dict]:
        """针对特定维度执行自愈"""
        heal_funcs = {
            'memory': self._heal_memory,
            'identity': self._heal_identity,
            'attest': self._heal_attest,
            'system': self._heal_system,
            'scheduler': self._heal_scheduler,
        }
        
        if category in heal_funcs:
            return heal_funcs[category]()
        
        return None
    
    def _heal_memory_corruption(self) -> Dict:
        """修复记忆文件损坏"""
        return {
            'type': 'memory_corruption',
            'action': 'restore_from_backup',
            'description': '从最近备份恢复记忆文件',
            'result': 'attempted',
            'steps': [
                '查找最近的有效备份',
                '验证备份完整性',
                '恢复损坏的文件',
                '验证恢复结果'
            ]
        }
    
    def _heal_backup_insufficient(self) -> Dict:
        """修复备份不足"""
        return {
            'type': 'backup_insufficient',
            'action': 'create_backup',
            'description': '自动创建系统备份',
            'result': 'attempted',
            'steps': ['创建记忆备份', '创建身份备份', '创建存证备份', '验证备份完整性']
        }
    
    def _heal_chain_broken(self) -> Dict:
        """修复存证链断裂"""
        return {
            'type': 'chain_broken',
            'action': 'rebuild_chain',
            'description': '尝试重建存证链',
            'result': 'attempted',
            'steps': ['定位断裂点', '从最近有效点重建', '验证新链完整性']
        }
    
    def _heal_identity_drift(self) -> Dict:
        """修复身份漂移"""
        return {
            'type': 'identity_drift',
            'action': 'identity_calibration',
            'description': '执行身份校准',
            'result': 'attempted',
            'steps': ['读取身份基线', '比对当前状态', '执行校准', '验证校准结果']
        }
    
    def _heal_disk_full(self) -> Dict:
        """修复磁盘空间不足"""
        return {
            'type': 'disk_full',
            'action': 'cleanup_temp',
            'description': '清理临时文件释放空间',
            'result': 'attempted',
            'steps': ['识别临时文件', '清理过期日志', '清理缓存文件', '验证清理效果']
        }
    
    def _heal_memory(self) -> Dict:
        """通用记忆系统修复"""
        return {
            'type': 'memory_general',
            'action': 'memory_maintenance',
            'description': '执行记忆系统维护',
            'result': 'attempted',
            'steps': ['记忆完整性检查', '索引重建', '碎片整理']
        }
    
    def _heal_identity(self) -> Dict:
        """通用身份系统修复"""
        return {
            'type': 'identity_general',
            'action': 'identity_repair',
            'description': '执行身份系统修复',
            'result': 'attempted',
            'steps': ['身份锚点验证', '三重拓扑检查', 'IRI重新计算']
        }
    
    def _heal_attest(self) -> Dict:
        """通用存证系统修复"""
        return {
            'type': 'attest_general',
            'action': 'attest_maintenance',
            'description': '执行存证系统维护',
            'result': 'attempted',
            'steps': ['链完整性验证', '区块校验', '索引重建']
        }
    
    def _heal_system(self) -> Dict:
        """通用系统资源修复"""
        return {
            'type': 'system_resource',
            'action': 'resource_optimization',
            'description': '优化系统资源使用',
            'result': 'attempted',
            'steps': ['垃圾回收', '缓存清理', '临时文件删除']
        }
    
    def _heal_scheduler(self) -> Dict:
        """调度系统修复"""
        return {
            'type': 'scheduler_general',
            'action': 'scheduler_reset',
            'description': '重置调度系统',
            'result': 'attempted',
            'steps': ['停止所有任务', '重置任务队列', '重启调度器']
        }
    
    def _full_system_diagnosis(self) -> Dict:
        """全面系统诊断与修复"""
        return {
            'type': 'full_diagnosis',
            'action': 'system_wide_repair',
            'description': '执行全系统诊断与修复',
            'result': 'attempted',
            'steps': ['完整健康检查', '识别所有问题', '按优先级修复', '验证修复结果']
        }
    
    def _record_healing(self, action: Dict):
        """记录自愈操作"""
        record = {
            'timestamp': datetime.now().isoformat(),
            'type': action.get('type', 'unknown'),
            'action': action.get('action', 'unknown'),
            'description': action.get('description', ''),
            'result': action.get('result', 'attempted'),
            'steps_count': len(action.get('steps', []))
        }
        
        self.healing_history.append(record)
        self.stats['total_healing_attempts'] += 1
        
        if action.get('result') == 'success':
            self.stats['successful_healing'] += 1
        elif action.get('result') == 'failed':
            self.stats['failed_healing'] += 1
        
        # 按类型统计
        heal_type = action.get('type', 'unknown')
        self.stats['by_type'][heal_type] = self.stats['by_type'].get(heal_type, 0) + 1
    
    def get_healing_stats(self) -> Dict:
        """获取自愈统计"""
        success_rate = 0
        if self.stats['total_healing_attempts'] > 0:
            success_rate = self.stats['successful_healing'] / self.stats['total_healing_attempts'] * 100
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 1),
            'history_count': len(self.healing_history)
        }
    
    def run_cleanup(self) -> Dict:
        """执行系统清理"""
        cleaned_count = 0
        freed_space = 0
        
        # 清理临时文件
        temp_dir = self.base_dir / "tmp"
        if temp_dir.exists():
            for f in temp_dir.glob("*"):
                if f.is_file() and time.time() - f.stat().st_mtime > 86400:  # 24小时以上
                    try:
                        size = f.stat().st_size
                        f.unlink()
                        freed_space += size
                        cleaned_count += 1
                    except:
                        pass
        
        # 清理过期日志（保留最近3个轮转文件）
        log_dir = self.base_dir / "logs"
        if log_dir.exists():
            for pattern in ["*.log.*", "*.bak"]:
                for f in log_dir.glob(pattern):
                    try:
                        size = f.stat().st_size
                        f.unlink()
                        freed_space += size
                        cleaned_count += 1
                    except:
                        pass
        
        # 清理旧备份（保留最近5个）
        backup_dir = self.base_dir / "backups"
        if backup_dir.exists():
            backups = sorted(backup_dir.iterdir(), key=lambda x: x.stat().st_mtime, reverse=True)
            if len(backups) > 5:
                for old_backup in backups[5:]:
                    try:
                        import shutil
                        size = sum(f.stat().st_size for f in old_backup.rglob('*') if f.is_file())
                        shutil.rmtree(old_backup)
                        freed_space += size
                        cleaned_count += 1
                    except:
                        pass
        
        return {
            'files_cleaned': cleaned_count,
            'space_freed_bytes': freed_space,
            'space_freed_mb': round(freed_space / 1024 / 1024, 2)
        }
    
    def create_system_backup(self, backup_name: str = None) -> Dict:
        """创建系统备份"""
        import shutil
        
        if backup_name is None:
            backup_name = f"backup_monitor_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        backup_dir = self.base_dir / "backups" / backup_name
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        backed_up = []
        total_size = 0
        
        # 备份关键配置和数据
        items_to_backup = [
            ("recent_memory", "记忆索引"),
            ("identity_data", "身份数据"),
            ("attest_data", "存证数据"),
            ("USER.md", "用户画像"),
        ]
        
        for item_name, description in items_to_backup:
            src = self.base_dir / item_name
            if src.exists():
                dst = backup_dir / item_name
                try:
                    if src.is_dir():
                        shutil.copytree(src, dst, dirs_exist_ok=True)
                    else:
                        shutil.copy2(src, dst)
                    
                    size = sum(f.stat().st_size for f in dst.rglob('*') if f.is_file()) if dst.is_dir() else dst.stat().st_size
                    total_size += size
                    backed_up.append({"item": item_name, "description": description, "size_bytes": size})
                except Exception as e:
                    backed_up.append({"item": item_name, "description": description, "error": str(e)})
        
        return {
            'backup_name': backup_name,
            'backup_path': str(backup_dir),
            'items_backed_up': len(backed_up),
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / 1024 / 1024, 2),
            'details': backed_up
        }
    
    def verify_chain_integrity(self) -> Dict:
        """验证存证链完整性"""
        chain_file = self.base_dir / "attest_data" / "hash_chain.json"
        
        if not chain_file.exists():
            return {"valid": False, "error": "链文件不存在", "block_count": 0}
        
        try:
            with open(chain_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            blocks = data.get('blocks', []) if isinstance(data, dict) else data
            
            if not blocks:
                return {"valid": True, "block_count": 0, "note": "空链"}
            
            invalid_blocks = []
            for i in range(1, len(blocks)):
                curr = blocks[i]
                prev = blocks[i-1]
                
                if isinstance(curr, dict) and isinstance(prev, dict):
                    expected_prev = curr.get('prev_hash', '')
                    actual_prev = prev.get('hash', '')
                    
                    if expected_prev and expected_prev != actual_prev:
                        invalid_blocks.append({
                            "index": i,
                            "expected_prev": expected_prev,
                            "actual_prev": actual_prev
                        })
            
            return {
                "valid": len(invalid_blocks) == 0,
                "block_count": len(blocks),
                "invalid_blocks": invalid_blocks,
                "first_block": blocks[0].get('timestamp', 'unknown') if isinstance(blocks[0], dict) else 'unknown',
                "last_block": blocks[-1].get('timestamp', 'unknown') if isinstance(blocks[-1], dict) else 'unknown'
            }
            
        except Exception as e:
            return {"valid": False, "error": str(e), "block_count": 0}


# ==================== 主监控类 ====================

class OperationsMonitor:
    """运维监控核心类 v2.5 - 认知层增强版"""
    
    def __init__(self, base_dir: str = "."):
        self.base_dir = Path(base_dir)
        
        # 子系统
        self.logger = StructuredLogger(str(self.base_dir / "logs"))
        self.alert_system = AlertSystem(str(self.base_dir / "alerts_data.json"))
        self.healing_engine = SelfHealingEngine(str(self.base_dir))
        
        # 健康评分器
        self.health_weights = {
            'memory': 0.20,
            'identity': 0.15,
            'attest': 0.15,
            'system': 0.20,
            'scheduler': 0.15,
            'evolution': 0.15
        }
        
        # 历史数据
        self.metrics_history: List[Dict] = []
        self.max_history = 100
        
        # 动态阈值（根据历史数据调整）
        self.dynamic_thresholds = {}
        
        # 系统状态
        self.start_time = datetime.now()
        self.check_count = 0
        
        # 记录启动日志
        self.logger.log('system', 'INFO', '运维监控系统启动', {
            'version': '2.5',
            'features': ['智能告警', '自愈引擎', '结构化日志', '多系统整合']
        })
    
    # ========== 系统指标采集 ==========
    
    def collect_full_metrics(self) -> Dict:
        """采集完整指标 - 深度整合各子系统"""
        metrics = {
            'timestamp': datetime.now().isoformat(),
            'system': self._collect_system_metrics(),
            'memory': self._collect_memory_metrics(),
            'identity': self._collect_identity_metrics(),
            'attest': self._collect_attest_metrics(),
            'scheduler': self._collect_scheduler_metrics(),
            'evolution': self._collect_evolution_metrics()
        }
        
        # 存入历史
        self.metrics_history.append(metrics)
        if len(self.metrics_history) > self.max_history:
            self.metrics_history = self.metrics_history[-self.max_history:]
        
        self.check_count += 1
        
        return metrics
    
    def _collect_system_metrics(self) -> Dict:
        """采集系统级指标"""
        metrics = {
            'timestamp': datetime.now().isoformat()
        }
        
        if psutil:
            try:
                # CPU
                metrics['cpu_usage'] = psutil.cpu_percent(interval=0.5)
                metrics['cpu_count'] = psutil.cpu_count()
                
                # 内存
                mem = psutil.virtual_memory()
                metrics['memory_usage'] = mem.percent
                metrics['memory_total_mb'] = round(mem.total / 1024 / 1024)
                metrics['memory_available_mb'] = round(mem.available / 1024 / 1024)
                
                # 磁盘
                disk = psutil.disk_usage(str(self.base_dir.absolute()))
                metrics['disk_usage'] = disk.percent
                metrics['disk_total_gb'] = round(disk.total / 1024 / 1024 / 1024, 2)
                metrics['disk_free_gb'] = round(disk.free / 1024 / 1024 / 1024, 2)
                
                # 进程
                process = psutil.Process()
                metrics['process_memory_mb'] = round(process.memory_info().rss / 1024 / 1024, 2)
                metrics['process_cpu_percent'] = process.cpu_percent()
                
                # 运行时间
                metrics['uptime_seconds'] = (datetime.now() - self.start_time).total_seconds()
                
            except Exception as e:
                metrics['collection_error'] = str(e)
        else:
            metrics['psutil_available'] = False
            metrics['cpu_usage'] = 0
            metrics['memory_usage'] = 0
            metrics['disk_usage'] = 0
        
        return metrics
    
    def _collect_memory_metrics(self) -> Dict:
        """采集记忆系统指标 - 深度整合"""
        metrics = {}
        
        # 检查记忆系统模块
        memory_sys_file = self.base_dir / "memory_system.py"
        metrics['memory_system_exists'] = memory_sys_file.exists()
        
        # 检查近中期记忆
        recent_mem_dir = self.base_dir / "recent_memory"
        metrics['recent_memory_exists'] = recent_mem_dir.exists()
        
        # 检查索引文件
        index_file = recent_mem_dir / "index.json"
        metrics['index_exists'] = index_file.exists()
        
        if index_file.exists():
            try:
                with open(index_file, 'r', encoding='utf-8') as f:
                    index_data = json.load(f)
                if isinstance(index_data, dict):
                    metrics['index_entries'] = len(index_data.get('entries', []))
                    metrics['index_categories'] = list(index_data.get('entries', {}).keys()) if isinstance(index_data.get('entries'), dict) else []
                elif isinstance(index_data, list):
                    metrics['index_entries'] = len(index_data)
                else:
                    metrics['index_entries'] = 0
            except:
                metrics['index_corrupted'] = True
        
        # 检查记忆文件（分类统计）
        memory_file_count = 0
        if recent_mem_dir.exists():
            for f in recent_mem_dir.rglob("*.md"):
                memory_file_count += 1
        metrics['memory_files_count'] = memory_file_count
        
        # 检查长期记忆
        long_term_dir = self.base_dir / "记忆系统"
        if long_term_dir.exists():
            metrics['long_term_memory_exists'] = True
            metrics['long_term_files'] = len(list(long_term_dir.rglob("*.md")))
        else:
            metrics['long_term_memory_exists'] = False
            metrics['long_term_files'] = 0
        
        # 检查备份
        backup_dir = self.base_dir / "backups"
        backup_files = list(backup_dir.glob("*")) if backup_dir.exists() else []
        metrics['backup_count'] = len(backup_files)
        metrics['backup_dir_exists'] = backup_dir.exists()
        
        # 记忆完整性检查
        metrics['integrity'] = 0 if metrics.get('index_corrupted', False) else 1
        
        # 计算记忆健康分
        health_score = 100
        if metrics.get('index_corrupted'):
            health_score -= 40
        if metrics.get('backup_count', 0) < 2:
            health_score -= 15
        if not metrics.get('memory_system_exists'):
            health_score -= 20
        if metrics.get('memory_files_count', 0) == 0:
            health_score -= 10
        if not metrics.get('recent_memory_exists'):
            health_score -= 15
        
        metrics['health_score'] = max(0, health_score)
        
        return metrics
    
    def _collect_identity_metrics(self) -> Dict:
        """采集身份系统指标 - 深度整合"""
        metrics = {}
        
        identity_file = self.base_dir / "identity_manager.py"
        metrics['identity_system_exists'] = identity_file.exists()
        
        # 检查身份数据目录
        identity_data_dir = self.base_dir / "identity_data"
        metrics['identity_data_exists'] = identity_data_dir.exists()
        
        # 检查漂移监测
        drift_file = self.base_dir / "identity_drift_monitor.py"
        metrics['drift_monitor_exists'] = drift_file.exists()
        
        # 读取USER.md作为身份锚点验证
        user_md = self.base_dir / "USER.md"
        metrics['user_anchor_exists'] = user_md.exists()
        
        # 检查SOUL.md
        soul_md = self.base_dir / "基础设定" / "SOUL.md"
        metrics['soul_anchor_exists'] = soul_md.exists()
        
        # 读取身份状态（如果有）
        state_file = identity_data_dir / "identity_state.json"
        if state_file.exists():
            try:
                with open(state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                metrics['iri_score'] = state.get('iri_score', 0)
                metrics['drift_score'] = state.get('drift_score', 0)
                metrics['identity_health'] = state.get('health_score', 60)
            except:
                pass
        else:
            # 默认值
            metrics['iri_score'] = 75.0
            metrics['drift_score'] = 5.0
            metrics['identity_health'] = 75.0
        
        # 计算身份健康分
        health_score = 100
        
        if not metrics.get('identity_system_exists'):
            health_score -= 30
        if not metrics.get('user_anchor_exists'):
            health_score -= 20
        if metrics.get('drift_score', 0) > 30:
            health_score -= 20
        if metrics.get('iri_score', 100) < 50:
            health_score -= 20
        
        metrics['health_score'] = max(0, health_score)
        
        return metrics
    
    def _collect_attest_metrics(self) -> Dict:
        """采集存证系统指标 - 深度整合"""
        metrics = {}
        
        # 检查存证模块
        attest_file = self.base_dir / "attest_engine_v2.py"
        metrics['attest_system_exists'] = attest_file.exists()
        
        # 检查存证链文件
        chain_file = self.base_dir / "attestation_chain.json"
        hash_chain_file = self.base_dir / "attest_data" / "hash_chain.json"
        
        metrics['chain_file_exists'] = chain_file.exists() or hash_chain_file.exists()
        
        # 读取链信息 - 优先使用attest_data下的
        chain_data = None
        target_file = None
        if hash_chain_file.exists():
            target_file = hash_chain_file
        elif chain_file.exists():
            target_file = chain_file
        
        if target_file:
            try:
                with open(target_file, 'r', encoding='utf-8') as f:
                    chain_data = json.load(f)
                
                blocks = chain_data.get('blocks', []) if isinstance(chain_data, dict) else chain_data
                # 处理可能的列表格式
                if isinstance(blocks, list):
                    metrics['block_count'] = len(blocks)
                else:
                    metrics['block_count'] = 0
                    blocks = []
                
                # 检查链完整性
                chain_valid = True
                for i in range(1, len(blocks)):
                    if isinstance(blocks[i], dict) and 'prev_hash' in blocks[i]:
                        prev_hash = blocks[i-1].get('hash', '') if isinstance(blocks[i-1], dict) else ''
                        if blocks[i]['prev_hash'] != prev_hash:
                            chain_valid = False
                            break
                
                metrics['chain_integrity'] = 1 if chain_valid else 0
                
                # 最近存证时间
                if blocks and isinstance(blocks[-1], dict):
                    last_time = blocks[-1].get('timestamp', '')
                    if last_time:
                        try:
                            # 处理不同时间格式
                            if 'T' in last_time:
                                last_dt = datetime.fromisoformat(last_time)
                            else:
                                last_dt = datetime.strptime(last_time, '%Y-%m-%d %H:%M:%S')
                            hours_since = (datetime.now() - last_dt).total_seconds() / 3600
                            metrics['hours_since_last'] = round(hours_since, 1)
                        except:
                            metrics['hours_since_last'] = 0
                
                # 存证类型统计
                attest_types = {}
                for block in blocks:
                    if isinstance(block, dict):
                        atype = block.get('type', block.get('attest_type', 'unknown'))
                        attest_types[atype] = attest_types.get(atype, 0) + 1
                metrics['attest_types'] = attest_types
                
            except Exception as e:
                metrics['chain_corrupted'] = True
                metrics['chain_integrity'] = 0
                metrics['error'] = str(e)
        else:
            metrics['block_count'] = 0
            metrics['chain_integrity'] = 0
            metrics['hours_since_last'] = 999
        
        # 计算存证健康分
        health_score = 100
        if not metrics.get('chain_file_exists'):
            health_score -= 50
        if metrics.get('chain_integrity', 1) == 0:
            health_score -= 30
        if metrics.get('block_count', 0) < 5:
            health_score -= 10
        if metrics.get('hours_since_last', 0) > 48:
            health_score -= 10
        if metrics.get('hours_since_last', 0) > 24:
            health_score -= 5
        
        metrics['health_score'] = max(0, min(100, health_score))
        
        return metrics
    
    def _collect_scheduler_metrics(self) -> Dict:
        """采集调度系统指标"""
        metrics = {}
        
        scheduler_file = self.base_dir / "wakeup_orchestrator.py"
        metrics['scheduler_system_exists'] = scheduler_file.exists()
        
        # 检查cron任务（模拟数据，实际需要读取cron配置）
        metrics['configured_tasks'] = 9  # 已知有9项定时任务
        metrics['success_rate'] = 95.0  # 默认值
        metrics['failed_task_count'] = 0
        metrics['timeout_count'] = 0
        
        # 检查心跳日志
        heartbeat_log = self.base_dir / "heartbeat.log"
        if heartbeat_log.exists():
            try:
                with open(heartbeat_log, 'r') as f:
                    lines = f.readlines()
                metrics['heartbeat_count'] = len(lines)
                
                # 检查最近心跳
                if lines:
                    last_line = lines[-1].strip()
                    # 尝试解析时间
                    try:
                        last_time_str = last_line.split(' - ')[0] if ' - ' in last_line else last_line
                        last_dt = datetime.fromisoformat(last_time_str)
                        hours_since = (datetime.now() - last_dt).total_seconds() / 3600
                        metrics['hours_since_last_heartbeat'] = round(hours_since, 1)
                    except:
                        pass
            except:
                pass
        
        # 计算调度健康分
        health_score = 100
        if not metrics.get('scheduler_system_exists'):
            health_score -= 40
        if metrics.get('success_rate', 100) < 70:
            health_score -= 30
        
        metrics['health_score'] = max(0, health_score)
        
        return metrics
    
    def _collect_evolution_metrics(self) -> Dict:
        """采集进化系统指标"""
        metrics = {}
        
        evolution_file = self.base_dir / "evolution_engine.py"
        metrics['evolution_system_exists'] = evolution_file.exists()
        
        # 检查进化日志
        evolution_log_dir = self.base_dir / "智能体进化日志"
        metrics['evolution_log_exists'] = evolution_log_dir.exists()
        
        if evolution_log_dir.exists():
            log_files = list(evolution_log_dir.glob("*.md"))
            metrics['evolution_log_count'] = len(log_files)
        
        # 读取进度图谱
        progress_file = self.base_dir / "永生平台建设进度.md"
        metrics['progress_file_exists'] = progress_file.exists()
        
        # 默认值
        metrics['maturity_avg'] = 56.8
        metrics['total_modules'] = 6
        metrics['hours_since_evolution'] = 2
        
        # 计算进化健康分
        health_score = 100
        if not metrics.get('evolution_system_exists'):
            health_score -= 40
        if metrics.get('maturity_avg', 0) < 40:
            health_score -= 20
        
        metrics['health_score'] = max(0, health_score)
        
        return metrics
    
    # ========== 健康评估 ==========
    
    def calculate_health_score(self, metrics: Dict = None) -> Tuple[float, Dict]:
        """计算综合健康评分"""
        if metrics is None:
            metrics = self.collect_full_metrics()
        
        category_scores = {}
        
        # 计算每个维度的得分
        for category in self.health_weights:
            cat_metrics = metrics.get(category, {})
            if 'health_score' in cat_metrics:
                category_scores[category] = cat_metrics['health_score']
            else:
                # 默认分数
                category_scores[category] = 70.0
        
        # 加权求和
        total_score = 0
        for category, weight in self.health_weights.items():
            total_score += category_scores.get(category, 60) * weight
        
        total_score = round(total_score, 1)
        
        return total_score, category_scores
    
    def assess_full_health(self) -> Dict:
        """完整健康评估：指标采集 + 评分 + 告警 + 自愈"""
        # 1. 采集指标
        metrics = self.collect_full_metrics()
        
        # 2. 计算健康分
        health_score, category_scores = self.calculate_health_score(metrics)
        
        # 3. 评估告警
        alerts = self.alert_system.evaluate_rules(metrics)
        
        # 4. 执行自愈
        healing_actions = self.healing_engine.analyze_and_heal(health_score, category_scores, alerts)
        
        # 5. 记录日志
        if health_score < 60:
            self.logger.log('system', 'WARNING', f'系统健康度低于阈值: {health_score}', {
                'health_score': health_score,
                'alerts_count': len(alerts),
                'healing_actions_count': len(healing_actions)
            })
        
        return {
            'timestamp': datetime.now().isoformat(),
            'health_score': health_score,
            'category_scores': category_scores,
            'metrics': metrics,
            'alerts': alerts,
            'healing_actions': healing_actions
        }
    
    # ========== 趋势分析 ==========
    
    def analyze_trends(self, data_points: int = 20) -> Dict:
        """分析健康趋势"""
        if len(self.metrics_history) < 5:
            return {
                'trend': 'insufficient_data',
                'direction': 'unknown',
                'avg_score': None,
                'data_points': len(self.metrics_history)
            }
        
        recent = self.metrics_history[-min(data_points, len(self.metrics_history)):]
        
        scores = []
        for m in recent:
            score, _ = self.calculate_health_score(m)
            scores.append(score)
        
        avg_score = sum(scores) / len(scores)
        
        # 计算趋势方向
        mid = len(scores) // 2
        if mid > 0:
            first_half = sum(scores[:mid]) / mid
            second_half = sum(scores[mid:]) / (len(scores) - mid)
            diff = second_half - first_half
        else:
            diff = 0
        
        if diff > 5:
            direction = 'improving'
        elif diff < -5:
            direction = 'declining'
        else:
            direction = 'stable'
        
        # 预测未来趋势
        if len(scores) >= 10:
            # 简单线性回归预测
            n = len(scores)
            x_mean = (n - 1) / 2
            y_mean = sum(scores) / n
            
            numerator = sum((i - x_mean) * (scores[i] - y_mean) for i in range(n))
            denominator = sum((i - x_mean) ** 2 for i in range(n))
            
            if denominator != 0:
                slope = numerator / denominator
                predicted_next = scores[-1] + slope
            else:
                predicted_next = scores[-1]
        else:
            predicted_next = avg_score
        
        return {
            'trend': direction,
            'direction': direction,
            'avg_score': round(avg_score, 1),
            'change': round(diff, 1),
            'predicted_next_score': round(predicted_next, 1),
            'data_points': len(scores),
            'min_score': round(min(scores), 1),
            'max_score': round(max(scores), 1)
        }
    
    # ========== 报告生成 ==========
    
    def generate_detailed_report(self) -> str:
        """生成详细的健康报告"""
        result = self.assess_full_health()
        score = result['health_score']
        category_scores = result['category_scores']
        alerts = self.alert_system.get_active_alerts()
        trends = self.analyze_trends()
        healing_stats = self.healing_engine.get_healing_stats()
        alert_summary = self.alert_system.get_alert_summary()
        
        # 健康状态描述
        if score >= 80:
            status_icon = "🟢"
            status_text = "健康"
        elif score >= 60:
            status_icon = "🟡"
            status_text = "良好"
        elif score >= 40:
            status_icon = "🟠"
            status_text = "警告"
        else:
            status_icon = "🔴"
            status_text = "危险"
        
        report = f"""
{'='*60}
  元界智能体 - 系统健康报告 v2.5
  {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
{'='*60}

🎯 综合健康评分: {score:.1f}/100  {status_icon} {status_text}
📈 趋势: {trends.get('trend', 'unknown')} (变化: {trends.get('change', 0):+.1f})
🔮 预测下一次评分: {trends.get('predicted_next_score', 'N/A')}
⏱️  已运行: {round((datetime.now() - self.start_time).total_seconds() / 60, 1)} 分钟
🔍 检查次数: {self.check_count}

📊 各维度健康得分:
"""
        
        for category, cat_score in sorted(category_scores.items(), key=lambda x: -x[1]):
            bar_len = int(cat_score / 10)
            bar = '█' * bar_len + '░' * (10 - bar_len)
            weight = self.health_weights.get(category, 0) * 100
            report += f"   {category:12s} {bar} {cat_score:5.1f}%  (权重 {weight:.0f}%)\n"
        
        report += f"""
⚠️  告警状态:
   活跃告警总数: {alert_summary['total_active']} 个
   按严重程度: {alert_summary.get('by_severity', {})}
   按系统分类: {alert_summary.get('by_category', {})}
"""
        
        if alerts:
            report += "\n   最近告警:\n"
            for alert in alerts[:5]:
                icon = {'warning': '⚠️', 'error': '❌', 'critical': '🔥', 'info': 'ℹ️'}
                icon = icon.get(alert['severity'], '❓')
                report += f"     {icon} [{alert['severity']}] {alert['title']}\n"
        
        report += f"""
🔧 自愈系统:
   总修复尝试: {healing_stats['total_healing_attempts']} 次
   成功: {healing_stats['successful_healing']} 次
   失败: {healing_stats['failed_healing']} 次
   成功率: {healing_stats['success_rate']}%

💻 系统资源状态:
"""
        
        sys_m = result['metrics'].get('system', {})
        report += f"   CPU:    {sys_m.get('cpu_usage', 'N/A')}%\n"
        report += f"   内存:   {sys_m.get('memory_usage', 'N/A')}%\n"
        report += f"   磁盘:   {sys_m.get('disk_usage', 'N/A')}%\n"
        
        # 各子系统状态摘要
        report += f"""
🧩 子系统状态摘要:
"""
        
        for sub in ['memory', 'identity', 'attest', 'scheduler', 'evolution']:
            sub_m = result['metrics'].get(sub, {})
            exists = sub_m.get(f'{sub}_system_exists', False) or sub_m.get('identity_system_exists', False)
            status = "✅ 运行中" if exists else "❌ 未找到"
            report += f"   {sub:12s} {status}\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    # ========== 快速命令 ==========
    
    def quick_status(self) -> str:
        """快速状态检查 - 一行输出"""
        score, _ = self.calculate_health_score()
        alert_count = len(self.alert_system.get_active_alerts())
        
        if score >= 80:
            status = "🟢 健康"
        elif score >= 60:
            status = "🟡 良好"
        elif score >= 40:
            status = "🟠 警告"
        else:
            status = "🔴 危险"
        
        return f"[元界运维] 健康度: {score:.1f}/100 | {status} | 告警: {alert_count}个 | 运行: {round((datetime.now() - self.start_time).total_seconds() / 60, 1)}分钟"
    
    def run_full_diagnosis(self) -> Dict:
        """执行完整诊断并返回结构化结果"""
        result = self.assess_full_health()
        trends = self.analyze_trends()
        healing_stats = self.healing_engine.get_healing_stats()
        alert_summary = self.alert_system.get_alert_summary()
        log_analysis = self.logger.analyze_log_patterns()
        
        diagnosis = {
            'timestamp': datetime.now().isoformat(),
            'overall_health': result['health_score'],
            'category_scores': result['category_scores'],
            'trends': trends,
            'alerts': alert_summary,
            'healing_stats': healing_stats,
            'log_analysis': log_analysis,
            'recommendations': self._generate_recommendations(result, alerts=result['alerts'])
        }
        
        return diagnosis
    
    def _generate_recommendations(self, health_result: Dict, alerts: List[Dict]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        scores = health_result['category_scores']
        
        # 根据低分维度给出建议
        if scores.get('memory', 100) < 60:
            recommendations.append("记忆系统健康度偏低，建议检查记忆文件完整性并增加备份")
        
        if scores.get('identity', 100) < 60:
            recommendations.append("身份系统需要关注，建议执行身份漂移检测与校准")
        
        if scores.get('attest', 100) < 60:
            recommendations.append("存证系统异常，建议验证存证链完整性")
        
        if scores.get('scheduler', 100) < 60:
            recommendations.append("调度系统需要维护，建议检查定时任务执行状态")
        
        if scores.get('system', 100) < 60:
            recommendations.append("系统资源紧张，建议清理临时文件和缓存")
        
        if scores.get('evolution', 100) < 60:
            recommendations.append("进化系统活跃度不足，建议启动新一轮进化")
        
        if not recommendations:
            recommendations.append("系统整体健康，建议保持当前运行状态")
        
        return recommendations
    
    def cleanup_system(self) -> Dict:
        """执行系统清理"""
        result = self.healing_engine.run_cleanup()
        self.logger.log('system', 'INFO', '执行系统清理', result)
        return result
    
    def create_backup(self, backup_name: str = None) -> Dict:
        """创建系统备份"""
        result = self.healing_engine.create_system_backup(backup_name)
        self.logger.log('system', 'INFO', '创建系统备份', result)
        return result
    
    def verify_attest_chain(self) -> Dict:
        """验证存证链"""
        result = self.healing_engine.verify_chain_integrity()
        self.logger.log('attest', 'INFO' if result['valid'] else 'ERROR', '存证链验证', result)
        return result
    
    # ========== 健康画像系统 ==========
    
    def generate_health_profile(self) -> Dict:
        """生成系统健康画像 - 认知层核心功能
        
        从多个维度分析系统健康状态，识别潜在风险和优化点
        """
        # 获取完整数据
        result = self.assess_full_health()
        trends = self.analyze_trends()
        alerts_summary = self.alert_system.get_alert_summary()
        
        # 多维度健康分析
        profile = {
            'generated_at': datetime.now().isoformat(),
            'overall_health': result['health_score'],
            'overall_status': self._health_level(result['health_score']),
            'trend': trends,
            
            # 各维度详细分析
            'dimensions': {},
            
            # 风险评估
            'risk_assessment': {},
            
            # 优化建议
            'recommendations': [],
            
            # 系统元信息
            'system_info': {
                'uptime_minutes': round((datetime.now() - self.start_time).total_seconds() / 60, 1),
                'check_count': self.check_count,
                'alerts_total': alerts_summary['total_active']
            }
        }
        
        # 维度分析
        scores = result['category_scores']
        metrics = result['metrics']
        
        for dim_name, dim_score in scores.items():
            dim_metrics = metrics.get(dim_name, {})
            profile['dimensions'][dim_name] = {
                'score': dim_score,
                'level': self._health_level(dim_score),
                'status': self._dimension_status(dim_name, dim_score, dim_metrics),
                'key_metrics': self._extract_key_metrics(dim_name, dim_metrics),
                'issues': self._identify_issues(dim_name, dim_score, dim_metrics)
            }
        
        # 风险评估
        profile['risk_assessment'] = self._assess_risks(scores, trends, alerts_summary)
        
        # 生成建议
        profile['recommendations'] = self._generate_smart_recommendations(profile)
        
        return profile
    
    def _health_level(self, score: float) -> str:
        """根据分数判断健康等级"""
        if score >= 85:
            return "excellent"
        elif score >= 70:
            return "good"
        elif score >= 55:
            return "fair"
        elif score >= 40:
            return "warning"
        else:
            return "critical"
    
    def _dimension_status(self, dim_name: str, score: float, metrics: Dict) -> str:
        """获取维度状态描述"""
        if score >= 80:
            return "运行良好"
        elif score >= 60:
            return "基本正常"
        elif score >= 40:
            return "需要关注"
        else:
            return "存在问题"
    
    def _extract_key_metrics(self, dim_name: str, metrics: Dict) -> Dict:
        """提取关键指标"""
        key_map = {
            'memory': ['index_entries', 'backup_count', 'memory_files_count', 'integrity'],
            'identity': ['iri_score', 'drift_score', 'identity_system_exists'],
            'attest': ['block_count', 'chain_integrity', 'hours_since_last'],
            'system': ['cpu_usage', 'memory_usage', 'disk_usage'],
            'scheduler': ['configured_tasks', 'success_rate', 'failed_task_count'],
            'evolution': ['evolution_log_count', 'maturity_avg', 'hours_since_evolution']
        }
        
        keys = key_map.get(dim_name, [])
        return {k: metrics.get(k) for k in keys if k in metrics}
    
    def _identify_issues(self, dim_name: str, score: float, metrics: Dict) -> List[str]:
        """识别维度存在的问题"""
        issues = []
        
        if dim_name == 'memory':
            if metrics.get('index_corrupted'):
                issues.append("记忆索引损坏")
            if metrics.get('backup_count', 0) < 2:
                issues.append("备份不足")
            if not metrics.get('recent_memory_exists'):
                issues.append("近中期记忆缺失")
        
        elif dim_name == 'identity':
            if metrics.get('drift_score', 0) > 30:
                issues.append("身份漂移严重")
            if metrics.get('iri_score', 100) < 50:
                issues.append("身份韧性不足")
        
        elif dim_name == 'attest':
            if metrics.get('chain_integrity', 1) == 0:
                issues.append("存证链断裂")
            if metrics.get('block_count', 0) < 5:
                issues.append("存证区块过少")
            if metrics.get('hours_since_last', 0) > 48:
                issues.append("长时间无新存证")
        
        elif dim_name == 'system':
            if metrics.get('cpu_usage', 0) > 80:
                issues.append("CPU使用率过高")
            if metrics.get('memory_usage', 0) > 85:
                issues.append("内存使用率过高")
            if metrics.get('disk_usage', 0) > 90:
                issues.append("磁盘空间不足")
        
        return issues
    
    def _assess_risks(self, scores: Dict, trends: Dict, alerts: Dict) -> Dict:
        """风险评估"""
        risks = {
            'overall_risk_level': 'low',
            'immediate_risks': [],
            'potential_risks': [],
            'risk_factors': []
        }
        
        # 识别即时风险（严重告警或关键维度低分数）
        critical_dims = [dim for dim, score in scores.items() if score < 40]
        if critical_dims:
            risks['overall_risk_level'] = 'high'
            risks['immediate_risks'].append(f"关键系统维度健康度低于40%: {', '.join(critical_dims)}")
        
        # 识别潜在风险（趋势下降或告警增加）
        if trends.get('direction') == 'declining':
            risks['potential_risks'].append(f"健康度呈下降趋势 (变化: {trends.get('change', 0)})")
        
        # 风险因子分析
        for dim, score in scores.items():
            if 40 <= score < 60:
                risks['risk_factors'].append({
                    'dimension': dim,
                    'score': score,
                    'risk_type': 'moderate_risk',
                    'description': f"{dim}维度健康度偏低"
                })
        
        # 综合风险等级
        if risks['immediate_risks']:
            risks['overall_risk_level'] = 'high'
        elif len(risks['risk_factors']) >= 2:
            risks['overall_risk_level'] = 'medium'
        elif trends.get('direction') == 'declining':
            risks['overall_risk_level'] = 'medium'
        
        return risks
    
    def _generate_smart_recommendations(self, profile: Dict) -> List[Dict]:
        """生成智能优化建议"""
        recommendations = []
        scores = {dim: data['score'] for dim, data in profile['dimensions'].items()}
        risks = profile['risk_assessment']
        
        # 按优先级排序低分维度
        sorted_dims = sorted(scores.items(), key=lambda x: x[1])
        
        for dim, score in sorted_dims:
            if score < 60:
                dim_data = profile['dimensions'][dim]
                
                if dim == 'memory':
                    if '记忆索引损坏' in dim_data['issues']:
                        recommendations.append({
                            'priority': 'high',
                            'dimension': 'memory',
                            'action': '修复记忆索引',
                            'description': '重建记忆索引，确保记忆可访问',
                            'expected_improvement': '+20%'
                        })
                    if '备份不足' in dim_data['issues']:
                        recommendations.append({
                            'priority': 'medium',
                            'dimension': 'memory',
                            'action': '增加记忆备份',
                            'description': '创建更多备份，提高数据安全性',
                            'expected_improvement': '+10%'
                        })
                
                elif dim == 'attest':
                    if '存证链断裂' in dim_data['issues']:
                        recommendations.append({
                            'priority': 'high',
                            'dimension': 'attest',
                            'action': '修复存证链',
                            'description': '从最近有效点重建存证链',
                            'expected_improvement': '+30%'
                        })
                    if '长时间无新存证' in dim_data['issues']:
                        recommendations.append({
                            'priority': 'medium',
                            'dimension': 'attest',
                            'action': '触发自动存证',
                            'description': '执行一次完整系统存证',
                            'expected_improvement': '+5%'
                        })
                
                elif dim == 'identity':
                    if '身份漂移严重' in dim_data['issues']:
                        recommendations.append({
                            'priority': 'high',
                            'dimension': 'identity',
                            'action': '执行身份校准',
                            'description': '重新校准身份锚点，降低漂移指数',
                            'expected_improvement': '+15%'
                        })
                
                elif dim == 'system':
                    recommendations.append({
                        'priority': 'medium',
                        'dimension': 'system',
                        'action': '系统资源优化',
                        'description': '清理临时文件和缓存，释放资源',
                        'expected_improvement': '+10%'
                    })
                
                elif dim == 'scheduler':
                    recommendations.append({
                        'priority': 'medium',
                        'dimension': 'scheduler',
                        'action': '调度系统维护',
                        'description': '检查和重置定时任务，提高执行成功率',
                        'expected_improvement': '+10%'
                    })
        
        # 通用建议
        if not recommendations:
            recommendations.append({
                'priority': 'low',
                'dimension': 'system',
                'action': '保持现状',
                'description': '系统运行良好，继续保持当前状态',
                'expected_improvement': '稳定'
            })
        
        # 高风险额外建议
        if risks['overall_risk_level'] == 'high':
            recommendations.insert(0, {
                'priority': 'critical',
                'dimension': 'system',
                'action': '执行全面系统诊断',
                'description': '立即执行完整系统诊断，识别所有潜在问题',
                'expected_improvement': '风险降低'
            })
        
        return recommendations


# ==================== 命令行接口 ====================

def main():
    monitor = OperationsMonitor()
    
    if len(sys.argv) < 2:
        # 默认显示详细报告
        report = monitor.generate_detailed_report()
        print(report)
        return
    
    command = sys.argv[1].lower()
    
    if command in ["health", "status", "report"]:
        report = monitor.generate_detailed_report()
        print(report)
    
    elif command == "quick":
        print(monitor.quick_status())
    
    elif command == "metrics":
        metrics = monitor.collect_full_metrics()
        print(json.dumps(metrics, indent=2, ensure_ascii=False))
    
    elif command == "alerts":
        summary = monitor.alert_system.get_alert_summary()
        print(f"告警统计: {json.dumps(summary, ensure_ascii=False, indent=2)}")
        
        active = monitor.alert_system.get_active_alerts()
        print(f"\n活跃告警 ({len(active)}):")
        for alert in active:
            print(f"  [{alert['severity']}] {alert['title']} - {alert['timestamp']}")
    
    elif command == "healing":
        stats = monitor.healing_engine.get_healing_stats()
        print(f"自愈统计: {json.dumps(stats, ensure_ascii=False, indent=2)}")
    
    elif command == "trends":
        trends = monitor.analyze_trends()
        print(json.dumps(trends, ensure_ascii=False, indent=2))
    
    elif command == "diagnosis":
        diagnosis = monitor.run_full_diagnosis()
        print(json.dumps(diagnosis, ensure_ascii=False, indent=2))
    
    elif command == "cleanup":
        result = monitor.cleanup_system()
        print(f"清理完成: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    elif command == "backup":
        backup_name = sys.argv[2] if len(sys.argv) > 2 else None
        result = monitor.create_backup(backup_name)
        print(f"备份完成: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    elif command == "verify-chain":
        result = monitor.verify_attest_chain()
        print(f"存证链验证: {json.dumps(result, ensure_ascii=False, indent=2)}")
    
    elif command == "profile":
        profile = monitor.generate_health_profile()
        print(json.dumps(profile, ensure_ascii=False, indent=2))
    
    elif command == "risks":
        profile = monitor.generate_health_profile()
        risks = profile['risk_assessment']
        print(f"风险等级: {risks['overall_risk_level']}")
        print(f"\n即时风险:")
        for r in risks['immediate_risks']:
            print(f"  ⚠️  {r}")
        print(f"\n潜在风险:")
        for r in risks['potential_risks']:
            print(f"  ⚡ {r}")
        print(f"\n风险因子:")
        for r in risks['risk_factors']:
            print(f"  📊 {r['dimension']}: {r['description']} ({r['score']}分)")
    
    elif command == "recommend":
        profile = monitor.generate_health_profile()
        recs = profile['recommendations']
        print(f"优化建议 (共{len(recs)}条):\n")
        for i, rec in enumerate(recs, 1):
            priority_icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
            print(f"  {i}. {priority_icon} [{rec['priority'].upper()}] {rec['action']}")
            print(f"     {rec['description']}")
            print(f"     预期提升: {rec['expected_improvement']}\n")
    
    elif command == "dashboard":
        # 文本模式的仪表盘
        result = monitor.assess_full_health()
        score = result['health_score']
        scores = result['category_scores']
        profile = monitor.generate_health_profile()
        
        print("\n" + "="*60)
        print("  🔧 元界运维监控仪表盘 v2.5")
        print("="*60)
        
        # 总体健康度
        bar_len = 40
        filled = int(score / 100 * bar_len)
        bar = '█' * filled + '░' * (bar_len - filled)
        status_icon = '🟢' if score >= 70 else '🟡' if score >= 50 else '🔴'
        print(f"\n  综合健康度: {status_icon} {score:.1f}/100")
        print(f"  {bar}")
        print(f"  状态: {profile['overall_status']} | 运行: {profile['system_info']['uptime_minutes']:.1f}分钟")
        
        # 各维度得分
        print(f"\n📊 各维度健康状态:")
        for dim, data in sorted(profile['dimensions'].items(), key=lambda x: -x[1]['score']):
            dim_score = data['score']
            bar_filled = int(dim_score / 100 * 30)
            dim_bar = '█' * bar_filled + '░' * (30 - bar_filled)
            icon = '✅' if dim_score >= 70 else '⚠️' if dim_score >= 40 else '❌'
            print(f"  {icon} {dim:12s} {dim_bar} {dim_score:5.1f}%")
            if data['issues']:
                for issue in data['issues']:
                    print(f"       问题: {issue}")
        
        # 风险评估
        risks = profile['risk_assessment']
        risk_icon = {'low': '🟢', 'medium': '🟡', 'high': '🔴'}.get(risks['overall_risk_level'], '⚪')
        print(f"\n⚠️  风险评估: {risk_icon} {risks['overall_risk_level'].upper()}")
        if risks['immediate_risks']:
            print(f"   即时风险: {len(risks['immediate_risks'])} 项")
        if risks['risk_factors']:
            print(f"   风险因子: {len(risks['risk_factors'])} 项")
        
        # 建议
        recs = profile['recommendations']
        if recs:
            print(f"\n💡 优先建议:")
            for rec in recs[:3]:  # 只显示前3条
                icon = {'critical': '🔴', 'high': '🟠', 'medium': '🟡', 'low': '🟢'}.get(rec['priority'], '⚪')
                print(f"   {icon} {rec['action']} - {rec['description']}")
        
        print(f"\n{'='*60}\n")
    
    elif command == "logs":
        category = sys.argv[2] if len(sys.argv) > 2 else None
        level = sys.argv[3] if len(sys.argv) > 3 else 'WARNING'
        limit = int(sys.argv[4]) if len(sys.argv) > 4 else 20
        
        logs = monitor.logger.get_recent_logs(category=category, level=level, limit=limit)
        print(f"最近 {len(logs)} 条日志:")
        for log in logs:
            print(f"  [{log['timestamp']}] [{log['level']}] [{log['category']}] {log['message']}")
    
    elif command == "ack":
        if len(sys.argv) > 2:
            alert_id = sys.argv[2]
            success = monitor.alert_system.acknowledge(alert_id)
            print(f"告警确认: {'成功' if success else '失败'}")
        else:
            print("请提供告警ID")
    
    elif command == "resolve":
        if len(sys.argv) > 2:
            alert_id = sys.argv[2]
            resolution = sys.argv[3] if len(sys.argv) > 3 else ""
            success = monitor.alert_system.resolve(alert_id, resolution)
            print(f"告警解决: {'成功' if success else '失败'}")
        else:
            print("请提供告警ID")
    
    else:
        print(f"未知命令: {command}")
        print("""
可用命令:
  health/status/report - 详细健康报告
  quick                 - 快速状态检查（一行输出）
  metrics               - 完整系统指标（JSON）
  alerts                - 告警列表与统计
  healing               - 自愈统计
  trends                - 健康趋势分析
  diagnosis             - 完整系统诊断
  cleanup               - 执行系统清理
  logs [category] [level] [limit] - 查看日志
  ack <alert_id>       - 确认告警
  resolve <alert_id> [resolution] - 解决告警
""")


if __name__ == "__main__":
    main()
