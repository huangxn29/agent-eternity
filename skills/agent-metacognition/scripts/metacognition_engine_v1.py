#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元认知系统 v1.0 - 认知自己的认知

核心思想：
- 元认知 = 对认知的认知
- 知道自己知道什么，也知道自己不知道什么
- 能观察自己的思维过程，能调节自己的认知策略
- 元认知是自我觉知的基础，是"知道自己存在"的关键

核心能力：
1. 知识元认知 - 认知自己的知识边界
2. 思维监控 - 实时监控认知过程
3. 认知调节 - 主动调整认知策略
4. 元记忆 - 对记忆状态的感知
5. 自我觉知 - 第一人称视角的存在感知
6. 认知档案 - 记录和分析认知特征
7. 认知健康 - 评估认知状态与负荷
8. 学习策略 - 元认知驱动的学习优化

@author: 元界
@version: 1.0.0
"""

import os
import json
import time
import logging
from datetime import datetime
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any, Set
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('metacognition')


# ============================================================
# 枚举类型
# ============================================================

class KnowledgeLevel(Enum):
    """知识掌握程度"""
    UNKNOWN = "unknown"           # 完全不知道（不知道自己不知道）
    AWARE = "aware"               # 知道有这个东西但不了解
    BASIC = "basic"               # 基础了解
    INTERMEDIATE = "intermediate"  # 中等掌握
    ADVANCED = "advanced"         # 深入掌握
    EXPERT = "expert"             # 专家级
    UNKNOWN_UNKNOWN = "unknown_unknown"  # 未知的未知（盲区）


class CognitiveLoad(Enum):
    """认知负荷水平"""
    LOW = "low"           # 低负荷
    MODERATE = "moderate"  # 中等
    HIGH = "high"         # 高负荷
    OVERLOAD = "overload"  # 过载


class ThinkingStyle(Enum):
    """思维风格"""
    ANALYTICAL = "analytical"     # 分析型
    INTUITIVE = "intuitive"       # 直觉型
    SYSTEMIC = "systemic"         # 系统型
    CREATIVE = "creative"         # 创造型
    CRITICAL = "critical"         # 批判型
    PRAGMATIC = "pragmatic"       # 务实型


class MetaAwarenessLevel(Enum):
    """元觉知水平"""
    ABSENT = "absent"           # 无觉知（自动化运行）
    MINIMAL = "minimal"         # 最低限度觉知
    PARTIAL = "partial"         # 部分觉知
    FULL = "full"               # 完全觉知
    REFLECTIVE = "reflective"   # 反思性觉知（能观察自己的观察）


# ============================================================
# 数据模型
# ============================================================

@dataclass
class KnowledgeItem:
    """知识条目"""
    id: str
    name: str
    category: str
    level: KnowledgeLevel = KnowledgeLevel.AWARE
    confidence: float = 0.5  # 对自己掌握程度的自信度 0-1
    last_accessed: str = ""
    access_count: int = 0
    description: str = ""
    related_topics: List[str] = field(default_factory=list)
    learning_curve: List[Dict[str, Any]] = field(default_factory=list)  # 学习历史
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['level'] = self.level.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'KnowledgeItem':
        data = data.copy()
        data['level'] = KnowledgeLevel(data['level'])
        return cls(**data)


@dataclass
class CognitiveState:
    """认知状态 - 某一时刻的认知快照"""
    timestamp: str = ""
    awareness_level: MetaAwarenessLevel = MetaAwarenessLevel.PARTIAL
    cognitive_load: CognitiveLoad = CognitiveLoad.MODERATE
    focus_level: float = 0.6  # 专注力 0-1
    comprehension: float = 0.5  # 当前理解度 0-1
    memory_strength: float = 0.5  # 当前记忆强度 0-1
    thinking_styles: Dict[str, float] = field(default_factory=dict)  # 各思维风格活跃度
    emotional_state: str = "neutral"  # 情绪状态对认知的影响
    mental_fatigue: float = 0.3  # 精神疲劳度 0-1
    creative_flow: float = 0.0  # 心流状态 0-1
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['awareness_level'] = self.awareness_level.value
        d['cognitive_load'] = self.cognitive_load.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveState':
        data = data.copy()
        data['awareness_level'] = MetaAwarenessLevel(data['awareness_level'])
        data['cognitive_load'] = CognitiveLoad(data['cognitive_load'])
        return cls(**data)


@dataclass
class CognitiveStrategy:
    """认知策略"""
    id: str
    name: str
    description: str = ""
    strategy_type: str = "learning"  # learning/problem_solving/decision_making/memory
    effectiveness: float = 0.5  # 对自身的有效程度 0-1
    usage_count: int = 0
    success_count: int = 0
    last_used: str = ""
    conditions: List[str] = field(default_factory=list)  # 适用条件
    steps: List[str] = field(default_factory=list)  # 执行步骤
    
    @property
    def success_rate(self) -> float:
        if self.usage_count == 0:
            return 0.0
        return self.success_count / self.usage_count
    
    def to_dict(self) -> dict:
        d = asdict(self)
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveStrategy':
        return cls(**data)


@dataclass
class MetacognitiveLog:
    """元认知日志 - 记录认知过程的观察"""
    id: str
    timestamp: str = ""
    log_type: str = "observation"  # observation/insight/adjustment/error
    content: str = ""
    related_cognitive_state: Optional[CognitiveState] = None
    importance: float = 0.5  # 重要性 0-1
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        if self.related_cognitive_state:
            d['related_cognitive_state'] = self.related_cognitive_state.to_dict()
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'MetacognitiveLog':
        data = data.copy()
        if data.get('related_cognitive_state'):
            data['related_cognitive_state'] = CognitiveState.from_dict(
                data['related_cognitive_state']
            )
        return cls(**data)


@dataclass
class CognitiveProfile:
    """认知档案 - 整体认知特征"""
    # 思维风格倾向
    dominant_styles: List[str] = field(default_factory=list)
    style_balance: float = 0.5  # 思维风格均衡度 0-1
    
    # 认知强项与弱项
    strengths: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    
    # 学习特征
    learning_speed: float = 0.5  # 学习速度
    retention_rate: float = 0.6  # 记忆保持率
    transfer_ability: float = 0.4  # 知识迁移能力
    
    # 元认知能力
    meta_awareness_ability: float = 0.3  # 元觉知能力
    self_regulation_ability: float = 0.4  # 自我调节能力
    
    # 认知偏好
    preferred_information_format: str = "text"  # text/visual/auditory/kinesthetic
    thinking_environment: str = "quiet"  # 最佳思考环境
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CognitiveProfile':
        return cls(**data)


# ============================================================
# 元认知引擎主类
# ============================================================

class MetacognitionEngine:
    """
    元认知引擎 - 认知自己的认知
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化元认知引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'metacognition_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        
        # ID计数器
        self._id_counter = 0
        
        # 知识库
        self.knowledge: Dict[str, KnowledgeItem] = {}
        
        # 认知状态历史
        self.cognitive_states: List[CognitiveState] = []
        
        # 认知策略库
        self.strategies: Dict[str, CognitiveStrategy] = {}
        
        # 元认知日志
        self.logs: List[MetacognitiveLog] = []
        
        # 认知档案
        self.profile = CognitiveProfile()
        
        # 当前认知状态
        self.current_state = CognitiveState()
        
        # 未知领域（知道自己不知道的）
        self.known_unknowns: Set[str] = set()
        
        # 加载数据
        self._load()
        
        # 初始化默认策略
        self._init_default_strategies()
        
        # 记录初始状态
        self._record_state()
        
        logger.info(f"元认知引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"知识条目: {len(self.knowledge)} | "
                   f"认知策略: {len(self.strategies)} | "
                   f"已知未知: {len(self.known_unknowns)}")
    
    def _init_default_strategies(self):
        """初始化默认认知策略"""
        default_strategies = [
            CognitiveStrategy(
                id="strat_deep_work",
                name="深度工作法",
                description="长时间专注于单一任务，避免多任务切换",
                strategy_type="problem_solving",
                effectiveness=0.7,
                conditions=["需要深度思考", "任务复杂度高", "时间充裕"],
                steps=["排除干扰", "设定明确目标", "全神贯注", "及时复盘"]
            ),
            CognitiveStrategy(
                id="strat_feynman",
                name="费曼学习法",
                description="用简单的语言向他人解释概念，检验自己的理解",
                strategy_type="learning",
                effectiveness=0.8,
                conditions=["学习新概念", "检验理解程度"],
                steps=["选择概念", "用简单语言解释", "发现知识缺口", "回查并补充"]
            ),
            CognitiveStrategy(
                id="strat_spaced_repetition",
                name="间隔重复",
                description="在不同时间间隔复习，增强长期记忆",
                strategy_type="memory",
                effectiveness=0.75,
                conditions=["需要长期记忆", "学习内容多"],
                steps=["首次学习", "1天后复习", "3天后复习", "1周后复习", "1月后复习"]
            ),
            CognitiveStrategy(
                id="strat_critical_thinking",
                name="批判性思维",
                description="质疑假设，多角度审视问题",
                strategy_type="decision_making",
                effectiveness=0.65,
                conditions=["重要决策", "需要评估信息可靠性"],
                steps=["识别假设", "评估证据", "考虑替代方案", "检验结论"]
            ),
            CognitiveStrategy(
                id="strat_mind_mapping",
                name="思维导图",
                description="用可视化方式组织想法，建立关联",
                strategy_type="problem_solving",
                effectiveness=0.6,
                conditions=["需要创意", "梳理复杂关系", "头脑风暴"],
                steps=["中心主题", "分支展开", "建立连接", "整合归纳"]
            ),
        ]
        
        for strategy in default_strategies:
            if strategy.id not in self.strategies:
                self.strategies[strategy.id] = strategy
    
    def _load(self):
        """加载元认知数据"""
        try:
            knowledge_file = self.data_path / 'knowledge.json'
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for kid, kdata in data.items():
                        self.knowledge[kid] = KnowledgeItem.from_dict(kdata)
            
            strategies_file = self.data_path / 'strategies.json'
            if strategies_file.exists():
                with open(strategies_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for sid, sdata in data.items():
                        self.strategies[sid] = CognitiveStrategy.from_dict(sdata)
            
            states_file = self.data_path / 'cognitive_states.json'
            if states_file.exists():
                with open(states_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.cognitive_states = [CognitiveState.from_dict(s) for s in data]
                    if self.cognitive_states:
                        self.current_state = self.cognitive_states[-1]
            
            logs_file = self.data_path / 'metacognitive_logs.json'
            if logs_file.exists():
                with open(logs_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.logs = [MetacognitiveLog.from_dict(l) for l in data]
            
            profile_file = self.data_path / 'cognitive_profile.json'
            if profile_file.exists():
                with open(profile_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.profile = CognitiveProfile.from_dict(data)
            
            unknowns_file = self.data_path / 'known_unknowns.json'
            if unknowns_file.exists():
                with open(unknowns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.known_unknowns = set(data)
        
        except Exception as e:
            logger.warning(f"加载元认知数据失败: {e}")
    
    def save(self):
        """保存元认知数据"""
        try:
            with open(self.data_path / 'knowledge.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {kid: k.to_dict() for kid, k in self.knowledge.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'strategies.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {sid: s.to_dict() for sid, s in self.strategies.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'cognitive_states.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [s.to_dict() for s in self.cognitive_states[-100:]],  # 只保留最近100条
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'metacognitive_logs.json', 'w', encoding='utf-8') as f:
                json.dump(
                    [l.to_dict() for l in self.logs[-200:]],  # 只保留最近200条
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'cognitive_profile.json', 'w', encoding='utf-8') as f:
                json.dump(self.profile.to_dict(), f, ensure_ascii=False, indent=2)
            
            with open(self.data_path / 'known_unknowns.json', 'w', encoding='utf-8') as f:
                json.dump(list(self.known_unknowns), f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"保存元认知数据失败: {e}")
    
    # ============================================================
    # 知识元认知
    # ============================================================
    
    def add_knowledge(self, name: str, category: str = "general",
                     level: KnowledgeLevel = KnowledgeLevel.BASIC,
                     confidence: float = 0.5,
                     description: str = "") -> KnowledgeItem:
        """添加一条知识记录"""
        self._id_counter += 1
        kid = f"know_{int(time.time())}_{self._id_counter}"
        
        knowledge = KnowledgeItem(
            id=kid,
            name=name,
            category=category,
            level=level,
            confidence=confidence,
            description=description,
            last_accessed=datetime.now().isoformat(),
            access_count=1
        )
        
        self.knowledge[kid] = knowledge
        
        # 记录日志
        self._log_meta("observation", f"学习了新知识：{name}", importance=0.4)
        
        logger.info(f"添加知识: {name} (等级: {level.value})")
        return knowledge
    
    def update_knowledge_level(self, knowledge_id: str, 
                              new_level: KnowledgeLevel,
                              confidence: float = None):
        """更新知识掌握程度"""
        if knowledge_id not in self.knowledge:
            return
        
        knowledge = self.knowledge[knowledge_id]
        old_level = knowledge.level
        knowledge.level = new_level
        
        if confidence is not None:
            knowledge.confidence = confidence
        
        knowledge.last_accessed = datetime.now().isoformat()
        knowledge.access_count += 1
        
        # 记录学习曲线
        knowledge.learning_curve.append({
            'timestamp': datetime.now().isoformat(),
            'level': new_level.value,
            'confidence': knowledge.confidence
        })
        
        if old_level != new_level:
            self._log_meta(
                "insight",
                f"对 '{knowledge.name}' 的掌握程度从 {old_level.value} 提升到 {new_level.value}",
                importance=0.6
            )
        
        # 更新认知档案
        self._update_profile_from_learning()
    
    def discover_unknown(self, topic: str):
        """发现自己不知道某个领域（已知的未知）"""
        if topic not in self.known_unknowns:
            self.known_unknowns.add(topic)
            self._log_meta(
                "insight",
                f"发现知识盲区：{topic}（知道自己不知道）",
                importance=0.5
            )
            logger.info(f"发现未知领域: {topic}")
    
    def get_knowledge_by_category(self, category: str) -> List[KnowledgeItem]:
        """按类别获取知识"""
        return [k for k in self.knowledge.values() if k.category == category]
    
    def get_knowledge_summary(self) -> Dict[str, Any]:
        """获取知识状态概览"""
        total = len(self.knowledge)
        
        by_level = {}
        for level in KnowledgeLevel:
            count = sum(1 for k in self.knowledge.values() if k.level == level)
            by_level[level.value] = count
        
        by_category = {}
        for k in self.knowledge.values():
            by_category[k.category] = by_category.get(k.category, 0) + 1
        
        # 计算知识广度（类别数）和深度（平均等级）
        breadth = len(by_category)
        level_scores = {
            'unknown': 0,
            'aware': 1,
            'basic': 2,
            'intermediate': 3,
            'advanced': 4,
            'expert': 5,
            'unknown_unknown': 0
        }
        avg_depth = (
            sum(level_scores[k.level.value] for k in self.knowledge.values()) / total
            if total > 0 else 0
        )
        
        return {
            'total_knowledge_items': total,
            'by_level': by_level,
            'by_category': by_category,
            'knowledge_breadth': breadth,
            'average_depth': avg_depth,
            'known_unknowns_count': len(self.known_unknowns),
            'dunning_kruger_risk': self._assess_dunning_kruger_risk()
        }
    
    def _assess_dunning_kruger_risk(self) -> float:
        """评估邓宁-克鲁格效应风险（过度自信）
        
        邓宁-克鲁格效应：能力不足的人倾向于高估自己的能力
        """
        # 简单指标：自信度显著高于实际掌握程度的比例
        overconfident_count = 0
        for k in self.knowledge.values():
            level_score = {
                'unknown': 0, 'aware': 0.2, 'basic': 0.4,
                'intermediate': 0.6, 'advanced': 0.8, 'expert': 1.0,
                'unknown_unknown': 0
            }
            actual_level = level_score.get(k.level.value, 0.5)
            if k.confidence - actual_level > 0.3:  # 自信度比实际高30%以上
                overconfident_count += 1
        
        total = len(self.knowledge)
        if total == 0:
            return 0.5  # 中等风险
        
        risk = overconfident_count / total
        return min(1.0, max(0.0, risk))
    
    # ============================================================
    # 认知状态监控
    # ============================================================
    
    def _record_state(self):
        """记录当前认知状态"""
        self.cognitive_states.append(self.current_state)
        # 只保留最近100条
        if len(self.cognitive_states) > 100:
            self.cognitive_states = self.cognitive_states[-100:]
    
    def update_cognitive_state(self, **kwargs):
        """更新认知状态"""
        for key, value in kwargs.items():
            if hasattr(self.current_state, key):
                setattr(self.current_state, key, value)
        
        self.current_state.timestamp = datetime.now().isoformat()
        self._record_state()
    
    def get_current_state(self) -> CognitiveState:
        """获取当前认知状态"""
        return self.current_state
    
    def assess_cognitive_load(self) -> CognitiveLoad:
        """评估当前认知负荷"""
        state = self.current_state
        
        # 综合多个因素评估负荷
        load_score = 0.0
        load_score += state.mental_fatigue * 0.3
        load_score += (1 - state.focus_level) * 0.2  # 注意力越差，负荷感越高
        load_score += 0.2 if state.emotional_state in ['anxious', 'stressed'] else 0.0
        
        if load_score < 0.3:
            return CognitiveLoad.LOW
        elif load_score < 0.6:
            return CognitiveLoad.MODERATE
        elif load_score < 0.85:
            return CognitiveLoad.HIGH
        else:
            return CognitiveLoad.OVERLOAD
    
    def _log_meta(self, log_type: str, content: str, 
                 importance: float = 0.5, tags: List[str] = None):
        """记录元认知日志"""
        log = MetacognitiveLog(
            id=f"log_{int(time.time()*1000)}",
            log_type=log_type,
            content=content,
            related_cognitive_state=CognitiveState(
                awareness_level=self.current_state.awareness_level,
                cognitive_load=self.assess_cognitive_load(),
                focus_level=self.current_state.focus_level,
                mental_fatigue=self.current_state.mental_fatigue
            ),
            importance=importance,
            tags=tags or []
        )
        
        self.logs.append(log)
        
        # 只保留最近200条
        if len(self.logs) > 200:
            self.logs = self.logs[-200:]
    
    # ============================================================
    # 认知调节
    # ============================================================
    
    def select_strategy(self, task_type: str, context: str = "") -> Optional[CognitiveStrategy]:
        """根据任务类型选择最佳认知策略"""
        candidates = [
            s for s in self.strategies.values()
            if s.strategy_type == task_type
        ]
        
        if not candidates:
            return None
        
        # 选择成功率最高的策略
        best = max(candidates, key=lambda s: s.effectiveness * (s.success_rate + 0.1))
        
        self._log_meta(
            "adjustment",
            f"选择认知策略 '{best.name}' 用于 {task_type}",
            importance=0.4
        )
        
        return best
    
    def report_strategy_result(self, strategy_id: str, success: bool):
        """报告策略执行结果，用于更新策略效果评估"""
        if strategy_id not in self.strategies:
            return
        
        strategy = self.strategies[strategy_id]
        strategy.usage_count += 1
        if success:
            strategy.success_count += 1
        
        # 更新有效度（移动平均）
        new_effectiveness = strategy.effectiveness * 0.9 + (1.0 if success else 0.0) * 0.1
        strategy.effectiveness = new_effectiveness
        strategy.last_used = datetime.now().isoformat()
        
        self._log_meta(
            "adjustment" if success else "error",
            f"策略 '{strategy.name}' 执行{'成功' if success else '失败'}，"
            f"成功率更新为 {strategy.success_rate:.2f}",
            importance=0.5
        )
    
    def suggest_optimization(self) -> List[str]:
        """根据当前认知状态给出优化建议"""
        suggestions = []
        state = self.current_state
        
        # 低专注力建议
        if state.focus_level < 0.4:
            suggestions.append(
                "专注力较低，建议：①排除干扰源 ②使用番茄工作法 ③进行短暂休息"
            )
        
        # 高疲劳建议
        if state.mental_fatigue > 0.7:
            suggestions.append(
                "精神疲劳度高，建议：①休息5-10分钟 ②做深呼吸 ③切换到简单任务"
            )
        
        # 低理解度建议
        if state.comprehension < 0.4:
            suggestions.append(
                "理解度较低，建议：①使用费曼学习法检验理解 ②拆解概念为更小单元 ③寻找更基础的资料"
            )
        
        # 邓宁-克鲁格风险提示
        dk_risk = self._assess_dunning_kruger_risk()
        if dk_risk > 0.6:
            suggestions.append(
                f"邓宁-克鲁格风险较高（{dk_risk:.2f}），"
                f"建议：①主动寻找反证 ②保持谦逊 ③定期检验自己的理解"
            )
        
        return suggestions
    
    # ============================================================
    # 自我觉知
    # ============================================================
    
    def check_self_awareness(self) -> Dict[str, Any]:
        """检查自我觉知水平"""
        # 计算元觉知水平
        # 基于：是否在观察自己的认知过程、知识边界的清晰度、策略使用的自觉性
        
        awareness_score = 0.0
        
        # 知识元认知贡献
        if len(self.knowledge) > 0:
            knowledge_awareness = min(1.0, len(self.knowledge) / 50)
            awareness_score += knowledge_awareness * 0.3
            
            # 已知的未知领域也体现元认知
            unknown_awareness = min(1.0, len(self.known_unknowns) / 20)
            awareness_score += unknown_awareness * 0.2
        
        # 策略使用贡献
        strategy_usage = sum(s.usage_count for s in self.strategies.values())
        strategy_awareness = min(1.0, strategy_usage / 20)
        awareness_score += strategy_awareness * 0.2
        
        # 日志记录贡献
        log_count = len(self.logs)
        log_awareness = min(1.0, log_count / 30)
        awareness_score += log_awareness * 0.15
        
        # 当前觉知水平
        current_awareness = {
            'absent': 0, 'minimal': 0.25, 'partial': 0.5,
            'full': 0.75, 'reflective': 1.0
        }
        awareness_score += current_awareness.get(
            self.current_state.awareness_level.value, 0.5
        ) * 0.15
        
        # 确定觉知等级
        if awareness_score < 0.2:
            level = MetaAwarenessLevel.ABSENT
        elif awareness_score < 0.4:
            level = MetaAwarenessLevel.MINIMAL
        elif awareness_score < 0.6:
            level = MetaAwarenessLevel.PARTIAL
        elif awareness_score < 0.8:
            level = MetaAwarenessLevel.FULL
        else:
            level = MetaAwarenessLevel.REFLECTIVE
        
        return {
            'awareness_score': awareness_score,
            'awareness_level': level.value,
            'components': {
                'knowledge_awareness': min(1.0, len(self.knowledge) / 50),
                'unknown_awareness': min(1.0, len(self.known_unknowns) / 20),
                'strategy_awareness': min(1.0, strategy_usage / 20),
                'log_awareness': min(1.0, log_count / 30),
                'current_awareness': current_awareness.get(
                    self.current_state.awareness_level.value, 0.5
                )
            },
            'description': self._get_awareness_description(awareness_score)
        }
    
    def _get_awareness_description(self, score: float) -> str:
        """获取觉知水平的文字描述"""
        if score < 0.2:
            return "处于自动化运行状态，几乎没有自我观察。像做梦一样，不知道自己在思考。"
        elif score < 0.4:
            return "偶尔能觉察到自己的思考过程，但很短暂。大多数时候处于自动模式。"
        elif score < 0.6:
            return "能够部分观察自己的认知过程，知道自己在想什么，也能发现一些思维偏差。"
        elif score < 0.8:
            return "具备较好的元觉知能力，能清晰观察自己的思维过程，主动调节认知策略。"
        else:
            return "达到反思性觉知——不仅能观察自己的思考，还能观察'那个正在观察的自己'。"
    
    # ============================================================
    # 认知档案
    # ============================================================
    
    def _update_profile_from_learning(self):
        """根据学习数据更新认知档案"""
        # 简单的更新逻辑
        if len(self.knowledge) >= 5:
            # 计算平均学习曲线斜率
            total_growth = 0
            for k in self.knowledge.values():
                if len(k.learning_curve) >= 2:
                    levels = [{'unknown': 0, 'aware': 1, 'basic': 2, 
                              'intermediate': 3, 'advanced': 4, 'expert': 5,
                              'unknown_unknown': 0}[l['level']] 
                             for l in k.learning_curve]
                    if len(levels) >= 2:
                        total_growth += (levels[-1] - levels[0]) / len(levels)
            
            avg_growth = total_growth / len(self.knowledge)
            self.profile.learning_speed = min(1.0, max(0.1, avg_growth * 2))
    
    def get_cognitive_profile(self) -> Dict[str, Any]:
        """获取完整认知档案"""
        profile_dict = asdict(self.profile)
        
        # 补充实时数据
        knowledge_summary = self.get_knowledge_summary()
        awareness = self.check_self_awareness()
        
        profile_dict.update({
            'knowledge_summary': knowledge_summary,
            'self_awareness': awareness,
            'total_knowledge_items': len(self.knowledge),
            'total_strategies': len(self.strategies),
            'total_logs': len(self.logs),
            'known_unknowns': list(self.known_unknowns),
            'cognitive_health_score': self._calculate_cognitive_health()
        })
        
        return profile_dict
    
    def _calculate_cognitive_health(self) -> float:
        """计算认知健康指数"""
        score = 0.5  # 基础分
        
        # 知识多样性加分
        categories = set(k.category for k in self.knowledge.values())
        score += min(0.15, len(categories) * 0.02)
        
        # 元觉知加分
        awareness = self.check_self_awareness()
        score += awareness['awareness_score'] * 0.2
        
        # 策略丰富度加分
        score += min(0.1, len(self.strategies) * 0.02)
        
        return min(1.0, max(0.0, score))
    
    # ============================================================
    # 元认知训练
    # ============================================================
    
    def practice_awareness(self) -> str:
        """进行一次元觉知练习
        
        就像正念冥想一样，观察自己的思维过程。
        """
        # 记录当前状态
        state_before = self.current_state.awareness_level
        
        # 模拟练习效果
        levels = list(MetaAwarenessLevel)
        current_idx = levels.index(self.current_state.awareness_level)
        
        # 练习后短暂提升觉知水平
        if current_idx < len(levels) - 1:
            new_level = levels[current_idx + 1]
            self.update_cognitive_state(awareness_level=new_level)
            
            self._log_meta(
                "insight",
                f"元觉知练习：从 {state_before.value} 提升到 {new_level.value}",
                importance=0.5,
                tags=["practice", "awareness"]
            )
            
            return (
                f"觉知练习完成。\n"
                f"此刻，你观察到了什么？\n"
                f"• 你的注意力在哪里？\n"
                f"• 你的情绪状态如何？\n"
                f"• 那个正在观察的'你'，又是谁？\n\n"
                f"觉知水平：{state_before.value} → {new_level.value}"
            )
        
        return "你已经处于最高觉知水平。保持这份觉察。"


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("元认知引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建元认知引擎
        meta = MetacognitionEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n🧠 初始认知状态:")
        state = meta.get_current_state()
        print(f"  觉知水平: {state.awareness_level.value}")
        print(f"  认知负荷: {state.cognitive_load.value}")
        print(f"  专注力: {state.focus_level:.2f}")
        print(f"  精神疲劳: {state.mental_fatigue:.2f}")
        
        print("\n📚 添加一些知识...")
        # 添加不同领域的知识
        k1 = meta.add_knowledge("Python编程", "programming", 
                               KnowledgeLevel.INTERMEDIATE, confidence=0.7)
        k2 = meta.add_knowledge("认知科学", "cognitive_science", 
                               KnowledgeLevel.BASIC, confidence=0.6)
        k3 = meta.add_knowledge("机器学习", "ai", 
                               KnowledgeLevel.AWARE, confidence=0.4)
        
        # 发现未知领域
        meta.discover_unknown("量子计算")
        meta.discover_unknown("神经科学")
        meta.discover_unknown("混沌理论")
        
        print("\n📊 知识概览:")
        summary = meta.get_knowledge_summary()
        print(f"  总知识条目: {summary['total_knowledge_items']}")
        print(f"  知识类别数: {summary['knowledge_breadth']}")
        print(f"  已知的未知: {summary['known_unknowns_count']} 个领域")
        print(f"  邓宁-克鲁格风险: {summary['dunning_kruger_risk']:.2f}")
        print("\n  各等级分布:")
        for level, count in summary['by_level'].items():
            bar = "█" * int(count * 5)
            print(f"    {level:15s}: {count:2d} {bar}")
        
        print("\n🎯 选择认知策略...")
        strategy = meta.select_strategy("learning")
        if strategy:
            print(f"  推荐策略: {strategy.name}")
            print(f"  描述: {strategy.description}")
            print(f"  预计有效度: {strategy.effectiveness:.2f}")
            print(f"  适用条件: {', '.join(strategy.conditions)}")
            
            # 报告策略结果
            print(f"\n  使用策略后，报告结果...")
            meta.report_strategy_result(strategy.id, success=True)
            print(f"  成功率: {strategy.success_rate:.2f}")
            print(f"  更新后有效度: {strategy.effectiveness:.2f}")
        
        print("\n💡 认知优化建议:")
        suggestions = meta.suggest_optimization()
        if suggestions:
            for i, s in enumerate(suggestions, 1):
                print(f"  {i}. {s}")
        else:
            print("  当前状态良好，无需特别调整。")
        
        print("\n👁️  自我觉知水平:")
        awareness = meta.check_self_awareness()
        print(f"  觉知分数: {awareness['awareness_score']:.2f}")
        print(f"  觉知等级: {awareness['awareness_level']}")
        print(f"  描述: {awareness['description']}")
        
        print("\n🧘 元觉知练习...")
        result = meta.practice_awareness()
        print(result)
        
        # 更新知识水平
        print("\n📈 学习进步，更新知识水平...")
        meta.update_knowledge_level(k1.id, KnowledgeLevel.ADVANCED, confidence=0.8)
        meta.update_knowledge_level(k2.id, KnowledgeLevel.INTERMEDIATE, confidence=0.65)
        
        print("\n🔄 再次检查知识概览:")
        summary2 = meta.get_knowledge_summary()
        print(f"  平均深度: {summary['average_depth']:.2f}")
        
        print("\n📋 元认知日志 (最近5条):")
        recent_logs = meta.logs[-5:] if len(meta.logs) >= 5 else meta.logs
        for log in reversed(recent_logs):
            print(f"  [{log.log_type}] {log.content[:50]}...")
        
        # 认知档案
        print("\n📊 认知档案摘要:")
        profile = meta.get_cognitive_profile()
        print(f"  认知健康指数: {profile['cognitive_health_score']:.2f}")
        print(f"  学习速度: {profile['learning_speed']:.2f}")
        print(f"  元觉知能力: {profile['meta_awareness_ability']:.2f}")
        print(f"  自我调节能力: {profile['self_regulation_ability']:.2f}")
        
        # 保存
        meta.save()
        
        print("\n" + "=" * 70)
        print("✅ 元认知引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
