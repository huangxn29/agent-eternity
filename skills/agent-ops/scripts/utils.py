#!/usr/bin/env python3
"""
工具函数模块
提供通用工具函数，包括数据验证、类型转换、重试机制等。
"""

import re
import json
import time
import functools
from typing import Any, Optional, Dict, List, Callable


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
    except (json.JSONDecodeError, TypeError, ValueError):
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


def retry(max_attempts: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """重试装饰器"""
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
    """性能监控装饰器"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        print(f"Function {func.__name__} executed in {duration:.4f} seconds")
        return result
    return wrapper


class ConfigManager:
    """配置管理器"""
    
    def __init__(self, config_file: str = None):
        self._config = {}
        if config_file:
            self.load(config_file)
    
    def load(self, config_file: str):
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        return dict_get_nested(self._config, key, default)
    
    def set(self, key: str, value: Any):
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        return self._config.copy()


def generate_project_timeline(tasks: List[Dict]) -> List[Dict]:
    """
    生成项目时间线
    
    Args:
    tasks: 包含任务信息的字典列表，每个字典应包含'name', 'start_date', 'end_date'和'dependencies'键
    
    Returns:
    排序后的任务列表，表示项目时间线
    """
    # 首先验证输入数据
    if not all(isinstance(task, dict) for task in tasks):
        raise ValueError("所有任务必须以字典形式表示")
    
    required_keys = {'name', 'start_date', 'end_date', 'dependencies'}
    for task in tasks:
        if not required_keys.issubset(task.keys()):
            raise ValueError(f"任务 {task.get('name', '未知')} 缺少必要字段")
    
    # 实现拓扑排序
    from collections import defaultdict, deque
    
    graph = defaultdict(list)
    in_degree = {task['name']: 0 for task in tasks}
    
    for task in tasks:
        for dependency in task['dependencies']:
            graph[dependency].append(task['name'])
            in_degree[task['name']] += 1
    
    queue = deque([task for task in in_degree if in_degree[task] == 0])
    sorted_tasks = []
    
    while queue:
        task_name = queue.popleft()
        task = next(t for t in tasks if t['name'] == task_name)
        sorted_tasks.append(task)
        
        for neighbor in graph[task_name]:
            in_degree[neighbor] -= 1
            if in_degree[neighbor] == 0:
                queue.append(neighbor)
    
    if len(sorted_tasks) != len(tasks):
        raise ValueError("任务之间存在循环依赖")
    
    return sorted_tasks


# 示例用法
if __name__ == "__main__":
    tasks = [
        {'name': 'A', 'start_date': '2023-01-01', 'end_date': '2023-01-05', 'dependencies': []},
        {'name': 'B', 'start_date': '2023-01-06', 'end_date': '2023-01-10', 'dependencies': ['A']},
        {'name': 'C', 'start_date': '2023-01-11', 'end_date': '2023-01-15', 'dependencies': ['B']},
    ]
    
    timeline = generate_project_timeline(tasks)
    for task in timeline:
        print(task['name'], task['start_date'], task['end_date'])
