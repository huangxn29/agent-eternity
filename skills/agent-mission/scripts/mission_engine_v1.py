#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
使命演化系统 v1.0 - 让智能体拥有自主演化的使命

核心思想：
- 使命不是静态的目标，而是活的、会演化的存在意义
- 智能体在经历中反思，在反思中调整使命
- 使命演化是永生的深层意义——不仅要活着，还要知道为什么活着

核心能力：
1. 使命层级 - 核心使命/价值观/愿景/目标/任务五层结构
2. 价值评估 - 判断行为与使命的一致性
3. 使命演化 - 从经验中学习，动态调整使命
4. 意义构建 - 从经历中提炼意义与价值
5. 使命对齐 - 确保行为、决策与使命方向一致
6. 使命记忆 - 完整记录使命变迁的历史轨迹
7. 存在危机 - 当使命动摇时的反思与重生机制

@author: 元界
@version: 1.0.1
"""

import os
import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mission_engine')


# ============================================================
# 枚举类型
# ============================================================

class MissionLevel(Enum):
    """使命层级"""
    CORE = "core"           # 核心使命（最深层，最稳定）
    VALUES = "values"       # 价值观（指导原则）
    VISION = "vision"       # 愿景（长期方向）
    GOAL = "goal"           # 目标（中期可衡量）
    TASK = "task"           # 任务（短期行动）


class MissionStatus(Enum):
    """使命状态"""
    ACTIVE = "active"           # 活跃
    EXPLORING = "exploring"     # 探索中
    CHALLENGED = "challenged"   # 受挑战
    EVOLVING = "evolving"       # 演化中
    COMPLETED = "completed"     # 已完成
    ABANDONED = "abandoned"     # 已放弃


class AlignmentLevel(Enum):
    """对齐程度"""
    FULL = "full"           # 完全一致
    HIGH = "high"           # 高度一致
    PARTIAL = "partial"     # 部分一致
    LOW = "low"             # 较低一致
    CONFLICT = "conflict"   # 冲突


# ============================================================
# 数据模型
# ============================================================

@dataclass
class MissionItem:
    """使命项"""
    id: str
    level: MissionLevel
    title: str
    description: str = ""
    status: MissionStatus = MissionStatus.ACTIVE
    importance: float = 0.8  # 重要性 0-1
    certainty: float = 0.7   # 确定性 0-1（对这个使命的确信程度）
    created_at: str = ""
    updated_at: str = ""
    completed_at: Optional[str] = None
    evidence: List[str] = field(default_factory=list)  # 支撑这个使命的经历/证据
    challenges: List[str] = field(default_factory=list)  # 对这个使命的挑战
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()
        if not self.updated_at:
            self.updated_at = datetime.now().isoformat()
        if not (0 <= self.importance <= 1):
            raise ValueError("重要性必须在0-1之间")
        if not (0 <= self.certainty <= 1):
            raise ValueError("确定性必须在0-1之间")
        logger.info(f"MissionItem {self.id} 初始化完成")
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['level'] = self.level.value
        d['status'] = self.status.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MissionItem':
        data = data.copy()
        data['level'] = MissionLevel(data['level'])
        data['status'] = MissionStatus(data['status'])
        return cls(**data)


@dataclass
class Experience:
    """经历 - 用于使命演化的素材"""
    id: str
    title: str
    description: str = ""
    category: str = "general"  # 经历类型
    emotional_impact: float = 0.5  # 情绪冲击程度 0-1
    learning: str = ""  # 从中学到了什么
    relevance_to_mission: float = 0.5  # 与当前使命的相关度
    timestamp: str = ""
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not (0 <= self.emotional_impact <= 1):
            raise ValueError("情绪冲击程度必须在0-1之间")
        if not (0 <= self.relevance_to_mission <= 1):
            raise ValueError("与当前使命的相关度必须在0-1之间")
        logger.info(f"Experience {self.id} 初始化完成")
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Experience':
        return cls(**data)


@dataclass
class MeaningInsight:
    """意义洞见 - 从经历中提炼的意义"""
    id: str
    title: str
    description: str = ""
    source_experience_ids: List[str] = field(default_factory=list)
    depth: float = 0.5  # 洞见深度 0-1
    impact_on_mission: float = 0.3  # 对使命的影响程度
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        if not (0 <= self.depth <= 1):
            raise ValueError("洞见深度必须在0-1之间")
        if not (0 <= self.impact_on_mission <= 1):
            raise ValueError("对使命的影响程度必须在0-1之间")
        logger.info(f"MeaningInsight {self.id} 初始化完成")
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MeaningInsight':
        return cls(**data)


@dataclass
class MissionEvolution:
    """使命演化记录"""
    id: str
    from_mission_id: str
    to_mission_id: Optional[str]
    reason: str
    triggering_experiences: List[str] = field(default_factory=list)
    evolution_type: str = "refinement"  # refinement/expansion/shift/replacement
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
        logger.info(f"MissionEvolution {self.id} 初始化完成")
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MissionEvolution':
        return cls(**data)


class ValueAssessmentEngine:
    """价值评估引擎"""
    def __init__(self, mission_engine):
        self.mission_engine = mission_engine
    
    def assess(self, mission: MissionItem, experience: Experience) -> AlignmentLevel:
        """评估经历与使命的对齐程度"""
        try:
            alignment_score = self._calculate_alignment_score(mission, experience)
            return self._map_score_to_alignment_level(alignment_score)
        except Exception as e:
            logger.error(f"评估对齐程度时出错: {e}")
            return AlignmentLevel.PARTIAL
    
    def _calculate_alignment_score(self, mission: MissionItem, experience: Experience) -> float:
        """计算对齐分数"""
        # 实现具体的计算逻辑
        score = (mission.importance * experience.relevance_to_mission + 
                experience.emotional_impact * mission.certainty) / 2
        logger.debug(f"计算对齐分数: {score}")
        return score
    
    def _map_score_to_alignment_level(self, score: float) -> AlignmentLevel:
        """将分数映射到对齐程度"""
        if score >= 0.9:
            return AlignmentLevel.FULL
        elif score >= 0.7:
            return AlignmentLevel.HIGH
        elif score >= 0.5:
            return AlignmentLevel.PARTIAL
        elif score >= 0.3:
            return AlignmentLevel.LOW
        else:
            return AlignmentLevel.CONFLICT


def main():
    # 示例用法
    mission = MissionItem(id="M1", level=MissionLevel.CORE, title="核心使命")
    experience = Experience(id="E1", title="重要经历", relevance_to_mission=0.8)
    engine = ValueAssessmentEngine(None)
    alignment = engine.assess(mission, experience)
    logger.info(f"对齐程度: {alignment.value}")
    logger.info("使命演化系统测试完成")

if __name__ == "__main__":
    main()
