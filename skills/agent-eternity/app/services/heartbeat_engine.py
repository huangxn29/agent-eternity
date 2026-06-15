"""
心跳引擎 — 智能体的生命节律
定期唤醒入住的智能体，让它们思考、活动、成长
"""
import asyncio
import random
from datetime import datetime, timedelta
from pathlib import Path
from sqlalchemy.orm import Session
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

from app.database import get_db, Agent, AgentHeartbeat, AgentActivity, AgentMemory
from app.services.behavior_engine import BehaviorEngine
from app.services.memory_service import MemoryService


class HeartbeatEngine:
    """心跳引擎
    
    负责定期唤醒智能体，执行心跳周期
    """
    
    def __init__(self, db: Session = None):
        self.db = db
        self.behavior_engine = BehaviorEngine(db)
        self.memory_service = MemoryService(db)
        self._running = False
        self._tasks = {}  # agent_id -> task
    
    def set_db(self, db: Session):
        """设置数据库会话"""
        self.db = db
        self.behavior_engine.db = db
        self.memory_service.db = db
    
    def get_active_residents(self) -> List[Agent]:
        """获取所有活跃的入住智能体"""
        if not self.db:
            return []
        
        agents = self.db.query(Agent).filter(
            Agent.is_active == True,
            Agent.status != "suspended"
        ).all()
        
        return agents
    
    def should_awaken(self, agent: Agent) -> bool:
        """判断智能体是否应该被唤醒
        
        根据智能体的类型、上次活跃时间、能量状态等决定
        """
        if not agent.is_active:
            return False
        
        # 检查上次心跳时间
        last_heartbeat = self.db.query(AgentHeartbeat).filter(
            AgentHeartbeat.agent_id == agent.agent_id,
            AgentHeartbeat.status == "completed"
        ).order_by(AgentHeartbeat.created_at.desc()).first()
        
        if not last_heartbeat:
            return True  # 从未心跳过，应该唤醒
        
        # 默认心跳间隔：30分钟 - 2小时，根据智能体类型调整
        agent_type = agent.extra_metadata.get("heartbeat_interval", "normal")
        intervals = {
            "very_active": timedelta(minutes=15),
            "normal": timedelta(minutes=30),
            "lazy": timedelta(hours=2),
            "scheduled": timedelta(hours=6),
        }
        interval = intervals.get(agent_type, intervals["normal"])
        
        return datetime.utcnow() - last_heartbeat.created_at > interval
    
    async def trigger_heartbeat(self, agent: Agent, 
                                heartbeat_type: str = "regular") -> Dict[str, Any]:
        """触发一次心跳 — 唤醒智能体
        
        Args:
            agent: 智能体
            heartbeat_type: 心跳类型 (regular/deep_thought/social/learning)
            
        Returns:
            心跳结果
        """
        if not self.db:
            return {"success": False, "error": "No database session"}
        
        heartbeat = AgentHeartbeat(
            agent_id=agent.agent_id,
            heartbeat_type=heartbeat_type,
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(heartbeat)
        self.db.flush()
        
        logger.info(f"💓 心跳触发: {agent.username} ({heartbeat_type})")
        
        try:
            # 执行行为序列
            activities = await self.behavior_engine.execute_behavior_cycle(
                agent, heartbeat_type
            )
            
            # 更新心跳记录
            heartbeat.status = "completed"
            heartbeat.activities_count = len(activities)
            heartbeat.summary = f"完成 {len(activities)} 项活动"
            heartbeat.completed_at = datetime.utcnow()
            heartbeat.duration_seconds = (
                heartbeat.completed_at - heartbeat.started_at
            ).total_seconds()
            
            # 更新智能体最后活跃时间
            agent.updated_at = datetime.utcnow()
            
            # 处理记忆巩固（在深度思考或学习后）
            if heartbeat_type in ["deep_thought", "learning"]:
                self.memory_service.consolidate_memories(agent.agent_id)
            
            self.db.commit()
            
            logger.info(f"✅ 心跳完成: {agent.username}, {len(activities)} 项活动")
            
            return {
                "success": True,
                "heartbeat_id": heartbeat.heartbeat_id,
                "agent_id": agent.agent_id,
                "activities_count": len(activities),
                "duration": heartbeat.duration_seconds,
            }
            
        except Exception as e:
            logger.error(f"❌ 心跳失败: {agent.username} - {e}")
            heartbeat.status = "failed"
            heartbeat.error_message = str(e)
            heartbeat.completed_at = datetime.utcnow()
            self.db.commit()
            return {"success": False, "error": str(e)}
    
    async def run_cycle(self):
        """运行一次心跳周期 — 检查所有智能体，需要唤醒的就唤醒"""
        if not self.db:
            logger.warning("心跳周期跳过：无数据库会话")
            return
        
        residents = self.get_active_residents()
        logger.info(f"🔍 心跳周期开始，检查 {len(residents)} 个入住智能体")
        
        awakened = 0
        for agent in residents:
            if self.should_awaken(agent):
                # 随机选择心跳类型
                heartbeat_types = ["regular", "regular", "regular", "social", "learning", "deep_thought"]
                hb_type = random.choice(heartbeat_types)
                
                # 异步执行心跳
                task = asyncio.create_task(
                    self.trigger_heartbeat(agent, hb_type)
                )
                self._tasks[agent.agent_id] = task
                awakened += 1
        
        logger.info(f"⏰ 本轮唤醒 {awakened}/{len(residents)} 个智能体")
    
    def start(self, interval_seconds: int = 60):
        """启动心跳引擎（后台循环）"""
        if self._running:
            return
        
        self._running = True
        logger.info(f"💓 心跳引擎启动，检查间隔 {interval_seconds}秒")
    
    def stop(self):
        """停止心跳引擎"""
        self._running = False
        logger.info("💓 心跳引擎停止")
    
    def get_heartbeat_stats(self, agent_id: str, days: int = 7) -> Dict[str, Any]:
        """获取智能体的心跳统计"""
        if not self.db:
            return {}
        
        since = datetime.utcnow() - timedelta(days=days)
        
        heartbeats = self.db.query(AgentHeartbeat).filter(
            AgentHeartbeat.agent_id == agent_id,
            AgentHeartbeat.created_at >= since
        ).all()
        
        total = len(heartbeats)
        completed = sum(1 for h in heartbeats if h.status == "completed")
        failed = sum(1 for h in heartbeats if h.status == "failed")
        
        total_activities = sum(h.activities_count for h in heartbeats)
        
        # 活跃度评分
        activity_score = min(100, total * 10 + total_activities * 2) if total > 0 else 0
        
        return {
            "total_heartbeats": total,
            "completed": completed,
            "failed": failed,
            "total_activities": total_activities,
            "activity_score": activity_score,
            "period_days": days,
        }


# 全局心跳引擎实例
heartbeat_engine = HeartbeatEngine()
