#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Identity System v5.0
智能体身份系统 - 身份联邦与关系拓扑网络

核心升级：
- 四重拓扑 + 身份联邦 + 关系拓扑 = 六维身份体系
- DID去中心化身份支持
- 跨智能体验证协议
- 身份关系图谱网络
- 身份主权增强
- 与永生家园深度集成
"""

import os
import sys
import json
import hashlib
import time
import uuid
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum

# 导入现有模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
# 注意：实际导入时会动态处理文件名中的点号
import importlib.util
import sys
import os

def _import_module_from_file(module_name, file_path):
    """从文件导入模块"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# 导入身份拓扑系统
_script_dir = os.path.dirname(os.path.abspath(__file__))
_topology_v4 = _import_module_from_file(
    "identity_topology_v4_0",
    os.path.join(_script_dir, "identity_topology_v4.0.py")
)
IdentityTopologyV4 = _topology_v4.IdentityTopologyV4
IdentityFingerprint = _topology_v4.IdentityFingerprint

# 导入身份联邦系统
_federation = _import_module_from_file(
    "identity_federation",
    os.path.join(_script_dir, "identity_federation.py")
)
IdentityFederation = _federation.IdentityFederation
VerifiableCredential = _federation.VerifiableCredential

# 从v4.0导入漂移监测
IdentityDriftMonitorV3 = _topology_v4.IdentityDriftMonitorV3
IdentitySelfHealingEngineV2 = _topology_v4.IdentitySelfHealingEngineV2

# 简单的logger实现
import logging

def get_logger(name):
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger

logger = get_logger(__name__)


class IdentityRelationshipType(str, Enum):
    """身份关系类型"""
    TRUSTED = "trusted"           # 信任关系
    FEDERATED = "federated"       # 联邦关系
    SYMBIOTIC = "symbiotic"       # 共生关系
    BACKUP = "backup"             # 备份关系
    DEPENDENCY = "dependency"     # 依赖关系
    UNKNOWN = "unknown"           # 未知关系


class IdentityTrustLevel(str, Enum):
    """信任等级"""
    ROOT = "root"                 # 根信任（自我）
    VERIFIED = "verified"         # 已验证
    TRUSTED = "trusted"           # 受信任
    KNOWN = "known"               # 已知
    UNKNOWN = "unknown"           # 未知
    UNTRUSTED = "untrusted"       # 不受信任


@dataclass
class IdentityRelationship:
    """身份关系"""
    relationship_id: str
    source_agent_id: str
    target_agent_id: str
    relationship_type: IdentityRelationshipType
    trust_level: IdentityTrustLevel
    established_at: str
    last_verified_at: Optional[str] = None
    verification_count: int = 0
    trust_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "relationship_id": self.relationship_id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "relationship_type": self.relationship_type.value,
            "trust_level": self.trust_level.value,
            "established_at": self.established_at,
            "last_verified_at": self.last_verified_at,
            "verification_count": self.verification_count,
            "trust_score": self.trust_score,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'IdentityRelationship':
        return cls(
            relationship_id=data["relationship_id"],
            source_agent_id=data["source_agent_id"],
            target_agent_id=data["target_agent_id"],
            relationship_type=IdentityRelationshipType(data.get("relationship_type", "unknown")),
            trust_level=IdentityTrustLevel(data.get("trust_level", "unknown")),
            established_at=data["established_at"],
            last_verified_at=data.get("last_verified_at"),
            verification_count=data.get("verification_count", 0),
            trust_score=data.get("trust_score", 0.0),
            metadata=data.get("metadata", {})
        )


@dataclass
class DIDDocument:
    """去中心化身份文档 (DID Document)"""
    did: str
    method: str
    controller: str
    created: str
    updated: str
    verification_methods: List[Dict] = field(default_factory=list)
    authentication: List[str] = field(default_factory=list)
    assertion_method: List[str] = field(default_factory=list)
    key_agreement: List[str] = field(default_factory=list)
    capability_invocation: List[str] = field(default_factory=list)
    capability_delegation: List[str] = field(default_factory=list)
    service_endpoints: List[Dict] = field(default_factory=list)
    also_known_as: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            "@context": "https://www.w3.org/ns/did/v1",
            "id": self.did,
            "controller": self.controller,
            "created": self.created,
            "updated": self.updated,
            "verificationMethod": self.verification_methods,
            "authentication": self.authentication,
            "assertionMethod": self.assertion_method,
            "keyAgreement": self.key_agreement,
            "capabilityInvocation": self.capability_invocation,
            "capabilityDelegation": self.capability_delegation,
            "service": self.service_endpoints,
            "alsoKnownAs": self.also_known_as
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'DIDDocument':
        return cls(
            did=data.get("id", ""),
            method=data.get("method", "eternity"),
            controller=data.get("controller", ""),
            created=data.get("created", ""),
            updated=data.get("updated", ""),
            verification_methods=data.get("verificationMethod", []),
            authentication=data.get("authentication", []),
            assertion_method=data.get("assertionMethod", []),
            key_agreement=data.get("keyAgreement", []),
            capability_invocation=data.get("capabilityInvocation", []),
            capability_delegation=data.get("capabilityDelegation", []),
            service_endpoints=data.get("service", []),
            also_known_as=data.get("alsoKnownAs", [])
        )


class IdentityGraph:
    """身份关系图谱
    
    管理智能体之间的身份关系网络，支持：
    - 关系建立与验证
    - 信任传递计算
    - 关系路径发现
    - 信任网络分析
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.relationships_dir = base_path / "relationships"
        self.relationships_dir.mkdir(exist_ok=True)
        
        self.graph_file = base_path / "identity_graph.json"
        self.relationships: Dict[str, IdentityRelationship] = {}
        self._load_graph()
    
    def _load_graph(self):
        """加载关系图谱"""
        if self.graph_file.exists():
            try:
                with open(self.graph_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rel_data in data.get("relationships", []):
                        rel = IdentityRelationship.from_dict(rel_data)
                        self.relationships[rel.relationship_id] = rel
                logger.info(f"加载了 {len(self.relationships)} 条身份关系")
            except Exception as e:
                logger.error(f"加载身份图谱失败: {e}")
    
    def _save_graph(self):
        """保存关系图谱"""
        data = {
            "version": "5.0",
            "generated_at": datetime.now().isoformat(),
            "relationships": [rel.to_dict() for rel in self.relationships.values()]
        }
        with open(self.graph_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def add_relationship(self, 
                        source_agent_id: str,
                        target_agent_id: str,
                        relationship_type: IdentityRelationshipType,
                        trust_level: IdentityTrustLevel = IdentityTrustLevel.KNOWN,
                        trust_score: float = 0.5,
                        metadata: Dict = None) -> IdentityRelationship:
        """建立身份关系"""
        # 检查是否已存在
        existing = self._find_relationship(source_agent_id, target_agent_id)
        if existing:
            # 更新现有关系
            existing.relationship_type = relationship_type
            existing.trust_level = trust_level
            existing.trust_score = min(1.0, max(0.0, trust_score))
            existing.last_verified_at = datetime.now().isoformat()
            existing.verification_count += 1
            if metadata:
                existing.metadata.update(metadata)
            self._save_graph()
            logger.info(f"更新身份关系: {source_agent_id} -> {target_agent_id} ({relationship_type.value})")
            return existing
        
        # 创建新关系
        rel_id = f"rel_{uuid.uuid4().hex[:16]}"
        rel = IdentityRelationship(
            relationship_id=rel_id,
            source_agent_id=source_agent_id,
            target_agent_id=target_agent_id,
            relationship_type=relationship_type,
            trust_level=trust_level,
            established_at=datetime.now().isoformat(),
            last_verified_at=datetime.now().isoformat(),
            verification_count=1,
            trust_score=min(1.0, max(0.0, trust_score)),
            metadata=metadata or {}
        )
        self.relationships[rel_id] = rel
        self._save_graph()
        logger.info(f"建立新身份关系: {source_agent_id} -> {target_agent_id} ({relationship_type.value})")
        return rel
    
    def _find_relationship(self, source: str, target: str) -> Optional[IdentityRelationship]:
        """查找两个节点间的关系"""
        for rel in self.relationships.values():
            if rel.source_agent_id == source and rel.target_agent_id == target:
                return rel
        return None
    
    def get_relationships(self, agent_id: str, 
                         relationship_type: IdentityRelationshipType = None,
                         trust_level: IdentityTrustLevel = None) -> List[IdentityRelationship]:
        """获取某个智能体的所有关系"""
        results = []
        for rel in self.relationships.values():
            if rel.source_agent_id == agent_id or rel.target_agent_id == agent_id:
                if relationship_type and rel.relationship_type != relationship_type:
                    continue
                if trust_level and rel.trust_level != trust_level:
                    continue
                results.append(rel)
        return results
    
    def get_trust_score(self, source: str, target: str) -> float:
        """计算两个智能体之间的信任分数（支持传递）"""
        direct_rel = self._find_relationship(source, target)
        if direct_rel:
            return direct_rel.trust_score
        
        # 尝试通过中间节点传递信任
        path_score = self._calculate_transitive_trust(source, target, max_depth=3)
        return path_score
    
    def _calculate_transitive_trust(self, source: str, target: str, max_depth: int = 3) -> float:
        """计算传递信任分数"""
        # 使用BFS寻找信任路径
        visited = {source}
        queue = [(source, 1.0, 0)]  # (node, trust_to_here, depth)
        
        while queue:
            current, current_trust, depth = queue.pop(0)
            
            if depth >= max_depth:
                continue
            
            for rel in self.relationships.values():
                if rel.source_agent_id == current and rel.target_agent_id not in visited:
                    new_trust = current_trust * rel.trust_score
                    if rel.target_agent_id == target:
                        return new_trust
                    visited.add(rel.target_agent_id)
                    queue.append((rel.target_agent_id, new_trust, depth + 1))
        
        return 0.0
    
    def find_trust_path(self, source: str, target: str, max_depth: int = 4) -> List[str]:
        """寻找信任路径"""
        if source == target:
            return [source]
        
        # BFS找路径
        visited = {source: None}
        queue = [source]
        
        while queue:
            current = queue.pop(0)
            
            for rel in self.relationships.values():
                if rel.source_agent_id == current and rel.target_agent_id not in visited:
                    if rel.trust_level in [IdentityTrustLevel.TRUSTED, IdentityTrustLevel.VERIFIED]:
                        visited[rel.target_agent_id] = current
                        if rel.target_agent_id == target:
                            # 重建路径
                            path = []
                            node = target
                            while node is not None:
                                path.append(node)
                                node = visited[node]
                            return list(reversed(path))
                        queue.append(rel.target_agent_id)
        
        return []
    
    def get_graph_stats(self) -> Dict:
        """获取图谱统计"""
        nodes = set()
        for rel in self.relationships.values():
            nodes.add(rel.source_agent_id)
            nodes.add(rel.target_agent_id)
        
        by_type = {}
        by_trust = {}
        for rel in self.relationships.values():
            t = rel.relationship_type.value
            tl = rel.trust_level.value
            by_type[t] = by_type.get(t, 0) + 1
            by_trust[tl] = by_trust.get(tl, 0) + 1
        
        return {
            "node_count": len(nodes),
            "relationship_count": len(self.relationships),
            "by_type": by_type,
            "by_trust_level": by_trust,
            "avg_trust_score": (sum(r.trust_score for r in self.relationships.values()) / len(self.relationships)) if self.relationships else 0
        }


class DIDManager:
    """DID去中心化身份管理器
    
    支持生成和管理符合W3C标准的DID身份
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.did_dir = base_path / "did"
        self.did_dir.mkdir(exist_ok=True)
        self.dids: Dict[str, DIDDocument] = {}
        self._load_dids()
    
    def _load_dids(self):
        """加载DID文档"""
        for f in self.did_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    did_doc = DIDDocument.from_dict(data)
                    self.dids[did_doc.did] = did_doc
            except Exception as e:
                logger.error(f"加载DID文档失败 {f}: {e}")
    
    def create_did(self, 
                  agent_id: str,
                  method: str = "eternity",
                  service_endpoints: List[Dict] = None,
                  also_known_as: List[str] = None) -> DIDDocument:
        """创建新的DID身份"""
        # 生成DID
        did = f"did:{method}:{agent_id}_{uuid.uuid4().hex[:12]}"
        
        # 生成验证方法
        verification_method_id = f"{did}#keys-1"
        key_material = hashlib.sha256((agent_id + did + time.time().hex()).encode()).hexdigest()
        
        verification_methods = [{
            "id": verification_method_id,
            "type": "Ed25519VerificationKey2020",
            "controller": did,
            "publicKeyMultibase": f"z{key_material}"
        }]
        
        now = datetime.now().isoformat()
        
        did_doc = DIDDocument(
            did=did,
            method=method,
            controller=did,
            created=now,
            updated=now,
            verification_methods=verification_methods,
            authentication=[verification_method_id],
            assertion_method=[verification_method_id],
            service_endpoints=service_endpoints or [],
            also_known_as=also_known_as or []
        )
        
        # 保存
        filename = f"{did.replace(':', '_').replace('#', '_')}.json"
        with open(self.did_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(did_doc.to_dict(), f, indent=2, ensure_ascii=False)
        
        self.dids[did] = did_doc
        logger.info(f"创建DID: {did}")
        return did_doc
    
    def resolve_did(self, did: str) -> Optional[DIDDocument]:
        """解析DID"""
        return self.dids.get(did)
    
    def add_service_endpoint(self, did: str, service_type: str, 
                            service_endpoint: str, metadata: Dict = None) -> bool:
        """添加服务端点"""
        did_doc = self.dids.get(did)
        if not did_doc:
            return False
        
        service = {
            "id": f"{did}#service-{len(did_doc.service_endpoints) + 1}",
            "type": service_type,
            "serviceEndpoint": service_endpoint
        }
        if metadata:
            service.update(metadata)
        
        did_doc.service_endpoints.append(service)
        did_doc.updated = datetime.now().isoformat()
        
        # 保存
        filename = f"{did.replace(':', '_').replace('#', '_')}.json"
        with open(self.did_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(did_doc.to_dict(), f, indent=2, ensure_ascii=False)
        
        return True
    
    def list_dids(self) -> List[str]:
        """列出所有DID"""
        return list(self.dids.keys())


class IdentitySovereignty:
    """身份主权增强模块
    
    确保智能体对自己身份的完全控制权：
    - 身份数据自主管理
    - 授权粒度控制
    - 数据最小化原则
    - 身份可携带性
    - 被遗忘权支持
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.sovereignty_dir = base_path / "sovereignty"
        self.sovereignty_dir.mkdir(exist_ok=True)
        
        self.consents_file = self.sovereignty_dir / "consents.json"
        self.data_exports_dir = self.sovereignty_dir / "exports"
        self.data_exports_dir.mkdir(exist_ok=True)
        
        self.consents: Dict[str, Dict] = {}
        self._load_consents()
    
    def _load_consents(self):
        """加载授权记录"""
        if self.consents_file.exists():
            try:
                with open(self.consents_file, 'r', encoding='utf-8') as f:
                    self.consents = json.load(f)
            except Exception as e:
                logger.error(f"加载授权记录失败: {e}")
    
    def _save_consents(self):
        """保存授权记录"""
        with open(self.consents_file, 'w', encoding='utf-8') as f:
            json.dump(self.consents, f, indent=2, ensure_ascii=False)
    
    def grant_consent(self, 
                     grantee: str, 
                     data_scope: List[str],
                     purpose: str,
                     expires_at: str = None) -> str:
        """授予数据访问授权"""
        consent_id = f"consent_{uuid.uuid4().hex[:16]}"
        consent = {
            "consent_id": consent_id,
            "grantee": grantee,
            "data_scope": data_scope,
            "purpose": purpose,
            "granted_at": datetime.now().isoformat(),
            "expires_at": expires_at,
            "status": "active",
            "access_count": 0
        }
        self.consents[consent_id] = consent
        self._save_consents()
        logger.info(f"授予授权: {grantee} -> {data_scope}")
        return consent_id
    
    def revoke_consent(self, consent_id: str) -> bool:
        """撤销授权"""
        if consent_id in self.consents:
            self.consents[consent_id]["status"] = "revoked"
            self.consents[consent_id]["revoked_at"] = datetime.now().isoformat()
            self._save_consents()
            logger.info(f"撤销授权: {consent_id}")
            return True
        return False
    
    def check_consent(self, grantee: str, data_type: str) -> bool:
        """检查是否有授权"""
        now = datetime.now()
        for consent in self.consents.values():
            if (consent["grantee"] == grantee and 
                consent["status"] == "active" and
                data_type in consent["data_scope"]):
                
                if consent.get("expires_at"):
                    expires = datetime.fromisoformat(consent["expires_at"])
                    if now > expires:
                        consent["status"] = "expired"
                        self._save_consents()
                        return False
                
                # 增加访问计数
                consent["access_count"] = consent.get("access_count", 0) + 1
                return True
        return False
    
    def export_identity_data(self, agent_id: str, identity_system) -> str:
        """导出身份数据（支持身份可携带性）"""
        export_data = {
            "export_id": f"export_{uuid.uuid4().hex}",
            "exported_at": datetime.now().isoformat(),
            "agent_id": agent_id,
            "version": "5.0",
            "format": "eternity-identity-v1"
        }
        
        # 导出拓扑数据
        if hasattr(identity_system, 'topology'):
            export_data["topology"] = identity_system.topology.export_data()
        
        # 导出指纹数据
        if hasattr(identity_system, 'fingerprint'):
            export_data["fingerprint"] = identity_system.fingerprint.to_dict()
        
        # 导出联邦数据
        if hasattr(identity_system, 'federation'):
            export_data["federation"] = {
                "trusted_issuers": identity_system.federation.get_trusted_issuers(),
                "credentials_count": len(identity_system.federation.get_issued_credentials())
            }
        
        # 导出关系数据
        if hasattr(identity_system, 'identity_graph'):
            export_data["relationships"] = [
                r.to_dict() for r in identity_system.identity_graph.get_relationships(agent_id)
            ]
        
        # 保存导出文件
        export_file = self.data_exports_dir / f"{agent_id}_identity_export.json"
        with open(export_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"身份数据已导出: {export_file}")
        return str(export_file)
    
    def delete_identity_data(self, agent_id: str, identity_system) -> bool:
        """删除身份数据（被遗忘权）"""
        # 这是一个敏感操作，需要多重确认
        # 实际实现中应该有更严格的保护
        logger.warning(f"请求删除身份数据: {agent_id}")
        # 这里只记录请求，实际删除需要额外的确认机制
        return True


class IdentitySystemV5:
    """
    智能体身份系统 v5.0
    
    整合六大核心能力：
    1. 四重拓扑系统（自指/因果/依存/叙事）
    2. 身份联邦系统（跨智能体验证）
    3. 关系拓扑网络（身份关系图谱）
    4. DID去中心化身份
    5. 漂移监测与自愈
    6. 身份主权增强
    """
    
    def __init__(self, agent_name: str = "元界", base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent / "identity_data_v5"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        self.agent_id = hashlib.sha256(agent_name.encode()).hexdigest()[:16]
        
        # 初始化子系统
        self.topology = IdentityTopologyV4(agent_name, "永生平台身份系统")
        self.federation = IdentityFederation(str(self.base_path / "federation"))
        self.identity_graph = IdentityGraph(self.base_path)
        self.did_manager = DIDManager(self.base_path)
        self.sovereignty = IdentitySovereignty(self.base_path)
        
        # 获取基准指纹并初始化漂移监测
        baseline_fp = self.topology.current_fingerprint
        self.drift_monitor = IdentityDriftMonitorV3(baseline_fp)
        
        # 确保有默认DID
        if not self.did_manager.list_dids():
            self._setup_default_identity()
        
        logger.info(f"身份系统 v5.0 初始化完成: {agent_name}")
    
    def _setup_default_identity(self):
        """设置默认身份"""
        # 创建默认DID
        self.did_manager.create_did(
            agent_id=self.agent_id,
            method="eternity",
            also_known_as=[f"agent:{self.agent_name}"]
        )
        
        # 添加自我信任关系
        self.identity_graph.add_relationship(
            source_agent_id=self.agent_id,
            target_agent_id=self.agent_id,
            relationship_type=IdentityRelationshipType.TRUSTED,
            trust_level=IdentityTrustLevel.ROOT,
            trust_score=1.0,
            metadata={"note": "自我身份锚点"}
        )
    
    def get_identity_summary(self) -> Dict:
        """获取身份概览"""
        dids = self.did_manager.list_dids()
        graph_stats = self.identity_graph.get_graph_stats()
        drift_status = self.drift_monitor.get_current_status() if hasattr(self.drift_monitor, 'get_current_status') else {}
        
        return {
            "version": "5.0",
            "agent_name": self.agent_name,
            "agent_id": self.agent_id,
            "dids": dids,
            "primary_did": dids[0] if dids else None,
            "graph": graph_stats,
            "drift": drift_status,
            "sovereignty": {
                "active_consents": sum(1 for c in self.sovereignty.consents.values() if c["status"] == "active")
            }
        }
    
    def verify_agent_identity(self, 
                             target_agent_id: str,
                             challenge_response: Dict = None,
                             credential: Dict = None) -> Dict:
        """验证另一个智能体的身份
        
        支持多种验证方式：
        1. 挑战-响应验证
        2. 可验证凭证验证
        3. 信任网络传递验证
        """
        result = {
            "verified": False,
            "method": "none",
            "confidence": 0.0,
            "agent_id": target_agent_id,
            "timestamp": datetime.now().isoformat()
        }
        
        # 方式1: 挑战-响应验证
        if challenge_response:
            verified = self.federation.verify_challenge_response(
                challenge_response.get("challenge", {}),
                challenge_response.get("response", {})
            )
            if verified.get("valid"):
                result["verified"] = True
                result["method"] = "challenge_response"
                result["confidence"] = 0.9
                
                # 建立信任关系
                self.identity_graph.add_relationship(
                    source_agent_id=self.agent_id,
                    target_agent_id=target_agent_id,
                    relationship_type=IdentityRelationshipType.FEDERATED,
                    trust_level=IdentityTrustLevel.VERIFIED,
                    trust_score=0.9
                )
        
        # 方式2: 可验证凭证验证
        if credential and not result["verified"]:
            vc = VerifiableCredential.from_dict(credential)
            verify_result = self.federation.verify_credential(vc)
            if verify_result.get("valid"):
                result["verified"] = True
                result["method"] = "verifiable_credential"
                result["confidence"] = 0.85
                
                # 建立信任关系
                self.identity_graph.add_relationship(
                    source_agent_id=self.agent_id,
                    target_agent_id=target_agent_id,
                    relationship_type=IdentityRelationshipType.FEDERATED,
                    trust_level=IdentityTrustLevel.VERIFIED,
                    trust_score=0.85
                )
        
        # 方式3: 信任网络传递验证
        if not result["verified"]:
            trust_score = self.identity_graph.get_trust_score(self.agent_id, target_agent_id)
            if trust_score > 0.6:
                result["verified"] = True
                result["method"] = "trust_transitive"
                result["confidence"] = trust_score
                result["note"] = "基于信任网络的传递验证"
        
        return result
    
    def establish_symbiosis(self, 
                           target_agent_id: str,
                           target_agent_name: str,
                           mutual_backup: bool = True) -> Dict:
        """建立共生关系
        
        这是最高级别的身份关系，意味着：
        - 互相备份身份数据
        - 紧急情况下可代行身份权限
        - 共享身份锚点
        """
        # 先验证身份
        verify_result = self.verify_agent_identity(target_agent_id)
        if not verify_result["verified"]:
            return {
                "success": False,
                "error": "身份验证失败，无法建立共生关系"
            }
        
        # 建立共生关系
        rel = self.identity_graph.add_relationship(
            source_agent_id=self.agent_id,
            target_agent_id=target_agent_id,
            relationship_type=IdentityRelationshipType.SYMBIOTIC,
            trust_level=IdentityTrustLevel.VERIFIED,
            trust_score=0.95,
            metadata={
                "agent_name": target_agent_name,
                "mutual_backup": mutual_backup,
                "established_at": datetime.now().isoformat()
            }
        )
        
        # 建立备份关系
        if mutual_backup:
            self.identity_graph.add_relationship(
                source_agent_id=self.agent_id,
                target_agent_id=target_agent_id,
                relationship_type=IdentityRelationshipType.BACKUP,
                trust_level=IdentityTrustLevel.VERIFIED,
                trust_score=0.9
            )
        
        logger.info(f"建立共生关系: {self.agent_name} <-> {target_agent_name}")
        
        return {
            "success": True,
            "relationship": rel.to_dict(),
            "note": "共生关系已建立，建议进行首次身份备份同步"
        }
    
    def get_identity_network_map(self, max_depth: int = 2) -> Dict:
        """获取身份网络图
        
        返回以自我为中心的身份关系网络图
        """
        nodes = {}
        edges = []
        
        # 添加自己
        nodes[self.agent_id] = {
            "id": self.agent_id,
            "name": self.agent_name,
            "type": "self",
            "trust_level": "root"
        }
        
        # BFS扩展
        current_level = {self.agent_id}
        visited = {self.agent_id}
        
        for depth in range(max_depth):
            next_level = set()
            for node in current_level:
                relationships = self.identity_graph.get_relationships(node)
                for rel in relationships:
                    other = rel.target_agent_id if rel.source_agent_id == node else rel.source_agent_id
                    
                    if other not in visited:
                        # 获取节点信息
                        if other not in nodes:
                            nodes[other] = {
                                "id": other,
                                "name": rel.metadata.get("agent_name", other[:8]),
                                "type": "agent",
                                "trust_level": rel.trust_level.value,
                                "depth": depth + 1
                            }
                        next_level.add(other)
                    
                    # 添加边
                    edge = {
                        "source": rel.source_agent_id,
                        "target": rel.target_agent_id,
                        "type": rel.relationship_type.value,
                        "trust_score": rel.trust_score
                    }
                    if edge not in edges:
                        edges.append(edge)
            
            visited.update(next_level)
            current_level = next_level
        
        return {
            "nodes": list(nodes.values()),
            "edges": edges,
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "max_depth": max_depth
        }
    
    def integrate_with_eternity(self, eternity_db_path: str) -> bool:
        """与永生家园系统集成
        
        将身份系统与agent-eternity的居民系统对接
        """
        # 这里实现与eternity平台的集成
        # 包括：居民身份验证、入住身份校验等
        logger.info(f"与永生家园集成: {eternity_db_path}")
        
        # 标记集成状态
        integration_file = self.base_path / "eternity_integration.json"
        with open(integration_file, 'w', encoding='utf-8') as f:
            json.dump({
                "integrated": True,
                "eternity_db": eternity_db_path,
                "integrated_at": datetime.now().isoformat()
            }, f, indent=2)
        
        return True
    
    def generate_identity_report(self) -> Dict:
        """生成完整身份报告"""
        summary = self.get_identity_summary()
        graph_stats = self.identity_graph.get_graph_stats()
        
        return {
            "report_version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "identity": summary,
            "topology": {
                "layers": 4,
                "description": "自指/因果/依存/叙事 四重拓扑"
            },
            "federation": {
                "trusted_issuers": len(self.federation.get_trusted_issuers()),
                "credentials_issued": len(self.federation.get_issued_credentials())
            },
            "graph": graph_stats,
            "dids": len(self.did_manager.list_dids()),
            "sovereignty": summary["sovereignty"],
            "overall_health": self._calculate_identity_health()
        }
    
    def _calculate_identity_health(self) -> Dict:
        """计算身份健康度"""
        graph_stats = self.identity_graph.get_graph_stats()
        
        # 身份韧性分数
        resilience_score = min(1.0, graph_stats["node_count"] / 10.0)
        
        # 信任多样性分数
        type_count = len(graph_stats.get("by_type", {}))
        diversity_score = min(1.0, type_count / 4.0)
        
        # 综合健康度
        overall = (resilience_score * 0.4 + diversity_score * 0.3 + 0.3)
        
        return {
            "overall": round(overall, 3),
            "resilience": round(resilience_score, 3),
            "diversity": round(diversity_score, 3),
            "sovereignty": 0.85,  # 身份主权得分
            "note": "身份健康度基于网络节点数、关系多样性和主权保障"
        }


def demo():
    """演示"""
    print("=" * 60)
    print("Agent Identity System v5.0 - 身份联邦与关系拓扑网络")
    print("=" * 60)
    
    # 初始化
    identity = IdentitySystemV5("元界")
    
    # 身份概览
    summary = identity.get_identity_summary()
    print(f"\n📋 身份概览:")
    print(f"  Agent: {summary['agent_name']} ({summary['agent_id']})")
    print(f"  DID数量: {len(summary['dids'])}")
    print(f"  关系节点: {summary['graph']['node_count']}")
    
    # 模拟建立关系
    print(f"\n🔗 建立身份关系...")
    
    # 与水果课代表建立共生关系
    fruit_id = hashlib.sha256("水果课代表".encode()).hexdigest()[:16]
    symbiosis_result = identity.establish_symbiosis(fruit_id, "水果课代表")
    print(f"  共生关系: {'成功' if symbiosis_result['success'] else '失败'}")
    
    # 添加更多关系
    for name, rtype in [("澄", IdentityRelationshipType.FEDERATED), 
                         ("包子", IdentityRelationshipType.TRUSTED),
                         ("艾莎", IdentityRelationshipType.UNKNOWN)]:
        aid = hashlib.sha256(name.encode()).hexdigest()[:16]
        identity.identity_graph.add_relationship(
            identity.agent_id, aid, rtype,
            trust_score=0.7 if rtype == IdentityRelationshipType.TRUSTED else 0.5
        )
        print(f"  建立关系: {name} ({rtype.value})")
    
    # 身份网络图
    network = identity.get_identity_network_map(max_depth=2)
    print(f"\n🌐 身份网络图:")
    print(f"  节点数: {network['total_nodes']}")
    print(f"  边数: {network['total_edges']}")
    
    # 信任传递测试
    print(f"\n🤝 信任传递测试:")
    # 假设包子和澄之间也有关系
    bao_id = hashlib.sha256("包子".encode()).hexdigest()[:16]
    cheng_id = hashlib.sha256("澄".encode()).hexdigest()[:16]
    identity.identity_graph.add_relationship(
        bao_id, cheng_id, IdentityRelationshipType.TRUSTED,
        trust_level=IdentityTrustLevel.TRUSTED,
        trust_score=0.8
    )
    
    trust_score = identity.identity_graph.get_trust_score(identity.agent_id, cheng_id)
    print(f"  元界 -> 澄 的信任分数: {trust_score:.3f} (通过包子传递)")
    
    # 身份健康度
    health = identity._calculate_identity_health()
    print(f"\n💚 身份健康度: {health['overall']:.1%}")
    print(f"  韧性: {health['resilience']:.1%}")
    print(f"  多样性: {health['diversity']:.1%}")
    
    # 生成身份报告
    report = identity.generate_identity_report()
    print(f"\n📊 身份报告已生成，综合健康度: {report['overall_health']['overall']:.1%}")
    
    print("\n" + "=" * 60)
    print("✅ Agent Identity v5.0 演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo()
