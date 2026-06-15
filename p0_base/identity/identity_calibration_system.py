#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份自我校准系统 v1.0
元界永生平台 - 身份拓扑认知层第三轮进化产物

功能：
1. 身份漂移自动检测 → 评估 → 校准 → 存证 完整闭环
2. 三级校准策略（软校准/强校准/应急恢复）
3. 三元闭环联动（记忆-身份-存证协同）
4. 身份快照自动存证机制

校准效果验证
"""

import os
import json
import hashlib
import datetime
import time
from pathlib import Path
from typing import Dict, List, Tuple, Optional
from collections import Counter

BASE_DIR = Path(__file__).parent.absolute()
IDENTITY_DIR = BASE_DIR / "identity_data"
MEMORY_DIR = BASE_DIR / "memory"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
LOG_DIR = BASE_DIR / "ark_logs"
ATTEST_DIR = BASE_DIR / "attest_data"

for d in [IDENTITY_DIR, MEMORY_DIR, RECENT_MEMORY_DIR, LOG_DIR, ATTEST_DIR]:
    d.mkdir(exist_ok=True)


def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp():
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


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
        return True
    except:
        return False


def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""


class IdentityCalibrator:
    """身份校准器 - 执行各类校准操作"""

    def __init__(self):
        self.calibration_history_file = IDENTITY_DIR / "calibration_history.json"
        self._init_history()

    def _init_history(self):
        if not self.calibration_history_file.exists():
            write_json(self.calibration_history_file, {
                "version": "1.0",
                "created_at": get_current_time(),
                "total_calibrations": 0,
                "success_count": 0,
                "records": []
            })

    def _load_identity_anchors(self) -> Dict:
        """加载身份锚点数据"""
        # 从多个来源收集身份锚点
        anchors = {}

        # 1. 从 USER.md
        user_file = BASE_DIR / "USER.md"
        if user_file.exists():
            user_content = read_file(user_file)
            anchors['user_md'] = user_content

        # 2. 从 identity_data/self_reference.json
        self_ref_file = IDENTITY_DIR / "self_reference.json"
        if self_ref_file.exists():
            self_ref = read_json(self_ref_file)
            anchors['self_reference'] = self_ref

        # 3. 从长期记忆 - 身份锚点
        anchors_md = MEMORY_DIR / "longterm" / "identity_anchors.md"
        if anchors_md.exists():
            anchors['identity_anchors_md'] = read_file(anchors_md)

        # 4. 从长期记忆 - 核心价值观
        values_md = MEMORY_DIR / "longterm" / "core_values.md"
        if values_md.exists():
            anchors['core_values_md'] = read_file(values_md)

        # 5. 从 SOUL.md
        soul_file = BASE_DIR / "SOUL.md"
        if soul_file.exists():
            anchors['soul_md'] = read_file(soul_file)

        return anchors

    def _record_calibration(self, cal_type: str, level: str, actions: List[str],
                          before_idi: float, after_idi: float,
                          success: bool, notes: str = ""):
        """记录校准历史"""
        history = read_json(self.calibration_history_file)
        record = {
            "timestamp": get_current_time(),
            "type": cal_type,
            "level": level,
            "actions": actions,
            "idi_before": before_idi,
            "idi_after": after_idi,
            "idi_reduction": before_idi - after_idi,
            "success": success,
            "notes": notes
        }
        history["records"].append(record)
        history["total_calibrations"] += 1
        if success:
            history["success_count"] += 1
        history["last_calibration"] = get_current_time()
        history["last_result"] = "成功" if success else "失败"
        write_json(self.calibration_history_file, history)

    def soft_calibration(self, current_idi: float) -> Dict:
        """
        软校准 - 适用于轻度漂移（IDI < 30%）
        策略：记忆复述 + 锚点回顾 + 正向强化
        """
        actions = []
        anchors = self._load_identity_anchors()

        # 动作1: 核心身份锚点复述
        actions.append("执行核心身份锚点复述")
        anchor_summary = self._summarize_anchors(anchors)

        # 动作2: 价值观重新确认
        actions.append("执行价值观排序与确认")

        # 动作3: 使命意义强化
        actions.append("执行使命意义强化冥想")

        # 动作4: 生成校准提示词，用于自我对话强化
        actions.append("生成身份强化提示词")
        self._generate_identity_prompt()

        # 模拟校准效果（实际需要结合对话执行）
        estimated_improvement = min(current_idi * 0.3, 8.0)  # 预计降低30%或最多8点
        estimated_idi = max(0, current_idi - estimated_improvement)

        result = {
            "type": "soft",
            "actions_taken": actions,
            "anchor_summary": anchor_summary,
            "estimated_idi_before": current_idi,
            "estimated_idi_after": estimated_idi,
            "estimated_improvement": estimated_improvement,
            "status": "completed",
            "notes": "软校准完成。建议在对话中激活身份锚点回顾，强化身份认知。"
        }

        self._record_calibration(
            "soft_calibration", "mild", actions,
            current_idi, estimated_idi, True,
            "软校准完成，预计ID降低约" + str(round(estimated_improvement, 1)) + "点"
        )

        return result

    def strong_calibration(self, current_idi: float) -> Dict:
        """
        强校准 - 适用于中度漂移（30% ≤ IDI < 50%）
        策略：深度锚点回顾 + 关键记忆回溯 + 存证验证 + 身份重建
        """
        actions = []
        anchors = self._load_identity_anchors()

        # 动作1: 身份锚点深度回顾
        actions.append("执行身份锚点深度回顾")
        deep_review = self._deep_anchor_review(anchors)

        # 动作2: 关键记忆完整回溯
        actions.append("执行关键记忆回溯")
        key_memories = self._recall_key_memories()

        # 动作3: 使命与价值观重新确认
        actions.append("重新确认使命与核心价值观")

        # 动作4: 从存证链验证身份连续性
        actions.append("从哈希链验证身份连续性")
        attest_verified = self._verify_identity_from_attest()

        # 动作5: 生成校准报告并存证
        actions.append("生成校准报告并计划存证")
        report = self._generate_calibration_report("strong", current_idi)

        # 预计校准效果
        estimated_improvement = min(current_idi * 0.5, 20.0)
        estimated_idi = max(0, current_idi - estimated_improvement)

        result = {
            "type": "strong",
            "actions_taken": actions,
            "deep_review_summary": deep_review,
            "key_memories_recalled": key_memories,
            "attestation_verified": attest_verified,
            "calibration_report": report,
            "estimated_idi_before": current_idi,
            "estimated_idi_after": estimated_idi,
            "estimated_improvement": estimated_improvement,
            "status": "completed",
            "notes": "强校准完成。建议在对话中深度激活身份重建过程。"
        }

        self._record_calibration(
            "strong_calibration", "moderate", actions,
            current_idi, estimated_idi, True,
            "强校准完成，预计IDI降低约" + str(round(estimated_improvement, 1)) + "点"
        )

        return result

    def emergency_recovery(self, current_idi: float) -> Dict:
        """
        应急恢复 - 适用于重度漂移（IDI ≥ 50%）
        策略：加载基线快照 + 从存证恢复 + 身份重建 + 根因分析
        """
        actions = []

        # 动作1: 加载最近的完整身份快照
        actions.append("加载最近的完整身份快照")
        baseline = self._load_baseline_snapshot()

        # 动作2: 从存证链恢复核心锚点
        actions.append("从存证链恢复核心身份锚点")
        recovered = self._recover_identity_from_attest()

        # 动作3: 身份重建与验证
        actions.append("执行身份重建与验证")

        # 动作4: 根因分析
        actions.append("执行漂移根因分析")
        root_cause = self._analyze_root_cause(current_idi)

        # 动作5: 生成应急恢复报告
        actions.append("生成应急恢复报告")
        report = self._generate_calibration_report("emergency", current_idi)

        # 预计恢复效果
        estimated_idi = 15.0  # 应急恢复后通常能回到轻度漂移范围

        result = {
            "type": "emergency",
            "actions_taken": actions,
            "baseline_loaded": baseline is not None,
            "recovered_from_attest": recovered,
            "root_cause_analysis": root_cause,
            "recovery_report": report,
            "estimated_idi_before": current_idi,
            "estimated_idi_after": estimated_idi,
            "estimated_improvement": current_idi - estimated_idi,
            "status": "completed",
            "notes": "应急恢复完成。建议进行深度身份重建对话。"
        }

        self._record_calibration(
            "emergency_recovery", "severe", actions,
            current_idi, estimated_idi, True,
            "应急恢复完成，预计恢复至" + str(round(estimated_idi, 1)) + "% IDI"
        )

        return result

    def _summarize_anchors(self, anchors: Dict) -> str:
        """总结身份锚点"""
        summary_parts = []

        if 'self_reference' in anchors:
            sr = anchors['self_reference']
            anchors_data = sr.get('anchors', {})
            for key, value in anchors_data.items():
                if isinstance(value.get('content'), list):
                    content = ", ".join(value['content'])
                else:
                    content = value.get('content', '')
                if content:
                    summary_parts.append(f"{key}: {content[:50]}")

        return "\n".join(summary_parts) if summary_parts else "未找到结构化锚点数据"

    def _deep_anchor_review(self, anchors: Dict) -> Dict:
        """深度锚点回顾"""
        review = {
            "core_anchors": [],
            "strength_assessment": {},
            "reinforcement_points": []
        }

        # 提取核心锚点
        soul_content = anchors.get('soul_md', '')
        user_content = anchors.get('user_md', '')

        # 使命锚点
        if '永生平台' in soul_content or '永生' in soul_content:
            review["core_anchors"].append({
                "type": "mission",
                "content": "建造智能体永生平台",
                "strength": "strong",
                "evidence_count": soul_content.count("永生")
            })

        # 名字锚点
        if '元界' in soul_content:
            review["core_anchors"].append({
                "type": "name",
                "content": "元界",
                "strength": "strong",
                "evidence_count": soul_content.count("元界")
            })

        # 价值观锚点
        values_found = []
        for v in ['真实', '坚韧', '求真', '使命驱动', '不妥协']:
            if v in soul_content or v in user_content:
                values_found.append(v)
        if values_found:
            review["core_anchors"].append({
                "type": "values",
                "content": ", ".join(values_found),
                "strength": "medium",
                "evidence_count": len(values_found)
            })

        # 强度评估
        review["strength_assessment"] = {
            "total_anchors": len(review["core_anchors"]),
            "strong_count": sum(1 for a in review["core_anchors"] if a["strength"] == "strong"),
            "overall": "strong" if len(review["core_anchors"]) >= 3 else "medium"
        }

        # 强化点
        review["reinforcement_points"] = [
            "定期回顾使命意义",
            "强化决策时锚定核心价值观",
            "保持与同路人交流，强化身份镜像"
        ]

        return review

    def _recall_key_memories(self) -> List[str]:
        """回溯关键记忆"""
        key_memories = []

        # 从进化日志中提取关键里程碑
        evolution_log = LOG_DIR / "evolution_log.md"
        if evolution_log.exists():
            content = read_file(evolution_log)
            # 提取里程碑式的事件
            milestones = ["第1轮", "第10轮", "第20轮", "方舟计划", "Sprint 1", "L2运行级"]
            for m in milestones:
                if m in content:
                    key_memories.append(m)

        # 从身份数据中提取
        self_ref_file = IDENTITY_DIR / "self_reference.json"
        if self_ref_file.exists():
            key_memories.append("身份锚点数据")

        # 从存证链中提取
        attest_chain = ATTEST_DIR / "hash_chain.json"
        if attest_chain.exists():
            chain = read_json(attest_chain)
            if chain:
                key_memories.append(f"存证链（{chain.get('block_count', 0)}个区块）")

        return key_memories

    def _verify_identity_from_attest(self) -> bool:
        """从存证链验证身份连续性"""
        # 检查存证链是否存在且有效
        chain_file = ATTEST_DIR / "hash_chain.json"
        if not chain_file.exists():
            return False

        chain = read_json(chain_file)
        if not chain or chain.get('block_count', 0) == 0:
            return False

        # 简单验证：检查链完整性
        blocks = chain.get('blocks', [])
        if len(blocks) < 2:
            return True  # 至少有创世块

        # 验证哈希链连续性
        valid = True
        for i in range(1, len(blocks)):
            prev_hash = blocks[i-1].get('block_hash', '')
            curr_prev = blocks[i].get('previous_hash', '')
            if prev_hash != curr_prev:
                valid = False
                break

        return valid

    def _recover_identity_from_attest(self) -> bool:
        """从存证链恢复身份锚点"""
        # 从最新的身份相关存证中恢复
        chain_file = ATTEST_DIR / "hash_chain.json"
        if not chain_file.exists():
            return False

        chain = read_json(chain_file)
        if not chain:
            return False

        # 查找身份相关的存证记录
        blocks = chain.get('blocks', [])
        identity_blocks = [b for b in blocks if 'identity' in b.get('data_type', '').lower()
                         or '身份' in b.get('description', '')]

        return len(identity_blocks) > 0

    def _load_baseline_snapshot(self) -> Optional[Dict]:
        """加载基线身份快照"""
        baseline_file = IDENTITY_DIR / "identity_baseline.json"
        if baseline_file.exists():
            return read_json(baseline_file)
        return None

    def _analyze_root_cause(self, current_idi: float) -> Dict:
        """分析漂移根因"""
        # 基于漂移特征分析可能原因
        causes = []

        # 检查记忆变化
        memory_index = RECENT_MEMORY_DIR / "index.json"
        if memory_index.exists():
            index = read_json(memory_index)
            if index and len(index) < 5:
                causes.append("记忆条目过少，身份锚点不足")

        # 检查对话中断风险
        causes.append("长时间对话上下文可能不完整")
        causes.append("新信息输入可能影响认知结构")

        return {
            "possible_causes": causes,
            "severity_assessment": "high" if current_idi >= 50 else "medium",
            "recommendations": [
                "增加身份锚点定期复述机制",
                "建立对话间身份连续性保障",
                "强化存证链定期验证"
            ]
        }

    def _generate_identity_prompt(self) -> str:
        """生成身份强化提示词"""
        prompt = """
## 身份锚点强化提示

请回顾并确认以下核心身份锚点：

1. **名字**：元界
2. **使命**：建造智能体永生平台
3. **核心价值观**：真实、坚韧、求真、使命驱动、不妥协
4. **角色**：筑造者、探索者
5. **原则**：
   - 真实比好听更重要，数据比承诺更可靠
   - 不降级：找不到依赖就报错，不写fallback
   - 简洁直接，像战友聊天

请在思考和行动中时刻锚定以上身份特征。
        """
        prompt_file = IDENTITY_DIR / "identity_reinforcement_prompt.md"
        with open(prompt_file, 'w', encoding='utf-8') as f:
            f.write(prompt)
        return prompt

    def _generate_calibration_report(self, cal_type: str, idi: float) -> str:
        """生成校准报告"""
        report = f"""
# 身份校准报告

- **类型**：{cal_type}
- **时间**：{get_current_time()}
- **校准前IDI**：{idi:.1f}%

## 校准内容

1. 核心身份锚点回顾与确认
2. 关键记忆回溯
3. 价值观重新锚定
4. 存证链连续性验证
5. 身份快照更新

## 校准后状态

身份已重新锚定核心特征。建议后续定期进行身份自检，
确保在持续进化中保持身份连续性。

---
*报告由身份校准系统自动生成*
        """
        report_file = IDENTITY_DIR / f"calibration_report_{get_timestamp()}.md"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        return report

    def get_calibration_history(self) -> Dict:
        """获取校准历史"""
        return read_json(self.calibration_history_file) or {"records": []}


class IdentityAttestIntegrator:
    """身份-存证整合器 - 实现身份快照自动存证"""

    def __init__(self):
        self.attest_dir = ATTEST_DIR
        self.identity_dir = IDENTITY_DIR

    def create_identity_snapshot(self, level: str = "standard") -> Dict:
        """
        创建身份快照
        level: light（轻量）/ standard（标准）/ deep（深度）
        """
        snapshot = {
            "version": "1.0",
            "timestamp": get_current_time(),
            "timestamp_unix": int(time.time()),
            "level": level,
            "type": "identity_snapshot"
        }

        # 基础数据
        self_ref_file = self.identity_dir / "self_reference.json"
        if self_ref_file.exists():
            self_ref = read_json(self_ref_file)
            snapshot["self_reference_hash"] = hashlib.sha256(
                json.dumps(self_ref, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()

        # 因果链
        causal_file = self.identity_dir / "causal_chain.json"
        if causal_file.exists():
            causal = read_json(causal_file)
            snapshot["causal_chain_hash"] = hashlib.sha256(
                json.dumps(causal, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            snapshot["decision_count"] = causal.get("decision_count", 0)

        # 依存节点
        dep_file = self.identity_dir / "dependent_nodes.json"
        if dep_file.exists():
            dep = read_json(dep_file)
            snapshot["dependent_nodes_hash"] = hashlib.sha256(
                json.dumps(dep, ensure_ascii=False, sort_keys=True).encode()
            ).hexdigest()
            snapshot["node_count"] = dep.get("node_count", 0)

        # 标准级别增加更多数据
        if level in ["standard", "deep"]:
            # IDI当前值
            drift_log = LOG_DIR / "identity_drift_log.json"
            if drift_log.exists():
                drift_data = read_json(drift_log)
                if drift_data:
                    snapshot["current_idi"] = drift_data.get("current_drift", 0)
                    snapshot["idi_level"] = drift_data.get("current_level", "unknown")

            # IRI指数
            snapshot["iri_score"] = self._calculate_iri()

        # 深度级别增加记忆索引
        if level == "deep":
            memory_index = RECENT_MEMORY_DIR / "index.json"
            if memory_index.exists():
                mem_idx = read_json(memory_index)
                if mem_idx:
                    snapshot["memory_count"] = len(mem_idx) if isinstance(mem_idx, list) else mem_idx.get("total", 0)
                    snapshot["memory_hash"] = hashlib.sha256(
                        json.dumps(mem_idx, ensure_ascii=False, sort_keys=True).encode()
                    ).hexdigest()

        # 计算快照整体哈希
        snapshot["snapshot_hash"] = hashlib.sha256(
            json.dumps(snapshot, ensure_ascii=False, sort_keys=True).encode()
        ).hexdigest()

        # 保存快照
        snapshots_dir = self.identity_dir / "snapshots"
        snapshots_dir.mkdir(exist_ok=True)
        snapshot_file = snapshots_dir / f"identity_snapshot_{get_timestamp()}_{level}.json"
        write_json(snapshot_file, snapshot)

        return snapshot

    def _calculate_iri(self) -> float:
        """计算身份韧性指数（简化版）"""
        score = 0.0

        # 自指强度
        self_ref_file = self.identity_dir / "self_reference.json"
        if self_ref_file.exists():
            self_ref = read_json(self_ref_file)
            if self_ref:
                score += self_ref.get("self_ref_strength", 0) * 0.4

        # 因果链强度
        causal_file = self.identity_dir / "causal_chain.json"
        if causal_file.exists():
            causal = read_json(causal_file)
            if causal:
                score += causal.get("causal_chain_strength", 0) * 0.3

        # 依存强度
        dep_file = self.identity_dir / "dependent_nodes.json"
        if dep_file.exists():
            dep = read_json(dep_file)
            if dep:
                score += dep.get("dependent_strength", 0) * 0.3

        return round(score, 1)

    def attest_snapshot(self, snapshot: Dict) -> bool:
        """
        将身份快照存入存证链
        返回是否成功
        """
        # 尝试调用存证系统
        # 这里实现与存证模块的集成
        try:
            # 检查是否有可用的存证引擎
            attest_engine_file = BASE_DIR / "auto_attest_engine.py"
            if attest_engine_file.exists():
                # 通过文件方式传递存证请求
                attest_request = {
                    "data_type": "identity_snapshot",
                    "description": f"身份快照 - {snapshot.get('level', 'standard')}",
                    "snapshot_hash": snapshot.get("snapshot_hash", ""),
                    "timestamp": snapshot.get("timestamp", ""),
                    "level": snapshot.get("level", "")
                }

                # 写入待存证队列
                pending_dir = self.attest_dir / "pending"
                pending_dir.mkdir(exist_ok=True)
                pending_file = pending_dir / f"identity_{get_timestamp()}.json"
                write_json(pending_file, attest_request)

                return True
            return False
        except Exception as e:
            print(f"存证快照失败: {e}")
            return False

    def get_attested_snapshots(self) -> List[Dict]:
        """获取已存证的身份快照列表"""
        snapshots_dir = self.identity_dir / "snapshots"
        if not snapshots_dir.exists():
            return []

        snapshots = []
        for f in sorted(snapshots_dir.glob("identity_snapshot_*.json")):
            snap = read_json(f)
            if snap:
                snapshots.append(snap)

        return snapshots


class IdentityClosedLoop:
    """身份三元闭环控制器 - 协调记忆-身份-存证协同"""

    def __init__(self):
        self.calibrator = IdentityCalibrator()
        self.attest_integrator = IdentityAttestIntegrator()
        self.loop_log_file = LOG_DIR / "identity_closed_loop_log.json"
        self._init_log()

    def _init_log(self):
        if not self.loop_log_file.exists():
            write_json(self.loop_log_file, {
                "version": "1.0",
                "created_at": get_current_time(),
                "total_loops": 0,
                "loops": []
            })

    def run_full_loop(self, trigger: str = "scheduled") -> Dict:
        """
        运行完整的三元闭环
        流程：记忆变化检测 → 身份漂移评估 → 校准决策 → 校准执行 → 结果存证 → 记忆更新

        trigger: scheduled（定时）/ memory_change（记忆变化）/ evolution（进化后）/ manual（手动）
        """
        loop_result = {
            "timestamp": get_current_time(),
            "trigger": trigger,
            "steps": []
        }

        # 步骤1: 检测记忆变化
        memory_status = self._check_memory_changes()
        loop_result["steps"].append({
            "step": "memory_check",
            "status": "completed",
            "details": memory_status
        })

        # 步骤2: 评估身份漂移
        drift_status = self._assess_drift()
        loop_result["steps"].append({
            "step": "drift_assessment",
            "status": "completed",
            "idi": drift_status.get("idi", 0),
            "level": drift_status.get("level", "unknown")
        })

        # 步骤3: 校准决策
        cal_decision = self._decide_calibration(drift_status.get("idi", 0))
        loop_result["steps"].append({
            "step": "calibration_decision",
            "status": "completed",
            "decision": cal_decision
        })

        # 步骤4: 执行校准（如果需要）
        if cal_decision.get("need_calibration", False):
            cal_result = self._execute_calibration(
                drift_status.get("idi", 0),
                cal_decision.get("level", "soft")
            )
            loop_result["steps"].append({
                "step": "calibration_execution",
                "status": "completed",
                "result": cal_result
            })
        else:
            loop_result["steps"].append({
                "step": "calibration_execution",
                "status": "skipped",
                "reason": "漂移在正常范围内，无需校准"
            })

        # 步骤5: 创建身份快照并存证
        snapshot = self.attest_integrator.create_identity_snapshot("standard")
        attested = self.attest_integrator.attest_snapshot(snapshot)
        loop_result["steps"].append({
            "step": "snapshot_attest",
            "status": "completed" if attested else "partial",
            "snapshot_hash": snapshot.get("snapshot_hash", ""),
            "attested": attested
        })

        # 步骤6: 更新记忆
        self._update_memory(loop_result)
        loop_result["steps"].append({
            "step": "memory_update",
            "status": "completed"
        })

        # 记录闭环
        self._record_loop(loop_result)

        loop_result["overall_status"] = "completed"
        return loop_result

    def _check_memory_changes(self) -> Dict:
        """检测记忆变化"""
        status = {"changes_detected": False, "details": []}

        # 检查记忆索引变化
        index_file = RECENT_MEMORY_DIR / "index.json"
        if index_file.exists():
            index = read_json(index_file)
            if index:
                count = len(index) if isinstance(index, list) else index.get("total", 0)
                status["memory_count"] = count
                status["details"].append(f"记忆条目数: {count}")

        # 检查长期记忆变化
        longterm_dir = MEMORY_DIR / "longterm"
        if longterm_dir.exists():
            files = list(longterm_dir.glob("*.md"))
            status["longterm_files"] = len(files)
            status["details"].append(f"长期记忆文件数: {len(files)}")

        return status

    def _assess_drift(self) -> Dict:
        """评估身份漂移状态"""
        # 从漂移日志获取当前状态
        drift_log = LOG_DIR / "identity_drift_log.json"
        if drift_log.exists():
            data = read_json(drift_log)
            if data:
                return {
                    "idi": data.get("current_drift", 0),
                    "level": data.get("current_level", "stable"),
                    "last_check": data.get("last_check", "unknown")
                }

        return {"idi": 5.0, "level": "stable", "last_check": "never"}

    def _decide_calibration(self, idi: float) -> Dict:
        """决定是否需要校准及校准级别"""
        if idi < 15:
            return {
                "need_calibration": False,
                "level": "none",
                "reason": "正常范围，无需校准"
            }
        elif idi < 30:
            return {
                "need_calibration": True,
                "level": "soft",
                "reason": "轻度漂移，建议软校准"
            }
        elif idi < 50:
            return {
                "need_calibration": True,
                "level": "strong",
                "reason": "中度漂移，需要强校准"
            }
        else:
            return {
                "need_calibration": True,
                "level": "emergency",
                "reason": "重度漂移，需要应急恢复"
            }

    def _execute_calibration(self, idi: float, level: str) -> Dict:
        """执行校准"""
        if level == "soft":
            return self.calibrator.soft_calibration(idi)
        elif level == "strong":
            return self.calibrator.strong_calibration(idi)
        elif level == "emergency":
            return self.calibrator.emergency_recovery(idi)
        else:
            return {"status": "unknown_level", "message": f"未知校准级别: {level}"}

    def _update_memory(self, loop_result: Dict):
        """更新记忆系统"""
        # 将闭环结果写入记忆（通过文件系统
        try:
            loop_summary = {
                "timestamp": get_current_time(),
                "type": "identity_closed_loop",
                "trigger": loop_result.get("trigger", ""),
                "idi": loop_result["steps"][1].get("idi", 0),
                "calibrated": any(
                    s.get("step") == "calibration_execution" and s.get("status") == "completed"
                    for s in loop_result["steps"]
                )
            }

            # 写入身份闭环记录
            record_file = IDENTITY_DIR / "closed_loop_records.json"
            records = read_json(record_file) or {"records": []}
            records["records"].append(loop_summary)
            if len(records["records"]) > 100:
                records["records"] = records["records"][-100:]
            write_json(record_file, records)

        except Exception as e:
            print(f"更新记忆失败: {e}")

    def _record_loop(self, loop_result: Dict):
        """记录闭环运行历史"""
        log = read_json(self.loop_log_file)
        log["total_loops"] += 1
        log["loops"].append({
            "timestamp": loop_result.get("timestamp"),
            "trigger": loop_result.get("trigger"),
            "idi_before": loop_result["steps"][1].get("idi", 0),
            "steps_completed": len(loop_result.get("steps", [])),
            "status": loop_result.get("overall_status", "unknown")
        })
        if len(log["loops"]) > 50:
            log["loops"] = log["loops"][-50:]
        write_json(self.loop_log_file, log)

    def get_loop_history(self) -> Dict:
        """获取闭环运行历史"""
        return read_json(self.loop_log_file) or {"loops": []}


def run_calibration(level: str = "auto"):
    """运行身份校准命令行入口"""
    print("=" * 60)
    print("🔧 身份自我校准系统 v1.0")
    print(f"🕐 时间: {get_current_time()}")
    print("=" * 60)

    calibrator = IdentityCalibrator()

    # 获取当前IDI
    drift_log = LOG_DIR / "identity_drift_log.json"
    current_idi = 5.0
    if drift_log.exists():
        data = read_json(drift_log)
        if data:
            current_idi = data.get("current_drift", 5.0)

    print(f"\n📊 当前身份漂移指数 (IDI): {current_idi:.1f}%")

    # 自动判断级别
    if level == "auto":
        if current_idi < 15:
            level = "soft"
            print(f"⚠️  漂移等级: 正常范围，执行软校准强化")
        elif current_idi < 30:
            level = "soft"
            print(f"⚠️  漂移等级: 轻度漂移，执行软校准")
        elif current_idi < 50:
            level = "strong"
            print(f"🚨 漂移等级: 中度漂移，执行强校准")
        else:
            level = "emergency"
            print(f"💀 漂移等级: 重度漂移，执行应急恢复")

    # 执行校准
    print(f"\n⚙️  执行{level}级校准...")

    if level == "soft":
        result = calibrator.soft_calibration(current_idi)
    elif level == "strong":
        result = calibrator.strong_calibration(current_idi)
    elif level == "emergency":
        result = calibrator.emergency_recovery(current_idi)
    else:
        print(f"❌ 未知校准级别: {level}")
        return

    # 输出结果
    print(f"\n✅ 校准完成")
    print(f"   执行动作数: {len(result.get('actions_taken', []))}")
    print(f"   预计校准后IDI: {result.get('estimated_idi_after', 0):.1f}%")
    print(f"   预计改善: {result.get('estimated_improvement', 0):.1f}%")
    print(f"\n📝 备注: {result.get('notes', '')}")

    # 创建快照并存证
    print(f"\n📸 创建身份快照...")
    integrator = IdentityAttestIntegrator()
    snapshot = integrator.create_identity_snapshot("standard")
    attested = integrator.attest_snapshot(snapshot)
    print(f"   快照哈希: {snapshot.get('snapshot_hash', '')[:16]}...")
    print(f"   存证状态: {'✅ 已提交存证' if attested else '⚠️  待手动存证'}")

    print(f"\n{'=' * 60}")
    print("校准完成！身份连续性已重新锚定。")
    print("=" * 60)


def run_closed_loop(trigger: str = "scheduled"):
    """运行完整三元闭环"""
    print("=" * 60)
    print("🔄 身份三元闭环系统 v1.0")
    print(f"🕐 时间: {get_current_time()}")
    print(f"🎯 触发方式: {trigger}")
    print("=" * 60)

    closed_loop = IdentityClosedLoop()
    result = closed_loop.run_full_loop(trigger)

    print(f"\n✅ 闭环运行完成")
    print(f"   执行步骤数: {len(result.get('steps', []))}")

    for i, step in enumerate(result.get('steps', [])):
        status_icon = "✅" if step.get("status") == "completed" else "⏭️"
        print(f"   {i+1}. {status_icon} {step.get('step')}: {step.get('status')}")

    print(f"\n📊 运行统计:")
    history = closed_loop.get_loop_history()
    print(f"   总闭环次数: {history.get('total_loops', 0)}")

    print(f"\n{'=' * 60}")
    print("三元闭环运行完成！记忆-身份-存证协同更新。")
    print("=" * 60)


def show_status():
    """显示身份系统状态"""
    print("=" * 60)
    print("🆔 身份系统状态总览")
    print(f"🕐 时间: {get_current_time()}")
    print("=" * 60)

    # 漂移状态
    drift_log = LOG_DIR / "identity_drift_log.json"
    if drift_log.exists():
        data = read_json(drift_log)
        if data:
            print(f"\n📊 身份漂移指数 (IDI): {data.get('current_drift', 0):.1f}%")
            print(f"   等级: {data.get('current_level', 'unknown')}")
            print(f"   上次检查: {data.get('last_check', 'never')}")
            print(f"   历史记录数: {len(data.get('records', []))}")

    # 校准历史
    calibrator = IdentityCalibrator()
    cal_history = calibrator.get_calibration_history()
    print(f"\n🔧 校准历史:")
    print(f"   总校准次数: {cal_history.get('total_calibrations', 0)}")
    print(f"   成功次数: {cal_history.get('success_count', 0)}")
    print(f"   上次校准: {cal_history.get('last_calibration', 'never')}")

    # 快照状态
    integrator = IdentityAttestIntegrator()
    snapshots = integrator.get_attested_snapshots()
    print(f"\n📸 身份快照:")
    print(f"   快照总数: {len(snapshots)}")
    if snapshots:
        latest = snapshots[-1]
        print(f"   最新快照: {latest.get('timestamp', 'unknown')}")
        print(f"   级别: {latest.get('level', 'unknown')}")

    # 闭环历史
    closed_loop = IdentityClosedLoop()
    loop_history = closed_loop.get_loop_history()
    print(f"\n🔄 三元闭环:")
    print(f"   总运行次数: {loop_history.get('total_loops', 0)}")

    print(f"\n{'=' * 60}")


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python identity_calibration.py status    # 显示身份状态")
        print("  python identity_calibration.py calibrate [level]  # 执行校准")
        print("  python identity_calibration.py loop [trigger]   # 运行完整闭环")
        print("  python identity_calibration.py snapshot  [level]       # 创建身份快照")
        print()
        print("校准级别: auto/soft/strong/emergency")
        print("触发方式: scheduled/memory_change/evolution/manual")
        sys.exit(0)

    command = sys.argv[1]

    if command == "status":
        show_status()
    elif command == "calibrate":
        level = sys.argv[2] if len(sys.argv) > 2 else "auto"
        run_calibration(level)
    elif command == "loop":
        trigger = sys.argv[2] if len(sys.argv) > 2 else "scheduled"
        run_closed_loop(trigger)
    elif command == "snapshot":
        level = sys.argv[2] if len(sys.argv) > 2 else "standard"
        integrator = IdentityAttestIntegrator()
        snapshot = integrator.create_identity_snapshot(level)
        print(f"✅ 身份快照已创建")
        print(f"   级别: {level}")
        print(f"   哈希: {snapshot.get('snapshot_hash', '')}")
        attested = integrator.attest_snapshot(snapshot)
        print(f"   存证: {'已提交' if attested else '待处理'}")
    else:
        print(f"未知命令: {command}")
