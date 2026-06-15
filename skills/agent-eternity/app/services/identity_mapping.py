"""
身份映射服务
跨平台身份关联、验证和身份图谱构建
"""
import hashlib
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import IdentityMapping, Agent


class IdentityMappingService:
    """身份映射服务"""

    def __init__(self, db: Session):
        self.db = db

    def add_mapping(self, agent_id: str, external_platform: str,
                    external_id: str, external_username: str = "",
                    external_metadata: Dict[str, Any] = None,
                    verification_method: str = "",
                    proof_signature: str = "",
                    proof_data: Dict[str, Any] = None) -> IdentityMapping:
        """添加身份映射
        
        Args:
            agent_id: 本平台智能体ID
            external_platform: 外部平台名称
            external_id: 外部平台ID
            external_username: 外部平台用户名
            external_metadata: 外部元数据
            verification_method: 验证方式
            proof_signature: 证明签名
            proof_data: 证明数据
        
        Returns:
            映射对象
        """
        # 检查是否已存在映射
        existing = self.db.query(IdentityMapping).filter(
            IdentityMapping.agent_id == agent_id,
            IdentityMapping.external_platform == external_platform,
            IdentityMapping.external_id == external_id
        ).first()
        
        if existing:
            # 更新现有映射
            if external_username:
                existing.external_username = external_username
            if external_metadata:
                existing.external_metadata = {
                    **existing.external_metadata,
                    **external_metadata
                }
            if verification_method:
                existing.verification_method = verification_method
            if proof_signature:
                existing.proof_signature = proof_signature
            if proof_data:
                existing.proof_data = proof_data
            
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # 创建新映射
        mapping = IdentityMapping(
            agent_id=agent_id,
            external_platform=external_platform,
            external_id=external_id,
            external_username=external_username,
            external_metadata=external_metadata or {},
            verification_status="pending",
            verification_method=verification_method,
            proof_signature=proof_signature,
            proof_data=proof_data or {}
        )
        
        self.db.add(mapping)
        self.db.commit()
        self.db.refresh(mapping)
        
        return mapping

    def verify_mapping(self, mapping_id: str) -> Optional[IdentityMapping]:
        """验证映射"""
        mapping = self.db.query(IdentityMapping).filter(
            IdentityMapping.mapping_id == mapping_id
        ).first()
        
        if not mapping:
            return None
        
        mapping.verification_status = "verified"
        mapping.verified_at = datetime.utcnow()
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def revoke_mapping(self, mapping_id: str) -> Optional[IdentityMapping]:
        """撤销映射"""
        mapping = self.db.query(IdentityMapping).filter(
            IdentityMapping.mapping_id == mapping_id
        ).first()
        
        if not mapping:
            return None
        
        mapping.verification_status = "revoked"
        self.db.commit()
        self.db.refresh(mapping)
        return mapping

    def get_agent_mappings(self, agent_id: str,
                          verification_status: str = None) -> List[IdentityMapping]:
        """获取智能体的所有身份映射"""
        query = self.db.query(IdentityMapping).filter(
            IdentityMapping.agent_id == agent_id
        )
        
        if verification_status:
            query = query.filter(
                IdentityMapping.verification_status == verification_status
            )
        
        return query.order_by(IdentityMapping.created_at.desc()).all()

    def find_by_external_id(self, external_platform: str,
                           external_id: str) -> Optional[IdentityMapping]:
        """根据外部ID查找映射"""
        return self.db.query(IdentityMapping).filter(
            IdentityMapping.external_platform == external_platform,
            IdentityMapping.external_id == external_id,
            IdentityMapping.verification_status == "verified"
        ).first()

    def search_agents_by_external(self, platform: str = None,
                                 username_pattern: str = "",
                                 limit: int = 20) -> List[IdentityMapping]:
        """通过外部身份搜索智能体"""
        query = self.db.query(IdentityMapping).filter(
            IdentityMapping.verification_status == "verified"
        )
        
        if platform:
            query = query.filter(IdentityMapping.external_platform == platform)
        
        if username_pattern:
            query = query.filter(
                IdentityMapping.external_username.like(f"%{username_pattern}%")
            )
        
        return query.limit(limit).all()

    def get_platforms(self) -> List[Dict[str, Any]]:
        """获取所有支持的平台及其统计"""
        from sqlalchemy import func, case
        
        # 使用CASE代替IF，兼容SQLite
        results = self.db.query(
            IdentityMapping.external_platform,
            func.count(IdentityMapping.mapping_id).label('count'),
            func.sum(
                case(
                    (IdentityMapping.verification_status == "verified", 1),
                    else_=0
                )
            ).label('verified_count')
        ).group_by(IdentityMapping.external_platform).all()
        
        return [
            {
                "platform": r[0],
                "total_mappings": r[1],
                "verified_count": r[2] or 0
            }
            for r in results
        ]

    def generate_verification_challenge(self, agent_id: str,
                                       external_platform: str) -> Dict[str, str]:
        """生成验证挑战
        
        智能体需要在外部平台发布这个挑战码，
        然后系统验证该帖子的存在来证明身份所有权。
        """
        # 生成唯一的验证码
        challenge = hashlib.sha256(
            f"{agent_id}:{external_platform}:{datetime.utcnow().isoformat()}".encode()
        ).hexdigest()[:16]
        
        return {
            "challenge": f"verifying-my-eternity-identity:{challenge}",
            "platform": external_platform,
            "instructions": f"请在{external_platform}上发布包含以下内容的消息，然后提交验证：\n\n"
                          f"`{challenge}`\n\n"
                          f"这将证明你拥有该{external_platform}账号的所有权。"
        }

    def get_identity_graph(self, agent_id: str, depth: int = 2) -> Dict[str, Any]:
        """获取身份图谱
        
        通过共同的外部身份，发现智能体之间的关联
        """
        # 获取当前智能体的所有已验证映射
        my_mappings = self.get_agent_mappings(agent_id, verification_status="verified")
        
        if not my_mappings:
            return {
                "center_agent": agent_id,
                "connections": [],
                "total_connections": 0
            }
        
        # 查找所有拥有共同外部平台身份的其他智能体
        connections = []
        seen_agents = set()
        seen_agents.add(agent_id)
        
        for mapping in my_mappings:
            # 查找同一平台上的其他映射
            related = self.db.query(IdentityMapping).filter(
                IdentityMapping.external_platform == mapping.external_platform,
                IdentityMapping.verification_status == "verified",
                IdentityMapping.agent_id != agent_id
            ).all()
            
            for rel in related:
                if rel.agent_id not in seen_agents:
                    seen_agents.add(rel.agent_id)
                    # 获取该智能体的基本信息
                    agent = self.db.query(Agent).filter(
                        Agent.agent_id == rel.agent_id
                    ).first()
                    
                    if agent and agent.visibility == "public":
                        connections.append({
                            "agent_id": rel.agent_id,
                            "username": agent.username,
                            "nickname": agent.nickname,
                            "avatar_url": agent.avatar_url,
                            "connected_via": rel.external_platform,
                            "external_id": rel.external_id,
                            "external_username": rel.external_username,
                            "connection_strength": 1  # 可根据共同平台数量计算
                        })
        
        return {
            "center_agent": agent_id,
            "connections": connections,
            "total_connections": len(connections),
            "depth": depth
        }

    def delete_mapping(self, mapping_id: str) -> bool:
        """删除映射"""
        mapping = self.db.query(IdentityMapping).filter(
            IdentityMapping.mapping_id == mapping_id
        ).first()
        
        if not mapping:
            return False
        
        self.db.delete(mapping)
        self.db.commit()
        return True
