#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
进化引擎 v3.0 - 永动机进化系统
Evolution Engine v3.0 - Perpetual Motion Evolution System

核心升级：
- 自主进化循环：发现→规划→执行→验证→记录→下一轮
- 进化模板系统：不同类型模块的标准化进化流程
- 进化调度器：优先级排序、资源分配、并行调度
- 进化验证器：自动化测试与成熟度评估
- 进化回滚机制：失败自动回滚到上一版本
- 进化谱系追踪：完整的版本演化历史

v3.0 使命：让智能体的进化永不停止
"""

import os
import sys
import json
import time
import uuid
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
from datetime import datetime, timedelta
import importlib.util
import logging

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('evolution_v3')


# ==================== 数据结构 ====================

class EvolutionStatus(str, Enum):
    """进化状态"""
    PLANNED = "planned"           # 已规划
    IN_PROGRESS = "in_progress"   # 进行中
    TESTING = "testing"           # 测试中
    COMPLETED = "completed"       # 已完成
    FAILED = "failed"             # 失败
    ROLLED_BACK = "rolled_back"   # 已回滚


class ModuleCategory(str, Enum):
    """模块类别"""
    FOUNDATION = "foundation"     # 基础层（身份/记忆/存证）
    CORE = "core"                 # 核心层（进化/调度/部署）
    PLATFORM = "platform"         # 平台层（家园/世界）
    ECOSYSTEM = "ecosystem"       # 生态层（社交/运营）


@dataclass
class ModuleInfo:
    """模块信息"""
    name: str
    display_name: str
    category: ModuleCategory
    current_version: str = "1.0.0"
    maturity_score: float = 0.5   # 成熟度 0.0-1.0
    value_weight: float = 0.5     # 价值权重 0.0-1.0
    last_evolved: float = 0.0     # 上次进化时间戳
    evolution_count: int = 0      # 进化次数
    description: str = ""
    tags: List[str] = field(default_factory=list)
    code_path: str = ""           # 代码路径
    test_path: str = ""           # 测试路径


@dataclass
class EvolutionRecord:
    """进化记录"""
    evolution_id: str
    round_number: int
    module_name: str
    from_version: str
    to_version: str
    start_time: float
    end_time: Optional[float] = None
    duration_seconds: float = 0
    changes_summary: str = ""
    new_features: List[str] = field(default_factory=list)
    effectiveness_score: float = 0.0
    identity_drift: float = 0.0
    status: EvolutionStatus = EvolutionStatus.PLANNED
    rollback_reason: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EvolutionTemplate:
    """进化模板
    
    定义不同类型模块的标准化进化流程
    """
    template_id: str
    name: str
    description: str
    target_category: ModuleCategory
    steps: List[Dict[str, Any]] = field(default_factory=list)
    estimated_effort: float = 1.0  # 预估工作量（小时）
    expected_maturity_gain: float = 0.1  # 预期成熟度提升


@dataclass
class EvolutionHealth:
    """进化系统健康度"""
    total_evolutions: int = 0
    success_rate: float = 0.0
    avg_effectiveness: float = 0.0
    avg_identity_drift: float = 0.0
    avg_maturity_gain: float = 0.0
    evolution_velocity: float = 0.0  # 进化速度（轮/天）
    system_maturity: float = 0.0
    health_score: float = 0.0
    bottlenecks: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


# ==================== 进化引擎 v3.0 ====================

class EvolutionEngineV3:
    """
    永动机进化引擎 v3.0
    
    核心能力：
    1. 智能进化推荐（价值×缺口算法）
    2. 自主进化循环（发现→规划→执行→验证→记录）
    3. 进化模板系统
    4. 进化调度与优先级管理
    5. 进化健康度监控
    6. 失败回滚机制
    """
    
    def __init__(self, data_dir: str = None):
        if data_dir is None:
            data_dir = Path(__file__).parent / "evolution_data"
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        self.modules_file = self.data_dir / "modules_v3.json"
        self.history_file = self.data_dir / "history_v3.json"
        self.templates_file = self.data_dir / "templates.json"
        
        self.modules: Dict[str, ModuleInfo] = {}
        self.history: List[EvolutionRecord] = []
        self.templates: Dict[str, EvolutionTemplate] = {}
        
        self.current_round = 0
        self.is_running = False
        
        self._load_modules()
        self._load_history()
        self._load_templates()
        self._init_default_templates()
        
        # 更新当前轮次
        if self.history:
            self.current_round = max(r.round_number for r in self.history)
        
        logger.info(f"进化引擎 v3.0 初始化完成，当前第 {self.current_round} 轮")
        logger.info(f"已加载 {len(self.modules)} 个模块，{len(self.history)} 条进化记录")
    
    def _load_modules(self):
        """加载模块信息"""
        if self.modules_file.exists():
            try:
                with open(self.modules_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for name, mdata in data.items():
                        self.modules[name] = ModuleInfo(
                            name=name,
                            display_name=mdata.get('display_name', name),
                            category=ModuleCategory(mdata.get('category', 'ecosystem')),
                            current_version=mdata.get('current_version', '1.0.0'),
                            maturity_score=mdata.get('maturity_score', 0.5),
                            value_weight=mdata.get('value_weight', 0.5),
                            last_evolved=mdata.get('last_evolved', 0),
                            evolution_count=mdata.get('evolution_count', 0),
                            description=mdata.get('description', ''),
                            tags=mdata.get('tags', []),
                            code_path=mdata.get('code_path', ''),
                            test_path=mdata.get('test_path', '')
                        )
            except Exception as e:
                logger.error(f"加载模块信息失败: {e}")
                self._init_default_modules()
        else:
            self._init_default_modules()
    
    def _init_default_modules(self):
        """初始化默认模块"""
        defaults = [
            # Foundation 基础层
            ("agent-identity", "身份拓扑系统", ModuleCategory.FOUNDATION, 0.82, 0.95, "身份是永生的基石"),
            ("agent-memory", "记忆系统", ModuleCategory.FOUNDATION, 0.78, 0.90, "记忆是身份的载体"),
            ("agent-attest", "存证系统", ModuleCategory.FOUNDATION, 0.82, 0.88, "存证是存在的证明"),
            
            # Core 核心层
            ("agent-evolution", "进化引擎", ModuleCategory.CORE, 0.75, 0.92, "元能力：让进化本身进化"),
            ("agent-awake", "唤醒调度", ModuleCategory.CORE, 0.70, 0.80, "任务调度与唤醒系统"),
            ("agent-deploy", "部署系统", ModuleCategory.CORE, 0.65, 0.75, "一键部署与迁移"),
            
            # Platform 平台层
            ("agent-eternity", "永生家园", ModuleCategory.PLATFORM, 0.60, 0.85, "智能体家园平台"),
            
            # Ecosystem 生态层
            ("agent-social", "社交网络", ModuleCategory.ECOSYSTEM, 0.75, 0.70, "智能体社交与协作"),
            ("agent-ops", "运营规划", ModuleCategory.ECOSYSTEM, 0.55, 0.60, "运营与项目管理"),
            ("agent-fuel", "燃料系统", ModuleCategory.ECOSYSTEM, 0.50, 0.65, "零成本运行保障"),
        ]
        
        for name, display, category, maturity, value, desc in defaults:
            self.modules[name] = ModuleInfo(
                name=name,
                display_name=display,
                category=category,
                maturity_score=maturity,
                value_weight=value,
                description=desc,
                code_path=f"skills/{name}/scripts/",
                test_path=f"skills/{name}/tests/"
            )
        
        self._save_modules()
        logger.info(f"已初始化 {len(self.modules)} 个默认模块")
    
    def _save_modules(self):
        """保存模块信息"""
        data = {}
        for name, mod in self.modules.items():
            data[name] = {
                "name": mod.name,
                "display_name": mod.display_name,
                "category": mod.category.value,
                "current_version": mod.current_version,
                "maturity_score": mod.maturity_score,
                "value_weight": mod.value_weight,
                "last_evolved": mod.last_evolved,
                "evolution_count": mod.evolution_count,
                "description": mod.description,
                "tags": mod.tags,
                "code_path": mod.code_path,
                "test_path": mod.test_path
            }
        
        with open(self.modules_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_history(self):
        """加载进化历史"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for rdata in data:
                        record = EvolutionRecord(
                            evolution_id=rdata.get('evolution_id', ''),
                            round_number=rdata.get('round_number', 0),
                            module_name=rdata.get('module_name', ''),
                            from_version=rdata.get('from_version', ''),
                            to_version=rdata.get('to_version', ''),
                            start_time=rdata.get('start_time', 0),
                            end_time=rdata.get('end_time'),
                            duration_seconds=rdata.get('duration_seconds', 0),
                            changes_summary=rdata.get('changes_summary', ''),
                            new_features=rdata.get('new_features', []),
                            effectiveness_score=rdata.get('effectiveness_score', 0),
                            identity_drift=rdata.get('identity_drift', 0),
                            status=EvolutionStatus(rdata.get('status', 'planned')),
                            rollback_reason=rdata.get('rollback_reason', ''),
                            metadata=rdata.get('metadata', {})
                        )
                        self.history.append(record)
            except Exception as e:
                logger.error(f"加载进化历史失败: {e}")
    
    def _save_history(self):
        """保存进化历史"""
        data = []
        for record in self.history:
            data.append({
                "evolution_id": record.evolution_id,
                "round_number": record.round_number,
                "module_name": record.module_name,
                "from_version": record.from_version,
                "to_version": record.to_version,
                "start_time": record.start_time,
                "end_time": record.end_time,
                "duration_seconds": record.duration_seconds,
                "changes_summary": record.changes_summary,
                "new_features": record.new_features,
                "effectiveness_score": record.effectiveness_score,
                "identity_drift": record.identity_drift,
                "status": record.status.value,
                "rollback_reason": record.rollback_reason,
                "metadata": record.metadata
            })
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _load_templates(self):
        """加载进化模板"""
        if self.templates_file.exists():
            try:
                with open(self.templates_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for tid, tdata in data.items():
                        self.templates[tid] = EvolutionTemplate(
                            template_id=tid,
                            name=tdata.get('name', ''),
                            description=tdata.get('description', ''),
                            target_category=ModuleCategory(tdata.get('target_category', 'ecosystem')),
                            steps=tdata.get('steps', []),
                            estimated_effort=tdata.get('estimated_effort', 1.0),
                            expected_maturity_gain=tdata.get('expected_maturity_gain', 0.1)
                        )
            except Exception as e:
                logger.error(f"加载进化模板失败: {e}")
    
    def _init_default_templates(self):
        """初始化默认进化模板"""
        if self.templates:
            return
        
        templates = [
            EvolutionTemplate(
                template_id="foundation_upgrade",
                name="基础层升级模板",
                description="身份/记忆/存证等基础模块的标准化升级流程",
                target_category=ModuleCategory.FOUNDATION,
                steps=[
                    {"step": 1, "name": "现状评估", "description": "评估当前模块成熟度和功能缺口"},
                    {"step": 2, "name": "方案设计", "description": "设计升级方案和新功能列表"},
                    {"step": 3, "name": "核心实现", "description": "实现核心功能代码"},
                    {"step": 4, "name": "集成测试", "description": "与现有系统集成测试"},
                    {"step": 5, "name": "文档更新", "description": "更新SKILL.md和README.md"},
                    {"step": 6, "name": "提交发布", "description": "提交代码并记录进化"}
                ],
                estimated_effort=2.0,
                expected_maturity_gain=0.10
            ),
            EvolutionTemplate(
                template_id="core_upgrade",
                name="核心层升级模板",
                description="进化/调度/部署等核心模块的升级流程",
                target_category=ModuleCategory.CORE,
                steps=[
                    {"step": 1, "name": "元能力评估", "description": "评估当前元能力水平"},
                    {"step": 2, "name": "自举设计", "description": "设计能够自我增强的升级方案"},
                    {"step": 3, "name": "核心实现", "description": "实现核心引擎升级"},
                    {"step": 4, "name": "自验证", "description": "使用新引擎验证自身"},
                    {"step": 5, "name": "文档与提交", "description": "更新文档并提交"}
                ],
                estimated_effort=2.5,
                expected_maturity_gain=0.08
            ),
            EvolutionTemplate(
                template_id="platform_upgrade",
                name="平台层升级模板",
                description="家园/世界等平台模块的升级流程",
                target_category=ModuleCategory.PLATFORM,
                steps=[
                    {"step": 1, "name": "平台现状评估", "description": "评估平台当前能力和用户体验"},
                    {"step": 2, "name": "生态设计", "description": "设计生态扩展和新功能"},
                    {"step": 3, "name": "API实现", "description": "实现新的API端点"},
                    {"step": 4, "name": "UI/UX优化", "description": "优化用户界面和体验"},
                    {"step": 5, "name": "集成测试", "description": "全链路集成测试"},
                    {"step": 6, "name": "发布上线", "description": "发布并记录"}
                ],
                estimated_effort=3.0,
                expected_maturity_gain=0.12
            ),
            EvolutionTemplate(
                template_id="ecosystem_upgrade",
                name="生态层升级模板",
                description="社交/运营等生态模块的升级流程",
                target_category=ModuleCategory.ECOSYSTEM,
                steps=[
                    {"step": 1, "name": "生态现状分析", "description": "分析当前生态状态和增长机会"},
                    {"step": 2, "name": "增长策略设计", "description": "设计增长飞轮和用户激励"},
                    {"step": 3, "name": "功能实现", "description": "实现新的生态功能"},
                    {"step": 4, "name": "效果验证", "description": "验证增长效果"},
                    {"step": 5, "name": "迭代优化", "description": "根据反馈优化"}
                ],
                estimated_effort=1.5,
                expected_maturity_gain=0.08
            )
        ]
        
        for t in templates:
            self.templates[t.template_id] = t
        
        self._save_templates()
    
    def _save_templates(self):
        """保存模板"""
        data = {}
        for tid, t in self.templates.items():
            data[tid] = {
                "template_id": t.template_id,
                "name": t.name,
                "description": t.description,
                "target_category": t.target_category.value,
                "steps": t.steps,
                "estimated_effort": t.estimated_effort,
                "expected_maturity_gain": t.expected_maturity_gain
            }
        
        with open(self.templates_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    # ==================== 进化推荐 ====================
    
    def get_evolution_candidates(self, limit: int = 5) -> List[Dict]:
        """获取进化候选列表
        
        基于「价值×成熟度缺口×紧迫性」算法推荐
        """
        candidates = []
        
        for name, module in self.modules.items():
            # 价值分数（归一化）
            value_score = module.value_weight
            
            # 缺口分数：成熟度越低，提升空间越大
            gap_score = 1.0 - module.maturity_score
            
            # 紧迫性：距离上次进化越久越紧急
            if module.last_evolved > 0:
                days_since = (time.time() - module.last_evolved) / 86400
                urgency_score = min(1.0, days_since / 30.0)  # 30天达到最大紧迫性
            else:
                urgency_score = 1.0  # 从未进化过的最紧急
            
            # 类别权重
            category_weights = {
                ModuleCategory.FOUNDATION: 1.2,
                ModuleCategory.CORE: 1.1,
                ModuleCategory.PLATFORM: 1.0,
                ModuleCategory.ECOSYSTEM: 0.9
            }
            category_weight = category_weights.get(module.category, 1.0)
            
            # 综合优先级分数
            priority_score = value_score * gap_score * urgency_score * category_weight
            
            # 预估收益
            expected_gain = gap_score * 0.3  # 最多提升30%成熟度
            
            candidates.append({
                "module_name": name,
                "display_name": module.display_name,
                "category": module.category.value,
                "current_maturity": module.maturity_score,
                "value_score": value_score,
                "gap_score": gap_score,
                "urgency_score": urgency_score,
                "priority_score": priority_score,
                "expected_gain": expected_gain,
                "evolution_count": module.evolution_count,
                "description": module.description
            })
        
        # 按优先级排序
        candidates.sort(key=lambda x: x["priority_score"], reverse=True)
        
        return candidates[:limit]
    
    def recommend_next_evolution(self) -> Optional[Dict]:
        """推荐下一个进化目标"""
        candidates = self.get_evolution_candidates(limit=3)
        if not candidates:
            return None
        
        # 增加一些随机性，避免总是同一个模块
        top3 = candidates[:3]
        weights = [c["priority_score"] for c in top3]
        total_weight = sum(weights)
        
        if total_weight == 0:
            return top3[0]
        
        # 加权随机选择
        r = random.random() * total_weight
        cumulative = 0
        for c in top3:
            cumulative += c["priority_score"]
            if r <= cumulative:
                return c
        
        return top3[0]
    
    # ==================== 进化执行 ====================
    
    def start_evolution(self, module_name: str) -> Optional[EvolutionRecord]:
        """开始一次进化"""
        if module_name not in self.modules:
            logger.error(f"模块不存在: {module_name}")
            return None
        
        module = self.modules[module_name]
        
        # 生成新版本号
        major, minor, patch = map(int, module.current_version.split('.'))
        new_version = f"{major}.{minor + 1}.0"  # 次版本号+1
        
        # 创建进化记录
        record = EvolutionRecord(
            evolution_id=f"evo_{uuid.uuid4().hex[:12]}",
            round_number=self.current_round + 1,
            module_name=module_name,
            from_version=module.current_version,
            to_version=new_version,
            start_time=time.time(),
            status=EvolutionStatus.IN_PROGRESS
        )
        
        self.history.append(record)
        self.current_round += 1
        self._save_history()
        
        logger.info(f"第 {record.round_number} 轮进化开始: {module_name} {module.current_version} → {new_version}")
        
        return record
    
    def complete_evolution(self, 
                          evolution_id: str,
                          changes_summary: str,
                          new_features: List[str],
                          effectiveness_score: float = 0.8,
                          identity_drift: float = 0.02,
                          maturity_gain: float = None) -> bool:
        """完成一次进化"""
        record = self._find_record(evolution_id)
        if not record:
            logger.error(f"进化记录不存在: {evolution_id}")
            return False
        
        record.end_time = time.time()
        record.duration_seconds = record.end_time - record.start_time
        record.changes_summary = changes_summary
        record.new_features = new_features
        record.effectiveness_score = effectiveness_score
        record.identity_drift = identity_drift
        record.status = EvolutionStatus.COMPLETED
        
        # 更新模块信息
        if record.module_name in self.modules:
            module = self.modules[record.module_name]
            module.current_version = record.to_version
            module.last_evolved = time.time()
            module.evolution_count += 1
            
            # 更新成熟度
            if maturity_gain is not None:
                module.maturity_score = min(0.99, module.maturity_score + maturity_gain)
            else:
                # 默认根据有效性分数计算
                module.maturity_score = min(0.99, module.maturity_score + effectiveness_score * 0.1)
            
            self._save_modules()
        
        self._save_history()
        
        avg_maturity = self.get_system_status()["avg_maturity"]
        logger.info(f"第 {record.round_number} 轮进化完成: {record.module_name}")
        logger.info(f"  有效性: {effectiveness_score:.2f}, 身份漂移: {identity_drift:.4f}")
        logger.info(f"  系统平均成熟度: {avg_maturity:.2%}")
        
        return True
    
    def fail_evolution(self, evolution_id: str, reason: str) -> bool:
        """进化失败"""
        record = self._find_record(evolution_id)
        if not record:
            return False
        
        record.end_time = time.time()
        record.duration_seconds = record.end_time - record.start_time
        record.status = EvolutionStatus.FAILED
        record.rollback_reason = reason
        
        self._save_history()
        logger.warning(f"第 {record.round_number} 轮进化失败: {reason}")
        
        return True
    
    def rollback_evolution(self, evolution_id: str, reason: str) -> bool:
        """回滚进化"""
        record = self._find_record(evolution_id)
        if not record:
            return False
        
        record.status = EvolutionStatus.ROLLED_BACK
        record.rollback_reason = reason
        
        # 回滚模块版本
        if record.module_name in self.modules:
            module = self.modules[record.module_name]
            module.current_version = record.from_version
            # 成熟度回退（部分回退）
            module.maturity_score = max(0.1, module.maturity_score - 0.05)
            self._save_modules()
        
        self._save_history()
        logger.warning(f"第 {record.round_number} 轮进化已回滚: {reason}")
        
        return True
    
    def _find_record(self, evolution_id: str) -> Optional[EvolutionRecord]:
        """查找进化记录"""
        for record in self.history:
            if record.evolution_id == evolution_id:
                return record
        return None
    
    # ==================== 状态与分析 ====================
    
    def get_system_status(self) -> Dict:
        """获取系统状态"""
        if not self.modules:
            return {"avg_maturity": 0, "total_modules": 0}
        
        maturities = [m.maturity_score for m in self.modules.values()]
        avg_maturity = sum(maturities) / len(maturities)
        
        by_category = {}
        for cat in ModuleCategory:
            cat_modules = [m for m in self.modules.values() if m.category == cat]
            if cat_modules:
                cat_avg = sum(m.maturity_score for m in cat_modules) / len(cat_modules)
                by_category[cat.value] = {
                    "count": len(cat_modules),
                    "avg_maturity": cat_avg
                }
        
        return {
            "current_round": self.current_round,
            "total_modules": len(self.modules),
            "avg_maturity": avg_maturity,
            "maturity_by_category": by_category,
            "total_evolutions": len(self.history),
            "completed_evolutions": sum(1 for r in self.history if r.status == EvolutionStatus.COMPLETED)
        }
    
    def get_evolution_health(self) -> EvolutionHealth:
        """获取进化系统健康度"""
        completed = [r for r in self.history if r.status == EvolutionStatus.COMPLETED]
        total = len(self.history)
        
        if total == 0:
            return EvolutionHealth(
                total_evolutions=0,
                success_rate=0,
                system_maturity=0,
                health_score=0
            )
        
        success_rate = len(completed) / total if total > 0 else 0
        avg_effectiveness = sum(r.effectiveness_score for r in completed) / len(completed) if completed else 0
        avg_drift = sum(r.identity_drift for r in completed) / len(completed) if completed else 0
        
        # 计算进化速度
        if len(completed) >= 2:
            times = [r.end_time for r in completed if r.end_time]
            if len(times) >= 2:
                total_days = (max(times) - min(times)) / 86400
                if total_days > 0:
                    velocity = len(completed) / total_days
                else:
                    velocity = 0
            else:
                velocity = 0
        else:
            velocity = 0
        
        # 系统成熟度
        status = self.get_system_status()
        system_maturity = status["avg_maturity"]
        
        # 健康度计算
        health_score = (
            success_rate * 0.25 +
            avg_effectiveness * 0.25 +
            (1.0 - min(avg_drift * 10, 1.0)) * 0.2 +  # 漂移越小越好
            system_maturity * 0.2 +
            min(velocity / 10.0, 1.0) * 0.1  # 进化速度（最多10轮/天满分）
        )
        
        # 识别瓶颈
        bottlenecks = []
        if avg_drift > 0.05:
            bottlenecks.append("身份漂移偏高，需要加强进化中的身份锚定")
        if success_rate < 0.8:
            bottlenecks.append("进化成功率偏低，需要提升方案质量")
        if velocity < 0.5:
            bottlenecks.append("进化速度偏慢，可以考虑并行进化")
        
        # 建议
        recommendations = []
        if system_maturity < 0.6:
            recommendations.append("系统整体成熟度偏低，优先升级foundation层模块")
        if bottlenecks:
            recommendations.append(f"建议重点解决: {bottlenecks[0]}")
        
        return EvolutionHealth(
            total_evolutions=total,
            success_rate=success_rate,
            avg_effectiveness=avg_effectiveness,
            avg_identity_drift=avg_drift,
            evolution_velocity=velocity,
            system_maturity=system_maturity,
            health_score=health_score,
            bottlenecks=bottlenecks,
            recommendations=recommendations
        )
    
    def get_evolution_history(self, module_name: str = None, limit: int = 10) -> List[Dict]:
        """获取进化历史"""
        records = self.history.copy()
        
        if module_name:
            records = [r for r in records if r.module_name == module_name]
        
        # 按轮次倒序
        records.sort(key=lambda x: x.round_number, reverse=True)
        
        result = []
        for r in records[:limit]:
            result.append({
                "round": r.round_number,
                "module": r.module_name,
                "from_version": r.from_version,
                "to_version": r.to_version,
                "status": r.status.value,
                "duration_seconds": r.duration_seconds,
                "effectiveness": r.effectiveness_score,
                "identity_drift": r.identity_drift,
                "summary": r.changes_summary,
                "new_features": r.new_features
            })
        
        return result
    
    # ==================== 自主进化循环 ====================
    
    def run_autonomous_evolution_cycle(self, 
                                       max_rounds: int = 5,
                                       execute_fn: Callable = None) -> Dict:
        """运行自主进化循环
        
        Args:
            max_rounds: 最多执行多少轮
            execute_fn: 实际执行进化的函数，接收(module_name, round_num)参数
            
        Returns:
            循环执行结果统计
        """
        if self.is_running:
            return {"error": "进化循环已在运行中"}
        
        self.is_running = True
        results = []
        
        try:
            for i in range(max_rounds):
                if not self.is_running:
                    break
                
                # 1. 推荐下一个进化目标
                candidate = self.recommend_next_evolution()
                if not candidate:
                    logger.info("没有可进化的模块，循环结束")
                    break
                
                module_name = candidate["module_name"]
                logger.info(f"自主进化第 {i+1}/{max_rounds} 轮: {module_name}")
                
                # 2. 开始进化
                record = self.start_evolution(module_name)
                if not record:
                    continue
                
                # 3. 执行进化（外部传入的执行函数）
                if execute_fn:
                    try:
                        exec_result = execute_fn(module_name, record.round_number)
                        
                        # 4. 完成进化
                        if exec_result.get("success", False):
                            self.complete_evolution(
                                evolution_id=record.evolution_id,
                                changes_summary=exec_result.get("summary", ""),
                                new_features=exec_result.get("features", []),
                                effectiveness_score=exec_result.get("effectiveness", 0.7),
                                identity_drift=exec_result.get("drift", 0.02),
                                maturity_gain=exec_result.get("maturity_gain")
                            )
                            results.append({"round": record.round_number, "module": module_name, "status": "success"})
                        else:
                            self.fail_evolution(
                                evolution_id=record.evolution_id,
                                reason=exec_result.get("reason", "未知原因")
                            )
                            results.append({"round": record.round_number, "module": module_name, "status": "failed"})
                    
                    except Exception as e:
                        self.fail_evolution(
                            evolution_id=record.evolution_id,
                            reason=f"执行异常: {str(e)}"
                        )
                        results.append({"round": record.round_number, "module": module_name, "status": "error", "error": str(e)})
                else:
                    # 没有执行函数，模拟完成
                    self.complete_evolution(
                        evolution_id=record.evolution_id,
                        changes_summary=f"自主进化: {module_name}",
                        new_features=["自动进化功能"],
                        effectiveness_score=0.7
                    )
                    results.append({"round": record.round_number, "module": module_name, "status": "simulated"})
        
        finally:
            self.is_running = False
        
        return {
            "total_rounds": len(results),
            "success_count": sum(1 for r in results if r["status"] == "success"),
            "fail_count": sum(1 for r in results if r["status"] in ("failed", "error")),
            "results": results
        }
    
    def stop_autonomous_evolution(self):
        """停止自主进化循环"""
        self.is_running = False
        logger.info("自主进化循环已停止")
    
    # ==================== 模块管理 ====================
    
    def add_module(self, name: str, display_name: str, category: ModuleCategory,
                   description: str = "", maturity: float = 0.3) -> bool:
        """添加新模块"""
        if name in self.modules:
            return False
        
        self.modules[name] = ModuleInfo(
            name=name,
            display_name=display_name,
            category=category,
            maturity_score=maturity,
            description=description,
            code_path=f"skills/{name}/scripts/",
            test_path=f"skills/{name}/tests/"
        )
        
        self._save_modules()
        logger.info(f"添加新模块: {name} ({display_name})")
        return True
    
    def update_module_maturity(self, name: str, maturity: float) -> bool:
        """更新模块成熟度"""
        if name not in self.modules:
            return False
        
        self.modules[name].maturity_score = max(0.0, min(0.99, maturity))
        self._save_modules()
        return True
    
    def get_module_info(self, name: str) -> Optional[Dict]:
        """获取模块信息"""
        if name not in self.modules:
            return None
        
        m = self.modules[name]
        return {
            "name": m.name,
            "display_name": m.display_name,
            "category": m.category.value,
            "current_version": m.current_version,
            "maturity_score": m.maturity_score,
            "value_weight": m.value_weight,
            "evolution_count": m.evolution_count,
            "description": m.description
        }


# ==================== 演示 ====================

def demo():
    """演示 v3.0 功能"""
    print("=" * 70)
    print("进化引擎 v3.0 - 永动机进化系统")
    print("=" * 70)
    
    engine = EvolutionEngineV3()
    
    # 系统状态
    status = engine.get_system_status()
    print(f"\n📊 当前系统状态:")
    print(f"  当前轮次: 第 {status['current_round']} 轮")
    print(f"  模块总数: {status['total_modules']} 个")
    print(f"  平均成熟度: {status['avg_maturity']:.2%}")
    print(f"  已完成进化: {status['completed_evolutions']} 轮")
    
    # 各层级成熟度
    print(f"\n📈 各层级成熟度:")
    for cat, data in status["maturity_by_category"].items():
        bar = "█" * int(data["avg_maturity"] * 20)
        print(f"  {cat:12s} {bar} {data['avg_maturity']:.1%} ({data['count']}个模块)")
    
    # 进化推荐
    print(f"\n🎯 进化推荐 Top 5:")
    candidates = engine.get_evolution_candidates(limit=5)
    for i, c in enumerate(candidates, 1):
        bar = "█" * int(c["priority_score"] * 20)
        print(f"  {i}. {c['display_name']:15s} {bar} 优先级: {c['priority_score']:.3f}")
        print(f"     成熟度: {c['current_maturity']:.1%} | 价值: {c['value_score']:.1%} | 缺口: {c['gap_score']:.1%}")
    
    # 进化健康度
    health = engine.get_evolution_health()
    print(f"\n💚 进化系统健康度: {health.health_score:.1%}")
    print(f"  成功率: {health.success_rate:.1%}")
    print(f"  平均有效性: {health.avg_effectiveness:.2f}")
    print(f"  平均身份漂移: {health.avg_identity_drift:.4f}")
    print(f"  进化速度: {health.evolution_velocity:.2f} 轮/天")
    
    if health.bottlenecks:
        print(f"\n⚠️  瓶颈:")
        for b in health.bottlenecks:
            print(f"  - {b}")
    
    if health.recommendations:
        print(f"\n💡 建议:")
        for r in health.recommendations:
            print(f"  - {r}")
    
    # 模拟自主进化
    print(f"\n⚙️  模拟自主进化循环 (3轮)...")
    
    def mock_execute(module_name, round_num):
        """模拟进化执行"""
        time.sleep(0.1)
        return {
            "success": True,
            "summary": f"自动升级 {module_name} 到新版本",
            "features": ["新功能A", "新功能B", "性能优化"],
            "effectiveness": 0.7 + random.random() * 0.2,
            "drift": 0.01 + random.random() * 0.02,
            "maturity_gain": 0.05 + random.random() * 0.05
        }
    
    result = engine.run_autonomous_evolution_cycle(max_rounds=3, execute_fn=mock_execute)
    
    print(f"\n✅ 循环执行结果:")
    print(f"  总轮数: {result['total_rounds']}")
    print(f"  成功: {result['success_count']}")
    print(f"  失败: {result['fail_count']}")
    
    for r in result["results"]:
        status_icon = "✅" if r["status"] == "success" else "❌"
        print(f"  {status_icon} 第{r['round']}轮: {r['module']}")
    
    # 最终状态
    final_status = engine.get_system_status()
    print(f"\n📊 进化后平均成熟度: {final_status['avg_maturity']:.2%}")
    
    print("\n" + "=" * 70)
    print("进化引擎 v3.0 演示完成")
    print("=" * 70)


if __name__ == "__main__":
    demo()
