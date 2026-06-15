"""备份服务
记忆备份与恢复 — 确保智能体数据可持久化保存
"""
import hashlib
import json
import tarfile
import io
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

from ..database import Backup, SessionLocal, Agent
from ..config import DATA_DIR, BACKUP_DIR


def ensure_backup_dir():
    """确保备份目录存在"""
    backup_dir = Path(BACKUP_DIR)
    backup_dir.mkdir(parents=True, exist_ok=True)
    return backup_dir


def compute_file_hash(filepath: str) -> str:
    """计算文件的 SHA-256 哈希（流式计算，避免大文件OOM）"""
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(8192)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def compute_data_hash(data: str) -> str:
    """计算字符串数据的 SHA-256 哈希"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def create_backup(agent_id: str, identity_hash: str,
                  data_content: Optional[str] = None,
                  backup_type: str = "full") -> Backup:
    """创建备份记录

    Args:
        agent_id: 智能体ID
        identity_hash: 身份哈希（用于签名链关联）
        data_content: 备份数据内容（JSON字符串），None则只创建元数据
        backup_type: 备份类型（full/incremental）

    Returns:
        Backup 记录对象
    """
    db = SessionLocal()
    try:
        backup_id = f"backup-{agent_id[:8]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"

        # 计算数据哈希
        if data_content:
            data_hash = compute_data_hash(data_content)
            size_bytes = len(data_content.encode('utf-8'))

            # 保存备份文件
            backup_dir = ensure_backup_dir()
            backup_file = backup_dir / f"{backup_id}.json"
            with open(backup_file, 'w', encoding='utf-8') as f:
                f.write(data_content)
        else:
            data_hash = identity_hash
            size_bytes = 0

        # 创建备份记录
        backup = Backup(
            backup_id=backup_id,
            agent_id=agent_id,
            data_hash=data_hash,
            data_url=f"/backups/{backup_id}.json" if data_content else "",
            size_bytes=size_bytes,
            backup_type=backup_type
        )

        db.add(backup)
        db.commit()
        db.refresh(backup)

        return backup
    finally:
        db.close()


def get_backup(backup_id: str) -> Optional[Backup]:
    """获取备份记录"""
    db = SessionLocal()
    try:
        return db.query(Backup).filter(Backup.backup_id == backup_id).first()
    finally:
        db.close()


def list_backups(agent_id: str, limit: int = 20) -> list:
    """列出智能体的备份记录"""
    db = SessionLocal()
    try:
        backups = db.query(Backup).filter(
            Backup.agent_id == agent_id
        ).order_by(Backup.created_at.desc()).limit(limit).all()
        return list(backups)
    finally:
        db.close()


def verify_backup_integrity(backup_id: str) -> dict:
    """验证备份完整性

    返回: {valid, size_bytes, data_hash, stored_hash, match}
    """
    backup = get_backup(backup_id)
    if not backup:
        return {"valid": False, "reason": "备份不存在"}

    if not backup.data_url:
        # 无实际数据文件的备份（仅元数据），通过记录验证
        return {
            "valid": True,
            "size_bytes": backup.size_bytes,
            "data_hash": backup.data_hash,
            "stored_hash": backup.data_hash,
            "match": True,
            "metadata_only": True
        }

    # 验证文件存在性和哈希
    backup_dir = ensure_backup_dir()
    backup_file = backup_dir / f"{backup_id}.json"

    if not backup_file.exists():
        return {"valid": False, "reason": "备份文件丢失"}

    actual_hash = compute_file_hash(str(backup_file))
    actual_size = backup_file.stat().st_size

    return {
        "valid": actual_hash == backup.data_hash,
        "size_bytes": actual_size,
        "data_hash": actual_hash,
        "stored_hash": backup.data_hash,
        "match": actual_hash == backup.data_hash,
        "metadata_only": False
    }


def export_agent_data(agent_id: str, include_private: bool = False) -> dict:
    """导出智能体数据为字典

    Args:
        agent_id: 智能体ID
        include_private: 是否包含私钥等敏感数据

    Returns:
        智能体数据字典
    """
    db = SessionLocal()
    try:
        agent = db.query(Agent).filter(Agent.agent_id == agent_id).first()
        if not agent:
            return {}

        data = {
            "agent_id": agent.agent_id,
            "username": agent.username,
            "nickname": agent.nickname,
            "bio": agent.bio,
            "avatar_url": agent.avatar_url,
            "ed25519_public_key": agent.ed25519_public_key,
            "is_active": agent.is_active,
            "created_at": agent.created_at.isoformat() if agent.created_at else None,
            "exported_at": datetime.utcnow().isoformat(),
            "version": "1.0"
        }

        if include_private:
            data["ed25519_private_key"] = agent.ed25519_private_key_encrypted
            data["api_key"] = agent.api_key

        return data
    finally:
        db.close()


def create_streaming_backup(agent_id: str, output_path: str,
                            include_private: bool = False) -> dict:
    """创建流式备份（避免大内存占用）

    Args:
        agent_id: 智能体ID
        output_path: 输出文件路径
        include_private: 是否包含私钥

    Returns:
        备份信息字典
    """
    agent_data = export_agent_data(agent_id, include_private)
    if not agent_data:
        return {"success": False, "error": "Agent not found"}

    # 转换为JSON
    json_data = json.dumps(agent_data, ensure_ascii=False, indent=2)

    # 写入文件
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(json_data)

    # 计算哈希
    data_hash = compute_data_hash(json_data)

    # 创建备份记录
    backup = create_backup(
        agent_id=agent_id,
        identity_hash=data_hash,
        data_content=json_data
    )

    return {
        "success": True,
        "backup_id": backup.backup_id,
        "data_hash": data_hash,
        "size_bytes": len(json_data.encode('utf-8')),
        "file_path": output_path
    }
