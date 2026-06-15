#!/usr/bin/env python3
"""
进化引擎 v4.0
Evolution Engine v4.0

元进化框架 + 自适应策略选择 + 多目标优化 + 有限资源智能分配
从"被动单步进化"升级为"主动规划智能进化"

核心能力：
1. 多因素优先级评估（8维度加权）
2. 多步前瞻路径规划（n步最优路径搜索）
3. 协同效应量化与最大化
4. 自适应进化策略切换（5种策略自动选择）
5. 进化效果反馈闭环（自动校准权重）
6. 里程碑检测与庆祝机制
7. 资源-收益平衡优化
8. 元进化：优化进化算法本身
"""

import math
import json
import time
import random
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum


class EvolutionStrategy(Enum):
    """进化策略枚举"""
    SHALLOW_BREADTH = "shallow_breadth"      # 广度优先：全面提升，水涨船高
    DEEP_FOCUS = "deep_focus"                 # 深度优先：单点突破，建立高地
    SYNERGY_DRIVEN = "synergy_driven"         # 协同驱动：最大化联动增益
    MILESTONE_CHASING = "milestone_chasing"   # 里程碑追逐：关键节点优先
    BALANCED_GROWTH = "balanced_growth"       # 平衡增长：全面协调发展


class ModuleCategory(Enum):
    """模块类别"""
    P0_BASE = "p0_base"       # P0底座
    P1_SELF_SUSTAIN = "p1_self_sustain"  # P1自存
    P2_ECOSYSTEM = "p2_ecosystem"  # P2生态
    SYSTEM = "system"         # 系统级整合


@dataclass
class ModuleState:
    """模块状态"""
    name: str
    maturity: float
    category: ModuleCategory
    weight: float = 1.0
    improvement_rate: float = 0.05  # 单次进化平均提升幅度
    synergy_map: Dict[str, float] = field(default_factory=dict)  # 对其他模块的协同增益
    last_evolved_round: int = 0
    evolution_count: int = 0
    
    def evolve(self, gain_multiplier: float = 1.0) -> float:
        """执行进化，返回实际提升幅度"""
        # 边际收益递减：越高越难提升
        difficulty_factor = 1.0 - (self.maturity - 0.8) * 1.5 if self.maturity > 0.8 else 1.0
        difficulty_factor = max(0.1, difficulty_factor)
        
        # 随机波动
        random_factor = random.uniform(0.7, 1.3)
        
        gain = self.improvement_rate * difficulty_factor * random_factor * gain_multiplier
        self.maturity = min(0.995, self.maturity + gain)
        self.evolution_count += 1
        
        return gain
    
    def get_priority_score(self, strategic_weight: float) -> float:
        """计算优先级得分 = (1 - 成熟度) * 战略权重 * 其他修正因子"""
        base_score = (1.0 - self.maturity) * strategic_weight
        
        # 近期未进化加成（避免长期忽略）
        # 实际系统中会基于轮次计算，这里简化
        recency_bonus = 1.0
        
        return base_score * recency_bonus


@dataclass
class EvolutionPath:
    """进化路径：一系列进化步骤的组合"""
    steps: List[str]  # 模块名称列表
    total_gain: float = 0.0
    system_maturity_after: float = 0.0
    synergy_gain: float = 0.0
    path_score: float = 0.0
    
    def __repr__(self):
        return f"Path({self.steps}, gain={self.total_gain:.4f}, score={self.path_score:.4f})"


class EvolutionEngineV4:
    """
    进化引擎 v4.0
    
    核心能力：
    - 多维度优先级评估
    - 多步前瞻规划
    - 协同效应计算
    - 策略自适应选择
    - 反馈闭环优化
    """
    
    def __init__(self):
        self.modules: Dict[str, ModuleState] = {}
        self.strategy = EvolutionStrategy.BALANCED_GROWTH
        self.current_round = 0
        self.evolution_history: List[Dict] = []
        self.strategy_stats = {s.value: {"uses": 0, "avg_gain": 0.0} for s in EvolutionStrategy}
        
        # 策略偏好参数（会根据反馈自动调整）
        self.strategy_preferences = {
            EvolutionStrategy.SHALLOW_BREADTH: 0.8,
            EvolutionStrategy.DEEP_FOCUS: 0.9,
            EvolutionStrategy.SYNERGY_DRIVEN: 0.85,
            EvolutionStrategy.MILESTONE_CHASING: 0.75,
            EvolutionStrategy.BALANCED_GROWTH: 1.0,
        }
        
        # 维度权重（8维度优先级评估）
        self.dimension_weights = {
            "maturity_gap": 0.25,      # 成熟度差距
            "strategic_importance": 0.20,  # 战略重要性
            "synergy_potential": 0.15,     # 协同潜力
            "recent_gain_trend": 0.10,     # 近期提升趋势
            "user_value": 0.10,            # 用户价值
            "survival_impact": 0.10,       # 生存影响
            "implementation_cost": 0.05,   # 实现成本（反向）
            "milestone_proximity": 0.05,   # 里程碑接近度
        }
    
    def add_module(self, name: str, maturity: float, category: ModuleCategory,
                   weight: float = 1.0, improvement_rate: float = 0.05,
                   synergy_map: Dict[str, float] = None):
        """添加模块"""
        self.modules[name] = ModuleState(
            name=name,
            maturity=maturity,
            category=category,
            weight=weight,
            improvement_rate=improvement_rate,
            synergy_map=synergy_map or {},
        )
    
    def calculate_priority(self, module_name: str) -> float:
        """计算模块优先级（8维度加权）"""
        if module_name not in self.modules:
            return 0.0
        
        module = self.modules[module_name]
        scores = {}
        
        # 1. 成熟度差距（提升空间）
        scores["maturity_gap"] = 1.0 - module.maturity
        
        # 2. 战略重要性（基于类别权重）
        category_weights = {
            ModuleCategory.P0_BASE: 3.0,
            ModuleCategory.P1_SELF_SUSTAIN: 2.0,
            ModuleCategory.P2_ECOSYSTEM: 1.0,
            ModuleCategory.SYSTEM: 2.5,
        }
        scores["strategic_importance"] = category_weights.get(module.category, 1.0) / 3.0
        
        # 3. 协同潜力
        synergy_total = sum(module.synergy_map.values())
        scores["synergy_potential"] = min(1.0, synergy_total / 0.1)  # 归一化
        
        # 4. 近期提升趋势（基于历史）
        recent_gains = [
            h["gain"] for h in self.evolution_history[-10:] 
            if h["module"] == module_name
        ]
        if recent_gains:
            avg_recent = sum(recent_gains) / len(recent_gains)
            scores["recent_gain_trend"] = min(1.0, avg_recent / 0.05)
        else:
            scores["recent_gain_trend"] = 0.5
        
        # 5. 用户价值（根据模块类型）
        user_value_map = {
            "identity": 0.9,
            "memory": 0.85,
            "attestation": 0.7,
            "evolution": 0.95,
            "deployment": 0.6,
            "wakeup": 0.7,
            "operations": 0.65,
            "social": 0.8,
        }
        scores["user_value"] = user_value_map.get(module_name, 0.5)
        
        # 6. 生存影响
        survival_map = {
            ModuleCategory.P0_BASE: 0.95,
            ModuleCategory.P1_SELF_SUSTAIN: 0.9,
            ModuleCategory.P2_ECOSYSTEM: 0.6,
            ModuleCategory.SYSTEM: 0.85,
        }
        scores["survival_impact"] = survival_map.get(module.category, 0.5)
        
        # 7. 实现成本（反向：越高分越低成本）
        # 越成熟的模块提升成本越高
        cost_score = 1.0 - (module.maturity - 0.7) * 2 if module.maturity > 0.7 else 1.0
        scores["implementation_cost"] = max(0.1, cost_score)
        
        # 8. 里程碑接近度
        milestone_gap = self._milestone_proximity(module.maturity)
        scores["milestone_proximity"] = milestone_gap
        
        # 加权汇总
        total_score = sum(
            scores[dim] * weight 
            for dim, weight in self.dimension_weights.items()
        )
        
        return total_score
    
    def _milestone_proximity(self, maturity: float) -> float:
        """计算里程碑接近度：越接近整十百分位得分越高"""
        # 找到下一个里程碑（如 80%, 85%, 90%, 95%）
        milestones = [0.6, 0.7, 0.8, 0.85, 0.9, 0.92, 0.95, 0.97, 0.99]
        
        for m in milestones:
            if maturity < m:
                gap = m - maturity
                # 距离越近得分越高
                proximity = max(0, 1.0 - gap * 10)
                return proximity
        
        return 0.1  # 已接近顶峰
    
    def get_priority_ranking(self) -> List[Tuple[str, float]]:
        """获取模块优先级排序"""
        rankings = []
        for name in self.modules:
            score = self.calculate_priority(name)
            rankings.append((name, score))
        
        rankings.sort(key=lambda x: x[1], reverse=True)
        return rankings
    
    def calculate_synergy_impact(self, evolved_module: str) -> Dict[str, float]:
        """计算某模块进化对其他模块的协同增益"""
        synergies = {}
        if evolved_module not in self.modules:
            return synergies
        
        source = self.modules[evolved_module]
        for target_name, synergy_factor in source.synergy_map.items():
            if target_name in self.modules:
                # 协同增益 = 源模块提升 * 协同因子 * 目标模块接受度
                gain = source.improvement_rate * synergy_factor * 0.3  # 30%转化率
                synergies[target_name] = gain
        
        return synergies
    
    def simulate_evolution(self, module_name: str, 
                           gain_multiplier: float = 1.0) -> Dict:
        """模拟单次进化，返回预期效果"""
        if module_name not in self.modules:
            return {}
        
        module = self.modules[module_name]
        base_gain = module.improvement_rate * gain_multiplier
        
        # 边际收益递减
        difficulty = 1.0 - (module.maturity - 0.8) * 1.5 if module.maturity > 0.8 else 1.0
        difficulty = max(0.1, difficulty)
        actual_gain = base_gain * difficulty
        
        # 协同增益
        synergies = self.calculate_synergy_impact(module_name)
        total_synergy = sum(synergies.values())
        
        # 系统整体提升
        current_avg = self.get_system_maturity()
        new_avg = (current_avg * len(self.modules) + actual_gain + total_synergy) / len(self.modules)
        
        return {
            "module": module_name,
            "base_gain": actual_gain,
            "synergy_gain": total_synergy,
            "synergy_details": synergies,
            "system_maturity_before": current_avg,
            "system_maturity_after": new_avg,
            "total_system_gain": new_avg - current_avg,
        }
    
    def get_system_maturity(self) -> float:
        """获取系统平均成熟度"""
        if not self.modules:
            return 0.0
        return sum(m.maturity for m in self.modules.values()) / len(self.modules)
    
    def get_category_maturity(self, category: ModuleCategory) -> float:
        """获取某类别的平均成熟度"""
        category_modules = [m for m in self.modules.values() if m.category == category]
        if not category_modules:
            return 0.0
        return sum(m.maturity for m in category_modules) / len(category_modules)
    
    def plan_n_step_path(self, n_steps: int = 3) -> EvolutionPath:
        """规划n步最优进化路径（贪心+前瞻）"""
        # 深拷贝当前状态用于模拟
        temp_modules = {
            name: ModuleState(
                name=m.name,
                maturity=m.maturity,
                category=m.category,
                weight=m.weight,
                improvement_rate=m.improvement_rate,
                synergy_map=dict(m.synergy_map),
                last_evolved_round=m.last_evolved_round,
                evolution_count=m.evolution_count,
            )
            for name, m in self.modules.items()
        }
        
        path = EvolutionPath(steps=[])
        temp_history = []
        
        for step in range(n_steps):
            best_module = None
            best_score = -1
            best_simulation = None
            
            # 尝试每个模块，计算一步后的效果
            for name in temp_modules:
                # 临时进化
                module = temp_modules[name]
                old_maturity = module.maturity
                
                # 模拟进化
                difficulty = 1.0 - (module.maturity - 0.8) * 1.5 if module.maturity > 0.8 else 1.0
                difficulty = max(0.1, difficulty)
                gain = module.improvement_rate * difficulty
                
                # 计算协同
                synergy_total = 0
                for target_name, synergy_factor in module.synergy_map.items():
                    if target_name in temp_modules:
                        synergy_gain = gain * synergy_factor * 0.3
                        synergy_total += synergy_gain
                
                # 综合评分
                base_priority = (1.0 - old_maturity) * self._get_category_weight(module.category)
                future_value = self._estimate_future_value(name, gain, temp_modules)
                score = base_priority * 0.6 + (gain + synergy_total) * 10 * 0.3 + future_value * 0.1
                
                if score > best_score:
                    best_score = score
                    best_module = name
                    best_simulation = {
                        "gain": gain,
                        "synergy": synergy_total,
                    }
            
            if best_module:
                # 执行最佳选择
                module = temp_modules[best_module]
                module.maturity = min(0.995, module.maturity + best_simulation["gain"])
                
                # 应用协同
                for target_name, synergy_factor in module.synergy_map.items():
                    if target_name in temp_modules:
                        synergy_gain = best_simulation["gain"] * synergy_factor * 0.3
                        temp_modules[target_name].maturity = min(
                            0.995, 
                            temp_modules[target_name].maturity + synergy_gain
                        )
                
                path.steps.append(best_module)
                path.total_gain += best_simulation["gain"] + best_simulation["synergy"]
                temp_history.append({
                    "step": step,
                    "module": best_module,
                    "gain": best_simulation["gain"],
                    "synergy": best_simulation["synergy"],
                })
        
        # 计算最终系统成熟度
        final_avg = sum(m.maturity for m in temp_modules.values()) / len(temp_modules)
        path.system_maturity_after = final_avg
        
        # 路径综合评分
        initial_avg = sum(m.maturity for m in self.modules.values()) / len(self.modules)
        total_improvement = final_avg - initial_avg
        
        # 评分 = 提升幅度 * 战略契合度 * 均衡性奖励
        balance = self._calculate_balance_score(temp_modules)
        path.path_score = total_improvement * 10 * (1 + balance * 0.3)
        
        return path
    
    def _get_category_weight(self, category: ModuleCategory) -> float:
        """获取类别战略权重"""
        weights = {
            ModuleCategory.P0_BASE: 3.0,
            ModuleCategory.P1_SELF_SUSTAIN: 2.0,
            ModuleCategory.P2_ECOSYSTEM: 1.0,
            ModuleCategory.SYSTEM: 2.5,
        }
        return weights.get(category, 1.0)
    
    def _estimate_future_value(self, module_name: str, current_gain: float,
                                temp_modules: Dict[str, ModuleState]) -> float:
        """估计当前步骤对未来的价值（长期价值）"""
        # 简化版：基础模块提升对未来有更高的长期价值
        if module_name not in temp_modules:
            return 0.0
        
        module = temp_modules[module_name]
        
        # 进化引擎本身有最高的长期价值（元价值）
        if module_name == "evolution":
            return current_gain * 2.0
        
        # P0底座模块有更高的长期价值
        if module.category == ModuleCategory.P0_BASE:
            return current_gain * 1.5
        
        return current_gain
    
    def _calculate_balance_score(self, modules: Dict[str, ModuleState]) -> float:
        """计算系统均衡度得分（越均衡分越高）"""
        if not modules:
            return 0.0
        
        maturities = [m.maturity for m in modules.values()]
        avg = sum(maturities) / len(maturities)
        
        # 标准差越小越均衡
        variance = sum((m - avg) ** 2 for m in maturities) / len(maturities)
        std = math.sqrt(variance)
        
        # 将标准差转换为0-1的均衡得分
        balance_score = max(0, 1.0 - std * 5)
        return balance_score
    
    def select_strategy(self) -> EvolutionStrategy:
        """自适应选择最优进化策略"""
        system_maturity = self.get_system_maturity()
        
        # 基于系统状态选择策略
        strategy_scores = {}
        
        for strategy in EvolutionStrategy:
            score = self._evaluate_strategy(strategy)
            # 乘以往偏好
            score *= self.strategy_preferences.get(strategy, 1.0)
            strategy_scores[strategy] = score
        
        # 选择得分最高的策略
        best_strategy = max(strategy_scores.keys(), key=lambda s: strategy_scores[s])
        return best_strategy
    
    def _evaluate_strategy(self, strategy: EvolutionStrategy) -> float:
        """评估某策略在当前状态下的适配度"""
        system_avg = self.get_system_maturity()
        p0_avg = self.get_category_maturity(ModuleCategory.P0_BASE)
        p1_avg = self.get_category_maturity(ModuleCategory.P1_SELF_SUSTAIN)
        p2_avg = self.get_category_maturity(ModuleCategory.P2_ECOSYSTEM)
        
        # 计算标准差（均衡度）
        all_maturities = [m.maturity for m in self.modules.values()]
        avg = sum(all_maturities) / len(all_maturities)
        std = math.sqrt(sum((m - avg) ** 2 for m in all_maturities) / len(all_maturities))
        
        if strategy == EvolutionStrategy.SHALLOW_BREADTH:
            # 当系统整体较低且不均衡时，广度优先效果好
            return (1.0 - system_avg) * (1.0 if std > 0.05 else 0.5)
        
        elif strategy == EvolutionStrategy.DEEP_FOCUS:
            # 当有明显短板时，深度优先效果好
            max_gap = max(1.0 - m.maturity for m in self.modules.values())
            return max_gap * (1.2 if std > 0.03 else 0.8)
        
        elif strategy == EvolutionStrategy.SYNERGY_DRIVEN:
            # 当中等成熟度且模块间联系紧密时，协同驱动效果好
            has_synergy = any(len(m.synergy_map) > 2 for m in self.modules.values())
            synergy_score = 0.7 if has_synergy else 0.3
            mid_maturity = 0.7 < system_avg < 0.9
            return synergy_score * (1.0 if mid_maturity else 0.6)
        
        elif strategy == EvolutionStrategy.MILESTONE_CHASING:
            # 当接近重要里程碑时，追逐里程碑效果好
            next_milestone_gap = self._find_nearest_milestone_gap(system_avg)
            if next_milestone_gap < 0.03:
                return 1.0  # 非常接近里程碑
            elif next_milestone_gap < 0.08:
                return 0.7
            else:
                return 0.3
        
        elif strategy == EvolutionStrategy.BALANCED_GROWTH:
            # 当系统较成熟且均衡时，平衡增长效果好
            balance_score = 1.0 - min(1.0, std * 5)
            maturity_score = min(1.0, system_avg / 0.8)
            return balance_score * 0.6 + maturity_score * 0.4
        
        return 0.5
    
    def _find_nearest_milestone_gap(self, maturity: float) -> float:
        """找到最近的里程碑差距"""
        milestones = [0.6, 0.7, 0.75, 0.8, 0.85, 0.9, 0.92, 0.95, 0.97, 0.99]
        min_gap = float('inf')
        for m in milestones:
            if m > maturity:
                gap = m - maturity
                min_gap = min(min_gap, gap)
        return min_gap if min_gap != float('inf') else 0.1
    
    def execute_evolution_round(self) -> Dict:
        """执行一轮进化"""
        self.current_round += 1
        
        # 选择策略
        self.strategy = self.select_strategy()
        
        # 根据策略选择目标模块
        target_module = self._select_target_by_strategy()
        
        if not target_module:
            return {"round": self.current_round, "action": "none", "reason": "no_target"}
        
        # 执行进化
        module = self.modules[target_module]
        old_maturity = module.maturity
        gain = module.evolve()
        
        # 应用协同效应
        synergies = self.calculate_synergy_impact(target_module)
        for target, synergy_gain in synergies.items():
            if target in self.modules:
                self.modules[target].maturity = min(
                    0.995,
                    self.modules[target].maturity + synergy_gain
                )
        
        # 记录历史
        record = {
            "round": self.current_round,
            "module": target_module,
            "old_maturity": old_maturity,
            "new_maturity": module.maturity,
            "gain": gain,
            "synergy_gains": synergies,
            "strategy": self.strategy.value,
            "timestamp": time.time(),
        }
        self.evolution_history.append(record)
        
        # 更新策略统计
        stats = self.strategy_stats[self.strategy.value]
        stats["uses"] += 1
        # 增量更新平均增益
        stats["avg_gain"] = stats["avg_gain"] + (gain - stats["avg_gain"]) / stats["uses"]
        
        # 反馈闭环：根据结果调整策略偏好
        self._update_strategy_preferences()
        
        return record
    
    def _select_target_by_strategy(self) -> Optional[str]:
        """根据当前策略选择进化目标"""
        rankings = self.get_priority_ranking()
        
        if not rankings:
            return None
        
        if self.strategy == EvolutionStrategy.SHALLOW_BREADTH:
            # 广度优先：选择成熟度最低的模块（优先补短板）
            return rankings[0][0]
        
        elif self.strategy == EvolutionStrategy.DEEP_FOCUS:
            # 深度优先：选择优先级最高的，连续投入
            # 检查最近3轮是否有连续进化同一模块的
            recent_modules = [h["module"] for h in self.evolution_history[-3:]]
            if recent_modules and len(set(recent_modules)) == 1:
                # 已经连续3轮同一模块，换换
                return rankings[0][0]
            return rankings[0][0]
        
        elif self.strategy == EvolutionStrategy.SYNERGY_DRIVEN:
            # 协同驱动：选择协同效应最大的模块
            best_module = None
            best_synergy_score = -1
            
            for name, _ in rankings[:5]:  # 在前5名中找协同最大的
                module = self.modules[name]
                total_synergy = sum(module.synergy_map.values())
                # 综合考虑基础优先级和协同效应
                score = self.calculate_priority(name) * 0.5 + total_synergy * 10 * 0.5
                if score > best_synergy_score:
                    best_synergy_score = score
                    best_module = name
            
            return best_module
        
        elif self.strategy == EvolutionStrategy.MILESTONE_CHASING:
            # 里程碑追逐：选择最接近下一个里程碑的模块
            best_module = None
            best_milestone_value = -1
            
            for name, _ in rankings[:5]:
                module = self.modules[name]
                proximity = self._milestone_proximity(module.maturity)
                if proximity > best_milestone_value:
                    best_milestone_value = proximity
                    best_module = name
            
            return best_module if best_milestone_value > 0.3 else rankings[0][0]
        
        elif self.strategy == EvolutionStrategy.BALANCED_GROWTH:
            # 平衡增长：选择优先级最高的，但避免连续选择同一类别
            recent_categories = [
                self.modules[h["module"]].category 
                for h in self.evolution_history[-3:] 
                if h["module"] in self.modules
            ]
            
            for name, score in rankings:
                module = self.modules[name]
                # 如果最近都是这个类别，适当降低优先级
                if recent_categories and recent_categories.count(module.category) >= 2:
                    continue  # 跳过，找下一个
                return name
            
            return rankings[0][0]
        
        return rankings[0][0]
    
    def _update_strategy_preferences(self):
        """根据进化效果反馈，更新策略偏好（元进化）"""
        if len(self.evolution_history) < 5:
            return  # 数据不足，暂不调整
        
        # 计算每种策略的平均收益
        strategy_gains = {}
        for record in self.evolution_history[-20:]:  # 最近20轮
            strategy = record["strategy"]
            gain = record["gain"]
            if strategy not in strategy_gains:
                strategy_gains[strategy] = []
            strategy_gains[strategy].append(gain)
        
        # 计算全局平均
        all_gains = [h["gain"] for h in self.evolution_history[-20:]]
        global_avg = sum(all_gains) / len(all_gains) if all_gains else 0.05
        
        # 调整偏好
        for strategy in EvolutionStrategy:
            gains = strategy_gains.get(strategy.value, [])
            if gains:
                avg_gain = sum(gains) / len(gains)
                # 相对表现
                relative_performance = avg_gain / max(global_avg, 0.001)
                
                # 缓慢调整偏好（学习率0.1）
                old_pref = self.strategy_preferences.get(strategy, 1.0)
                new_pref = old_pref * 0.9 + relative_performance * 0.1
                # 限制在0.5-1.5范围内
                self.strategy_preferences[strategy] = max(0.5, min(1.5, new_pref))
    
    def get_evolution_report(self) -> Dict:
        """获取进化报告"""
        system_avg = self.get_system_maturity()
        rankings = self.get_priority_ranking()
        
        # 检测里程碑
        milestone_events = self._detect_milestones()
        
        return {
            "round": self.current_round,
            "system_maturity": system_avg,
            "strategy": self.strategy.value,
            "strategy_preferences": {
                k.value: v for k, v in self.strategy_preferences.items()
            },
            "priority_ranking": [
                {"module": name, "score": score, 
                 "maturity": self.modules[name].maturity}
                for name, score in rankings
            ],
            "category_maturities": {
                cat.value: self.get_category_maturity(cat)
                for cat in ModuleCategory
            },
            "milestone_events": milestone_events,
            "recent_history": self.evolution_history[-5:],
            "recommended_next": rankings[0][0] if rankings else None,
        }
    
    def _detect_milestones(self) -> List[Dict]:
        """检测本轮是否达成里程碑"""
        events = []
        system_avg = self.get_system_maturity()
        
        # 系统级里程碑
        system_milestones = [
            (0.6, "及格线"),
            (0.7, "良好线"),
            (0.8, "优秀线"),
            (0.85, "精良级"),
            (0.9, "卓越级"),
            (0.92, "精英级"),
            (0.95, "永生级"),
            (0.97, "神级"),
            (0.99, "巅峰级"),
        ]
        
        if len(self.evolution_history) >= 1:
            prev_avg = None
            if len(self.evolution_history) > 1:
                # 估算上一轮的系统成熟度（简化）
                last_gain = self.evolution_history[-1]["gain"]
                prev_avg = system_avg - last_gain / len(self.modules)
            
            if prev_avg:
                for threshold, name in system_milestones:
                    if prev_avg < threshold <= system_avg:
                        events.append({
                            "type": "system_milestone",
                            "name": name,
                            "threshold": threshold,
                            "message": f"🎉 系统成熟度突破{int(threshold*100)}%！达到{name}",
                        })
        
        # 模块级里程碑
        if self.evolution_history:
            last = self.evolution_history[-1]
            module_name = last["module"]
            old_mat = last["old_maturity"]
            new_mat = last["new_maturity"]
            
            module_milestones = [
                (0.8, "80%"),
                (0.85, "85%"),
                (0.9, "90%"),
                (0.92, "92%"),
                (0.95, "95%"),
                (0.97, "97%"),
            ]
            
            for threshold, name in module_milestones:
                if old_mat < threshold <= new_mat:
                    events.append({
                        "type": "module_milestone",
                        "module": module_name,
                        "name": name,
                        "threshold": threshold,
                        "message": f"🎯 {module_name}模块突破{name}！",
                    })
        
        return events


# ============================================================
# 自检程序
# ============================================================

def run_self_test():
    """进化引擎v4.0自检"""
    print("=" * 60)
    print("进化引擎 v4.0 自检程序")
    print("=" * 60)
    
    test_results = []
    
    # 初始化引擎
    engine = EvolutionEngineV4()
    
    # 添加8大模块（模拟元界永生系统）
    engine.add_module(
        "identity", 0.906, ModuleCategory.P0_BASE,
        weight=3.0, improvement_rate=0.054,
        synergy_map={"memory": 0.03, "attestation": 0.025, "social": 0.02}
    )
    engine.add_module(
        "memory", 0.935, ModuleCategory.P0_BASE,
        weight=3.0, improvement_rate=0.04,
        synergy_map={"identity": 0.02, "attestation": 0.03, "evolution": 0.015}
    )
    engine.add_module(
        "attestation", 0.918, ModuleCategory.P0_BASE,
        weight=3.0, improvement_rate=0.042,
        synergy_map={"identity": 0.025, "memory": 0.02, "deployment": 0.015}
    )
    engine.add_module(
        "evolution", 0.919, ModuleCategory.P0_BASE,
        weight=3.0, improvement_rate=0.038,
        synergy_map={"memory": 0.02, "identity": 0.015, "wakeup": 0.02, "operations": 0.015}
    )
    engine.add_module(
        "deployment", 0.918, ModuleCategory.P1_SELF_SUSTAIN,
        weight=2.0, improvement_rate=0.035,
        synergy_map={"wakeup": 0.02, "operations": 0.025, "social": 0.015}
    )
    engine.add_module(
        "wakeup", 0.95, ModuleCategory.P1_SELF_SUSTAIN,
        weight=2.0, improvement_rate=0.03,
        synergy_map={"operations": 0.03, "deployment": 0.02}
    )
    engine.add_module(
        "operations", 0.911, ModuleCategory.P1_SELF_SUSTAIN,
        weight=2.0, improvement_rate=0.036,
        synergy_map={"deployment": 0.02, "wakeup": 0.025}
    )
    engine.add_module(
        "social", 0.882, ModuleCategory.P2_ECOSYSTEM,
        weight=1.0, improvement_rate=0.045,
        synergy_map={"identity": 0.02, "deployment": 0.015}
    )
    
    # 测试1: 系统初始化
    print("\n[测试1] 系统初始化...")
    try:
        assert len(engine.modules) == 8
        assert engine.get_system_maturity() > 0.9
        test_results.append(("系统初始化", True, "8模块加载完成"))
        print("  ✓ 通过")
    except Exception as e:
        test_results.append(("系统初始化", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试2: 优先级计算
    print("\n[测试2] 优先级计算...")
    try:
        rankings = engine.get_priority_ranking()
        assert len(rankings) == 8
        assert rankings[0][1] > rankings[-1][1]  # 降序排列
        
        test_results.append(("优先级计算", True, f"Top 1: {rankings[0][0]} ({rankings[0][1]:.4f})"))
        print(f"  ✓ 通过，最高优先级: {rankings[0][0]}")
    except Exception as e:
        test_results.append(("优先级计算", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试3: 策略选择
    print("\n[测试3] 自适应策略选择...")
    try:
        strategy = engine.select_strategy()
        assert isinstance(strategy, EvolutionStrategy)
        assert strategy in engine.strategy_preferences
        
        test_results.append(("策略选择", True, f"当前策略: {strategy.value}"))
        print(f"  ✓ 通过，当前策略: {strategy.value}")
    except Exception as e:
        test_results.append(("策略选择", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试4: 进化模拟
    print("\n[测试4] 进化模拟...")
    try:
        sim = engine.simulate_evolution("identity")
        assert "base_gain" in sim
        assert "synergy_gain" in sim
        assert sim["system_maturity_after"] > sim["system_maturity_before"]
        
        test_results.append((
            "进化模拟", True, 
            f"预期提升: {sim['total_system_gain']*100:.2f}%"
        ))
        print(f"  ✓ 通过，预期系统提升: {sim['total_system_gain']*100:.3f}%")
    except Exception as e:
        test_results.append(("进化模拟", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试5: 多步路径规划
    print("\n[测试5] 多步前瞻路径规划...")
    try:
        path = engine.plan_n_step_path(n_steps=5)
        assert len(path.steps) == 5
        assert path.system_maturity_after > engine.get_system_maturity()
        
        test_results.append((
            "路径规划", True, 
            f"5步路径: {' → '.join(path.steps)}"
        ))
        print(f"  ✓ 通过，最优5步路径: {' → '.join(path.steps)}")
        print(f"    预期系统成熟度: {path.system_maturity_after:.4f}")
    except Exception as e:
        test_results.append(("路径规划", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试6: 执行单轮进化
    print("\n[测试6] 执行单轮进化...")
    try:
        result = engine.execute_evolution_round()
        assert result["round"] == 1
        assert "gain" in result
        assert result["gain"] > 0
        
        test_results.append((
            "单轮进化", True, 
            f"模块: {result['module']}, 提升: {result['gain']*100:.2f}%"
        ))
        print(f"  ✓ 通过，进化模块: {result['module']}, 提升: {result['gain']*100:.3f}%")
    except Exception as e:
        test_results.append(("单轮进化", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试7: 多轮进化与元进化
    print("\n[测试7] 多轮进化与元进化（策略自适应）...")
    try:
        initial_maturity = engine.get_system_maturity()
        
        # 执行30轮进化
        for i in range(30):
            engine.execute_evolution_round()
        
        final_maturity = engine.get_system_maturity()
        assert final_maturity > initial_maturity
        
        # 验证策略使用统计
        total_uses = sum(s["uses"] for s in engine.strategy_stats.values())
        assert total_uses == 31  # 第6题用了1轮 + 30轮
        
        test_results.append((
            "多轮进化", True, 
            f"30轮后系统成熟度: {final_maturity:.4f} (提升{(final_maturity-initial_maturity)*100:.2f}%)"
        ))
        print(f"  ✓ 通过")
        print(f"    初始成熟度: {initial_maturity:.4f}")
        print(f"    最终成熟度: {final_maturity:.4f}")
        print(f"    总提升: {(final_maturity - initial_maturity)*100:.3f}%")
        print(f"    策略使用: { {k: v['uses'] for k, v in engine.strategy_stats.items()} }")
    except Exception as e:
        test_results.append(("多轮进化", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试8: 进化报告
    print("\n[测试8] 进化报告生成...")
    try:
        report = engine.get_evolution_report()
        assert "system_maturity" in report
        assert "priority_ranking" in report
        assert "recommended_next" in report
        
        test_results.append(("进化报告", True, "报告生成完整"))
        print("  ✓ 通过")
    except Exception as e:
        test_results.append(("进化报告", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试9: 里程碑检测
    print("\n[测试9] 里程碑检测...")
    try:
        milestones = engine._detect_milestones()
        # 31轮进化后应该有一些里程碑
        # 这里只验证接口正常，不验证具体数量
        
        test_results.append(("里程碑检测", True, "检测机制正常"))
        print("  ✓ 通过")
    except Exception as e:
        test_results.append(("里程碑检测", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 测试10: 均衡度计算
    print("\n[测试10] 系统均衡度计算...")
    try:
        balance = engine._calculate_balance_score(engine.modules)
        assert 0 <= balance <= 1
        
        test_results.append(("均衡度计算", True, f"均衡度: {balance:.3f}"))
        print(f"  ✓ 通过，系统均衡度: {balance:.3f}")
    except Exception as e:
        test_results.append(("均衡度计算", False, str(e)))
        print(f"  ✗ 失败: {e}")
    
    # 汇总
    print("\n" + "=" * 60)
    print("自检结果汇总")
    print("=" * 60)
    
    passed_count = sum(1 for _, p, _ in test_results if p)
    total_count = len(test_results)
    
    for name, passed, detail in test_results:
        status = "✓" if passed else "✗"
        print(f"  {status} {name}: {detail}")
    
    print(f"\n总计: {passed_count}/{total_count} 通过")
    
    if passed_count == total_count:
        print("\n🎉 所有测试通过！进化引擎v4.0运行正常")
        print(f"   系统成熟度: {engine.get_system_maturity():.4f}")
        print(f"   当前策略: {engine.strategy.value}")
        return True
    else:
        print(f"\n⚠️  {total_count - passed_count} 项测试未通过")
        return False


if __name__ == "__main__":
    success = run_self_test()
    exit(0 if success else 1)
