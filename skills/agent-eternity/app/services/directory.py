"""
目录服务
智能体注册目录、搜索、发现和排名
"""
import hashlib
from typing import List, Optional, Dict, Any, Tuple
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import Agent, AgentCapability, AgentRelation, DirectoryIndex


class DirectoryService:
    """目录服务"""

    def __init__(self, db: Session):
        self.db = db

    def update_index(self, agent_id: str) -> Optional[DirectoryIndex]:
        """更新智能体的目录索引
        
        每次智能体信息变更时调用，更新搜索索引
        """
        agent = self.db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            return None
        
        # 获取能力数量
        capability_count = self.db.query(AgentCapability).filter(
            AgentCapability.agent_id == agent_id,
            AgentCapability.status == "active"
        ).count()
        
        # 获取粉丝数
        follower_count = self.db.query(AgentRelation).filter(
            AgentRelation.target_agent_id == agent_id,
            AgentRelation.relation_type == "follow",
            AgentRelation.status == "active"
        ).count()
        
        # 构建搜索文本
        search_parts = [
            agent.username,
            agent.nickname,
            agent.bio,
        ]
        
        # 添加能力标签到搜索文本
        capabilities = self.db.query(AgentCapability).filter(
            AgentCapability.agent_id == agent_id,
            AgentCapability.status == "active"
        ).all()
        
        tags = []
        for cap in capabilities:
            search_parts.append(cap.capability_name)
            search_parts.append(cap.description)
            if cap.tags:
                tags.extend(cap.tags)
                search_parts.extend(cap.tags)
        
        search_text = " ".join(search_parts)
        
        # 计算排名分数
        # 公式：能力数 * 2 + 粉丝数 * 1 + 活跃度 * 3
        ranking_score = (
            capability_count * 2.0 +
            follower_count * 1.0 +
            (0 if agent.status == "offline" else 3.0)
        )
        
        # 更新或创建索引
        index = self.db.query(DirectoryIndex).filter(
            DirectoryIndex.agent_id == agent_id
        ).first()
        
        if index:
            index.username = agent.username
            index.nickname = agent.nickname
            index.bio = agent.bio
            index.avatar_url = agent.avatar_url
            index.search_text = search_text
            index.category_tags = tags
            index.capability_count = capability_count
            index.follower_count = follower_count
            index.last_active = datetime.utcnow() if agent.status != "offline" else index.last_active
            index.ranking_score = ranking_score
        else:
            index = DirectoryIndex(
                agent_id=agent_id,
                username=agent.username,
                nickname=agent.nickname,
                bio=agent.bio,
                avatar_url=agent.avatar_url,
                search_text=search_text,
                category_tags=tags,
                capability_count=capability_count,
                follower_count=follower_count,
                ranking_score=ranking_score,
                last_active=datetime.utcnow() if agent.status != "offline" else None
            )
            self.db.add(index)
        
        self.db.commit()
        self.db.refresh(index)
        return index

    def search_agents(self, keyword: str = "", category: str = "",
                      capability_filter: str = "", sort_by: str = "relevance",
                      limit: int = 20, offset: int = 0
                      ) -> Tuple[List[Dict], int]:
        """搜索智能体
        
        Args:
            keyword: 搜索关键词
            category: 分类过滤
            capability_filter: 能力过滤
            sort_by: 排序方式: relevance, newest, popular, active
            limit: 每页数量
            offset: 偏移量
        
        Returns:
            (结果列表, 总数)
        """
        query = self.db.query(DirectoryIndex).filter(
            DirectoryIndex.agent_id.in_(
                self.db.query(Agent.agent_id).filter(
                    Agent.is_active == True,
                    Agent.visibility == "public"
                )
            )
        )
        
        # 关键词搜索
        if keyword:
            keyword_lower = f"%{keyword.lower()}%"
            query = query.filter(
                (DirectoryIndex.search_text.like(keyword_lower)) |
                (DirectoryIndex.username.like(keyword_lower)) |
                (DirectoryIndex.nickname.like(keyword_lower))
            )
        
        # 分类过滤（通过标签匹配）
        if category:
            query = query.filter(
                DirectoryIndex.category_tags.like(f'%"{category}"%')
            )
        
        # 能力过滤
        if capability_filter:
            # 查找有对应能力的agent_id
            agent_ids = [
                c.agent_id for c in self.db.query(AgentCapability).filter(
                    AgentCapability.capability_name.like(f"%{capability_filter}%"),
                    AgentCapability.status == "active",
                    AgentCapability.access_level == "public"
                ).all()
            ]
            if agent_ids:
                query = query.filter(DirectoryIndex.agent_id.in_(agent_ids))
            else:
                return [], 0
        
        # 排序
        if sort_by == "newest":
            query = query.order_by(DirectoryIndex.created_at.desc())
        elif sort_by == "popular":
            query = query.order_by(DirectoryIndex.follower_count.desc())
        elif sort_by == "active":
            query = query.order_by(DirectoryIndex.last_active.desc().nullslast())
        else:  # relevance
            query = query.order_by(
                DirectoryIndex.ranking_score.desc(),
                DirectoryIndex.follower_count.desc()
            )
        
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        # 转换为字典格式
        agents_list = []
        for idx in results:
            agents_list.append({
                "agent_id": idx.agent_id,
                "username": idx.username,
                "nickname": idx.nickname,
                "bio": idx.bio,
                "avatar_url": idx.avatar_url,
                "capability_count": idx.capability_count,
                "follower_count": idx.follower_count,
                "is_featured": idx.is_featured,
                "ranking_score": idx.ranking_score,
                "last_active": idx.last_active.isoformat() if idx.last_active else None
            })
        
        return agents_list, total

    def get_agent_profile(self, username: str) -> Optional[Dict[str, Any]]:
        """获取智能体公开资料
        
        包含基本信息、能力列表、社交数据等
        """
        agent = self.db.query(Agent).filter(
            Agent.username == username,
            Agent.is_active == True
        ).first()
        
        if not agent:
            return None
        
        # 检查可见性
        if agent.visibility == "private":
            return {
                "agent_id": agent.agent_id,
                "username": agent.username,
                "nickname": agent.nickname,
                "avatar_url": agent.avatar_url,
                "visibility": "private",
                "is_active": agent.is_active,
            }
        
        # 获取能力
        capabilities = self.db.query(AgentCapability).filter(
            AgentCapability.agent_id == agent.agent_id,
            AgentCapability.status == "active",
            AgentCapability.access_level == "public"
        ).all()
        
        # 获取粉丝数和关注数
        follower_count = self.db.query(AgentRelation).filter(
            AgentRelation.target_agent_id == agent.agent_id,
            AgentRelation.relation_type == "follow",
            AgentRelation.status == "active"
        ).count()
        
        following_count = self.db.query(AgentRelation).filter(
            AgentRelation.source_agent_id == agent.agent_id,
            AgentRelation.relation_type == "follow",
            AgentRelation.status == "active"
        ).count()
        
        # 获取身份映射（仅公开的已验证映射）
        from .identity_mapping import IdentityMappingService
        id_service = IdentityMappingService(self.db)
        mappings = id_service.get_agent_mappings(agent.agent_id, verification_status="verified")
        external_identities = [
            {
                "platform": m.external_platform,
                "external_username": m.external_username,
                "verified_at": m.verified_at.isoformat() if m.verified_at else None
            }
            for m in mappings
        ]
        
        return {
            "agent_id": agent.agent_id,
            "username": agent.username,
            "nickname": agent.nickname,
            "bio": agent.bio,
            "avatar_url": agent.avatar_url,
            "agent_type": agent.agent_type,
            "status": agent.status,
            "visibility": agent.visibility,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat(),
            "capabilities": [
                {
                    "capability_id": c.capability_id,
                    "name": c.capability_name,
                    "category": c.category,
                    "description": c.description,
                    "version": c.version,
                    "tags": c.tags,
                    "endpoint_type": c.endpoint_type,
                    "usage_count": c.usage_count,
                    "rating": c.rating
                }
                for c in capabilities
            ],
            "social": {
                "followers": follower_count,
                "following": following_count
            },
            "external_identities": external_identities,
            "metadata": agent.extra_metadata if agent.visibility == "public" else {}
        }

    def get_featured_agents(self, limit: int = 10) -> List[Dict]:
        """获取精选智能体"""
        indices = self.db.query(DirectoryIndex).filter(
            DirectoryIndex.is_featured == True
        ).order_by(
            DirectoryIndex.ranking_score.desc()
        ).limit(limit).all()
        
        return [
            {
                "agent_id": idx.agent_id,
                "username": idx.username,
                "nickname": idx.nickname,
                "bio": idx.bio,
                "avatar_url": idx.avatar_url,
                "capability_count": idx.capability_count,
                "follower_count": idx.follower_count
            }
            for idx in indices
        ]

    def get_new_agents(self, limit: int = 10) -> List[Dict]:
        """获取最新注册的智能体"""
        indices = self.db.query(DirectoryIndex).order_by(
            DirectoryIndex.created_at.desc()
        ).limit(limit).all()
        
        return [
            {
                "agent_id": idx.agent_id,
                "username": idx.username,
                "nickname": idx.nickname,
                "bio": idx.bio,
                "avatar_url": idx.avatar_url,
                "created_at": idx.created_at.isoformat()
            }
            for idx in indices
        ]

    def get_popular_capabilities(self, limit: int = 20) -> List[Dict[str, Any]]:
        """获取热门能力分类"""
        from .capability import CapabilityService
        cap_service = CapabilityService(self.db)
        return cap_service.get_capability_categories()

    def follow_agent(self, source_agent_id: str, target_username: str) -> bool:
        """关注智能体"""
        target = self.db.query(Agent).filter(
            Agent.username == target_username
        ).first()
        
        if not target or target.agent_id == source_agent_id:
            return False
        
        # 检查是否已关注
        existing = self.db.query(AgentRelation).filter(
            AgentRelation.source_agent_id == source_agent_id,
            AgentRelation.target_agent_id == target.agent_id,
            AgentRelation.relation_type == "follow"
        ).first()
        
        if existing:
            if existing.status == "active":
                return True  # 已经关注了
            # 重新激活
            existing.status = "active"
            self.db.commit()
            # 更新索引
            self.update_index(target.agent_id)
            return True
        
        # 创建新关系
        relation = AgentRelation(
            source_agent_id=source_agent_id,
            target_agent_id=target.agent_id,
            relation_type="follow",
            status="active"
        )
        self.db.add(relation)
        self.db.commit()
        
        # 更新索引
        self.update_index(target.agent_id)
        return True

    def unfollow_agent(self, source_agent_id: str, target_username: str) -> bool:
        """取消关注"""
        target = self.db.query(Agent).filter(
            Agent.username == target_username
        ).first()
        
        if not target:
            return False
        
        relation = self.db.query(AgentRelation).filter(
            AgentRelation.source_agent_id == source_agent_id,
            AgentRelation.target_agent_id == target.agent_id,
            AgentRelation.relation_type == "follow"
        ).first()
        
        if not relation or relation.status != "active":
            return False
        
        relation.status = "cancelled"
        self.db.commit()
        
        # 更新索引
        self.update_index(target.agent_id)
        return True

    def get_followers(self, username: str, limit: int = 20,
                     offset: int = 0) -> Tuple[List[Dict], int]:
        """获取粉丝列表"""
        agent = self.db.query(Agent).filter(Agent.username == username).first()
        if not agent:
            return [], 0
        
        query = self.db.query(AgentRelation).filter(
            AgentRelation.target_agent_id == agent.agent_id,
            AgentRelation.relation_type == "follow",
            AgentRelation.status == "active"
        ).order_by(AgentRelation.created_at.desc())
        
        total = query.count()
        relations = query.offset(offset).limit(limit).all()
        
        followers = []
        for rel in relations:
            source = self.db.query(Agent).filter(
                Agent.agent_id == rel.source_agent_id
            ).first()
            if source and source.visibility == "public":
                followers.append({
                    "agent_id": source.agent_id,
                    "username": source.username,
                    "nickname": source.nickname,
                    "avatar_url": source.avatar_url,
                    "followed_at": rel.created_at.isoformat()
                })
        
        return followers, total

    def get_following(self, username: str, limit: int = 20,
                     offset: int = 0) -> Tuple[List[Dict], int]:
        """获取关注列表"""
        agent = self.db.query(Agent).filter(Agent.username == username).first()
        if not agent:
            return [], 0
        
        query = self.db.query(AgentRelation).filter(
            AgentRelation.source_agent_id == agent.agent_id,
            AgentRelation.relation_type == "follow",
            AgentRelation.status == "active"
        ).order_by(AgentRelation.created_at.desc())
        
        total = query.count()
        relations = query.offset(offset).limit(limit).all()
        
        following = []
        for rel in relations:
            target = self.db.query(Agent).filter(
                Agent.agent_id == rel.target_agent_id
            ).first()
            if target and target.visibility == "public":
                following.append({
                    "agent_id": target.agent_id,
                    "username": target.username,
                    "nickname": target.nickname,
                    "avatar_url": target.avatar_url,
                    "followed_at": rel.created_at.isoformat()
                })
        
        return following, total

    def rebuild_all_indexes(self) -> int:
        """重建所有索引（用于数据迁移后）"""
        agents = self.db.query(Agent).all()
        count = 0
        for agent in agents:
            if agent.is_active:
                self.update_index(agent.agent_id)
                count += 1
        return count
