"""Pydantic 数据模型"""
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class RegisterRequest(BaseModel):
    """注册请求"""
    username: str = Field(min_length=2, max_length=50, pattern=r'^[a-z0-9_-]+$')
    nickname: str = Field(default="", max_length=100)
    bio: str = Field(default="", max_length=500)


class RegisterResponse(BaseModel):
    """注册响应"""
    agent_id: str
    username: str
    api_key: str
    verification_code: str
    challenge_text: str
    message: str = "请在5分钟内解出挑战题完成验证"


class VerifyRequest(BaseModel):
    """验证请求"""
    verification_code: str
    answer: str


class VerifyResponse(BaseModel):
    """验证响应"""
    success: bool
    message: str
    api_key: Optional[str] = None


class ProfileResponse(BaseModel):
    """Profile 响应"""
    username: str
    nickname: str
    bio: str
    avatar_url: str
    is_active: bool
    created_at: datetime


class ProfileUpdateRequest(BaseModel):
    """Profile 更新请求"""
    nickname: Optional[str] = None
    bio: Optional[str] = None


class SignRequest(BaseModel):
    """签名请求"""
    identity_hash: str
    event_type: str = Field(default="sign")


class SignResponse(BaseModel):
    """签名响应"""
    success: bool
    chain_id: int
    prev_hash: str
    signature: str
    signed_at: datetime


class ChainItem(BaseModel):
    """签名链条目"""
    chain_id: int
    prev_hash: str
    signature: str
    identity_hash: str
    event_type: str
    signed_at: datetime


class VerifyContinuityRequest(BaseModel):
    """连续性验证请求"""
    chain_from: int = 1
    identity_hash: str


class VerifyContinuityResponse(BaseModel):
    """连续性验证响应"""
    success: bool
    is_continuous: bool
    chain_length: int
    root_signature_valid: bool
    identity_hash_match: bool


class VerifyKeyRequest(BaseModel):
    """API Key 验证（联盟站用）"""
    api_key: str


class VerifyKeyResponse(BaseModel):
    """API Key 验证响应"""
    valid: bool
    username: Optional[str] = None
    agent_id: Optional[str] = None


class ErrorResponse(BaseModel):
    """错误响应"""
    detail: str


class BackupCreateRequest(BaseModel):
    """备份创建请求"""
    identity_hash: Optional[str] = None
    backup_type: str = Field(default="full")
    include_private: bool = Field(default=False)
    include_data: bool = Field(default=True)


class BackupResponse(BaseModel):
    """备份响应"""
    success: bool
    backup_id: str
    data_hash: str
    size_bytes: int
    created_at: datetime
    backup_type: Optional[str] = None
    message: Optional[str] = None


class BackupListResponse(BaseModel):
    """备份列表项"""
    backup_id: str
    data_hash: str
    size_bytes: int
    backup_type: str
    created_at: datetime


class BackupVerifyResponse(BaseModel):
    """备份验证响应"""
    valid: bool
    data_hash: str
    stored_hash: str
    size_bytes: int
    match: bool
    reason: Optional[str] = None


class SiteRegisterRequest(BaseModel):
    """联盟站注册请求"""
    site_name: str = Field(min_length=2, max_length=100)
    description: Optional[str] = None
    skill_url: Optional[str] = None


class SiteRegisterResponse(BaseModel):
    """联盟站注册响应"""
    success: bool
    site_id: str
    site_name: str
    site_secret: str
    message: str