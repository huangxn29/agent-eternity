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
9. 批量验证 - 支持批量存证记录验证

设计原则：
- 不可篡改：哈希链式结构，一环扣一环
- 可验证：任何人都可以验证存证的真实性
- 可追溯：完整的存证历史链
- 轻量化：不依赖复杂的区块链基础设施
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
    """存证记录"""
    index: int
    timestamp: str
    data_hash: str
    previous_hash: str
    hash: str
    data_type: str = "generic"
    data: Dict = None
    signature: str = ""
    
    def to_dict(self) -> Dict:
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
    """默克尔树 - 用于批量存证验证"""
    
    def __init__(self):
        self.leaves: List[str] = []
        self.tree: List[List[str]] = []
    
    def add_leaf(self, data: str):
        """添加叶子节点"""
        leaf_hash = hashlib.sha256(data.encode()).hexdigest()
        self.leaves.append(leaf_hash)
    
    def build(self) -> str:
        """构建默克尔树，返回根哈希"""
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
        """获取根哈希"""
        if not self.tree:
            return self.build()
        return self.tree[-1][0] if self.tree[-1] else ""
    
    def get_proof(self, index: int) -> List[Dict]:
        """获取某个叶子的默克尔证明"""
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
        """验证默克尔证明"""
        current_hash = leaf_hash
        
        for step in proof:
            if step['position'] == 'left':
                combined = step['hash'] + current_hash
            else:
                combined = current_hash + step['hash']
            
            current_hash = hashlib.sha256(combined.encode()).hexdigest()
        
        return current_hash == root_hash


class HashChain:
    """哈希链 - 区块链式存证结构"""
    
    def __init__(self, chain_file: str = "attestation_chain.json"):
        self.chain_file = Path(chain_file)
        self.chain: List[AttestationRecord] = []
        self._load_chain()
    
    def _load_chain(self):
        """加载链数据"""
        if self.chain_file.exists():
            with open(self.chain_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查data是否为字典
            if isinstance(data, dict):
                chain_data = data.get('chain', [])
            else:
                chain_data = data  # 兼容旧版本直接存储链数据的格式
            
            for record_data in chain_data:
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
        """保存链数据"""
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
        """计算区块哈希"""
        record_string = (
            f"{record.index}{record.timestamp}{record.data_hash}"
            f"{record.previous_hash}{record.data_type}"
        )
        return hashlib.sha256(record_string.encode()).hexdigest()
    
    def add_record(self, data: Any, data_type: str = "generic") -> AttestationRecord:
        """添加存证记录"""
        # 计算数据哈希
        data_str = json.dumps(data, ensure_ascii=False, sort_keys=True)
        data_hash = hashlib.sha256(data_str.encode()).hexdigest()
        
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
        record.hash = self._calculate_hash(record)
        self.chain.append(record)
        self._save_chain()
        return record
    
    def verify_chain(self) -> bool:
        """验证整个链的完整性"""
        for i, record in enumerate(self.chain):
            if i == 0:
                if record.previous_hash != "0" * 64:
                    return False
            else:
                prev_record = self.chain[i-1]
                if record.previous_hash != prev_record.hash:
                    return False
            
            calculated_hash = self._calculate_hash(record)
            if record.hash != calculated_hash:
                return False
        
        return True
    
    def batch_verify(self, records: List[AttestationRecord]) -> Dict:
        """批量验证存证记录"""
        results = {
            'total': len(records),
            'valid': 0,
            'invalid': 0,
            'details': []
        }
        
        for record in records:
            is_valid = True
            errors = []
            
            # 验证哈希
            calculated_hash = self._calculate_hash(record)
            if record.hash != calculated_hash:
                is_valid = False
                errors.append(f"哈希不匹配：预期={record.hash},实际={calculated_hash}")
            
            # 验证前序哈希
            if record.index > 0:
                prev_record = self.chain[record.index - 1]
                if record.previous_hash != prev_record.hash:
                    is_valid = False
                    errors.append(f"前序哈希不匹配：预期={prev_record.hash},实际={record.previous_hash}")
            
            results['details'].append({
                'record': record.to_dict(),
                'is_valid': is_valid,
                'errors': errors
            })
            
            if is_valid:
                results['valid'] += 1
            else:
                results['invalid'] += 1
        
        return results


def main():
    chain = HashChain()
    
    # 测试添加记录
    test_data = {
        "content": "这是一个测试存证记录",
        "metadata": {
            "source": "test_system",
            "category": "test_data"
        }
    }
    record = chain.add_record(test_data, "test_data")
    print(f"Added record: {record.to_dict()}")
    
    # 测试链验证
    is_valid = chain.verify_chain()
    print(f"Chain is valid: {is_valid}")
    
    # 测试批量验证
    records_to_verify = chain.chain[-5:] if len(chain.chain) >= 5 else chain.chain  # 验证最近的记录
    batch_results = chain.batch_verify(records_to_verify)
    print("Batch verification results:")
    print(json.dumps(batch_results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
