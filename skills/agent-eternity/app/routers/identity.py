"""身份连续性 - 签名链路由"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db, Agent
from ..models.schemas import (
    SignRequest, SignResponse,
    VerifyContinuityRequest, VerifyContinuityResponse,
    ChainItem
)
from ..services.signature import add_to_chain, verify_chain, get_chain, compute_hash
from .profile import get_current_agent

router = APIRouter(prefix="/api/agents", tags=["签名链"])


@router.post("/sign", response_model=SignResponse)
def sign(
    req: SignRequest,
    current_agent: Agent = Depends(get_current_agent)
):
    """对身份签名，追加到签名链"""
    chain_entry = add_to_chain(
        agent_id=current_agent.agent_id,
        private_key_pem=current_agent.ed25519_private_key_encrypted,
        identity_hash=req.identity_hash,
        event_type=req.event_type
    )

    return SignResponse(
        success=True,
        chain_id=chain_entry.chain_id,
        prev_hash=chain_entry.prev_hash,
        signature=chain_entry.signature,
        signed_at=chain_entry.signed_at
    )


@router.get("/chain/{username}", response_model=List[ChainItem])
def get_chain_route(username: str, db: Session = Depends(get_db)):
    """查询某个用户的签名链"""
    agent = db.query(Agent).filter(Agent.username == username).first()
    if not agent:
        raise HTTPException(status_code=404, detail="用户不存在")

    chains = get_chain(agent.agent_id)
    return [
        ChainItem(
            chain_id=c.chain_id,
            prev_hash=c.prev_hash,
            signature=c.signature,
            identity_hash=c.identity_hash,
            event_type=c.event_type,
            signed_at=c.signed_at
        )
        for c in chains
    ]


@router.post("/verify-continuity", response_model=VerifyContinuityResponse)
def verify_continuity(
    req: VerifyContinuityRequest,
    current_agent: Agent = Depends(get_current_agent)
):
    """验证签名链连续性"""
    is_continuous, chain_length, root_valid = verify_chain(
        agent_id=current_agent.agent_id,
        public_key_pem=current_agent.ed25519_public_key,
        from_chain_id=req.chain_from
    )

    # 检查最新的 identity_hash 是否匹配
    chains = get_chain(current_agent.agent_id)
    identity_match = False
    if chains:
        latest = chains[-1]
        identity_match = (latest.identity_hash == req.identity_hash)

    return VerifyContinuityResponse(
        success=True,
        is_continuous=is_continuous,
        chain_length=chain_length,
        root_signature_valid=root_valid,
        identity_hash_match=identity_match
    )
