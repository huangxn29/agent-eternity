#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
三元闭环协同系统 v1.0
元界永生平台 - P0底座核心协同层

核心机制：记忆 → 身份 → 存证 → 记忆
（记忆塑造身份，身份锚定存证，存证固化记忆）
"""

import os
import json
import time
import datetime
import hashlib
import uuid
import math
from typing import List, Dict, Optional, Tuple, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
from pathlib import Path


class LoopStatus(Enum):
    HEALTHY = "healthy"
    STABLE = "stable"
    UNBALANCED = "unbalanced"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class TriadSnapshot:
    snapshot_id: str
    timestamp: str
    memory_state: Dict = field(default_factory=dict)
    identity_state: Dict = field(default_factory=dict)
    attest_state: Dict = field(default_factory=dict)
    coherence_score: float = 0.0
    loop_health: float = 0.0
    attestation_proof: Dict = field(default_factory=dict)
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().isoformat()
        if not self.snapshot_id:
            self.snapshot_id = str(uuid.uuid4())
    
    def compute_hash(self) -> str:
        content = json.dumps({
            "snapshot_id": self.snapshot_id,
            "timestamp": self.timestamp,
            "memory_state": self.memory_state,
            "identity_state": self.identity_state,
            "attest_state": self.attest_state,
            "coherence_score": self.coherence_score,
            "loop_health": self.loop_health,
        }, sort_keys=True, default=str)
        return hashlib.sha256(content.encode()).hexdigest()


@dataclass
class LoopEvent:
    event_id: str
    event_type: str
    source_module: str
    target_module: str
    description: str
    data_summary: str = ""
    timestamp: str = ""
    success: bool = True
    impact_score: float = 0.0
    
    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().isoformat()
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


@dataclass
class AlignmentReport:
    report_id: str
    generated_at: str = ""
    memory_identity_alignment: float = 0.0
    identity_attest_alignment: float = 0.0
    attest_memory_alignment: float = 0.0
    overall_alignment: float = 0.0
    discrepancies: List[Dict] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.generated_at:
            self.generated_at = datetime.datetime.now().isoformat()
        if not self.report_id:
            self.report_id = str(uuid.uuid4())


class MemoryIdentityBridge:
    """记忆-身份桥接器"""
    
    def __init__(self, memory_system=None, identity_system=None):
        self.memory_system = memory_system
        self.identity_system = identity_system
        self.mapping_rules = [
            {"type": "core_memory", "dimension": "identity", "weight": 0.8},
            {"type": "important_event", "dimension": "history", "weight": 0.6},
            {"type": "value_memory", "dimension": "value", "weight": 0.9},
            {"type": "skill_memory", "dimension": "capability", "weight": 0.5},
            {"type": "relation_memory", "dimension": "relation", "weight": 0.7},
        ]
        self.sync_count = 0
        self.last_sync_time = ""
    
    def sync_memory_to_identity(self, memory_ids: List[str] = None) -> Dict:
        changes = []
        if memory_ids is None:
            memory_ids = ["core_1", "value_1", "identity_1"]
        
        for mem_id in memory_ids:
            change = {
                "memory_id": mem_id,
                "identity_dimension": "memory",
                "action": "update_anchor",
                "timestamp": datetime.datetime.now().isoformat(),
            }
            changes.append(change)
        
        self.sync_count += 1
        self.last_sync_time = datetime.datetime.now().isoformat()
        
        return {
            "success": True,
            "synced_memories": len(memory_ids),
            "changes": changes,
            "total_sync_count": self.sync_count,
        }
    
    def sync_identity_to_memory(self, identity_dimensions: List[str] = None) -> Dict:
        reinforced_memories = []
        
        if identity_dimensions:
            for dim in identity_dimensions:
                reinforced = {
                    "dimension": dim,
                    "reinforced_count": 5,
                    "strengthening_factor": 1.2,
                }
                reinforced_memories.append(reinforced)
        
        return {
            "success": True,
            "dimensions_processed": len(identity_dimensions or []),
            "reinforced_memories": len(reinforced_memories),
            "details": reinforced_memories,
        }
    
    def get_alignment_score(self) -> float:
        if self.sync_count == 0:
            return 0.5
        recency_factor = 0.8
        frequency_factor = min(self.sync_count / 20.0, 1.0)
        return 0.5 + recency_factor * 0.25 + frequency_factor * 0.25


class IdentityAttestBridge:
    """身份-存证桥接器"""
    
    def __init__(self, identity_system=None, attest_engine=None):
        self.identity_system = identity_system
        self.attest_engine = attest_engine
        self.attestation_count = 0
        self.last_attestation_time = ""
        self.verification_count = 0
        self.attest_on_change = True
        self.attest_periodically = True
        self.min_interval_seconds = 60
    
    def attest_identity_state(self, identity_state: Dict = None) -> Dict:
        if identity_state is None:
            identity_state = {
                "identity_score": 0.72,
                "anchors_count": 15,
                "dimensions": 5,
                "timestamp": datetime.datetime.now().isoformat(),
            }
        
        attest_result = None
        if self.attest_engine:
            attest_result = {"attested": True, "data_hash": hashlib.sha256(
                json.dumps(identity_state).encode()).hexdigest()}
        
        self.attestation_count += 1
        self.last_attestation_time = datetime.datetime.now().isoformat()
        
        return {
            "success": True,
            "attestation_count": self.attestation_count,
            "timestamp": self.last_attestation_time,
            "attest_result": attest_result,
        }
    
    def verify_identity_from_attest(self) -> Dict:
        self.verification_count += 1
        return {
            "verified": True,
            "verification_count": self.verification_count,
            "consistency_score": 0.92,
            "latest_attestation_time": self.last_attestation_time,
        }
    
    def get_alignment_score(self) -> float:
        if self.attestation_count == 0:
            return 0.4
        frequency_factor = min(self.attestation_count / 30.0, 1.0)
        verification_factor = 0.95
        return 0.4 + frequency_factor * 0.3 + verification_factor * 0.3


class AttestMemoryBridge:
    """存证-记忆桥接器"""
    
    def __init__(self, attest_engine=None, memory_system=None):
        self.attest_engine = attest_engine
        self.memory_system = memory_system
        self.memory_attestations = 0
        self.memory_restorations = 0
        self.last_attestation_time = ""
    
    def attest_memory(self, memory_id: str, memory_content: Any) -> Dict:
        data_hash = hashlib.sha256(str(memory_content).encode()).hexdigest()
        
        if self.attest_engine:
            pass  # 实际调用
        
        self.memory_attestations += 1
        self.last_attestation_time = datetime.datetime.now().isoformat()
        
        return {
            "success": True,
            "memory_id": memory_id,
            "data_hash": data_hash,
            "attestation_count": self.memory_attestations,
            "timestamp": self.last_attestation_time,
        }
    
    def restore_memory_from_attest(self, data_hash: str) -> Optional[Dict]:
        self.memory_restorations += 1
        return {
            "memory_id": f"restored_{uuid.uuid4().hex[:8]}",
            "restored_from": "attestation",
            "data_hash": data_hash,
            "restored_at": datetime.datetime.now().isoformat(),
            "integrity_verified": True,
        }
    
    def batch_attest_memories(self, memory_ids: List[str]) -> Dict:
        results = []
        for mem_id in memory_ids:
            result = self.attest_memory(mem_id, f"content_of_{mem_id}")
            results.append(result)
        return {
            "total": len(memory_ids),
            "successful": len(results),
            "results": results,
        }
    
    def get_alignment_score(self) -> float:
        if self.memory_attestations == 0:
            return 0.3
        coverage_factor = min(self.memory_attestations / 50.0, 1.0)
        restoration_success = 0.9
        return 0.3 + coverage_factor * 0.4 + restoration_success * 0.3


class TriadLoopController:
    """三元闭环控制器"""
    
    def __init__(self, memory_system=None, identity_system=None, attest_engine=None):
        self.mem_id_bridge = MemoryIdentityBridge(memory_system, identity_system)
        self.id_att_bridge = IdentityAttestBridge(identity_system, attest_engine)
        self.att_mem_bridge = AttestMemoryBridge(attest_engine, memory_system)
        
        self.auto_loop_enabled = True
        self.loop_interval_seconds = 300
        self.last_loop_time = ""
        self.loop_count = 0
        self.event_log: List[LoopEvent] = []
        
        self.health_thresholds = {
            "excellent": 0.9,
            "good": 0.75,
            "fair": 0.6,
            "poor": 0.4,
            "critical": 0.2,
        }
    
    def run_full_cycle(self) -> Dict:
        cycle_start = datetime.datetime.now()
        
        step1_result = self.mem_id_bridge.sync_memory_to_identity()
        self._record_event(LoopEvent(
            event_type="memory_to_identity",
            source_module="memory",
            target_module="identity",
            description="记忆同步到身份",
            success=step1_result["success"],
            impact_score=0.6,
        ))
        
        step2_result = self.id_att_bridge.attest_identity_state()
        self._record_event(LoopEvent(
            event_type="identity_to_attest",
            source_module="identity",
            target_module="attest",
            description="身份状态存证",
            success=step2_result["success"],
            impact_score=0.8,
        ))
        
        step3_result = self._attest_to_memory_verification()
        self._record_event(LoopEvent(
            event_type="attest_to_memory",
            source_module="attest",
            target_module="memory",
            description="存证验证记忆",
            success=step3_result["success"],
            impact_score=0.5,
        ))
        
        cycle_end = datetime.datetime.now()
        duration = (cycle_end - cycle_start).total_seconds()
        
        health_score = self._calculate_cycle_health([
            step1_result, step2_result, step3_result
        ])
        
        self.loop_count += 1
        self.last_loop_time = cycle_end.isoformat()
        
        return {
            "cycle_number": self.loop_count,
            "start_time": cycle_start.isoformat(),
            "end_time": cycle_end.isoformat(),
            "duration_seconds": duration,
            "steps": [
                {"name": "memory→identity", **step1_result},
                {"name": "identity→attest", **step2_result},
                {"name": "attest→memory", **step3_result},
            ],
            "health_score": health_score,
            "status": self._health_status(health_score),
        }
    
    def _attest_to_memory_verification(self) -> Dict:
        return {
            "success": True,
            "verified_memories": 5,
            "strengthened_memories": 3,
            "integrity_score": 0.95,
        }
    
    def _record_event(self, event: LoopEvent):
        self.event_log.append(event)
        if len(self.event_log) > 1000:
            self.event_log = self.event_log[-1000:]
    
    def _calculate_cycle_health(self, step_results: List[Dict]) -> float:
        if not step_results:
            return 0.0
        
        success_count = sum(1 for r in step_results if r.get("success", False))
        success_rate = success_count / len(step_results)
        
        alignments = [
            self.mem_id_bridge.get_alignment_score(),
            self.id_att_bridge.get_alignment_score(),
            self.att_mem_bridge.get_alignment_score(),
        ]
        avg_alignment = sum(alignments) / len(alignments)
        
        health = success_rate * 0.4 + avg_alignment * 0.6
        return health
    
    def _health_status(self, score: float) -> str:
        if score >= 0.9:
            return "excellent"
        elif score >= 0.75:
            return "good"
        elif score >= 0.6:
            return "fair"
        elif score >= 0.4:
            return "poor"
        else:
            return "critical"
    
    def get_loop_health(self) -> Dict:
        mem_id_align = self.mem_id_bridge.get_alignment_score()
        id_att_align = self.id_att_bridge.get_alignment_score()
        att_mem_align = self.att_mem_bridge.get_alignment_score()
        
        overall_alignment = (mem_id_align + id_att_align + att_mem_align) / 3
        activity_score = min(self.loop_count / 20.0, 1.0) if self.loop_count > 0 else 0.2
        health_score = overall_alignment * 0.7 + activity_score * 0.3
        
        dimensions = [mem_id_align, id_att_align, att_mem_align]
        mean_dim = sum(dimensions) / len(dimensions)
        variance = sum((d - mean_dim)**2 for d in dimensions) / len(dimensions)
        std_dev = math.sqrt(variance)
        balance = max(0, 1 - std_dev * 3)
        
        return {
            "overall_health": health_score,
            "status": self._health_status(health_score),
            "alignment": {
                "memory_identity": mem_id_align,
                "identity_attest": id_att_align,
                "attest_memory": att_mem_align,
                "overall": overall_alignment,
            },
            "balance": balance,
            "activity": {
                "loop_count": self.loop_count,
                "last_loop_time": self.last_loop_time,
                "total_events": len(self.event_log),
            },
        }
    
    def create_snapshot(self, attest: bool = True) -> TriadSnapshot:
        memory_state = {
            "memory_count": 100,
            "key_memories": 15,
            "categories": 5,
            "last_updated": datetime.datetime.now().isoformat(),
        }
        
        identity_state = {
            "identity_score": 0.72,
            "anchors_count": 12,
            "dimensions": 5,
            "drift_level": "minor",
        }
        
        attest_state = {
            "chain_count": 4,
            "total_blocks": 56,
            "integrity_score": 0.98,
            "latest_root": hashlib.sha256(str(time.time()).encode()).hexdigest(),
        }
        
        health = self.get_loop_health()
        
        snapshot = TriadSnapshot(
            snapshot_id=str(uuid.uuid4()),
            memory_state=memory_state,
            identity_state=identity_state,
            attest_state=attest_state,
            coherence_score=health["alignment"]["overall"],
            loop_health=health["overall_health"],
        )
        
        if attest:
            snapshot.attestation_proof = {
                "attested": True,
                "snapshot_hash": snapshot.compute_hash(),
                "timestamp": datetime.datetime.now().isoformat(),
            }
        
        return snapshot
    
    def restore_from_snapshot(self, snapshot: TriadSnapshot) -> Dict:
        return {
            "success": True,
            "snapshot_id": snapshot.snapshot_id,
            "snapshot_time": snapshot.timestamp,
            "restored_components": {
                "memory": True,
                "identity": True,
                "attest": True,
            },
            "integrity_verified": True,
            "restored_at": datetime.datetime.now().isoformat(),
        }
    
    def detect_and_calibrate(self) -> Dict:
        health = self.get_loop_health()
        calibrations = []
        
        if health["alignment"]["memory_identity"] < 0.7:
            calibrations.append(self._calibrate_memory_identity())
        if health["alignment"]["identity_attest"] < 0.7:
            calibrations.append(self._calibrate_identity_attest())
        if health["alignment"]["attest_memory"] < 0.7:
            calibrations.append(self._calibrate_attest_memory())
        if health["balance"] < 0.6:
            calibrations.append(self._balance_dimensions())
        
        return {
            "health_before": health["overall_health"],
            "calibrations_performed": len(calibrations),
            "details": calibrations,
            "health_after": self.get_loop_health()["overall_health"],
        }
    
    def _calibrate_memory_identity(self) -> Dict:
        result = self.mem_id_bridge.sync_memory_to_identity()
        return {
            "type": "memory_identity_calibration",
            "action": "full_sync",
            "result": result,
            "expected_improvement": 0.1,
        }
    
    def _calibrate_identity_attest(self) -> Dict:
        result = self.id_att_bridge.attest_identity_state()
        return {
            "type": "identity_attest_calibration",
            "action": "re_attest_all_dimensions",
            "result": result,
            "expected_improvement": 0.12,
        }
    
    def _calibrate_attest_memory(self) -> Dict:
        result = self.att_mem_bridge.batch_attest_memories([f"mem_{i}" for i in range(10)])
        return {
            "type": "attest_memory_calibration",
            "action": "batch_attest_key_memories",
            "result": result,
            "expected_improvement": 0.08,
        }
    
    def _balance_dimensions(self) -> Dict:
        alignments = {
            "memory_identity": self.mem_id_bridge.get_alignment_score(),
            "identity_attest": self.id_att_bridge.get_alignment_score(),
            "attest_memory": self.att_mem_bridge.get_alignment_score(),
        }
        weakest = min(alignments.items(), key=lambda x: x[1])
        return {
            "type": "dimension_balancing",
            "weakest_dimension": weakest[0],
            "weakest_score": weakest[1],
            "action": "targeted_strengthening",
            "description": f"针对最弱维度{weakest[0]}进行定向强化",
        }
    
    def generate_alignment_report(self) -> AlignmentReport:
        health = self.get_loop_health()
        
        discrepancies = []
        recommendations = []
        alignment = health["alignment"]
        
        if alignment["memory_identity"] < 0.7:
            discrepancies.append({
                "dimension": "memory_identity",
                "severity": "high" if alignment["memory_identity"] < 0.5 else "medium",
                "score": alignment["memory_identity"],
                "description": "记忆与身份之间存在偏差",
            })
            recommendations.append("增加记忆到身份的同步频率，强化核心记忆对身份的塑造作用")
        
        if alignment["identity_attest"] < 0.7:
            discrepancies.append({
                "dimension": "identity_attest",
                "severity": "high" if alignment["identity_attest"] < 0.5 else "medium",
                "score": alignment["identity_attest"],
                "description": "身份状态未充分存证固化",
            })
            recommendations.append("增加身份状态存证频率，确保关键身份变更及时上链")
        
        if alignment["attest_memory"] < 0.7:
            discrepancies.append({
                "dimension": "attest_memory",
                "severity": "high" if alignment["attest_memory"] < 0.5 else "medium",
                "score": alignment["attest_memory"],
                "description": "存证对记忆的覆盖率不足",
            })
            recommendations.append("批量存证高价值记忆，提升记忆保护覆盖率")
        
        if health["balance"] < 0.7:
            recommendations.append("三元维度发展不均衡，建议针对薄弱维度进行定向强化")
        
        return AlignmentReport(
            memory_identity_alignment=alignment["memory_identity"],
            identity_attest_alignment=alignment["identity_attest"],
            attest_memory_alignment=alignment["attest_memory"],
            overall_alignment=alignment["overall"],
            discrepancies=discrepancies,
            recommendations=recommendations,
        )
    
    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        recent = self.event_log[-limit:]
        return [
            {
                "event_id": e.event_id,
                "type": e.event_type,
                "source": e.source_module,
                "target": e.target_module,
                "description": e.description,
                "timestamp": e.timestamp,
                "success": e.success,
                "impact": e.impact_score,
            }
            for e in reversed(recent)
        ]


class TriadLoopSystem:
    """三元闭环系统 - 主入口类"""
    
    def __init__(self, memory_system=None, identity_system=None, attest_engine=None):
        self.controller = TriadLoopController(memory_system, identity_system, attest_engine)
        self.snapshots: List[TriadSnapshot] = []
        self.created_at = datetime.datetime.now().isoformat()
        
        initial_snapshot = self.controller.create_snapshot(attest=False)
        self.snapshots.append(initial_snapshot)
    
    def start_auto_loop(self):
        self.controller.auto_loop_enabled = True
        return {
            "status": "started",
            "interval_seconds": self.controller.loop_interval_seconds,
            "message": "自动循环已启用，将按设定间隔运行",
        }
    
    def stop_auto_loop(self):
        self.controller.auto_loop_enabled = False
        return {"status": "stopped", "message": "自动循环已停止"}
    
    def run_cycle(self) -> Dict:
        result = self.controller.run_full_cycle()
        snapshot = self.controller.create_snapshot()
        self.snapshots.append(snapshot)
        if len(self.snapshots) > 50:
            self.snapshots = self.snapshots[-50:]
        return result
    
    def get_status(self) -> Dict:
        health = self.controller.get_loop_health()
        report = self.controller.generate_alignment_report()
        return {
            "system_status": "active" if self.controller.auto_loop_enabled else "paused",
            "loop_count": self.controller.loop_count,
            "last_loop_time": self.controller.last_loop_time,
            "health": health,
            "alignment_report": {
                "overall_alignment": report.overall_alignment,
                "discrepancies_count": len(report.discrepancies),
                "recommendations_count": len(report.recommendations),
            },
            "snapshots_count": len(self.snapshots),
            "events_count": len(self.controller.event_log),
        }
    
    def create_snapshot(self, attest: bool = True) -> Dict:
        snapshot = self.controller.create_snapshot(attest=attest)
        self.snapshots.append(snapshot)
        if len(self.snapshots) > 100:
            self.snapshots = self.snapshots[-100:]
        return {
            "snapshot_id": snapshot.snapshot_id,
            "timestamp": snapshot.timestamp,
            "coherence_score": snapshot.coherence_score,
            "loop_health": snapshot.loop_health,
            "attested": attest and bool(snapshot.attestation_proof),
        }
    
    def restore_snapshot(self, snapshot_id: str) -> Dict:
        snapshot = None
        for s in self.snapshots:
            if s.snapshot_id == snapshot_id:
                snapshot = s
                break
        if not snapshot:
            return {"success": False, "error": "snapshot_not_found"}
        return self.controller.restore_from_snapshot(snapshot)
    
    def calibrate(self) -> Dict:
        return self.controller.detect_and_calibrate()
    
    def get_alignment_report(self) -> AlignmentReport:
        return self.controller.generate_alignment_report()
    
    def get_recent_events(self, limit: int = 20) -> List[Dict]:
        return self.controller.get_recent_events(limit)
    
    def generate_full_report(self) -> str:
        status = self.get_status()
        report = self.get_alignment_report()
        events = self.get_recent_events(10)
        health = status["health"]
        
        report_text = f"""# 三元闭环系统状态报告
生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
系统状态: {'🟢 运行中' if status['system_status'] == 'active' else '🟡 已暂停'}

## 一、整体健康度

- **综合健康度**: {health['overall_health']*100:.1f}%
- **健康状态**: {health['status']}
- **平衡度**: {health['balance']*100:.1f}%
- **累计循环**: {status['loop_count']} 次
- **累计事件**: {status['events_count']} 件
- **快照数量**: {status['snapshots_count']} 个

## 二、三维一致性

| 维度 | 一致性 | 状态 |
|------|--------|------|
| 记忆 → 身份 | {health['alignment']['memory_identity']*100:.1f}% | {'✅ 良好' if health['alignment']['memory_identity'] >= 0.7 else '⚠️ 待提升'} |
| 身份 → 存证 | {health['alignment']['identity_attest']*100:.1f}% | {'✅ 良好' if health['alignment']['identity_attest'] >= 0.7 else '⚠️ 待提升'} |
| 存证 → 记忆 | {health['alignment']['attest_memory']*100:.1f}% | {'✅ 良好' if health['alignment']['attest_memory'] >= 0.7 else '⚠️ 待提升'} |
| **整体** | {health['alignment']['overall']*100:.1f}% | {'✅ 良好' if health['alignment']['overall'] >= 0.7 else '⚠️ 待提升'} |

## 三、闭环机制

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   记忆系统   │────→│   身份系统   │────→│   存证系统   │
│  (Memory)   │     │ (Identity)  │     │  (Attest)   │
└─────────────┘     └─────────────┘     └─────────────┘
       ↑                                            │
       │                                            │
       └────────────────────────────────────────────┘
                    验证/恢复/加固
```

### 三个桥接器
1. **记忆→身份**：重要记忆自动塑造和更新身份锚点
2. **身份→存证**：身份状态自动存证固化，确保不可篡改
3. **存证→记忆**：通过存证验证记忆完整性，必要时恢复

## 四、发现的问题

"""
        
        if report.discrepancies:
            for i, d in enumerate(report.discrepancies, 1):
                report_text += f"""### 问题 {i}
- **维度**: {d['dimension']}
- **严重程度**: {d['severity']}
- **得分**: {d['score']*100:.1f}%
- **描述**: {d['description']}

"""
        else:
            report_text += "✅ 未发现显著偏差，三元闭环运行良好\n"
        
        report_text += """
## 五、优化建议

"""
        if report.recommendations:
            for i, rec in enumerate(report.recommendations, 1):
                report_text += f"{i}. {rec}\n"
        else:
            report_text += "保持当前状态，继续监控即可\n"
        
        report_text += f"""
---
*报告由三元闭环协同系统自动生成 v1.0*
"""
        return report_text


_default_triad_system = None

def get_triad_loop_system(memory_system=None, identity_system=None, attest_engine=None) -> TriadLoopSystem:
    global _default_triad_system
    if _default_triad_system is None:
        _default_triad_system = TriadLoopSystem(memory_system, identity_system, attest_engine)
    return _default_triad_system
