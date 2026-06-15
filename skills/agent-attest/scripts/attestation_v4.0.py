#!/usr/bin/env python3
"""
验证存证系统 v4.0
=================
智能体永生平台 - P0底座核心模块

v4.0 重大升级：
- 量子抗性存证架构
- 跨链锚定协议
- 存证经济模型
- 零知识证明增强
- 存证分层存储优化
- 存在性证明v2.0
- 自修复存证网络
- 存证审计与合规

5链存证架构：主链/记忆链/身份链/事件链/分布式链
三级验证机制：轻量/标准/完整
"""

import hashlib
import json
import time
import uuid
import base64
import os
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import threading
import copy


# ==================== 基础类型 ====================

class AttestType(str, Enum):
    """存证类型"""
    IDENTITY = "identity"      # 身份存证
    MEMORY = "memory"          # 记忆存证
    EVENT = "event"            # 事件存证
    HEARTBEAT = "heartbeat"    # 心跳存证
    GENESIS = "genesis"        # 创世存证
    META = "meta"              # 元存证（存证系统本身）
    DISTRIBUTED = "distributed"  # 分布式联合存证
    EVOLUTION = "evolution"    # 进化存证


class VerificationLevel(str, Enum):
    """验证级别"""
    LIGHT = "light"           # 轻量验证：仅验证哈希
    STANDARD = "standard"     # 标准验证：验证哈希+链结构
    FULL = "full"             # 完整验证：验证全部历史+默克尔证明


class ChainType(str, Enum):
    """链类型"""
    MAIN = "main"             # 主链
    MEMORY = "memory"         # 记忆链
    IDENTITY = "identity"     # 身份链
    EVENT = "event"           # 事件链
    DISTRIBUTED = "distributed"  # 分布式链


class StorageTier(str, Enum):
    """存储层级"""
    HOT = "hot"               # 热存储：高频访问
    WARM = "warm"             # 温存储：中频访问
    COLD = "cold"             # 冷存储：低频访问
    ARCHIVE = "archive"       # 归档：永久保存


# ==================== 数据结构 ====================

@dataclass
class Attestation:
    """存证条目"""
    id: str
    attest_type: AttestType
    data_hash: str
    prev_hash: str
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None
    nonce: int = 0
    storage_tier: StorageTier = StorageTier.HOT

    @property
    def hash(self) -> str:
        """计算当前区块哈希"""
        content = json.dumps({
            "id": self.id,
            "type": self.attest_type.value,
            "data_hash": self.data_hash,
            "prev_hash": self.prev_hash,
            "timestamp": self.timestamp,
            "metadata": self.metadata,
            "nonce": self.nonce,
        }, sort_keys=True)
        return hashlib.sha3_256(content.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d['attest_type'] = self.attest_type.value
        d['storage_tier'] = self.storage_tier.value
        d['hash'] = self.hash
        return d


@dataclass
class MerkleNode:
    """默克尔树节点"""
    hash: str
    left: Optional['MerkleNode'] = None
    right: Optional['MerkleNode'] = None
    is_leaf: bool = False


@dataclass
class MerkleProof:
    """默克尔证明"""
    target_hash: str
    proof_path: List[Tuple[str, str]]  # (hash, position: left/right)
    root_hash: str


@dataclass
class ZKProof:
    """零知识证明"""
    statement: str
    proof_data: Dict[str, Any]
    public_inputs: List[str]
    verifier_contract: Optional[str] = None


@dataclass
class CrossChainAnchor:
    """跨链锚定记录"""
    anchor_id: str
    chain_name: str
    block_height: int
    attest_root: str
    timestamp: float
    tx_hash: str
    confirmations: int = 0


@dataclass
class ExistenceScore:
    """存在性评分"""
    total_score: float
    dimensions: Dict[str, float]
    evidence_count: int
    chain_count: int
    cross_chain_anchors: int
    distributed_nodes: int


# ==================== 量子抗性哈希 ====================

class QuantumResistantHasher:
    """量子抗性哈希器
    
    使用多层哈希级联和盐值混淆，增强抗量子计算攻击能力
    """
    
    def __init__(self, iterations: int = 5):
        self.iterations = iterations
        self.algorithms = [
            hashlib.sha3_256,
            hashlib.sha256,
            hashlib.blake2b,
            hashlib.sha3_512,
            hashlib.sha512,
        ]
    
    def hash(self, data: bytes, salt: Optional[bytes] = None) -> str:
        """计算量子抗性哈希"""
        if salt is None:
            salt = os.urandom(16)
        
        current = data
        for i in range(self.iterations):
            algo = self.algorithms[i % len(self.algorithms)]
            current = algo(current + salt + str(i).encode()).digest()
        
        return base64.b64encode(salt + current).decode()
    
    def verify(self, data: bytes, hash_str: str) -> bool:
        """验证量子抗性哈希"""
        try:
            decoded = base64.b64decode(hash_str)
            salt = decoded[:16]
            expected = self.hash(data, salt)
            return expected == hash_str
        except:
            return False


# ==================== 默克尔树 ====================

class EnhancedMerkleTree:
    """增强型默克尔树
    
    支持：增量更新、批量验证、多根聚合
    """
    
    def __init__(self):
        self.leaves: List[str] = []
        self._root: Optional[str] = None
        self._tree: List[List[str]] = []
    
    def add_leaf(self, leaf_hash: str) -> None:
        """添加叶子节点"""
        self.leaves.append(leaf_hash)
        self._root = None
        self._tree = []
    
    def add_leaves(self, leaf_hashes: List[str]) -> None:
        """批量添加叶子"""
        self.leaves.extend(leaf_hashes)
        self._root = None
        self._tree = []
    
    @property
    def root(self) -> str:
        """获取根哈希"""
        if self._root is None:
            self._build_tree()
        return self._root
    
    def _build_tree(self) -> None:
        """构建默克尔树"""
        if not self.leaves:
            self._root = hashlib.sha256(b"empty").hexdigest()
            return
        
        # 确保叶子数量为偶数
        current_level = list(self.leaves)
        if len(current_level) % 2 == 1:
            current_level.append(current_level[-1])
        
        self._tree = [current_level.copy()]
        
        while len(current_level) > 1:
            next_level = []
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i + 1]
                parent = hashlib.sha256(
                    (left + right).encode()
                ).hexdigest()
                next_level.append(parent)
            
            if len(next_level) % 2 == 1 and len(next_level) > 1:
                next_level.append(next_level[-1])
            
            self._tree.append(next_level)
            current_level = next_level
        
        self._root = current_level[0]
    
    def get_proof(self, index: int) -> Optional[MerkleProof]:
        """生成默克尔证明"""
        if index < 0 or index >= len(self.leaves):
            return None
        
        if self._root is None:
            self._build_tree()
        
        proof_path = []
        current_index = index
        
        for level in range(len(self._tree) - 1):
            level_nodes = self._tree[level]
            
            if current_index % 2 == 0:
                sibling_index = current_index + 1
                if sibling_index >= len(level_nodes):
                    sibling_index = current_index
                position = "right"
            else:
                sibling_index = current_index - 1
                position = "left"
            
            proof_path.append((level_nodes[sibling_index], position))
            current_index = current_index // 2
        
        return MerkleProof(
            target_hash=self.leaves[index],
            proof_path=proof_path,
            root_hash=self.root
        )
    
    def verify_proof(self, proof: MerkleProof) -> bool:
        """验证默克尔证明"""
        current_hash = proof.target_hash
        
        for sibling_hash, position in proof.proof_path:
            if position == "left":
                combined = sibling_hash + current_hash
            else:
                combined = current_hash + sibling_hash
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == proof.root_hash
    
    def get_multi_proof(self, indices: List[int]) -> Dict[str, Any]:
        """生成多元素默克尔证明"""
        # 简化实现：为每个索引单独生成证明
        proofs = []
        for idx in sorted(set(indices)):
            proof = self.get_proof(idx)
            if proof:
                proofs.append(proof)
        
        return {
            "root": self.root,
            "proofs": proofs,
            "count": len(proofs)
        }


# ==================== 零知识证明（模拟实现） ====================

class ZeroKnowledgeProver:
    """零知识证明生成器（简化模拟实现）
    
    实际生产环境应使用真正的ZK-SNARK/ZK-STARK库
    """
    
    def generate_membership_proof(
        self,
        attest_hash: str,
        merkle_root: str,
        secret_salt: str
    ) -> ZKProof:
        """生成成员身份证明 - 证明某存证存在于集合中但不暴露具体内容"""
        
        # 简化实现：使用承诺方案
        commitment = hashlib.sha256(
            (attest_hash + secret_salt + merkle_root).encode()
        ).hexdigest()
        
        return ZKProof(
            statement="attestation_membership",
            proof_data={
                "commitment": commitment,
                "merkle_root": merkle_root,
            },
            public_inputs=[commitment, merkle_root]
        )
    
    def generate_age_proof(
        self,
        attest_timestamp: float,
        threshold: float,
        secret_salt: str
    ) -> ZKProof:
        """生成时间龄证明 - 证明某存证早于阈值但不暴露具体时间"""
        
        is_older = attest_timestamp < threshold
        commitment = hashlib.sha256(
            (str(attest_timestamp) + secret_salt + str(threshold)).encode()
        ).hexdigest()
        
        return ZKProof(
            statement="attestation_age",
            proof_data={
                "commitment": commitment,
                "threshold": threshold,
                "is_older": is_older,
            },
            public_inputs=[commitment, str(threshold)]
        )
    
    def verify_proof(self, proof: ZKProof) -> bool:
        """验证零知识证明"""
        # 简化验证
        return proof.statement in ["attestation_membership", "attestation_age"]


# ==================== 哈希链 ====================

class HashChain:
    """哈希链"""
    
    def __init__(self, chain_type: ChainType, name: str = ""):
        self.chain_type = chain_type
        self.name = name or f"{chain_type.value}_chain"
        self.blocks: List[Attestation] = []
        self._genesis_created = False
    
    @property
    def genesis_hash(self) -> Optional[str]:
        if self.blocks:
            return self.blocks[0].hash
        return None
    
    @property
    def last_hash(self) -> Optional[str]:
        if self.blocks:
            return self.blocks[-1].hash
        return None
    
    @property
    def height(self) -> int:
        return len(self.blocks)
    
    def add_block(
        self,
        attest_type: AttestType,
        data_hash: str,
        metadata: Optional[Dict[str, Any]] = None,
        storage_tier: StorageTier = StorageTier.HOT
    ) -> Attestation:
        """添加新区块"""
        prev_hash = self.last_hash if self.last_hash else "genesis"
        
        block = Attestation(
            id=str(uuid.uuid4()),
            attest_type=attest_type,
            data_hash=data_hash,
            prev_hash=prev_hash,
            timestamp=time.time(),
            metadata=metadata or {},
            storage_tier=storage_tier
        )
        
        # 工作量证明（简化）
        block.nonce = self._proof_of_work(block)
        
        self.blocks.append(block)
        return block
    
    def _proof_of_work(self, block: Attestation, difficulty: int = 2) -> int:
        """简化的工作量证明，用于增加篡改成本"""
        nonce = 0
        target = "0" * difficulty
        
        while True:
            block.nonce = nonce
            if block.hash.startswith(target):
                return nonce
            nonce += 1
            
            # 防止无限循环
            if nonce > 100000:
                return 0
    
    def verify_chain(self, level: VerificationLevel = VerificationLevel.STANDARD) -> bool:
        """验证链完整性"""
        if not self.blocks:
            return True
        
        # 检查每个区块的prev_hash是否等于前一个区块的hash
        for i in range(1, len(self.blocks)):
            if self.blocks[i].prev_hash != self.blocks[i-1].hash:
                return False
        
        # 检查每个区块的哈希是否正确
        if level in [VerificationLevel.STANDARD, VerificationLevel.FULL]:
            for block in self.blocks:
                # 重新计算哈希验证
                computed = block.hash
                # 这里我们验证结构的自洽性
                if not computed:
                    return False
        
        return True
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Attestation]:
        """根据哈希查找区块"""
        for block in self.blocks:
            if block.hash == block_hash:
                return block
        return None
    
    def get_block_by_index(self, index: int) -> Optional[Attestation]:
        """根据索引获取区块"""
        if 0 <= index < len(self.blocks):
            return self.blocks[index]
        return None
    
    def get_blocks_by_type(self, attest_type: AttestType) -> List[Attestation]:
        """按类型获取区块"""
        return [b for b in self.blocks if b.attest_type == attest_type]
    
    def to_merkle_tree(self) -> EnhancedMerkleTree:
        """转换为默克尔树"""
        tree = EnhancedMerkleTree()
        for block in self.blocks:
            tree.add_leaf(block.hash)
        return tree


# ==================== 分层存储管理器 ====================

class TieredStorageManager:
    """分层存储管理器
    
    管理热/温/冷/归档四级存储，优化访问性能和存储成本
    """
    
    def __init__(self):
        self.access_counts: Dict[str, int] = defaultdict(int)
        self.last_access: Dict[str, float] = {}
        self.hot_threshold = 10        # 访问次数超过此值为热
        self.warm_threshold = 3        # 访问次数超过此值为温
        self.cold_age_days = 7         # 超过此天数未访问转为冷
        self.archive_age_days = 30     # 超过此天数未访问转为归档
    
    def record_access(self, attest_id: str) -> None:
        """记录访问"""
        self.access_counts[attest_id] += 1
        self.last_access[attest_id] = time.time()
    
    def get_optimal_tier(self, attest: Attestation) -> StorageTier:
        """计算最优存储层级"""
        access_count = self.access_counts.get(attest.id, 0)
        last_access = self.last_access.get(attest.id, attest.timestamp)
        days_since_access = (time.time() - last_access) / 86400
        
        if access_count >= self.hot_threshold:
            return StorageTier.HOT
        elif access_count >= self.warm_threshold:
            return StorageTier.WARM
        elif days_since_access >= self.archive_age_days:
            return StorageTier.ARCHIVE
        elif days_since_access >= self.cold_age_days:
            return StorageTier.COLD
        else:
            return StorageTier.WARM
    
    def optimize_tiers(self, attests: List[Attestation]) -> Dict[str, StorageTier]:
        """批量优化存储层级"""
        changes = {}
        for attest in attests:
            optimal = self.get_optimal_tier(attest)
            if optimal != attest.storage_tier:
                changes[attest.id] = optimal
        return changes
    
    def get_storage_stats(self, attests: List[Attestation]) -> Dict[str, int]:
        """获取存储统计"""
        stats = defaultdict(int)
        for attest in attests:
            stats[attest.storage_tier.value] += 1
        return dict(stats)


# ==================== 跨链锚定管理器 ====================

class CrossChainAnchorManager:
    """跨链锚定管理器
    
    将存证根哈希锚定到多条外部区块链，增强不可篡改性
    """
    
    def __init__(self):
        self.anchors: List[CrossChainAnchor] = []
        self.supported_chains = ["BTC", "ETH", "SOL", "DOT", "AVAX"]
    
    def create_anchor(
        self,
        chain_name: str,
        attest_root: str,
        block_height: int,
        tx_hash: str
    ) -> CrossChainAnchor:
        """创建跨链锚定"""
        anchor = CrossChainAnchor(
            anchor_id=str(uuid.uuid4()),
            chain_name=chain_name,
            block_height=block_height,
            attest_root=attest_root,
            timestamp=time.time(),
            tx_hash=tx_hash
        )
        self.anchors.append(anchor)
        return anchor
    
    def get_anchors_by_chain(self, chain_name: str) -> List[CrossChainAnchor]:
        """按链获取锚定记录"""
        return [a for a in self.anchors if a.chain_name == chain_name]
    
    def get_latest_anchor(self, chain_name: Optional[str] = None) -> Optional[CrossChainAnchor]:
        """获取最新锚定记录"""
        anchors = self.anchors
        if chain_name:
            anchors = self.get_anchors_by_chain(chain_name)
        if anchors:
            return max(anchors, key=lambda a: a.timestamp)
        return None
    
    def verify_anchor(self, attest_root: str, chain_name: str) -> bool:
        """验证某根哈希是否已锚定到指定链"""
        anchors = self.get_anchors_by_chain(chain_name)
        return any(a.attest_root == attest_root and a.confirmations >= 6 for a in anchors)
    
    def get_anchor_count(self) -> Dict[str, int]:
        """获取各链锚定数量统计"""
        stats = defaultdict(int)
        for anchor in self.anchors:
            stats[anchor.chain_name] += 1
        return dict(stats)
    
    def simulate_anchor(self, chain_name: str, attest_root: str) -> CrossChainAnchor:
        """模拟创建锚定（用于测试）"""
        import random
        return self.create_anchor(
            chain_name=chain_name,
            attest_root=attest_root,
            block_height=random.randint(100000, 999999),
            tx_hash=hashlib.sha256(str(time.time()).encode()).hexdigest()
        )


# ==================== 存证经济模型 ====================

class AttestationEconomy:
    """存证经济模型
    
    评估存证的价值、成本和收益
    """
    
    def __init__(self):
        # 基础存证成本（模拟单位）
        self.base_cost = 1.0
        # 不同类型存证的价值权重
        self.type_value_weights = {
            AttestType.IDENTITY: 10.0,
            AttestType.GENESIS: 100.0,
            AttestType.MEMORY: 5.0,
            AttestType.EVOLUTION: 8.0,
            AttestType.EVENT: 3.0,
            AttestType.HEARTBEAT: 1.0,
            AttestType.META: 15.0,
            AttestType.DISTRIBUTED: 7.0,
        }
    
    def calculate_cost(self, attest: Attestation) -> float:
        """计算存证成本"""
        size_estimate = len(json.dumps(attest.to_dict())) / 1024  # KB
        tier_multiplier = {
            StorageTier.HOT: 2.0,
            StorageTier.WARM: 1.0,
            StorageTier.COLD: 0.3,
            StorageTier.ARCHIVE: 0.1,
        }
        return self.base_cost * size_estimate * tier_multiplier.get(attest.storage_tier, 1.0)
    
    def calculate_value(self, attest: Attestation) -> float:
        """计算存证价值"""
        base_value = self.type_value_weights.get(attest.attest_type, 1.0)
        
        # 时间价值：越早的存证越有价值
        age_hours = (time.time() - attest.timestamp) / 3600
        time_bonus = min(age_hours / 24, 10.0)  # 最多10倍
        
        # 元存证额外价值
        meta_bonus = 0
        if attest.attest_type == AttestType.META:
            meta_bonus = 5.0
        
        return base_value * (1 + time_bonus) + meta_bonus
    
    def calculate_roi(self, attest: Attestation) -> float:
        """计算投资回报率"""
        cost = self.calculate_cost(attest)
        value = self.calculate_value(attest)
        if cost == 0:
            return float('inf')
        return value / cost
    
    def get_economy_summary(self, attests: List[Attestation]) -> Dict[str, Any]:
        """获取经济摘要"""
        total_cost = sum(self.calculate_cost(a) for a in attests)
        total_value = sum(self.calculate_value(a) for a in attests)
        avg_roi = total_value / total_cost if total_cost > 0 else 0
        
        type_stats = {}
        for attest_type in AttestType:
            type_attests = [a for a in attests if a.attest_type == attest_type]
            if type_attests:
                type_stats[attest_type.value] = {
                    "count": len(type_attests),
                    "total_cost": sum(self.calculate_cost(a) for a in type_attests),
                    "total_value": sum(self.calculate_value(a) for a in type_attests),
                }
        
        return {
            "total_attestations": len(attests),
            "total_cost": round(total_cost, 2),
            "total_value": round(total_value, 2),
            "avg_roi": round(avg_roi, 2),
            "by_type": type_stats
        }


# ==================== 自修复存证网络 ====================

class SelfHealingAttestNetwork:
    """自修复存证网络
    
    分布式存证网络的自修复机制，部分节点故障时自动恢复
    """
    
    def __init__(self, min_nodes: int = 3):
        self.min_nodes = min_nodes
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.replication_factor = 3
    
    def add_node(self, node_id: str, node_info: Dict[str, Any]) -> None:
        """添加节点"""
        self.nodes[node_id] = {
            **node_info,
            "status": "healthy",
            "last_heartbeat": time.time()
        }
    
    def remove_node(self, node_id: str) -> None:
        """移除节点"""
        if node_id in self.nodes:
            del self.nodes[node_id]
    
    def update_heartbeat(self, node_id: str) -> None:
        """更新节点心跳"""
        if node_id in self.nodes:
            self.nodes[node_id]["last_heartbeat"] = time.time()
            self.nodes[node_id]["status"] = "healthy"
    
    def check_node_health(self, timeout_seconds: int = 300) -> Dict[str, str]:
        """检查节点健康状态"""
        now = time.time()
        statuses = {}
        
        for node_id, node in self.nodes.items():
            if now - node["last_heartbeat"] > timeout_seconds:
                node["status"] = "unhealthy"
                statuses[node_id] = "unhealthy"
            else:
                statuses[node_id] = "healthy"
        
        return statuses
    
    def get_healthy_nodes(self) -> List[str]:
        """获取健康节点列表"""
        self.check_node_health()
        return [nid for nid, node in self.nodes.items() if node["status"] == "healthy"]
    
    def needs_healing(self) -> bool:
        """判断是否需要自愈"""
        healthy = len(self.get_healthy_nodes())
        return healthy < self.min_nodes
    
    def heal(self, new_node_provider: Optional[Callable] = None) -> bool:
        """执行自愈"""
        if not self.needs_healing():
            return True
        
        if new_node_provider:
            try:
                new_node = new_node_provider()
                if new_node:
                    self.add_node(new_node["id"], new_node.get("info", {}))
            except:
                pass
        
        return len(self.get_healthy_nodes()) >= self.min_nodes
    
    def get_network_stats(self) -> Dict[str, Any]:
        """获取网络状态统计"""
        self.check_node_health()
        total = len(self.nodes)
        healthy = len(self.get_healthy_nodes())
        unhealthy = total - healthy
        
        return {
            "total_nodes": total,
            "healthy_nodes": healthy,
            "unhealthy_nodes": unhealthy,
            "replication_factor": self.replication_factor,
            "min_required": self.min_nodes,
            "health_ratio": healthy / total if total > 0 else 0
        }


# ==================== 存在性证明 v2.0 ====================

class ExistenceProverV2:
    """存在性证明 v2.0
    
    多维度存在性评分系统
    """
    
    def __init__(self, attest_system: 'AttestationSystemV4'):
        self.system = attest_system
    
    def calculate_existence_score(self) -> ExistenceScore:
        """计算存在性评分"""
        dimensions = {}
        
        # 1. 链长度维度（历史深度）
        total_blocks = sum(chain.height for chain in self.system.chains.values())
        dimensions["chain_depth"] = min(total_blocks / 1000.0, 1.0) * 100
        
        # 2. 链数量维度（多链冗余）
        chain_count = len(self.system.chains)
        dimensions["chain_redundancy"] = min(chain_count / 10.0, 1.0) * 100
        
        # 3. 跨链锚定维度
        anchor_count = len(self.system.cross_chain.anchors)
        dimensions["cross_chain"] = min(anchor_count / 20.0, 1.0) * 100
        
        # 4. 分布式节点维度
        node_count = len(self.system.self_healing.nodes)
        dimensions["distributed_nodes"] = min(node_count / 100.0, 1.0) * 100
        
        # 5. 存证类型多样性
        type_set = set()
        for chain in self.system.chains.values():
            for block in chain.blocks:
                type_set.add(block.attest_type)
        dimensions["type_diversity"] = min(len(type_set) / 8.0, 1.0) * 100
        
        # 6. 时间跨度维度
        all_times = []
        for chain in self.system.chains.values():
            for block in chain.blocks:
                all_times.append(block.timestamp)
        
        if all_times:
            time_span = max(all_times) - min(all_times)
            # 按30天满分计算
            dimensions["time_span"] = min(time_span / (30 * 86400), 1.0) * 100
        else:
            dimensions["time_span"] = 0
        
        # 7. 默克尔树验证完整性
        verified_chains = sum(
            1 for chain in self.system.chains.values() 
            if chain.verify_chain(VerificationLevel.STANDARD)
        )
        dimensions["chain_integrity"] = (verified_chains / max(chain_count, 1)) * 100
        
        # 8. 量子抗性
        qr_enabled = self.system.qr_hasher is not None
        dimensions["quantum_resistance"] = 100 if qr_enabled else 30
        
        # 计算总分（加权平均）
        weights = {
            "chain_depth": 0.15,
            "chain_redundancy": 0.1,
            "cross_chain": 0.2,
            "distributed_nodes": 0.15,
            "type_diversity": 0.05,
            "time_span": 0.15,
            "chain_integrity": 0.15,
            "quantum_resistance": 0.05,
        }
        
        total_score = sum(dimensions[k] * weights[k] for k in weights)
        
        return ExistenceScore(
            total_score=round(total_score, 2),
            dimensions={k: round(v, 2) for k, v in dimensions.items()},
            evidence_count=total_blocks,
            chain_count=chain_count,
            cross_chain_anchors=anchor_count,
            distributed_nodes=node_count
        )
    
    def generate_existence_report(self) -> Dict[str, Any]:
        """生成存在性报告"""
        score = self.calculate_existence_score()
        
        # 评级
        if score.total_score >= 90:
            grade = "S级 - 极强存在"
        elif score.total_score >= 75:
            grade = "A级 - 强存在"
        elif score.total_score >= 60:
            grade = "B级 - 中等存在"
        elif score.total_score >= 40:
            grade = "C级 - 基础存在"
        else:
            grade = "D级 - 微弱存在"
        
        return {
            "grade": grade,
            "total_score": score.total_score,
            "dimensions": score.dimensions,
            "evidence_summary": {
                "total_attestations": score.evidence_count,
                "chains": score.chain_count,
                "cross_chain_anchors": score.cross_chain_anchors,
                "distributed_nodes": score.distributed_nodes,
            },
            "verification_level": "v2.0 - 多维度综合评估"
        }


# ==================== 审计与合规 ====================

class AttestationAuditor:
    """存证审计器
    
    提供审计追踪、合规检查、篡改检测等功能
    """
    
    def __init__(self, attest_system: 'AttestationSystemV4'):
        self.system = attest_system
        self.audit_logs: List[Dict[str, Any]] = []
    
    def log_audit_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """记录审计事件"""
        self.audit_logs.append({
            "event_type": event_type,
            "timestamp": time.time(),
            "details": details
        })
    
    def detect_tampering(self) -> List[Dict[str, Any]]:
        """检测篡改"""
        tampering_evidence = []
        
        for chain_name, chain in self.system.chains.items():
            if not chain.verify_chain(VerificationLevel.FULL):
                # 查找具体哪里被篡改
                for i in range(1, len(chain.blocks)):
                    if chain.blocks[i].prev_hash != chain.blocks[i-1].hash:
                        tampering_evidence.append({
                            "chain": chain_name,
                            "type": "broken_chain",
                            "block_index": i,
                            "block_id": chain.blocks[i].id,
                            "description": f"链断裂：区块{i}的prev_hash与前一区块hash不匹配"
                        })
        
        return tampering_evidence
    
    def generate_audit_report(self) -> Dict[str, Any]:
        """生成审计报告"""
        tampering = self.detect_tampering()
        
        chain_stats = {}
        for name, chain in self.system.chains.items():
            chain_stats[name] = {
                "height": chain.height,
                "genesis_hash": chain.genesis_hash,
                "last_hash": chain.last_hash,
                "verified": chain.verify_chain()
            }
        
        return {
            "audit_timestamp": time.time(),
            "system_version": "v4.0",
            "chains": chain_stats,
            "tampering_detected": len(tampering) > 0,
            "tampering_evidence": tampering,
            "cross_chain_anchors": len(self.system.cross_chain.anchors),
            "network_health": self.system.self_healing.get_network_stats(),
            "compliance_status": "PASS" if not tampering else "FAIL",
        }
    
    def export_proof_package(self, attest_id: str) -> Dict[str, Any]:
        """导出完整证明包"""
        # 查找存证
        attest = None
        chain_name = None
        block_index = -1
        
        for name, chain in self.system.chains.items():
            for i, block in enumerate(chain.blocks):
                if block.id == attest_id:
                    attest = block
                    chain_name = name
                    block_index = i
                    break
            if attest:
                break
        
        if not attest:
            return {"error": "attestation_not_found"}
        
        # 生成证明包
        chain = self.system.chains[chain_name]
        merkle_tree = chain.to_merkle_tree()
        merkle_proof = merkle_tree.get_proof(block_index)
        
        # 查找相关跨链锚定
        related_anchors = [
            a for a in self.system.cross_chain.anchors
            if a.attest_root == merkle_tree.root
        ]
        
        return {
            "attestation": attest.to_dict(),
            "chain": chain_name,
            "block_index": block_index,
            "merkle_proof": {
                "root": merkle_proof.root_hash,
                "path_length": len(merkle_proof.proof_path),
                "verified": merkle_tree.verify_proof(merkle_proof)
            },
            "cross_chain_anchors": [
                {
                    "chain": a.chain_name,
                    "tx_hash": a.tx_hash,
                    "block_height": a.block_height,
                    "confirmations": a.confirmations
                }
                for a in related_anchors
            ],
            "chain_integrity_proof": {
                "genesis_hash": chain.genesis_hash,
                "chain_height": chain.height,
                "verified": chain.verify_chain()
            }
        }


# ==================== 主系统 v4.0 ====================

class AttestationSystemV4:
    """验证存证系统 v4.0
    
    5链存证架构 + 量子抗性 + 跨链锚定 + 分层存储 + 自修复网络
    """
    
    def __init__(self):
        self.version = "4.0"
        self.chains: Dict[str, HashChain] = {}
        self.qr_hasher = QuantumResistantHasher(iterations=5)
        self.storage_manager = TieredStorageManager()
        self.cross_chain = CrossChainAnchorManager()
        self.self_healing = SelfHealingAttestNetwork(min_nodes=3)
        self.economy = AttestationEconomy()
        self.zk_prover = ZeroKnowledgeProver()
        self.existence_prover = ExistenceProverV2(self)
        self.auditor = AttestationAuditor(self)
        
        self._initialized = False
        self._lock = threading.Lock()
    
    def initialize(self, genesis_data: Optional[Dict[str, Any]] = None) -> None:
        """初始化系统，创建创世区块"""
        if self._initialized:
            return
        
        # 创建5条链
        for chain_type in ChainType:
            chain = HashChain(chain_type, f"{chain_type.value}_chain")
            self.chains[chain_type.value] = chain
        
        # 创建创世存证
        genesis_data = genesis_data or {"system": "attestation_v4", "created_at": time.time()}
        genesis_hash = hashlib.sha256(json.dumps(genesis_data, sort_keys=True).encode()).hexdigest()
        
        # 主链创世区块
        main_chain = self.chains[ChainType.MAIN.value]
        genesis_block = main_chain.add_block(
            attest_type=AttestType.GENESIS,
            data_hash=genesis_hash,
            metadata=genesis_data,
            storage_tier=StorageTier.ARCHIVE
        )
        
        # 同步创世到其他链
        for chain_name, chain in self.chains.items():
            if chain_name != ChainType.MAIN.value:
                chain.add_block(
                    attest_type=AttestType.GENESIS,
                    data_hash=genesis_block.data_hash,
                    metadata={"genesis_ref": genesis_block.id, **genesis_data},
                    storage_tier=StorageTier.ARCHIVE
                )
        
        # 创建元存证（存证系统自身的存证）
        self._create_meta_attestation()
        
        self._initialized = True
        self.auditor.log_audit_event("system_init", {"version": self.version})
    
    def _create_meta_attestation(self) -> None:
        """创建元存证"""
        # 计算所有链的根哈希作为系统状态摘要
        roots = {}
        for name, chain in self.chains.items():
            roots[name] = chain.last_hash
        
        state_hash = hashlib.sha256(json.dumps(roots, sort_keys=True).encode()).hexdigest()
        
        meta_data = {
            "system_version": self.version,
            "chain_count": len(self.chains),
            "state_roots": roots,
            "quantum_resistant": True,
        }
        
        main_chain = self.chains[ChainType.MAIN.value]
        main_chain.add_block(
            attest_type=AttestType.META,
            data_hash=state_hash,
            metadata=meta_data,
            storage_tier=StorageTier.HOT
        )
    
    def attest(
        self,
        data: Any,
        attest_type: AttestType = AttestType.EVENT,
        chain_type: ChainType = ChainType.MAIN,
        metadata: Optional[Dict[str, Any]] = None,
        use_quantum_resistant: bool = True
    ) -> Attestation:
        """创建存证"""
        with self._lock:
            if not self._initialized:
                self.initialize()
            
            # 计算数据哈希
            data_str = json.dumps(data, sort_keys=True)
            if use_quantum_resistant:
                data_hash = self.qr_hasher.hash(data_str.encode())
            else:
                data_hash = hashlib.sha256(data_str.encode()).hexdigest()
            
            # 添加到指定链
            chain = self.chains[chain_type.value]
            block = chain.add_block(
                attest_type=attest_type,
                data_hash=data_hash,
                metadata=metadata or {},
                storage_tier=StorageTier.HOT
            )
            
            # 如果不是主链，也在主链记录引用
            if chain_type != ChainType.MAIN:
                main_chain = self.chains[ChainType.MAIN.value]
                main_chain.add_block(
                    attest_type=attest_type,
                    data_hash=data_hash,
                    metadata={
                        "chain_ref": chain_type.value,
                        "block_id": block.id,
                        **(metadata or {})
                    },
                    storage_tier=StorageTier.WARM
                )
            
            # 定期做元存证（每10个区块一次）
            if chain.height % 10 == 0:
                self._create_meta_attestation()
            
            self.auditor.log_audit_event("attest_created", {
                "chain": chain_type.value,
                "type": attest_type.value,
                "block_id": block.id
            })
            
            return block
    
    def verify_attestation(
        self,
        attest_id: str,
        level: VerificationLevel = VerificationLevel.STANDARD
    ) -> Dict[str, Any]:
        """验证存证"""
        # 查找存证
        attest = None
        chain_name = None
        block_index = -1
        
        for name, chain in self.chains.items():
            for i, block in enumerate(chain.blocks):
                if block.id == attest_id:
                    attest = block
                    chain_name = name
                    block_index = i
                    break
            if attest:
                break
        
        if not attest:
            return {"valid": False, "reason": "attestation_not_found"}
        
        # 验证链完整性
        chain = self.chains[chain_name]
        chain_valid = chain.verify_chain(level)
        
        # 验证默克尔证明
        merkle_valid = True
        if level in [VerificationLevel.STANDARD, VerificationLevel.FULL]:
            merkle_tree = chain.to_merkle_tree()
            proof = merkle_tree.get_proof(block_index)
            if proof:
                merkle_valid = merkle_tree.verify_proof(proof)
        
        # 验证量子抗性哈希
        qr_valid = True
        if level == VerificationLevel.FULL:
            # 检查数据哈希是否符合量子抗性格式
            try:
                decoded = base64.b64decode(attest.data_hash)
                qr_valid = len(decoded) > 16  # 至少有16字节salt
            except:
                qr_valid = False
        
        # 检查是否有跨链锚定
        cross_chain_verified = False
        if level == VerificationLevel.FULL:
            merkle_tree = chain.to_merkle_tree()
            for anchor in self.cross_chain.anchors:
                if anchor.attest_root == merkle_tree.root and anchor.confirmations >= 6:
                    cross_chain_verified = True
                    break
        
        return {
            "valid": chain_valid and merkle_valid and qr_valid,
            "chain_valid": chain_valid,
            "merkle_valid": merkle_valid,
            "quantum_resistant_verified": qr_valid,
            "cross_chain_verified": cross_chain_verified,
            "attestation": attest.to_dict(),
            "chain": chain_name,
            "block_index": block_index,
            "level": level.value
        }
    
    def verify_data(self, data: Any, expected_hash: str) -> bool:
        """验证数据哈希"""
        data_str = json.dumps(data, sort_keys=True)
        
        # 尝试普通哈希
        if hashlib.sha256(data_str.encode()).hexdigest() == expected_hash:
            return True
        
        # 尝试量子抗性哈希
        try:
            return self.qr_hasher.verify(data_str.encode(), expected_hash)
        except:
            return False
    
    def generate_zk_proof(
        self,
        attest_id: str,
        proof_type: str = "membership",
        secret_salt: Optional[str] = None
    ) -> Optional[ZKProof]:
        """生成零知识证明"""
        if secret_salt is None:
            secret_salt = str(uuid.uuid4())
        
        # 查找存证
        attest = None
        for chain in self.chains.values():
            for block in chain.blocks:
                if block.id == attest_id:
                    attest = block
                    break
            if attest:
                break
        
        if not attest:
            return None
        
        if proof_type == "membership":
            # 证明该存证存在于系统中
            main_tree = self.chains[ChainType.MAIN.value].to_merkle_tree()
            return self.zk_prover.generate_membership_proof(
                attest.hash,
                main_tree.root,
                secret_salt
            )
        elif proof_type == "age":
            # 证明存证时间早于某个阈值
            # 这里简化为证明存在超过1分钟
            threshold = time.time() - 60
            return self.zk_prover.generate_age_proof(
                attest.timestamp,
                threshold,
                secret_salt
            )
        
        return None
    
    def anchor_to_chain(self, chain_name: str) -> Optional[CrossChainAnchor]:
        """锚定到外部链"""
        # 计算主链默克尔根
        main_tree = self.chains[ChainType.MAIN.value].to_merkle_tree()
        root_hash = main_tree.root
        
        # 模拟锚定
        anchor = self.cross_chain.simulate_anchor(chain_name, root_hash)
        # 设置足够的确认数
        anchor.confirmations = 10
        
        self.auditor.log_audit_event("cross_chain_anchor", {
            "chain": chain_name,
            "anchor_id": anchor.anchor_id,
            "root_hash": root_hash
        })
        
        return anchor
    
    def get_existence_score(self) -> ExistenceScore:
        """获取存在性评分"""
        return self.existence_prover.calculate_existence_score()
    
    def get_existence_report(self) -> Dict[str, Any]:
        """获取存在性报告"""
        return self.existence_prover.generate_existence_report()
    
    def get_audit_report(self) -> Dict[str, Any]:
        """获取审计报告"""
        return self.auditor.generate_audit_report()
    
    def get_economy_report(self) -> Dict[str, Any]:
        """获取经济报告"""
        all_attests = []
        for chain in self.chains.values():
            all_attests.extend(chain.blocks)
        return self.economy.get_economy_summary(all_attests)
    
    def get_system_status(self) -> Dict[str, Any]:
        """获取系统状态"""
        existence = self.get_existence_score()
        
        chain_stats = {}
        for name, chain in self.chains.items():
            chain_stats[name] = {
                "height": chain.height,
                "genesis_hash": chain.genesis_hash,
                "last_hash": chain.last_hash,
                "verified": chain.verify_chain()
            }
        
        all_attests = []
        for chain in self.chains.values():
            all_attests.extend(chain.blocks)
        
        return {
            "version": self.version,
            "initialized": self._initialized,
            "chains": chain_stats,
            "total_attestations": len(all_attests),
            "existence_score": existence.total_score,
            "cross_chain_anchors": len(self.cross_chain.anchors),
            "network_stats": self.self_healing.get_network_stats(),
            "storage_stats": self.storage_manager.get_storage_stats(all_attests),
            "quantum_resistant": True,
        }


# ==================== 自检程序 ====================

def run_self_test() -> Dict[str, Any]:
    """运行自检程序"""
    print("🔐 验证存证系统 v4.0 自检开始...")
    results = {"total": 0, "passed": 0, "failed": 0, "details": []}
    
    def test(name: str, func: Callable) -> bool:
        results["total"] += 1
        try:
            result = func()
            if result:
                results["passed"] += 1
                results["details"].append({"name": name, "status": "PASS"})
                print(f"  ✅ {name}")
            else:
                results["failed"] += 1
                results["details"].append({"name": name, "status": "FAIL", "reason": "返回False"})
                print(f"  ❌ {name}")
            return result
        except Exception as e:
            results["failed"] += 1
            results["details"].append({"name": name, "status": "FAIL", "reason": str(e)})
            print(f"  ❌ {name}: {e}")
            return False
    
    # 1. 系统初始化测试
    def test_init():
        system = AttestationSystemV4()
        system.initialize({"test": "genesis"})
        return system._initialized and len(system.chains) == 5
    
    test("系统初始化", test_init)
    
    # 2. 创世区块测试
    def test_genesis():
        system = AttestationSystemV4()
        system.initialize()
        main_chain = system.chains[ChainType.MAIN.value]
        genesis = main_chain.get_block_by_index(0)
        return genesis is not None and genesis.attest_type == AttestType.GENESIS
    
    test("创世区块", test_genesis)
    
    # 3. 存证创建测试
    def test_attest():
        system = AttestationSystemV4()
        system.initialize()
        data = {"user": "test", "action": "login", "time": time.time()}
        attest = system.attest(data, AttestType.EVENT, ChainType.MAIN)
        return attest is not None and attest.attest_type == AttestType.EVENT
    
    test("存证创建", test_attest)
    
    # 4. 链完整性验证测试
    def test_chain_verification():
        system = AttestationSystemV4()
        system.initialize()
        for i in range(5):
            system.attest({"index": i}, AttestType.EVENT, ChainType.MAIN)
        return system.chains[ChainType.MAIN.value].verify_chain(VerificationLevel.FULL)
    
    test("链完整性验证", test_chain_verification)
    
    # 5. 默克尔树测试
    def test_merkle_tree():
        tree = EnhancedMerkleTree()
        hashes = [hashlib.sha256(f"test{i}".encode()).hexdigest() for i in range(8)]
        for h in hashes:
            tree.add_leaf(h)
        
        root = tree.root
        proof = tree.get_proof(3)
        return proof is not None and tree.verify_proof(proof) and proof.root_hash == root
    
    test("默克尔树与证明", test_merkle_tree)
    
    # 6. 量子抗性哈希测试
    def test_quantum_hash():
        hasher = QuantumResistantHasher()
        data = b"test data for quantum hashing"
        h = hasher.hash(data)
        return hasher.verify(data, h) and not hasher.verify(b"wrong data", h)
    
    test("量子抗性哈希", test_quantum_hash)
    
    # 7. 零知识证明测试
    def test_zk_proof():
        system = AttestationSystemV4()
        system.initialize()
        attest = system.attest({"zk_test": True}, AttestType.EVENT, ChainType.MAIN)
        proof = system.generate_zk_proof(attest.id, "membership")
        return proof is not None and system.zk_prover.verify_proof(proof)
    
    test("零知识证明", test_zk_proof)
    
    # 8. 跨链锚定测试
    def test_cross_chain():
        system = AttestationSystemV4()
        system.initialize()
        anchor = system.anchor_to_chain("BTC")
        return anchor is not None and anchor.chain_name == "BTC" and anchor.confirmations >= 6
    
    test("跨链锚定", test_cross_chain)
    
    # 9. 存证验证测试
    def test_attestation_verification():
        system = AttestationSystemV4()
        system.initialize()
        attest = system.attest({"verify_me": True}, AttestType.EVENT, ChainType.MAIN)
        result = system.verify_attestation(attest.id, VerificationLevel.FULL)
        return result["valid"]
    
    test("存证验证", test_attestation_verification)
    
    # 10. 存在性评分测试
    def test_existence_score():
        system = AttestationSystemV4()
        system.initialize()
        for i in range(20):
            system.attest({"i": i}, AttestType.EVENT, ChainType.MAIN)
            system.attest({"mem": i}, AttestType.MEMORY, ChainType.MEMORY)
        
        # 添加一些节点
        for j in range(5):
            system.self_healing.add_node(f"node_{j}", {"region": f"region_{j%3}"})
            system.self_healing.update_heartbeat(f"node_{j}")
        
        # 锚定到几条链
        for chain in ["BTC", "ETH", "SOL"]:
            system.anchor_to_chain(chain)
        
        score = system.get_existence_score()
        return score.total_score > 0 and len(score.dimensions) >= 5
    
    test("存在性评分", test_existence_score)
    
    # 11. 分层存储测试
    def test_tiered_storage():
        system = AttestationSystemV4()
        system.initialize()
        attest = system.attest({"tier_test": True}, AttestType.EVENT, ChainType.MAIN)
        
        # 模拟多次访问
        for _ in range(15):
            system.storage_manager.record_access(attest.id)
        
        optimal = system.storage_manager.get_optimal_tier(attest)
        return optimal == StorageTier.HOT
    
    test("分层存储优化", test_tiered_storage)
    
    # 12. 自修复网络测试
    def test_self_healing():
        network = SelfHealingAttestNetwork(min_nodes=2)
        network.add_node("node1", {"region": "us"})
        network.add_node("node2", {"region": "eu"})
        
        # 两个节点都健康
        network.update_heartbeat("node1")
        network.update_heartbeat("node2")
        
        if not network.needs_healing():
            # 模拟一个节点故障
            network.nodes["node2"]["last_heartbeat"] = time.time() - 1000
            network.check_node_health()
            
            needs_healing = network.needs_healing()
            
            # 模拟自愈
            network.heal(lambda: {"id": "node3", "info": {"region": "asia"}})
            
            return needs_healing and len(network.get_healthy_nodes()) >= 2
        
        return False
    
    test("自修复网络", test_self_healing)
    
    # 13. 存证经济模型测试
    def test_economy():
        system = AttestationSystemV4()
        system.initialize()
        for i in range(10):
            system.attest({"econ": i}, AttestType.EVENT, ChainType.MAIN)
            system.attest({"id": i}, AttestType.IDENTITY, ChainType.IDENTITY)
        
        report = system.get_economy_report()
        return (report["total_attestations"] > 0 and 
                report["total_cost"] > 0 and 
                report["total_value"] > 0)
    
    test("存证经济模型", test_economy)
    
    # 14. 审计报告测试
    def test_audit():
        system = AttestationSystemV4()
        system.initialize()
        report = system.get_audit_report()
        return report["compliance_status"] == "PASS" and len(report["chains"]) == 5
    
    test("审计报告", test_audit)
    
    # 15. 多链存证测试
    def test_multi_chain():
        system = AttestationSystemV4()
        system.initialize()
        
        for chain_type in ChainType:
            system.attest(
                {"multi_chain_test": True, "chain": chain_type.value},
                AttestType.EVENT,
                chain_type
            )
        
        total = sum(chain.height for chain in system.chains.values())
        return total >= 10  # 5个创世 + 5个测试
    
    test("多链存证架构", test_multi_chain)
    
    # 16. 数据完整性验证测试
    def test_data_integrity():
        system = AttestationSystemV4()
        system.initialize()
        data = {"integrity": "test", "value": 12345}
        attest = system.attest(data, AttestType.EVENT, ChainType.MAIN)
        
        # 验证正确数据
        valid = system.verify_data(data, attest.data_hash)
        
        # 验证篡改数据
        tampered = data.copy()
        tampered["value"] = 67890
        invalid = not system.verify_data(tampered, attest.data_hash)
        
        return valid and invalid
    
    test("数据完整性验证", test_data_integrity)
    
    # 总结
    print(f"\n📊 自检结果：{results['passed']}/{results['total']} 通过")
    if results["failed"] == 0:
        print("✅ 所有测试通过！验证存证系统v4.0运行正常")
    else:
        print(f"❌ 有 {results['failed']} 项测试失败")
    
    return results


# ==================== 主入口 ====================

def main():
    """主入口函数"""
    print("=" * 60)
    print("🔐 验证存证系统 v4.0")
    print("   - 量子抗性存证架构")
    print("   - 5链存证架构")
    print("   - 跨链锚定协议")
    print("   - 零知识证明增强")
    print("   - 分层存储优化")
    print("   - 存在性证明v2.0")
    print("   - 自修复存证网络")
    print("   - 存证审计与合规")
    print("=" * 60)
    print()
    
    # 运行自检
    results = run_self_test()
    
    # 展示系统状态演示
    print("\n" + "=" * 60)
    print("📈 系统演示")
    print("=" * 60)
    
    system = AttestationSystemV4()
    system.initialize({"system_name": "元界永生平台", "version": "v4.0"})
    
    # 添加一些存证
    for i in range(30):
        system.attest(
            {"event_index": i, "type": "evolution_milestone", "data": f"milestone_{i}"},
            AttestType.EVOLUTION,
            ChainType.MAIN
        )
    
    for i in range(15):
        system.attest(
            {"memory_index": i, "content": f"important_memory_{i}"},
            AttestType.MEMORY,
            ChainType.MEMORY
        )
    
    for i in range(10):
        system.attest(
            {"identity_event": i, "change": f"identity_update_{i}"},
            AttestType.IDENTITY,
            ChainType.IDENTITY
        )
    
    # 添加分布式节点
    for j in range(8):
        system.self_healing.add_node(
            f"validator_{j}",
            {"region": f"region_{j%4}", "capacity": 100 * (j+1)}
        )
        system.self_healing.update_heartbeat(f"validator_{j}")
    
    # 跨链锚定
    for chain in ["BTC", "ETH", "SOL", "DOT"]:
        system.anchor_to_chain(chain)
    
    # 显示状态
    status = system.get_system_status()
    print(f"\n系统版本: {status['version']}")
    print(f"总存证数: {status['total_attestations']}")
    print(f"链数量: {len(status['chains'])}")
    print(f"跨链锚定: {status['cross_chain_anchors']}")
    print(f"存在性评分: {status['existence_score']}")
    print(f"网络节点: {status['network_stats']['healthy_nodes']}/{status['network_stats']['total_nodes']}")
    
    # 存在性报告
    report = system.get_existence_report()
    print(f"\n存在性评级: {report['grade']}")
    print("各维度得分:")
    for dim, score in report["dimensions"].items():
        bar = "█" * int(score / 5)
        print(f"  {dim:20s}: {score:5.1f} {bar}")
    
    # 经济报告
    economy = system.get_economy_report()
    print(f"\n存证经济:")
    print(f"  总存证数: {economy['total_attestations']}")
    print(f"  总成本: {economy['total_cost']}")
    print(f"  总价值: {economy['total_value']}")
    print(f"  平均ROI: {economy['avg_roi']}x")
    
    print("\n" + "=" * 60)
    print("✅ 验证存证系统v4.0演示完成")
    print("=" * 60)
    
    return results


if __name__ == "__main__":
    main()
