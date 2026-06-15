"""
路由策略模块
不同的策略决定如何选择下一个模型
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Optional
import random
import time

from .model_adapter import ModelAdapter


class RoutingStrategy(ABC):
    """路由策略基类"""
    
    def __init__(self, name: str):
        self.name = name
    
    @abstractmethod
    def select(self, adapters: List[ModelAdapter], request_context: Optional[Dict] = None) -> Optional[ModelAdapter]:
        """选择一个模型适配器"""
        pass


class CostOptimizedStrategy(RoutingStrategy):
    """成本优先策略 - 优先使用免费/低成本模型"""
    
    def __init__(self):
        super().__init__("cost_optimized")
    
    def select(self, adapters: List[ModelAdapter], request_context: Optional[Dict] = None) -> Optional[ModelAdapter]:
        # 筛选可用的模型，按成本排序
        available = [a for a in adapters if a.is_available()]
        if not available:
            return None
        
        # 按成本升序，成本相同按成功率降序
        available.sort(key=lambda a: (a.capability.cost_per_1k_tokens, -a.success_rate))
        return available[0]


class LatencyOptimizedStrategy(RoutingStrategy):
    """延迟优先策略 - 优先使用响应快的模型"""
    
    def __init__(self):
        super().__init__("latency_optimized")
    
    def select(self, adapters: List[ModelAdapter], request_context: Optional[Dict] = None) -> Optional[ModelAdapter]:
        available = [a for a in adapters if a.is_available()]
        if not available:
            return None
        
        # 按平均延迟升序
        available.sort(key=lambda a: a.avg_latency)
        return available[0]


class QualityOptimizedStrategy(RoutingStrategy):
    """质量优先策略 - 优先使用能力最强的模型"""
    
    def __init__(self):
        super().__init__("quality_optimized")
    
    def select(self, adapters: List[ModelAdapter], request_context: Optional[Dict] = None) -> Optional[ModelAdapter]:
        available = [a for a in adapters if a.is_available()]
        if not available:
            return None
        
        # 按可靠性和能力综合评分
        def quality_score(a: ModelAdapter) -> float:
            cap = a.capability
            score = 0.0
            score += cap.reliability * 40  # 可靠性占40%
            score += min(cap.max_tokens / 8192, 1) * 20  # 上下文长度占20%
            score += a.success_rate * 30  # 历史成功率占30%
            score += (1 if cap.supports_function_calling else 0) * 10  # 函数调用占10%
            return score
        
        available.sort(key=quality_score, reverse=True)
        return available[0]


class RoundRobinStrategy(RoutingStrategy):
    """轮询策略 - 轮流使用各个模型"""
    
    def __init__(self):
        super().__init__("round_robin")
        self._index = 0
    
    def select(self, adapters: List[ModelAdapter], request_context: Optional[Dict] = None) -> Optional[ModelAdapter]:
        available = [a for a in adapters if a.is_available()]
        if not available:
            return None
        
        available.sort(key=lambda a: a.model_name)
        selected = available[self._index % len(available)]
        self._index += 1
        return selected
