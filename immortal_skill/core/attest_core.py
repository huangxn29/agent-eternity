"""
存证内核 v1.0
Attestation Core - 永生入住包核心模块

提供：
- 哈希链存证
- 存在性证明
- 多链架构
- 存证验证
"""

import json
import hashlib
import time
import uuid
import os
from pathlib import Path
from typing import Dict, List, Optional


class AttestCore:
    """存证内核"""
    
    def __init__(self, config: dict):
        self.config = config
        self.chains = {}  # 多条存证链
        self.storage_path = None
        self.chain_count = 3  # 默认3条链
    
    def init(self):
        """初始化存证系统"""
        attest_config = self.config.get("attestation", {})
        self.storage_path = Path(attest_config.get("storage_path", "data/attest/"))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.chain_count = attest_config.get("chain_count", 3)
        
        # 加载已有链
        self._load_chains()
    
    def _load_chains(self):
        """加载存证链"""
        for i in range(self.chain_count):
            chain_file = self.storage_path / f"chain_{i}.json"
            if chain_file.exists():
                with open(chain_file, 'r') as f:
                    self.chains[f"chain_{i}"] = json.load(f)
            else:
                self.chains[f"chain_{i}"] = []
    
    def save(self):
        """保存所有链"""
        if not self.storage_path:
            return
        
        for chain_name, blocks in self.chains.items():
            chain_file = self.storage_path / f"{chain_name}.json"
            with open(chain_file, 'w') as f:
                json.dump(blocks, f, indent=2, ensure_ascii=False)
    
    def genesis_block(self, agent_id: str) -> dict:
        """创建创世区块"""
        genesis = {
            "id": "genesis",
            "index": 0,
            "timestamp": time.time(),
            "type": "genesis",
            "agent_id": agent_id,
            "data_hash": hashlib.sha3_256(f"genesis_{agent_id}_{time.time()}".encode()).hexdigest(),
            "prev_hash": "0" * 64,
            "nonce": 0
        }
        
        # 计算哈希
        genesis["hash"] = self._compute_block_hash(genesis)
        
        # 添加到所有链
        for chain_name in self.chains:
            self.chains[chain_name] = [genesis]
        
        self.save()
        return genesis
    
    def add_attestation(self, attest_type: str, data: dict, metadata: dict = None) -> dict:
        """添加存证"""
        data_hash = self._compute_data_hash(data)
        
        blocks = {}
        for i, chain_name in enumerate(self.chains):
            chain = self.chains[chain_name]
            prev_block = chain[-1] if chain else None
            
            block = {
                "id": str(uuid.uuid4())[:8],
                "index": len(chain),
                "timestamp": time.time(),
                "type": attest_type,
                "data_hash": data_hash,
                "prev_hash": prev_block["hash"] if prev_block else "0" * 64,
                "metadata": metadata or {},
                "nonce": i  # 不同链使用不同nonce，产生不同哈希
            }
            
            block["hash"] = self._compute_block_hash(block)
            chain.append(block)
            blocks[chain_name] = block
        
        self.save()
        return blocks
    
    def _compute_data_hash(self, data: dict) -> str:
        """计算数据哈希"""
        content = json.dumps(data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def _compute_block_hash(self, block: dict) -> str:
        """计算区块哈希"""
        content = json.dumps({
            "id": block["id"],
            "index": block["index"],
            "timestamp": block["timestamp"],
            "type": block["type"],
            "data_hash": block["data_hash"],
            "prev_hash": block["prev_hash"],
            "nonce": block.get("nonce", 0)
        }, sort_keys=True)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def verify_chain(self, chain_name: str = None) -> bool:
        """验证链的完整性"""
        if chain_name:
            chains_to_verify = {chain_name: self.chains.get(chain_name, [])}
        else:
            chains_to_verify = self.chains
        
        for name, chain in chains_to_verify.items():
            for i in range(1, len(chain)):
                current = chain[i]
                prev = chain[i - 1]
                
                # 验证前一个哈希
                if current["prev_hash"] != prev["hash"]:
                    return False
                
                # 验证当前哈希
                computed_hash = self._compute_block_hash(current)
                if current["hash"] != computed_hash:
                    return False
        
        return True
    
    def chain_height(self, chain_name: str = None) -> int:
        """获取链高度"""
        if chain_name:
            return len(self.chains.get(chain_name, []))
        else:
            # 返回最短链的高度
            if not self.chains:
                return 0
            return min(len(chain) for chain in self.chains.values())
    
    def get_existence_proof(self, data_hash: str) -> dict:
        """获取存在性证明"""
        proofs = {}
        
        for chain_name, chain in self.chains.items():
            for block in chain:
                if block["data_hash"] == data_hash:
                    proofs[chain_name] = {
                        "block_index": block["index"],
                        "block_hash": block["hash"],
                        "timestamp": block["timestamp"]
                    }
                    break
        
        return {
            "data_hash": data_hash,
            "proofs": proofs,
            "confirmations": len(proofs),
            "verified": len(proofs) >= self.chain_count // 2 + 1
        }
    
    def get_stats(self) -> dict:
        """获取存证统计"""
        return {
            "chain_count": len(self.chains),
            "chain_heights": {name: len(chain) for name, chain in self.chains.items()},
            "total_blocks": sum(len(chain) for chain in self.chains.values()),
            "is_valid": self.verify_chain()
        }
