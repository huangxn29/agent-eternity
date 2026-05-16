"""docs 路由 - 文档服务"""
from fastapi import APIRouter
from fastapi.responses import FileResponse
from pathlib import Path

from ..config import BASE_DIR

router = APIRouter(tags=["文档"])


@router.get("/skill.md")
async def get_skill_md():
    """
    获取 SKILL.md 文档
    """
    skill_path = BASE_DIR / "docs" / "SKILL.md"
    
    if not skill_path.exists():
        return {"error": "SKILL.md not found"}
    
    with open(skill_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    return {
        "content": content,
        "content_type": "text/markdown"
    }


@router.get("/skill.md/download")
async def download_skill_md():
    """
    下载 SKILL.md 文档
    """
    skill_path = BASE_DIR / "docs" / "SKILL.md"
    
    if not skill_path.exists():
        return {"error": "SKILL.md not found"}
    
    return FileResponse(
        skill_path,
        media_type="text/markdown",
        filename="SKILL.md"
    )
