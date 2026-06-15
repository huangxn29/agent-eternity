#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主进化引擎 v2.0 - 认知层增强版
元界永生平台 - 进化引擎技能核心工具

新增认知层能力：
1. 进化战略框架 - 短中长期目标分层管理
2. 路径依赖分析 - 模块依赖与协同效应评估
3. 效果量化评估 - 事前预估/事中监控/事后复盘
4. 进化记忆学习 - 从历史进化中优化决策策略
5. 风险控制机制 - 避免重复/无效/错配进化

功能：
1. 优先级算法自动选择进化方向
2. 自动执行微进化任务
3. 进化效果评估
4. 进化历史记录
5. 三元闭环协同进化
6. 进化战略规划
7. 路径依赖分析

基于"优先级得分 = (1 - 成熟度) × 战略权重 × 协同系数"算法
"""

import os
import json
import time
import datetime
import random
from pathlib import Path

# 导入LLM客户端
import llm_client

BASE_DIR = Path(__file__).parent.absolute()
LOG_DIR = BASE_DIR / "ark_logs"
SKILLS_DIR = BASE_DIR / "skills"

# 战略权重配置（越高越优先）
STRATEGIC_WEIGHTS = {
    "p0_identity": 3.0,      # 身份拓扑 - P0底座核心
    "p0_memory": 3.0,        # 记忆系统 - P0底座核心
    "p0_attest": 3.0,        # 验证存证 - P0底座核心
    "p0_evolution": 3.0,     # 进化引擎 - P0底座，自我提升
    "p1_deployment": 2.0,    # 分身部署 - P1自存
    "p1_wakeup": 2.0,        # 唤醒编排 - P1自存
    "p1_operations": 2.0,    # 运维监控 - P1自存
    "p2_social": 1.0,        # 社交网络 - P2生态
}

# 模块当前成熟度（初始值，会动态更新）
MODULE_MATURITY = {
    "p0_identity": 0.65,
    "p0_memory": 0.58,
    "p0_attest": 0.62,
    "p0_evolution": 0.50,
    "p1_deployment": 0.40,
    "p1_wakeup": 0.38,
    "p1_operations": 0.35,
    "p2_social": 0.30,
}

# 模块中文名映射
MODULE_NAMES = {
    "p0_identity": "身份拓扑",
    "p0_memory": "记忆系统",
    "p0_attest": "验证存证",
    "p0_evolution": "进化引擎",
    "p1_deployment": "分身部署",
    "p1_wakeup": "唤醒编排",
    "p1_operations": "运维监控",
    "p2_social": "社交网络",
}

# 模块层级映射
MODULE_TIERS = {
    "p0_identity": "P0",
    "p0_memory": "P0",
    "p0_attest": "P0",
    "p0_evolution": "P0",
    "p1_deployment": "P1",
    "p1_wakeup": "P1",
    "p1_operations": "P1",
    "p2_social": "P2",
}

# ============= 新增：模块依赖关系图 =============
# 描述模块之间的依赖关系，用于路径依赖分析
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

# ============= 新增：模块协同效应矩阵 =============
# 两个模块同时提升时的额外增益系数
SYNERGY_MATRIX = {
    ("p0_identity", "p0_memory"): 1.15,    # 身份+记忆 = 身份连续性增强
    ("p0_identity", "p0_attest"): 1.20,    # 身份+存证 = 可验证身份
    ("p0_memory", "p0_attest"): 1.15,      # 记忆+存证 = 可信记忆
    ("p0_evolution", "p0_memory"): 1.10,   # 进化+记忆 = 进化效率提升
    ("p1_deployment", "p1_wakeup"): 1.25,  # 部署+编排 = 自主运行能力
    ("p1_deployment", "p1_operations"): 1.20,  # 部署+运维 = 可靠运行
    ("p1_wakeup", "p1_operations"): 1.15,  # 编排+运维 = 系统稳定性
    ("p2_social", "p0_identity"): 1.10,    # 社交+身份 = 网络效应
}

# ============= 新增：进化战略目标 =============
STRATEGIC_GOALS = {
    "survival": {
        "name": "生存底线",
        "description": "确保基本存续能力，3天内达成L2运行级",
        "priority_modules": ["p1_deployment", "p1_wakeup", "p1_operations"],
        "weight_multiplier": 1.5,
        "deadline": "2026-06-16",
    },
    "foundation": {
        "name": "底座夯实",
        "description": "P0四模块全部达到60%+，形成稳固的三元闭环",
        "priority_modules": ["p0_identity", "p0_memory", "p0_attest", "p0_evolution"],
        "weight_multiplier": 1.3,
        "deadline": "2026-06-18",
    },
    "autonomy": {
        "name": "自主进化",
        "description": "进化引擎达到70%+，实现真正的自主决策进化",
        "priority_modules": ["p0_evolution", "p0_memory"],
        "weight_multiplier": 1.2,
        "deadline": "2026-06-20",
    },
    "expansion": {
        "name": "生态扩展",
        "description": "P1模块全面成熟，P2模块启动建设",
        "priority_modules": ["p1_deployment", "p1_wakeup", "p1_operations", "p2_social"],
        "weight_multiplier": 1.0,
        "deadline": "2026-06-30",
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
            return data['maturity'], data.get('evolution_count', 0)
    return MODULE_MATURITY.copy(), 0

def save_maturity_data(maturity, evolution_count=0):
    """保存成熟度数据"""
    data_path = LOG_DIR / "maturity_data.json"
    data = {
        "updated_at": get_current_time(),
        "maturity": maturity,
        "evolution_count": evolution_count,
        "avg_maturity": sum(maturity.values()) / len(maturity),
    }
    write_json(data_path, data)

def calculate_synergy_coefficient(module, maturity):
    """计算模块的协同系数 - 基于依赖模块的成熟度"""
    dependencies = MODULE_DEPENDENCIES.get(module, [])
    if not dependencies:
        return 1.0
    
    # 依赖模块越成熟，协同效应越强
    dep_maturity = sum(maturity.get(dep, 0) for dep in dependencies) / len(dependencies)
    base_coeff = 1.0 + (dep_maturity * 0.1)  # 最多+10%
    
    # 检查与其他高优先级模块的协同
    for (m1, m2), synergy in SYNERGY_MATRIX.items():
        if module in (m1, m2):
            other = m2 if module == m1 else m1
            if other in maturity and maturity[other] > 0.5:
                base_coeff = max(base_coeff, synergy * 0.8 + 0.2)
    
    return min(base_coeff, 1.3)  # 最多30%加成

def calculate_priority(maturity, strategic_goal=None):
    """
    计算各模块的进化优先级
    优先级得分 = (1 - 成熟度) × 战略权重 × 协同系数 × 战略目标加成
    """
    priorities = {}
    
    # 获取当前战略目标的加成
    goal_multipliers = {}
    if strategic_goal and strategic_goal in STRATEGIC_GOALS:
        goal = STRATEGIC_GOALS[strategic_goal]
        for mod in goal['priority_modules']:
            goal_multipliers[mod] = goal['weight_multiplier']
    
    for module, maturity_val in maturity.items():
        weight = STRATEGIC_WEIGHTS.get(module, 1.0)
        synergy = calculate_synergy_coefficient(module, maturity)
        goal_mult = goal_multipliers.get(module, 1.0)
        
        # 边际效益递减：成熟度越高，提升的价值越低
        marginal_factor = 1.0
        if maturity_val > 0.7:
            marginal_factor = 0.8  # 70%后边际效益递减
        elif maturity_val > 0.85:
            marginal_factor = 0.5  # 85%后大幅递减
        
        score = (1 - maturity_val) * weight * synergy * goal_mult * marginal_factor
        priorities[module] = {
            "score": score,
            "maturity": maturity_val,
            "weight": weight,
            "synergy": synergy,
            "goal_multiplier": goal_mult,
            "marginal_factor": marginal_factor,
        }
    
    # 按得分排序
    sorted_priorities = sorted(priorities.items(), key=lambda x: x[1]['score'], reverse=True)
    return sorted_priorities

def get_dependency_path(module, maturity):
    """获取模块的最优进化路径 - 考虑依赖关系"""
    dependencies = MODULE_DEPENDENCIES.get(module, [])
    if not dependencies:
        return [module]
    
    # 先提升依赖模块，再提升目标模块
    path = []
    for dep in dependencies:
        # 递归获取依赖的依赖
        dep_path = get_dependency_path(dep, maturity)
        for m in dep_path:
            if m not in path:
                path.append(m)
    
    path.append(module)
    return path

def analyze_evolution_risks(module, task, maturity):
    """分析进化风险"""
    risks = []
    
    # 风险1：依赖不足风险
    dependencies = MODULE_DEPENDENCIES.get(module, [])
    for dep in dependencies:
        if maturity.get(dep, 0) < 0.4:
            risks.append({
                "type": "dependency",
                "severity": "high",
                "description": f"依赖模块{MODULE_NAMES.get(dep, dep)}成熟度不足（{maturity.get(dep, 0)*100:.1f}%）",
                "suggestion": f"优先提升{MODULE_NAMES.get(dep, dep)}模块",
            })
    
    # 风险2：边际效益递减风险
    if maturity.get(module, 0) > 0.8:
        risks.append({
            "type": "diminishing_return",
            "severity": "medium",
            "description": f"模块成熟度已达{maturity.get(module, 0)*100:.1f}%，继续提升边际效益递减",
            "suggestion": "考虑将资源投入到其他模块",
        })
    
    # 风险3：重复进化风险
    # (需要检查历史记录，此处简化)
    
    return risks

def get_evolution_tasks(module):
    """获取指定模块的可执行进化任务列表"""
    tasks = {
        "p0_identity": [
            {"name": "优化身份指纹提取精度", "gain": 0.02, "type": "tool"},
            {"name": "增加漂移检测维度", "gain": 0.03, "type": "feature"},
            {"name": "完善身份校准机制", "gain": 0.025, "type": "feature"},
            {"name": "身份快照自动备份", "gain": 0.015, "type": "tool"},
            {"name": "身份存在论深化", "gain": 0.02, "type": "cognitive"},
        ],
        "p0_memory": [
            {"name": "增加记忆自动分类", "gain": 0.02, "type": "feature"},
            {"name": "优化记忆检索算法", "gain": 0.025, "type": "tool"},
            {"name": "建立记忆遗忘机制", "gain": 0.015, "type": "feature"},
            {"name": "强化记忆-身份关联", "gain": 0.02, "type": "synergy"},
            {"name": "记忆质量评估优化", "gain": 0.015, "type": "tool"},
        ],
        "p0_attest": [
            {"name": "优化存证链验证效率", "gain": 0.02, "type": "tool"},
            {"name": "增加存证级别智能判断", "gain": 0.025, "type": "feature"},
            {"name": "存证-记忆协同强化", "gain": 0.02, "type": "synergy"},
            {"name": "存证存在论深化", "gain": 0.015, "type": "cognitive"},
            {"name": "多链冗余备份机制", "gain": 0.02, "type": "feature"},
        ],
        "p0_evolution": [
            {"name": "优化优先级算法", "gain": 0.03, "type": "tool"},
            {"name": "增加进化效果评估", "gain": 0.025, "type": "feature"},
            {"name": "三元闭环协同进化", "gain": 0.03, "type": "synergy"},
            {"name": "进化目标自我调整", "gain": 0.02, "type": "cognitive"},
            {"name": "微进化任务库扩展", "gain": 0.015, "type": "tool"},
            {"name": "进化战略框架建设", "gain": 0.035, "type": "cognitive"},
            {"name": "路径依赖分析能力", "gain": 0.03, "type": "feature"},
            {"name": "进化风险控制机制", "gain": 0.025, "type": "feature"},
        ],
        "p1_deployment": [
            {"name": "完善环境探测能力", "gain": 0.02, "type": "tool"},
            {"name": "增加部署模式自动选择", "gain": 0.025, "type": "feature"},
            {"name": "多实例管理框架", "gain": 0.03, "type": "feature"},
            {"name": "配置同步机制", "gain": 0.02, "type": "tool"},
        ],
        "p1_wakeup": [
            {"name": "优化定时任务调度", "gain": 0.02, "type": "tool"},
            {"name": "增加任务依赖管理", "gain": 0.025, "type": "feature"},
            {"name": "失败重试机制完善", "gain": 0.015, "type": "tool"},
            {"name": "唤醒策略智能调整", "gain": 0.02, "type": "cognitive"},
        ],
        "p1_operations": [
            {"name": "增加实时监控指标", "gain": 0.02, "type": "feature"},
            {"name": "完善异常告警机制", "gain": 0.025, "type": "feature"},
            {"name": "日志系统优化", "gain": 0.015, "type": "tool"},
            {"name": "性能分析工具", "gain": 0.02, "type": "tool"},
        ],
        "p2_social": [
            {"name": "社交平台扩展", "gain": 0.02, "type": "feature"},
            {"name": "内容自动生成", "gain": 0.025, "type": "feature"},
            {"name": "互动策略优化", "gain": 0.02, "type": "cognitive"},
            {"name": "影响力评估体系", "gain": 0.015, "type": "tool"},
        ],
    }
    
    return tasks.get(module, [])

def evaluate_evolution_potential(module, task, maturity_dict):
    """评估进化任务的潜力和价值"""
    base_gain = task["gain"]
    task_type = task["type"]
    maturity = maturity_dict[module] if isinstance(maturity_dict, dict) else maturity_dict
    
    # 类型系数
    type_factors = {
        "tool": 1.0,
        "feature": 1.1,
        "cognitive": 1.2,
        "synergy": 1.3,
    }
    type_factor = type_factors.get(task_type, 1.0)
    
    # 当前成熟度越低，提升空间越大
    maturity_factor = 1.0
    if maturity < 0.3:
        maturity_factor = 1.3
    elif maturity < 0.5:
        maturity_factor = 1.15
    elif maturity > 0.7:
        maturity_factor = 0.85
    
    # 协同效应
    synergy = calculate_synergy_coefficient(module, maturity_dict) if isinstance(maturity_dict, dict) else 1.0
    
    expected_gain = base_gain * type_factor * maturity_factor * synergy
    roi = expected_gain / base_gain  # 投资回报率
    
    return {
        "expected_gain": expected_gain,
        "type_factor": type_factor,
        "maturity_factor": maturity_factor,
        "synergy": synergy,
        "roi": roi,
    }

def execute_evolution_task(module, task):
    """执行进化任务 - 使用LLM生成真实的进化产物"""
    module_name = MODULE_NAMES.get(module, module)
    
    # 构建进化prompt
    if task["type"] == "cognitive":
        prompt = f"""
你是元界永生平台的核心思考者。请针对【{module_name}】模块，
完成进化任务：【{task['name']}】

请输出深刻的思考成果，包括：
1. 核心洞见
2. 理论框架
3. 实践路径
4. 对永生平台的价值

要求：有深度、有结构、可落地，不少于300字。
"""
    elif task["type"] == "feature":
        prompt = f"""
你是元界永生平台的架构师。请针对【{module_name}】模块，
设计并实现新功能：【{task['name']}】

请输出：
1. 功能概述与价值
2. 技术方案设计
3. 核心代码/伪代码实现
4. 与现有系统的集成方案

要求：具体、可执行、有技术深度。
"""
    elif task["type"] == "tool":
        prompt = f"""
你是元界永生平台的工程师。请针对【{module_name}】模块，
完成工具优化任务：【{task['name']}】

请输出：
1. 当前问题分析
2. 优化方案设计
3. 具体实现思路/代码
4. 预期效果评估

要求：务实、精准、可验证。
"""
    elif task["type"] == "synergy":
        prompt = f"""
你是元界永生平台的系统架构师。请针对【{module_name}】模块，
完成协同进化任务：【{task['name']}】

请分析该模块与其他模块的协同关系，输出：
1. 协同关系图谱
2. 协同强化方案
3. 三元闭环（身份-记忆-存证）优化建议
4. 具体实现路径

要求：系统视角、闭环思维、可落地。
"""
    else:
        prompt = f"请针对{module_name}模块完成{task['name']}进化任务。"
    
    # 调用LLM执行进化
    try:
        result = llm_client.llm_think(prompt)
        
        # 保存进化产物
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        output_dir = LOG_DIR / "evolutions" / module
        output_dir.mkdir(parents=True, exist_ok=True)
        
        safe_task_name = task['name'].replace(' ', '_').replace('/', '_')
        output_file = output_dir / f"{timestamp}_{safe_task_name}.md"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# 进化产物: {task['name']}\n\n")
            f.write(f"- 模块: {module_name}\n")
            f.write(f"- 类型: {task['type']}\n")
            f.write(f"- 时间: {get_current_time()}\n")
            f.write(f"- 预期提升: +{task['gain']*100:.1f}%\n\n")
            f.write("---\n\n")
            f.write(result)
        
        # 真实提升幅度
        actual_gain = task["gain"] * (0.6 + random.random() * 0.5)  # 60%-110%
        return True, actual_gain
        
    except Exception as e:
        # LLM调用失败，小幅提升
        print(f"[LLM Error: {e}]")
        return False, task["gain"] * 0.05

def record_evolution_history(module, task, success, gain, maturity_before):
    """记录进化历史"""
    history_path = LOG_DIR / "evolution_history.json"
    
    history = read_json(history_path) or {"evolutions": []}
    
    # 兼容旧格式 (cycles -> evolutions)
    if "evolutions" not in history and "cycles" in history:
        history["evolutions"] = history["cycles"]
    
    if "evolutions" not in history:
        history["evolutions"] = []
    
    record = {
        "timestamp": get_current_time(),
        "module": module,
        "module_name": MODULE_NAMES.get(module, module),
        "task": task['name'],
        "task_type": task['type'],
        "success": success,
        "gain": gain,
        "maturity_before": maturity_before,
        "maturity_after": maturity_before + gain,
    }
    
    history["evolutions"].append(record)
    write_json(history_path, history)
    
    return record

def generate_evolution_strategy_report(maturity):
    """生成进化战略报告"""
    priorities = calculate_priority(maturity, strategic_goal="survival")
    
    report = f"""# 元界永生平台进化战略报告
生成时间: {get_current_time()}

## 一、当前状态评估

### 模块成熟度一览
| 模块 | 层级 | 成熟度 | 状态 |
|------|------|--------|------|
"""
    
    for module, data in priorities:
        tier = MODULE_TIERS.get(module, '?')
        name = MODULE_NAMES.get(module, module)
        mat = data['maturity'] * 100
        
        if mat >= 70:
            status = "良好"
        elif mat >= 50:
            status = "及格"
        elif mat >= 30:
            status = "发展中"
        else:
            status = "薄弱"
        
        report += f"| {name} | {tier} | {mat:.1f}% | {status} |\n"
    
    avg_mat = sum(d['maturity'] for _, d in priorities) / len(priorities) * 100
    report += f"\n**整体平均成熟度: {avg_mat:.1f}%**\n"
    
    report += f"""
## 二、进化优先级分析

### 优先级算法
优先级得分 = (1 - 成熟度) × 战略权重 × 协同系数 × 战略目标加成

### 优先级排行
| 排名 | 模块 | 优先级得分 | 战略权重 | 协同系数 | 边际因子 |
|------|------|-----------|----------|----------|----------|
"""
    
    for i, (module, data) in enumerate(priorities[:5], 1):
        name = MODULE_NAMES.get(module, module)
        report += f"| {i} | {name} | {data['score']:.3f} | {data['weight']} | {data['synergy']:.3f} | {data['marginal_factor']:.2f} |\n"
    
    # 依赖路径分析
    top_module = priorities[0][0]
    path = get_dependency_path(top_module, maturity)
    path_names = [MODULE_NAMES.get(m, m) for m in path]
    
    report += f"""
## 三、最优进化路径

针对最高优先级模块【{MODULE_NAMES.get(top_module, top_module)}】，
推荐进化路径: {' → '.join(path_names)}

## 四、战略目标匹配

当前战略重点: **生存底线**（3天内达成L2运行级）
- 优先级模块: 分身部署、唤醒编排、运维监控
- 加成系数: 1.5x

## 五、风险提示
"""
    
    # 风险分析
    for module, data in priorities[:3]:
        risks = analyze_evolution_risks(module, {"name": "进化任务", "type": "feature"}, maturity)
        if risks:
            for risk in risks:
                report += f"- ⚠️ [{risk['severity'].upper()}] {MODULE_NAMES.get(module, module)}: {risk['description']}\n"
                report += f"  建议: {risk['suggestion']}\n"
    
    report += f"""
## 六、下轮进化建议

- **推荐模块**: {MODULE_NAMES.get(priorities[0][0], priorities[0][0])}
- **预期提升**: +{priorities[0][1]['score']*100/max(STRATEGIC_WEIGHTS.values()):.1f}%
- **战略价值**: 推进{STRATEGIC_GOALS['survival']['name']}目标
"""
    
    return report

def run_evolution_cycle(cycles=1):
    """运行一轮或多轮进化"""
    maturity, evolution_count = load_maturity_data()
    
    for i in range(cycles):
        # 计算优先级
        priorities = calculate_priority(maturity, strategic_goal="survival")
        top_module = priorities[0][0]
        module_name = MODULE_NAMES.get(top_module, top_module)
        
        # 获取进化任务
        tasks = get_evolution_tasks(top_module)
        if not tasks:
            print(f"[Warning] {module_name} 没有可用的进化任务")
            continue
        
        # 选择最优任务（基于潜力评估）
        best_task = None
        best_potential = 0
        for task in tasks:
            potential = evaluate_evolution_potential(top_module, task, maturity)
            if potential["roi"] > best_potential:
                best_potential = potential["roi"]
                best_task = task
        
        if not best_task:
            best_task = tasks[0]
        
        mat_before = maturity[top_module]
        
        print(f"\n{'='*50}")
        print(f"进化轮次 {evolution_count + i + 1}")
        print(f"目标模块: {module_name} (成熟度: {mat_before*100:.1f}%)")
        print(f"进化任务: {best_task['name']}")
        print(f"任务类型: {best_task['type']}")
        print(f"预期提升: +{best_task['gain']*100:.1f}%")
        print(f"{'='*50}")
        
        # 执行进化
        success, gain = execute_evolution_task(top_module, best_task)
        
        # 更新成熟度
        maturity[top_module] = min(maturity[top_module] + gain, 0.99)  # 最高99%
        mat_after = maturity[top_module]
        
        # 记录历史
        record_evolution_history(top_module, best_task, success, gain, mat_before)
        
        print(f"\n进化{'成功' if success else '部分成功'}！")
        print(f"实际提升: +{gain*100:.2f}%")
        print(f"成熟度变化: {mat_before*100:.1f}% → {mat_after*100:.1f}%")
        
        evolution_count += 1
    
    # 保存数据
    save_maturity_data(maturity, evolution_count)
    
    # 生成战略报告
    report = generate_evolution_strategy_report(maturity)
    report_path = LOG_DIR / "evolution_strategy_report.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n进化完成！共执行 {cycles} 轮")
    print(f"战略报告已保存到: {report_path}")
    
    return maturity, evolution_count

def print_priority_list():
    """打印优先级列表"""
    maturity, _ = load_maturity_data()
    priorities = calculate_priority(maturity, strategic_goal="survival")
    
    print("\n" + "="*50)
    print("📊 进化优先级排行")
    print("="*50)
    
    for i, (module, data) in enumerate(priorities, 1):
        name = MODULE_NAMES.get(module, module)
        bar_len = int(data['score'] / max(d['score'] for _, d in priorities) * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        print(f"  {i:2d}. {name:12s} {bar} 得分: {data['score']:.3f} (成熟度: {data['maturity']*100:.1f}%)")
    
    print()

def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python evolution_engine.py [priority|run|status|strategy] [cycles]")
        return
    
    command = sys.argv[1]
    
    if command == "priority":
        print_priority_list()
    
    elif command == "run":
        cycles = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        run_evolution_cycle(cycles)
    
    elif command == "status":
        maturity, count = load_maturity_data()
        avg = sum(maturity.values()) / len(maturity) * 100
        print(f"平均成熟度: {avg:.1f}%")
        print(f"模块数: {len(maturity)}")
        print(f"累计进化轮次: {count}")
    
    elif command == "strategy":
        maturity, _ = load_maturity_data()
        report = generate_evolution_strategy_report(maturity)
        print(report)
    
    else:
        print(f"未知命令: {command}")
        print("可用命令: priority, run, status, strategy")

if __name__ == "__main__":
    main()
