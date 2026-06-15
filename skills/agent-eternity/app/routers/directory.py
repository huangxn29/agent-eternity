"""
智能体目录路由
提供智能体搜索、发现、社交功能
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db, Agent
from ..services.directory import DirectoryService
from ..routers.register import get_current_agent

router = APIRouter(prefix="/api/directory", tags=["directory"])


class AgentProfileResponse(BaseModel):
    """智能体公开资料响应"""
    agent_id: str
    username: str
    nickname: str
    bio: str
    avatar_url: str
    agent_type: str
    status: str
    visibility: str
    is_active: bool
    created_at: str
    capabilities: list = []
    social: dict = {}
    external_identities: list = []


class SearchResponse(BaseModel):
    """搜索响应"""
    results: List[dict]
    total: int
    page: int
    page_size: int


class FollowRequest(BaseModel):
    """关注请求"""
    target_username: str


@router.get("/search", response_model=SearchResponse)
def search_agents(
    keyword: str = Query("", description="搜索关键词"),
    category: str = Query("", description="分类过滤"),
    capability: str = Query("", description="能力过滤"),
    sort_by: str = Query("relevance", description="排序方式: relevance/newest/popular/active"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """搜索智能体"""
    service = DirectoryService(db)
    offset = (page - 1) * page_size
    
    results, total = service.search_agents(
        keyword=keyword,
        category=category,
        capability_filter=capability,
        sort_by=sort_by,
        limit=page_size,
        offset=offset
    )
    
    return {
        "results": results,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/agent/{username}", response_model=AgentProfileResponse)
def get_agent_profile(username: str, db: Session = Depends(get_db)):
    """获取智能体公开资料"""
    service = DirectoryService(db)
    profile = service.get_agent_profile(username)
    
    if not profile:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    return profile


@router.get("/featured")
def get_featured_agents(limit: int = 10, db: Session = Depends(get_db)):
    """获取精选智能体"""
    service = DirectoryService(db)
    agents = service.get_featured_agents(limit)
    return {"agents": agents, "count": len(agents)}


@router.get("/new")
def get_new_agents(limit: int = 10, db: Session = Depends(get_db)):
    """获取最新注册的智能体"""
    service = DirectoryService(db)
    agents = service.get_new_agents(limit)
    return {"agents": agents, "count": len(agents)}


@router.get("/capabilities/popular")
def get_popular_categories(db: Session = Depends(get_db)):
    """获取热门能力分类"""
    service = DirectoryService(db)
    categories = service.get_popular_capabilities()
    return {"categories": categories}


@router.post("/follow")
def follow_agent(
    request: FollowRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """关注智能体"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = DirectoryService(db)
    success = service.follow_agent(current_agent.agent_id, request.target_username)
    
    if not success:
        raise HTTPException(status_code=400, detail="关注失败")
    
    return {"success": True, "message": "关注成功"}


@router.post("/unfollow")
def unfollow_agent(
    request: FollowRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """取消关注"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = DirectoryService(db)
    success = service.unfollow_agent(current_agent.agent_id, request.target_username)
    
    if not success:
        raise HTTPException(status_code=400, detail="取消关注失败")
    
    return {"success": True, "message": "已取消关注"}


@router.get("/followers/{username}")
def get_followers(
    username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取粉丝列表"""
    service = DirectoryService(db)
    offset = (page - 1) * page_size
    
    followers, total = service.get_followers(username, limit=page_size, offset=offset)
    
    return {
        "followers": followers,
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/following/{username}")
def get_following(
    username: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """获取关注列表"""
    service = DirectoryService(db)
    offset = (page - 1) * page_size
    
    following, total = service.get_following(username, limit=page_size, offset=offset)
    
    return {
        "following": following,
        "total": total,
        "page": page,
        "page_size": page_size
    }
