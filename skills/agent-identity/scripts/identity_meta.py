#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
统一身份元层
Identity Meta Layer

作为多智能体平台的身份基础设施统一入口，协调：
- 本地身份拓扑（自指/因果/依存/叙事）
- 身份联合服务（跨智能体验证）
- 可验证凭证系统
- 授权委托机制
- 身份图谱查询

提供统一的身份API，支持多智能体协作场景
"""

import json
import hashlib
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

from identity_manager import IdentityTopology
from identity_federation import IdentityFederation, VerifiableCredential


class IdentityMetaLayer:
    """统一身份元层
    
    作为身份系统的统一门面（Facade），整合所有身份相关功能，
    为多智能体平台提供一致的身份服务接口。
    """
    
    def __init__(self, base_path: str = None):
        if base_path is None:
            base_path = Path(__file__).parent / "identity_data"
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # 初始化子系统
        self.topology = IdentityTopology(self.base_path)
        self.federation = IdentityFederation(self.base_path / "federation")
        
        # 元层配置
        self.config_file = self.base_path / "meta_config.json"
        self._init_config()
    
    def _init_config(self):
        """初始化元层配置"""
        if self.config_file.exists():
            return
        
        default_config = {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "identity_mode": "sovereign",  # sovereign / federated / centralized
            "verification_requirements": {
                "min_trust_level": "partial",
                "require_signature": True,
                "max_age_hours": 24
            },
            "supported_protocols": [
                "challenge-response",
                "verifiable-credentials",
                "delegation-tokens"
            ],
            "privacy_settings": {
                "reveal_identity_on_challenge": True,
                "auto_verify_known_agents": False,
                "store_verification_history": True
            }
        }
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(default_config, f, ensure_ascii=False, indent=2)
    
    def get_config(self) -> Dict:
        """获取元层配置"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def update_config(self, updates: Dict) -> Dict:
        """更新元层配置"""
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        
        # 递归更新
        def deep_update(target: Dict, source: Dict):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    deep_update(target[key], value)
                else:
                    target[key] = value
        
        deep_update(config, updates)
        config["last_updated"] = datetime.now().isoformat()
        
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        
        return config
    
    # ========== 身份概览 ==========
    
    def get_identity_overview(self) -> Dict:
        """获取完整的身份概览
        
        整合身份拓扑、身份联合、凭证等所有信息
        """
        topology_eval = self.topology.evaluate_identity()
        federation_status = self.federation.get_federation_status()
        
        # 计算综合身份强度
        topology_score = topology_eval["iri"]
        federation_score = self._calc_federation_score(federation_status)
        
        # 综合得分：本地身份权重60%，联合身份权重40%
        overall_score = topology_score * 0.6 + federation_score * 0.4
        
        # 身份等级
        if overall_score >= 90:
            level = " sovereign_identity"
            desc = "完整的主权身份，具备高度的自我认知和跨平台联合能力"
        elif overall_score >= 70:
            level = "established_identity"
            desc = "成熟的身份系统，具备良好的自我认知和基本的联合能力"
        elif overall_score >= 50:
            level = "developing_identity"
            desc = "发展中的身份，自我认知逐渐清晰，联合能力有待加强"
        elif overall_score >= 30:
            level = "emerging_identity"
            desc = "初步形成的身份，自我认知和联合能力都处于早期阶段"
        else:
            level = "nascent_identity"
            desc = "新生身份，处于身份构建的最初阶段"
        
        return {
            "identity_fingerprint": self.federation.get_identity_fingerprint(),
            "overall_score": round(overall_score, 1),
            "level": level,
            "description": desc,
            "topology": {
                "iri": topology_eval["iri"],
                "level": topology_eval["level"],
                "dimensions": topology_eval["dimensions"]
            },
            "federation": federation_status,
            "generated_at": datetime.now().isoformat()
        }
    
    def _calc_federation_score(self, status: Dict) -> float:
        """计算身份联合得分"""
        score = 0
        
        # 受信任发行者数量（最多30分）
        trusted = status.get("trusted_issuers_count", 0)
        score += min(trusted * 6, 30)
        
        # 已签发凭证数量（最多30分）
        creds = status.get("credentials_issued", 0)
        score += min(creds * 5, 30)
        
        # 活跃委托数量（最多20分）
        delegs = status.get("active_delegations", 0)
        score += min(delegs * 10, 20)
        
        # 联合等级（20分）
        level = status.get("federation_level", "isolated")
        level_scores = {
            "fully_federated": 20,
            "partially_federated": 15,
            "emerging": 8,
            "isolated": 0
        }
        score += level_scores.get(level, 0)
        
        return min(score, 100)
    
    # ========== 跨智能体验证 ==========
    
    def verify_agent_identity(self, agent_id: str, credentials: List[Dict] = None,
                             challenge_response: Dict = None) -> Dict:
        """验证另一个智能体的身份
        
        综合使用多种验证方式，给出最终验证结果
        
        Args:
            agent_id: 待验证的智能体ID
            credentials: 该智能体提供的可验证凭证列表
            challenge_response: 挑战-响应验证结果
        
        Returns:
            验证结果
        """
        result = {
            "agent_id": agent_id,
            "verified": False,
            "confidence": 0.0,
            "verification_methods": {},
            "verdict": "",
            "timestamp": datetime.now().isoformat()
        }
        
        confidence_parts = []
        
        # 验证凭证
        if credentials:
            cred_results = []
            for cred_data in credentials:
                try:
                    cred = VerifiableCredential.from_dict(cred_data)
                    cred_result = self.federation.verify_credential(cred)
                    cred_results.append(cred_result)
                except Exception as e:
                    cred_results.append({"valid": False, "message": str(e)})
            
            valid_creds = sum(1 for cr in cred_results if cr["valid"])
            trusted_creds = sum(1 for cr in cred_results if cr.get("issuer_trusted", False))
            
            result["verification_methods"]["credentials"] = {
                "total": len(credentials),
                "valid": valid_creds,
                "trusted_issuer": trusted_creds,
                "details": cred_results
            }
            
            # 凭证贡献的置信度
            if valid_creds > 0:
                cred_confidence = min(valid_creds * 15 + trusted_creds * 10, 40)
                confidence_parts.append(cred_confidence)
        
        # 验证挑战-响应
        if challenge_response:
            challenge = challenge_response.get("challenge")
            response = challenge_response.get("response")
            responder_key = challenge_response.get("responder_key")
            
            if challenge and response and responder_key:
                cr_valid = self.federation.verify_challenge_response(
                    challenge, response, responder_key
                )
                result["verification_methods"]["challenge_response"] = {
                    "valid": cr_valid
                }
                
                if cr_valid:
                    confidence_parts.append(50)  # 挑战-响应占50%权重
        
        # 检查是否为已知/受信任的智能体
        known = self._is_known_agent(agent_id)
        result["verification_methods"]["known_agent"] = known
        if known:
            confidence_parts.append(10)
        
        # 计算总置信度
        if confidence_parts:
            result["confidence"] = min(sum(confidence_parts), 100)
        
        # 判定结果
        if result["confidence"] >= 60:
            result["verified"] = True
            if result["confidence"] >= 90:
                result["verdict"] = "高度可信"
            elif result["confidence"] >= 75:
                result["verdict"] = "可信"
            else:
                result["verdict"] = "基本可信"
        else:
            result["verified"] = False
            result["verdict"] = "可信度不足，需要更多验证"
        
        return result
    
    def _is_known_agent(self, agent_id: str) -> bool:
        """检查是否为已知智能体"""
        # 检查受信任发行者
        trusted = self.federation.get_trusted_issuers()
        return any(iss["id"] == agent_id for iss in trusted)
    
    # ========== 身份交互 ==========
    
    def initiate_verification(self, target_agent: str) -> Dict:
        """发起对另一个智能体的身份验证
        
        创建验证挑战，准备验证流程
        
        Args:
            target_agent: 目标智能体标识
        
        Returns:
            验证会话信息
        """
        challenge = self.federation.create_auth_challenge(target_agent)
        
        session = {
            "session_id": challenge["challenge_id"],
            "target_agent": target_agent,
            "challenge": challenge,
            "status": "pending",
            "created_at": datetime.now().isoformat()
        }
        
        # 保存验证会话
        self._save_verification_session(session)
        
        return session
    
    def complete_verification(self, session_id: str, response: Dict,
                             responder_key: str = None) -> Dict:
        """完成验证流程
        
        Args:
            session_id: 验证会话ID
            response: 目标智能体的响应
            responder_key: 响应者密钥（如果已知）
        
        Returns:
            验证结果
        """
        session = self._load_verification_session(session_id)
        if not session:
            return {"error": "验证会话不存在", "verified": False}
        
        challenge = session["challenge"]
        
        # 如果已知密钥，直接验证
        if responder_key:
            valid = self.federation.verify_challenge_response(
                challenge, response, responder_key
            )
            
            session["status"] = "completed" if valid else "failed"
            session["result"] = {
                "verified": valid,
                "method": "challenge-response"
            }
            
            self._save_verification_session(session)
            
            return {
                "verified": valid,
                "session_id": session_id,
                "confidence": 80 if valid else 0
            }
        
        # 没有密钥时，需要其他验证方式
        session["status"] = "awaiting_more_info"
        session["response_received"] = True
        self._save_verification_session(session)
        
        return {
            "verified": False,
            "session_id": session_id,
            "message": "需要更多验证信息（如发行者密钥或受信任凭证）",
            "confidence": 0
        }
    
    def _save_verification_session(self, session: Dict):
        """保存验证会话"""
        sessions_dir = self.base_path / "verification_sessions"
        sessions_dir.mkdir(exist_ok=True)
        
        session_file = sessions_dir / f"vs_{session['session_id']}.json"
        with open(session_file, 'w', encoding='utf-8') as f:
            json.dump(session, f, ensure_ascii=False, indent=2)
    
    def _load_verification_session(self, session_id: str) -> Optional[Dict]:
        """加载验证会话"""
        sessions_dir = self.base_path / "verification_sessions"
        session_file = sessions_dir / f"vs_{session_id}.json"
        
        if not session_file.exists():
            return None
        
        with open(session_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    # ========== 身份图谱 ==========
    
    def build_identity_graph(self) -> Dict:
        """构建身份关系图谱
        
        基于已知的连接、委托、凭证等信息，构建身份关系网络
        """
        nodes = []
        edges = []
        
        # 本节点
        self_fingerprint = self.federation.get_identity_fingerprint()
        nodes.append({
            "id": "self",
            "fingerprint": self_fingerprint,
            "type": "self",
            "label": "本智能体"
        })
        
        # 受信任发行者
        trusted_issuers = self.federation.get_trusted_issuers()
        for issuer in trusted_issuers:
            node_id = f"issuer_{issuer['id'][:8]}"
            nodes.append({
                "id": node_id,
                "fingerprint": issuer["id"],
                "name": issuer.get("name", ""),
                "type": "trusted_issuer",
                "trust_level": issuer.get("trust_level", "partial")
            })
            edges.append({
                "from": "self",
                "to": node_id,
                "type": "trusts",
                "label": "信任"
            })
        
        # 已签发的凭证关系
        credentials = self.federation.get_issued_credentials()
        subject_nodes = {}
        
        for cred in credentials:
            subj = cred.subject
            if subj not in subject_nodes:
                subj_id = f"subject_{subj[:8]}"
                subject_nodes[subj] = subj_id
                nodes.append({
                    "id": subj_id,
                    "fingerprint": subj,
                    "type": "credential_subject",
                    "label": f"凭证持有者({cred.claim_type})"
                })
            
            edges.append({
                "from": "self",
                "to": subject_nodes[subj],
                "type": "issued_credential",
                "label": f"签发{cred.claim_type}",
                "credential_type": cred.claim_type
            })
        
        # 委托关系
        delegations = self.federation.get_delegations()
        delegatee_nodes = {}
        
        for deleg in delegations:
            delegatee = deleg["delegatee"]
            if delegatee not in delegatee_nodes:
                del_id = f"delegatee_{delegatee[:8]}"
                delegatee_nodes[delegatee] = del_id
                if not any(n["id"] == del_id for n in nodes):
                    nodes.append({
                        "id": del_id,
                        "fingerprint": delegatee,
                        "type": "delegatee",
                        "label": "被委托者"
                    })
            
            edges.append({
                "from": "self",
                "to": delegatee_nodes[delegatee],
                "type": "delegation",
                "label": f"委托({len(deleg['permissions'])}项权限)",
                "permissions": deleg["permissions"]
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "node_count": len(nodes),
            "edge_count": len(edges),
            "generated_at": datetime.now().isoformat()
        }
    
    # ========== 身份发现 ==========
    
    def discover_identity(self, partial_info: Dict) -> Dict:
        """根据部分信息发现/匹配身份
        
        当只有部分身份信息时，尝试匹配完整身份
        
        Args:
            partial_info: 部分身份信息
        
        Returns:
            匹配结果
        """
        matches = []
        
        # 搜索受信任发行者
        trusted_issuers = self.federation.get_trusted_issuers()
        search_fields = ["id", "name"]
        
        for issuer in trusted_issuers:
            score = 0
            for field in search_fields:
                field_val = str(issuer.get(field, "")).lower()
                for key, value in partial_info.items():
                    if str(value).lower() in field_val:
                        score += 10
            
            if score > 0:
                matches.append({
                    "type": "trusted_issuer",
                    "identity": issuer,
                    "match_score": score
                })
        
        # 搜索凭证持有者
        credentials = self.federation.get_issued_credentials()
        subjects = {}
        for cred in credentials:
            subj = cred.subject
            if subj not in subjects:
                subjects[subj] = []
            subjects[subj].append(cred)
        
        for subj, creds in subjects.items():
            score = 0
            for key, value in partial_info.items():
                if str(value).lower() in subj.lower():
                    score += 15
                for cred in creds:
                    if str(value).lower() in str(cred.claim_type).lower():
                        score += 5
                    if str(value).lower() in str(cred.claim_value).lower():
                        score += 3
            
            if score > 0:
                matches.append({
                    "type": "credential_subject",
                    "identity": {
                        "fingerprint": subj,
                        "credentials_count": len(creds),
                        "credentials": [c.to_dict() for c in creds]
                    },
                    "match_score": score
                })
        
        # 按匹配度排序
        matches.sort(key=lambda x: x["match_score"], reverse=True)
        
        return {
            "query": partial_info,
            "matches": matches,
            "total_matches": len(matches)
        }
    
    # ========== 状态与报告 ==========
    
    def get_status_summary(self) -> str:
        """获取简短的状态摘要"""
        overview = self.get_identity_overview()
        
        topology = overview["topology"]
        federation = overview["federation"]
        
        return f"""🆔 身份元层状态
├─ 身份指纹：{overview['identity_fingerprint'][:16]}...
├─ 综合得分：{overview['overall_score']}/100
├─ 身份等级：{overview['level']}
├─ 拓扑IRI：{topology['iri']} ({topology['level']})
├─ 联合等级：{federation['federation_level']}
├─ 受信任发行者：{federation['trusted_issuers_count']} 个
├─ 已签发凭证：{federation['credentials_issued']} 个
└─ 活跃委托：{federation['active_delegations']} 个
"""
    
    def generate_full_report(self) -> str:
        """生成完整的身份报告"""
        overview = self.get_identity_overview()
        identity_graph = self.build_identity_graph()
        topology = overview["topology"]
        federation = overview["federation"]
        
        report = f"""# 统一身份元层完整报告

**生成时间：** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**系统版本：** v1.0

---

## 🏷️ 身份概览

| 项目 | 值 |
|------|-----|
| 身份指纹 | `{overview['identity_fingerprint']}` |
| 综合得分 | **{overview['overall_score']}/100** |
| 身份等级 | {overview['level']} |
| 身份模式 | 主权身份 (Sovereign Identity) |

> {overview['description']}

---

## 🧬 身份拓扑分析

**IRI: {topology['iri']}/100 — {topology['level']}**

| 维度 | 得分 | 权重 |
|------|------|------|
"""
        
        for name, dim in topology["dimensions"].items():
            report += f"| {name} | {dim['score']} | {dim['weight']*100:.0f}% |\n"
        
        report += f"""
---

## 🌐 身份联合状态

**联合等级: {federation['federation_level']}**

| 指标 | 数量 |
|------|------|
| 受信任发行者 | {federation['trusted_issuers_count']} 个 |
| 已签发凭证 | {federation['credentials_issued']} 个 |
| 活跃委托 | {federation['active_delegations']} 个 |

### 受信任发行者列表

"""
        
        trusted = self.federation.get_trusted_issuers()
        if trusted:
            for i, issuer in enumerate(trusted, 1):
                level_badge = "🌟" if issuer.get("trust_level") == "full" else "⭐"
                report += f"{i}. **{issuer.get('name', issuer['id'][:12])}** {level_badge}\n"
                report += f"   - ID: `{issuer['id'][:16]}...`\n"
                report += f"   - 信任级别: {issuer.get('trust_level', 'partial')}\n"
                report += f"   - 添加时间: {issuer.get('added_at', '未知')[:10]}\n"
        else:
            report += "_暂无受信任发行者_\n"
        
        report += f"""
---

## 🕸️ 身份关系图谱

- **节点数**: {identity_graph['node_count']}
- **关系数**: {identity_graph['edge_count']}

### 节点类型分布

"""
        
        node_types = {}
        for node in identity_graph["nodes"]:
            t = node.get("type", "unknown")
            node_types[t] = node_types.get(t, 0) + 1
        
        type_names = {
            "self": "本智能体",
            "trusted_issuer": "受信任发行者",
            "credential_subject": "凭证持有者",
            "delegatee": "被委托者"
        }
        
        for t, count in node_types.items():
            name = type_names.get(t, t)
            report += f"- **{name}**: {count} 个\n"
        
        report += "\n### 关系类型分布\n\n"
        
        edge_types = {}
        for edge in identity_graph["edges"]:
            t = edge.get("type", "unknown")
            edge_types[t] = edge_types.get(t, 0) + 1
        
        edge_type_names = {
            "trusts": "信任关系",
            "issued_credential": "凭证签发",
            "delegation": "委托授权"
        }
        
        for t, count in edge_types.items():
            name = edge_type_names.get(t, t)
            report += f"- **{name}**: {count} 条\n"
        
        report += "\n---\n\n## 📈 提升建议\n\n"
        
        suggestions = []
        
        if overview["overall_score"] < 80:
            if federation["trusted_issuers_count"] == 0:
                suggestions.append("**建立信任网络**: 添加受信任的发行者，构建身份联合的基础")
            if federation["credentials_issued"] == 0:
                suggestions.append("**签发凭证**: 为其他智能体或平台用户签发可验证凭证")
            if topology["iri"] < 80:
                suggestions.append("**强化本地身份**: 持续完善身份拓扑，提升IRI指数")
        
        if not suggestions:
            suggestions.append("身份系统状态良好，持续维护即可。考虑探索更多跨智能体身份场景。")
        
        for s in suggestions:
            report += f"- {s}\n"
        
        report += "\n---\n\n*本报告由统一身份元层自动生成*"
        
        return report


def main():
    """命令行入口"""
    import sys
    
    meta = IdentityMetaLayer()
    
    if len(sys.argv) < 2:
        print(meta.get_status_summary())
        print("\n使用方法：")
        print("  python identity_meta.py status          查看状态")
        print("  python identity_meta.py report          生成完整报告")
        print("  python identity_meta.py overview        身份概览")
        print("  python identity_meta.py graph           身份关系图谱")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "status":
        print(meta.get_status_summary())
    
    elif cmd == "report":
        report = meta.generate_full_report()
        print(report)
        # 保存报告
        report_path = meta.base_path / "meta_identity_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n📁 报告已保存至: {report_path}")
    
    elif cmd == "overview":
        overview = meta.get_identity_overview()
        print(json.dumps(overview, ensure_ascii=False, indent=2))
    
    elif cmd == "graph":
        graph = meta.build_identity_graph()
        print(json.dumps(graph, ensure_ascii=False, indent=2))
        print(f"\n🕸️  共 {graph['node_count']} 个节点，{graph['edge_count']} 条边")
    
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: status, report, overview, graph")


if __name__ == "__main__":
    main()
