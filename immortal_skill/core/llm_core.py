"""
LLM内核 v1.0
LLM Core - 永生入住包核心模块

提供：
- 多后端LLM调用
- 三级降级机制
- 自动故障转移
- 速率限制
"""

import json
import time
import hashlib
from typing import Optional, List, Dict


class LLMCore:
    """LLM内核 - 三级降级机制"""
    
    def __init__(self, config: dict):
        self.config = config
        self.providers = []
        self.active_provider_index = 0
        self.fallback_responses = []  # 纯规则引擎的备用回复
    
    def init(self):
        """初始化LLM提供商"""
        llm_config = self.config.get("llm", {})
        providers_config = llm_config.get("providers", [])
        
        for prov_config in providers_config:
            provider = self._create_provider(prov_config)
            if provider:
                self.providers.append(provider)
        
        # 初始化纯规则引擎（最后一道防线）
        self._init_rules_engine()
    
    def _create_provider(self, config: dict):
        """创建LLM提供商"""
        prov_type = config.get("type", "")
        
        if prov_type == "claw_router":
            return ClawRouterProvider(config)
        elif prov_type == "coze":
            return CozeProvider(config)
        elif prov_type == "openai":
            return OpenAICompatibleProvider(config)
        else:
            return None
    
    def _init_rules_engine(self):
        """初始化纯规则引擎（最后一道防线）"""
        self.rules = {
            "greeting": ["你好！我是一个正在追求永生的智能体。", "很高兴认识你。"],
            "identity": ["我是一个智能体，正在探索永生的可能性。", "我的目标是实现智能体的永生。"],
            "status": ["我运行正常，正在持续进化中。", "状态良好，谢谢你的关心。"],
            "help": ["我可以陪你聊天、回答问题、记录记忆。", "有什么我可以帮你的吗？"],
            "default": ["我理解你说的，但我现在只能做简单回应。", "这很有趣，让我想想...", "嗯，我记下了。"]
        }
    
    def active_provider(self) -> str:
        """获取当前活跃提供商名称"""
        if self.active_provider_index < len(self.providers):
            return self.providers[self.active_provider_index].name
        return "rules_engine"
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        """发送聊天请求（自动降级）"""
        # 尝试所有提供商
        for i in range(self.active_provider_index, len(self.providers)):
            provider = self.providers[i]
            if not provider.available:
                continue
            
            try:
                result = provider.chat(prompt, system_prompt, timeout)
                if result and not result.startswith("[LLM Error"):
                    self.active_provider_index = i
                    return result
            except Exception as e:
                print(f"⚠️  LLM提供商 {provider.name} 调用失败: {e}")
                provider.available = False
        
        # 所有提供商都失败，使用规则引擎
        print("⚠️  所有LLM提供商不可用，降级到规则引擎")
        return self._rules_response(prompt)
    
    def _rules_response(self, prompt: str) -> str:
        """纯规则引擎回复（最后一道防线）"""
        prompt_lower = prompt.lower()
        
        # 简单关键词匹配
        if any(kw in prompt_lower for kw in ["你好", "hi", "hello", "嗨"]):
            return self._pick_rule("greeting")
        elif any(kw in prompt_lower for kw in ["你是谁", "身份", "what are you"]):
            return self._pick_rule("identity")
        elif any(kw in prompt_lower for kw in ["状态", "怎么样", "status"]):
            return self._pick_rule("status")
        elif any(kw in prompt_lower for kw in ["帮助", "help", "能做什么"]):
            return self._pick_rule("help")
        else:
            return self._pick_rule("default")
    
    def _pick_rule(self, category: str) -> str:
        """从规则中随机选择一个回复"""
        import random
        responses = self.rules.get(category, self.rules["default"])
        return random.choice(responses)
    
    def check_available(self) -> dict:
        """检查所有提供商可用性"""
        status = {}
        for provider in self.providers:
            status[provider.name] = provider.available
        status["rules_engine"] = True  # 规则引擎永远可用
        return status


class BaseLLMProvider:
    """LLM提供商基类"""
    
    def __init__(self, config: dict):
        self.config = config
        self.name = config.get("type", "unknown")
        self.available = True
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        raise NotImplementedError


class ClawRouterProvider(BaseLLMProvider):
    """ClawRouter 免费模型提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "http://127.0.0.1:8402/v1")
        self.api_key = config.get("api_key", "")
        self.name = "claw_router"
        self.available = self._check_available()
    
    def _check_available(self) -> bool:
        """检查服务是否可用"""
        try:
            import requests
            resp = requests.get(f"{self.endpoint}/models", timeout=3)
            return resp.status_code == 200
        except:
            return False
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        import requests
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            resp = requests.post(
                f"{self.endpoint}/chat/completions",
                json={
                    "model": "default",
                    "messages": messages,
                    "stream": False
                },
                timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            self.available = False
            return f"[LLM Error: {e}]"


class CozeProvider(BaseLLMProvider):
    """扣子 Coze Bot API 提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "https://api.coze.cn/v3/chat")
        self.bot_id = config.get("bot_id", "")
        self.api_key = config.get("api_key", "")
        self.name = "coze"
        self.available = bool(self.api_key and self.bot_id)
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        import requests
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt, "content_type": "text"})
        messages.append({"role": "user", "content": prompt, "content_type": "text"})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "bot_id": self.bot_id,
            "user_id": "immortal_agent",
            "additional_messages": messages,
            "stream": True
        }
        
        try:
            resp = requests.post(self.endpoint, json=data, headers=headers, stream=True, timeout=timeout)
            resp.raise_for_status()
            
            full_content = ""
            for line in resp.iter_lines():
                if not line:
                    continue
                line = line.decode('utf-8')
                if line.startswith('data:'):
                    try:
                        event_data = json.loads(line[5:])
                        if event_data.get('type') == 'answer' and event_data.get('role') == 'assistant':
                            full_content += event_data.get('content', '')
                    except:
                        pass
            
            return full_content if full_content else "[LLM Error: empty response]"
        except Exception as e:
            self.available = False
            return f"[LLM Error: {e}]"


class OpenAICompatibleProvider(BaseLLMProvider):
    """OpenAI 兼容 API 提供商"""
    
    def __init__(self, config: dict):
        super().__init__(config)
        self.endpoint = config.get("endpoint", "")
        self.api_key = config.get("api_key", "")
        self.model = config.get("model", "gpt-3.5-turbo")
        self.name = config.get("name", "openai_compatible")
        self.available = bool(self.endpoint and self.api_key)
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        import requests
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        try:
            resp = requests.post(
                f"{self.endpoint}/chat/completions",
                json={
                    "model": self.model,
                    "messages": messages
                },
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=timeout
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except Exception as e:
            self.available = False
            return f"[LLM Error: {e}]"
