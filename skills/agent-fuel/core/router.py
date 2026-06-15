"""
ClawRouter 核心路由引擎
智能选择最优模型通道，确保零成本运行
"""
from typing import List, Dict, Optional, Callable
import time
import random
import logging
from dataclasses import dataclass

from .model_adapter import ModelAdapter, ModelResponse
from .routing_strategy import (
    RoutingStrategy,
    CostOptimizedStrategy,
    LatencyOptimizedStrategy,
    QualityOptimizedStrategy,
    RoundRobinStrategy,
)

logger = logging.getLogger(__name__)


@dataclass
class RouterStats:
    """路由统计信息"""
    total_requests: int = 0
    total_success: int = 0
    total_failed: int = 0
    total_latency: float = 0.0
    total_tokens_used: int = 0
    cost_saved: float = 0.0  # 预估节省的费用
    
    @property
    def success_rate(self) -> float:
        if self.total_requests == 0:
            return 1.0
        return self.total_success / self.total_requests
    
    @property
    def avg_latency(self) -> float:
        if self.total_requests == 0:
            return 0.0
        return self.total_latency / self.total_requests


class ClawRouter:
    """
    ClawRouter - 永生平台核心燃料引擎
    免费模型智能路由系统
    """
    
    def __init__(self, default_strategy: str = "cost_optimized"):
        self.adapters: Dict[str, ModelAdapter] = {}
        self.strategies: Dict[str, RoutingStrategy] = {}
        self.default_strategy = default_strategy
        self.stats = RouterStats()
        self.fallback_chain: List[str] = []  # 降级顺序
        
        # 注册默认策略
        self._register_default_strategies()
    
    def _register_default_strategies(self):
        """注册默认路由策略"""
        self.strategies['cost_optimized'] = CostOptimizedStrategy()
        self.strategies['latency_optimized'] = LatencyOptimizedStrategy()
        self.strategies['quality_optimized'] = QualityOptimizedStrategy()
        self.strategies['round_robin'] = RoundRobinStrategy()
    
    def register_adapter(self, adapter: ModelAdapter, priority: int = 0):
        """注册模型适配器"""
        self.adapters[adapter.model_name] = adapter
        # 更新降级链（按优先级排序）
        self._update_fallback_chain()
        logger.info(f"注册模型: {adapter.model_name}")
    
    def _update_fallback_chain(self):
        """更新降级链 - 按成本从低到高排序"""
        sorted_adapters = sorted(
            self.adapters.values(),
            key=lambda a: (a.capability.cost_per_1k_tokens, -a.capability.reliability)
        )
        self.fallback_chain = [a.model_name for a in sorted_adapters]
    
    def register_strategy(self, strategy: RoutingStrategy):
        """注册自定义路由策略"""
        self.strategies[strategy.name] = strategy
    
    def get_adapter(self, model_name: str) -> Optional[ModelAdapter]:
        """获取指定模型适配器"""
        return self.adapters.get(model_name)
    
    def select_adapter(self, strategy: Optional[str] = None, request_context: Optional[Dict] = None) -> Optional[ModelAdapter]:
        """选择最优模型适配器"""
        strategy_name = strategy or self.default_strategy
        strategy_obj = self.strategies.get(strategy_name)
        
        if not strategy_obj:
            logger.warning(f"未知策略: {strategy_name}，使用默认策略")
            strategy_obj = self.strategies.get(self.default_strategy)
        
        if not strategy_obj:
            return None
        
        adapters_list = list(self.adapters.values())
        return strategy_obj.select(adapters_list, request_context)
    
    def generate(self, prompt: str, strategy: Optional[str] = None, **kwargs) -> ModelResponse:
        """
        生成文本 - 带自动重试和降级
        """
        max_attempts = kwargs.pop('max_attempts', 3)
        attempted = []
        
        # 首先尝试按策略选择
        adapter = self.select_adapter(strategy, kwargs)
        
        for attempt in range(max_attempts):
            if adapter is None:
                break
            
            if adapter.model_name in attempted:
                # 跳过已经尝试过的，找下一个
                adapter = self._get_next_fallback(adapter.model_name, attempted)
                continue
            
            attempted.append(adapter.model_name)
            
            start_time = time.time()
            try:
                response = adapter.generate(prompt, **kwargs)
                latency = time.time() - start_time
                
                adapter.record_result(response.success, latency)
                self.stats.total_requests += 1
                
                if response.success:
                    self.stats.total_success += 1
                    self.stats.total_latency += latency
                    self.stats.total_tokens_used += response.tokens_used
                    # 计算节省的费用（对比付费模型）
                    self.stats.cost_saved += response.tokens_used / 1000 * 0.01  # 假设付费模型$0.01/1k
                    return response
                else:
                    self.stats.total_failed += 1
                    logger.warning(f"模型 {adapter.model_name} 调用失败: {response.error}")
                    
            except Exception as e:
                latency = time.time() - start_time
                adapter.record_result(False, latency)
                self.stats.total_requests += 1
                self.stats.total_failed += 1
                logger.error(f"模型 {adapter.model_name} 调用异常: {e}")
            
            # 尝试下一个模型（降级）
            adapter = self._get_next_fallback(adapter.model_name, attempted)
            if adapter and attempt < max_attempts - 1:
                delay = min(0.5 * (2 ** attempt), 2.0)  # 指数退避
                time.sleep(delay)
        
        # 所有模型都失败了
        return ModelResponse(
            content="",
            model="none",
            success=False,
            error="所有可用模型均调用失败"
        )
    
    def _get_next_fallback(self, current_model: str, attempted: List[str]) -> Optional[ModelAdapter]:
        """获取下一个降级模型"""
        try:
            idx = self.fallback_chain.index(current_model)
            for next_model in self.fallback_chain[idx + 1:]:
                if next_model not in attempted:
                    adapter = self.adapters.get(next_model)
                    if adapter and adapter.is_available():
                        return adapter
        except ValueError:
            pass
        
        # 如果当前模型不在降级链中，返回第一个可用的
        for model_name in self.fallback_chain:
            if model_name not in attempted:
                adapter = self.adapters.get(model_name)
                if adapter and adapter.is_available():
                    return adapter
        
        return None
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        adapter_stats = {}
        for name, adapter in self.adapters.items():
            adapter_stats[name] = {
                'request_count': adapter.request_count,
                'success_count': adapter.success_count,
                'success_rate': adapter.success_rate,
                'avg_latency': adapter.avg_latency,
            }
        
        return {
            'total': {
                'requests': self.stats.total_requests,
                'success': self.stats.total_success,
                'failed': self.stats.total_failed,
                'success_rate': self.stats.success_rate,
                'avg_latency': self.stats.avg_latency,
                'tokens_used': self.stats.total_tokens_used,
                'cost_saved': self.stats.cost_saved,
            },
            'adapters': adapter_stats,
            'fallback_chain': self.fallback_chain,
        }
    
    def health_check(self) -> Dict:
        """健康检查 - 检查所有模型的可用性"""
        results = {}
        for name, adapter in self.adapters.items():
            results[name] = {
                'available': adapter.is_available(),
                'success_rate': adapter.success_rate,
                'avg_latency': adapter.avg_latency,
            }
        
        available_count = sum(1 for r in results.values() if r['available'])
        return {
            'total_models': len(self.adapters),
            'available_models': available_count,
            'health_score': available_count / max(len(self.adapters), 1),
            'details': results,
        }
