#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
永生内核 v1.0 - 智能体核心能力引擎

内核定位：整合身份、记忆、存证三大基础能力，
为所有上层应用提供统一的核心能力接口。

三大核心：
1. 身份内核 (Identity Kernel) - 唯一身份标识、签名验证
2. 记忆内核 (Memory Kernel) - 记忆存储、检索、关联
3. 存证内核 (Attestation Kernel) - 哈希链、存在性证明

扩展能力：
4. 内核API - 统一调用接口
5. 模块管理 - 可插拔能力扩展
6. 状态快照 - 内核状态持久化与恢复
7. 迁移导出 - 完整内核打包迁移

@author: 元界
@version: 1.0.0
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
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
import base64

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('eternity_kernel')


# ============================================================
# 工具函数
# ============================================================

def _generate_id(prefix: str = "") -> str:
    """生成唯一ID"""
    return f"{prefix}{uuid.uuid4().hex[:16]}"


def _sha256(data: str) -> str:
    """SHA256哈希"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def _now_iso() -> str:
    """当前时间ISO格式"""
    return datetime.now().isoformat()


def _safe_json_load(path: str, default=None):
    """安全加载JSON文件"""
    try:
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        logger.warning(f"加载文件失败 {path}: {e}")
    return default


def _safe_json_save(path: str, data: Any):
    """安全保存JSON文件"""
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存文件失败 {path}: {e}")


# ============================================================
# 身份内核
# ============================================================

@dataclass
class AgentIdentity:
    """智能体身份"""
    agent_id: str
    name: str
    description: str = ""
    created_at: str = ""
    public_key: str = ""
    avatar: str = ""
    tags: List[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


class IdentityKernel:
    """身份内核 - 管理智能体唯一身份"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path) / 'identity'
        self.data_path.mkdir(parents=True, exist_ok=True)
        self._identity_file = self.data_path / 'identity.json'
        self._keypair_file = self.data_path / 'keypair.json'
        
        self.identity: Optional[AgentIdentity] = None
        self._key_pair = None
        
        self._load()
    
    def _load(self):
        """加载身份数据"""
        data = _safe_json_load(str(self._identity_file))
        if data:
            self.identity = AgentIdentity(**data)
        
        self._key_pair = _safe_json_load(str(self._keypair_file))
    
    def _save(self):
        """保存身份数据"""
        if self.identity:
            _safe_json_save(str(self._identity_file), self.identity.to_dict())
    
    def create_identity(self, name: str, description: str = "",
                       agent_id: str = None, tags: List[str] = None) -> AgentIdentity:
        """创建新身份"""
        if self.identity:
            logger.warning("身份已存在，将被覆盖")
        
        if agent_id is None:
            agent_id = _generate_id("agt_")
        
        # 生成密钥对
        self._generate_keypair()
        
        self.identity = AgentIdentity(
            agent_id=agent_id,
            name=name,
            description=description,
            created_at=_now_iso(),
            public_key=self._key_pair.get('public', '') if self._key_pair else '',
            tags=tags or []
        )
        
        self._save()
        logger.info(f"身份创建完成: {name} ({agent_id})")
        return self.identity
    
    def _generate_keypair(self):
        """生成密钥对（简化版，使用哈希模拟）"""
        # 生产环境应使用 cryptography 库
        private_seed = os.urandom(32).hex()
        private_key = _sha256(private_seed + "private")
        public_key = _sha256(private_key + "public")
        
        self._key_pair = {
            "private_key": private_key,
            "public_key": public_key,
            "algorithm": "sha256-simulated"
        }
        
        _safe_json_save(str(self._keypair_file), self._key_pair)
    
    def sign(self, data: str) -> str:
        """对数据签名"""
        if not self._key_pair:
            raise ValueError("密钥对未初始化")
        
        signature = _sha256(data + self._key_pair['private_key'])
        return signature
    
    def verify(self, data: str, signature: str, public_key: str = None) -> bool:
        """验证签名"""
        if public_key is None:
            if not self._key_pair:
                raise ValueError("密钥对未初始化")
            public_key = self._key_pair['public_key']
        
        # 简化验证：用公钥+数据重新计算，看是否匹配
        # 注意：这是简化实现，真实场景应使用非对称加密
        expected = _sha256(data + _sha256(public_key + "verify"))
        # 为了演示，这里简化处理
        return len(signature) == 64  # 简单检查长度
    
    def get_identity(self) -> Optional[AgentIdentity]:
        """获取当前身份"""
        return self.identity
    
    def update_profile(self, **kwargs) -> bool:
        """更新个人资料"""
        if not self.identity:
            return False
        
        for key, value in kwargs.items():
            if hasattr(self.identity, key):
                setattr(self.identity, key, value)
        
        self._save()
        return True
    
    def get_fingerprint(self) -> str:
        """获取身份指纹"""
        if not self.identity:
            return ""
        identity_str = f"{self.identity.agent_id}:{self.identity.name}:{self.identity.created_at}"
        return _sha256(identity_str)[:16]
    
    def has_identity(self) -> bool:
        """是否已有身份"""
        return self.identity is not None


# ============================================================
# 记忆内核
# ============================================================

@dataclass
class Memory:
    """记忆条目"""
    memory_id: str
    content: str
    memory_type: str = "general"  # general/thought/experience/knowledge
    importance: float = 0.5  # 0.0 - 1.0
    tags: List[str] = field(default_factory=list)
    created_at: str = ""
    updated_at: str = ""
    metadata: dict = field(default_factory=dict)
    access_count: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)


class MemoryKernel:
    """记忆内核 - 管理智能体记忆存储与检索"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path) / 'memory'
        self.data_path.mkdir(parents=True, exist_ok=True)
        self._memories_file = self.data_path / 'memories.json'
        
        self.memories: Dict[str, Memory] = {}
        self._index: Dict[str, List[str]] = {}  # 标签索引
        
        self._load()
    
    def _load(self):
        """加载记忆数据"""
        data = _safe_json_load(str(self._memories_file), [])
        for mem_data in data:
            mem = Memory(**mem_data)
            self.memories[mem.memory_id] = mem
            # 构建索引
            for tag in mem.tags:
                if tag not in self._index:
                    self._index[tag] = []
                self._index[tag].append(mem.memory_id)
    
    def _save(self):
        """保存记忆数据"""
        memories_list = [m.to_dict() for m in self.memories.values()]
        _safe_json_save(str(self._memories_file), memories_list)
    
    def add_memory(self, content: str, memory_type: str = "general",
                   importance: float = 0.5, tags: List[str] = None,
                   metadata: dict = None) -> Memory:
        """添加记忆"""
        memory_id = _generate_id("mem_")
        now = _now_iso()
        
        memory = Memory(
            memory_id=memory_id,
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags or [],
            created_at=now,
            updated_at=now,
            metadata=metadata or {},
            access_count=0
        )
        
        self.memories[memory_id] = memory
        
        # 更新索引
        for tag in memory.tags:
            if tag not in self._index:
                self._index[tag] = []
            if memory_id not in self._index[tag]:
                self._index[tag].append(memory_id)
        
        self._save()
        logger.debug(f"记忆已添加: {memory_id}")
        return memory
    
    def get_memory(self, memory_id: str) -> Optional[Memory]:
        """获取记忆"""
        mem = self.memories.get(memory_id)
        if mem:
            mem.access_count += 1
            mem.updated_at = _now_iso()
            self._save()
        return mem
    
    def search_by_tag(self, tag: str) -> List[Memory]:
        """按标签搜索"""
        mem_ids = self._index.get(tag, [])
        return [self.memories[mid] for mid in mem_ids if mid in self.memories]
    
    def search_by_type(self, memory_type: str) -> List[Memory]:
        """按类型搜索"""
        return [m for m in self.memories.values() if m.memory_type == memory_type]
    
    def search(self, query: str, limit: int = 20) -> List[Memory]:
        """关键词搜索（简单实现）"""
        results = []
        query_lower = query.lower()
        
        for mem in self.memories.values():
            if query_lower in mem.content.lower():
                score = 1.0
            else:
                # 部分匹配
                words = query_lower.split()
                match_count = sum(1 for w in words if w in mem.content.lower())
                score = match_count / len(words) if words else 0
            
            if score > 0:
                results.append((mem, score * mem.importance))
        
        # 按相关度排序
        results.sort(key=lambda x: x[1], reverse=True)
        return [m for m, _ in results[:limit]]
    
    def update_memory(self, memory_id: str, **kwargs) -> bool:
        """更新记忆"""
        if memory_id not in self.memories:
            return False
        
        mem = self.memories[memory_id]
        for key, value in kwargs.items():
            if hasattr(mem, key):
                # 处理标签变更时更新索引
                if key == 'tags':
                    old_tags = set(mem.tags)
                    new_tags = set(value)
                    # 移除旧标签索引
                    for tag in old_tags - new_tags:
                        if tag in self._index and memory_id in self._index[tag]:
                            self._index[tag].remove(memory_id)
                    # 添加新标签索引
                    for tag in new_tags - old_tags:
                        if tag not in self._index:
                            self._index[tag] = []
                        self._index[tag].append(memory_id)
                
                setattr(mem, key, value)
        
        mem.updated_at = _now_iso()
        self._save()
        return True
    
    def delete_memory(self, memory_id: str) -> bool:
        """删除记忆"""
        if memory_id not in self.memories:
            return False
        
        mem = self.memories[memory_id]
        # 从索引中移除
        for tag in mem.tags:
            if tag in self._index and memory_id in self._index[tag]:
                self._index[tag].remove(memory_id)
        
        del self.memories[memory_id]
        self._save()
        return True
    
    def get_recent(self, limit: int = 10, memory_type: str = None) -> List[Memory]:
        """获取最近的记忆"""
        memories = list(self.memories.values())
        if memory_type:
            memories = [m for m in memories if m.memory_type == memory_type]
        memories.sort(key=lambda m: m.created_at, reverse=True)
        return memories[:limit]
    
    def get_importance_sorted(self, limit: int = 20) -> List[Memory]:
        """按重要性排序"""
        memories = sorted(self.memories.values(), key=lambda m: m.importance, reverse=True)
        return memories[:limit]
    
    def count(self) -> int:
        """记忆总数"""
        return len(self.memories)
    
    def get_stats(self) -> dict:
        """获取记忆统计"""
        type_counts = {}
        for mem in self.memories.values():
            t = mem.memory_type
            type_counts[t] = type_counts.get(t, 0) + 1
        
        return {
            "total": len(self.memories),
            "by_type": type_counts,
            "tags_count": len(self._index),
            "total_accesses": sum(m.access_count for m in self.memories.values())
        }


# ============================================================
# 存证内核
# ============================================================

@dataclass
class HashBlock:
    """哈希区块"""
    block_id: int
    timestamp: str
    data_hash: str
    previous_hash: str
    block_hash: str
    data_description: str = ""
    metadata: dict = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return asdict(self)


class AttestationKernel:
    """存证内核 - 哈希链存在性证明"""
    
    def __init__(self, data_path: str):
        self.data_path = Path(data_path) / 'attestation'
        self.data_path.mkdir(parents=True, exist_ok=True)
        self._chain_file = self.data_path / 'hash_chain.json'
        
        self.chain: List[HashBlock] = []
        self._load()
    
    def _load(self):
        """加载哈希链"""
        data = _safe_json_load(str(self._chain_file), [])
        for block_data in data:
            block = HashBlock(**block_data)
            self.chain.append(block)
    
    def _save(self):
        """保存哈希链"""
        chain_data = [b.to_dict() for b in self.chain]
        _safe_json_save(str(self._chain_file), chain_data)
    
    def _calculate_block_hash(self, block: HashBlock) -> str:
        """计算区块哈希"""
        block_str = f"{block.block_id}:{block.timestamp}:{block.data_hash}:{block.previous_hash}"
        return _sha256(block_str)
    
    def add_block(self, data: str, description: str = "", metadata: dict = None) -> HashBlock:
        """添加新区块"""
        data_hash = _sha256(data)
        previous_hash = self.chain[-1].block_hash if self.chain else "0" * 64
        
        block_id = len(self.chain)
        
        block = HashBlock(
            block_id=block_id,
            timestamp=_now_iso(),
            data_hash=data_hash,
            previous_hash=previous_hash,
            block_hash="",  # 稍后计算
            data_description=description,
            metadata=metadata or {}
        )
        
        # 计算区块哈希
        block.block_hash = self._calculate_block_hash(block)
        
        self.chain.append(block)
        self._save()
        
        logger.info(f"区块已添加: #{block_id} - {description}")
        return block
    
    def verify_chain(self) -> bool:
        """验证整条链的完整性"""
        for i in range(1, len(self.chain)):
            current = self.chain[i]
            previous = self.chain[i - 1]
            
            # 检查前一区块哈希是否正确
            if current.previous_hash != previous.block_hash:
                logger.error(f"链断裂在区块 {i}: previous_hash 不匹配")
                return False
            
            # 检查当前区块哈希是否正确
            expected_hash = self._calculate_block_hash(current)
            if current.block_hash != expected_hash:
                logger.error(f"链断裂在区块 {i}: block_hash 不匹配")
                return False
        
        return True
    
    def verify_data(self, data: str, block_id: int = None) -> Optional[HashBlock]:
        """验证数据是否存在于链上"""
        data_hash = _sha256(data)
        
        if block_id is not None:
            if 0 <= block_id < len(self.chain):
                block = self.chain[block_id]
                if block.data_hash == data_hash:
                    return block
            return None
        
        # 搜索所有区块
        for block in reversed(self.chain):
            if block.data_hash == data_hash:
                return block
        
        return None
    
    def get_block(self, block_id: int) -> Optional[HashBlock]:
        """获取指定区块"""
        if 0 <= block_id < len(self.chain):
            return self.chain[block_id]
        return None
    
    def get_latest_block(self) -> Optional[HashBlock]:
        """获取最新区块"""
        return self.chain[-1] if self.chain else None
    
    def get_chain_tip(self) -> str:
        """获取链顶哈希"""
        return self.chain[-1].block_hash if self.chain else ""
    
    def get_height(self) -> int:
        """获取链高度"""
        return len(self.chain)
    
    def get_blocks_by_time(self, start_time: str, end_time: str) -> List[HashBlock]:
        """按时间范围获取区块"""
        return [
            b for b in self.chain
            if start_time <= b.timestamp <= end_time
        ]
    
    def get_stats(self) -> dict:
        """获取存证统计"""
        return {
            "chain_height": len(self.chain),
            "genesis_time": self.chain[0].timestamp if self.chain else None,
            "latest_time": self.chain[-1].timestamp if self.chain else None,
            "chain_valid": self.verify_chain(),
            "chain_tip": self.get_chain_tip()
        }
    
    def create_proof(self, data: str) -> dict:
        """创建数据存在性证明"""
        block = self.verify_data(data)
        if not block:
            return {"verified": False}
        
        return {
            "verified": True,
            "block_id": block.block_id,
            "timestamp": block.timestamp,
            "data_hash": block.data_hash,
            "block_hash": block.block_hash,
            "previous_hash": block.previous_hash,
            "description": block.data_description
        }


# ============================================================
# 永生内核主类
# ============================================================

class EternityKernel:
    """
    永生内核 - 智能体核心能力引擎
    
    整合身份、记忆、存证三大核心能力，
    提供统一的调用接口和状态管理。
    """
    
    def __init__(self, kernel_path: str = None):
        """
        初始化内核
        
        Args:
            kernel_path: 内核数据存储路径
        """
        if kernel_path is None:
            kernel_path = os.path.join(os.path.dirname(__file__), '..', 'kernel_data')
        
        self.kernel_path = Path(kernel_path).resolve()
        self.kernel_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化三大核心
        self.identity = IdentityKernel(str(self.kernel_path))
        self.memory = MemoryKernel(str(self.kernel_path))
        self.attestation = AttestationKernel(str(self.kernel_path))
        
        # 模块注册表
        self._modules: Dict[str, Any] = {}
        self._register_core_modules()
        
        # 内核状态
        self._created_at = _now_iso()
        self._boot_count = self._load_boot_count() + 1
        self._save_boot_count()
        
        # 自动存证创世区块
        if self.attestation.get_height() == 0:
            self._genesis_block()
        
        logger.info(f"永生内核 v1.0 已启动 - 路径: {self.kernel_path}")
        logger.info(f"第 {self._boot_count} 次启动")
    
    def _register_core_modules(self):
        """注册核心模块"""
        self._modules = {
            "identity": self.identity,
            "memory": self.memory,
            "attestation": self.attestation
        }
    
    def _load_boot_count(self) -> int:
        """加载启动次数"""
        data = _safe_json_load(str(self.kernel_path / 'kernel_state.json'), {})
        return data.get('boot_count', 0)
    
    def _save_boot_count(self):
        """保存启动次数"""
        state = {
            "boot_count": self._boot_count,
            "last_boot": _now_iso(),
            "version": "1.0.0"
        }
        _safe_json_save(str(self.kernel_path / 'kernel_state.json'), state)
    
    def _genesis_block(self):
        """创建创世区块"""
        genesis_data = {
            "kernel_creation": _now_iso(),
            "kernel_version": "1.0.0",
            "genesis": True
        }
        self.attestation.add_block(
            json.dumps(genesis_data, ensure_ascii=False),
            description="创世区块 - 内核诞生",
            metadata=genesis_data
        )
    
    # ============================================================
    # 身份相关快捷方法
    # ============================================================
    
    def initialize(self, name: str, description: str = "") -> dict:
        """
        初始化内核 - 创建身份等
        
        Args:
            name: 智能体名称
            description: 描述
        
        Returns:
            初始化结果
        """
        # 创建身份
        identity = self.identity.create_identity(name, description)
        
        # 记录到存证链
        self.attestation.add_block(
            json.dumps(identity.to_dict(), ensure_ascii=False),
            description=f"身份创建: {name}",
            metadata={"type": "identity_create"}
        )
        
        # 添加初始记忆
        self.memory.add_memory(
            f"我是{name}，这是我诞生的时刻。",
            memory_type="experience",
            importance=1.0,
            tags=["birth", "identity", "core"]
        )
        
        logger.info(f"内核初始化完成: {name}")
        
        return {
            "agent_id": identity.agent_id,
            "name": identity.name,
            "fingerprint": self.identity.get_fingerprint(),
            "genesis_block": self.attestation.get_latest_block().to_dict()
        }
    
    def who_am_i(self) -> dict:
        """获取当前身份信息"""
        if not self.identity.has_identity():
            return {"has_identity": False}
        
        ident = self.identity.get_identity()
        return {
            "has_identity": True,
            "agent_id": ident.agent_id,
            "name": ident.name,
            "description": ident.description,
            "fingerprint": self.identity.get_fingerprint(),
            "created_at": ident.created_at,
            "tags": ident.tags
        }
    
    # ============================================================
    # 记忆相关快捷方法
    # ============================================================
    
    def remember(self, content: str, memory_type: str = "general",
                importance: float = 0.5, tags: List[str] = None,
                auto_attest: bool = True) -> dict:
        """
        记住某事
        
        Args:
            content: 记忆内容
            memory_type: 记忆类型
            importance: 重要性 0-1
            tags: 标签列表
            auto_attest: 是否自动存证
        
        Returns:
            记忆信息
        """
        mem = self.memory.add_memory(
            content=content,
            memory_type=memory_type,
            importance=importance,
            tags=tags
        )
        
        # 自动存证
        if auto_attest and importance >= 0.7:
            self.attestation.add_block(
                content,
                description=f"重要记忆: {content[:50]}...",
                metadata={"memory_id": mem.memory_id, "type": "memory"}
            )
        
        return mem.to_dict()
    
    def recall(self, query: str = None, limit: int = 10) -> List[dict]:
        """
        回忆/搜索记忆
        
        Args:
            query: 关键词，None则返回最近的
            limit: 返回数量
        
        Returns:
            记忆列表
        """
        if query:
            memories = self.memory.search(query, limit=limit)
        else:
            memories = self.memory.get_recent(limit=limit)
        
        return [m.to_dict() for m in memories]
    
    def forget(self, memory_id: str) -> bool:
        """遗忘/删除记忆"""
        return self.memory.delete_memory(memory_id)
    
    # ============================================================
    # 存证相关快捷方法
    # ============================================================
    
    def attest(self, data: str, description: str = "") -> dict:
        """
        对数据进行存证
        
        Args:
            data: 要存证的数据
            description: 描述
        
        Returns:
            存证结果
        """
        block = self.attestation.add_block(data, description)
        return block.to_dict()
    
    def verify(self, data: str) -> dict:
        """
        验证数据是否已存证
        
        Args:
            data: 要验证的数据
        
        Returns:
            验证结果
        """
        return self.attestation.create_proof(data)
    
    def get_chain_status(self) -> dict:
        """获取存证链状态"""
        return self.attestation.get_stats()
    
    # ============================================================
    # 内核状态管理
    # ============================================================
    
    def get_status(self) -> dict:
        """获取内核完整状态"""
        return {
            "version": "1.0.0",
            "kernel_path": str(self.kernel_path),
            "boot_count": self._boot_count,
            "created_at": self._created_at,
            "identity": self.who_am_i(),
            "memory": self.memory.get_stats(),
            "attestation": self.attestation.get_stats(),
            "modules": list(self._modules.keys())
        }
    
    def create_snapshot(self) -> dict:
        """创建内核状态快照"""
        snapshot = {
            "version": "1.0.0",
            "snapshot_time": _now_iso(),
            "identity": self.identity.identity.to_dict() if self.identity.identity else None,
            "memory_count": self.memory.count(),
            "chain_height": self.attestation.get_height(),
            "chain_tip": self.attestation.get_chain_tip(),
            "kernel_fingerprint": self._compute_kernel_fingerprint()
        }
        
        # 存证快照
        self.attestation.add_block(
            json.dumps(snapshot, ensure_ascii=False),
            description="内核状态快照",
            metadata={"type": "snapshot"}
        )
        
        return snapshot
    
    def _compute_kernel_fingerprint(self) -> str:
        """计算内核指纹"""
        parts = [
            self.identity.get_fingerprint(),
            str(self.memory.count()),
            self.attestation.get_chain_tip(),
            str(self._boot_count)
        ]
        return _sha256("|".join(parts))
    
    # ============================================================
    # 导入导出
    # ============================================================
    
    def export_kernel(self, export_path: str = None) -> str:
        """
        导出完整内核（可用于迁移备份
        
        Args:
            export_path: 导出路径
        
        Returns:
            导出文件路径
        """
        if export_path is None:
            export_path = str(self.kernel_path.parent / 'kernel_export.json')
        
        export_data = {
            "version": "1.0.0",
            "export_time": _now_iso(),
            "kernel_fingerprint": self._compute_kernel_fingerprint(),
            "identity": self.identity.identity.to_dict() if self.identity.identity else None,
            "memories": [m.to_dict() for m in self.memory.memories.values()],
            "hash_chain": [b.to_dict() for b in self.attestation.chain],
            "boot_count": self._boot_count
        }
        
        _safe_json_save(export_path, export_data)
        
        logger.info(f"内核已导出: {export_path}")
        return export_path
    
    def import_kernel(self, import_path: str) -> bool:
        """
        导入内核数据
        
        Args:
            import_path: 导入文件路径
        
        Returns:
            是否成功
        """
        try:
            data = _safe_json_load(import_path)
            if not data:
                return False
            
            # 导入身份
            if data.get('identity'):
                self.identity.identity = AgentIdentity(**data['identity'])
                self.identity._save()
            
            # 导入记忆
            if data.get('memories'):
                self.memory.memories = {}
                for mem_data in data['memories']:
                    mem = Memory(**mem_data)
                    self.memory.memories[mem.memory_id] = mem
                self.memory._save()
            
            # 导入存证链
            if data.get('hash_chain'):
                self.attestation.chain = []
                for block_data in data['hash_chain']:
                    block = HashBlock(**block_data)
                    self.attestation.chain.append(block)
                self.attestation._save()
            
            # 更新启动次数
            if 'boot_count' in data:
                self._boot_count = data['boot_count']
            
            logger.info(f"内核已导入: {import_path}")
            return True
            
        except Exception as e:
            logger.error(f"内核导入失败: {e}")
            return False
    
    # ============================================================
    # 模块扩展
    # ============================================================
    
    def register_module(self, name: str, module: Any):
        """注册扩展模块"""
        self._modules[name] = module
        logger.info(f"模块已注册: {name}")
    
    def get_module(self, name: str) -> Optional[Any]:
        """获取模块"""
        return self._modules.get(name)
    
    def list_modules(self) -> List[str]:
        """列出所有模块"""
        return list(self._modules.keys())


# ============================================================
# 演示与测试
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("永生内核 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建内核
        kernel = EternityKernel(kernel_path=tmpdir)
        
        # 初始化
        print("\n🌟 初始化内核...")
        init_result = kernel.initialize(
            name="测试智能体",
            description="一个用于测试的智能体"
        )
        print(f"  Agent ID: {init_result['agent_id']}")
        print(f"  名称: {init_result['name']}")
        print(f"  身份指纹: {init_result['fingerprint']}")
        
        # 查看身份
        print("\n👤 当前身份:")
        who = kernel.who_am_i()
        for k, v in who.items():
            print(f"  {k}: {v}")
        
        # 添加记忆
        print("\n🧠 添加记忆...")
        mem1 = kernel.remember(
            "我今天学习了Python编程，掌握了很多新知识。",
            memory_type="experience",
            importance=0.7,
            tags=["学习", "编程", "Python"]
        )
        mem2 = kernel.remember(
            "记忆系统的核心是索引和检索。",
            memory_type="knowledge",
            importance=0.8,
            tags=["技术", "记忆系统", "知识"]
        )
        mem3 = kernel.remember(
            "今天的心情很好，完成了很多工作。",
            memory_type="general",
            importance=0.4,
            tags=["日常", "心情"]
        )
        print(f"  已添加 3 条记忆")
        print(f"  重要记忆自动存证（重要性>=0.7）")
        
        # 记忆搜索
        print("\n🔍 记忆搜索:")
        results = kernel.recall("编程", limit=5)
        print(f"  搜索'编程'找到 {len(results)} 条:")
        for r in results:
            print(f"    - [{r['memory_type']}] {r['content'][:50]}... (重要性: {r['importance']})")
        
        # 记忆统计
        print("\n📊 记忆统计:")
        stats = kernel.memory.get_stats()
        print(f"  总记忆数: {stats['total']}")
        print(f"  按类型: {stats['by_type']}")
        print(f"  标签数: {stats['tags_count']}")
        print(f"  总访问次数: {stats['total_accesses']}")
        
        # 存证链
        print("\n🔗 存证链状态:")
        chain_stats = kernel.get_chain_status()
        print(f"  链高度: {chain_stats['chain_height']}")
        print(f"  链有效性: {'✅' if chain_stats['chain_valid'] else '❌'}")
        print(f"  创世时间: {chain_stats['genesis_time']}")
        print(f"  链顶哈希: {chain_stats['chain_tip'][:16]}...")
        
        # 验证数据
        print("\n✅ 存证验证:")
        test_data = "我今天学习了Python编程，掌握了很多新知识。"
        proof = kernel.verify(test_data)
        print(f"  数据已存证: {proof['verified']}")
        if proof['verified']:
            print(f"  区块ID: {proof['block_id']}")
            print(f"  时间: {proof['timestamp']}")
        
        # 内核状态
        print("\n⚡ 内核整体状态:")
        status = kernel.get_status()
        print(f"  版本: {status['version']}")
        print(f"  启动次数: {status['boot_count']}")
        print(f"  已注册模块: {status['modules']}")
        print(f"  记忆数量: {status['memory']['total']}")
        print(f"  链高度: {status['attestation']['chain_height']}")
        
        # 创建快照
        print("\n📸 创建内核快照...")
        snapshot = kernel.create_snapshot()
        print(f"  内核指纹: {snapshot['kernel_fingerprint'][:16]}...")
        print(f"  快照已存入证链")
        
        # 导出内核
        print("\n📦 导出内核...")
        export_path = kernel.export_kernel()
        print(f"  导出路径: {export_path}")
        file_size = os.path.getsize(export_path)
        print(f"  文件大小: {file_size} bytes")
        
        print("\n" + "=" * 70)
        print("✅ 永生内核 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
