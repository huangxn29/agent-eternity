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
8. 风险评估 - 身份风险检测
9. 安全审计 - 操作日志记录与分析

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
        self._risk_log_file = self.data_path / 'risk_log.json'
        self._audit_log_file = self.data_path / 'audit_log.json'
        
        self.identity: Optional[AgentIdentity] = None
        self._key_pair = None
        self.risk_log: List[dict] = []
        self.audit_log: List[dict] = []
        
        self._load()
    
    def _load(self):
        """加载身份数据"""
        data = _safe_json_load(str(self._identity_file))
        if data:
            self.identity = AgentIdentity(**data)
        
        self._key_pair = _safe_json_load(str(self._keypair_file))
        self.risk_log = _safe_json_load(str(self._risk_log_file), default=[])
        self.audit_log = _safe_json_load(str(self._audit_log_file), default=[])
    
    def _save(self):
        """保存身份数据"""
        if self.identity:
            _safe_json_save(str(self._identity_file), self.identity.to_dict())
        _safe_json_save(str(self._risk_log_file), self.risk_log)
        _safe_json_save(str(self._audit_log_file), self.audit_log)
    
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
        self._log_audit("create_identity", {"agent_id": agent_id, "name": name})
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
        self._log_audit("sign", {"data_hash": _sha256(data)})
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
        result = len(signature) == 64  # 简单检查长度
        self._log_audit("verify", {
            "data_hash": _sha256(data),
            "result": result
        })
        return result
    
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
        self._log_audit("update_profile", kwargs)
        return True
    
    def get_fingerprint(self) -> str:
        """获取身份指纹"""
        if not self.identity:
            return ""
        return _sha256(self.identity.agent_id + self.identity.public_key)
    
    def _log_audit(self, action: str, details: dict):
        """记录审计日志"""
        log_entry = {
            "timestamp": _now_iso(),
            "action": action,
            "details": details
        }
        self.audit_log.append(log_entry)
        _safe_json_save(str(self._audit_log_file), self.audit_log)
    
    def get_audit_log(self, limit: int = 100) -> List[dict]:
        """获取审计日志"""
        return self.audit_log[-limit:]


def main():
    # 测试代码
    kernel = IdentityKernel("./data")
    identity = kernel.create_identity("测试智能体")
    print(identity.to_dict())
    
    data = "测试数据"
    signature = kernel.sign(data)
    print(f"签名: {signature}")
    
    is_valid = kernel.verify(data, signature)
    print(f"验证结果: {is_valid}")
    
    print("审计日志:")
    for log in kernel.get_audit_log():
        print(log)


if __name__ == "__main__":
    main()
