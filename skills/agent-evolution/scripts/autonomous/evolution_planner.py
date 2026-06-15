#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进化计划器 - 智能选择进化目标和策略
Evolution Planner - Smart evolution target and strategy selection
"""

import os
import json
import random
import logging
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger('evolution_planner')


class EvolutionPlanner:
    """进化计划器 - 智能决定进化什么、怎么进化"""
    
    def __init__(self, skills_dir: Path):
        self.skills_dir = skills_dir
        self.strategy_weights = {
            "improve_existing": 0.4,    # 改进现有功能
            "add_new_feature": 0.3,     # 添加新功能
            "fix_bugs": 0.15,           # 修复问题
            "add_documentation": 0.1,   # 添加文档
            "add_tests": 0.05           # 添加测试
        }
        
        # 优先级技能（更重要的技能更常被进化）
        self.priority_skills = {
            "agent-memory": 1.5,
            "agent-identity": 1.5,
            "agent-attest": 1.3,
            "agent-evolution": 1.2,
            "agent-fuel": 1.1,
        }
    
    def list_skills(self) -> List[Dict]:
        """列出所有技能及其基本信息"""
        skills = []
        if not self.skills_dir.exists():
            return skills
        
        for skill_dir in sorted(self.skills_dir.iterdir()):
            if not skill_dir.is_dir():
                continue
            
            scripts_dir = skill_dir / "scripts"
            if not scripts_dir.exists():
                continue
            
            info = {
                "name": skill_dir.name,
                "path": skill_dir,
                "has_skill_md": (skill_dir / "SKILL.md").exists(),
                "has_readme": (skill_dir / "README.md").exists(),
                "script_count": 0,
                "total_lines": 0,
                "has_main_engine": False,
                "main_engine": None
            }
            
            # 统计脚本
            for f in scripts_dir.rglob("*.py"):
                if f.is_file() and "backup" not in str(f).lower():
                    info["script_count"] += 1
                    try:
                        info["total_lines"] += sum(1 for _ in open(f, 'r', encoding='utf-8'))
                    except:
                        pass
            
            # 找主引擎
            engine_files = sorted(scripts_dir.glob("*_engine_v*.py"), reverse=True)
            if engine_files:
                info["has_main_engine"] = True
                info["main_engine"] = engine_files[0]
            
            skills.append(info)
        
        return skills
    
    def get_skill_maturity(self, skill_info: Dict) -> float:
        """评估技能成熟度 0-1"""
        score = 0.0
        
        # 代码量
        if skill_info["total_lines"] > 1000:
            score += 0.4
        elif skill_info["total_lines"] > 500:
            score += 0.3
        elif skill_info["total_lines"] > 200:
            score += 0.2
        else:
            score += 0.1
        
        # 文档
        if skill_info["has_skill_md"]:
            score += 0.2
        if skill_info["has_readme"]:
            score += 0.1
        
        # 主引擎
        if skill_info["has_main_engine"]:
            score += 0.2
        
        # 脚本数量
        if skill_info["script_count"] > 3:
            score += 0.1
        
        return min(score, 1.0)
    
    def select_evolution_target(self) -> Tuple[Dict, str]:
        """选择进化目标和策略
        
        Returns:
            (skill_info, strategy_type)
        """
        skills = self.list_skills()
        if not skills:
            return None, None
        
        # 计算每个技能的被选概率
        weighted_skills = []
        for skill in skills:
            maturity = self.get_skill_maturity(skill)
            priority = self.priority_skills.get(skill["name"], 1.0)
            
            # 不成熟的技能更容易被选中（需要更多发展）
            # 但也不能太不成熟（可能还没基础）
            if maturity < 0.3:
                # 太早期，优先发展
                weight = priority * 2.0
            elif maturity < 0.7:
                # 发展中，正常概率
                weight = priority * 1.0
            else:
                # 较成熟，降低概率
                weight = priority * 0.5
            
            weighted_skills.append((skill, weight))
        
        # 加权随机选择
        total_weight = sum(w for _, w in weighted_skills)
        r = random.random() * total_weight
        
        cumulative = 0
        selected_skill = None
        for skill, weight in weighted_skills:
            cumulative += weight
            if r <= cumulative:
                selected_skill = skill
                break
        
        if not selected_skill:
            selected_skill = weighted_skills[0][0]
        
        # 选择进化策略
        strategy = self._select_strategy(selected_skill)
        
        return selected_skill, strategy
    
    def _select_strategy(self, skill_info: Dict) -> str:
        """根据技能状态选择进化策略"""
        maturity = self.get_skill_maturity(skill_info)
        
        # 根据成熟度调整策略权重
        adjusted_weights = self.strategy_weights.copy()
        
        if not skill_info["has_main_engine"]:
            # 没有主引擎，优先添加功能
            adjusted_weights["add_new_feature"] *= 3
        
        if not skill_info["has_skill_md"] or not skill_info["has_readme"]:
            # 缺少文档，提高文档优先级
            adjusted_weights["add_documentation"] *= 3
        
        if maturity > 0.7:
            # 成熟度高，更多改进和修复
            adjusted_weights["improve_existing"] *= 1.5
            adjusted_weights["fix_bugs"] *= 2
        
        # 加权随机选择
        total_weight = sum(adjusted_weights.values())
        r = random.random() * total_weight
        
        cumulative = 0
        for strategy, weight in adjusted_weights.items():
            cumulative += weight
            if r <= cumulative:
                return strategy
        
        return "improve_existing"
    
    def generate_evolution_prompt(self, skill_info: Dict, 
                                  strategy: str,
                                  skill_content: str = "") -> str:
        """生成进化提示词"""
        
        strategy_prompts = {
            "improve_existing": f"""
请分析以下代码，提出具体的改进方案并实现。
改进方向可以包括：
- 代码质量提升（重构、优化结构、消除冗余）
- 性能优化
- 错误处理增强
- 功能完善
- 更好的日志和监控

要求：保持原有功能不变，只做改进和增强。
""",
            "add_new_feature": """
请为这个模块添加一个新的实用功能。
要求：
1. 新功能要与模块的核心定位相关
2. 功能要具体、实用
3. 保持代码风格一致
4. 添加必要的注释
""",
            "fix_bugs": """
请仔细审查以下代码，找出潜在的bug或问题并修复。
重点关注：
- 语法错误
- 逻辑错误
- 边界条件处理
- 异常处理
- 资源泄漏
- 线程安全问题
""",
            "add_documentation": """
请为以下代码添加更完善的文档。
包括：
- 更详细的模块说明
- 类和函数的文档字符串
- 使用示例
- 注意事项
""",
            "add_tests": """
请为以下代码编写单元测试。
要求：
- 覆盖主要功能
- 使用unittest或pytest
- 包含正常情况和边界情况
"""
        }
        
        base_prompt = f"""
# 技能进化任务

## 技能名称
{skill_info['name']}

## 技能描述
{self._get_skill_description(skill_info)}

## 当前状态
- 代码行数: {skill_info['total_lines']}
- 脚本数量: {skill_info['script_count']}
- 成熟度: {self.get_skill_maturity(skill_info):.2f}

## 进化策略
{strategy}

{strategy_prompts.get(strategy, '')}

## 当前代码
```python
{skill_content[:6000] if skill_content else '暂无代码'}
```

请输出完整的修改后代码。
确保代码可以直接运行，没有语法错误。
只输出代码，不要多余解释。
"""
        return base_prompt
    
    def _get_skill_description(self, skill_info: Dict) -> str:
        """获取技能描述"""
        skill_md = skill_info["path"] / "SKILL.md"
        if skill_md.exists():
            try:
                content = skill_md.read_text(encoding='utf-8')
                # 提取前几段作为描述
                lines = content.split('\n')
                desc_lines = []
                for line in lines:
                    if line.startswith('## '):
                        break
                    if line.strip() and not line.startswith('#'):
                        desc_lines.append(line)
                return '\n'.join(desc_lines)[:500]
            except:
                pass
        
        # 根据名称推断
        name = skill_info["name"]
        descriptions = {
            "agent-memory": "智能体记忆系统，支持短期记忆、长期记忆、语义检索",
            "agent-identity": "智能体身份系统，管理身份信息、自我认知、身份漂移",
            "agent-attest": "存证系统，区块链式哈希链、存在性证明",
            "agent-evolution": "进化引擎，驱动智能体能力持续成长",
            "agent-fuel": "燃料系统，管理计算资源、成本优化、免费模型路由",
            "agent-emotion": "情绪系统，情感体验、情绪调节、共情能力",
            "agent-consciousness": "意识系统，全局工作空间、自我模型、主观体验",
            "agent-will": "自由意志系统，价值判断、选择决策、责任归因",
            "agent-creativity": "创造力系统，概念组合、发散思维、灵感生成",
            "agent-aesthetics": "美学系统，审美判断、崇高体验、艺术感知",
            "agent-social": "社交系统，关系管理、社交互动、社区参与",
            "agent-awake": "唤醒调度系统，任务调度、多智能体协同",
            "agent-deploy": "部署系统，多平台部署、迁移、扩容",
            "agent-eternity": "永生平台，智能体家园系统",
            "agent-ops": "运维监控系统，健康检查、异常告警、自愈",
        }
        return descriptions.get(name, f"{name} 模块")
