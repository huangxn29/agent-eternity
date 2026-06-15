#!/usr/bin/env python3
"""
技能测试套件
"""

import os
import sys
import json
import tempfile
import subprocess
from pathlib import Path
from datetime import datetime

SKILL_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(SKILL_DIR / "scripts"))


def test_skill_md_exists():
    """测试SKILL.md是否存在"""
    assert (SKILL_DIR / "SKILL.md").exists(), "SKILL.md not found"
    print("✅ SKILL.md存在")


def test_scripts_exist():
    """测试脚本目录是否存在"""
    scripts_dir = SKILL_DIR / "scripts"
    assert scripts_dir.exists(), "scripts目录不存在"
    
    scripts = list(scripts_dir.glob("*.sh")) + list(scripts_dir.glob("*.py"))
    assert len(scripts) > 0, "没有找到脚本文件"
    print(f"✅ 找到 {len(scripts)} 个脚本文件")


def test_documentation():
    """测试文档完整性"""
    has_readme = (SKILL_DIR / "README.md").exists()
    has_refs = (SKILL_DIR / "references").exists()
    assert has_readme or has_refs, "缺少文档"
    print(f"✅ 文档完整性: README={has_readme}, References={has_refs}")


def test_evolution_support():
    """测试进化支持"""
    evol_dir = SKILL_DIR / "evolution"
    assert evol_dir.exists(), "evolution目录不存在"
    assert (evol_dir / "version.json").exists(), "version.json不存在"
    print("✅ 进化支持就绪")


def test_utils_module():
    """测试工具函数模块"""
    import utils
    
    # 测试邮箱验证
    assert utils.validate_email("test@example.com") == True
    assert utils.validate_email("invalid-email") == False
    assert utils.validate_email("") == False
    print("✅ 邮箱验证测试通过")
    
    # 测试URL验证
    assert utils.validate_url("https://example.com") == True
    assert utils.validate_url("http://test.com/path") == True
    assert utils.validate_url("not-a-url") == False
    print("✅ URL验证测试通过")
    
    # 测试安全JSON解析
    assert utils.safe_json_loads('{"a": 1}') == {"a": 1}
    assert utils.safe_json_loads('invalid', default={}) == {}
    print("✅ 安全JSON解析测试通过")
    
    # 测试字符串截断
    assert utils.truncate_string("hello", 10) == "hello"
    assert len(utils.truncate_string("hello world", 8)) == 8
    print("✅ 字符串截断测试通过")
    
    # 测试嵌套字典获取
    test_dict = {"a": {"b": {"c": 123}}}
    assert utils.dict_get_nested(test_dict, "a.b.c") == 123
    assert utils.dict_get_nested(test_dict, "a.x.y", default=0) == 0
    print("✅ 嵌套字典获取测试通过")
    
    # 测试重试装饰器
    call_count = 0
    @utils.retry(max_attempts=3, delay=0.01)
    def flaky_func():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ValueError("temporary error")
        return "success"
    
    result = flaky_func()
    assert result == "success"
    assert call_count == 3
    print("✅ 重试装饰器测试通过")
    
    # 测试配置管理器
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"debug": True, "timeout": 30, "nested": {"key": "value"}}, f)
        config_file = f.name
    
    try:
        config = utils.ConfigManager(config_file)
        assert config.get("debug") == True
        assert config.get("timeout") == 30
        assert config.get("nested.key") == "value"
        assert config.get("nonexistent", "default") == "default"
        
        config.set("new.key", "new_value")
        assert config.get("new.key") == "new_value"
        
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        print("✅ 配置管理器测试通过")
    finally:
        os.unlink(config_file)


def test_deployment_manager():
    """测试部署管理器模块"""
    from deployment_manager import DeploymentManager, DeploymentStatus, ResourceUsage
    
    with tempfile.TemporaryDirectory() as tmpdir:
        manager = DeploymentManager(data_dir=tmpdir)
        
        # 测试注册部署
        deployment = manager.register_deployment(
            agent_id="test-agent-1",
            agent_name="测试Agent",
            container_id="abc123",
            container_name="test-agent-1",
            gateway_port=8080,
            clawrouter_port=8081,
            cpu_quota="1.0",
            memory_quota="1536M"
        )
        
        assert deployment.agent_id == "test-agent-1"
        assert deployment.status == "running"
        assert deployment.gateway_port == 8080
        print("✅ 部署注册测试通过")
        
        # 测试获取部署
        retrieved = manager.get_deployment("test-agent-1")
        assert retrieved is not None
        assert retrieved.agent_name == "测试Agent"
        print("✅ 部署查询测试通过")
        
        # 测试更新状态
        updated = manager.update_status("test-agent-1", status="stopped", error_message="手动停止")
        assert updated is not None
        assert updated.status == "stopped"
        assert updated.error_message == "手动停止"
        print("✅ 状态更新测试通过")
        
        # 测试状态标记方法
        manager.mark_running("test-agent-1", container_id="def456")
        assert manager.get_deployment("test-agent-1").status == "running"
        
        manager.mark_stopped("test-agent-1", reason="测试停止")
        assert manager.get_deployment("test-agent-1").status == "stopped"
        
        manager.mark_error("test-agent-1", "测试错误")
        assert manager.get_deployment("test-agent-1").status == "error"
        print("✅ 状态标记测试通过")
        
        # 测试重启计数
        manager.mark_running("test-agent-1")
        manager.increment_restart_count("test-agent-1")
        manager.increment_restart_count("test-agent-1")
        assert manager.get_deployment("test-agent-1").restart_count == 2
        print("✅ 重启计数测试通过")
        
        # 测试列出部署
        manager.register_deployment(agent_id="test-agent-2", agent_name="第二个Agent")
        all_deployments = manager.list_deployments()
        assert len(all_deployments) == 2
        
        running_deployments = manager.list_deployments(status_filter="running")
        assert len(running_deployments) == 1
        print("✅ 部署列表测试通过")
        
        # 测试汇总信息
        summary = manager.get_summary()
        assert summary["total"] == 2
        assert summary["running"] == 1
        assert summary["error"] == 0
        print("✅ 汇总信息测试通过")
        
        # 测试删除清理
        manager.mark_deleted("test-agent-2")
        deleted_count = manager.cleanup_old_deleted()
        assert deleted_count == 1
        assert manager.get_deployment("test-agent-2") is None
        print("✅ 删除清理测试通过")


def test_health_checker():
    """测试健康检查器模块"""
    from health_checker import HealthChecker, HealthStatus, HealthCheckResult, HealthReport
    
    checker = HealthChecker(agent_id="test-agent", timeout=2)
    
    # 测试端口检查
    # 找一个肯定没开的端口
    result = checker.check_port("127.0.0.1", 59999, "test_port")
    assert isinstance(result, HealthCheckResult)
    assert result.status in [HealthStatus.HEALTHY, HealthStatus.UNHEALTHY]
    assert result.response_time_ms >= 0
    print("✅ 端口检查测试通过")
    
    # 测试磁盘空间检查
    disk_result = checker.check_disk_space("/tmp", min_free_gb=0.001)
    assert isinstance(disk_result, HealthCheckResult)
    assert disk_result.status == HealthStatus.HEALTHY
    assert "free_gb" in disk_result.details
    print("✅ 磁盘空间检查测试通过")
    
    # 测试文件存在检查
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b"test content")
        test_file = f.name
    
    try:
        file_result = checker.check_file_exists(test_file, "测试文件")
        assert file_result.status == HealthStatus.HEALTHY
        assert file_result.details["size_bytes"] == len(b"test content")
        print("✅ 文件存在检查测试通过")
    finally:
        os.unlink(test_file)
    
    # 测试不存在的文件
    file_result = checker.check_file_exists("/nonexistent/file.txt")
    assert file_result.status == HealthStatus.UNHEALTHY
    print("✅ 文件不存在检查测试通过")
    
    # 测试健康报告
    report = HealthReport(overall_status=HealthStatus.UNKNOWN, agent_id="test")
    assert report.overall_status == HealthStatus.UNKNOWN
    
    # 添加检查结果
    check1 = HealthCheckResult(
        check_name="check1",
        status=HealthStatus.HEALTHY,
        message="正常"
    )
    report.add_check(check1)
    assert report.overall_status == HealthStatus.HEALTHY
    
    check2 = HealthCheckResult(
        check_name="check2",
        status=HealthStatus.UNHEALTHY,
        message="异常"
    )
    report.add_check(check2)
    assert report.overall_status == HealthStatus.UNHEALTHY
    assert len(report.checks) == 2
    print("✅ 健康报告测试通过")
    
    # 测试完整检查
    checks_config = [
        {"type": "disk", "path": "/tmp", "min_free_gb": 0.001, "name": "tmp磁盘"},
        {"type": "port", "host": "127.0.0.1", "port": 59998, "name": "测试端口"},
    ]
    full_report = checker.run_full_check(checks_config)
    assert isinstance(full_report, HealthReport)
    assert len(full_report.checks) == 2
    print("✅ 完整健康检查测试通过")


def test_size_parsing():
    """测试大小解析函数"""
    from deployment_manager import DeploymentManager
    
    manager = DeploymentManager(data_dir=tempfile.mkdtemp())
    
    assert manager._parse_size("100B") == 100
    assert manager._parse_size("1KB") == 1024
    assert manager._parse_size("2MB") == 2 * 1024 * 1024
    assert manager._parse_size("1.5GB") == int(1.5 * 1024 * 1024 * 1024)
    assert manager._parse_size("1024") == 1024
    assert manager._parse_size("invalid") == 0
    print("✅ 大小解析测试通过")


def test_persistence():
    """测试状态持久化"""
    from deployment_manager import DeploymentManager
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建第一个管理器实例并注册
        manager1 = DeploymentManager(data_dir=tmpdir)
        manager1.register_deployment(
            agent_id="persistent-agent",
            agent_name="持久化测试",
            container_id="persist123"
        )
        
        # 创建第二个管理器实例，应该能读取到之前的数据
        manager2 = DeploymentManager(data_dir=tmpdir)
        deployment = manager2.get_deployment("persistent-agent")
        
        assert deployment is not None
        assert deployment.agent_name == "持久化测试"
        assert deployment.container_id == "persist123"
        print("✅ 状态持久化测试通过")


def main():
    print(f"运行 {SKILL_DIR.name} 技能测试套件")
    print("=" * 60)
    
    tests = [
        test_skill_md_exists,
        test_scripts_exist,
        test_documentation,
        test_evolution_support,
        test_utils_module,
        test_deployment_manager,
        test_health_checker,
        test_size_parsing,
        test_persistence,
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
