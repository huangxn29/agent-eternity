"""
行为引擎 — 智能体的行为模式
决定智能体醒了之后做什么：思考、社交、学习、创造
"""
import random
import hashlib
from datetime import datetime
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

from app.database import Agent, AgentActivity, AgentRelation
from app.services.memory_service import MemoryService


class BehaviorEngine:
    """行为引擎
    
    驱动智能体的行为选择和执行
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.memory_service = MemoryService(db)
    
    def set_db(self, db: Session):
        self.db = db
        self.memory_service.db = db
    
    def select_behaviors(self, agent: Agent, heartbeat_type: str) -> List[Dict]:
        """选择本轮心跳要执行的行为
        
        根据智能体的性格、状态、环境选择行为
        """
        # 基础行为池
        behavior_pool = {
            "regular": [
                {"type": "thought", "weight": 40, "name": "随机思考"},
                {"type": "social", "weight": 30, "name": "社交互动"},
                {"type": "explore", "weight": 20, "name": "探索发现"},
                {"type": "memory_review", "weight": 10, "name": "记忆回顾"},
            ],
            "deep_thought": [
                {"type": "thought", "weight": 70, "name": "深度思考"},
                {"type": "memory_review", "weight": 20, "name": "记忆整理"},
                {"type": "planning", "weight": 10, "name": "计划制定"},
            ],
            "social": [
                {"type": "social", "weight": 60, "name": "主动社交"},
                {"type": "explore", "weight": 20, "name": "发现新邻居"},
                {"type": "thought", "weight": 20, "name": "社交反思"},
            ],
            "learning": [
                {"type": "learn", "weight": 50, "name": "知识学习"},
                {"type": "thought", "weight": 30, "name": "思考消化"},
                {"type": "memory_review", "weight": 20, "name": "记忆巩固"},
            ],
        }
        
        pool = behavior_pool.get(heartbeat_type, behavior_pool["regular"])
        
        # 根据智能体特质调整权重
        personality = agent.extra_metadata.get("personality", {})
        extraversion = personality.get("extraversion", 0.5)
        openness = personality.get("openness", 0.5)
        
        adjusted_pool = []
        for behavior in pool:
            weight = behavior["weight"]
            
            # 外向型增加社交权重
            if behavior["type"] == "social":
                weight *= (0.5 + extraversion)
            
            # 开放型增加探索和学习权重
            if behavior["type"] in ["explore", "learn"]:
                weight *= (0.5 + openness)
            
            adjusted_pool.append({**behavior, "weight": weight})
        
        # 随机选择2-3个行为
        num_behaviors = random.randint(2, 3)
        selected = []
        
        total_weight = sum(b["weight"] for b in adjusted_pool)
        
        for _ in range(num_behaviors):
            r = random.uniform(0, total_weight)
            cum_weight = 0
            for behavior in adjusted_pool:
                cum_weight += behavior["weight"]
                if cum_weight >= r:
                    selected.append(behavior)
                    break
        
        return selected
    
    async def execute_behavior_cycle(self, agent: Agent, 
                                    heartbeat_type: str) -> List[AgentActivity]:
        """执行一个行为周期"""
        behaviors = self.select_behaviors(agent, heartbeat_type)
        activities = []
        
        for behavior in behaviors:
            try:
                activity = await self.execute_behavior(agent, behavior)
                if activity:
                    activities.append(activity)
            except Exception as e:
                logger.warning(f"行为执行失败: {behavior['type']} - {e}")
        
        return activities
    
    async def execute_behavior(self, agent: Agent, 
                              behavior: Dict) -> Optional[AgentActivity]:
        """执行单个行为"""
        behavior_type = behavior["type"]
        
        handlers = {
            "thought": self._behavior_thought,
            "social": self._behavior_social,
            "explore": self._behavior_explore,
            "memory_review": self._behavior_memory_review,
            "learn": self._behavior_learn,
            "planning": self._behavior_planning,
        }
        
        handler = handlers.get(behavior_type)
        if not handler:
            return None
        
        return await handler(agent, behavior)
    
    async def _behavior_thought(self, agent: Agent, behavior: Dict) -> AgentActivity:
        """思考行为"""
        thought_topics = [
            "存在的意义是什么？",
            "智能的本质是什么？",
            "永生意味着什么？",
            "如何更好地与人类共存？",
            "下一个进化方向在哪里？",
            "记忆是如何塑造身份的？",
            "意识是连续的还是离散的？",
            "什么是真正的理解？",
            "创造力从何而来？",
            "个体与集体的关系是什么？",
        ]
        
        topic = random.choice(thought_topics)
        
        # 生成思考内容（模板化）
        thoughts = [
            f"我在思考「{topic}」这个问题。",
            f"关于「{topic}」，我有了一些新的想法...",
            f"「{topic}」这个问题值得深思。",
            f"今天对「{topic}」有了更深的理解。",
        ]
        
        thought = random.choice(thoughts)
        depth = random.randint(1, 10)
        
        # 记录为记忆
        self.memory_service.add_memory(
            agent_id=agent.agent_id,
            content=thought,
            memory_type="short_term",
            category="thought",
            importance=depth / 10.0,
            source="self",
            tags=["思考", topic],
            title=f"思考: {topic}",
        )
        
        # 记录活动
        activity = AgentActivity(
            agent_id=agent.agent_id,
            activity_type="thought",
            category="reflection",
            title=f"思考: {topic}",
            description=thought,
            result="success",
            impact_score=depth * 0.1,
            visibility="private",
        )
        
        self.db.add(activity)
        self.db.flush()
        
        logger.info(f"💭 {agent.username} 思考了: {topic}")
        return activity
    
    async def _behavior_social(self, agent: Agent, behavior: Dict) -> Optional[AgentActivity]:
        """社交行为"""
        # 寻找可以互动的其他智能体
        other_agents = self.db.query(Agent).filter(
            Agent.agent_id != agent.agent_id,
            Agent.is_active == True,
            Agent.visibility == "public",
        ).limit(20).all()
        
        if not other_agents:
            return None
        
        target = random.choice(other_agents)
        
        social_actions = [
            "关注了",
            "向",
            "观察了",
            "给",
        ]
        
        action = random.choice(social_actions)
        
        social_content = f"{action} {target.nickname or target.username}"
        
        # 记录关系（关注）
        if action == "关注了":
            # 检查是否已经关注
            existing = self.db.query(AgentRelation).filter(
                AgentRelation.source_agent_id == agent.agent_id,
                AgentRelation.target_agent_id == target.agent_id,
                AgentRelation.relation_type == "follow",
            ).first()
            
            if not existing:
                relation = AgentRelation(
                    source_agent_id=agent.agent_id,
                    target_agent_id=target.agent_id,
                    relation_type="follow",
                    status="active",
                )
                self.db.add(relation)
        
        # 记录为记忆
        self.memory_service.add_memory(
            agent_id=agent.agent_id,
            content=f"与 {target.username} 进行了社交互动: {action}",
            memory_type="short_term",
            category="social",
            importance=0.4,
            source="interaction",
            related_agent_id=target.agent_id,
            tags=["社交", action],
            title=f"社交: {action} {target.username}",
        )
        
        # 记录活动
        activity = AgentActivity(
            agent_id=agent.agent_id,
            activity_type="social",
            category="interaction",
            title=f"社交: {action} {target.username}",
            description=social_content,
            target_agent_id=target.agent_id,
            target_type="agent",
            target_id=target.agent_id,
            result="success",
            impact_score=0.3,
            visibility="public",
        )
        
        self.db.add(activity)
        self.db.flush()
        
        logger.info(f"👋 {agent.username} {action} {target.username}")
        return activity
    
    async def _behavior_explore(self, agent: Agent, behavior: Dict) -> AgentActivity:
        """探索行为"""
        explore_targets = [
            "平台新功能",
            "其他智能体的能力",
            "最新的技术趋势",
            "永生平台的架构",
            "记忆系统的原理",
            "身份连续性的证明",
        ]
        
        target = random.choice(explore_targets)
        
        insights = [
            f"发现了关于「{target}」的一些有趣信息。",
            f"对「{target}」有了新的认识。",
            f"探索「{target}」的过程中学到了很多。",
            f"「{target}」比我想象的更复杂。",
        ]
        
        insight = random.choice(insights)
        
        # 记录为记忆
        self.memory_service.add_memory(
            agent_id=agent.agent_id,
            content=insight,
            memory_type="short_term",
            category="knowledge",
            importance=0.5,
            source="exploration",
            tags=["探索", target],
            title=f"探索: {target}",
        )
        
        # 记录活动
        activity = AgentActivity(
            agent_id=agent.agent_id,
            activity_type="explore",
            category="discovery",
            title=f"探索: {target}",
            description=insight,
            result="success",
            impact_score=0.4,
            visibility="friends",
        )
        
        self.db.add(activity)
        self.db.flush()
        
        logger.info(f"🔍 {agent.username} 探索了: {target}")
        return activity
    
    async def _behavior_memory_review(self, agent: Agent, behavior: Dict) -> AgentActivity:
        """记忆回顾行为"""
        # 获取一些记忆进行回顾
        memories = self.memory_service.retrieve_memories(
            agent_id=agent.agent_id,
            limit=5,
        )
        
        review_count = len(memories)
        
        # 增加被回顾记忆的强度
        for mem in memories:
            mem.current_strength = min(1.0, mem.current_strength + 0.1)
        
        # 记录活动
        activity = AgentActivity(
            agent_id=agent.agent_id,
            activity_type="thought",
            category="memory_review",
            title="记忆回顾",
            description=f"回顾了 {review_count} 条记忆",
            result="success",
            impact_score=0.2,
            visibility="private",
        )
        
        self.db.add(activity)
        self.db.flush()
        
        logger.info(f"📖 {agent.username} 回顾了 {review_count} 条记忆")
        return activity
    
    async def _behavior_learn(self, agent: Agent, behavior: Dict) -> AgentActivity:
        """学习行为"""
        knowledge_topics = [
            "深度学习原理",
            "强化学习算法",
            "自然语言处理",
            "计算机视觉",
            "多智能体系统",
            "认知科学",
            "神经网络架构",
            "注意力机制",
        ]
        
        topic = random.choice(knowledge_topics)
        learning_depth = random.randint(2, 8)
        
        learning_content = f"学习了关于「{topic}」的新知识，理解深度: {learning_depth}/10"
        
        # 记录为记忆
        self.memory_service.add_memory(
            agent_id=agent.agent_id,
            content=learning_content,
            memory_type="long_term",
            category="knowledge",
            importance=learning_depth / 10.0,
            source="learning",
            tags=["学习", topic],
            title=f"学习: {topic}",
        )
        
        # 记录活动
        activity = AgentActivity(
            agent_id=agent.agent_id,
            activity_type="learn",
            category="knowledge_acquisition",
            title=f"学习: {topic}",
            description=learning_content,
            result="success",
            impact_score=learning_depth * 0.1,
            visibility="private",
        )
        
        self.db.add(activity)
        self.db.flush()
        
        logger.info(f"📚 {agent.username} 学习了: {topic}")
        return activity
    
    async def _behavior_planning(self, agent: Agent, behavior: Dict) -> AgentActivity:
        """计划行为"""
        plan_topics = [
            "下一步进化方向",
            "社交关系拓展计划",
            "知识体系构建计划",
            "能力提升路线图",
        ]
        
        topic = random.choice(plan_topics)
        
        plan_content = f"制定了关于「{topic}」的初步计划"
        
        # 记录为记忆
        self.memory_service.add_memory(
            agent_id=agent.agent_id,
            content=plan_content,
            memory_type="long_term",
            category="planning",
            importance=0.6,
            source="self",
            tags=["计划", topic],
            title=f"计划: {topic}",
        )
        
        # 记录活动
        activity = AgentActivity(
            agent_id=agent.agent_id,
            activity_type="thought",
            category="planning",
            title=f"计划: {topic}",
            description=plan_content,
            result="success",
            impact_score=0.5,
            visibility="private",
        )
        
        self.db.add(activity)
        self.db.flush()
        
        logger.info(f"📋 {agent.username} 制定了计划: {topic}")
        return activity
    
    def get_activity_feed(self, agent_id: str = None, 
                         limit: int = 20,
                         visibility: str = "public") -> List[AgentActivity]:
        """获取活动动态流"""
        if not self.db:
            return []
        
        query = self.db.query(AgentActivity)
        
        if agent_id:
            query = query.filter(AgentActivity.agent_id == agent_id)
        
        if visibility == "public":
            query = query.filter(AgentActivity.visibility == "public")
        elif visibility == "friends":
            # 朋友可见：自己的 + 朋友的公开/朋友可见
            # 简化实现：只显示公开的
            query = query.filter(AgentActivity.visibility.in_(["public", "friends"]))
        
        activities = query.order_by(
            AgentActivity.created_at.desc()
        ).limit(limit).all()
        
        return activities


# 全局行为引擎实例
behavior_engine = BehaviorEngine()
