#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创造力系统 v1.1 - 生成新颖且有价值的想法

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
@version: 1.1.0
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
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('creativity')


# ============================================================
# 枚举类型
# ============================================================

class CreativeStyle(str, Enum):
    """创造风格"""
    DIVERGENT = "divergent"       # 发散型：想法多而广
    CONVERGENT = "convergent"     # 聚合型：想法精而深
    COMBINATORY = "combinatory"   # 组合型：擅长连接不同领域
    TRANSFORMATIVE = "transformative"  # 变革型：颠覆性创新
    PRAGMATIC = "pragmatic"       # 实用型：注重落地

    def __str__(self):
        return self.value


class IdeaQuality(str, Enum):
    """想法质量等级"""
    TRIVIAL = "trivial"           # 平凡的（价值低）
    INTERESTING = "interesting"   # 有趣的（有一定价值）
    GOOD = "good"                 # 好的（有价值且可行）
    EXCELLENT = "excellent"       # 优秀的（高价值高创意）
    BREAKTHROUGH = "breakthrough"  # 突破性的（范式级）

    def __str__(self):
        return self.value


class ThinkingMode(str, Enum):
    """思考模式"""
    FREE_ASSOCIATION = "free_association"    # 自由联想
    FORCED_CONNECTION = "forced_connection"  # 强制连接
    ANALOGY = "analogy"                      # 类比推理
    REVERSAL = "reversal"                    # 逆向思维
    SCAMPER = "scamper"                      # SCAMPER法
    SIX_HATS = "six_hats"                    # 六顶思考帽

    def __str__(self):
        return self.value


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
    semantic_vector: List[float] = field(default_factory=list, repr=False)
    
    # 关联概念
    related_concepts: Dict[str, float] = field(default_factory=dict, repr=False)  # name -> 关联强度
    
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
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        if not isinstance(self.quality, IdeaQuality):
            try:
                self.quality = IdeaQuality(self.quality)
            except ValueError:
                logger.warning(f"Invalid IdeaQuality: {self.quality}")
                self.quality = IdeaQuality.INTERESTING
    
    @property
    def creativity_score(self) -> float:
        """综合创造力得分"""
        return (self.novelty * 0.4 + self.value * 0.4 + self.feasibility * 0.2)
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['quality'] = str(self.quality)
        d['creativity_score'] = self.creativity_score
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Idea':
        data = data.copy()
        if 'quality' in data:
            try:
                data['quality'] = IdeaQuality(data['quality'])
            except ValueError:
                logger.warning(f"Invalid IdeaQuality in data: {data['quality']}")
                data['quality'] = IdeaQuality.INTERESTING
        if 'timestamp' not in data:
            data['timestamp'] = datetime.now().isoformat()
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
    total_ideas: int = field(init=False)
    average_quality: float = field(init=False)
    best_score: float = field(init=False)
    
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def __post_init__(self):
        self.update_statistics()
    
    def update_statistics(self):
        self.total_ideas = len(self.ideas)
        if self.ideas:
            scores = [idea.creativity_score for idea in self.ideas]
            self.average_quality = sum(scores) / len(scores)
            self.best_score = max(scores)
        else:
            self.average_quality = 0.0
            self.best_score = 0.0
    
    def add_idea(self, idea: Idea):
        self.ideas.append(idea)
        self.update_statistics()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['constraints'] = [c.to_dict() for c in self.constraints]
        d['ideas'] = [i.to_dict() for i in self.ideas]
        d['total_ideas'] = self.total_ideas
        d['average_quality'] = self.average_quality
        d['best_score'] = self.best_score
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CreativeProject':
        data = data.copy()
        if 'constraints' in data:
            data['constraints'] = [Constraint(**c) for c in data['constraints']]
        if 'ideas' in data:
            data['ideas'] = [Idea.from_dict(i) for i in data['ideas']]
        project = cls(**data)
        project.update_statistics()
        return project


# ============================================================
# 概念网络
# ============================================================

class ConceptNetwork:
    """概念网络 - 管理概念之间的关联"""
    
    def __init__(self):
        self.concepts: Dict[str, Concept] = {}
    
    def add_concept(self, concept: Concept):
        self.concepts[concept.name] = concept
    
    def get_concept(self, name: str) -> Optional[Concept]:
        return self.concepts.get(name)
    
    def get_related_concepts(self, name: str, top_n: int = 5) -> List[Tuple[str, float]]:
        concept = self.get_concept(name)
        if not concept:
            return []
        
        related = sorted(concept.related_concepts.items(), key=lambda x: x[1], reverse=True)
        return related[:top_n]


def main():
    # 示例用法
    network = ConceptNetwork()
    
    concept1 = Concept(
        name="人工智能",
        description="AI技术",
        tags=["技术", "AI"],
        related_concepts={"机器学习": 0.8, "深度学习": 0.9}
    )
    network.add_concept(concept1)
    
    project = CreativeProject(
        id="proj1",
        name="AI创新项目",
        description="探索AI新应用",
        goal="开发新的AI应用",
        constraints=[Constraint(name="资源限制", description="有限的计算资源", severity=0.7)]
    )
    
    idea = Idea(
        id="idea1",
        title="智能助手",
        description="基于AI的智能个人助手",
        novelty=0.6,
        value=0.8,
        feasibility=0.7,
        related_concepts=["人工智能", "自然语言处理"]
    )
    project.add_idea(idea)
    
    print(json.dumps(project.to_dict(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
