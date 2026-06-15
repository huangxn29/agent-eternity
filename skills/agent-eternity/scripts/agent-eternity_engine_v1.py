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

# 创建日志目录
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
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
        logger.warning(f"JSON解析失败: {json_str}")
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
        try:
            batch_results = [func(item) for item in batch]
            results.extend(batch_results)
        except Exception as e:
            logger.error(f"批量处理失败: {e}")
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
                    logger.warning(f"操作失败，重试中... ({attempts}/{max_attempts})")
                    if attempts < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"操作失败，重试次数达到上限: {max_attempts}")
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
            dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
        except ValueError:
            logger.warning(f"日期时间解析失败: {dt}")
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
        logger.error(f"文件未找到: {file_path}")
        return None
    except Exception as e:
        logger.error(f"读取文件失败: {file_path}, {e}")
        return None


def write_file(file_path: str, content: str, encoding: str = 'utf-8') -> bool:
    """
    写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
    
    Returns:
        bool: 是否写入成功
    
    Examples:
        >>> write_file('example.txt', 'Hello, World!')
        True
    """
    try:
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, 'w', encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件失败: {file_path}, {e}")
        return False


def edit_file(file_path: str, edit_func: Callable[[str], str], encoding: str = 'utf-8') -> bool:
    """
    编辑文件内容
    
    Args:
        file_path: 文件路径
        edit_func: 编辑函数，接受原内容返回新内容
        encoding: 文件编码
    
    Returns:
        bool: 是否编辑成功
    
    Examples:
        >>> edit_file('example.txt', lambda content: content + 'Appended content')
        True
    """
    try:
        content = read_file(file_path, encoding)
        if content is None:
            return False
        new_content = edit_func(content)
        return write_file(file_path, new_content, encoding)
    except Exception as e:
        logger.error(f"编辑文件失败: {file_path}, {e}")
        return False
