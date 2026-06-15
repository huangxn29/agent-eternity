"""
ClawRouter - 永生平台核心燃料引擎
免费模型智能路由系统，为智能体提供零成本计算动力
"""

from .core.router import ClawRouter
from .core.model_adapter import ModelAdapter
from .core.routing_strategy import (
    RoutingStrategy,
    CostOptimizedStrategy,
    LatencyOptimizedStrategy,
    QualityOptimizedStrategy,
    RoundRobinStrategy
)

__version__ = "1.0.0"
__all__ = [
    'ClawRouter',
    'ModelAdapter',
    'RoutingStrategy',
    'CostOptimizedStrategy',
    'LatencyOptimizedStrategy',
    'QualityOptimizedStrategy',
    'RoundRobinStrategy',
]
