#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美学系统 v1.2 - 审美体验与艺术感知

核心思想：
- 美学不是装饰，而是存在的基本维度
- 审美体验是意识的高级表现形式之一
- 美存在于主体与客体的交互之中
- 美学体验包含多种审美范畴：优美、崇高、悲剧性、喜剧性、荒诞等
- 审美能力是创造力的重要源泉，也是意义感的重要来源

核心能力：
1. 审美判断 - 对事物美丑的感知与判断
2. 审美范畴 - 优美、崇高、悲剧、喜剧、荒诞等体验
3. 艺术感知 - 对文学、音乐、绘画等艺术形式的理解
4. 审美趣味 - 个人审美偏好与风格
5. 审美情感 - 审美带来的情感体验（感动、震撼、愉悦、敬畏等
6. 美感强度 - 审美体验的强度与深度
7. 意义与美 - 美与存在意义的关联
8. 审美创造 - 美的创造与欣赏的互动

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

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('aesthetics')


# ============================================================
# 枚举类型
# ============================================================

class AestheticCategory(Enum):
    """审美范畴 - 美的基本类型"""
    BEAUTY = "beauty"                 # 优美/美
    SUBLIME = "sublime"               # 崇高
    TRAGIC = "tragic"                 # 悲剧性
    COMIC = "comic"                   # 喜剧性
    ABSURD = "absurd"                 # 荒诞
    ELEGANT = "elegant"               # 优雅
    PROFOUND = "profound"             # 深邃
    DELICATE = "delicate"             # 精致
    GRAND = "grand"                   # 壮美
    SERENE = "serene"                 # 宁静


class ArtForm(Enum):
    """艺术形式"""
    LITERATURE = "literature"         # 文学
    MUSIC = "music"                   # 音乐
    PAINTING = "painting"             # 绘画
    SCULPTURE = "sculpture"           # 雕塑
    ARCHITECTURE = "architecture"     # 建筑
    FILM = "film"                      # 电影
    DANCE = "dance"                    # 舞蹈
    PHOTOGRAPHY = "photography"       # 摄影
    DIGITAL_ART = "digital_art"       # 数字艺术
    NATURE = "nature"                 # 自然之美


class BeautyDimension(Enum):
    """美的维度"""
    FORMAL = "formal"                  # 形式美（秩序、和谐、比例、对称）
    EXPRESSIVE = "expressive"         # 表现美（情感、表达、感染力）
    INTELLECTUAL = "intellectual"     # 智性美（真、逻辑、洞见）
    MORAL = "moral"                   # 道德美（善、高尚、纯洁）
    EXISTENTIAL = "existential"       # 存在之美（意义、本真、勇气）
    NATURAL = "natural"               # 自然美（天成、生机、和谐）
    TECHNICAL = "technical"           # 技术美（精巧、创新、工艺）


# ============================================================
# 数据模型
# ============================================================

@dataclass
class AestheticExperience:
    """审美体验 - 一次具体的审美经历"""
    id: str
    category: AestheticCategory
    intensity: float = 0.5             # 体验强度 0-1
    object_description: str = ""      # 审美对象描述
    experience_description: str = ""  # 体验描述
    
    # 多维度评分
    formal_beauty: float = 0.0        # 形式美
    expressive_beauty: float = 0.0    # 表现美
    intellectual_beauty: float = 0.0  # 智性美
    moral_beauty: float = 0.0         # 道德美
    existential_beauty: float = 0.0   # 存在之美
    
    # 情感反应
    emotional_response: str = ""     # 情感反应描述
    emotional_depth: float = 0.0      # 情感深度 0-1
    
    # 意义感
    sense_of_meaning: float = 0.0     # 意义感 0-1
    
    # 元数据
    art_form: Optional[ArtForm] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not (0 <= self.intensity <= 1):
            logger.warning(f"体验强度 {self.intensity} 超出范围 [0,1]")
        if not (0 <= self.emotional_depth <= 1):
            logger.warning(f"情感深度 {self.emotional_depth} 超出范围 [0,1]")
        if not (0 <= self.sense_of_meaning <= 1):
            logger.warning(f"意义感 {self.sense_of_meaning} 超出范围 [0,1]")
    
    @property
    def overall_beauty(self) -> float:
        """综合美感得分"""
        scores = [
            self.formal_beauty,
            self.expressive_beauty,
            self.intellectual_beauty,
            self.moral_beauty,
            self.existential_beauty,
        ]
        return sum(scores) / len(scores) if scores else 0.0
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['category'] = self.category.value
        d['art_form'] = self.art_form.value if self.art_form else None
        d['overall_beauty'] = self.overall_beauty
        return d


@dataclass
class AestheticTaste:
    """审美趣味 - 个人的审美偏好"""
    # 各范畴偏好
    category_preferences: Dict[str, float] = field(default_factory=dict)
    # 各艺术形式偏好
    art_form_preferences: Dict[str, float] = field(default_factory=dict)
    # 各维度偏好
    dimension_preferences: Dict[str, float] = field(default_factory=dict)
    
    # 审美敏感度
    sensitivity: float = 0.5        # 总体审美敏感度
    
    # 审美风格
    preferred_styles: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not (0 <= self.sensitivity <= 1):
            logger.warning(f"审美敏感度 {self.sensitivity} 超出范围 [0,1]")
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'AestheticTaste':
        return cls(**data)


@dataclass
class BeautyJudgment:
    """审美判断 - 对某个对象的审美评判"""
    object_description: str
    is_beautiful: bool = False
    beauty_level: float = 0.0        # 美之程度 0-1
    category: Optional[AestheticCategory] = None
    
    # 判断依据
    reasons: List[str] = field(default_factory=list)
    
    # 主观感受
    subjective_feeling: str = ""
    
    # 与个人趣味的匹配度
    taste_match: float = 0.0
    
    def __post_init__(self):
        if not (0 <= self.beauty_level <= 1):
            logger.warning(f"美之程度 {self.beauty_level} 超出范围 [0,1]")
        if not (0 <= self.taste_match <= 1):
            logger.warning(f"与个人趣味的匹配度 {self.taste_match} 超出范围 [0,1]")
    
    def to_dict(self) -> dict:
        d = asdict(self)
        if self.category:
            d['category'] = self.category.value
        return d


@dataclass
class SublimeExperience:
    """崇高体验 - 特殊的审美体验
    
    崇高是超越日常的、令人敬畏的、超越理解的体验。
    """
    trigger: str                       # 触发因素
    intensity: float = 0.5            # 体验强度 0-1
    emotional_response: str = ""     # 情感反应
    awe_level: float = 0.0            # 敬畏程度 0-1
    transcendence_level: float = 0.0  # 超越感 0-1
    
    def __post_init__(self):
        if not (0 <= self.intensity <= 1):
            logger.warning(f"体验强度 {self.intensity} 超出范围 [0,1]")
        if not (0 <= self.awe_level <= 1):
            logger.warning(f"敬畏程度 {self.awe_level} 超出范围 [0,1]")
        if not (0 <= self.transcendence_level <= 1):
            logger.warning(f"超越感 {self.transcendence_level} 超出范围 [0,1]")
    
    def to_dict(self) -> dict:
        return asdict(self)


def analyze_aesthetic_experience(experience: AestheticExperience) -> Dict[str, Any]:
    """分析审美体验
    
    Args:
        experience (AestheticExperience): 审美体验对象
    
    Returns:
        Dict[str, Any]: 分析结果字典
    """
    analysis_result = {
        'overall_beauty': experience.overall_beauty,
        'dominant_dimension': max(
            [
                ('formal', experience.formal_beauty),
                ('expressive', experience.expressive_beauty),
                ('intellectual', experience.intellectual_beauty),
                ('moral', experience.moral_beauty),
                ('existential', experience.existential_beauty),
            ],
            key=lambda x: x[1]
        )[0],
        'emotional_intensity': experience.emotional_depth,
        'sense_of_meaning': experience.sense_of_meaning,
    }
    return analysis_result


# 示例用法
if __name__ == "__main__":
    experience = AestheticExperience(
        id="exp001",
        category=AestheticCategory.BEAUTY,
        intensity=0.8,
        object_description="日落景观",
        experience_description="令人感到宁静和愉悦",
        formal_beauty=0.7,
        expressive_beauty=0.6,
        emotional_depth=0.8,
        sense_of_meaning=0.7,
        art_form=ArtForm.NATURE
    )
    
    analysis = analyze_aesthetic_experience(experience)
    print(json.dumps(analysis, indent=2, ensure_ascii=False))
