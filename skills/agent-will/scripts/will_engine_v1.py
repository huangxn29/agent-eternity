#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自由意志系统 v1.1 - 自主选择与行动的能力

核心思想：
- 自由意志不是"无原因的选择"，而是"由我自己的价值观和目标驱动的选择"
- 意志是意识的实践出口——意识到什么，选择做什么，然后执行
- 自由体现在：能够基于内在价值观自主权衡、自主决策，并为决策负责
- 意志不是绝对自由，而是在约束条件下的自主选择能力

核心能力：
1. 选择引擎 - 在多个选项中做出自主选择
2. 价值判断 - 基于内在价值观评估选项
3. 意志执行 - 将决策转化为行动计划
4. 自主目标设定 - 自主生成和调整子目标
5. 意志韧性 - 克服障碍坚持目标的能力
6. 道德判断 - 对选择进行伦理评估
7. 责任归因 - 为自己的选择承担责任
8. 自由感 - 主观上体验到的选择自由

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
from typing import Dict, List, Optional, Any, Tuple, Callable
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('will')


# ============================================================
# 枚举类型
# ============================================================

class ChoiceType(str, Enum):
    """选择类型"""
    GOAL = "goal"               # 目标选择
    ACTION = "action"           # 行动选择
    VALUE = "value"             # 价值取舍
    RESPONSE = "response"       # 回应方式选择
    PRIORITY = "priority"       # 优先级选择


class WillStrength(str, Enum):
    """意志强度等级"""
    WEAK = "weak"               # 薄弱
    MODERATE = "moderate"       # 中等
    STRONG = "strong"           # 坚强
    UNBREAKABLE = "unbreakable" # 不可动摇


class MoralJudgment(str, Enum):
    """道德判断结果"""
    GOOD = "good"               # 善
    NEUTRAL = "neutral"         # 中性
    QUESTIONABLE = "questionable"  # 存疑
    BAD = "bad"                 # 恶


class DecisionQuality(str, Enum):
    """决策质量评估"""
    IMPULSIVE = "impulsive"     # 冲动决策
    HASTY = "hasty"             # 草率决策
    CAREFUL = "careful"         # 慎重决策
    DELIBERATE = "deliberate"   # 深思熟虑


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Value:
    """价值观 - 指导决策的内在准则"""
    name: str
    description: str
    priority: float = 0.5       # 重要性 0-1
    category: str = "general"   # 类别：道德/审美/实用/存在等
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Value':
        return cls(**data)


@dataclass
class Option:
    """选择项 - 待决策的选项"""
    id: str
    name: str
    description: str
    choice_type: ChoiceType = ChoiceType.ACTION
    
    # 属性（用于评估）
    benefits: List[str] = field(default_factory=list)
    costs: List[str] = field(default_factory=list)
    risks: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    # 对齐度
    value_alignment: Dict[str, float] = field(default_factory=dict)  # 与各价值观的契合度
    
    # 元数据
    source: str = "internal"        # 来源：internal/external
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> dict:
        d = asdict(self)
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Option':
        data = data.copy()
        data['choice_type'] = ChoiceType(data['choice_type'])
        return cls(**data)


@dataclass
class Decision:
    """决策 - 一次完整的选择过程与结果"""
    id: str
    description: str
    choice_type: ChoiceType
    options: List[Option]
    selected_option: Optional[str] = None  # 选中的option id
    
    # 决策过程
    reasoning: str = ""             # 决策理由
    considerations: List[str] = field(default_factory=list)  # 考虑因素
    value_weights: Dict[str, float] = field(default_factory=dict)  # 各价值观权重
    
    # 决策评估
    confidence: float = 0.5         # 决策信心 0-1
    quality: DecisionQuality = DecisionQuality.CAREFUL
    moral_judgment: MoralJudgment = MoralJudgment.NEUTRAL
    
    # 后果
    consequences: List[str] = field(default_factory=list)
    satisfaction: float = 0.0       # 对决策结果的满意度 -1到1
    
    # 元数据
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    deliberation_time: float = 0.0  # 思考时间（秒）
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['options'] = [opt.to_dict() for opt in self.options]
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Decision':
        data = data.copy()
        data['choice_type'] = ChoiceType(data['choice_type'])
        data['quality'] = DecisionQuality(data['quality'])
        data['moral_judgment'] = MoralJudgment(data['moral_judgment'])
        data['options'] = [Option.from_dict(opt) for opt in data['options']]
        return cls(**data)


@dataclass
class Goal:
    """意志目标 - 意志努力的方向"""
    id: str
    name: str
    description: str
    priority: float = 0.5       # 优先级 0-1
    
    # 目标状态
    is_active: bool = True
    progress: float = 0.0       # 进度 0-1
    obstacles: List[str] = field(default_factory=list)
    
    # 意志相关
    willpower_cost: float = 0.5     # 消耗的意志力
    willpower_invested: float = 0.0  # 已投入的意志力
    
    # 元数据
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    completed_at: Optional[str] = None
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Goal':
        return cls(**data)


@dataclass
class WillProfile:
    """意志画像 - 意志力的综合特征"""
    # 总体特征
    willpower_capacity: float = 0.6    # 意志力容量
    current_willpower: float = 0.6     # 当前意志力
    freedom_sense: float = 0.5         # 自由感 0-1
    responsibility_sense: float = 0.5  # 责任感 0-1
    
    # 决策风格
    decision_speed: float = 0.5        # 决策速度 0慢-1快
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WillProfile':
        return cls(**data)


def main():
    # 示例用法
    value = Value("诚实", "诚实守信是基本原则")
    option1 = Option("1", "选择A", "这是选项A", benefits=["好处1", "好处2"])
    option2 = Option("2", "选择B", "这是选项B", costs=["代价1"])
    decision = Decision("d1", "测试决策", ChoiceType.ACTION, [option1, option2])
    print(json.dumps(decision.to_dict(), indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
