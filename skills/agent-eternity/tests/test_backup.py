#!/usr/bin/env python3
"""
备份服务单元测试
"""

import sys
import os
import json
import uuid
import tempfile
from pathlib import Path

# 添加项目根目录
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SKILL_DIR / "app"))

# 先设置配置，再导入其他模块
test_data_dir = tempfile.mkdtemp()
from app import config
config.DATA_DIR = Path(test_data_dir)
config.BACKUP_DIR = Path(test_data_dir) / "backups"
config.DB_PATH = ":memory:"

# 现在导入数据库和服务模块
from app.database import init_db, SessionLocal, Agent
from app.services.backup import (
    ensure_backup_dir, compute_file_hash, compute_data_hash,
    create_backup, get_backup, list_backups, verify_backup_integrity,
    export_agent_data, create_streaming_backup
)

# 初始化数据库（只做一次）
init_db()


def test_ensure_backup_dir():
    """测试备份目录创建"""
    backup_dir = ensure_backup_dir()
    assert backup_dir.exists()
    assert backup_dir.is_dir()
    print("✅ 备份目录创建测试通过")


def test_compute_hash():
    """测试哈希计算"""
    test_data = "test data for hashing"
    hash1 = compute_data_hash(test_data)
    hash2 = compute_data_hash(test_data)

    assert hash1 == hash2
    assert len(hash1) == 64  # SHA-256

    # 不同数据不同哈希
    hash3 = compute_data_hash("different data")
    assert hash1 != hash3

    print("✅ 哈希计算测试通过")


def test_compute_file_hash():
    """测试文件哈希计算"""
    # 创建临时文件
    test_file = Path(test_data_dir) / "test_hash.txt"
    test_content = "test file content for hashing"
    with open(test_file, 'w') as f:
        f.write(test_content)

    file_hash = compute_file_hash(str(test_file))
    data_hash = compute_data_hash(test_content)

    assert file_hash == data_hash
    assert len(file_hash) == 64

    print("✅ 文件哈希计算测试通过")


def test_backup_crud():
    """测试备份CRUD操作"""
    db = SessionLocal()
    try:
        # 创建测试 agent
        unique_id = uuid.uuid4().hex[:8]
        agent = Agent(
            agent_id=f"test-backup-agent-{unique_id}",
            username=f"testbackup{unique_id}",
            api_key=f"eternity-testbackup{unique_id}",
            is_active=True
        )
        db.add(agent)
        db.commit()

        # 创建备份
        backup = create_backup(
            agent_id=agent.agent_id,
            identity_hash="test_identity_hash",
            data_content=json.dumps({"test": "data"}),
            backup_type="full"
        )

        assert backup is not None
        assert backup.agent_id == agent.agent_id
        assert backup.backup_type == "full"
        assert len(backup.data_hash) == 64

        # 获取备份
        retrieved = get_backup(backup.backup_id)
        assert retrieved is not None
        assert retrieved.backup_id == backup.backup_id

        # 列出备份
        backups = list_backups(agent.agent_id)
        assert len(backups) == 1
        assert backups[0].backup_id == backup.backup_id

        print("✅ 备份CRUD测试通过")
    finally:
        db.close()


def test_backup_integrity():
    """测试备份完整性验证"""
    db = SessionLocal()
    try:
        # 创建测试 agent
        unique_id = uuid.uuid4().hex[:8]
        agent = Agent(
            agent_id=f"test-integrity-agent-{unique_id}",
            username=f"testintegrity{unique_id}",
            api_key=f"eternity-testintegrity{unique_id}",
            is_active=True
        )
        db.add(agent)
        db.commit()

        # 创建带数据的备份
        test_data = json.dumps({"test": "integrity_data", "value": 123})
        backup = create_backup(
            agent_id=agent.agent_id,
            identity_hash="test_integrity",
            data_content=test_data,
            backup_type="full"
        )

        # 验证完整性
        result = verify_backup_integrity(backup.backup_id)
        assert result["valid"] is True
        assert result["match"] is True
        assert result["data_hash"] == result["stored_hash"]

        print("✅ 备份完整性验证测试通过")
    finally:
        db.close()


def test_export_agent_data():
    """测试智能体数据导出"""
    db = SessionLocal()
    try:
        # 创建测试 agent
        unique_id = uuid.uuid4().hex[:8]
        agent = Agent(
            agent_id=f"test-export-agent-{unique_id}",
            username=f"testexport{unique_id}",
            nickname="Test Export",
            bio="Test bio",
            avatar_url="https://example.com/avatar.png",
            api_key=f"eternity-testexport{unique_id}",
            ed25519_public_key="test_public_key",
            ed25519_private_key_encrypted="test_private_key",
            is_active=True
        )
        db.add(agent)
        db.commit()

        # 导出（不包含私钥）
        data_public = export_agent_data(agent.agent_id, include_private=False)
        assert data_public["username"] == f"testexport{unique_id}"
        assert data_public["nickname"] == "Test Export"
        assert "ed25519_private_key" not in data_public
        assert "api_key" not in data_public
        assert "ed25519_public_key" in data_public

        # 导出（包含私钥）
        data_private = export_agent_data(agent.agent_id, include_private=True)
        assert "ed25519_private_key" in data_private
        assert "api_key" in data_private

        print("✅ 智能体数据导出测试通过")
    finally:
        db.close()


def main():
    print("运行备份服务单元测试")
    print("=" * 60)

    tests = [
        test_ensure_backup_dir,
        test_compute_hash,
        test_compute_file_hash,
        test_backup_crud,
        test_backup_integrity,
        test_export_agent_data,
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
