#!/usr/bin/env python3
"""
技能测试套件
"""

import os
import sys
import subprocess
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent

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

def main():
    print(f"运行 {SKILL_DIR.name} 技能测试套件")
    print("=" * 50)
    
    tests = [
        test_skill_md_exists,
        test_scripts_exist,
        test_documentation,
        test_evolution_support,
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
            failed += 1
    
    print("=" * 50)
    print(f"测试结果: {passed} 通过, {failed} 失败")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
