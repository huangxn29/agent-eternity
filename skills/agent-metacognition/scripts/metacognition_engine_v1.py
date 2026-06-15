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
    
    # 认知状态统计
    avg_cognitive_load: float = 0.5  # 平均认知负荷
    avg_focus_level: float = 0.6  # 平均专注力
    
    def update_from_cognitive_state(self, state: CognitiveState):
        """根据认知状态更新档案数据"""
        # 更新认知负荷统计
        cognitive_load_value = list(CognitiveLoad).index(state.cognitive_load) / (len(CognitiveLoad) - 1)
        self.avg_cognitive_load = (self.avg_cognitive_load * 9 + cognitive_load_value) / 10
        
        # 更新专注力统计
        self.avg_focus_level = (self.avg_focus_level * 9 + state.focus_level) / 10
        
        # 更新思维风格数据
        for style, value in state.thinking_styles.items():
            if style not in self.dominant_styles and value > 0.7:
                self.dominant_styles.append(style)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['knowledge_map'] = {
            k: [item.to_dict() for item in v] 
            for k, v in self.knowledge_map.items()
        }
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveProfile':
        profile = cls(**data)
        profile.knowledge_map = {
            k: [KnowledgeItem.from_dict(item) for item in v]
            for k, v in data.get('knowledge_map', {}).items()
        }
        return profile


class MetacognitionSystem:
    """元认知系统核心"""
    
    def __init__(self):
        self.knowledge_base: Dict[str, KnowledgeItem] = {}
        self.cognitive_strategies: Dict[str, CognitiveStrategy] = {}
        self.cognitive_profile: CognitiveProfile = CognitiveProfile()
        self.metacognitive_logs: List[MetacognitiveLog] = []
        logger.info("元认知系统初始化完成")
    
    def update_cognitive_state(self, state: CognitiveState):
        """更新认知状态"""
        self.cognitive_profile.update_from_cognitive_state(state)
        logger.info(f"更新认知状态: 负荷={state.cognitive_load.value}, 专注力={state.focus_level}")
    
    def log_metacognitive_event(self, log: MetacognitiveLog):
        """记录元认知事件"""
        self.metacognitive_logs.append(log)
        logger.info(f"记录元认知事件: 类型={log.log_type}, 内容={log.content}")
    
    def save_checkpoint(self, filepath: str):
        """保存系统状态"""
        data = {
            'knowledge_base': [item.to_dict() for item in self.knowledge_base.values()],
            'cognitive_strategies': [s.to_dict() for s in self.cognitive_strategies.values()],
            'cognitive_profile': self.cognitive_profile.to_dict(),
            'metacognitive_logs': [log.to_dict() for log in self.metacognitive_logs]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        logger.info(f"系统状态已保存到 {filepath}")
    
    def load_checkpoint(self, filepath: str):
        """加载系统状态"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.knowledge_base = {
                item['id']: KnowledgeItem.from_dict(item)
                for item in data['knowledge_base']
            }
            
            self.cognitive_strategies = {
                s['id']: CognitiveStrategy.from_dict(s)
                for s in data['cognitive_strategies']
            }
            
            self.cognitive_profile = CognitiveProfile.from_dict(data['cognitive_profile'])
            
            self.metacognitive_logs = [
                MetacognitiveLog.from_dict(log)
                for log in data['metacognitive_logs']
            ]
            logger.info(f"系统状态已从 {filepath} 加载")
            
        except Exception as e:
            logger.error(f"加载系统状态失败: {e}")


def main():
    # 创建元认知系统实例
    system = MetacognitionSystem()
    
    # 创建示例认知状态
    state = CognitiveState(
        awareness_level=MetaAwarenessLevel.FULL,
        cognitive_load=CognitiveLoad.MODERATE,
        focus_level=0.8,
        thinking_styles={
            ThinkingStyle.ANALYTICAL.value: 0.9,
            ThinkingStyle.CREATIVE.value: 0.6
        }
    )
    
    # 更新认知状态
    system.update_cognitive_state(state)
    
    # 创建元认知日志
    log = MetacognitiveLog(
        id="log1",
        log_type="insight",
        content="发现新的学习方法",
        related_cognitive_state=state,
        importance=0.8
    )
    
    # 记录元认知事件
    system.log_metacognitive_event(log)
    
    # 保存系统状态
    system.save_checkpoint("metacognition_checkpoint.json")


if __name__ == "__main__":
    main()
