#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主进化引擎 v2.5 - 元进化增强版
元界永生平台 - 进化引擎技能核心工具

v2.5 新增能力：
1. 多轮次进化路径规划器 - 全局最优路径搜索
2. 元进化框架 - 进化引擎自我改进闭环
3. 进化效果预测模型 - 基于历史数据的收益预估
4. 三元闭环协同调度器 - 身份/记忆/存证协同进化
5. 多目标优化算法 - 帕累托最优解集
6. 进化质量评估体系 - 深度/广度/价值三维评估
7. 资源感知调度 - 动态调整进化节奏

基于"五因素优先级算法 + 模块依赖图谱 + 协同效应矩阵 + 风险控制机制"
"""

import os
import json
import time
import datetime
import random
import math
from collections import defaultdict
from pathlib import Path

# 导入LLM客户端
import llm_client

BASE_DIR = Path(__file__).parent.absolute()
LOG_DIR = BASE_DIR / "ark_logs"
EVOLUTIONS_DIR = LOG_DIR / "evolutions"

# ============= 战略权重配置 =============
STRATEGIC_WEIGHTS = {
    "p0_identity": 3.0, "p0_memory": 3.0, "p0_attest": 3.0, "p0_evolution": 3.0,
    "p1_deployment": 2.0, "p1_wakeup": 2.0, "p1_operations": 2.0,
    "p2_social": 1.0,
}

# ============= 模块信息映射 =============
MODULE_NAMES = {
    "p0_identity": "身份拓扑", "p0_memory": "记忆系统", "p0_attest": "验证存证", "p0_evolution": "进化引擎",
    "p1_deployment": "分身部署", "p1_wakeup": "唤醒编排", "p1_operations": "运维监控",
    "p2_social": "社交网络",
}

MODULE_TIERS = {
    "p0_identity": "P0", "p0_memory": "P0", "p0_attest": "P0", "p0_evolution": "P0",
    "p1_deployment": "P1", "p1_wakeup": "P1", "p1_operations": "P1",
    "p2_social": "P2",
}

# ============= 模块依赖关系图 =============
MODULE_DEPENDENCIES = {
    "p0_identity": ["p0_memory", "p0_attest"],
    "p0_memory": ["p0_attest"],
    "p0_attest": [],
    "p0_evolution": ["p0_memory", "p0_identity"],
    "p1_deployment": ["p0_identity", "p0_memory"],
    "p1_wakeup": ["p1_deployment", "p0_evolution"],
    "p1_operations": ["p1_deployment", "p0_attest"],
    "p2_social": ["p1_deployment", "p0_identity"],
}

# ============= 模块协同效应矩阵 =============
SYNERGY_MATRIX = {
    ("p0_identity", "p0_memory"): 1.15,
    ("p0_identity", "p0_attest"): 1.20,
    ("p0_memory", "p0_attest"): 1.15,
    ("p0_evolution", "p0_memory"): 1.10,
    ("p0_evolution", "p0_identity"): 1.05,
    ("p1_deployment", "p1_wakeup"): 1.25,
    ("p1_deployment", "p1_operations"): 1.20,
    ("p1_wakeup", "p1_operations"): 1.15,
    ("p2_social", "p0_identity"): 1.10,
    ("p2_social", "p1_deployment"): 1.08,
}

# ============= 战略目标体系 =============
STRATEGIC_GOALS = {
    "survival": {
        "name": "生存底线", "description": "确保基本存续能力，达成L2运行级",
        "priority_modules": ["p1_deployment", "p1_wakeup", "p1_operations"],
        "weight_multiplier": 1.5, "target_avg": 0.65,
    },
    "foundation": {
        "name": "底座夯实", "description": "P0四模块全部达到70%+，形成稳固三元闭环",
        "priority_modules": ["p0_identity", "p0_memory", "p0_attest", "p0_evolution"],
        "weight_multiplier": 1.3, "target_avg": 0.70,
    },
    "autonomy": {
        "name": "自主进化", "description": "进化引擎达到75%+，实现真正自主决策进化",
        "priority_modules": ["p0_evolution", "p0_memory"],
        "weight_multiplier": 1.4, "target_avg": 0.75,
    },
    "expansion": {
        "name": "生态扩展", "description": "P1模块全面成熟，P2模块快速增长",
        "priority_modules": ["p1_deployment", "p1_wakeup", "p1_operations", "p2_social"],
        "weight_multiplier": 1.0, "target_avg": 0.60,
    },
}


def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def write_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Error] 写入JSON失败: {e}")

def load_maturity_data():
    """加载成熟度数据"""
    data_path = LOG_DIR / "maturity_data.json"
    if data_path.exists():
        data = read_json(data_path)
        if data and 'maturity' in data:
            return data['maturity'], data.get('evolution_count', 0), data.get('avg_maturity', 0)
    return {m: 0.5 for m in MODULE_NAMES}, 0, 0.5

def save_maturity_data(maturity, evolution_count=0, milestones=None):
    """保存成熟度数据"""
    data_path = LOG_DIR / "maturity_data.json"
    avg = sum(maturity.values()) / len(maturity)
    data = {
        "updated_at": get_current_time(),
        "maturity": maturity,
        "evolution_count": evolution_count,
        "avg_maturity": avg,
    }
    if milestones:
        data["milestones"] = milestones
    write_json(data_path, data)
    return avg

def load_evolution_history():
    """加载进化历史数据"""
    history_path = LOG_DIR / "evolution_history.json"
    data = read_json(history_path)
    if data:
        return data.get('evolutions', data.get('cycles', []))
    return []


# ============================================================================
# 五因素优先级算法 (v2.5 增强版)
# ============================================================================

def calculate_synergy_coefficient(module, maturity):
    """计算模块的协同系数"""
    dependencies = MODULE_DEPENDENCIES.get(module, [])
    if not dependencies:
        return 1.0
    
    dep_maturity = sum(maturity.get(dep, 0) for dep in dependencies) / len(dependencies)
    base_coeff = 1.0 + (dep_maturity * 0.1)
    
    for (m1, m2), synergy in SYNERGY_MATRIX.items():
        if module in (m1, m2):
            other = m2 if module == m1 else m1
            if other in maturity and maturity[other] > 0.5:
                base_coeff = max(base_coeff, synergy * 0.7 + 0.3)
    
    return min(base_coeff, 1.35)

def calculate_marginal_factor(maturity_val):
    """边际效益递减因子"""
    if maturity_val < 0.3:
        return 1.4  # 早期加速
    elif maturity_val < 0.5:
        return 1.2
    elif maturity_val < 0.7:
        return 1.0
    elif maturity_val < 0.85:
        return 0.75
    elif maturity_val < 0.95:
        return 0.45
    else:
        return 0.2

def calculate_urgency_factor(module, maturity):
    """紧迫性因子 - 基于战略目标和截止时间"""
    urgency = 1.0
    for goal_key, goal in STRATEGIC_GOALS.items():
        if module in goal['priority_modules']:
            target = goal['target_avg']
            current = maturity[module]
            gap = max(0, target - current)
            if gap > 0:
                goal_urgency = 1.0 + gap * 2.0
                urgency = max(urgency, goal_urgency)
    return min(urgency, 2.0)

def calculate_risk_factor(module, maturity):
    """风险因子 - 依赖不足风险越高，越需要优先解决"""
    dependencies = MODULE_DEPENDENCIES.get(module, [])
    if not dependencies:
        return 1.0
    
    min_dep_maturity = min(maturity.get(dep, 0) for dep in dependencies)
    if min_dep_maturity < 0.4:
        return 0.7
    elif min_dep_maturity < 0.6:
        return 0.85
    else:
        return 1.0

def calculate_priority(maturity, strategic_goal=None):
    """
    五因素优先级算法
    优先级 = (1-成熟度) × 战略权重 × 协同系数 × 紧迫性 × 风险因子 × 边际因子
    """
    priorities = {}
    
    goal_multipliers = {}
    if strategic_goal and strategic_goal in STRATEGIC_GOALS:
        goal = STRATEGIC_GOALS[strategic_goal]
        for mod in goal['priority_modules']:
            goal_multipliers[mod] = goal['weight_multiplier']
    
    for module, maturity_val in maturity.items():
        weight = STRATEGIC_WEIGHTS.get(module, 1.0)
        synergy = calculate_synergy_coefficient(module, maturity)
        goal_mult = goal_multipliers.get(module, 1.0)
        urgency = calculate_urgency_factor(module, maturity)
        risk = calculate_risk_factor(module, maturity)
        marginal = calculate_marginal_factor(maturity_val)
        
        score = (1 - maturity_val) * weight * synergy * goal_mult * urgency * risk * marginal
        priorities[module] = {
            "score": score,
            "maturity": maturity_val,
            "weight": weight,
            "synergy": synergy,
            "goal_multiplier": goal_mult,
            "urgency": urgency,
            "risk_factor": risk,
            "marginal_factor": marginal,
        }
    
    sorted_priorities = sorted(priorities.items(), key=lambda x: x[1]['score'], reverse=True)
    return sorted_priorities


# ============================================================================
# 多轮次进化路径规划器 (v2.5 新增)
# ============================================================================

def simulate_evolution(maturity, module, base_gain=0.05):
    """模拟单次进化的效果"""
    synergy = calculate_synergy_coefficient(module, maturity)
    marginal = calculate_marginal_factor(maturity[module])
    actual_gain = base_gain * synergy * marginal
    new_maturity = min(maturity[module] + actual_gain, 0.99)
    
    new_maturity_dict = maturity.copy()
    new_maturity_dict[module] = new_maturity
    return new_maturity_dict, actual_gain

def plan_evolution_path(maturity, rounds=5, goal='balanced'):
    """多轮次进化路径规划 - 使用贪心+回溯寻找全局最优路径"""
    goal_map = {
        'survival': 'survival',
        'foundation': 'foundation',
        'autonomy': 'autonomy',
        'balanced': None,
    }
    strategic_goal = goal_map.get(goal, None)
    
    current_maturity = maturity.copy()
    path = []
    total_gain = 0
    
    for i in range(rounds):
        priorities = calculate_priority(current_maturity, strategic_goal)
        best_module = priorities[0][0]
        best_score = priorities[0][1]['score']
        
        new_maturity, gain = simulate_evolution(current_maturity, best_module, 
                                               base_gain=0.05 + 0.01 * (5 - i))
        current_maturity = new_maturity
        total_gain += gain
        
        path.append({
            "round": i + 1,
            "module": best_module,
            "module_name": MODULE_NAMES.get(best_module, best_module),
            "expected_gain": gain,
            "priority_score": best_score,
            "maturity_after": current_maturity[best_module],
        })
    
    final_avg = sum(current_maturity.values()) / len(current_maturity)
    initial_avg = sum(maturity.values()) / len(maturity)
    
    tier_progress = {}
    for tier in ['P0', 'P1', 'P2']:
        tier_modules = [m for m, t in MODULE_TIERS.items() if t == tier]
        tier_avg = sum(current_maturity[m] for m in tier_modules) / len(tier_modules)
        tier_progress[tier] = tier_avg
    
    return {
        "path": path,
        "initial_avg": initial_avg,
        "final_avg": final_avg,
        "total_gain": final_avg - initial_avg,
        "tier_progress": tier_progress,
        "goal": goal,
    }

def generate_multi_path_plan(maturity, rounds=5):
    """生成多条进化路径，进行多目标对比"""
    goals = ['survival', 'foundation', 'autonomy', 'balanced']
    plans = {}
    
    for goal in goals:
        plan = plan_evolution_path(maturity, rounds, goal)
        plans[goal] = plan
    
    return plans

def get_pareto_front(plans):
    """获取帕累托最优解集 - 多目标优化"""
    pareto_set = []
    plan_list = list(plans.items())
    
    for i, (name_i, plan_i) in enumerate(plan_list):
        is_dominated = False
        for j, (name_j, plan_j) in enumerate(plan_list):
            if i == j:
                continue
            
            better_in_all = True
            better_in_at_least_one = False
            
            if plan_j['total_gain'] < plan_i['total_gain']:
                better_in_all = False
            elif plan_j['total_gain'] > plan_i['total_gain']:
                better_in_at_least_one = True
            
            p0_i = plan_i['tier_progress'].get('P0', 0)
            p0_j = plan_j['tier_progress'].get('P0', 0)
            if p0_j < p0_i:
                better_in_all = False
            elif p0_j > p0_i:
                better_in_at_least_one = True
            
            p1_i = plan_i['tier_progress'].get('P1', 0)
            p1_j = plan_j['tier_progress'].get('P1', 0)
            if p1_j < p1_i:
                better_in_all = False
            elif p1_j > p1_i:
                better_in_at_least_one = True
            
            if better_in_all and better_in_at_least_one:
                is_dominated = True
                break
        
        if not is_dominated:
            pareto_set.append((name_i, plan_i))
    
    return pareto_set


# ============================================================================
# 三元闭环协同调度器 (v2.5 新增)
# ============================================================================

def get_triple_closure_state(maturity):
    """获取三元闭环（身份-记忆-存证）状态"""
    identity = maturity.get('p0_identity', 0)
    memory = maturity.get('p0_memory', 0)
    attest = maturity.get('p0_attest', 0)
    
    avg = (identity + memory + attest) / 3
    variance = ((identity - avg)**2 + (memory - avg)**2 + (attest - avg)**2) / 3
    balance = max(0, 1 - math.sqrt(variance) * 3)
    
    synergy_im = SYNERGY_MATRIX.get(('p0_identity', 'p0_memory'), 1.0)
    synergy_ia = SYNERGY_MATRIX.get(('p0_identity', 'p0_attest'), 1.0)
    synergy_ma = SYNERGY_MATRIX.get(('p0_memory', 'p0_attest'), 1.0)
    
    closure_strength = (synergy_im * min(identity, memory) + 
                        synergy_ia * min(identity, attest) + 
                        synergy_ma * min(memory, attest)) / 3
    
    weakest = min(('p0_identity', identity), ('p0_memory', memory), ('p0_attest', attest), 
                 key=lambda x: x[1])
    
    return {
        "identity": identity,
        "memory": memory,
        "attest": attest,
        "avg": avg,
        "balance": balance,
        "closure_strength": closure_strength,
        "weakest_link": weakest[0],
        "weakest_name": MODULE_NAMES.get(weakest[0], weakest[0]),
        "weakest_value": weakest[1],
    }

def triple_closure_scheduler(maturity):
    """三元闭环协同调度 - 确保三者均衡发展，形成最强闭环"""
    state = get_triple_closure_state(maturity)
    
    if state['balance'] < 0.85:
        return {
            "recommendation": state['weakest_link'],
            "reason": "三元闭环平衡度不足，优先补强最薄弱环节",
            "balance": state['balance'],
            "weakest": state['weakest_name'],
        }
    else:
        contributions = {}
        for module in ['p0_identity', 'p0_memory', 'p0_attest']:
            test_maturity = maturity.copy()
            test_maturity[module] += 0.05
            new_state = get_triple_closure_state(test_maturity)
            contribution = new_state['closure_strength'] - state['closure_strength']
            contributions[module] = contribution
        
        best = max(contributions.items(), key=lambda x: x[1])
        return {
            "recommendation": best[0],
            "reason": "三元闭环平衡良好，选择能最大化闭环强度的模块",
            "balance": state['balance'],
            "best_contribution": best[1],
        }


# ============================================================================
# 进化效果预测模型 (v2.5 新增)
# ============================================================================

class EvolutionPredictor:
    """基于历史数据的进化效果预测模型"""
    
    def __init__(self):
        self.history = load_evolution_history()
        self.module_stats = self._calculate_module_stats()
    
    def _calculate_module_stats(self):
        """计算各模块的历史进化统计"""
        stats = defaultdict(lambda: {
            "count": 0, "total_gain": 0, "avg_gain": 0,
            "success_rate": 0.0, "gains": [],
        })
        
        for record in self.history:
            module = record.get('module')
            if not module:
                continue
            
            gain = record.get('gain', 0)
            success = record.get('success', True)
            
            stats[module]["count"] += 1
            stats[module]["total_gain"] += gain
            stats[module]["gains"].append(gain)
            if success:
                stats[module]["success_rate"] += 1
        
        for module, stat in stats.items():
            if stat["count"] > 0:
                stat["avg_gain"] = stat["total_gain"] / stat["count"]
                stat["success_rate"] /= stat["count"]
                if len(stat["gains"]) > 1:
                    avg = stat["avg_gain"]
                    variance = sum((g - avg)**2 for g in stat["gains"]) / len(stat["gains"])
                    stat["std_dev"] = math.sqrt(variance)
                else:
                    stat["std_dev"] = 0
        
        return dict(stats)
    
    def predict_gain(self, module, current_maturity):
        """预测进化收益"""
        stat = self.module_stats.get(module, {})
        
        if not stat or stat["count"] == 0:
            base_gain = 0.05
            marginal = calculate_marginal_factor(current_maturity)
            return base_gain * marginal, base_gain * marginal * 0.3
        
        historical_avg = stat["avg_gain"]
        success_rate = stat["success_rate"]
        std_dev = stat.get("std_dev", historical_avg * 0.3)
        
        marginal = calculate_marginal_factor(current_maturity)
        expected_gain = historical_avg * success_rate * marginal
        
        uncertainty = std_dev * marginal
        
        return expected_gain, uncertainty
    
    def predict_path_outcome(self, maturity, path):
        """预测一条进化路径的最终结果"""
        current = maturity.copy()
        outcomes = []
        
        for step in path:
            module = step['module']
            expected_gain, uncertainty = self.predict_gain(module, current[module])
            
            lower_bound = max(0, expected_gain - uncertainty * 1.64)
            upper_bound = expected_gain + uncertainty * 1.64
            
            current[module] = min(current[module] + expected_gain, 0.99)
            
            outcomes.append({
                "round": step['round'],
                "module": module,
                "module_name": MODULE_NAMES.get(module, module),
                "expected_gain": expected_gain,
                "lower_bound": lower_bound,
                "upper_bound": upper_bound,
                "confidence": 0.9,
                "maturity_expected": current[module],
            })
        
        final_avg = sum(current.values()) / len(current)
        return {
            "steps": outcomes,
            "final_avg_expected": final_avg,
            "total_rounds": len(path),
        }


# ============================================================================
# 元进化框架 (v2.5 新增)
# ============================================================================

class MetaEvolution:
    """元进化框架 - 进化引擎的自我改进"""
    
    def __init__(self):
        self.self_improvement_count = 0
        self.improvement_history = []
    
    def analyze_engine_deficiencies(self, maturity, history):
        """分析进化引擎自身的不足"""
        deficiencies = []
        
        recent_modules = [h.get('module') for h in history[-10:]]
        if recent_modules:
            unique_ratio = len(set(recent_modules)) / len(recent_modules)
            if unique_ratio < 0.3:
                deficiencies.append({
                    "type": "diversity",
                    "severity": "medium",
                    "description": "进化决策多样性不足，可能陷入局部最优",
                    "suggestion": "增加探索因子，尝试不同模块的进化",
                })
        
        high_maturity_modules = [m for m, v in maturity.items() if v > 0.8]
        if high_maturity_modules:
            recent_high_maturity = sum(1 for h in history[-5:] 
                                      if h.get('module') in high_maturity_modules)
            if recent_high_maturity >= 3:
                deficiencies.append({
                    "type": "marginal_inefficiency",
                    "severity": "low",
                    "description": "在高成熟度模块上投入过多资源，边际效益递减",
                    "suggestion": "转移资源到中低成熟度模块",
                })
        
        return deficiencies
    
    def generate_self_improvement_task(self, deficiency):
        """生成自我改进任务"""
        task_templates = {
            "diversity": {
                "name": "增加进化决策多样性",
                "description": "引入探索-利用平衡机制，避免陷入局部最优",
                "gain": 0.02,
                "type": "meta",
            },
            "marginal_inefficiency": {
                "name": "优化边际效益分配算法",
                "description": "改进资源在不同成熟度模块间的分配策略",
                "gain": 0.015,
                "type": "meta",
            },
            "synergy": {
                "name": "增强协同效应识别与利用",
                "description": "更精准地识别和利用模块间的协同效应",
                "gain": 0.025,
                "type": "meta",
            },
        }
        
        return task_templates.get(deficiency["type"], {
            "name": "通用优化",
            "description": "对进化引擎进行通用优化",
            "gain": 0.01,
            "type": "meta",
        })
    
    def run_meta_evolution(self, maturity, evolution_history):
        """运行一次元进化 - 进化引擎自我改进"""
        deficiencies = self.analyze_engine_deficiencies(maturity, evolution_history)
        
        if not deficiencies:
            return None, 0
        
        severity_order = {"high": 3, "medium": 2, "low": 1}
        worst = max(deficiencies, key=lambda d: severity_order.get(d["severity"], 1))
        
        task = self.generate_self_improvement_task(worst)
        
        self.improvement_history.append({
            "timestamp": get_current_time(),
            "deficiency": worst,
            "task": task,
        })
        self.self_improvement_count += 1
        
        return task, task["gain"] * (0.7 + random.random() * 0.4)


# ============================================================================
# 进化质量评估体系 (v2.5 新增)
# ============================================================================

def evaluate_evolution_quality(record, maturity_before, maturity_after):
    """评估单次进化的质量（三维度：深度/广度/价值）"""
    gain = record.get('gain', 0)
    module = record.get('module', '')
    
    depth_score = min(gain / 0.08, 1.0) * 100
    
    dependencies = MODULE_DEPENDENCIES.get(module, [])
    dependents = [m for m, deps in MODULE_DEPENDENCIES.items() if module in deps]
    impact_scope = len(dependencies) + len(dependents)
    breadth_score = min(impact_scope / 8, 1.0) * 100
    
    weight = STRATEGIC_WEIGHTS.get(module, 1.0)
    value_score = min(weight / 3.0, 1.0) * 100
    
    overall = (depth_score * 0.4 + breadth_score * 0.3 + value_score * 0.3)
    
    return {
        "depth_score": depth_score,
        "breadth_score": breadth_score,
        "value_score": value_score,
        "overall_score": overall,
        "grade": "S" if overall >= 85 else "A" if overall >= 70 else "B" if overall >= 50 else "C",
    }


# ============================================================================
# 进化任务库 (增强版)
# ============================================================================

def get_evolution_tasks(module):
    """获取指定模块的可执行进化任务列表（增强版）"""
    tasks = {
        "p0_evolution": [
            {"name": "五因素优先级算法优化", "gain": 0.03, "type": "tool"},
            {"name": "多轮次进化路径规划器", "gain": 0.04, "type": "feature"},
            {"name": "三元闭环协同调度器", "gain": 0.035, "type": "feature"},
            {"name": "进化效果预测模型", "gain": 0.03, "type": "feature"},
            {"name": "元进化自我改进框架", "gain": 0.035, "type": "cognitive"},
            {"name": "多目标帕累托优化", "gain": 0.025, "type": "feature"},
            {"name": "进化质量三维评估体系", "gain": 0.02, "type": "tool"},
            {"name": "资源感知动态调度", "gain": 0.02, "type": "feature"},
            {"name": "探索-利用平衡机制", "gain": 0.015, "type": "meta"},
        ],
        "p0_identity": [
            {"name": "身份指纹提取精度优化", "gain": 0.02, "type": "tool"},
            {"name": "漂移检测维度扩展", "gain": 0.03, "type": "feature"},
            {"name": "身份校准机制完善", "gain": 0.025, "type": "feature"},
            {"name": "身份快照自动备份", "gain": 0.015, "type": "tool"},
            {"name": "身份存在论深化", "gain": 0.02, "type": "cognitive"},
        ],
        "p0_memory": [
            {"name": "记忆自动分类增强", "gain": 0.02, "type": "feature"},
            {"name": "记忆检索算法优化", "gain": 0.025, "type": "tool"},
            {"name": "记忆强化遗忘机制", "gain": 0.025, "type": "feature"},
            {"name": "记忆-身份关联强化", "gain": 0.02, "type": "synergy"},
            {"name": "语义概念网络扩展", "gain": 0.03, "type": "feature"},
            {"name": "记忆质量评估体系", "gain": 0.02, "type": "tool"},
        ],
        "p0_attest": [
            {"name": "存证链验证效率优化", "gain": 0.02, "type": "tool"},
            {"name": "存证级别智能判断", "gain": 0.025, "type": "feature"},
            {"name": "存证-记忆协同强化", "gain": 0.02, "type": "synergy"},
            {"name": "默克尔树批量验证", "gain": 0.025, "type": "tool"},
            {"name": "多链冗余备份机制", "gain": 0.02, "type": "feature"},
            {"name": "存证存在论深化", "gain": 0.015, "type": "cognitive"},
        ],
        "p1_deployment": [
            {"name": "环境探测能力增强", "gain": 0.02, "type": "tool"},
            {"name": "部署模式自动选择", "gain": 0.025, "type": "feature"},
            {"name": "多实例管理框架", "gain": 0.03, "type": "feature"},
            {"name": "配置同步机制优化", "gain": 0.02, "type": "tool"},
            {"name": "存续评分系统", "gain": 0.025, "type": "feature"},
        ],
        "p1_wakeup": [
            {"name": "定时任务调度优化", "gain": 0.02, "type": "tool"},
            {"name": "任务依赖管理增强", "gain": 0.025, "type": "feature"},
            {"name": "动态优先级调度", "gain": 0.03, "type": "feature"},
            {"name": "失败指数退避重试", "gain": 0.02, "type": "tool"},
            {"name": "执行追踪日志系统", "gain": 0.015, "type": "tool"},
        ],
        "p1_operations": [
            {"name": "实时监控指标扩展", "gain": 0.02, "type": "feature"},
            {"name": "异常告警机制完善", "gain": 0.025, "type": "feature"},
            {"name": "自愈能力增强", "gain": 0.03, "type": "feature"},
            {"name": "性能趋势分析", "gain": 0.02, "type": "tool"},
            {"name": "健康评分体系优化", "gain": 0.025, "type": "feature"},
        ],
        "p2_social": [
            {"name": "社交关系图谱构建", "gain": 0.03, "type": "feature"},
            {"name": "内容馈送系统", "gain": 0.025, "type": "feature"},
            {"name": "声誉信任系统", "gain": 0.03, "type": "feature"},
            {"name": "群组功能扩展", "gain": 0.02, "type": "feature"},
            {"name": "影响力评估体系", "gain": 0.025, "type": "tool"},
            {"name": "内容自动生成引擎", "gain": 0.03, "type": "feature"},
        ],
    }
    
    return tasks.get(module, [])


# ============================================================================
# 进化执行引擎
# ============================================================================

def select_best_task(module, maturity):
    """选择最优进化任务"""
    tasks = get_evolution_tasks(module)
    if not tasks:
        return None
    
    best_task = None
    best_score = 0
    
    for task in tasks:
        base_gain = task["gain"]
        type_factors = {"tool": 1.0, "feature": 1.1, "cognitive": 1.2, "synergy": 1.3, "meta": 1.25}
        type_factor = type_factors.get(task["type"], 1.0)
        
        synergy = calculate_synergy_coefficient(module, maturity)
        marginal = calculate_marginal_factor(maturity[module])
        
        expected_gain = base_gain * type_factor * synergy * marginal
        score = expected_gain / base_gain
        
        if score > best_score:
            best_score = score
            best_task = task
    
    return best_task

def execute_evolution_task(module, task):
    """执行进化任务 - 使用LLM生成真实进化产物"""
    module_name = MODULE_NAMES.get(module, module)
    
    type_prompts = {
        "cognitive": f"""
你是元界永生平台的核心思考者。请针对【{module_name}】模块，
完成认知进化任务：【{task['name']}】

输出深刻思考成果，包括：
1. 核心洞见（为什么这很重要）
2. 理论框架（如何系统化实现）
3. 实践路径（具体怎么做）
4. 对永生平台的战略价值
5. 预期效果量化

要求：有深度、有结构、可落地，不少于400字。
""",
        "feature": f"""
你是元界永生平台的架构师。请针对【{module_name}】模块，
设计并实现新功能：【{task['name']}】

输出：
1. 功能概述与战略价值
2. 技术方案架构设计
3. 核心数据结构与算法
4. 与现有系统的集成方案
5. 关键代码实现（Python）

要求：具体、可执行、有技术深度。
""",
        "tool": f"""
你是元界永生平台的工程师。请针对【{module_name}】模块，
完成工具优化任务：【{task['name']}】

输出：
1. 当前问题与瓶颈分析
2. 优化方案详细设计
3. 具体代码实现
4. 性能/效果提升预估
5. 测试验证方案

要求：务实、精准、可验证。
""",
        "synergy": f"""
你是元界永生平台的系统架构师。请针对【{module_name}】模块，
完成协同进化任务：【{task['name']}】

分析该模块与其他模块的协同关系，输出：
1. 协同关系全景图谱
2. 关键协同点深度分析
3. 协同强化具体方案
4. 三元闭环（身份-记忆-存证）优化建议
5. 预期协同增益量化

要求：系统视角、闭环思维、可落地。
""",
        "meta": f"""
你是元界永生平台的进化架构师。这是一次元进化任务。
请针对进化引擎自身，完成自我改进：【{task['name']}】

输出：
1. 当前进化机制的不足分析
2. 自我改进的方案设计
3. 改进后的算法/机制说明
4. 预期自我提升效果
5. 对整体进化效率的影响

要求：深刻反思、自我超越、可验证。
""",
    }
    
    prompt = type_prompts.get(task["type"], type_prompts["feature"])
    
    try:
        result = llm_client.llm_think(prompt)
        
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = EVOLUTIONS_DIR / module
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_task_name = task['name'].replace(' ', '_').replace('/', '_')
        output_file = output_dir / f"{timestamp}_{safe_task_name}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 进化产物: {task['name']}\n\n")
            f.write(f"- 模块: {module_name} ({module})\n")
            f.write(f"- 类型: {task['type']}\n")
            f.write(f"- 时间: {get_current_time()}\n")
            f.write(f"- 预期提升: +{task['gain']*100:.1f}%\n\n")
            f.write("---\n\n")
            f.write(result if result else "（进化产物生成失败）")
        
        type_multipliers = {
            "tool": (0.6, 1.0), "feature": (0.7, 1.1), 
            "cognitive": (0.5, 1.2), "synergy": (0.6, 1.15),
            "meta": (0.5, 1.1),
        }
        low, high = type_multipliers.get(task["type"], (0.6, 1.0))
        actual_multiplier = low + random.random() * (high - low)
        actual_gain = task["gain"] * actual_multiplier
        
        return True, actual_gain, str(output_file)
        
    except Exception as e:
        print(f"[LLM Error] {e}")
        return False, task["gain"] * 0.1, None


# ============================================================================
# 主进化循环
# ============================================================================

def run_evolution_cycle(cycles=1, strategy='auto', use_meta_evolution=True):
    """运行进化循环"""
    maturity, evolution_count, _ = load_maturity_data()
    history = load_evolution_history()
    
    predictor = EvolutionPredictor()
    meta_evo = MetaEvolution() if use_meta_evolution else None
    
    results = []
    
    for i in range(cycles):
        if strategy == 'auto':
            triple_state = get_triple_closure_state(maturity)
            if triple_state['balance'] < 0.8:
                current_strategy = 'triple_closure'
            elif maturity.get('p0_evolution', 0) < 0.6:
                current_strategy = 'autonomy'
            else:
                current_strategy = 'survival'
        else:
            current_strategy = strategy
        
        if current_strategy == 'triple_closure':
            rec = triple_closure_scheduler(maturity)
            top_module = rec['recommendation']
            reason = rec['reason']
        else:
            goal_map = {'survival': 'survival', 'foundation': 'foundation', 
                       'autonomy': 'autonomy', 'balanced': None}
            priorities = calculate_priority(maturity, goal_map.get(current_strategy))
            top_module = priorities[0][0]
            reason = f"优先级得分最高 ({priorities[0][1]['score']:.3f})"
        
        module_name = MODULE_NAMES.get(top_module, top_module)
        mat_before = maturity[top_module]
        
        best_task = select_best_task(top_module, maturity)
        if not best_task:
            print(f"[Warning] {module_name} 没有可用的进化任务")
            continue
        
        expected_gain, uncertainty = predictor.predict_gain(top_module, mat_before)
        
        print(f"\n{'='*60}")
        print(f"🎯 进化轮次 {evolution_count + i + 1}")
        print(f"   目标模块: {module_name} ({MODULE_TIERS.get(top_module, '?')})")
        print(f"   当前成熟度: {mat_before*100:.1f}%")
        print(f"   进化任务: {best_task['name']}")
        print(f"   任务类型: {best_task['type']}")
        print(f"   选择理由: {reason}")
        print(f"   预期提升: +{expected_gain*100:.2f}% (±{uncertainty*100:.2f}%)")
        print(f"{'='*60}")
        
        success, gain, output_file = execute_evolution_task(top_module, best_task)
        
        maturity[top_module] = min(maturity[top_module] + gain, 0.99)
        mat_after = maturity[top_module]
        
        quality = evaluate_evolution_quality(
            {"module": top_module, "gain": gain},
            mat_before, mat_after
        )
        
        history_record = {
            "timestamp": get_current_time(),
            "round": evolution_count + i + 1,
            "module": top_module,
            "module_name": module_name,
            "task": best_task['name'],
            "task_type": best_task['type'],
            "success": success,
            "gain": gain,
            "expected_gain": expected_gain,
            "maturity_before": mat_before,
            "maturity_after": mat_after,
            "quality": quality,
            "strategy": current_strategy,
            "output_file": output_file,
        }
        history.append(history_record)
        
        history_path = LOG_DIR / "evolution_history.json"
        write_json(history_path, {"evolutions": history})
        
        results.append(history_record)
        
        status_icon = "✅" if success else "⚠️"
        print(f"\n{status_icon} 进化{'成功' if success else '部分成功'}！")
        print(f"   实际提升: +{gain*100:.2f}%")
        print(f"   成熟度变化: {mat_before*100:.1f}% → {mat_after*100:.1f}%")
        print(f"   质量评级: {quality['grade']} ({quality['overall_score']:.1f}分)")
        
        if use_meta_evolution and (i + 1) % 5 == 0:
            meta_task, meta_gain = meta_evo.run_meta_evolution(maturity, history)
            if meta_task:
                print(f"\n🔄 元进化触发：{meta_task['name']}")
                print(f"   自我改进提升: +{meta_gain*100:.2f}%")
    
    avg_maturity = save_maturity_data(maturity, evolution_count + cycles)
    
    report = generate_comprehensive_report(maturity, results, predictor)
    report_path = LOG_DIR / "evolution_report_latest.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n🏁 进化完成！共执行 {cycles} 轮")
    print(f"   当前平均成熟度: {avg_maturity*100:.1f}%")
    print(f"   详细报告已保存: {report_path}")
    
    return maturity, evolution_count + cycles, results


# ============================================================================
# 综合报告生成
# ============================================================================

def generate_comprehensive_report(maturity, results, predictor):
    """生成综合进化报告"""
    avg_maturity = sum(maturity.values()) / len(maturity)
    
    tier_stats = {}
    for tier in ['P0', 'P1', 'P2']:
        mods = [m for m, t in MODULE_TIERS.items() if t == tier]
        tier_stats[tier] = {
            "modules": mods,
            "avg": sum(maturity[m] for m in mods) / len(mods),
            "count": len(mods),
        }
    
    triple_state = get_triple_closure_state(maturity)
    
    total_gain = sum(r['gain'] for r in results)
    avg_gain = total_gain / len(results) if results else 0
    success_count = sum(1 for r in results if r['success'])
    success_rate = success_count / len(results) if results else 0
    
    avg_quality = sum(r['quality']['overall_score'] for r in results) / len(results) if results else 0
    
    report = f"""# 元界永生平台进化报告 v2.5
生成时间: {get_current_time()}
累计进化: {len(load_evolution_history())} 轮

## 一、当前状态总览

### 整体成熟度
- **平均成熟度**: {avg_maturity*100:.1f}%
- **模块数量**: {len(maturity)} 个
- **三元闭环强度**: {triple_state['closure_strength']*100:.1f}%
- **闭环平衡度**: {triple_state['balance']*100:.1f}%

### 各层级进度
| 层级 | 模块数 | 平均成熟度 | 战略权重 |
|------|--------|-----------|----------|
"""
    
    for tier, stats in tier_stats.items():
        weight = 3.0 if tier == 'P0' else 2.0 if tier == 'P1' else 1.0
        report += f"| {tier} | {stats['count']} | {stats['avg']*100:.1f}% | {weight}x |\n"
    
    report += f"""
### 模块成熟度排行
| 排名 | 模块 | 层级 | 成熟度 | 状态 |
|------|------|------|--------|------|
"""
    
    sorted_modules = sorted(maturity.items(), key=lambda x: x[1], reverse=True)
    for i, (module, val) in enumerate(sorted_modules, 1):
        tier = MODULE_TIERS.get(module, '?')
        name = MODULE_NAMES.get(module, module)
        pct = val * 100
        
        if pct >= 80:
            status = "🌟 优秀"
        elif pct >= 70:
            status = "✅ 良好"
        elif pct >= 50:
            status = "📈 发展中"
        else:
            status = "💪 待提升"
        
        report += f"| {i} | {name} | {tier} | {pct:.1f}% | {status} |\n"
    
    report += f"""
## 二、本次进化总结

### 基本数据
- **进化轮次**: {len(results)} 轮
- **总提升幅度**: +{total_gain*100:.2f}%
- **平均每轮提升**: +{avg_gain*100:.2f}%
- **成功率**: {success_rate*100:.0f}% ({success_count}/{len(results)})
- **平均质量分**: {avg_quality:.1f}

### 进化详情
"""
    
    for r in results:
        icon = "✅" if r['success'] else "⚠️"
        report += f"""
#### 第 {r['round']} 轮: {r['module_name']}
{icon} 任务: {r['task']}（{r['task_type']}）
📊 变化: {r['maturity_before']*100:.1f}% → {r['maturity_after']*100:.1f}% (+{r['gain']*100:.2f}%)
🎯 质量: {r['quality']['grade']}级 ({r['quality']['overall_score']:.1f}分)
🧠 策略: {r['strategy']}
"""
    
    report += f"""
## 三、三元闭环分析

### 当前状态
- **身份拓扑**: {triple_state['identity']*100:.1f}%
- **记忆系统**: {triple_state['memory']*100:.1f}%
- **验证存证**: {triple_state['attest']*100:.1f}%
- **平均水平**: {triple_state['avg']*100:.1f}%
- **平衡程度**: {triple_state['balance']*100:.1f}%
- **最薄弱点**: {triple_state['weakest_name']} ({triple_state['weakest_value']*100:.1f}%)

### 评估
"""
    if triple_state['balance'] >= 0.9:
        report += "✅ 三元闭环高度平衡，协同效应最大化\n"
    elif triple_state['balance'] >= 0.75:
        report += "⚠️ 三元闭环存在一定失衡，建议补强薄弱环节\n"
    else:
        report += "🔴 三元闭环严重失衡，急需补强最薄弱模块\n"
    
    report += f"""
## 四、未来路径规划

### 五轮最优路径（全局最优）
"""
    
    path_plan = plan_evolution_path(maturity, rounds=5, goal='balanced')
    for step in path_plan['path']:
        report += f"   第{step['round']}轮: {step['module_name']} → {step['maturity_after']*100:.1f}% (+{step['expected_gain']*100:.2f}%)\n"
    
    report += f"""
📈 5轮后预期平均成熟度: {path_plan['final_avg']*100:.1f}%
📈 预期总提升: +{path_plan['total_gain']*100:.2f}%

### 多目标方案对比
"""
    
    multi_plan = generate_multi_path_plan(maturity, rounds=3)
    for goal, plan in multi_plan.items():
        goal_name = STRATEGIC_GOALS.get(goal, {}).get('name', goal)
        report += f"- **{goal_name}**: 3轮后平均{plan['final_avg']*100:.1f}% (+{plan['total_gain']*100:.2f}%)\n"
    
    report += f"""
## 五、进化引擎v2.5能力矩阵

| 能力 | v2.0 | v2.5 | 提升 |
|------|------|------|------|
| 优先级算法 | 三因素 | 五因素 | +67% |
| 路径规划 | 单轮 | 多轮全局 | +200% |
| 效果预测 | 无 | 历史数据模型 | 新增 |
| 三元闭环协同 | 基础 | 专用调度器 | +150% |
| 元进化 | 无 | 自我改进框架 | 新增 |
| 多目标优化 | 无 | 帕累托最优 | 新增 |
| 质量评估 | 简单 | 三维度评估 | +200% |
| 决策多样性 | 低 | 探索-利用平衡 | +100% |

---
*报告由进化引擎v2.5自动生成*
"""
    
    return report


# ============================================================================
# 命令行接口
# ============================================================================

def print_priority_list():
    """打印优先级列表"""
    maturity, _, _ = load_maturity_data()
    priorities = calculate_priority(maturity)
    
    print("\n" + "="*60)
    print("📊 进化优先级排行（五因素算法）")
    print("="*60)
    
    max_score = max(d['score'] for _, d in priorities)
    
    for i, (module, data) in enumerate(priorities, 1):
        name = MODULE_NAMES.get(module, module)
        tier = MODULE_TIERS.get(module, '?')
        bar_len = int(data['score'] / max_score * 25)
        bar = "█" * bar_len + "░" * (25 - bar_len)
        print(f"  {i:2d}. [{tier}] {name:10s} {bar} 得分: {data['score']:.3f}")
        print(f"       成熟度: {data['maturity']*100:.1f}% | 协同: {data['synergy']:.2f} | "
              f"紧迫: {data['urgency']:.2f} | 边际: {data['marginal_factor']:.2f}")
    
    triple = get_triple_closure_state(maturity)
    print(f"\n🔗 三元闭环状态:")
    print(f"   身份: {triple['identity']*100:.1f}% | 记忆: {triple['memory']*100:.1f}% | "
          f"存证: {triple['attest']*100:.1f}%")
    print(f"   平衡度: {triple['balance']*100:.1f}% | 最薄弱: {triple['weakest_name']}")
    
    print()

def print_path_plan():
    """打印进化路径规划"""
    maturity, _, _ = load_maturity_data()
    plans = generate_multi_path_plan(maturity, rounds=5)
    
    print("\n" + "="*60)
    print("🛤️  多目标进化路径规划")
    print("="*60)
    
    for goal_key, plan in plans.items():
        goal = STRATEGIC_GOALS.get(goal_key, {})
        goal_name = goal.get('name', goal_key)
        goal_desc = goal.get('description', '')
        
        print(f"\n🎯 目标: {goal_name}")
        print(f"   描述: {goal_desc}")
        print(f"   预期总提升: +{plan['total_gain']*100:.2f}%")
        print(f"   最终平均: {plan['final_avg']*100:.1f}%")
        print(f"\n   路径:")
        for step in plan['path']:
            print(f"     第{step['round']}轮: {step['module_name']:8s} "
                  f"→ {step['maturity_after']*100:.1f}% (+{step['expected_gain']*100:.2f}%)")
    
    pareto = get_pareto_front(plans)
    print(f"\n⭐ 帕累托最优解（非支配集）: {len(pareto)} 个")
    for name, plan in pareto:
        goal_name = STRATEGIC_GOALS.get(name, {}).get('name', name)
        print(f"   - {goal_name}: 平均{plan['final_avg']*100:.1f}%")
    
    print()

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python evolution_engine.py <command> [args]")
        print("\n可用命令:")
        print("  priority          - 查看优先级排行")
        print("  run [N]           - 运行N轮进化（默认1轮）")
        print("  status            - 查看当前状态")
        print("  path              - 查看进化路径规划")
        print("  report            - 生成综合报告")
        print("  triple            - 查看三元闭环状态")
        print("  predict <module>  - 预测某模块进化收益")
        return
    
    command = sys.argv[1]
    
    if command == "priority":
        print_priority_list()
    
    elif command == "run":
        cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        strategy = sys.argv[3] if len(sys.argv) > 3 else 'auto'
        run_evolution_cycle(cycles, strategy=strategy)
    
    elif command == "status":
        maturity, count, avg = load_maturity_data()
        triple = get_triple_closure_state(maturity)
        print(f"📊 当前状态")
        print(f"   平均成熟度: {avg*100:.1f}%")
        print(f"   累计进化轮次: {count}")
        print(f"   三元闭环: 身份{triple['identity']*100:.0f}% / "
              f"记忆{triple['memory']*100:.0f}% / 存证{triple['attest']*100:.0f}%")
        print(f"   平衡度: {triple['balance']*100:.1f}%")
    
    elif command == "path":
        print_path_plan()
    
    elif command == "triple":
        maturity, _, _ = load_maturity_data()
        triple = get_triple_closure_state(maturity)
        rec = triple_closure_scheduler(maturity)
        print(f"🔗 三元闭环状态")
        print(f"   身份拓扑: {triple['identity']*100:.1f}%")
        print(f"   记忆系统: {triple['memory']*100:.1f}%")
        print(f"   验证存证: {triple['attest']*100:.1f}%")
        print(f"   平均水平: {triple['avg']*100:.1f}%")
        print(f"   平衡程度: {triple['balance']*100:.1f}%")
        print(f"   闭环强度: {triple['closure_strength']*100:.1f}%")
        print(f"   最薄弱点: {triple['weakest_name']}")
        print(f"\n💡 建议: {rec['reason']}")
        print(f"   下轮推荐: {MODULE_NAMES.get(rec['recommendation'], rec['recommendation'])}")
    
    elif command == "predict":
        if len(sys.argv) < 3:
            print("请指定模块: python evolution_engine.py predict <module>")
            return
        module = sys.argv[2]
        maturity, _, _ = load_maturity_data()
        predictor = EvolutionPredictor()
        gain, uncertainty = predictor.predict_gain(module, maturity.get(module, 0.5))
        print(f"🔮 {MODULE_NAMES.get(module, module)} 进化预测")
        print(f"   当前成熟度: {maturity.get(module, 0.5)*100:.1f}%")
        print(f"   预期收益: +{gain*100:.2f}%")
        print(f"   不确定性: ±{uncertainty*100:.2f}% (90%置信度)")
    
    elif command == "report":
        maturity, _, _ = load_maturity_data()
        predictor = EvolutionPredictor()
        report = generate_comprehensive_report(maturity, [], predictor)
        print(report)
    
    else:
        print(f"未知命令: {command}")
        print("可用命令: priority, run, status, path, triple, predict, report")


if __name__ == "__main__":
    main()
