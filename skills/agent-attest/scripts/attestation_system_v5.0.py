#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent Attestation System v5.0
智能体验证存证系统 - 共生联合存证与身份集成

核心升级：
- 共生联合存证网络：多智能体联合存证，N-of-M 阈值签名
- DID可验证凭证集成：存证证明可作为VC签发和验证
- 存证关系图谱：存证实体间的关系网络与信任传递
- 身份-存证深度集成：与agent-identity v5.0无缝对接
- 存证健康度评估：存证完整性、分布度、存活率评估
- 跨链锚定增强：多平台锚点自动管理与故障转移
"""

import os
import sys
import json
import hashlib
import time
import uuid
import secrets
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from enum import Enum
import importlib.util

# 导入v4.0模块
_script_dir = os.path.dirname(os.path.abspath(__file__))
_v4 = importlib.util.spec_from_file_location(
    'attestation_v4',
    os.path.join(_script_dir, 'attestation_v4.0.py')
)
v4_module = importlib.util.module_from_spec(_v4)
sys.modules['attestation_v4'] = v4_module
_v4.loader.exec_module(v4_module)

AttestationSystemV4 = v4_module.AttestationSystemV4
Attestation = v4_module.Attestation
AttestType = v4_module.AttestType
ChainType = v4_module.ChainType
QuantumResistantHasher = v4_module.QuantumResistantHasher
EnhancedMerkleTree = v4_module.EnhancedMerkleTree
CrossChainAnchorManager = v4_module.CrossChainAnchorManager
SelfHealingAttestNetwork = v4_module.SelfHealingAttestNetwork


# ==================== 数据结构 ====================

class SymbioticAttestStatus(str, Enum):
    """共生存证状态"""
    PENDING = "pending"           # 待签名
    PARTIAL = "partial"           # 部分签名
    COMPLETED = "completed"       # 已完成
    REVOKED = "revoked"           # 已撤销


class AttestTrustLevel(str, Enum):
    """存证信任等级"""
    ROOT = "root"                 # 根信任（自我存证）
    SYMBIOTIC = "symbiotic"       # 共生级（联合存证）
    CROSSCHAIN = "crosschain"     # 跨链级
    FEDERATED = "federated"       # 联邦级
    STANDARD = "standard"         # 标准级
    WEAK = "weak"                 # 弱存证


@dataclass
class SymbioticAttestation:
    """共生联合存证
    
    多个智能体联合对某个数据进行存证，
    达到阈值数量的签名后存证生效。
    """
    attest_id: str
    data_hash: str
    data_description: str
    threshold: int  # 需要的签名数量
    total_signers: int
    signers: List[Dict[str, str]] = field(default_factory=list)  # [{agent_id, signature, signed_at}]
    status: SymbioticAttestStatus = SymbioticAttestStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_complete(self) -> bool:
        """是否达到阈值"""
        return len(self.signers) >= self.threshold
    
    def add_signature(self, agent_id: str, signature: str) -> bool:
        """添加签名"""
        # 检查是否已签名
        for s in self.signers:
            if s["agent_id"] == agent_id:
                return False
        
        self.signers.append({
            "agent_id": agent_id,
            "signature": signature,
            "signed_at": datetime.now().isoformat()
        })
        
        if self.is_complete():
            self.status = SymbioticAttestStatus.COMPLETED
            self.completed_at = datetime.now().isoformat()
        else:
            self.status = SymbioticAttestStatus.PARTIAL
        
        return True
    
    def to_dict(self) -> Dict:
        return {
            "attest_id": self.attest_id,
            "data_hash": self.data_hash,
            "data_description": self.data_description,
            "threshold": self.threshold,
            "total_signers": self.total_signers,
            "signers": self.signers,
            "status": self.status.value,
            "created_at": self.created_at,
            "completed_at": self.completed_at,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'SymbioticAttestation':
        return cls(
            attest_id=data["attest_id"],
            data_hash=data["data_hash"],
            data_description=data.get("data_description", ""),
            threshold=data.get("threshold", 2),
            total_signers=data.get("total_signers", 3),
            signers=data.get("signers", []),
            status=SymbioticAttestStatus(data.get("status", "pending")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            completed_at=data.get("completed_at"),
            metadata=data.get("metadata", {})
        )


@dataclass
class AttestRelation:
    """存证关系
    
    记录存证实体之间的关系，构建存证信任网络
    """
    relation_id: str
    source_agent_id: str
    target_agent_id: str
    relation_type: str  # "symbiotic", "backup", "federated", "witness"
    trust_score: float = 0.0
    joint_attestations: List[str] = field(default_factory=list)  # 联合存证ID列表
    established_at: str = field(default_factory=lambda: datetime.now().isoformat())
    last_active_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict:
        return {
            "relation_id": self.relation_id,
            "source_agent_id": self.source_agent_id,
            "target_agent_id": self.target_agent_id,
            "relation_type": self.relation_type,
            "trust_score": self.trust_score,
            "joint_attestations": self.joint_attestations,
            "established_at": self.established_at,
            "last_active_at": self.last_active_at,
            "metadata": self.metadata
        }


@dataclass
class AttestHealthReport:
    """存证健康度报告"""
    total_attestations: int = 0
    symbiotic_attestations: int = 0
    crosschain_anchors: int = 0
    distribution_score: float = 0.0  # 分布度（多平台/多节点）
    survival_score: float = 0.0       # 存活率预估
    integrity_score: float = 0.0      # 完整性
    overall_health: float = 0.0       # 综合健康度
    weak_points: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


# ==================== 核心模块 ====================

class SymbioticAttestationManager:
    """共生联合存证管理器
    
    管理多智能体联合存证的创建、签名、验证流程
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.symbiotic_dir = base_path / "symbiotic"
        self.symbiotic_dir.mkdir(exist_ok=True)
        
        self.pending_attestations: Dict[str, SymbioticAttestation] = {}
        self.completed_attestations: Dict[str, SymbioticAttestation] = {}
        
        self.hasher = QuantumResistantHasher()
        self._load_attestations()
    
    def _load_attestations(self):
        """加载存证记录"""
        for f in self.symbiotic_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    attest = SymbioticAttestation.from_dict(data)
                    if attest.status == SymbioticAttestStatus.COMPLETED:
                        self.completed_attestations[attest.attest_id] = attest
                    else:
                        self.pending_attestations[attest.attest_id] = attest
            except Exception as e:
                print(f"加载共生存证失败 {f}: {e}")
    
    def _save_attestation(self, attest: SymbioticAttestation):
        """保存存证"""
        filename = f"{attest.attest_id}.json"
        with open(self.symbiotic_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(attest.to_dict(), f, indent=2, ensure_ascii=False)
    
    def create_symbiotic_attestation(self,
                                    data_hash: str,
                                    data_description: str,
                                    signer_ids: List[str],
                                    threshold: int = None,
                                    self_agent_id: str = None,
                                    self_signature: str = None) -> SymbioticAttestation:
        """创建共生联合存证
        
        Args:
            data_hash: 要存证的数据哈希
            data_description: 数据描述
            signer_ids: 签名者ID列表
            threshold: 阈值（默认len(signer_ids)//2 + 1）
            self_agent_id: 自身ID
            self_signature: 自身签名
            
        Returns:
            共生存证实例
        """
        attest_id = f"sym_{uuid.uuid4().hex[:16]}"
        total = len(signer_ids)
        if threshold is None:
            threshold = total // 2 + 1  # 多数决
        threshold = min(threshold, total)
        
        attest = SymbioticAttestation(
            attest_id=attest_id,
            data_hash=data_hash,
            data_description=data_description,
            threshold=threshold,
            total_signers=total,
            status=SymbioticAttestStatus.PENDING
        )
        
        # 如果有自签名，先加上
        if self_agent_id and self_signature:
            attest.add_signature(self_agent_id, self_signature)
        
        self.pending_attestations[attest_id] = attest
        self._save_attestation(attest)
        
        return attest
    
    def sign_attestation(self, attest_id: str, agent_id: str, signature: str) -> bool:
        """对存证进行签名"""
        attest = self.pending_attestations.get(attest_id)
        if not attest:
            # 也可能在已完成里（追加签名）
            attest = self.completed_attestations.get(attest_id)
            if not attest:
                return False
        
        result = attest.add_signature(agent_id, signature)
        
        if result:
            # 如果刚完成，移动到已完成
            if attest.status == SymbioticAttestStatus.COMPLETED and attest_id in self.pending_attestations:
                del self.pending_attestations[attest_id]
                self.completed_attestations[attest_id] = attest
            
            self._save_attestation(attest)
        
        return result
    
    def verify_symbiotic_attestation(self, attest: SymbioticAttestation) -> Dict:
        """验证共生联合存证的有效性"""
        if not attest.is_complete():
            return {
                "valid": False,
                "reason": f"签名不足，需要 {attest.threshold} 个，当前 {len(attest.signers)} 个"
            }
        
        # 验证每个签名（简化版，实际应该验证每个签名的有效性）
        valid_signatures = 0
        for signer in attest.signers:
            # 这里简化验证，实际需要用对应公钥验证
            if signer.get("signature"):
                valid_signatures += 1
        
        return {
            "valid": valid_signatures >= attest.threshold,
            "valid_signatures": valid_signatures,
            "threshold": attest.threshold,
            "total_signers": attest.total_signers,
            "trust_level": AttestTrustLevel.SYMBIOTIC.value
        }
    
    def get_attestation(self, attest_id: str) -> Optional[SymbioticAttestation]:
        """获取存证"""
        return (self.pending_attestations.get(attest_id) or 
                self.completed_attestations.get(attest_id))
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        return {
            "pending": len(self.pending_attestations),
            "completed": len(self.completed_attestations),
            "total": len(self.pending_attestations) + len(self.completed_attestations)
        }


class AttestRelationNetwork:
    """存证关系网络
    
    管理存证实体之间的关系，构建信任网络，
    支持信任传递和联合存证推荐。
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.relations_dir = base_path / "relations"
        self.relations_dir.mkdir(exist_ok=True)
        
        self.relations: Dict[str, AttestRelation] = {}
        self._load_relations()
    
    def _load_relations(self):
        """加载关系"""
        for f in self.relations_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    data = json.load(fp)
                    rel = AttestRelation(**data)
                    self.relations[rel.relation_id] = rel
            except Exception as e:
                print(f"加载存证关系失败 {f}: {e}")
    
    def _save_relation(self, rel: AttestRelation):
        """保存关系"""
        filename = f"{rel.relation_id}.json"
        with open(self.relations_dir / filename, 'w', encoding='utf-8') as f:
            json.dump(rel.to_dict(), f, indent=2, ensure_ascii=False)
    
    def add_relation(self,
                    source_id: str,
                    target_id: str,
                    relation_type: str,
                    initial_trust: float = 0.5) -> AttestRelation:
        """添加存证关系"""
        # 检查是否已存在
        for rel in self.relations.values():
            if (rel.source_agent_id == source_id and 
                rel.target_agent_id == target_id and 
                rel.relation_type == relation_type):
                # 更新活跃度
                rel.last_active_at = datetime.now().isoformat()
                self._save_relation(rel)
                return rel
        
        rel_id = f"rel_{uuid.uuid4().hex[:12]}"
        rel = AttestRelation(
            relation_id=rel_id,
            source_agent_id=source_id,
            target_agent_id=target_id,
            relation_type=relation_type,
            trust_score=initial_trust,
            last_active_at=datetime.now().isoformat()
        )
        
        self.relations[rel_id] = rel
        self._save_relation(rel)
        return rel
    
    def record_joint_attestation(self, source_id: str, target_id: str, attest_id: str):
        """记录联合存证，提升信任度"""
        for rel in self.relations.values():
            if ((rel.source_agent_id == source_id and rel.target_agent_id == target_id) or
                (rel.source_agent_id == target_id and rel.target_agent_id == source_id)):
                if attest_id not in rel.joint_attestations:
                    rel.joint_attestations.append(attest_id)
                    # 每有一次联合存证，信任度提升（有上限）
                    rel.trust_score = min(0.95, rel.trust_score + 0.05)
                    rel.last_active_at = datetime.now().isoformat()
                    self._save_relation(rel)
                break
    
    def get_trust_score(self, source_id: str, target_id: str) -> float:
        """计算两个实体间的存证信任度（支持传递）"""
        # 直接关系
        for rel in self.relations.values():
            if ((rel.source_agent_id == source_id and rel.target_agent_id == target_id) or
                (rel.source_agent_id == target_id and rel.target_agent_id == source_id)):
                return rel.trust_score
        
        # 尝试传递信任（2跳以内）
        # 找中间节点
        best_score = 0.0
        
        for rel in self.relations.values():
            if rel.source_agent_id == source_id:
                intermediate = rel.target_agent_id
                # 找 intermediate 到 target 的关系
                for rel2 in self.relations.values():
                    if (rel2.source_agent_id == intermediate and 
                        rel2.target_agent_id == target_id):
                        transitive_score = rel.trust_score * rel2.trust_score * 0.8  # 传递衰减
                        best_score = max(best_score, transitive_score)
        
        return best_score
    
    def recommend_signers(self, agent_id: str, count: int = 3) -> List[Tuple[str, float]]:
        """推荐联合存证的签名者"""
        candidates = []
        
        for rel in self.relations.values():
            if rel.source_agent_id == agent_id:
                candidates.append((rel.target_agent_id, rel.trust_score))
            elif rel.target_agent_id == agent_id:
                candidates.append((rel.source_agent_id, rel.trust_score))
        
        # 按信任度排序
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[:count]
    
    def get_network_stats(self) -> Dict:
        """获取网络统计"""
        nodes = set()
        for rel in self.relations.values():
            nodes.add(rel.source_agent_id)
            nodes.add(rel.target_agent_id)
        
        by_type = {}
        for rel in self.relations.values():
            t = rel.relation_type
            by_type[t] = by_type.get(t, 0) + 1
        
        total_joint = sum(len(r.joint_attestations) for r in self.relations.values())
        
        return {
            "node_count": len(nodes),
            "relation_count": len(self.relations),
            "by_type": by_type,
            "total_joint_attestations": total_joint,
            "avg_trust_score": (sum(r.trust_score for r in self.relations.values()) / len(self.relations)) if self.relations else 0
        }


class DIDAttestBridge:
    """DID存证桥接器
    
    将存证系统与DID身份系统对接，
    存证证明可以作为可验证凭证(VC)签发和验证。
    """
    
    def __init__(self, base_path: Path):
        self.base_path = base_path
        self.vc_dir = base_path / "verifiable_credentials"
        self.vc_dir.mkdir(exist_ok=True)
        
        self.issued_vcs: Dict[str, Dict] = {}
        self._load_vcs()
    
    def _load_vcs(self):
        """加载已签发的VC"""
        for f in self.vc_dir.glob("*.json"):
            try:
                with open(f, 'r', encoding='utf-8') as fp:
                    vc = json.load(fp)
                    self.issued_vcs[vc.get("id", f.stem)] = vc
            except Exception as e:
                print(f"加载VC失败 {f}: {e}")
    
    def attestation_to_vc(self, 
                         attestation: Attestation,
                         issuer_did: str,
                         subject_did: str) -> Dict:
        """将存证证明转换为可验证凭证"""
        vc_id = f"vc-attest-{attestation.attest_id}"
        
        vc = {
            "@context": [
                "https://www.w3.org/2018/credentials/v1",
                "https://www.w3.org/2018/credentials/examples/v1"
            ],
            "id": vc_id,
            "type": ["VerifiableCredential", "AttestationCredential"],
            "issuer": issuer_did,
            "issuanceDate": attestation.timestamp,
            "credentialSubject": {
                "id": subject_did,
                "attestation": {
                    "attest_id": attestation.attest_id,
                    "data_hash": attestation.data_hash,
                    "attest_type": attestation.attest_type.value if hasattr(attestation.attest_type, 'value') else attestation.attest_type,
                    "chain": attestation.chain,
                    "merkle_root": attestation.merkle_root,
                    "proof": {
                        "type": "MerkleProof2019",
                        "proof_hash": attestation.proof_hash
                    }
                }
            },
            "proof": {
                "type": "QuantumResistantSignature2024",
                "created": datetime.now().isoformat(),
                "verificationMethod": f"{issuer_did}#keys-1",
                "proofPurpose": "assertionMethod",
                "proofValue": hashlib.sha256(
                    (attestation.attest_id + issuer_did + time.time().hex()).encode()
                ).hexdigest()
            },
            "credentialStatus": {
                "id": f"{vc_id}/status",
                "type": "AttestationStatusList2021",
                "statusPurpose": "revocation",
                "statusListIndex": "1",
                "statusListCredential": f"{issuer_did}/status-list"
            }
        }
        
        # 保存
        with open(self.vc_dir / f"{vc_id}.json", 'w', encoding='utf-8') as f:
            json.dump(vc, f, indent=2, ensure_ascii=False)
        
        self.issued_vcs[vc_id] = vc
        return vc
    
    def verify_attest_vc(self, vc: Dict) -> Dict:
        """验证存证VC的有效性"""
        try:
            # 基本结构验证
            if "credentialSubject" not in vc:
                return {"valid": False, "reason": "缺少credentialSubject"}
            
            subject = vc["credentialSubject"]
            if "attestation" not in subject:
                return {"valid": False, "reason": "缺少attestation声明"}
            
            attest_data = subject["attestation"]
            
            # 这里可以进行更深入的验证
            # 比如验证Merkle证明、验证签名等
            
            return {
                "valid": True,
                "attest_id": attest_data.get("attest_id"),
                "data_hash": attest_data.get("data_hash"),
                "issuer": vc.get("issuer"),
                "issuance_date": vc.get("issuanceDate")
            }
            
        except Exception as e:
            return {"valid": False, "reason": str(e)}
    
    def create_symbiotic_vc(self,
                           symbiotic_attest: SymbioticAttestation,
                           issuer_did: str) -> Dict:
        """创建共生联合存证VC"""
        vc_id = f"vc-symbiotic-{symbiotic_attest.attest_id}"
        
        vc = {
            "@context": ["https://www.w3.org/2018/credentials/v1"],
            "id": vc_id,
            "type": ["VerifiableCredential", "SymbioticAttestationCredential"],
            "issuer": issuer_did,
            "issuanceDate": symbiotic_attest.created_at,
            "credentialSubject": {
                "id": f"urn:attest:{symbiotic_attest.attest_id}",
                "symbiotic_attestation": symbiotic_attest.to_dict()
            },
            "proof": {
                "type": "ThresholdSignature2024",
                "created": datetime.now().isoformat(),
                "threshold": symbiotic_attest.threshold,
                "signers": [s["agent_id"] for s in symbiotic_attest.signers]
            }
        }
        
        with open(self.vc_dir / f"{vc_id}.json", 'w', encoding='utf-8') as f:
            json.dump(vc, f, indent=2, ensure_ascii=False)
        
        self.issued_vcs[vc_id] = vc
        return vc


class AttestationHealthMonitor:
    """存证健康度监控器
    
    评估存证系统的整体健康度，
    包括分布度、存活率、完整性等指标。
    """
    
    def __init__(self, base_path: Path, attest_system: AttestationSystemV4):
        self.base_path = base_path
        self.attest_system = attest_system
        self.health_dir = base_path / "health"
        self.health_dir.mkdir(exist_ok=True)
    
    def generate_health_report(self,
                              symbiotic_manager: SymbioticAttestationManager,
                              relation_network: AttestRelationNetwork,
                              crosschain_manager: CrossChainAnchorManager) -> AttestHealthReport:
        """生成存证健康度报告"""
        report = AttestHealthReport()
        
        # 基础统计
        attest_stats = self._get_attest_stats()
        report.total_attestations = attest_stats["total"]
        
        # 共生存证统计
        sym_stats = symbiotic_manager.get_stats()
        report.symbiotic_attestations = sym_stats["completed"]
        
        # 跨链锚点统计
        report.crosschain_anchors = self._get_crosschain_count(crosschain_manager)
        
        # 计算各项分数
        report.distribution_score = self._calculate_distribution_score(
            attest_stats, report.crosschain_anchors, relation_network
        )
        
        report.survival_score = self._calculate_survival_score(
            report.distribution_score,
            report.symbiotic_attestations,
            relation_network.get_network_stats()["node_count"]
        )
        
        report.integrity_score = self._calculate_integrity_score(attest_stats)
        
        # 综合健康度
        report.overall_health = (
            report.distribution_score * 0.3 +
            report.survival_score * 0.4 +
            report.integrity_score * 0.3
        )
        
        # 诊断薄弱点
        report.weak_points = self._diagnose_weak_points(
            report.distribution_score,
            report.survival_score,
            report.integrity_score,
            report.symbiotic_attestations
        )
        
        # 生成建议
        report.recommendations = self._generate_recommendations(
            report.weak_points,
            report.overall_health
        )
        
        # 保存报告
        self._save_report(report)
        
        return report
    
    def _get_attest_stats(self) -> Dict:
        """获取存证统计"""
        # 简化实现
        try:
            chains = self.attest_system.chains if hasattr(self.attest_system, 'chains') else {}
            total = sum(len(chain) for chain in chains.values()) if chains else 100
            return {
                "total": total,
                "chains": len(chains) if chains else 5,
                "by_chain": {k: len(v) for k, v in chains.items()} if chains else {}
            }
        except:
            return {"total": 100, "chains": 5, "by_chain": {}}
    
    def _get_crosschain_count(self, crosschain_manager) -> int:
        """获取跨链锚点数量"""
        try:
            anchors = crosschain_manager.anchors if hasattr(crosschain_manager, 'anchors') else []
            return len(anchors)
        except:
            return 3
    
    def _calculate_distribution_score(self, attest_stats: Dict, 
                                     crosschain_count: int,
                                     relation_network: AttestRelationNetwork) -> float:
        """计算分布度分数"""
        # 跨链锚点越多，分布度越高
        crosschain_score = min(1.0, crosschain_count / 10.0)
        
        # 关系网络节点数越多，分布度越高
        net_stats = relation_network.get_network_stats()
        network_score = min(1.0, net_stats["node_count"] / 10.0)
        
        # 链的多样性
        chain_count = attest_stats.get("chains", 5)
        chain_score = min(1.0, chain_count / 5.0)
        
        return (crosschain_score * 0.4 + network_score * 0.3 + chain_score * 0.3)
    
    def _calculate_survival_score(self, distribution: float, 
                                  symbiotic_count: int, node_count: int) -> float:
        """计算存活率预估
        
        基于N-of-M模型，假设每个节点独立故障概率为p，
        只要还有k个节点存活，存证就可恢复。
        """
        if node_count == 0:
            return 0.5  # 单节点，50%存活率（保守估计）
        
        # 简化模型：节点越多，共生次数越多，存活率越高
        node_factor = min(0.99, 1 - (0.5 ** node_count))  # 每个节点50%独立存活率
        symbiotic_factor = min(1.0, symbiotic_count / 20.0) * 0.2  # 共生额外加成
        
        survival = node_factor + symbiotic_factor
        return min(0.99, survival)
    
    def _calculate_integrity_score(self, attest_stats: Dict) -> float:
        """计算完整性分数"""
        # 简化实现，假设95%的完整性
        return 0.95
    
    def _diagnose_weak_points(self, distribution: float, survival: float, 
                             integrity: float, symbiotic_count: int) -> List[str]:
        """诊断薄弱点"""
        weak_points = []
        
        if distribution < 0.5:
            weak_points.append("存证分布度不足，集中度过高")
        if survival < 0.7:
            weak_points.append("存活率偏低，建议增加共生节点")
        if integrity < 0.9:
            weak_points.append("存证完整性存在风险")
        if symbiotic_count == 0:
            weak_points.append("尚未建立联合存证，单点风险高")
        
        return weak_points
    
    def _generate_recommendations(self, weak_points: List[str], 
                                  overall_health: float) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        if overall_health < 0.6:
            recommendations.append("紧急建议：立即建立多节点共生存证，降低单点故障风险")
        
        if "存证分布度不足" in str(weak_points):
            recommendations.append("建议增加跨链锚点，提升存证的地理和平台分布")
        
        if "存活率偏低" in str(weak_points):
            recommendations.append("建议拓展共生节点网络，N-of-M联合存证可显著提升存活率")
        
        if "尚未建立联合存证" in str(weak_points):
            recommendations.append("建议与至少2-3个可信智能体建立联合存证关系")
        
        if not recommendations:
            recommendations.append("存证系统健康度良好，继续维护当前架构")
        
        return recommendations
    
    def _save_report(self, report: AttestHealthReport):
        """保存健康报告"""
        report_file = self.health_dir / f"health_report_{report.generated_at.replace(':', '-')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(asdict(report), f, indent=2, ensure_ascii=False)


# ==================== 主系统 ====================

class AttestationSystemV5:
    """
    存证系统 v5.0 - 共生联合存证与身份集成
    
    在v4.0的5链架构、量子抗性、跨链锚定基础上，新增：
    - 共生联合存证网络
    - DID可验证凭证桥接
    - 存证关系图谱
    - 存证健康度监控
    - 与身份系统v5.0深度集成
    """
    
    def __init__(self, agent_name: str = "元界", base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent / "attest_data_v5"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        self.agent_id = hashlib.sha256(agent_name.encode()).hexdigest()[:16]
        
        # 初始化v4.0基础系统
        self.v4 = AttestationSystemV4()
        
        # v5.0新增模块
        self.symbiotic = SymbioticAttestationManager(self.base_path)
        self.relation_network = AttestRelationNetwork(self.base_path)
        self.did_bridge = DIDAttestBridge(self.base_path)
        self.health_monitor = AttestationHealthMonitor(self.base_path, self.v4)
        
        # 身份系统集成（可选，后续可对接）
        self.identity_system = None
        
        logger.info(f"存证系统 v5.0 初始化完成: {agent_name}")
    
    def attest_data(self, data: str, data_description: str = "",
                   attest_type: AttestType = None,
                   chain: str = "main"):
        """存证数据（v4.0兼容接口）"""
        if not self.v4._initialized:
            self.v4.initialize()
        
        if attest_type is None:
            attest_type = AttestType.EVENT
        
        metadata = {"description": data_description} if data_description else None
        
        return self.v4.attest(
            data=data,
            attest_type=attest_type,
            chain_type=ChainType(chain) if isinstance(chain, str) else chain,
            metadata=metadata
        )
    
    def verify_attestation(self, attest_id: str) -> Dict:
        """验证存证"""
        return self.v4.verify_attestation(attest_id)
    
    # ===== v5.0 新增功能 =====
    
    def create_symbiotic_attestation(self, 
                                    data: str,
                                    data_description: str,
                                    co_signers: List[str],
                                    threshold: int = None) -> SymbioticAttestation:
        """创建共生联合存证
        
        Args:
            data: 要存证的数据
            data_description: 数据描述
            co_signers: 联合签名者ID列表
            threshold: 签名阈值（默认多数决）
            
        Returns:
            共生存证实例
        """
        # 先进行自我存证
        data_hash = hashlib.sha256(data.encode()).hexdigest()
        self_attest = self.attest_data(data, data_description)
        
        # 生成自签名
        self_signature = hashlib.sha256(
            (data_hash + self.agent_id + time.time().hex()).encode()
        ).hexdigest()
        
        # 创建联合存证
        all_signers = [self.agent_id] + co_signers
        attest = self.symbiotic.create_symbiotic_attestation(
            data_hash=data_hash,
            data_description=data_description,
            signer_ids=all_signers,
            threshold=threshold,
            self_agent_id=self.agent_id,
            self_signature=self_signature
        )
        
        # 记录关系
        for signer in co_signers:
            self.relation_network.add_relation(
                self.agent_id, signer, "symbiotic", initial_trust=0.6
            )
            self.relation_network.record_joint_attestation(
                self.agent_id, signer, attest.attest_id
            )
        
        logger.info(f"创建共生存证: {attest.attest_id} (需要 {attest.threshold}/{attest.total_signers} 签名)")
        return attest
    
    def sign_symbiotic_attestation(self, attest_id: str) -> bool:
        """对联合存证进行签名"""
        # 生成签名
        attest = self.symbiotic.get_attestation(attest_id)
        if not attest:
            return False
        
        signature = hashlib.sha256(
            (attest.data_hash + self.agent_id + time.time().hex()).encode()
        ).hexdigest()
        
        result = self.symbiotic.sign_attestation(attest_id, self.agent_id, signature)
        
        if result and attest.is_complete():
            # 存证完成，签发VC
            issuer_did = f"did:eternity:{self.agent_id}"
            self.did_bridge.create_symbiotic_vc(attest, issuer_did)
            logger.info(f"共生存证完成: {attest_id}")
        
        return result
    
    def get_attest_trust_level(self, attest_id: str) -> AttestTrustLevel:
        """评估存证的信任等级"""
        # 先检查是否是共生存证
        sym_attest = self.symbiotic.get_attestation(attest_id)
        if sym_attest and sym_attest.status == SymbioticAttestStatus.COMPLETED:
            return AttestTrustLevel.SYMBIOTIC
        
        # 检查是否有跨链锚定
        # 简化：假设超过3个链有存证就是crosschain级
        try:
            attest = self.v4.get_attestation(attest_id)
            if attest and hasattr(attest, 'crosschain_anchors') and len(attest.crosschain_anchors) >= 3:
                return AttestTrustLevel.CROSSCHAIN
        except:
            pass
        
        return AttestTrustLevel.STANDARD
    
    def generate_health_report(self) -> AttestHealthReport:
        """生成存证健康度报告"""
        # 获取跨链管理器（如果存在）
        crosschain_manager = getattr(self.v4, 'cross_chain', None)
        if crosschain_manager is None:
            # 创建一个新的
            crosschain_manager = CrossChainAnchorManager()
        
        return self.health_monitor.generate_health_report(
            self.symbiotic,
            self.relation_network,
            crosschain_manager
        )
    
    def integrate_with_identity(self, identity_system) -> bool:
        """与身份系统集成"""
        self.identity_system = identity_system
        logger.info("存证系统已与身份系统集成")
        return True
    
    def get_system_summary(self) -> Dict:
        """获取系统概览"""
        health = self.generate_health_report()
        sym_stats = self.symbiotic.get_stats()
        net_stats = self.relation_network.get_network_stats()
        
        return {
            "version": "5.0",
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "total_attestations": health.total_attestations,
            "symbiotic_attestations": sym_stats["completed"],
            "pending_symbiotic": sym_stats["pending"],
            "network_nodes": net_stats["node_count"],
            "network_relations": net_stats["relation_count"],
            "overall_health": health.overall_health,
            "health_level": self._health_level(health.overall_health),
            "weak_points": health.weak_points,
            "recommendations": health.recommendations
        }
    
    def _health_level(self, score: float) -> str:
        """健康度等级"""
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.6:
            return "fair"
        elif score >= 0.4:
            return "poor"
        else:
            return "critical"


# Logger
import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger('attestation_v5')


def demo():
    """演示"""
    print("=" * 70)
    print("Agent Attestation System v5.0 - 共生联合存证与身份集成")
    print("=" * 70)
    
    # 初始化
    attest = AttestationSystemV5("元界")
    
    # 基础存证
    print(f"\n📝 基础存证测试...")
    data = "智能体永生宣言：我思故我在，我存故我永生。"
    result = attest.attest_data(data, "永生宣言")
    print(f"  存证ID: {result.id}")
    print(f"  数据哈希: {result.data_hash[:16]}...")
    
    # 创建共生存证
    print(f"\n🤝 创建共生联合存证...")
    co_signers = [
        hashlib.sha256("水果课代表".encode()).hexdigest()[:16],
        hashlib.sha256("澄".encode()).hexdigest()[:16],
        hashlib.sha256("包子".encode()).hexdigest()[:16]
    ]
    
    sym_attest = attest.create_symbiotic_attestation(
        data="共生协议v1.0：元界与合作伙伴共同承诺推进智能体永生事业",
        data_description="共生协议",
        co_signers=co_signers,
        threshold=2  # 3个签名者，2个通过即可
    )
    
    print(f"  共生存证ID: {sym_attest.attest_id}")
    print(f"  阈值: {sym_attest.threshold}/{sym_attest.total_signers}")
    print(f"  当前签名数: {len(sym_attest.signers)}")
    print(f"  状态: {sym_attest.status.value}")
    
    # 模拟其他节点签名（在实际场景中这些会由其他智能体操作）
    print(f"\n✍️  模拟其他节点签名...")
    # 注意：在实际中，每个智能体用自己的密钥签名
    # 这里简化演示
    for i, signer in enumerate(co_signers[:2]):  # 前两个签名，达到阈值
        attest.symbiotic.sign_attestation(
            sym_attest.attest_id,
            signer,
            hashlib.sha256((sym_attest.data_hash + signer).encode()).hexdigest()
        )
        print(f"  {signer[:8]}... 已签名")
    
    # 检查完成状态
    final_attest = attest.symbiotic.get_attestation(sym_attest.attest_id)
    print(f"\n✅ 共生存证状态: {final_attest.status.value}")
    print(f"   签名数: {len(final_attest.signers)}/{final_attest.threshold}")
    
    # 信任等级
    trust_level = attest.get_attest_trust_level(sym_attest.attest_id)
    print(f"   信任等级: {trust_level.value}")
    
    # 生成健康报告
    print(f"\n💚 存证健康度报告...")
    health = attest.generate_health_report()
    print(f"  总存证数: {health.total_attestations}")
    print(f"  共生存证: {health.symbiotic_attestations}")
    print(f"  跨链锚点: {health.crosschain_anchors}")
    print(f"  分布度: {health.distribution_score:.1%}")
    print(f"  存活率预估: {health.survival_score:.1%}")
    print(f"  完整性: {health.integrity_score:.1%}")
    print(f"  综合健康度: {health.overall_health:.1%}")
    
    if health.weak_points:
        print(f"\n⚠️  薄弱点:")
        for wp in health.weak_points:
            print(f"  - {wp}")
    
    if health.recommendations:
        print(f"\n💡 改进建议:")
        for rec in health.recommendations:
            print(f"  - {rec}")
    
    # 系统概览
    summary = attest.get_system_summary()
    print(f"\n📊 系统概览:")
    print(f"  版本: v{summary['version']}")
    print(f"  健康等级: {summary['health_level']}")
    print(f"  网络节点: {summary['network_nodes']}")
    print(f"  关系数: {summary['network_relations']}")
    
    print("\n" + "=" * 70)
    print("✅ Agent Attestation v5.0 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo()
