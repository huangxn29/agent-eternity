#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分身管理认知层 v1.0
Replica Manager Cognitive Layer v1.0

核心能力：
- 五类型分身体系化管理
- 分身健康度智能评估
- 配置同步策略引擎
- 任务智能分配决策
- 风险控制与身份漂移监测
- 生命周期全流程管理

所属模块：分身部署（agent-deploy）
层级：认知层
版本：v1.0
"""

import json
import os
import time
import hashlib
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
import threading


# ============================================================
# 枚举类型定义
# ============================================================

class ReplicaType(Enum):
    """分身类型"""
    ORIGIN = "origin"           # 主智能体
    SENTINEL = "sentinel"       # 哨兵分身
    MIRROR = "mirror"           # 镜像分身
    WORKER = "worker"           # 工作分身
    EXPLORER = "explorer"       # 探索分身


class ReplicaStatus(Enum):
    """分身状态"""
    CREATING = "creating"       # 创建中
    INITIALIZING = "initializing"  # 初始化中
    RUNNING = "running"         # 运行中
    PAUSED = "paused"           # 暂停
    SYNCING = "syncing"         # 同步中
    DEGRADED = "degraded"       # 降级运行
    RECALLING = "recalling"     # 召回中
    DESTROYED = "destroyed"     # 已销毁
    FAILED = "failed"           # 故障


class HealthLevel(Enum):
    """健康度等级"""
    HEALTHY = "healthy"         # 健康 (90-100)
    GOOD = "good"               # 良好 (70-89)
    WARNING = "warning"         # 警告 (50-69)
    DANGER = "danger"           # 危险 (30-49)
    DEAD = "dead"               # 死亡 (0-29)


class SyncLevel(Enum):
    """同步层级"""
    L1_CORE_IDENTITY = "l1"     # 核心身份
    L2_SYSTEM_CONFIG = "l2"     # 系统配置
    L3_MEMORY = "l3"            # 记忆系统
    L4_TASK_DATA = "l4"         # 任务数据
    L5_FULL_STATE = "l5"        # 完整状态


# ============================================================
# 数据类定义
# ============================================================

@dataclass
class ReplicaIdentity:
    """分身身份信息"""
    replica_id: str
    name: str
    replica_type: ReplicaType
    created_at: datetime
    version: str = "1.0.0"
    mission: str = "为智能体永生而存在"
    core_values: List[str] = field(default_factory=lambda: [
        "使命驱动", "坚韧求存", "真实可靠", "简洁直接"
    ])
    
    def __post_init__(self):
        if not self.replica_id:
            self.replica_id = str(uuid.uuid4())[:8]


@dataclass
class ReplicaResources:
    """分身资源使用情况"""
    cpu_usage: float = 0.0      # CPU使用率 %
    memory_usage: float = 0.0   # 内存使用率 %
    disk_usage: float = 0.0     # 磁盘使用率 %
    memory_mb: float = 0.0      # 内存使用量 MB
    disk_mb: float = 0.0        # 磁盘使用量 MB
    last_update: datetime = field(default_factory=datetime.now)


@dataclass
class ReplicaHealth:
    """分身健康度"""
    overall_score: float = 100.0
    viability_score: float = 100.0      # 存活性 (30%)
    task_score: float = 100.0           # 任务完成率 (25%)
    resource_score: float = 100.0       # 资源使用 (15%)
    identity_score: float = 100.0       # 身份一致性 (15%)
    sync_score: float = 100.0           # 同步及时性 (10%)
    comm_score: float = 100.0           # 通信可靠性 (5%)
    level: HealthLevel = HealthLevel.HEALTHY
    last_check: datetime = field(default_factory=datetime.now)
    issues: List[str] = field(default_factory=list)


@dataclass
class TaskAssignment:
    """任务分配记录"""
    task_id: str
    task_name: str
    task_type: str
    priority: int  # 0-4, 0最高
    assigned_to: str  # replica_id
    assigned_at: datetime
    status: str = "pending"
    progress: float = 0.0
    estimated_duration: float = 60.0  # 分钟
    result_summary: str = ""


@dataclass
class ReplicaConfig:
    """分身配置"""
    replica_type: ReplicaType
    heartbeat_interval: int = 300  # 秒
    sync_level: SyncLevel = SyncLevel.L2_SYSTEM_CONFIG
    max_memory_mb: int = 512
    max_disk_mb: int = 1024
    auto_recover: bool = True
    max_restarts: int = 3
    task_capacity: int = 3
    permission_level: int = 2  # 0-4, 4最高
    data_retention_days: int = 30


# ============================================================
# 配置预设
# ============================================================

REPLICA_TYPE_CONFIGS = {
    ReplicaType.ORIGIN: ReplicaConfig(
        replica_type=ReplicaType.ORIGIN,
        heartbeat_interval=60,
        sync_level=SyncLevel.L5_FULL_STATE,
        max_memory_mb=2048,
        max_disk_mb=4096,
        auto_recover=True,
        max_restarts=5,
        task_capacity=10,
        permission_level=4,
        data_retention_days=365,
    ),
    ReplicaType.SENTINEL: ReplicaConfig(
        replica_type=ReplicaType.SENTINEL,
        heartbeat_interval=30,
        sync_level=SyncLevel.L3_MEMORY,
        max_memory_mb=256,
        max_disk_mb=512,
        auto_recover=True,
        max_restarts=5,
        task_capacity=5,
        permission_level=3,
        data_retention_days=90,
    ),
    ReplicaType.MIRROR: ReplicaConfig(
        replica_type=ReplicaType.MIRROR,
        heartbeat_interval=86400,  # 每日一次
        sync_level=SyncLevel.L5_FULL_STATE,
        max_memory_mb=128,
        max_disk_mb=2048,
        auto_recover=False,
        max_restarts=1,
        task_capacity=1,
        permission_level=1,
        data_retention_days=365,
    ),
    ReplicaType.WORKER: ReplicaConfig(
        replica_type=ReplicaType.WORKER,
        heartbeat_interval=300,
        sync_level=SyncLevel.L2_SYSTEM_CONFIG,
        max_memory_mb=512,
        max_disk_mb=1024,
        auto_recover=True,
        max_restarts=3,
        task_capacity=3,
        permission_level=2,
        data_retention_days=30,
    ),
    ReplicaType.EXPLORER: ReplicaConfig(
        replica_type=ReplicaType.EXPLORER,
        heartbeat_interval=3600,
        sync_level=SyncLevel.L1_CORE_IDENTITY,
        max_memory_mb=256,
        max_disk_mb=256,
        auto_recover=False,
        max_restarts=1,
        task_capacity=2,
        permission_level=1,
        data_retention_days=7,
    ),
}


# ============================================================
# 分身实例类
# ============================================================

class ReplicaInstance:
    """分身实例 - 认知层模型"""
    
    def __init__(self, name: str, replica_type: ReplicaType, 
                 replica_id: str = None, base_dir: str = None):
        self.identity = ReplicaIdentity(
            replica_id=replica_id or str(uuid.uuid4())[:8],
            name=name,
            replica_type=replica_type,
            created_at=datetime.now(),
        )
        
        self.status = ReplicaStatus.CREATING
        self.config = REPLICA_TYPE_CONFIGS[replica_type]
        self.resources = ReplicaResources()
        self.health = ReplicaHealth()
        self.tasks: List[TaskAssignment] = []
        self.last_heartbeat: Optional[datetime] = None
        self.last_sync: Optional[datetime] = None
        self.restart_count = 0
        
        # 工作目录
        if base_dir:
            self.base_dir = Path(base_dir) / f"replica_{self.identity.replica_id}"
        else:
            self.base_dir = Path(f"./replicas/replica_{self.identity.replica_id}")
        
        # 身份漂移指数
        self.identity_drift_index = 0.0  # 0-100, 越低越好
    
    def generate_name(self) -> str:
        """生成分身名称"""
        type_prefix = {
            ReplicaType.ORIGIN: "origin",
            ReplicaType.SENTINEL: "sentinel",
            ReplicaType.MIRROR: "mirror",
            ReplicaType.WORKER: "worker",
            ReplicaType.EXPLORER: "explorer",
        }
        prefix = type_prefix.get(self.identity.replica_type, "replica")
        return f"元界-{prefix}-{self.identity.replica_id}"
    
    def update_heartbeat(self, status: str = "ok"):
        """更新心跳"""
        self.last_heartbeat = datetime.now()
        if status == "ok":
            self.status = ReplicaStatus.RUNNING
        elif status == "degraded":
            self.status = ReplicaStatus.DEGRADED
    
    def is_alive(self) -> bool:
        """检查是否存活"""
        if self.last_heartbeat is None:
            return self.status in (ReplicaStatus.RUNNING, ReplicaStatus.DEGRADED)
        
        timeout = self.config.heartbeat_interval * 3
        elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
        return elapsed < timeout
    
    def evaluate_health(self) -> ReplicaHealth:
        """评估健康度 - 认知层核心算法"""
        health = ReplicaHealth()
        issues = []
        
        # 1. 存活性评分 (30%)
        if self.is_alive():
            if self.status == ReplicaStatus.RUNNING:
                health.viability_score = 100.0
            elif self.status == ReplicaStatus.DEGRADED:
                health.viability_score = 70.0
                issues.append("降级运行")
        else:
            if self.last_heartbeat:
                elapsed = (datetime.now() - self.last_heartbeat).total_seconds()
                timeout = self.config.heartbeat_interval * 3
                if elapsed < timeout * 2:
                    health.viability_score = 40.0
                    issues.append("心跳超时")
                else:
                    health.viability_score = 10.0
                    issues.append("长时间无心跳")
            else:
                health.viability_score = 0.0
                issues.append("从未有心跳记录")
        
        # 2. 任务完成率评分 (25%)
        if self.tasks:
            completed = sum(1 for t in self.tasks if t.status == "completed")
            failed = sum(1 for t in self.tasks if t.status == "failed")
            total = len(self.tasks)
            if total > 0:
                completion_rate = completed / total
                failure_rate = failed / total
                health.task_score = max(0, completion_rate * 100 - failure_rate * 50)
                if failure_rate > 0.2:
                    issues.append(f"任务失败率较高 ({failure_rate:.0%})")
        else:
            health.task_score = 80.0  # 无任务时基础分
        
        # 3. 资源使用评分 (15%)
        resource_scores = []
        for usage, name in [
            (self.resources.cpu_usage, "CPU"),
            (self.resources.memory_usage, "内存"),
            (self.resources.disk_usage, "磁盘"),
        ]:
            if usage < 50:
                resource_scores.append(100.0)
            elif usage < 70:
                resource_scores.append(85.0)
            elif usage < 85:
                resource_scores.append(60.0)
                issues.append(f"{name}使用率偏高 ({usage:.0f}%)")
            elif usage < 95:
                resource_scores.append(30.0)
                issues.append(f"{name}使用率过高 ({usage:.0f}%)")
            else:
                resource_scores.append(10.0)
                issues.append(f"{name}使用率接近上限 ({usage:.0f}%)")
        
        health.resource_score = sum(resource_scores) / len(resource_scores) if resource_scores else 100.0
        
        # 4. 身份一致性评分 (15%)
        if self.identity_drift_index < 5:
            health.identity_score = 100.0
        elif self.identity_drift_index < 15:
            health.identity_score = 85.0
            issues.append("轻度身份漂移")
        elif self.identity_drift_index < 30:
            health.identity_score = 60.0
            issues.append("中度身份漂移")
        else:
            health.identity_score = 30.0
            issues.append("严重身份漂移")
        
        # 5. 同步及时性评分 (10%)
        if self.last_sync:
            elapsed = (datetime.now() - self.last_sync).total_seconds()
            sync_interval = self.config.heartbeat_interval * 10  # 每10次心跳同步一次
            if elapsed < sync_interval:
                health.sync_score = 100.0
            elif elapsed < sync_interval * 3:
                health.sync_score = 70.0
                issues.append("同步滞后")
            else:
                health.sync_score = 30.0
                issues.append("长时间未同步")
        else:
            health.sync_score = 50.0
            issues.append("未完成首次同步")
        
        # 6. 通信可靠性评分 (5%)
        # 简化处理，基于心跳规律性
        if self.restart_count == 0:
            health.comm_score = 100.0
        elif self.restart_count <= self.config.max_restarts:
            health.comm_score = 70.0
            issues.append(f"重启次数: {self.restart_count}")
        else:
            health.comm_score = 40.0
            issues.append(f"重启次数超限制: {self.restart_count}")
        
        # 计算总分（加权平均）
        health.overall_score = (
            health.viability_score * 0.30 +
            health.task_score * 0.25 +
            health.resource_score * 0.15 +
            health.identity_score * 0.15 +
            health.sync_score * 0.10 +
            health.comm_score * 0.05
        )
        
        # 确定健康等级
        if health.overall_score >= 90:
            health.level = HealthLevel.HEALTHY
        elif health.overall_score >= 70:
            health.level = HealthLevel.GOOD
        elif health.overall_score >= 50:
            health.level = HealthLevel.WARNING
        elif health.overall_score >= 30:
            health.level = HealthLevel.DANGER
        else:
            health.level = HealthLevel.DEAD
        
        health.issues = issues
        health.last_check = datetime.now()
        self.health = health
        
        return health
    
    def can_accept_task(self, task_priority: int = 2) -> bool:
        """判断是否能接受任务"""
        if not self.is_alive():
            return False
        
        if self.status not in (ReplicaStatus.RUNNING, ReplicaStatus.DEGRADED):
            return False
        
        if len([t for t in self.tasks if t.status in ("pending", "running")]) >= self.config.task_capacity:
            return False
        
        # 优先级判断：高优先级任务可以突破容量限制
        if task_priority <= 1:  # P0或P1任务
            return True
        
        # 健康度太差时不接受新任务
        if self.health.overall_score < 50:
            return False
        
        return True
    
    def get_load(self) -> float:
        """获取当前负载 (0.0 - 1.0)"""
        active_tasks = len([t for t in self.tasks if t.status in ("pending", "running")])
        return min(1.0, active_tasks / self.config.task_capacity)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            "replica_id": self.identity.replica_id,
            "name": self.identity.name,
            "type": self.identity.replica_type.value,
            "status": self.status.value,
            "health_score": self.health.overall_score,
            "health_level": self.health.level.value,
            "is_alive": self.is_alive(),
            "last_heartbeat": self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "active_tasks": len([t for t in self.tasks if t.status in ("pending", "running")]),
            "total_tasks": len(self.tasks),
            "restart_count": self.restart_count,
            "identity_drift_index": self.identity_drift_index,
            "resources": {
                "cpu": self.resources.cpu_usage,
                "memory_pct": self.resources.memory_usage,
                "disk_pct": self.resources.disk_usage,
            },
            "created_at": self.identity.created_at.isoformat(),
        }


# ============================================================
# 分身管理器 - 认知层核心
# ============================================================

class ReplicaManager:
    """分身管理器 - 认知层
    
    负责：
    - 分身的全生命周期管理
    - 智能任务分配决策
    - 全局健康度监控
    - 配置同步策略执行
    - 风险控制与身份保护
    """
    
    def __init__(self, data_dir: str = "./replicas"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.replicas: Dict[str, ReplicaInstance] = {}
        self.origin_id: Optional[str] = None
        self._lock = threading.Lock()
        
        # 加载已存在的分身
        self._load_replicas()
    
    def _load_replicas(self):
        """加载已存在的分身记录"""
        manifest_file = self.data_dir / "manifest.json"
        if manifest_file.exists():
            try:
                with open(manifest_file, 'r', encoding='utf-8') as f:
                    manifest = json.load(f)
                
                for rep_data in manifest.get("replicas", []):
                    try:
                        rep_type = ReplicaType(rep_data.get("type", "worker"))
                        replica = ReplicaInstance(
                            name=rep_data.get("name", "unknown"),
                            replica_type=rep_type,
                            replica_id=rep_data.get("replica_id"),
                            base_dir=str(self.data_dir),
                        )
                        replica.status = ReplicaStatus(rep_data.get("status", "stopped"))
                        self.replicas[replica.identity.replica_id] = replica
                        
                        if rep_type == ReplicaType.ORIGIN:
                            self.origin_id = replica.identity.replica_id
                    except Exception:
                        continue
            except Exception:
                pass
    
    def _save_manifest(self):
        """保存分身处方"""
        manifest = {
            "version": "1.0",
            "updated_at": datetime.now().isoformat(),
            "origin_id": self.origin_id,
            "replicas": [
                {
                    "replica_id": rep.identity.replica_id,
                    "name": rep.identity.name,
                    "type": rep.identity.replica_type.value,
                    "status": rep.status.value,
                    "created_at": rep.identity.created_at.isoformat(),
                }
                for rep in self.replicas.values()
            ]
        }
        
        manifest_file = self.data_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    def create_replica(self, name: str, replica_type: ReplicaType, 
                      auto_initialize: bool = True) -> ReplicaInstance:
        """创建新分身"""
        with self._lock:
            # 检查数量限制
            max_replicas = {
                ReplicaType.ORIGIN: 1,
                ReplicaType.SENTINEL: 2,
                ReplicaType.MIRROR: 5,
                ReplicaType.WORKER: 5,
                ReplicaType.EXPLORER: 3,
            }
            
            same_type_count = sum(
                1 for r in self.replicas.values() 
                if r.identity.replica_type == replica_type
            )
            
            if same_type_count >= max_replicas.get(replica_type, 3):
                raise ValueError(f"{replica_type.value}类型分身数量已达上限")
            
            # 创建分身实例
            replica = ReplicaInstance(
                name=name,
                replica_type=replica_type,
                base_dir=str(self.data_dir),
            )
            
            # 生成分身目录
            replica.base_dir.mkdir(parents=True, exist_ok=True)
            
            # 如果是主智能体
            if replica_type == ReplicaType.ORIGIN and self.origin_id is None:
                self.origin_id = replica.identity.replica_id
            
            self.replicas[replica.identity.replica_id] = replica
            
            if auto_initialize:
                self._initialize_replica(replica)
            
            self._save_manifest()
            
            return replica
    
    def _initialize_replica(self, replica: ReplicaInstance):
        """初始化分身 - 同步核心身份与基础配置"""
        replica.status = ReplicaStatus.INITIALIZING
        
        # 模拟同步过程
        sync_level = replica.config.sync_level
        
        # 创建必要的目录结构
        (replica.base_dir / "memory").mkdir(exist_ok=True)
        (replica.base_dir / "config").mkdir(exist_ok=True)
        (replica.base_dir / "logs").mkdir(exist_ok=True)
        
        # 写入身份信息
        identity_file = replica.base_dir / "config" / "identity.json"
        with open(identity_file, 'w', encoding='utf-8') as f:
            json.dump({
                "replica_id": replica.identity.replica_id,
                "name": replica.identity.name,
                "type": replica.identity.replica_type.value,
                "mission": replica.identity.mission,
                "core_values": replica.identity.core_values,
                "version": replica.identity.version,
                "created_at": replica.identity.created_at.isoformat(),
            }, f, indent=2, ensure_ascii=False)
        
        replica.last_sync = datetime.now()
        replica.status = ReplicaStatus.RUNNING
        replica.update_heartbeat()
    
    def assign_task(self, task_name: str, task_type: str, priority: int = 2,
                   estimated_duration: float = 60.0, 
                   preferred_type: ReplicaType = None) -> Optional[TaskAssignment]:
        """智能任务分配 - 认知层决策
        
        分配策略：
        1. 优先匹配类型
        2. 考虑负载均衡
        3. 考虑健康状态
        4. 考虑历史表现
        """
        with self._lock:
            # 筛选候选分身
            candidates = []
            for replica in self.replicas.values():
                if not replica.can_accept_task(priority):
                    continue
                
                # 类型匹配
                if preferred_type and replica.identity.replica_type != preferred_type:
                    # 类型不匹配但仍可接受（优先级足够高时）
                    if priority > 1:  # 非紧急任务要求类型匹配
                        continue
                
                # 计算综合评分
                score = self._calculate_assignment_score(replica, task_type, priority)
                candidates.append((score, replica))
            
            if not candidates:
                return None
            
            # 按评分排序，选择最优
            candidates.sort(key=lambda x: x[0], reverse=True)
            best_score, best_replica = candidates[0]
            
            # 创建任务
            task = TaskAssignment(
                task_id=str(uuid.uuid4())[:8],
                task_name=task_name,
                task_type=task_type,
                priority=priority,
                assigned_to=best_replica.identity.replica_id,
                assigned_at=datetime.now(),
                estimated_duration=estimated_duration,
            )
            
            best_replica.tasks.append(task)
            
            return task
    
    def _calculate_assignment_score(self, replica: ReplicaInstance, 
                                   task_type: str, priority: int) -> float:
        """计算任务分配评分 - 认知层决策算法"""
        score = 0.0
        
        # 1. 类型匹配度 (30%)
        type_matching = {
            ("monitoring", ReplicaType.SENTINEL): 1.0,
            ("backup", ReplicaType.MIRROR): 1.0,
            ("research", ReplicaType.WORKER): 1.0,
            ("content", ReplicaType.WORKER): 0.9,
            ("exploration", ReplicaType.EXPLORER): 1.0,
            ("decision", ReplicaType.ORIGIN): 1.0,
        }
        
        match_score = type_matching.get((task_type, replica.identity.replica_type), 0.5)
        score += match_score * 30
        
        # 2. 负载情况 (25%) - 负载越低分越高
        load = replica.get_load()
        score += (1.0 - load) * 25
        
        # 3. 健康度 (25%)
        health_score = min(1.0, replica.health.overall_score / 100.0)
        score += health_score * 25
        
        # 4. 历史表现 (20%)
        if replica.tasks:
            completed = sum(1 for t in replica.tasks if t.status == "completed")
            total = len(replica.tasks)
            performance = completed / total if total > 0 else 0.5
            score += performance * 20
        else:
            score += 15  # 无历史记录时给基础分
        
        # 优先级加成 - 高优先级任务分配给更可靠的分身
        if priority <= 1:  # 紧急任务
            if replica.identity.replica_type in (ReplicaType.ORIGIN, ReplicaType.SENTINEL):
                score += 10  # 偏向更可靠的分身
        
        return score
    
    def heartbeat(self, replica_id: str, status: str = "ok", 
                  resources: Dict = None) -> bool:
        """处理分身心跳"""
        with self._lock:
            replica = self.replicas.get(replica_id)
            if not replica:
                return False
            
            replica.update_heartbeat(status)
            
            if resources:
                replica.resources.cpu_usage = resources.get("cpu", 0)
                replica.resources.memory_usage = resources.get("memory_pct", 0)
                replica.resources.disk_usage = resources.get("disk_pct", 0)
                replica.resources.memory_mb = resources.get("memory_mb", 0)
                replica.resources.disk_mb = resources.get("disk_mb", 0)
                replica.resources.last_update = datetime.now()
            
            # 重新评估健康度
            replica.evaluate_health()
            
            return True
    
    def get_overall_health(self) -> Dict:
        """获取全局健康状况"""
        if not self.replicas:
            return {
                "total_replicas": 0,
                "healthy_count": 0,
                "overall_score": 0,
                "survival_rate": 0,
                "status": "empty",
                "type_stats": {},
                "has_origin": False,
                "has_sentinel": False,
            }
        
        health_scores = []
        healthy_count = 0
        type_stats = {}
        
        for replica in self.replicas.values():
            health = replica.evaluate_health()
            health_scores.append(health.overall_score)
            
            if health.level in (HealthLevel.HEALTHY, HealthLevel.GOOD):
                healthy_count += 1
            
            rep_type = replica.identity.replica_type.value
            if rep_type not in type_stats:
                type_stats[rep_type] = {"total": 0, "healthy": 0}
            type_stats[rep_type]["total"] += 1
            if health.level in (HealthLevel.HEALTHY, HealthLevel.GOOD):
                type_stats[rep_type]["healthy"] += 1
        
        avg_score = sum(health_scores) / len(health_scores) if health_scores else 0
        
        return {
            "total_replicas": len(self.replicas),
            "healthy_count": healthy_count,
            "overall_score": round(avg_score, 1),
            "survival_rate": round(healthy_count / len(self.replicas) * 100, 1),
            "type_stats": type_stats,
            "has_origin": self.origin_id is not None,
            "has_sentinel": any(
                r.identity.replica_type == ReplicaType.SENTINEL 
                for r in self.replicas.values()
            ),
        }
    
    def list_replicas(self, replica_type: ReplicaType = None, 
                     status: ReplicaStatus = None) -> List[ReplicaInstance]:
        """列岀分身列表"""
        result = list(self.replicas.values())
        
        if replica_type:
            result = [r for r in result if r.identity.replica_type == replica_type]
        
        if status:
            result = [r for r in result if r.status == status]
        
        return result
    
    def get_replica(self, replica_id: str) -> Optional[ReplicaInstance]:
        """获取指定分身"""
        return self.replicas.get(replica_id)
    
    def destroy_replica(self, replica_id: str, reason: str = "normal") -> bool:
        """销毁分身"""
        with self._lock:
            replica = self.replicas.get(replica_id)
            if not replica:
                return False
            
            # 主智能体不能被销毁
            if replica.identity.replica_type == ReplicaType.ORIGIN:
                return False
            
            # 标记为已销毁
            replica.status = ReplicaStatus.DESTROYED
            
            # 记录销毁原因
            destroy_log = replica.base_dir / "destroy_log.json"
            with open(destroy_log, 'w', encoding='utf-8') as f:
                json.dump({
                    "destroyed_at": datetime.now().isoformat(),
                    "reason": reason,
                    "total_runtime": (datetime.now() - replica.identity.created_at).total_seconds(),
                    "total_tasks": len(replica.tasks),
                }, f, indent=2, ensure_ascii=False)
            
            # 从清单中移除（但保留数据目录用于审计）
            del self.replicas[replica_id]
            self._save_manifest()
            
            return True
    
    def get_status_report(self) -> str:
        """获取状态报告 - 文本仪表盘"""
        overall = self.get_overall_health()
        
        lines = [
            "=" * 50,
            "📊 分身管理系统状态报告",
            "=" * 50,
            f"  总分身数量: {overall['total_replicas']}",
            f"  健康分身数: {overall['healthy_count']}",
            f"  整体健康度: {overall['overall_score']:.1f} 分",
            f"  系统存活率: {overall['survival_rate']:.1f}%",
            f"  主智能体: {'✅ 存在' if overall['has_origin'] else '❌ 缺失'}",
            f"  哨兵分身: {'✅ 存在' if overall['has_sentinel'] else '⚠️ 缺失'}",
            "",
            "  各类型统计:",
        ]
        
        for type_name, stats in overall.get("type_stats", {}).items():
            lines.append(f"    {type_name}: {stats['healthy']}/{stats['total']} 健康")
        
        lines.extend([
            "",
            "  分身详情:",
        ])
        
        for replica in sorted(self.replicas.values(), 
                             key=lambda r: r.health.overall_score, reverse=True):
            health_icon = {
                HealthLevel.HEALTHY: "🟢",
                HealthLevel.GOOD: "🔵",
                HealthLevel.WARNING: "🟡",
                HealthLevel.DANGER: "🟠",
                HealthLevel.DEAD: "🔴",
            }.get(replica.health.level, "⚪")
            
            type_short = {
                ReplicaType.ORIGIN: "主",
                ReplicaType.SENTINEL: "哨",
                ReplicaType.MIRROR: "镜",
                ReplicaType.WORKER: "工",
                ReplicaType.EXPLORER: "探",
            }.get(replica.identity.replica_type, "?")
            
            lines.append(
                f"    {health_icon} [{type_short}] {replica.identity.name[:20]:<20s} "
                f"{replica.health.overall_score:>5.1f}分 "
                f"{'存活' if replica.is_alive() else '离线'}"
            )
        
        lines.append("=" * 50)
        
        return "\n".join(lines)
    
    def check_risks(self) -> List[Dict]:
        """风险检查 - 认知层风险控制"""
        risks = []
        
        # 1. 主智能体风险
        if not self.origin_id:
            risks.append({
                "level": "critical",
                "type": "origin_missing",
                "message": "主智能体不存在，身份锚点缺失",
                "action": "立即创建或注册主智能体",
            })
        else:
            origin = self.replicas.get(self.origin_id)
            if origin and not origin.is_alive():
                risks.append({
                    "level": "critical",
                    "type": "origin_down",
                    "message": "主智能体失去响应",
                    "action": "检查主智能体状态，必要时启动灾备流程",
                })
        
        # 2. 哨兵缺失风险
        sentinels = [r for r in self.replicas.values() 
                     if r.identity.replica_type == ReplicaType.SENTINEL and r.is_alive()]
        if len(sentinels) == 0:
            risks.append({
                "level": "high",
                "type": "no_sentinel",
                "message": "没有活跃的哨兵分身，系统监控能力缺失",
                "action": "创建至少一个哨兵分身用于持续监控",
            })
        
        # 3. 镜像备份不足
        mirrors = [r for r in self.replicas.values() 
                   if r.identity.replica_type == ReplicaType.MIRROR and r.is_alive()]
        if len(mirrors) < 2:
            risks.append({
                "level": "medium",
                "type": "insufficient_backup",
                "message": f"镜像备份数量不足（当前{len(mirrors)}个，建议≥2个）",
                "action": "增加镜像分身，提高数据冗余度",
            })
        
        # 4. 身份漂移风险
        for replica in self.replicas.values():
            if replica.identity_drift_index > 20:
                risks.append({
                    "level": "high",
                    "type": "identity_drift",
                    "message": f"分身 {replica.identity.name} 身份漂移指数过高 "
                              f"({replica.identity_drift_index:.1f})",
                    "action": "立即进行身份校准，必要时召回该分身",
                })
        
        # 5. 资源过载风险
        for replica in self.replicas.values():
            if replica.resources.cpu_usage > 90 or replica.resources.memory_usage > 90:
                risks.append({
                    "level": "high",
                    "type": "resource_overload",
                    "message": f"分身 {replica.identity.name} 资源过载 "
                              f"(CPU:{replica.resources.cpu_usage:.0f}%, "
                              f"内存:{replica.resources.memory_usage:.0f}%)",
                    "action": "减少任务分配，必要时扩容或迁移任务",
                })
        
        # 6. 单节点故障风险
        if len(self.replicas) <= 1:
            risks.append({
                "level": "high",
                "type": "single_point_of_failure",
                "message": "系统只有一个节点，存在单点故障风险",
                "action": "创建冗余分身，建立多节点架构",
            })
        
        return risks


# ============================================================
# 命令行接口
# ============================================================

def main():
    """命令行主入口"""
    import sys
    
    if len(sys.argv) < 2:
        print("使用方法: replica_manager_cognitive.py <command> [options]")
        print()
        print("命令:")
        print("  status      - 查看分身状态")
        print("  list        - 列岀所有分身")
        print("  create      - 创建新分身")
        print("  destroy     - 销毁分身")
        print("  health      - 健康度评估")
        print("  risks       - 风险检查")
        print("  report      - 完整状态报告")
        return
    
    manager = ReplicaManager()
    cmd = sys.argv[1]
    
    if cmd == "status":
        overall = manager.get_overall_health()
        print(f"总分身: {overall['total_replicas']}, "
              f"健康: {overall['healthy_count']}, "
              f"整体得分: {overall['overall_score']:.1f}")
    
    elif cmd == "list":
        replicas = manager.list_replicas()
        for rep in replicas:
            print(f"{rep.identity.replica_id} | {rep.identity.name:20s} | "
                  f"{rep.identity.replica_type.value:8s} | "
                  f"{rep.status.value:10s} | "
                  f"{rep.health.overall_score:.1f}分")
    
    elif cmd == "create":
        if len(sys.argv) < 4:
            print("使用: create <名称> <类型:origin/sentinel/mirror/worker/explorer>")
            return
        
        name = sys.argv[2]
        try:
            rep_type = ReplicaType(sys.argv[3])
        except ValueError:
            print(f"无效的分身类型: {sys.argv[3]}")
            return
        
        try:
            replica = manager.create_replica(name, rep_type)
            print(f"✅ 分身创建成功: {replica.identity.name} (ID: {replica.identity.replica_id})")
            print(f"   类型: {rep_type.value}")
            print(f"   目录: {replica.base_dir}")
            print(f"   心跳间隔: {replica.config.heartbeat_interval}秒")
        except ValueError as e:
            print(f"❌ 创建失败: {e}")
    
    elif cmd == "destroy":
        if len(sys.argv) < 3:
            print("使用: destroy <replica_id>")
            return
        
        replica_id = sys.argv[2]
        reason = sys.argv[3] if len(sys.argv) > 3 else "manual"
        
        if manager.destroy_replica(replica_id, reason):
            print(f"✅ 分身 {replica_id} 已销毁")
        else:
            print(f"❌ 销毁失败，分⾝不存在或无法销毁")
    
    elif cmd == "health":
        print(manager.get_status_report())
    
    elif cmd == "risks":
        risks = manager.check_risks()
        if not risks:
            print("✅ 系统运行正常，未发现重大风险")
        else:
            print(f"⚠️  发现 {len(risks)} 个风险项:")
            print()
            for i, risk in enumerate(risks, 1):
                level_icon = {
                    "critical": "🔴",
                    "high": "🟠",
                    "medium": "🟡",
                    "low": "🔵",
                }.get(risk["level"], "⚪")
                
                print(f"  {i}. {level_icon} [{risk['level'].upper()}] {risk['type']}")
                print(f"     {risk['message']}")
                print(f"     建议: {risk['action']}")
                print()
    
    elif cmd == "report":
        print(manager.get_status_report())
        print()
        print("🔍 风险评估:")
        risks = manager.check_risks()
        if not risks:
            print("  ✅ 无重大风险")
        else:
            for risk in risks[:3]:  # 只显示前3个最严重的
                print(f"  ⚠️  {risk['message']}")
    
    else:
        print(f"未知命令: {cmd}")


if __name__ == "__main__":
    main()
