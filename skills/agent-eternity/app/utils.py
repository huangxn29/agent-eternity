"""工具函数模块
通用工具函数集合
"""
import hashlib
import secrets
import string
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List


def generate_random_string(length: int,
                           include_digits: bool = True,
                           include_punctuation: bool = False) -> str:
    """生成随机字符串

    Args:
        length: 字符串长度
        include_digits: 是否包含数字
        include_punctuation: 是否包含标点符号

    Returns:
        随机字符串
    """
    chars = string.ascii_letters
    if include_digits:
        chars += string.digits
    if include_punctuation:
        chars += string.punctuation

    return ''.join(secrets.choice(chars) for _ in range(length))


def compute_sha256(data: str) -> str:
    """计算 SHA-256 哈希值"""
    return hashlib.sha256(data.encode('utf-8')).hexdigest()


def compute_file_sha256(filepath: str, chunk_size: int = 8192) -> str:
    """流式计算文件的 SHA-256 哈希值

    Args:
        filepath: 文件路径
        chunk_size: 块大小（字节）

    Returns:
        SHA-256 哈希值
    """
    sha256 = hashlib.sha256()
    with open(filepath, 'rb') as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            sha256.update(chunk)
    return sha256.hexdigest()


def format_timestamp(dt: Optional[datetime] = None) -> str:
    """格式化时间戳为 ISO 格式字符串

    Args:
        dt:  datetime 对象，None 则使用当前时间

    Returns:
        ISO 格式时间字符串
    """
    if dt is None:
        dt = datetime.utcnow()
    return dt.isoformat()


def parse_timestamp(ts: str) -> datetime:
    """解析 ISO 格式时间字符串

    Args:
        ts: ISO 格式时间字符串

    Returns:
        datetime 对象
    """
    return datetime.fromisoformat(ts)


def time_ago(dt: datetime) -> str:
    """计算时间差的人类可读格式

    Args:
        dt: 过去的时间

    Returns:
        人类可读的时间差字符串
    """
    now = datetime.utcnow()
    delta = now - dt

    if delta.total_seconds() < 60:
        return f"{int(delta.total_seconds())} 秒前"
    elif delta.total_seconds() < 3600:
        return f"{int(delta.total_seconds() / 60)} 分钟前"
    elif delta.total_seconds() < 86400:
        return f"{int(delta.total_seconds() / 3600)} 小时前"
    elif delta.days < 30:
        return f"{delta.days} 天前"
    elif delta.days < 365:
        return f"{int(delta.days / 30)} 个月前"
    else:
        return f"{int(delta.days / 365)} 年前"


def ensure_dir(path: str) -> Path:
    """确保目录存在，不存在则创建

    Args:
        path: 目录路径

    Returns:
        Path 对象
    """
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def validate_username(username: str) -> bool:
    """验证用户名格式

    规则：2-50字符，仅允许小写字母、数字、下划线、短横线

    Args:
        username: 用户名

    Returns:
        是否有效
    """
    if not username or len(username) < 2 or len(username) > 50:
        return False

    allowed = set('abcdefghijklmnopqrstuvwxyz0123456789_-')
    return all(c in allowed for c in username)


def sanitize_filename(filename: str) -> str:
    """清理文件名，移除不安全字符

    Args:
        filename: 原始文件名

    Returns:
        安全的文件名
    """
    # 移除路径分隔符和特殊字符
    safe_chars = set(string.ascii_letters + string.digits + '._-')
    sanitized = ''.join(c for c in filename if c in safe_chars)

    # 移除连续的点号（防止 .. 路径遍历）
    while '..' in sanitized:
        sanitized = sanitized.replace('..', '.')

    # 不以点号开头（隐藏文件/路径遍历）
    while sanitized.startswith('.'):
        sanitized = sanitized[1:]

    # 不以短横线开头（防止命令行参数混淆）
    while sanitized.startswith('-'):
        sanitized = sanitized[1:]

    # 确保不为空
    if not sanitized:
        sanitized = 'unnamed'

    # 限制长度
    if len(sanitized) > 255:
        # 保留扩展名
        if '.' in sanitized:
            name_part, ext_part = sanitized.rsplit('.', 1)
            ext_part = '.' + ext_part
            max_name_len = 255 - len(ext_part)
            sanitized = name_part[:max_name_len] + ext_part
        else:
            sanitized = sanitized[:255]

    return sanitized


def truncate_text(text: str, max_length: int, suffix: str = "...") -> str:
    """截断文本到指定长度

    Args:
        text: 原始文本
        max_length: 最大长度（包含后缀）
        suffix: 截断后缀

    Returns:
        截断后的文本
    """
    if len(text) <= max_length:
        return text

    truncated = text[:max_length - len(suffix)]
    return truncated + suffix


def chunk_list(lst: list, chunk_size: int) -> List[list]:
    """将列表分块

    Args:
        lst: 原始列表
        chunk_size: 每块大小

    Returns:
        分块后的列表
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def is_valid_api_key(api_key: str, prefix: str = "") -> bool:
    """验证 API Key 格式

    Args:
        api_key: API Key
        prefix: 预期前缀

    Returns:
        是否有效
    """
    if not api_key:
        return False

    if prefix and not api_key.startswith(prefix):
        return False

    # 检查长度和字符
    key_part = api_key[len(prefix):] if prefix else api_key
    if len(key_part) < 16:
        return False

    allowed = set(string.hexdigits.lower() + string.hexdigits.upper())
    return all(c in allowed for c in key_part)
