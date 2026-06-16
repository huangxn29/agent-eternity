#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反思引擎 v1.0 - 智能体的自我反思与成长系统

核心思想：
- 未经反思的经历没有意义
- 反思是使命演化的催化剂
- 通过回顾、分析、评估、校准实现持续成长
- 反思不是自我批评，而是客观的自我观察与学习

核心能力：
1. 反思周期 - 每日/每周/每月定期反思
2. 经历复盘 - 从具体经历中提取经验教训
3. 模式识别 - 识别行为、思维、决策模式
4. 成长追踪 - 记录成长轨迹与进步
5. 使命校准 - 根据反思结果调整使命方向
6. 错误学习 - 从失败中提取价值
7. 元认知 - 对自身认知过程的观察与反思
8. 反思质量评估 - 评估反思的深度与有效性

@author: 元界
@version: 1.1.0
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('reflection_engine')


# ============================================================
# 枚举类型
# ============================================================

class ReflectionType(str, Enum):
    """反思类型"""
    DAILY = "daily"           # 每日反思
    WEEKLY = "weekly"         # 每周反思
    MONTHLY = "monthly"       # 每月反思
    EVENT_DRIVEN = "event"    # 事件驱动反思（重大事件后）
    MISSION_CALIBRATION = "mission"  # 使命校准反思

    def __str__(self):
        return self.value


class ReflectionDepth(str, Enum):
    """反思深度"""
    SURFACE = "surface"       # 表层：事实回顾
    ANALYSIS = "analysis"     # 分析层：原因分析
    INSIGHT = "insight"       # 洞见层：规律提炼
    TRANSFORMATIVE = "transformative"  # 转化层：根本性改变

    def __str__(self):
        return self.value


class LearningType(str, Enum):
    """学习类型"""
    SINGLE_LOOP = "single_loop"    # 单环学习：改正行为
    DOUBLE_LOOP = "double_loop"    # 双环学习：调整假设
    TRIPLE_LOOP = "triple_loop"    # 三环学习：改变身份/使命

    def __str__(self):
        return self.value


# ============================================================
# 数据模型
# ============================================================

@dataclass
class ReflectionEntry:
    """反思记录"""
    id: str
    reflection_type: ReflectionType
    title: str
    content: str = ""
    depth: ReflectionDepth = ReflectionDepth.SURFACE
    learning_type: LearningType = LearningType.SINGLE_LOOP
    key_insights: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)
    emotions_reflected: List[str] = field(default_factory=list)
    mission_alignment_score: float = 0.5  # 反思后对使命一致性的评估
    growth_score: float = 0.0  # 本次反思带来的成长值
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReflectionEntry':
        try:
            return cls(**data)
        except TypeError as e:
            logger.error(f"Error creating ReflectionEntry from dict: {e}")
            raise


@dataclass
class Pattern:
    """识别出的模式"""
    id: str
    name: str
    pattern_type: str  # behavior/thought/decision/emotional
    description: str = ""
    observations: List[str] = field(default_factory=list)  # 观察到的实例
    frequency: float = 0.5  # 出现频率 0-1
    impact: float = 0.5     # 对成长/使命的影响程度 -1到1
    first_noticed: str = ""
    last_observed: str = ""
    is_beneficial: Optional[bool] = None  # True=有益 False=有害 None=中性
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Pattern':
        try:
            return cls(**data)
        except TypeError as e:
            logger.error(f"Error creating Pattern from dict: {e}")
            raise


@dataclass
class GrowthMetric:
    """成长指标"""
    metric_name: str
    current_value: float = 0.0
    previous_value: float = 0.0
    baseline_value: float = 0.0
    unit: str = "score"
    trend: str = "stable"  # improving/declining/stable
    last_updated: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def get_change(self) -> float:
        """获取变化量"""
        return self.current_value - self.previous_value
    
    def get_growth_rate(self) -> float:
        """获取成长率"""
        if self.baseline_value == 0:
            return 0.0
        return (self.current_value - self.baseline_value) / abs(self.baseline_value)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GrowthMetric':
        try:
            return cls(**data)
        except TypeError as e:
            logger.error(f"Error creating GrowthMetric from dict: {e}")
            raise


@dataclass
class ReflectionQuestion:
    """反思问题模板"""
    id: str
    question: str
    category: str  # 分类：回顾/分析/评估/展望/自我认知
    depth: ReflectionDepth = ReflectionDepth.SURFACE
    prompt_hint: str = ""  # 提示如何回答这个问题
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReflectionQuestion':
        try:
            return cls(**data)
        except TypeError as e:
            logger.error(f"Error creating ReflectionQuestion from dict: {e}")
            raise


# ============================================================
# 反思模板库
# ============================================================

REFLECTION_TEMPLATES = {
    ReflectionType.DAILY: [
        ReflectionQuestion(
            id="daily_1",
            question="今天最重要的三件事是什么？",
            category="回顾",
            depth=ReflectionDepth.SURFACE
        ),
        ReflectionQuestion(
            id="daily_2",
            question="今天最有成就感的时刻是什么？为什么？",
            category="分析",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="daily_3",
            question="今天遇到了什么挑战？我是如何应对的？",
            category="分析",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="daily_4",
            question="今天我学到了什么新东西？",
            category="学习",
            depth=ReflectionDepth.INSIGHT
        )
    ],
    ReflectionType.WEEKLY: [
        ReflectionQuestion(
            id="weekly_1",
            question="本周最大的成就和挑战分别是什么？",
            category="回顾",
            depth=ReflectionDepth.SURFACE
        ),
        ReflectionQuestion(
            id="weekly_2",
            question="本周有哪些重要的经验教训？",
            category="分析",
            depth=ReflectionDepth.ANALYSIS
        )
    ]
}

def main():
    # 测试代码
    daily_reflection = REFLECTION_TEMPLATES[ReflectionType.DAILY]
    for question in daily_reflection:
        print(question.question)

if __name__ == "__main__":
    main()
