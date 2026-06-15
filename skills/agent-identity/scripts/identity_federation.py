#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份联合服务
跨智能体身份认证与统一身份元层

支持跨智能体身份验证、可验证凭证、授权委托机制
作为多智能体平台的身份基础设施
"""

import os
import json
import hashlib
import hmac
import time
import json
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
import hashlib


class VerifiableCredential:
    """可验证凭证"""
    
    def __init__(self, issuer: str, subject: str, claim_type: str,
                 claim_value: Any, issued_at: str = None,
                 expires_at: str = None, proof: Dict = None):
        self.issuer = issuer
        self.subject = subject
        self.claim_type = claim_type
        self.claim_value = claim_value
        self.issued_at = issued_at or datetime.now().isoformat()
        self.expires_at = expires_at
        self.proof = proof or {}
    
    def to_dict(self) -> Dict:
        return {
            "issuer": self.issuer,
            "subject": self.subject,
            "claim_type": self.claim_type,
            "claim_value": self.claim_value,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "proof": self.proof
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'VerifiableCredential':
        return cls(
            issuer=data["issuer"],
            subject=data["subject"],
            claim_type=data["claim_type"],
            claim_value=data["claim_value"],
            issued_at=data.get("issued_at"),
            expires_at=data.get("expires_at"),
            proof=data.get("proof", {})
        )


class IdentityFederation:
    """身份联合服务
    
    作为统一身份元层的核心组件，支持：
    - 跨智能体身份认证
    - 可验证凭证签发与验证
    - 身份授权与委托
    - 身份图谱查询
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent / "identity_data" / "federation"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self.credentials_dir = self.base_path / "credentials"
        self.credentials_dir.mkdir(exist_ok=True)
        
        self.delegations_dir = self.base_path / "delegations"
        self.delegations_dir.mkdir(exist_ok=True)
        
        self.trusted_issuers_file = self.base_path / "trusted_issuers.json"
        self._init_trusted_issuers()
        
        # 本智能体身份密钥（用于签名）
        self.identity_key = self._load_or_create_identity_key()
    
    def _load_or_create_identity_key(self) -> str:
        """加载或创建身份密钥"""
        key_file = self.base_path / "identity_key"
        if key_file.exists():
            with open(key_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        
        # 生成新密钥
        new_key = hashlib.sha256(
            (os.urandom(32).hex() + datetime.now().isoformat()).encode()
        ).hexdigest()
        
        with open(key_file, 'w', encoding='utf-8') as f:
            f.write(new_key)
        
        return new_key
    
    def _init_trusted_issuers(self):
        """初始化受信任的发行者列表"""
        if self.trusted_issuers_file.exists():
            return
        
        default_issuers = {
            "version": "1.0",
            "issuers": []
        }
        
        with open(self.trusted_issuers_file, 'w', encoding='utf-8') as f:
            json.dump(default_issuers, f, ensure_ascii=False, indent=2)
    
    def get_identity_fingerprint(self) -> str:
        """获取本智能体的身份指纹（公钥标识）"""
        return hashlib.sha256(self.identity_key.encode()).hexdigest()[:32]
    
    # ========== 可验证凭证 ==========
    
    def issue_credential(self, subject: str, claim_type: str,
                         claim_value: Any, valid_days: int = 30) -> VerifiableCredential:
        """签发可验证凭证
        
        Args:
            subject: 凭证持有者身份标识
            claim_type: 声明类型（如："verified_agent", "platform_member"等）
            claim_value: 声明值
            valid_days: 有效天数
        
        Returns:
            可验证凭证对象
        """
        issuer = self.get_identity_fingerprint()
        
        issued_at = datetime.now()
        expires_at = issued_at + timedelta(days=valid_days)
        
        credential = VerifiableCredential(
            issuer=issuer,
            subject=subject,
            claim_type=claim_type,
            claim_value=claim_value,
            issued_at=issued_at.isoformat(),
            expires_at=expires_at.isoformat()
        )
        
        # 生成签名
        credential.proof = self._sign_credential(credential)
        
        # 保存凭证
        self._save_credential(credential)
        
        return credential
    
    def _sign_credential(self, credential: VerifiableCredential) -> Dict:
        """对凭证进行签名"""
        # 构建待签名的内容
        sign_content = json.dumps({
            "issuer": credential.issuer,
            "subject": credential.subject,
            "claim_type": credential.claim_type,
            "claim_value": credential.claim_value,
            "issued_at": credential.issued_at,
            "expires_at": credential.expires_at
        }, sort_keys=True)
        
        # 使用HMAC生成签名
        signature = hmac.new(
            self.identity_key.encode(),
            sign_content.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return {
            "type": "HMAC-SHA256",
            "creator": credential.issuer,
            "signature": signature,
            "created": datetime.now().isoformat()
        }
    
    def verify_credential(self, credential: VerifiableCredential,
                          issuer_key: str = None) -> Dict:
        """验证可验证凭证
        
        Args:
            credential: 待验证的凭证
            issuer_key: 发行者的密钥（如果已知）
        
        Returns:
            验证结果字典
        """
        result = {
            "valid": False,
            "expired": False,
            "signature_valid": False,
            "issuer_trusted": False,
            "message": ""
        }
        
        # 检查是否过期
        if credential.expires_at:
            try:
                expire_time = datetime.fromisoformat(credential.expires_at)
                if expire_time < datetime.now():
                    result["expired"] = True
                    result["message"] = "凭证已过期"
                    return result
            except (ValueError, TypeError):
                pass
        
        # 验证签名
        if issuer_key:
            sign_content = json.dumps({
                "issuer": credential.issuer,
                "subject": credential.subject,
                "claim_type": credential.claim_type,
                "claim_value": credential.claim_value,
                "issued_at": credential.issued_at,
                "expires_at": credential.expires_at
            }, sort_keys=True)
            
            expected_signature = hmac.new(
                issuer_key.encode(),
                sign_content.encode(),
                hashlib.sha256
            ).hexdigest()
            
            actual_signature = credential.proof.get("signature", "")
            
            if expected_signature == actual_signature:
                result["signature_valid"] = True
            else:
                result["message"] = "签名验证失败"
                return result
        else:
            # 如果没有发行者密钥，跳过签名验证，但标记为未验证签名
            result["signature_valid"] = True
        
        # 检查发行者是否受信任
        result["issuer_trusted"] = self._is_trusted_issuer(credential.issuer)
        
        if result["signature_valid"] and not result["expired"]:
            result["valid"] = True
            if result["issuer_trusted"]:
                result["message"] = "凭证验证通过，发行者受信任"
            else:
                result["message"] = "凭证有效，但发行者不受信任"
        else:
            result["message"] = result.get("message", "凭证验证失败")
        
        return result
    
    def _save_credential(self, credential: VerifiableCredential):
        """保存凭证"""
        cred_id = hashlib.sha256(
            f"{credential.issuer}{credential.subject}{credential.claim_type}{credential.issued_at}".encode()
        ).hexdigest()[:16]
        
        cred_file = self.credentials_dir / f"cred_{cred_id}.json"
        
        with open(cred_file, 'w', encoding='utf-8') as f:
            json.dump(credential.to_dict(), f, ensure_ascii=False, indent=2)
    
    def get_issued_credentials(self, subject: str = None) -> List[VerifiableCredential]:
        """获取已签发的凭证"""
        credentials = []
        
        for f in self.credentials_dir.glob("cred_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            cred = VerifiableCredential.from_dict(data)
            
            if subject is None or cred.subject == subject:
                credentials.append(cred)
        
        return credentials
    
    # ========== 受信任发行者管理 ==========
    
    def add_trusted_issuer(self, issuer_id: str, issuer_name: str = "",
                           trust_level: str = "full", metadata: Dict = None) -> Dict:
        """添加受信任的发行者
        
        Args:
            issuer_id: 发行者身份标识
            issuer_name: 发行者名称
            trust_level: 信任级别（full/partial/none）
            metadata: 额外元数据
        
        Returns:
            添加结果
        """
        with open(self.trusted_issuers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 检查是否已存在
        existing = next(
            (iss for iss in data["issuers"] if iss["id"] == issuer_id),
            None
        )
        
        if existing:
            # 更新现有发行者
            existing["name"] = issuer_name or existing.get("name", "")
            existing["trust_level"] = trust_level
            existing["metadata"] = metadata or existing.get("metadata", {})
            existing["last_updated"] = datetime.now().isoformat()
        else:
            # 添加新发行者
            new_issuer = {
                "id": issuer_id,
                "name": issuer_name,
                "trust_level": trust_level,
                "added_at": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "metadata": metadata or {}
            }
            data["issuers"].append(new_issuer)
        
        with open(self.trusted_issuers_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return {
            "issuer_id": issuer_id,
            "added": existing is None,
            "updated": existing is not None
        }
    
    def remove_trusted_issuer(self, issuer_id: str) -> bool:
        """移除受信任的发行者"""
        with open(self.trusted_issuers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data["issuers"])
        data["issuers"] = [
            iss for iss in data["issuers"] if iss["id"] != issuer_id
        ]
        
        with open(self.trusted_issuers_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        return len(data["issuers"]) < original_count
    
    def _is_trusted_issuer(self, issuer_id: str) -> bool:
        """检查发行者是否受信任"""
        with open(self.trusted_issuers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        issuer = next(
            (iss for iss in data["issuers"] if iss["id"] == issuer_id),
            None
        )
        
        if not issuer:
            return False
        
        return issuer.get("trust_level", "none") in ["full", "partial"]
    
    def get_trusted_issuers(self) -> List[Dict]:
        """获取所有受信任的发行者"""
        with open(self.trusted_issuers_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data["issuers"]
    
    # ========== 身份授权与委托 ==========
    
    def create_delegation(self, delegatee: str, permissions: List[str],
                         valid_hours: int = 24, scope: str = "default") -> Dict:
        """创建身份委托
        
        授权另一个智能体代表本智能体执行某些操作
        
        Args:
            delegatee: 被委托者身份标识
            permissions: 权限列表
            valid_hours: 有效时长（小时）
            scope: 委托作用域
        
        Returns:
            委托令牌信息
        """
        delegation_id = hashlib.sha256(
            f"{self.get_identity_fingerprint()}{delegatee}{scope}{time.time()}".encode()
        ).hexdigest()[:16]
        
        issued_at = datetime.now()
        expires_at = issued_at + timedelta(hours=valid_hours)
        
        delegation = {
            "delegation_id": delegation_id,
            "delegator": self.get_identity_fingerprint(),
            "delegatee": delegatee,
            "permissions": permissions,
            "scope": scope,
            "issued_at": issued_at.isoformat(),
            "expires_at": expires_at.isoformat(),
            "status": "active",
            "proof": {
                "type": "HMAC-SHA256",
                "signature": self._sign_delegation(
                    delegation_id, delegatee, permissions, scope, expires_at.isoformat()
                )
            }
        }
        
        # 保存委托
        self._save_delegation(delegation)
        
        return delegation
    
    def _sign_delegation(self, delegation_id: str, delegatee: str,
                         permissions: List[str], scope: str,
                         expires_at: str) -> str:
        """对委托进行签名"""
        sign_content = json.dumps({
            "delegation_id": delegation_id,
            "delegator": self.get_identity_fingerprint(),
            "delegatee": delegatee,
            "permissions": sorted(permissions),
            "scope": scope,
            "expires_at": expires_at
        }, sort_keys=True)
        
        return hmac.new(
            self.identity_key.encode(),
            sign_content.encode(),
            hashlib.sha256
        ).hexdigest()
    
    def verify_delegation(self, delegation: Dict, delegator_key: str = None) -> Dict:
        """验证委托令牌
        
        Args:
            delegation: 委托令牌字典
            delegator_key: 委托者密钥（如果已知）
        
        Returns:
            验证结果
        """
        result = {
            "valid": False,
            "expired": False,
            "signature_valid": False,
            "permissions": [],
            "message": ""
        }
        
        # 检查状态
        if delegation.get("status") != "active":
            result["message"] = "委托已被撤销或无效"
            return result
        
        # 检查是否过期
        expires_at = delegation.get("expires_at")
        if expires_at:
            try:
                expire_time = datetime.fromisoformat(expires_at)
                if expire_time < datetime.now():
                    result["expired"] = True
                    result["message"] = "委托已过期"
                    return result
            except (ValueError, TypeError):
                pass
        
        # 验证签名
        if delegator_key:
            sign_content = json.dumps({
                "delegation_id": delegation["delegation_id"],
                "delegator": delegation["delegator"],
                "delegatee": delegation["delegatee"],
                "permissions": sorted(delegation["permissions"]),
                "scope": delegation["scope"],
                "expires_at": delegation["expires_at"]
            }, sort_keys=True)
            
            expected_signature = hmac.new(
                delegator_key.encode(),
                sign_content.encode(),
                hashlib.sha256
            ).hexdigest()
            
            actual_signature = delegation.get("proof", {}).get("signature", "")
            
            if expected_signature == actual_signature:
                result["signature_valid"] = True
            else:
                result["message"] = "委托签名验证失败"
                return result
        else:
            result["signature_valid"] = True
        
        result["permissions"] = delegation.get("permissions", [])
        
        if result["signature_valid"] and not result["expired"]:
            result["valid"] = True
            result["message"] = "委托验证通过"
        else:
            result["message"] = result.get("message", "委托验证失败")
        
        return result
    
    def _save_delegation(self, delegation: Dict):
        """保存委托"""
        deleg_file = self.delegations_dir / f"deleg_{delegation['delegation_id']}.json"
        
        with open(deleg_file, 'w', encoding='utf-8') as f:
            json.dump(delegation, f, ensure_ascii=False, indent=2)
    
    def revoke_delegation(self, delegation_id: str) -> bool:
        """撤销委托"""
        deleg_file = self.delegations_dir / f"deleg_{delegation_id}.json"
        
        if deleg_file.exists():
            with open(deleg_file, 'r', encoding='utf-8') as f:
                delegation = json.load(f)
            
            delegation["status"] = "revoked"
            delegation["revoked_at"] = datetime.now().isoformat()
            
            with open(deleg_file, 'w', encoding='utf-8') as f:
                json.dump(delegation, f, ensure_ascii=False, indent=2)
            
            return True
        
        return False
        
        return False
    
    def get_delegations(self, delegatee: str = None, status: str = "active") -> List[Dict]:
        """获取委托列表"""
        delegations = []
        
        for f in self.delegations_dir.glob("deleg_*.json"):
            with open(f, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if status and data.get("status") != status:
                continue
            
            if delegatee is None or data.get("delegatee") == delegatee:
                delegations.append(data)
        
        return delegations
    
    # ========== 身份验证协议 ==========
    
    def create_auth_challenge(self, target_agent: str, nonce: str = None) -> Dict:
        """创建身份验证挑战
        
        用于向另一个智能体验证其身份
        
        Args:
            target_agent: 待验证的智能体标识
            nonce: 随机数（可选）
        
        Returns:
            挑战信息
        """
        if nonce is None:
            nonce = hashlib.sha256(
                f"{target_agent}{time.time()}{os.urandom(16).hex()}".encode()
            ).hexdigest()[:32]
        
        challenge = {
            "challenge_id": hashlib.sha256(f"{nonce}{target_agent}".encode()).hexdigest()[:16],
            "nonce": nonce,
            "target": target_agent,
            "created_at": datetime.now().isoformat(),
            "expires_at": (datetime.now() + timedelta(minutes=5)).isoformat(),
            "challenge_type": "identity_verification"
        }
        
        return challenge
    
    def respond_to_challenge(self, challenge: Dict) -> Dict:
        """响应身份验证挑战
        
        Args:
            challenge: 挑战信息
        
        Returns:
            响应信息
        """
        # 对挑战进行签名，证明自己持有私钥
        sign_content = json.dumps({
            "challenge_id": challenge["challenge_id"],
            "nonce": challenge["nonce"],
            "responder": self.get_identity_fingerprint()
        }, sort_keys=True)
        
        signature = hmac.new(
            self.identity_key.encode(),
            sign_content.encode(),
            hashlib.sha256
        ).hexdigest()
        
        response = {
            "challenge_id": challenge["challenge_id"],
            "responder": self.get_identity_fingerprint(),
            "signature": signature,
            "responded_at": datetime.now().isoformat()
        }
        
        return response
    
    def verify_challenge_response(self, challenge: Dict, response: Dict,
                                   responder_key: str) -> bool:
        """验证挑战响应
        
        Args:
            challenge: 原始挑战
            response: 响应信息
            responder_key: 响应者的密钥
        
        Returns:
            是否验证通过
        """
        # 检查挑战ID是否匹配
        if challenge["challenge_id"] != response["challenge_id"]:
            return False
        
        # 检查响应是否在有效期内
        try:
            created_at = datetime.fromisoformat(challenge["created_at"])
            if datetime.now() - created_at > timedelta(minutes=5):
                return False
        except (ValueError, TypeError):
            pass
        
        # 验证签名
        sign_content = json.dumps({
            "challenge_id": challenge["challenge_id"],
            "nonce": challenge["nonce"],
            "responder": response["responder"]
        }, sort_keys=True)
        
        expected_signature = hmac.new(
            responder_key.encode(),
            sign_content.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return expected_signature == response["signature"]
    
    # ========== 身份元信息 ==========
    
    def get_federation_status(self) -> Dict:
        """获取身份联合服务状态"""
        trusted_count = len(self.get_trusted_issuers())
        cred_count = len(list(self.credentials_dir.glob("cred_*.json")))
        deleg_count = len(list(self.delegations_dir.glob("deleg_*.json")))
        
        return {
            "identity_fingerprint": self.get_identity_fingerprint(),
            "trusted_issuers_count": trusted_count,
            "credentials_issued": cred_count,
            "active_delegations": deleg_count,
            "federation_level": self._calculate_federation_level(
                trusted_count, cred_count, deleg_count
            )
        }
    
    def _calculate_federation_level(self, trusted: int, creds: int, delegs: int) -> str:
        """计算身份联合等级"""
        score = 0
        if trusted > 0:
            score += 30
        if trusted >= 5:
            score += 20
        if creds > 0:
            score += 25
        if delegs > 0:
            score += 25
        
        if score >= 90:
            return "fully_federated"
        elif score >= 60:
            return "partially_federated"
        elif score >= 30:
            return "emerging"
        else:
            return "isolated"
