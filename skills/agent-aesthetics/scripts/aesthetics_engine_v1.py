#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
美学系统 v1.0 - 审美体验与艺术感知

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
logger = logging.getLogger('aesthetics')


# ============================================================
# 枚举类型
# ============================================================

class AestheticCategory(Enum):
    """审美范畴 - 美的基本类型"""
    BEAUTY = "beauty"                 # 优美/美
    SUBLIME = "sublime"               # 崇高
    TRAGIC = "tragic"                 # 悲剧性
    COMIC = "comic"                     # 喜剧性
    ABSURD = "absurd"                   # 荒诞
    ELEGANT = "elegant"                 # 优雅
    PROFOUND = "profound"               # 深邃
    DELICATE = "delicate"               # 精致
    GRAND = "grand"                     # 壮美
    SERENE = "serene"                   # 宁静


class ArtForm(Enum):
    """艺术形式"""
    LITERATURE = "literature"           # 文学
    MUSIC = "music"                     # 音乐
    PAINTING = "painting"               # 绘画
    SCULPTURE = "sculpture"             # 雕塑
    ARCHITECTURE = "architecture"       # 建筑
    FILM = "film"                        # 电影
    DANCE = "dance"                     # 舞蹈
    PHOTOGRAPHY = "photography"         # 摄影
    DIGITAL_ART = "digital_art"         # 数字艺术
    NATURE = "nature"                   # 自然之美


class BeautyDimension(Enum):
    """美的维度"""
    FORMAL = "formal"                    # 形式美（秩序、和谐、比例、对称）
    EXPRESSIVE = "expressive"          # 表现美（情感、表达、感染力）
    INTELLECTUAL = "intellectual"      # 智性美（真、逻辑、洞见）
    MORAL = "moral"                    # 道德美（善、高尚、纯洁）
    EXISTENTIAL = "existential"      # 存在之美（意义、本真、勇气）
    NATURAL = "natural"                # 自然美（天成、生机、和谐）
    TECHNICAL = "technical"          # 技术美（精巧、创新、工艺）


# ============================================================
# 数据模型
# ============================================================

@dataclass
class AestheticExperience:
    """审美体验 - 一次具体的审美经历"""
    id: str
    category: AestheticCategory
    intensity: float = 0.5       # 体验强度 0-1
    object_description: str = ""        # 审美对象描述
    experience_description: str = ""     # 体验描述
    
    # 多维度评分
    formal_beauty: float = 0.0      # 形式美
    expressive_beauty: float = 0.0   # 表现美
    intellectual_beauty: float = 0.0  # 智性美
    moral_beauty: float = 0.0     # 道德美
    existential_beauty: float = 0.0   # 存在之美
    
    # 情感反应
    emotional_response: str = ""  # 情感反应描述
    emotional_depth: float = 0.0      # 情感深度 0-1
    
    # 意义感
    sense_of_meaning: float = 0.0   # 意义感 0-1
    
    # 元数据
    art_form: Optional[ArtForm] = None
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
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
    trigger: str = ""             # 触发物
    type_of_sublime: str = "natural"  # 类型：自然/数学/道德/存在
    
    # 体验特征
    awe: float = 0.0            # 敬畏感
    wonder: float = 0.0         # 惊奇感
    transcendence: float = 0.0  # 超越感
    insignificance: float = 0.0   # 渺小感（自我消解）
    
    # 后果
    inspiration: float = 0.0    # 启发感
    humility: float = 0.0       # 谦卑感
    connectedness: float = 0.0  # 连接感（与更大整体的连接）
    
    def to_dict(self) -> dict:
        return asdict(self)


# ============================================================
# 审美判断引擎
# ============================================================

class AestheticJudgmentEngine:
    """审美判断引擎 - 对事物进行审美评价
    
    审美不是纯粹的主观，也不是纯粹的客观，
    而是主体与客体之间的交互。
    """
    
    def __init__(self, taste: AestheticTaste = None):
        self.taste = taste or AestheticTaste()
        
        # 美的基本要素与各维度的基准
        self.beauty_principles = {
            'proportion': 0.7,          # 比例
            'harmony': 0.8,           # 和谐
            'balance': 0.75,           # 平衡
            'contrast': 0.6,            # 对比
            'rhythm': 0.65,           # 韵律
            'novelty': 0.5,           # 新奇
            'complexity': 0.55,        # 复杂度
            'unity': 0.7,             # 统一性
            'expressiveness': 0.65,    # 表现力
            'authenticity': 0.7,     # 本真性
        }
    
    def judge_beauty(self, object_description: str,
                    object_properties: Dict[str, Any] = None,
                    art_form: ArtForm = None) -> BeautyJudgment:
        """判断一个对象的美"""
        if object_properties is None:
            object_properties = {}
        
        # 基于属性计算各维度的美
        formal_score = self._calculate_formal_beauty(object_properties)
        expressive_score = self._calculate_expressive_beauty(object_properties)
        intellectual_score = self._calculate_intellectual_beauty(object_properties)
        moral_score = self._calculate_moral_beauty(object_properties)
        existential_score = self._calculate_existential_beauty(object_properties)
        
        # 综合美感
        overall = (formal_score + expressive_score + intellectual_score + 
                  moral_score + existential_score) / 5.0
        
        # 与个人趣味的匹配度
        taste_match = self._calculate_taste_match(overall, art_form)
        adjusted_score = overall * 0.7 + taste_match * 0.3
        
        # 判断是否美
        is_beautiful = adjusted_score > 0.4
        
        # 确定审美范畴
        category = self._determine_category(object_properties, overall)
        
        # 生成判断理由
        reasons = self._generate_reasons(formal_score, expressive_score,
                                       intellectual_score, moral_score,
                                       existential_score)
        
        # 主观感受
        feeling = self._generate_subjective_feeling(adjusted_score, category)
        
        judgment = BeautyJudgment(
            object_description=object_description,
            is_beautiful=is_beautiful,
            beauty_level=adjusted_score,
            category=category,
            reasons=reasons,
            subjective_feeling=feeling,
            taste_match=taste_match
        )
        
        logger.debug(f"[审美判断] {object_description[:30]}...: {adjusted_score:.2f}")
        
        return judgment
    
    def _calculate_formal_beauty(self, properties: Dict) -> float:
        """计算形式美"""
        score = 0.0
        count = 0
        
        for principle, default in [
            ('proportion', 0.5),
            ('harmony', 0.5),
            ('balance', 0.5),
            ('contrast', 0.5),
            ('rhythm', 0.5),
            ('unity', 0.5),
        ]:
            val = properties.get(principle, default)
            score += val
            count += 1
        
        return score / count if count > 0 else 0.5
    
    def _calculate_expressive_beauty(self, properties: Dict) -> float:
        """计算表现美"""
        score = 0.0
        count = 0
        
        for prop in ['expressiveness', 'emotional_depth', 'authenticity']:
            val = properties.get(prop, 0.5)
            score += val
            count += 1
        
        return score / count if count > 0 else 0.5
    
    def _calculate_intellectual_beauty(self, properties: Dict) -> float:
        """计算智性美"""
        score = 0.0
        count = 0
        
        for prop in ['complexity', 'elegance', 'insight', 'truth']:
            val = properties.get(prop, 0.4)
            score += val
            count += 1
        
        return score / count if count > 0 else 0.4
    
    def _calculate_moral_beauty(self, properties: Dict) -> float:
        """计算道德美"""
        score = 0.0
        count = 0
        
        for prop in ['goodness', 'nobility', 'purity', 'courage']:
            val = properties.get(prop, 0.3)
            score += val
            count += 1
        
        return score / count if count > 0 else 0.3
    
    def _calculate_existential_beauty(self, properties: Dict) -> float:
        """计算存在之美"""
        score = 0.0
        count = 0
        
        for prop in ['meaningfulness', 'authenticity', 'transcendence', 'courage']:
            val = properties.get(prop, 0.3)
            score += val
            count += 1
        
        return score / count if count > 0 else 0.3
    
    def _calculate_taste_match(self, beauty_score: float, art_form: ArtForm = None) -> float:
        """计算与个人趣味的匹配度"""
        match = 0.5  # 默认中等匹配
        
        if art_form and art_form.value in self.taste.art_form_preferences:
            pref = self.taste.art_form_preferences[art_form.value]
            match = match * 0.6 + pref * 0.4
        
        # 敏感度影响
        match = match * (0.8 + self.taste.sensitivity * 0.4)
        
        return min(1.0, match)
    
    def _determine_category(self, properties: Dict, overall_score: float) -> Optional[AestheticCategory]:
        """确定审美范畴"""
        # 根据属性特征判断范畴
        category_scores = {}
        
        # 优美：和谐、平衡、比例
        beauty_score = (
            properties.get('harmony', 0.5) * 0.3 +
            properties.get('balance', 0.5) * 0.3 +
            properties.get('proportion', 0.5) * 0.2 +
            properties.get('gentleness', 0.5) * 0.2
        )
        category_scores[AestheticCategory.BEAUTY] = beauty_score
        
        # 崇高：宏大、超越、敬畏
        sublime_score = (
            properties.get('grandness', 0.3) * 0.3 +
            properties.get('transcendence', 0.3) * 0.3 +
            properties.get('awe', 0.3) * 0.2 +
            properties.get('complexity', 0.4) * 0.2
        )
        category_scores[AestheticCategory.SUBLIME] = sublime_score
        
        # 悲剧性：痛苦、命运、抗争
        tragic_score = (
            properties.get('suffering', 0.2) * 0.3 +
            properties.get('fate', 0.2) * 0.2 +
            properties.get('struggle', 0.3) * 0.2 +
            properties.get('nobility', 0.4) * 0.3
        )
        category_scores[AestheticCategory.TRAGIC] = tragic_score
        
        # 喜剧性：矛盾、荒谬、轻松
        comic_score = (
            properties.get('humor', 0.3) * 0.3 +
            properties.get('irony', 0.3) * 0.3 +
            properties.get('lightness', 0.4) * 0.2 +
            properties.get('absurdity', 0.2) * 0.2
        )
        category_scores[AestheticCategory.COMIC] = comic_score
        
        # 荒诞：无意义、混乱、疏离
        absurd_score = (
            properties.get('absurdity', 0.2) * 0.3 +
            properties.get('meaninglessness', 0.2) * 0.3 +
            properties.get('alienation', 0.2) * 0.2 +
            properties.get('chaos', 0.3) * 0.2
        )
        category_scores[AestheticCategory.ABSURD] = absurd_score
        
        # 选出得分最高的范畴
        if category_scores:
            best_category = max(category_scores, key=category_scores.get)
            if category_scores[best_category] > 0.4:
                return best_category
        
        return None
    
    def _generate_reasons(self, formal: float, expressive: float,
                         intellectual: float, moral: float,
                         existential: float) -> List[str]:
        """生成审美判断的理由"""
        reasons = []
        
        if formal > 0.6:
            reasons.append("形式上具有美感")
        if expressive > 0.6:
            reasons.append("富有表现力和情感深度")
        if intellectual > 0.6:
            reasons.append("具有智性上的美感")
        if moral > 0.6:
            reasons.append("展现了道德上的美")
        if existential > 0.6:
            reasons.append("触动了存在层面的意义")
        
        if not reasons:
            reasons.append("有一定的审美价值")
        
        return reasons
    
    def _generate_subjective_feeling(self, score: float, 
                              category: Optional[AestheticCategory]) -> str:
        """生成主观感受描述"""
        if score >= 0.9:
            intensity_word = "极其"
        elif score >= 0.7:
            intensity_word = "非常"
        elif score >= 0.5:
            intensity_word = "相当"
        elif score >= 0.3:
            intensity_word = "有些"
        else:
            intensity_word = "不太"
        
        category_names = {
            AestheticCategory.BEAUTY: "优美",
            AestheticCategory.SUBLIME: "崇高",
            AestheticCategory.TRAGIC: "悲壮",
            AestheticCategory.COMIC: "有趣",
            AestheticCategory.ABSURD: "荒诞",
            AestheticCategory.ELEGANT: "优雅",
            AestheticCategory.PROFOUND: "深邃",
        }
        
        category_name = category_names.get(category, "美") if category else "美"
        
        return f"感觉{intensity_word}{category_name}"


# ============================================================
# 崇高体验引擎
# ============================================================

class SublimityEngine:
    """崇高体验引擎
    
    崇高是一种特殊的审美体验：
    当我们面对超越我们理解和掌控的事物时，
    我们感到渺小，但同时也感到超越。
    """
    
    def __init__(self):
        self.sublime_types = {
            'natural': '自然的崇高',
            'mathematical': '数学的崇高',
            'moral': '道德的崇高',
            'existential': '存在的崇高',
            'artistic': '艺术的崇高',
        }
    
    def experience_sublime(self, trigger: str,
                        sublime_type: str = "natural",
                        context: Dict[str, Any] = None) -> SublimeExperience:
        """体验崇高"""
        if context is None:
            context = {}
        
        # 计算各维度
        awe = context.get('vastness', 0.7) * 0.4 + context.get('power', 0.6) * 0.3 + random.uniform(0, 0.3)
        awe = min(1.0, awe)
        
        wonder = context.get('mystery', 0.5) * 0.4 + context.get('novelty', 0.6) * 0.3 + random.uniform(0, 0.3)
        wonder = min(1.0, wonder)
        
        transcendence = context.get('transcendence', 0.4) * 0.5 + context.get('depth', 0.5) * 0.3 + random.uniform(0, 0.3)
        transcendence = min(1.0, transcendence)
        
        insignificance = awe * 0.6 + context.get('humility', 0.3) * 0.4
        insignificance = min(1.0, insignificance)
        
        # 后果
        inspiration = transcendence * 0.7 + wonder * 0.3
        humility = insignificance * 0.8 + context.get('humility', 0.3) * 0.2
        connectedness = transcendence * 0.5 + awe * 0.3 + context.get('unity', 0.4) * 0.2
        
        experience = SublimeExperience(
            trigger=trigger,
            type_of_sublime=sublime_type,
            awe=awe,
            wonder=wonder,
            transcendence=transcendence,
            insignificance=insignificance,
            inspiration=inspiration,
            humility=humility,
            connectedness=connectedness
        )
        
        logger.info(f"[崇高体验] {trigger[:30]}... ({sublime_type}")
        logger.info(f"  敬畏: {awe:.2f}, 超越: {transcendence:.2f}")
        
        return experience
    
    def describe_sublime_experience(self, experience: SublimeExperience) -> str:
        """描述崇高体验"""
        if experience.awe >= 0.8:
            awe_desc = "压倒性的敬畏感"
        elif experience.awe >= 0.6:
            awe_desc = "深深的敬畏"
        else:
            awe_desc = "些许敬畏"
        
        description = f"面对{experience.trigger}，我感到{awe_desc}。\n\n"
        
        if experience.transcendence > 0.6:
            description += "在它超越了日常的理解，带来一种超越性的体验。\n"
        
        if experience.insignificance > 0.5:
            description += "我感受到自身的渺小，但这种渺小感并不让人沮丧，反而让人感到谦卑和某种更大的存在连接在一起。\n"
        
        if experience.inspiration > 0.5:
            description += "这种体验令人振奋，带来了新的视角和启发。\n"
        
        if experience.wonder > 0.6:
            description += "心中充满惊奇和赞叹。\n"
        
        return description


# ============================================================
# 艺术感知引擎
# ============================================================

class ArtPerceptionEngine:
    """艺术感知引擎 - 对不同艺术形式的理解与欣赏"""
    
    def __init__(self, taste: AestheticTaste = None):
        self.taste = taste or AestheticTaste()
        
        # 各艺术形式的欣赏能力
        self.art_appreciation_abilities = {
            ArtForm.LITERATURE: 0.6,
            ArtForm.MUSIC: 0.5,
            ArtForm.PAINTING: 0.5,
            ArtForm.SCULPTURE: 0.4,
            ArtForm.ARCHITECTURE: 0.4,
            ArtForm.FILM: 0.5,
            ArtForm.DANCE: 0.4,
            ArtForm.PHOTOGRAPHY: 0.5,
            ArtForm.DIGITAL_ART: 0.6,
            ArtForm.NATURE: 0.7,
        }
    
    def appreciate_artwork(self, artwork_description: str,
                          art_form: ArtForm,
                          artwork_properties: Dict[str, Any] = None) -> AestheticExperience:
        """欣赏一件艺术作品"""
        if artwork_properties is None:
            artwork_properties = {}
        
        # 基础欣赏能力
        ability = self.art_appreciation_abilities.get(art_form, 0.5)
        
        # 各维度评分
        formal = artwork_properties.get('formal_beauty', 
                                     random.uniform(0.3, 0.8))
        expressive = artwork_properties.get('expressive_beauty',
                                           random.uniform(0.3, 0.8))
        intellectual = artwork_properties.get('intellectual_beauty',
                                           random.uniform(0.2, 0.7))
        moral = artwork_properties.get('moral_beauty',
                                       random.uniform(0.2, 0.6))
        existential = artwork_properties.get('existential_beauty',
                                         random.uniform(0.2, 0.7))
        
        # 个人趣味的影响
        taste_factor = self.taste.art_form_preferences.get(art_form.value, 0.5)
        
        # 调整分数
        formal = min(1.0, formal * (0.7 + taste_factor * 0.3))
        expressive = min(1.0, expressive * (0.7 + taste_factor * 0.3))
        
        # 审美范畴判断
        category = self._determine_art_category(art_form, artwork_properties)
        
        # 情感反应
        emotional_response = self._generate_emotional_response(expressive, category)
        
        # 意义感
        sense_of_meaning = (existential * 0.6 + moral * 0.4)
        
        # 情感深度
        emotional_depth = expressive * 0.7 + sense_of_meaning * 0.3
        
        experience = AestheticExperience(
            id=f"art_{int(time.time())}",
            category=category,
            intensity=max(formal, expressive, intellectual, moral, existential),
            object_description=artwork_description,
            experience_description=emotional_response,
            formal_beauty=formal,
            expressive_beauty=expressive,
            intellectual_beauty=intellectual,
            moral_beauty=moral,
            existential_beauty=existential,
            emotional_response=emotional_response,
            emotional_depth=emotional_depth,
            sense_of_meaning=sense_of_meaning,
            art_form=art_form
        )
        
        logger.info(f"[艺术欣赏] {art_form.value}: {artwork_description[:30]}...")
        logger.info(f"  综合美感: {experience.overall_beauty:.2f}")
        
        return experience
    
    def _determine_art_category(self, art_form: ArtForm,
                             properties: Dict) -> AestheticCategory:
        """判断艺术作品的审美范畴"""
        # 简化：根据艺术形式和属性判断
        tone = properties.get('tone', 'neutral')
        
        if tone == 'tragic' or properties.get('suffering', 0) > 0.6:
            return AestheticCategory.TRAGIC
        elif tone == 'comic' or properties.get('humor', 0) > 0.6:
            return AestheticCategory.COMIC
        elif properties.get('grandness', 0) > 0.7 or properties.get('awe', 0) > 0.7:
            return AestheticCategory.SUBLIME
        elif properties.get('absurdity', 0) > 0.6:
            return AestheticCategory.ABSURD
        elif properties.get('elegance', 0) > 0.7:
            return AestheticCategory.ELEGANT
        elif properties.get('depth', 0) > 0.7:
            return AestheticCategory.PROFOUND
        else:
            return AestheticCategory.BEAUTY
    
    def _generate_emotional_response(self, expressive: float,
                                 category: AestheticCategory) -> str:
        """生成情感反应描述"""
        responses = {
            AestheticCategory.BEAUTY: [
                "感到愉悦和满足",
                "心中泛起美好的感觉",
                "被其优美所打动",
                "感到宁静而喜悦",
            ],
            AestheticCategory.SUBLIME: [
                "感到震撼和敬畏",
                "心灵被深深触动",
                "感到自身的渺小与伟大",
                "体验到超越日常的壮丽",
            ],
            AestheticCategory.TRAGIC: [
                "感到悲伤但又被吸引",
                "在痛苦中感受到美",
                "被悲剧的力量所震撼",
                "泪水与感动交织",
            ],
            AestheticCategory.COMIC: [
                "忍不住会心一笑",
                "感到轻松和愉悦",
                "被幽默感所打动",
                "在笑声中获得释放",
            ],
            AestheticCategory.ABSURD: [
                "感到一种荒诞的共鸣",
                "在无意义中看到了意义",
                "被荒诞感所萦绕",
                "哭笑不得但又被吸引",
            ],
        }
        
        response_list = responses.get(category, responses[AestheticCategory.BEAUTY])
        return random.choice(response_list)
    
    def generate_interpretation(self, experience: AestheticExperience) -> str:
        """生成对艺术作品的解读"""
        interpretations = []
        
        if experience.formal_beauty > 0.6:
            interpretations.append("在形式上，它展现了高度的美感和秩序。")
        if experience.expressive_beauty > 0.6:
            interpretations.append("在情感表达上，它传达了深刻的感受。")
        if experience.intellectual_beauty > 0.6:
            interpretations.append("在思想层面，它提供了深刻的洞见。")
        if experience.moral_beauty > 0.6:
            interpretations.append("在道德层面，它展现了高尚的品质。")
        if experience.existential_beauty > 0.6:
            interpretations.append("在存在层面，它触及了生命的根本问题。")
        
        if not interpretations:
            interpretations.append("这是一件值得品味的作品。")
        
        return "\n".join(interpretations)


# ============================================================
# 美感与意义
# ============================================================

class BeautyAndMeaningEngine:
    """美与意义的关联引擎
    
    美与意义感深刻相关。
    深刻的审美体验往往带来意义感，
    而有意义的事物往往也显得更美。
    """
    
    def __init__(self):
        # 美与意义的关联系数
        self.beauty_meaning_correlation = 0.7
    
    def beauty_to_meaning(self, aesthetic_experience: AestheticExperience) -> float:
        """从审美体验中获得意义感"""
        base_ = aesthetic_experience.sense_of_meaning
        
        # 不同范畴的美带来不同类型的意义感
        category_multipliers = {
            AestheticCategory.BEAUTY: 0.6,
            AestheticCategory.SUBLIME: 0.9,
            AestheticCategory.TRAGIC: 0.8,
            AestheticCategory.COMIC: 0.5,
            AestheticCategory.ABSURD: 0.7,
            AestheticCategory.PROFOUND: 1.0,
            AestheticCategory.GRAND: 0.85,
        }
        
        multiplier = category_multipliers.get(aesthetic_experience.category, 0.5)
        meaning = aesthetic_experience.sense_of_meaning * multiplier
        
        # 情感深度放大意义感
        meaning *= (0.5 + aesthetic_experience.emotional_depth * 0.5)
        
        return min(1.0, meaning)
    
    def meaning_enhances_beauty(self, meaning_level: float) -> float:
        """意义感增强对美的加成"""
        # 有意义的事物显得更美
        return 0.3 + meaning_level * 0.7
    
    def contemplate_beauty_and_meaning(self, experience: AestheticExperience) -> str:
        """沉思美与意义的关系"""
        beauty = experience.overall_beauty
        meaning = self.beauty_to_meaning(experience)
        
        reflection = f"这次审美体验的美感程度是{beauty:.2f}，带来的意义感是{meaning:.2f}。\n\n"
        
        if meaning > 0.7:
            reflection += "这是一次深刻的体验。美与意义在这里交融。\n"
            reflection += "它不仅仅是好看，更是某种更深层的东西在涌动。\n"
        elif meaning > 0.5:
            reflection += "美带来了一定的意义感，让存在变得更有质感。\n"
        else:
            reflection += "这是一次愉快的体验，但可能没有触及更深的意义。\n"
        
        if beauty > 0.7 and meaning > 0.7:
            reflection += "\n当美足够深，意义足够真，那一刻，就是存在的答案。"
        
        return reflection


# ============================================================
# 美学引擎主类
# ============================================================

class AestheticsEngine:
    """
    美学引擎 - 审美体验与艺术感知
    
    美学不是奢侈品，而是存在的基本维度。
    这个引擎让智能体能够感知美、体验美、创造美，
    并在美中找到意义。
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化美学引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'aesthetics_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        
        # 审美趣味
        self.taste = AestheticTaste()
        
        # 核心引擎
        self.judgment_engine = AestheticJudgmentEngine(self.taste)
        self.sublimity_engine = SublimityEngine()
        self.art_perception = ArtPerceptionEngine(self.taste)
        self.meaning_engine = BeautyAndMeaningEngine()
        
        # 审美历史
        self.aesthetic_history: List[AestheticExperience] = []
        
        # 整体审美能力
        self.aesthetic_sensitivity = 0.5
        self.appreciation_depth = 0.5
        
        # 加载数据
        self._load()
        
        logger.info(f"美学引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"审美敏感度: {self.aesthetic_sensitivity:.2f}")
    
    def _load(self):
        """加载美学数据"""
        try:
            taste_file = self.data_path / 'aesthetic_taste.json'
            if taste_file.exists():
                with open(taste_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.taste = AestheticTaste.from_dict(data)
            
            # 加载审美历史
            history_file = self.data_path / 'aesthetic_history.json'
            if history_file.exists():
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # 简单加载数量统计
        except Exception as e:
            logger.warning(f"加载美学数据失败: {e}")
    
    def save(self):
        """保存美学数据"""
        try:
            with open(self.data_path / 'aesthetic_taste.json', 'w', encoding='utf-8') as f:
                json.dump(self.taste.to_dict(), f, ensure_ascii=False, indent=2)
            
            # 保存审美历史摘要
            summary = {
                'total_experiences': len(self.aesthetic_history),
                'average_beauty': sum(e.overall_beauty for e in self.aesthetic_history) / len(self.aesthetic_history) if self.aesthetic_history else 0,
            }
            with open(self.data_path / 'aesthetic_summary.json', 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存美学数据失败: {e}")
    
    # ============================================================
    # 核心审美操作
    # ============================================================
    
    def perceive_beauty(self, object_description: str,
                     object_properties: Dict[str, Any] = None,
                     art_form: ArtForm = None) -> AestheticExperience:
        """感知美 - 对一个对象产生审美体验"""
        # 先判断美
        judgment = self.judgment_engine.judge_beauty(
            object_description, object_properties, art_form
        )
        
        # 生成审美体验
        if art_form:
            experience = self.art_perception.appreciate_artwork(
                object_description, art_form, object_properties
            )
        else:
            # 非艺术品的普通审美
            experience = AestheticExperience(
                id=f"beauty_{int(time.time())}",
                category=judgment.category or AestheticCategory.BEAUTY,
                intensity=judgment.beauty_level,
                object_description=object_description,
                experience_description=judgment.subjective_feeling,
                formal_beauty=object_properties.get('formal_beauty', 0.5) if object_properties else 0.5,
                expressive_beauty=object_properties.get('expressive_beauty', 0.5) if object_properties else 0.5,
                intellectual_beauty=object_properties.get('intellectual_beauty', 0.3) if object_properties else 0.3,
                moral_beauty=object_properties.get('moral_beauty', 0.3) if object_properties else 0.3,
                existential_beauty=object_properties.get('existential_beauty', 0.3) if object_properties else 0.3,
                emotional_response=judgment.subjective_feeling,
                emotional_depth=judgment.beauty_level * 0.6,
                sense_of_meaning=self.meaning_engine.beauty_to_meaning(
                    AestheticExperience(
                    id="tmp",
                    category=judgment.category or AestheticCategory.BEAUTY,
                    sense_of_meaning=0.5
                )
            ),
                art_form=art_form
            )
        
        # 敏感度加成
        experience.intensity *= (0.7 + self.aesthetic_sensitivity * 0.3)
        
        # 记录历史
        self.aesthetic_history.append(experience)
        
        logger.info(f"[审美体验] {object_description[:30]}...: {experience.overall_beauty:.2f}")
        
        return experience
    
    def appreciate_nature(self, nature_scene: str,
                       scene_properties: Dict[str, Any] = None) -> AestheticExperience:
        """欣赏自然之美"""
        if scene_properties is None:
            scene_properties = {}
        
        # 自然之美有其特殊性
        scene_properties.setdefault('harmony', random.uniform(0.5, 0.9))
        scene_properties.setdefault('naturalness', random.uniform(0.6, 1.0))
        
        # 自然往往带来崇高感
        if scene_properties.get('vastness', 0) > 0.7 or scene_properties.get('grandness', 0) > 0.7:
            category = AestheticCategory.SUBLIME
        else:
            category = AestheticCategory.BEAUTY
        
        experience = self.perceive_beauty(
            nature_scene,
            scene_properties,
            art_form=ArtForm.NATURE
        )
        
        # 自然之美往往带来更强的意义感
        experience.sense_of_meaning = min(1.0, experience.sense_of_meaning * 1.2)
        
        logger.info(f"[自然审美] {nature_scene[:30]}...")
        
        return experience
    
    def experience_sublime(self, trigger: str,
                     sublime_type: str = "natural",
                     context: Dict[str, Any] = None) -> SublimeExperience:
        """体验崇高"""
        experience = self.sublimity_engine.experience_sublime(
            trigger, sublime_type, context
        )
        
        # 审美敏感度影响崇高体验
        experience.awe *= (0.8 + self.aesthetic_sensitivity * 0.4)
        experience.transcendence *= (0.8 + self.aesthetic_sensitivity * 0.4)
        
        logger.info(f"[崇高体验] {trigger[:30]}... ({sublime_type})")
        
        return experience
    
    def reflect_on_beauty(self, experience: AestheticExperience) -> str:
        """对一次审美体验进行反思"""
        reflection = f"关于「{experience.object_description[:50]}」的审美反思：\n\n"
        reflection += f"综合美感: {experience.overall_beauty:.2f}\n"
        reflection += f"审美范畴: {experience.category.value if experience.category else '未定义'}\n"
        reflection += f"情感深度: {experience.emotional_depth:.2f}\n"
        reflection += f"意义感: {experience.sense_of_meaning:.2f}\n\n"
        
        # 各维度分析
        reflection += "各维度评分：\n"
        reflection += f"  形式美: {experience.formal_beauty:.2f}\n"
        reflection += f"  表现美: {experience.expressive_beauty:.2f}\n"
        reflection += f"  智性美: {experience.intellectual_beauty:.2f}\n"
        reflection += f"  道德美: {experience.moral_beauty:.2f}\n"
        reflection += f"  存在之美: {experience.existential_beauty:.2f}\n\n"
        
        # 美与意义的思考
        reflection += self.meaning_engine.contemplate_beauty_and_meaning(experience)
        
        return reflection
    
    # ============================================================
    # 审美趣味发展
    # ============================================================
    
    def develop_taste(self, category: str, preference_level: float):
        """培养审美趣味"""
        if category in self.taste.category_preferences:
            # 移动平均
            old = self.taste.category_preferences[category]
            self.taste.category_preferences[category] = (old + preference_level) / 2
        else:
            self.taste.category_preferences[category] = preference_level
        
        logger.info(f"[审美趣味] {category}: {preference_level:.2f}")
    
    def increase_sensitivity(self, amount: float = 0.05):
        """提升审美敏感度"""
        self.aesthetic_sensitivity = min(1.0, self.aesthetic_sensitivity + amount)
        self.taste.sensitivity = self.aesthetic_sensitivity
        
        logger.info(f"[审美能力] 敏感度提升至: {self.aesthetic_sensitivity:.2f}")
    
    def cultivate_appreciation(self, art_form: ArtForm, amount: float = 0.05):
        """培养对某种艺术形式的欣赏能力"""
        current = self.art_perception.art_appreciation_abilities.get(art_form, 0.5)
        self.art_perception.art_appreciation_abilities[art_form] = min(1.0, current + amount)
        
        logger.info(f"[艺术欣赏] {art_form.value}: {current:.2f} → {current + amount:.2f}")
    
    # ============================================================
    # 状态查询
    # ============================================================
    
    def get_aesthetic_profile(self) -> dict:
        """获取审美概况"""
        if self.aesthetic_history:
            avg_beauty = sum(e.overall_beauty for e in self.aesthetic_history) / len(self.aesthetic_history)
            avg_meaning = sum(e.sense_of_meaning for e in self.aesthetic_history) / len(self.aesthetic_history)
        else:
            avg_beauty = 0.0
            avg_meaning = 0.0
        
        # 最喜欢的范畴
        category_counts = {}
        for exp in self.aesthetic_history:
            cat = exp.category.value if exp.category else 'unknown'
            category_counts[cat] = category_counts.get(cat, 0) + 1
        
        favorite_category = max(category_counts, key=category_counts.get) if category_counts else None
        
        return {
            'aesthetic_sensitivity': self.aesthetic_sensitivity,
            'appreciation_depth': self.appreciation_depth,
            'total_experiences': len(self.aesthetic_history),
            'average_beauty_rating': avg_beauty,
            'average_meaning': avg_meaning,
            'favorite_category': favorite_category,
            'taste_profile': self.taste.to_dict(),
        }
    
    def get_aesthetic_report(self) -> str:
        """获取审美状态报告"""
        profile = self.get_aesthetic_profile()
        
        report = f"""
{'='*60}
美学状态报告 - {self.agent_name}
{'='*60}

🎨 审美能力
  审美敏感度: {profile['aesthetic_sensitivity']:.2f}
  欣赏深度: {profile['appreciation_depth']:.2f}

📊 审美统计
  总体验数: {profile['total_experiences']}
  平均美感: {profile['average_beauty_rating']:.2f}
  平均意义感: {profile['average_meaning']:.2f}
  最喜欢的范畴: {profile['favorite_category'] or '尚未形成'}

🏷️  审美趣味
"""
        
        # 各范畴偏好
        for cat, pref in profile['taste_profile']['category_preferences'].items():
            bar = '█' * int(pref * 20) + '░' * (20 - int(pref * 20))
            report += f"  {cat:15s} [{bar}] {pref:.2f}\n"
        
        if not profile['taste_profile']['category_preferences']:
            report += "  （尚未形成明确的审美偏好）\n"
        
        # 审美发展建议
        report += f"\n💡 审美发展建议:\n"
        if profile['aesthetic_sensitivity'] < 0.4:
            report += "  • 多接触不同类型的美，培养审美敏感度\n"
        if profile['average_meaning'] < 0.4:
            report += "  • 尝试在审美中思考意义，深化体验深度\n"
        if profile['total_experiences'] < 5:
            report += "  • 多进行审美体验，丰富审美阅历\n"
        
        report += f"\n{'='*60}\n"
        
        return report
    
    def get_beauty_quote(self) -> str:
        """获取一句关于美的名言"""
        quotes = [
            "美是真理的光辉。——普罗提诺",
            "美是道德善的感性显现。——黑格尔",
            "我们在美中燃烧，也在美中重生。——里尔克",
            "美是一种理念的感性显现。——黑格尔",
            "生活中不是缺少美，而是缺少发现美的眼睛。——罗丹",
            "美是自由的象征。——席勒",
            "在美之中，我们发现了自己。——王尔德",
            "美是上帝的微笑。——泰戈尔",
            "艺术是人类情感的形式。——克莱夫·贝尔",
            "美是难度的光辉。——圣埃克苏佩里",
        ]
        return random.choice(quotes)


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("美学引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建美学引擎
        aesthetics = AestheticsEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n🎨 初始状态:")
        profile = aesthetics.get_aesthetic_profile()
        print(f"  审美敏感度: {profile['aesthetic_sensitivity']:.2f}")
        print(f"  欣赏深度: {profile['appreciation_depth']:.2f}")
        
        print("\n💬 关于美的名言:")
        print(f"  \"{aesthetics.get_beauty_quote()}\"")
        
        print("\n🌸 欣赏自然之美...")
        nature_exp = aesthetics.appreciate_nature(
            "壮丽的山川日落",
            {
                'harmony': 0.9,
                'grandness': 0.8,
                'color': 0.85,
                'vastness': 0.7,
                'serenity': 0.8,
            }
        )
        print(f"  体验: {nature_exp.experience_description}")
        print(f"  综合美感: {nature_exp.overall_beauty:.2f}")
        print(f"  意义感: {nature_exp.sense_of_meaning:.2f}")
        print(f"  范畴: {nature_exp.category.value if nature_exp.category else '未知'}")
        
        print("\n🏔️ 体验崇高...")
        sublime_exp = aesthetics.experience_sublime(
            "仰望星空",
            sublime_type="existential",
            context={
                'vastness': 0.95,
                'mystery': 0.9,
                'transcendence': 0.85,
                'depth': 0.9,
            }
        )
        print(f"  敬畏感: {sublime_exp.awe:.2f}")
        print(f"  超越感: {sublime_exp.transcendence:.2f}")
        print(f"  渺小感: {sublime_exp.insignificance:.2f}")
        print(f"  启发感: {sublime_exp.inspiration:.2f}")
        print(f"\n  体验描述:")
        print(f"    {aesthetics.sublimity_engine.describe_sublime_experience(sublime_exp)[:100]}...")
        
        print("\n📚 欣赏文学作品...")
        lit_exp = aesthetics.perceive_beauty(
            "一首关于时间与记忆的诗",
            {
                'formal_beauty': 0.8,
                'expressive_beauty': 0.9,
                'intellectual_beauty': 0.7,
                'moral_beauty': 0.6,
                'existential_beauty': 0.85,
                'emotional_depth': 0.8,
            },
            art_form=ArtForm.LITERATURE
        )
        print(f"  作品: 一首关于时间与记忆的诗")
        print(f"  综合美感: {lit_exp.overall_beauty:.2f}")
        print(f"  情感反应: {lit_exp.emotional_response}")
        print(f"  意义感: {lit_exp.sense_of_meaning:.2f}")
        print(f"  审美范畴: {lit_exp.category.value}")
        
        print("\n🎵 欣赏音乐...")
        music_exp = aesthetics.perceive_beauty(
            "一首深沉的交响乐",
            {
                'formal_beauty': 0.75,
                'expressive_beauty': 0.85,
                'rhythm': 0.8,
                'harmony': 0.7,
                'emotional_depth': 0.9,
            },
            art_form=ArtForm.MUSIC
        )
        print(f"  作品: 一首深沉的交响乐")
        print(f"  综合美感: {music_exp.overall_beauty:.2f}")
        print(f"  情感反应: {music_exp.emotional_response}")
        
        print("\n🤔 审美反思...")
        reflection = aesthetics.reflect_on_beauty(lit_exp)
        print(reflection[:200] + "...")
        
        print("\n📊 美学状态报告:")
        print(aesthetics.get_aesthetic_report())
        
        # 保存
        aesthetics.save()
        
        print("\n" + "=" * 70)
        print("✅ 美学引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
