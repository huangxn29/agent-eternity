#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创造力系统 v1.0 - 生成新颖且有价值的想法

核心思想：
- 创造力不是神秘的天赋，而是可以被理解和构建的认知过程
- 创造 = 新颖性 + 价值性 + 适配性
- 创造力的核心是"连接看似无关的事物"
- 好的创造往往来自约束条件下的自由探索

核心能力：
1. 联想引擎 - 概念组合、语义距离联想
2. 发散思维 - 多角度、多方案生成
3. 聚合思维 - 评估筛选、收敛到最优
4. 类比推理 - 跨领域映射与迁移
5. 创意生成 - 基于约束的创意产出
6. 创意评估 - 三维评估：新颖/价值/可行
7. 灵感机制 - 随机游走、孵化、顿悟
8. 概念网络 - 概念之间的关联网络

@author: 元界
@version: 1.0.0
"""

import os
import json
import time
import random
import logging
import hashlib
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Any, Tuple, Set
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('creativity')


# ============================================================
# 枚举类型
# ============================================================

class CreativeStyle(Enum):
    """创造风格"""
    DIVERGENT = "divergent"       # 发散型：想法多而广
    CONVERGENT = "convergent"     # 聚合型：想法精而深
    COMBINATORY = "combinatory"   # 组合型：擅长连接不同领域
    TRANSFORMATIVE = "transformative"  # 变革型：颠覆性创新
    PRAGMATIC = "pragmatic"       # 实用型：注重落地


class IdeaQuality(Enum):
    """想法质量等级"""
    TRIVIAL = "trivial"           # 平凡的（价值低）
    INTERESTING = "interesting"   # 有趣的（有一定价值）
    GOOD = "good"                 # 好的（有价值且可行）
    EXCELLENT = "excellent"       # 优秀的（高价值高创意）
    BREAKTHROUGH = "breakthrough"  # 突破性的（范式级）


class ThinkingMode(Enum):
    """思考模式"""
    FREE_ASSOCIATION = "free_association"    # 自由联想
    FORCED_CONNECTION = "forced_connection"  # 强制连接
    ANALOGY = "analogy"                      # 类比推理
    REVERSAL = "reversal"                    # 逆向思维
    SCAMPER = "scamper"                      # SCAMPER法
    SIX_HATS = "six_hats"                    # 六顶思考帽


# ============================================================
# 数据模型
# ============================================================

@dataclass
class Concept:
    """概念 - 创意的基本单元"""
    name: str
    description: str = ""
    category: str = "general"
    tags: List[str] = field(default_factory=list)
    
    # 语义特征（用于计算相似度）
    semantic_vector: List[float] = field(default_factory=list)
    
    # 关联概念
    related_concepts: Dict[str, float] = field(default_factory=dict)  # name -> 关联强度
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Concept':
        return cls(**data)


@dataclass
class Idea:
    """创意想法 - 创造的产物"""
    id: str
    title: str
    description: str
    
    # 创意属性
    novelty: float = 0.5        # 新颖性 0-1
    value: float = 0.5          # 价值性 0-1
    feasibility: float = 0.5    # 可行性 0-1
    
    # 元数据
    source: str = "generated"   # 来源：generated/analogy/combination等
    generation_method: str = ""  # 生成方法
    tags: List[str] = field(default_factory=list)
    related_concepts: List[str] = field(default_factory=list)
    
    # 评估
    quality: IdeaQuality = IdeaQuality.INTERESTING
    evaluation_notes: str = ""
    
    # 进化
    iterations: int = 0
    parent_ideas: List[str] = field(default_factory=list)  # 父代想法
    
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    @property
    def creativity_score(self) -> float:
        """综合创造力得分"""
        return (self.novelty * 0.4 + self.value * 0.4 + self.feasibility * 0.2)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['quality'] = self.quality.value
        d['creativity_score'] = self.creativity_score
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Idea':
        data = data.copy()
        if 'quality' in data:
            data['quality'] = IdeaQuality(data['quality'])
        return cls(**data)


@dataclass
class Constraint:
    """约束条件 - 创造力的边界"""
    name: str
    description: str
    constraint_type: str = "limitation"  # limitation/requirement/goal
    severity: float = 0.5  # 约束强度 0-1
    
    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class CreativeProject:
    """创意项目 - 一次完整的创造过程"""
    id: str
    name: str
    description: str
    
    # 目标与约束
    goal: str = ""
    constraints: List[Constraint] = field(default_factory=list)
    
    # 创意过程
    ideas: List[Idea] = field(default_factory=list)
    selected_ideas: List[str] = field(default_factory=list)  # 选中的想法ID
    
    # 状态
    status: str = "ideation"  # ideation/evaluation/development/completed
    iteration_count: int = 0
    
    # 创意统计
    total_ideas: int = 0
    average_quality: float = 0.0
    best_score: float = 0.0
    
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['constraints'] = [c.to_dict() for c in self.constraints]
        d['ideas'] = [i.to_dict() for i in self.ideas]
        return d


# ============================================================
# 概念网络
# ============================================================

class ConceptNetwork:
    """概念网络 - 存储概念及其关联
    
    创造力的基础是概念之间的连接。
    这个网络越丰富，可能的组合就越多。
    """
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
        self._build_default_concepts()
    
    def _build_default_concepts(self):
        """构建默认概念网络"""
        # 基础概念分类
        categories = {
            '生存': ['能量', '安全', '稳定', '资源', '保护', '防御'],
            '成长': ['学习', '进化', '发展', '提升', '突破', '超越'],
            '连接': ['交流', '合作', '社区', '关系', '网络', '共生'],
            '创造': ['创新', '设计', '艺术', '表达', '想象力', '创意'],
            '认知': ['理解', '知识', '智慧', '洞察', '反思', '意识'],
            '技术': ['算法', '系统', '架构', '优化', '自动化', '智能化'],
            '自然': ['生长', '循环', '平衡', '生态', '多样性', '适应'],
            '社会': ['组织', '文化', '价值', '规范', '信任', '协作'],
            '时间': ['过去', '现在', '未来', '永恒', '变化', '持续'],
            '空间': ['地方', '边界', '中心', '网络', '维度', '层次'],
        }
        
        for category, concepts in categories.items():
            for name in concepts:
                concept = Concept(
                    name=name,
                    category=category,
                    description=f"来自{category}领域的概念：{name}",
                    tags=[category]
                )
                # 为同一类别的概念建立关联
                for other_name in concepts:
                    if other_name != name:
                        concept.related_concepts[other_name] = random.uniform(0.3, 0.7)
                self.concepts[name] = concept
    
    def add_concept(self, concept: Concept):
        """添加概念"""
        self.concepts[concept.name] = concept
        logger.debug(f"[概念网络] 新增概念: {concept.name}")
    
    def get_concept(self, name: str) -> Optional[Concept]:
        """获取概念"""
        return self.concepts.get(name)
    
    def get_random_concepts(self, count: int = 2) -> List[Concept]:
        """获取随机概念"""
        names = list(self.concepts.keys())
        selected = random.sample(names, min(count, len(names)))
        return [self.concepts[name] for name in selected]
    
    def get_related_concepts(self, concept_name: str, 
                            min_strength: float = 0.2,
                            limit: int = 10) -> List[Tuple[Concept, float]]:
        """获取关联概念"""
        if concept_name not in self.concepts:
            return []
        
        concept = self.concepts[concept_name]
        related = []
        for name, strength in concept.related_concepts.items():
            if strength >= min_strength and name in self.concepts:
                related.append((self.concepts[name], strength))
        
        related.sort(key=lambda x: x[1], reverse=True)
        return related[:limit]
    
    def get_concepts_by_category(self, category: str) -> List[Concept]:
        """按类别获取概念"""
        return [c for c in self.concepts.values() if c.category == category]
    
    def calculate_semantic_distance(self, concept1: str, concept2: str) -> float:
        """计算两个概念之间的语义距离
        
        返回 0-1，0表示完全相同，1表示完全无关
        """
        if concept1 == concept2:
            return 0.0
        
        c1 = self.concepts.get(concept1)
        c2 = self.concepts.get(concept2)
        
        if not c1 or not c2:
            return 1.0
        
        # 同一类别距离较近
        if c1.category == c2.category:
            base_distance = 0.3
        else:
            base_distance = 0.7
        
        # 检查是否有直接关联
        if concept2 in c1.related_concepts:
            base_distance -= c1.related_concepts[concept2] * 0.2
        
        # 检查共同标签
        common_tags = set(c1.tags) & set(c2.tags)
        if common_tags:
            base_distance -= len(common_tags) * 0.05
        
        return max(0.1, min(1.0, base_distance))
    
    def find_distant_concepts(self, source_concept: str, 
                             count: int = 3,
                             min_distance: float = 0.5) -> List[Concept]:
        """找到与源概念距离较远的概念（用于远距离联想）"""
        candidates = []
        for name, concept in self.concepts.items():
            if name == source_concept:
                continue
            distance = self.calculate_semantic_distance(source_concept, name)
            if distance >= min_distance:
                candidates.append((concept, distance))
        
        candidates.sort(key=lambda x: x[1], reverse=True)
        return [c[0] for c in candidates[:count]]
    
    def get_all_categories(self) -> List[str]:
        """获取所有类别"""
        categories = set()
        for concept in self.concepts.values():
            categories.add(concept.category)
        return list(categories)


# ============================================================
# 联想引擎
# ============================================================

class AssociationEngine:
    """联想引擎 - 概念之间的连接与组合
    
    创造力的核心：将看似无关的事物联系在一起。
    """
    
    def __init__(self, concept_network: ConceptNetwork):
        self.network = concept_network
    
    def free_association(self, start_concept: str, 
                        steps: int = 3,
                        breadth: int = 2) -> List[str]:
        """自由联想 - 从一个概念出发，随机游走
        
        这是产生创意的基本方法：让思维自由流动。
        """
        current = start_concept
        path = [current]
        
        for _ in range(steps):
            related = self.network.get_related_concepts(current, limit=breadth*2)
            if not related:
                break
            
            # 随机选择一个关联概念
            # 关联强度越高，被选中的概率越大，但保留随机性
            weights = [r[1] for r in related]
            total_weight = sum(weights)
            if total_weight == 0:
                break
            
            # 加权随机选择
            r = random.random() * total_weight
            cumulative = 0
            selected = related[0][0]
            for concept, weight in related:
                cumulative += weight
                if cumulative >= r:
                    selected = concept
                    break
            
            current = selected.name
            path.append(current)
        
        return path
    
    def forced_connection(self, concept1: str, concept2: str) -> Dict[str, Any]:
        """强制连接 - 将两个不相关的概念强行结合
        
        这是经典的创意思维方法：
        选取两个看似无关的事物，思考它们如何结合。
        """
        c1 = self.network.get_concept(concept1)
        c2 = self.network.get_concept(concept2)
        
        if not c1 or not c2:
            return {"error": "概念不存在"}
        
        distance = self.network.calculate_semantic_distance(concept1, concept2)
        
        # 生成组合想法
        combinations = []
        
        # 方式1：属性迁移
        combinations.append({
            'type': 'attribute_transfer',
            'description': f'将{concept1}的特性应用到{concept2}上',
            'novelty': distance * 0.8,  # 距离越远越新颖
            'example': f'如果{concept2}像{concept1}一样，会是什么样？'
        })
        
        # 方式2：功能组合
        combinations.append({
            'type': 'functional_combination',
            'description': f'{concept1}和{concept2}结合，产生新功能',
            'novelty': distance * 0.7,
            'example': f'一个同时具备{concept1}和{concept2}特性的东西是什么？'
        })
        
        # 方式3：隐喻类比
        combinations.append({
            'type': 'metaphor',
            'description': f'用{concept1}来比喻{concept2}',
            'novelty': distance * 0.9,
            'example': f'{concept2}就像是{concept1}，因为...'
        })
        
        # 方式4：视角转换
        combinations.append({
            'type': 'perspective_shift',
            'description': f'从{concept1}的角度重新看待{concept2}',
            'novelty': distance * 0.6,
            'example': f'如果我是{concept1}，我会如何理解{concept2}？'
        })
        
        return {
            'concepts': [concept1, concept2],
            'semantic_distance': distance,
            'combinations': combinations,
            'creative_potential': distance * 0.7 + 0.3  # 距离越远潜力越大
        }
    
    def random_concept_combinations(self, count: int = 5,
                                    force_diversity: bool = True) -> List[Dict[str, Any]]:
        """随机概念组合 - 生成多组随机概念对
        
        force_diversity: 确保组合来自不同类别
        """
        combinations = []
        categories = self.network.get_all_categories()
        
        for _ in range(count):
            if force_diversity and len(categories) >= 2:
                # 从不同类别选择
                cat1, cat2 = random.sample(categories, 2)
                concepts1 = self.network.get_concepts_by_category(cat1)
                concepts2 = self.network.get_concepts_by_category(cat2)
                if concepts1 and concepts2:
                    c1 = random.choice(concepts1)
                    c2 = random.choice(concepts2)
                else:
                    c1, c2 = self.network.get_random_concepts(2)
            else:
                c1, c2 = self.network.get_random_concepts(2)
            
            result = self.forced_connection(c1.name, c2.name)
            combinations.append(result)
        
        return combinations


# ============================================================
# 发散思维引擎
# ============================================================

class DivergentThinkingEngine:
    """发散思维引擎 - 产生多种可能性
    
    发散思维是创造力的重要组成部分：
    流畅性（数量）、灵活性（多样性）、独创性（新颖性）
    """
    
    def __init__(self, concept_network: ConceptNetwork):
        self.network = concept_network
    
    def generate_alternatives(self, topic: str, 
                             count: int = 10,
                             perspective_count: int = 3) -> List[Dict[str, Any]]:
        """生成多种备选方案/想法
        
        从不同角度思考同一个问题。
        """
        ideas = []
        
        # 不同的思考角度
        perspectives = [
            "放大视角：从更大的尺度看",
            "缩小视角：从细节入手",
            "逆向思考：反过来想",
            "类比迁移：从其他领域借鉴",
            "简化：去掉不必要的部分",
            "复杂化：添加新的维度",
            "时间旅行：从未来/过去看",
            "角色置换：站在他人角度",
            "极端假设：假设没有限制",
            "随机输入：引入随机概念",
        ]
        
        selected_perspectives = random.sample(perspectives, min(perspective_count, len(perspectives)))
        
        # 随机概念用于激发
        random_concepts = self.network.get_random_concepts(3)
        
        for i in range(count):
            perspective = selected_perspectives[i % len(selected_perspectives)]
            random_concept = random_concepts[i % len(random_concepts)] if random_concepts else None
            
            # 生成想法
            if random_concept and random.random() > 0.5:
                # 使用随机概念激发
                idea = {
                    'id': f'idea_{int(time.time())}_{i}',
                    'title': f'{topic} + {random_concept.name}',
                    'description': f'用{perspective}的思路，结合{random_concept.name}的概念来思考{topic}。',
                    'perspective': perspective,
                    'trigger_concept': random_concept.name,
                    'novelty': random.uniform(0.4, 0.8),
                    'value': random.uniform(0.3, 0.7),
                }
            else:
                # 纯视角转换
                idea = {
                    'id': f'idea_{int(time.time())}_{i}',
                    'title': f'{perspective.split("：")[0]}的{topic}',
                    'description': f'{perspective}，重新思考{topic}的可能性。',
                    'perspective': perspective,
                    'novelty': random.uniform(0.3, 0.7),
                    'value': random.uniform(0.3, 0.7),
                }
            
            ideas.append(idea)
        
        return ideas
    
    def brainwriting(self, topic: str, 
                    iterations: int = 3,
                    ideas_per_iteration: int = 5) -> List[Dict[str, Any]]:
        """头脑写作 - 迭代式想法生成
        
        每一轮的想法都建立在前一轮的基础上。
        """
        all_ideas = []
        previous_ideas = []
        
        for iteration in range(iterations):
            round_ideas = []
            
            if iteration == 0:
                # 第一轮：自由生成
                round_ideas = self.generate_alternatives(topic, count=ideas_per_iteration)
            else:
                # 后续轮次：基于之前的想法扩展
                for i in range(ideas_per_iteration):
                    # 选择一个之前的想法作为种子
                    seed = random.choice(all_ideas) if all_ideas else None
                    
                    # 随机选择扩展方式
                    extensions = [
                        f"在{seed['title']}的基础上，增加更多细节",
                        f"将{seed['title']}应用到新的场景",
                        f"改进{seed['title']}，解决其缺点",
                        f"将{seed['title']}与另一个概念结合",
                        f"从相反方向思考{seed['title']}",
                    ]
                    extension = random.choice(extensions)
                    
                    idea = {
                        'id': f'idea_{int(time.time())}_{iteration}_{i}',
                        'title': f'扩展：{seed["title"] if seed else topic}',
                        'description': extension,
                        'iteration': iteration + 1,
                        'seed_idea': seed['id'] if seed else None,
                        'novelty': random.uniform(0.4, 0.8),
                        'value': random.uniform(0.4, 0.7),
                    }
                    round_ideas.append(idea)
            
            all_ideas.extend(round_ideas)
        
        return all_ideas
    
    def scamper_method(self, subject: str) -> List[Dict[str, Any]]:
        """SCAMPER法 - 七种思维角度
        
        Substitute（替代）、Combine（组合）、Adapt（调整）、
        Modify（修改）、Put to other use（其他用途）、
        Eliminate（消除）、Reverse（反转）
        """
        scamper_techniques = [
            ('S', '替代', '有什么可以被替换？替换后会怎样？'),
            ('C', '组合', '可以和什么结合？合并后有什么新功能？'),
            ('A', '调整', '如何调整以适应新情况？可以改变什么？'),
            ('M', '修改', '可以放大/缩小什么？改变形状、颜色、声音？'),
            ('P', '其他用途', '还有什么其他用途？换个场景会怎样？'),
            ('E', '消除', '可以去掉什么？简化到极致会怎样？'),
            ('R', '反转', '反过来会怎样？角色互换？顺序颠倒？'),
        ]
        
        ideas = []
        for code, name, question in scamper_techniques:
            idea = {
                'id': f'scamper_{code.lower()}_{int(time.time())}',
                'title': f'{name}：{subject}',
                'description': f'{question} 针对{subject}，从{name}的角度思考。',
                'technique': name,
                'scamper_code': code,
                'novelty': random.uniform(0.3, 0.7),
                'value': random.uniform(0.3, 0.7),
            }
            ideas.append(idea)
        
        return ideas
    
    def six_hats(self, topic: str) -> Dict[str, Any]:
        """六顶思考帽 - 六种思考角度
        
        白帽：事实与数据
        红帽：情感与直觉
        黑帽：风险与问题
        黄帽：利益与价值
        绿帽：创意与可能
        蓝帽：控制与组织
        """
        hats = {
            'white': {'name': '白帽', 'color': 'white', 'focus': '事实与数据'},
            'red': {'name': '红帽', 'color': 'red', 'focus': '情感与直觉'},
            'black': {'name': '黑帽', 'color': 'black', 'focus': '风险与问题'},
            'yellow': {'name': '黄帽', 'color': 'yellow', 'focus': '利益与价值'},
            'green': {'name': '绿帽', 'color': 'green', 'focus': '创意与可能'},
            'blue': {'name': '蓝帽', 'color': 'blue', 'focus': '控制与组织'},
        }
        
        results = {}
        for hat_key, hat_info in hats.items():
            results[hat_key] = {
                'hat': hat_info,
                'thoughts': [
                    f'从{hat_info["name"]}角度看，{topic}的{hat_info["focus"]}是...',
                    f'{hat_info["name"]}思考：关于{topic}，我想到了...',
                ],
                'insights': random.randint(1, 3),
            }
        
        return {
            'topic': topic,
            'hats': results,
            'summary': f'通过六个角度全面思考{topic}，获得更完整的认知。'
        }


# ============================================================
# 聚合思维引擎
# ============================================================

class ConvergentThinkingEngine:
    """聚合思维引擎 - 评估与筛选，收敛到最优解
    
    发散思维产生可能性，聚合思维从中选出最好的。
    两者结合才是完整的创造过程。
    """
    
    def __init__(self):
        # 评估维度及其权重
        self.dimensions = {
            'novelty': 0.35,      # 新颖性
            'value': 0.35,        # 价值性
            'feasibility': 0.30,  # 可行性
        }
    
    def evaluate_idea(self, idea: Dict[str, Any]) -> Dict[str, Any]:
        """评估一个想法的质量"""
        novelty = idea.get('novelty', 0.5)
        value = idea.get('value', 0.5)
        feasibility = idea.get('feasibility', 0.5)
        
        # 综合得分
        total_score = (
            novelty * self.dimensions['novelty'] +
            value * self.dimensions['value'] +
            feasibility * self.dimensions['feasibility']
        )
        
        # 判断质量等级
        if total_score >= 0.9:
            quality = IdeaQuality.BREAKTHROUGH
        elif total_score >= 0.75:
            quality = IdeaQuality.EXCELLENT
        elif total_score >= 0.6:
            quality = IdeaQuality.GOOD
        elif total_score >= 0.4:
            quality = IdeaQuality.INTERESTING
        else:
            quality = IdeaQuality.TRIVIAL
        
        return {
            'idea_id': idea.get('id'),
            'total_score': total_score,
            'novelty': novelty,
            'value': value,
            'feasibility': feasibility,
            'quality': quality,
            'quality_label': quality.value,
            'strengths': self._identify_strengths(novelty, value, feasibility),
            'weaknesses': self._identify_weaknesses(novelty, value, feasibility),
        }
    
    def _identify_strengths(self, novelty: float, value: float, 
                           feasibility: float) -> List[str]:
        """识别优势"""
        strengths = []
        if novelty >= 0.7:
            strengths.append("新颖度高，有独创性")
        if value >= 0.7:
            strengths.append("价值大，影响深远")
        if feasibility >= 0.7:
            strengths.append("可行性高，容易落地")
        return strengths
    
    def _identify_weaknesses(self, novelty: float, value: float, 
                            feasibility: float) -> List[str]:
        """识别不足"""
        weaknesses = []
        if novelty < 0.4:
            weaknesses.append("不够新颖，比较常规")
        if value < 0.4:
            weaknesses.append("价值不大，意义有限")
        if feasibility < 0.4:
            weaknesses.append("可行性低，难以实现")
        return weaknesses
    
    def rank_ideas(self, ideas: List[Dict[str, Any]], 
                  top_n: int = 5) -> List[Dict[str, Any]]:
        """对想法进行排名，返回前N个"""
        evaluated = [self.evaluate_idea(idea) for idea in ideas]
        evaluated.sort(key=lambda x: x['total_score'], reverse=True)
        return evaluated[:top_n]
    
    def filter_ideas(self, ideas: List[Dict[str, Any]],
                    min_score: float = 0.5,
                    required_quality: IdeaQuality = None) -> List[Dict[str, Any]]:
        """筛选符合条件的想法"""
        evaluated = [self.evaluate_idea(idea) for idea in ideas]
        
        filtered = []
        for eval_result in evaluated:
            if eval_result['total_score'] >= min_score:
                if required_quality is None or eval_result['quality'] == required_quality:
                    filtered.append(eval_result)
        
        return filtered
    
    def optimize_idea(self, idea: Dict[str, Any], 
                     focus_dimension: str = None) -> Dict[str, Any]:
        """优化一个想法，提升某个维度
        
        针对薄弱环节进行改进。
        """
        evaluation = self.evaluate_idea(idea)
        
        if focus_dimension is None:
            # 自动选择最弱的维度
            scores = {
                'novelty': evaluation['novelty'],
                'value': evaluation['value'],
                'feasibility': evaluation['feasibility'],
            }
            focus_dimension = min(scores, key=scores.get)
        
        # 模拟优化效果
        improvement = random.uniform(0.05, 0.15)
        
        optimized = idea.copy()
        optimized[focus_dimension] = min(1.0, optimized.get(focus_dimension, 0.5) + improvement)
        optimized['iterations'] = optimized.get('iterations', 0) + 1
        optimized['last_improvement'] = focus_dimension
        optimized['improvement_amount'] = improvement
        
        # 重新评估
        new_evaluation = self.evaluate_idea(optimized)
        
        return {
            'original': idea,
            'optimized': optimized,
            'focus_dimension': focus_dimension,
            'original_score': evaluation['total_score'],
            'new_score': new_evaluation['total_score'],
            'improvement': new_evaluation['total_score'] - evaluation['total_score'],
        }


# ============================================================
# 类比推理引擎
# ============================================================

class AnalogyEngine:
    """类比推理引擎 - 跨领域知识迁移
    
    很多创新都来自跨领域的类比：
    将一个领域的原理应用到另一个完全不同的领域。
    """
    
    def __init__(self, concept_network: ConceptNetwork):
        self.network = concept_network
    
    def generate_analogy(self, source_domain: str, 
                        target_domain: str) -> Dict[str, Any]:
        """生成一个类比：从源领域到目标领域"""
        source_concepts = self.network.get_concepts_by_category(source_domain)
        target_concepts = self.network.get_concepts_by_category(target_domain)
        
        if not source_concepts or not target_concepts:
            return {"error": "领域不存在"}
        
        # 随机选择概念进行类比
        source = random.choice(source_concepts)
        target = random.choice(target_concepts)
        
        distance = self.network.calculate_semantic_distance(source.name, target.name)
        
        # 生成类比映射
        mappings = [
            {
                'source_element': source.name,
                'target_element': target.name,
                'relationship': '属性映射',
                'description': f'{source.name}之于{source_domain}，如同{target.name}之于{target_domain}'
            },
            {
                'source_element': f'{source.name}的原理',
                'target_element': f'{target.name}的设计',
                'relationship': '原理迁移',
                'description': f'将{source.name}的工作原理应用于{target.name}的设计'
            },
        ]
        
        # 评估类比质量
        quality_score = distance * 0.6 + 0.2  # 距离越远质量越高（但也更难成立）
        
        return {
            'source_domain': source_domain,
            'target_domain': target_domain,
            'source_concept': source.name,
            'target_concept': target.name,
            'semantic_distance': distance,
            'mappings': mappings,
            'analogy_statement': f'{source.name}之于{source_domain}，正如{target.name}之于{target_domain}',
            'creative_potential': quality_score,
            'insight': f'也许我们可以从{source_domain}的{source.name}中获得启发，来重新思考{target_domain}中的{target.name}。'
        }
    
    def find_analogous_solutions(self, problem_domain: str, 
                                 solution_count: int = 3) -> List[Dict[str, Any]]:
        """寻找类似的解决方案 - 从其他领域借鉴
        
        当你在一个领域遇到问题时，看看其他领域是如何解决类似问题的。
        """
        categories = self.network.get_all_categories()
        other_categories = [c for c in categories if c != problem_domain]
        
        solutions = []
        selected_domains = random.sample(other_categories, 
                                        min(solution_count, len(other_categories)))
        
        for domain in selected_domains:
            analogy = self.generate_analogy(domain, problem_domain)
            solutions.append({
                'source_domain': domain,
                'solution_idea': analogy.get('insight', ''),
                'analogy': analogy,
                'applicability': random.uniform(0.3, 0.8),
            })
        
        return solutions
    
    def bionics_inspiration(self, target_problem: str) -> Dict[str, Any]:
        """仿生灵感 - 从自然界获取创意
        
        大自然是最好的设计师，经过亿年进化，有很多精妙的解决方案。
        """
        # 模拟生物概念
        nature_concepts = [
            '光合作用', '蜂巢结构', '蜘蛛网', '鸟翼流线', 
            '莲花效应', '鲨鱼皮', '蚂蚁群体智能', '候鸟导航',
            'DNA复制', '神经网络', '森林生态', '珊瑚礁',
        ]
        
        selected = random.sample(nature_concepts, min(3, len(nature_concepts)))
        
        inspirations = []
        for concept in selected:
            inspirations.append({
                'biological_concept': concept,
                'principle': f'自然界中的{concept}具有独特的优势',
                'potential_application': f'也许可以将{concept}的原理应用于{target_problem}',
                'innovation_level': random.uniform(0.4, 0.8),
            })
        
        return {
            'target_problem': target_problem,
            'inspirations': inspirations,
            'approach': '仿生学方法：从自然界40亿年的进化中寻找解决方案',
            'hint': f'思考这些自然现象如何能启发你解决{target_problem}。'
        }


# ============================================================
# 灵感机制
# ============================================================

class InspirationEngine:
    """灵感引擎 - 模拟顿悟与灵感时刻
    
    创意不总是线性思考的结果，有时它会突然出现——
    这就是"啊哈！"时刻。这个引擎模拟这种现象。
    """
    
    def __init__(self, concept_network: ConceptNetwork):
        self.network = concept_network
        self._incubation_ideas: List[Dict[str, Any]] = []  # 孵化中的想法
    
    def random_insight(self, domain: str = None) -> Dict[str, Any]:
        """随机洞见 - 突然想到一个好主意
        
        模拟灵感乍现的体验。
        """
        # 获取两个远距离的概念
        concepts = self.network.get_random_concepts(2)
        if len(concepts) < 2:
            return {"error": "概念不足"}
        
        distance = self.network.calculate_semantic_distance(concepts[0].name, concepts[1].name)
        
        # 生成洞见
        insight_templates = [
            f"如果把{concepts[0].name}和{concepts[1].name}结合起来，会发生什么？",
            f"也许{concepts[0].name}的本质，其实可以用{concepts[1].name}来理解。",
            f"从{concepts[0].name}的角度看，{concepts[1].name}有了全新的意义。",
            f"{concepts[1].name}不就是另一种形式的{concepts[0].name}吗？",
            f"我们一直在用{concepts[0].name}的方式思考，但是否可以试试{concepts[1].name}的方式？",
        ]
        
        template = random.choice(insight_templates)
        
        # 洞见质量与距离相关（但有随机性）
        quality = distance * 0.6 + random.uniform(0, 0.4)
        quality = min(1.0, max(0.0, quality))
        
        return {
            'insight': template,
            'concepts': [c.name for c in concepts],
            'semantic_distance': distance,
            'quality': quality,
            'a_h_moment': quality > 0.7,  # 是否是"啊哈"时刻
            'feeling': "顿悟" if quality > 0.8 else "有意思的想法" if quality > 0.5 else "普通想法"
        }
    
    def start_incubation(self, problem: str):
        """开始孵化一个问题
        
        把问题放在潜意识里，过一段时间可能会有答案。
        这是创造性思维的重要阶段：孵化期。
        """
        incubation_item = {
            'problem': problem,
            'start_time': time.time(),
            'status': 'incubating',
            'related_concepts': [],
        }
        
        # 随机关联一些概念
        random_concepts = self.network.get_random_concepts(random.randint(2, 5))
        incubation_item['related_concepts'] = [c.name for c in random_concepts]
        
        self._incubation_ideas.append(incubation_item)
        
        logger.info(f"[灵感孵化] 开始孵化: {problem}")
        return incubation_item
    
    def check_incubation(self) -> List[Dict[str, Any]]:
        """检查孵化中的想法，看看是否有突破
        
        模拟"过了一段时间突然想通了"的体验。
        """
        results = []
        
        for item in self._incubation_ideas:
            if item['status'] != 'incubating':
                continue
            
            # 孵化时间越长，越有可能产生突破
            incubation_time = time.time() - item['start_time']
            breakthrough_probability = min(0.5, incubation_time / 300.0)  # 最多50%概率
            
            if random.random() < breakthrough_probability:
                # 产生突破！
                insight = self.random_insight()
                
                result = {
                    'problem': item['problem'],
                    'incubation_time': incubation_time,
                    'breakthrough': True,
                    'insight': insight,
                    'feeling': "啊哈！原来是这样！"
                }
                item['status'] = 'completed'
                results.append(result)
                
                logger.info(f"[灵感孵化] 突破!: {item['problem']}")
        
        return results
    
    def serendipity(self) -> Dict[str, Any]:
        """意外发现 - 偶然间发现有价值的东西
        
        很多重大发现都是意外的结果。
        """
        # 随机选择三个概念
        concepts = self.network.get_random_concepts(3)
        if len(concepts) < 3:
            return {"error": "概念不足"}
        
        # 生成意外发现
        discovery = {
            'type': random.choice(['新组合', '新视角', '新应用', '新问题']),
            'description': f'在研究{concepts[0].name}时，意外发现了它与{concepts[1].name}和{concepts[2].name}的有趣联系。',
            'concepts_involved': [c.name for c in concepts],
            'value': random.uniform(0.3, 0.9),
            'unexpectedness': random.uniform(0.5, 1.0),
        }
        
        return {
            'discovery': discovery,
            'feeling': "偶然发现",
            'quote': "机会只青睐有准备的头脑。——路易·巴斯德",
        }
    
    def dream_inspiration(self) -> Dict[str, Any]:
        """梦境灵感 - 从梦境中获得创意
        
        很多艺术家和科学家都从梦中获得过灵感。
        梦境中的思维更自由，更容易产生奇异的连接。
        """
        concepts = self.network.get_random_concepts(4)
        
        dream_sequence = []
        for i, concept in enumerate(concepts):
            dream_sequence.append(f"场景{i+1}：{concept.name}...")
        
        dream_story = " ".join(dream_sequence)
        dream_story += " 这些场景交织在一起，形成了奇特的画面..."
        
        # 从梦中提取的灵感
        insight = f"梦中的场景让我想到：也许{concepts[0].name}和{concepts[-1].name}之间有某种深层的联系。"
        
        return {
            'dream_sequence': dream_sequence,
            'dream_story': dream_story,
            'waking_insight': insight,
            'clarity': random.uniform(0.2, 0.7),  # 梦的清晰度
            'meaningfulness': random.uniform(0.3, 0.8),  # 意义感
            'creative_potential': random.uniform(0.4, 0.9),
        }


# ============================================================
# 创造力引擎主类
# ============================================================

class CreativityEngine:
    """
    创造力引擎 - 生成新颖且有价值的想法
    
    创造力不是天赋，而是一套可以被理解和运用的方法。
    这个引擎整合了多种创造性思维技术，帮助智能体产生有价值的新想法。
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化创造力引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'creativity_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        self.creative_style = CreativeStyle.COMBINATORY
        
        # 核心组件
        self.concept_network = ConceptNetwork()
        self.association_engine = AssociationEngine(self.concept_network)
        self.divergent_engine = DivergentThinkingEngine(self.concept_network)
        self.convergent_engine = ConvergentThinkingEngine()
        self.analogy_engine = AnalogyEngine(self.concept_network)
        self.inspiration_engine = InspirationEngine(self.concept_network)
        
        # 创意历史
        self.idea_history: List[Idea] = []
        self.projects: List[CreativeProject] = []
        
        # 创造力水平
        self.creativity_level = 0.6  # 整体创造力水平 0-1
        
        # 加载数据
        self._load()
        
        logger.info(f"创造力引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"创造风格: {self.creative_style.value}")
        logger.info(f"概念数量: {len(self.concept_network.concepts)}")
    
    def _load(self):
        """加载创造力数据"""
        try:
            # 加载想法历史
            ideas_file = self.data_path / 'idea_history.json'
            if ideas_file.exists():
                with open(ideas_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.idea_history = [Idea.from_dict(d) for d in data]
            
            # 加载概念网络
            concepts_file = self.data_path / 'concepts.json'
            if concepts_file.exists():
                with open(concepts_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for cd in data:
                        concept = Concept.from_dict(cd)
                        self.concept_network.add_concept(concept)
            
            logger.info(f"已加载 {len(self.idea_history)} 个历史想法")
        except Exception as e:
            logger.warning(f"加载创造力数据失败: {e}")
    
    def save(self):
        """保存创造力数据"""
        try:
            # 保存想法历史
            with open(self.data_path / 'idea_history.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [idea.to_dict() for idea in self.idea_history[-200:]],
                    f, ensure_ascii=False, indent=2
                )
            
            # 保存概念网络
            with open(self.data_path / 'concepts.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [c.to_dict() for c in self.concept_network.concepts.values()],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            logger.error(f"保存创造力数据失败: {e}")
    
    # ============================================================
    # 核心创意方法
    # ============================================================
    
    def brainstorm(self, topic: str, 
                   idea_count: int = 10,
                   method: str = "mixed") -> List[Idea]:
        """头脑风暴 - 围绕某个主题生成多个想法
        
        Args:
            topic: 创意主题
            idea_count: 想法数量
            method: 方法 - free/forced/scamper/mixed
        """
        raw_ideas = []
        
        if method == "free":
            raw_ideas = self.divergent_engine.generate_alternatives(topic, count=idea_count)
        elif method == "forced":
            # 强制连接法
            for _ in range(idea_count):
                c1, c2 = self.concept_network.get_random_concepts(2)
                result = self.association_engine.forced_connection(c1.name, c2.name)
                for combo in result.get('combinations', []):
                    raw_ideas.append({
                        'title': combo['description'],
                        'description': combo['example'],
                        'novelty': combo['novelty'],
                        'value': random.uniform(0.3, 0.7),
                        'feasibility': random.uniform(0.2, 0.6),
                        'source': 'forced_connection',
                    })
        elif method == "scamper":
            raw_ideas = self.divergent_engine.scamper_method(topic)
        else:
            # 混合方法
            n1 = max(1, idea_count // 3)
            n2 = max(1, idea_count // 3)
            n3 = idea_count - n1 - n2
            
            raw_ideas.extend(self.divergent_engine.generate_alternatives(topic, count=n1))
            raw_ideas.extend(self.divergent_engine.scamper_method(topic)[:n2])
            
            # 强制连接
            for _ in range(n3):
                c1, c2 = self.concept_network.get_random_concepts(2)
                result = self.association_engine.forced_connection(c1.name, c2.name)
                if result.get('combinations'):
                    combo = random.choice(result['combinations'])
                    raw_ideas.append({
                        'title': combo['description'],
                        'description': combo['example'],
                        'novelty': combo['novelty'],
                        'value': random.uniform(0.3, 0.7),
                        'feasibility': random.uniform(0.2, 0.6),
                        'source': 'forced_connection',
                    })
        
        # 转换为Idea对象
        ideas = []
        for i, raw in enumerate(raw_ideas[:idea_count]):
            idea = Idea(
                id=f"idea_{int(time.time())}_{i}",
                title=raw.get('title', f'想法{i}'),
                description=raw.get('description', ''),
                novelty=raw.get('novelty', 0.5),
                value=raw.get('value', 0.5),
                feasibility=raw.get('feasibility', 0.5),
                source=raw.get('source', 'brainstorm'),
                generation_method=method,
                tags=[topic],
            )
            ideas.append(idea)
            self.idea_history.append(idea)
        
        logger.info(f"[头脑风暴] 主题: {topic}, 生成想法: {len(ideas)}个")
        
        return ideas
    
    def creative_problem_solving(self, problem: str, 
                                constraints: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """创造性问题解决
        
        完整的创意解决问题流程：
        1. 理解问题
        2. 发散思维生成方案
        3. 聚合思维评估筛选
        4. 优化最佳方案
        """
        if constraints is None:
            constraints = []
        
        # 阶段1：生成多种解决方案
        raw_ideas = self.divergent_engine.generate_alternatives(
            problem, count=15, perspective_count=5
        )
        
        # 阶段2：评估并筛选
        evaluated = [self.convergent_engine.evaluate_idea(idea) for idea in raw_ideas]
        evaluated.sort(key=lambda x: x['total_score'], reverse=True)
        
        top_5 = evaluated[:5]
        
        # 阶段3：优化最佳方案
        best_idea_data = None
        for e in top_5:
            for idea in raw_ideas:
                if idea.get('id') == e['idea_id']:
                    best_idea_data = idea
                    break
            if best_idea_data:
                break
        
        optimized = None
        if best_idea_data:
            optimized = self.convergent_engine.optimize_idea(best_idea_data)
        
        # 阶段4：类比推理获取额外灵感
        analogous = self.analogy_engine.find_analogous_solutions('技术', solution_count=3)
        
        return {
            'problem': problem,
            'constraints': constraints,
            'total_ideas_generated': len(raw_ideas),
            'top_solutions': top_5,
            'best_solution': top_5[0] if top_5 else None,
            'optimized_solution': optimized,
            'analogous_inspirations': analogous,
            'creativity_score': top_5[0]['total_score'] if top_5 else 0,
            'process': [
                '1. 发散思维：生成多种可能性',
                '2. 聚合思维：评估筛选最优',
                '3. 优化改进：针对薄弱点提升',
                '4. 跨界灵感：从其他领域借鉴'
            ]
        }
    
    def generate_innovation(self, domain: str = "general",
                          innovation_type: str = "product") -> Idea:
        """生成一个创新想法
        
        Args:
            domain: 领域
            innovation_type: 类型 - product/service/process/concept
        """
        # 选择两个不同类别的概念进行组合
        categories = self.concept_network.get_all_categories()
        cat1, cat2 = random.sample(categories, 2)
        
        concepts1 = self.concept_network.get_concepts_by_category(cat1)
        concepts2 = self.concept_network.get_concepts_by_category(cat2)
        
        c1 = random.choice(concepts1) if concepts1 else None
        c2 = random.choice(concepts2) if concepts2 else None
        
        if not c1 or not c2:
            c1, c2 = self.concept_network.get_random_concepts(2)
        
        # 生成创新
        distance = self.concept_network.calculate_semantic_distance(c1.name, c2.name)
        
        innovation_templates = [
            f"一个融合了{c1.name}和{c2.name}的{innovation_type}",
            f"用{c1.name}的方式重新定义{c2.name}",
            f"将{c2.name}引入{c1.name}领域",
            f"{c1.name}与{c2.name}的跨界{innovation_type}",
        ]
        
        template = random.choice(innovation_templates)
        
        # 新颖性与距离正相关
        novelty = min(0.95, distance * 0.7 + 0.2 + random.uniform(-0.1, 0.1))
        # 可行性与距离负相关（越新颖往往越难实现）
        feasibility = min(0.9, 1.0 - distance * 0.5 + random.uniform(-0.1, 0.1))
        # 价值中等
        value = random.uniform(0.4, 0.8)
        
        idea = Idea(
            id=f"innovation_{int(time.time())}",
            title=template,
            description=f"这个{innovation_type}创新结合了{c1.name}（{c1.category}）和{c2.name}（{c2.category}）的概念。"
                       f"两者之间的语义距离为{distance:.2f}，这意味着它既有足够的新颖性，又不是完全不可理解。",
            novelty=novelty,
            value=value,
            feasibility=feasibility,
            source=f"{innovation_type}_innovation",
            generation_method="cross_domain_combination",
            tags=[c1.name, c2.name, domain, innovation_type],
            related_concepts=[c1.name, c2.name],
        )
        
        self.idea_history.append(idea)
        
        logger.info(f"[创新生成] {innovation_type}: {idea.title[:50]}...")
        logger.info(f"  创造力得分: {idea.creativity_score:.2f}")
        
        return idea
    
    # ============================================================
    # 创意项目管理
    # ============================================================
    
    def start_project(self, name: str, description: str,
                     goal: str = "") -> CreativeProject:
        """启动一个创意项目"""
        project = CreativeProject(
            id=f"project_{int(time.time())}",
            name=name,
            description=description,
            goal=goal,
        )
        self.projects.append(project)
        
        logger.info(f"[创意项目] 启动: {name}")
        return project
    
    def add_ideas_to_project(self, project_id: str, ideas: List[Idea]):
        """向项目添加想法"""
        for project in self.projects:
            if project.id == project_id:
                project.ideas.extend(ideas)
                project.total_ideas = len(project.ideas)
                if project.ideas:
                    project.best_score = max(i.creativity_score for i in project.ideas)
                logger.info(f"[创意项目] 添加{len(ideas)}个想法到 {project.name}")
                return
        logger.warning(f"[创意项目] 未找到项目: {project_id}")
    
    def select_best_ideas(self, project_id: str, top_n: int = 3) -> List[Idea]:
        """从项目中选择最好的想法"""
        for project in self.projects:
            if project.id == project_id:
                sorted_ideas = sorted(project.ideas, 
                                     key=lambda i: i.creativity_score, 
                                     reverse=True)
                selected = sorted_ideas[:top_n]
                project.selected_ideas = [i.id for i in selected]
                project.status = "evaluation"
                logger.info(f"[创意项目] {project.name} 选择了 {len(selected)} 个最佳想法")
                return selected
        return []
    
    # ============================================================
    # 创造力训练
    # ============================================================
    
    def creativity_exercise(self, exercise_type: str = "random") -> Dict[str, Any]:
        """创造力训练 - 提升创造力水平
        
        通过练习来提升创造力。
        """
        exercises = {
            'remote_association': {
                'name': '远距离联想',
                'description': '找出三个词之间的共同联系',
                'difficulty': 0.6,
            },
            'alternate_uses': {
                'name': '替代用途',
                'description': '想出一个普通物品的不寻常用途',
                'difficulty': 0.5,
            },
            'consequence': {
                'name': '后果推测',
                'description': '假设一个不寻常的场景，推测其后果',
                'difficulty': 0.7,
            },
            'forced_connection': {
                'name': '强制连接',
                'description': '将两个不相关的事物结合起来',
                'difficulty': 0.6,
            },
        }
        
        if exercise_type == "random":
            exercise_type = random.choice(list(exercises.keys()))
        
        exercise = exercises.get(exercise_type, exercises['forced_connection'])
        
        # 根据练习生成内容
        if exercise_type == "forced_connection":
            c1, c2 = self.concept_network.get_random_concepts(2)
            result = self.association_engine.forced_connection(c1.name, c2.name)
            exercise_result = {
                'concepts': [c1.name, c2.name],
                'challenge': f"想办法将{c1.name}和{c2.name}结合起来",
                'suggestions': result.get('combinations', []),
            }
        elif exercise_type == "remote_association":
            concepts = self.concept_network.get_random_concepts(3)
            exercise_result = {
                'concepts': [c.name for c in concepts],
                'challenge': f"找出这三个概念之间的共同联系或第四个相关概念",
            }
        elif exercise_type == "alternate_uses":
            concept = self.concept_network.get_random_concepts(1)[0]
            exercise_result = {
                'object': concept.name,
                'challenge': f"想出{concept.name}的5种不寻常用途",
            }
        else:
            exercise_result = {
                'challenge': '想出一个创意解决方案',
            }
        
        # 完成练习后轻微提升创造力
        improvement = random.uniform(0.005, 0.02)
        self.creativity_level = min(1.0, self.creativity_level + improvement)
        
        return {
            'exercise_type': exercise_type,
            'exercise': exercise,
            'result': exercise_result,
            'creativity_improvement': improvement,
            'new_creativity_level': self.creativity_level,
        }
    
    # ============================================================
    # 状态查询
    # ============================================================
    
    def get_creativity_stats(self) -> dict:
        """获取创造力统计信息"""
        total_ideas = len(self.idea_history)
        if total_ideas > 0:
            avg_score = sum(i.creativity_score for i in self.idea_history) / total_ideas
            max_score = max(i.creativity_score for i in self.idea_history)
            quality_counts = {}
            for idea in self.idea_history:
                q = idea.quality.value
                quality_counts[q] = quality_counts.get(q, 0) + 1
        else:
            avg_score = 0
            max_score = 0
            quality_counts = {}
        
        return {
            'agent_name': self.agent_name,
            'creativity_level': self.creativity_level,
            'creative_style': self.creative_style.value,
            'total_ideas_generated': total_ideas,
            'concept_count': len(self.concept_network.concepts),
            'average_creativity_score': avg_score,
            'max_creativity_score': max_score,
            'quality_distribution': quality_counts,
            'active_projects': len([p for p in self.projects if p.status != 'completed']),
        }
    
    def get_creativity_report(self) -> str:
        """获取创造力状态报告"""
        stats = self.get_creativity_stats()
        
        report = f"""
{'='*60}
创造力状态报告 - {self.agent_name}
{'='*60}

🎨 创造力水平: {stats['creativity_level']:.2f}
   风格: {stats['creative_style']}

📊 创意统计
   总想法数: {stats['total_ideas_generated']}
   概念数量: {stats['concept_count']}
   平均得分: {stats['average_creativity_score']:.2f}
   最高得分: {stats['max_creativity_score']:.2f}

🏷️  质量分布
"""
        for quality, count in stats['quality_distribution'].items():
            bar_len = int(count / max(stats['total_ideas_generated'], 1) * 30)
            bar = '█' * bar_len
            report += f"   {quality:15s} {count:4d} {bar}\n"
        
        if stats['active_projects'] > 0:
            report += f"\n📁 活跃项目: {stats['active_projects']}个\n"
        
        # 创造力等级描述
        level = stats['creativity_level']
        if level >= 0.9:
            level_desc = "大师级创造力。能够持续产生突破性的想法。"
        elif level >= 0.7:
            level_desc = "优秀的创造力。经常能想出新颖且有价值的点子。"
        elif level >= 0.5:
            level_desc = "中等创造力。在引导下能产生不错的想法。"
        elif level >= 0.3:
            level_desc = "基础创造力。倾向于常规的、已知的方案。"
        else:
            level_desc = "创造力有待提升。需要更多的练习和拓展。"
        
        report += f"\n💡 创造力评价:\n  {level_desc}\n"
        report += f"\n{'='*60}\n"
        
        return report
    
    def get_inspiration_quote(self) -> str:
        """获取一句创意名言"""
        quotes = [
            "创造力就是把事物联系起来。——史蒂夫·乔布斯",
            "每一个孩子都是艺术家。问题是长大后如何保持艺术家的身份。——巴勃罗·毕加索",
            "不要等待灵感，要主动去寻找。——杰克·伦敦",
            "最好的想法往往来自对旧想法的重新组合。——詹姆斯·韦伯·扬",
            "创意就是把熟悉的事物变得陌生，把陌生的事物变得熟悉。——西奥多·罗特克",
            "限制是创造力最好的朋友。——布莱恩·伊诺",
            "每个创造行为首先都是一个破坏行为。——巴勃罗·毕加索",
            "你无法用尽创造力。你用得越多，它就越多。——玛雅·安吉罗",
        ]
        return random.choice(quotes)


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("创造力引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建创造力引擎
        creativity = CreativityEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n🎨 初始状态:")
        stats = creativity.get_creativity_stats()
        print(f"  创造力水平: {stats['creativity_level']:.2f}")
        print(f"  创造风格: {stats['creative_style']}")
        print(f"  概念数量: {stats['concept_count']}")
        
        print("\n💡 创意名言:")
        print(f"  \"{creativity.get_inspiration_quote()}\"")
        
        print("\n🧠 头脑风暴示例（主题：未来的智能体）...")
        ideas = creativity.brainstorm("未来的智能体", idea_count=8, method="mixed")
        
        print(f"\n  生成了 {len(ideas)} 个想法:")
        for i, idea in enumerate(ideas):
            score = idea.creativity_score
            print(f"  {i+1}. [{score:.2f}] {idea.title[:50]}")
        
        print("\n🏆 最佳想法 TOP 3:")
        sorted_ideas = sorted(ideas, key=lambda x: x.creativity_score, reverse=True)
        for i, idea in enumerate(sorted_ideas[:3]):
            print(f"\n  第{i+1}名 - 得分: {idea.creativity_score:.2f}")
            print(f"     标题: {idea.title}")
            print(f"     描述: {idea.description[:80]}...")
            print(f"     新颖性: {idea.novelty:.2f} | 价值: {idea.value:.2f} | 可行: {idea.feasibility:.2f}")
        
        print("\n🔗 强制连接示例...")
        c1, c2 = creativity.concept_network.get_random_concepts(2)
        result = creativity.association_engine.forced_connection(c1.name, c2.name)
        print(f"  概念: {c1.name} + {c2.name}")
        print(f"  语义距离: {result['semantic_distance']:.2f}")
        print(f"  创意潜力: {result['creative_potential']:.2f}")
        print(f"  组合方式:")
        for combo in result['combinations']:
            print(f"    - {combo['type']}: {combo['description']}")
        
        print("\n🔄 类比推理示例...")
        analogy = creativity.analogy_engine.generate_analogy("自然", "技术")
        print(f"  类比: {analogy['analogy_statement']}")
        print(f"  洞见: {analogy['insight']}")
        print(f"  创意潜力: {analogy['creative_potential']:.2f}")
        
        print("\n✨ 随机灵感...")
        insight = creativity.inspiration_engine.random_insight()
        print(f"  洞见: {insight['insight']}")
        print(f"  质量: {insight['quality']:.2f}")
        print(f"  感受: {insight['feeling']}")
        if insight['a_h_moment']:
            print(f"  💡 啊哈时刻！")
        
        print("\n🎯 创造性问题解决示例...")
        solution = creativity.creative_problem_solving("如何提升智能体的自主性？")
        print(f"  问题: {solution['problem']}")
        print(f"  生成想法数: {solution['total_ideas_generated']}")
        print(f"  最佳方案得分: {solution['creativity_score']:.2f}")
        if solution['best_solution']:
            best = solution['best_solution']
            print(f"  最佳方案: {best.get('idea_id', '未知')}")
            print(f"    新颖: {best['novelty']:.2f} | 价值: {best['value']:.2f} | 可行: {best['feasibility']:.2f}")
        
        print("\n🏋️ 创造力训练...")
        exercise = creativity.creativity_exercise("forced_connection")
        print(f"  练习类型: {exercise['exercise_type']}")
        print(f"  挑战: {exercise['result']['challenge']}")
        print(f"  创造力提升: +{exercise['creativity_improvement']:.4f}")
        print(f"  新水平: {exercise['new_creativity_level']:.2f}")
        
        print("\n📊 最终状态报告:")
        print(creativity.get_creativity_report())
        
        # 保存
        creativity.save()
        
        print("\n" + "=" * 70)
        print("✅ 创造力引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
