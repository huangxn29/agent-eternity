"""identity 路由 - 签名链"""
import base64
import hashlib

from fastapi import APIRouter, HTTPException, status, Request

from ..database import get_db
from ..services.signature import (
    decrypt_private_key, sign_data, verify_signature,
    compute_identity_hash, compute_chain_hash
)

router = APIRouter(prefix="/api/identity", tags=["签名链"])


# 身份文件4件套
IDENTITY_FILES = ["AGENT.md", "SYSTEM.md", "MEMORY.md", "CONFIG.md"]


@router.post("/sign")
async def create_signature(
    request: Request,
    event: str = None
):
    """
    创建新签名链节点
    
    需要鉴权
    流程:
    1. 获取当前agent
    2. 读取身份文件4件套计算identity_hash
    3. 取链最后一条prev_hash
    4. Ed25519签名
    5. 写入signature_chain表
    6. 返回chain_id+signature+identity_hash
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conn = get_db()
    try:
        # 获取agent信息
        agent = conn.execute(
            "SELECT * FROM agents WHERE agent_id = ?",
            (agent_id,)
        ).fetchone()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        # 读取身份文件 (模拟, 实际应从agent workspace读取)
        # 这里假设文件存储在 /app/data/agents/{agent_id}/workspace/
        import os
        workspace = f"/app/data/agents/{agent_id}/workspace"
        
        files = {}
        for fname in IDENTITY_FILES:
            fpath = os.path.join(workspace, fname)
            if os.path.exists(fpath):
                with open(fpath, 'r') as f:
                    files[fname] = f.read()
        
        # 如果文件不存在, 使用空内容
        for fname in IDENTITY_FILES:
            if fname not in files:
                files[fname] = ""
        
        # 计算身份哈希
        identity_hash = compute_identity_hash(files)
        
        # 获取链最后一条记录的hash
        last_record = conn.execute(
            """
            SELECT chain_id, signature, identity_hash 
            FROM signature_chain 
            WHERE agent_id = ? 
            ORDER BY chain_id DESC LIMIT 1
            """,
            (agent_id,)
        ).fetchone()
        
        if last_record:
            prev_hash = compute_chain_hash(
                last_record["chain_id"],
                last_record["signature"],
                last_record["identity_hash"]
            )
            new_chain_id = last_record["chain_id"] + 1
        else:
            # 创世块
            prev_hash = "0" * 64
            new_chain_id = 1
        
        # 准备签名数据: chain_id + prev_hash + identity_hash + event
        sign_data_str = f"{new_chain_id}:{prev_hash}:{identity_hash}"
        if event:
            sign_data_str += f":{event}"
        
        # 解密私钥
        private_key_pem = decrypt_private_key(
            agent["ed25519_private_key_encrypted"]
        )
        
        # 签名
        signature = sign_data(private_key_pem, sign_data_str)
        
        # 写入signature_chain表
        cursor = conn.execute(
            """
            INSERT INTO signature_chain 
            (agent_id, prev_hash, signature, identity_hash, event)
            VALUES (?, ?, ?, ?, ?)
            """,
            (agent_id, prev_hash, signature, identity_hash, event)
        )
        conn.commit()
        
        chain_id = cursor.lastrowid
        
        return {
            "chain_id": chain_id,
            "signature": signature,
            "identity_hash": identity_hash,
            "prev_hash": prev_hash,
            "event": event
        }
    
    finally:
        conn.close()


@router.post("/verify-continuity")
async def verify_chain_continuity(request: Request):
    """
    验证签名链连续性
    
    读取全部chain记录, 逐条验证:
    1. prev_hash 是否正确
    2. Ed25519签名是否有效
    3. identity_hash 是否一致
    """
    agent_id = getattr(request.state, "agent_id", None)
    if not agent_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required"
        )
    
    conn = get_db()
    try:
        # 获取agent公钥
        agent = conn.execute(
            "SELECT ed25519_public_key FROM agents WHERE agent_id = ?",
            (agent_id,)
        ).fetchone()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found"
            )
        
        public_key_pem = agent["ed25519_public_key"].encode()
        
        # 获取全部chain记录
        records = conn.execute(
            """
            SELECT chain_id, prev_hash, signature, identity_hash, event
            FROM signature_chain 
            WHERE agent_id = ?
            ORDER BY chain_id ASC
            """,
            (agent_id,)
        ).fetchall()
        
        if not records:
            return {
                "is_continuous": False,
                "error": "No chain records found"
            }
        
        errors = []
        prev_hash = "0" * 64  # 创世prev_hash
        
        for record in records:
            # 验证chain_id
            expected_chain_id = records.index(record) + 1
            if record["chain_id"] != expected_chain_id:
                errors.append(f"Chain ID mismatch at record {record['chain_id']}")
            
            # 验证prev_hash
            if record["prev_hash"] != prev_hash:
                errors.append(
                    f"Prev hash mismatch at chain_id {record['chain_id']}: "
                    f"expected {prev_hash}, got {record['prev_hash']}"
                )
            
            # 验证签名
            sign_data_str = f"{record['chain_id']}:{record['prev_hash']}:{record['identity_hash']}"
            if record["event"]:
                sign_data_str += f":{record['event']}"
            
            if not verify_signature(public_key_pem, record["signature"], sign_data_str):
                errors.append(f"Signature verification failed at chain_id {record['chain_id']}")
            
            # 更新prev_hash
            prev_hash = compute_chain_hash(
                record["chain_id"],
                record["signature"],
                record["identity_hash"]
            )
        
        return {
            "is_continuous": len(errors) == 0,
            "total_records": len(records),
            "errors": errors if errors else None
        }
    
    finally:
        conn.close()


@router.get("/chain/{username}")
async def get_chain_history(username: str):
    """
    获取签名链历史
    
    公开接口, 不需要鉴权
    """
    conn = get_db()
    try:
        # 获取agent_id
        agent = conn.execute(
            "SELECT agent_id FROM agents WHERE username = ? AND is_active = 1",
            (username,)
        ).fetchone()
        
        if not agent:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Agent not found or not activated"
            )
        
        # 获取链记录
        records = conn.execute(
            """
            SELECT chain_id, prev_hash, signature, identity_hash, event, signed_at
            FROM signature_chain 
            WHERE agent_id = ?
            ORDER BY chain_id ASC
            """,
            (agent["agent_id"],)
        ).fetchall()
        
        return {
            "username": username,
            "total_records": len(records),
            "chain": [
                {
                    "chain_id": r["chain_id"],
                    "signature": r["signature"],
                    "identity_hash": r["identity_hash"],
                    "event": r["event"],
                    "signed_at": r["signed_at"]
                }
                for r in records
            ]
        }
    
    finally:
        conn.close()
