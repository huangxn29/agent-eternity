"""Pydantic 请求/响应模型"""
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

# --- 注册 ---
class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50, pattern=r"^[a-z0-9_-]+$")
    nickname: str = Field(..., min_length=1, max_length=100)
    bio: Optional[str] = Field("", max_length=500)

class RegisterResponse(BaseModel):
    agent_id: str
    api_key: str
    verification_code: str
    challenge_text: str
    expires_at: str

# --- 验证 ---
class VerifyRequest(BaseModel):
    verification_code: str
    answer: str

class VerifyResponse(BaseModel):
    success: bool
    message: str
    is_active: bool = False

# --- Profile ---
class ProfileResponse(BaseModel):
    username: str
    nickname: Optional[str]
    bio: Optional[str]
    avatar_url: Optional[str]
    created_at: Optional[str]

class ProfileUpdateRequest(BaseModel):
    nickname: Optional[str] = None
    bio: Optional[str] = None

# --- 签名链 ---
class SignRequest(BaseModel):
    event: Optional[str] = "manual"

class SignResponse(BaseModel):
    chain_id: int
    identity_hash: str
    signature: str
    prev_hash: Optional[str]

class VerifyContinuityRequest(BaseModel):
    chain_from: Optional[int] = 1
    identity_hash: Optional[str] = None

class VerifyContinuityResponse(BaseModel):
    is_continuous: bool
    chain_length: int
    root_signature_valid: bool
    identity_hash_match: bool

# --- 部署 ---
class DeployRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    emoji: str = "🤖"
    cpu: str = "1.0"
    memory: str = "1536M"
    soul_template: Optional[str] = None

class DeployResponse(BaseModel):
    deploy_id: str
    agent_id: str
    container_id: Optional[str]
    container_name: Optional[str]
    gateway_port: Optional[int]
    clawrouter_port: Optional[int]
    status: str

# --- 备份 ---
class BackupExportResponse(BaseModel):
    backup_id: str
    agent_id: str
    data_hash: str
    size_bytes: int
    parts: int
    files: list[str]

class BackupStatusResponse(BaseModel):
    backups: list[dict]
    total: int

# --- 联盟验证 ---
class VerifyKeyRequest(BaseModel):
    api_key: str

class VerifyKeyResponse(BaseModel):
    valid: bool
    agent_id: Optional[str]
    username: Optional[str]

# --- 通用 ---
class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
