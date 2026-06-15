#!/usr/bin/env python3
"""
工具函数模块
提供通用的工具函数，包括数据验证、类型转换、重试机制等。
"""

import re
import json
import time
import functools
from typing import Any, Optional, Dict, List, Callable, Union

import logging
import os
from datetime import datetime
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(), logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log')]
)
logger = logging.getLogger(__name__)


def validate_email(email: str) -> bool:
    """
    验证邮箱格式是否正确
    
    Args:
        email: 待验证的邮箱地址
    
    Returns:
        bool: 邮箱格式是否正确
    
    Examples:
        >>> validate_email("test@example.com")
        True
        >>> validate_email("invalid_email")
        False
    """
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """
    验证URL格式是否正确
    
    Args:
        url: 待验证的URL
    
    Returns:
        bool: URL格式是否正确
    
    Examples:
        >>> validate_url("https://www.example.com")
        True
        >>> validate_url("invalid_url")
        False
    """
    if not url:
        return False
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """
    安全的JSON解析，失败时返回默认值
    
    Args:
        json_str: 待解析的JSON字符串
        default: 解析失败时的默认值
    
    Returns:
        Any: 解析结果或默认值
    
    Examples:
        >>> safe_json_loads('{"key": "value"}')
        {'key': 'value'}
        >>> safe_json_loads('invalid_json', default={})
        {}
    """
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """
    截断字符串到指定长度
    
    Args:
        s: 原始字符串
        max_length: 最大长度
        suffix: 截断时添加的后缀
    
    Returns:
        str: 截断后的字符串
    
    Examples:
        >>> truncate_string("This is a long string", 10)
        'This is...'
    """
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def dict_get_nested(d: Dict, path: str, default: Any = None) -> Any:
    """
    安全地获取嵌套字典中的值
    
    Args:
        d: 字典
        path: 路径，用点号分隔，如 "a.b.c"
        default: 默认值
    
    Returns:
        Any: 获取的值或默认值
    
    Examples:
        >>> dict_get_nested({'a': {'b': {'c': 'value'}}}, 'a.b.c')
        'value'
        >>> dict_get_nested({'a': {}}, 'a.b.c', default='default')
        'default'
    """
    keys = path.split('.')
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def batch_process(items: List, func: Callable, batch_size: int = 10) -> List:
    """
    批量处理数据
    
    Args:
        items: 待处理的项目列表
        func: 处理函数
        batch_size: 批次大小
    
    Returns:
        List: 处理结果列表
    
    Examples:
        >>> batch_process([1, 2, 3, 4], lambda x: x*2, batch_size=2)
        [2, 4, 6, 8]
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = [func(item) for item in batch]
        results.extend(batch_results)
    return results


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    重试装饰器，用于处理可能失败的操作
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍增因子
    
    Examples:
        @retry(max_attempts=5)
        def may_fail():
            # 可能失败的操作
            pass
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_exception = e
                    if attempts < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            raise last_exception
        return wrapper
    return decorator


def monitor_performance(func: Callable) -> Callable:
    """
    性能监控装饰器，记录函数执行时间
    
    Examples:
        @monitor_performance
        def my_function():
            # 被监控的函数
            pass
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        
        logger.info(f"函数 {func.__name__} 执行时间: {duration:.4f}秒")
        
        return result
    return wrapper


def format_datetime(dt: Union[datetime, str], fmt: str = '%Y-%m-%d %H:%M:%S') -> str:
    """
    格式化日期时间
    
    Args:
        dt: 日期时间对象或字符串
        fmt: 目标格式
    
    Returns:
        str: 格式化后的日期时间字符串
    
    Examples:
        >>> format_datetime(datetime.now())
        '2023-04-01 12:00:00'
        >>> format_datetime('2023-04-01T12:00:00')
        '2023-04-01 12:00:00'
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt  # 如果解析失败，返回原字符串
    return dt.strftime(fmt)


def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """
    读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
    
    Returns:
        Optional[str]: 文件内容或None（读取失败时）
    
    Examples:
        >>> read_file('example.txt')
        '文件内容'
    """
    try:
        with open(file_path, 'r', encoding=encoding) as f:
            return f.read()
    except FileNotFoundError:
        logger.warning(f"文件 {file_path} 不存在")
        return None
    except Exception as e:
        logger.error(f"读取文件 {file_path} 失败: {e}")
        return None


def write_file(file_path: str, content: str, encoding: str = 'utf-8', mode: str = 'w') -> bool:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        mode: 写入模式 ('w' 或 'a')
    
    Returns:
        bool: 写入是否成功
    
    Examples:
        >>> write_file('example.txt', 'Hello, World!')
        True
    """
    try:
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {e}")
        return False


class ConfigManager:
    """
    简单的配置管理器
    
    Attributes:
        _config: 配置字典
    
    Examples:
        config = ConfigManager('config.json')
        value = config.get('key')
    """
    
    def __init__(self, config_file: str = None):
        self._config = {}
        if config_file:
            self.load(config_file)
    
    def load(self, config_file: str):
        """
        从文件加载配置
        
        Args:
            config_file: 配置文件路径
        """
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值
        
        Args:
            key: 配置键
            default: 默认值
        
        Returns:
            Any: 配置值或默认值
        """
        return dict_get_nested(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """
        设置配置值
        
        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """
        返回配置字典
        
        Returns:
            Dict: 配置字典的副本
        """
        return self._config.copy()


def is_blank(s: Optional[str]) -> bool:
    """
    检查字符串是否为空或空白
    
    Args:
        s: 待检查的字符串
    
    Returns:
        bool: 是否为空或空白
    
    Examples:
        >>> is_blank('')
        True
        >>> is_blank('   ')
        True
        >>> is_blank('hello')
        False
    """
    return not s or s.strip() == ''


def mask_sensitive_info(s: str, keep_start: int = 3, keep_end: int = 3, mask_char: str = '*') -> str:
    """
    遮蔽敏感信息
    
    Args:
        s: 原始字符串
        keep_start: 开头保留字符数
        keep_end: 结尾保留字符数
        mask_char: 遮蔽字符
    
    Returns:
        str: 遮蔽后的字符串
    
    Examples:
        >>> mask_sensitive_info('1234567890')
        '123*****890'
    """
    if not s:
        return s
    
    if len(s) <= keep_start + keep_end:
        return s
    
    masked_length = len(s) - keep_start - keep_end
    mask = mask_char * masked_length
    
    return s[:keep_start] + mask + s[-keep_end:]
