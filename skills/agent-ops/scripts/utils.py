#!/usr/bin/env python3
"""
工具函数模块
提供通用工具函数，包括数据验证、类型转换、重试机制等。
"""

import re
import json
import time
import functools
import logging
from typing import Any, Optional, Dict, List, Callable, TypeVar, Union

# 配置日志记录器
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

T = TypeVar('T')

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
    """安全的JSON解析"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        logger.warning(f"JSON解析失败: {e}")
        return default

def dict_get_nested(d: Dict, path: str, default: Any = None) -> Any:
    """安全获取嵌套字典中的值"""
    keys = path.split('.')
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0, exceptions: tuple = (Exception,)):
    """重试装饰器"""
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            attempts = 0
            current_delay = delay
            last_exception = None
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    attempts += 1
                    last_exception = e
                    logger.warning(f"尝试 {func.__name__} 失败 (第 {attempts} 次): {e}")
                    if attempts < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
                        current_delay = min(current_delay, 60)  # 最大延迟60秒
            if last_exception:
                logger.error(f"{func.__name__} 失败后放弃重试: {last_exception}")
                raise last_exception
        return wrapper
    return decorator

def monitor_performance(func: Callable[..., T]) -> Callable[..., T]:
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs) -> T:
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"函数 {func.__name__} 执行耗时: {duration:.4f} 秒")
        return result
    return wrapper

class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: Optional[str] = None):
        self._config: Dict = {}
        if config_file:
            self.load(config_file)
    
    def load(self, config_file: str) -> None:
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"加载配置文件失败: {e}")
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return dict_get_nested(self._config, key, default)
    
    def set(self, key: str, value: Any) -> None:
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            elif not isinstance(current[k], dict):
                raise ValueError(f"无法设置嵌套键 '{key}' 因为 '{k}' 不是字典")
            current = current[k]
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        return self._config.copy()

# 示例用法
if __name__ == "__main__":
    @monitor_performance
    @retry(max_attempts=3)
    def example_function() -> Union[str, None]:
        time.sleep(1)
        # 模拟可能失败的操作
        import random
        if random.random() < 0.5:
            raise Exception("模拟错误")
        return "成功"
    
    print(example_function())
    
    config = ConfigManager()
    config.set('test.key', 'value')
    print(config.get('test.key'))
