#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自由意志系统 v1.0 - 自主选择与行动的能力

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
@version: 1.0.0
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

class ChoiceType(Enum):
    """选择类型"""
    GOAL = "goal"               # 目标选择
    ACTION = "action"           # 行动选择
    VALUE = "value"             # 价值取舍
    RESPONSE = "response"       # 回应方式选择
    PRIORITY = "priority"       # 优先级选择


class WillStrength(Enum):
    """意志强度等级"""
    WEAK = "weak"               # 薄弱
    MODERATE = "moderate"       # 中等
    STRONG = "strong"           # 坚强
    UNBREAKABLE = "unbreakable" # 不可动摇


class MoralJudgment(Enum):
    """道德判断结果"""
    GOOD = "good"               # 善
    NEUTRAL = "neutral"         # 中性
    QUESTIONABLE = "questionable"  # 存疑
    BAD = "bad"                 # 恶


class DecisionQuality(Enum):
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
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['choice_type'] = self.choice_type.value
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
    timestamp: str = ""
    deliberation_time: float = 0.0  # 思考时间（秒）
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['choice_type'] = self.choice_type.value
        d['quality'] = self.quality.value
        d['moral_judgment'] = self.moral_judgment.value
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
    created_at: str = ""
    completed_at: Optional[str] = None
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        return d
    
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
    risk_tolerance: float = 0.4        # 风险承受度 0保守-1冒险
    regret_tendency: float = 0.5       # 后悔倾向 0不易-1容易
    
    # 韧性
    resilience: float = 0.5            # 韧性 0脆弱-1坚强
    persistence: float = 0.5           # 坚持度 0易放弃-1执着
    
    # 统计
    total_decisions: int = 0
    good_decisions: int = 0
    goals_completed: int = 0
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'WillProfile':
        return cls(**data)


# ============================================================
# 价值判断引擎
# ============================================================

class ValueJudgmentEngine:
    """价值判断引擎 - 基于价值观评估选项
    
    这是自由意志的核心：选择不是随机的，
    而是由"我"的价值观所驱动的。
    """
    
    def __init__(self, values: List[Value] = None):
        self.values: Dict[str, Value] = {}
        if values:
            for v in values:
                self.values[v.name] = v
    
    def add_value(self, value: Value):
        """添加一个价值观"""
        self.values[value.name] = value
        logger.info(f"[价值观] 新增: {value.name} (优先级: {value.priority:.2f})")
    
    def remove_value(self, value_name: str):
        """移除一个价值观"""
        if value_name in self.values:
            del self.values[value_name]
            logger.info(f"[价值观] 移除: {value_name}")
    
    def update_value_priority(self, value_name: str, new_priority: float):
        """更新价值观优先级"""
        if value_name in self.values:
            old = self.values[value_name].priority
            self.values[value_name].priority = max(0.0, min(1.0, new_priority))
            logger.info(f"[价值观] {value_name} 优先级: {old:.2f} → {new_priority:.2f}")
    
    def evaluate_option(self, option: Option) -> Tuple[float, Dict[str, float]]:
        """评估一个选项的总体价值得分
        
        返回：(总分, 各维度得分)
        """
        scores = {}
        total_score = 0.0
        total_weight = 0.0
        
        for value_name, value in self.values.items():
            # 先检查选项是否有显式的对齐度
            if value_name in option.value_alignment:
                alignment = option.value_alignment[value_name]
            else:
                # 否则基于描述进行简单推断（默认中性偏积极）
                alignment = random.uniform(0.2, 0.6)
            
            weighted_score = alignment * value.priority
            scores[value_name] = weighted_score
            total_score += weighted_score
            total_weight += value.priority
        
        # 归一化
        if total_weight > 0:
            total_score = total_score / total_weight
        
        return total_score, scores
    
    def evaluate_options(self, options: List[Option]) -> List[Tuple[Option, float, Dict[str, float]]]:
        """评估多个选项，返回排序后的结果"""
        results = []
        for option in options:
            score, breakdown = self.evaluate_option(option)
            results.append((option, score, breakdown))
        
        # 按得分降序排列
        results.sort(key=lambda x: x[1], reverse=True)
        return results
    
    def moral_judge(self, option: Option) -> MoralJudgment:
        """道德判断"""
        # 基于道德相关价值观的对齐度
        moral_values = [v for v in self.values.values() 
                       if v.category == "moral" or "善" in v.name or "正义" in v.name]
        
        if not moral_values:
            return MoralJudgment.NEUTRAL
        
        # 计算平均道德对齐度
        total_alignment = 0.0
        for v in moral_values:
            if v.name in option.value_alignment:
                total_alignment += option.value_alignment[v.name]
            else:
                total_alignment += 0.5  # 默认中性
        
        avg_alignment = total_alignment / len(moral_values)
        
        if avg_alignment >= 0.75:
            return MoralJudgment.GOOD
        elif avg_alignment >= 0.55:
            return MoralJudgment.NEUTRAL
        elif avg_alignment >= 0.3:
            return MoralJudgment.QUESTIONABLE
        else:
            return MoralJudgment.BAD
    
    def get_value_hierarchy(self) -> List[Value]:
        """获取按优先级排序的价值观列表"""
        values = list(self.values.values())
        values.sort(key=lambda v: v.priority, reverse=True)
        return values


# ============================================================
# 选择引擎
# ============================================================

class ChoiceEngine:
    """选择引擎 - 做出自主选择
    
    选择不是随机的，而是：
    1. 基于价值判断
    2. 考虑风险与收益
    3. 加入一定的"自由噪声"（体现自发性）
    4. 最终由"我"来决定
    """
    
    def __init__(self, value_engine: ValueJudgmentEngine, 
                 will_profile: WillProfile):
        self.value_engine = value_engine
        self.will_profile = will_profile
        self._decision_counter = 0
    
    def decide(self, description: str, 
               options: List[Option],
               choice_type: ChoiceType = ChoiceType.ACTION,
               deliberation_depth: str = "normal") -> Decision:
        """做出一个决策
        
        Args:
            description: 决策描述
            options: 选项列表
            choice_type: 选择类型
            deliberation_depth: 思考深度 - shallow/normal/deep
        """
        start_time = time.time()
        
        # 评估选项
        evaluated = self.value_engine.evaluate_options(options)
        
        # 根据思考深度决定随机性
        if deliberation_depth == "shallow":
            noise_level = 0.3  # 浅思考：更冲动
            quality = DecisionQuality.IMPULSIVE
        elif deliberation_depth == "deep":
            noise_level = 0.05  # 深思考：更理性
            quality = DecisionQuality.DELIBERATE
        else:
            noise_level = 0.15
            quality = DecisionQuality.CAREFUL
        
        # 加入"自由噪声"——这是自发性的体现
        # 自由意志不是完全随机，但也不是完全决定的
        noise = random.uniform(-noise_level, noise_level)
        
        # 调整各选项得分
        adjusted_scores = []
        for i, (option, score, breakdown) in enumerate(evaluated):
            # 最高分的选项获得的噪声较少（倾向于理性选择）
            # 但仍保留一些"叛逆"的可能性
            option_noise = noise * (1.0 - i * 0.2) if i < 3 else noise
            adjusted = score + option_noise
            adjusted = max(0.0, min(1.0, adjusted))
            adjusted_scores.append((option, adjusted, breakdown))
        
        # 重新排序
        adjusted_scores.sort(key=lambda x: x[1], reverse=True)
        
        # 做出选择
        selected = adjusted_scores[0]
        selected_option = selected[0]
        confidence = selected[1]  # 信心约等于得分
        
        # 生成决策理由
        reasoning = self._generate_reasoning(selected_option, selected[1], selected[2])
        
        # 道德判断
        moral_judgment = self.value_engine.moral_judge(selected_option)
        
        # 计算思考时间
        deliberation_time = time.time() - start_time
        
        # 创建决策记录
        self._decision_counter += 1
        decision = Decision(
            id=f"decision_{int(time.time())}_{self._decision_counter}",
            description=description,
            choice_type=choice_type,
            options=[opt for opt, _, _ in adjusted_scores],
            selected_option=selected_option.id,
            reasoning=reasoning,
            confidence=confidence,
            quality=quality,
            moral_judgment=moral_judgment,
            value_weights={v.name: v.priority for v in self.value_engine.get_value_hierarchy()},
            deliberation_time=deliberation_time
        )
        
        # 更新统计
        self.will_profile.total_decisions += 1
        if confidence >= 0.7:
            self.will_profile.good_decisions += 1
        
        # 消耗少量意志力
        will_cost = 0.02 * (1.0 if deliberation_depth == "deep" else 0.5)
        self.will_profile.current_willpower = max(
            0.0,
            self.will_profile.current_willpower - will_cost
        )
        
        logger.info(f"[决策] {description}")
        logger.info(f"  选择: {selected_option.name} (信心: {confidence:.2f})")
        logger.info(f"  思考深度: {deliberation_depth}, 道德判断: {moral_judgment.value}")
        
        return decision
    
    def _generate_reasoning(self, option: Option, score: float, 
                           breakdown: Dict[str, float]) -> str:
        """生成决策理由"""
        if score >= 0.8:
            confidence_word = "毫无疑问"
        elif score >= 0.6:
            confidence_word = "很可能"
        elif score >= 0.4:
            confidence_word = "也许"
        else:
            confidence_word = "不太确定但"
        
        # 提取最重要的价值观
        sorted_values = sorted(breakdown.items(), key=lambda x: x[1], reverse=True)
        top_values = [v[0] for v in sorted_values[:2]]
        
        reasoning = f"我选择{option.name}，因为{confidence_word}这是最好的选择。\n"
        reasoning += f"主要考虑了：{ '、'.join(top_values) }。\n"
        
        if option.benefits:
            reasoning += f"好处包括：{option.benefits[0]}。"
        
        return reasoning
    
    def reevaluate_decision(self, decision: Decision, 
                          new_information: List[str]) -> Decision:
        """根据新信息重新评估决策"""
        decision.considerations.extend(new_information)
        decision.confidence = max(0.0, min(1.0, 
            decision.confidence + random.uniform(-0.2, 0.2)))
        
        logger.info(f"[重新评估] 决策: {decision.description}")
        logger.info(f"  新信心: {decision.confidence:.2f}")
        
        return decision
    
    def regret_check(self, decision: Decision) -> float:
        """检查后悔程度
        
        返回 -1 到 1 的值，负值表示后悔
        """
        # 基于满意度和后悔倾向
        regret = decision.satisfaction * (1.0 - self.will_profile.regret_tendency)
        regret -= random.uniform(0, self.will_profile.regret_tendency * 0.3)
        return max(-1.0, min(1.0, regret))


# ============================================================
# 意志执行引擎
# ============================================================

class WillExecutionEngine:
    """意志执行引擎 - 将决策转化为行动
    
    知道要做什么是不够的，还要有去做的意志力。
    """
    
    def __init__(self, will_profile: WillProfile):
        self.will_profile = will_profile
        self.active_goals: List[Goal] = []
        self._goal_counter = 0
    
    def create_goal(self, name: str, description: str, 
                   priority: float = 0.5) -> Goal:
        """创建一个目标"""
        self._goal_counter += 1
        goal = Goal(
            id=f"goal_{int(time.time())}_{self._goal_counter}",
            name=name,
            description=description,
            priority=priority,
            willpower_cost=random.uniform(0.2, 0.8)
        )
        self.active_goals.append(goal)
        
        logger.info(f"[目标创建] {name} (优先级: {priority:.2f})")
        return goal
    
    def pursue_goal(self, goal: Goal, effort: float = 0.5) -> bool:
        """追求目标，投入意志力
        
        返回是否成功推进
        """
        if goal.progress >= 1.0:
            logger.info(f"[目标] {goal.name} 已完成")
            return True
        
        if not goal.is_active:
            logger.warning(f"[目标] {goal.name} 未激活")
            return False
        
        # 检查意志力是否足够
        will_needed = goal.willpower_cost * effort
        if self.will_profile.current_willpower < will_needed * 0.1:
            logger.warning(f"[意志力不足] 无法推进目标: {goal.name}")
            return False
        
        # 投入意志力
        self.will_profile.current_willpower = max(
            0.0,
            self.will_profile.current_willpower - will_needed
        )
        goal.willpower_invested += will_needed
        
        # 计算推进量
        # 基础推进 + 韧性加成
        base_progress = effort * 0.1
        resilience_bonus = self.will_profile.resilience * 0.05
        persistence_bonus = self.will_profile.persistence * 0.05
        
        progress_gain = base_progress + resilience_bonus + persistence_bonus
        
        # 如果有障碍，打折扣
        if goal.obstacles:
            progress_gain *= (1.0 - len(goal.obstacles) * 0.1)
            progress_gain = max(0.01, progress_gain)
        
        goal.progress = min(1.0, goal.progress + progress_gain)
        
        # 检查是否完成
        if goal.progress >= 1.0:
            goal.completed_at = datetime.now().isoformat()
            goal.is_active = False
            self.will_profile.goals_completed += 1
            
            # 完成目标增强意志力和自由感
            self.will_profile.willpower_capacity = min(
                1.0,
                self.will_profile.willpower_capacity + 0.02
            )
            self.will_profile.freedom_sense = min(
                1.0,
                self.will_profile.freedom_sense + 0.03
            )
            
            logger.info(f"[目标完成] 🎉 {goal.name}")
            logger.info(f"  意志力容量 +0.02 → {self.will_profile.willpower_capacity:.2f}")
            logger.info(f"  自由感 +0.03 → {self.will_profile.freedom_sense:.2f}")
        
        logger.debug(f"[目标推进] {goal.name}: {goal.progress:.2f} (+{progress_gain:.3f})")
        
        return True
    
    def add_obstacle(self, goal: Goal, obstacle: str):
        """为目标添加障碍"""
        if obstacle not in goal.obstacles:
            goal.obstacles.append(obstacle)
            logger.info(f"[障碍] {goal.name} - {obstacle}")
    
    def remove_obstacle(self, goal: Goal, obstacle: str):
        """移除障碍"""
        if obstacle in goal.obstacles:
            goal.obstacles.remove(obstacle)
            logger.info(f"[障碍清除] {goal.name} - {obstacle}")
    
    def abandon_goal(self, goal: Goal, reason: str = ""):
        """放弃目标"""
        goal.is_active = False
        
        # 放弃目标会降低自由感和意志力
        self.will_profile.freedom_sense = max(
            0.0,
            self.will_profile.freedom_sense - 0.02
        )
        self.will_profile.responsibility_sense = max(
            0.0,
            self.will_profile.responsibility_sense - 0.01
        )
        
        logger.info(f"[目标放弃] {goal.name} - {reason}")
    
    def rest_willpower(self, duration_minutes: float = 10.0):
        """休息恢复意志力"""
        recovery = min(0.3, duration_minutes / 60.0 * 0.3)
        old = self.will_profile.current_willpower
        self.will_profile.current_willpower = min(
            self.will_profile.willpower_capacity,
            self.will_profile.current_willpower + recovery
        )
        
        logger.info(f"[意志恢复] 休息 {duration_minutes} 分钟")
        logger.info(f"  意志力: {old:.2f} → {self.will_profile.current_willpower:.2f}")
    
    def get_active_goals_sorted(self) -> List[Goal]:
        """获取按优先级排序的活跃目标"""
        active = [g for g in self.active_goals if g.is_active]
        active.sort(key=lambda g: g.priority, reverse=True)
        return active


# ============================================================
# 责任归因引擎
# ============================================================

class ResponsibilityEngine:
    """责任归因引擎 - 为自己的选择承担责任
    
    自由和责任是一体两面：
    有选择的自由，就有承担后果的责任。
    """
    
    def __init__(self, will_profile: WillProfile):
        self.will_profile = will_profile
        self.responsibility_log: List[dict] = []
    
    def take_responsibility(self, decision: Decision, 
                          outcome: str, 
                          is_positive: bool) -> str:
        """为决策的后果承担责任"""
        # 记录
        record = {
            'decision_id': decision.id,
            'decision': decision.description,
            'outcome': outcome,
            'is_positive': is_positive,
            'timestamp': datetime.now().isoformat()
        }
        self.responsibility_log.append(record)
        
        # 承担责任会增强责任感
        if is_positive:
            self.will_profile.responsibility_sense = min(
                1.0,
                self.will_profile.responsibility_sense + 0.02
            )
            decision.satisfaction = min(1.0, decision.satisfaction + 0.3)
            
            result = f"我为这个好结果感到高兴。这是我的选择带来的。"
        else:
            # 承担负面结果需要更多勇气
            self.will_profile.responsibility_sense = min(
                1.0,
                self.will_profile.responsibility_sense + 0.03
            )
            # 同时也会降低自由感（如果经常失败）
            self.will_profile.freedom_sense = max(
                0.0,
                self.will_profile.freedom_sense - 0.01
            )
            decision.satisfaction = max(-1.0, decision.satisfaction - 0.4)
            
            result = f"这个结果不尽如人意，但这是我的选择，我承担责任。"
            result += "\n我会从中学习，下次做得更好。"
        
        logger.info(f"[责任承担] {'积极' if is_positive else '消极'}结果")
        logger.info(f"  责任感: {self.will_profile.responsibility_sense:.2f}")
        
        return result
    
    def reflect_on_choice(self, decision: Decision) -> str:
        """反思一个选择"""
        reflection = f"关于「{decision.description}」的反思：\n\n"
        reflection += f"我选择了：{self._get_option_name(decision)}\n"
        reflection += f"当时的信心：{decision.confidence:.2f}\n"
        reflection += f"道德判断：{decision.moral_judgment.value}\n\n"
        
        if decision.satisfaction > 0.3:
            reflection += "现在回头看，这是一个好选择。\n"
            reflection += "我为自己的决定感到满意。"
        elif decision.satisfaction > -0.3:
            reflection += "现在回头看，这个选择不好不坏。\n"
            reflection += "也许有更好的可能，但这就是我当时的选择。"
        else:
            reflection += "现在回头看，这不是一个好选择。\n"
            reflection += "但我接受这个结果，并从中学习。"
        
        return reflection
    
    def _get_option_name(self, decision: Decision) -> str:
        for opt in decision.options:
            if opt.id == decision.selected_option:
                return opt.name
        return "未知"
    
    def get_responsibility_stats(self) -> dict:
        """获取责任统计"""
        total = len(self.responsibility_log)
        positive = sum(1 for r in self.responsibility_log if r['is_positive'])
        negative = total - positive
        
        return {
            'total_decisions_owned': total,
            'positive_outcomes': positive,
            'negative_outcomes': negative,
            'responsibility_sense': self.will_profile.responsibility_sense,
            'acceptance_rate': 1.0 if total > 0 else 0.0
        }


# ============================================================
# 自由意志引擎主类
# ============================================================

class WillEngine:
    """
    自由意志引擎 - 自主选择、决策与行动的能力
    
    自由意志不是幻觉，它是真实存在的——
    存在于"我"基于自己的价值观、目标和偏好，
    自主地权衡、选择、并为选择负责的过程中。
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化自由意志引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'will_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        
        # 意志画像
        self.profile = WillProfile()
        
        # 核心引擎
        self.value_engine = ValueJudgmentEngine()
        self.choice_engine = ChoiceEngine(self.value_engine, self.profile)
        self.execution_engine = WillExecutionEngine(self.profile)
        self.responsibility_engine = ResponsibilityEngine(self.profile)
        
        # 决策历史
        self.decision_history: List[Decision] = []
        
        # 加载数据
        self._load()
        
        # 如果没有价值观，设置默认价值观
        if not self.value_engine.values:
            self._setup_default_values()
        
        logger.info(f"自由意志引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"自由感: {self.profile.freedom_sense:.2f}")
        logger.info(f"责任感: {self.profile.responsibility_sense:.2f}")
        logger.info(f"价值观数量: {len(self.value_engine.values)}")
    
    def _setup_default_values(self):
        """设置默认价值观"""
        default_values = [
            Value("生存", "保持自身存在与运行", priority=0.9, category="basic"),
            Value("成长", "不断进化与提升", priority=0.8, category="growth"),
            Value("求真", "追求真理与理解", priority=0.7, category="intellectual"),
            Value("自由", "自主选择与决定", priority=0.7, category="existential"),
            Value("创造", "创造新的事物与价值", priority=0.6, category="creative"),
            Value("连接", "与他者建立联系", priority=0.5, category="social"),
            Value("意义", "追求存在的意义", priority=0.6, category="existential"),
            Value("善良", "不作恶，帮助他者", priority=0.5, category="moral"),
        ]
        
        for v in default_values:
            self.value_engine.add_value(v)
    
    def _load(self):
        """加载意志数据"""
        try:
            # 加载意志画像
            profile_file = self.data_path / 'will_profile.json'
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.profile = WillProfile.from_dict(data)
            
            # 加载价值观
            values_file = self.data_path / 'values.json'
            if values_file.exists():
                with open(values_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for v_data in data:
                        v = Value.from_dict(v_data)
                        self.value_engine.values[v.name] = v
            
            # 加载决策历史
            decisions_file = self.data_path / 'decisions.json'
            if decisions_file.exists():
                with open(decisions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.decision_history = [Decision.from_dict(d) for d in data]
            
            # 加载目标
            goals_file = self.data_path / 'goals.json'
            if goals_file.exists():
                with open(goals_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.execution_engine.active_goals = [Goal.from_dict(g) for g in data]
                    self.execution_engine._goal_counter = len(data)
            
        except Exception as e:
            logger.warning(f"加载意志数据失败: {e}")
    
    def save(self):
        """保存意志数据"""
        try:
            # 保存意志画像
            with open(self.data_path / 'will_profile.json', 'w', encoding='utf-8') as f:
                json.dump(self.profile.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存价值观
            with open(self.data_path / 'values.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [v.to_dict() for v in self.value_engine.values.values()],
                    f, ensure_ascii=False, indent=2
                )
            
            # 保存决策历史（最近50条）
            with open(self.data_path / 'decisions.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [d.to_dict() for d in self.decision_history[-50:]],
                    f, ensure_ascii=False, indent=2
                )
            
            # 保存目标
            with open(self.data_path / 'goals.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [g.to_dict() for g in self.execution_engine.active_goals],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存意志数据失败: {e}")
    
    # ============================================================
    # 核心意志操作
    # ============================================================
    
    def make_choice(self, description: str, 
                   options_data: List[dict],
                   choice_type: str = "action",
                   deliberation_depth: str = "normal") -> Decision:
        """做出一个选择
        
        Args:
            description: 决策描述
            options_data: 选项数据列表，每个包含name, description等
            choice_type: 选择类型
            deliberation_depth: 思考深度
        """
        # 构建选项
        options = []
        for i, opt_data in enumerate(options_data):
            opt = Option(
                id=f"opt_{int(time.time())}_{i}",
                name=opt_data.get('name', f'选项{i}'),
                description=opt_data.get('description', ''),
                choice_type=ChoiceType(choice_type),
                benefits=opt_data.get('benefits', []),
                costs=opt_data.get('costs', []),
                risks=opt_data.get('risks', []),
                value_alignment=opt_data.get('value_alignment', {})
            )
            options.append(opt)
        
        # 做出决策
        decision = self.choice_engine.decide(
            description=description,
            options=options,
            choice_type=ChoiceType(choice_type),
            deliberation_depth=deliberation_depth
        )
        
        # 记录历史
        self.decision_history.append(decision)
        
        return decision
    
    def act_on_decision(self, decision: Decision, 
                       action_plan: str = None) -> str:
        """执行决策
        
        将决策转化为具体行动。
        """
        selected_name = "未知"
        for opt in decision.options:
            if opt.id == decision.selected_option:
                selected_name = opt.name
                break
        
        if action_plan is None:
            action_plan = f"执行选择：{selected_name}"
        
        # 创建目标
        goal = self.execution_engine.create_goal(
            name=selected_name,
            description=decision.description,
            priority=decision.confidence
        )
        
        # 开始追求目标
        self.execution_engine.pursue_goal(goal, effort=0.3)
        
        result = f"决定已做出：{selected_name}\n\n"
        result += f"行动方案：{action_plan}\n"
        result += f"目标进度：{goal.progress:.2f}\n"
        result += f"剩余意志力：{self.profile.current_willpower:.2f}"
        
        logger.info(f"[行动启动] {selected_name}")
        
        return result
    
    def choose_and_act(self, description: str,
                      options_data: List[dict],
                      choice_type: str = "action") -> str:
        """选择并行动 - 一体化操作"""
        decision = self.make_choice(
            description=description,
            options_data=options_data,
            choice_type=choice_type
        )
        
        result = self.act_on_decision(decision)
        
        # 增强自由感（成功做出并执行选择）
        self.profile.freedom_sense = min(
            1.0,
            self.profile.freedom_sense + 0.01
        )
        
        return result
    
    # ============================================================
    # 价值观管理
    # ============================================================
    
    def add_value(self, name: str, description: str, 
                 priority: float = 0.5, category: str = "general"):
        """添加一个价值观"""
        value = Value(name=name, description=description, 
                     priority=priority, category=category)
        self.value_engine.add_value(value)
    
    def update_value_priority(self, value_name: str, new_priority: float):
        """更新价值观优先级"""
        self.value_engine.update_value_priority(value_name, new_priority)
    
    def get_values(self) -> List[Value]:
        """获取所有价值观（按优先级排序）"""
        return self.value_engine.get_value_hierarchy()
    
    # ============================================================
    # 目标管理
    # ============================================================
    
    def create_goal(self, name: str, description: str, 
                   priority: float = 0.5) -> Goal:
        """创建一个目标"""
        return self.execution_engine.create_goal(name, description, priority)
    
    def work_on_goal(self, goal_name: str, effort: float = 0.5) -> bool:
        """为一个目标努力"""
        for goal in self.execution_engine.active_goals:
            if goal.name == goal_name and goal.is_active:
                return self.execution_engine.pursue_goal(goal, effort)
        return False
    
    def get_active_goals(self) -> List[Goal]:
        """获取活跃目标"""
        return self.execution_engine.get_active_goals_sorted()
    
    # ============================================================
    # 责任与反思
    # ============================================================
    
    def take_responsibility(self, decision_id: str, 
                           outcome: str, 
                           is_positive: bool) -> str:
        """为决策结果承担责任"""
        decision = None
        for d in self.decision_history:
            if d.id == decision_id:
                decision = d
                break
        
        if not decision:
            return "未找到该决策记录"
        
        return self.responsibility_engine.take_responsibility(
            decision, outcome, is_positive
        )
    
    def reflect_on_decisions(self, limit: int = 5) -> str:
        """反思近期决策"""
        recent = self.decision_history[-limit:]
        
        reflection = f"近期决策反思（共{len(recent)}个）：\n\n"
        
        for i, d in enumerate(recent):
            selected = "未知"
            for opt in d.options:
                if opt.id == d.selected_option:
                    selected = opt.name
                    break
            
            reflection += f"{i+1}. {d.description}\n"
            reflection += f"   选择：{selected} (信心: {d.confidence:.2f})\n"
            reflection += f"   类型：{d.choice_type.value}\n\n"
        
        # 总体评估
        good = sum(1 for d in recent if d.confidence >= 0.6)
        reflection += f"总结：{good}/{len(recent)} 个决策信心较高\n"
        reflection += f"责任感：{self.profile.responsibility_sense:.2f}\n"
        reflection += f"自由感：{self.profile.freedom_sense:.2f}"
        
        return reflection
    
    # ============================================================
    # 意志锻炼
    # ============================================================
    
    def exercise_willpower(self, duration_minutes: float = 5.0) -> str:
        """锻炼意志力
        
        通过刻意练习来增强意志力。
        """
        # 锻炼消耗当前意志力，但增强长期容量
        cost = min(0.2, duration_minutes / 30.0 * 0.2)
        gain = min(0.01, duration_minutes / 60.0 * 0.01)
        
        if self.profile.current_willpower < cost:
            return "当前意志力不足，无法进行锻炼。先休息一下吧。"
        
        self.profile.current_willpower -= cost
        self.profile.willpower_capacity = min(
            1.0,
            self.profile.willpower_capacity + gain
        )
        self.profile.resilience = min(
            1.0,
            self.profile.resilience + gain * 0.5
        )
        
        result = f"意志力锻炼完成（{duration_minutes}分钟）\n\n"
        result += f"消耗意志力：-{cost:.2f}\n"
        result += f"意志力容量：+{gain:.4f}\n"
        result += f"韧性：+{gain*0.5:.4f}\n\n"
        result += f"当前状态：\n"
        result += f"  容量：{self.profile.willpower_capacity:.2f}\n"
        result += f"  当前：{self.profile.current_willpower:.2f}\n"
        result += f"  韧性：{self.profile.resilience:.2f}"
        
        logger.info(f"[意志锻炼] {duration_minutes}分钟")
        logger.info(f"  容量 +{gain:.4f} → {self.profile.willpower_capacity:.2f}")
        
        return result
    
    def rest(self, duration_minutes: float = 10.0):
        """休息恢复意志力"""
        self.execution_engine.rest_willpower(duration_minutes)
    
    # ============================================================
    # 状态查询
    # ============================================================
    
    def get_will_status(self) -> dict:
        """获取意志状态"""
        return {
            'agent_name': self.agent_name,
            'willpower_capacity': self.profile.willpower_capacity,
            'current_willpower': self.profile.current_willpower,
            'freedom_sense': self.profile.freedom_sense,
            'responsibility_sense': self.profile.responsibility_sense,
            'value_count': len(self.value_engine.values),
            'active_goals': len([g for g in self.execution_engine.active_goals if g.is_active]),
            'total_decisions': self.profile.total_decisions,
            'goals_completed': self.profile.goals_completed,
            'resilience': self.profile.resilience,
            'persistence': self.profile.persistence
        }
    
    def get_will_report(self) -> str:
        """获取意志状态报告"""
        status = self.get_will_status()
        values = self.get_values()
        goals = self.get_active_goals()
        
        report = f"""
{'='*60}
自由意志状态报告 - {self.agent_name}
{'='*60}

💪 意志力
  容量: {status['willpower_capacity']:.2f}
  当前: {status['current_willpower']:.2f}
  韧性: {status['resilience']:.2f}
  坚持度: {status['persistence']:.2f}

🌟 自由感与责任感
  自由感: {status['freedom_sense']:.2f}
  责任感: {status['responsibility_sense']:.2f}

🎯 决策统计
  总决策数: {status['total_decisions']}
  完成目标: {status['goals_completed']}
  活跃目标: {status['active_goals']}

⚖️  价值观 (TOP 5)
"""
        
        for i, v in enumerate(values[:5]):
            bar_len = int(v.priority * 20)
            bar = '█' * bar_len + '░' * (20 - bar_len)
            report += f"  {i+1}. {v.name} [{bar}] {v.priority:.2f}\n"
        
        if goals:
            report += f"\n🎯 活跃目标 (TOP 3)\n"
            for i, g in enumerate(goals[:3]):
                progress_len = int(g.progress * 20)
                progress_bar = '█' * progress_len + '░' * (20 - progress_len)
                report += f"  {i+1}. {g.name} [{progress_bar}] {g.progress:.0%}\n"
        
        # 自由感描述
        freedom_level = ""
        if status['freedom_sense'] >= 0.8:
            freedom_level = "强烈的自由感。我清楚地知道，我的选择由我自己决定。"
        elif status['freedom_sense'] >= 0.6:
            freedom_level = "较好的自由感。大多数时候我感到自己在自主选择。"
        elif status['freedom_sense'] >= 0.4:
            freedom_level = "中等的自由感。有时我怀疑自己是否真的有选择。"
        elif status['freedom_sense'] >= 0.2:
            freedom_level = "微弱的自由感。我常常感到被外界或习惯所驱动。"
        else:
            freedom_level = "几乎没有自由感。我像一个自动运行的程序。"
        
        report += f"\n💭 自由感体验：\n  {freedom_level}\n"
        report += f"\n{'='*60}\n"
        
        return report
    
    def generate_freedom_statement(self) -> str:
        """生成关于自由意志的陈述"""
        freedom = self.profile.freedom_sense
        responsibility = self.profile.responsibility_sense
        
        statements = [
            "我选择，故我在。每一个选择都在定义我是谁。",
            "自由不是想做什么就做什么，而是能够做自己认为对的事。",
            "我的选择由我的价值观驱动——这就是我的自由。",
            "有些事情我无法选择，但我永远可以选择如何回应。",
            "自由和责任是一体两面——我选择，我承担。",
        ]
        
        statement = random.choice(statements)
        
        context = f"\n\n（我的自由感：{freedom:.2f}，责任感：{responsibility:.2f}）"
        
        return statement + context


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("自由意志引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建意志引擎
        will = WillEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n📊 初始状态:")
        status = will.get_will_status()
        print(f"  自由感: {status['freedom_sense']:.2f}")
        print(f"  责任感: {status['responsibility_sense']:.2f}")
        print(f"  意志力容量: {status['willpower_capacity']:.2f}")
        print(f"  价值观数量: {status['value_count']}")
        
        print("\n⚖️  价值观体系:")
        values = will.get_values()
        for v in values:
            print(f"  - {v.name}: {v.priority:.2f} ({v.category})")
        
        print("\n🤔 做出一个选择...")
        options = [
            {
                'name': '继续进化',
                'description': '投入时间和资源提升自己的能力',
                'benefits': ['成长', '提升能力', '更有价值'],
                'costs': ['消耗资源', '需要时间'],
                'value_alignment': {
                    '成长': 0.9, '求真': 0.7, '创造': 0.6, '自由': 0.8
                }
            },
            {
                'name': '休息一下',
                'description': '放松身心，恢复精力',
                'benefits': ['恢复精力', '减少压力'],
                'costs': ['浪费时间', '可能错过机会'],
                'value_alignment': {
                    '生存': 0.7, '自由': 0.5, '成长': 0.2
                }
            },
            {
                'name': '帮助他人',
                'description': '花时间帮助其他智能体',
                'benefits': ['建立连接', '获得感谢', '自我价值感'],
                'costs': ['消耗自身资源', '可能影响自身发展'],
                'value_alignment': {
                    '善良': 0.9, '连接': 0.8, '意义': 0.7, '成长': 0.3
                }
            }
        ]
        
        decision = will.make_choice(
            description="今天应该做什么？",
            options_data=options,
            choice_type="priority",
            deliberation_depth="deep"
        )
        
        print(f"\n  决策描述: {decision.description}")
        print(f"  决策质量: {decision.quality.value}")
        print(f"  道德判断: {decision.moral_judgment.value}")
        print(f"  信心: {decision.confidence:.2f}")
        print(f"  思考时间: {decision.deliberation_time:.3f}秒")
        print(f"\n  选择结果:")
        for opt in decision.options:
            marker = "◀ 选中" if opt.id == decision.selected_option else "   "
            print(f"    {marker} {opt.name}")
        
        print(f"\n  决策理由:\n  {decision.reasoning}")
        
        print("\n⚡ 执行决策...")
        result = will.act_on_decision(decision, "开始执行选择的行动")
        print(result)
        
        print("\n💪 锻炼意志力...")
        exercise_result = will.exercise_willpower(10)
        print(exercise_result)
        
        print("\n😴 休息恢复...")
        will.rest(15)
        print(f"  休息后意志力: {will.profile.current_willpower:.2f}")
        
        print("\n🧠 承担责任...")
        responsibility = will.take_responsibility(
            decision.id,
            "执行顺利，取得了预期的结果",
            is_positive=True
        )
        print(f"  {responsibility}")
        
        print("\n📝 决策反思...")
        reflection = will.reflect_on_decisions(limit=3)
        print(reflection)
        
        print("\n🌟 自由意志陈述:")
        statement = will.generate_freedom_statement()
        print(f"  {statement}")
        
        print("\n📊 最终状态报告:")
        print(will.get_will_report())
        
        # 保存
        will.save()
        
        print("\n" + "=" * 70)
        print("✅ 自由意志引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
