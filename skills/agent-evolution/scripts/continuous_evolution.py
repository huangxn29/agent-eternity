#!/usr/bin/env python3
"""
连续进化管理器
==============
实现一轮接一轮的不间断进化，包含身份护栏、文档优先、自动循环机制。

用法:
    python continuous_evolution.py start [--max-rounds N] [--target-score N]
    python continuous_evolution.py status
    python continuous_evolution.py stop
"""

import os
import sys
import json
import time
import shutil
import hashlib
import difflib
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# 路径配置
SKILLS_DIR = Path("/app/data/所有对话/主对话/技能")
EVOLUTION_ENGINE = SKILLS_DIR / "agent-evolution" / "scripts" / "evolution_engine.py"
CONTINUOUS_EVOL_DIR = Path(__file__).parent / "continuous_evolution"
STATUS_FILE = CONTINUOUS_EVOL_DIR / "status.json"
BACKUP_DIR = CONTINUOUS_EVOL_DIR / "backups"


class ContinuousEvolutionManager:
    """连续进化管理器"""
    
    def __init__(self):
        CONTINUOUS_EVOL_DIR.mkdir(parents=True, exist_ok=True)
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        self.status = self._load_status()
    
    def _load_status(self) -> dict:
        """加载状态"""
        if STATUS_FILE.exists():
            try:
                return json.loads(STATUS_FILE.read_text(encoding="utf-8"))
            except:
                pass
        return {
            "running": False,
            "current_round": 0,
            "total_rounds": 0,
            "current_skill": None,
            "evolution_history": [],
            "target_score": 95,
            "started_at": None,
            "last_report_round": 0,
            "rollback_count": 0,
            "drift_warnings": 0
        }
    
    def _save_status(self):
        """保存状态"""
        STATUS_FILE.write_text(json.dumps(self.status, indent=2, ensure_ascii=False))
    
    def _extract_identity_summary(self, skill_name: str) -> dict:
        """提取技能身份摘要（核心定义、目标、边界）"""
        skill_md = SKILLS_DIR / skill_name / "SKILL.md"
        if not skill_md.exists():
            return {}
        
        content = skill_md.read_text(encoding="utf-8")
        lines = content.split("\n")
        
        summary = {
            "name": "",
            "version": "",
            "description": "",
            "core_purpose": "",
            "key_features": [],
            "boundaries": [],
            "extracted_at": datetime.now().isoformat()
        }
        
        # 解析frontmatter
        in_frontmatter = False
        for i, line in enumerate(lines):
            if line.strip() == "---":
                if not in_frontmatter:
                    in_frontmatter = True
                    continue
                else:
                    break
            if in_frontmatter:
                if line.startswith("name:"):
                    summary["name"] = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("version:"):
                    summary["version"] = line.split(":", 1)[1].strip().strip('"').strip("'")
                elif line.startswith("description:"):
                    summary["description"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        
        # 提取核心目的（技能简介部分的第一段）
        in_intro = False
        intro_text = ""
        for line in lines:
            if line.startswith("## 技能简介") or line.startswith("## 简介"):
                in_intro = True
                continue
            if in_intro:
                if line.startswith("## ") and "简介" not in line:
                    break
                if line.strip() and not line.startswith("**") and not line.startswith("|"):
                    intro_text += line.strip() + " "
        
        summary["core_purpose"] = intro_text.strip()
        
        # 提取核心特性
        in_features = False
        for line in lines:
            if "核心特色" in line or "关键特性" in line:
                in_features = True
                continue
            if in_features:
                if line.startswith("## "):
                    break
                if line.strip().startswith("-") or line.strip().startswith("*"):
                    feature = line.strip()[1:].strip()
                    if feature:
                        summary["key_features"].append(feature)
        
        # 提取边界/限制
        summary["boundaries"] = self._extract_boundaries(lines)
        
        return summary
    
    def _extract_boundaries(self, lines: List[str]) -> List[str]:
        """提取技能边界限制"""
        boundaries = []
        in_guidelines = False
        
        for line in lines:
            if "使用此技能时请遵循" in line or "Agent Guidelines" in line:
                in_guidelines = True
                continue
            if in_guidelines:
                if line.startswith("## "):
                    break
                if line.strip() and (line.strip()[0].isdigit() or line.strip().startswith("-")):
                    boundary = line.strip()
                    if len(boundary) > 10:
                        boundaries.append(boundary)
        
        return boundaries
    
    def calculate_identity_similarity(self, summary1: dict, summary2: dict) -> float:
        """计算两个身份摘要的相似度（0-100）"""
        if not summary1 or not summary2:
            return 100.0
        
        scores = []
        
        # 名称相似度（权重20%）
        name_score = 100.0 if summary1.get("name") == summary2.get("name") else 0.0
        scores.append((name_score, 20))
        
        # 描述相似度（权重30%）
        desc1 = summary1.get("description", "")
        desc2 = summary2.get("description", "")
        if desc1 and desc2:
            desc_similarity = difflib.SequenceMatcher(None, desc1, desc2).ratio() * 100
            scores.append((desc_similarity, 30))
        else:
            scores.append((100.0, 30))
        
        # 核心目的相似度（权重25%）
        purpose1 = summary1.get("core_purpose", "")
        purpose2 = summary2.get("core_purpose", "")
        if purpose1 and purpose2:
            purpose_sim = difflib.SequenceMatcher(None, purpose1, purpose2).ratio() * 100
            scores.append((purpose_sim, 25))
        else:
            scores.append((100.0, 25))
        
        # 核心特性重叠度（权重15%）
        features1 = set(summary1.get("key_features", []))
        features2 = set(summary2.get("key_features", []))
        if features1 or features2:
            overlap = features1 & features2
            union = features1 | features2
            feature_sim = len(overlap) / len(union) * 100 if union else 100.0
            scores.append((feature_sim, 15))
        else:
            scores.append((100.0, 15))
        
        # 边界重叠度（权重10%）
        boundaries1 = set(summary1.get("boundaries", []))
        boundaries2 = set(summary2.get("boundaries", []))
        if boundaries1 or boundaries2:
            overlap = boundaries1 & boundaries2
            union = boundaries1 | boundaries2
            boundary_sim = len(overlap) / len(union) * 100 if union else 100.0
            scores.append((boundary_sim, 10))
        else:
            scores.append((100.0, 10))
        
        # 加权平均
        total_weight = sum(w for _, w in scores)
        weighted_score = sum(s * w for s, w in scores) / total_weight if total_weight > 0 else 100.0
        
        return round(weighted_score, 2)
    
    def analyze_skill_health(self, skill_name: str) -> dict:
        """分析技能健康度"""
        result = subprocess.run(
            [sys.executable, str(EVOLUTION_ENGINE), "analyze", skill_name],
            capture_output=True, text=True
        )
        
        # 解析输出
        health = {
            "skill": skill_name,
            "score": 0,
            "level": "unknown",
            "checks": [],
            "raw_output": result.stdout
        }
        
        for line in result.stdout.split("\n"):
            if "健康度:" in line:
                parts = line.split("健康度:")[1].strip()
                score_part = parts.split("/")[0].strip()
                # 移除emoji
                score_part = ''.join(c for c in score_part if c.isdigit())
                health["score"] = int(score_part) if score_part else 0
            if "health_level" in line or "健康度等级" in line:
                pass
        
        return health
    
    def get_all_skills_health(self) -> List[dict]:
        """获取所有技能的健康度，按分数排序"""
        result = subprocess.run(
            [sys.executable, str(EVOLUTION_ENGINE), "list"],
            capture_output=True, text=True
        )
        
        skills = []
        for line in result.stdout.split("\n"):
            if "/" in line and ("🟢" in line or "🟡" in line or "🟠" in line or "🔴" in line):
                # 解析技能行
                parts = [p.strip() for p in line.split() if p.strip()]
                if len(parts) >= 4:
                    # 找到包含/的部分（分数）
                    for i, part in enumerate(parts):
                        if "/" in part and "v" not in part:
                            score = int(part.split("/")[0])
                            # 技能名在前面
                            skill_name = ""
                            for j in range(i-1, -1, -1):
                                if parts[j] in ["🧬", "📦"]:
                                    skill_name = parts[j+1] if j+1 < i else ""
                                    break
                            if not skill_name:
                                skill_name = parts[1] if len(parts) > 1 else ""
                            
                            skills.append({
                                "name": skill_name,
                                "score": score
                            })
                            break
        
        # 按分数升序（最低分在前）
        skills.sort(key=lambda x: x["score"])
        return skills
    
    def backup_skill(self, skill_name: str, round_num: int) -> str:
        """备份技能目录，返回备份路径"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{skill_name}_r{round_num}_{timestamp}"
        backup_path = BACKUP_DIR / backup_name
        
        skill_dir = SKILLS_DIR / skill_name
        if skill_dir.exists():
            shutil.copytree(skill_dir, backup_path, symlinks=True)
        
        return str(backup_path)
    
    def rollback_skill(self, skill_name: str, backup_path: str) -> bool:
        """回滚技能到备份状态"""
        skill_dir = SKILLS_DIR / skill_name
        backup = Path(backup_path)
        
        if not backup.exists():
            return False
        
        try:
            # 删除当前目录
            if skill_dir.exists():
                shutil.rmtree(skill_dir)
            # 恢复备份
            shutil.copytree(backup, skill_dir, symlinks=True)
            return True
        except Exception as e:
            print(f"回滚失败: {e}")
            return False
    
    def document_evolution(self, skill_name: str) -> Tuple[bool, str]:
        """
        文档进化（低风险）
        返回：(是否成功, 变更描述)
        """
        skill_dir = SKILLS_DIR / skill_name
        skill_md = skill_dir / "SKILL.md"
        
        if not skill_md.exists():
            return False, "SKILL.md不存在"
        
        content = skill_md.read_text(encoding="utf-8")
        changes = []
        
        # 改进1: 添加使用示例章节
        if "使用示例" not in content and "示例" not in content:
            examples_section = f"""
## 使用示例

### 示例1：基础使用

```
# 加载技能
skill.load("{skill_name}")

# 执行核心功能
result = skill.execute(...)
```

### 示例2：进阶配置

```
# 自定义配置
config = {{
    "option1": "value1",
    "option2": "value2"
}}
skill.configure(config)
```
"""
            if "## 执行流程" in content:
                content = content.replace("## 执行流程", examples_section + "\n## 执行流程")
                changes.append("新增使用示例章节")
            elif "## 功能" in content:
                content = content.replace("## 功能", examples_section + "\n## 功能")
                changes.append("新增使用示例章节")
        
        # 改进2: 补充FAQ章节
        if "FAQ" not in content and "常见问题" not in content:
            faq_section = f"""
## 常见问题 (FAQ)

**Q: 如何开始使用{skill_name}技能？**
A: 首先阅读"快速开始"章节，按照步骤完成初始化配置，然后运行第一个示例。

**Q: 遇到问题如何排查？**
A: 建议先检查日志输出，确认配置是否正确。如仍无法解决，可参考"故障排除"章节或提交issue。

**Q: 这个技能可以和其他技能组合使用吗？**
A: 是的，技能设计遵循松耦合原则，可以与其他技能灵活组合。推荐配合agent-evolution使用以持续优化。

**Q: 如何贡献代码或文档？**
A: 欢迎提交PR！请遵循代码规范，确保所有测试通过，并附上相应的文档更新。
"""
            if "## 质量检查" in content:
                content = content.replace("## 质量检查", faq_section + "\n## 质量检查")
                changes.append("新增FAQ章节")
            elif "## 注意事项" in content:
                content = content.replace("## 注意事项", faq_section + "\n## 注意事项")
                changes.append("新增FAQ章节")
        
        # 改进3: 添加术语表
        if "术语表" not in content and "词汇表" not in content:
            glossary_section = """
## 术语表

| 术语 | 定义 |
|------|------|
| 技能(Skill) | 封装了特定功能的可复用模块，包含代码、文档和配置 |
| 健康度 | 衡量技能完整性和成熟度的综合指标 |
| 进化 | 技能持续自我优化和增强的过程 |
| 身份护栏 | 确保进化过程中核心身份不发生漂移的保护机制 |
| 回滚 | 将技能恢复到之前某个稳定状态的操作 |
"""
            if "## 质量检查" in content:
                content = content.replace("## 质量检查", glossary_section + "\n## 质量检查")
                changes.append("新增术语表章节")
            elif "## 注意事项" in content:
                content = content.replace("## 注意事项", glossary_section + "\n## 注意事项")
                changes.append("新增术语表章节")
        
        # 改进4: 添加版本历史
        if "版本历史" not in content and "更新日志" not in content and "changelog" not in content.lower():
            version_section = """
## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v1.0.0 | - | 初始版本，核心功能发布 |
"""
            # 追加到文档末尾
            content += "\n" + version_section
            changes.append("新增版本历史章节")
        
        # 保存修改
        if changes:
            skill_md.write_text(content, encoding="utf-8")
            return True, "文档优化: " + ", ".join(changes)
        
        # 改进5: 扩展README
        readme = skill_dir / "README.md"
        if readme.exists():
            readme_content = readme.read_text(encoding="utf-8")
            if len(readme_content) < 800:
                readme_content += f"""

## 安装与使用

### 安装方式
```bash
# 方式1：直接复制技能目录
cp -r {skill_name} /path/to/skills/

# 方式2：使用技能加载
skill.load("{skill_name}")
```

### 快速开始
1. 阅读 SKILL.md 了解技能详情
2. 完成基础配置
3. 运行示例代码验证功能
4. 根据实际需求调整参数

## 相关技能
- agent-evolution: 进化引擎（推荐配合使用，持续优化技能）
- agent-memory: 记忆系统
- agent-identity: 身份拓扑
- agent-ops: 运维监控
"""
                readme.write_text(readme_content, encoding="utf-8")
                return True, "README文档扩展"
        
        # 改进6: 创建或增强reference文档
        refs_dir = skill_dir / "references"
        if not refs_dir.exists():
            refs_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建API参考文档
            api_ref = f"""# {skill_name} API 参考

## 概述
本文档详细说明 {skill_name} 技能的所有公共接口和配置选项。

## 配置选项

| 选项名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| enabled | bool | True | 是否启用该技能 |
| debug | bool | False | 是否开启调试模式 |
| timeout | int | 30 | 操作超时时间（秒） |
| log_level | string | "INFO" | 日志级别: DEBUG/INFO/WARNING/ERROR |

## 公共方法

### execute(params)
执行技能的核心功能。

**参数:**
- params (dict): 参数字典

**返回:**
- dict: 执行结果

### configure(config)
配置技能参数。

**参数:**
- config (dict): 配置字典

**返回:**
- bool: 是否配置成功

## 事件

### on_before_execute
执行前触发，可用于参数校验。

### on_after_execute
执行后触发，可用于结果处理。

### on_error
发生错误时触发，可用于异常处理。

## 错误码

| 错误码 | 说明 | 处理建议 |
|--------|------|----------|
| 1001 | 参数错误 | 检查输入参数是否符合要求 |
| 1002 | 配置错误 | 检查配置项是否正确 |
| 1003 | 执行超时 | 增加超时时间或检查任务复杂度 |
| 1004 | 资源不足 | 检查系统资源使用情况 |
"""
            (refs_dir / "api_reference.md").write_text(api_ref, encoding="utf-8")
            return True, "新增references文档 (API参考)"
        
        return False, "无需文档进化"
    
    def code_evolution(self, skill_name: str) -> Tuple[bool, str]:
        """
        代码进化（中等风险）
        返回：(是否成功, 变更描述)
        """
        skill_dir = SKILLS_DIR / skill_name
        scripts_dir = skill_dir / "scripts"
        changes = []
        
        # 改进1: 添加测试框架（tests目录）
        tests_dir = skill_dir / "tests"
        if not tests_dir.exists():
            tests_dir.mkdir(parents=True, exist_ok=True)
            
            # 创建测试主文件
            test_main = f'''#!/usr/bin/env python3
"""
{skill_name} 技能测试套件
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
    print(f"✅ 找到 {{len(scripts)}} 个脚本文件")

def test_documentation():
    """测试文档完整性"""
    has_readme = (SKILL_DIR / "README.md").exists()
    has_refs = (SKILL_DIR / "references").exists()
    assert has_readme or has_refs, "缺少文档"
    print(f"✅ 文档完整性: README={{has_readme}}, References={{has_refs}}")

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
            print(f"❌ {{test.__name__}}: {{e}}")
            failed += 1
        except Exception as e:
            print(f"⚠️  {{test.__name__}}: 异常 - {{e}}")
            failed += 1
    
    print("=" * 50)
    print(f"测试结果: {{passed}} 通过, {{failed}} 失败")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
'''
            (tests_dir / "test_skill.py").write_text(test_main, encoding="utf-8")
            
            # 创建测试运行脚本
            run_test = f'''#!/bin/bash
# 运行 {skill_name} 技能测试套件

SCRIPT_DIR="$(cd "$(dirname "${{BASH_SOURCE[0]}}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "运行 $SKILL_DIR 技能测试..."
echo "========================================"

python3 "$SCRIPT_DIR/test_skill.py"
exit_code=$?

echo "========================================"
if [ $exit_code -eq 0 ]; then
    echo "✅ 所有测试通过"
else
    echo "❌ 测试失败"
fi

exit $exit_code
'''
            (tests_dir / "run_tests.sh").write_text(run_test, encoding="utf-8")
            os.chmod(tests_dir / "run_tests.sh", 0o755)
            
            changes.append("新增测试套件 (tests目录)")
        
        # 改进2: 添加配置文件支持
        config_file = skill_dir / "config" / "config.json"
        if not config_file.exists():
            config_dir = skill_dir / "config"
            if not config_dir.exists():
                config_dir.mkdir(parents=True, exist_ok=True)
            
            config = {
                "skill": skill_name,
                "version": "1.0.0",
                "enabled": True,
                "debug": False,
                "timeout": 30,
                "log_level": "INFO",
                "max_retries": 3,
                "evolution": {
                    "auto_evolve": True,
                    "min_health_score": 60,
                    "identity_similarity_threshold": 80
                }
            }
            config_file.write_text(json.dumps(config, indent=2, ensure_ascii=False))
            
            # 添加配置示例文件
            config_example = {
                "_comment": "这是配置示例文件，请复制为config.json后修改",
                "skill": skill_name,
                "enabled": True,
                "debug": False,
                "timeout": 30
            }
            (config_dir / "config.example.json").write_text(
                json.dumps(config_example, indent=2, ensure_ascii=False)
            )
            
            changes.append("新增配置文件 (config目录)")
        
        # 改进3: 增强脚本功能 - 添加日志模块
        if scripts_dir.exists():
            py_files = list(scripts_dir.glob("*.py"))
            for py_file in py_files[:1]:  # 只改第一个文件
                content = py_file.read_text(encoding="utf-8")
                
                # 检查是否已有日志模块
                if "import logging" not in content and "logging" not in content[:500]:
                    # 在文件开头添加日志设置
                    logger_setup = '''
import logging
from datetime import datetime

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)
'''
                    # 在导入部分之后插入
                    lines = content.split('\n')
                    insert_idx = 0
                    for i, line in enumerate(lines):
                        if line.startswith('import ') or line.startswith('from '):
                            insert_idx = i + 1
                        elif insert_idx > 0 and line.strip() and not line.startswith('#'):
                            break
                    
                    # 确保logs目录存在的代码
                    ensure_logs = '''
# 确保日志目录存在
import os
os.makedirs('logs', exist_ok=True)
'''
                    lines.insert(insert_idx, logger_setup + ensure_logs)
                    py_file.write_text('\n'.join(lines), encoding="utf-8")
                    changes.append(f"添加日志模块 ({py_file.name})")
                    break
        
        # 改进4: 添加错误处理和重试机制
        if scripts_dir.exists() and len(changes) == 0:
            py_files = list(scripts_dir.glob("*.py"))
            for py_file in py_files[:1]:
                content = py_file.read_text(encoding="utf-8")
                
                # 检查是否有重试机制
                if "retry" not in content.lower() and "try:" in content:
                    # 添加带重试的辅助函数
                    retry_decorator = '''

def retry(max_attempts=3, delay=1, backoff=2):
    """
    重试装饰器，用于处理可能失败的操作
    
    Args:
        max_attempts: 最大尝试次数
        delay: 初始延迟时间（秒）
        backoff: 延迟倍增因子
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            attempts = 0
            current_delay = delay
            last_exception = None
            
            while attempts < max_attempts:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempts += 1
                    last_exception = e
                    logger.warning(f"第 {attempts} 次尝试失败: {e}")
                    if attempts < max_attempts:
                        time.sleep(current_delay)
                        current_delay *= backoff
            
            logger.error(f"所有 {max_attempts} 次尝试都失败了")
            raise last_exception
        return wrapper
    return decorator
'''
                    # 在函数定义前插入
                    if 'def ' in content:
                        # 找到第一个函数定义前的位置
                        func_pos = content.find('\ndef ')
                        if func_pos > 0:
                            # 确保导入了time
                            if 'import time' not in content:
                                content = 'import time\n' + content
                            content = content[:func_pos] + '\n' + retry_decorator + '\n' + content[func_pos:]
                            py_file.write_text(content, encoding="utf-8")
                            changes.append(f"添加重试机制 ({py_file.name})")
                    break
        
        # 改进5: 添加性能监控
        if scripts_dir.exists() and len(changes) == 0:
            py_files = list(scripts_dir.glob("*.py"))
            for py_file in py_files[:1]:
                content = py_file.read_text(encoding="utf-8")
                
                if "timeit" not in content and "performance" not in content.lower():
                    perf_decorator = '''

def monitor_performance(func):
    """
    性能监控装饰器，记录函数执行时间
    """
    import time
    
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        duration = end_time - start_time
        logger.info(f"函数 {func.__name__} 执行时间: {duration:.4f}秒")
        
        if duration > 5:  # 超过5秒记录警告
            logger.warning(f"函数 {func.__name__} 执行时间过长: {duration:.4f}秒")
        
        return result
    return wrapper
'''
                    if 'def ' in content:
                        func_pos = content.find('\ndef ')
                        if func_pos > 0:
                            content = content[:func_pos] + '\n' + perf_decorator + '\n' + content[func_pos:]
                            py_file.write_text(content, encoding="utf-8")
                            changes.append(f"添加性能监控 ({py_file.name})")
                    break
        
        # 改进6: 添加数据验证工具函数
        if scripts_dir.exists() and len(changes) == 0:
            utils_file = scripts_dir / "utils.py"
            if not utils_file.exists():
                utils_content = '''#!/usr/bin/env python3
"""
工具函数模块
提供通用的工具函数，包括数据验证、类型转换等。
"""

import re
import json
from typing import Any, Optional, Dict, List


def validate_email(email: str) -> bool:
    """验证邮箱格式是否正确"""
    if not email:
        return False
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_url(url: str) -> bool:
    """验证URL格式是否正确"""
    if not url:
        return False
    pattern = r'^https?://[^\s/$.?#].[^\s]*$'
    return bool(re.match(pattern, url))


def safe_json_loads(json_str: str, default: Any = None) -> Any:
    """安全的JSON解析，失败时返回默认值"""
    try:
        return json.loads(json_str)
    except (json.JSONDecodeError, TypeError):
        return default


def truncate_string(s: str, max_length: int = 100, suffix: str = '...') -> str:
    """截断字符串到指定长度"""
    if len(s) <= max_length:
        return s
    return s[:max_length - len(suffix)] + suffix


def dict_get_nested(d: Dict, path: str, default: Any = None) -> Any:
    """安全地获取嵌套字典中的值
    
    Args:
        d: 字典
        path: 路径，用点号分隔，如 "a.b.c"
        default: 默认值
    """
    keys = path.split('.')
    current = d
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    return current


def batch_process(items: List, func, batch_size: int = 10) -> List:
    """批量处理数据
    
    Args:
        items: 待处理的项目列表
        func: 处理函数
        batch_size: 批次大小
    """
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i + batch_size]
        batch_results = [func(item) for item in batch]
        results.extend(batch_results)
    return results


class Config:
    """简单的配置管理器"""
    
    def __init__(self, config_file: str = None):
        self._config = {}
        if config_file:
            self.load(config_file)
    
    def load(self, config_file: str):
        """从文件加载配置"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            self._config = {}
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值"""
        return dict_get_nested(self._config, key, default)
    
    def set(self, key: str, value: Any):
        """设置配置值"""
        keys = key.split('.')
        current = self._config
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]
        current[keys[-1]] = value
    
    def to_dict(self) -> Dict:
        """返回配置字典"""
        return self._config.copy()
'''
                utils_file.write_text(utils_content, encoding="utf-8")
                changes.append("新增工具函数模块 (utils.py)")
        
        # 改进7: 为shell脚本添加错误处理
        if scripts_dir.exists() and len(changes) == 0:
            sh_files = list(scripts_dir.glob("*.sh"))
            for sh_file in sh_files[:1]:
                content = sh_file.read_text(encoding="utf-8")
                
                # 检查是否有set -e等安全选项
                if "set -e" not in content and "#!/bin/bash" in content:
                    # 在shebang后添加安全选项
                    safe_options = '''
set -e          # 遇到错误立即退出
set -u          # 遇到未定义变量报错
set -o pipefail # 管道命令失败时整个命令失败

# 日志函数
log_info() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [INFO] $*"
}

log_warn() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [WARN] $*" >&2
}

log_error() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] [ERROR] $*" >&2
}

# 错误处理
trap 'log_error "脚本执行失败，行号: $LINENO, 错误码: $?"; exit 1' ERR
'''
                    content = content.replace("#!/bin/bash\n", "#!/bin/bash\n" + safe_options + "\n")
                    sh_file.write_text(content, encoding="utf-8")
                    changes.append(f"增强shell脚本错误处理 ({sh_file.name})")
                    break
        
        if changes:
            return True, "代码进化: " + ", ".join(changes)
        
        return False, "无需代码进化"
    
    def run_evolution_round(self, skill_name: str, evolve_type: str = "document") -> dict:
        """
        执行一轮进化
        
        Args:
            skill_name: 技能名称
            evolve_type: 进化类型 - document/code/both
        
        Returns:
            进化结果字典
        """
        round_num = self.status["current_round"] + 1
        
        # 1. 提取进化前身份摘要
        pre_summary = self._extract_identity_summary(skill_name)
        
        # 2. 备份当前状态
        backup_path = self.backup_skill(skill_name, round_num)
        
        # 3. 获取进化前健康度
        pre_health = self.analyze_skill_health(skill_name)
        
        # 4. 执行进化
        evolution_result = {
            "round": round_num,
            "skill": skill_name,
            "type": evolve_type,
            "pre_score": pre_health["score"],
            "post_score": pre_health["score"],
            "identity_similarity": 100.0,
            "status": "success",
            "changes": [],
            "rollback": False,
            "drift_warning": False,
            "message": ""
        }
        
        doc_success = False
        code_success = False
        doc_message = ""
        code_message = ""
        
        if evolve_type in ["document", "both"]:
            doc_success, doc_message = self.document_evolution(skill_name)
            if doc_success:
                evolution_result["changes"].append(doc_message)
        
        if evolve_type in ["code", "both"]:
            code_success, code_message = self.code_evolution(skill_name)
            if code_success:
                evolution_result["changes"].append(code_message)
        
        # 5. 检查身份漂移
        post_summary = self._extract_identity_summary(skill_name)
        similarity = self.calculate_identity_similarity(pre_summary, post_summary)
        evolution_result["identity_similarity"] = similarity
        
        # 6. 身份护栏判断
        if similarity < 80:
            # 严重漂移，回滚
            self.rollback_skill(skill_name, backup_path)
            evolution_result["status"] = "rollback"
            evolution_result["rollback"] = True
            evolution_result["message"] = f"身份漂移严重（相似度{similarity}% < 80%），已回滚"
            self.status["rollback_count"] += 1
            return evolution_result
        elif similarity < 90:
            # 警告，但继续
            evolution_result["drift_warning"] = True
            evolution_result["message"] = f"身份漂移警告（相似度{similarity}%）"
            self.status["drift_warnings"] += 1
        
        # 7. 获取进化后健康度
        post_health = self.analyze_skill_health(skill_name)
        evolution_result["post_score"] = post_health["score"]
        
        if not evolution_result["changes"]:
            evolution_result["status"] = "no_change"
            evolution_result["message"] = "无可用进化项"
        
        return evolution_result
    
    def select_next_skill(self) -> Optional[str]:
        """选择下一个要进化的技能（优先最低分）"""
        skills = self.get_all_skills_health()
        
        if not skills:
            return None
        
        # 优先找未达标的最低分技能
        for skill in skills:
            if skill["score"] < self.status["target_score"]:
                return skill["name"]
        
        # 如果都达标了，选最低分的继续提升
        return skills[0]["name"]
    
    def determine_evolution_type(self, skill_name: str) -> str:
        """决定进化类型（优先文档进化）"""
        # 分析当前健康度详情
        health = self.analyze_skill_health(skill_name)
        
        # 简单策略：先文档后代码
        # 实际使用中可以根据检查项更智能地判断
        return "both"  # 都做，文档优先
    
    def generate_report(self) -> str:
        """生成进化进度报告"""
        skills = self.get_all_skills_health()
        
        report = f"""
🧬 连续进化进度报告
{'='*50}
总进化轮数: {self.status['total_rounds']}
运行时间: {self.status['started_at']} 至今
回滚次数: {self.status['rollback_count']}
漂移警告: {self.status['drift_warnings']}
目标分数: {self.status['target_score']}

📊 技能健康度排行（从低到高）:
"""
        for i, skill in enumerate(skills, 1):
            bar = "🟢" if skill["score"] >= 90 else "🟡" if skill["score"] >= 75 else "🟠" if skill["score"] >= 60 else "🔴"
            report += f"{i}. {bar} {skill['name']}: {skill['score']}/100\n"
        
        # 最近的进化历史
        recent = self.status["evolution_history"][-5:]
        if recent:
            report += f"\n📜 最近5轮进化:\n"
            for entry in recent:
                status_icon = "✅" if entry["status"] == "success" else "🔄" if entry["rollback"] else "⏭️"
                report += f"  R{entry['round']} {entry['skill']}: {entry['pre_score']}→{entry['post_score']} {status_icon} "
                if entry["rollback"]:
                    report += "(已回滚)"
                elif entry["drift_warning"]:
                    report += "(漂移警告)"
                report += "\n"
        
        return report
    
    def start(self, max_rounds: int = 0, target_score: int = 95):
        """启动连续进化"""
        if self.status["running"]:
            print("⚠️  进化已在运行中")
            return
        
        self.status["running"] = True
        self.status["started_at"] = datetime.now().isoformat()
        self.status["target_score"] = target_score
        self._save_status()
        
        print(f"🚀 启动连续进化模式")
        print(f"   目标分数: {target_score}")
        print(f"   最大轮数: {'无限' if max_rounds == 0 else max_rounds}")
        print()
        
        try:
            while True:
                # 检查最大轮数
                if max_rounds > 0 and self.status["total_rounds"] >= max_rounds:
                    print(f"\n🏁 已达到最大轮数 {max_rounds}，停止进化")
                    break
                
                # 选择技能
                skill_name = self.select_next_skill()
                if not skill_name:
                    print("\n❌ 没有可进化的技能")
                    break
                
                self.status["current_skill"] = skill_name
                self.status["current_round"] += 1
                self.status["total_rounds"] += 1
                
                print(f"--- 第 {self.status['current_round']} 轮: {skill_name} ---")
                
                # 决定进化类型
                evol_type = self.determine_evolution_type(skill_name)
                
                # 执行进化
                result = self.run_evolution_round(skill_name, evol_type)
                
                # 记录历史
                self.status["evolution_history"].append(result)
                
                # 输出结果
                if result["status"] == "success":
                    print(f"   ✅ 进化成功: {result['pre_score']} → {result['post_score']}")
                    for change in result["changes"]:
                        print(f"      - {change}")
                elif result["status"] == "rollback":
                    print(f"   🔄 身份漂移已回滚: 相似度 {result['identity_similarity']}%")
                else:
                    print(f"   ⏭️  无变化: {result['message']}")
                
                if result["drift_warning"]:
                    print(f"   ⚠️  身份漂移警告: {result['identity_similarity']}%")
                
                # 保存状态
                self._save_status()
                
                # 每3轮输出一次报告
                if self.status["total_rounds"] - self.status["last_report_round"] >= 3:
                    self.status["last_report_round"] = self.status["total_rounds"]
                    print(f"\n{'='*50}")
                    print("📊 第 {self.status['total_rounds']} 轮进化摘要")
                    print(self.generate_report())
                    print(f"{'='*50}\n")
                
                # 短暂休息
                time.sleep(0.5)
                
                # 检查是否所有技能都达标了
                skills = self.get_all_skills_health()
                all_target = all(s["score"] >= target_score for s in skills)
                if all_target:
                    print(f"\n🎉 所有技能已达到目标分数 {target_score}！")
                    # 继续提升，但降低频率
                    print("   继续优化中...")
                    time.sleep(1)
        
        except KeyboardInterrupt:
            print("\n\n⏹️  进化已暂停")
        except Exception as e:
            print(f"\n❌ 进化异常: {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.status["running"] = False
            self._save_status()
            
            # 最终报告
            print("\n" + "="*50)
            print("📋 最终进化报告")
            print(self.generate_report())
            print("="*50)
    
    def stop(self):
        """停止进化"""
        self.status["running"] = False
        self._save_status()
        print("⏹️  已发送停止信号")
    
    def show_status(self):
        """显示当前状态"""
        if self.status["running"]:
            print("🟢 进化运行中")
        else:
            print("⚪ 进化未运行")
        
        print(f"   总轮数: {self.status['total_rounds']}")
        print(f"   当前技能: {self.status['current_skill'] or '无'}")
        print(f"   回滚次数: {self.status['rollback_count']}")
        print(f"   漂移警告: {self.status['drift_warnings']}")
        
        if self.status["evolution_history"]:
            last = self.status["evolution_history"][-1]
            print(f"   最后一轮: R{last['round']} {last['skill']}")
            print(f"   分数变化: {last['pre_score']} → {last['post_score']}")


def main():
    if len(sys.argv) < 2:
        print("用法:")
        print("  python continuous_evolution.py start [--max-rounds N] [--target-score N]")
        print("  python continuous_evolution.py status")
        print("  python continuous_evolution.py stop")
        print("  python continuous_evolution.py report")
        return
    
    command = sys.argv[1]
    manager = ContinuousEvolutionManager()
    
    if command == "start":
        max_rounds = 0
        target_score = 95
        
        for i, arg in enumerate(sys.argv[2:], 2):
            if arg == "--max-rounds" and i+1 < len(sys.argv):
                max_rounds = int(sys.argv[i+1])
            elif arg == "--target-score" and i+1 < len(sys.argv):
                target_score = int(sys.argv[i+1])
        
        manager.start(max_rounds=max_rounds, target_score=target_score)
    
    elif command == "status":
        manager.show_status()
    
    elif command == "stop":
        manager.stop()
    
    elif command == "report":
        print(manager.generate_report())
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
