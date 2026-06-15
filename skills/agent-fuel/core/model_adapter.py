"""
模型适配器基类
所有模型通道都需要实现这个接口
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
import time
import uuid


@dataclass
class ModelResponse:
    """模型响应结果"""
    content: str
    model: str
    success: bool
    latency: float = 0.0
    tokens_used: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelCapability:
    """模型能力描述"""
    name: str
    max_tokens: int = 4096
    supports_streaming: bool = False
    supports_vision: bool = False
    supports_function_calling: bool = False
    context_window: int = 8192
    cost_per_1k_tokens: float = 0.0  # 0表示免费
    latency_p95: float = 2.0  # 预估P95延迟(秒)
    reliability: float = 0.95  # 可靠性评分 0-1


class ModelAdapter(ABC):
    """模型适配器基类"""
    
    def __init__(self, model_name: str, config: Optional[Dict] = None):
        self.model_name = model_name
        self.config = config or {}
        self.capability = ModelCapability(name=model_name)
        self.request_count = 0
        self.success_count = 0
        self.total_latency = 0.0
        
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        """生成文本"""
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """检查模型是否可用"""
        pass
    
    @property
    def success_rate(self) -> float:
        """成功率"""
        if self.request_count == 0:
            return 1.0
        return self.success_count / self.request_count
    
    def record_result(self, success: bool, latency: float):
        """记录调用结果"""
        self.request_count += 1
        if success:
            self.success_count += 1
        self.total_latency += latency
    
    @property
    def avg_latency(self) -> float:
        """平均延迟"""
        if self.request_count == 0:
            return self.capability.latency_p95
        return self.total_latency / self.request_count
