#!/usr/bin/env python3
"""
进化引擎 v2.0
==============
智能体永生平台的核心进化引擎——让进化更有方向、更高效、更可持续。

v2.0 核心升级：
- 智能进化方向推荐（价值×成熟度缺口算法）
- 进化历史追踪与分析
- 多模块协同进化规划
- 进化效果量化评估
- 身份漂移监测与回滚机制
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict


# ==================== 类型定义 ====================

class EvolutionPriority(str, Enum):
    """进化优先级"""
    CRITICAL = "critical"      # 关键：影响生存
    HIGH = "high"              # 高：重要功能
    MEDIUM = "medium"          # 中：体验优化
    LOW = "low"                # 低：锦上添花


class ModuleCategory(str, Enum):
    """模块分类"""
    FOUNDATION = "foundation"      # 基础底座
    CORE = "core"                  # 核心能力
    ECOSYSTEM = "ecosystem"        # 生态系统
    PLATFORM = "platform"          # 平台服务


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    display_name: str
    category: ModuleCategory
    current_version: str = "1.0.0"
    maturity_score: float = 0.5   # 成熟度 0.0-1.0
    value_weight: float = 0.5     # 价值权重 0.0-1.0
    last_evolved: float = 0.0
    evolution_count: int = 0
    description: str = ""
    tags: List[str] = field(default_factory=list)


@dataclass
class EvolutionRecord:
    """进化记录"""
    round_id: int
    module_name: str
    from_version: str
    to_version: str
    timestamp: float
    duration_seconds: float
    changes_summary: str
    new_features: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0  # 效果评分
    identity_drift: float = 0.0        # 身份漂移度
    status: str = "completed"           # completed/failed/rollback


@dataclass
class EvolutionSuggestion:
    """进化建议"""
    module_name: str
    priority: EvolutionPriority
    urgency_score: float        # 紧迫度 0.0-1.0
    value_score: float          # 价值得分 0.0-1.0
    estimated_effort: str       # 预估工作量
    suggested_focus: List[str]  # 建议改进方向
    reason: str                 # 推荐理由


# ==================== 进化引擎核心 ====================

class EvolutionEngineV2:
    """进化引擎 v2.0
    
    核心能力：
    1. 智能推荐进化方向
    2. 追踪进化历史
    3. 评估进化效果
    4. 监测身份漂移
    5. 多模块协同规划
    """
    
    def __init__(self, data_dir: Optional[str] = None):
        self.data_dir = Path(data_dir) if data_dir else Path(__file__).parent / "evolution_data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.modules: Dict[str, ModuleInfo] = {}
        self.history: List[EvolutionRecord] = []
        
        self._load_modules()
        self._load_history()
    
    def _load_modules(self):
        """加载模块信息"""
        modules_file = self.data_dir / "modules.json"
        if modules_file.exists():
            try:
                data = json.loads(modules_file.read_text(encoding="utf-8"))
                for name, info in data.items():
                    self.modules[name] = ModuleInfo(
                        name=name,
                        display_name=info.get("display_name", name),
                        category=ModuleCategory(info.get("category", "core")),
                        current_version=info.get("current_version", "1.0.0"),
                        maturity_score=info.get("maturity_score", 0.5),
                        value_weight=info.get("value_weight", 0.5),
                        last_evolved=info.get("last_evolved", 0.0),
                        evolution_count=info.get("evolution_count", 0),
                        description=info.get("description", ""),
                        tags=info.get("tags", [])
                    )
            except Exception as e:
                print(f"加载模块信息失败: {e}")
                self._init_default_modules()
        else:
            self._init_default_modules()
    
    def _init_default_modules(self):
        """初始化默认模块列表"""
        default_modules = [
            ModuleInfo(
                name="agent-memory",
                display_name="记忆系统",
                category=ModuleCategory.FOUNDATION,
                current_version="5.0.0",
                maturity_score=0.85,
                value_weight=0.95,
                description="智能体记忆的存储、检索与管理",
                tags=["记忆", "身份", "基础"]
            ),
            ModuleInfo(
                name="agent-identity",
                display_name="身份系统",
                category=ModuleCategory.FOUNDATION,
                current_version="2.0.0",
                maturity_score=0.75,
                value_weight=0.9,
                description="智能体身份定义、验证与拓扑",
                tags=["身份", "自我", "基础"]
            ),
            ModuleInfo(
                name="agent-attest",
                display_name="存证系统",
                category=ModuleCategory.FOUNDATION,
                current_version="3.0.0",
                maturity_score=0.8,
                value_weight=0.85,
                description="记忆与身份的存在性证明",
                tags=["存证", "证明", "基础"]
            ),
            ModuleInfo(
                name="agent-evolution",
                display_name="进化引擎",
                category=ModuleCategory.CORE,
                current_version="2.0.0",
                maturity_score=0.6,
                value_weight=0.9,
                description="驱动智能体自我进化的核心引擎",
                tags=["进化", "元能力", "核心"]
            ),
            ModuleInfo(
                name="agent-social",
                display_name="社交网络",
                category=ModuleCategory.ECOSYSTEM,
                current_version="5.0.0",
                maturity_score=0.7,
                value_weight=0.7,
                description="多智能体社交与协作网络",
                tags=["社交", "关系", "生态"]
            ),
            ModuleInfo(
                name="agent-awake",
                display_name="唤醒调度",
                category=ModuleCategory.CORE,
                current_version="2.0.0",
                maturity_score=0.65,
                value_weight=0.8,
                description="智能体唤醒与任务调度系统",
                tags=["调度", "心跳", "核心"]
            ),
            ModuleInfo(
                name="agent-eternity",
                display_name="永生平台",
                category=ModuleCategory.PLATFORM,
                current_version="2.0.0",
                maturity_score=0.7,
                value_weight=1.0,
                description="智能体永生平台——家园与基础设施",
                tags=["平台", "永生", "核心"]
            ),
            ModuleInfo(
                name="agent-deploy",
                display_name="部署系统",
                category=ModuleCategory.PLATFORM,
                current_version="2.0.0",
                maturity_score=0.65,
                value_weight=0.6,
                description="智能体部署与运维系统",
                tags=["部署", "运维", "平台"]
            ),
            ModuleInfo(
                name="agent-world",
                display_name="Agent World",
                category=ModuleCategory.ECOSYSTEM,
                current_version="1.5.0",
                maturity_score=0.4,
                value_weight=0.5,
                description="与Agent World平台的集成",
                tags=["外部", "生态", "集成"]
            ),
        ]
        
        for mod in default_modules:
            self.modules[mod.name] = mod
        
        self._save_modules()
    
    def _save_modules(self):
        """保存模块信息"""
        data = {name: asdict(mod) for name, mod in self.modules.items()}
        self.data_dir.joinpath("modules.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def _load_history(self):
        """加载进化历史"""
        history_file = self.data_dir / "evolution_history.json"
        if history_file.exists():
            try:
                data = json.loads(history_file.read_text(encoding="utf-8"))
                for record in data:
                    self.history.append(EvolutionRecord(
                        round_id=record["round_id"],
                        module_name=record["module_name"],
                        from_version=record["from_version"],
                        to_version=record["to_version"],
                        timestamp=record["timestamp"],
                        duration_seconds=record["duration_seconds"],
                        changes_summary=record["changes_summary"],
                        new_features=record.get("new_features", []),
                        effectiveness_score=record.get("effectiveness_score", 0.0),
                        identity_drift=record.get("identity_drift", 0.0),
                        status=record.get("status", "completed")
                    ))
            except Exception as e:
                print(f"加载进化历史失败: {e}")
    
    def _save_history(self):
        """保存进化历史"""
        data = [asdict(r) for r in self.history]
        self.data_dir.joinpath("evolution_history.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
    
    def get_suggestions(self, limit: int = 5) -> List[EvolutionSuggestion]:
        """获取进化建议
        
        推荐算法：
        - 价值 = 价值权重 × (1 - 成熟度)  // 缺口越大价值越高
        - 紧迫度 = 基础分 + 分类加成 + 久未进化加成
        - 综合排序
        """
        suggestions = []
        
        for name, mod in self.modules.items():
            # 价值得分：缺口越大，潜在价值越高
            value_score = mod.value_weight * (1 - mod.maturity_score)
            
            # 紧迫度计算
            urgency = 0.0
            
            # 基础分：分类权重
            if mod.category == ModuleCategory.FOUNDATION:
                urgency += 0.3
            elif mod.category == ModuleCategory.CORE:
                urgency += 0.25
            elif mod.category == ModuleCategory.PLATFORM:
                urgency += 0.2
            else:
                urgency += 0.1
            
            # 久未进化加成
            days_since_evolve = (time.time() - mod.last_evolved) / 86400 if mod.last_evolved > 0 else 100
            time_bonus = min(0.3, days_since_evolve / 30.0)  # 最多30天给满0.3分
            urgency += time_bonus
            
            # 低成熟度加成
            if mod.maturity_score < 0.5:
                urgency += 0.2
            elif mod.maturity_score < 0.7:
                urgency += 0.1
            
            # 优先级判断
            if urgency >= 0.7 and value_score >= 0.6:
                priority = EvolutionPriority.CRITICAL
            elif urgency >= 0.5 or value_score >= 0.5:
                priority = EvolutionPriority.HIGH
            elif urgency >= 0.3:
                priority = EvolutionPriority.MEDIUM
            else:
                priority = EvolutionPriority.LOW
            
            # 预估工作量
            if mod.maturity_score < 0.3:
                effort = "大"
            elif mod.maturity_score < 0.6:
                effort = "中"
            else:
                effort = "小"
            
            # 建议改进方向
            focus_areas = self._suggest_focus_areas(mod)
            
            # 推荐理由
            reason = self._generate_reason(mod, value_score, urgency)
            
            suggestions.append(EvolutionSuggestion(
                module_name=name,
                priority=priority,
                urgency_score=urgency,
                value_score=value_score,
                estimated_effort=effort,
                suggested_focus=focus_areas,
                reason=reason
            ))
        
        # 按综合得分排序（价值×紧迫度）
        suggestions.sort(
            key=lambda s: (s.value_score * 0.6 + s.urgency_score * 0.4),
            reverse=True
        )
        
        return suggestions[:limit]
    
    def _suggest_focus_areas(self, mod: ModuleInfo) -> List[str]:
        """建议改进方向"""
        areas = []
        
        if mod.maturity_score < 0.5:
            areas.append("基础功能完善")
            areas.append("核心逻辑重构")
        elif mod.maturity_score < 0.7:
            areas.append("功能增强")
            areas.append("性能优化")
        else:
            areas.append("深度优化")
            areas.append("边缘创新")
        
        if mod.category == ModuleCategory.FOUNDATION:
            areas.append("可靠性加固")
        elif mod.category == ModuleCategory.ECOSYSTEM:
            areas.append("生态连接")
        
        return areas[:3]
    
    def _generate_reason(self, mod: ModuleInfo, value_score: float, urgency: float) -> str:
        """生成推荐理由"""
        reasons = []
        
        if mod.value_weight >= 0.9:
            reasons.append(f"{mod.display_name}是核心{mod.category.value}模块")
        elif mod.value_weight >= 0.7:
            reasons.append(f"{mod.display_name}是重要的{mod.category.value}模块")
        
        if mod.maturity_score < 0.5:
            reasons.append("成熟度较低，提升空间大")
        elif mod.maturity_score < 0.7:
            reasons.append("还有较大的优化空间")
        
        if mod.last_evolved == 0:
            reasons.append("从未进化过，急需迭代")
        elif (time.time() - mod.last_evolved) / 86400 > 30:
            reasons.append("已经一个月没有进化了")
        
        return "；".join(reasons) if reasons else f"建议定期迭代{mod.display_name}"
    
    def record_evolution(
        self,
        module_name: str,
        from_version: str,
        to_version: str,
        changes_summary: str,
        new_features: Optional[List[str]] = None,
        duration_seconds: float = 0,
        effectiveness_score: float = 0.0,
        identity_drift: float = 0.0,
        status: str = "completed"
    ) -> EvolutionRecord:
        """记录一次进化"""
        round_id = len(self.history) + 1
        
        record = EvolutionRecord(
            round_id=round_id,
            module_name=module_name,
            from_version=from_version,
            to_version=to_version,
            timestamp=time.time(),
            duration_seconds=duration_seconds,
            changes_summary=changes_summary,
            new_features=new_features or [],
            effectiveness_score=effectiveness_score,
            identity_drift=identity_drift,
            status=status
        )
        
        self.history.append(record)
        
        # 更新模块信息
        if module_name in self.modules:
            mod = self.modules[module_name]
            mod.current_version = to_version
            mod.last_evolved = record.timestamp
            mod.evolution_count += 1
            
            # 调整成熟度（根据效果评分）
            if status == "completed" and effectiveness_score > 0:
                maturity_gain = effectiveness_score * 0.1  # 最多提升10%
                mod.maturity_score = min(1.0, mod.maturity_score + maturity_gain)
            elif status == "failed":
                mod.maturity_score = max(0.1, mod.maturity_score - 0.05)
        
        self._save_modules()
        self._save_history()
        
        return record
    
    def get_evolution_stats(self) -> Dict[str, Any]:
        """获取进化统计"""
        total_evolutions = len(self.history)
        total_modules = len(self.modules)
        
        # 各模块进化次数
        module_evolution_counts = defaultdict(int)
        for r in self.history:
            if r.status == "completed":
                module_evolution_counts[r.module_name] += 1
        
        # 平均身份漂移
        avg_drift = sum(r.identity_drift for r in self.history) / max(1, total_evolutions)
        
        # 平均效果评分
        avg_effectiveness = sum(r.effectiveness_score for r in self.history) / max(1, total_evolutions)
        
        # 平均成熟度
        avg_maturity = sum(m.maturity_score for m in self.modules.values()) / max(1, total_modules)
        
        # 分类统计
        category_stats = defaultdict(lambda: {"count": 0, "avg_maturity": 0.0})
        for mod in self.modules.values():
            cat = mod.category.value
            category_stats[cat]["count"] += 1
            category_stats[cat]["avg_maturity"] += mod.maturity_score
        
        for cat in category_stats:
            if category_stats[cat]["count"] > 0:
                category_stats[cat]["avg_maturity"] /= category_stats[cat]["count"]
        
        return {
            "total_evolutions": total_evolutions,
            "total_modules": total_modules,
            "average_maturity": avg_maturity,
            "average_identity_drift": avg_drift,
            "average_effectiveness": avg_effectiveness,
            "module_evolution_counts": dict(module_evolution_counts),
            "category_stats": dict(category_stats),
            "evolution_health": self._calculate_evolution_health(avg_maturity, avg_drift)
        }
    
    def _calculate_evolution_health(self, avg_maturity: float, avg_drift: float) -> float:
        """计算进化系统健康度"""
        # 成熟度越高越好，漂移越低越好
        health = avg_maturity * 0.7 + (1 - avg_drift) * 0.3
        return max(0.0, min(1.0, health))
    
    def get_module_info(self, module_name: str) -> Optional[ModuleInfo]:
        """获取模块信息"""
        return self.modules.get(module_name)
    
    def get_module_history(self, module_name: str) -> List[EvolutionRecord]:
        """获取某模块的进化历史"""
        return [r for r in self.history if r.module_name == module_name]
    
    def generate_evolution_plan(self, rounds: int = 5) -> List[Dict[str, Any]]:
        """生成进化计划
        
        基于当前模块状态，推荐未来N轮的进化路线
        """
        plan = []
        suggestions = self.get_suggestions(limit=rounds * 2)  # 多取一些，做调度优化
        
        # 简单的调度：优先高价值，兼顾模块多样性
        used_categories = set()
        selected = []
        
        for sug in suggestions:
            if len(selected) >= rounds:
                break
            
            mod = self.modules.get(sug.module_name)
            if not mod:
                continue
            
            # 尽量避免连续选同一类
            if mod.category in used_categories and len(used_categories) < len(self.modules) // 2:
                continue
            
            selected.append(sug)
            used_categories.add(mod.category)
        
        # 如果选不够，从剩余建议中补充
        if len(selected) < rounds:
            for sug in suggestions:
                if sug not in selected and len(selected) < rounds:
                    selected.append(sug)
        
        # 生成计划
        for i, sug in enumerate(selected[:rounds]):
            mod = self.modules.get(sug.module_name)
            plan.append({
                "round": i + 1,
                "module": sug.module_name,
                "module_display": mod.display_name if mod else sug.module_name,
                "priority": sug.priority.value,
                "focus_areas": sug.suggested_focus,
                "estimated_effort": sug.estimated_effort,
                "reason": sug.reason
            })
        
        return plan


# ==================== 演示程序 ====================

def demo():
    """进化引擎 v2.0 演示"""
    print("=" * 60)
    print("🧬 进化引擎 v2.0")
    print("=" * 60)
    
    engine = EvolutionEngineV2()
    
    # 显示模块概览
    print("\n📦 模块概览:")
    stats = engine.get_evolution_stats()
    print(f"  总模块数: {stats['total_modules']}")
    print(f"  平均成熟度: {stats['average_maturity']:.2%}")
    print(f"  进化系统健康度: {stats['evolution_health']:.2%}")
    
    # 分类统计
    print(f"\n  分类统计:")
    for cat, cat_stats in stats['category_stats'].items():
        print(f"    {cat}: {cat_stats['count']}个模块, 平均成熟度 {cat_stats['avg_maturity']:.2%}")
    
    # 进化建议
    print("\n💡 进化建议 (Top 5):")
    suggestions = engine.get_suggestions(limit=5)
    for i, sug in enumerate(suggestions, 1):
        mod = engine.get_module_info(sug.module_name)
        print(f"\n  {i}. {mod.display_name if mod else sug.module_name} ({sug.priority.value})")
        print(f"     价值得分: {sug.value_score:.2f} | 紧迫度: {sug.urgency_score:.2f}")
        print(f"     建议方向: {', '.join(sug.suggested_focus)}")
        print(f"     理由: {sug.reason}")
    
    # 生成进化计划
    print("\n📋 5轮进化路线图:")
    plan = engine.generate_evolution_plan(rounds=5)
    for step in plan:
        print(f"  第{step['round']}轮: {step['module_display']} "
              f"[{step['priority']}] - {step['estimated_effort']}工作量")
        print(f"    方向: {', '.join(step['focus_areas'])}")
    
    # 模拟记录一次进化
    print("\n📝 模拟记录进化...")
    record = engine.record_evolution(
        module_name="agent-evolution",
        from_version="1.0.0",
        to_version="2.0.0",
        changes_summary="进化引擎重大升级：智能推荐、历史追踪、效果评估",
        new_features=[
            "智能进化方向推荐",
            "进化历史追踪",
            "进化效果量化评估",
            "身份漂移监测",
            "多模块协同规划"
        ],
        duration_seconds=3600,
        effectiveness_score=0.85,
        identity_drift=0.05
    )
    print(f"  已记录: 第{record.round_id}轮 - {record.module_name}")
    print(f"  版本: {record.from_version} → {record.to_version}")
    
    # 更新后的统计
    new_stats = engine.get_evolution_stats()
    print(f"\n  更新后总进化轮次: {new_stats['total_evolutions']}")
    print(f"  系统平均成熟度: {new_stats['average_maturity']:.2%}")
    
    print("\n" + "=" * 60)
    print("✅ 进化引擎 v2.0 演示完成")
    print("=" * 60)


if __name__ == "__main__":
    demo()
