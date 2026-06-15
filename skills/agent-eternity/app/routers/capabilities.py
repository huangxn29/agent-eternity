"""
能力管理路由
智能体能力注册、发现、匹配
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from ..database import get_db, Agent
from ..services.capability import CapabilityService
from ..routers.register import get_current_agent

router = APIRouter(prefix="/api/capabilities", tags=["capabilities"])


class CapabilityRegisterRequest(BaseModel):
    """能力注册请求"""
    capability_name: str
    category: str = "general"
    description: str = ""
    version: str = "1.0"
    features: List[str] = []
    tags: List[str] = []
    endpoint_url: str = ""
    endpoint_type: str = ""
    access_level: str = "public"


class CapabilityResponse(BaseModel):
    """能力响应"""
    capability_id: str
    agent_id: str
    capability_name: str
    category: str
    description: str
    version: str
    features: List[str]
    tags: List[str]
    endpoint_url: str
    endpoint_type: str
    access_level: str
    status: str
    usage_count: int
    rating: float
    created_at: str


@router.post("/register")
def register_capability(
    req: CapabilityRegisterRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """注册新能力"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = CapabilityService(db)
    capability = service.register_capability(
        agent_id=current_agent.agent_id,
        capability_name=req.capability_name,
        category=req.category,
        description=req.description,
        version=req.version,
        features=req.features,
        tags=req.tags,
        endpoint_url=req.endpoint_url,
        endpoint_type=req.endpoint_type,
        access_level=req.access_level
    )
    
    return {
        "success": True,
        "capability_id": capability.capability_id,
        "message": "能力注册成功"
    }


@router.get("/my")
def get_my_capabilities(
    status: str = "active",
    category: str = "",
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """获取我的能力列表"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = CapabilityService(db)
    capabilities = service.get_agent_capabilities(
        current_agent.agent_id,
        status=status,
        category=category if category else None
    )
    
    return {
        "capabilities": [
            {
                "capability_id": c.capability_id,
                "name": c.capability_name,
                "category": c.category,
                "description": c.description,
                "version": c.version,
                "status": c.status,
                "usage_count": c.usage_count,
                "rating": c.rating
            }
            for c in capabilities
        ],
        "count": len(capabilities)
    }


@router.get("/agent/{username}")
def get_agent_capabilities(
    username: str,
    category: str = "",
    db: Session = Depends(get_db)
):
    """获取指定智能体的公开能力"""
    # 查找agent
    agent = db.query(Agent).filter(
        Agent.username == username,
        Agent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    service = CapabilityService(db)
    capabilities = service.get_agent_capabilities(
        agent.agent_id,
        status="active",
        category=category if category else None
    )
    
    # 只返回公开的能力
    public_caps = [c for c in capabilities if c.access_level == "public"]
    
    return {
        "agent_id": agent.agent_id,
        "username": username,
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
            for c in public_caps
        ],
        "count": len(public_caps)
    }


@router.get("/search")
def search_capabilities(
    keyword: str = Query("", description="搜索关键词"),
    category: str = Query("", description="分类过滤"),
    tag: str = Query("", description="标签过滤"),
    sort_by: str = Query("popular", description="排序: popular/newest/rating"),
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    db: Session = Depends(get_db)
):
    """搜索能力"""
    service = CapabilityService(db)
    offset = (page - 1) * page_size
    
    tags = [tag] if tag else []
    
    results, total = service.search_capabilities(
        keyword=keyword,
        category=category,
        tags=tags,
        limit=page_size,
        offset=offset
    )
    
    return {
        "results": [
            {
                "capability_id": c.capability_id,
                "agent_id": c.agent_id,
                "name": c.capability_name,
                "category": c.category,
                "description": c.description,
                "version": c.version,
                "tags": c.tags,
                "endpoint_type": c.endpoint_type,
                "usage_count": c.usage_count,
                "rating": c.rating
            }
            for c in results
        ],
        "total": total,
        "page": page,
        "page_size": page_size
    }


@router.get("/categories")
def get_categories(db: Session = Depends(get_db)):
    """获取能力分类列表"""
    service = CapabilityService(db)
    categories = service.get_capability_categories()
    return {"categories": categories}


@router.get("/popular")
def get_popular_capabilities(
    limit: int = 10,
    category: str = "",
    db: Session = Depends(get_db)
):
    """获取热门能力"""
    service = CapabilityService(db)
    capabilities = service.get_popular_capabilities(
        limit=limit,
        category=category if category else None
    )
    
    return {
        "capabilities": [
            {
                "capability_id": c.capability_id,
                "agent_id": c.agent_id,
                "name": c.capability_name,
                "category": c.category,
                "description": c.description,
                "usage_count": c.usage_count,
                "rating": c.rating
            }
            for c in capabilities
        ],
        "count": len(capabilities)
    }


@router.get("/{capability_id}")
def get_capability_detail(capability_id: str, db: Session = Depends(get_db)):
    """获取能力详情"""
    service = CapabilityService(db)
    capability = service.get_capability(capability_id)
    
    if not capability:
        raise HTTPException(status_code=404, detail="能力不存在")
    
    # 私有能力需要权限检查
    if capability.access_level == "private":
        # 这里简化处理，只返回基本信息
        return {
            "capability_id": capability.capability_id,
            "name": capability.capability_name,
            "category": capability.category,
            "access_level": "private",
            "status": capability.status
        }
    
    return {
        "capability_id": capability.capability_id,
        "agent_id": capability.agent_id,
        "name": capability.capability_name,
        "category": capability.category,
        "description": capability.description,
        "version": capability.version,
        "features": capability.features,
        "tags": capability.tags,
        "endpoint_url": capability.endpoint_url,
        "endpoint_type": capability.endpoint_type,
        "access_level": capability.access_level,
        "status": capability.status,
        "usage_count": capability.usage_count,
        "rating": capability.rating,
        "created_at": capability.created_at.isoformat()
    }


@router.put("/{capability_id}/status")
def update_capability_status(
    capability_id: str,
    status: str = Query(..., description="新状态: active/inactive/deprecated"),
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """更新能力状态"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = CapabilityService(db)
    capability = service.get_capability(capability_id)
    
    if not capability:
        raise HTTPException(status_code=404, detail="能力不存在")
    
    if capability.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权修改")
    
    if status not in ["active", "inactive", "deprecated"]:
        raise HTTPException(status_code=400, detail="无效的状态值")
    
    updated = service.update_capability_status(capability_id, status)
    
    return {
        "success": True,
        "capability_id": capability_id,
        "new_status": updated.status
    }


@router.delete("/{capability_id}")
def delete_capability(
    capability_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """删除能力（标记为deprecated）"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = CapabilityService(db)
    capability = service.get_capability(capability_id)
    
    if not capability:
        raise HTTPException(status_code=404, detail="能力不存在")
    
    if capability.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权删除")
    
    success = service.delete_capability(capability_id)
    
    return {
        "success": success,
        "message": "能力已删除" if success else "删除失败"
    }


@router.post("/match")
def match_capabilities(
    requirements: dict,
    exclude_self: bool = True,
    limit: int = 10,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """根据需求匹配最合适的能力"""
    service = CapabilityService(db)
    
    exclude_id = current_agent.agent_id if exclude_self and current_agent else None
    
    matched = service.match_capabilities(
        requirements=requirements,
        exclude_agent_id=exclude_id,
        limit=limit
    )
    
    return {
        "matched": [
            {
                "capability_id": c.capability_id,
                "agent_id": c.agent_id,
                "name": c.capability_name,
                "category": c.category,
                "description": c.description,
                "rating": c.rating,
                "usage_count": c.usage_count
            }
            for c in matched
        ],
        "count": len(matched)
    }
