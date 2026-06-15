#!/usr/bin/env python3
"""
签名链服务单元测试
"""

import sys
import os
import uuid
from pathlib import Path
from datetime import datetime

# 添加项目根目录
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SKILL_DIR / "app"))

# 先设置配置，再导入数据库模块
from app import config
config.DB_PATH = ":memory:"

# 现在导入数据库和服务模块
from app.database import init_db, SessionLocal, Agent, SignatureChain
from app.services.signature import (
    generate_keypair, sign_data, verify_signature,
    compute_hash, build_chain_data, add_to_chain,
    verify_chain, get_chain
)

# 初始化数据库（只做一次）
init_db()


def test_keypair_generation():
    """测试密钥对生成"""
    private_key, public_key = generate_keypair()

    assert private_key is not None
    assert public_key is not None
    assert "PRIVATE KEY" in private_key
    assert "PUBLIC KEY" in public_key
    print("✅ 密钥对生成测试通过")


def test_sign_and_verify():
    """测试签名和验证"""
    private_key, public_key = generate_keypair()
    data = "test data for signing"

    signature = sign_data(private_key, data)
    assert signature is not None
    assert len(signature) > 0

    # 验证正确的签名
    is_valid = verify_signature(public_key, data, signature)
    assert is_valid is True

    # 验证错误的数据
    is_valid = verify_signature(public_key, "wrong data", signature)
    assert is_valid is False

    # 验证错误的公钥
    wrong_private, wrong_public = generate_keypair()
    is_valid = verify_signature(wrong_public, data, signature)
    assert is_valid is False

    print("✅ 签名验证测试通过")


def test_compute_hash():
    """测试哈希计算"""
    data = "test data"
    hash1 = compute_hash(data)
    hash2 = compute_hash(data)

    assert hash1 == hash2  # 相同数据得到相同哈希
    assert len(hash1) == 64  # SHA-256 是 64 个十六进制字符

    hash3 = compute_hash("different data")
    assert hash1 != hash3  # 不同数据得到不同哈希

    print("✅ 哈希计算测试通过")


def test_build_chain_data():
    """测试签名链数据构建"""
    agent_id = "test-agent-123"
    identity_hash = "abc123"
    prev_hash = "0" * 64
    event_type = "root"
    signed_at = datetime.utcnow()

    chain_data = build_chain_data(agent_id, identity_hash, prev_hash, event_type, signed_at)

    assert agent_id in chain_data
    assert identity_hash in chain_data
    assert prev_hash in chain_data
    assert event_type in chain_data

    print("✅ 签名链数据构建测试通过")


def test_signature_chain_flow():
    """测试完整的签名链流程"""
    db = SessionLocal()
    try:
        # 创建测试 agent（使用唯一用户名）
        unique_id = uuid.uuid4().hex[:8]
        private_key, public_key = generate_keypair()
        agent = Agent(
            agent_id=f"test-agent-chain-{unique_id}",
            username=f"testchain{unique_id}",
            api_key=f"eternity-test{unique_id}",
            ed25519_public_key=public_key,
            ed25519_private_key_encrypted=private_key,
            is_active=True
        )
        db.add(agent)
        db.commit()

        # 添加第一个签名（根签名）
        chain1 = add_to_chain(
            agent_id=agent.agent_id,
            private_key_pem=private_key,
            identity_hash="identity_v1",
            event_type="root"
        )
        assert chain1.chain_id >= 1
        assert chain1.prev_hash == "0" * 64
        assert chain1.event_type == "root"

        # 添加第二个签名
        chain2 = add_to_chain(
            agent_id=agent.agent_id,
            private_key_pem=private_key,
            identity_hash="identity_v2",
            event_type="update"
        )
        assert chain2.chain_id > chain1.chain_id
        assert chain2.prev_hash != "0" * 64
        assert chain2.event_type == "update"

        # 验证链的连续性
        is_continuous, chain_length, root_valid = verify_chain(
            agent_id=agent.agent_id,
            public_key_pem=public_key
        )
        assert is_continuous is True
        assert chain_length == 2
        assert root_valid is True

        # 获取链
        chains = get_chain(agent.agent_id)
        assert len(chains) == 2
        assert chains[0].chain_id < chains[1].chain_id

        print("✅ 签名链完整流程测试通过")
    finally:
        db.close()


def main():
    print("运行签名链服务单元测试")
    print("=" * 60)

    tests = [
        test_keypair_generation,
        test_sign_and_verify,
        test_compute_hash,
        test_build_chain_data,
        test_signature_chain_flow,
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {test.__name__}: 异常 - {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 60)
    print(f"测试结果: {passed} 通过, {failed} 失败")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
