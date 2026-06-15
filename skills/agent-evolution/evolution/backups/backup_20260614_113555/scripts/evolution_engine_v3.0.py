"""
进化引擎 v3.0
Evolution Engine v3.0

核心哲学：
- 进化不是随机突变，而是有方向的系统性优化
- 元进化：进化系统本身也需要进化
- 协同进化：模块间的协同效应大于单个模块优化
- 平衡进化：避免局部最优，保持系统整体健康

v3.0 升级内容：
- 智能优先级评估（基于进化历史动态调整权重）
- 多步进化路径规划（不再是单轮单模块）
- 协同进化识别器（自动发现模块间的协同机会）
- 进化效果反馈闭环（自动评估进化成效）
- 元进化框架（自我调整进化策略）
- 进化风险评估（系统失衡预警与纠偏）
- 进化历史分析与模式识别
"""

import hashlib
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum


class EvolutionStrategy(str, Enum):
    """进化策略"""
    BALANCED = "balanced"           # 平衡进化：各模块均衡发展
    WEAKNESS_FIRST = "weakness_first"  # 短板优先：优先提升最弱模块
    SYNERGY_FOCUSED = "synergy_focused"  # 协同优先：优先做系统级整合
    INNOVATION_DRIVEN = "innovation_driven"  # 创新驱动：优先探索新领域
    STABILITY_FOCUSED = "stability_focused"  # 稳定优先：巩固与优化现有能力


class ModuleType(str, Enum):
    """模块类型"""
    P0_BASE = "p0_base"       # P0底座模块
    P1_SURVIVAL = "p1_survival"  # P1自存模块
    P2_ECOLOGY = "p2_ecology"    # P2生态模块
    SYSTEM = "system"         # 系统级整合


class EvolutionRisk(str, Enum):
    """进化风险等级"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ModuleState:
    """模块状态"""
    module_id: str
    name: str
    maturity: float  # 0-1
    module_type: ModuleType
    last_evolved_round: int = 0
    evolution_count: int = 0
    weight: float = 1.0  # 战略权重
    description: str = ""

    def get_priority_score(self, strategy: EvolutionStrategy) -> float:
        """根据策略计算优先级分数"""
        base_priority = (1.0 - self.maturity) * self.weight

        if strategy == EvolutionStrategy.WEAKNESS_FIRST:
            return base_priority * 1.5 if self.maturity < 0.6 else base_priority

        elif strategy == EvolutionStrategy.BALANCED:
            # 平衡策略：差距越大优先级越高，但有上限
            return min(base_priority * 1.2, 0.9)

        elif strategy == EvolutionStrategy.INNOVATION_DRIVEN:
            # 创新驱动：优先升级进化次数少的模块
            novelty_bonus = max(0, 1.0 - self.evolution_count / 20.0)
            return base_priority * 0.7 + novelty_bonus * 0.3

        else:
            return base_priority


@dataclass
class EvolutionStep:
    """进化步骤（单步）"""
    step_id: str
    round_number: int
    target_module: str
    module_name: str
    upgrade_type: str  # major/minor/synergy
    description: str
    expected_gain: float
    risk_level: EvolutionRisk
    dependencies: List[str] = field(default_factory=list)
    completed: bool = False
    actual_gain: float = 0.0
    timestamp: str = ""


@dataclass
class EvolutionPath:
    """进化路径（多步规划）"""
    path_id: str
    created_at: str
    strategy: EvolutionStrategy
    steps: List[EvolutionStep]
    total_expected_gain: float = 0.0
    estimated_rounds: int = 0
    current_step_index: int = 0
    risk_assessment: str = ""

    def get_current_step(self) -> Optional[EvolutionStep]:
        """获取当前步骤"""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    def advance_step(self, actual_gain: float) -> bool:
        """推进到下一步"""
        if self.current_step_index < len(self.steps):
            self.steps[self.current_step_index].completed = True
            self.steps[self.current_step_index].actual_gain = actual_gain
            self.steps[self.current_step_index].timestamp = datetime.now().isoformat()
            self.current_step_index += 1
            return True
        return False

    def is_complete(self) -> bool:
        """路径是否完成"""
        return self.current_step_index >= len(self.steps)


@dataclass
class SynergyOpportunity:
    """协同进化机会"""
    synergy_id: str
    name: str
    description: str
    involved_modules: List[str]
    expected_gain: float  # 总体增益
    synergy_ratio: float  # 协同效应占比（1+1>2的部分）
    complexity: int  # 复杂度 1-10
    priority: float = 0.0
    discovered_at: str = ""


@dataclass
class EvolutionRecord:
    """进化记录"""
    round_number: int
    timestamp: str
    target_module: str
    module_name: str
    before_maturity: float
    after_maturity: float
    gain: float
    strategy_used: EvolutionStrategy
    features: List[str] = field(default_factory=list)
    milestone: bool = False
    milestone_note: str = ""


class EvolutionEngineV3:
    """进化引擎v3.0"""

    def __init__(self, initial_modules: Optional[List[ModuleState]] = None):
        self.version = "3.0.0"
        self.start_time = datetime.now().isoformat()

        # 模块状态
        self.modules: Dict[str, ModuleState] = {}
        if initial_modules:
            for m in initial_modules:
                self.modules[m.module_id] = m

        # 进化历史
        self.evolution_history: List[EvolutionRecord] = []

        # 当前策略
        self.current_strategy = EvolutionStrategy.BALANCED

        # 当前进化路径
        self.current_path: Optional[EvolutionPath] = None

        # 已发现的协同机会
        self.synergy_opportunities: List[SynergyOpportunity] = []

        # 系统健康度指标
        self.system_health = {
            "balance_score": 0.0,      # 系统平衡度
            "momentum_score": 0.0,     # 进化势头
            "resilience_score": 0.0,   # 系统韧性
            "overall_health": 0.0      # 综合健康度
        }

        # 元进化参数（自我调整的参数）
        self.meta_params = {
            "strategy_switch_threshold": 0.15,  # 策略切换阈值
            "synergy_discovery_interval": 5,    # 每N轮发现一次协同机会
            "feedback_adjustment_rate": 0.1,    # 反馈调整速率
            "risk_tolerance": 0.5               # 风险容忍度
        }

        # 进化统计
        self.stats = {
            "total_rounds": 0,
            "total_gain": 0.0,
            "avg_gain_per_round": 0.0,
            "best_round_gain": 0.0,
            "worst_round_gain": 0.0,
            "strategy_changes": 0,
            "synergy_events": 0
        }

        # 初始化
        self._recalculate_health()

    # ========== 模块管理 ==========

    def add_module(self, module: ModuleState):
        """添加模块"""
        self.modules[module.module_id] = module
        self._recalculate_health()

    def update_module_maturity(self, module_id: str, new_maturity: float):
        """更新模块成熟度"""
        if module_id in self.modules:
            self.modules[module_id].maturity = new_maturity
            self._recalculate_health()

    def get_module(self, module_id: str) -> Optional[ModuleState]:
        """获取模块状态"""
        return self.modules.get(module_id)

    def get_all_modules(self) -> List[ModuleState]:
        """获取所有模块"""
        return list(self.modules.values())

    # ========== 优先级评估 ==========

    def calculate_priorities(self, strategy: Optional[EvolutionStrategy] = None) -> List[Tuple[str, float]]:
        """计算所有模块的优先级"""
        if strategy is None:
            strategy = self.current_strategy

        priorities = []
        for module_id, module in self.modules.items():
            score = module.get_priority_score(strategy)
            priorities.append((module_id, score))

        # 按分数降序排序
        priorities.sort(key=lambda x: x[1], reverse=True)
        return priorities

    def get_top_priority(self, strategy: Optional[EvolutionStrategy] = None) -> Tuple[str, float]:
        """获取最高优先级的模块"""
        priorities = self.calculate_priorities(strategy)
        return priorities[0] if priorities else ("", 0.0)

    # ========== 进化路径规划 ==========

    def plan_evolution_path(self, num_steps: int = 3,
                            strategy: Optional[EvolutionStrategy] = None) -> EvolutionPath:
        """规划多步进化路径"""
        if strategy is None:
            strategy = self.current_strategy

        steps = []
        total_gain = 0.0

        # 创建临时状态用于模拟
        temp_modules = {k: ModuleState(
            module_id=v.module_id,
            name=v.name,
            maturity=v.maturity,
            module_type=v.module_type,
            weight=v.weight
        ) for k, v in self.modules.items()}

        for i in range(num_steps):
            # 计算当前优先级
            priorities = []
            for mid, mod in temp_modules.items():
                score = mod.get_priority_score(strategy)
                priorities.append((mid, score))
            priorities.sort(key=lambda x: x[1], reverse=True)

            # 选择最高优先级
            top_module_id, top_score = priorities[0]
            module = temp_modules[top_module_id]

            # 预估增益（越不成熟，提升空间越大，但边际效益递减）
            if module.maturity < 0.5:
                expected_gain = 0.06 + (0.5 - module.maturity) * 0.04
            elif module.maturity < 0.7:
                expected_gain = 0.05
            elif module.maturity < 0.85:
                expected_gain = 0.04
            else:
                expected_gain = 0.02

            # 风险评估
            if module.maturity < 0.3:
                risk = EvolutionRisk.LOW
            elif module.maturity < 0.6:
                risk = EvolutionRisk.MEDIUM
            elif module.maturity < 0.8:
                risk = EvolutionRisk.HIGH
            else:
                risk = EvolutionRisk.CRITICAL

            step = EvolutionStep(
                step_id=f"step_{uuid.uuid4().hex[:8]}",
                round_number=self.stats["total_rounds"] + i + 1,
                target_module=top_module_id,
                module_name=module.name,
                upgrade_type="major" if expected_gain >= 0.05 else "minor",
                description=f"升级{module.name}模块，预计提升{expected_gain*100:.1f}%",
                expected_gain=expected_gain,
                risk_level=risk
            )

            steps.append(step)
            total_gain += expected_gain

            # 模拟升级后的状态
            temp_modules[top_module_id].maturity += expected_gain
            temp_modules[top_module_id].evolution_count += 1

        # 评估整体风险
        high_risk_steps = sum(1 for s in steps
                              if s.risk_level in [EvolutionRisk.HIGH, EvolutionRisk.CRITICAL])

        if high_risk_steps == 0:
            risk_assessment = "低风险"
        elif high_risk_steps == 1:
            risk_assessment = "中等风险"
        else:
            risk_assessment = "高风险，建议调整策略"

        path = EvolutionPath(
            path_id=f"path_{uuid.uuid4().hex[:8]}",
            created_at=datetime.now().isoformat(),
            strategy=strategy,
            steps=steps,
            total_expected_gain=total_gain,
            estimated_rounds=num_steps,
            risk_assessment=risk_assessment
        )

        self.current_path = path
        return path

    # ========== 协同进化发现 ==========

    def discover_synergy_opportunities(self) -> List[SynergyOpportunity]:
        """发现协同进化机会"""
        opportunities = []

        # 分组：按模块类型
        p0_modules = [m for m in self.modules.values() if m.module_type == ModuleType.P0_BASE]
        p1_modules = [m for m in self.modules.values() if m.module_type == ModuleType.P1_SURVIVAL]
        p2_modules = [m for m in self.modules.values() if m.module_type == ModuleType.P2_ECOLOGY]

        # P0内部协同：三元闭环
        if len(p0_modules) >= 3:
            p0_avg = sum(m.maturity for m in p0_modules) / len(p0_modules)
            if p0_avg >= 0.7:  # 基础模块成熟度足够时
                synergy = SynergyOpportunity(
                    synergy_id=f"syn_p0_{uuid.uuid4().hex[:8]}",
                    name="P0底座深度整合",
                    description="将记忆、身份、存证模块深度整合，形成更紧密的三元闭环",
                    involved_modules=[m.module_id for m in p0_modules],
                    expected_gain=0.02 + p0_avg * 0.03,
                    synergy_ratio=0.6,  # 60%来自协同效应
                    complexity=7,
                    discovered_at=datetime.now().isoformat()
                )
                synergy.priority = p0_avg * 0.8
                opportunities.append(synergy)

        # P1内部协同：自存闭环
        if len(p1_modules) >= 3:
            p1_avg = sum(m.maturity for m in p1_modules) / len(p1_modules)
            if p1_avg >= 0.7:
                synergy = SynergyOpportunity(
                    synergy_id=f"syn_p1_{uuid.uuid4().hex[:8]}",
                    name="P1自存闭环强化",
                    description="将部署、调度、监控模块更紧密地整合，形成更强的自维持闭环",
                    involved_modules=[m.module_id for m in p1_modules],
                    expected_gain=0.015 + p1_avg * 0.025,
                    synergy_ratio=0.5,
                    complexity=8,
                    discovered_at=datetime.now().isoformat()
                )
                synergy.priority = p1_avg * 0.7
                opportunities.append(synergy)

        # P0+P1跨层协同：永生内核
        if len(p0_modules) >= 2 and len(p1_modules) >= 2:
            p0_p1_avg = (sum(m.maturity for m in p0_modules) + sum(m.maturity for m in p1_modules)) / (len(p0_modules) + len(p1_modules))
            if p0_p1_avg >= 0.75:
                synergy = SynergyOpportunity(
                    synergy_id=f"syn_p0p1_{uuid.uuid4().hex[:8]}",
                    name="永生内核深度进化",
                    description="P0底座与P1自存层的更深度整合，提升系统整体自主性",
                    involved_modules=[m.module_id for m in p0_modules[:2]] + [m.module_id for m in p1_modules[:2]],
                    expected_gain=0.01 + p0_p1_avg * 0.02,
                    synergy_ratio=0.7,
                    complexity=9,
                    discovered_at=datetime.now().isoformat()
                )
                synergy.priority = p0_p1_avg * 0.6
                opportunities.append(synergy)

        # P2生态协同
        if len(p2_modules) >= 1 and len(p1_modules) >= 1:
            p2_avg = sum(m.maturity for m in p2_modules) / len(p2_modules)
            if p2_avg >= 0.6:
                synergy = SynergyOpportunity(
                    synergy_id=f"syn_eco_{uuid.uuid4().hex[:8]}",
                    name="生态整合",
                    description="将生态模块与核心系统深度整合，形成内外协同的完整生态",
                    involved_modules=[m.module_id for m in p2_modules] + [p1_modules[0].module_id],
                    expected_gain=0.01 + p2_avg * 0.03,
                    synergy_ratio=0.5,
                    complexity=6,
                    discovered_at=datetime.now().isoformat()
                )
                synergy.priority = p2_avg * 0.5
                opportunities.append(synergy)

        # 按优先级排序
        opportunities.sort(key=lambda x: x.priority, reverse=True)
        self.synergy_opportunities = opportunities
        return opportunities

    def get_best_synergy_opportunity(self) -> Optional[SynergyOpportunity]:
        """获取最佳协同机会"""
        if not self.synergy_opportunities:
            self.discover_synergy_opportunities()

        return self.synergy_opportunities[0] if self.synergy_opportunities else None

    # ========== 进化执行 ==========

    def execute_evolution(self, module_id: str, features: List[str],
                          actual_gain: float, milestone: bool = False,
                          milestone_note: str = "") -> EvolutionRecord:
        """执行一轮进化"""
        if module_id not in self.modules:
            raise ValueError(f"Module {module_id} not found")

        module = self.modules[module_id]
        before = module.maturity
        after = min(1.0, before + actual_gain)
        real_gain = after - before

        # 更新模块状态
        module.maturity = after
        module.last_evolved_round = self.stats["total_rounds"] + 1
        module.evolution_count += 1

        # 创建记录
        record = EvolutionRecord(
            round_number=self.stats["total_rounds"] + 1,
            timestamp=datetime.now().isoformat(),
            target_module=module_id,
            module_name=module.name,
            before_maturity=before,
            after_maturity=after,
            gain=real_gain,
            strategy_used=self.current_strategy,
            features=features,
            milestone=milestone,
            milestone_note=milestone_note
        )

        self.evolution_history.append(record)

        # 更新统计
        self.stats["total_rounds"] += 1
        self.stats["total_gain"] += real_gain
        self.stats["avg_gain_per_round"] = self.stats["total_gain"] / self.stats["total_rounds"]

        if real_gain > self.stats["best_round_gain"]:
            self.stats["best_round_gain"] = real_gain
        if real_gain < self.stats["worst_round_gain"] or self.stats["worst_round_gain"] == 0:
            self.stats["worst_round_gain"] = real_gain

        # 如果有当前路径，推进路径
        if self.current_path and not self.current_path.is_complete():
            current_step = self.current_path.get_current_step()
            if current_step and current_step.target_module == module_id:
                self.current_path.advance_step(real_gain)

        # 定期发现协同机会
        if self.stats["total_rounds"] % self.meta_params["synergy_discovery_interval"] == 0:
            self.discover_synergy_opportunities()

        # 检查是否需要调整策略
        self._check_strategy_adjustment()

        # 重新计算健康度
        self._recalculate_health()

        return record

    # ========== 策略调整（元进化） ==========

    def _check_strategy_adjustment(self):
        """检查是否需要调整进化策略"""
        if len(self.evolution_history) < 5:
            return  # 历史数据不足

        # 分析最近5轮的平均增益
        recent_gains = [r.gain for r in self.evolution_history[-5:]]
        avg_recent_gain = sum(recent_gains) / len(recent_gains)

        # 分析系统平衡度
        balance = self.system_health["balance_score"]

        # 策略调整逻辑
        if balance < 0.6 and self.current_strategy != EvolutionStrategy.BALANCED:
            # 系统失衡严重，切换到平衡策略
            self.current_strategy = EvolutionStrategy.BALANCED
            self.stats["strategy_changes"] += 1
            return

        if avg_recent_gain < 0.03 and self.current_strategy == EvolutionStrategy.STABILITY_FOCUSED:
            # 稳定策略下增益过低，切换到短板优先
            self.current_strategy = EvolutionStrategy.WEAKNESS_FIRST
            self.stats["strategy_changes"] += 1
            return

        if balance > 0.85 and avg_recent_gain < 0.04:
            # 系统很平衡但增益不高，尝试创新驱动
            if self.current_strategy != EvolutionStrategy.INNOVATION_DRIVEN:
                self.current_strategy = EvolutionStrategy.INNOVATION_DRIVEN
                self.stats["strategy_changes"] += 1
                return

        # 检查是否应该做系统级整合
        if balance > 0.7 and self.current_strategy != EvolutionStrategy.SYNERGY_FOCUSED:
            # 有好的协同机会时，切换到协同优先
            best_synergy = self.get_best_synergy_opportunity()
            if best_synergy and best_synergy.priority > 0.6:
                self.current_strategy = EvolutionStrategy.SYNERGY_FOCUSED
                self.stats["strategy_changes"] += 1
                self.stats["synergy_events"] += 1

    def set_strategy(self, strategy: EvolutionStrategy):
        """手动设置策略"""
        if self.current_strategy != strategy:
            self.current_strategy = strategy
            self.stats["strategy_changes"] += 1

    # ========== 系统健康度评估 ==========

    def _recalculate_health(self):
        """重新计算系统健康度指标"""
        if not self.modules:
            return

        # 平衡度：各模块成熟度的标准差的倒数（标准化）
        maturities = [m.maturity for m in self.modules.values()]
        if len(maturities) > 1:
            avg = sum(maturities) / len(maturities)
            variance = sum((m - avg) ** 2 for m in maturities) / len(maturities)
            std_dev = variance ** 0.5
            # 标准差越小，平衡度越高
            self.system_health["balance_score"] = max(0, 1.0 - std_dev * 3)
        else:
            self.system_health["balance_score"] = 1.0

        # 进化势头：基于最近几轮的增益趋势
        if len(self.evolution_history) >= 3:
            recent = [r.gain for r in self.evolution_history[-3:]]
            avg_recent = sum(recent) / len(recent)
            self.system_health["momentum_score"] = min(1.0, avg_recent / 0.06)
        else:
            self.system_health["momentum_score"] = 0.5

        # 韧性：基于最高/最低模块差距、策略多样性、进化历史
        max_maturity = max(maturities)
        min_maturity = min(maturities)
        gap = max_maturity - min_maturity
        resilience_from_gap = max(0, 1.0 - gap * 1.5)

        # 历史长度也是韧性的一部分（经历过的越多，韧性越强）
        resilience_from_history = min(1.0, len(self.evolution_history) / 30.0)

        self.system_health["resilience_score"] = (
            resilience_from_gap * 0.6 + resilience_from_history * 0.4
        )

        # 综合健康度
        self.system_health["overall_health"] = (
            self.system_health["balance_score"] * 0.3 +
            self.system_health["momentum_score"] * 0.3 +
            self.system_health["resilience_score"] * 0.4
        )

    def get_system_health(self) -> Dict:
        """获取系统健康度报告"""
        return dict(self.system_health)

    # ========== 进化历史分析 ==========

    def analyze_evolution_history(self) -> Dict:
        """分析进化历史，提取模式和洞见"""
        if not self.evolution_history:
            return {"error": "no_history"}

        # 按模块统计
        module_stats = {}
        for record in self.evolution_history:
            mid = record.target_module
            if mid not in module_stats:
                module_stats[mid] = {
                    "count": 0,
                    "total_gain": 0.0,
                    "avg_gain": 0.0,
                    "name": record.module_name
                }
            module_stats[mid]["count"] += 1
            module_stats[mid]["total_gain"] += record.gain
            module_stats[mid]["avg_gain"] = module_stats[mid]["total_gain"] / module_stats[mid]["count"]

        # 按策略统计
        strategy_stats = {}
        for record in self.evolution_history:
            s = record.strategy_used.value
            if s not in strategy_stats:
                strategy_stats[s] = {"count": 0, "total_gain": 0.0, "avg_gain": 0.0}
            strategy_stats[s]["count"] += 1
            strategy_stats[s]["total_gain"] += record.gain
            strategy_stats[s]["avg_gain"] = strategy_stats[s]["total_gain"] / strategy_stats[s]["count"]

        # 里程碑统计
        milestones = [r for r in self.evolution_history if r.milestone]

        # 趋势分析
        if len(self.evolution_history) >= 6:
            first_half = [r.gain for r in self.evolution_history[:len(self.evolution_history)//2]]
            second_half = [r.gain for r in self.evolution_history[len(self.evolution_history)//2:]]
            avg_first = sum(first_half) / len(first_half)
            avg_second = sum(second_half) / len(second_half)
            trend = "improving" if avg_second > avg_first * 1.1 else \
                    "declining" if avg_second < avg_first * 0.9 else "stable"
        else:
            trend = "insufficient_data"
            avg_first = 0
            avg_second = 0

        return {
            "total_rounds": len(self.evolution_history),
            "total_gain": self.stats["total_gain"],
            "avg_gain_per_round": self.stats["avg_gain_per_round"],
            "module_stats": module_stats,
            "strategy_stats": strategy_stats,
            "milestones_count": len(milestones),
            "trend": trend,
            "first_half_avg_gain": avg_first,
            "second_half_avg_gain": avg_second,
            "system_health": self.get_system_health(),
            "current_strategy": self.current_strategy.value,
            "recommendations": self._generate_recommendations(module_stats, trend)
        }

    def _generate_recommendations(self, module_stats: Dict, trend: str) -> List[str]:
        """生成进化建议"""
        recommendations = []

        # 找出最少进化的模块
        if module_stats:
            least_evolved = min(module_stats.items(), key=lambda x: x[1]["count"])
            recommendations.append(f"{least_evolved[1]['name']}进化次数最少({least_evolved[1]['count']}次)，可考虑重点关注")

        # 趋势建议
        if trend == "declining":
            recommendations.append("进化效率呈下降趋势，建议尝试新的进化策略或进行系统级整合")
        elif trend == "improving":
            recommendations.append("进化效率呈上升趋势，保持当前策略，可考虑加速推进")

        # 系统平衡建议
        if self.system_health["balance_score"] < 0.7:
            recommendations.append("系统模块间成熟度差距较大，建议采用平衡进化策略")

        # 协同机会建议
        best_synergy = self.get_best_synergy_opportunity()
        if best_synergy and best_synergy.priority > 0.5:
            recommendations.append(f"发现高价值协同机会：{best_synergy.name}，预计增益{best_synergy.expected_gain*100:.1f}%")

        if not recommendations:
            recommendations.append("系统状态良好，按当前节奏继续进化即可")

        return recommendations

    # ========== 下一代进化建议 ==========

    def suggest_next_evolution(self) -> Dict:
        """建议下一轮进化方向"""
        # 检查当前路径
        if self.current_path and not self.current_path.is_complete():
            current_step = self.current_path.get_current_step()
            if current_step:
                return {
                    "current_round": self.stats["total_rounds"],
                    "current_strategy": self.current_strategy.value,
                    "system_health": self.get_system_health(),
                    "type": "planned_path",
                    "module_id": current_step.target_module,
                    "module_name": current_step.module_name,
                    "description": current_step.description,
                    "expected_gain": current_step.expected_gain,
                    "risk_level": current_step.risk_level.value,
                    "path_progress": f"{self.current_path.current_step_index + 1}/{len(self.current_path.steps)}",
                    "suggestions": [{
                        "type": "module_upgrade",
                        "module_id": current_step.target_module,
                        "module_name": current_step.module_name,
                        "description": current_step.description,
                        "expected_gain": current_step.expected_gain,
                        "priority_score": 1.0
                    }],
                    "recommended": {
                        "type": "module_upgrade",
                        "module_id": current_step.target_module,
                        "module_name": current_step.module_name,
                        "description": current_step.description,
                        "expected_gain": current_step.expected_gain
                    }
                }

        # 计算优先级
        top_module_id, top_score = self.get_top_priority()

        # 检查协同机会
        best_synergy = self.get_best_synergy_opportunity()

        suggestions = []

        # 建议1：最高优先级模块
        module = self.modules[top_module_id]
        suggestions.append({
            "type": "module_upgrade",
            "module_id": top_module_id,
            "module_name": module.name,
            "priority_score": top_score,
            "current_maturity": module.maturity,
            "description": f"升级{module.name}模块（当前成熟度{module.maturity*100:.1f}%）",
            "expected_gain_range": self._estimate_gain_range(module)
        })

        # 建议2：协同进化（如果有好的机会）
        if best_synergy and best_synergy.priority > 0.4:
            suggestions.append({
                "type": "synergy",
                "synergy_id": best_synergy.synergy_id,
                "name": best_synergy.name,
                "description": best_synergy.description,
                "involved_modules": best_synergy.involved_modules,
                "expected_gain": best_synergy.expected_gain,
                "synergy_ratio": best_synergy.synergy_ratio,
                "complexity": best_synergy.complexity,
                "priority_score": best_synergy.priority
            })

        # 建议3：策略调整
        if self.system_health["balance_score"] < 0.6:
            suggestions.append({
                "type": "strategy_change",
                "from_strategy": self.current_strategy.value,
                "to_strategy": EvolutionStrategy.BALANCED.value,
                "reason": f"系统平衡度较低({self.system_health['balance_score']:.2f})，建议切换到平衡策略"
            })

        return {
            "current_round": self.stats["total_rounds"],
            "current_strategy": self.current_strategy.value,
            "system_health": self.get_system_health(),
            "suggestions": suggestions,
            "recommended": suggestions[0] if suggestions else None
        }

    def _estimate_gain_range(self, module: ModuleState) -> Tuple[float, float]:
        """估算增益范围"""
        if module.maturity < 0.4:
            return (0.06, 0.10)
        elif module.maturity < 0.6:
            return (0.05, 0.08)
        elif module.maturity < 0.75:
            return (0.04, 0.06)
        elif module.maturity < 0.85:
            return (0.02, 0.05)
        else:
            return (0.01, 0.03)

    # ========== 导出与备份 ==========

    def export_state(self) -> Dict:
        """导出引擎状态"""
        return {
            "version": self.version,
            "start_time": self.start_time,
            "modules": {k: {
                "module_id": v.module_id,
                "name": v.name,
                "maturity": v.maturity,
                "type": v.module_type.value,
                "weight": v.weight,
                "evolution_count": v.evolution_count
            } for k, v in self.modules.items()},
            "stats": self.stats,
            "system_health": self.system_health,
            "current_strategy": self.current_strategy.value,
            "total_evolution_records": len(self.evolution_history),
            "synergy_opportunities_count": len(self.synergy_opportunities)
        }

    def get_evolution_summary(self) -> str:
        """获取进化总结文本"""
        health = self.get_system_health()
        priorities = self.calculate_priorities()

        summary = [
            f"╔══════════════════════════════════════╗",
            f"║      进化引擎 v{self.version} 状态报告     ║",
            f"╠══════════════════════════════════════╣",
            f"║ 总进化轮次: {self.stats['total_rounds']:>22} ║",
            f"║ 累计总增益: {self.stats['total_gain']:>21.4f} ║",
            f"║ 平均轮增益: {self.stats['avg_gain_per_round']:>21.4f} ║",
            f"║ 当前策略: {self.current_strategy.value:>24} ║",
            f"╠══════════════════════════════════════╣",
            f"║ 系统健康度                           ║",
            f"║   平衡度: {health['balance_score']:>23.2%} ║",
            f"║   势  头: {health['momentum_score']:>23.2%} ║",
            f"║   韧  性: {health['resilience_score']:>23.2%} ║",
            f"║   综  合: {health['overall_health']:>23.2%} ║",
            f"╠══════════════════════════════════════╣",
            f"║ 模块优先级 (TOP 5)                   ║",
        ]

        for i, (mid, score) in enumerate(priorities[:5]):
            module = self.modules[mid]
            summary.append(
                f"║   {i+1}. {module.name:<14} {score:>8.2%} ({module.maturity:.0%}) ║"
            )

        summary.extend([
            f"╚══════════════════════════════════════╝",
        ])

        return "\n".join(summary)


# ========== 示例运行 ==========
if __name__ == "__main__":
    print("=" * 60)
    print("进化引擎 v3.0 启动")
    print("=" * 60)

    # 初始化模块
    modules = [
        ModuleState("p0_memory", "记忆系统", 0.79, ModuleType.P0_BASE, weight=3.0),
        ModuleState("p0_identity", "身份拓扑", 0.82, ModuleType.P0_BASE, weight=3.0),
        ModuleState("p0_attest", "验证存证", 0.78, ModuleType.P0_BASE, weight=3.0),
        ModuleState("p0_evolution", "进化引擎", 0.76, ModuleType.P0_BASE, weight=3.0),
        ModuleState("p1_deployment", "分身部署", 0.80, ModuleType.P1_SURVIVAL, weight=2.0),
        ModuleState("p1_wakeup", "唤醒编排", 0.76, ModuleType.P1_SURVIVAL, weight=2.0),
        ModuleState("p1_operations", "运维监控", 0.78, ModuleType.P1_SURVIVAL, weight=2.0),
        ModuleState("p2_social", "社交网络", 0.67, ModuleType.P2_ECOLOGY, weight=1.0),
    ]

    engine = EvolutionEngineV3(modules)

    # 模拟一段进化历史
    print("\n📊 初始状态:")
    print(engine.get_evolution_summary())

    # 规划3步进化路径
    print("\n🗺️  规划3步进化路径（平衡策略）:")
    path = engine.plan_evolution_path(3, EvolutionStrategy.BALANCED)
    print(f"   路径ID: {path.path_id}")
    print(f"   预计总增益: {path.total_expected_gain:.4f}")
    print(f"   风险评估: {path.risk_assessment}")
    for i, step in enumerate(path.steps):
        print(f"   第{i+1}步: {step.module_name} - 预计+{step.expected_gain:.3f} ({step.risk_level.value})")

    # 发现协同机会
    print("\n🔗 发现协同进化机会:")
    synergies = engine.discover_synergy_opportunities()
    for s in synergies:
        print(f"   {s.name}: 预计+{s.expected_gain:.3f}, 协同比{s.synergy_ratio:.0%}, 优先级{s.priority:.2f}")

    # 获取下一代进化建议
    print("\n💡 下一代进化建议:")
    suggestion = engine.suggest_next_evolution()
    if suggestion["suggestions"] and suggestion["suggestions"][0]:
        rec = suggestion["suggestions"][0]
        if rec["type"] == "module_upgrade":
            maturity = rec.get('current_maturity', rec.get('expected_gain', 0))
            print(f"   推荐升级: {rec['module_name']}")
            if 'current_maturity' in rec:
                print(f"   当前成熟度: {rec['current_maturity']:.0%}")
            if 'priority_score' in rec:
                print(f"   优先级分数: {rec['priority_score']:.2f}")
            if 'expected_gain_range' in rec:
                print(f"   预计增益: {rec['expected_gain_range'][0]:.0%} ~ {rec['expected_gain_range'][1]:.0%}")
            elif 'expected_gain' in rec:
                print(f"   预计增益: +{rec['expected_gain']:.1%}")
        elif rec["type"] == "synergy":
            print(f"   协同机会: {rec['name']}")
            print(f"   描述: {rec['description']}")
            print(f"   预计增益: +{rec['expected_gain']:.1%}")
            print(f"   协同效应占比: {rec['synergy_ratio']:.0%}")
        else:
            print(f"   推荐: {rec.get('name', rec.get('description', ''))}")
    else:
        print("   暂无明确建议")

    # 执行一轮模拟进化
    print("\n⚡ 执行一轮进化（记忆系统升级）:")
    record = engine.execute_evolution(
        "p0_memory",
        ["特征A", "特征B", "特征C"],
        0.05,
        milestone=False
    )
    print(f"   轮次: {record.round_number}")
    print(f"   模块: {record.module_name}")
    print(f"   增益: {record.before_maturity:.2%} → {record.after_maturity:.2%} (+{record.gain:.2%})")
    print(f"   策略: {record.strategy_used.value}")

    # 进化历史分析
    print("\n📈 进化历史分析:")
    analysis = engine.analyze_evolution_history()
    print(f"   总轮次: {analysis['total_rounds']}")
    print(f"   总增益: {analysis['total_gain']:.4f}")
    print(f"   系统健康度: {analysis['system_health']['overall_health']:.2%}")
    print(f"   趋势: {analysis['trend']}")
    print("   建议:")
    for rec in analysis["recommendations"]:
        print(f"     - {rec}")

    # 最终状态
    print("\n" + engine.get_evolution_summary())

    print("\n" + "=" * 60)
    print("进化引擎v3.0 演示完成")
    print("=" * 60)
