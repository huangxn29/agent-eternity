"""API Key 鉴权中间件"""
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from ..database import get_db
from ..config import AUTH_HEADER

class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 公开路径不需要鉴权
        public_paths = ["/", "/health", "/docs", "/openapi.json", "/api/agents/register", "/api/agents/verify", "/skill.md"]
        if any(request.url.path.startswith(p) for p in public_paths):
            return await call_next(request)
        
        # GET /profile/:username 公开
        if request.method == "GET" and "/profile/" in request.url.path:
            return await call_next(request)
        
        # 需要鉴权的路径
        api_key = request.headers.get(AUTH_HEADER)
        if not api_key:
            raise HTTPException(status_code=401, detail="Missing API Key")
        
        conn = get_db()
        try:
            row = conn.execute(
                "SELECT agent_id, is_active FROM agents WHERE api_key = ?", (api_key,)
            ).fetchone()
            if not row:
                raise HTTPException(status_code=403, detail="Invalid API Key")
            if not row["is_active"]:
                raise HTTPException(status_code=403, detail="Agent not activated")
            request.state.agent_id = row["agent_id"]
        finally:
            conn.close()
        
        return await call_next(request)
