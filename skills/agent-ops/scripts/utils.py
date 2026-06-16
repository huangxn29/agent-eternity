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
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            end_time = time.time()
            duration = end_time - start_time
            logger.info(f"函数 {func.__name__} 执行耗时: {duration:.4f} 秒，执行失败: {e}")
            raise
        else:
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

import unittest
from tempfile import NamedTemporaryFile
from unittest.mock import patch, MagicMock

class TestUtils(unittest.TestCase):

    def test_validate_email(self):
        self.assertTrue(validate_email("test@example.com"))
        self.assertFalse(validate_email("invalid_email"))
        self.assertFalse(validate_email(""))

    def test_validate_url(self):
        self.assertTrue(validate_url("http://example.com"))
        self.assertTrue(validate_url("https://example.com"))
        self.assertFalse(validate_url("invalid_url"))
        self.assertFalse(validate_url(""))

    def test_safe_json_loads(self):
        self.assertEqual(safe_json_loads('{"key": "value"}'), {"key": "value"})
        self.assertIsNone(safe_json_loads('invalid_json'))
        self.assertEqual(safe_json_loads('invalid_json', default="default"), "default")

    def test_dict_get_nested(self):
        d = {"a": {"b": {"c": "value"}}}
        self.assertEqual(dict_get_nested(d, "a.b.c"), "value")
        self.assertIsNone(dict_get_nested(d, "a.b.d"))
        self.assertEqual(dict_get_nested(d, "a.b.d", default="default"), "default")

    def test_retry(self):
        @retry(max_attempts=3)
        def mock_func():
            raise Exception("Test exception")

        with self.assertRaises(Exception):
            mock_func()

        @retry(max_attempts=3)
        def mock_func_success():
            return "Success"

        self.assertEqual(mock_func_success(), "Success")

    def test_monitor_performance(self):
        @monitor_performance
        def mock_func():
            time.sleep(0.1)
            return "Success"

        self.assertEqual(mock_func(), "Success")

    def test_config_manager_load(self):
        with NamedTemporaryFile(mode='w', encoding='utf-8') as tmp_file:
            json.dump({"key": "value"}, tmp_file)
            tmp_file.flush()
            config = ConfigManager(tmp_file.name)
            self.assertEqual(config.get("key"), "value")

    def test_config_manager_get_set(self):
        config = ConfigManager()
        config.set("a.b.c", "value")
        self.assertEqual(config.get("a.b.c"), "value")

    def test_config_manager_to_dict(self):
        config = ConfigManager()
        config.set("a.b.c", "value")
        self.assertEqual(config.to_dict(), {"a": {"b": {"c": "value"}}})

    def test_config_manager_load_invalid_json(self):
        with NamedTemporaryFile(mode='w', encoding='utf-8') as tmp_file:
            tmp_file.write("invalid_json")
            tmp_file.flush()
            config = ConfigManager(tmp_file.name)
            self.assertEqual(config.to_dict(), {})

    def test_config_manager_set_nested_key_error(self):
        config = ConfigManager()
        config.set("a.b", "value")
        with self.assertRaises(ValueError):
            config.set("a.b.c", "value")

if __name__ == "__main__":
    unittest.main()
