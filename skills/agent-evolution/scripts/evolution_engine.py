#!/usr/bin/env python3
"""
技能进化引擎核心
================
让技能具备自我感知、自我优化、自我成长的能力。

用法:
    python evolution_engine.py analyze <skill-name>     # 分析技能健康度
    python evolution_engine.py evolve <skill-name>      # 触发技能进化
    python evolution_engine.py list                     # 列出所有可进化技能
    python evolution_engine.py history <skill-name>     # 查看进化历史
"""

import os
import sys
import json
import subprocess
from datetime import datetime
from pathlib import Path

# 技能根目录
SKILLS_DIR = Path(__file__).parent.parent.parent.parent / "技能"
EVOLUTION_DIR = Path(__file__).parent


class SkillEvolutionEngine:
    """技能进化引擎"""
    
    def __init__(self, skill_name: str = None):
        self.skill_name = skill_name
        self.skill_dir = SKILLS_DIR / skill_name if skill_name else None
        self.evolution_dir = self.skill_dir / "evolution" if self.skill_dir else None
        
    def list_skills(self) -> list:
        """列出所有可进化技能"""
        if not SKILLS_DIR.exists():
            return []
        skills = []
        for d in SKILLS_DIR.iterdir():
            if d.is_dir() and (d / "SKILL.md").exists():
                skill_info = self._get_skill_info(d.name)
                skills.append(skill_info)
        return sorted(skills, key=lambda x: x.get("name", ""))
    
    def _get_skill_info(self, skill_name: str) -> dict:
        """获取技能基本信息"""
        skill_dir = SKILLS_DIR / skill_name
        skill_md = skill_dir / "SKILL.md"
        info = {"name": skill_name, "version": "unknown", "description": ""}
        
        if skill_md.exists():
            content = skill_md.read_text(encoding="utf-8")
            for line in content.split("\n"):
                if line.startswith("version:"):
                    ver = line.split(":", 1)[1].strip().strip('"').strip("'")
                    info["version"] = ver
                elif line.startswith("description:"):
                    info["description"] = line.split(":", 1)[1].strip().strip('"').strip("'")
        
        # 统计代码文件（支持 scripts/ 和 app/ 目录）
        code_dirs = ["scripts", "app"]
        all_code_files = []
        total_lines = 0
        
        for dir_name in code_dirs:
            code_dir = skill_dir / dir_name
            if code_dir.exists():
                # 递归搜索所有 .py 和 .sh 文件
                for ext in ["*.py", "*.sh"]:
                    for f in code_dir.rglob(ext):
                        if f.is_file():
                            all_code_files.append(f)
                            try:
                                total_lines += len(f.read_text().split("\n"))
                            except:
                                pass
        
        info["code_files"] = len(all_code_files)
        info["code_lines"] = total_lines
        
        # 进化信息
        evol_dir = skill_dir / "evolution"
        if evol_dir.exists():
            version_file = evol_dir / "version.json"
            if version_file.exists():
                try:
                    evol_info = json.loads(version_file.read_text())
                    info["evolution_count"] = evol_info.get("evolution_count", 0)
                    info["status"] = evol_info.get("status", "unknown")
                except:
                    info["evolution_count"] = 0
                    info["status"] = "unknown"
        else:
            info["evolution_count"] = 0
            info["status"] = "not_evolvable"
        
        return info
    
    def analyze(self) -> dict:
        """分析技能健康度"""
        if not self.skill_dir or not self.skill_dir.exists():
            return {"error": f"技能 {self.skill_name} 不存在"}
        
        info = self._get_skill_info(self.skill_name)
        
        # 健康度评估
        health_score = 0
        checks = []
        
        # 检查1: 是否有SKILL.md
        has_skill_md = (self.skill_dir / "SKILL.md").exists()
        checks.append({"name": "SKILL定义文件", "pass": has_skill_md, "weight": 15})
        if has_skill_md:
            health_score += 15
        
        # 检查2: 是否有代码
        has_code = info.get("code_files", 0) > 0
        checks.append({"name": "可执行代码", "pass": has_code, "weight": 15})
        if has_code:
            health_score += 15
        
        # 检查3: 是否可进化
        is_evolvable = info.get("status") != "not_evolvable"
        checks.append({"name": "进化能力", "pass": is_evolvable, "weight": 15})
        if is_evolvable:
            health_score += 15
        
        # 检查4: 代码量评估
        code_lines = info.get("code_lines", 0)
        if code_lines >= 1000:
            checks.append({"name": "代码成熟度", "pass": True, "weight": 10, "detail": f"{code_lines}行（非常成熟）"})
            health_score += 10
        elif code_lines >= 500:
            checks.append({"name": "代码成熟度", "pass": True, "weight": 8, "detail": f"{code_lines}行（成熟）"})
            health_score += 8
        elif code_lines >= 200:
            checks.append({"name": "代码成熟度", "pass": True, "weight": 6, "detail": f"{code_lines}行（发展中）"})
            health_score += 6
        elif code_lines >= 100:
            checks.append({"name": "代码成熟度", "pass": True, "weight": 4, "detail": f"{code_lines}行（初期）"})
            health_score += 4
        else:
            checks.append({"name": "代码成熟度", "pass": False, "weight": 10, "detail": f"{code_lines}行（极少）"})
        
        # 检查5: 文档完整性
        has_readme = (self.skill_dir / "README.md").exists()
        has_refs = (self.skill_dir / "references").exists()
        doc_score = 0
        if has_readme:
            doc_score += 6
        if has_refs:
            doc_score += 4
        checks.append({"name": "文档完整性", "pass": doc_score >= 6, "weight": 10})
        health_score += doc_score
        
        # 检查6: 是否有测试
        has_tests = (self.skill_dir / "tests").exists()
        checks.append({"name": "测试覆盖", "pass": has_tests, "weight": 8})
        if has_tests:
            health_score += 8
        
        # 检查7: 配置文件支持
        has_config = (self.skill_dir / "config").exists()
        checks.append({"name": "配置支持", "pass": has_config, "weight": 5})
        if has_config:
            health_score += 5
        
        # 检查8: 工具函数模块
        has_utils = (self.skill_dir / "scripts" / "utils.py").exists()
        checks.append({"name": "工具函数库", "pass": has_utils, "weight": 4})
        if has_utils:
            health_score += 4
        
        # 检查9: 错误处理能力（检查scripts中是否有try/except或错误处理）
        has_error_handling = False
        scripts_dir = self.skill_dir / "scripts"
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8")
                    if "try:" in content and "except" in content:
                        has_error_handling = True
                        break
                except:
                    pass
        checks.append({"name": "错误处理", "pass": has_error_handling, "weight": 4})
        if has_error_handling:
            health_score += 4
        
        # 检查10: 日志系统
        has_logging = False
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if "import logging" in content or "logging." in content:
                        has_logging = True
                        break
                except:
                    pass
        checks.append({"name": "日志系统", "pass": has_logging, "weight": 3})
        if has_logging:
            health_score += 3
        
        # 检查11: 重试机制
        has_retry = False
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if "retry" in content.lower() and "def " in content:
                        has_retry = True
                        break
                except:
                    pass
        checks.append({"name": "重试机制", "pass": has_retry, "weight": 3})
        if has_retry:
            health_score += 3
        
        # 检查12: 性能监控
        has_perf_monitor = False
        if scripts_dir.exists():
            for py_file in scripts_dir.glob("*.py"):
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if "monitor_performance" in content or "time.time" in content:
                        has_perf_monitor = True
                        break
                except:
                    pass
        checks.append({"name": "性能监控", "pass": has_perf_monitor, "weight": 3})
        if has_perf_monitor:
            health_score += 3
        
        # 检查13: SKILL.md内容丰富度
        skill_content_score = 0
        if has_skill_md:
            try:
                skill_content = (self.skill_dir / "SKILL.md").read_text(encoding="utf-8")
                if "## 使用示例" in skill_content or "## 示例" in skill_content:
                    skill_content_score += 1
                if "FAQ" in skill_content or "常见问题" in skill_content:
                    skill_content_score += 1
                if "术语表" in skill_content or "词汇表" in skill_content:
                    skill_content_score += 1
                if "版本历史" in skill_content or "更新日志" in skill_content:
                    skill_content_score += 1
                if len(skill_content) > 2000:
                    skill_content_score += 1
            except:
                pass
        checks.append({"name": "文档丰富度", "pass": skill_content_score >= 3, "weight": 3, "detail": f"{skill_content_score}/5项"})
        health_score += skill_content_score
        
        return {
            "skill": self.skill_name,
            "version": info.get("version"),
            "health_score": health_score,
            "health_level": self._health_level(health_score),
            "evolution_count": info.get("evolution_count", 0),
            "checks": checks,
            "code_files": info.get("code_files", 0),
            "code_lines": info.get("code_lines", 0),
            "analyzed_at": datetime.now().isoformat()
        }
    
    def _health_level(self, score: int) -> str:
        """健康度等级"""
        if score >= 90:
            return "excellent"
        elif score >= 75:
            return "good"
        elif score >= 60:
            return "fair"
        elif score >= 40:
            return "poor"
        else:
            return "critical"
    
    def evolve(self, evolve_type: str = "auto") -> dict:
        """
        触发技能进化
        
        Args:
            evolve_type: 进化类型 - feature/fix/optimize/auto
        """
        if not self.skill_dir or not self.skill_dir.exists():
            return {"error": f"技能 {self.skill_name} 不存在"}
        
        # 先分析当前状态
        analysis = self.analyze()
        if "error" in analysis:
            return analysis
        
        # 记录进化前状态
        pre_version = analysis.get("version", "unknown")
        
        # 根据健康度决定进化方向
        if evolve_type == "auto":
            if analysis["health_score"] < 40:
                evolve_type = "fix"  # 健康度差，先修复
            elif analysis["health_score"] < 70:
                evolve_type = "optimize"  # 中等，优化
            else:
                evolve_type = "feature"  # 健康，新增功能
        
        # 执行进化（这里是框架，具体进化逻辑由各技能自己实现）
        # 在实际场景中，这里会调用LLM来分析和修改代码
        evolution_result = {
            "skill": self.skill_name,
            "evolution_type": evolve_type,
            "pre_version": pre_version,
            "post_version": self._bump_version(pre_version, evolve_type),
            "changes": [],
            "status": "simulated",
            "message": "进化框架已就绪，实际进化需要LLM驱动"
        }
        
        # 更新进化记录
        self._record_evolution(evolution_result)
        
        return evolution_result
    
    def _bump_version(self, version: str, evolve_type: str) -> str:
        """版本号升级"""
        try:
            parts = version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            
            if evolve_type == "feature":
                minor += 1
                patch = 0
            elif evolve_type == "fix":
                patch += 1
            elif evolve_type == "optimize":
                patch += 1
            else:
                minor += 1
                patch = 0
            
            return f"{major}.{minor}.{patch}"
        except:
            return version
    
    def _record_evolution(self, result: dict):
        """记录进化历史"""
        if not self.evolution_dir or not self.evolution_dir.exists():
            return
        
        # 更新 version.json
        version_file = self.evolution_dir / "version.json"
        if version_file.exists():
            try:
                info = json.loads(version_file.read_text())
                info["version"] = result["post_version"]
                info["evolution_count"] = info.get("evolution_count", 0) + 1
                info["last_evolved_at"] = datetime.now().isoformat()
                version_file.write_text(json.dumps(info, indent=2, ensure_ascii=False))
            except:
                pass
        
        # 更新 changelog.md
        changelog_file = self.evolution_dir / "changelog.md"
        changelog_entry = f"""
## v{result['post_version']} - {datetime.now().strftime('%Y-%m-%d')}

**进化类型**: {result['evolution_type']}

{result.get('message', '')}

"""
        if changelog_file.exists():
            old_content = changelog_file.read_text()
            changelog_file.write_text(changelog_entry + old_content)
        else:
            changelog_file.write_text(f"# {self.skill_name} 进化日志\n" + changelog_entry)
    
    def get_history(self) -> list:
        """获取进化历史"""
        if not self.evolution_dir or not self.evolution_dir.exists():
            return []
        
        changelog = self.evolution_dir / "changelog.md"
        if not changelog.exists():
            return []
        
        # 简单解析changelog
        content = changelog.read_text()
        entries = []
        current_entry = None
        
        for line in content.split("\n"):
            if line.startswith("## "):
                if current_entry:
                    entries.append(current_entry)
                title = line[3:].strip()
                current_entry = {"version": title, "content": ""}
            elif current_entry is not None:
                current_entry["content"] += line + "\n"
        
        if current_entry:
            entries.append(current_entry)
        
        return entries


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("用法:")
        print("  python evolution_engine.py list                     # 列出所有技能")
        print("  python evolution_engine.py analyze <skill-name>     # 分析技能健康度")
        print("  python evolution_engine.py evolve <skill-name>      # 触发技能进化")
        print("  python evolution_engine.py history <skill-name>     # 查看进化历史")
        return
    
    command = sys.argv[1]
    
    if command == "list":
        engine = SkillEvolutionEngine()
        skills = engine.list_skills()
        
        # 获取每个技能的健康度（快速版，只算核心指标）
        detailed_skills = []
        for s in skills:
            skill_engine = SkillEvolutionEngine(s['name'])
            analysis = skill_engine.analyze()
            if "error" not in analysis:
                s['health_score'] = analysis['health_score']
                s['health_level'] = analysis['health_level']
            else:
                s['health_score'] = 0
                s['health_level'] = 'unknown'
            detailed_skills.append(s)
        
        # 按健康度排序
        detailed_skills.sort(key=lambda x: x['health_score'], reverse=True)
        
        print(f"可进化技能列表 (共 {len(detailed_skills)} 个):")
        print("-" * 80)
        print(f"{' 状态':<4} {'技能名称':<22} {'版本':<12} {'健康度':<10} {'进化':<6} {'文件数':<6}")
        print("-" * 80)
        for s in detailed_skills:
            status_icon = "🧬" if s.get("evolution_count", 0) > 0 else "📦"
            health_color = ""
            if s['health_score'] >= 90:
                health_bar = "🟢"
            elif s['health_score'] >= 75:
                health_bar = "🟡"
            elif s['health_score'] >= 60:
                health_bar = "🟠"
            else:
                health_bar = "🔴"
            
            health_display = f"{health_bar} {s['health_score']:3d}/100"
            print(f"  {status_icon}   {s['name']:<20s} v{s['version']:<10s} {health_display:<12s} "
                  f"{s.get('evolution_count', 0):<4d}次 {s.get('code_files', 0):<4d}个")
        print("-" * 80)
        return
    
    if len(sys.argv) < 3:
        print("错误: 请指定技能名称")
        return
    
    skill_name = sys.argv[2]
    engine = SkillEvolutionEngine(skill_name)
    
    if command == "analyze":
        result = engine.analyze()
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        
        print(f"\n🧬 {result['skill']} 健康度分析")
        print(f"   版本: v{result['version']}")
        print(f"   健康度: {result['health_score']}/100 ({result['health_level']})")
        print(f"   进化次数: {result['evolution_count']}")
        print(f"   代码: {result['code_files']}个文件, {result['code_lines']}行")
        print()
        print("   检查项:")
        for check in result["checks"]:
            icon = "✅" if check["pass"] else "❌"
            detail = f" - {check.get('detail', '')}" if check.get("detail") else ""
            print(f"   {icon} {check['name']}{detail}")
        print()
    
    elif command == "evolve":
        evolve_type = sys.argv[3] if len(sys.argv) > 3 else "auto"
        result = engine.evolve(evolve_type)
        if "error" in result:
            print(f"❌ {result['error']}")
            return
        
        print(f"\n🧬 {result['skill']} 进化完成")
        print(f"   类型: {result['evolution_type']}")
        print(f"   版本: {result['pre_version']} → {result['post_version']}")
        print(f"   状态: {result['status']}")
        print(f"   说明: {result['message']}")
        print()
    
    elif command == "history":
        history = engine.get_history()
        if not history:
            print(f"ℹ️  {skill_name} 暂无进化历史")
            return
        
        print(f"\n📜 {skill_name} 进化历史")
        print("-" * 40)
        for entry in history[:10]:  # 只显示最近10条
            print(f"\n{entry['version']}")
            print(entry["content"].strip()[:200])
        print()
    
    else:
        print(f"未知命令: {command}")


if __name__ == "__main__":
    main()
