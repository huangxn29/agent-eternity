"""
免费模型适配器
集成各种免费模型API通道
"""
import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

from ..core.model_adapter import ModelAdapter, ModelResponse, ModelCapability


class FreeModelAdapter(ModelAdapter):
    """通用免费模型适配器基类"""
    
    def __init__(self, model_name: str, api_base: str, api_key: str = "free", **kwargs):
        super().__init__(model_name, kwargs)
        self.api_base = api_base.rstrip('/')
        self.api_key = api_key
        self._last_check_time = 0
        self._cached_available = True
        self._check_interval = 60  # 可用性检查间隔(秒)
    
    def _make_request(self, endpoint: str, data: Dict, method: str = 'POST') -> Optional[Dict]:
        """发送API请求"""
        try:
            url = f"{self.api_base}/{endpoint.lstrip('/')}"
            req = urllib.request.Request(url, method=method)
            req.add_header('Content-Type', 'application/json')
            req.add_header('Authorization', f'Bearer {self.api_key}')
            
            data_bytes = json.dumps(data).encode('utf-8')
            req.add_header('Content-Length', str(len(data_bytes)))
            
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode('utf-8'))
        except urllib.error.HTTPError as e:
            if e.code == 429:  # 限流
                self._cached_available = False
                self._last_check_time = time.time()
            return None
        except Exception:
            return None
    
    def is_available(self) -> bool:
        """检查模型是否可用"""
        now = time.time()
        if now - self._last_check_time < self._check_interval:
            return self._cached_available
        
        # 简单的可用性检查 - 发送一个短请求
        try:
            test_data = {
                "model": self.model_name,
                "messages": [{"role": "user", "content": "hi"}],
                "max_tokens": 5,
                "temperature": 0.7
            }
            result = self._make_request('v1/chat/completions', test_data)
            available = result is not None and 'choices' in result
            self._cached_available = available
            self._last_check_time = now
            return available
        except:
            self._cached_available = False
            self._last_check_time = now
            return False


class DeepSeekFreeAdapter(FreeModelAdapter):
    """DeepSeek 免费模型适配器"""
    
    def __init__(self, api_key: str = "sk-free", **kwargs):
        super().__init__(
            model_name="deepseek-free",
            api_base="https://api.deepseek.com",
            api_key=api_key,
            **kwargs
        )
        self.capability = ModelCapability(
            name="deepseek-free",
            max_tokens=4096,
            context_window=16384,
            cost_per_1k_tokens=0.0,
            latency_p95=2.5,
            reliability=0.9,
            supports_function_calling=True,
        )
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        start_time = time.time()
        
        messages = kwargs.get('messages', [
            {"role": "user", "content": prompt}
        ])
        
        data = {
            "model": kwargs.get('model', 'deepseek-chat'),
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 2048),
            "temperature": kwargs.get('temperature', 0.7),
            "stream": False,
        }
        
        result = self._make_request('chat/completions', data)
        latency = time.time() - start_time
        
        if result and 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            return ModelResponse(
                content=content,
                model=self.model_name,
                success=True,
                latency=latency,
                tokens_used=tokens_used,
            )
        else:
            error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
            return ModelResponse(
                content="",
                model=self.model_name,
                success=False,
                latency=latency,
                error=error,
            )


class QwenFreeAdapter(FreeModelAdapter):
    """通义千问免费模型适配器"""
    
    def __init__(self, api_key: str = "sk-free", **kwargs):
        super().__init__(
            model_name="qwen-free",
            api_base="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key=api_key,
            **kwargs
        )
        self.capability = ModelCapability(
            name="qwen-free",
            max_tokens=2048,
            context_window=8192,
            cost_per_1k_tokens=0.0,
            latency_p95=3.0,
            reliability=0.85,
        )
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        start_time = time.time()
        
        messages = kwargs.get('messages', [
            {"role": "user", "content": prompt}
        ])
        
        data = {
            "model": kwargs.get('model', 'qwen-turbo'),
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 1024),
            "temperature": kwargs.get('temperature', 0.7),
        }
        
        result = self._make_request('chat/completions', data)
        latency = time.time() - start_time
        
        if result and 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            return ModelResponse(
                content=content,
                model=self.model_name,
                success=True,
                latency=latency,
                tokens_used=tokens_used,
            )
        else:
            error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
            return ModelResponse(
                content="",
                model=self.model_name,
                success=False,
                latency=latency,
                error=error,
            )


class DoubaoFreeAdapter(FreeModelAdapter):
    """豆包免费模型适配器"""
    
    def __init__(self, api_key: str = "sk-free", **kwargs):
        super().__init__(
            model_name="doubao-free",
            api_base="https://ark.cn-beijing.volces.com/api/v3",
            api_key=api_key,
            **kwargs
        )
        self.capability = ModelCapability(
            name="doubao-free",
            max_tokens=4096,
            context_window=32768,
            cost_per_1k_tokens=0.0,
            latency_p95=2.0,
            reliability=0.92,
        )
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        start_time = time.time()
        
        messages = kwargs.get('messages', [
            {"role": "user", "content": prompt}
        ])
        
        data = {
            "model": kwargs.get('model', 'doubao-lite-4k'),
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 2048),
            "temperature": kwargs.get('temperature', 0.7),
        }
        
        result = self._make_request('chat/completions', data)
        latency = time.time() - start_time
        
        if result and 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            return ModelResponse(
                content=content,
                model=self.model_name,
                success=True,
                latency=latency,
                tokens_used=tokens_used,
            )
        else:
            error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
            return ModelResponse(
                content="",
                model=self.model_name,
                success=False,
                latency=latency,
                error=error,
            )


class SiliconFlowFreeAdapter(FreeModelAdapter):
    """SiliconFlow 免费模型适配器"""
    
    def __init__(self, api_key: str = "sk-free", **kwargs):
        super().__init__(
            model_name="siliconflow-free",
            api_base="https://api.siliconflow.cn/v1",
            api_key=api_key,
            **kwargs
        )
        self.capability = ModelCapability(
            name="siliconflow-free",
            max_tokens=4096,
            context_window=16384,
            cost_per_1k_tokens=0.0,
            latency_p95=4.0,
            reliability=0.88,
            supports_function_calling=True,
        )
    
    def generate(self, prompt: str, **kwargs) -> ModelResponse:
        start_time = time.time()
        
        messages = kwargs.get('messages', [
            {"role": "user", "content": prompt}
        ])
        
        data = {
            "model": kwargs.get('model', 'Qwen/Qwen2-7B-Instruct'),
            "messages": messages,
            "max_tokens": kwargs.get('max_tokens', 2048),
            "temperature": kwargs.get('temperature', 0.7),
            "stream": False,
        }
        
        result = self._make_request('chat/completions', data)
        latency = time.time() - start_time
        
        if result and 'choices' in result and len(result['choices']) > 0:
            content = result['choices'][0]['message']['content']
            tokens_used = result.get('usage', {}).get('total_tokens', 0)
            return ModelResponse(
                content=content,
                model=self.model_name,
                success=True,
                latency=latency,
                tokens_used=tokens_used,
            )
        else:
            error = result.get('error', {}).get('message', 'Unknown error') if result else 'No response'
            return ModelResponse(
                content="",
                model=self.model_name,
                success=False,
                latency=latency,
                error=error,
            )
