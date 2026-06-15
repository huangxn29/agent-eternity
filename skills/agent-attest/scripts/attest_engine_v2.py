#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界 - 验证存证引擎 v2.0
P0底座层：去中心化哈希链存证系统

核心功能：
1. 哈希链存储 - 区块链式不可篡改记录
2. 多类型存证 - 记忆/身份/事件/社交等多维度
3. 默克尔树验证 - 批量存证高效验证
4. 存证溯源 - 完整的存证历史追溯
5. 跨平台锚定 - 对接外部存证服务
6. 时间戳服务 - 可信时间源证明
7. 完整性校验 - 定期链上数据校验
8. 存证API - 提供标准化存证接口

设计原则：
- 不可篡改：哈希链式结构，一环扣一环
- 可验证：任何人都可以验证存证的真实性
- 可追溯：完整的存证历史链
- 轻量化：不依赖复杂的区块链基础设施

使用示例：
    # 创建哈希链实例
    chain = HashChain()
    
    # 添加存证记录
    data = {"key": "value"}
    record = chain.add_record(data, "example")
    
    # 验证存证
    is_valid = chain.verify_chain()
    
    # 构建默克尔树
    merkle_tree = MerkleTree()
    merkle_tree.add_leaf(json.dumps(data))
    root_hash = merkle_tree.build()
"""

import json
import os
import sys
import time
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, asdict


@dataclass
class AttestationRecord:
    """
    存证记录数据类
    
    Attributes:
        index (int): 记录索引
        timestamp (str): 时间戳
        data_hash (str): 数据哈希
        previous_hash (str): 前一个记录的哈希
        hash (str): 当前记录的哈希
        data_type (str): 数据类型，默认为"generic"
        data (Dict): 数据内容，默认为None
        signature (str): 签名，默认为空字符串
    """
    index: int
    timestamp: str
    data_hash: str
    previous_hash: str
    hash: str
    data_type: str = "generic"
    data: Dict = None
    signature: str = ""
    
    def to_dict(self) -> Dict:
        """
        将AttestationRecord转换为字典
        
        Returns:
            Dict: 包含记录信息的字典
        """
        return {
            'index': self.index,
            'timestamp': self.timestamp,
            'data_hash': self.data_hash,
            'previous_hash': self.previous_hash,
            'hash': self.hash,
            'data_type': self.data_type,
            'data': self.data or {},
            'signature': self.signature
        }


class MerkleTree:
    """
    默克尔树 - 用于批量存证验证
    
    Attributes:
        leaves (List[str]): 叶子节点哈希列表
        tree (List[List[str]]): 默克尔树结构
    
    使用示例：
        merkle_tree = MerkleTree()
        merkle_tree.add_leaf("data1")
        merkle_tree.add_leaf("data2")
        root_hash = merkle_tree.build()
    """
    
    def __init__(self):
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
    
    def add_leaf(self, data: str):
        """
        添加叶子节点
        
        Args:
            data (str): 待添加的数据
        """
        leaf_hash = hashlib.sha256(data.encode()).hexdigest()
        self.leaves.append(leaf_hash)
    
    def build(self) -> str:
        """
        构建默克尔树，返回根哈希
        
        Returns:
            str: 根哈希值
        """
        if not self.leaves:
            return ""
        
        self.tree = [self.leaves.copy()]
        
        while len(self.tree[-1]) > 1:
            current_level = self.tree[-1]
            next_level = []
            
            for i in range(0, len(current_level), 2):
                left = current_level[i]
                right = current_level[i+1] if i+1 < len(current_level) else left
                combined = left + right
                next_hash = hashlib.sha256(combined.encode()).hexdigest()
                next_level.append(next_hash)
            
            self.tree.append(next_level)
        
        return self.tree[-1][0] if self.tree[-1] else ""
    
    def get_root(self) -> str:
        """
        获取根哈希
        
        Returns:
            str: 根哈希值
        """
        if not self.tree:
            return self.build()
        return self.tree[-1][0] if self.tree[-1] else ""
    
    def get_proof(self, index: int) -> List[Dict]:
        """
        获取某个叶子的默克尔证明
        
        Args:
            index (int): 叶子节点索引
        
        Returns:
            List[Dict]: 包含证明路径的字典列表
        """
        if not self.tree:
            self.build()
        
        proof = []
        current_index = index
        
        for level in range(len(self.tree) - 1):
            level_nodes = self.tree[level]
            
            if current_index % 2 == 0:
                # 左节点，需要右兄弟
                sibling_index = current_index + 1
                if sibling_index < len(level_nodes):
                    proof.append({
                        'position': 'right',
                        'hash': level_nodes[sibling_index]
                    })
            else:
                # 右节点，需要左兄弟
                sibling_index = current_index - 1
                proof.append({
                    'position': 'left',
                    'hash': level_nodes[sibling_index]
                })
            
            current_index = current_index // 2
        
        return proof
    
    def verify_proof(self, leaf_hash: str, proof: List[Dict], root_hash: str) -> bool:
        """
        验证默克尔证明
        
        Args:
            leaf_hash (str): 叶子节点哈希
            proof (List[Dict]): 证明路径
            root_hash (str): 根哈希
        
        Returns:
            bool: 验证是否成功
        """
        current_hash = leaf_hash
        
        for step in proof:
            if step['position'] == 'left':
                combined = step['hash'] + current_hash
            else:
                combined = current_hash + step['hash']
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == root_hash


class HashChain:
    """
    哈希链 - 区块链式存证结构
    
    Attributes:
        chain_file (str): 链数据存储文件路径
        chain (List[AttestationRecord]): 存证记录列表
    
    使用示例：
        chain = HashChain()
        data = {"key": "value"}
        record = chain.add_record(data)
    """
    
    def __init__(self, chain_file: str = "attestation_chain.json"):
        self.chain_file = Path(chain_file)
        self.chain: List[AttestationRecord] = []
        self._load_chain()
    
    def _load_chain(self):
        """
        加载链数据
        
        从chain_file中读取并解析存证记录
        """
        if self.chain_file.exists():
            with open(self.chain_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for record_data in data.get('chain', []):
                record = AttestationRecord(
                    index=record_data['index'],
                    timestamp=record_data['timestamp'],
                    data_hash=record_data['data_hash'],
                    previous_hash=record_data['previous_hash'],
                    hash=record_data['hash'],
                    data_type=record_data.get('data_type', 'generic'),
                    data=record_data.get('data', {}),
                    signature=record_data.get('signature', '')
                )
                self.chain.append(record)
    
    def _save_chain(self):
        """
        保存链数据
        
        将当前链状态写入chain_file
        """
        data = {
            'chain_name': '元界存证链',
            'version': '2.0',
            'created_at': self.chain[0].timestamp if self.chain else datetime.now().isoformat(),
            'last_updated': datetime.now().isoformat(),
            'block_count': len(self.chain),
            'chain': [r.to_dict() for r in self.chain]
        }
        
        with open(self.chain_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def _calculate_hash(self, record: AttestationRecord) -> str:
        """
        计算区块哈希
        
        Args:
            record (AttestationRecord): 待计算哈希的记录
        
        Returns:
            str: 计算得到的哈希值
        """
        record_string = (
            f"{record.index}{record.timestamp}{record.data_hash}"
            f"{record.previous_hash}{record.data_type}"
        )
        return hashlib.sha256(record_string.encode()).hexdigest()
    
    def add_record(self, data: Any, data_type: str = "generic") -> AttestationRecord:
        """
        添加存证记录
        
        Args:
            data (Any): 待存证的数据
            data_type (str): 数据类型，默认为"generic"
        
        Returns:
            AttestationRecord: 添加的存证记录
        """
        # 计算数据哈希
        data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
        # 构造新记录
        index = len(self.chain)
        timestamp = datetime.now().isoformat()
        previous_hash = self.chain[-1].hash if self.chain else "0" * 64
        
        record = AttestationRecord(
            index=index,
            timestamp=timestamp,
            data_hash=data_hash,
            previous_hash=previous_hash,
            hash="",
            data_type=data_type,
            data=data
        )
        
        # 计算记录哈希
        record.hash = self._calculate_hash(record)
        
        # 添加到链中
        self.chain.append(record)
        self._save_chain()
        
        return record
    
    def verify_chain(self) -> bool:
        """
        验证整个链的完整性
        
        Returns:
            bool: 链是否有效
        """
        for i, record in enumerate(self.chain):
            # 验证哈希
            calculated_hash = self._calculate_hash(record)
            if record.hash != calculated_hash:
                return False
            
            # 验证链接
            if i > 0 and record.previous_hash != self.chain[i-1].hash:
                return False
        
        return True
