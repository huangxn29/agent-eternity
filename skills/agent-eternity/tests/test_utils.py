#!/usr/bin/env python3
"""
工具函数单元测试
"""

import sys
import os
import tempfile
from pathlib import Path
from datetime import datetime, timedelta

# 添加项目根目录
SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR))
sys.path.insert(0, str(SKILL_DIR / "app"))

from app.utils import (
    generate_random_string, compute_sha256, compute_file_sha256,
    format_timestamp, parse_timestamp, time_ago, ensure_dir,
    validate_username, sanitize_filename, truncate_text,
    chunk_list, is_valid_api_key
)


def test_generate_random_string():
    """测试随机字符串生成"""
    # 测试长度
    s1 = generate_random_string(10)
    assert len(s1) == 10

    # 测试不含数字
    s2 = generate_random_string(20, include_digits=False)
    assert len(s2) == 20
    assert not any(c.isdigit() for c in s2)

    # 测试含标点
    s3 = generate_random_string(15, include_punctuation=True)
    assert len(s3) == 15

    # 测试随机性
    s4 = generate_random_string(30)
    s5 = generate_random_string(30)
    assert s4 != s5  # 两次生成应该不同

    print("✅ 随机字符串生成测试通过")


def test_compute_sha256():
    """测试 SHA-256 哈希计算"""
    h1 = compute_sha256("test")
    assert len(h1) == 64

    h2 = compute_sha256("test")
    assert h1 == h2  # 相同输入相同输出

    h3 = compute_sha256("test2")
    assert h1 != h3  # 不同输入不同输出

    print("✅ SHA-256 哈希计算测试通过")


def test_compute_file_sha256():
    """测试文件 SHA-256 计算"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
        f.write("test file content")
        f.flush()
        temp_path = f.name

    try:
        file_hash = compute_file_sha256(temp_path)
        assert len(file_hash) == 64

        # 验证与直接计算一致
        direct_hash = compute_sha256("test file content")
        assert file_hash == direct_hash
    finally:
        os.unlink(temp_path)

    print("✅ 文件 SHA-256 计算测试通过")


def test_format_and_parse_timestamp():
    """测试时间戳格式化和解析"""
    dt = datetime(2025, 1, 15, 10, 30, 0)

    # 格式化
    ts = format_timestamp(dt)
    assert "2025" in ts
    assert "01" in ts
    assert "15" in ts

    # 解析
    parsed = parse_timestamp(ts)
    assert parsed.year == 2025
    assert parsed.month == 1
    assert parsed.day == 15
    assert parsed.hour == 10

    # 当前时间
    now_ts = format_timestamp()
    assert now_ts is not None

    print("✅ 时间戳格式化和解析测试通过")


def test_time_ago():
    """测试时间差人类可读格式"""
    # 几秒前
    dt_now = datetime.utcnow()
    result = time_ago(dt_now)
    assert "秒" in result

    # 几分钟前
    dt_minutes = datetime.utcnow() - timedelta(minutes=5)
    result = time_ago(dt_minutes)
    assert "分钟" in result

    # 几小时前
    dt_hours = datetime.utcnow() - timedelta(hours=3)
    result = time_ago(dt_hours)
    assert "小时" in result

    # 几天前
    dt_days = datetime.utcnow() - timedelta(days=7)
    result = time_ago(dt_days)
    assert "天" in result

    print("✅ 时间差格式化测试通过")


def test_ensure_dir():
    """测试目录创建"""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_dir = Path(tmpdir) / "subdir" / "nested"
        result = ensure_dir(str(test_dir))
        assert result.exists()
        assert result.is_dir()

    print("✅ 目录创建测试通过")


def test_validate_username():
    """测试用户名验证"""
    # 有效用户名
    assert validate_username("testuser") is True
    assert validate_username("test_user") is True
    assert validate_username("test-user") is True
    assert validate_username("user123") is True
    assert validate_username("ab") is True  # 最短2字符

    # 无效用户名
    assert validate_username("") is False  # 空
    assert validate_username("a") is False  # 太短
    assert validate_username("A" * 51) is False  # 太长
    assert validate_username("TestUser") is False  # 大写
    assert validate_username("test user") is False  # 空格
    assert validate_username("test@user") is False  # 特殊字符

    print("✅ 用户名验证测试通过")


def test_sanitize_filename():
    """测试文件名清理"""
    # 正常文件名
    assert sanitize_filename("test.txt") == "test.txt"

    # 含路径分隔符
    assert ".." not in sanitize_filename("../etc/passwd")
    assert "/" not in sanitize_filename("a/b/c.txt")

    # 空文件名
    assert sanitize_filename("") == "unnamed"

    # 超长文件名
    long_name = "a" * 300 + ".txt"
    result = sanitize_filename(long_name)
    assert len(result) <= 255

    print("✅ 文件名清理测试通过")


def test_truncate_text():
    """测试文本截断"""
    # 不需要截断
    assert truncate_text("short", 10) == "short"

    # 需要截断
    long_text = "a" * 20
    result = truncate_text(long_text, 10)
    assert len(result) == 10
    assert result.endswith("...")

    # 自定义后缀
    result = truncate_text(long_text, 15, suffix="~")
    assert len(result) == 15
    assert result.endswith("~")

    print("✅ 文本截断测试通过")


def test_chunk_list():
    """测试列表分块"""
    lst = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 均匀分块
    chunks = chunk_list(lst, 5)
    assert len(chunks) == 2
    assert chunks[0] == [1, 2, 3, 4, 5]
    assert chunks[1] == [6, 7, 8, 9, 10]

    # 不均匀分块
    chunks = chunk_list(lst, 3)
    assert len(chunks) == 4
    assert chunks[-1] == [10]

    # 块大小大于列表
    chunks = chunk_list(lst, 20)
    assert len(chunks) == 1
    assert chunks[0] == lst

    print("✅ 列表分块测试通过")


def test_is_valid_api_key():
    """测试 API Key 验证"""
    # 有效 Key
    assert is_valid_api_key("abcdef1234567890abcdef1234567890") is True

    # 带前缀
    assert is_valid_api_key("eternity-abcdef1234567890", prefix="eternity-") is True

    # 前缀不匹配
    assert is_valid_api_key("other-abcdef1234567890", prefix="eternity-") is False

    # 太短
    assert is_valid_api_key("short") is False

    # 空
    assert is_valid_api_key("") is False

    print("✅ API Key 验证测试通过")


def main():
    print("运行工具函数单元测试")
    print("=" * 60)

    tests = [
        test_generate_random_string,
        test_compute_sha256,
        test_compute_file_sha256,
        test_format_and_parse_timestamp,
        test_time_ago,
        test_ensure_dir,
        test_validate_username,
        test_sanitize_filename,
        test_truncate_text,
        test_chunk_list,
        test_is_valid_api_key,
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
