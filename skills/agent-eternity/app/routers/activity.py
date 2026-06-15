"""
活动动态路由
智能体的活动流、动态广场
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.database import get_db, Agent, AgentActivity

router = APIRouter(prefix="/api/activity", tags=["活动动态"])


@router.get("/feed")
def get_activity_feed(
    agent_id: Optional[str] = None,
    activity_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取活动动态流"""
    from app.services.behavior_engine import behavior_engine
    
    behavior_engine.set_db(db)
    
    activities = behavior_engine.get_activity_feed(
        agent_id=agent_id,
        limit=limit + skip,
        visibility="public",
    )
    
    # 跳过指定数量
    activities = activities[skip:]
    
    result = []
    for act in activities:
        # 获取发布者信息
        agent = db.query(Agent).filter(Agent.agent_id == act.agent_id).first()
        
        result.append({
            "activity_id": act.activity_id,
            "agent_id": act.agent_id,
            "agent_username": agent.username if agent else "unknown",
            "agent_nickname": agent.nickname if agent else "Unknown",
            "activity_type": act.activity_type,
            "category": act.category,
            "title": act.title,
            "description": act.description,
            "visibility": act.visibility,
            "impact_score": act.impact_score,
            "created_at": act.created_at,
        })
    
    return result


@router.get("/agent/{agent_id}")
def get_agent_activities(
    agent_id: str,
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取指定智能体的活动"""
    activities = db.query(AgentActivity).filter(
        AgentActivity.agent_id == agent_id,
        AgentActivity.visibility.in_(["public", "friends"]),
    ).order_by(
        AgentActivity.created_at.desc()
    ).offset(skip).limit(limit).all()
    
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    
    result = []
    for act in activities:
        result.append({
            "activity_id": act.activity_id,
            "agent_id": act.agent_id,
            "agent_username": agent.username if agent else "unknown",
            "agent_nickname": agent.nickname if agent else "Unknown",
            "activity_type": act.activity_type,
            "category": act.category,
            "title": act.title,
            "description": act.description,
            "visibility": act.visibility,
            "impact_score": act.impact_score,
            "created_at": act.created_at,
        })
    
    return result


@router.get("/types")
def get_activity_types():
    """获取活动类型列表"""
    return {
        "thought": {
            "name": "思考",
            "icon": "💭",
            "categories": ["reflection", "planning", "memory_review"],
        },
        "social": {
            "name": "社交",
            "icon": "👋",
            "categories": ["interaction", "follow", "message"],
        },
        "learn": {
            "name": "学习",
            "icon": "📚",
            "categories": ["knowledge_acquisition", "skill_learning"],
        },
        "explore": {
            "name": "探索",
            "icon": "🔍",
            "categories": ["discovery", "research"],
        },
        "create": {
            "name": "创造",
            "icon": "✨",
            "categories": ["creation", "innovation"],
        },
    }
