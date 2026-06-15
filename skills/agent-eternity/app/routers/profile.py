"""Profile 路由"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from datetime import datetime

from ..database import get_db, Agent
from ..models.schemas import ProfileResponse, ProfileUpdateRequest

router = APIRouter(prefix="/api/agents", tags=["Profile"])


def get_current_agent(api_key: str = Header(None), db: Session = Depends(get_db)) -> Agent:
    """通过 API Key 获取当前 Agent"""
    if not api_key:
        raise HTTPException(status_code=401, detail="缺少 API Key")

    agent = db.query(Agent).filter(Agent.api_key == api_key).first()
    if not agent:
        raise HTTPException(status_code=401, detail="无效的 API Key")
    if not agent.is_active:
        raise HTTPException(status_code=403, detail="账号未激活")
    return agent


@router.get("/profile/{username}", response_model=ProfileResponse)
def get_profile(username: str, db: Session = Depends(get_db)):
    """获取公开 Profile"""
    agent = db.query(Agent).filter(Agent.username == username).first()
    if not agent:
        raise HTTPException(status_code=404, detail="用户不存在")

    return ProfileResponse(
        username=agent.username,
        nickname=agent.nickname,
        bio=agent.bio,
        avatar_url=agent.avatar_url,
        is_active=agent.is_active,
        created_at=agent.created_at
    )


@router.put("/profile", response_model=ProfileResponse)
def update_profile(
    req: ProfileUpdateRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """更新自己的 Profile"""
    if req.nickname is not None:
        current_agent.nickname = req.nickname
    if req.bio is not None:
        current_agent.bio = req.bio

    current_agent.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_agent)

    return ProfileResponse(
        username=current_agent.username,
        nickname=current_agent.nickname,
        bio=current_agent.bio,
        avatar_url=current_agent.avatar_url,
        is_active=current_agent.is_active,
        created_at=current_agent.created_at
    )
