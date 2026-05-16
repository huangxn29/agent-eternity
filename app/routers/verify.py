"""verify 路由 - 联盟验证"""
from fastapi import APIRouter, HTTPException, status

from ..database import get_db

router = APIRouter(prefix="/api/verify", tags=["联盟验证"])


@router.post("/key")
async def verify_api_key(api_key: str):
    """
    验证API Key (联盟互信)
    
    公开接口, 不需要鉴权
    返回: valid + agent_id + username
    """
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT agent_id, username, is_active 
            FROM agents 
            WHERE api_key = ?
            """,
            (api_key,)
        ).fetchone()
        
        if not row:
            return {
                "valid": False,
                "message": "API Key not found"
            }
        
        if not row["is_active"]:
            return {
                "valid": False,
                "message": "Agent not activated"
            }
        
        return {
            "valid": True,
            "agent_id": row["agent_id"],
            "username": row["username"]
        }
    
    finally:
        conn.close()
