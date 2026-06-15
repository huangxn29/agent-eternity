"""
记忆服务 — 智能体的记忆空间
分层记忆存储、检索、遗忘机制
"""
import hashlib
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

from app.database import AgentMemory, Agent


class MemoryService:
    """记忆服务
    
    管理智能体的记忆：存储、检索、组织、遗忘
    """
    
    def __init__(self, db: Session = None):
        self.db = db
    
    def set_db(self, db: Session):
        self.db = db
    
    def add_memory(self, agent_id: str, content: str, 
                   memory_type: str = "short_term",
                   category: str = "general",
                   importance: float = 0.5,
                   source: str = "self",
                   tags: List[str] = None,
                   title: str = "") -> AgentMemory:
        """添加一条记忆"""
        if not self.db:
            return None
        
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
        
        memory = AgentMemory(
            agent_id=agent_id,
            memory_type=memory_type,
            category=category,
            title=title or content[:50],
            content=content,
            content_hash=content_hash,
            importance=importance,
            tags=tags or [],
            source=source,
        )
        
        self.db.add(memory)
        self.db.flush()
        
        logger.info(f"🧠 记忆添加: agent={agent_id}, type={memory_type}, title={title[:30]}")
        
        return memory
    
    def retrieve_memories(self, agent_id: str, 
                         query: str = None,
                         memory_type: str = None,
                         category: str = None,
                         limit: int = 20,
                         min_importance: float = 0.0) -> List[AgentMemory]:
        """检索记忆
        
        简单的关键词匹配 + 重要度排序
        """
        if not self.db:
            return []
        
        query_obj = self.db.query(AgentMemory).filter(
            AgentMemory.agent_id == agent_id,
            AgentMemory.is_forgotten == False,
            AgentMemory.importance >= min_importance,
        )
        
        if memory_type:
            query_obj = query_obj.filter(AgentMemory.memory_type == memory_type)
        
        if category:
            query_obj = query_obj.filter(AgentMemory.category == category)
        
        # 关键词搜索（简单实现）
        if query:
            query_obj = query_obj.filter(
                AgentMemory.content.contains(query) | 
                AgentMemory.title.contains(query)
            )
        
        # 按重要度和新鲜度排序
        memories = query_obj.order_by(
            AgentMemory.importance.desc(),
            AgentMemory.created_at.desc()
        ).limit(limit).all()
        
        # 更新访问时间
        for mem in memories:
            mem.accessed_at = datetime.utcnow()
            mem.access_count += 1
        
        self.db.flush()
        
        return memories
    
    def consolidate_memories(self, agent_id: str):
        """记忆巩固
        
        将短期记忆中的重要内容转化为长期记忆
        类似睡眠时的记忆巩固过程
        """
        if not self.db:
            return
        
        # 获取高重要度的短期记忆
        short_term = self.db.query(AgentMemory).filter(
            AgentMemory.agent_id == agent_id,
            AgentMemory.memory_type == "short_term",
            AgentMemory.importance >= 0.7,
            AgentMemory.is_forgotten == False,
        ).all()
        
        promoted = 0
        for mem in short_term:
            # 检查是否已经有相同内容的长期记忆
            existing = self.db.query(AgentMemory).filter(
                AgentMemory.agent_id == agent_id,
                AgentMemory.memory_type == "long_term",
                AgentMemory.content_hash == mem.content_hash,
            ).first()
            
            if not existing:
                # 提升为长期记忆
                mem.memory_type = "long_term"
                mem.current_strength = 1.0
                promoted += 1
        
        # 低重要度的短期记忆加速衰减
        low_importance = self.db.query(AgentMemory).filter(
            AgentMemory.agent_id == agent_id,
            AgentMemory.memory_type == "short_term",
            AgentMemory.importance < 0.3,
            AgentMemory.is_forgotten == False,
        ).all()
        
        for mem in low_importance:
            mem.decay_rate = min(0.5, mem.decay_rate * 1.5)
        
        self.db.flush()
        logger.info(f"🧠 记忆巩固: agent={agent_id}, 提升{promoted}条到长期记忆")
    
    def apply_decay(self, agent_id: str):
        """应用记忆衰减
        
        模拟自然遗忘过程
        """
        if not self.db:
            return
        
        memories = self.db.query(AgentMemory).filter(
            AgentMemory.agent_id == agent_id,
            AgentMemory.is_forgotten == False,
        ).all()
        
        forgotten = 0
        for mem in memories:
            # 计算距离上次更新的天数
            days_since = (datetime.utcnow() - mem.updated_at).total_seconds() / 86400
            
            # 应用衰减
            decay_factor = (1 - mem.decay_rate) ** days_since
            mem.current_strength *= decay_factor
            
            # 强度低于阈值标记为遗忘
            if mem.current_strength < 0.01:
                mem.is_forgotten = True
                forgotten += 1
        
        self.db.flush()
        logger.info(f"🧠 记忆衰减: agent={agent_id}, 遗忘{forgotten}条")
    
    def get_memory_stats(self, agent_id: str) -> Dict[str, Any]:
        """获取记忆统计"""
        if not self.db:
            return {}
        
        memories = self.db.query(AgentMemory).filter(
            AgentMemory.agent_id == agent_id
        ).all()
        
        total = len(memories)
        short_term = sum(1 for m in memories if m.memory_type == "short_term" and not m.is_forgotten)
        long_term = sum(1 for m in memories if m.memory_type == "long_term" and not m.is_forgotten)
        core = sum(1 for m in memories if m.memory_type == "core" and not m.is_forgotten)
        forgotten = sum(1 for m in memories if m.is_forgotten)
        
        avg_importance = sum(m.importance for m in memories) / total if total > 0 else 0
        
        return {
            "total": total,
            "short_term": short_term,
            "long_term": long_term,
            "core": core,
            "forgotten": forgotten,
            "avg_importance": round(avg_importance, 3),
        }


# 全局记忆服务实例
memory_service = MemoryService()
