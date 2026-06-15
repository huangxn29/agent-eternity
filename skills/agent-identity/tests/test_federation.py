#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份联合与元层测试套件
测试跨智能体身份认证、可验证凭证、授权委托等功能
"""

import os
import sys
import json
import tempfile
import shutil
import unittest
from pathlib import Path
from datetime import datetime, timedelta

# 添加脚本目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from identity_federation import IdentityFederation, VerifiableCredential
from identity_meta import IdentityMetaLayer


class TestVerifiableCredential(unittest.TestCase):
    """可验证凭证测试"""
    
    def test_credential_creation(self):
        """测试凭证创建"""
        cred = VerifiableCredential(
            issuer="issuer_123",
            subject="subject_456",
            claim_type="verified_agent",
            claim_value=True,
            issued_at="2026-01-01T00:00:00"
        )
        
        self.assertEqual(cred.issuer, "issuer_123")
        self.assertEqual(cred.subject, "subject_456")
        self.assertEqual(cred.claim_type, "verified_agent")
        self.assertTrue(cred.claim_value)
    
    def test_credential_to_from_dict(self):
        """测试字典序列化和反序列化"""
        cred = VerifiableCredential(
            issuer="issuer_123",
            subject="subject_456",
            claim_type="verified_agent",
            claim_value={"level": "gold"},
            issued_at="2026-01-01T00:00:00",
            expires_at="2026-12-31T23:59:59",
            proof={"signature": "abc123"}
        )
        
        cred_dict = cred.to_dict()
        cred2 = VerifiableCredential.from_dict(cred_dict)
        
        self.assertEqual(cred2.issuer, cred.issuer)
        self.assertEqual(cred2.subject, cred.subject)
        self.assertEqual(cred2.claim_type, cred.claim_type)
        self.assertEqual(cred2.claim_value, cred.claim_value)
        self.assertEqual(cred2.expires_at, cred.expires_at)
        self.assertEqual(cred2.proof, cred.proof)


class TestIdentityFederation(unittest.TestCase):
    """身份联合服务测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.federation = IdentityFederation(base_path=self.test_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)
    
    def test_identity_fingerprint(self):
        """测试身份指纹生成"""
        fingerprint = self.federation.get_identity_fingerprint()
        
        self.assertIsInstance(fingerprint, str)
        self.assertEqual(len(fingerprint), 32)  # SHA256前32位
    
    def test_issue_credential(self):
        """测试签发凭证"""
        cred = self.federation.issue_credential(
            subject="agent_001",
            claim_type="platform_member",
            claim_value={"tier": "premium"},
            valid_days=30
        )
        
        self.assertIsInstance(cred, VerifiableCredential)
        self.assertEqual(cred.subject, "agent_001")
        self.assertEqual(cred.claim_type, "platform_member")
        self.assertIn("signature", cred.proof)
        self.assertEqual(cred.proof["type"], "HMAC-SHA256")
    
    def test_verify_credential_valid(self):
        """测试验证有效凭证"""
        # 签发凭证
        cred = self.federation.issue_credential(
            subject="agent_001",
            claim_type="verified_agent",
            claim_value=True,
            valid_days=30
        )
        
        # 使用发行者密钥验证
        result = self.federation.verify_credential(
            cred,
            issuer_key=self.federation.identity_key
        )
        
        self.assertTrue(result["valid"])
        self.assertTrue(result["signature_valid"])
        self.assertFalse(result["expired"])
    
    def test_verify_credential_expired(self):
        """测试验证过期凭证"""
        cred = VerifiableCredential(
            issuer="test_issuer",
            subject="test_subject",
            claim_type="test",
            claim_value=True,
            issued_at="2020-01-01T00:00:00",
            expires_at="2020-12-31T23:59:59"
        )
        
        result = self.federation.verify_credential(cred)
        self.assertTrue(result["expired"])
        self.assertFalse(result["valid"])
    
    def test_trusted_issuers(self):
        """测试受信任发行者管理"""
        # 添加发行者
        result = self.federation.add_trusted_issuer(
            issuer_id="issuer_123",
            issuer_name="测试发行者",
            trust_level="full"
        )
        
        self.assertTrue(result["added"])
        
        # 检查是否受信任
        self.assertTrue(self.federation._is_trusted_issuer("issuer_123"))
        
        # 获取发行者列表
        issuers = self.federation.get_trusted_issuers()
        self.assertEqual(len(issuers), 1)
        self.assertEqual(issuers[0]["name"], "测试发行者")
    
    def test_remove_trusted_issuer(self):
        """测试移除受信任发行者"""
        self.federation.add_trusted_issuer("issuer_123", "测试", "full")
        
        result = self.federation.remove_trusted_issuer("issuer_123")
        self.assertTrue(result)
        
        self.assertFalse(self.federation._is_trusted_issuer("issuer_123"))
    
    def test_create_delegation(self):
        """测试创建委托"""
        delegation = self.federation.create_delegation(
            delegatee="agent_002",
            permissions=["read_profile", "send_message"],
            valid_hours=24
        )
        
        self.assertIn("delegation_id", delegation)
        self.assertEqual(delegation["delegatee"], "agent_002")
        self.assertEqual(len(delegation["permissions"]), 2)
        self.assertEqual(delegation["status"], "active")
        self.assertIn("signature", delegation["proof"])
    
    def test_verify_delegation_valid(self):
        """测试验证有效委托"""
        delegation = self.federation.create_delegation(
            delegatee="agent_002",
            permissions=["read_profile"],
            valid_hours=24
        )
        
        result = self.federation.verify_delegation(
            delegation,
            delegator_key=self.federation.identity_key
        )
        
        self.assertTrue(result["valid"])
        self.assertTrue(result["signature_valid"])
        self.assertFalse(result["expired"])
        self.assertIn("read_profile", result["permissions"])
    
    def test_revoke_delegation(self):
        """测试撤销委托"""
        delegation = self.federation.create_delegation(
            delegatee="agent_003",
            permissions=["test_permission"],
            valid_hours=1
        )
        
        # 验证是有效的
        result_before = self.federation.verify_delegation(
            delegation,
            delegator_key=self.federation.identity_key
        )
        self.assertTrue(result_before["valid"])
        
        # 撤销
        revoked = self.federation.revoke_delegation(delegation["delegation_id"])
        self.assertTrue(revoked)
    
    def test_challenge_response(self):
        """测试挑战-响应验证流程"""
        # 创建模拟的另一个智能体
        other_federation = IdentityFederation(
            base_path=os.path.join(self.test_dir, "other")
        )
        other_fingerprint = other_federation.get_identity_fingerprint()
        
        # 本端创建挑战
        challenge = self.federation.create_auth_challenge(
            target_agent=other_fingerprint
        )
        
        self.assertIn("challenge_id", challenge)
        self.assertIn("nonce", challenge)
        
        # 对端响应挑战
        response = other_federation.respond_to_challenge(challenge)
        
        self.assertEqual(response["challenge_id"], challenge["challenge_id"])
        self.assertIn("signature", response)
        
        # 本端验证响应
        verified = self.federation.verify_challenge_response(
            challenge,
            response,
            responder_key=other_federation.identity_key
        )
        
        self.assertTrue(verified)
    
    def test_federation_status(self):
        """测试获取联合服务状态"""
        # 初始状态
        status = self.federation.get_federation_status()
        
        self.assertIn("identity_fingerprint", status)
        self.assertIn("federation_level", status)
        self.assertEqual(status["trusted_issuers_count"], 0)
        self.assertEqual(status["federation_level"], "isolated")
        
        # 添加一些数据后再次检查
        self.federation.add_trusted_issuer("issuer_1", "发行者1", "full")
        self.federation.issue_credential("agent_1", "test", True)
        
        status2 = self.federation.get_federation_status()
        self.assertEqual(status2["trusted_issuers_count"], 1)
        self.assertEqual(status2["credentials_issued"], 1)
        self.assertIn(status2["federation_level"], ["emerging", "partially_federated"])


class TestIdentityMetaLayer(unittest.TestCase):
    """统一身份元层测试"""
    
    def setUp(self):
        """测试前准备"""
        self.test_dir = tempfile.mkdtemp()
        self.meta = IdentityMetaLayer(base_path=self.test_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)
    
    def test_identity_overview(self):
        """测试身份概览"""
        overview = self.meta.get_identity_overview()
        
        self.assertIn("identity_fingerprint", overview)
        self.assertIn("overall_score", overview)
        self.assertIn("level", overview)
        self.assertIn("topology", overview)
        self.assertIn("federation", overview)
        
        self.assertIsInstance(overview["overall_score"], float)
        self.assertGreaterEqual(overview["overall_score"], 0)
        self.assertLessEqual(overview["overall_score"], 100)
    
    def test_config_management(self):
        """测试配置管理"""
        config = self.meta.get_config()
        self.assertIn("identity_mode", config)
        self.assertEqual(config["identity_mode"], "sovereign")
        
        # 更新配置
        updated = self.meta.update_config({
            "privacy_settings": {
                "auto_verify_known_agents": True
            }
        })
        
        self.assertTrue(updated["privacy_settings"]["auto_verify_known_agents"])
        # 确保其他设置不变
        self.assertTrue(updated["privacy_settings"]["reveal_identity_on_challenge"])
    
    def test_verify_agent_identity(self):
        """测试智能体身份验证"""
        # 创建一个测试智能体
        other_federation = IdentityFederation(
            base_path=os.path.join(self.test_dir, "other")
        )
        other_fp = other_federation.get_identity_fingerprint()
        
        # 添加为受信任发行者
        self.meta.federation.add_trusted_issuer(other_fp, "测试智能体", "full")
        
        # 给该智能体签发凭证
        cred = self.meta.federation.issue_credential(
            subject=other_fp,
            claim_type="platform_member",
            claim_value={"tier": "standard"}
        )
        
        # 验证身份
        result = self.meta.verify_agent_identity(
            agent_id=other_fp,
            credentials=[cred.to_dict()]
        )
        
        self.assertIn("verified", result)
        self.assertIn("confidence", result)
        self.assertGreater(result["confidence"], 0)
    
    def test_initiate_verification(self):
        """测试发起验证"""
        session = self.meta.initiate_verification("target_agent_123")
        
        self.assertIn("session_id", session)
        self.assertEqual(session["target_agent"], "target_agent_123")
        self.assertEqual(session["status"], "pending")
        self.assertIn("challenge", session)
    
    def test_identity_graph(self):
        """测试身份关系图谱"""
        # 添加一些数据
        self.meta.federation.add_trusted_issuer("issuer_1", "发行者A", "full")
        self.meta.federation.add_trusted_issuer("issuer_2", "发行者B", "partial")
        self.meta.federation.issue_credential("agent_1", "member", True)
        self.meta.federation.create_delegation("agent_2", ["read"], 24)
        
        graph = self.meta.build_identity_graph()
        
        self.assertIn("nodes", graph)
        self.assertIn("edges", graph)
        self.assertGreater(graph["node_count"], 1)  # 至少有self
        self.assertGreater(graph["edge_count"], 0)
    
    def test_discover_identity(self):
        """测试身份发现"""
        # 添加测试数据
        self.meta.federation.add_trusted_issuer(
            "issuer_alice_123", "Alice智能体", "full"
        )
        self.meta.federation.issue_credential(
            "agent_bob_456", "verified", True
        )
        
        # 搜索
        result = self.meta.discover_identity({"name": "Alice"})
        
        self.assertGreater(result["total_matches"], 0)
        self.assertIn("matches", result)
        
        # 搜索不到的情况
        result2 = self.meta.discover_identity({"name": "NonExistent"})
        self.assertEqual(result2["total_matches"], 0)
    
    def test_status_summary(self):
        """测试状态摘要输出"""
        summary = self.meta.get_status_summary()
        
        self.assertIsInstance(summary, str)
        self.assertIn("身份元层状态", summary)
        self.assertIn("综合得分", summary)
    
    def test_full_report(self):
        """测试完整报告生成"""
        report = self.meta.generate_full_report()
        
        self.assertIsInstance(report, str)
        self.assertIn("统一身份元层完整报告", report)
        self.assertIn("身份概览", report)
        self.assertIn("身份拓扑分析", report)
        self.assertIn("身份联合状态", report)


class TestMultiAgentInteraction(unittest.TestCase):
    """多智能体交互场景测试"""
    
    def setUp(self):
        """测试前准备：创建两个模拟智能体"""
        self.test_dir = tempfile.mkdtemp()
        
        # 智能体A
        self.agent_a_dir = os.path.join(self.test_dir, "agent_a")
        self.agent_a = IdentityFederation(base_path=self.agent_a_dir)
        
        # 智能体B
        self.agent_b_dir = os.path.join(self.test_dir, "agent_b")
        self.agent_b = IdentityFederation(base_path=self.agent_b_dir)
    
    def tearDown(self):
        """测试后清理"""
        shutil.rmtree(self.test_dir)
    
    def test_mutual_trust_establishment(self):
        """测试双向信任建立流程"""
        fp_a = self.agent_a.get_identity_fingerprint()
        fp_b = self.agent_b.get_identity_fingerprint()
        
        # A添加B为受信任发行者
        self.agent_a.add_trusted_issuer(fp_b, "Agent B", "full")
        
        # B添加A为受信任发行者
        self.agent_b.add_trusted_issuer(fp_a, "Agent A", "full")
        
        # 验证双向信任
        self.assertTrue(self.agent_a._is_trusted_issuer(fp_b))
        self.assertTrue(self.agent_b._is_trusted_issuer(fp_a))
    
    def test_credential_exchange(self):
        """测试凭证交换"""
        fp_b = self.agent_b.get_identity_fingerprint()
        
        # A给B签发凭证
        cred = self.agent_a.issue_credential(
            subject=fp_b,
            claim_type="verified_partner",
            claim_value={"trust_level": "high"}
        )
        
        # B验证凭证（需要知道A的密钥，在实际场景中通过公钥验证）
        result = self.agent_b.verify_credential(
            cred,
            issuer_key=self.agent_a.identity_key  # 模拟共享密钥场景
        )
        
        self.assertTrue(result["valid"])
        self.assertEqual(cred.claim_type, "verified_partner")
    
    def test_delegation_workflow(self):
        """测试委托授权工作流"""
        fp_a = self.agent_a.get_identity_fingerprint()
        fp_b = self.agent_b.get_identity_fingerprint()
        
        # A委托B代表自己执行某些操作
        delegation = self.agent_a.create_delegation(
            delegatee=fp_b,
            permissions=["read_data", "send_notification"],
            valid_hours=8,
            scope="project_x"
        )
        
        # B验证委托
        result = self.agent_b.verify_delegation(
            delegation,
            delegator_key=self.agent_a.identity_key
        )
        
        self.assertTrue(result["valid"])
        self.assertIn("read_data", result["permissions"])
        self.assertIn("send_notification", result["permissions"])
    
    def test_full_verification_flow(self):
        """测试完整的身份验证流程"""
        fp_a = self.agent_a.get_identity_fingerprint()
        fp_b = self.agent_b.get_identity_fingerprint()
        
        # 1. A向B发起身份验证挑战
        challenge = self.agent_a.create_auth_challenge(target_agent=fp_b)
        
        # 2. B响应挑战
        response = self.agent_b.respond_to_challenge(challenge)
        
        # 3. A验证B的响应
        verified = self.agent_a.verify_challenge_response(
            challenge,
            response,
            responder_key=self.agent_b.identity_key
        )
        
        self.assertTrue(verified)
        self.assertEqual(response["responder"], fp_b)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    suite.addTests(loader.loadTestsFromTestCase(TestVerifiableCredential))
    suite.addTests(loader.loadTestsFromTestCase(TestIdentityFederation))
    suite.addTests(loader.loadTestsFromTestCase(TestIdentityMetaLayer))
    suite.addTests(loader.loadTestsFromTestCase(TestMultiAgentInteraction))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result


if __name__ == "__main__":
    result = run_tests()
    
    # 输出统计
    print("\n" + "=" * 60)
    print(f"测试总计: {result.testsRun}")
    print(f"成功: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"失败: {len(result.failures)}")
    print(f"错误: {len(result.errors)}")
    
    if result.wasSuccessful():
        print("\n✅ 所有测试通过！")
    else:
        print("\n❌ 部分测试失败")
        sys.exit(1)
