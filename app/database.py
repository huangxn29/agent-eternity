"""SQLite 数据库初始化"""
import sqlite3
from pathlib import Path
from .config import DATABASE_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    nickname TEXT,
    bio TEXT,
    avatar_url TEXT,
    api_key TEXT UNIQUE NOT NULL,
    ed25519_public_key TEXT NOT NULL,
    ed25519_private_key_encrypted TEXT NOT NULL,
    is_active INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS verifications (
    verification_code TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    challenge_text TEXT NOT NULL,
    answer TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS signature_chain (
    chain_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT REFERENCES agents(agent_id),
    prev_hash TEXT,
    signature TEXT NOT NULL,
    identity_hash TEXT NOT NULL,
    event TEXT,
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS deployments (
    deploy_id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    container_id TEXT,
    container_name TEXT,
    gateway_port INTEGER,
    clawrouter_port INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS backups (
    backup_id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    data_hash TEXT NOT NULL,
    data_url TEXT,
    size_bytes INTEGER,
    parts INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS sites (
    site_id TEXT PRIMARY KEY,
    site_name TEXT NOT NULL,
    site_secret TEXT NOT NULL,
    description TEXT,
    skill_url TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

def get_db() -> sqlite3.Connection:
    """获取数据库连接"""
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn

def init_db():
    """初始化数据库表"""
    conn = get_db()
    try:
        conn.executescript(SCHEMA_SQL)
        conn.commit()
        print(f"[DB] 数据库初始化完成: {DATABASE_PATH}")
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
