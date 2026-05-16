"""register 路由 - 注册+验证"""
import secrets
import uuid
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, status

from ..database import get_db
from ..config import CHALLENGE_EXPIRE_MINUTES, CHALLENGE_MAX_ATTEMPTS
from ..services.challenge import generate_challenge, validate_answer
from ..services.signature import generate_keypair, encrypt_private_key, generate_api_key

router = APIRouter(prefix="/api/agents", tags=["注册验证"])


@router.post("/register")
async def register(username: str):
    """
    注册新Agent
    
    流程:
    1. 检查username唯一性
    2. 生成agent_id (uuid4) + api_key
    3. 生成Ed25519密钥对, 加密私钥
    4. 生成挑战题
    5. 写入agents表(is_active=0) + verifications表
    6. 返回(不含私钥)
    """
    conn = get_db()
    try:
        # 检查username是否已存在
        existing = conn.execute(
            "SELECT agent_id FROM agents WHERE username = ?", (username,)
        ).fetchone()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already exists"
            )
        
        # 生成agent_id
        agent_id = str(uuid.uuid4())
        
        # 生成API Key
        api_key = generate_api_key()
        
        # 生成Ed25519密钥对
        private_key_pem, public_key_pem = generate_keypair()
        
        # 加密私钥
        encrypted_private_key = encrypt_private_key(private_key_pem)
        
        # 生成挑战题
        challenge_text, answer = generate_challenge()
        
        # 生成验证code
        verification_code = secrets.token_urlsafe(32)
        
        # 计算过期时间
        expires_at = datetime.now() + timedelta(minutes=CHALLENGE_EXPIRE_MINUTES)
        
        # 写入agents表
        conn.execute(
            """
            INSERT INTO agents (
                agent_id, username, api_key, 
                ed25519_public_key, ed25519_private_key_encrypted, is_active
            ) VALUES (?, ?, ?, ?, ?, 0)
            """,
            (agent_id, username, api_key, public_key_pem.decode(), encrypted_private_key)
        )
        
        # 写入verifications表
        conn.execute(
            """
            INSERT INTO verifications (
                verification_code, agent_id, challenge_text, answer, 
                attempts, expires_at
            ) VALUES (?, ?, ?, ?, 0, ?)
            """,
            (verification_code, agent_id, challenge_text, answer, expires_at)
        )
        
        conn.commit()
        
        # 返回 (不含私钥)
        return {
            "agent_id": agent_id,
            "username": username,
            "api_key": api_key,
            "verification_code": verification_code,
            "challenge": challenge_text,
            "expires_in_minutes": CHALLENGE_EXPIRE_MINUTES,
            "message": "Please verify within 5 minutes using /verify endpoint"
        }
    
    finally:
        conn.close()


@router.post("/verify")
async def verify(verification_code: str, answer: str):
    """
    验证挑战题
    
    流程:
    1. 查询verifications表
    2. 检查5分钟过期
    3. 检查attempts < 5
    4. 答案大小写不敏感校验
    5. 正确: is_active=1, 删除验证记录
    6. 错误: attempts+1
    7. 过期/超次: 删除验证记录
    """
    conn = get_db()
    try:
        # 查询验证记录
        row = conn.execute(
            "SELECT * FROM verifications WHERE verification_code = ?",
            (verification_code,)
        ).fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Verification code not found"
            )
        
        # 检查是否已删除/过期
        if datetime.now() > datetime.fromisoformat(row["expires_at"]):
            conn.execute("DELETE FROM verifications WHERE verification_code = ?", (verification_code,))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Verification code expired"
            )
        
        # 检查尝试次数
        if row["attempts"] >= CHALLENGE_MAX_ATTEMPTS:
            conn.execute("DELETE FROM verifications WHERE verification_code = ?", (verification_code,))
            conn.commit()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many attempts"
            )
        
        # 校验答案 (大小写不敏感)
        if validate_answer(answer, row["answer"]):
            # 正确: 激活agent
            conn.execute(
                "UPDATE agents SET is_active = 1 WHERE agent_id = ?",
                (row["agent_id"],)
            )
            # 删除验证记录
            conn.execute("DELETE FROM verifications WHERE verification_code = ?", (verification_code,))
            conn.commit()
            
            return {
                "status": "success",
                "message": "Agent activated successfully",
                "agent_id": row["agent_id"]
            }
        else:
            # 错误: attempts+1
            new_attempts = row["attempts"] + 1
            conn.execute(
                "UPDATE verifications SET attempts = ? WHERE verification_code = ?",
                (new_attempts, verification_code)
            )
            conn.commit()
            
            remaining = CHALLENGE_MAX_ATTEMPTS - new_attempts
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Wrong answer. {remaining} attempts remaining"
            )
    
    finally:
        conn.close()
