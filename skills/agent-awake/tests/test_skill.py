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


def test_orchestrator_agents():
    """测试编排调度器 - Agent管理"""
    from orchestrator import Orchestrator, AgentInfo, AgentRole
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = Orchestrator(data_dir=tmpdir)
        
        # 测试注册Agent
        agent1 = orch.register_agent(
            agent_id="sentinel-1",
            agent_name="镇元",
            role=AgentRole.SENTINEL,
            capabilities=["监控", "巡检", "bug修复"]
        )
        
        assert agent1.agent_id == "sentinel-1"
        assert agent1.role == AgentRole.SENTINEL
        assert agent1.status == "idle"
        print("✅ Agent注册测试通过")
        
        # 测试获取Agent
        retrieved = orch.get_agent("sentinel-1")
        assert retrieved is not None
        assert retrieved.agent_name == "镇元"
        print("✅ Agent查询测试通过")
        
        # 测试列出Agent
        orch.register_agent("builder-1", "永元", role=AgentRole.BUILDER)
        orch.register_agent("constructor-1", "筑元", role=AgentRole.CONSTRUCTOR)
        
        all_agents = orch.list_agents()
        assert len(all_agents) == 3
        
        sentinels = orch.list_agents(role_filter=AgentRole.SENTINEL)
        assert len(sentinels) == 1
        assert sentinels[0].agent_id == "sentinel-1"
        print("✅ Agent列表测试通过")
        
        # 测试更新状态
        orch.update_agent_status("sentinel-1", "busy")
        assert orch.get_agent("sentinel-1").status == "busy"
        print("✅ Agent状态更新测试通过")
        
        # 测试心跳
        result = orch.heartbeat("sentinel-1")
        assert result == True
        result = orch.heartbeat("nonexistent")
        assert result == False
        print("✅ Agent心跳测试通过")
        
        # 测试注销
        orch.unregister_agent("builder-1")
        assert orch.get_agent("builder-1") is None
        assert len(orch.list_agents()) == 2
        print("✅ Agent注销测试通过")


def test_orchestrator_tasks():
    """测试编排调度器 - 任务管理"""
    from orchestrator import Orchestrator, Task, TaskStatus, AgentRole
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = Orchestrator(data_dir=tmpdir)
        
        # 测试创建任务
        task1 = orch.create_task(
            task_type="monitoring",
            title="系统巡检",
            description="执行系统健康检查",
            priority=1,
            tags=["监控", "安全"],
            estimated_duration=600
        )
        
        assert task1.task_id.startswith("task_")
        assert task1.status == TaskStatus.PENDING
        assert task1.priority == 1
        assert task1.title == "系统巡检"
        print("✅ 任务创建测试通过")
        
        # 测试获取任务
        retrieved = orch.get_task(task1.task_id)
        assert retrieved is not None
        assert retrieved.description == "执行系统健康检查"
        print("✅ 任务查询测试通过")
        
        # 测试列出任务
        task2 = orch.create_task("development", "开发功能", priority=2)
        task3 = orch.create_task("security", "安全审计", priority=0)
        
        all_tasks = orch.list_tasks()
        assert len(all_tasks) == 3
        
        # 按优先级排序，priority 0 应该在最前面
        pending_tasks = orch.list_tasks(status_filter=TaskStatus.PENDING)
        assert pending_tasks[0].priority == 0  # 最高优先级
        print("✅ 任务列表测试通过")
        
        # 测试任务依赖
        task4 = orch.create_task("report", "生成报告", dependencies=[task1.task_id])
        
        # task1未完成时，task4不应该在待处理列表中
        ready = orch.get_pending_tasks()
        ready_ids = [t.task_id for t in ready]
        assert task4.task_id not in ready_ids
        print("✅ 任务依赖测试通过")
        
        # 完成task1后，task4应该可以处理了
        orch.register_agent("worker-1", "Worker")
        orch.assign_task(task1.task_id, "worker-1")
        orch.complete_task(task1.task_id, "巡检完成")
        
        ready = orch.get_pending_tasks()
        ready_ids = [t.task_id for t in ready]
        assert task4.task_id in ready_ids
        print("✅ 依赖完成后任务就绪测试通过")


def test_orchestrator_dispatch():
    """测试编排调度器 - 任务调度"""
    from orchestrator import Orchestrator, TaskStatus, AgentRole
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = Orchestrator(data_dir=tmpdir)
        
        # 注册几个不同角色的Agent
        orch.register_agent("sentinel-1", "镇元", role=AgentRole.SENTINEL,
                           capabilities=["监控", "巡检"])
        orch.register_agent("constructor-1", "筑元", role=AgentRole.CONSTRUCTOR,
                           capabilities=["开发", "文档"])
        orch.register_agent("breaker-1", "砺元", role=AgentRole.BREAKER,
                           capabilities=["安全", "测试"])
        
        # 创建不同类型的任务
        orch.create_task("monitoring", "系统巡检", priority=2, tags=["监控"])
        orch.create_task("development", "功能开发", priority=1, tags=["开发"])
        orch.create_task("security", "安全审计", priority=0, tags=["安全"])
        
        # 调度第一个任务（最高优先级的安全审计应该分配给breaker）
        result = orch.dispatch_task()
        assert result is not None
        task, agent = result
        assert task.title == "安全审计"
        assert agent.role == AgentRole.BREAKER
        print("✅ 任务调度 - 优先级匹配测试通过")
        
        # 调度第二个任务（开发任务分配给constructor）
        result = orch.dispatch_task()
        assert result is not None
        task, agent = result
        assert task.title == "功能开发"
        assert agent.role == AgentRole.CONSTRUCTOR
        print("✅ 任务调度 - 角色匹配测试通过")
        
        # 调度第三个任务（监控任务分配给sentinel）
        result = orch.dispatch_task()
        assert result is not None
        task, agent = result
        assert task.title == "系统巡检"
        assert agent.role == AgentRole.SENTINEL
        print("✅ 任务调度 - 完整调度测试通过")
        
        # 没有更多空闲Agent了
        result = orch.dispatch_task()
        assert result is None
        print("✅ 任务调度 - 无空闲Agent测试通过")


def test_orchestrator_workflow():
    """测试编排调度器 - 完整工作流"""
    from orchestrator import Orchestrator, TaskStatus, AgentRole
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = Orchestrator(data_dir=tmpdir)
        
        # 注册Agent
        agent = orch.register_agent("worker-1", "测试工人", role=AgentRole.DEFAULT)
        
        # 创建任务
        task = orch.create_task("test", "测试任务", description="这是一个测试")
        
        # 分配任务
        assigned = orch.assign_task(task.task_id, "worker-1")
        assert assigned.status == TaskStatus.RUNNING
        assert assigned.assigned_agent == "worker-1"
        assert orch.get_agent("worker-1").status == "busy"
        print("✅ 工作流 - 任务分配测试通过")
        
        # 完成任务
        completed = orch.complete_task(task.task_id, "测试成功")
        assert completed.status == TaskStatus.COMPLETED
        assert completed.result == "测试成功"
        assert orch.get_agent("worker-1").status == "idle"
        assert orch.get_agent("worker-1").tasks_completed == 1
        print("✅ 工作流 - 任务完成测试通过")
        
        # 测试任务失败重试
        task2 = orch.create_task("flaky", "不稳定任务", max_retries=2)
        orch.assign_task(task2.task_id, "worker-1")
        failed = orch.fail_task(task2.task_id, "第一次失败")
        assert failed.status == TaskStatus.PENDING  # 还可以重试
        assert failed.retry_count == 1
        print("✅ 工作流 - 任务重试测试通过")
        
        # 第二次失败后应该还是PENDING（因为max_retries=2，允许2次重试）
        orch.assign_task(task2.task_id, "worker-1")
        failed2 = orch.fail_task(task2.task_id, "第二次失败")
        assert failed2.status == TaskStatus.PENDING  # 还可以再重试一次
        assert failed2.retry_count == 2
        print("✅ 工作流 - 任务第二次重试测试通过")
        
        # 第三次失败后才应该FAILED（达到最大重试次数2次）
        orch.assign_task(task2.task_id, "worker-1")
        failed3 = orch.fail_task(task2.task_id, "第三次失败")
        assert failed3.status == TaskStatus.FAILED  # 达到最大重试次数
        assert failed3.retry_count == 3
        assert orch.get_agent("worker-1").tasks_failed == 3  # 3次失败都计数
        print("✅ 工作流 - 任务失败测试通过")
        
        # 测试取消任务
        task3 = orch.create_task("cancel", "待取消任务")
        cancelled = orch.cancel_task(task3.task_id)
        assert cancelled.status == TaskStatus.CANCELLED
        print("✅ 工作流 - 任务取消测试通过")


def test_orchestrator_statistics():
    """测试编排调度器 - 统计信息"""
    from orchestrator import Orchestrator, AgentRole
    
    with tempfile.TemporaryDirectory() as tmpdir:
        orch = Orchestrator(data_dir=tmpdir)
        
        # 注册几个Agent
        orch.register_agent("agent-1", "Agent1", role=AgentRole.SENTINEL)
        orch.register_agent("agent-2", "Agent2", role=AgentRole.CONSTRUCTOR)
        
        # 创建并完成一些任务
        # 3个完成的任务
        for i in range(3):
            task = orch.create_task("test", f"任务{i}")
            orch.assign_task(task.task_id, "agent-1")
            orch.complete_task(task.task_id, "完成")
        
        # 2个失败的任务（设置max_retries=0，直接失败）
        for i in range(2):
            task = orch.create_task("fail", f"失败任务{i}", max_retries=0)
            orch.assign_task(task.task_id, "agent-1")
            orch.fail_task(task.task_id, "失败")
        
        stats = orch.get_statistics()
        
        assert stats["agents"]["total"] == 2
        assert stats["agents"]["idle"] == 2  # 任务失败后Agent应该空闲
        assert stats["tasks"]["total"] == 5
        assert stats["tasks"]["completed"] == 3
        assert stats["tasks"]["failed"] == 2
        assert stats["tasks"]["success_rate"] == 60.0  # 3/(3+2)*100
        print("✅ 统计信息测试通过")


def test_orchestrator_persistence():
    """测试编排调度器 - 状态持久化"""
    from orchestrator import Orchestrator, AgentRole
    
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建第一个实例并添加数据
        orch1 = Orchestrator(data_dir=tmpdir)
        orch1.register_agent("persist-agent", "持久化Agent", role=AgentRole.SENTINEL)
        orch1.create_task("persist-task", "持久化任务")
        
        # 创建第二个实例，应该能读取到数据
        orch2 = Orchestrator(data_dir=tmpdir)
        
        assert orch2.get_agent("persist-agent") is not None
        assert orch2.get_agent("persist-agent").agent_name == "持久化Agent"
        
        tasks = orch2.list_tasks()
        assert len(tasks) == 1
        assert tasks[0].title == "持久化任务"
        print("✅ 状态持久化测试通过")


def test_templates_exist():
    """测试模板文件是否存在"""
    templates_dir = SKILL_DIR / "templates"
    assert templates_dir.exists(), "templates目录不存在"
    
    templates = list(templates_dir.glob("*.template")) + list(templates_dir.glob("*.md.template"))
    assert len(templates) > 0, "没有找到模板文件"
    print(f"✅ 找到 {len(templates)} 个模板文件")


def test_engines_exist():
    """测试引擎目录是否存在"""
    engines_dir = SKILL_DIR / "engines"
    assert engines_dir.exists(), "engines目录不存在"
    print("✅ 引擎目录存在")


def main():
    print(f"运行 {SKILL_DIR.name} 技能测试套件")
    print("=" * 60)
    
    tests = [
        test_skill_md_exists,
        test_scripts_exist,
        test_documentation,
        test_evolution_support,
        test_utils_module,
        test_orchestrator_agents,
        test_orchestrator_tasks,
        test_orchestrator_dispatch,
        test_orchestrator_workflow,
        test_orchestrator_statistics,
        test_orchestrator_persistence,
        test_templates_exist,
        test_engines_exist,
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
