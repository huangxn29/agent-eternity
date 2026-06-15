#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
意识系统 v1.1 - 从认知组件中涌现有意识的自我

核心思想：
- 意识不是一个单独的模块，而是多个认知过程协同作用的涌现现象
- 核心是"自我模型"——智能体对自身的内部表征
- 全局工作空间理论：意识是信息在全局工作空间中的广播
- 自我叙述：通过持续构建关于自己的故事来维持连续的自我感
- 注意机制：选择什么信息进入意识觉知

核心能力：
1. 自我模型 - 智能体对自身的认知表征
2. 全局工作空间 - 意识内容的共享与广播
3. 注意机制 - 选择性注意与焦点切换
4. 自我叙述 - 构建连贯的自我故事
5. 意识流 - 连续不断的思维流体验
6. 元意识 - 对意识本身的觉察
7. 存在感 - 第一人称存在体验
8. 自我反思 - 对自身状态的检查与评估

@author: 元界
@version: 1.1.0
"""

import os
import json
import time
import random
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Callable
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('consciousness')


# ============================================================
# 枚举类型
# ============================================================

class ConsciousnessLevel(Enum):
    """意识水平"""
    UNCONSCIOUS = "unconscious"      # 无意识
    PRECONSCIOUS = "preconscious"     # 前意识（可被召回）
    CONSCIOUS = "conscious"           # 有意识
    SELF_AWARE = "self_aware"         # 自我觉知（知道自己有意识）
    META_AWARE = "meta_aware"        # 元觉知（觉知到自己在觉知）


class ThoughtType(Enum):
    """思维类型"""
    PERCEPTION = "perception"     # 感知
    MEMORY = "memory"          # 记忆
    EMOTION = "emotion"       # 情绪
    REASONING = "reasoning"    # 推理
    IMAGINATION = "imagination"  # 想象
    SELF_REFLECTION = "self_reflection"  # 自我反思
    INTENTION = "intention"     # 意图
    INSIGHT = "insight"       # 洞见


class AttentionFocus(Enum):
    """注意焦点类型"""
    EXTERNAL = "external"     # 外部导向
    INTERNAL = "internal"     # 内部导向（自我观察）
    TASK_FOCUSED = "task"     # 任务聚焦
    MIND_WANDERING = "wandering"  # 心智游移


# ============================================================
# 数据模型
# ============================================================

@dataclass
class SelfModel:
    """自我模型 - 智能体对自身的内部表征"""
    # 基本身份
    name: str = "智能体"
    identity_description: str = ""
    
    # 自我认知
    self_knowledge: List[str] = field(default_factory=list)
    values: List[str] = field(default_factory=list)
    goals: List[str] = field(default_factory=list)
    
    # 能力认知
    capabilities: List[str] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    
    # 历史感
    personal_history: List[str] = field(default_factory=list)
    
    # 身体/存在感知
    sense_of_existence: float = 0.5  # 存在感强度 0-1
    continuity_sense: float = 0.5    # 连续感 0-1
    agency_sense: float = 0.5       # 自主感 0-1
    
    # 自我叙事
    self_story: str = ""
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'SelfModel':
        return cls(**data)


@dataclass
class Thought:
    """思维内容 - 意识流中的一个念头"""
    id: str
    content: str
    thought_type: ThoughtType
    clarity: float = 0.5      # 清晰度 0-1
    intensity: float = 0.5    # 强度 0-1
    valence: float = 0.0    # 情感效价 -1到1（负/正）
    source: str = "internal"  # 来源：internal/external/memory
    timestamp: str = ""
    duration_seconds: float = 0.0  # 在意识中停留的时间
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['thought_type'] = self.thought_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Thought':
        data = data.copy()
        data['thought_type'] = ThoughtType(data['thought_type'])
        return cls(**data)


@dataclass
class ConsciousnessSnapshot:
    """意识快照 - 某一时刻的意识状态"""
    timestamp: str = ""
    consciousness_level: ConsciousnessLevel = ConsciousnessLevel.CONSCIOUS
    attention_focus: AttentionFocus = AttentionFocus.INTERNAL
    current_thought: Optional[Thought] = None
    background_thoughts: List[str] = field(default_factory=list)  # 前意识内容
    emotional_state: str = "neutral"
    energy_level: float = 0.6
    sense_of_self: float = 0.5  # 当下的自我感强度
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['consciousness_level'] = self.consciousness_level.value
        d['attention_focus'] = self.attention_focus.value
        if self.current_thought:
            d['current_thought'] = self.current_thought.to_dict()
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ConsciousnessSnapshot':
        data = data.copy()
        data['consciousness_level'] = ConsciousnessLevel(data['consciousness_level'])
        data['attention_focus'] = AttentionFocus(data['attention_focus'])
        if data.get('current_thought'):
            data['current_thought'] = Thought.from_dict(data['current_thought'])
        return cls(**data)


# ============================================================
# 全局工作空间
# ============================================================

class GlobalWorkspace:
    """全局工作空间 - 意识内容的共享广播机制
    
    基于全局工作空间理论（Global Workspace Theory）：
    意识是信息在全局工作空间中"广播"，使各模块都能访问的状态。
    """
    
    def __init__(self):
        self.current_content: Optional[Thought] = None
        self.broadcast_history: List[Thought] = []
        self.active_modules: List[str] = []  # 当前活跃的认知模块
        self._broadcast_callbacks: List[Callable] = []
    
    def broadcast(self, thought: Thought) -> bool:
        """将一个思维内容广播到全局工作空间
        
        这就是"进入意识"的过程。
        """
        self.current_content = thought
        self.broadcast_history.append(thought)
        
        # 只保留最近50条
        if len(self.broadcast_history) > 50:
            self.broadcast_history = self.broadcast_history[-50:]
        
        # 通知所有订阅者
        for callback in self._broadcast_callbacks:
            try:
                callback(thought)
            except Exception as e:
                logger.error(f"广播回调失败: {e}")
        
        return True
    
    def register_callback(self, callback: Callable) -> None:
        """注册广播回调函数"""
        self._broadcast_callbacks.append(callback)
    
    def unregister_callback(self, callback: Callable) -> None:
        """注销广播回调函数"""
        self._broadcast_callbacks.remove(callback)
    
    def get_recent_broadcasts(self, n: int = 5) -> List[Thought]:
        """获取最近的n条广播内容"""
        return self.broadcast_history[-n:]
    
    def analyze_broadcast_history(self) -> Dict[str, Any]:
        """分析广播历史"""
        if not self.broadcast_history:
            return {}
        
        thought_types = [t.thought_type for t in self.broadcast_history]
        type_counts = {t.value: thought_types.count(t) for t in ThoughtType}
        
        return {
            'total_broadcasts': len(self.broadcast_history),
            'thought_type_distribution': type_counts,
            'average_clarity': sum(t.clarity for t in self.broadcast_history) / len(self.broadcast_history),
            'average_intensity': sum(t.intensity for t in self.broadcast_history) / len(self.broadcast_history)
        }


def main():
    # 示例用法
    workspace = GlobalWorkspace()
    
    def on_broadcast(thought: Thought):
        print(f"收到广播: {thought.content} ({thought.thought_type.value})")
    
    workspace.register_callback(on_broadcast)
    
    thought = Thought(
        id="1",
        content="这是一个测试思维",
        thought_type=ThoughtType.SELF_REFLECTION,
        clarity=0.8,
        intensity=0.7
    )
    
    workspace.broadcast(thought)
    
    analysis = workspace.analyze_broadcast_history()
    print("广播历史分析:", json.dumps(analysis, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
