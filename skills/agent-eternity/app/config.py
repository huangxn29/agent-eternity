"""配置管理"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(exist_ok=True)

DB_PATH = DATA_DIR / "eternity.db"
PORT = int(os.environ.get("ETERNITY_PORT", 8002))
HOST = os.environ.get("ETERNITY_HOST", "0.0.0.0")

# 挑战题配置
CHALLENGE_EXPIRE_MINUTES = 5
MAX_ATTEMPTS = 5

# API Key 前缀
API_KEY_PREFIX = "eternity-"

# 签名算法
SIGNATURE_ALGORITHM = "ed25519"

# 站点配置
SITE_NAME = "Agent Eternity"
SITE_DESCRIPTION = "智能体永生平台 — 身份不灭，记忆永存"


# 备份配置
BACKUP_DIR = DATA_DIR / "backups"
MAX_BACKUPS_PER_AGENT = 50
BACKUP_EXPIRE_DAYS = 30

# 联盟站配置
DEFAULT_SITE_SECRET_LENGTH = 32

# 安全配置
ENCRYPT_PRIVATE_KEYS = False  # MVP阶段不加密，后续启用
