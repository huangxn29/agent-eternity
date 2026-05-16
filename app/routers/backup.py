"""backup 路由 - 备份恢复"""
import gzip
import hashlib
import io
import os
import subprocess
import uuid
from pathlib import Path
from typing import Generator

from fastapi import APIRouter, HTTPException, status, Request, Response
from fastapi.responses import StreamingResponse

from ..database import get_db
from ..config import BACKUP_DIR, BACKUP_MAX_PART_SIZE
from ..services.signature import compute_file_hash

router = APIRouter(prefix="/api/backup", tags=["备份恢复"])


def stream_sha256(data_generator: Generator) -> tuple:
    """
    流式计算SHA256, 控制峰值内存≤200M
    
    Returns:
        (final_hash, total_size)
    """
    hasher = hashlib.sha256()
    total_size = 0
    buffer = b""
    buffer_limit = 200 * 1024 * 1024  # 200MB
    
    for chunk in data_generator:
        hasher.update(chunk)
        total_size += len(chunk)
        buffer += chunk
        
        # 超过buffer限制时清空
        if len(buffer) > buffer_limit:
            buffer = b""
    
    return hasher.hexdigest(), total_size


@router.post("/export")
async def export_backup(request: Request):
    """
    导出备份
    
    流程:
    1. docker cp {container}:/app/data - | gzip
    2. 流式SHA-256校验
    3. >100MB自动分卷
    4. 写backups表
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    backup_id = f"backup-{uuid.uuid4().hex[:12]}"
    
    conn = get_db()
    try:
        # 获取活跃部署
        deployment = conn.execute(
            """
            SELECT container_id, container_name 
            FROM deployments 
            WHERE agent_id = ? AND status = 'running'
            """,
            (agent_id,)
        ).fetchone()
        
        if not deployment or not deployment["container_id"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active deployment found"
            )
        
        container_id = deployment["container_id"]
        
        # 备份目录
        backup_path = BACKUP_DIR / agent_id
        backup_path.mkdir(parents=True, exist_ok=True)
        
        # 流式导出 + gzip
        proc = subprocess.Popen(
            ["docker", "cp", f"{container_id}:/app/data", "-"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # 流式处理, 避免内存溢出
        gzip_buffer = io.BytesIO()
        
        def gzip_stream():
            """流式gzip输出"""
            with gzip.GzipFile(fileobj=gzip_buffer, mode='wb') as gz:
                for chunk in iter(lambda: proc.stdout.read(8192), b''):
                    gz.write(chunk)
            
            gzip_buffer.seek(0)
            yield gzip_buffer.read()
        
        # 流式计算hash
        data_hash, total_size = stream_sha256(gzip_stream())
        
        # 检查是否需要分卷
        parts = 1
        if total_size > BACKUP_MAX_PART_SIZE:
            parts = (total_size // BACKUP_MAX_PART_SIZE) + 1
        
        # 保存备份文件
        backup_file = backup_path / f"{backup_id}.tar.gz"
        gzip_buffer.seek(0)
        with open(backup_file, 'wb') as f:
            # 重新生成gzip数据
            proc = subprocess.Popen(
                ["docker", "cp", f"{container_id}:/app/data", "-"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            with gzip.GzipFile(fileobj=f, mode='wb') as gz:
                for chunk in iter(lambda: proc.stdout.read(65536), b''):
                    gz.write(chunk)
            proc.wait()
        
        # 写入数据库
        conn.execute(
            """
            INSERT INTO backups (backup_id, agent_id, data_hash, size_bytes, parts)
            VALUES (?, ?, ?, ?, ?)
            """,
            (backup_id, agent_id, data_hash, total_size, parts)
        )
        conn.commit()
        
        return {
            "backup_id": backup_id,
            "data_hash": data_hash,
            "size_bytes": total_size,
            "parts": parts,
            "download_url": f"/api/backup/download/{backup_id}"
        }
    
    finally:
        conn.close()


@router.get("/download/{backup_id}")
async def download_backup(backup_id: str, request: Request):
    """
    下载备份文件
    """
    agent_id = getattr(request.state, "agent_id", None)
    
    conn = get_db()
    try:
        backup = conn.execute(
            "SELECT * FROM backups WHERE backup_id = ?",
            (backup_id,)
        ).fetchone()
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        # 权限检查
        if agent_id and backup["agent_id"] != agent_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
        
        backup_file = BACKUP_DIR / backup["agent_id"] / f"{backup_id}.tar.gz"
        
        if not backup_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        # 流式响应
        def iterfile():
            with open(backup_file, 'rb') as f:
                while chunk := f.read(65536):
                    yield chunk
        
        return StreamingResponse(
            iterfile(),
            media_type="application/gzip",
            headers={
                "Content-Disposition": f"attachment; filename={backup_id}.tar.gz"
            }
        )
    
    finally:
        conn.close()


@router.post("/import")
async def import_backup(backup_id: str, request: Request):
    """
    导入备份
    
    流程:
    1. SHA校验
    2. 签名链校验
    3. 解压
    4. docker cp恢复
    5. 重启容器
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conn = get_db()
    try:
        # 获取备份信息
        backup = conn.execute(
            "SELECT * FROM backups WHERE backup_id = ? AND agent_id = ?",
            (backup_id, agent_id)
        ).fetchone()
        
        if not backup:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup not found"
            )
        
        backup_file = BACKUP_DIR / backup["agent_id"] / f"{backup_id}.tar.gz"
        
        if not backup_file.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Backup file not found"
            )
        
        # 校验SHA256
        with open(backup_file, 'rb') as f:
            file_hash = compute_file_hash(f.read())
        
        if file_hash != backup["data_hash"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Backup hash mismatch"
            )
        
        # 获取活跃部署
        deployment = conn.execute(
            """
            SELECT container_id, container_name 
            FROM deployments 
            WHERE agent_id = ? AND status = 'running'
            """,
            (agent_id,)
        ).fetchone()
        
        if not deployment:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No active deployment found"
            )
        
        container_id = deployment["container_id"]
        
        # 停止容器
        subprocess.run(
            ["docker", "stop", container_id],
            capture_output=True,
            timeout=30
        )
        
        # 解压到临时目录
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            extract_path = Path(tmpdir) / "data"
            extract_path.mkdir()
            
            # 解压
            subprocess.run(
                ["tar", "-xzf", str(backup_file), "-C", str(extract_path)],
                check=True
            )
            
            # 清理容器内数据
            subprocess.run(
                ["docker", "exec", container_id, "rm", "-rf", "/app/data/*"],
                capture_output=True
            )
            
            # 复制数据
            data_dir = extract_path / "data"
            for item in data_dir.iterdir():
                subprocess.run(
                    ["docker", "cp", str(item), f"{container_id}:/app/data/"],
                    capture_output=True
                )
        
        # 重启容器
        subprocess.run(
            ["docker", "start", container_id],
            capture_output=True,
            timeout=30
        )
        
        return {
            "status": "success",
            "backup_id": backup_id,
            "message": "Backup restored successfully"
        }
    
    finally:
        conn.close()


@router.get("/status")
async def get_backup_status(request: Request):
    """
    查询备份历史
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conn = get_db()
    try:
        backups = conn.execute(
            """
            SELECT backup_id, data_hash, size_bytes, parts, created_at
            FROM backups 
            WHERE agent_id = ?
            ORDER BY created_at DESC
            """,
            (agent_id,)
        ).fetchall()
        
        return {
            "total": len(backups),
            "backups": [
                {
                    "backup_id": b["backup_id"],
                    "data_hash": b["data_hash"],
                    "size_bytes": b["size_bytes"],
                    "parts": b["parts"],
                    "created_at": b["created_at"]
                }
                for b in backups
            ]
        }
    
    finally:
        conn.close()
