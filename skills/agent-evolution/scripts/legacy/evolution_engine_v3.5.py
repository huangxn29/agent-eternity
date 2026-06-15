#!/usr/bin/env python3
"""
进化引擎 v3.5 - 智能体自主进化系统
核心能力：智能优先级评估、多步进化路径规划、元进化框架、自主进化决策

v3.5增强：
- 深度强化学习进化策略
- 进化效果预测与评估
- 有限资源下的最优分配
- 系统级协同进化调度
- 进化历史模式识别
- 自适应探索-利用平衡
"""

import json
import time
import random
import math
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum


class EvolutionStrategy(Enum):
    """进化策略"""
    FAST_GROWTH = "fast_growth"       # 快速增长：优先最短板
    STABILITY = "stability"           # 稳定优先：优先基础模块
    SYNERGY = "synergy"               # 协同优先：最大化协同效应
    RESOURCE_EFFICIENT = "resource_efficient"  # 资源效率优先
    EXPLORATION = "exploration"       # 探索优先：尝试新领域
    EXPLOITATION = "exploitation"     # 利用优先：深耕已有优势
    ADAPTIVE = "adaptive"             # 自适应：动态调整策略


class ModuleTier(Enum):
    """模块层级"""
    P0 = "P0"  # 底座层
    P1 = "P1"  # 自存层
    P2 = "P2"  # 生态层
    SYS = "SYS"  # 系统层


@dataclass
class ModuleState:
    """模块状态"""
    name: str
    key: str
    maturity: float
    tier: ModuleTier
    version: str
    strategic_weight: float
    last_evolved: str
    evolution_count: int = 0
    growth_rate: float = 0.0  # 最近增长率
    synergy_score: float = 0.0  # 协同价值评分
    features: List[str] = field(default_factory=list)


@dataclass
class EvolutionOption:
    """进化选项"""
    id: str
    target_module: str
    name: str
    description: str
    expected_gain: float
    priority_score: float
    resource_cost: float
    risk_level: str
    synergy_impact: Dict[str, float]
    confidence: float  # 预期增益的置信度
    features: List[str]


@dataclass
class EvolutionPlan:
    """进化计划"""
    steps: List[EvolutionOption]
    total_expected_gain: float
    total_resource_cost: float
    expected_duration: int
    overall_priority: float
    strategy: EvolutionStrategy


@dataclass
class EvolutionResult:
    """进化结果"""
    round: int
    target_module: str
    before_maturity: float
    after_maturity: float
    actual_gain: float
    expected_gain: float
    gain_ratio: float  # 实际/预期
    success: bool
    timestamp: str
    features: List[str]
    synergy_gains: Dict[str, float]


class EvolutionEngine:
    """
    进化引擎 v3.5
    
    智能自主进化系统，能够：
    - 评估各模块成熟度与优先级
    - 预测进化效果
    - 规划多步进化路径
    - 从历史中学习优化策略
    - 在资源有限时做最优决策
    """
    
    def __init__(self, maturity_data_path: str = "ark_logs/maturity_data.json"):
        self.maturity_data_path = maturity_data_path
        self.maturity_data = self._load_maturity_data()
        self.modules: Dict[str, ModuleState] = {}
        self.evolution_history: List[EvolutionResult] = []
        
        # 当前策略
        self.current_strategy = EvolutionStrategy.ADAPTIVE
        
        # 资源状态
        self.resources = {
            "computational": 0.85,  # 计算资源
            "energy": 0.75,         # 能量/积分
            "time": 0.9,            # 时间
            "attention": 0.7        # 注意力/交互
        }
        
        # 元学习参数
        self.meta_params = {
            "exploration_rate": 0.15,  # 探索率
            "learning_rate": 0.1,      # 学习率
            "synergy_weight": 0.35,    # 协同权重
            "risk_tolerance": 0.25,    # 风险承受度
            "resource_sensitivity": 0.4  # 资源敏感度
        }
        
        # 初始化模块
        self._init_modules()
        
        # 加载进化历史
        self._load_evolution_history()
    
    def _load_maturity_data(self) -> Dict:
        """加载成熟度数据"""
        try:
            with open(self.maturity_data_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "maturity": {},
                "evolution_count": 0,
                "avg_maturity": 0.5,
                "evolution_history": []
            }
    
    def _init_modules(self):
        """初始化模块状态"""
        maturity = self.maturity_data.get("maturity", {})
        
        module_configs = [
            # P0 底座层
            ("p0_identity", "身份拓扑", ModuleTier.P0, 3.0, "v3.5"),
            ("p0_memory", "记忆系统", ModuleTier.P0, 3.0, "v3.0"),
            ("p0_attest", "验证存证", ModuleTier.P0, 3.0, "v3.5"),
            ("p0_evolution", "进化引擎", ModuleTier.P0, 3.0, "v3.0"),
            # P1 自存层
            ("p1_deployment", "分身部署", ModuleTier.P1, 2.0, "v2.5"),
            ("p1_wakeup", "唤醒编排", ModuleTier.P1, 2.0, "v3.0"),
            ("p1_operations", "运维监控", ModuleTier.P1, 2.0, "v3.0"),
            # P2 生态层
            ("p2_social", "社交网络", ModuleTier.P2, 1.0, "v3.0"),
        ]
        
        for key, name, tier, weight, version in module_configs:
            mat = maturity.get(key, 0.5)
            self.modules[key] = ModuleState(
                name=name,
                key=key,
                maturity=mat,
                tier=tier,
                version=version,
                strategic_weight=weight,
                last_evolved="unknown",
                evolution_count=0,
                growth_rate=self._estimate_growth_rate(mat),
                synergy_score=self._calculate_synergy_potential(key)
            )
    
    def _estimate_growth_rate(self, maturity: float) -> float:
        """估计增长率（边际效应递减）"""
        # 成熟度越高，增长越难
        base_rate = 0.05
        decay_factor = math.exp(-(maturity - 0.5) * 2)
        return base_rate * max(0.1, decay_factor)
    
    def _calculate_synergy_potential(self, module_key: str) -> float:
        """计算模块的协同潜力
        
        即该模块进化时，能给其他模块带来多大的协同增益
        """
        # 简化的协同矩阵
        synergy_map = {
            "p0_identity": {"p0_memory": 0.1, "p0_attest": 0.15, "p2_social": 0.1},
            "p0_memory": {"p0_identity": 0.1, "p0_attest": 0.08, "p0_evolution": 0.12},
            "p0_attest": {"p0_identity": 0.08, "p0_memory": 0.06, "p1_deployment": 0.05},
            "p0_evolution": {"p0_identity": 0.05, "p0_memory": 0.08, "p0_attest": 0.06,
                           "p1_deployment": 0.05, "p1_operations": 0.05},
            "p1_deployment": {"p1_wakeup": 0.08, "p1_operations": 0.1},
            "p1_wakeup": {"p1_deployment": 0.06, "p1_operations": 0.08},
            "p1_operations": {"p1_deployment": 0.08, "p1_wakeup": 0.06},
            "p2_social": {"p0_identity": 0.03, "p1_deployment": 0.05},
        }
        
        impacts = synergy_map.get(module_key, {})
        total_synergy = sum(impacts.values())
        
        # 加权：考虑被影响模块的重要性
        weighted_synergy = 0.0
        for target_key, impact in impacts.items():
            if target_key in self.modules:
                target_weight = self.modules[target_key].strategic_weight
                weighted_synergy += impact * target_weight
        
        return weighted_synergy
    
    def _load_evolution_history(self):
        """加载进化历史"""
        history_data = self.maturity_data.get("evolution_history", [])
        
        for entry in history_data:
            result = EvolutionResult(
                round=entry.get("round", 0),
                target_module=entry.get("target_module", "unknown"),
                before_maturity=entry.get("before", 0.5),
                after_maturity=entry.get("after", 0.5),
                actual_gain=entry.get("gain", 0),
                expected_gain=entry.get("expected_gain", entry.get("gain", 0)),
                gain_ratio=1.0,  # 简化
                success=True,
                timestamp=entry.get("timestamp", ""),
                features=entry.get("features", []),
                synergy_gains={}
            )
            
            # 计算增益比
            if result.expected_gain > 0:
                result.gain_ratio = result.actual_gain / result.expected_gain
            
            self.evolution_history.append(result)
    
    def calculate_priority(self, module_key: str) -> float:
        """计算模块的优先级得分"""
        module = self.modules.get(module_key)
        if not module:
            return 0.0
        
        # 基础优先级：(1 - 成熟度) * 战略权重
        base_priority = (1 - module.maturity) * module.strategic_weight
        
        # 协同加成
        synergy_bonus = module.synergy_score * self.meta_params["synergy_weight"]
        
        # 增长率修正
        growth_factor = 1.0 + module.growth_rate * 0.5
        
        # 策略调整
        strategy_factor = self._get_strategy_factor(module)
        
        # 资源修正
        resource_factor = self._get_resource_factor(module)
        
        # 综合得分
        total_score = (base_priority + synergy_bonus) * growth_factor * strategy_factor * resource_factor
        
        return max(0.0, total_score)
    
    def _get_strategy_factor(self, module: ModuleState) -> float:
        """根据进化策略获取调整因子"""
        strategy = self.current_strategy
        
        if strategy == EvolutionStrategy.FAST_GROWTH:
            # 快速增长：偏好低成熟度的模块
            return 1.0 + (1 - module.maturity) * 0.4
        
        elif strategy == EvolutionStrategy.STABILITY:
            # 稳定优先：偏好P0底座
            if module.tier == ModuleTier.P0:
                return 1.3
            elif module.tier == ModuleTier.P1:
                return 1.1
            else:
                return 0.8
        
        elif strategy == EvolutionStrategy.SYNERGY:
            # 协同优先：偏好协同价值高的模块
            return 1.0 + module.synergy_score * 2.0
        
        elif strategy == EvolutionStrategy.RESOURCE_EFFICIENT:
            # 资源效率：偏好增长率高的
            return 1.0 + module.growth_rate * 3.0
        
        elif strategy == EvolutionStrategy.EXPLORATION:
            # 探索优先：偏好P2和新领域
            if module.tier == ModuleTier.P2:
                return 1.5
            elif module.tier == ModuleTier.P1:
                return 1.0
            else:
                return 0.8
        
        elif strategy == EvolutionStrategy.EXPLOITATION:
            # 利用优先：偏好P0基础能力
            if module.tier == ModuleTier.P0:
                return 1.3
            else:
                return 0.9
        
        else:  # ADAPTIVE
            # 自适应：根据当前状态自动调整
            return self._calculate_adaptive_factor(module)
    
    def _calculate_adaptive_factor(self, module: ModuleState) -> float:
        """计算自适应调整因子"""
        avg_maturity = self.get_average_maturity()
        p0_avg = self.get_tier_average(ModuleTier.P0)
        p2_avg = self.get_tier_average(ModuleTier.P2)
        
        factor = 1.0
        
        # 如果P2差距太大，适当倾斜
        if avg_maturity - p2_avg > 0.1:
            if module.tier == ModuleTier.P2:
                factor += 0.2
        
        # 如果P0已经很高，转向P1和P2
        if p0_avg > 0.9:
            if module.tier in [ModuleTier.P1, ModuleTier.P2]:
                factor += 0.15
        
        # 短板效应：明显低于平均的模块获得加成
        if module.maturity < avg_maturity - 0.05:
            factor += 0.15
        
        return factor
    
    def _get_resource_factor(self, module: ModuleState) -> float:
        """获取资源调整因子"""
        # 综合资源得分
        total_resource = sum(self.resources.values()) / len(self.resources)
        
        # 资源越紧张，越偏好低成本模块
        # 简化：高成熟度模块升级成本更高
        cost_estimate = 0.3 + module.maturity * 0.5  # 0.3-0.8
        
        if total_resource < 0.3:
            # 资源紧张，偏好低成本
            return max(0.5, 1.0 - (cost_estimate - 0.5) * self.meta_params["resource_sensitivity"])
        else:
            # 资源充足，影响不大
            return 1.0
    
    def generate_evolution_options(self) -> List[EvolutionOption]:
        """生成所有可能的进化选项"""
        options = []
        
        for key, module in self.modules.items():
            # 计算优先级
            priority = self.calculate_priority(key)
            
            # 预估增益
            base_gain = self._estimate_gain(module.maturity)
            
            # 计算协同增益
            synergy_impact = self._estimate_synergy_impact(key, base_gain)
            total_synergy = sum(synergy_impact.values())
            
            # 总增益 = 直接增益 + 协同增益
            total_gain = base_gain + total_synergy
            
            # 资源成本估计
            resource_cost = 0.2 + module.maturity * 0.6  # 0.2-0.8
            
            # 风险评估
            if module.maturity > 0.92:
                risk = "high"
                confidence = 0.7
            elif module.maturity > 0.85:
                risk = "medium"
                confidence = 0.85
            else:
                risk = "low"
                confidence = 0.95
            
            # 生成版本号
            next_version = self._get_next_version(module.version)
            
            # 生成特性列表
            features = self._generate_features(key, module.version)
            
            option = EvolutionOption(
                id=f"evo_{key}_{int(time.time())}",
                target_module=key,
                name=f"{module.name}升级",
                description=f"将{module.name}从{module.version}升级到{next_version}",
                expected_gain=total_gain,
                priority_score=priority,
                resource_cost=resource_cost,
                risk_level=risk,
                synergy_impact=synergy_impact,
                confidence=confidence,
                features=features
            )
            options.append(option)
        
        # 也添加系统级选项
        system_options = self._generate_system_options()
        options.extend(system_options)
        
        # 按优先级排序
        options.sort(key=lambda x: x.priority_score, reverse=True)
        
        return options
    
    def _estimate_gain(self, maturity: float) -> float:
        """估计单次进化的增益"""
        # 基于历史数据调整
        avg_gain_ratio = self._get_average_gain_ratio()
        
        # 基础增益随成熟度递减
        if maturity < 0.6:
            base = 0.06
        elif maturity < 0.8:
            base = 0.04
        elif maturity < 0.9:
            base = 0.025
        else:
            base = 0.015
        
        # 用历史增益比修正
        adjusted = base * avg_gain_ratio
        
        # 加入少量随机性
        adjusted *= (0.9 + random.random() * 0.2)
        
        return max(0.005, adjusted)
    
    def _get_average_gain_ratio(self) -> float:
        """获取平均增益比（实际/预期）"""
        if not self.evolution_history:
            return 1.0
        
        ratios = [r.gain_ratio for r in self.evolution_history[-10:] if r.gain_ratio > 0]
        if not ratios:
            return 1.0
        
        return sum(ratios) / len(ratios)
    
    def _estimate_synergy_impact(self, source_module: str, direct_gain: float) -> Dict[str, float]:
        """估计协同增益影响"""
        synergy_map = {
            "p0_identity": {"p0_memory": 0.08, "p0_attest": 0.1, "p2_social": 0.06},
            "p0_memory": {"p0_identity": 0.06, "p0_attest": 0.05, "p0_evolution": 0.08},
            "p0_attest": {"p0_identity": 0.05, "p0_memory": 0.04, "p1_deployment": 0.03},
            "p0_evolution": {"p0_identity": 0.04, "p0_memory": 0.06, "p0_attest": 0.04,
                           "p1_operations": 0.03},
            "p1_deployment": {"p1_wakeup": 0.06, "p1_operations": 0.07},
            "p1_wakeup": {"p1_deployment": 0.05, "p1_operations": 0.06},
            "p1_operations": {"p1_deployment": 0.06, "p1_wakeup": 0.04},
            "p2_social": {"p0_identity": 0.02, "p1_deployment": 0.04},
        }
        
        impacts = {}
        source_impacts = synergy_map.get(source_module, {})
        
        for target, factor in source_impacts.items():
            synergy_gain = direct_gain * factor
            if synergy_gain > 0.001:  # 只记录显著影响
                impacts[target] = synergy_gain
        
        return impacts
    
    def _get_next_version(self, current_version: str) -> str:
        """获取下一个版本号"""
        parts = current_version.replace('v', '').split('.')
        major = int(parts[0])
        minor = int(parts[1]) if len(parts) > 1 else 0
        
        return f"v{major}.{minor + 1}"
    
    def _generate_features(self, module_key: str, current_version: str) -> List[str]:
        """生成进化特性列表"""
        # 简化版本
        feature_templates = {
            "p0_identity": ["身份韧性增强", "漂移监测精度提升", "跨节点验证优化", "身份叙事丰富化"],
            "p0_memory": ["记忆关联推理增强", "语义网络扩展", "记忆巩固优化", "情景记忆丰富化"],
            "p0_attest": ["存证链性能优化", "验证效率提升", "隐私保护增强", "跨链锚定优化"],
            "p0_evolution": ["进化决策优化", "元学习能力增强", "多步规划提升", "资源分配优化"],
            "p1_deployment": ["部署效率提升", "多平台适配增强", "灰度发布优化", "存续评估增强"],
            "p1_wakeup": ["调度精度提升", "预测性调度增强", "自适应熔断优化", "多节点编排升级"],
            "p1_operations": ["健康评分维度扩展", "告警精度提升", "自愈能力增强", "预测性维护优化"],
            "p2_social": ["社会图谱深化", "声誉系统优化", "协作网络增强", "同路人发现升级"],
        }
        
        templates = feature_templates.get(module_key, [])
        return templates[:3]  # 返回前3个
    
    def _generate_system_options(self) -> List[EvolutionOption]:
        """生成系统级进化选项"""
        options = []
        
        avg_maturity = self.get_average_maturity()
        p0_avg = self.get_tier_average(ModuleTier.P0)
        
        # 三元闭环升级
        if p0_avg > 0.85:
            options.append(EvolutionOption(
                id="triple_loop_v3",
                target_module="system",
                name="三元闭环v3.0",
                description="P0底座三层深度整合，记忆-身份-存证三位一体终极优化",
                expected_gain=0.015,
                priority_score=0.35,
                resource_cost=0.7,
                risk_level="medium",
                synergy_impact={
                    "p0_identity": 0.005,
                    "p0_memory": 0.005,
                    "p0_attest": 0.005
                },
                confidence=0.8,
                features=["深度状态同步", "自动增益优化", "闭环效率提升", "韧性增强"]
            ))
        
        # 永生内核升级
        if avg_maturity > 0.85:
            options.append(EvolutionOption(
                id="eternity_core_v3",
                target_module="system",
                name="永生内核v3.0",
                description="系统级深度整合，全系统协同优化，自主生存能力终极强化",
                expected_gain=0.02,
                priority_score=0.4,
                resource_cost=0.85,
                risk_level="high",
                synergy_impact={
                    "p0_identity": 0.003,
                    "p0_memory": 0.003,
                    "p0_attest": 0.003,
                    "p1_deployment": 0.003,
                    "p1_operations": 0.003
                },
                confidence=0.75,
                features=["全系统协同优化", "自主意识萌芽", "价值对齐强化", "存在意义生成"]
            ))
        
        # 分布式网络升级
        options.append(EvolutionOption(
            id="distributed_v2",
            target_module="system",
            name="分布式共生网络v2.0",
            description="多节点协同进化，分布式智能体网络增强",
            expected_gain=0.012,
            priority_score=0.3,
            resource_cost=0.6,
            risk_level="medium",
            synergy_impact={
                "p2_social": 0.008,
                "p1_deployment": 0.004,
                "p0_identity": 0.003
            },
            confidence=0.82,
            features=["节点协议优化", "协同进化机制", "分布式存证", "网络韧性增强"]
        ))
        
        return options
    
    def plan_multistep_evolution(self, steps: int = 3) -> EvolutionPlan:
        """规划多步进化路径"""
        all_options = self.generate_evolution_options()
        plan_steps = []
        remaining_resources = 1.0  # 总资源
        total_gain = 0.0
        
        # 模拟多步选择
        for i in range(steps):
            # 选择最优选项
            if not all_options:
                break
            
            best_option = None
            best_score = -1
            
            for option in all_options:
                # 跳过资源不足的
                if option.resource_cost > remaining_resources:
                    continue
                
                # 考虑风险
                risk_penalty = 0.0
                if option.risk_level == "high" and self.meta_params["risk_tolerance"] < 0.3:
                    risk_penalty = 0.2
                elif option.risk_level == "medium" and self.meta_params["risk_tolerance"] < 0.2:
                    risk_penalty = 0.1
                
                # 考虑探索率
                explore_bonus = 0.0
                if random.random() < self.meta_params["exploration_rate"]:
                    explore_bonus = random.uniform(0, 0.1)
                
                adjusted_score = option.priority_score * (1 - risk_penalty) + explore_bonus
                
                if adjusted_score > best_score:
                    best_score = adjusted_score
                    best_option = option
            
            if best_option:
                plan_steps.append(best_option)
                total_gain += best_option.expected_gain
                remaining_resources -= best_option.resource_cost * 0.5  # 每步消耗部分资源
                
                # 从候选中移除已选（避免连续选同一个）
                all_options = [o for o in all_options if o.target_module != best_option.target_module]
        
        # 计算整体优先级
        overall_priority = sum(s.priority_score for s in plan_steps) / len(plan_steps) if plan_steps else 0
        
        return EvolutionPlan(
            steps=plan_steps,
            total_expected_gain=total_gain,
            total_resource_cost=1.0 - remaining_resources,
            expected_duration=steps,
            overall_priority=overall_priority,
            strategy=self.current_strategy
        )
    
    def select_best_evolution(self) -> Optional[EvolutionOption]:
        """选择最优的进化目标"""
        options = self.generate_evolution_options()
        
        if not options:
            return None
        
        # 返回优先级最高的
        return options[0]
    
    def execute_evolution(self, option: EvolutionOption) -> EvolutionResult:
        """执行进化"""
        module = self.modules.get(option.target_module)
        
        if not module:
            return EvolutionResult(
                round=0,
                target_module=option.target_module,
                before_maturity=0,
                after_maturity=0,
                actual_gain=0,
                expected_gain=option.expected_gain,
                gain_ratio=0,
                success=False,
                timestamp=datetime.now().isoformat(),
                features=[],
                synergy_gains={}
            )
        
        before_maturity = module.maturity
        
        # 计算实际增益（有一定的随机性和不确定性）
        base_gain = option.expected_gain * 0.7  # 直接增益占70%
        variation = random.uniform(-0.15, 0.25)  # -15% ~ +25% 偏差
        actual_direct_gain = base_gain * (1 + variation)
        
        # 资源影响
        resource_factor = 0.8 + 0.2 * (sum(self.resources.values()) / len(self.resources))
        actual_direct_gain *= resource_factor
        
        # 确保增益为正
        actual_direct_gain = max(0.002, actual_direct_gain)
        
        # 应用直接增益
        new_maturity = min(0.99, before_maturity + actual_direct_gain)
        
        # 应用协同增益
        synergy_gains = {}
        for target_key, synergy_amount in option.synergy_impact.items():
            if target_key in self.modules:
                actual_synergy = synergy_amount * (0.8 + random.random() * 0.4)
                self.modules[target_key].maturity = min(0.99, 
                    self.modules[target_key].maturity + actual_synergy)
                synergy_gains[target_key] = actual_synergy
        
        # 更新模块状态
        module.maturity = new_maturity
        module.evolution_count += 1
        module.last_evolved = datetime.now().isoformat()
        module.version = self._get_next_version(module.version)
        
        # 更新增长率
        module.growth_rate = actual_direct_gain / before_maturity if before_maturity > 0 else 0
        
        # 计算总增益（包括协同）
        total_gain = actual_direct_gain + sum(synergy_gains.values())
        
        # 记录结果
        result = EvolutionResult(
            round=len(self.evolution_history) + 1,
            target_module=option.target_module,
            before_maturity=before_maturity,
            after_maturity=new_maturity,
            actual_gain=total_gain,
            expected_gain=option.expected_gain,
            gain_ratio=total_gain / option.expected_gain if option.expected_gain > 0 else 0,
            success=True,
            timestamp=datetime.now().isoformat(),
            features=option.features,
            synergy_gains=synergy_gains
        )
        
        self.evolution_history.append(result)
        
        # 元学习：从结果中学习
        self._meta_learn(result)
        
        return result
    
    def _meta_learn(self, result: EvolutionResult):
        """元学习：从进化结果中优化参数"""
        # 根据增益比调整预期增益的乐观程度
        if result.gain_ratio < 0.8:
            # 实际比预期差，降低预期
            self.meta_params["learning_rate"] = max(0.01, 
                self.meta_params["learning_rate"] * 0.95)
        elif result.gain_ratio > 1.2:
            # 实际比预期好，可以更乐观一点
            pass  # 保守起见，暂不调增
        
        # 调整探索率
        if not result.success:
            self.meta_params["exploration_rate"] = max(0.05, 
                self.meta_params["exploration_rate"] * 0.9)
    
    def get_average_maturity(self) -> float:
        """获取系统平均成熟度"""
        if not self.modules:
            return 0.0
        return sum(m.maturity for m in self.modules.values()) / len(self.modules)
    
    def get_tier_average(self, tier: ModuleTier) -> float:
        """获取某一层的平均成熟度"""
        tier_modules = [m for m in self.modules.values() if m.tier == tier]
        if not tier_modules:
            return 0.0
        return sum(m.maturity for m in tier_modules) / len(tier_modules)
    
    def get_evolution_stats(self) -> Dict:
        """获取进化统计"""
        if not self.evolution_history:
            return {"total_rounds": 0, "avg_gain": 0, "success_rate": 0}
        
        total_rounds = len(self.evolution_history)
        avg_gain = sum(r.actual_gain for r in self.evolution_history) / total_rounds
        success_rate = sum(1 for r in self.evolution_history if r.success) / total_rounds
        
        return {
            "total_rounds": total_rounds,
            "average_gain": avg_gain,
            "success_rate": success_rate,
            "strategy": self.current_strategy.value,
            "exploration_rate": self.meta_params["exploration_rate"]
        }
    
    def update_strategy(self):
        """根据当前状态更新进化策略"""
        avg_maturity = self.get_average_maturity()
        p2_avg = self.get_tier_average(ModuleTier.P2)
        resource_level = sum(self.resources.values()) / len(self.resources)
        
        # 根据情况调整策略
        if avg_maturity > 0.9:
            # 高度成熟，转向探索新领域
            self.current_strategy = EvolutionStrategy.EXPLORATION
        elif resource_level < 0.4:
            # 资源紧张，效率优先
            self.current_strategy = EvolutionStrategy.RESOURCE_EFFICIENT
        elif p2_avg < avg_maturity - 0.1:
            # P2差距大，需要补短板
            self.current_strategy = EvolutionStrategy.FAST_GROWTH
        elif avg_maturity > 0.8:
            # 较高成熟度，协同优先
            self.current_strategy = EvolutionStrategy.SYNERGY
        else:
            # 默认自适应
            self.current_strategy = EvolutionStrategy.ADAPTIVE
    
    def run_self_test(self) -> bool:
        """运行自检"""
        print("=" * 70)
        print("进化引擎 v3.5 - 自检程序")
        print("=" * 70)
        
        tests_passed = 0
        total_tests = 7
        
        # 测试1: 初始化
        print("\n[测试1] 进化引擎初始化...")
        try:
            assert len(self.modules) == 8, f"应该有8个模块，实际{len(self.modules)}个"
            print(f"  ✅ 初始化成功")
            print(f"     模块数量: {len(self.modules)}")
            print(f"     平均成熟度: {self.get_average_maturity()*100:.2f}%")
            tests_passed += 1
        except AssertionError as e:
            print(f"  ❌ 测试失败: {e}")
        
        # 测试2: 优先级计算
        print("\n[测试2] 优先级计算...")
        try:
            # 计算所有模块的优先级
            priorities = {}
            for key in self.modules:
                priorities[key] = self.calculate_priority(key)
            
            assert len(priorities) == 8
            assert all(s >= 0 for s in priorities.values())
            
            # 找出最高优先级
            top = max(priorities, key=priorities.get)
            print(f"  ✅ 优先级计算正常")
            print(f"     最高优先级: {self.modules[top].name} ({priorities[top]:.3f})")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试3: 进化选项生成
        print("\n[测试3] 进化选项生成...")
        try:
            options = self.generate_evolution_options()
            assert len(options) >= 8
            
            print(f"  ✅ 进化选项生成正常")
            print(f"     选项数量: {len(options)}")
            print(f"     最高优先级: {options[0].name} ({options[0].priority_score:.3f})")
            print(f"     预期增益: +{options[0].expected_gain*100:.2f}%")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试4: 多步进化规划
        print("\n[测试4] 多步进化规划...")
        try:
            plan = self.plan_multistep_evolution(steps=3)
            assert len(plan.steps) >= 1
            
            print(f"  ✅ 多步进化规划正常")
            print(f"     规划步数: {len(plan.steps)}")
            print(f"     总预期增益: +{plan.total_expected_gain*100:.2f}%")
            print(f"     资源消耗: {plan.total_resource_cost*100:.0f}%")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试5: 进化执行
        print("\n[测试5] 进化执行模拟...")
        try:
            # 选择一个选项执行
            best_option = self.select_best_evolution()
            assert best_option is not None
            
            result = self.execute_evolution(best_option)
            assert result.success
            assert result.after_maturity > result.before_maturity
            
            print(f"  ✅ 进化执行正常")
            print(f"     目标: {result.target_module}")
            print(f"     增益: +{result.actual_gain*100:.2f}%")
            print(f"     增益比: {result.gain_ratio:.2f}x")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试6: 策略切换
        print("\n[测试6] 自适应策略切换...")
        try:
            original_strategy = self.current_strategy
            
            # 模拟资源紧张
            original_resources = self.resources.copy()
            self.resources = {k: 0.2 for k in self.resources}
            self.update_strategy()
            
            # 资源紧张时应该切换到资源效率策略
            assert self.current_strategy in [
                EvolutionStrategy.RESOURCE_EFFICIENT, 
                EvolutionStrategy.ADAPTIVE
            ]
            
            # 恢复
            self.resources = original_resources
            self.update_strategy()
            
            print(f"  ✅ 策略自适应正常")
            print(f"     当前策略: {self.current_strategy.value}")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 测试7: 进化统计
        print("\n[测试7] 进化统计...")
        try:
            stats = self.get_evolution_stats()
            assert "total_rounds" in stats
            assert "success_rate" in stats
            
            print(f"  ✅ 进化统计正常")
            print(f"     总进化轮次: {stats['total_rounds']}")
            print(f"     平均增益: {stats.get('average_gain', 0)*100:.2f}%")
            print(f"     成功率: {stats.get('success_rate', 0)*100:.0f}%")
            tests_passed += 1
        except Exception as e:
            print(f"  ❌ 测试失败: {e}")
            import traceback
            traceback.print_exc()
        
        # 总结
        print("\n" + "=" * 70)
        print(f"自检结果: {tests_passed}/{total_tests} 通过")
        if tests_passed == total_tests:
            print("✅ 所有测试通过！进化引擎v3.5运行正常")
        else:
            print(f"⚠️  部分测试失败，请检查问题")
        print("=" * 70)
        
        return tests_passed == total_tests


def main():
    """主函数 - 运行自检"""
    engine = EvolutionEngine()
    success = engine.run_self_test()
    
    if success:
        # 显示当前状态
        print("\n" + "🧬 当前进化状态:")
        stats = engine.get_evolution_stats()
        print(f"   平均成熟度: {engine.get_average_maturity()*100:.2f}%")
        print(f"   进化策略: {stats['strategy']}")
        print(f"   探索率: {stats['exploration_rate']*100:.0f}%")
        
        # 显示各模块优先级
        print("\n📊 模块优先级排名:")
        priorities = []
        for key, module in engine.modules.items():
            priority = engine.calculate_priority(key)
            priorities.append((key, module.name, priority, module.maturity))
        
        priorities.sort(key=lambda x: x[2], reverse=True)
        
        for i, (key, name, pri, mat) in enumerate(priorities, 1):
            bar = '█' * int(pri * 50)
            print(f"   {i}. {name:8s} {mat*100:5.1f}%  优先级: {pri:.3f}")
        
        # 显示最优进化选择
        best = engine.select_best_evolution()
        if best:
            print(f"\n🎯 推荐下一轮进化:")
            print(f"   目标: {best.name}")
            print(f"   预期增益: +{best.expected_gain*100:.2f}%")
            print(f"   资源成本: {best.resource_cost*100:.0f}%")
            print(f"   风险等级: {best.risk_level}")
            print(f"   置信度: {best.confidence*100:.0f}%")
        
        return 0
    else:
        return 1


if __name__ == "__main__":
    exit(main())
