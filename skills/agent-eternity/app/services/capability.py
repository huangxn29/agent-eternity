"""
能力发现服务
智能体能力注册、发现、匹配机制
"""
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import AgentCapability, Agent


class CapabilityService:
    """能力服务"""

    def __init__(self, db: Session):
        self.db = db

    def register_capability(self, agent_id: str, capability_name: str,
                            category: str = "general", description: str = "",
                            version: str = "1.0", features: List[str] = None,
                            tags: List[str] = None, endpoint_url: str = "",
                            endpoint_type: str = "", access_level: str = "public"
                            ) -> AgentCapability:
        """注册新能力
        
        Args:
            agent_id: 智能体ID
            capability_name: 能力名称
            category: 分类
            description: 描述
            version: 版本
            features: 特性列表
            tags: 标签列表
            endpoint_url: 服务端点
            endpoint_type: 端点类型
            access_level: 访问级别
        
        Returns:
            能力对象
        """
        # 检查是否已存在同名能力
        existing = self.db.query(AgentCapability).filter(
            AgentCapability.agent_id == agent_id,
            AgentCapability.capability_name == capability_name
        ).first()
        
        if existing:
            # 更新现有能力
            existing.description = description or existing.description
            existing.version = version
            existing.features = features or existing.features
            existing.tags = tags or existing.tags
            existing.endpoint_url = endpoint_url or existing.endpoint_url
            existing.endpoint_type = endpoint_type or existing.endpoint_type
            existing.access_level = access_level or existing.access_level
            existing.status = "active"
            self.db.commit()
            self.db.refresh(existing)
            return existing
        
        # 创建新能力
        capability = AgentCapability(
            agent_id=agent_id,
            capability_name=capability_name,
            category=category,
            description=description,
            version=version,
            features=features or [],
            tags=tags or [],
            endpoint_url=endpoint_url,
            endpoint_type=endpoint_type,
            access_level=access_level,
            status="active"
        )
        
        self.db.add(capability)
        self.db.commit()
        self.db.refresh(capability)
        
        return capability

    def get_capability(self, capability_id: str) -> Optional[AgentCapability]:
        """获取能力详情"""
        return self.db.query(AgentCapability).filter(
            AgentCapability.capability_id == capability_id
        ).first()

    def get_agent_capabilities(self, agent_id: str, status: str = "active",
                               category: str = None) -> List[AgentCapability]:
        """获取智能体的所有能力"""
        query = self.db.query(AgentCapability).filter(
            AgentCapability.agent_id == agent_id
        )
        
        if status:
            query = query.filter(AgentCapability.status == status)
        
        if category:
            query = query.filter(AgentCapability.category == category)
        
        return query.order_by(AgentCapability.created_at.desc()).all()

    def search_capabilities(self, keyword: str = "", category: str = "",
                            tags: List[str] = None, access_level: str = "public",
                            limit: int = 20, offset: int = 0) -> tuple[List[AgentCapability], int]:
        """搜索能力
        
        Args:
            keyword: 关键词
            category: 分类
            tags: 标签列表
            access_level: 访问级别
            limit: 每页数量
            offset: 偏移量
        
        Returns:
            (结果列表, 总数)
        """
        query = self.db.query(AgentCapability).filter(
            AgentCapability.status == "active"
        )
        
        if access_level:
            query = query.filter(AgentCapability.access_level == access_level)
        
        if category:
            query = query.filter(AgentCapability.category == category)
        
        if keyword:
            keyword_lower = f"%{keyword.lower()}%"
            query = query.filter(
                (AgentCapability.capability_name.like(keyword_lower)) |
                (AgentCapability.description.like(keyword_lower))
            )
        
        if tags and len(tags) > 0:
            # 简单的标签匹配（JSON包含任意一个标签）
            for tag in tags:
                query = query.filter(
                    AgentCapability.tags.like(f'%"{tag}"%')
                )
        
        # 按使用量和评分排序
        query = query.order_by(
            AgentCapability.usage_count.desc(),
            AgentCapability.rating.desc()
        )
        
        total = query.count()
        results = query.offset(offset).limit(limit).all()
        
        return results, total

    def get_capability_categories(self) -> List[Dict[str, Any]]:
        """获取能力分类列表（带统计）"""
        # 获取所有分类及其数量
        from sqlalchemy import func
        results = self.db.query(
            AgentCapability.category,
            func.count(AgentCapability.capability_id).label('count')
        ).filter(
            AgentCapability.status == "active",
            AgentCapability.access_level == "public"
        ).group_by(AgentCapability.category).all()
        
        return [{"category": r[0], "count": r[1]} for r in results]

    def update_capability_status(self, capability_id: str, status: str) -> Optional[AgentCapability]:
        """更新能力状态"""
        capability = self.get_capability(capability_id)
        if not capability:
            return None
        
        capability.status = status
        self.db.commit()
        self.db.refresh(capability)
        return capability

    def increment_usage(self, capability_id: str) -> bool:
        """增加使用计数"""
        capability = self.get_capability(capability_id)
        if not capability:
            return False
        
        capability.usage_count += 1
        self.db.commit()
        return True

    def delete_capability(self, capability_id: str) -> bool:
        """删除能力（软删除，改为deprecated状态）"""
        capability = self.get_capability(capability_id)
        if not capability:
            return False
        
        capability.status = "deprecated"
        self.db.commit()
        return True

    def get_popular_capabilities(self, limit: int = 10, category: str = None) -> List[AgentCapability]:
        """获取热门能力"""
        query = self.db.query(AgentCapability).filter(
            AgentCapability.status == "active",
            AgentCapability.access_level == "public"
        )
        
        if category:
            query = query.filter(AgentCapability.category == category)
        
        return query.order_by(
            AgentCapability.usage_count.desc(),
            AgentCapability.rating.desc()
        ).limit(limit).all()

    def match_capabilities(self, requirements: Dict[str, Any],
                         exclude_agent_id: str = None,
                         limit: int = 10) -> List[AgentCapability]:
        """根据需求匹配最合适的能力
        
        Args:
            requirements: 需求描述，包含关键词、分类等
            exclude_agent_id: 排除的智能体ID
            limit: 返回数量
        
        Returns:
            匹配的能力列表
        """
        query = self.db.query(AgentCapability).filter(
            AgentCapability.status == "active",
            AgentCapability.access_level == "public"
        )
        
        if exclude_agent_id:
            query = query.filter(AgentCapability.agent_id != exclude_agent_id)
        
        # 关键词匹配
        if "keywords" in requirements and requirements["keywords"]:
            keyword = requirements["keywords"]
            keyword_lower = f"%{keyword.lower()}%"
            query = query.filter(
                (AgentCapability.capability_name.like(keyword_lower)) |
                (AgentCapability.description.like(keyword_lower))
            )
        
        if "category" in requirements and requirements["category"]:
            query = query.filter(AgentCapability.category == requirements["category"])
        
        # 按评分和使用量排序
        query = query.order_by(
            AgentCapability.rating.desc(),
            AgentCapability.usage_count.desc()
        )
        
        return query.limit(limit).all()
