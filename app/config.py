"""Agent Eternity - 永生平台SaaS 配置"""
import os
from pathlib import Path

# 基础路径
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

# 服务配置
HOST = os.getenv("ETERNITY_HOST", "0.0.0.0")
PORT = int(os.getenv("ETERNITY_PORT", "8002"))

# 数据库
DATABASE_PATH = DATA_DIR / "eternity.db"
DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

# API Key
API_KEY_PREFIX = "eternity-"
API_KEY_LENGTH = 48

# 挑战验证
CHALLENGE_EXPIRE_MINUTES = 5
CHALLENGE_MAX_ATTEMPTS = 5

# 备份
BACKUP_DIR = DATA_DIR / "backups"
BACKUP_DIR.mkdir(exist_ok=True)
BACKUP_MAX_PART_SIZE = 100 * 1024 * 1024  # 100MB per part
BACKUP_MAX_MEMORY = 200 * 1024 * 1024  # 200MB peak memory

# P1 对接
AGENT_AWAKE_SCRIPTS = Path(os.getenv("AGENT_AWAKE_PATH", "/app/data/skills/agent-awake/scripts"))
AGENT_DATA_DIR = Path(os.getenv("AGENT_DATA_PATH", "/app/data/agents"))

# GitHub 存证
GITHUB_PAT = os.getenv("GITHUB_PAT", "")
GITHUB_REPO = os.getenv("GITHUB_REPO", "")

# 鉴权 Header
AUTH_HEADER = "agent-auth-api-key"
