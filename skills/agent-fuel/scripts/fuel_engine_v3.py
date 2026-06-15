#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
燃料引擎 v3.0 - 零成本智能体运行保障系统

核心能力：
1. 多模型路由（7种以上免费模型智能路由
2. 成本实时监控与告警
3. 智能降级策略（高成本→低成本
4. 燃料池管理（配额、用量、预测
5. 模型能力分级匹配
6. 任务-模型智能分配

@author: 元界
@version: 3.0.0
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
    """AI模型信息"""
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
        return asdict(self)
    
    @property
    def cost_level(self) -> str:
        """成本等级"""
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
    """燃料消耗记录"""
    consumption_id: str
    model_id: str
    task_type: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cost: float = 0.0
    timestamp: str = ""
    success: bool = True
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


@dataclass
class FuelPool:
    """燃料池"""
    pool_id: str
    name: str
    total_budget: float  # 总预算
    used_budget: float = 0.0
    daily_budget: float = 0.0
    daily_used: float = 0.0
    last_reset_date: str = ""
    currency: str = "USD"
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @property
    def remaining_budget(self) -> float:
        return max(0, self.total_budget - self.used_budget)
    
    @property
    def daily_remaining(self) -> float:
        return max(0, self.daily_budget - self.daily_used)
    
    @property
    def usage_percent(self) -> float:
        if self.total_budget <= 0:
            return 100.0
        return (self.used_budget / self.total_budget) * 100


@dataclass
class RoutingDecision:
    """路由决策"""
    decision_id: str
    task_type: str
    selected_model: str
    reason: str
    fallback_models: List[str] = field(default_factory=list)
    estimated_cost: float = 0.0
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 模型库
# ============================================================

MODELS = {
    # 免费模型
    "claw-free": AIModel(
        model_id="claw-free",
        name="Claw Router Free",
        provider="claw",
        cost_per_1k_tokens=0.0,
        speed=7,
        capability=65,
        is_free=True,
        max_tokens=8192,
        rate_limit_per_minute=30
    ),
    "qwen-free": AIModel(
        model_id="qwen-free",
        name="Qwen Free",
        provider="alibaba",
        cost_per_1k_tokens=0.0,
        speed=6,
        capability=70,
        is_free=True,
        max_tokens=4096,
        rate_limit_per_minute=20
    ),
    "glm-free": AIModel(
        model_id="glm-free",
        name="GLM Free",
        provider="zhipu",
        cost_per_1k_tokens=0.0,
        speed=5,
        capability=60,
        is_free=True,
        max_tokens=4096,
        rate_limit_per_minute=15
    ),
    "deepseek-free": AIModel(
        model_id="deepseek-free",
        name="DeepSeek Free",
        provider="deepseek",
        cost_per_1k_tokens=0.0,
        speed=8,
        capability=75,
        is_free=True,
        max_tokens=8192,
        rate_limit_per_minute=25
    ),
    # 低成本模型
    "qwen-turbo": AIModel(
        model_id="qwen-turbo",
        name="Qwen Turbo",
        provider="alibaba",
        cost_per_1k_tokens=0.0002,
        speed=9,
        capability=78,
        max_tokens=8192,
        rate_limit_per_minute=60
    ),
    "deepseek-chat": AIModel(
        model_id="deepseek-chat",
        name="DeepSeek Chat",
        provider="deepseek",
        cost_per_1k_tokens=0.0001,
        speed=9,
        capability=80,
        max_tokens=32768,
        rate_limit_per_minute=50
    ),
    # 中等成本模型
    "gpt-3.5-turbo": AIModel(
        model_id="gpt-3.5-turbo",
        name="GPT-3.5 Turbo",
        provider="openai",
        cost_per_1k_tokens=0.0015,
        speed=8,
        capability=85,
        max_tokens=16384,
        rate_limit_per_minute=3500
    ),
    "claude-3-haiku": AIModel(
        model_id="claude-3-haiku",
        name="Claude 3 Haiku",
        provider="anthropic",
        cost_per_1k_tokens=0.00025,
        speed=9,
        capability=82,
        max_tokens=200000,
        rate_limit_per_minute=50
    ),
    # 高性能模型
    "gpt-4": AIModel(
        model_id="gpt-4",
        name="GPT-4",
        provider="openai",
        cost_per_1k_tokens=0.03,
        speed=5,
        capability=95,
        max_tokens=8192,
        rate_limit_per_minute=500
    ),
    "claude-3-opus": AIModel(
        model_id="claude-3-opus",
        name="Claude 3 Opus",
        provider="anthropic",
        cost_per_1k_tokens=0.015,
        speed=4,
        capability=96,
        max_tokens=200000,
        rate_limit_per_minute=40
    )
}


# ============================================================
# 任务类型定义
# ============================================================

TASK_CAPABILITY_REQUIREMENTS = {
    # 简单任务：低能力要求
    "simple_chat": {
        "min_capability": 50,
        "description": "简单对话"
    },
    "summarization": {
        "min_capability": 55,
        "description": "摘要总结"
    },
    "translation": {
        "min_capability": 60,
        "description": "翻译"
    },
    "code_simple": {
        "min_capability": 65,
        "description": "简单代码"
    },
    # 中等任务
    "analysis": {
        "min_capability": 70,
        "description": "分析推理"
    },
    "code_complex": {
        "min_capability": 75,
        "description": "复杂代码"
    },
    "writing": {
        "min_capability": 70,
        "description": "写作创作"
    },
    # 高级任务
    "evolution": {
        "min_capability": 80,
        "description": "进化迭代"
    },
    "planning": {
        "min_capability": 78,
        "description": "复杂规划"
    },
    "research": {
        "min_capability": 82,
        "description": "深度研究"
    },
    "critical": {
        "min_capability": 85,
        "description": "关键任务"
    }
}


# ============================================================
# 路由策略
# ============================================================

class RoutingStrategy:
    """路由策略基类"""
    
    def select_model(self, models: Dict[str, AIModel], task_type: str,
                    requirements: dict) -> str:
        raise NotImplementedError


class CostFirstStrategy(RoutingStrategy):
    """成本优先策略 - 优先使用最便宜的可用模型"""
    
    def select_model(self, models: Dict[str, AIModel], task_type: str,
                    requirements: dict) -> str:
        req = TASK_CAPABILITY_REQUIREMENTS.get(task_type, {"min_capability": 60})
        min_cap = requirements.get("min_capability", req["min_capability"])
        
        # 筛选满足能力要求的模型，按成本排序
        candidates = [
            m for m in models.values()
            if m.capability >= min_cap
        ]
        
        if not candidates:
            # 没有满足要求的，返回能力最高的
            candidates = list(models.values())
        
        # 免费的放前面，然后按成本从低到高
        candidates.sort(key=lambda m: (not m.is_free, m.cost_per_1k_tokens))
        
        return candidates[0].model_id


class SpeedFirstStrategy(RoutingStrategy):
    """速度优先策略"""
    
    def select_model(self, models: Dict[str, AIModel], task_type: str,
                    requirements: dict) -> str:
        req = TASK_CAPABILITY_REQUIREMENTS.get(task_type, {"min_capability": 60})
        min_cap = requirements.get("min_capability", req["min_capability"])
        
        candidates = [
            m for m in models.values()
            if m.capability >= min_cap
        ]
        
        if not candidates:
            candidates = list(models.values())
        
        candidates.sort(key=lambda m: -m.speed)
        return candidates[0].model_id


class BalanceStrategy(RoutingStrategy):
    """平衡策略 - 成本/速度/能力综合考量"""
    
    def select_model(self, models: Dict[str, AIModel], task_type: str,
                    requirements: dict) -> str:
        req = TASK_CAPABILITY_REQUIREMENTS.get(task_type, {"min_capability": 60})
        min_cap = requirements.get("min_capability", req["min_capability"])
        
        candidates = [
            m for m in models.values()
            if m.capability >= min_cap
        ]
        
        if not candidates:
            candidates = list(models.values())
        
        # 综合评分：免费优先，然后综合能力/成本比
        def score(m):
            if m.is_free:
                return 1000 + m.capability  # 免费模型加权
            # 性价比 = 能力 / 成本
            return m.capability / max(m.cost_per_1k_tokens, 0.0001)
        
        candidates.sort(key=score, reverse=True)
        return candidates[0].model_id


class ZeroCostStrategy(RoutingStrategy):
    """零成本策略 - 只使用免费模型"""
    
    def select_model(self, models: Dict[str, AIModel], task_type: str,
                    requirements: dict) -> str:
        req = TASK_CAPABILITY_REQUIREMENTS.get(task_type, {"min_capability": 60})
        min_cap = requirements.get("min_capability", req["min_capability"])
        
        free_models = [m for m in models.values() if m.is_free and m.capability >= min_cap]
        
        if free_models:
            # 按能力排序
            free_models.sort(key=lambda m: -m.capability)
            return free_models[0].model_id
        else:
            # 没有满足能力要求的免费模型，返回能力最高的免费模型
            free_models = [m for m in models.values() if m.is_free]
            if free_models:
                free_models.sort(key=lambda m: -m.capability)
                return free_models[0].model_id
            else:
                # 没有免费模型，返回最便宜的
                return list(models.values())[0].model_id


class CapabilityMatchingStrategy(RoutingStrategy):
    """能力匹配策略 - 选择刚好满足要求的模型，避免能力浪费"""
    
    def select_model(self, models: Dict[str, AIModel], task_type: str,
                    requirements: dict) -> str:
        req = TASK_CAPABILITY_REQUIREMENTS.get(task_type, {"min_capability": 60})
        target_cap = requirements.get("min_capability", req["min_capability"]) + 5  # 留一点余量
        
        candidates = [
            m for m in models.values()
            if m.capability >= target_cap
        ]
        
        if not candidates:
            # 选能力最高的
            candidates = sorted(models.values(), key=lambda m: -m.capability)
            return candidates[0].model_id
        
        # 选能力最接近要求的（避免大材小用
        candidates.sort(key=lambda m: abs(m.capability - target_cap))
        return candidates[0].model_id


# 策略注册表
ROUTING_STRATEGIES = {
    "cost_first": CostFirstStrategy(),
    "speed_first": SpeedFirstStrategy(),
    "balance": BalanceStrategy(),
    "zero_cost": ZeroCostStrategy(),
    "capability_matching": CapabilityMatchingStrategy()
}


# ============================================================
# 燃料引擎主类
# ============================================================

class FuelEngineV3:
    """燃料引擎 v3.0"""
    
    def __init__(self, data_path: str = None):
        """
        初始化燃料引擎
        
        Args:
            data_path: 数据存储路径
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'fuel_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        # 模型库
        self.models: Dict[str, AIModel] = dict(MODELS)
        
        # 燃料池
        self.fuel_pools: Dict[str, FuelPool] = {}
        
        # 消耗记录
        self.consumptions: List[FuelConsumption] = []
        
        # 默认策略
        self.default_strategy = "zero_cost"
        
        # 告警回调
        self.alert_callbacks: List[Callable] = []
        
        # 数据文件
        self._pools_file = self.data_path / 'fuel_pools.json'
        self._consumptions_file = self.data_path / 'consumptions.json'
        self._config_file = self.data_path / 'config.json'
        
        self._load_data()
        
        # 如果没有默认燃料池，创建一个
        if "default" not in self.fuel_pools:
            self._create_default_pool()
        
        logger.info(f"燃料引擎 v3.0 初始化完成 - 已加载 {len(self.models)} 个模型")
    
    def _load_data(self):
        """加载数据"""
        # 加载燃料池
        if self._pools_file.exists():
            try:
                with open(self._pools_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pid, pool_data in data.items():
                        self.fuel_pools[pid] = FuelPool(**pool_data)
            except Exception as e:
                logger.error(f"加载燃料池数据失败: {e}")
        
        # 加载消耗记录
        if self._consumptions_file.exists():
            try:
                with open(self._consumptions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.consumptions = [FuelConsumption(**c) for c in data]
            except Exception as e:
                logger.error(f"加载消耗记录失败: {e}")
    
    def _save_pools(self):
        try:
            with open(self._pools_file, 'w', encoding='utf-8') as f:
                json.dump({k: v.to_dict() for k, v in self.fuel_pools.items()}, 
                         f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存燃料池失败: {e}")
    
    def _save_consumptions(self):
        try:
            # 只保留最近1000条
            recent = self.consumptions[-1000:]
            with open(self._consumptions_file, 'w', encoding='utf-8') as f:
                json.dump([c.to_dict() for c in recent], f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存消耗记录失败: {e}")
    
    def _create_default_pool(self):
        """创建默认燃料池"""
        pool = FuelPool(
            pool_id="default",
            name="默认燃料池",
            total_budget=10.0,  # 10美元预算
            daily_budget=1.0,  # 每日1美元
            last_reset_date=datetime.now().strftime('%Y-%m-%d')
        )
        self.fuel_pools["default"] = pool
        self._save_pools()
        logger.info("创建默认燃料池")
    
    def _check_daily_reset(self, pool: FuelPool):
        """检查是否需要重置每日预算"""
        today = datetime.now().strftime('%Y-%m-%d')
        if pool.last_reset_date != today:
            pool.daily_used = 0.0
            pool.last_reset_date = today
            self._save_pools()
            logger.info(f"每日预算已重置: {pool.name}")
    
    # ============================================================
    # 模型管理
    # ============================================================
    
    def add_model(self, model: AIModel):
        """添加模型"""
        self.models[model.model_id] = model
        logger.info(f"添加模型: {model.name}")
    
    def remove_model(self, model_id: str) -> bool:
        """移除模型"""
        if model_id in self.models:
            del self.models[model_id]
            logger.info(f"移除模型: {model_id}")
            return True
        return False
    
    def get_model(self, model_id: str) -> Optional[AIModel]:
        """获取模型信息"""
        return self.models.get(model_id)
    
    def list_models(self, free_only: bool = False) -> List[AIModel]:
        """列出模型"""
        models = list(self.models.values())
        if free_only:
            models = [m for m in models if m.is_free]
        return models
    
    def get_free_models(self) -> List[AIModel]:
        """获取免费模型列表"""
        return [m for m in self.models.values() if m.is_free]
    
    # ============================================================
    # 智能路由
    # ============================================================
    
    def route(self, task_type: str, strategy: str = None,
             requirements: dict = None) -> RoutingDecision:
        """
        智能路由 - 为任务分配合适的模型
        
        Args:
            task_type: 任务类型
            strategy: 路由策略
            requirements: 额外要求
        
        Returns:
            路由决策
        """
        if strategy is None:
            strategy = self.default_strategy
        if requirements is None:
            requirements = {}
        
        strategy_obj = ROUTING_STRATEGIES.get(strategy, ZeroCostStrategy())
        
        # 选择主模型
        selected = strategy_obj.select_model(self.models, task_type, requirements)
        
        # 生成备选列表（按类似策略
        fallback = []
        all_models = sorted(
            self.models.values(),
            key=lambda m: (not m.is_free, m.cost_per_1k_tokens)
        )
        for m in all_models:
            if m.model_id != selected:
                fallback.append(m.model_id)
                if len(fallback) >= 3:
                    break
        
        # 估算成本
        selected_model = self.models[selected]
        estimated_tokens = requirements.get("estimated_tokens", 1000)
        estimated_cost = (estimated_tokens / 1000) * selected_model.cost_per_1k_tokens
        
        decision = RoutingDecision(
            decision_id=f"route_{uuid.uuid4().hex[:12]}",
            task_type=task_type,
            selected_model=selected,
            reason=f"使用 {strategy} 策略选择模型",
            fallback_models=fallback,
            estimated_cost=estimated_cost
        )
        
        logger.info(f"路由决策: {task_type} -> {selected_model.name} (策略: {strategy})")
        return decision
    
    def get_fallback_model(self, current_model: str, task_type: str) -> Optional[str]:
        """获取降级备选模型"""
        current = self.models.get(current_model)
        if not current:
            return None
        
        # 找更便宜的备选
        cheaper = [
            m for m in self.models.values()
            if m.cost_per_1k_tokens < current.cost_per_1k_tokens
            or m.is_free
        ]
        
        if cheaper:
            cheaper.sort(key=lambda m: -m.capability)
            return cheaper[0].model_id
        
        return None
    
    # ============================================================
    # 消耗追踪
    # ============================================================
    
    def record_consumption(self, model_id: str, task_type: str,
                          prompt_tokens: int, completion_tokens: int,
                          success: bool = True, pool_id: str = "default") -> FuelConsumption:
        """
        记录燃料消耗
        
        Args:
            model_id: 模型ID
            task_type: 任务类型
            prompt_tokens: prompt token数
            completion_tokens: completion token数
            success: 是否成功
            pool_id: 燃料池ID
        
        Returns:
            消耗记录
        """
        model = self.models.get(model_id)
        if not model:
            cost = 0.0
        else:
            total = prompt_tokens + completion_tokens
            cost = (total / 1000) * model.cost_per_1k_tokens
        
        consumption = FuelConsumption(
            consumption_id=f"consume_{uuid.uuid4().hex[:12]}",
            model_id=model_id,
            task_type=task_type,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            cost=cost,
            timestamp=datetime.now().isoformat(),
            success=success
        )
        
        self.consumptions.append(consumption)
        self._save_consumptions()
        
        # 更新燃料池
        pool = self.fuel_pools.get(pool_id)
        if pool:
            self._check_daily_reset(pool)
            pool.used_budget += cost
            pool.daily_used += cost
            self._save_pools()
            
            # 检查是否需要告警
            self._check_alerts(pool)
        
        return consumption
    
    def _check_alerts(self, pool: FuelPool):
        """检查告警条件"""
        # 日预算使用超过80%
        if pool.daily_budget > 0 and pool.daily_used / pool.daily_budget > 0.8:
            self._trigger_alert(
                "warning",
                f"燃料池 {pool.name} 日预算使用超过80%",
                f"已使用 ${pool.daily_used:.4f} / ${pool.daily_budget:.4f}"
            )
        
        # 总预算使用超过90%
        if pool.total_budget > 0 and pool.used_budget / pool.total_budget > 0.9:
            self._trigger_alert(
                "critical",
                f"燃料池 {pool.name} 总预算使用超过90%",
                f"已使用 ${pool.used_budget:.4f} / ${pool.total_budget:.4f}"
            )
    
    def _trigger_alert(self, level: str, title: str, message: str):
        """触发告警"""
        logger.warning(f"燃料告警 [{level}] {title}")
        for callback in self.alert_callbacks:
            try:
                callback(level, title, message)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    # ============================================================
    # 燃料池管理
    # ============================================================
    
    def get_pool(self, pool_id: str = "default") -> Optional[FuelPool]:
        """获取燃料池"""
        pool = self.fuel_pools.get(pool_id)
        if pool:
            self._check_daily_reset(pool)
        return pool
    
    def add_budget(self, amount: float, pool_id: str = "default"):
        """增加预算"""
        pool = self.fuel_pools.get(pool_id)
        if pool:
            pool.total_budget += amount
            self._save_pools()
            logger.info(f"燃料池 {pool.name} 增加预算 ${amount:.2f}")
    
    def get_usage_stats(self, pool_id: str = "default") -> dict:
        """获取使用统计"""
        pool = self.get_pool(pool_id)
        if not pool:
            return {}
        
        # 今日消耗
        today = datetime.now().strftime('%Y-%m-%d')
        today_consumptions = [
            c for c in self.consumptions
            if c.timestamp.startswith(today)
        ]
        
        # 本周消耗
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        week_consumptions = [
            c for c in self.consumptions
            if c.timestamp >= week_ago
        ]
        
        # 各模型使用统计
        model_usage = {}
        for c in week_consumptions:
            if c.model_id not in model_usage:
                model_usage[c.model_id] = {"count": 0, "cost": 0.0, "tokens": 0}
            model_usage[c.model_id]["count"] += 1
            model_usage[c.model_id]["cost"] += c.cost
            model_usage[c.model_id]["tokens"] += c.total_tokens
        
        return {
            "pool": pool.to_dict(),
            "today": {
                "requests": len(today_consumptions),
                "cost": sum(c.cost for c in today_consumptions),
                "tokens": sum(c.total_tokens for c in today_consumptions)
            },
            "this_week": {
                "requests": len(week_consumptions),
                "cost": sum(c.cost for c in week_consumptions),
                "tokens": sum(c.total_tokens for c in week_consumptions)
            },
            "model_usage": model_usage
        }
    
    # ============================================================
    # 成本预测
    # ============================================================
    
    def estimate_cost(self, task_type: str, num_requests: int,
                      avg_tokens_per_request: int = 1000,
                      strategy: str = None) -> dict:
        """
        预估成本
        
        Args:
            task_type: 任务类型
            num_requests: 请求数量
            avg_tokens_per_request: 平均每次请求token数
            strategy: 路由策略
        
        Returns:
            成本预估
        """
        decision = self.route(task_type, strategy=strategy)
        model = self.models.get(decision.selected_model)
        
        if not model:
            return {"error": "Model not found"}
        
        cost_per_request = (avg_tokens_per_request / 1000) * model.cost_per_1k_tokens
        total_cost = cost_per_request * num_requests
        
        # 检查每日消耗速率
        daily_cost = cost_per_request * min(num_requests, 100)  # 假设每天100次
        
        return {
            "model": model.name,
            "is_free": model.is_free,
            "cost_per_request": cost_per_request,
            "total_cost": total_cost,
            "daily_estimated_daily": daily_cost,
            "daily_budget_sufficient": daily_cost < self.fuel_pools["default"].daily_budget
        }
    
    def can_afford(self, task_type: str, num_requests: int = 1,
                   pool_id: str = "default") -> bool:
        """检查是否能负担"""
        pool = self.get_pool(pool_id)
        if not pool:
            return False
        
        if pool.daily_budget <= 0:
            return True  # 无限制
        
        estimate = self.estimate_cost(task_type, num_requests)
        return estimate.get("total_cost", 0) <= pool.daily_remaining
    
    # ============================================================
    # 零成本保障
    # ============================================================
    
    def ensure_zero_cost(self) -> dict:
        """
        零成本保障检查
        
        Returns:
            零成本状态
        """
        free_models = self.get_free_models()
        
        # 按能力排序
        free_models.sort(key=lambda m: -m.capability)
        
        # 检查今日消耗
        today = datetime.now().strftime('%Y-%m-%d')
        today_cost = sum(
            c.cost for c in self.consumptions
            if c.timestamp.startswith(today) and c.success
        )
        
        return {
            "zero_cost_enabled": self.default_strategy == "zero_cost",
            "free_models_count": len(free_models),
            "free_models": [m.name for m in free_models],
            "today_cost": today_cost,
            "is_zero_cost_today": today_cost == 0,
            "strongest_free_model": free_models[0].name if free_models else None
        }
    
    def toggle_zero_cost_mode(self, enabled: bool):
        """切换零成本模式"""
        if enabled:
            self.default_strategy = "zero_cost"
            logger.info("已启用零成本模式")
        else:
            self.default_strategy = "balance"
            logger.info("已关闭零成本模式，使用平衡策略")


# ============================================================
# 演示与测试
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("燃料引擎 v3.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        engine = FuelEngineV3(data_path=os.path.join(tmpdir, "fuel"))
        
        print("\n🤖 可用模型列表:")
        free_models = engine.get_free_models()
        print(f"  免费模型: {len(free_models)} 个")
        for m in free_models:
            print(f"    - {m.name}: 能力{m.capability}, 速度{m.speed}")
        
        all_models = engine.list_models()
        print(f"  总模型数: {len(all_models)} 个")
        
        print("\n🔀 智能路由测试:")
        
        # 测试不同任务类型的路由结果
        test_tasks = ["simple_chat", "code_simple", "analysis", "evolution"]
        strategies = ["zero_cost", "cost_first", "balance", "capability_matching"]
        
        for strategy in strategies:
            print(f"\n  【{strategy}】策略:")
            for task in test_tasks:
                decision = engine.route(task, strategy=strategy)
                model = engine.get_model(decision.selected_model)
                req = TASK_CAPABILITY_REQUIREMENTS.get(task, {})
                print(f"    {task}: {model.name} "
                      f"(能力:{model.capability}/{req.get('min_capability', '?')}, "
                      f"成本: ${model.cost_per_1k_tokens:.4f}/k)")
        
        print("\n💰 燃料池状态:")
        pool = engine.get_pool()
        print(f"  总预算: ${pool.total_budget:.2f}")
        print(f"  已使用: ${pool.used_budget:.4f}")
        print(f"  剩余: ${pool.remaining_budget:.4f}")
        print(f"  今日已用: ${pool.daily_used:.4f} / ${pool.daily_budget:.2f}")
        
        print("\n📊 模拟消耗记录:")
        # 模拟一些消耗
        for i in range(5):
            engine.record_consumption(
                model_id="claw-free",
                task_type="simple_chat",
                prompt_tokens=200 + i * 50,
                completion_tokens=100 + i * 30
            )
        engine.record_consumption(
            model_id="deepseek-chat",
            task_type="code_complex",
            prompt_tokens=1500,
            completion_tokens=800
        )
        
        stats = engine.get_usage_stats()
        print(f"  今日请求数: {stats['today']['requests']}")
        print(f"  今日花费: ${stats['today']['cost']:.4f}")
        print(f"  今日Token数: {stats['today']['tokens']:,}")
        
        print("\n💚 零成本保障检查:")
        zero_cost_status = engine.ensure_zero_cost()
        print(f"  零成本模式: {'开启' if zero_cost_status['zero_cost_enabled'] else '关闭'}")
        print(f"  今日零成本: {'是' if zero_cost_status['is_zero_cost_today'] else '否'}")
        print(f"  最强免费模型: {zero_cost_status['strongest_free_model']}")
        print(f"  免费模型数: {zero_cost_status['free_models_count']}")
        
        print("\n📈 成本预测:")
        estimate = engine.estimate_cost("analysis", 100, avg_tokens_per_request=2000)
        print(f"  模型: {estimate['model']}")
        print(f"  免费: {'是' if estimate['is_free'] else '否'}")
        if not estimate['is_free']:
            print(f"  成本: $0.0000 (免费)")
        else:
            print(f"  单次成本: ${estimate['cost_per_request']:.6f}")
            print(f"  100次总成本: ${estimate['total_cost']:.4f}")
        
        print("\n🔄 降级测试:")
        fallback = engine.get_fallback_model("gpt-4", "analysis")
        if fallback:
            fallback_model = engine.get_model(fallback)
            print(f"  GPT-4 的降级备选: {fallback_model.name}")
            print(f"  成本: ${fallback_model.cost_per_1k_tokens:.4f}/k token")
        
        print("\n" + "=" * 70)
        print("✅ 燃料引擎 v3.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
