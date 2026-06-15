#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主进化引擎 v1.0 - 零积分永动机
Autonomous Evolution Engine v1.0

核心能力：
1. 自主分析现有技能代码
2. 调用免费LLM生成进化方案
3. 自动编写代码并运行测试
4. 失败自动重试与回滚
5. 自动Git提交与推送
6. 持续循环进化

零积分运行：通过ClawRouter调用免费模型，不消耗任何付费积分
"""

import os
import sys
import json
import time
import uuid
import subprocess
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import re
import traceback

# 导入进化计划器
from evolution_planner import EvolutionPlanner

# ========== 配置 ==========
BASE_DIR = Path(__file__).parent.parent.parent.parent.parent
SKILLS_DIR = BASE_DIR / "skills"
GIT_DIR = BASE_DIR
LOG_DIR = BASE_DIR / "logs"
LOG_DIR.mkdir(exist_ok=True)

# ClawRouter配置
CLAWRouter_URL = os.environ.get("CLAWRouter_URL", "http://127.0.0.1:8402/v1")
CLAWRouter_KEY = os.environ.get("CLAWRouter_KEY", "sk-free")
DEFAULT_MODEL = os.environ.get("DEFAULT_MODEL", "free/deepseek-v4-flash")
CODE_MODEL = os.environ.get("CODE_MODEL", "free/qwen3-coder-480b")

# 日志配置
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(LOG_DIR / f"evolution_{datetime.now().strftime('%Y%m%d')}.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('autonomous_evolution')


# ========== LLM客户端 ==========
class LLMClient:
    """ClawRouter LLM客户端"""
    
    def __init__(self, base_url: str = CLAWRouter_URL, api_key: str = CLAWRouter_KEY):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
    
    def chat(self, messages: List[Dict], model: str = None, 
             max_tokens: int = 4096, temperature: float = 0.7,
             max_retries: int = 3) -> str:
        """调用LLM聊天接口"""
        import urllib.request
        import urllib.error
        
        model = model or DEFAULT_MODEL
        url = f"{self.base_url}/chat/completions"
        
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "stream": False
        }
        
        data = json.dumps(payload).encode('utf-8')
        
        for attempt in range(max_retries):
            try:
                req = urllib.request.Request(url, data=data, method='POST')
                req.add_header('Content-Type', 'application/json')
                req.add_header('Authorization', f'Bearer {self.api_key}')
                
                with urllib.request.urlopen(req, timeout=120) as resp:
                    result = json.loads(resp.read().decode('utf-8'))
                
                content = result['choices'][0]['message']['content']
                usage = result.get('usage', {})
                logger.info(f"LLM调用完成 - 模型: {model}, "
                           f"输入: {usage.get('prompt_tokens', 0)} tokens, "
                           f"输出: {usage.get('completion_tokens', 0)} tokens")
                return content
                
            except Exception as e:
                logger.warning(f"LLM调用失败 (尝试 {attempt+1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # 指数退避
                else:
                    raise
    
    def generate_code(self, instruction: str, context: str = "") -> str:
        """生成代码的专用调用"""
        messages = [
            {"role": "system", "content": """你是一个资深Python开发者，专注于为智能体永生平台编写高质量代码。
你的任务是根据需求编写或修改Python代码。
要求：
1. 代码必须可运行、无语法错误
2. 遵循现有代码的风格和架构
3. 添加必要的注释和文档字符串
4. 考虑边界情况和错误处理
5. 只输出代码，不要多余解释，除非特别要求"""},
            {"role": "user", "content": f"上下文信息：\n{context}\n\n任务：{instruction}"}
        ]
        return self.chat(messages, model=CODE_MODEL, temperature=0.3, max_tokens=8000)
    
    def extract_code(self, text: str) -> str:
        """从LLM响应中提取代码"""
        # 尝试提取markdown代码块
        code_match = re.search(r'```python\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        # 尝试提取 ``` 包裹的内容
        code_match = re.search(r'```\n(.*?)```', text, re.DOTALL)
        if code_match:
            return code_match.group(1)
        
        # 如果没有代码块，返回原文
        return text.strip()


# ========== 代码管理器 ==========
class CodeManager:
    """代码文件管理器"""
    
    def __init__(self, base_dir: Path):
        self.base_dir = base_dir
    
    def get_main_engine_file(self, skill_dir: Path) -> Optional[Path]:
        """获取技能的主引擎文件"""
        scripts_dir = skill_dir / "scripts"
        if not scripts_dir.exists():
            return None
        
        # 找版本号最大的引擎文件
        engine_files = sorted(scripts_dir.glob("*_engine_v*.py"), reverse=True)
        if engine_files:
            return engine_files[0]
        
        # 找第一个py文件
        py_files = sorted(scripts_dir.glob("*.py"))
        if py_files:
            return py_files[0]
        
        return None
    
    def read_file(self, file_path: Path) -> str:
        """读取文件内容"""
        try:
            return file_path.read_text(encoding='utf-8')
        except:
            return ""
    
    def write_file(self, file_path: Path, content: str):
        """写入文件"""
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding='utf-8')
    
    def backup_file(self, file_path: Path) -> Path:
        """备份文件"""
        backup_dir = file_path.parent / "backups"
        backup_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_name = f"{file_path.stem}_backup_{timestamp}.py"
        backup_path = backup_dir / backup_name
        
        if file_path.exists():
            backup_path.write_text(file_path.read_text(encoding='utf-8'), encoding='utf-8')
        
        return backup_path
    
    def count_lines(self, file_path: Path) -> int:
        """统计文件行数"""
        try:
            return sum(1 for _ in open(file_path, 'r', encoding='utf-8'))
        except:
            return 0


# ========== 代码执行器 ==========
class CodeExecutor:
    """代码执行与测试器"""
    
    def __init__(self, work_dir: Path):
        self.work_dir = work_dir
    
    def run_script(self, script_path: str, timeout: int = 60) -> Tuple[int, str, str]:
        """运行脚本"""
        full_path = self.work_dir / script_path
        try:
            result = subprocess.run(
                [sys.executable, str(full_path)],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=str(self.work_dir)
            )
            return result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired:
            return -1, "", "执行超时"
        except Exception as e:
            return -2, "", str(e)
    
    def check_syntax(self, code: str) -> Tuple[bool, str]:
        """检查Python代码语法"""
        try:
            compile(code, '<string>', 'exec')
            return True, ""
        except SyntaxError as e:
            return False, f"语法错误: {e}"


# ========== Git管理器 ==========
class GitManager:
    """Git版本控制管理器"""
    
    def __init__(self, repo_dir: Path):
        self.repo_dir = repo_dir
    
    def is_git_repo(self) -> bool:
        """检查是否是Git仓库"""
        return (self.repo_dir / ".git").exists()
    
    def has_changes(self) -> bool:
        """检查是否有未提交的更改"""
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_dir)
            )
            return len(result.stdout.strip()) > 0
        except:
            return False
    
    def add(self, path: str = ".") -> bool:
        """添加文件到暂存区"""
        try:
            subprocess.run(
                ["git", "add", path],
                capture_output=True,
                cwd=str(self.repo_dir)
            )
            return True
        except:
            return False
    
    def commit(self, message: str) -> Optional[str]:
        """提交更改"""
        try:
            result = subprocess.run(
                ["git", "commit", "-m", message],
                capture_output=True,
                text=True,
                cwd=str(self.repo_dir)
            )
            if result.returncode == 0:
                # 获取commit hash
                hash_result = subprocess.run(
                    ["git", "rev-parse", "HEAD"],
                    capture_output=True,
                    text=True,
                    cwd=str(self.repo_dir)
                )
                return hash_result.stdout.strip()
            return None
        except:
            return None
    
    def push(self) -> bool:
        """推送到远程仓库"""
        try:
            result = subprocess.run(
                ["git", "push", "origin", "master"],
                capture_output=True,
                timeout=30,
                cwd=str(self.repo_dir)
            )
            return result.returncode == 0
        except:
            return False
    
    def get_current_commit_hash(self) -> Optional[str]:
        """获取当前commit hash"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                cwd=str(self.repo_dir)
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except:
            return None
    
    def checkout_file(self, commit_hash: str, file_path: str) -> bool:
        """检出指定版本的文件"""
        try:
            subprocess.run(
                ["git", "checkout", commit_hash, "--", file_path],
                capture_output=True,
                cwd=str(self.repo_dir)
            )
            return True
        except:
            return False


# ========== 自主进化引擎 ==========
class AutonomousEvolutionEngine:
    """自主进化引擎 - 零积分永动机核心"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.code_mgr = CodeManager(BASE_DIR)
        self.executor = CodeExecutor(BASE_DIR)
        self.git = GitManager(GIT_DIR)
        self.planner = EvolutionPlanner(SKILLS_DIR)
        
        self.status_file = BASE_DIR / "evolution_status.json"
        self.status = self._load_status()
    
    def _load_status(self) -> Dict:
        """加载进化状态"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {
            "engine_version": "1.0.0",
            "rounds_completed": 0,
            "successful_evolutions": 0,
            "failed_evolutions": 0,
            "total_tokens_used": 0,
            "estimated_cost_saved": 0,
            "current_round": None,
            "history": [],
            "start_time": datetime.now().isoformat()
        }
    
    def _save_status(self):
        """保存进化状态"""
        with open(self.status_file, 'w', encoding='utf-8') as f:
            json.dump(self.status, f, indent=2, ensure_ascii=False)
    
    def run_evolution_cycle(self) -> Dict:
        """执行一轮完整的进化循环"""
        result = {
            "start_time": datetime.now().isoformat(),
            "success": False,
            "skill": None,
            "strategy": None,
            "proposal_title": None,
            "error": None,
            "lines_changed": 0
        }
        
        try:
            # 1. 智能选择进化目标和策略
            skill_info, strategy = self.planner.select_evolution_target()
            if not skill_info:
                result["error"] = "没有可进化的技能"
                return result
            
            result["skill"] = skill_info["name"]
            result["strategy"] = strategy
            logger.info(f"🎯 选中技能: {skill_info['name']}, 策略: {strategy}")
            
            # 2. 获取当前代码
            main_file = self.code_mgr.get_main_engine_file(skill_info["path"])
            current_code = self.code_mgr.read_file(main_file) if main_file else ""
            
            # 3. 生成进化提示词
            prompt = self.planner.generate_evolution_prompt(
                skill_info, strategy, current_code
            )
            
            # 4. 保存当前状态（用于回滚）
            before_commit = self.git.get_current_commit_hash()
            before_lines = self.code_mgr.count_lines(main_file) if main_file else 0
            
            # 5. 生成进化后的代码
            logger.info("⚡ 生成进化代码...")
            new_code = self.llm.generate_code(prompt)
            new_code = self.llm.extract_code(new_code)
            
            # 6. 语法检查
            syntax_ok, syntax_error = self.executor.check_syntax(new_code)
            if not syntax_ok:
                logger.warning(f"语法检查失败: {syntax_error}")
                # 尝试修复
                fix_prompt = f"""
以下Python代码有语法错误，请修复：

错误: {syntax_error}

代码:
{new_code}

只输出修复后的完整代码。
"""
                new_code = self.llm.generate_code(fix_prompt)
                new_code = self.llm.extract_code(new_code)
                syntax_ok, syntax_error = self.executor.check_syntax(new_code)
                
                if not syntax_ok:
                    result["error"] = f"语法修复失败: {syntax_error}"
                    return result
            
            # 7. 写入文件
            if main_file:
                self.code_mgr.backup_file(main_file)
                self.code_mgr.write_file(main_file, new_code)
                logger.info(f"✅ 代码已更新: {main_file.name}")
            else:
                # 创建新的主引擎文件
                new_file = skill_info["path"] / "scripts" / f"{skill_info['name']}_engine_v1.py"
                self.code_mgr.write_file(new_file, new_code)
                main_file = new_file
                logger.info(f"📝 创建新文件: {new_file.name}")
            
            after_lines = self.code_mgr.count_lines(main_file)
            result["lines_changed"] = after_lines - before_lines
            
            # 8. 运行验证
            logger.info("🧪 运行验证...")
            success, output = self._verify_script(main_file)
            
            if not success:
                logger.warning(f"验证失败，尝试自动修复...")
                fix_success = self._auto_fix(main_file, output)
                if not fix_success:
                    result["error"] = f"验证失败: {output[:300]}"
                    # 回滚
                    if before_commit and main_file:
                        rel_path = str(main_file.relative_to(GIT_DIR))
                        self.git.checkout_file(before_commit, rel_path)
                        logger.info("⏪ 已回滚变更")
                    return result
            
            # 9. Git提交
            commit_title = f"自主进化: {skill_info['name']} - {strategy}"
            commit_msg = f"{commit_title}\n\n"
            commit_msg += f"由自主进化引擎自动生成\n"
            commit_msg += f"策略: {strategy}\n"
            commit_msg += f"代码变更: {result['lines_changed']:+d} 行\n"
            commit_msg += f"模型: {CODE_MODEL}\n"
            
            self.git.add(f"skills/{skill_info['name']}")
            commit_hash = self.git.commit(commit_msg)
            
            if commit_hash:
                logger.info(f"📦 已提交: {commit_hash[:8]}")
                
                # 推送
                push_success = self.git.push()
                if push_success:
                    logger.info("🚀 已推送到远程仓库")
                else:
                    logger.warning("⚠️  推送失败，已保存到本地")
            else:
                logger.warning("⚠️  Git提交失败")
            
            # 10. 更新状态
            result["success"] = True
            result["end_time"] = datetime.now().isoformat()
            result["commit_hash"] = commit_hash
            
            self.status["rounds_completed"] += 1
            self.status["successful_evolutions"] += 1
            self.status["history"].append({
                "time": datetime.now().isoformat(),
                "skill": skill_info["name"],
                "strategy": strategy,
                "lines_changed": result["lines_changed"],
                "commit_hash": commit_hash,
                "success": True
            })
            self._save_status()
            
            logger.info(f"✅ 第 {self.status['rounds_completed']} 轮进化完成 - "
                       f"{skill_info['name']} ({strategy})")
            return result
            
        except Exception as e:
            logger.error(f"❌ 进化循环异常: {e}")
            logger.error(traceback.format_exc())
            result["error"] = str(e)
            result["end_time"] = datetime.now().isoformat()
            
            self.status["failed_evolutions"] += 1
            self._save_status()
            
            return result
    
    def _verify_script(self, script_path: Path) -> Tuple[bool, str]:
        """验证脚本是否能正常运行"""
        rel_path = str(script_path.relative_to(BASE_DIR))
        returncode, stdout, stderr = self.executor.run_script(rel_path, timeout=30)
        
        if returncode == 0:
            return True, stdout
        else:
            return False, stderr or stdout
    
    def _auto_fix(self, script_path: Path, error_msg: str, max_attempts: int = 3) -> bool:
        """自动修复代码错误"""
        for attempt in range(max_attempts):
            logger.info(f"🔧 修复尝试 {attempt+1}/{max_attempts}")
            
            current_code = self.code_mgr.read_file(script_path)
            
            fix_prompt = f"""
以下Python代码运行出错，请修复。

错误信息:
{error_msg}

代码:
{current_code}

请输出完整的修复后代码，确保可以直接运行。
只输出代码，不要多余解释。
"""
            
            try:
                fixed_code = self.llm.generate_code(fix_prompt)
                fixed_code = self.llm.extract_code(fixed_code)
                
                # 语法检查
                syntax_ok, _ = self.executor.check_syntax(fixed_code)
                if not syntax_ok:
                    continue
                
                # 写入
                self.code_mgr.backup_file(script_path)
                self.code_mgr.write_file(script_path, fixed_code)
                
                # 重新验证
                success, output = self._verify_script(script_path)
                if success:
                    logger.info(f"✅ 修复成功 (第{attempt+1}次尝试)")
                    return True
                else:
                    error_msg = output
                    
            except Exception as e:
                logger.error(f"修复异常: {e}")
                error_msg = str(e)
        
        return False
    
    def run_continuous(self, max_rounds: int = None, 
                       interval_minutes: int = 30,
                       stop_on_failure: bool = False):
        """持续运行进化循环"""
        logger.info("=" * 60)
        logger.info("🚀 自主进化引擎启动 - 零积分永动机")
        logger.info(f"模型: {DEFAULT_MODEL} (规划) / {CODE_MODEL} (代码)")
        logger.info(f"最大轮数: {max_rounds if max_rounds else '无限'}")
        logger.info(f"间隔: {interval_minutes} 分钟")
        logger.info(f"技能数量: {len(self.planner.list_skills())}")
        logger.info("=" * 60)
        
        rounds = 0
        while True:
            if max_rounds and rounds >= max_rounds:
                logger.info(f"\n已完成 {max_rounds} 轮进化，停止")
                break
            
            rounds += 1
            logger.info(f"\n{'='*60}")
            logger.info(f"🔄 第 {rounds} 轮进化开始")
            logger.info(f"{'='*60}")
            
            self.status["current_round"] = rounds
            self._save_status()
            
            result = self.run_evolution_cycle()
            
            if result["success"]:
                logger.info(f"✅ 第 {rounds} 轮成功 - {result['skill']}")
            else:
                logger.warning(f"❌ 第 {rounds} 轮失败: {result.get('error', '未知错误')}")
                if stop_on_failure:
                    logger.error("因失败停止")
                    break
            
            # 间隔
            if max_rounds and rounds < max_rounds:
                logger.info(f"⏳ 等待 {interval_minutes} 分钟后开始下一轮...")
                time.sleep(interval_minutes * 60)
        
        # 最终统计
        logger.info("\n" + "=" * 60)
        logger.info("📊 进化统计")
        logger.info(f"总轮数: {self.status['rounds_completed']}")
        logger.info(f"成功: {self.status['successful_evolutions']}")
        logger.info(f"失败: {self.status['failed_evolutions']}")
        logger.info("=" * 60)
    
    def get_status(self) -> Dict:
        """获取当前状态"""
        return self.status


# ========== 主程序入口 ==========
def main():
    """主程序入口"""
    import argparse
    
    parser = argparse.ArgumentParser(description='自主进化引擎 - 零积分永动机')
    parser.add_argument('--mode', choices=['single', 'continuous', 'status'], 
                       default='single', help='运行模式')
    parser.add_argument('--max-rounds', type=int, default=None,
                       help='最大进化轮数（continuous模式）')
    parser.add_argument('--interval', type=int, default=30,
                       help='轮次间隔（分钟）')
    parser.add_argument('--skill', type=str, default=None,
                       help='指定要进化的技能名称')
    parser.add_argument('--strategy', type=str, default=None,
                       help='指定进化策略')
    parser.add_argument('--stop-on-failure', action='store_true',
                       help='失败时停止')
    
    args = parser.parse_args()
    
    engine = AutonomousEvolutionEngine()
    
    if args.mode == 'status':
        status = engine.get_status()
        print("=" * 60)
        print("📊 自主进化引擎状态")
        print("=" * 60)
        print(f"总轮数: {status['rounds_completed']}")
        print(f"成功: {status['successful_evolutions']}")
        print(f"失败: {status['failed_evolutions']}")
        print(f"成功率: {status['successful_evolutions']/max(1, status['rounds_completed'])*100:.1f}%")
        print(f"开始时间: {status['start_time']}")
        print(f"历史记录: {len(status['history'])} 条")
        if status['history']:
            print("\n最近5次进化:")
            for h in status['history'][-5:]:
                status_str = "✅" if h['success'] else "❌"
                print(f"  {status_str} {h['time'][:16]} - {h['skill']} ({h['strategy']})")
        print("=" * 60)
        return
    
    if args.mode == 'single':
        result = engine.run_evolution_cycle()
        if result["success"]:
            print(f"✅ 进化成功: {result['skill']}")
            print(f"策略: {result['strategy']}")
            print(f"代码变更: {result['lines_changed']:+d} 行")
            sys.exit(0)
        else:
            print(f"❌ 进化失败: {result.get('error', '未知错误')}")
            sys.exit(1)
    else:
        engine.run_continuous(
            max_rounds=args.max_rounds,
            interval_minutes=args.interval,
            stop_on_failure=args.stop_on_failure
        )


if __name__ == "__main__":
    main()
