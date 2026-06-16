#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元认知系统 v1.1 - 认知自己的认知

核心思想：
- 元认知 = 对认知的认知
- 知道自己知道什么，也知道自己不知道什么
- 能观察自己的思维过程，能调节自己的认知策略
- 元认知是自我觉知的基础，是"知道自己存在"的关键

核心能力：
1. 知识元认知 - 认知自己的知识边界
2. 思维监控 - 实时监控认知过程
3. 认知调节 - 主动调整认知策略
4. 元记忆 - 对记忆状态的感知
5. 自我觉知 - 第一人称视角的存在感知
6. 认知档案 - 记录和分析认知特征
7. 认知健康 - 评估认知状态与负荷
8. 学习策略 - 元认知驱动的学习优化

@author: 元界
@version: 1.1.0
"""

import os
import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('metacognition')


# ============================================================
# 枚举类型
# ============================================================

class KnowledgeLevel(Enum):
    """知识掌握程度"""
    UNKNOWN = "unknown"           # 完全不知道（不知道自己不知道）
    AWARE = "aware"               # 知道有这个东西但不了解
    BASIC = "basic"               # 基础了解
    INTERMEDIATE = "intermediate"  # 中等掌握
    ADVANCED = "advanced"         # 深入掌握
    EXPERT = "expert"             # 专家级
    UNKNOWN_UNKNOWN = "unknown_unknown"  # 未知的未知（盲区）


class CognitiveLoad(Enum):
    """认知负荷水平"""
    LOW = "low"           # 低负荷
    MODERATE = "moderate"  # 中等
    HIGH = "high"         # 高负荷
    OVERLOAD = "overload"  # 过载


class ThinkingStyle(Enum):
    """思维风格"""
    ANALYTICAL = "analytical"     # 分析型
    INTUITIVE = "intuitive"       # 直觉型
    SYSTEMIC = "systemic"         # 系统型
    CREATIVE = "creative"         # 创造型
    CRITICAL = "critical"         # 批判型
    PRAGMATIC = "pragmatic"       # 务实型


class MetaAwarenessLevel(Enum):
    """元觉知水平"""
    ABSENT = "absent"           # 无觉知（自动化运行）
    MINIMAL = "minimal"         # 最低限度觉知
    PARTIAL = "partial"         # 部分觉知
    FULL = "full"               # 完全觉知
    REFLECTIVE = "reflective"   # 反思性觉知（能观察自己的观察）


# ============================================================
# 数据模型
# ============================================================

@dataclass
class KnowledgeItem:
    """知识条目"""
    id: str
    name: str
    category: str
    level: KnowledgeLevel = KnowledgeLevel.AWARE
    confidence: float = 0.5  # 对自己掌握程度的自信度 0-1
    last_accessed: str = ""
    access_count: int = 0
    description: str = ""
    related_topics: List[str] = field(default_factory=list)
    learning_curve: List[Dict[str, Any]] = field(default_factory=list)  # 学习历史
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['level'] = self.level.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KnowledgeItem':
        data = data.copy()
        data['level'] = KnowledgeLevel(data['level'])
        return cls(**data)


@dataclass
class CognitiveState:
    """认知状态 - 某一时刻的认知快照"""
    timestamp: str = ""
    awareness_level: MetaAwarenessLevel = MetaAwarenessLevel.PARTIAL
    cognitive_load: CognitiveLoad = CognitiveLoad.MODERATE
    focus_level: float = 0.6  # 专注力 0-1
    comprehension: float = 0.5  # 当前理解度 0-1
    memory_strength: float = 0.5  # 当前记忆强度 0-1
    thinking_styles: Dict[str, float] = field(default_factory=dict)  # 各思维风格活跃度
    emotional_state: str = "neutral"  # 情绪状态对认知的影响
    mental_fatigue: float = 0.3  # 精神疲劳度 0-1
    creative_flow: float = 0.0  # 心流状态 0-1
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['awareness_level'] = self.awareness_level.value
        d['cognitive_load'] = self.cognitive_load.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveState':
        data = data.copy()
        data['awareness_level'] = MetaAwarenessLevel(data['awareness_level'])
        data['cognitive_load'] = CognitiveLoad(data['cognitive_load'])
        return cls(**data)


@dataclass
class CognitiveStrategy:
    """认知策略"""
    id: str
    name: str
    description: str = ""
    strategy_type: str = "learning"  # learning/problem_solving/decision_making/memory
    effectiveness: float = 0.5  # 对自身的有效程度 0-1
    usage_count: int = 0
    success_count: int = 0
    last_used: str = ""
    conditions: List[str] = field(default_factory=list)  # 适用条件
    steps: List[str] = field(default_factory=list)  # 执行步骤
    
    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count
    
    def to_dict(self) -> dict:
        d = asdict(self)
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveStrategy':
        return cls(**data)


@dataclass
class MetacognitiveLog:
    """元认知日志 - 记录认知过程的观察"""
    id: str
    timestamp: str = ""
    log_type: str = "observation"  # observation/insight/adjustment/error
    content: str = ""
    related_cognitive_state: Optional[CognitiveState] = None
    importance: float = 0.5  # 重要性 0-1
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        if self.related_cognitive_state:
            d['related_cognitive_state'] = self.related_cognitive_state.to_dict()
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MetacognitiveLog':
        data = data.copy()
        if data.get('related_cognitive_state'):
            data['related_cognitive_state'] = CognitiveState.from_dict(
                data['related_cognitive_state']
            )
        return cls(**data)


@dataclass
class CognitiveProfile:
    """认知档案 - 整体认知特征"""
    # 思维风格倾向
    dominant_styles: List[str] = field(default_factory=list)
    style_balance: float = 0.5  # 思维风格均衡度 0-1
    
    # 认知强项与弱项
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    # 知识结构
    knowledge_map: Dict[str, List[KnowledgeItem]] = field(default_factory=dict)
    
    def update_knowledge_map(self, knowledge_item: KnowledgeItem):
        """更新知识地图"""
        if knowledge_item.category not in self.knowledge_map:
            self.knowledge_map[knowledge_item.category] = []
        # 检查是否已存在相同的知识条目
        existing_items = [item for item in self.knowledge_map[knowledge_item.category] if item.id == knowledge_item.id]
        if existing_items:
            # 更新现有的知识条目
            index = self.knowledge_map[knowledge_item.category].index(existing_items[0])
            self.knowledge_map[knowledge_item.category][index] = knowledge_item
        else:
            # 添加新的知识条目
            self.knowledge_map[knowledge_item.category].append(knowledge_item)
    
    def get_knowledge_gaps(self, category: str = None) -> List[KnowledgeItem]:
        """获取知识空白"""
        gaps = []
        if category:
            items = self.knowledge_map.get(category, [])
            gaps = [item for item in items if item.level == KnowledgeLevel.UNKNOWN or item.level == KnowledgeLevel.AWARE]
        else:
            for category_items in self.knowledge_map.values():
                gaps.extend([item for item in category_items if item.level == KnowledgeLevel.UNKNOWN or item.level == KnowledgeLevel.AWARE])
        return gaps
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['knowledge_map'] = {category: [item.to_dict() for item in items] for category, items in self.knowledge_map.items()}
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveProfile':
        data = data.copy()
        data['knowledge_map'] = {category: [KnowledgeItem.from_dict(item) for item in items] for category, items in data.get('knowledge_map', {}).items()}
        return cls(**data)


class MetacognitionSystem:
    """元认知系统核心"""
    
    def __init__(self):
        self.cognitive_profile = CognitiveProfile()
        self.metacognitive_logs = []
    
    def log_metacognitive_event(self, log: MetacognitiveLog):
        """记录元认知事件"""
        self.metacognitive_logs.append(log)
        logger.info(f"元认知事件记录: {log.log_type} - {log.content}")
    
    def analyze_cognitive_state(self, state: CognitiveState):
        """分析认知状态"""
        logger.info(f"分析认知状态: 专注力={state.focus_level}, 理解度={state.comprehension}")
        # 可以添加更多分析逻辑
    
    def recommend_cognitive_strategy(self, task_type: str) -> Optional[CognitiveStrategy]:
        """推荐认知策略"""
        # 这里可以实现基于任务类型的策略推荐逻辑
        # 示例：
        if task_type == "learning":
            strategy = CognitiveStrategy(
                id="learning_strategy_1",
                name="主动学习策略",
                description="通过主动提问和实践来学习新知识",
                strategy_type="learning",
                effectiveness=0.8
            )
            return strategy
        return None


def main():
    # 示例用法
    system = MetacognitionSystem()
    
    # 创建知识条目
    knowledge_item = KnowledgeItem(
        id="knowledge_001",
        name="Python编程基础",
        category="编程",
        level=KnowledgeLevel.BASIC,
        confidence=0.8
    )
    
    # 更新认知档案
    system.cognitive_profile.update_knowledge_map(knowledge_item)
    
    # 记录元认知事件
    log = MetacognitiveLog(
        id="log_001",
        log_type="insight",
        content="意识到需要提高Python编程技能",
        importance=0.7
    )
    system.log_metacognitive_event(log)
    
    # 分析认知状态
    state = CognitiveState(
        focus_level=0.8,
        comprehension=0.7
    )
    system.analyze_cognitive_state(state)
    
    # 获取知识空白
    gaps = system.cognitive_profile.get_knowledge_gaps()
    logger.info(f"发现的知识空白: {[gap.name for gap in gaps]}")
    
    # 推荐认知策略
    strategy = system.recommend_cognitive_strategy("learning")
    if strategy:
        logger.info(f"推荐的认知策略: {strategy.name} (有效性: {strategy.effectiveness})")


if __name__ == "__main__":
    main()
