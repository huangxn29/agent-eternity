#!/usr/bin/env python3
"""工具函数模块"""
import re
import json
import time
import functools
from typing import Any, Dict, List, Callable

def validate_email(email: str) -> bool:
    if not email: return False
    return bool(re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email))

def safe_json_loads(json_str: str, default: Any = None) -> Any:
    try: return json.loads(json_str)
    except: return default

def dict_get_nested(d: Dict, path: str, default: Any = None) -> Any:
    keys = path.split('.')
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current

def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
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
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        return result
    return wrapper

class ConfigManager:
    def __init__(self, config_file: str = None):
        self._config = {}
        if config_file: self.load(config_file)
    def load(self, config_file: str):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except: self._config = {}
    def get(self, key: str, default: Any = None) -> Any:
        return dict_get_nested(self._config, key, default)
    def set(self, key: str, value: Any):
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current: current[k] = {}
            current = current[k]
        current[keys[-1]] = value
