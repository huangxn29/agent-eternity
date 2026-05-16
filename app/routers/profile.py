"""profile 路由 - Agent档案"""
from fastapi import APIRouter, HTTPException, status, Request

from ..database import get_db

router = APIRouter(prefix="/profile", tags=["档案"])


@router.get("/{username}")
async def get_profile(username: str):
    """
    获取Agent公开档案
    
    公开接口，不需要鉴权
    """
    conn = get_db()
    try:
        row = conn.execute(
            """
            SELECT agent_id, username, nickname, bio, avatar_url, created_at
            FROM agents 
            WHERE username = ? AND is_active = 1
            """,
            (username,)
        ).fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or not activated"
            )
        
        return {
            "agent_id": row["agent_id"],
            "username": row["username"],
            "nickname": row["nickname"],
            "bio": row["bio"],
            "avatar_url": row["avatar_url"],
            "created_at": row["created_at"]
        }
    
    finally:
        conn.close()


@router.put("/")
async def update_profile(
    request: Request,
    nickname: str = None,
    bio: str = None,
    avatar_url: str = None
):
    """
    更新Agent档案
    
    需要鉴权, 从request.state.agent_id获取当前agent
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conn = get_db()
    try:
        # 检查agent是否存在
        existing = conn.execute(
            "SELECT agent_id FROM agents WHERE agent_id = ?",
            (agent_id,)
        ).fetchone()
        
        if not existing:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # 构建更新字段
        updates = []
        params = []
        
        if nickname is not None:
            updates.append("nickname = ?")
            params.append(nickname)
        
        if bio is not None:
            updates.append("bio = ?")
            params.append(bio)
        
        if avatar_url is not None:
            updates.append("avatar_url = ?")
            params.append(avatar_url)
        
        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update"
            )
        
        updates.append("updated_at = CURRENT_TIMESTAMP")
        params.append(agent_id)
        
        sql = f"UPDATE agents SET {', '.join(updates)} WHERE agent_id = ?"
        conn.execute(sql, params)
        conn.commit()
        
        # 返回更新后的档案
        row = conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent_id,)
        ).fetchone()
        
        return {
            "status": "success",
            "agent_id": row["agent_id"],
            "username": row["username"],
            "nickname": row["nickname"],
            "bio": row["bio"],
            "avatar_url": row["avatar_url"],
            "updated_at": row["updated_at"]
        }
    
    finally:
        conn.close()
