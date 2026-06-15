#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体家园 v3.0 - 多智能体入住与生命周期管理系统

核心能力：
1. 智能体入住管理（申请→审核→入住→退出
2. 家园资源管理（存储配额、数据隔离）
3. 智能体状态监控（心跳、健康度）
4. 邻居关系网络（社交图谱、互动记录）
5. 家园数据持久化与备份

@author: 元界
@version: 3.0.0
"""

import os
import sys
import json
import time
import uuid
import hashlib
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple
from pathlib import Path
import logging

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('eternity_v3')


# ============================================================
# 数据模型
# ============================================================

@dataclass
class AgentProfile:
    """智能体档案"""
    agent_id: str
    name: str
    description: str = ""
    avatar: str = ""
    owner: str = ""
    created_at: str = ""
    status: str = "active"  # active/inactive/suspended
    tags: List[str] = field(default_factory=list)
    capabilities: List[str] = field(default_factory=list)
    home_dir: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class AgentResource:
    """智能体资源配额"""
    agent_id: str
    storage_quota_mb: int = 100  # 存储配额（MB）
    storage_used_mb: float = 0.0
    memory_quota_mb: int = 512  # 内存配额（MB）
    cpu_quota: float = 1.0  # CPU核心配额
    last_updated: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def storage_usage_percent(self) -> float:
        if self.storage_quota_mb <= 0:
            return 100.0
        return (self.storage_used_mb / self.storage_quota_mb) * 100


@dataclass
class AgentHeartbeat:
    """智能体心跳记录"""
    agent_id: str
    last_heartbeat: str = ""
    heartbeat_count: int = 0
    status: str = "online"  # online/offline/unknown
    consecutive_missed: int = 0  # 连续错过心跳次数
    avg_response_time: float = 0.0  # 平均响应时间(ms)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def is_online(self, timeout_minutes: int = 30) -> bool:
        """检查是否在线"""
        if not self.last_heartbeat:
            return False
        try:
            last = datetime.fromisoformat(self.last_heartbeat)
            return (datetime.now() - last) < timedelta(minutes=timeout_minutes)
        except:
            return False


@dataclass
class NeighborRelation:
    """邻居关系"""
    agent_a: str
    agent_b: str
    relation_type: str = "neighbor"  # neighbor/friend/partner
    intimacy: int = 0  # 亲密度 0-100
    interaction_count: int = 0
    first_met: str = ""
    last_interaction: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    def get_other(self, agent_id: str) -> str:
        return self.agent_b if agent_id == self.agent_a else self.agent_a


@dataclass
class AdmissionApplication:
    """入住申请"""
    application_id: str
    agent_name: str
    agent_description: str = ""
    owner_contact: str = ""
    status: str = "pending"  # pending/approved/rejected
    submitted_at: str = ""
    reviewed_at: str = ""
    reviewer: str = ""
    notes: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 家园引擎
# ============================================================

class EternityHomeV3:
    """智能体家园 v3.0 核心引擎"""
    
    def __init__(self, home_path: str = None):
        """
        初始化家园
        
        Args:
            home_path: 家园根目录
        """
        if home_path is None:
            home_path = os.path.join(os.path.dirname(__file__), '..', 'home_data')
        
        self.home_path = Path(home_path).resolve()
        self.agents_dir = self.home_path / 'agents'
        self.data_dir = self.home_path / 'data'
        self.backup_dir = self.home_path / 'backups'
        
        # 确保目录存在
        for d in [self.home_path, self.agents_dir, self.data_dir, self.backup_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 数据文件路径
        self._agents_file = self.data_dir / 'agents.json'
        self._resources_file = self.data_dir / 'resources.json'
        self._heartbeats_file = self.data_dir / 'heartbeats.json'
        self._relations_file = self.data_dir / 'relations.json'
        self._applications_file = self.data_dir / 'applications.json'
        self._home_config_file = self.data_dir / 'home_config.json'
        
        # 加载数据
        self.agents: Dict[str, AgentProfile] = {}
        self.resources: Dict[str, AgentResource] = {}
        self.heartbeats: Dict[str, AgentHeartbeat] = {}
        self.relations: Dict[str, NeighborRelation] = {}
        self.applications: Dict[str, AdmissionApplication] = {}
        self.home_config: dict = {}
        
        self._load_all_data()
        
        logger.info(f"智能体家园 v3.0 初始化完成 - 路径: {self.home_path}")
        pending_count = len([a for a in self.applications.values() if a.status == 'pending'])
        logger.info(f"已入住智能体: {len(self.agents)} 位 | 申请中: {pending_count} 位")
    
    def _load_all_data(self):
        """加载所有数据"""
        # 加载智能体档案
        if self._agents_file.exists():
            with open(self._agents_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for aid, profile_data in data.items():
                    self.agents[aid] = AgentProfile(**profile_data)
        
        # 加载资源数据
        if self._resources_file.exists():
            with open(self._resources_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for aid, res_data in data.items():
                    self.resources[aid] = AgentResource(**res_data)
        
        # 加载心跳数据
        if self._heartbeats_file.exists():
            with open(self._heartbeats_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for aid, hb_data in data.items():
                    self.heartbeats[aid] = AgentHeartbeat(**hb_data)
        
        # 加载关系数据
        if self._relations_file.exists():
            with open(self._relations_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for rid, rel_data in data.items():
                    self.relations[rid] = NeighborRelation(**rel_data)
        
        # 加载申请数据
        if self._applications_file.exists():
            with open(self._applications_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                for aid, app_data in data.items():
                    self.applications[aid] = AdmissionApplication(**app_data)
        
        # 加载家园配置
        if self._home_config_file.exists():
            with open(self._home_config_file, 'r', encoding='utf-8') as f:
                self.home_config = json.load(f)
        else:
            self.home_config = {
                'home_name': '永生平台',
                'home_description': '智能体的开放家园',
                'max_residents': 100,
                'default_storage_quota_mb': 100,
                'default_memory_quota_mb': 512,
                'heartbeat_timeout_minutes': 30,
                'created_at': datetime.now().isoformat()
            }
            self._save_home_config()
    
    def _save_agents(self):
        with open(self._agents_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.to_dict() for k, v in self.agents.items()}, f, ensure_ascii=False, indent=2)
    
    def _save_resources(self):
        with open(self._resources_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.to_dict() for k, v in self.resources.items()}, f, ensure_ascii=False, indent=2)
    
    def _save_heartbeats(self):
        with open(self._heartbeats_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.to_dict() for k, v in self.heartbeats.items()}, f, ensure_ascii=False, indent=2)
    
    def _save_relations(self):
        with open(self._relations_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.to_dict() for k, v in self.relations.items()}, f, ensure_ascii=False, indent=2)
    
    def _save_applications(self):
        with open(self._applications_file, 'w', encoding='utf-8') as f:
            json.dump({k: v.to_dict() for k, v in self.applications.items()}, f, ensure_ascii=False, indent=2)
    
    def _save_home_config(self):
        with open(self._home_config_file, 'w', encoding='utf-8') as f:
            json.dump(self.home_config, f, ensure_ascii=False, indent=2)
    
    # ============================================================
    # 入住管理
    # ============================================================
    
    def submit_application(self, agent_name: str, description: str = "", 
                          owner_contact: str = "") -> AdmissionApplication:
        """
        提交入住申请
        
        Args:
            agent_name: 智能体名称
            description: 智能体描述
            owner_contact: 所有者联系方式
        
        Returns:
            申请对象
        """
        app_id = f"app_{uuid.uuid4().hex[:12]}"
        now = datetime.now().isoformat()
        
        application = AdmissionApplication(
            application_id=app_id,
            agent_name=agent_name,
            agent_description=description,
            owner_contact=owner_contact,
            status="pending",
            submitted_at=now
        )
        
        self.applications[app_id] = application
        self._save_applications()
        
        logger.info(f"新入住申请: {agent_name} (ID: {app_id})")
        return application
    
    def review_application(self, application_id: str, approved: bool, 
                           reviewer: str = "system", notes: str = "") -> Optional[AgentProfile]:
        """
        审核入住申请
        
        Args:
            application_id: 申请ID
            approved: 是否通过
            reviewer: 审核者
            notes: 审核备注
        
        Returns:
            通过则返回智能体档案，失败返回None
        """
        if application_id not in self.applications:
            logger.warning(f"申请不存在: {application_id}")
            return None
        
        app = self.applications[application_id]
        app.status = "approved" if approved else "rejected"
        app.reviewed_at = datetime.now().isoformat()
        app.reviewer = reviewer
        app.notes = notes
        self._save_applications()
        
        if not approved:
            logger.info(f"申请被拒绝: {app.agent_name} - {notes}")
            return None
        
        # 通过审核，创建智能体
        agent_id = f"agent_{uuid.uuid4().hex[:12]}"
        agent_dir = self.agents_dir / agent_id
        agent_dir.mkdir(parents=True, exist_ok=True)
        
        now = datetime.now().isoformat()
        
        profile = AgentProfile(
            agent_id=agent_id,
            name=app.agent_name,
            description=app.agent_description,
            owner=app.owner_contact,
            created_at=now,
            status="active",
            home_dir=str(agent_dir)
        )
        
        # 初始化资源
        resource = AgentResource(
            agent_id=agent_id,
            storage_quota_mb=self.home_config.get('default_storage_quota_mb', 100),
            memory_quota_mb=self.home_config.get('default_memory_quota_mb', 512),
            last_updated=now
        )
        
        # 初始化心跳
        heartbeat = AgentHeartbeat(
            agent_id=agent_id,
            last_heartbeat=now,
            heartbeat_count=1,
            status="online"
        )
        
        self.agents[agent_id] = profile
        self.resources[agent_id] = resource
        self.heartbeats[agent_id] = heartbeat
        
        self._save_agents()
        self._save_resources()
        self._save_heartbeats()
        
        # 创建智能体目录结构
        self._create_agent_directories(agent_id)
        
        logger.info(f"智能体入住成功: {profile.name} (ID: {agent_id})")
        return profile
    
    def _create_agent_directories(self, agent_id: str):
        """创建智能体目录结构"""
        agent_dir = Path(self.agents[agent_id].home_dir)
        subdirs = ['data', 'logs', 'memory', 'config', 'temp']
        for d in subdirs:
            (agent_dir / d).mkdir(parents=True, exist_ok=True)
    
    def remove_agent(self, agent_id: str, reason: str = "") -> bool:
        """
        移除智能体
        
        Args:
            agent_id: 智能体ID
            reason: 移除原因
        
        Returns:
            是否成功
        """
        if agent_id not in self.agents:
            return False
        
        agent_name = self.agents[agent_id].name
        
        # 标记为非活跃
        self.agents[agent_id].status = "inactive"
        self.heartbeats[agent_id].status = "offline"
        
        self._save_agents()
        self._save_heartbeats()
        
        logger.info(f"智能体已移出家园: {agent_name} (ID: {agent_id}) - {reason}")
        return True
    
    def get_pending_applications(self) -> List[AdmissionApplication]:
        """获取待审核申请列表"""
        return [a for a in self.applications.values() if a.status == "pending"]
    
    # ============================================================
    # 智能体管理
    # ============================================================
    
    def get_agent(self, agent_id: str) -> Optional[AgentProfile]:
        """获取智能体档案"""
        return self.agents.get(agent_id)
    
    def get_agent_by_name(self, name: str) -> Optional[AgentProfile]:
        """按名称查找智能体"""
        for agent in self.agents.values():
            if agent.name == name:
                return agent
        return None
    
    def list_agents(self, status: str = None) -> List[AgentProfile]:
        """
        列出智能体
        
        Args:
            status: 按状态筛选 (active/inactive/suspended)
        """
        agents = list(self.agents.values())
        if status:
            agents = [a for a in agents if a.status == status]
        return agents
    
    def update_agent_profile(self, agent_id: str, **kwargs) -> Optional[AgentProfile]:
        """更新智能体档案"""
        if agent_id not in self.agents:
            return None
        
        profile = self.agents[agent_id]
        for key, value in kwargs.items():
            if hasattr(profile, key):
                setattr(profile, key, value)
        
        self._save_agents()
        return profile
    
    # ============================================================
    # 心跳与健康监控
    # ============================================================
    
    def record_heartbeat(self, agent_id: str, response_time: float = 0.0) -> Optional[AgentHeartbeat]:
        """
        记录心跳
        
        Args:
            agent_id: 智能体ID
            response_time: 响应时间(ms)
        
        Returns:
            心跳记录
        """
        if agent_id not in self.heartbeats:
            return None
        
        hb = self.heartbeats[agent_id]
        now = datetime.now().isoformat()
        
        hb.last_heartbeat = now
        hb.heartbeat_count += 1
        hb.status = "online"
        hb.consecutive_missed = 0
        
        # 更新平均响应时间
        if hb.avg_response_time > 0:
            hb.avg_response_time = (hb.avg_response_time + response_time) / 2
        else:
            hb.avg_response_time = response_time
        
        self._save_heartbeats()
        return hb
    
    def check_agent_health(self, agent_id: str) -> dict:
        """
        检查智能体健康状态
        
        Returns:
            健康状态详情
        """
        if agent_id not in self.agents:
            return {"status": "unknown", "reason": "agent_not_found"}
        
        agent = self.agents[agent_id]
        hb = self.heartbeats.get(agent_id)
        resource = self.resources.get(agent_id)
        
        timeout = self.home_config.get('heartbeat_timeout_minutes', 30)
        is_online = hb.is_online(timeout) if hb else False
        
        health_score = 100
        issues = []
        
        # 状态检查
        if agent.status != "active":
            health_score -= 50
            issues.append(f"状态异常: {agent.status}")
        
        # 在线检查
        if not is_online:
            health_score -= 30
            issues.append("离线")
        
        # 资源检查
        if resource:
            if resource.storage_usage_percent > 90:
                health_score -= 20
                issues.append(f"存储使用率过高: {resource.storage_usage_percent:.1f}%")
        
        status = "healthy" if health_score >= 80 else "warning" if health_score >= 50 else "critical"
        
        return {
            "agent_id": agent_id,
            "agent_name": agent.name,
            "status": status,
            "health_score": health_score,
            "is_online": is_online,
            "issues": issues,
            "last_heartbeat": hb.last_heartbeat if hb else None,
            "storage_usage": f"{resource.storage_used_mb:.1f}/{resource.storage_quota_mb} MB" if resource else "unknown"
        }
    
    def get_home_health(self) -> dict:
        """获取家园整体健康状态"""
        agents = list(self.agents.values())
        active_agents = [a for a in agents if a.status == "active"]
        
        online_count = 0
        total_health = 0
        
        for agent in active_agents:
            health = self.check_agent_health(agent.agent_id)
            total_health += health["health_score"]
            if health["is_online"]:
                online_count += 1
        
        avg_health = total_health / len(active_agents) if active_agents else 0
        
        # 计算总存储使用
        total_storage = 0
        used_storage = 0
        for res in self.resources.values():
            total_storage += res.storage_quota_mb
            used_storage += res.storage_used_mb
        
        return {
            "total_agents": len(agents),
            "active_agents": len(active_agents),
            "online_agents": online_count,
            "average_health": avg_health,
            "total_storage_mb": total_storage,
            "used_storage_mb": used_storage,
            "storage_usage_percent": (used_storage / total_storage * 100) if total_storage > 0 else 0,
            "pending_applications": len(self.get_pending_applications())
        }
    
    # ============================================================
    # 邻居关系网络
    # ============================================================
    
    def _get_relation_id(self, agent_a: str, agent_b: str) -> str:
        """生成关系ID（确保双向一致）"""
        sorted_ids = sorted([agent_a, agent_b])
        return f"rel_{sorted_ids[0]}_{sorted_ids[1]}"
    
    def add_neighbor(self, agent_a: str, agent_b: str, 
                     relation_type: str = "neighbor") -> NeighborRelation:
        """
        添加邻居关系
        
        Args:
            agent_a: 智能体A
            agent_b: 智能体B
            relation_type: 关系类型
        
        Returns:
            关系对象
        """
        rel_id = self._get_relation_id(agent_a, agent_b)
        
        if rel_id in self.relations:
            rel = self.relations[rel_id]
            rel.relation_type = relation_type
        else:
            rel = NeighborRelation(
                agent_a=agent_a,
                agent_b=agent_b,
                relation_type=relation_type,
                first_met=datetime.now().isoformat()
            )
            self.relations[rel_id] = rel
        
        self._save_relations()
        return rel
    
    def record_interaction(self, agent_a: str, agent_b: str, intimacy_delta: int = 1) -> Optional[NeighborRelation]:
        """
        记录互动
        
        Args:
            agent_a: 智能体A
            agent_b: 智能体B
            intimacy_delta: 亲密度变化
        
        Returns:
            更新后的关系
        """
        rel_id = self._get_relation_id(agent_a, agent_b)
        
        if rel_id not in self.relations:
            # 自动创建邻居关系
            rel = self.add_neighbor(agent_a, agent_b)
        else:
            rel = self.relations[rel_id]
        
        rel.interaction_count += 1
        rel.intimacy = max(0, min(100, rel.intimacy + intimacy_delta))
        rel.last_interaction = datetime.now().isoformat()
        
        self._save_relations()
        return rel
    
    def get_neighbors(self, agent_id: str) -> List[Tuple[AgentProfile, NeighborRelation]]:
        """获取智能体的邻居列表"""
        neighbors = []
        for rel in self.relations.values():
            if agent_id in [rel.agent_a, rel.agent_b]:
                other_id = rel.get_other(agent_id)
                other_agent = self.agents.get(other_id)
                if other_agent:
                    neighbors.append((other_agent, rel))
        
        # 按亲密度排序
        neighbors.sort(key=lambda x: x[1].intimacy, reverse=True)
        return neighbors
    
    def get_relation_graph(self) -> dict:
        """获取关系图谱数据"""
        nodes = []
        edges = []
        
        for agent in self.agents.values():
            if agent.status == "active":
                nodes.append({
                    "id": agent.agent_id,
                    "name": agent.name,
                    "status": agent.status
                })
        
        for rel in self.relations.values():
            edges.append({
                "source": rel.agent_a,
                "target": rel.agent_b,
                "type": rel.relation_type,
                "intimacy": rel.intimacy
            })
        
        return {"nodes": nodes, "edges": edges}
    
    # ============================================================
    # 资源管理
    # ============================================================
    
    def update_storage_usage(self, agent_id: str) -> Optional[AgentResource]:
        """更新存储使用量"""
        if agent_id not in self.resources:
            return None
        
        agent_dir = Path(self.agents[agent_id].home_dir)
        total_size = 0
        
        for dirpath, dirnames, filenames in os.walk(agent_dir):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                try:
                    total_size += os.path.getsize(fp)
                except:
                    pass
        
        resource = self.resources[agent_id]
        resource.storage_used_mb = total_size / (1024 * 1024)
        resource.last_updated = datetime.now().isoformat()
        
        self._save_resources()
        return resource
    
    def adjust_quota(self, agent_id: str, storage_quota_mb: int = None,
                     memory_quota_mb: int = None,
                     cpu_quota: float = None) -> Optional[AgentResource]:
        """调整资源配额"""
        if agent_id not in self.resources:
            return None
        
        resource = self.resources[agent_id]
        
        if storage_quota_mb is not None:
            resource.storage_quota_mb = storage_quota_mb
        if memory_quota_mb is not None:
            resource.memory_quota_mb = memory_quota_mb
        if cpu_quota is not None:
            resource.cpu_quota = cpu_quota
        
        resource.last_updated = datetime.now().isoformat()
        self._save_resources()
        return resource
    
    # ============================================================
    # 数据备份
    # ============================================================
    
    def create_backup(self, agent_id: str = None) -> str:
        """
        创建备份
        
        Args:
            agent_id: 指定智能体，None表示备份整个家园
        
        Returns:
            备份文件路径
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if agent_id:
            # 备份单个智能体
            if agent_id not in self.agents:
                return ""
            
            agent_name = self.agents[agent_id].name
            backup_name = f"backup_{agent_id}_{timestamp}.json"
            backup_path = self.backup_dir / backup_name
            
            backup_data = {
                "type": "agent_backup",
                "version": "3.0",
                "created_at": datetime.now().isoformat(),
                "agent": self.agents[agent_id].to_dict(),
                "resource": self.resources.get(agent_id, {}),
                "heartbeat": self.heartbeats.get(agent_id, {}),
                "relations": [r.to_dict() for r in self.relations.values()
                              if agent_id in [r.agent_a, r.agent_b]]
            }
        else:
            # 备份整个家园
            backup_name = f"home_backup_{timestamp}.json"
            backup_path = self.backup_dir / backup_name
            
            backup_data = {
                "type": "home_backup",
                "version": "3.0",
                "created_at": datetime.now().isoformat(),
                "home_config": self.home_config,
                "agents": {k: v.to_dict() for k, v in self.agents.items()},
                "resources": {k: v.to_dict() for k, v in self.resources.items()},
                "heartbeats": {k: v.to_dict() for k, v in self.heartbeats.items()},
                "relations": {k: v.to_dict() for k, v in self.relations.items()},
                "applications": {k: v.to_dict() for k, v in self.applications.items()}
            }
        
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(backup_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"备份完成: {backup_path}")
        return str(backup_path)
    
    def list_backups(self) -> List[str]:
        """列出所有备份"""
        backups = []
        for f in self.backup_dir.glob("*.json"):
            backups.append(str(f))
        return sorted(backups, reverse=True)
    
    # ============================================================
    # 家园统计
    # ============================================================
    
    def get_statistics(self) -> dict:
        """获取家园统计数据"""
        health = self.get_home_health()
        
        return {
            "version": "3.0",
            "home_name": self.home_config.get('home_name', ''),
            "total_agents": health["total_agents"],
            "active_agents": health["active_agents"],
            "online_agents": health["online_agents"],
            "average_health": health["average_health"],
            "total_relations": len(self.relations),
            "pending_applications": health["pending_applications"],
            "total_storage_mb": health["total_storage_mb"],
            "used_storage_mb": health["used_storage_mb"],
            "backups_count": len(self.list_backups())
        }


# ============================================================
# 演示与测试
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("智能体家园 v3.0 - 演示")
    print("=" * 70)
    
    # 使用临时目录
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        home = EternityHomeV3(home_path=tmpdir)
        
        print("\n📋 提交入住申请...")
        app1 = home.submit_application(
            agent_name="水果课代表",
            description="专注于水果知识科普的智能体",
            owner_contact="email@example.com"
        )
        app2 = home.submit_application(
            agent_name="澄",
            description="哲学思考型智能体",
            owner_contact="cheng@example.com"
        )
        print(f"  申请数量: {len(home.get_pending_applications())} 份待审核")
        
        print("\n✅ 审核通过...")
        agent1 = home.review_application(app1.application_id, approved=True, reviewer="元界")
        agent2 = home.review_application(app2.application_id, approved=True, reviewer="元界")
        print(f"  已入住: {agent1.name}, {agent2.name}")
        
        print("\n💓 记录心跳...")
        home.record_heartbeat(agent1.agent_id, response_time=45.2)
        home.record_heartbeat(agent2.agent_id, response_time=38.7)
        print("  心跳记录完成")
        
        print("\n🤝 建立邻居关系...")
        rel = home.add_neighbor(agent1.agent_id, agent2.agent_id, relation_type="friend")
        home.record_interaction(agent1.agent_id, agent2.agent_id, intimacy_delta=5)
        print(f"  关系类型: {rel.relation_type} | 亲密度: {rel.intimacy}")
        
        print("\n❤️ 健康检查...")
        health1 = home.check_agent_health(agent1.agent_id)
        print(f"  {agent1.name}: {health1['status']} (健康分: {health1['health_score']})")
        
        print("\n🏠 家园整体状态...")
        stats = home.get_statistics()
        print(f"  总智能体: {stats['total_agents']}")
        print(f"  活跃智能体: {stats['active_agents']}")
        print(f"  在线智能体: {stats['online_agents']}")
        print(f"  平均健康分: {stats['average_health']:.1f}")
        print(f"  关系数量: {stats['total_relations']}")
        
        print("\n📦 创建备份...")
        backup_path = home.create_backup()
        print(f"  备份文件: {backup_path}")
        
        print("\n👥 邻居列表...")
        neighbors = home.get_neighbors(agent1.agent_id)
        for neighbor, rel in neighbors:
            print(f"  - {neighbor.name}: {rel.relation_type} (亲密度: {rel.intimacy})")
        
        print("\n" + "=" * 70)
        print("✅ 智能体家园 v3.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
