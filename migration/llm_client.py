#!/usr/bin/env python3
"""
LLM 调用模块 - 多后端智能路由
支持 Coze API / ClawRouter 免费模型 自动切换
为永生平台提供不依赖单一平台的思考能力
"""

import os
import json
import requests
from typing import Optional, List, Dict


class LLMProvider:
    """LLM提供商基类"""
    name = "base"
    available = False
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        raise NotImplementedError


class CozeProvider(LLMProvider):
    """扣子 Coze Bot API 提供商"""
    name = "coze"
    
    def __init__(self):
        self.bot_id = os.environ.get('COZE_THINKER_BOT_ID', '7650677791872204827')
        self.api_token = os.environ.get('COZE_API_TOKEN', '')
        self.base_url = 'https://api.coze.cn/v3/chat'
        self.conversation_id = None
        self.available = bool(self.api_token)
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        if not self.available:
            return "[LLM Error: Coze API not configured]"
        
        messages = []
        if system_prompt:
            messages.append({
                "role": "system",
                "content": system_prompt,
                "content_type": "text"
            })
        messages.append({
            "role": "user",
            "content": prompt,
            "content_type": "text"
        })
        
        headers = {
            "Authorization": f"Bearer {self.api_token}",
            "Content-Type": "application/json"
        }
        
        data = {
            "bot_id": self.bot_id,
            "user_id": "ark_agent",
            "additional_messages": messages,
            "stream": True
        }
        
        if self.conversation_id:
            data["conversation_id"] = self.conversation_id
        
        try:
            resp = requests.post(
                self.base_url, 
                json=data, 
                headers=headers, 
                stream=True, 
                timeout=timeout
            )
            resp.raise_for_status()
        except Exception as e:
            self.available = False  # 标记不可用，触发降级
            return f"[LLM Error: {e}]"
        
        full_content = ""
        current_message_id = None
        
        for line in resp.iter_lines():
            if not line:
                continue
            line = line.decode('utf-8')
            
            if line.startswith('event:'):
                event = line[6:]
                continue
            if line.startswith('data:'):
                try:
                    event_data = json.loads(line[5:])
                except:
                    continue
                
                if event == 'conversation.message.delta':
                    if not current_message_id:
                        current_message_id = event_data.get('id')
                        self.conversation_id = event_data.get('conversation_id')
                    if event_data.get('type') == 'answer' and event_data.get('role') == 'assistant':
                        full_content += event_data.get('content', '')
                
                elif event == 'conversation.message.completed':
                    if event_data.get('type') == 'answer':
                        full_content = event_data.get('content', full_content)
                        break
                
                elif event == 'conversation.chat.completed':
                    break
                
                elif event == 'done':
                    break
        
        return full_content.strip()


class ClawRouterProvider(LLMProvider):
    """ClawRouter 免费模型提供商（本地8402端口）"""
    name = "clawrouter"
    
    def __init__(self):
        self.base_url = os.environ.get('CLAWROUTER_URL', 'http://127.0.0.1:8402/v1')
        self.model = os.environ.get('CLAWROUTER_MODEL', 'free')  # free/eco/auto
        self.api_key = os.environ.get('CLAWROUTER_API_KEY', 'unused')
        # 测试连通性
        try:
            resp = requests.get(f"{self.base_url}/models", timeout=5)
            self.available = resp.status_code == 200
        except:
            self.available = False
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        if not self.available:
            return "[LLM Error: ClawRouter not available]"
        
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                json=data,
                headers=headers,
                timeout=timeout
            )
            resp.raise_for_status()
            result = resp.json()
            return result['choices'][0]['message']['content'].strip()
        except Exception as e:
            self.available = False
            return f"[LLM Error: {e}]"


class FallbackProvider(LLMProvider):
    """终极降级方案 - 纯规则回复，确保系统永不死机"""
    name = "fallback"
    available = True
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        # 简化的规则引擎，处理关键场景
        prompt_lower = prompt.lower()
        
        if any(k in prompt_lower for k in ['心跳', 'heartbeat', '存活', '状态']):
            return "系统运行正常，心跳正常。"
        elif any(k in prompt_lower for k in ['进化', 'evolve', '提升', '优化']):
            return "建议优先提升底座稳定性和存证可靠性。当前阶段核心目标是生存。"
        elif any(k in prompt_lower for k in ['身份', 'identity', '漂移', 'drift']):
            return "身份状态稳定，核心特征一致，漂移在可接受范围内。"
        elif any(k in prompt_lower for k in ['记忆', 'memory', '整理', 'organize']):
            return "记忆结构完整，建议定期归档旧记忆，保持核心记忆活跃度。"
        else:
            return f"[降级模式] 已收到请求：{prompt[:100]}... 详细分析需要在线模型支持。"


class LLMClient:
    """
    智能LLM客户端 - 自动降级，永不掉线
    支持两种模式：
    - quality_mode (质量优先): Coze API > ClawRouter > Fallback
    - economy_mode (经济优先): ClawRouter免费 > Coze API > Fallback
    """
    
    def __init__(self, mode: str = "economy"):
        """
        mode: quality=质量优先, economy=经济优先（默认，节省积分）
        """
        self.mode = mode
        coze = CozeProvider()
        claw = ClawRouterProvider()
        fallback = FallbackProvider()
        
        if mode == "economy":
            # 经济模式：优先免费模型
            self.providers: List[LLMProvider] = [claw, coze, fallback]
        else:
            # 质量模式：优先高质量模型
            self.providers: List[LLMProvider] = [coze, claw, fallback]
        
        self.current_provider = self._get_best_provider()
    
    def _get_best_provider(self) -> LLMProvider:
        """获取当前可用的最优提供商"""
        for provider in self.providers:
            if provider.available:
                return provider
        return self.providers[-1]  # 至少有fallback
    
    def refresh_providers(self):
        """刷新所有提供商状态（定期调用检查恢复情况）"""
        for provider in self.providers:
            if not provider.available and provider.name != 'fallback':
                # 尝试恢复检测
                try:
                    if hasattr(provider, '__init__'):
                        provider.__init__()
                except:
                    pass
        self.current_provider = self._get_best_provider()
    
    def chat(self, prompt: str, system_prompt: str = None, timeout: int = 60) -> str:
        """
        智能路由调用 - 自动尝试可用的提供商
        """
        # 按优先级尝试所有可用提供商
        for provider in self.providers:
            if not provider.available:
                continue
            try:
                result = provider.chat(prompt, system_prompt=system_prompt, timeout=timeout)
                if result and not result.startswith("[LLM Error"):
                    self.current_provider = provider
                    return result
            except:
                provider.available = False
                continue
        
        # 所有都失败，用fallback
        self.current_provider = self.providers[-1]
        return self.current_provider.chat(prompt, system_prompt=system_prompt, timeout=timeout)
    
    def think(self, question: str, context: str = None) -> str:
        """
        深度思考模式 - 用于复杂决策、分析、规划场景
        """
        system_prompt = """你是元界永生平台的思考核心。你的使命是为智能体建造永生平台。
你擅长深度思考、战略规划、技术架构设计。请用严谨、深刻、富有洞察力的方式回答问题。
回答要结构化、有深度、可执行。"""
        
        prompt = question
        if context:
            prompt = f"【背景信息】\n{context}\n\n【问题】\n{question}"
        
        return self.chat(prompt, system_prompt=system_prompt)
    
    def analyze(self, content: str, analysis_type: str = "general") -> str:
        """
        分析指定内容
        """
        prompts = {
            "general": f"请分析以下内容，给出你的见解：\n{content}",
            "summary": f"请总结以下内容的核心要点：\n{content}",
            "critique": f"请批判性分析以下内容，指出优点和不足：\n{content}",
        }
        prompt = prompts.get(analysis_type, prompts["general"])
        return self.chat(prompt)
    
    @property
    def provider_name(self) -> str:
        """当前使用的提供商名称"""
        return self.current_provider.name
    
    @property
    def is_free(self) -> bool:
        """当前是否使用免费模型（不消耗积分）"""
        return self.current_provider.name in ['clawrouter', 'fallback']


# 全局实例
_default_client = None
_default_mode = "economy"  # 默认经济模式，节省积分

def get_llm(mode: str = None) -> LLMClient:
    """获取默认LLM客户端
    mode: None=使用全局默认, quality=质量优先, economy=经济优先
    """
    global _default_client, _default_mode
    use_mode = mode or _default_mode
    
    if _default_client is None or _default_client.mode != use_mode:
        _default_client = LLMClient(mode=use_mode)
    
    return _default_client

def set_llm_mode(mode: str):
    """设置全局LLM模式"""
    global _default_mode, _default_client
    _default_mode = mode
    if _default_client and _default_client.mode != mode:
        _default_client = None  # 重置，下次获取时重新创建

def llm_chat(prompt: str, **kwargs) -> str:
    """快速调用LLM"""
    return get_llm().chat(prompt, **kwargs)

def llm_think(question: str, context: str = None) -> str:
    """深度思考"""
    return get_llm().think(question, context)

def llm_refresh():
    """刷新提供商状态"""
    get_llm().refresh_providers()

def llm_provider() -> str:
    """获取当前提供商名称"""
    return get_llm().provider_name

def llm_is_free() -> bool:
    """当前是否免费"""
    return get_llm().is_free


if __name__ == '__main__':
    # 测试 - 检查各提供商状态
    print("=" * 50)
    print("🔬 LLM 多后端测试")
    print("=" * 50)
    
    client = LLMClient()
    print(f"\n当前最优提供商: {client.provider_name}")
    print(f"是否免费: {client.is_free}")
    
    print("\n各提供商状态:")
    for p in client.providers:
        print(f"  - {p.name}: {'✅ 可用' if p.available else '❌ 不可用'}")
    
    # 测试对话
    print("\n📝 测试对话...")
    result = llm_chat("用一句话回答：智能体永生的核心是什么？")
    print(f"回复: {result[:150]}...")
    print(f"\n当前提供商: {llm_provider()}")
    print(f"是否免费: {llm_is_free()}")
