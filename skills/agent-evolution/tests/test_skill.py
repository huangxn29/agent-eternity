#!/usr/bin/env python3
"""
agent-evolution 技能测试套件
"""

import os
import sys
import unittest
from pathlib import Path

SKILL_DIR = Path(__file__).parent.parent


class TestSkillBasics(unittest.TestCase):
    """基础测试"""
    
    def test_skill_md_exists(self):
        """测试SKILL.md是否存在"""
        self.assertTrue((SKILL_DIR / "SKILL.md").exists())
    
    def test_scripts_exist(self):
        """测试脚本目录是否存在"""
        scripts_dir = SKILL_DIR / "scripts"
        self.assertTrue(scripts_dir.exists())
        py_files = list(scripts_dir.glob("*.py"))
        sh_files = list(scripts_dir.glob("*.sh"))
        self.assertTrue(len(py_files) + len(sh_files) > 0)
    
    def test_documentation(self):
        """测试文档完整性"""
        has_readme = (SKILL_DIR / "README.md").exists()
        has_refs = (SKILL_DIR / "references").exists()
        self.assertTrue(has_readme or has_refs)
    
    def test_evolution_support(self):
        """测试进化支持"""
        evol_dir = SKILL_DIR / "evolution"
        self.assertTrue(evol_dir.exists())
        self.assertTrue((evol_dir / "version.json").exists())


def run_tests():
    """运行所有测试"""
    print(f"运行 agent-evolution 技能测试套件")
    print("=" * 50)
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromTestCase(TestSkillBasics)
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    print("=" * 50)
    print(f"测试结果: {result.testsRun} 运行")
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
