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
    """验证邮箱格式是否正确"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """验证URL格式是否正确"""
    if not url:
        return False
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析，失败时返回默认值"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError):
        return default


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断字符串到指定长度"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def dict_get_nested(d: Dict, path: str, default: Any = None) -> Any:
    """安全地获取嵌套字典中的值
    
    Args:
        d: 字典
        path: 路径，用点号分隔，如 "a.b.c"
        default: 默认值
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
    """批量处理数据
    
    Args:
        items: 待处理的项目列表
        func: 处理函数
        batch_size: 批次大小
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
    """格式化日期时间
    
    Args:
        dt: 日期时间对象或字符串
        fmt: 目标格式
    """
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt)
        except ValueError:
            return dt  # 如果解析失败，返回原字符串
    return dt.strftime(fmt)


def read_file(file_path: str, encoding: str = 'utf-8') -> Optional[str]:
    """读取文件内容
    
    Args:
        file_path: 文件路径
        encoding: 文件编码
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
    """写入文件内容
    
    Args:
        file_path: 文件路径
        content: 文件内容
        encoding: 文件编码
        mode: 写入模式 ('w' 或 'a')
    """
    try:
        with open(file_path, mode, encoding=encoding) as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"写入文件 {file_path} 失败: {e}")
        return False


class ConfigManager:
    """简单的配置管理器"""
    
    def __init__(self, config_file: str = None):
        self._config = {}
        if config_file:
            self.load(config_file)
    
    def load(self, config_file: str):
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return dict_get_nested(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """返回配置字典"""
        return self._config.copy()


def is_blank(s: Optional[str]) -> bool:
    """检查字符串是否为空或空白"""
    return not s or s.strip() == ''


def mask_sensitive_info(s: str, keep_start: int = 3, keep_end: int = 3, mask_char: str = '*') -> str:
    """遮蔽敏感信息
    
    Args:
        s: 原始字符串
        keep_start: 开头保留字符数
        keep_end: 结尾保留字符数
        mask_char: 遮蔽字符
    """
    if not s:
        return s
    
    length = len(s)
    if length <= keep_start + keep_end:
        return s
    
    mask_length = length - keep_start - keep_end
    mask_str = mask_char * mask_length
    return s[:keep_start] + mask_str + s[-keep_end:]


def chunk_list(lst: List, chunk_size: int) -> List[List]:
    """将列表分块
    
    Args:
        lst: 原始列表
        chunk_size: 分块大小
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def remove_duplicates(lst: List, key: Optional[Callable] = None) -> List:
    """去除列表中的重复项
    
    Args:
        lst: 原始列表
        key: 用于确定唯一性的键函数
    """
    seen = set()
    result = []
    for item in lst:
        value = item if key is None else key(item)
        if value not in seen:
            seen.add(value)
            result.append(item)
    return result


def main():
    # 示例用法
    config = ConfigManager('config.json')
    logger.info(config.get('database.host'))
    
    # 测试字符串工具函数
    test_str = "这是一个测试字符串"
    logger.info(truncate_string(test_str, 10))
    logger.info(mask_sensitive_info("1234567890", 3, 3))
    
    # 测试日期时间格式化
    dt = datetime.now()
    logger.info(format_datetime(dt))
    
    # 测试文件操作
    file_path = "test.txt"
    content = "这是一个测试文件内容"
    if write_file(file_path, content):
        logger.info(read_file(file_path))
    
    # 测试列表操作
    test_list = [1, 2, 2, 3, 4, 4, 5]
    logger.info(remove_duplicates(test_list))
    logger.info(chunk_list(test_list, 2))


if __name__ == "__main__":
    main()
