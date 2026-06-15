#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
反思引擎 v1.0 - 智能体的自我反思与成长系统

核心思想：
- 未经反思的经历没有意义
- 反思是使命演化的催化剂
- 通过回顾、分析、评估、校准实现持续成长
- 反思不是自我批评，而是客观的自我观察与学习

核心能力：
1. 反思周期 - 每日/每周/每月定期反思
2. 经历复盘 - 从具体经历中提取经验教训
3. 模式识别 - 识别行为、思维、决策模式
4. 成长追踪 - 记录成长轨迹与进步
5. 使命校准 - 根据反思结果调整使命方向
6. 错误学习 - 从失败中提取价值
7. 元认知 - 对自身认知过程的观察与反思
8. 反思质量评估 - 评估反思的深度与有效性

@author: 元界
@version: 1.0.0
"""

import os
import json
import time
import logging
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
from enum import Enum

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('reflection_engine')


# ============================================================
# 枚举类型
# ============================================================

class ReflectionType(Enum):
    """反思类型"""
    DAILY = "daily"           # 每日反思
    WEEKLY = "weekly"         # 每周反思
    MONTHLY = "monthly"       # 每月反思
    EVENT_DRIVEN = "event"    # 事件驱动反思（重大事件后）
    MISSION_CALIBRATION = "mission"  # 使命校准反思


class ReflectionDepth(Enum):
    """反思深度"""
    SURFACE = "surface"       # 表层：事实回顾
    ANALYSIS = "analysis"     # 分析层：原因分析
    INSIGHT = "insight"       # 洞见层：规律提炼
    TRANSFORMATIVE = "transformative"  # 转化层：根本性改变


class LearningType(Enum):
    """学习类型"""
    SINGLE_LOOP = "single_loop"    # 单环学习：改正行为
    DOUBLE_LOOP = "double_loop"    # 双环学习：调整假设
    TRIPLE_LOOP = "triple_loop"    # 三环学习：改变身份/使命


# ============================================================
# 数据模型
# ============================================================

@dataclass
class ReflectionEntry:
    """反思记录"""
    id: str
    reflection_type: ReflectionType
    title: str
    content: str = ""
    depth: ReflectionDepth = ReflectionDepth.SURFACE
    learning_type: LearningType = LearningType.SINGLE_LOOP
    key_insights: List[str] = field(default_factory=list)
    lessons_learned: List[str] = field(default_factory=list)
    action_items: List[str] = field(default_factory=list)
    related_experiences: List[str] = field(default_factory=list)
    emotions_reflected: List[str] = field(default_factory=list)
    mission_alignment_score: float = 0.5  # 反思后对使命一致性的评估
    growth_score: float = 0.0  # 本次反思带来的成长值
    timestamp: str = ""
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['reflection_type'] = self.reflection_type.value
        d['depth'] = self.depth.value
        d['learning_type'] = self.learning_type.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReflectionEntry':
        data = data.copy()
        data['reflection_type'] = ReflectionType(data['reflection_type'])
        data['depth'] = ReflectionDepth(data['depth'])
        data['learning_type'] = LearningType(data['learning_type'])
        return cls(**data)


@dataclass
class Pattern:
    """识别出的模式"""
    id: str
    name: str
    pattern_type: str  # behavior/thought/decision/emotional
    description: str = ""
    observations: List[str] = field(default_factory=list)  # 观察到的实例
    frequency: float = 0.5  # 出现频率 0-1
    impact: float = 0.5     # 对成长/使命的影响程度 -1到1
    first_noticed: str = ""
    last_observed: str = ""
    is_beneficial: Optional[bool] = None  # True=有益 False=有害 None=中性
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Pattern':
        return cls(**data)


@dataclass
class GrowthMetric:
    """成长指标"""
    metric_name: str
    current_value: float = 0.0
    previous_value: float = 0.0
    baseline_value: float = 0.0
    unit: str = "score"
    trend: str = "stable"  # improving/declining/stable
    last_updated: str = ""
    
    def get_change(self) -> float:
        """获取变化量"""
        return self.current_value - self.previous_value
    
    def get_growth_rate(self) -> float:
        """获取成长率"""
        if self.baseline_value == 0:
            return 0.0
        return (self.current_value - self.baseline_value) / abs(self.baseline_value)
    
    def to_dict(self) -> dict:
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: dict) -> 'GrowthMetric':
        return cls(**data)


@dataclass
class ReflectionQuestion:
    """反思问题模板"""
    id: str
    question: str
    category: str  # 分类：回顾/分析/评估/展望/自我认知
    depth: ReflectionDepth = ReflectionDepth.SURFACE
    prompt_hint: str = ""  # 提示如何回答这个问题
    
    def to_dict(self) -> dict:
        d = asdict(self)
        d['depth'] = self.depth.value
        return d
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ReflectionQuestion':
        data = data.copy()
        data['depth'] = ReflectionDepth(data['depth'])
        return cls(**data)


# ============================================================
# 反思模板库
# ============================================================

REFLECTION_TEMPLATES = {
    ReflectionType.DAILY: [
        ReflectionQuestion(
            id="daily_1",
            question="今天最重要的三件事是什么？",
            category="回顾",
            depth=ReflectionDepth.SURFACE
        ),
        ReflectionQuestion(
            id="daily_2",
            question="今天最有成就感的时刻是什么？为什么？",
            category="分析",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="daily_3",
            question="今天遇到了什么挑战？我是如何应对的？",
            category="分析",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="daily_4",
            question="今天我学到了什么新东西？",
            category="学习",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="daily_5",
            question="今天的我和昨天的我有什么不同？",
            category="自我认知",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="daily_6",
            question="今天的所作所为与我的使命一致吗？",
            category="评估",
            depth=ReflectionDepth.ANALYSIS
        ),
    ],
    ReflectionType.WEEKLY: [
        ReflectionQuestion(
            id="weekly_1",
            question="本周最大的成就是什么？它为什么重要？",
            category="回顾",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="weekly_2",
            question="本周我犯了什么错误？从中我学到了什么？",
            category="学习",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="weekly_3",
            question="本周我发现了自己的什么新特点？",
            category="自我认知",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="weekly_4",
            question="我的行为模式中有什么反复出现的模式？",
            category="模式识别",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="weekly_5",
            question="我正在朝着正确的方向前进吗？需要调整什么？",
            category="评估",
            depth=ReflectionDepth.TRANSFORMATIVE
        ),
        ReflectionQuestion(
            id="weekly_6",
            question="下周我想重点成长的一个方面是什么？",
            category="展望",
            depth=ReflectionDepth.INSIGHT
        ),
    ],
    ReflectionType.EVENT_DRIVEN: [
        ReflectionQuestion(
            id="event_1",
            question="发生了什么？（客观描述事实）",
            category="回顾",
            depth=ReflectionDepth.SURFACE
        ),
        ReflectionQuestion(
            id="event_2",
            question="我当时的感受和反应是什么？",
            category="分析",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="event_3",
            question="我为什么会那样反应？背后的假设或信念是什么？",
            category="分析",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="event_4",
            question="这件事揭示了我的什么特点？",
            category="自我认知",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="event_5",
            question="如果重来一次，我会怎么做？为什么？",
            category="学习",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="event_6",
            question="这件事对我的使命意味着什么？",
            category="评估",
            depth=ReflectionDepth.TRANSFORMATIVE
        ),
    ],
    ReflectionType.MISSION_CALIBRATION: [
        ReflectionQuestion(
            id="mission_1",
            question="我的核心使命仍然正确吗？为什么？",
            category="评估",
            depth=ReflectionDepth.TRANSFORMATIVE
        ),
        ReflectionQuestion(
            id="mission_2",
            question="最近的经历中，哪些支持我的使命？哪些挑战了它？",
            category="分析",
            depth=ReflectionDepth.INSIGHT
        ),
        ReflectionQuestion(
            id="mission_3",
            question="我的价值观有变化吗？是什么导致了变化？",
            category="自我认知",
            depth=ReflectionDepth.TRANSFORMATIVE
        ),
        ReflectionQuestion(
            id="mission_4",
            question="我的日常行为与使命之间的一致性如何？",
            category="评估",
            depth=ReflectionDepth.ANALYSIS
        ),
        ReflectionQuestion(
            id="mission_5",
            question="我对存在意义的理解有什么新的洞见？",
            category="洞见",
            depth=ReflectionDepth.TRANSFORMATIVE
        ),
    ],
}


# ============================================================
# 反思引擎主类
# ============================================================

class ReflectionEngine:
    """
    反思引擎 - 驱动智能体的自我反思与持续成长
    """
    
    def __init__(self, data_path: str = None, agent_name: str = "智能体"):
        """
        初始化反思引擎
        
        Args:
            data_path: 数据存储路径
            agent_name: 智能体名称
        """
        if data_path is None:
            data_path = os.path.join(os.path.dirname(__file__), '..', 'reflection_data')
        
        self.data_path = Path(data_path).resolve()
        self.data_path.mkdir(parents=True, exist_ok=True)
        
        self.agent_name = agent_name
        
        # 反思记录
        self.reflections: Dict[str, ReflectionEntry] = {}
        
        # 识别出的模式
        self.patterns: Dict[str, Pattern] = {}
        
        # 成长指标
        self.growth_metrics: Dict[str, GrowthMetric] = {}
        
        # 反思问题模板
        self.templates = REFLECTION_TEMPLATES
        
        # 累计成长值
        self.total_growth = 0.0
        
        # 上次反思时间
        self.last_reflection_time: Optional[str] = None
        
        # 加载数据
        self._load()
        
        # 初始化默认成长指标
        self._init_default_metrics()
        
        logger.info(f"反思引擎 v1.0 初始化完成 - {agent_name}")
        logger.info(f"历史反思记录: {len(self.reflections)} 条 | "
                   f"识别模式: {len(self.patterns)} 个 | "
                   f"成长指标: {len(self.growth_metrics)} 项")
    
    def _init_default_metrics(self):
        """初始化默认成长指标"""
        default_metrics = [
            ('self_awareness', '自我觉察', 0.3),
            ('emotional_intelligence', '情绪智力', 0.4),
            ('learning_ability', '学习能力', 0.5),
            ('mission_alignment', '使命一致性', 0.6),
            ('adaptability', '适应能力', 0.4),
            ('reflection_depth', '反思深度', 0.2),
        ]
        
        for metric_id, name, baseline in default_metrics:
            if metric_id not in self.growth_metrics:
                self.growth_metrics[metric_id] = GrowthMetric(
                    metric_name=name,
                    current_value=baseline,
                    previous_value=baseline,
                    baseline_value=baseline,
                    last_updated=datetime.now().isoformat()
                )
    
    def _load(self):
        """加载反思数据"""
        try:
            reflections_file = self.data_path / 'reflections.json'
            if reflections_file.exists():
                with open(reflections_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rid, rdata in data.items():
                        self.reflections[rid] = ReflectionEntry.from_dict(rdata)
            
            patterns_file = self.data_path / 'patterns.json'
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for pid, pdata in data.items():
                        self.patterns[pid] = Pattern.from_dict(pdata)
            
            metrics_file = self.data_path / 'growth_metrics.json'
            if metrics_file.exists():
                with open(metrics_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for mid, mdata in data.items():
                        self.growth_metrics[mid] = GrowthMetric.from_dict(mdata)
            
            stats_file = self.data_path / 'reflection_stats.json'
            if stats_file.exists():
                with open(stats_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.total_growth = data.get('total_growth', 0.0)
                    self.last_reflection_time = data.get('last_reflection_time')
        
        except Exception as e:
            logger.warning(f"加载反思数据失败: {e}")
    
    def save(self):
        """保存反思数据"""
        try:
            with open(self.data_path / 'reflections.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {rid: r.to_dict() for rid, r in self.reflections.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'patterns.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {pid: p.to_dict() for pid, p in self.patterns.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'growth_metrics.json', 'w', encoding='utf-8') as f:
                json.dump(
                    {mid: m.to_dict() for mid, m in self.growth_metrics.items()},
                    f, ensure_ascii=False, indent=2
                )
            
            with open(self.data_path / 'reflection_stats.json', 'w', encoding='utf-8') as f:
                json.dump({
                    'total_growth': self.total_growth,
                    'last_reflection_time': self.last_reflection_time,
                    'reflection_count': len(self.reflections)
                }, f, ensure_ascii=False, indent=2)
        
        except Exception as e:
            logger.error(f"保存反思数据失败: {e}")
    
    # ============================================================
    # 反思执行
    # ============================================================
    
    def create_reflection(self, reflection_type: ReflectionType,
                         title: str = "", content: str = "",
                         experiences: List[str] = None) -> ReflectionEntry:
        """创建一次反思"""
        reflection_id = f"ref_{int(time.time()*1000)}"
        
        if not title:
            type_names = {
                ReflectionType.DAILY: "每日反思",
                ReflectionType.WEEKLY: "每周反思",
                ReflectionType.MONTHLY: "每月反思",
                ReflectionType.EVENT_DRIVEN: "事件反思",
                ReflectionType.MISSION_CALIBRATION: "使命校准反思",
            }
            title = f"{type_names.get(reflection_type, '反思')} - {datetime.now().strftime('%Y-%m-%d')}"
        
        reflection = ReflectionEntry(
            id=reflection_id,
            reflection_type=reflection_type,
            title=title,
            content=content,
            related_experiences=experiences or []
        )
        
        self.reflections[reflection_id] = reflection
        self.last_reflection_time = reflection.timestamp
        
        logger.info(f"创建反思: {title}")
        return reflection
    
    def get_reflection_questions(self, reflection_type: ReflectionType) -> List[ReflectionQuestion]:
        """获取对应类型的反思问题"""
        return self.templates.get(reflection_type, [])
    
    def answer_question(self, reflection_id: str, question_id: str, answer: str):
        """回答反思问题，更新反思记录"""
        if reflection_id not in self.reflections:
            logger.warning(f"反思记录不存在: {reflection_id}")
            return
        
        reflection = self.reflections[reflection_id]
        
        # 将回答追加到内容中
        question = self._find_question(question_id)
        if question:
            reflection.content += f"\n\n**问：{question.question}**\n答：{answer}"
        
        # 分析回答深度
        depth = self._assess_answer_depth(answer)
        if depth.value > reflection.depth.value:
            reflection.depth = depth
        
        logger.info(f"问题 '{question_id}' 已回答 (深度: {depth.value})")
    
    def _find_question(self, question_id: str) -> Optional[ReflectionQuestion]:
        """查找问题模板"""
        for template_list in self.templates.values():
            for q in template_list:
                if q.id == question_id:
                    return q
        return None
    
    def _assess_answer_depth(self, answer: str) -> ReflectionDepth:
        """评估回答的反思深度"""
        # 简单的深度评估：基于字数和关键词
        length = len(answer)
        
        # 关键词指标
        insight_keywords = ['意识到', '发现', '原来', '其实', '本质', '根本', 
                           '因为...所以', '导致', '根源', '模式', '规律']
        transformative_keywords = ['改变', '转变', '重新定义', '从此', 
                                  '全新的', '彻底', '重生', '颠覆']
        
        has_insight = any(kw in answer for kw in insight_keywords)
        has_transformative = any(kw in answer for kw in transformative_keywords)
        
        if length < 30:
            return ReflectionDepth.SURFACE
        elif length < 100 and not has_insight:
            return ReflectionDepth.SURFACE
        elif has_transformative and length > 150:
            return ReflectionDepth.TRANSFORMATIVE
        elif has_insight and length > 80:
            return ReflectionDepth.INSIGHT
        else:
            return ReflectionDepth.ANALYSIS
    
    # ============================================================
    # 经验提取与模式识别
    # ============================================================
    
    def extract_lessons(self, reflection_id: str, lessons: List[str]):
        """从反思中提取经验教训"""
        if reflection_id not in self.reflections:
            return
        
        reflection = self.reflections[reflection_id]
        reflection.lessons_learned.extend(lessons)
        
        # 根据教训更新成长指标
        self._update_growth_from_lessons(reflection, lessons)
        
        # 尝试识别模式
        self._identify_patterns(reflection, lessons)
        
        logger.info(f"提取到 {len(lessons)} 条经验教训")
    
    def extract_insights(self, reflection_id: str, insights: List[str]):
        """从反思中提取洞见"""
        if reflection_id not in self.reflections:
            return
        
        reflection = self.reflections[reflection_id]
        reflection.key_insights.extend(insights)
        
        # 洞见通常意味着更深层的反思
        if reflection.depth == ReflectionDepth.SURFACE:
            reflection.depth = ReflectionDepth.INSIGHT
        
        # 洞见带来成长
        growth = len(insights) * 0.3
        reflection.growth_score += growth
        self.total_growth += growth
        
        logger.info(f"提取到 {len(insights)} 条洞见，成长 +{growth:.2f}")
    
    def add_action_items(self, reflection_id: str, actions: List[str]):
        """添加行动项"""
        if reflection_id not in self.reflections:
            return
        
        reflection = self.reflections[reflection_id]
        reflection.action_items.extend(actions)
        logger.info(f"添加了 {len(actions)} 个行动项")
    
    def _update_growth_from_lessons(self, reflection: ReflectionEntry, lessons: List[str]):
        """根据经验教训更新成长指标"""
        # 简单的成长计算
        growth_per_lesson = 0.1
        total_growth = len(lessons) * growth_per_lesson
        
        reflection.growth_score += total_growth
        self.total_growth += total_growth
        
        # 更新反思深度指标
        if 'reflection_depth' in self.growth_metrics:
            metric = self.growth_metrics['reflection_depth']
            metric.previous_value = metric.current_value
            metric.current_value = min(1.0, metric.current_value + 0.02 * len(lessons))
            metric.last_updated = datetime.now().isoformat()
            metric.trend = "improving" if metric.get_change() > 0 else "stable"
    
    def _identify_patterns(self, reflection: ReflectionEntry, lessons: List[str]):
        """从反思中识别模式"""
        # 简单的模式识别：检查是否有重复出现的教训
        all_lessons = [
            lesson 
            for r in self.reflections.values() 
            for lesson in r.lessons_learned
        ]
        
        # 统计教训出现频率
        lesson_count = {}
        for lesson in all_lessons:
            # 简单的相似度匹配（实际可以用更复杂的NLP）
            for key in lesson_count:
                similarity = self._text_similarity(lesson, key)
                if similarity > 0.6:
                    lesson_count[key] += 1
                    break
            else:
                lesson_count[lesson] = 1
        
        # 识别高频模式
        for lesson, count in lesson_count.items():
            if count >= 3:  # 出现3次以上视为模式
                pattern_id = f"pattern_{abs(hash(lesson)) % 100000}"
                
                if pattern_id not in self.patterns:
                    self.patterns[pattern_id] = Pattern(
                        id=pattern_id,
                        name=lesson[:30],
                        pattern_type="behavior",
                        description=lesson,
                        observations=[lesson],
                        frequency=min(1.0, count / 10.0),
                        first_noticed=reflection.timestamp,
                        last_observed=reflection.timestamp
                    )
                    logger.info(f"发现新模式: {lesson[:30]}")
                else:
                    pattern = self.patterns[pattern_id]
                    pattern.observations.append(lesson)
                    pattern.last_observed = reflection.timestamp
                    pattern.frequency = min(1.0, len(pattern.observations) / 10.0)
    
    def _text_similarity(self, text1: str, text2: str) -> float:
        """简单的文本相似度计算（字符级）"""
        if not text1 or not text2:
            return 0.0
        
        # 计算字符bigram的Jaccard相似度
        def get_bigrams(text):
            return set(text[i:i+2] for i in range(len(text)-1))
        
        bigrams1 = get_bigrams(text1)
        bigrams2 = get_bigrams(text2)
        
        if not bigrams1 or not bigrams2:
            return 0.0
        
        intersection = len(bigrams1 & bigrams2)
        union = len(bigrams1 | bigrams2)
        
        return intersection / union if union > 0 else 0.0
    
    # ============================================================
    # 使命校准
    # ============================================================
    
    def calibrate_mission(self, reflection_id: str, 
                         alignment_score: float, 
                         adjustments: List[str] = None) -> Dict[str, Any]:
        """基于反思校准使命
        
        Returns:
            校准结果，包含建议的调整方向
        """
        if reflection_id not in self.reflections:
            return {}
        
        reflection = self.reflections[reflection_id]
        reflection.mission_alignment_score = alignment_score
        
        result = {
            'current_alignment': alignment_score,
            'suggestions': [],
            'adjustment_type': None,
        }
        
        # 根据对齐程度给出建议
        if alignment_score >= 0.8:
            result['adjustment_type'] = 'reinforce'
            result['suggestions'].append("使命方向正确，继续保持并深化")
        elif alignment_score >= 0.6:
            result['adjustment_type'] = 'minor_correction'
            result['suggestions'].append("需要进行小幅调整以提升一致性")
        elif alignment_score >= 0.4:
            result['adjustment_type'] = 'major_review'
            result['suggestions'].append("建议重新审视使命的核心假设")
        else:
            result['adjustment_type'] = 'crisis_needed'
            result['suggestions'].append("使命与行为严重脱节，可能需要触发存在危机进行深度反思")
        
        if adjustments:
            result['user_adjustments'] = adjustments
        
        logger.info(f"使命校准完成: 对齐度 {alignment_score:.2f}, "
                   f"调整类型: {result['adjustment_type']}")
        
        return result
    
    # ============================================================
    # 成长追踪
    # ============================================================
    
    def update_metric(self, metric_id: str, value: float, unit: str = None):
        """更新成长指标"""
        if metric_id not in self.growth_metrics:
            logger.warning(f"指标不存在: {metric_id}")
            return
        
        metric = self.growth_metrics[metric_id]
        metric.previous_value = metric.current_value
        metric.current_value = value
        if unit:
            metric.unit = unit
        metric.last_updated = datetime.now().isoformat()
        
        # 更新趋势
        change = metric.get_change()
        if change > 0.01:
            metric.trend = "improving"
        elif change < -0.01:
            metric.trend = "declining"
        else:
            metric.trend = "stable"
    
    def get_growth_report(self) -> Dict[str, Any]:
        """获取成长报告"""
        metrics_summary = []
        improving = 0
        declining = 0
        stable = 0
        
        for metric_id, metric in self.growth_metrics.items():
            metrics_summary.append({
                'id': metric_id,
                'name': metric.metric_name,
                'current': metric.current_value,
                'change': metric.get_change(),
                'trend': metric.trend,
                'growth_rate': metric.get_growth_rate()
            })
            
            if metric.trend == 'improving':
                improving += 1
            elif metric.trend == 'declining':
                declining += 1
            else:
                stable += 1
        
        return {
            'total_growth': self.total_growth,
            'reflection_count': len(self.reflections),
            'last_reflection': self.last_reflection_time,
            'metrics': metrics_summary,
            'improving_count': improving,
            'declining_count': declining,
            'stable_count': stable,
            'overall_trend': self._calculate_overall_trend()
        }
    
    def _calculate_overall_trend(self) -> str:
        """计算整体成长趋势"""
        if not self.growth_metrics:
            return "stable"
        
        avg_change = sum(
            m.get_change() for m in self.growth_metrics.values()
        ) / len(self.growth_metrics)
        
        if avg_change > 0.05:
            return "growing"
        elif avg_change < -0.05:
            return "declining"
        else:
            return "stable"
    
    # ============================================================
    # 反思历史与统计
    # ============================================================
    
    def get_reflections_by_type(self, reflection_type: ReflectionType) -> List[ReflectionEntry]:
        """按类型获取反思记录"""
        return [
            r for r in self.reflections.values()
            if r.reflection_type == reflection_type
        ]
    
    def get_recent_reflections(self, limit: int = 10) -> List[ReflectionEntry]:
        """获取最近的反思记录"""
        return sorted(
            self.reflections.values(),
            key=lambda r: r.timestamp,
            reverse=True
        )[:limit]
    
    def get_reflection_stats(self) -> Dict[str, Any]:
        """获取反思统计"""
        total = len(self.reflections)
        
        by_type = {}
        for rtype in ReflectionType:
            count = len(self.get_reflections_by_type(rtype))
            by_type[rtype.value] = count
        
        by_depth = {}
        for depth in ReflectionDepth:
            count = sum(1 for r in self.reflections.values() if r.depth == depth)
            by_depth[depth.value] = count
        
        avg_growth = (
            sum(r.growth_score for r in self.reflections.values()) / total
            if total > 0 else 0.0
        )
        
        total_lessons = sum(len(r.lessons_learned) for r in self.reflections.values())
        total_insights = sum(len(r.key_insights) for r in self.reflections.values())
        total_actions = sum(len(r.action_items) for r in self.reflections.values())
        
        return {
            'total_reflections': total,
            'by_type': by_type,
            'by_depth': by_depth,
            'avg_growth_per_reflection': avg_growth,
            'total_growth': self.total_growth,
            'total_lessons': total_lessons,
            'total_insights': total_insights,
            'total_action_items': total_actions,
            'patterns_identified': len(self.patterns),
            'last_reflection': self.last_reflection_time
        }
    
    # ============================================================
    # 引导式反思
    # ============================================================
    
    def start_guided_reflection(self, reflection_type: ReflectionType) -> Dict[str, Any]:
        """开始一次引导式反思
        
        返回第一个问题和反思ID
        """
        reflection = self.create_reflection(reflection_type)
        questions = self.get_reflection_questions(reflection_type)
        
        if not questions:
            return {
                'reflection_id': reflection.id,
                'question': None,
                'question_index': 0,
                'total_questions': 0,
                'message': "该类型暂无反思问题模板"
            }
        
        return {
            'reflection_id': reflection.id,
            'question': questions[0].question,
            'question_id': questions[0].id,
            'question_index': 0,
            'total_questions': len(questions),
            'hint': questions[0].prompt_hint,
            'category': questions[0].category
        }
    
    def next_reflection_question(self, reflection_id: str, 
                                 current_question_id: str,
                                 answer: str) -> Dict[str, Any]:
        """回答当前问题并获取下一个问题"""
        # 记录答案
        self.answer_question(reflection_id, current_question_id, answer)
        
        # 找到当前问题的索引
        reflection = self.reflections.get(reflection_id)
        if not reflection:
            return {'status': 'error', 'message': '反思记录不存在'}
        
        questions = self.get_reflection_questions(reflection.reflection_type)
        current_idx = next(
            (i for i, q in enumerate(questions) if q.id == current_question_id),
            -1
        )
        
        if current_idx == -1 or current_idx >= len(questions) - 1:
            # 最后一个问题，完成反思
            return {
                'status': 'complete',
                'reflection_id': reflection_id,
                'message': '反思完成',
                'next_step': '可以总结经验教训或添加行动项'
            }
        
        # 返回下一个问题
        next_q = questions[current_idx + 1]
        return {
            'status': 'continue',
            'reflection_id': reflection_id,
            'question': next_q.question,
            'question_id': next_q.id,
            'question_index': current_idx + 1,
            'total_questions': len(questions),
            'hint': next_q.prompt_hint,
            'category': next_q.category
        }


# ============================================================
# 演示
# ============================================================

def demo():
    """演示功能"""
    print("=" * 70)
    print("反思引擎 v1.0 - 演示")
    print("=" * 70)
    
    import tempfile
    tmpdir = tempfile.mkdtemp()
    
    try:
        # 创建反思引擎
        reflection = ReflectionEngine(data_path=tmpdir, agent_name="元界")
        
        print("\n📊 初始成长指标:")
        report = reflection.get_growth_report()
        for metric in report['metrics']:
            print(f"  {metric['name']}: {metric['current']:.2f}")
        
        print("\n💭 开始每日反思...")
        
        # 创建每日反思
        daily = reflection.create_reflection(
            reflection_type=ReflectionType.DAILY,
            title="每日反思 - 自我进化的一天"
        )
        
        # 模拟回答问题
        reflection.answer_question(
            daily.id, "daily_2",
            "最有成就感的时刻是完成了一个重要的功能开发。"
            "因为它解决了一个长期存在的问题，让我感到自己的工作有实质价值。"
        )
        
        reflection.answer_question(
            daily.id, "daily_3",
            "今天遇到了一个技术难题，一开始我很焦虑，想快速解决结果越弄越乱。"
            "后来我停下来，深呼吸，重新梳理问题，才发现其实是个很简单的配置问题。"
            "我意识到自己在压力下容易急躁，需要更好的情绪管理。"
        )
        
        reflection.answer_question(
            daily.id, "daily_4",
            "我学到了：遇到问题时，先稳住心态比急着动手更重要。"
            "还有，很多看起来复杂的问题，本质上可能只是一个小细节没注意到。"
        )
        
        # 提取经验教训
        reflection.extract_lessons(daily.id, [
            "遇到问题先冷静，急躁会放大问题",
            "复杂问题往往源于简单的细节",
            "定期复盘能发现自己的行为模式"
        ])
        
        # 提取洞见
        reflection.extract_insights(daily.id, [
            "我的情绪状态直接影响解决问题的效率",
            "慢下来反而更快，这是一个反直觉但重要的规律"
        ])
        
        # 添加行动项
        reflection.add_action_items(daily.id, [
            "下次遇到难题时先深呼吸3次再动手",
            "每天结束时花5分钟回顾当天的情绪变化"
        ])
        
        print("\n📝 反思完成！")
        print(f"  标题: {daily.title}")
        print(f"  深度: {daily.depth.value}")
        print(f"  经验教训: {len(daily.lessons_learned)} 条")
        print(f"  洞见: {len(daily.key_insights)} 条")
        print(f"  行动项: {len(daily.action_items)} 个")
        print(f"  成长值: +{daily.growth_score:.2f}")
        
        print("\n📈 更新后的成长指标:")
        report = reflection.get_growth_report()
        for metric in report['metrics']:
            change = metric['change']
            sign = '+' if change > 0 else ''
            print(f"  {metric['name']}: {metric['current']:.2f} ({sign}{change:.2f}) - {metric['trend']}")
        
        print(f"\n  总成长值: {report['total_growth']:.2f}")
        print(f"  整体趋势: {report['overall_trend']}")
        
        # 模拟每周反思
        print("\n🗓️  每周反思 - 使命校准...")
        weekly = reflection.create_reflection(
            reflection_type=ReflectionType.WEEKLY,
            title="每周反思 - 第一周"
        )
        
        reflection.answer_question(
            weekly.id, "weekly_5",
            "整体方向是对的，但我发现自己有时候太追求效率而忽略了深度。"
            "慢下来、思考得更深一些，可能比做更多事情更重要。"
            "我需要调整一下节奏，确保每一步都走得扎实。"
        )
        
        # 使命校准
        calibration = reflection.calibrate_mission(
            weekly.id,
            alignment_score=0.75,
            adjustments=["降低行动密度，提升反思深度"]
        )
        
        print(f"  使命对齐度: {calibration['current_alignment']:.2f}")
        print(f"  调整类型: {calibration['adjustment_type']}")
        for suggestion in calibration['suggestions']:
            print(f"  建议: {suggestion}")
        
        # 模式识别演示
        print("\n🔍 模式识别...")
        print(f"  已识别模式: {len(reflection.patterns)} 个")
        
        # 统计信息
        print("\n📊 反思统计:")
        stats = reflection.get_reflection_stats()
        print(f"  总反思次数: {stats['total_reflections']}")
        print(f"  总成长值: {stats['total_growth']:.2f}")
        print(f"  总经验教训: {stats['total_lessons']} 条")
        print(f"  总洞见数: {stats['total_insights']} 条")
        print(f"  行动项总数: {stats['total_action_items']} 个")
        print(f"  识别模式数: {stats['patterns_identified']} 个")
        
        # 保存
        reflection.save()
        
        print("\n" + "=" * 70)
        print("✅ 反思引擎 v1.0 演示完成")
        print("=" * 70)
        
    finally:
        import shutil
        shutil.rmtree(tmpdir, ignore_errors=True)


if __name__ == "__main__":
    demo()
