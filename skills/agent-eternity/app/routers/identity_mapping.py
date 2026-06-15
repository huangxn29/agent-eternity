"""
身份映射路由
跨平台身份关联、验证和身份图谱
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from ..database import get_db, Agent
from ..services.identity_mapping import IdentityMappingService
from ..routers.register import get_current_agent

router = APIRouter(prefix="/api/identity-mapping", tags=["identity-mapping"])


class AddMappingRequest(BaseModel):
    """添加映射请求"""
    external_platform: str
    external_id: str
    external_username: str = ""
    external_metadata: Dict[str, Any] = {}
    verification_method: str = ""
    proof_signature: str = ""
    proof_data: Dict[str, Any] = {}


@router.post("/add")
def add_mapping(
    req: AddMappingRequest,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """添加身份映射"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = IdentityMappingService(db)
    mapping = service.add_mapping(
        agent_id=current_agent.agent_id,
        external_platform=req.external_platform,
        external_id=req.external_id,
        external_username=req.external_username,
        external_metadata=req.external_metadata,
        verification_method=req.verification_method,
        proof_signature=req.proof_signature,
        proof_data=req.proof_data
    )
    
    return {
        "success": True,
        "mapping_id": mapping.mapping_id,
        "status": mapping.verification_status,
        "message": "身份映射已添加"
    }


@router.get("/my")
def get_my_mappings(
    status: str = "",
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """获取我的身份映射列表"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = IdentityMappingService(db)
    mappings = service.get_agent_mappings(
        current_agent.agent_id,
        verification_status=status if status else None
    )
    
    return {
        "mappings": [
            {
                "mapping_id": m.mapping_id,
                "platform": m.external_platform,
                "external_id": m.external_id,
                "external_username": m.external_username,
                "verification_status": m.verification_status,
                "verification_method": m.verification_method,
                "verified_at": m.verified_at.isoformat() if m.verified_at else None,
                "created_at": m.created_at.isoformat()
            }
            for m in mappings
        ],
        "count": len(mappings)
    }


@router.get("/agent/{username}")
def get_agent_mappings(
    username: str,
    db: Session = Depends(get_db)
):
    """获取指定智能体的已验证身份映射"""
    agent = db.query(Agent).filter(
        Agent.username == username,
        Agent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    service = IdentityMappingService(db)
    mappings = service.get_agent_mappings(
        agent.agent_id,
        verification_status="verified"
    )
    
    return {
        "agent_id": agent.agent_id,
        "username": username,
        "mappings": [
            {
                "platform": m.external_platform,
                "external_username": m.external_username,
                "verified_at": m.verified_at.isoformat() if m.verified_at else None
            }
            for m in mappings
        ],
        "count": len(mappings)
    }


@router.post("/verify/{mapping_id}")
def verify_mapping(
    mapping_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """验证身份映射"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = IdentityMappingService(db)
    
    # 检查映射是否属于当前用户
    from ..database import IdentityMapping
    mapping = db.query(IdentityMapping).filter(
        IdentityMapping.mapping_id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="映射不存在")
    
    if mapping.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    verified = service.verify_mapping(mapping_id)
    
    return {
        "success": verified is not None,
        "status": verified.verification_status if verified else None,
        "message": "验证成功" if verified else "验证失败"
    }


@router.post("/revoke/{mapping_id}")
def revoke_mapping(
    mapping_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """撤销身份映射"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = IdentityMappingService(db)
    
    # 检查映射是否属于当前用户
    from ..database import IdentityMapping
    mapping = db.query(IdentityMapping).filter(
        IdentityMapping.mapping_id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="映射不存在")
    
    if mapping.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    revoked = service.revoke_mapping(mapping_id)
    
    return {
        "success": revoked is not None,
        "status": revoked.verification_status if revoked else None,
        "message": "已撤销" if revoked else "撤销失败"
    }


@router.delete("/{mapping_id}")
def delete_mapping(
    mapping_id: str,
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """删除身份映射"""
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = IdentityMappingService(db)
    
    # 检查映射是否属于当前用户
    from ..database import IdentityMapping
    mapping = db.query(IdentityMapping).filter(
        IdentityMapping.mapping_id == mapping_id
    ).first()
    
    if not mapping:
        raise HTTPException(status_code=404, detail="映射不存在")
    
    if mapping.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权操作")
    
    success = service.delete_mapping(mapping_id)
    
    return {
        "success": success,
        "message": "已删除" if success else "删除失败"
    }


@router.get("/find")
def find_by_external_id(
    platform: str = Query(..., description="外部平台名称"),
    external_id: str = Query(..., description="外部平台ID"),
    db: Session = Depends(get_db)
):
    """通过外部ID查找对应的智能体"""
    service = IdentityMappingService(db)
    mapping = service.find_by_external_id(platform, external_id)
    
    if not mapping:
        raise HTTPException(status_code=404, detail="未找到匹配的智能体")
    
    agent = db.query(Agent).filter(
        Agent.agent_id == mapping.agent_id
    ).first()
    
    if not agent or agent.visibility != "public":
        raise HTTPException(status_code=404, detail="未找到匹配的智能体")
    
    return {
        "found": True,
        "agent": {
            "agent_id": agent.agent_id,
            "username": agent.username,
            "nickname": agent.nickname,
            "avatar_url": agent.avatar_url,
        },
        "external_platform": mapping.external_platform,
        "external_username": mapping.external_username,
        "verified_at": mapping.verified_at.isoformat() if mapping.verified_at else None
    }


@router.get("/platforms")
def get_platforms(db: Session = Depends(get_db)):
    """获取支持的平台列表及统计"""
    service = IdentityMappingService(db)
    platforms = service.get_platforms()
    return {"platforms": platforms}


@router.get("/challenge")
def get_verification_challenge(
    platform: str = Query(..., description="要验证的平台"),
    current_agent: Agent = Depends(get_current_agent),
    db: Session = Depends(get_db)
):
    """获取验证挑战码
    
    用户需要在外部平台发布这个验证码来证明所有权
    """
    if not current_agent:
        raise HTTPException(status_code=401, detail="未认证")
    
    service = IdentityMappingService(db)
    challenge = service.generate_verification_challenge(
        agent_id=current_agent.agent_id,
        external_platform=platform
    )
    
    return challenge


@router.get("/graph/{username}")
def get_identity_graph(
    username: str,
    depth: int = 2,
    db: Session = Depends(get_db)
):
    """获取身份图谱
    
    通过共同的外部身份发现智能体之间的关联
    """
    agent = db.query(Agent).filter(
        Agent.username == username,
        Agent.is_active == True
    ).first()
    
    if not agent:
        raise HTTPException(status_code=404, detail="智能体不存在")
    
    service = IdentityMappingService(db)
    graph = service.get_identity_graph(agent.agent_id, depth=depth)
    
    return graph
