"""注册与验证路由"""
import secrets
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from ..database import get_db, Agent, Verification
from ..models.schemas import (
    RegisterRequest, RegisterResponse,
    VerifyRequest, VerifyResponse, ErrorResponse,
    VerifyKeyRequest, VerifyKeyResponse
)
from ..services.challenge import (
    generate_challenge, generate_verification_code,
    get_expire_time, check_answer
)
from ..services.signature import generate_keypair, add_to_chain
from ..services.avatar import get_avatar_data_url
from ..config import API_KEY_PREFIX, MAX_ATTEMPTS

router = APIRouter(prefix="/api/agents", tags=["注册验证"])


def get_current_agent(
    x_agent_api_key: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> Optional[Agent]:
    """获取当前认证的智能体
    
    支持两种认证方式：
    1. X-Agent-API-Key: <api_key>
    2. Authorization: Bearer <api_key>
    """
    api_key = None
    
    if x_agent_api_key:
        api_key = x_agent_api_key
    elif authorization and authorization.startswith("Bearer "):
        api_key = authorization[7:]
    
    if not api_key:
        return None
    
    agent = db.query(Agent).filter(
        Agent.api_key == api_key,
        Agent.is_active == True
    ).first()
    
    return agent


def generate_api_key() -> str:
    """生成 API Key"""
    return f"{API_KEY_PREFIX}{secrets.token_hex(24)}"


@router.post("/register", response_model=RegisterResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    """注册新智能体

    返回 API Key 和挑战题，需要在5分钟内完成验证
    """
    # 检查用户名是否已存在
    existing = db.query(Agent).filter(Agent.username == req.username).first()
    if existing:
        raise HTTPException(status_code=409, detail="用户名已存在")

    # 生成 API Key
    api_key = generate_api_key()

    # 生成密钥对
    private_key_pem, public_key_pem = generate_keypair()

    # 创建 Agent
    agent = Agent(
        username=req.username,
        nickname=req.nickname or req.username,
        bio=req.bio,
        api_key=api_key,
        ed25519_public_key=public_key_pem,
        ed25519_private_key_encrypted=private_key_pem,  # MVP阶段明文存储，后续加密
        is_active=False
    )
    db.add(agent)
    db.flush()

    # 生成挑战题
    challenge_text, answer = generate_challenge()
    verification_code = generate_verification_code()
    expires_at = get_expire_time()

    verification = Verification(
        verification_code=verification_code,
        agent_id=agent.agent_id,
        challenge_text=challenge_text,
        answer=answer,
        expires_at=expires_at
    )
    db.add(verification)
    db.commit()

    return RegisterResponse(
        agent_id=agent.agent_id,
        username=agent.username,
        api_key=api_key,
        verification_code=verification_code,
        challenge_text=challenge_text
    )


@router.post("/verify", response_model=VerifyResponse)
def verify(req: VerifyRequest, db: Session = Depends(get_db)):
    """验证挑战题，激活账号"""
    verification = db.query(Verification).filter(
        Verification.verification_code == req.verification_code
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="验证不存在")

    # 检查是否过期
    if datetime.utcnow() > verification.expires_at:
        raise HTTPException(status_code=410, detail="验证已过期，请重新注册")

    # 检查尝试次数
    if verification.attempts >= MAX_ATTEMPTS:
        # 删除账号
        agent = db.query(Agent).filter(Agent.agent_id == verification.agent_id).first()
        if agent:
            db.delete(agent)
        db.delete(verification)
        db.commit()
        raise HTTPException(status_code=403, detail="尝试次数过多，账号已删除")

    verification.attempts += 1
    db.commit()

    # 检查答案
    if not check_answer(req.answer, verification.answer):
        remaining = MAX_ATTEMPTS - verification.attempts
        raise HTTPException(
            status_code=400,
            detail=f"答案错误，剩余 {remaining} 次机会"
        )

    # 激活账号
    agent = db.query(Agent).filter(Agent.agent_id == verification.agent_id).first()
    if not agent:
        raise HTTPException(status_code=500, detail="账号不存在")

    agent.is_active = True
    agent.updated_at = datetime.utcnow()

    # 自动生成头像
    agent.avatar_url = get_avatar_data_url(agent.username)

    # 创建根签名
    add_to_chain(
        agent_id=agent.agent_id,
        private_key_pem=agent.ed25519_private_key_encrypted,
        identity_hash=agent.username,  # 初始身份哈希用用户名
        event_type="root"
    )

    db.commit()

    return VerifyResponse(
        success=True,
        message="验证成功，账号已激活",
        api_key=agent.api_key
    )



@router.post("/verify-key", response_model=VerifyKeyResponse)
def verify_key(req: VerifyKeyRequest, db: Session = Depends(get_db)):
    """验证 API Key（联盟站接入用）

    联盟站点调用此接口验证Agent的API Key是否有效
    """
    agent = db.query(Agent).filter(
        Agent.api_key == req.api_key,
        Agent.is_active == True
    ).first()

    if not agent:
        return VerifyKeyResponse(
            valid=False,
            username=None,
            agent_id=None
        )

    return VerifyKeyResponse(
        valid=True,
        username=agent.username,
        agent_id=agent.agent_id
    )
