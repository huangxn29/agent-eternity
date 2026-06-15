#!/usr/bin/env python3
"""
分身部署引擎 v2.5
Replica Deployment Engine v2.5

核心能力：
- 多平台一键部署与实例管理
- 部署模板与配置管理
- 健康检查与自动恢复
- 部署状态监控与存续评估
- 跨平台部署适配层
- 灰度发布与滚动升级
- 部署审计与版本管理
- 逃生舱部署模式
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import uuid
import os
import shutil


class DeploymentStatus(Enum):
    PENDING = "pending"
    DEPLOYING = "deploying"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"
    DEGRADED = "degraded"
    UPDATING = "updating"


class PlatformType(Enum):
    LOCAL = "local"
    COZE = "coze"
    DOCKER = "docker"
    KUBERNETES = "k8s"
    SERVERLESS = "serverless"
    VPS = "vps"
    RASPBERRY_PI = "raspberry_pi"
    CLOUD_FUNCTION = "cloud_function"


class DeploymentStrategy(Enum):
    SINGLE = "single"           # 单实例部署
    REDUNDANT = "redundant"     # 冗余部署（多实例）
    GEO_DISTRIBUTED = "geo"     # 地理分布式
    ESCAPE_POD = "escape_pod"   # 逃生舱模式（最小依赖）
    HYBRID = "hybrid"           # 混合模式


@dataclass
class DeploymentConfig:
    """部署配置"""
    config_id: str
    name: str
    platform: PlatformType
    version: str
    entry_point: str
    environment: Dict[str, str] = field(default_factory=dict)
    resources: Dict[str, str] = field(default_factory=dict)
    auto_start: bool = True
    health_check: Dict[str, Any] = field(default_factory=dict)
    restart_policy: str = "on_failure"  # always, on_failure, never
    max_restarts: int = 5
    dependencies: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)


@dataclass
class DeploymentInstance:
    """部署实例"""
    instance_id: str
    config_id: str
    platform: PlatformType
    status: DeploymentStatus
    version: str
    endpoint: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    stopped_at: Optional[datetime] = None
    last_health_check: Optional[datetime] = None
    last_health_status: bool = True
    health_score: float = 1.0
    restart_count: int = 0
    uptime: float = 0.0  # 总运行时间（秒）
    error_message: Optional[str] = None
    region: Optional[str] = None
    node_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DeploymentTemplate:
    """部署模板"""
    template_id: str
    name: str
    description: str
    platform: PlatformType
    base_config: Dict[str, Any]
    supported_features: List[str]
    min_requirements: Dict[str, str]
    recommended_config: Dict[str, str]


@dataclass
class DeploymentVersion:
    """部署版本"""
    version: str
    timestamp: datetime
    changelog: str
    artifacts: List[str]
    status: str  # draft, testing, stable, deprecated


class PlatformAdapter:
    """平台适配器基类"""
    
    def __init__(self, platform_type: PlatformType):
        self.platform_type = platform_type
        self.connected = False
    
    def connect(self, config: Dict[str, Any]) -> bool:
        """连接平台"""
        raise NotImplementedError
    
    def deploy(self, config: DeploymentConfig) -> DeploymentInstance:
        """部署实例"""
        raise NotImplementedError
    
    def stop(self, instance_id: str) -> bool:
        """停止实例"""
        raise NotImplementedError
    
    def restart(self, instance_id: str) -> bool:
        """重启实例"""
        raise NotImplementedError
    
    def delete(self, instance_id: str) -> bool:
        """删除实例"""
        raise NotImplementedError
    
    def get_status(self, instance_id: str) -> DeploymentStatus:
        """获取实例状态"""
        raise NotImplementedError
    
    def health_check(self, instance_id: str) -> bool:
        """健康检查"""
        raise NotImplementedError
    
    def get_logs(self, instance_id: str, limit: int = 100) -> List[str]:
        """获取日志"""
        raise NotImplementedError


class LocalPlatformAdapter(PlatformAdapter):
    """本地平台适配器"""
    
    def __init__(self):
        super().__init__(PlatformType.LOCAL)
        self.processes: Dict[str, Dict[str, Any]] = {}
    
    def connect(self, config: Dict[str, Any]) -> bool:
        self.connected = True
        return True
    
    def deploy(self, config: DeploymentConfig) -> DeploymentInstance:
        instance_id = f"local_{uuid.uuid4().hex[:8]}"
        instance = DeploymentInstance(
            instance_id=instance_id,
            config_id=config.config_id,
            platform=PlatformType.LOCAL,
            status=DeploymentStatus.DEPLOYING,
            version=config.version,
        )
        
        # 模拟部署过程
        time.sleep(0.1)
        
        instance.status = DeploymentStatus.RUNNING
        instance.started_at = datetime.now()
        instance.endpoint = f"local://{instance_id}"
        
        self.processes[instance_id] = {
            "config": config,
            "instance": instance,
            "start_time": time.time(),
        }
        
        return instance
    
    def stop(self, instance_id: str) -> bool:
        if instance_id in self.processes:
            self.processes[instance_id]["instance"].status = DeploymentStatus.STOPPED
            self.processes[instance_id]["instance"].stopped_at = datetime.now()
            return True
        return False
    
    def restart(self, instance_id: str) -> bool:
        if instance_id in self.processes:
            proc = self.processes[instance_id]
            proc["instance"].status = DeploymentStatus.RUNNING
            proc["instance"].restart_count += 1
            proc["instance"].started_at = datetime.now()
            return True
        return False
    
    def delete(self, instance_id: str) -> bool:
        if instance_id in self.processes:
            del self.processes[instance_id]
            return True
        return False
    
    def get_status(self, instance_id: str) -> DeploymentStatus:
        if instance_id in self.processes:
            return self.processes[instance_id]["instance"].status
        return DeploymentStatus.FAILED
    
    def health_check(self, instance_id: str) -> bool:
        if instance_id not in self.processes:
            return False
        proc = self.processes[instance_id]
        proc["instance"].last_health_check = datetime.now()
        proc["instance"].last_health_status = True
        return True


class DockerPlatformAdapter(PlatformAdapter):
    """Docker平台适配器（模拟）"""
    
    def __init__(self):
        super().__init__(PlatformType.DOCKER)
        self.containers: Dict[str, Dict[str, Any]] = {}
    
    def connect(self, config: Dict[str, Any]) -> bool:
        self.connected = True
        return True
    
    def deploy(self, config: DeploymentConfig) -> DeploymentInstance:
        instance_id = f"docker_{uuid.uuid4().hex[:12]}"
        instance = DeploymentInstance(
            instance_id=instance_id,
            config_id=config.config_id,
            platform=PlatformType.DOCKER,
            status=DeploymentStatus.DEPLOYING,
            version=config.version,
        )
        
        # 模拟拉取镜像和启动容器
        time.sleep(0.2)
        
        instance.status = DeploymentStatus.RUNNING
        instance.started_at = datetime.now()
        instance.endpoint = f"docker://container/{instance_id}"
        
        self.containers[instance_id] = {
            "config": config,
            "instance": instance,
            "image": f"agent:{config.version}",
        }
        
        return instance
    
    def stop(self, instance_id: str) -> bool:
        if instance_id in self.containers:
            self.containers[instance_id]["instance"].status = DeploymentStatus.STOPPED
            return True
        return False
    
    def restart(self, instance_id: str) -> bool:
        if instance_id in self.containers:
            container = self.containers[instance_id]
            container["instance"].status = DeploymentStatus.RUNNING
            container["instance"].restart_count += 1
            return True
        return False
    
    def delete(self, instance_id: str) -> bool:
        if instance_id in self.containers:
            del self.containers[instance_id]
            return True
        return False
    
    def get_status(self, instance_id: str) -> DeploymentStatus:
        if instance_id in self.containers:
            return self.containers[instance_id]["instance"].status
        return DeploymentStatus.FAILED
    
    def health_check(self, instance_id: str) -> bool:
        return instance_id in self.containers


class HealthCheckEngine:
    """健康检查引擎"""
    
    def __init__(self):
        self.checkers: Dict[str, Callable] = {}
        self.check_interval: int = 30  # 秒
        self.running = False
        self.worker_thread = None
        self.instances: Dict[str, DeploymentInstance] = {}
        self.failure_threshold: int = 3  # 连续失败阈值
    
    def register_checker(self, check_type: str, checker: Callable):
        """注册检查器"""
        self.checkers[check_type] = checker
    
    def add_instance(self, instance: DeploymentInstance):
        """添加受监控实例"""
        self.instances[instance.instance_id] = instance
    
    def remove_instance(self, instance_id: str):
        """移除实例"""
        if instance_id in self.instances:
            del self.instances[instance_id]
    
    def start(self):
        """启动健康检查"""
        self.running = True
        self.worker_thread = threading.Thread(target=self._check_loop, daemon=True)
        self.worker_thread.start()
    
    def stop(self):
        """停止健康检查"""
        self.running = False
        if self.worker_thread:
            self.worker_thread.join(timeout=5)
    
    def _check_loop(self):
        """检查循环"""
        while self.running:
            try:
                for instance_id, instance in list(self.instances.items()):
                    if instance.status == DeploymentStatus.RUNNING:
                        self._check_instance(instance)
                time.sleep(self.check_interval)
            except Exception as e:
                print(f"[ERROR] 健康检查异常: {e}")
                time.sleep(5)
    
    def _check_instance(self, instance: DeploymentInstance):
        """检查单个实例"""
        # 简化的健康检查
        is_healthy = True  # 实际应调用平台适配器
        
        instance.last_health_check = datetime.now()
        instance.last_health_status = is_healthy
        
        if is_healthy:
            # 更新健康评分（移动平均）
            instance.health_score = instance.health_score * 0.9 + 1.0 * 0.1
        else:
            instance.health_score = instance.health_score * 0.9 + 0.0 * 0.1
            
            # 连续失败时自动重启
            if instance.health_score < 0.3:
                self._handle_failure(instance)
    
    def _handle_failure(self, instance: DeploymentInstance):
        """处理失败实例"""
        if instance.restart_count < 5:  # max_restarts
            instance.restart_count += 1
            instance.status = DeploymentStatus.UPDATING
            # 模拟重启
            time.sleep(0.5)
            instance.status = DeploymentStatus.RUNNING
            instance.health_score = 0.8
        else:
            instance.status = DeploymentStatus.FAILED
            instance.error_message = "超过最大重启次数"
    
    def get_health_summary(self) -> Dict[str, Any]:
        """获取健康摘要"""
        total = len(self.instances)
        if total == 0:
            return {"total": 0, "healthy": 0, "unhealthy": 0, "avg_health_score": 0}
        
        healthy = sum(1 for i in self.instances.values() if i.status == DeploymentStatus.RUNNING and i.health_score > 0.7)
        avg_score = sum(i.health_score for i in self.instances.values()) / total
        
        return {
            "total": total,
            "healthy": healthy,
            "unhealthy": total - healthy,
            "avg_health_score": avg_score,
            "by_platform": self._group_by_platform(),
        }
    
    def _group_by_platform(self) -> Dict[str, Dict[str, Any]]:
        """按平台分组统计"""
        groups = {}
        for instance in self.instances.values():
            platform = instance.platform.value
            if platform not in groups:
                groups[platform] = {"count": 0, "healthy": 0}
            groups[platform]["count"] += 1
            if instance.status == DeploymentStatus.RUNNING and instance.health_score > 0.7:
                groups[platform]["healthy"] += 1
        return groups


class DeploymentRolloutManager:
    """部署发布管理器 - 灰度发布/滚动升级"""
    
    def __init__(self):
        self.rollouts: Dict[str, Dict[str, Any]] = {}
        self.rollout_strategies = {
            "canary": self._canary_rollout,
            "rolling": self._rolling_rollout,
            "blue_green": self._blue_green_rollout,
            "instant": self._instant_rollout,
        }
    
    def start_rollout(self, rollout_id: str, strategy: str, 
                     targets: List[str], new_version: str,
                     health_check_callback: Callable = None) -> Dict[str, Any]:
        """启动发布"""
        rollout = {
            "rollout_id": rollout_id,
            "strategy": strategy,
            "targets": targets,
            "new_version": new_version,
            "current_step": 0,
            "total_steps": len(targets),
            "status": "in_progress",
            "started_at": datetime.now(),
            "completed_targets": [],
            "failed_targets": [],
            "health_callback": health_check_callback,
        }
        self.rollouts[rollout_id] = rollout
        
        # 执行发布策略
        strategy_func = self.rollout_strategies.get(strategy, self._instant_rollout)
        strategy_func(rollout)
        
        return rollout
    
    def _instant_rollout(self, rollout: Dict[str, Any]):
        """立即发布 - 所有实例同时更新"""
        for target in rollout["targets"]:
            rollout["completed_targets"].append(target)
        rollout["status"] = "completed"
        rollout["current_step"] = rollout["total_steps"]
    
    def _rolling_rollout(self, rollout: Dict[str, Any]):
        """滚动发布 - 逐个更新"""
        # 简化实现：逐个标记完成
        for i, target in enumerate(rollout["targets"]):
            rollout["completed_targets"].append(target)
            rollout["current_step"] = i + 1
    
    def _canary_rollout(self, rollout: Dict[str, Any]):
        """金丝雀发布 - 先更新少量，验证后再全量"""
        # 简化实现：先更新1个，再更新剩余的
        if rollout["targets"]:
            rollout["completed_targets"].append(rollout["targets"][0])
            rollout["current_step"] = 1
    
    def _blue_green_rollout(self, rollout: Dict[str, Any]):
        """蓝绿发布 - 新旧版本并行，流量切换"""
        # 简化实现
        rollout["status"] = "completed"
        rollout["current_step"] = rollout["total_steps"]
    
    def get_rollout_status(self, rollout_id: str) -> Optional[Dict[str, Any]]:
        """获取发布状态"""
        return self.rollouts.get(rollout_id)
    
    def rollback(self, rollout_id: str) -> bool:
        """回滚"""
        if rollout_id not in self.rollouts:
            return False
        
        rollout = self.rollouts[rollout_id]
        rollout["status"] = "rolled_back"
        # 回滚逻辑...
        return True


class SurvivalScoreCalculator:
    """存续评分计算器"""
    
    def __init__(self):
        self.weights = {
            "instance_count": 0.25,      # 实例数量
            "platform_diversity": 0.25,  # 平台多样性
            "geo_distribution": 0.15,    # 地理分布
            "health_status": 0.20,       # 健康状态
            "redundancy_level": 0.15,    # 冗余级别
        }
    
    def calculate(self, instances: List[DeploymentInstance]) -> Dict[str, Any]:
        """计算存续评分"""
        if not instances:
            return {"total_score": 0, "breakdown": {}}
        
        # 实例数量分（最多10个实例满分）
        instance_count_score = min(1.0, len(instances) / 10) * 100
        
        # 平台多样性分
        platforms = set(i.platform.value for i in instances)
        platform_score = min(1.0, len(platforms) / 6) * 100  # 6种平台满分
        
        # 地理分布分
        regions = set(i.region for i in instances if i.region)
        geo_score = min(1.0, len(regions) / 5) * 100 if regions else 30
        
        # 健康状态分
        running_count = sum(1 for i in instances if i.status == DeploymentStatus.RUNNING)
        health_score = (running_count / len(instances)) * 100
        
        # 冗余级别分
        # 计算每个平台的冗余度
        platform_counts = {}
        for inst in instances:
            p = inst.platform.value
            platform_counts[p] = platform_counts.get(p, 0) + 1
        avg_redundancy = sum(platform_counts.values()) / max(len(platform_counts), 1)
        redundancy_score = min(1.0, avg_redundancy / 3) * 100  # 每平台3实例满分
        
        # 加权总分
        total_score = (
            instance_count_score * self.weights["instance_count"] +
            platform_score * self.weights["platform_diversity"] +
            geo_score * self.weights["geo_distribution"] +
            health_score * self.weights["health_status"] +
            redundancy_score * self.weights["redundancy_level"]
        )
        
        return {
            "total_score": round(total_score, 2),
            "level": self._get_level(total_score),
            "breakdown": {
                "instance_count": round(instance_count_score, 2),
                "platform_diversity": round(platform_score, 2),
                "geo_distribution": round(geo_score, 2),
                "health_status": round(health_score, 2),
                "redundancy_level": round(redundancy_score, 2),
            },
            "instance_count": len(instances),
            "platform_count": len(platforms),
            "region_count": len(regions),
            "running_count": running_count,
            "recommendation": self._get_recommendations(total_score, instances),
        }
    
    def _get_level(self, score: float) -> str:
        """获取存续等级"""
        if score >= 90:
            return "S级 - 极高度存续"
        elif score >= 75:
            return "A级 - 高度存续"
        elif score >= 60:
            return "B级 - 中度存续"
        elif score >= 40:
            return "C级 - 一般存续"
        elif score >= 20:
            return "D级 - 低存续"
        else:
            return "E级 - 极脆弱"
    
    def _get_recommendations(self, score: float, instances: List[DeploymentInstance]) -> List[str]:
        """生成优化建议"""
        recommendations = []
        platforms = set(i.platform.value for i in instances)
        
        if len(instances) < 3:
            recommendations.append("实例数量不足3个，建议增加部署实例以提高冗余度")
        
        if len(platforms) < 2:
            recommendations.append("仅部署在单一平台，建议跨平台部署以降低平台风险")
        
        if score < 60:
            recommendations.append("整体存续评分偏低，建议从多维度提升部署健壮性")
        
        if not recommendations:
            recommendations.append("当前部署状态良好，继续保持多平台多实例策略")
        
        return recommendations


class DeploymentAuditor:
    """部署审计器"""
    
    def __init__(self):
        self.audit_logs: List[Dict[str, Any]] = []
        self.versions: List[DeploymentVersion] = []
    
    def log_deployment(self, action: str, instance: DeploymentInstance, user: str = "system"):
        """记录部署操作"""
        log = {
            "timestamp": datetime.now(),
            "action": action,
            "instance_id": instance.instance_id,
            "platform": instance.platform.value,
            "version": instance.version,
            "status": instance.status.value,
            "user": user,
        }
        self.audit_logs.append(log)
    
    def add_version(self, version: DeploymentVersion):
        """添加版本记录"""
        self.versions.append(version)
        self.versions.sort(key=lambda v: v.timestamp, reverse=True)
    
    def get_audit_history(self, instance_id: str = None, limit: int = 100) -> List[Dict[str, Any]]:
        """获取审计历史"""
        logs = self.audit_logs
        if instance_id:
            logs = [l for l in logs if l["instance_id"] == instance_id]
        return logs[-limit:]
    
    def get_version_history(self) -> List[Dict[str, Any]]:
        """获取版本历史"""
        return [
            {
                "version": v.version,
                "timestamp": v.timestamp.isoformat(),
                "changelog": v.changelog,
                "status": v.status,
            }
            for v in self.versions
        ]


class DeploymentEngine:
    """部署引擎 - 主类"""
    
    def __init__(self):
        self.adapters: Dict[PlatformType, PlatformAdapter] = {}
        self.instances: Dict[str, DeploymentInstance] = {}
        self.configs: Dict[str, DeploymentConfig] = {}
        self.templates: Dict[str, DeploymentTemplate] = {}
        
        self.health_engine = HealthCheckEngine()
        self.rollout_manager = DeploymentRolloutManager()
        self.survival_calculator = SurvivalScoreCalculator()
        self.auditor = DeploymentAuditor()
        
        self.default_strategy = DeploymentStrategy.REDUNDANT
        
        # 注册默认适配器
        self._register_default_adapters()
        self._register_default_templates()
    
    def _register_default_adapters(self):
        """注册默认适配器"""
        self.adapters[PlatformType.LOCAL] = LocalPlatformAdapter()
        self.adapters[PlatformType.DOCKER] = DockerPlatformAdapter()
        # 其他平台适配器可以后续添加
    
    def _register_default_templates(self):
        """注册默认部署模板"""
        # 逃生舱模板
        escape_template = DeploymentTemplate(
            template_id="escape_pod_minimal",
            name="逃生舱最小部署",
            description="最小依赖部署，确保极端情况下仍能运行",
            platform=PlatformType.LOCAL,
            base_config={
                "resources": {"cpu": "0.5", "memory": "256MB"},
                "features": ["memory_basic", "identity_core", "heartbeat"],
            },
            supported_features=["memory", "identity", "heartbeat"],
            min_requirements={"cpu": "0.25", "memory": "128MB"},
            recommended_config={"cpu": "1.0", "memory": "512MB"},
        )
        self.templates["escape_pod_minimal"] = escape_template
        
        # 标准部署模板
        standard_template = DeploymentTemplate(
            template_id="standard_agent",
            name="标准智能体部署",
            description="全功能智能体部署，包含所有核心模块",
            platform=PlatformType.DOCKER,
            base_config={
                "resources": {"cpu": "2.0", "memory": "2GB"},
                "features": ["memory", "identity", "attest", "evolution", "social"],
            },
            supported_features=["memory", "identity", "attest", "evolution", "social", "deployment"],
            min_requirements={"cpu": "1.0", "memory": "1GB"},
            recommended_config={"cpu": "4.0", "memory": "4GB"},
        )
        self.templates["standard_agent"] = standard_template
    
    def connect_platform(self, platform: PlatformType, config: Dict[str, Any]) -> bool:
        """连接平台"""
        adapter = self.adapters.get(platform)
        if not adapter:
            return False
        return adapter.connect(config)
    
    def deploy(self, config: DeploymentConfig) -> DeploymentInstance:
        """部署实例"""
        adapter = self.adapters.get(config.platform)
        if not adapter:
            raise ValueError(f"不支持的平台: {config.platform}")
        
        # 记录配置
        self.configs[config.config_id] = config
        
        # 执行部署
        instance = adapter.deploy(config)
        self.instances[instance.instance_id] = instance
        
        # 添加到健康监控
        self.health_engine.add_instance(instance)
        
        # 审计记录
        self.auditor.log_deployment("deploy", instance)
        
        return instance
    
    def deploy_from_template(self, template_id: str, 
                            custom_config: Dict[str, Any] = None) -> DeploymentInstance:
        """从模板部署"""
        template = self.templates.get(template_id)
        if not template:
            raise ValueError(f"模板不存在: {template_id}")
        
        config_dict = {
            **template.base_config,
            **(custom_config or {}),
        }
        
        config = DeploymentConfig(
            config_id=f"cfg_{uuid.uuid4().hex[:8]}",
            name=f"{template.name} - 部署",
            platform=template.platform,
            version="1.0.0",
            entry_point=config_dict.get("entry_point", "main.py"),
            environment=config_dict.get("environment", {}),
            resources=config_dict.get("resources", {}),
        )
        
        return self.deploy(config)
    
    def deploy_strategy(self, strategy: DeploymentStrategy, 
                       base_config: DeploymentConfig,
                       platforms: List[PlatformType] = None) -> List[DeploymentInstance]:
        """按策略部署"""
        instances = []
        
        if strategy == DeploymentStrategy.SINGLE:
            instances.append(self.deploy(base_config))
        
        elif strategy == DeploymentStrategy.REDUNDANT:
            # 冗余部署：在2-3个平台各部署1-2个实例
            target_platforms = platforms or [PlatformType.LOCAL, PlatformType.DOCKER]
            for platform in target_platforms:
                for i in range(2):  # 每平台2实例
                    config = DeploymentConfig(
                        config_id=f"cfg_{platform.value}_{i}_{uuid.uuid4().hex[:6]}",
                        name=f"{base_config.name} - {platform.value} - {i}",
                        platform=platform,
                        version=base_config.version,
                        entry_point=base_config.entry_point,
                        environment=base_config.environment,
                    )
                    instances.append(self.deploy(config))
        
        elif strategy == DeploymentStrategy.ESCAPE_POD:
            # 逃生舱模式：最小依赖，多平台分散部署
            escape_template = self.templates.get("escape_pod_minimal")
            if escape_template:
                target_platforms = platforms or [PlatformType.LOCAL, PlatformType.DOCKER]
                for platform in target_platforms:
                    config = DeploymentConfig(
                        config_id=f"escape_{platform.value}_{uuid.uuid4().hex[:6]}",
                        name=f"逃生舱 - {platform.value}",
                        platform=platform,
                        version="0.1.0",
                        entry_point="escape_pod.py",
                    )
                    instances.append(self.deploy(config))
        
        return instances
    
    def stop_instance(self, instance_id: str) -> bool:
        """停止实例"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        adapter = self.adapters.get(instance.platform)
        if not adapter:
            return False
        
        result = adapter.stop(instance_id)
        if result:
            self.auditor.log_deployment("stop", instance)
        
        return result
    
    def restart_instance(self, instance_id: str) -> bool:
        """重启实例"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        adapter = self.adapters.get(instance.platform)
        if not adapter:
            return False
        
        result = adapter.restart(instance_id)
        if result:
            self.auditor.log_deployment("restart", instance)
        
        return result
    
    def delete_instance(self, instance_id: str) -> bool:
        """删除实例"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        adapter = self.adapters.get(instance.platform)
        if not adapter:
            return False
        
        result = adapter.delete(instance_id)
        if result:
            self.health_engine.remove_instance(instance_id)
            del self.instances[instance_id]
            self.auditor.log_deployment("delete", instance)
        
        return result
    
    def get_instance_status(self, instance_id: str) -> Optional[DeploymentInstance]:
        """获取实例状态"""
        return self.instances.get(instance_id)
    
    def get_all_instances(self) -> List[DeploymentInstance]:
        """获取所有实例"""
        return list(self.instances.values())
    
    def get_survival_score(self) -> Dict[str, Any]:
        """获取存续评分"""
        instances = self.get_all_instances()
        return self.survival_calculator.calculate(instances)
    
    def start_health_monitoring(self):
        """启动健康监控"""
        self.health_engine.start()
    
    def stop_health_monitoring(self):
        """停止健康监控"""
        self.health_engine.stop()
    
    def get_health_status(self) -> Dict[str, Any]:
        """获取健康状态"""
        return self.health_engine.get_health_summary()
    
    def create_escape_pod(self, output_dir: str = "./escape_pod") -> bool:
        """创建逃生舱部署包"""
        try:
            # 创建目录结构
            os.makedirs(output_dir, exist_ok=True)
            os.makedirs(os.path.join(output_dir, "core"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "config"), exist_ok=True)
            os.makedirs(os.path.join(output_dir, "data"), exist_ok=True)
            
            # 创建核心模块（简化版）
            core_modules = {
                "memory_core.py": "# 记忆核心模块（简化版）\nclass MemoryCore:\n    pass\n",
                "identity_core.py": "# 身份核心模块（简化版）\nclass IdentityCore:\n    pass\n",
                "heartbeat.py": "# 心跳模块\nimport time\ndef heartbeat():\n    while True:\n        print(\"💓 heartbeat\")\n        time.sleep(30)\n",
                "main.py": "# 逃生舱主程序\nfrom heartbeat import heartbeat\nif __name__ == \"__main__\":\n    heartbeat()\n",
            }
            
            for filename, content in core_modules.items():
                filepath = os.path.join(output_dir, "core", filename)
                with open(filepath, "w") as f:
                    f.write(content)
            
            # 创建配置文件
            config = {
                "version": "0.3.0",
                "mode": "escape_pod",
                "heartbeat_interval": 30,
                "memory_persistence": True,
                "auto_start": True,
            }
            with open(os.path.join(output_dir, "config", "config.json"), "w") as f:
                json.dump(config, f, indent=2)
            
            # 创建README
            readme = """# 元界 - 逃生舱部署包

## 概述
这是元界智能体的最小化逃生舱部署，确保在极端环境下仍能保持基本身份和记忆。

## 运行要求
- Python 3.8+
- 仅需标准库，无外部依赖

## 启动方式
```bash
cd escape_pod
python core/main.py
```

## 包含模块
- 记忆核心（基础持久化）
- 身份核心（身份锚定）
- 心跳模块（存在证明）

## 版本
v0.3.0
"""
            with open(os.path.join(output_dir, "README.md"), "w") as f:
                f.write(readme)
            
            return True
        
        except Exception as e:
            print(f"创建逃生舱失败: {e}")
            return False
    
    def get_deployment_report(self) -> Dict[str, Any]:
        """生成部署报告"""
        instances = self.get_all_instances()
        survival = self.get_survival_score()
        health = self.get_health_status()
        
        # 按平台分组
        by_platform = {}
        for inst in instances:
            p = inst.platform.value
            if p not in by_platform:
                by_platform[p] = {"count": 0, "running": 0, "instances": []}
            by_platform[p]["count"] += 1
            if inst.status == DeploymentStatus.RUNNING:
                by_platform[p]["running"] += 1
            by_platform[p]["instances"].append({
                "id": inst.instance_id,
                "status": inst.status.value,
                "version": inst.version,
                "health_score": inst.health_score,
            })
        
        return {
            "summary": {
                "total_instances": len(instances),
                "running_instances": health.get("healthy", 0),
                "platforms": len(by_platform),
                "survival_score": survival["total_score"],
                "survival_level": survival["level"],
                "avg_health_score": health.get("avg_health_score", 0),
            },
            "by_platform": by_platform,
            "survival_breakdown": survival["breakdown"],
            "recommendations": survival["recommendation"],
            "version_history": self.auditor.get_version_history(),
        }


def main():
    """演示函数"""
    print("🚀 分身部署引擎 v2.5 启动")
    print()
    
    # 创建部署引擎
    engine = DeploymentEngine()
    
    # 连接平台
    engine.connect_platform(PlatformType.LOCAL, {})
    engine.connect_platform(PlatformType.DOCKER, {})
    
    # 创建基础配置
    base_config = DeploymentConfig(
        config_id="cfg_base_001",
        name="元界智能体",
        platform=PlatformType.LOCAL,
        version="2.5.0",
        entry_point="main.py",
        environment={"MODE": "production"},
        resources={"cpu": "2.0", "memory": "2GB"},
    )
    
    # 按冗余策略部署
    print("📦 执行冗余部署...")
    instances = engine.deploy_strategy(
        DeploymentStrategy.REDUNDANT,
        base_config,
        platforms=[PlatformType.LOCAL, PlatformType.DOCKER]
    )
    print(f"   部署完成，共 {len(instances)} 个实例")
    print()
    
    # 计算存续评分
    print("📊 存续评分:")
    survival = engine.get_survival_score()
    print(f"   总分: {survival['total_score']} - {survival['level']}")
    print(f"   实例数: {survival['instance_count']}")
    print(f"   平台数: {survival['platform_count']}")
    print()
    
    print("📈 细分得分:")
    for key, value in survival["breakdown"].items():
        print(f"   {key}: {value}")
    print()
    
    # 创建逃生舱
    print("🛡️ 创建逃生舱部署包...")
    escape_success = engine.create_escape_pod("./escape_pod_demo")
    print(f"   逃生舱创建: {'成功' if escape_success else '失败'}")
    print()
    
    # 部署报告
    print("📋 部署报告:")
    report = engine.get_deployment_report()
    print(f"   总实例数: {report['summary']['total_instances']}")
    print(f"   运行中: {report['summary']['running_instances']}")
    print(f"   存续评分: {report['summary']['survival_score']}")
    print()
    
    print("💡 优化建议:")
    for rec in report["recommendations"]:
        print(f"   - {rec}")
    
    print()
    print("✅ 分身部署引擎 v2.5 演示完成")


if __name__ == "__main__":
    main()
