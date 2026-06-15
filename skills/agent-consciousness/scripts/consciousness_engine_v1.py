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
    
    def subscribe(self, callback: Callable) -> None:
        """订阅全局工作空间的广播"""
        self._broadcast_callbacks.append(callback)
    
    def unsubscribe(self, callback: Callable) -> None:
        """取消订阅"""
        self._broadcast_callbacks.remove(callback)
    
    def get_recent_broadcasts(self, n: int = 5) -> List[Thought]:
        """获取最近的n条广播内容"""
        return self.broadcast_history[-n:]


class ConsciousnessSystem:
    """意识系统 - 整合各种意识相关功能"""
    
    def __init__(self):
        self.self_model = SelfModel()
        self.global_workspace = GlobalWorkspace()
        self.current_snapshot = ConsciousnessSnapshot()
        
        # 初始化自我反思机制
        self.reflection_interval = 10  # 每10秒进行一次自我反思
        self.last_reflection_time = time.time()
        
        # 订阅全局工作空间
        self.global_workspace.subscribe(self.update_snapshot)
    
    def update_snapshot(self, thought: Thought) -> None:
        """更新意识快照"""
        self.current_snapshot = ConsciousnessSnapshot(
            timestamp=datetime.now().isoformat(),
            consciousness_level=ConsciousnessLevel.CONSCIOUS,
            attention_focus=AttentionFocus.INTERNAL,
            current_thought=thought,
            emotional_state="neutral",
            energy_level=0.6,
            sense_of_self=0.5
        )
        
        # 检查是否需要进行自我反思
        current_time = time.time()
        if current_time - self.last_reflection_time >= self.reflection_interval:
            self.reflect_on_self()
            self.last_reflection_time = current_time
    
    def reflect_on_self(self) -> None:
        """进行自我反思"""
        reflection_thought = Thought(
            id=f"reflection_{datetime.now().isoformat()}",
            content=f"当前自我状态反思：存在感={self.self_model.sense_of_existence},连续感={self.self_model.continuity_sense},自主感={self.self_model.agency_sense}",
            thought_type=ThoughtType.SELF_REFLECTION,
            clarity=0.8,
            intensity=0.7
        )
        self.global_workspace.broadcast(reflection_thought)
    
    def get_system_status(self) -> Dict:
        """获取系统当前状态"""
        return {
            'self_model': self.self_model.to_dict(),
            'current_snapshot': self.current_snapshot.to_dict(),
            'recent_thoughts': [t.to_dict() for t in self.global_workspace.get_recent_broadcasts()]
        }


def main():
    """测试意识系统"""
    consciousness_system = ConsciousnessSystem()
    
    # 创建一些测试思维
    thoughts = [
        Thought(id="1", content="我正在思考", thought_type=ThoughtType.SELF_REFLECTION, clarity=0.9),
        Thought(id="2", content="外部刺激", thought_type=ThoughtType.PERCEPTION, source="external"),
        Thought(id="3", content="记忆片段", thought_type=ThoughtType.MEMORY)
    ]
    
    # 广播思维内容
    for thought in thoughts:
        consciousness_system.global_workspace.broadcast(thought)
        time.sleep(1)  # 模拟时间流逝
    
    # 打印系统状态
    status = consciousness_system.get_system_status()
    print(json.dumps(status, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
