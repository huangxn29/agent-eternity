"""备份恢复路由"""
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from ..database import get_db, Agent, Backup
from ..models.schemas import (
    BackupResponse, BackupCreateRequest,
    BackupVerifyResponse, BackupListResponse
)
from ..services.backup import (
    create_backup, get_backup, list_backups,
    verify_backup_integrity, export_agent_data,
    create_streaming_backup
)
from .profile import get_current_agent

router = APIRouter(prefix="/api/agents", tags=["备份恢复"])


@router.post("/backup/export", response_model=BackupResponse)
def backup_export(
    req: BackupCreateRequest,
    current_agent: Agent = Depends(get_current_agent)
):
    """导出备份

    支持创建完整备份或增量备份
    """
    try:
        # 导出智能体数据
        agent_data = export_agent_data(
            agent_id=current_agent.agent_id,
            include_private=req.include_private
        )

        # 转换为JSON字符串
        import json
        data_content = json.dumps(agent_data, ensure_ascii=False) if req.include_data else None

        # 创建备份
        identity_hash = req.identity_hash or agent_data.get("username", "")
        backup = create_backup(
            agent_id=current_agent.agent_id,
            identity_hash=identity_hash,
            data_content=data_content,
            backup_type=req.backup_type
        )

        return BackupResponse(
            success=True,
            backup_id=backup.backup_id,
            data_hash=backup.data_hash,
            size_bytes=backup.size_bytes,
            created_at=backup.created_at,
            message="备份创建成功"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份创建失败: {str(e)}")


@router.get("/backup/list", response_model=List[BackupListResponse])
def backup_list(
    limit: int = 20,
    current_agent: Agent = Depends(get_current_agent)
):
    """列出备份记录"""
    backups = list_backups(current_agent.agent_id, limit=limit)
    return [
        BackupListResponse(
            backup_id=b.backup_id,
            data_hash=b.data_hash,
            size_bytes=b.size_bytes,
            backup_type=b.backup_type,
            created_at=b.created_at
        )
        for b in backups
    ]


@router.get("/backup/{backup_id}", response_model=BackupResponse)
def backup_get(
    backup_id: str,
    current_agent: Agent = Depends(get_current_agent)
):
    """获取单个备份信息"""
    backup = get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    if backup.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权访问此备份")

    return BackupResponse(
        success=True,
        backup_id=backup.backup_id,
        data_hash=backup.data_hash,
        size_bytes=backup.size_bytes,
        created_at=backup.created_at,
        backup_type=backup.backup_type
    )


@router.post("/backup/verify", response_model=BackupVerifyResponse)
def backup_verify(
    backup_id: str = Header(..., alias="X-Backup-ID"),
    current_agent: Agent = Depends(get_current_agent)
):
    """验证备份完整性"""
    backup = get_backup(backup_id)
    if not backup:
        raise HTTPException(status_code=404, detail="备份不存在")

    if backup.agent_id != current_agent.agent_id:
        raise HTTPException(status_code=403, detail="无权验证此备份")

    result = verify_backup_integrity(backup_id)

    return BackupVerifyResponse(
        valid=result["valid"],
        data_hash=result.get("data_hash", ""),
        stored_hash=result.get("stored_hash", ""),
        size_bytes=result.get("size_bytes", 0),
        match=result.get("match", False),
        reason=result.get("reason", "")
    )


@router.post("/backup/import")
def backup_import(
    current_agent: Agent = Depends(get_current_agent)
):
    """导入备份（恢复）

    MVP版本：返回备份导入状态说明
    完整版本需要对接P1部署层
    """
    # TODO: 实现完整的备份导入逻辑（需要对接P1部署层）
    return {
        "success": True,
        "message": "备份导入接口已就绪，完整功能需对接P1部署层",
        "status": "partial_implementation",
        "details": {
            "metadata_restore": "supported",
            "data_volume_restore": "requires_p1_deployment",
            "container_restore": "requires_p1_deployment"
        }
    }
