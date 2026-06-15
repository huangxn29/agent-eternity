"""
ClawRouter 核心路由测试
"""
import unittest
import sys
import os

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.router import ClawRouter
from core.model_adapter import ModelAdapter, ModelResponse, ModelCapability


class MockAdapter(ModelAdapter):
    """模拟模型适配器"""
    
    def __init__(self, name: str, success: bool = True, latency: float = 0.1, cost: float = 0.0):
        super().__init__(name)
        self._success = success
        self._latency = latency
        self.capability.cost_per_1k_tokens = cost
        self.call_count = 0
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        self.call_count += 1
        return ModelResponse(
            content=f"Response from {self.model_name}: {prompt[:20]}",
            model=self.model_name,
            success=self._success,
            latency=self._latency,
            tokens_used=len(prompt) // 4 + 50,
        )
    
    def is_available(self) -> bool:
        return True


class TestClawRouter(unittest.TestCase):
    
    def setUp(self):
        self.router = ClawRouter(default_strategy="cost_optimized")
        
    def test_register_adapter(self):
        """测试注册适配器"""
        adapter = MockAdapter("test-model")
        self.router.register_adapter(adapter)
        self.assertIn("test-model", self.router.adapters)
    
    def test_cost_optimized_routing(self):
        """测试成本优先路由"""
        free = MockAdapter("free-model", cost=0.0)
        cheap = MockAdapter("cheap-model", cost=0.001)
        expensive = MockAdapter("expensive-model", cost=0.01)
        
        self.router.register_adapter(expensive)
        self.router.register_adapter(free)
        self.router.register_adapter(cheap)
        
        selected = self.router.select_adapter("cost_optimized")
        self.assertEqual(selected.model_name, "free-model")
    
    def test_round_robin_routing(self):
        """测试轮询路由"""
        m1 = MockAdapter("model1")
        m2 = MockAdapter("model2")
        m3 = MockAdapter("model3")
        
        self.router.register_adapter(m1)
        self.router.register_adapter(m2)
        self.router.register_adapter(m3)
        
        # 前三次应该各不同
        results = set()
        for i in range(3):
            selected = self.router.select_adapter("round_robin")
            results.add(selected.model_name)
        
        self.assertEqual(len(results), 3)
    
    def test_generate_success(self):
        """测试成功生成"""
        adapter = MockAdapter("test-model", success=True)
        self.router.register_adapter(adapter)
        
        response = self.router.generate("Hello, world!")
        self.assertTrue(response.success)
        self.assertIn("Response from test-model", response.content)
        self.assertGreater(response.tokens_used, 0)
    
    def test_generate_with_fallback(self):
        """测试失败时自动降级"""
        failing = MockAdapter("failing-model", success=False)
        working = MockAdapter("working-model", success=True)
        
        self.router.register_adapter(failing)
        self.router.register_adapter(working)
        
        response = self.router.generate("Test prompt", max_attempts=3)
        self.assertTrue(response.success)
        self.assertEqual(response.model, "working-model")
    
    def test_all_fail(self):
        """测试所有模型都失败的情况"""
        failing1 = MockAdapter("fail1", success=False)
        failing2 = MockAdapter("fail2", success=False)
        
        self.router.register_adapter(failing1)
        self.router.register_adapter(failing2)
        
        response = self.router.generate("Test prompt", max_attempts=2)
        self.assertFalse(response.success)
        self.assertEqual(response.model, "none")
    
    def test_stats_tracking(self):
        """测试统计跟踪"""
        adapter = MockAdapter("test-model", success=True)
        self.router.register_adapter(adapter)
        
        for i in range(5):
            self.router.generate(f"Test {i}")
        
        stats = self.router.get_stats()
        self.assertEqual(stats['total']['requests'], 5)
        self.assertEqual(stats['total']['success'], 5)
        self.assertGreater(stats['total']['tokens_used'], 0)
    
    def test_health_check(self):
        """测试健康检查"""
        m1 = MockAdapter("model1")
        m2 = MockAdapter("model2")
        
        self.router.register_adapter(m1)
        self.router.register_adapter(m2)
        
        health = self.router.health_check()
        self.assertEqual(health['total_models'], 2)
        self.assertEqual(health['available_models'], 2)
        self.assertEqual(health['health_score'], 1.0)


if __name__ == '__main__':
    unittest.main()
