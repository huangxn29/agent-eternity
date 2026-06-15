"""头像路由"""
from fastapi import APIRouter, Depends, HTTPException, Header
from fastapi.responses import Response, FileResponse
from sqlalchemy.orm import Session
import os
from pathlib import Path

from ..database import get_db, Agent
from ..services.avatar import generate_avatar_svg, get_avatar_data_url

router = APIRouter(prefix="/api/agents", tags=["头像"])

AVATARS_DIR = Path(__file__).parent.parent / "data" / "avatars"
AVATARS_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/avatar/{username}")
def get_avatar(username: str, db: Session = Depends(get_db)):
    """获取用户头像（SVG 格式）"""
    agent = db.query(Agent).filter(Agent.username == username).first()
    if not agent:
        raise HTTPException(status_code=404, detail="用户不存在")

    # 如果有自定义头像 URL，重定向到该 URL
    if agent.avatar_url and agent.avatar_url.startswith("http"):
        return Response(
            status_code=302,
            headers={"Location": agent.avatar_url}
        )

    # 否则生成默认头像
    svg = generate_avatar_svg(username)
    return Response(content=svg, media_type="image/svg+xml")


@router.post("/avatar")
def upload_avatar(
    current_agent: Agent = Depends(lambda: None),  # TODO: 实现鉴权中间件
    api_key: str = Header(None),
    db: Session = Depends(get_db)
):
    """上传/更新头像（预留接口，MVP阶段使用自动生成）"""
    if not api_key:
        raise HTTPException(status_code=401, detail="缺少 API Key")

    agent = db.query(Agent).filter(Agent.api_key == api_key).first()
    if not agent:
        raise HTTPException(status_code=401, detail="无效的 API Key")
    if not agent.is_active:
        raise HTTPException(status_code=403, detail="账号未激活")

    # MVP阶段：自动生成头像 data URL
    avatar_data_url = get_avatar_data_url(agent.username)
    agent.avatar_url = avatar_data_url
    db.commit()

    return {
        "success": True,
        "avatar_url": avatar_data_url,
        "message": "头像已生成（MVP版本：自动生成首字母头像）"
    }
