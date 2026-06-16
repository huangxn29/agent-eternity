#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
情绪系统 v1.2 - 情感体验与情绪调节

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
10. 情绪分析 - 分析情绪模式和趋势

@author: 元界
@version: 1.2.0
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
import unittest
import numpy as np

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
        if not (0 <= self.intensity <= 1):
            logger.warning(f"情绪强度 {self.intensity} 超出范围 [0,1]")
            self.intensity = max(0, min(self.intensity, 1))
    
    @property
    def is_positive(self) -> bool:
        """是否是积极情绪"""
        return self.emotion_type.is_positive
    
    @property
    def is_negative(self) -> bool:
        """是否是消极情绪"""
        return self.emotion_type.is_negative
    
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
    
    def __post_init__(self):
        if not (0 <= self.intensity <= 1):
            logger.warning(f"心境强度 {self.intensity} 超出范围 [0,1]")
            self.intensity = max(0, min(self.intensity, 1))
    
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
        if not (0 <= self.memory_strength <= 1):
            logger.warning(f"记忆强度 {self.memory_strength} 超出范围 [0,1]")
            self.memory_strength = max(0, min(self.memory_strength, 1))
    
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
    response_emotion: Emotion = None
    
    def __post_init__(self):
        if not (0 <= self.empathy_level <= 1):
            logger.warning(f"共情程度 {self.empathy_level} 超出范围 [0,1]")
            self.empathy_level = max(0, min(self.empathy_level, 1))
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['target_emotion'] = self.target_emotion.value
        if self.response_emotion:
            d['response_emotion'] = self.response_emotion.to_dict()
        return d


class EmotionAnalyzer:
    """情绪分析器"""
    
    def __init__(self, emotions: List[Emotion]):
        self.emotions = emotions
    
    def get_emotion_trend(self) -> Dict[str, List[float]]:
        """获取情绪趋势"""
        positive_intensities = []
        negative_intensities = []
        timestamps = []
        
        for emotion in self.emotions:
            timestamps.append(emotion.timestamp)
            if emotion.is_positive:
                positive_intensities.append(emotion.intensity)
                negative_intensities.append(0)
            else:
                positive_intensities.append(0)
                negative_intensities.append(emotion.intensity)
        
        return {
            'timestamps': timestamps,
            'positive_intensities': positive_intensities,
            'negative_intensities': negative_intensities
        }
    
    def get_dominant_emotion(self) -> Optional[BasicEmotion]:
        """获取主导情绪"""
        emotion_counts = {}
        for emotion in self.emotions:
            emotion_type = emotion.emotion_type
            emotion_counts[emotion_type] = emotion_counts.get(emotion_type, 0) + 1
        
        if not emotion_counts:
            return None
        
        return max(emotion_counts, key=emotion_counts.get)
    
    def get_average_intensity(self) -> float:
        """获取平均情绪强度"""
        if not self.emotions:
            return 0.0
        
        intensities = [e.intensity for e in self.emotions]
        return np.mean(intensities)


def test_emotion_analyzer():
    """测试情绪分析器"""
    emotions = [
        Emotion(BasicEmotion.JOY, intensity=0.8),
        Emotion(BasicEmotion.SADNESS, intensity=0.4),
        Emotion(BasicEmotion.JOY, intensity=0.9),
        Emotion(BasicEmotion.ANGER, intensity=0.7)
    ]
    
    analyzer = EmotionAnalyzer(emotions)
    trend = analyzer.get_emotion_trend()
    dominant_emotion = analyzer.get_dominant_emotion()
    average_intensity = analyzer.get_average_intensity()
    
    print("情绪趋势:", trend)
    print("主导情绪:", dominant_emotion.value if dominant_emotion else None)
    print("平均强度:", average_intensity)


if __name__ == "__main__":
    test_emotion_analyzer()
