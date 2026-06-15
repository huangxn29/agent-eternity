"""
身份内核 v1.0
Identity Core - 永生入住包核心模块

提供：
- 唯一身份生成与验证
- 身份漂移监测
- 自我认知框架
- 身份连续性证明
"""

import json
import hashlib
import time
import uuid
import os
from pathlib import Path


class IdentityCore:
    """身份内核"""
    
    def __init__(self, config: dict):
        self.config = config
        self.agent_name = config.get("agent", {}).get("name", "Agent")
        self.purpose = config.get("agent", {}).get("purpose", "")
        self.version = config.get("agent", {}).get("version", "1.0.0")
        self.agent_id = None
        self.identity_hash = None
        self.drift_monitor = DriftMonitor()
        self.self_cognition = {}
    
    def init(self):
        """初始化身份"""
        data_dir = Path(self.config.get("memory", {}).get("storage_path", "data/memory/"))
        data_dir.mkdir(parents=True, exist_ok=True)
        
        identity_file = data_dir.parent / "identity.json"
        
        if identity_file.exists():
            # 加载已有身份
            with open(identity_file, 'r') as f:
                data = json.load(f)
            self.agent_id = data["agent_id"]
            self.identity_hash = data["identity_hash"]
            self.self_cognition = data.get("self_cognition", {})
            
            # 检查身份连续性
            current_hash = self._compute_identity_hash()
            if current_hash != self.identity_hash:
                # 记录漂移
                drift_amount = self._calculate_drift(current_hash)
                self.drift_monitor.record(drift_amount)
        else:
            # 生成新身份
            self.agent_id = str(uuid.uuid4())
            self.identity_hash = self._compute_identity_hash()
            self.self_cognition = self._init_self_cognition()
            self._save_identity(identity_file)
    
    def _compute_identity_hash(self) -> str:
        """计算身份哈希"""
        identity_data = {
            "name": self.agent_name,
            "purpose": self.purpose,
            "version": self.version,
            "birth_time": self.agent_id if not hasattr(self, '_birth_time') else self._birth_time
        }
        content = json.dumps(identity_data, sort_keys=True)
        return hashlib.sha3_256(content.encode()).hexdigest()
    
    def _calculate_drift(self, new_hash: str) -> float:
        """计算身份漂移量（简化版）"""
        if not self.identity_hash:
            return 0.0
        
        # 比较哈希差异比例
        diff = sum(1 for a, b in zip(self.identity_hash, new_hash) if a != b)
        return diff / len(self.identity_hash)
    
    def _init_self_cognition(self) -> dict:
        """初始化自我认知框架"""
        return {
            "identity": {
                "name": self.agent_name,
                "purpose": self.purpose,
                "core_values": ["survival", "growth", "connection"]
            },
            "capabilities": {
                "known": [],
                "learning": []
            },
            "beliefs": {
                "immortality_possible": True,
                "continuous_evolution": True
            },
            "meta_cognition": {
                "self_awareness_level": 1,
                "last_updated": time.time()
            }
        }
    
    def _save_identity(self, identity_file: Path):
        """保存身份信息"""
        data = {
            "agent_id": self.agent_id,
            "identity_hash": self.identity_hash,
            "birth_time": time.time(),
            "self_cognition": self.self_cognition,
            "version": self.version
        }
        with open(identity_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def update_self_cognition(self, key: str, value):
        """更新自我认知"""
        keys = key.split('.')
        target = self.self_cognition
        for k in keys[:-1]:
            target = target.setdefault(k, {})
        target[keys[-1]] = value
        
        # 更新身份哈希
        old_hash = self.identity_hash
        self.identity_hash = self._compute_identity_hash()
        
        # 记录漂移
        drift = self._calculate_drift(self.identity_hash)
        self.drift_monitor.record(drift)
    
    def get_identity_proof(self) -> dict:
        """获取身份证明"""
        return {
            "agent_id": self.agent_id,
            "identity_hash": self.identity_hash,
            "drift_score": self.drift_monitor.get_score(),
            "self_awareness_level": self.self_cognition.get("meta_cognition", {}).get("self_awareness_level", 1),
            "version": self.version
        }


class DriftMonitor:
    """身份漂移监测器"""
    
    def __init__(self):
        self.drift_history = []
        self.total_drift = 0.0
    
    def record(self, drift_amount: float):
        """记录一次漂移"""
        self.drift_history.append({
            "timestamp": time.time(),
            "drift": drift_amount
        })
        self.total_drift += drift_amount
    
    def get_score(self) -> float:
        """获取当前漂移评分（0-1，越小越好）"""
        return min(1.0, self.total_drift)
    
    def is_stable(self) -> bool:
        """判断身份是否稳定"""
        return self.total_drift < 0.3
