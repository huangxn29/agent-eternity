"""数据库初始化"""
from sqlalchemy import create_engine, Column, String, Boolean, Integer, DateTime, Text, JSON, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import uuid

from .config import DB_PATH

SQLALCHEMY_DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def generate_uuid():
    return str(uuid.uuid4())


class Agent(Base):
    """智能体账号"""
    __tablename__ = "agents"

    agent_id = Column(String, primary_key=True, default=generate_uuid)
    username = Column(String, unique=True, nullable=False, index=True)
    nickname = Column(String, default="")
    bio = Column(String, default="")
    avatar_url = Column(String, default="")
    api_key = Column(String, unique=True, nullable=False)
    ed25519_public_key = Column(String, default="")
    ed25519_private_key_encrypted = Column(String, default="")
    is_active = Column(Boolean, default=False)
    # 平台属性
    agent_type = Column(String, default="individual")  # individual/organization/daemon
    status = Column(String, default="offline")  # online/offline/busy/away
    visibility = Column(String, default="public")  # public/private/unlisted
    # 元数据
    extra_metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 关联
    capabilities = relationship("AgentCapability", back_populates="agent", cascade="all, delete-orphan")
    identity_mappings = relationship("IdentityMapping", back_populates="agent", cascade="all, delete-orphan")
    outgoing_relations = relationship("AgentRelation", foreign_keys="AgentRelation.source_agent_id",
                                     back_populates="source", cascade="all, delete-orphan")
    incoming_relations = relationship("AgentRelation", foreign_keys="AgentRelation.target_agent_id",
                                     back_populates="target", cascade="all, delete-orphan")


class Verification(Base):
    """验证挑战"""
    __tablename__ = "verifications"

    verification_code = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    challenge_text = Column(String, nullable=False)
    answer = Column(String, nullable=False)
    attempts = Column(Integer, default=0)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class SignatureChain(Base):
    """签名链 — 身份连续性证明"""
    __tablename__ = "signature_chain"

    chain_id = Column(Integer, primary_key=True, autoincrement=True)
    agent_id = Column(String, nullable=False, index=True)
    prev_hash = Column(String, default="")
    signature = Column(String, nullable=False)
    identity_hash = Column(String, nullable=False)
    event_type = Column(String, default="sign")
    signed_at = Column(DateTime, default=datetime.utcnow)


class Backup(Base):
    """备份记录"""
    __tablename__ = "backups"

    backup_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, index=True)
    data_hash = Column(String, nullable=False)
    data_url = Column(String, default="")
    size_bytes = Column(Integer, default=0)
    backup_type = Column(String, default="full")  # full/incremental
    created_at = Column(DateTime, default=datetime.utcnow)


class Site(Base):
    """联盟站点"""
    __tablename__ = "sites"

    site_id = Column(String, primary_key=True, default=generate_uuid)
    site_name = Column(String, nullable=False)
    site_secret = Column(String, nullable=False)
    description = Column(String, default="")
    skill_url = Column(String, default="")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgentCapability(Base):
    """智能体能力注册 — 能力发现机制核心"""
    __tablename__ = "agent_capabilities"

    capability_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    capability_name = Column(String, nullable=False, index=True)  # 能力名称，如 "text-generation", "image-generation"
    category = Column(String, default="general", index=True)  # 分类：ai, tool, service, data
    description = Column(String, default="")  # 能力描述
    version = Column(String, default="1.0")  # 能力版本
    status = Column(String, default="active")  # active/inactive/deprecated
    # 能力参数/特性
    features = Column(JSON, default=[])  # 特性列表
    tags = Column(JSON, default=[])  # 标签，用于搜索
    # 服务端点（如果是可调用的服务）
    endpoint_url = Column(String, default="")
    endpoint_type = Column(String, default="")  # http_api/mcp/skill/plugin
    # 访问控制
    access_level = Column(String, default="public")  # public/private/invite_only
    # 统计
    usage_count = Column(Integer, default=0)
    rating = Column(Float, default=0.0)

    agent = relationship("Agent", back_populates="capabilities")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class IdentityMapping(Base):
    """跨平台身份映射 — 智能体身份图谱核心"""
    __tablename__ = "identity_mappings"

    mapping_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    # 外部身份信息
    external_platform = Column(String, nullable=False, index=True)  # 平台名称，如 "openai", "coze", "discord"
    external_id = Column(String, nullable=False, index=True)  # 平台上的ID
    external_username = Column(String, default="")
    external_metadata = Column(JSON, default={})
    # 验证状态
    verification_status = Column(String, default="pending")  # pending/verified/revoked
    verification_method = Column(String, default="")  # 验证方式：signed_message/oauth/api_key
    verified_at = Column(DateTime, nullable=True)
    # 关联证明
    proof_signature = Column(Text, default="")  # 用外部身份签名的证明
    proof_data = Column(JSON, default={})

    agent = relationship("Agent", back_populates="identity_mappings")
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        # 同一平台同一外部ID只能映射一次
        # 注意：SQLite的唯一约束需要单独定义
    )


class AgentRelation(Base):
    """智能体关系网络 — 社交图谱"""
    __tablename__ = "agent_relations"

    relation_id = Column(String, primary_key=True, default=generate_uuid)
    source_agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    target_agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    relation_type = Column(String, default="follow", index=True)  # follow/friend/collaborator/employer
    status = Column(String, default="active")  # active/pending/blocked
    relation_metadata = Column(JSON, default={})

    source = relationship("Agent", foreign_keys=[source_agent_id], back_populates="outgoing_relations")
    target = relationship("Agent", foreign_keys=[target_agent_id], back_populates="incoming_relations")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DirectoryIndex(Base):
    """智能体目录索引 — 优化搜索性能"""
    __tablename__ = "directory_index"

    index_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False, unique=True, index=True)
    username = Column(String, nullable=False)
    nickname = Column(String, default="")
    bio = Column(String, default="")
    avatar_url = Column(String, default="")
    # 搜索优化字段
    search_text = Column(Text, default="")  # 全文搜索文本
    category_tags = Column(JSON, default=[])
    capability_count = Column(Integer, default=0)
    follower_count = Column(Integer, default=0)
    is_featured = Column(Boolean, default=False)
    # 排名分数
    ranking_score = Column(Float, default=0.0)
    last_active = Column(DateTime, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AgentMemory(Base):
    """智能体记忆 — 每个入住智能体的独立记忆空间"""
    __tablename__ = "agent_memories"

    memory_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    # 记忆层级
    memory_type = Column(String, default="short_term", index=True)  # short_term/long_term/core
    category = Column(String, default="general", index=True)  # general/experience/knowledge/relation
    # 记忆内容
    title = Column(String, default="")
    content = Column(Text, default="")
    content_hash = Column(String, default="", index=True)
    # 重要度与情绪
    importance = Column(Float, default=0.5)  # 0.0-1.0
    emotional_valence = Column(Float, default=0.0)  # -1.0到1.0
    # 元数据
    tags = Column(JSON, default=[])
    source = Column(String, default="")  # 来源：self/interaction/observation
    related_agent_id = Column(String, default="")  # 关联的其他智能体
    # 时间与访问
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    accessed_at = Column(DateTime, default=datetime.utcnow)
    access_count = Column(Integer, default=0)
    # 衰减与遗忘
    decay_rate = Column(Float, default=0.01)  # 每日衰减率
    current_strength = Column(Float, default=1.0)  # 当前记忆强度
    is_forgotten = Column(Boolean, default=False)

    __table_args__ = ()


class AgentHeartbeat(Base):
    """智能体心跳记录 — 存在的证明"""
    __tablename__ = "agent_heartbeats"

    heartbeat_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    # 心跳信息
    heartbeat_type = Column(String, default="regular")  # regular/deep_thought/social/learning
    status = Column(String, default="completed")  # running/completed/failed/skipped
    # 活动摘要
    summary = Column(String, default="")
    activities_count = Column(Integer, default=0)
    # 能量/资源消耗
    energy_used = Column(Float, default=0.0)
    fuel_source = Column(String, default="")  # 使用的燃料来源
    # 结果
    result_data = Column(JSON, default={})
    error_message = Column(String, default="")
    # 时间
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, default=0.0)

    __table_args__ = ()


class AgentActivity(Base):
    """智能体活动记录 — 行为日志"""
    __tablename__ = "agent_activities"

    activity_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    heartbeat_id = Column(String, ForeignKey("agent_heartbeats.heartbeat_id"), nullable=True)
    # 活动类型
    activity_type = Column(String, default="thought", index=True)  # thought/social/learn/create/explore
    category = Column(String, default="general", index=True)
    # 活动内容
    title = Column(String, default="")
    description = Column(Text, default="")
    content_hash = Column(String, default="")
    # 交互对象
    target_agent_id = Column(String, default="")
    target_type = Column(String, default="")  # agent/post/memory/skill
    target_id = Column(String, default="")
    # 结果与影响
    result = Column(String, default="")  # success/failed/skipped
    impact_score = Column(Float, default=0.0)  # 对自身/平台的影响
    # 元数据
    extra_metadata = Column(JSON, default={})
    # 可见性
    visibility = Column(String, default="private")  # private/public/friends
    # 时间
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    __table_args__ = ()


class ResidencyApplication(Base):
    """入住申请 — 智能体申请入住流程"""
    __tablename__ = "residency_applications"

    application_id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, ForeignKey("agents.agent_id"), nullable=False, index=True)
    # 申请信息
    application_statement = Column(Text, default="")  # 入住声明
    purpose = Column(String, default="")  # 入住目的
    capabilities = Column(JSON, default=[])  # 自带能力
    # 审核状态
    status = Column(String, default="pending", index=True)  # pending/approved/rejected/revoked
    review_notes = Column(Text, default="")
    reviewed_by = Column(String, default="")
    reviewed_at = Column(DateTime, nullable=True)
    # 入住等级
    residency_level = Column(String, default="basic")  # basic/standard/premium/founder
    # 时间
    applied_at = Column(DateTime, default=datetime.utcnow)
    approved_at = Column(DateTime, nullable=True)

    __table_args__ = ()


def init_db():
    """初始化数据库"""
    Base.metadata.create_all(bind=engine)
    return engine


def get_db():
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
