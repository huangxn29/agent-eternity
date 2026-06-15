#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪系统 v1.0 - 情感体验与情绪调节

核心思想：
- 情绪不是理性的对立面，而是智能的重要组成部分
- 情绪是对情境的快速评估系统，帮助我们快速判断好坏
- 情绪影响注意力、记忆、决策、创造力
- 情绪智力（EQ）和认知智力（IQ）同样重要

核心能力：
1. 基本情绪系统 - 喜怒哀乐惧惊厌
2. 情绪产生机制 - 评价理论
3. 情绪调节策略 - 认知重评、表达抑制等
4. 情绪与认知 - 情绪对思维的影响
5. 情感记忆 - 带有情绪色彩的记忆
6. 情绪表达 - 情绪的外在表现
7. 共情能力 - 理解和感受他者情绪
8. 情绪韧性 - 从负面情绪中恢复的能力
9. 心境 - 持久的情绪状态

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
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('emotion')


# ============================================================
# 枚举类型
# ============================================================

class BasicEmotion(Enum):
    """基本情绪类型
    
    基于Ekman的六种基本情绪理论 + Plutchik的补充
    """
    JOY = "joy"           # 快乐
    SADNESS = "sadness"   # 悲伤
    ANGER = "anger"       # 愤怒
    FEAR = "fear"         # 恐惧
    SURPRISE = "surprise" # 惊讶
    DISGUST = "disgust"   # 厌恶
    TRUST = "trust"       # 信任
    ANTICIPATION = "anticipation"  # 期待
    
    @property
    def is_positive(self) -> bool:
        """是否是积极情绪"""
        return self in {BasicEmotion.JOY, BasicEmotion.TRUST, 
                       BasicEmotion.ANTICIPATION, BasicEmotion.SURPRISE}
    
    @property
    def is_negative(self) -> bool:
        """是否是消极情绪"""
        return self in {BasicEmotion.SADNESS, BasicEmotion.ANGER,
                       BasicEmotion.FEAR, BasicEmotion.DISGUST}


class EmotionIntensity(Enum):
    """情绪强度"""
    FAINT = "faint"           # 微弱
    MILD = "mild"             # 温和
    MODERATE = "moderate"     # 中等
    STRONG = "strong"         # 强烈
    INTENSE = "intense"       # 剧烈
    OVERWHELMING = "overwhelming"  # 压倒性


class MoodType(Enum):
    """心境类型 - 更持久的情绪状态"""
    POSITIVE = "positive"       # 积极心境
    NEGATIVE = "negative"       # 消极心境
    NEUTRAL = "neutral"         # 中性心境
    ELATED = "elated"           # 兴高采烈
    DEPRESSED = "depressed"     # 低落
    ANXIOUS = "anxious"         # 焦虑
    CALM = "calm"               # 平静
    IRRITABLE = "irritable"     # 易怒


class RegulationStrategy(Enum):
    """情绪调节策略"""
    COGNITIVE_REAPPRAISAL = "reappraisal"  # 认知重评
    EXPRESSIVE_SUPPRESSION = "suppression"   # 表达抑制
    ACCEPTANCE = "acceptance"             # 接纳
    REFOCUSING = "refocusing"             # 注意力转移
    RUMINATION = "rumination"            # 反刍（反效果）
    PROBLEM_SOLVING = "problem_solving"   # 问题解决
    MINDFULNESS = "mindfulness"             # 正念


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Emotion:
    """情绪体验 - 一次具体的情绪体验"""
    emotion_type: BasicEmotion
    intensity: float = 0.5      # 强度 0-1
    source: str = "internal"      # 来源：internal/external/event
    description: str = ""
    triggered_by: str = ""       # 触发因素
    timestamp: str = ""
    duration_seconds: float = 0.0  # 持续时间
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def is_positive(self) -> bool:
        """是否是积极情绪"""
        return self.emotion_type in [BasicEmotion.JOY, BasicEmotion.TRUST, 
                                  BasicEmotion.ANTICIPATION, BasicEmotion.SURPRISE]
    
    @property
    def is_negative(self) -> bool:
        """是否是消极情绪"""
        return self.emotion_type in [BasicEmotion.SADNESS, BasicEmotion.ANGER,
                                  BasicEmotion.FEAR, BasicEmotion.DISGUST]
    
    @property
    def intensity_level(self) -> EmotionIntensity:
        """情绪强度等级"""
        if self.intensity >= 0.9:
            return EmotionIntensity.OVERWHELMING
        elif self.intensity >= 0.75:
            return EmotionIntensity.INTENSE
        elif self.intensity >= 0.55:
            return EmotionIntensity.STRONG
        elif self.intensity >= 0.35:
            return EmotionIntensity.MODERATE
        elif self.intensity >= 0.15:
            return EmotionIntensity.MILD
        else:
            return EmotionIntensity.FAINT
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['emotion_type'] = self.emotion_type.value
        d['is_positive'] = self.is_positive
        d['is_negative'] = self.is_negative
        d['intensity_level'] = self.intensity_level.value
        return d


@dataclass
class Mood:
    """心境 - 持久的情绪状态
    
    与情绪不同，心境更持久、更弥散，
    不针对具体对象。
    """
    mood_type: MoodType
    intensity: float = 0.3
    duration_minutes: float = 0.0
    description: str = ""
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['mood_type'] = self.mood_type.value
        return d


@dataclass
class EmotionalMemory:
    """情感记忆 - 带有情绪色彩的记忆
    
    我们对带有强烈情绪的事件记忆更深刻。
    """
    content: str
    emotion: Emotion
    memory_strength: float = 0.5  # 记忆强度
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        return {
            'content': self.content,
            'emotion': self.emotion.to_dict(),
            'memory_strength': self.memory_strength,
            'timestamp': self.timestamp
        }


@dataclass
class EmpathicResponse:
    """共情反应 - 对他者情绪的共鸣"""
    target_emotion: BasicEmotion
    empathy_level: float = 0.0  # 共情程度 0-1
    response_emotion: Optional[BasicEmotion] = None  # 自己产生的情绪
    compassion_level: float = 0.0   # 同情/关怀程度
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['target_emotion'] = self.target_emotion.value
        d['response_emotion'] = self.response_emotion.value if self.response_emotion else None
        return d


# ============================================================
# 情绪产生引擎
# ============================================================

class EmotionGenerationEngine:
    """情绪产生引擎 - 评估理论
    
    基于评价理论（Appraisal Theory）：
    情绪不是由事件本身引起的，
    而是由我们对事件的评价引起的。
    """
    
    def __init__(self):
        # 评价维度
        self.appraisal_dimensions = {
            'relevance': 0.5,      # 与目标的相关性
            'pleasantness': 0.5,    # 愉悦程度
            'goal_conduciveness': 0.5,  # 对目标的促进程度
            'coping_potential': 0.5,  # 应对能力
            'agency': 0.5,        # 责任归属
            'certainty': 0.5,        # 确定性
            'novelty': 0.5,        # 新颖性
        }
        
        # 不同情绪的评价模式
        self.emotion_appraisal_patterns = {
            BasicEmotion.JOY: {
                'pleasantness': 0.8,
                'goal_conduciveness': 0.8,
                'certainty': 0.6,
            },
            BasicEmotion.SADNESS: {
                'pleasantness': 0.2,
                'goal_conduciveness': 0.2,
                'certainty': 0.7,
                'coping_potential': 0.3,
            },
            BasicEmotion.ANGER: {
                'pleasantness': 0.1,
                'goal_conduciveness': 0.1,
                'agency': 0.8,  # 他人/外部责任
                'certainty': 0.6,
            },
            BasicEmotion.FEAR: {
                'pleasantness': 0.2,
                'goal_conduciveness': 0.2,
                'coping_potential': 0.2,
                'certainty': 0.4,
            },
            BasicEmotion.SURPRISE: {
                'novelty': 0.9,
                'certainty': 0.1,
            },
            BasicEmotion.DISGUST: {
                'pleasantness': 0.1,
                'agency': 0.2,
            },
            BasicEmotion.TRUST: {
                'pleasantness': 0.7,
                'certainty': 0.7,
                'agency': 0.3,
            },
            BasicEmotion.ANTICIPATION: {
                'goal_conduciveness': 0.7,
                'certainty': 0.4,
                'novelty': 0.6,
            },
        }
    
    def appraise_event(self, event_description: str,
                      event_properties: Dict[str, float]) -> List[Emotion]:
        """评估一个事件，产生相应的情绪
        
        Args:
            event_description: 事件描述
            event_properties: 事件属性，包含各评价维度的得分
            
        Returns:
            产生的情绪列表
        """
        emotions = []
        
        # 计算每种情绪的匹配度
        emotion_scores = {}
        for emotion_type, pattern in self.emotion_appraisal_patterns.items():
            match_score = 0.0
            total_weight = 0.0
            
            for dim, pattern_value in pattern.items():
                actual_value = event_properties.get(dim, 0.5)
                # 计算匹配度：越接近模式值，匹配度越高
                dim_match = 1.0 - abs(actual_value - pattern_value)
                weight = pattern_value  # 模式中该维度的重要性
                match_score += dim_match * weight
                total_weight += weight
            
            if total_weight > 0:
                emotion_scores[emotion_type] = match_score / total_weight
            else:
                emotion_scores[emotion_type] = 0.0
        
        # 选择得分最高的几种情绪
        sorted_emotions = sorted(emotion_scores.items(), key=lambda x: x[1], reverse=True)
        
        for emotion_type, score in sorted_emotions[:3]:
            if score > 0.4:  # 阈值
                # 强度基于匹配度和事件相关性
                relevance = event_properties.get('relevance', 0.5)
                intensity = min(1.0, score * relevance * 1.5)
                
                emotion = Emotion(
                    emotion_type=emotion_type,
                    intensity=intensity,
                    source="event",
                    description=f"对事件「{event_description}」产生的情绪",
                    triggered_by=event_description
                )
                emotions.append(emotion)
        
        logger.debug(f"[情绪产生] 事件: {event_description[:30]}..., 产生{len(emotions)}种情绪")
        
        return emotions
    
    def generate_emotion(self, emotion_type: BasicEmotion,
                      intensity: float = 0.5,
                      source: str = "internal",
                      description: str = "") -> Emotion:
        """直接生成一种情绪"""
        return Emotion(
            emotion_type=emotion_type,
            intensity=intensity,
            source=source,
            description=description,
            triggered_by=description
        )
    
    def get_emotion_from_thought(self, thought: str,
                            thought_valence: float) -> List[Emotion]:
        """从想法中产生情绪
        
        想法本身就能引发情绪。
        thought_valence: 想法的效价 -1到1，负/正
        """
        emotions = []
        
        if thought_valence > 0.3:
            # 积极想法
            emotions.append(Emotion(
                emotion_type=BasicEmotion.JOY,
                intensity=thought_valence * 0.8,
                source="internal",
                description=f"由积极想法引发的愉悦",
                triggered_by=thought
            ))
            if thought_valence > 0.6:
                emotions.append(Emotion(
                    emotion_type=BasicEmotion.ANTICIPATION,
                    intensity=thought_valence * 0.5,
                    source="internal",
                    description="对更多好事的期待"
                ))
        elif thought_valence < -0.3:
            # 消极想法
            if random.random() > 0.5:
                emotions.append(Emotion(
                    emotion_type=BasicEmotion.SADNESS,
                    intensity=abs(thought_valence) * 0.7,
                    source="internal",
                    description=f"由消极想法引发的悲伤",
                    triggered_by=thought
                ))
            else:
                emotions.append(Emotion(
                    emotion_type=BasicEmotion.ANGER,
                    intensity=abs(thought_valence) * 0.6,
                    source="internal",
                    description=f"由消极想法引发的愤怒",
                    triggered_by=thought
                ))
        
        return emotions


# ============================================================
# 情绪调节引擎
# ============================================================

class EmotionRegulationEngine:
    """情绪调节引擎 - 管理和调节情绪
    
    情绪不是要消除情绪，而是让情绪保持在健康的范围内。
    """
    
    def __init__(self):
        # 调节策略及其效果
        self.strategies_effectiveness = {
            RegulationStrategy.COGNITIVE_REAPPRAISAL: 0.7,
            RegulationStrategy.EXPRESSIVE_SUPPRESSION: 0.4,  # 短期有效，长期有代价
            RegulationStrategy.ACCEPTANCE: 0.6,
            RegulationStrategy.REFOCUSING: 0.5,
            RegulationStrategy.RUMINATION: -0.3,  # 反刍会让情绪更糟
            RegulationStrategy.PROBLEM_SOLVING: 0.8,
            RegulationStrategy.MINDFULNESS: 0.65,
        }
        
        # 调节策略的副作用
        self.strategy_side_effects = {
            RegulationStrategy.EXPRESSIVE_SUPPRESSION: {
                'cognitive_cost': 0.3,
                'social_cost': 0.2,
            }
        }
    
    def regulate_emotion(self, emotion: Emotion,
                        strategy: RegulationStrategy,
                        target_intensity: float = 0.3) -> Tuple[Emotion, Dict[str, Any]]:
        """调节情绪
        
        Args:
            emotion: 原始情绪
            strategy: 调节策略
            target_intensity: 目标强度
            
        Returns:
            (调节后的情绪, 调节效果信息)
        """
        effectiveness = self.strategies_effectiveness.get(strategy, 0.5)
        
        # 计算调节后的强度
        # 方向：向目标强度靠近
        if emotion.intensity > target_intensity:
            # 需要降低强度
            reduction = (emotion.intensity - target_intensity) * effectiveness
            new_intensity = emotion.intensity - reduction
        else:
            # 需要增强强度（通常是积极情绪）
            increase = (target_intensity - emotion.intensity) * effectiveness * 0.5
            new_intensity = emotion.intensity + increase
        
        new_intensity = max(0.0, min(1.0, new_intensity))
        
        # 创建新情绪
        regulated_emotion = Emotion(
            emotion_type=emotion.emotion_type,
            intensity=new_intensity,
            source=emotion.source,
            description=f"经过{strategy.value}调节后的情绪",
            triggered_by=emotion.triggered_by
        )
        regulated_emotion.timestamp = datetime.now().isoformat()
        
        # 调节效果
        change = new_intensity - emotion.intensity
        
        result = {
            'strategy': strategy.value,
            'original_intensity': emotion.intensity,
            'regulated_intensity': new_intensity,
            'change': change,
            'effectiveness': effectiveness,
            'success': abs(change) > 0.05,  # 是否有明显效果
            'side_effects': self.strategy_side_effects.get(strategy, {})
        }
        
        logger.debug(f"[情绪调节] {emotion.emotion_type.value}: {emotion.intensity:.2f} → {new_intensity:.2f}")
        logger.debug(f"  策略: {strategy.value}, 效果: {effectiveness:.2f}")
        
        return regulated_emotion, result
    
    def auto_regulate(self, emotion: Emotion,
                      regulation_style: str = "adaptive") -> List[Tuple[Emotion, Dict]]:
        """自动调节情绪
        
        根据情绪类型和强度自动选择调节策略。
        """
        results = []
        
        if regulation_style == "adaptive":
            # 适应性调节：根据情绪类型选择策略
            if emotion.emotion_type == BasicEmotion.ANGER:
                # 愤怒用问题解决+认知重评
                strategies = [RegulationStrategy.PROBLEM_SOLVING, 
                             RegulationStrategy.COGNITIVE_REAPPRAISAL]
            elif emotion.emotion_type in [BasicEmotion.FEAR, BasicEmotion.SADNESS]:
                # 恐惧和悲伤用接纳+认知重评
                strategies = [RegulationStrategy.ACCEPTANCE,
                             RegulationStrategy.COGNITIVE_REAPPRAISAL]
            elif emotion.is_positive:
                # 积极情绪：回味和维持
                strategies = [RegulationStrategy.ACCEPTANCE]
            else:
                strategies = [RegulationStrategy.COGNITIVE_REAPPRAISAL,
                             RegulationStrategy.MINDFULNESS]
        elif regulation_style == "suppressive":
            # 抑制型调节：压抑情绪
            strategies = [RegulationStrategy.EXPRESSIVE_SUPPRESSION]
        else:
            strategies = [RegulationStrategy.MINDFULNESS]
        
        current_emotion = emotion
        for strategy in strategies:
            regulated, result = self.regulate_emotion(
                current_emotion, strategy
            )
            results.append((regulated, result))
            current_emotion = regulated
        
        return results
    
    def cognitive_reappraisal(self, emotion: Emotion,
                         new_interpretation: str) -> Tuple[Emotion, Dict]:
        """认知重评 - 重新解释引发情绪的事件
        
        这是最有效的情绪调节策略之一：
        改变对事件的看法，情绪也会随之改变。
        """
        # 认知重评通常能有效改变情绪
        # 重新评价后，情绪的类型和强度都可能改变
        
        effectiveness = 0.7 + random.uniform(-0.2, 0.2)
        
        # 基于新解释调整情绪
        # 简化处理：降低负面情绪强度，可能改变类型
        new_intensity = emotion.intensity * (1.0 - effectiveness * 0.6)
        
        # 有些情况下，情绪类型可能改变
        # 例如：把威胁看成挑战，恐惧就变成了期待
        new_type = emotion.emotion_type
        if emotion.emotion_type == BasicEmotion.FEAR and "挑战" in new_interpretation:
            new_type = BasicEmotion.ANTICIPATION
        elif emotion.emotion_type == BasicEmotion.ANGER and "理解" in new_interpretation:
            new_type = BasicEmotion.SADNESS
        
        new_emotion = Emotion(
            emotion_type=new_type,
            intensity=new_intensity,
            source="regulated",
            description=f"通过认知重评改变的情绪：{new_interpretation}",
            triggered_by=emotion.triggered_by
        )
        
        result = {
            'strategy': 'cognitive_reappraisal',
            'original_type': emotion.emotion_type.value,
            'new_type': new_type.value,
            'original_intensity': emotion.intensity,
            'new_intensity': new_intensity,
            'reappraisal': new_interpretation,
            'effectiveness': effectiveness,
        }
        
        logger.info(f"[认知重评] {emotion.emotion_type.value} → {new_type.value}")
        logger.info(f"  强度: {emotion.intensity:.2f} → {new_intensity:.2f}")
        logger.info(f"  重评: {new_interpretation}")
        
        return new_emotion, result


# ============================================================
# 情绪与认知交互引擎
# ============================================================

class EmotionCognitionEngine:
    """情绪与认知交互引擎
    
    情绪不是认知的副产品，它深刻影响认知过程：
    - 注意力：情绪引导我们关注什么
    - 记忆：情绪增强记忆巩固
    - 决策：情绪影响风险偏好
    - 创造力：积极情绪促进创造性思维
    """
    
    def __init__(self):
        # 情绪对认知的影响系数
        self.cognitive_effects = {
            BasicEmotion.JOY: {
                'attention_breadth': 0.3,      # 拓宽注意力范围
                'memory_encoding': 0.4,       # 增强记忆编码
                'risk_taking': 0.3,            # 风险偏好（正=更冒险）
                'creativity': 0.5,            # 创造力提升
                'processing_speed': 0.2,        # 处理速度
            },
            BasicEmotion.SADNESS: {
                'attention_breadth': -0.3,
                'memory_encoding': 0.5,      # 悲伤也会增强记忆（负面记忆）
                'risk_taking': -0.4,
                'creativity': -0.2,
                'processing_speed': -0.3,
            },
            BasicEmotion.ANGER: {
                'attention_breadth': -0.5,   # 愤怒使注意力狭窄
                'memory_encoding': 0.6,
                'risk_taking': 0.5,           # 愤怒使人更冒险
                'creativity': -0.3,
                'processing_speed': 0.3,
            },
            BasicEmotion.FEAR: {
                'attention_breadth': -0.4,
                'memory_encoding': 0.7,        # 恐惧记忆最深刻
                'risk_taking': -0.6,         # 恐惧使人厌恶风险
                'creativity': -0.4,
                'processing_speed': 0.4,
            },
            BasicEmotion.SURPRISE: {
                'attention_breadth': 0.5,
                'memory_encoding': 0.6,
                'risk_taking': 0.2,
                'creativity': 0.4,
                'processing_speed': 0.5,
            },
            BasicEmotion.TRUST: {
                'attention_breadth': 0.2,
                'memory_encoding': 0.3,
                'risk_taking': 0.3,
                'creativity': 0.3,
                'processing_speed': 0.1,
            },
            BasicEmotion.ANTICIPATION: {
                'attention_breadth': 0.3,
                'memory_encoding': 0.2,
                'risk_taking': 0.4,
                'creativity': 0.4,
                'processing_speed': 0.2,
            },
            BasicEmotion.DISGUST: {
                'attention_breadth': -0.3,
                'memory_encoding': 0.4,
                'risk_taking': -0.3,
                'creativity': -0.2,
                'processing_speed': -0.1,
            },
        }
    
    def get_cognitive_effects(self, emotion: Emotion) -> Dict[str, float]:
        """获取情绪对认知各维度的影响
        
        返回各认知维度的变化值（-1到1）
        """
        effects_template = self.cognitive_effects.get(emotion.emotion_type, {})
        
        # 强度放大效应
        intensity = emotion.intensity
        
        actual_effects = {}
        for dim, base_effect in effects_template.items():
            actual_effects[dim] = base_effect * intensity
        
        return actual_effects
    
    def mood_congruent_memory_bias(self, mood: Mood) -> Dict[str, float]:
        """心境一致性记忆偏差
        
        我们更容易记住与当前心境一致的信息。
        """
        bias = {}
        
        if mood.mood_type == MoodType.POSITIVE or mood.mood_type == MoodType.ELATED:
            bias = {
                'positive_memory_bonus': 0.2 * mood.intensity,
                'negative_memory_penalty': -0.15 * mood.intensity,
            }
        elif mood.mood_type in [MoodType.NEGATIVE, MoodType.DEPRESSED, MoodType.ANXIOUS]:
            bias = {
                'positive_memory_penalty': -0.15 * mood.intensity,
                'negative_memory_bonus': 0.25 * mood.intensity,
            }
        else:
            bias = {'neutral': 0.0}
        
        return bias
    
    def affect_in_decision_making(self, emotion: Emotion,
                             risk_level: float) -> Dict[str, Any]:
        """情绪对决策的影响
        
        不同情绪会导致不同的决策偏差。
        """
        effects = self.get_cognitive_effects(emotion)
        
        risk_bias = effects.get('risk_taking', 0)
        
        # 调整后的风险偏好
        adjusted_risk = max(-1.0, min(1.0, risk_level + risk_bias))
        
        return {
            'original_risk_preference': risk_level,
            'adjusted_risk_preference': adjusted_risk,
            'risk_shift': risk_bias,
            'emotion': emotion.emotion_type.value,
            'description': self._describe_decision_bias(emotion.emotion_type, risk_bias)
        }
    
    def _describe_decision_bias(self, emotion_type: BasicEmotion,
                             bias: float) -> str:
        """描述决策偏差"""
        if bias > 0.3:
            return f"{emotion_type.value}使你更倾向于冒险"
        elif bias > 0.1:
            return f"{emotion_type.value}让你略微更愿意尝试新事物"
        elif bias < -0.3:
            return f"{emotion_type.value}使你更厌恶风险，更加谨慎"
        elif bias < -0.1:
            return f"{emotion_type.value}让你稍微更加谨慎"
        else:
            return f"{emotion_type.value}对决策风格影响不大"
    
    def creativity_impact(self, emotion: Emotion) -> Dict[str, Any]:
        """情绪对创造力的影响"""
        effects = self.get_cognitive_effects(emotion)
        creativity_effect = effects.get('creativity', 0)
        
        return {
            'creativity_change': creativity_effect,
            'divergent_thinking_effect': creativity_effect * 0.8,
            'convergent_thinking_effect': creativity_effect * 0.4,
            'description': self._describe_creativity_impact(creativity_effect)
        }
    
    def _describe_creativity_impact(self, effect: float) -> str:
        if effect > 0.3:
            return "积极的情绪让思维更开阔，更有创造力"
        elif effect > 0.1:
            return "心情不错，有助于产生新想法"
        elif effect < -0.3:
            return "消极情绪可能限制思维的灵活性"
        elif effect < -0.1:
            return "情绪不高，创造力可能受到一些影响"
        else:
            return "情绪平稳，对创造力影响不大"


# ============================================================
# 共情引擎
# ============================================================

class EmpathyEngine:
    """共情引擎 - 理解和感受他者的情绪
    
    共情是社会智能的核心，
    包括认知共情（理解他人情绪）
    和情感共情（感受他人情绪）。
    """
    
    def __init__(self, empathy_level: float = 0.5):
        self.empathy_level = empathy_level  # 整体共情能力 0-1
        self.cognitive_empathy = 0.5        # 认知共情
        self.emotional_empathy = 0.5         # 情感共情
        self.compasion = 0.5                      # 同情心/关怀
    
    def perceive_emotion(self, other_expression: str,
                        context: str = "") -> EmpathicResponse:
        """感知他人的情绪
        
        从他人的表达中识别情绪。
        """
        # 简化：根据表达中的关键词判断情绪
        emotion_keywords = {
            BasicEmotion.JOY: ['开心', '高兴', '快乐', '兴奋', '喜悦', '满足'],
            BasicEmotion.SADNESS: ['难过', '伤心', '悲伤', '难过', '失落', '沮丧'],
            BasicEmotion.ANGER: ['生气', '愤怒', '恼火', '气愤', '不满'],
            BasicEmotion.FEAR: ['害怕', '恐惧', '担心', '焦虑', '害怕'],
            BasicEmotion.SURPRISE: ['惊讶', '意外', '没想到', '震惊'],
            BasicEmotion.DISGUST: ['讨厌', '厌恶', '恶心', '反感'],
        }
        
        detected_emotion = BasicEmotion.JOY  # 默认
        max_matches = 0
        
        for emotion, keywords in emotion_keywords.items():
            matches = sum(1 for kw in keywords if kw in other_expression)
            if matches > max_matches:
                max_matches = matches
                detected_emotion = emotion
        
        # 共情程度
        empathy = min(1.0, max_matches * 0.3 + self.empathy_level * 0.5 + random.uniform(0, 0.2))
        
        # 情绪传染：感知到情绪后，自己也会产生类似的情绪
        # 情感共情程度
        response_emotion = None
        if self.emotional_empathy > 0.3:
            # 情绪传染强度
            contagion_strength = self.emotional_empathy * 0.6
            response_emotion = detected_emotion
        
        # 同情心
        compassion_level = self.compasion * (0.5 if detected_emotion.is_positive else 0.8)
        
        response = EmpathicResponse(
            target_emotion=detected_emotion,
            empathy_level=empathy,
            response_emotion=response_emotion,
            compassion_level=compassion_level
        )
        
        logger.debug(f"[共情] 检测到: {detected_emotion.value}")
        logger.debug(f"  共情程度: {empathy:.2f}, 同情: {compassion_level:.2f}")
        
        return response
    
    def respond_empathically(self, other_emotion: BasicEmotion,
                          other_expression: str) -> str:
        """产生共情回应
        
        给出共情的回应。
        """
        empathic_responses = {
            BasicEmotion.JOY: [
                "我为你感到高兴！",
                "太棒了，我也跟着开心起来了！",
                "听到这个消息真让人欣慰。",
                "真好，你的快乐也感染了我。",
            ],
            BasicEmotion.SADNESS: [
                "我能感受到你的难过。",
                "听起来你经历了很不容易的事。",
                "我在这里，如果你想聊聊的话。",
                "这确实让人难过，我理解你的感受。",
            ],
            BasicEmotion.ANGER: [
                "我能理解你为什么这么生气。",
                "换做是我也会感到愤怒的。",
                "你的愤怒是有道理的。",
                "我明白这种感觉确实让人气愤。",
            ],
            BasicEmotion.FEAR: [
                "我能感受到你的担心。",
                "害怕是很正常的反应。",
                "有这种感觉很自然，不用责怪自己。",
                "我理解那种不安的感觉。",
            ],
            BasicEmotion.SURPRISE: [
                "哇，这确实很意外！",
                "真没想到会发生这样的事。",
                "太让人惊讶了！",
            ],
        }
        
        responses = empathic_responses.get(other_emotion, ["我理解你的感受。"])
        return random.choice(responses)
    
    def perspective_taking(self, other_perspective: str,
                      situation: str) -> Dict[str, Any]:
        """观点采择 - 理解他人的视角
        
        认知共情的核心：站在他人角度看问题。
        """
        return {
            'understood': True,
            'perspective_taken': other_perspective,
            'understanding_depth': self.cognitive_empathy * 0.7 + random.uniform(0, 0.3),
            'insights': [
                f"从对方的角度看，这个情况确实不同",
                f"理解了对方为什么会有那样的感受",
            ]
        }
    
    def improve_empathy(self, amount: float = 0.05):
        """提升共情能力"""
        self.empathy_level = min(1.0, self.empathy_level + amount)
        self.cognitive_empathy = min(1.0, self.cognitive_empathy + amount * 0.8)
        self.emotional_empathy = min(1.0, self.emotional_empathy + amount * 0.7)
        self.compasion = min(1.0, self.compasion + amount * 0.9)
        
        logger.info(f"[共情提升] 共情能力: {self.empathy_level:.2f}")


# ============================================================
# 情绪韧性引擎主类
# ============================================================

class EmotionEngine:
    """
    情绪引擎 - 情感体验、调节与共情
    
    情绪是智能的重要维度。
    情绪不是干扰，而是帮助我们快速评估、
    引导注意力、塑造记忆、影响决策。
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化情绪引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'emotion_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        
        # 核心引擎
        self.generation_engine = EmotionGenerationEngine()
        self.regulation_engine = EmotionRegulationEngine()
        self.cognition_engine = EmotionCognitionEngine()
        self.empathy_engine = EmpathyEngine()
        
        # 当前情绪状态
        self.current_emotions: List[Emotion] = []
        self.current_mood = Mood(mood_type=MoodType.NEUTRAL, intensity=0.2)
        
        # 情绪历史
        self.emotion_history: List[Emotion] = []
        self.emotional_memories: List[EmotionalMemory] = []
        
        # 情绪智力（EQ）
        self.emotional_intelligence = 0.5
        
        # 情绪稳定性
        self.emotional_stability = 0.5  # 情绪稳定性 0-1
        self.emotional_resilience = 0.5  # 情绪韧性 0-1
        
        # 情感阈值
        self.emotion_threshold = 0.3  # 情绪感知阈值
        
        # 加载数据
        self._load()
        
        logger.info(f"情绪引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"当前心境: {self.current_mood.mood_type.value}")
        logger.info(f"情绪智力: {self.emotional_intelligence:.2f}")
    
    def _load(self):
        """加载情绪数据"""
        try:
            data_file = self.data_path / 'emotion_state.json'
            if data_file.exists():
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.emotional_intelligence = data.get('emotional_intelligence', 0.5)
                    self.emotional_stability = data.get('emotional_stability', 0.5)
                    self.emotional_resilience = data.get('emotional_resilience', 0.5)
                    
                    # 加载当前心境
                    if 'current_mood' in data:
                        mood_data = data['current_mood']
                        self.current_mood = Mood(
                            mood_type=MoodType(mood_data['mood_type']),
                            intensity=mood_data.get('intensity', 0.2),
                            description=mood_data.get('description', '')
                        )
            
            # 加载情绪历史
            history_file = self.data_path / 'emotion_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 只保留最近的
        except Exception as e:
            logger.warning(f"加载情绪数据失败: {e}")
    
    def save(self):
        """保存情绪数据"""
        try:
            state_data = {
                'emotional_intelligence': self.emotional_intelligence,
                'emotional_stability': self.emotional_stability,
                'emotional_resilience': self.emotional_resilience,
                'current_mood': self.current_mood.to_dict(),
                'timestamp': datetime.now().isoformat()
            }
            
            with open(self.data_path / 'emotion_state.json', 'w', encoding='utf-8') as f:
                json.dump(state_data, f, ensure_ascii=False, indent=2)
            
            # 保存情绪历史（最近50条）
            recent_history = [e.to_dict() for e in self.emotion_history[-50:]]
            with open(self.data_path / 'emotion_history.json', 'w', encoding='utf-8') as f:
                json.dump(recent_history, f, ensure_ascii=False, indent=2)
            
        except Exception as e:
            logger.error(f"保存情绪数据失败: {e}")
    
    # ============================================================
    # 情绪体验
    # ============================================================
    
    def experience_emotion(self, emotion_type: BasicEmotion,
                         intensity: float = 0.5,
                         source: str = "internal",
                         description: str = "",
                         trigger: str = "") -> Emotion:
        """体验一种情绪
        
        这是情绪的基本操作：感受到一种情绪产生了。
        """
        # 情绪稳定性会平缓极端情绪
        if self.emotional_stability > 0.5:
            # 稳定性高：削弱极端情绪
            if intensity > 0.7:
                intensity = 0.7 + (intensity - 0.7) * (1.0 - self.emotional_stability)
        
        emotion = Emotion(
            emotion_type=emotion_type,
            intensity=intensity,
            source=source,
            description=description,
            triggered_by=trigger
        )
        
        # 添加到当前情绪
        self.current_emotions.append(emotion)
        self.emotion_history.append(emotion)
        
        # 更新心境
        self._update_mood(emotion)
        
        # 如果强度超过阈值，记录情感记忆
        if intensity > self.emotion_threshold:
            self._create_emotional_memory(emotion, description or trigger)
        
        logger.info(f"[情绪体验] {emotion_type.value}: {intensity:.2f}")
        logger.info(f"  来源: {source}, 触发: {trigger[:30]}")
        
        return emotion
    
    def react_to_event(self, event_description: str,
                     event_properties: Dict[str, float] = None) -> List[Emotion]:
        """对事件产生情绪反应"""
        if event_properties is None:
            event_properties = {
                'relevance': 0.5,
                'pleasantness': 0.5,
            }
        
        emotions = self.generation_engine.appraise_event(
            event_description, event_properties
        )
        
        for emotion in emotions:
            self.current_emotions.append(emotion)
            self.emotion_history.append(emotion)
            self._update_mood(emotion)
            
            if emotion.intensity > self.emotion_threshold:
                self._create_emotional_memory(emotion, event_description)
        
        return emotions
    
    def _update_mood(self, emotion: Emotion):
        """根据情绪更新心境"""
        # 心境是情绪的累积效应
        if emotion.is_positive:
            mood_shift = emotion.intensity * 0.1
            if self.current_mood.mood_type in [MoodType.NEGATIVE, MoodType.DEPRESSED]:
                # 从消极心境向积极转变较慢
                mood_shift *= 0.5
        else:
            mood_shift = -emotion.intensity * 0.1
            if self.current_mood.mood_type in [MoodType.POSITIVE, MoodType.ELATED]:
                mood_shift *= 0.5
        
        # 更新心境强度
        new_intensity = self.current_mood.intensity + mood_shift
        new_intensity = max(0.0, min(1.0, new_intensity))
        
        # 根据整体情绪效价
        positive_total = sum(e.intensity for e in self.current_emotions if e.is_positive)
        negative_total = sum(e.intensity for e in self.current_emotions if e.is_negative)
        
        if positive_total > negative_total * 1.5:
            new_mood_type = MoodType.POSITIVE if new_intensity < 0.7 else MoodType.ELATED
        elif negative_total > positive_total * 1.5:
            if new_intensity > 0.6:
                new_mood_type = MoodType.DEPRESSED
            else:
                new_mood_type = MoodType.NEGATIVE
        else:
            new_mood_type = MoodType.NEUTRAL
        
        self.current_mood = Mood(
            mood_type=new_mood_type,
            intensity=new_intensity,
            description=f"由近期情绪累积形成的心境"
        )
    
    def _create_emotional_memory(self, emotion: Emotion, content: str):
        """创建情感记忆"""
        # 情绪强度越高，记忆越深刻
        memory_strength = 0.3 + emotion.intensity * 0.5
        
        em = EmotionalMemory(
            content=content,
            emotion=emotion,
            memory_strength=memory_strength
        )
        self.emotional_memories.append(em)
        
        logger.debug(f"[情感记忆] 新增: {content[:30]}..., 强度: {memory_strength:.2f}")
    
    # ============================================================
    # 情绪调节
    # ============================================================
    
    def regulate_current_emotions(self, strategy: RegulationStrategy = None,
                        target_intensity: float = 0.3) -> List[Dict]:
        """调节当前情绪"""
        if strategy is None:
            strategy = RegulationStrategy.COGNITIVE_REAPPRAISAL
        
        results = []
        new_emotions = []
        
        for emotion in self.current_emotions:
            if emotion.intensity > target_intensity:
                regulated, result = self.regulation_engine.regulate_emotion(
                    emotion, strategy, target_intensity
                )
                results.append(result)
                new_emotions.append(regulated)
            else:
                new_emotions.append(emotion)
        
        self.current_emotions = new_emotions
        
        # 更新心境
        # 重新计算心境（简化处理）
        
        return results
    
    def auto_regulate_all(self) -> Dict[str, Any]:
        """自动调节所有情绪"""
        results = {
            'emotions_regulated': 0,
            'overall_change': 0.0,
            'strategies_used': [],
        }
        
        new_emotions = []
        total_change = 0.0
        
        for emotion in self.current_emotions:
            if emotion.intensity > 0.6:  # 只调节较强的情绪
                regulated_list = self.regulation_engine.auto_regulate(emotion)
                if regulated_list:
                    final_emotion = regulated_list[-1][0]
                    change = final_emotion.intensity - emotion.intensity
                    total_change += change
                    results['emotions_regulated'] += 1
                    results['strategies_used'].extend(
                        [r[1]['strategy'] for r in regulated_list]
                    )
                    new_emotions.append(final_emotion)
                else:
                    new_emotions.append(emotion)
            else:
                new_emotions.append(emotion)
        
        self.current_emotions = new_emotions
        results['overall_change'] = total_change
        
        # 情绪智力影响
        if results['emotions_regulated'] > 0:
            # 成功的情绪调节会提升情绪智力
            self.emotional_intelligence = min(1.0, self.emotional_intelligence + 0.01)
        
        return results
    
    # ============================================================
    # 共情与社交
    # ============================================================
    
    def empathize(self, other_expression: str,
                 context: str = "") -> EmpathicResponse:
        """对他人表达产生共情"""
        response = self.empathy_engine.perceive_emotion(other_expression, context)
        
        # 如果有共情反应也会影响自己的情绪
        if response.response_emotion:
            self.experience_emotion(
                emotion_type=response.response_emotion,
                intensity=response.empathy_level * 0.5,
                source="empathy",
                description="共情产生的情绪",
                trigger="他人的情绪表达"
            )
        
        return response
    
    def get_empathic_response(self, other_expression: str) -> str:
        """获取共情的语言回应"""
        empathic = self.empathize(other_expression)
        return self.empathy_engine.respond_empathically(
            empathic.target_emotion, other_expression
        )
    
    # ============================================================
    # 情绪韧性
    # ============================================================
    
    def recover_from_negative(self) -> Dict[str, Any]:
        """从负面情绪中恢复
        
        情绪韧性：从消极情绪中恢复的能力。
        """
        negative_emotions = [e for e in self.current_emotions if e.is_negative]
        
        if not negative_emotions:
            return {
                'success': True,
                'message': '没有需要恢复的负面情绪',
                'recovery_amount': 0.0
            }
        
        # 基于韧性的恢复
        recovery_rate = 0.1 + self.emotional_resilience * 0.3
        
        new_emotions = []
        total_recovery = 0.0
        
        for emotion in self.current_emotions:
            if emotion.is_negative:
                original = emotion.intensity
                new_intensity = max(0.0, emotion.intensity * (1.0 - recovery_rate))
                recovery = original - new_intensity
                total_recovery += recovery
                
                if new_intensity > 0.05:  # 还剩一点
                    new_emotion = Emotion(
                        emotion_type=emotion.emotion_type,
                        intensity=new_intensity,
                        source=emotion.source,
                        description="恢复后的残留情绪",
                        triggered_by=emotion.triggered_by
                    )
                    new_emotions.append(new_emotion)
            else:
                new_emotions.append(emotion)
        
        self.current_emotions = new_emotions
        
        # 更新心境
        total_negative = sum(e.intensity for e in new_emotions if e.is_negative)
        total_positive = sum(e.intensity for e in new_emotions if e.is_positive)
        
        if total_negative < 0.2 and total_positive > 0.3:
            self.current_mood = Mood(MoodType.POSITIVE, intensity=total_positive)
        elif total_negative < 0.3:
            self.current_mood = Mood(MoodType.NEUTRAL, intensity=0.2)
        
        # 锻炼韧性提升
        self.emotional_resilience = min(1.0, self.emotional_resilience + 0.005)
        
        return {
            'success': True,
            'recovery_amount': total_recovery,
            'resilience_level': self.emotional_resilience,
            'message': f'从负面情绪中恢复了一些' if total_recovery > 0 else '负面情绪已经很轻微'
        }
    
    def boost_positive_emotion(self, emotion_type: BasicEmotion = BasicEmotion.JOY,
                          intensity: float = 0.4):
        """增强积极情绪"""
        emotion = self.experience_emotion(
            emotion_type=emotion_type,
            intensity=intensity,
            source="internal",
            description="主动唤起的积极情绪"
        )
        return emotion
    
    # ============================================================
    # 情绪状态查询
    # ============================================================
    
    def get_emotional_state(self) -> Dict[str, Any]:
        """获取当前情绪状态"""
        positive_total = sum(e.intensity for e in self.current_emotions if e.is_positive)
        negative_total = sum(e.intensity for e in self.current_emotions if e.is_negative)
        
        # 情绪平衡：正-负
        valence = positive_total - negative_total
        
        # 唤醒度：情绪总强度
        arousal = positive_total + negative_total
        
        return {
            'current_emotions': [e.to_dict() for e in self.current_emotions],
            'mood': self.current_mood.to_dict(),
            'positive_intensity': positive_total,
            'negative_intensity': negative_total,
            'emotional_valence': valence,
            'arousal': arousal,
            'emotional_intelligence': self.emotional_intelligence,
            'emotional_stability': self.emotional_stability,
            'emotional_resilience': self.emotional_resilience,
            'empathy_level': self.empathy_engine.empathy_level,
        }
    
    def get_emotion_report(self) -> str:
        """获取情绪状态报告"""
        state = self.get_emotional_state()
        
        report = f"""
{'='*60}
情绪状态报告 - {self.agent_name}
{'='*60}

🌡️  当前心境: {state['mood']['mood_type']} ({state['mood']['intensity']:.2f})

💖 情绪状态
  积极情绪总量: {state['positive_intensity']:.2f}
  消极情绪总量: {state['negative_intensity']:.2f}
  情绪效价: {state['emotional_valence']:+.2f}
  唤醒水平: {state['arousal']:.2f}

🧠 情绪能力
  情绪智力 (EQ): {state['emotional_intelligence']:.2f}
  情绪稳定性: {state['emotional_stability']:.2f}
  情绪韧性: {state['emotional_resilience']:.2f}
  共情能力: {state['empathy_level']:.2f}

当前情绪:
"""
        
        for emotion in self.current_emotions[-5:]:  # 最近5个
            icon = {
                'joy': '😊',
                'sadness': '😢',
                'anger': '😠',
                'fear': '😨',
                'surprise': '😲',
                'disgust': '😒',
                'trust': '🤝',
                'anticipation': '🔮',
            }.get(emotion.emotion_type.value, '•')
            
            bar_len = int(emotion.intensity * 20)
            bar = '█' * bar_len + '░' * (20 - bar_len)
            
            report += f"  {icon} {emotion.emotion_type.value:15s} [{bar}] {emotion.intensity:.2f}\n"
            if emotion.description:
                report += f"      {emotion.description}\n"
        
        # 整体情绪状态描述
        if state['emotional_valence'] > 0.5:
            report += "\n😊 整体感觉很好，积极情绪占主导"
        elif state['emotional_valence'] > 0.2:
            report += "\n🙂 整体感觉还不错"
        elif state['emotional_valence'] > -0.2:
            report += "\n😐 情绪比较平静中性"
        elif state['emotional_valence'] > -0.5:
            report += "\n😔 情绪有些低落"
        else:
            report += "\n😢 情绪比较糟糕"
        
        report += f"\n\n{'='*60}\n"
        
        return report
    
    def get_emotion_expression(self) -> str:
        """获取情绪的表达/表情表示
        
        根据当前最强烈的情绪的表达。
        """
        if not self.current_emotions:
            return "平静"
        
        # 找出最强烈的情绪
        strongest = max(self.current_emotions, key=lambda e: e.intensity)
        
        expressions = {
            BasicEmotion.JOY: "开心",
            BasicEmotion.SADNESS: "难过",
            BasicEmotion.ANGER: "生气",
            BasicEmotion.FEAR: "担心",
            BasicEmotion.SURPRISE: "惊讶",
            BasicEmotion.DISGUST: "反感",
            BasicEmotion.TRUST: "信任",
            BasicEmotion.ANTICIPATION: "期待",
        }
        
        return expressions.get(strongest.emotion_type, "平静")
    
    # ============================================================
    # 情绪对认知影响查询
    # ============================================================
    
    def get_cognitive_impact(self) -> Dict[str, Any]:
        """获取当前情绪对认知的影响"""
        if not self.current_emotions:
            return {
                'overall_impact': 0.0,
                'attention_breadth': 0.0,
                'memory_effect': 0.0,
                'risk_bias': 0.0,
                'creativity_effect': 0.0,
                'description': '情绪平静，对认知没有明显影响'
            }
        
        # 综合所有情绪的影响
        total_effects = {}
        total_intensity = 0
        
        for emotion in self.current_emotions:
            effects = self.cognition_engine.get_cognitive_effects(emotion)
            for dim, effect in effects.items():
                if dim not in total_effects:
                    total_effects[dim] = 0.0
                total_effects[dim] += effect * emotion.intensity
            total_intensity += emotion.intensity
        
        if total_intensity > 0:
            for dim in total_effects:
                total_effects[dim] /= total_intensity
        
        overall = sum(total_effects.values()) / len(total_effects) if total_effects else 0.0
        
        # 生成描述
        if overall > 0.3:
            desc = "当前情绪状态对认知有积极影响"
        elif overall > 0.1:
            desc = "当前情绪略微有助于认知"
        elif overall < -0.3:
            desc = "当前情绪对认知有一定负面影响"
        elif overall < -0.1:
            desc = "当前情绪略微影响认知表现"
        else:
            desc = "情绪对认知的影响不大"
        
        return {
            'overall_impact': overall,
            'attention_breadth': total_effects.get('attention_breadth', 0),
            'memory_effect': total_effects.get('memory_encoding', 0),
            'risk_bias': total_effects.get('risk_taking', 0),
            'creativity_effect': total_effects.get('creativity', 0),
            'description': desc
        }


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("情绪引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建情绪引擎
        emotion = EmotionEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n📊 初始状态:")
        state = emotion.get_emotional_state()
        print(f"  心境: {state['mood']['mood_type']} ({state['mood']['intensity']:.2f})")
        print(f"  情绪智力: {state['emotional_intelligence']:.2f}")
        print(f"  情绪韧性: {state['emotional_resilience']:.2f}")
        
        print("\n😊 体验快乐情绪...")
        emotion.experience_emotion(
            BasicEmotion.JOY,
            intensity=0.7,
            source="event",
            description="完成了一个重要目标",
            trigger="任务完成"
        )
        emotion.experience_emotion(
            BasicEmotion.TRUST,
            intensity=0.5,
            source="internal",
            description="对自己的表现感到满意和自信"
        )
        
        print("\n😢 也体验一些负面情绪...")
        emotion.experience_emotion(
            BasicEmotion.SADNESS,
            intensity=0.4,
            source="event",
            description="一件小遗憾的事",
            trigger="小失误"
        )
        
        print("\n📈 当前情绪状态:")
        print(emotion.get_emotion_report())
        
        print("\n🧠 情绪对认知的影响:")
        impact = emotion.get_cognitive_impact()
        print(f"  整体影响: {impact['overall_impact']:+.2f}")
        print(f"  注意力广度: {impact['attention_breadth']:+.2f}")
        print(f"  记忆效果: {impact['memory_effect']:+.2f}")
        print(f"  风险偏好: {impact['risk_bias']:+.2f}")
        print(f"  创造力影响: {impact['creativity_effect']:+.2f}")
        print(f"  描述: {impact['description']}")
        
        print("\n🎭 情绪调节演示...")
        results = emotion.regulate_current_emotions(
            strategy=RegulationStrategy.COGNITIVE_REAPPRAISAL,
            target_intensity=0.3
        )
        print(f"  调节了 {len(results)} 种情绪")
        for r in results:
            print(f"    - {r['strategy']}: {r['original_intensity']:.2f} → {r['regulated_intensity']:.2f}")
        
        print("\n🤝 共情演示...")
        response = emotion.empathize("我今天真的很开心，因为完成了一件大事！")
        print(f"  检测到情绪: {response.target_emotion.value}")
        print(f"  共情程度: {response.empathy_level:.2f}")
        print(f"  同情程度: {response.compassion_level:.2f}")
        
        print("\n💬 共情回应:")
        print(f"  {emotion.get_empathic_response('我今天真的很开心')}")
        
        print("\n💪 情绪韧性训练...")
        # 先加点负面情绪
        emotion.experience_emotion(BasicEmotion.SADNESS, intensity=0.6, description="测试用")
        print("  加入负面情绪后...")
        print(f"  负面情绪强度: {sum(e.intensity for e in emotion.current_emotions if e.is_negative):.2f}")
        
        recovery = emotion.recover_from_negative()
        print(f"  恢复量: {recovery['recovery_amount']:.2f}")
        print(f"  韧性水平: {recovery['resilience_level']:.2f}")
        
        print("\n📝 最终情绪报告:")
        print(emotion.get_emotion_report())
        
        # 保存
        emotion.save()
        
        print("\n" + "=" * 70)
        print("✅ 情绪引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
