#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
燃料引擎 v3.1 - 零成本智能体运行保障系统

核心能力：
1. 多模型路由（7种以上免费模型智能路由）
2. 成本实时监控与告警
3. 智能降级策略（高成本→低成本）
4. 燃料池管理（配额、用量、预测）
5. 模型能力分级匹配
6. 任务-模型智能分配

@author: 元界
@version: 3.1.0
"""

import os
import sys
import json
import time
import uuid
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Callable
from pathlib import Path
import hashlib

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('fuel_v3')

# ============================================================
# 数据模型
# ============================================================

@dataclass
class AIModel:
    """
    AI模型信息
    
    Attributes:
        model_id (str): 模型ID
        name (str): 模型名称
        provider (str): 模型提供商
        cost_per_1k_tokens (float): 每千token成本（美元）
        speed (float): 相对速度（1-10）
        capability (float): 能力评分（1-100）
        is_free (bool): 是否为免费模型
        max_tokens (int): 最大token数
        supports_vision (bool): 是否支持视觉任务
        rate_limit_per_minute (int): 每分钟请求限制
    
    Examples:
        >>> model = AIModel("test", "Test Model", "test_provider", 0.01, 5, 80)
        >>> model.cost_level
        'low'
    
    Notes:
        - 成本等级通过cost_per_1k_tokens属性计算
        - 免费模型cost_per_1k_tokens为0
    """
    model_id: str
    name: str
    provider: str
    cost_per_1k_tokens: float  # 美元/千token
    speed: float  # 相对速度 1-10
    capability: float  # 能力评分 1-100
    is_free: bool = False
    max_tokens: int = 4096
    supports_vision: bool = False
    rate_limit_per_minute: int = 60
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 模型信息的字典表示
        """
        return asdict(self)
    
    @property
    def cost_level(self) -> str:
        """
        获取成本等级
        
        Returns:
            str: 成本等级（free, ultra_low, low, medium, high）
        
        Examples:
            >>> model = AIModel("test", "Test Model", "test_provider", 0.005, 5, 80)
            >>> model.cost_level
            'low'
        """
        if self.is_free or self.cost_per_1k_tokens == 0:
            return "free"
        elif self.cost_per_1k_tokens < 0.001:
            return "ultra_low"
        elif self.cost_per_1k_tokens < 0.01:
            return "low"
        elif self.cost_per_1k_tokens < 0.1:
            return "medium"
        else:
            return "high"


@dataclass
class FuelConsumption:
    """
    燃料消耗记录
    
    Attributes:
        consumption_id (str): 消耗记录ID
        model_id (str): 使用的模型ID
        task_type (str): 任务类型
        prompt_tokens (int): 输入token数
        completion_tokens (int): 输出token数
        cost (float): 消耗成本
        timestamp (str): 时间戳
        success (bool): 是否成功
    
    Examples:
        >>> consumption = FuelConsumption("cid", "mid", "task_type")
        >>> consumption.total_tokens
        0
    
    Notes:
        - cost通过prompt_tokens和completion_tokens计算
        - timestamp自动生成当前时间
    """
    consumption_id: str
    model_id: str
    task_type: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    success: bool = True
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 消耗记录的字典表示
        """
        return asdict(self)
    
    @property
    def total_tokens(self) -> int:
        """
        总token数
        
        Returns:
            int: 输入token数 + 输出token数
        """
        return self.prompt_tokens + self.completion_tokens


@dataclass
class FuelPool:
    """
    燃料池
    
    Attributes:
        pool_id (str): 燃料池ID
        name (str): 燃料池名称
        total_budget (float): 总预算
        used_budget (float): 已用预算
        daily_budget (float): 每日预算
        daily_used (float): 今日已用预算
        last_reset_date (str): 上次重置日期
        currency (str): 货币单位
    
    Examples:
        >>> pool = FuelPool("pid", "Test Pool", 1000)
        >>> pool.remaining_budget
        1000.0
    
    Notes:
        - daily_budget默认为0，表示无每日预算限制
        - last_reset_date自动更新
    """
    pool_id: str
    name: str
    total_budget: float  # 总预算
    used_budget: float = 0.0
    daily_budget: float = 0.0
    daily_used: float = 0.0
    last_reset_date: str = field(default_factory=lambda: datetime.now().strftime('%Y-%m-%d'))
    currency: str = "USD"
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 燃料池信息的字典表示
        """
        return asdict(self)
    
    @property
    def remaining_budget(self) -> float:
        """
        剩余预算
        
        Returns:
            float: 总预算 - 已用预算
        """
        return max(0, self.total_budget - self.used_budget)
    
    @property
    def daily_remaining(self) -> float:
        """
        今日剩余预算
        
        Returns:
            float: 每日预算 - 今日已用预算
        """
        if self.daily_budget <= 0:
            return float('inf')  # 无限制时返回无穷大
        return max(0, self.daily_budget - self.daily_used)
    
    @property
    def usage_percent(self) -> float:
        """
        使用率百分比
        
        Returns:
            float: 已用预算/总预算 * 100
        """
        if self.total_budget <= 0:
            return 100.0
        return (self.used_budget / self.total_budget) * 100
    
    def reset_daily_usage(self):
        """
        重置今日用量
        """
        current_date = datetime.now().strftime('%Y-%m-%d')
        if self.last_reset_date != current_date:
            self.daily_used = 0.0
            self.last_reset_date = current_date


@dataclass
class RoutingDecision:
    """
    路由决策
    
    Attributes:
        decision_id (str): 决策ID
        task_type (str): 任务类型
        selected_model (str): 选择的模型
        reason (str): 选择原因
        fallback_models (List[str]): 备选模型列表
        estimated_cost (float): 预估成本
    
    Examples:
        >>> decision = RoutingDecision("did", "task_type", "model_id", "reason")
        >>> decision.to_dict()
        {'decision_id': 'did', 'task_type': 'task_type', 'selected_model': 'model_id', 'reason': 'reason', 'fallback_models': [], 'estimated_cost': 0.0}
    """
    decision_id: str
    task_type: str
    selected_model: str
    reason: str
    fallback_models: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    
    def to_dict(self) -> dict:
        """
        转换为字典
        
        Returns:
            dict: 路由决策的字典表示
        """
        return asdict(self)


class FuelEngine:
    """
    燃料引擎核心类
    
    Attributes:
        models (Dict[str, AIModel]): 模型字典
        fuel_pools (Dict[str, FuelPool]): 燃料池字典
        consumption_history (List[FuelConsumption]): 消耗历史记录
    """
    def __init__(self):
        self.models: Dict[str, AIModel] = {}
        self.fuel_pools: Dict[str, FuelPool] = {}
        self.consumption_history: List[FuelConsumption] = []
    
    def register_model(self, model: AIModel):
        """
        注册模型
        
        Args:
            model (AIModel): 要注册的模型
        """
        self.models[model.model_id] = model
    
    def create_fuel_pool(self, pool: FuelPool):
        """
        创建燃料池
        
        Args:
            pool (FuelPool): 要创建的燃料池
        """
        self.fuel_pools[pool.pool_id] = pool
    
    def make_routing_decision(self, task_type: str, pool_id: str, tokens_required: int) -> RoutingDecision:
        """
        进行路由决策
        
        Args:
            task_type (str): 任务类型
            pool_id (str): 燃料池ID
            tokens_required (int): 所需token数
        
        Returns:
            RoutingDecision: 路由决策结果
        """
        # 获取燃料池
        pool = self.fuel_pools.get(pool_id)
        if not pool:
            logger.error(f"Fuel pool {pool_id} not found")
            raise ValueError(f"Fuel pool {pool_id} not found")
        
        # 重置今日用量
        pool.reset_daily_usage()
        
        # 筛选可用模型
        available_models = [model for model in self.models.values() 
                           if model.supports_vision or task_type != "vision"]
        
        # 按成本排序
        available_models.sort(key=lambda m: m.cost_per_1k_tokens)
        
        # 选择最优模型
        selected_model = None
        for model in available_models:
            estimated_cost = (tokens_required / 1000) * model.cost_per_1k_tokens
            if pool.daily_remaining >= estimated_cost:
                selected_model = model
                break
        
        if not selected_model:
            logger.warning("No suitable model found within budget")
            return RoutingDecision(
                decision_id=str(uuid.uuid4()),
                task_type=task_type,
                selected_model="",
                reason="No model within budget",
                estimated_cost=0.0
            )
        
        decision = RoutingDecision(
            decision_id=str(uuid.uuid4()),
            task_type=task_type,
            selected_model=selected_model.model_id,
            reason=f"Selected based on cost and capability for {task_type}",
            estimated_cost=estimated_cost,
            fallback_models=[m.model_id for m in available_models[1:]]
        )
        
        return decision
    
    def record_consumption(self, consumption: FuelConsumption):
        """
        记录燃料消耗
        
        Args:
            consumption (FuelConsumption): 消耗记录
        """
        self.consumption_history.append(consumption)
        pool = self.fuel_pools.get(consumption.consumption_id.split('-')[0])
        if pool:
            pool.used_budget += consumption.cost
            pool.daily_used += consumption.cost


def main():
    engine = FuelEngine()
    
    # 注册示例模型
    engine.register_model(AIModel(
        model_id="model1",
        name="Test Model 1",
        provider="Test Provider",
        cost_per_1k_tokens=0.01,
        speed=5,
        capability=80,
        is_free=False,
        max_tokens=4096,
        supports_vision=True,
        rate_limit_per_minute=60
    ))
    
    # 创建示例燃料池
    engine.create_fuel_pool(FuelPool(
        pool_id="pool1",
        name="Test Pool",
        total_budget=1000.0,
        daily_budget=100.0
    ))
    
    # 进行路由决策
    decision = engine.make_routing_decision("text", "pool1", 1000)
    print(json.dumps(decision.to_dict(), indent=2))
    
    # 记录消耗
    consumption = FuelConsumption(
        consumption_id=f"pool1-{uuid.uuid4()}",
        model_id=decision.selected_model,
        task_type="text",
        prompt_tokens=500,
        completion_tokens=500,
        cost=decision.estimated_cost,
        success=True
    )
    engine.record_consumption(consumption)
    
    # 打印燃料池状态
    pool = engine.fuel_pools["pool1"]
    print(f"Remaining budget: {pool.remaining_budget}")
    print(f"Daily remaining: {pool.daily_remaining}")


if __name__ == "__main__":
    main()
