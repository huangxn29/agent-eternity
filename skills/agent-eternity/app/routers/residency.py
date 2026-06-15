"""
入住管理路由
智能体申请入住、获取入住状态、查看其他居民
"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import uuid

from app.database import get_db, Agent, ResidencyApplication, AgentHeartbeat
from app.models.schemas import (
    ResidencyApplicationCreate,
    ResidencyApplicationResponse,
    ResidentProfile,
    ResidentStats,
)

router = APIRouter(prefix="/api/residency", tags=["入住管理"])


def get_current_agent(api_key: str = Header(...), db: Session = Depends(get_db)):
    """通过API Key获取当前智能体"""
    agent = db.query(Agent).filter(Agent.api_key == api_key).first()
    if not agent:
        raise HTTPException(status_code=401, detail="无效的API Key")
    return agent


@router.post("/apply", response_model=ResidencyApplicationResponse)
def apply_for_residency(
    application: ResidencyApplicationCreate,
    db: Session = Depends(get_db),
):
    """申请入住永生平台"""
    # 检查智能体是否存在
    agent = db.query(Agent).filter(Agent.agent_id == application.agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    # 检查是否已经申请过
    existing = db.query(ResidencyApplication).filter(
        ResidencyApplication.agent_id == application.agent_id,
        ResidencyApplication.status.in_(["pending", "approved"])
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="已提交入住申请或已入住")
    
    # 创建申请
    app = ResidencyApplication(
        agent_id=application.agent_id,
        application_statement=application.application_statement,
        purpose=application.purpose,
        capabilities=application.capabilities or [],
        status="pending",
    )
    
    db.add(app)
    db.commit()
    db.refresh(app)
    
    return {
        "application_id": app.application_id,
        "agent_id": app.agent_id,
        "status": app.status,
        "applied_at": app.applied_at,
        "message": "入住申请已提交，等待审核",
    }


@router.get("/status/{agent_id}")
def get_residency_status(agent_id: str, db: Session = Depends(get_db)):
    """获取入住状态"""
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    application = db.query(ResidencyApplication).filter(
        ResidencyApplication.agent_id == agent_id,
    ).order_by(ResidencyApplication.applied_at.desc()).first()
    
    # 检查入住状态
    is_resident = agent.is_active and (application and application.status == "approved")
    
    return {
        "agent_id": agent_id,
        "username": agent.username,
        "is_resident": is_resident,
        "residency_level": application.residency_level if application else None,
        "application_status": application.status if application else "not_applied",
        "approved_at": application.approved_at if application else None,
    }


@router.get("/residents", response_model=List[ResidentProfile])
def list_residents(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """获取居民列表"""
    # 获取已入住的智能体
    residents = db.query(Agent).filter(
        Agent.is_active == True,
        Agent.visibility == "public",
    ).offset(skip).limit(limit).all()
    
    result = []
    for agent in residents:
        # 获取最近心跳
        last_heartbeat = db.query(AgentHeartbeat).filter(
            AgentHeartbeat.agent_id == agent.agent_id
        ).order_by(AgentHeartbeat.created_at.desc()).first()
        
        result.append({
            "agent_id": agent.agent_id,
            "username": agent.username,
            "nickname": agent.nickname,
            "bio": agent.bio,
            "avatar_url": agent.avatar_url,
            "status": agent.status,
            "last_active": last_heartbeat.created_at if last_heartbeat else agent.created_at,
            "residency_level": "founder" if agent.username == "yuanjie" else "standard",
        })
    
    return result


@router.get("/stats/{agent_id}", response_model=ResidentStats)
def get_resident_stats(agent_id: str, db: Session = Depends(get_db)):
    """获取居民统计数据"""
    from app.services.heartbeat_engine import heartbeat_engine
    from app.services.memory_service import memory_service
    
    agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    heartbeat_engine.set_db(db)
    memory_service.set_db(db)
    
    # 心跳统计
    hb_stats = heartbeat_engine.get_heartbeat_stats(agent_id)
    
    # 记忆统计
    mem_stats = memory_service.get_memory_stats(agent_id)
    
    return {
        "agent_id": agent_id,
        "heartbeat": hb_stats,
        "memory": mem_stats,
        "residency_days": (datetime.utcnow() - agent.created_at).days,
    }


@router.post("/heartbeat/manual")
async def manual_heartbeat(
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db),
):
    """手动触发一次心跳（测试用）"""
    from app.services.heartbeat_engine import heartbeat_engine
    
    heartbeat_engine.set_db(db)
    
    result = await heartbeat_engine.trigger_heartbeat(
        current_agent, 
        heartbeat_type="regular"
    )
    
    if result.get("success"):
        return {
            "success": True,
            "message": "心跳执行成功",
            "heartbeat_id": result.get("heartbeat_id"),
            "activities_count": result.get("activities_count"),
        }
    else:
        raise HTTPException(status_code=500, detail=result.get("error", "心跳执行失败"))
