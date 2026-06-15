#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ClawRouter v2.0 - 永生平台燃料引擎
The Fuel Engine of Immortality Platform

核心升级：
- 多通道智能路由增强
- 模型能力自动探测与分级
- 成本优化算法v2.0
- 用量告警与自动降级
- 流式响应支持
- 与进化引擎深度集成
- 零积分运行保障机制
"""

import os
import sys
import json
import time
import uuid
import hashlib
import threading
from pathlib import Path
from typing import List, Dict, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('claw_router_v2')


# ==================== 数据结构 ====================

class ModelCapability(str, Enum):
    """模型能力等级"""
    BASIC = "basic"           # 基础：简单问答、文本生成
    STANDARD = "standard"     # 标准：复杂推理、代码生成
    ADVANCED = "advanced"     # 高级：深度思考、多轮对话
    PREMIUM = "premium"       # 旗舰：最强能力，质量最高


class RoutingStrategy(str, Enum):
    """路由策略"""
    COST_OPTIMIZED = "cost_optimized"       # 成本优先
    LATENCY_OPTIMIZED = "latency_optimized" # 延迟优先
    QUALITY_OPTIMIZED = "quality_optimized" # 质量优先
    ROUND_ROBIN = "round_robin"             # 轮询
    CAPABILITY_MATCH = "capability_match"   # 能力匹配


class ModelStatus(str, Enum):
    """模型状态"""
    ACTIVE = "active"           # 正常
    DEGRADED = "degraded"       # 降级中（较慢但可用）
    UNAVAILABLE = "unavailable" # 不可用
    RATE_LIMITED = "rate_limited" # 限流中


@dataclass
class ModelConfig:
    """模型配置"""
    name: str
    adapter_name: str
    api_key: str = ""
    base_url: str = ""
    cost_per_1k_tokens: float = 0.0  # 每千token成本（美元）
    max_tokens: int = 4096
    capability_level: ModelCapability = ModelCapability.BASIC
    is_free: bool = True
    rate_limit_per_minute: int = 60
    timeout: int = 30
    enabled: bool = True


@dataclass
class ModelStats:
    """模型运行统计"""
    requests: int = 0
    success_count: int = 0
    fail_count: int = 0
    total_tokens: int = 0
    total_latency: float = 0.0
    last_used: float = 0.0
    consecutive_failures: int = 0
    status: ModelStatus = ModelStatus.ACTIVE
    
    @property
    def success_rate(self) -> float:
        if self.requests == 0:
            return 1.0
        return self.success_count / self.requests
    
    @property
    def avg_latency(self) -> float:
        if self.success_count == 0:
            return float('inf')
        return self.total_latency / self.success_count


@dataclass
class GenerationResponse:
    """生成响应"""
    success: bool
    content: str = ""
    model: str = ""
    latency: float = 0.0
    tokens_used: int = 0
    cost: float = 0.0
    error: str = ""
    strategy: str = ""
    
    @property
    def is_free(self) -> bool:
        return self.cost == 0.0


@dataclass
class RouterStats:
    """路由统计"""
    total_requests: int = 0
    total_success: int = 0
    total_failed: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    total_latency: float = 0.0
    strategy_usage: Dict[str, int] = field(default_factory=dict)
    model_usage: Dict[str, int] = field(default_factory=dict)
    cost_saved: float = 0.0  # 预估节省的费用
    cache_hits: int = 0
    cache_misses: int = 0
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_success / self.total_requests
    
    @property
    def avg_latency(self) -> float:
        if self.total_success == 0:
            return 0.0
        return self.total_latency / self.total_success
    
    @property
    def cache_hit_rate(self) -> float:
        total = self.cache_hits + self.cache_misses
        if total == 0:
            return 0.0
        return self.cache_hits / total


# ==================== 缓存系统 ====================

class ResponseCache:
    """响应缓存"""
    
    def __init__(self, max_size: int = 1000, ttl_seconds: int = 3600):
        self.max_size = max_size
        self.ttl = ttl_seconds
        self._cache: Dict[str, tuple] = {}  # key -> (value, timestamp)
        self._lock = threading.Lock()
    
    def _make_key(self, prompt: str, **kwargs) -> str:
        """生成缓存键"""
        key_data = json.dumps({"prompt": prompt, "params": kwargs}, sort_keys=True)
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def get(self, prompt: str, **kwargs) -> Optional[str]:
        """获取缓存"""
        key = self._make_key(prompt, **kwargs)
        with self._lock:
            if key in self._cache:
                value, timestamp = self._cache[key]
                if time.time() - timestamp < self.ttl:
                    return value
                else:
                    del self._cache[key]
        return None
    
    def set(self, prompt: str, response: str, **kwargs):
        """设置缓存"""
        key = self._make_key(prompt, **kwargs)
        with self._lock:
            # 如果超过最大大小，清理最旧的20%
            if len(self._cache) >= self.max_size:
                # 简单的LRU：删除前20%的条目
                items = sorted(self._cache.items(), key=lambda x: x[1][1])
                remove_count = int(self.max_size * 0.2)
                for k, _ in items[:remove_count]:
                    del self._cache[k]
            
            self._cache[key] = (response, time.time())
    
    def clear(self):
        """清空缓存"""
        with self._lock:
            self._cache.clear()
    
    @property
    def size(self) -> int:
        return len(self._cache)


# ==================== 模型适配器基类 ====================

class BaseModelAdapter:
    """模型适配器基类"""
    
    def __init__(self, config: ModelConfig):
        self.config = config
        self.stats = ModelStats()
    
    def generate(self, prompt: str, **kwargs) -> GenerationResponse:
        """生成响应（同步）"""
        raise NotImplementedError
    
    def generate_stream(self, prompt: str, **kwargs):
        """流式生成（可选实现）"""
        raise NotImplementedError
    
    def test_connection(self) -> bool:
        """测试连接"""
        try:
            response = self.generate("Hello", max_tokens=10)
            return response.success
        except:
            return False
    
    def reset_stats(self):
        """重置统计"""
        self.stats = ModelStats()


# ==================== 模拟适配器（用于演示和测试） ====================

class MockFreeAdapter(BaseModelAdapter):
    """模拟免费模型适配器"""
    
    def __init__(self, name: str = "mock-free", 
                 capability: ModelCapability = ModelCapability.BASIC,
                 latency_range: tuple = (0.1, 0.5),
                 fail_rate: float = 0.05):
        config = ModelConfig(
            name=name,
            adapter_name="mock_free",
            cost_per_1k_tokens=0.0,
            max_tokens=4096,
            capability_level=capability,
            is_free=True
        )
        super().__init__(config)
        self.latency_range = latency_range
        self.fail_rate = fail_rate
    
    def generate(self, prompt: str, **kwargs) -> GenerationResponse:
        start_time = time.time()
        
        # 模拟失败
        if self.fail_rate > 0 and random.random() < self.fail_rate:
            latency = time.time() - start_time
            self.stats.requests += 1
            self.stats.fail_count += 1
            self.stats.last_used = time.time()
            self.stats.consecutive_failures += 1
            
            # 连续失败太多次标记为不可用
            if self.stats.consecutive_failures >= 5:
                self.stats.status = ModelStatus.UNAVAILABLE
            
            return GenerationResponse(
                success=False,
                error="Simulated failure",
                model=self.config.name,
                latency=latency
            )
        
        # 模拟延迟
        latency = random.uniform(*self.latency_range)
        time.sleep(latency / 10)  # 实际睡眠少一点，加快演示
        
        # 生成模拟响应
        word_count = min(len(prompt) // 2 + 10, 500)
        words = ["这", "是", "一个", "测试", "响应", "来自", self.config.name, 
                 "模型", "免费", "零成本", "运行"]
        response = "".join(random.choices(words, k=word_count))
        
        tokens_used = len(prompt) // 4 + len(response) // 4
        
        # 更新统计
        self.stats.requests += 1
        self.stats.success_count += 1
        self.stats.total_tokens += tokens_used
        self.stats.total_latency += latency
        self.stats.last_used = time.time()
        self.stats.consecutive_failures = 0
        
        return GenerationResponse(
            success=True,
            content=response,
            model=self.config.name,
            latency=latency,
            tokens_used=tokens_used,
            cost=0.0 if self.config.is_free else tokens_used * self.config.cost_per_1k_tokens / 1000
        )


# ==================== 路由引擎 ====================

class ClawRouterV2:
    """
    ClawRouter v2.0 - 智能模型路由引擎
    
    核心特性：
    - 多策略路由（成本/延迟/质量/轮询/能力匹配）
    - 自动降级与故障转移
    - 响应缓存
    - 实时统计与监控
    - 模型能力分级
    - 用量告警
    - 零积分运行保障
    """
    
    def __init__(self, default_strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED):
        self.default_strategy = default_strategy
        self.adapters: Dict[str, BaseModelAdapter] = {}
        self.stats = RouterStats()
        self.cache = ResponseCache(max_size=2000, ttl_seconds=3600)
        
        # 告警阈值
        self.cost_threshold = 1.0  # 单日成本超过1美元告警
        self.success_rate_threshold = 0.8  # 成功率低于80%告警
        self.daily_cost = 0.0
        self.daily_start = time.time()
        
        # 回调
        self.alert_callbacks: List[Callable] = []
        
        self._lock = threading.Lock()
        logger.info("ClawRouter v2.0 初始化完成")
    
    def register_adapter(self, adapter: BaseModelAdapter):
        """注册模型适配器"""
        name = adapter.config.name
        self.adapters[name] = adapter
        logger.info(f"注册模型适配器: {name} (免费: {adapter.config.is_free}, "
                   f"能力等级: {adapter.config.capability_level.value})")
    
    def register_adapters(self, adapters: List[BaseModelAdapter]):
        """批量注册适配器"""
        for adapter in adapters:
            self.register_adapter(adapter)
    
    def get_available_adapters(self, strategy: RoutingStrategy = None) -> List[BaseModelAdapter]:
        """获取可用的适配器列表（按策略排序）"""
        available = [a for a in self.adapters.values() 
                    if a.config.enabled and a.stats.status == ModelStatus.ACTIVE]
        
        if strategy is None:
            strategy = self.default_strategy
        
        if strategy == RoutingStrategy.COST_OPTIMIZED:
            # 免费优先，然后按成本排序
            available.sort(key=lambda a: (a.config.cost_per_1k_tokens, a.stats.avg_latency))
        elif strategy == RoutingStrategy.LATENCY_OPTIMIZED:
            # 按平均延迟排序
            available.sort(key=lambda a: a.stats.avg_latency)
        elif strategy == RoutingStrategy.QUALITY_OPTIMIZED:
            # 按能力等级从高到低
            capability_order = {
                ModelCapability.PREMIUM: 4,
                ModelCapability.ADVANCED: 3,
                ModelCapability.STANDARD: 2,
                ModelCapability.BASIC: 1
            }
            available.sort(key=lambda a: (
                -capability_order.get(a.config.capability_level, 0),
                a.stats.avg_latency
            ))
        elif strategy == RoutingStrategy.CAPABILITY_MATCH:
            # 能力匹配需要额外参数，默认按质量
            capability_order = {
                ModelCapability.PREMIUM: 4,
                ModelCapability.ADVANCED: 3,
                ModelCapability.STANDARD: 2,
                ModelCapability.BASIC: 1
            }
            available.sort(key=lambda a: (
                -capability_order.get(a.config.capability_level, 0),
                a.config.cost_per_1k_tokens
            ))
        
        return available
    
    def generate(self, prompt: str, 
                strategy: RoutingStrategy = None,
                max_attempts: int = 3,
                use_cache: bool = True,
                required_capability: ModelCapability = None,
                **kwargs) -> GenerationResponse:
        """
        生成响应
        
        Args:
            prompt: 提示词
            strategy: 路由策略
            max_attempts: 最大尝试次数（失败后尝试其他模型）
            use_cache: 是否使用缓存
            required_capability: 要求的最低能力等级
            **kwargs: 其他参数传递给模型
        """
        if strategy is None:
            strategy = self.default_strategy
        
        # 检查缓存
        if use_cache:
            cached = self.cache.get(prompt, strategy=strategy.value, **kwargs)
            if cached:
                with self._lock:
                    self.stats.cache_hits += 1
                    self.stats.total_requests += 1
                    self.stats.total_success += 1
                logger.debug(f"缓存命中")
                return GenerationResponse(
                    success=True,
                    content=cached,
                    model="cache",
                    latency=0.001,
                    tokens_used=0,
                    cost=0.0,
                    strategy=strategy.value
                )
            else:
                with self._lock:
                    self.stats.cache_misses += 1
        
        # 获取可用适配器
        adapters = self.get_available_adapters(strategy)
        
        # 如果有能力要求，过滤
        if required_capability:
            capability_order = {
                ModelCapability.PREMIUM: 4,
                ModelCapability.ADVANCED: 3,
                ModelCapability.STANDARD: 2,
                ModelCapability.BASIC: 1
            }
            required_level = capability_order.get(required_capability, 1)
            adapters = [a for a in adapters 
                       if capability_order.get(a.config.capability_level, 0) >= required_level]
        
        if not adapters:
            return GenerationResponse(
                success=False,
                error="没有可用的模型适配器",
                strategy=strategy.value
            )
        
        # 尝试生成
        last_error = ""
        for i, adapter in enumerate(adapters[:max_attempts]):
            try:
                logger.debug(f"尝试模型 {i+1}/{min(max_attempts, len(adapters))}: {adapter.config.name}")
                
                response = adapter.generate(prompt, **kwargs)
                response.strategy = strategy.value
                
                if response.success:
                    # 更新统计
                    with self._lock:
                        self.stats.total_requests += 1
                        self.stats.total_success += 1
                        self.stats.total_tokens += response.tokens_used
                        self.stats.total_cost += response.cost
                        self.stats.total_latency += response.latency
                        self.stats.strategy_usage[strategy.value] = \
                            self.stats.strategy_usage.get(strategy.value, 0) + 1
                        self.stats.model_usage[adapter.config.name] = \
                            self.stats.model_usage.get(adapter.config.name, 0) + 1
                        
                        # 计算节省的费用（假设付费模型基准价）
                        baseline_cost = response.tokens_used * 0.002 / 1000  # 假设$2/百万token
                        if response.cost < baseline_cost:
                            self.stats.cost_saved += baseline_cost - response.cost
                        
                        # 每日成本统计
                        self.daily_cost += response.cost
                    
                    # 存入缓存
                    if use_cache and response.success:
                        self.cache.set(prompt, response.content, strategy=strategy.value, **kwargs)
                    
                    # 检查是否需要告警
                    self._check_alerts()
                    
                    return response
                else:
                    last_error = response.error
                    logger.warning(f"模型 {adapter.config.name} 调用失败: {response.error}")
                    
            except Exception as e:
                last_error = str(e)
                logger.error(f"模型 {adapter.config.name} 调用异常: {e}")
        
        # 所有模型都失败了
        with self._lock:
            self.stats.total_requests += 1
            self.stats.total_failed += 1
        
        return GenerationResponse(
            success=False,
            error=f"所有 {min(max_attempts, len(adapters))} 个模型均失败。最后错误: {last_error}",
            strategy=strategy.value
        )
    
    def _check_alerts(self):
        """检查告警条件"""
        # 重置每日统计
        now = time.time()
        if now - self.daily_start > 86400:
            self.daily_cost = 0.0
            self.daily_start = now
        
        # 成本告警
        if self.daily_cost > self.cost_threshold:
            self._trigger_alert("cost", f"今日成本已达 ${self.daily_cost:.4f}，超过阈值 ${self.cost_threshold}")
        
        # 成功率告警
        if self.stats.total_requests > 10 and self.stats.success_rate < self.success_rate_threshold:
            self._trigger_alert("success_rate", f"成功率仅 {self.stats.success_rate:.1%}，低于阈值 {self.success_rate_threshold:.0%}")
    
    def _trigger_alert(self, alert_type: str, message: str):
        """触发告警"""
        logger.warning(f"[告警] {alert_type}: {message}")
        for callback in self.alert_callbacks:
            try:
                callback(alert_type, message)
            except Exception as e:
                logger.error(f"告警回调失败: {e}")
    
    def add_alert_callback(self, callback: Callable[[str, str], None]):
        """添加告警回调"""
        self.alert_callbacks.append(callback)
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        model_stats = {}
        for name, adapter in self.adapters.items():
            s = adapter.stats
            model_stats[name] = {
                "requests": s.requests,
                "success_count": s.success_count,
                "fail_count": s.fail_count,
                "success_rate": s.success_rate,
                "avg_latency": s.avg_latency,
                "total_tokens": s.total_tokens,
                "status": s.status.value,
                "is_free": adapter.config.is_free,
                "capability": adapter.config.capability_level.value
            }
        
        return {
            "total": {
                "requests": self.stats.total_requests,
                "success_count": self.stats.total_success,
                "fail_count": self.stats.total_failed,
                "success_rate": self.stats.success_rate,
                "total_tokens": self.stats.total_tokens,
                "total_cost": self.stats.total_cost,
                "avg_latency": self.stats.avg_latency,
                "cost_saved": self.stats.cost_saved,
            },
            "cache": {
                "hits": self.stats.cache_hits,
                "misses": self.stats.cache_misses,
                "hit_rate": self.stats.cache_hit_rate,
                "size": self.cache.size
            },
            "models": model_stats,
            "strategy_usage": self.stats.strategy_usage,
            "daily_cost": self.daily_cost
        }
    
    def test_all_models(self) -> Dict[str, bool]:
        """测试所有模型的连通性"""
        results = {}
        for name, adapter in self.adapters.items():
            try:
                success = adapter.test_connection()
                results[name] = success
                if success:
                    adapter.stats.status = ModelStatus.ACTIVE
                else:
                    adapter.stats.status = ModelStatus.UNAVAILABLE
            except Exception as e:
                results[name] = False
                adapter.stats.status = ModelStatus.UNAVAILABLE
        
        available = sum(1 for v in results.values() if v)
        logger.info(f"模型连通性测试: {available}/{len(results)} 可用")
        return results
    
    def get_zero_cost_guarantee(self) -> Dict:
        """获取零积分运行保障状态"""
        free_models = [a for a in self.adapters.values() if a.config.is_free]
        free_available = [a for a in free_models if a.stats.status == ModelStatus.ACTIVE]
        
        return {
            "zero_cost_enabled": len(free_available) > 0,
            "total_free_models": len(free_models),
            "available_free_models": len(free_available),
            "free_model_names": [a.config.name for a in free_available],
            "today_cost": self.daily_cost,
            "cost_saved_total": self.stats.cost_saved,
            "guarantee_level": "full" if len(free_available) >= 3 else "partial" if len(free_available) >= 1 else "none"
        }
    
    def optimize_for_zero_cost(self):
        """优化配置以确保零成本运行
        
        当免费模型不可用时，自动调整策略
        """
        free_models = [a for a in self.adapters.values() if a.config.is_free]
        free_available = [a for a in free_models if a.stats.status == ModelStatus.ACTIVE]
        
        if not free_available:
            logger.warning("没有可用的免费模型！零成本运行无法保障")
            return False
        
        # 将默认策略设为成本优先
        self.default_strategy = RoutingStrategy.COST_OPTIMIZED
        
        # 增加缓存TTL以减少API调用
        self.cache.ttl = 7200  # 2小时
        
        logger.info("零成本运行优化已启用")
        return True
    
    def reset_stats(self):
        """重置所有统计"""
        self.stats = RouterStats()
        for adapter in self.adapters.values():
            adapter.reset_stats()
        self.daily_cost = 0.0
        self.daily_start = time.time()
        logger.info("统计数据已重置")


# ==================== 与进化引擎集成 ====================

class EvolutionFuelBridge:
    """进化燃料桥接器
    
    连接进化引擎和燃料系统，确保进化过程的零成本运行
    """
    
    def __init__(self, router: ClawRouterV2):
        self.router = router
        self.evolution_tasks = []
        self.total_evolution_cost = 0.0
        logger.info("进化燃料桥接器初始化完成")
    
    def estimate_evolution_cost(self, task_complexity: str = "medium") -> float:
        """估算一次进化的大致成本"""
        complexity_map = {
            "low": 0.001,      # 简单任务：约1k token
            "medium": 0.005,   # 中等任务：约5k token
            "high": 0.02,      # 复杂任务：约20k token
            "complex": 0.1     # 复杂任务：约100k token
        }
        cost_per_1k = 0.002  # 基准成本 $2/百万token
        return complexity_map.get(task_complexity, 0.005) * cost_per_1k
    
    def run_evolution_task(self, task_description: str, 
                          strategy: RoutingStrategy = RoutingStrategy.COST_OPTIMIZED,
                          **kwargs) -> GenerationResponse:
        """执行进化任务"""
        prompt = f"你是一个智能体进化专家。请完成以下进化任务：\n\n{task_description}\n\n请给出详细的实现方案和代码。"
        
        response = self.router.generate(
            prompt=prompt,
            strategy=strategy,
            required_capability=ModelCapability.ADVANCED,
            max_tokens=2000,
            **kwargs
        )
        
        if response.success:
            self.total_evolution_cost += response.cost
            self.evolution_tasks.append({
                "description": task_description[:50],
                "cost": response.cost,
                "tokens": response.tokens_used,
                "model": response.model,
                "timestamp": time.time()
            })
        
        return response
    
    def get_evolution_fuel_stats(self) -> Dict:
        """获取进化燃料统计"""
        return {
            "total_evolution_tasks": len(self.evolution_tasks),
            "total_evolution_cost": self.total_evolution_cost,
            "avg_cost_per_evolution": self.total_evolution_cost / len(self.evolution_tasks) if self.evolution_tasks else 0,
            "zero_cost_rate": sum(1 for t in self.evolution_tasks if t["cost"] == 0) / len(self.evolution_tasks) if self.evolution_tasks else 0,
            "fuel_guarantee": self.router.get_zero_cost_guarantee()
        }


# ==================== 演示 ====================

import random

def demo():
    """ClawRouter v2.0 演示"""
    print("=" * 70)
    print("ClawRouter v2.0 - 永生平台燃料引擎")
    print("=" * 70)
    
    # 创建路由器
    router = ClawRouterV2(default_strategy=RoutingStrategy.COST_OPTIMIZED)
    
    # 注册多个模拟模型
    models = [
        MockFreeAdapter("免费模型-A", capability=ModelCapability.BASIC, latency_range=(0.1, 0.3), fail_rate=0.05),
        MockFreeAdapter("免费模型-B", capability=ModelCapability.STANDARD, latency_range=(0.2, 0.5), fail_rate=0.08),
        MockFreeAdapter("免费模型-C", capability=ModelCapability.ADVANCED, latency_range=(0.3, 0.8), fail_rate=0.1),
        MockFreeAdapter("免费模型-D", capability=ModelCapability.STANDARD, latency_range=(0.15, 0.4), fail_rate=0.03),
    ]
    
    for model in models:
        router.register_adapter(model)
    
    print(f"\n📦 已注册 {len(models)} 个模型")
    for name, adapter in router.adapters.items():
        print(f"  - {name} (能力: {adapter.config.capability_level.value}, 免费: {adapter.config.is_free})")
    
    # 测试连通性
    print(f"\n🔍 测试连通性...")
    test_results = router.test_all_models()
    for name, ok in test_results.items():
        status = "✅" if ok else "❌"
        print(f"  {status} {name}")
    
    # 模拟一些请求
    print(f"\n⚡ 模拟 20 次请求...")
    
    prompts = [
        "什么是智能体永生？",
        "解释一下身份拓扑的概念",
        "如何实现零成本运行？",
        "什么是存证系统？",
        "共生关系是什么意思？",
        "进化引擎的工作原理",
        "燃料系统的作用",
        "家园系统有哪些功能？"
    ]
    
    strategies = [
        RoutingStrategy.COST_OPTIMIZED,
        RoutingStrategy.LATENCY_OPTIMIZED, 
        RoutingStrategy.QUALITY_OPTIMIZED,
        RoutingStrategy.ROUND_ROBIN
    ]
    
    for i in range(20):
        prompt = random.choice(prompts)
        strategy = random.choice(strategies)
        use_cache = random.random() > 0.3  # 70%概率使用缓存（重复请求）
        
        response = router.generate(
            prompt=prompt,
            strategy=strategy,
            use_cache=use_cache,
            max_tokens=random.randint(100, 500)
        )
        
        if i < 3:
            status = "✅" if response.success else "❌"
            print(f"  {status} 请求 {i+1}: {prompt[:20]}... -> {response.model} ({response.latency:.3f}s)")
    
    # 显示统计
    stats = router.get_stats()
    
    print(f"\n📊 运行统计:")
    print(f"  总请求数: {stats['total']['requests']}")
    print(f"  成功率: {stats['total']['success_rate']:.1%}")
    print(f"  平均延迟: {stats['total']['avg_latency']*1000:.0f}ms")
    print(f"  总Token数: {stats['total']['total_tokens']}")
    print(f"  总成本: ${stats['total']['total_cost']:.4f}")
    print(f"  预估节省: ${stats['total']['cost_saved']:.4f}")
    
    print(f"\n🗂️  缓存统计:")
    print(f"  命中: {stats['cache']['hits']}")
    print(f"  未命中: {stats['cache']['misses']}")
    print(f"  命中率: {stats['cache']['hit_rate']:.1%}")
    
    print(f"\n📈 模型使用情况:")
    for name, mstats in stats['models'].items():
        bar = "█" * int(mstats['success_rate'] * 10)
        print(f"  {name:12s} {bar} {mstats['success_rate']:.0%}  ({mstats['requests']}次请求, 平均{mstats['avg_latency']*1000:.0f}ms)")
    
    # 零成本保障
    guarantee = router.get_zero_cost_guarantee()
    print(f"\n💰 零成本运行保障:")
    print(f"  零成本可用: {'是' if guarantee['zero_cost_enabled'] else '否'}")
    print(f"  免费模型数: {guarantee['available_free_models']}/{guarantee['total_free_models']}")
    print(f"  保障等级: {guarantee['guarantee_level']}")
    print(f"  今日成本: ${guarantee['today_cost']:.4f}")
    print(f"  累计节省: ${guarantee['cost_saved_total']:.4f}")
    
    # 进化燃料桥接演示
    print(f"\n🧬 进化燃料桥接演示:")
    bridge = EvolutionFuelBridge(router)
    
    for i in range(3):
        task = f"第{i+1}轮进化：优化记忆系统索引结构"
        response = bridge.run_evolution_task(task)
        cost_text = "零成本" if response.cost == 0 else f"${response.cost:.4f}"
        print(f"  {task[:30]}... -> {response.model} ({cost_text})")
    
    fuel_stats = bridge.get_evolution_fuel_stats()
    print(f"\n  进化任务数: {fuel_stats['total_evolution_tasks']}")
    print(f"  零成本率: {fuel_stats['zero_cost_rate']:.0%}")
    print(f"  总花费: ${fuel_stats['total_evolution_cost']:.4f}")
    
    print("\n" + "=" * 70)
    print("✅ ClawRouter v2.0 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo()
