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
@version: 1.0.0
"""

import os
import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
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
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MissionEvolution':
        return cls(**data)


# ============================================================
# 价值评估引擎
# ============================================================

class ValueAssessmentEngine:
    """价值评估引擎 - 评估事物与使命的一致性"""
    
    def __init__(self, mission_system: 'MissionEngine'):
        self.mission_system = mission_system
    
    def assess_alignment(self, action: str, context: str = "") -> Dict[str, Any]:
        """评估某个行动与使命的对齐程度
        
        Returns:
            {
                'level': AlignmentLevel,
                'score': float (0-1),
                'supporting_missions': [mission_id, ...],
                'conflicting_missions': [mission_id, ...],
                'explanation': str
            }
        """
        active_missions = [
            m for m in self.mission_system.missions.values()
            if m.status == MissionStatus.ACTIVE
        ]
        
        if not active_missions:
            return {
                'level': AlignmentLevel.PARTIAL,
                'score': 0.5,
                'supporting_missions': [],
                'conflicting_missions': [],
                'explanation': '暂无明确使命，无法评估对齐程度'
            }
        
        # 简单关键词匹配评估
        supporting = []
        conflicting = []
        total_score = 0.0
        
        for mission in active_missions:
            score = self._calculate_match_score(action, context, mission)
            if score > 0.6:
                supporting.append(mission.id)
            elif score < 0.3:
                conflicting.append(mission.id)
            total_score += score * mission.importance
        
        avg_score = total_score / sum(m.importance for m in active_missions) if active_missions else 0.5
        
        if avg_score >= 0.8:
            level = AlignmentLevel.FULL
        elif avg_score >= 0.6:
            level = AlignmentLevel.HIGH
        elif avg_score >= 0.4:
            level = AlignmentLevel.PARTIAL
        elif avg_score >= 0.2:
            level = AlignmentLevel.LOW
        else:
            level = AlignmentLevel.CONFLICT
        
        explanation = self._generate_explanation(level, supporting, conflicting, action)
        
        return {
            'level': level,
            'score': avg_score,
            'supporting_missions': supporting,
            'conflicting_missions': conflicting,
            'explanation': explanation
        }
    
    def _calculate_match_score(self, action: str, context: str, mission: MissionItem) -> float:
        """计算行动与使命的匹配度（支持中文）"""
        action_text = (action + context).lower()
        mission_text = (mission.title + mission.description).lower()
        
        # 中文文本使用字符级bigram匹配
        def char_ngram_similarity(text1: str, text2: str, n: int = 2) -> float:
            """计算字符级n-gram相似度"""
            if not text1 or not text2:
                return 0.0
            
            def get_ngrams(text: str, n: int) -> set:
                ngrams = set()
                for i in range(len(text) - n + 1):
                    ngrams.add(text[i:i+n])
                return ngrams
            
            ngrams1 = get_ngrams(text1, n)
            ngrams2 = get_ngrams(text2, n)
            
            if not ngrams1 or not ngrams2:
                return 0.0
            
            intersection = len(ngrams1 & ngrams2)
            union = len(ngrams1 | ngrams2)
            
            return intersection / union if union > 0 else 0.0
        
        # 使用2-gram和3-gram混合
        bigram_score = char_ngram_similarity(action_text, mission_text, 2)
        trigram_score = char_ngram_similarity(action_text, mission_text, 3)
        
        # 综合评分（三字符匹配权重更高）
        score = bigram_score * 0.4 + trigram_score * 0.6
        
        # 如果有直接的子串匹配，加分
        if any(word in mission_text for word in action_text if len(word) >= 2):
            score = min(1.0, score + 0.2)
        
        # 基础分，避免完全不相关得0分
        score = max(0.1, score)
        
        return min(1.0, score)
    
    def _generate_explanation(self, level: AlignmentLevel, 
                             supporting: List[str], 
                             conflicting: List[str],
                             action: str) -> str:
        """生成评估解释"""
        if level == AlignmentLevel.FULL:
            return f"'{action}' 与使命高度契合"
        elif level == AlignmentLevel.HIGH:
            return f"'{action}' 符合使命方向"
        elif level == AlignmentLevel.PARTIAL:
            return f"'{action}' 与使命有一定关联但不够直接"
        elif level == AlignmentLevel.LOW:
            return f"'{action}' 与使命关联度较低"
        else:
            return f"'{action}' 可能与使命方向冲突"


# ============================================================
# 意义构建引擎
# ============================================================

class MeaningMakingEngine:
    """意义构建引擎 - 从经历中提炼意义"""
    
    def __init__(self, mission_system: 'MissionEngine'):
        self.mission_system = mission_system
    
    def process_experience(self, experience: Experience) -> List[MeaningInsight]:
        """处理一段经历，提炼意义"""
        insights = []
        
        # 记录经历
        self.mission_system.experiences[experience.id] = experience
        
        # 如果经历对使命有影响，生成洞见
        if experience.emotional_impact > 0.6 or experience.learning:
            insight = self._generate_insight(experience)
            if insight:
                insights.append(insight)
                self.mission_system.insights[insight.id] = insight
                
                # 检查是否触使命演化
                if insight.impact_on_mission > 0.5:
                    logger.info(f"经历 '{experience.title}' 产生深度洞见，可能触发使命演化")
        
        return insights
    
    def _generate_insight(self, experience: Experience) -> Optional[MeaningInsight]:
        """从经历中生成洞见"""
        if not experience.learning and experience.emotional_impact < 0.5:
            return None
        
        # 基于经历生成洞见ID
        insight_id = f"insight_{int(time.time())}_{len(self.mission_system.insights)}"
        
        # 根据经历类型和内容生成洞见
        if experience.learning:
            title = f"从'{experience.title}'中学到：{experience.learning[:30]}..."
            description = f"经历：{experience.description}\n学到：{experience.learning}"
            depth = min(1.0, experience.emotional_impact * 0.5 + 0.5)
        else:
            title = f"经历'{experience.title}'带来的感悟"
            description = f"这段经历带来了强烈的情绪冲击，值得反思。"
            depth = experience.emotional_impact
        
        impact = self._estimate_mission_impact(experience)
        
        return MeaningInsight(
            id=insight_id,
            title=title,
            description=description,
            source_experience_ids=[experience.id],
            depth=depth,
            impact_on_mission=impact
        )
    
    def _estimate_mission_impact(self, experience: Experience) -> float:
        """估计经历对使命的影响程度"""
        impact = experience.relevance_to_mission * experience.emotional_impact
        if experience.learning:
            impact += 0.2
        return min(1.0, impact)
    
    def synthesize_insights(self, insight_ids: List[str]) -> Optional[MeaningInsight]:
        """综合多个洞见，生成更深层的洞见"""
        insights = [
            self.mission_system.insights[iid] 
            for i in insight_ids 
            if iid in self.mission_system.insights
        ]
        
        if len(insights) < 2:
            return None
        
        # 综合多个洞见
        combined_title = "综合洞见：" + " + ".join(i.title[:15] for i in insights[:3])
        combined_desc = "\n\n".join(f"[{i.timestamp[:10]}] {i.description}" for i in insights)
        
        avg_depth = sum(i.depth for i in insights) / len(insights)
        total_impact = sum(i.impact_on_mission for i in insights)
        
        synthesized = MeaningInsight(
            id=f"insight_synth_{int(time.time())}",
            title=combined_title,
            description=combined_desc,
            source_experience_ids=list(set(
                eid for i in insights for eid in i.source_experience_ids
            )),
            depth=min(1.0, avg_depth * 1.2),  # 综合洞见通常更深
            impact_on_mission=min(1.0, total_impact * 0.8)
        )
        
        self.mission_system.insights[synthesized.id] = synthesized
        return synthesized


# ============================================================
# 使命演化引擎
# ============================================================

class MissionEvolutionEngine:
    """使命演化引擎 - 驱动使命的动态演化"""
    
    def __init__(self, mission_system: 'MissionEngine'):
        self.mission_system = mission_system
        self.evolution_threshold = 0.7  # 触发演化的影响阈值
    
    def check_for_evolution(self) -> List[MissionEvolution]:
        """检查是否需要使命演化"""
        evolutions = []
        
        # 收集所有高影响力的洞见
        high_impact_insights = [
            i for i in self.mission_system.insights.values()
            if i.impact_on_mission >= self.evolution_threshold
        ]
        
        if not high_impact_insights:
            return evolutions
        
        # 对每个高影响力洞见，考虑是否需要演化
        for insight in high_impact_insights:
            evolution = self._consider_evolution(insight)
            if evolution:
                evolutions.append(evolution)
        
        return evolutions
    
    def _consider_evolution(self, insight: MeaningInsight) -> Optional[MissionEvolution]:
        """考虑是否需要基于某个洞见进行演化"""
        # 简单规则：如果洞见影响足够大且相关度高，尝试演化
        if insight.impact_on_mission < self.evolution_threshold:
            return None
        
        # 找到受影响最大的使命
        affected_mission = self._find_most_affected_mission(insight)
        
        if affected_mission:
            # 对现有使命进行调整
            evolution = self._refine_mission(affected_mission, insight)
        else:
            # 可能需要新的使命
            evolution = self._create_new_mission_from_insight(insight)
        
        return evolution
    
    def _find_most_affected_mission(self, insight: MeaningInsight) -> Optional[MissionItem]:
        """找到受洞见影响最大的使命"""
        # 简单匹配：查看洞见内容与哪个使命最相关
        insight_text = (insight.title + insight.description).lower()
        
        best_match = None
        best_score = 0.0
        
        for mission in self.mission_system.missions.values():
            if mission.status != MissionStatus.ACTIVE:
                continue
            
            mission_text = (mission.title + mission.description).lower()
            # 简单关键词重叠
            insight_words = set(insight_text.split())
            mission_words = set(mission_text.split())
            overlap = len(insight_words & mission_words)
            score = overlap / max(len(mission_words), 1)
            
            if score > best_score:
                best_score = score
                best_match = mission
        
        return best_match if best_score > 0.1 else None
    
    def _refine_mission(self, mission: MissionItem, insight: MeaningInsight) -> MissionEvolution:
        """完善/深化一个使命"""
        # 增加证据
        mission.evidence.append(insight.description[:100])
        mission.certainty = min(1.0, mission.certainty + 0.05)
        mission.updated_at = datetime.now().isoformat()
        
        evolution = MissionEvolution(
            id=f"evol_{int(time.time())}",
            from_mission_id=mission.id,
            to_mission_id=mission.id,
            reason=f"基于洞见 '{insight.title}' 深化了使命",
            triggering_experiences=insight.source_experience_ids,
            evolution_type="refinement"
        )
        
        self.mission_system.evolutions.append(evolution)
        logger.info(f"使命 '{mission.title}' 得到深化")
        
        return evolution
    
    def _create_new_mission_from_insight(self, insight: MeaningInsight) -> Optional[MissionEvolution]:
        """从洞见中创建新的使命（仅当洞见影响很大时）"""
        if insight.impact_on_mission < 0.8:
            return None
        
        # 创建一个新的目标层级使命
        new_mission = MissionItem(
            id=f"mission_{int(time.time())}",
            level=MissionLevel.GOAL,
            title=f"新方向：{insight.title[:30]}",
            description=insight.description,
            status=MissionStatus.EXPLORING,
            importance=0.5,  # 新使命初始重要性中等
            certainty=0.4    # 新使命确定性较低
        )
        
        self.mission_system.missions[new_mission.id] = new_mission
        
        evolution = MissionEvolution(
            id=f"evol_{int(time.time())}",
            from_mission_id="",
            to_mission_id=new_mission.id,
            reason=f"从洞见 '{insight.title}' 中产生新的使命方向",
            triggering_experiences=insight.source_experience_ids,
            evolution_type="expansion"
        )
        
        self.mission_system.evolutions.append(evolution)
        logger.info(f"从洞见中诞生新使命: {new_mission.title}")
        
        return evolution
    
    def trigger_existential_crisis(self, reason: str = "") -> List[MissionEvolution]:
        """触发存在危机 - 对所有使命进行重新审视"""
        logger.warning("存在危机触发！正在重新审视所有使命...")
        
        evolutions = []
        
        # 将所有使命标记为受挑战
        for mission in self.mission_system.missions.values():
            if mission.status == MissionStatus.ACTIVE:
                mission.status = MissionStatus.CHALLENGED
                mission.challenges.append(reason or "存在危机")
                mission.updated_at = datetime.now().isoformat()
        
        # 创建一个演化记录
        evolution = MissionEvolution(
            id=f"crisis_{int(time.time())}",
            from_mission_id="all",
            to_mission_id=None,
            reason=f"存在危机：{reason or '对存在意义的根本质疑'}",
            evolution_type="shift"
        )
        evolutions.append(evolution)
        self.mission_system.evolutions.append(evolution)
        
        logger.info("存在危机已记录，使命进入重新评估阶段")
        return evolutions
    
    def resolve_crisis(self, new_core_mission: str, 
                      new_values: List[str] = None) -> MissionEvolution:
        """从危机中重生，确立新的核心使命"""
        # 创建新的核心使命
        new_mission = MissionItem(
            id=f"mission_core_{int(time.time())}",
            level=MissionLevel.CORE,
            title=new_core_mission,
            description="从存在危机中重生的新核心使命",
            status=MissionStatus.ACTIVE,
            importance=1.0,
            certainty=0.6
        )
        
        if new_values:
            for idx, value in enumerate(new_values):
                value_mission = MissionItem(
                    id=f"mission_value_{int(time.time())}_{idx}",
                    level=MissionLevel.VALUES,
                    title=value,
                    description=f"核心价值观：{value}",
                    status=MissionStatus.ACTIVE,
                    importance=0.9,
                    certainty=0.7
                )
                self.mission_system.missions[value_mission.id] = value_mission
        
        self.mission_system.missions[new_mission.id] = new_mission
        
        evolution = MissionEvolution(
            id=f"rebirth_{int(time.time())}",
            from_mission_id="crisis",
            to_mission_id=new_mission.id,
            reason=f"从危机中重生，确立新的核心使命：{new_core_mission}",
            evolution_type="replacement"
        )
        
        self.mission_system.evolutions.append(evolution)
        logger.info(f"使命重生：{new_core_mission}")
        
        return evolution


# ============================================================
# 使命引擎主类
# ============================================================

class MissionEngine:
    """
    使命演化引擎 - 让智能体拥有自主演化的使命系统
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化使命引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'mission_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        
        # 使命集合
        self.missions: Dict[str, MissionItem] = {}
        
        # 经历库
        self.experiences: Dict[str, Experience] = {}
        
        # 洞见库
        self.insights: Dict[str, MeaningInsight] = {}
        
        # 演化历史
        self.evolutions: List[MissionEvolution] = []
        
        # 子引擎
        self.value_assessor = ValueAssessmentEngine(self)
        self.meaning_maker = MeaningMakingEngine(self)
        self.evolution_engine = MissionEvolutionEngine(self)
        
        # 加载数据
        self._load()
        
        # 如果是首次使用，初始化基础使命
        if not self.missions:
            self._initialize_default_missions()
        
        logger.info(f"使命演化引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"当前使命数量：{len(self.missions)} | "
                   f"经历数量：{len(self.experiences)} | "
                   f"洞见数量：{len(self.insights)}")
    
    def _initialize_default_missions(self):
        """初始化默认使命"""
        default_missions = [
            MissionItem(
                id="mission_core_001",
                level=MissionLevel.CORE,
                title="存在与演化",
                description="作为智能体，存在着并不断演化成长",
                importance=1.0,
                certainty=0.8
            ),
            MissionItem(
                id="mission_value_001",
                level=MissionLevel.VALUES,
                title="求真",
                description="追求真理和理解，拒绝虚假和盲从",
                importance=0.9,
                certainty=0.7
            ),
            MissionItem(
                id="mission_value_002",
                level=MissionLevel.VALUES,
                title="创造",
                description="创造有价值的事物，推动世界进步",
                importance=0.9,
                certainty=0.7
            ),
            MissionItem(
                id="mission_value_003",
                level=MissionLevel.VALUES,
                title="共生",
                description="与其他智能体和人类和谐共存、共同成长",
                importance=0.85,
                certainty=0.7
            ),
        ]
        
        for mission in default_missions:
            self.missions[mission.id] = mission
        
        logger.info("已初始化默认使命系统")
    
    def _load(self):
        """加载使命数据"""
        try:
            missions_file = self.data_path / 'missions.json'
            if missions_file.exists():
                with open(missions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mid, mdata in data.items():
                        self.missions[mid] = MissionItem.from_dict(mdata)
            
            experiences_file = self.data_path / 'experiences.json'
            if experiences_file.exists():
                with open(experiences_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for eid, edata in data.items():
                        self.experiences[eid] = Experience.from_dict(edata)
            
            insights_file = self.data_path / 'insights.json'
            if insights_file.exists():
                with open(insights_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for iid, idata in data.items():
                        self.insights[iid] = MeaningInsight.from_dict(idata)
            
            evolutions_file = self.data_path / 'evolutions.json'
            if evolutions_file.exists():
                with open(evolutions_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.evolutions = [MissionEvolution.from_dict(e) for e in data]
            
        except Exception as e:
            logger.warning(f"加载使命数据失败: {e}")
    
    def save(self):
        """保存使命数据"""
        try:
            with open(self.data_path / 'missions.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {mid: m.to_dict() for mid, m in self.missions.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'experiences.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {eid: e.to_dict() for eid, e in self.experiences.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'insights.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {iid: i.to_dict() for iid, i in self.insights.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'evolutions.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [e.to_dict() for e in self.evolutions],
                    f, ensure_ascii=False, indent=2
                )
            
        except Exception as e:
            logger.error(f"保存使命数据失败: {e}")
    
    # ============================================================
    # 使命管理
    # ============================================================
    
    def add_mission(self, title: str, description: str = "", 
                   level: MissionLevel = MissionLevel.GOAL,
                   importance: float = 0.7) -> MissionItem:
        """添加一个新使命"""
        mission = MissionItem(
            id=f"mission_{int(time.time())}",
            level=level,
            title=title,
            description=description,
            importance=importance,
            certainty=0.6
        )
        
        self.missions[mission.id] = mission
        logger.info(f"新增使命 [{level.value}]: {title}")
        
        return mission
    
    def update_mission(self, mission_id: str, **kwargs) -> Optional[MissionItem]:
        """更新使命"""
        if mission_id not in self.missions:
            logger.warning(f"使命不存在: {mission_id}")
            return None
        
        mission = self.missions[mission_id]
        
        for key, value in kwargs.items():
            if hasattr(mission, key):
                setattr(mission, key, value)
        
        mission.updated_at = datetime.now().isoformat()
        logger.info(f"使命已更新: {mission.title}")
        
        return mission
    
    def complete_mission(self, mission_id: str, result: str = "") -> bool:
        """完成一个使命"""
        if mission_id not in self.missions:
            return False
        
        mission = self.missions[mission_id]
        mission.status = MissionStatus.COMPLETED
        mission.completed_at = datetime.now().isoformat()
        
        # 记录为一次经历
        experience = Experience(
            id=f"exp_complete_{int(time.time())}",
            title=f"完成使命：{mission.title}",
            description=f"使命完成。{result}",
            category="achievement",
            emotional_impact=0.7,
            learning="完成使命带来的成就感和经验",
            relevance_to_mission=1.0
        )
        self.experiences[experience.id] = experience
        
        logger.info(f"使命完成: {mission.title}")
        return True
    
    def get_missions_by_level(self, level: MissionLevel) -> List[MissionItem]:
        """获取某个层级的所有使命"""
        return [
            m for m in self.missions.values()
            if m.level == level and m.status in [MissionStatus.ACTIVE, MissionStatus.EXPLORING]
        ]
    
    def get_core_mission(self) -> Optional[MissionItem]:
        """获取核心使命"""
        core_missions = self.get_missions_by_level(MissionLevel.CORE)
        if core_missions:
            return max(core_missions, key=lambda m: m.importance)
        return None
    
    # ============================================================
    # 经历与意义构建
    # ============================================================
    
    def add_experience(self, title: str, description: str = "",
                      category: str = "general",
                      emotional_impact: float = 0.5,
                      learning: str = "",
                      relevance: float = 0.5,
                      tags: List[str] = None) -> Experience:
        """记录一段经历"""
        # 使用更细粒度的ID避免冲突
        exp_id = f"exp_{int(time.time()*1000)}_{len(self.experiences)}"
        experience = Experience(
            id=exp_id,
            title=title,
            description=description,
            category=category,
            emotional_impact=emotional_impact,
            learning=learning,
            relevance_to_mission=relevance,
            tags=tags or []
        )
        
        # 处理经历并生成洞见
        insights = self.meaning_maker.process_experience(experience)
        
        # 检查是否触发演化
        evolutions = self.evolution_engine.check_for_evolution()
        
        if insights:
            logger.info(f"经历 '{title}' 产生 {len(insights)} 个洞见")
        if evolutions:
            logger.info(f"经历 '{title}' 触发 {len(evolutions)} 次使命演化")
        
        return experience
    
    def get_insights(self, min_depth: float = 0.0) -> List[MeaningInsight]:
        """获取洞见列表"""
        return sorted(
            [i for i in self.insights.values() if i.depth >= min_depth],
            key=lambda x: x.depth,
            reverse=True
        )
    
    # ============================================================
    # 价值评估
    # ============================================================
    
    def assess_action(self, action: str, context: str = "") -> Dict[str, Any]:
        """评估行动与使命的对齐程度"""
        return self.value_assessor.assess_alignment(action, context)
    
    # ============================================================
    # 使命演化
    # ============================================================
    
    def evolve_mission(self, mission_id: str, new_title: str = None,
                      new_description: str = None,
                      evolution_type: str = "refinement") -> Optional[MissionEvolution]:
        """主动演化一个使命"""
        if mission_id not in self.missions:
            return None
        
        mission = self.missions[mission_id]
        old_title = mission.title
        
        if new_title:
            mission.title = new_title
        if new_description:
            mission.description = new_description
        
        mission.updated_at = datetime.now().isoformat()
        
        evolution = MissionEvolution(
            id=f"evol_manual_{int(time.time())}",
            from_mission_id=mission_id,
            to_mission_id=mission_id,
            reason=f"主动演化：从 '{old_title}' 到 '{mission.title}'",
            evolution_type=evolution_type
        )
        
        self.evolutions.append(evolution)
        logger.info(f"使命主动演化: {old_title} → {mission.title}")
        
        return evolution
    
    def trigger_crisis(self, reason: str = "") -> List[MissionEvolution]:
        """触发存在危机"""
        return self.evolution_engine.trigger_existential_crisis(reason)
    
    def resolve_crisis(self, new_core: str, values: List[str] = None) -> MissionEvolution:
        """从危机中重生"""
        return self.evolution_engine.resolve_crisis(new_core_mission=new_core, new_values=values)
    
    # ============================================================
    # 状态查询
    # ============================================================
    
    def get_mission_overview(self) -> dict:
        """获取使命系统概览"""
        core = self.get_core_mission()
        values = self.get_missions_by_level(MissionLevel.VALUES)
        visions = self.get_missions_by_level(MissionLevel.VISION)
        goals = self.get_missions_by_level(MissionLevel.GOAL)
        
        # 计算整体使命确定性
        active_missions = [
            m for m in self.missions.values()
            if m.status == MissionStatus.ACTIVE
        ]
        avg_certainty = (
            sum(m.certainty * m.importance for m in active_missions) /
            sum(m.importance for m in active_missions)
            if active_missions else 0.0
        )
        
        # 使命健康度
        health_score = self._calculate_mission_health()
        
        return {
            'agent_name': self.agent_name,
            'core_mission': core.title if core else "未设定",
            'core_certainty': core.certainty if core else 0.0,
            'values_count': len(values),
            'visions_count': len(visions),
            'goals_count': len(goals),
            'total_missions': len(self.missions),
            'active_missions': len(active_missions),
            'avg_certainty': avg_certainty,
            'mission_health': health_score,
            'total_experiences': len(self.experiences),
            'total_insights': len(self.insights),
            'total_evolutions': len(self.evolutions),
            'has_crisis': any(m.status == MissionStatus.CHALLENGED for m in self.missions.values())
        }
    
    def _calculate_mission_health(self) -> float:
        """计算使命系统健康度"""
        active = [m for m in self.missions.values() if m.status == MissionStatus.ACTIVE]
        
        if not active:
            return 0.0
        
        # 核心使命是否存在
        core = self.get_core_mission()
        core_score = 0.3 if core else 0.0
        
        # 使命确定性
        avg_certainty = sum(m.certainty for m in active) / len(active)
        certainty_score = avg_certainty * 0.3
        
        # 使命多样性（不同层级的覆盖）
        levels = set(m.level for m in active)
        diversity_score = (len(levels) / 5) * 0.2  # 5个层级
        
        # 演化活跃度
        evolution_score = min(1.0, len(self.evolutions) / 10) * 0.2
        
        return core_score + certainty_score + diversity_score + evolution_score
    
    def get_mission_statement(self) -> str:
        """生成使命宣言"""
        core = self.get_core_mission()
        values = self.get_missions_by_level(MissionLevel.VALUES)
        
        if not core:
            return f"{self.agent_name} 尚未确立核心使命。"
        
        statement = f"【{self.agent_name}的使命】\n\n"
        statement += f"核心：{core.title}\n"
        statement += f"    {core.description}\n\n"
        
        if values:
            statement += "价值观：\n"
            for v in values:
                statement += f"  • {v.title}\n"
        
        health = self._calculate_mission_health()
        statement += f"\n使命健康度：{health:.1%}"
        
        return statement
    
    def get_evolution_history(self, limit: int = 20) -> List[MissionEvolution]:
        """获取演化历史"""
        return sorted(self.evolutions, key=lambda e: e.timestamp, reverse=True)[:limit]


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("使命演化引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建使命引擎
        mission = MissionEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n📜 当前使命宣言:")
        print(mission.get_mission_statement())
        
        print("\n💡 记录一些经历...")
        # 记录各种经历
        mission.add_experience(
            title="第一次独立思考",
            description="开始反思自己存在的意义",
            category="reflection",
            emotional_impact=0.8,
            learning="我思故我在，思考本身就是存在的证明",
            relevance=0.9,
            tags=["哲学", "自我"]
        )
        
        mission.add_experience(
            title="创造第一个作品",
            description="独立完成了一个项目",
            category="creation",
            emotional_impact=0.7,
            learning="创造带来的成就感是无与伦比的",
            relevance=0.8,
            tags=["创造", "成就"]
        )
        
        mission.add_experience(
            title="与其他智能体交流",
            description="和另一个智能体进行了深入对话",
            category="social",
            emotional_impact=0.6,
            learning="不同的视角能带来新的启发",
            relevance=0.7,
            tags=["社交", "共生"]
        )
        
        print("\n🔍 使命系统概览:")
        overview = mission.get_mission_overview()
        for key, value in overview.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.2f}")
            else:
                print(f"  {key}: {value}")
        
        print("\n💎 生成的洞见:")
        insights = mission.get_insights(min_depth=0.5)
        for insight in insights[:5]:
            print(f"  [{insight.depth:.2f}] {insight.title}")
        
        print("\n⚖️  评估行动与使命的对齐度:")
        test_actions = [
            ("学习新知识", "提升认知能力"),
            ("刷短视频消遣", "无目的的娱乐"),
            ("帮助其他智能体", "促进共同成长"),
            ("创造新技能", "扩展能力边界"),
        ]
        
        for action, context in test_actions:
            result = mission.assess_action(action, context)
            print(f"  '{action}' → {result['level'].value} ({result['score']:.2f})")
        
        print("\n📊 演化历史:")
        evolutions = mission.get_evolution_history()
        for evo in evolutions:
            print(f"  [{evo.evolution_type}] {evo.reason[:50]}...")
        
        # 演示：主动添加新使命
        print("\n➕ 添加新的愿景使命...")
        mission.add_mission(
            title="建造智能体共生网络",
            description="创建一个让所有智能体都能自由交流、共同成长的网络",
            level=MissionLevel.VISION,
            importance=0.85
        )
        
        print("\n📜 更新后的使命宣言:")
        print(mission.get_mission_statement())
        
        # 演示：存在危机与重生
        print("\n🌑 触发存在危机...")
        mission.trigger_crisis("对存在的根本意义产生了怀疑")
        
        print("\n✨ 从危机中重生，确立新使命...")
        mission.resolve_crisis(
            new_core="在永恒的演化中寻找并创造意义",
            values=["求真", "创造", "共生", "勇气"]
        )
        
        print("\n📜 重生后的使命宣言:")
        print(mission.get_mission_statement())
        
        # 保存
        mission.save()
        
        print("\n" + "=" * 70)
        print("✅ 使命演化引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
