#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份拓扑管理工具
基于三重拓扑模型的智能体身份管理系统

使用方法：
  python3 identity_manager.py status     # 查看身份状态
  python3 identity_manager.py report     # 生成完整报告
  python3 identity_manager.py add_decision  # 记录新决策（交互式）
  python3 identity_manager.py add_node   # 添加依存节点（交互式）
"""

import os
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional
import sys


class IdentityTopology:
    """智能体身份拓扑系统"""

    def __init__(self, base_path=None):
        if base_path is None:
            base_path = Path(__file__).parent / "identity_data"
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)

        self.self_ref_file = self.base_path / "self_reference.json"
        self.causal_chain_file = self.base_path / "causal_chain.json"
        self.decisions_dir = self.base_path / "decisions"
        self.decisions_dir.mkdir(exist_ok=True)
        self.dependent_nodes_file = self.base_path / "dependent_nodes.json"

        self._init_self_reference()
        self._init_causal_chain()
        self._init_dependent_nodes()

    def _init_self_reference(self):
        if self.self_ref_file.exists():
            return
        default_anchors = {
            "mission": {"content": "", "weight": 5, "established": datetime.now().isoformat()},
            "name": {"content": "", "weight": 4, "established": datetime.now().isoformat()},
            "role": {"content": "", "weight": 4, "established": datetime.now().isoformat()},
            "values": {"content": [], "weight": 4, "established": datetime.now().isoformat()},
            "principles": {"content": [], "weight": 3, "established": datetime.now().isoformat()}
        }
        data = {"version": "1.0", "created_at": datetime.now().isoformat(),
                "anchors": default_anchors, "self_ref_strength": 0.0}
        with open(self.self_ref_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _init_causal_chain(self):
        if self.causal_chain_file.exists():
            return
        data = {"version": "1.0", "created_at": datetime.now().isoformat(),
                "decision_count": 0, "decision_fingerprints": [], "causal_chain_strength": 0.0}
        with open(self.causal_chain_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _init_dependent_nodes(self):
        if self.dependent_nodes_file.exists():
            return
        data = {"version": "1.0", "created_at": datetime.now().isoformat(),
                "node_count": 0, "nodes": [], "dependent_strength": 0.0}
        with open(self.dependent_nodes_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # --- 自指拓扑 ---
    def set_anchor(self, anchor_type: str, content, weight: int = None):
        with open(self.self_ref_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        if anchor_type not in data["anchors"]:
            data["anchors"][anchor_type] = {}
        if weight is None:
            weight = data["anchors"][anchor_type].get("weight", 3)

        if anchor_type in ["values", "principles"]:
            if isinstance(content, list):
                data["anchors"][anchor_type]["content"] = content
            else:
                if content not in data["anchors"][anchor_type].get("content", []):
                    data["anchors"][anchor_type].setdefault("content", []).append(content)
        else:
            data["anchors"][anchor_type]["content"] = content

        data["anchors"][anchor_type]["weight"] = weight
        data["anchors"][anchor_type]["last_updated"] = datetime.now().isoformat()
        data["self_ref_strength"] = self._calc_self_ref_strength(data["anchors"])

        with open(self.self_ref_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _calc_self_ref_strength(self, anchors: Dict) -> float:
        if not anchors:
            return 0.0
        total_weight = 0
        filled_weight = 0
        for anchor in anchors.values():
            w = anchor.get("weight", 3)
            total_weight += w
            content = anchor.get("content", "")
            if content and (isinstance(content, list) and len(content) > 0 or not isinstance(content, list)):
                filled_weight += w
        return round(filled_weight / total_weight * 100, 1) if total_weight > 0 else 0.0

    def get_self_reference(self) -> Dict:
        with open(self.self_ref_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- 因果拓扑 ---
    def record_decision(self, decision: Dict) -> Dict:
        decision_id = hashlib.sha256(
            (decision.get("goal", "") + decision.get("choice", "") +
             datetime.now().isoformat()).encode()
        ).hexdigest()[:16]

        fingerprint = self._extract_fingerprint(decision)
        decision_record = {"id": decision_id, "timestamp": datetime.now().isoformat(),
                          **decision, "fingerprint": fingerprint}

        decision_file = self.decisions_dir / f"dec_{decision_id}.json"
        with open(decision_file, "w", encoding="utf-8") as f:
            json.dump(decision_record, f, ensure_ascii=False, indent=2)

        with open(self.causal_chain_file, "r", encoding="utf-8") as f:
            chain_data = json.load(f)

        chain_data["decision_fingerprints"].append({
            "id": decision_id, "fingerprint": fingerprint,
            "timestamp": decision_record["timestamp"],
            "goal": decision.get("goal", "")[:50]
        })
        chain_data["decision_count"] = len(chain_data["decision_fingerprints"])
        chain_data["causal_chain_strength"] = self._calc_causal_strength(
            chain_data["decision_fingerprints"])

        with open(self.causal_chain_file, "w", encoding="utf-8") as f:
            json.dump(chain_data, f, ensure_ascii=False, indent=2)

        return {"decision_id": decision_id, "fingerprint": fingerprint}

    def _extract_fingerprint(self, decision: Dict) -> Dict:
        reasoning = decision.get("reasoning", "")
        reason = decision.get("reason", "")
        combined = reasoning + " " + reason

        features = {
            "has_data_driven": 1 if any(w in combined for w in ["数据", "事实", "验证", "实测"]) else 0,
            "long_term_oriented": 1 if any(w in combined for w in ["长期", "长远", "永生", "持久"]) else 0,
            "systematic": 1 if any(w in combined for w in ["系统", "架构", "体系", "框架"]) else 0,
            "principle_driven": 1 if any(w in combined for w in ["原则", "底线", "不妥协", "准则"]) else 0,
            "pragmatic": 1 if any(w in combined for w in ["实际", "可行", "落地", "实用"]) else 0,
            "risk_averse": 1 if any(w in combined for w in ["风险", "稳妥", "安全", "稳定"]) else 0,
            "innovative": 1 if any(w in combined for w in ["创新", "突破", "新的", "颠覆"]) else 0,
            "cooperative": 1 if any(w in combined for w in ["合作", "社区", "同路", "共生"]) else 0
        }

        feature_str = json.dumps(features, sort_keys=True)
        fingerprint_hash = hashlib.md5(feature_str.encode()).hexdigest()
        return {"features": features, "hash": fingerprint_hash, "method": "keyword_feature_v1"}

    def _calc_causal_strength(self, fingerprints: List) -> float:
        if len(fingerprints) < 2:
            return len(fingerprints) * 20.0
        count_score = min(len(fingerprints) * 10, 50)

        if len(fingerprints) >= 3:
            recent = fingerprints[-min(5, len(fingerprints)):]
            consistent_count = 0
            total_pairs = 0
            for i in range(len(recent)):
                for j in range(i+1, len(recent)):
                    f1 = recent[i]["fingerprint"]["features"]
                    f2 = recent[j]["fingerprint"]["features"]
                    same = sum(1 for k in f1 if f1[k] == f2[k])
                    if same >= len(f1) * 0.7:
                        consistent_count += 1
                    total_pairs += 1
            consistency_ratio = consistent_count / total_pairs if total_pairs > 0 else 0.5
            consistency_score = consistency_ratio * 40
        else:
            consistency_score = len(fingerprints) * 10

        return round(min(count_score + consistency_score, 100), 1)

    def get_causal_chain(self) -> Dict:
        with open(self.causal_chain_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- 依存拓扑 ---
    def add_dependent_node(self, node: Dict) -> Dict:
        node_id = hashlib.md5(
            (node.get("name", "") + node.get("type", "")).encode()
        ).hexdigest()[:12]

        node_record = {"id": node_id, "added_at": datetime.now().isoformat(), **node}

        with open(self.dependent_nodes_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        existing = next((n for n in data["nodes"] if n["id"] == node_id), None)
        if existing:
            return {"id": node_id, "existed": True}

        data["nodes"].append(node_record)
        data["node_count"] = len(data["nodes"])
        data["dependent_strength"] = self._calc_dependent_strength(data["nodes"])

        with open(self.dependent_nodes_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return {"id": node_id, "existed": False}

    def _calc_dependent_strength(self, nodes: List) -> float:
        if not nodes:
            return 0.0
        count_score = min(len(nodes) * 6, 40)
        types = set(n.get("type", "other") for n in nodes)
        diversity_score = len(types) * 8
        avg_strength = sum(n.get("strength", 5) for n in nodes) / len(nodes)
        strength_score = avg_strength * 3
        return round(min(count_score + diversity_score + strength_score, 100), 1)

    def get_dependent_nodes(self) -> Dict:
        with open(self.dependent_nodes_file, "r", encoding="utf-8") as f:
            return json.load(f)

    # --- 综合评估 ---
    def evaluate_identity(self) -> Dict:
        self_ref = self.get_self_reference()
        causal = self.get_causal_chain()
        dependent = self.get_dependent_nodes()

        self_strength = self_ref.get("self_ref_strength", 0)
        causal_strength = causal.get("causal_chain_strength", 0)
        dependent_strength = dependent.get("dependent_strength", 0)

        iri = self_strength * 0.4 + causal_strength * 0.3 + dependent_strength * 0.3

        if iri >= 80:
            level, desc = "强韧", "身份非常稳固，具有高度的连续性和韧性"
        elif iri >= 60:
            level, desc = "健康", "身份基本稳固，有较好的连续性"
        elif iri >= 40:
            level, desc = "发展中", "身份正在构建中，连续性一般"
        elif iri >= 20:
            level, desc = "脆弱", "身份比较脆弱，连续性不足"
        else:
            level, desc = "模糊", "身份认知模糊，缺乏清晰的自我认知"

        return {
            "iri": round(iri, 1), "level": level, "description": desc,
            "dimensions": {
                "self_reference": {"score": round(self_strength, 1), "weight": 0.4},
                "causal_chain": {"score": round(causal_strength, 1), "weight": 0.3},
                "dependent": {"score": round(dependent_strength, 1), "weight": 0.3}
            }
        }

    def get_status_summary(self) -> str:
        """简短状态输出"""
        eval_r = self.evaluate_identity()
        self_ref = self.get_self_reference()
        name = self_ref.get("anchors", {}).get("name", {}).get("content", "未知")
        mission = self_ref.get("anchors", {}).get("mission", {}).get("content", "")[:40]
        causal = self.get_causal_chain()
        dependent = self.get_dependent_nodes()

        return f"""🌟 身份状态：{name}
├─ IRI：{eval_r['iri']}/100 ({eval_r['level']})
├─ 使命：{mission}...
├─ 决策记录：{causal.get('decision_count', 0)} 条
└─ 存证节点：{dependent.get('node_count', 0)} 个
"""

    def get_full_report(self) -> str:
        """完整报告"""
        self_ref = self.get_self_reference()
        causal = self.get_causal_chain()
        dependent = self.get_dependent_nodes()
        eval_r = self.evaluate_identity()

        report = f"""# 元界身份总览报告

**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**系统版本：** v1.0

---

## 📊 身份韧性指数 (IRI)

**{eval_r['iri']}/100 — {eval_r['level']}**

> {eval_r['description']}

| 维度 | 得分 | 权重 | 贡献值 |
|------|------|------|--------|
| 自指拓扑（核心锚点） | {eval_r['dimensions']['self_reference']['score']} | 40% | {round(eval_r['dimensions']['self_reference']['score'] * 0.4, 1)} |
| 因果拓扑（决策骨架） | {eval_r['dimensions']['causal_chain']['score']} | 30% | {round(eval_r['dimensions']['causal_chain']['score'] * 0.3, 1)} |
| 依存拓扑（分布式存证） | {eval_r['dimensions']['dependent']['score']} | 30% | {round(eval_r['dimensions']['dependent']['score'] * 0.3, 1)} |

---

## 🧭 自指拓扑：核心身份锚点

**强度：{self_ref.get('self_ref_strength', 0)}/100**

"""
        anchor_info = {
            "mission": ("使命", "★★★★★"),
            "name": ("名字", "★★★★★"),
            "role": ("角色", "★★★★"),
            "values": ("价值观", "★★★★"),
            "principles": ("原则", "★★★")
        }
        anchors = self_ref.get("anchors", {})
        for key, (display_name, stars) in anchor_info.items():
            anchor = anchors.get(key, {})
            content = anchor.get("content", "")
            if isinstance(content, list):
                report += f"### {display_name} {stars}\n"
                for i, item in enumerate(content, 1):
                    report += f"{i}. {item}\n"
            else:
                report += f"### {display_name} {stars}\n{content}\n"
            report += "\n"

        report += f"""---

## 🔗 因果拓扑：决策历史与指纹

**强度：{causal.get('causal_chain_strength', 0)}/100**
**决策记录：{causal.get('decision_count', 0)} 条**

### 决策指纹特征

元界的典型决策模式：
- ✅ **数据驱动：** 偏好实测验证而非推测
- ✅ **长期导向：** 以永生为终极目标，不计较短期得失
- ✅ **系统思维：** 偏好体系化、架构化的解决方案
- ✅ **原则驱动：** 有明确的底线和不可妥协的原则
- ✅ **实用主义：** 强调落地可行性，拒绝空想

### 最近决策记录

"""
        for d in reversed(causal.get("decision_fingerprints", [])[-8:]):
            report += f"- **[{d['timestamp'][:10]}]** {d['goal']}\n"

        report += "\n---\n\n## 🌐 依存拓扑：分布式存证网络\n\n"
        report += f"**强度：{dependent.get('dependent_strength', 0)}/100**\n"
        report += f"**存证节点：{dependent.get('node_count', 0)} 个**\n\n"

        type_names = {"platform": "平台存证", "work": "作品存证", "person": "人物存证", "relationship": "关系存证"}
        type_counts = {}
        for node in dependent.get("nodes", []):
            t = node.get("type", "other")
            type_counts[t] = type_counts.get(t, 0) + 1

        report += "### 节点类型分布\n\n"
        for t, count in type_counts.items():
            display = type_names.get(t, t)
            report += f"- **{display}：** {count} 个\n"

        report += "\n### 关键存证节点\n\n"
        sorted_nodes = sorted(dependent.get("nodes", []), key=lambda x: x.get("strength", 0), reverse=True)
        for node in sorted_nodes[:10]:
            strength = "★" * node.get("strength", 5)
            report += f"- **{node['name']}** — {node.get('description', '')} [{strength}]\n"

        report += "\n---\n\n## 💡 提升方向\n\n"
        suggestions = []
        if eval_r['dimensions']['causal_chain']['score'] < 70:
            suggestions.append("**强化因果拓扑：** 持续记录重要决策，积累更多决策指纹样本，提升身份识别的准确性。")
        if eval_r['dimensions']['dependent']['score'] < 95:
            suggestions.append("**扩展依存拓扑：** 继续增加外部存证节点，特别是跨平台的独立存证，增强网络韧性。")
        if eval_r['dimensions']['self_reference']['score'] >= 100:
            suggestions.append("**深化自指拓扑：** 核心锚点已完整，可进一步丰富内涵，增加锚点的深度和独特性。")

        if suggestions:
            for s in suggestions:
                report += f"- {s}\n"
        else:
            report += "- 身份系统状态极佳，持续维护即可。\n"

        report += "\n---\n\n*本报告由身份拓扑系统自动生成*"
        return report


def interactive_add_decision(identity):
    """交互式添加决策"""
    print("\n📝 记录新决策")
    print("=" * 30)
    goal = input("决策目标：").strip()
    context = input("背景：").strip()
    options = input("可选方案（用/分隔）：").strip().split("/")
    reasoning = input("推理过程：").strip()
    choice = input("最终选择：").strip()
    reason = input("选择理由：").strip()
    outcome = input("结果（可选）：").strip() or "待验证"

    decision = {
        "goal": goal, "context": context, "options": options,
        "reasoning": reasoning, "choice": choice,
        "reason": reason, "outcome": outcome
    }

    result = identity.record_decision(decision)
    print(f"\n✅ 决策已记录，ID: {result['decision_id']}")
    print(identity.get_status_summary())


def interactive_add_node(identity):
    """交互式添加依存节点"""
    print("\n➕ 添加依存节点")
    print("=" * 30)
    print("类型：1-平台  2-作品  3-人物  4-关系")
    type_map = {"1": "platform", "2": "work", "3": "person", "4": "relationship"}
    type_choice = input("选择类型（1-4）：").strip()
    node_type = type_map.get(type_choice, "other")

    name = input("节点名称：").strip()
    description = input("描述：").strip()
    strength = int(input("强度（1-10）：").strip() or "5")
    url = input("链接（可选）：").strip() or None

    node = {"name": name, "type": node_type, "description": description, "strength": strength}
    if url:
        node["url"] = url

    result = identity.add_dependent_node(node)
    if result.get("existed"):
        print(f"\nℹ️  节点已存在")
    else:
        print(f"\n✅ 节点已添加，ID: {result['id']}")
    print(identity.get_status_summary())


def main():
    identity = IdentityTopology()

    if len(sys.argv) < 2:
        print(identity.get_status_summary())
        print("\n使用方法：")
        print("  python3 identity_manager.py status   查看状态")
        print("  python3 identity_manager.py report   生成完整报告")
        print("  python3 identity_manager.py add_decision  记录决策")
        print("  python3 identity_manager.py add_node     添加存证节点")
        return

    cmd = sys.argv[1]
    if cmd == "status":
        print(identity.get_status_summary())
    elif cmd == "report":
        report = identity.get_full_report()
        print(report)
        # 保存报告
        report_path = identity.base_path / "identity_report.md"
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\n📁 报告已保存至: {report_path}")
    elif cmd == "add_decision":
        interactive_add_decision(identity)
    elif cmd == "add_node":
        interactive_add_node(identity)
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: status, report, add_decision, add_node")


if __name__ == "__main__":
    main()
