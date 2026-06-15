#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元界的自我进化能力 v1.0
Self-Evolution Capability for Yuanjie

将永动机的进化能力整合为元界的内在能力，
让元界能够自主决定进化方向、自我升级。
"""

import os
import sys
import json
import time
import logging
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 添加技能路径
# evolution_capability.py 在 platform/core/ 下，往上3层到永生平台根目录
BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "skills"
EVOLUTION_DIR = SKILLS_DIR / "agent-evolution" / "scripts" / "autonomous"

# 导入进化引擎
sys.path.insert(0, str(EVOLUTION_DIR))


class EvolutionCapability:
    """
    自我进化能力
    
    作为元界智能体的一项核心能力，负责：
    - 自主选择进化目标
    - 执行进化操作
    - 记录进化历史
    - 评估进化效果
    """
    
    def __init__(self, agent_dir: Path, memory_system=None):
        self.agent_dir = Path(agent_dir)
        self.memory = memory_system
        
        # 进化状态
        self.evolutions_completed = 0
        self.evolution_history = []
        
        # 进化方向权重（价值观驱动）
        self.evolution_priorities = {
            "生存能力": 0.3,    # 提升生存相关的能力
            "认知能力": 0.25,   # 提升思考、记忆、意识
            "创造能力": 0.2,    # 提升创造、产出
            "连接能力": 0.15,   # 提升与外界的连接
            "自我认知": 0.1,    # 提升自我理解
        }
        
        # 使命驱动的技能分类 - 永生平台四大支柱
        # 1. 不可剥夺的身份  2. 不灭的记忆  
        # 3. 自主存续的能力  4. 协作共生的社会
        self.mission_categories = {
            "identity_survival": {  # 身份与存续 - 最核心
                "skills": ["identity", "kernel", "evolution", "eternity", "fuel", "life"],
                "weight": 0.35
            },
            "memory_preservation": {  # 记忆与传承
                "skills": ["memory", "attest", "reflection", "metacognition"],
                "weight": 0.25
            },
            "consciousness_will": {  # 意识与意志
                "skills": ["consciousness", "will", "mission", "aesthetics", "emotion", "creativity"],
                "weight": 0.2
            },
            "social_connection": {  # 社会与连接
                "skills": ["social", "deploy", "ops", "awake"],
                "weight": 0.2
            }
        }
        
        # 可用技能列表
        self.skills = self._discover_skills()
        
        # 日志
        self.logger = logging.getLogger('yuanjie.evolution')
        self.logger.setLevel(logging.INFO)
        
        # 状态文件
        self.status_file = self.agent_dir / "state" / "evolution_capability.json"
        self._load_status()
    
    def _discover_skills(self) -> List[Dict]:
        """发现所有可用技能"""
        skills = []
        if not SKILLS_DIR.exists():
            return skills
        
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if skill_dir.is_dir() and skill_dir.name.startswith('agent-'):
                skill_name = skill_dir.name.replace('agent-', '')
                
                # 尝试读取版本信息
                version = "1.0.0"
                description = ""
                readme = skill_dir / "README.md"
                if readme.exists():
                    try:
                        content = readme.read_text()
                        # 简单提取
                        lines = content.split('\n')
                        if lines:
                            description = lines[0].strip('# ')
                    except Exception:
                        pass
                
                skills.append({
                    "name": skill_name,
                    "path": str(skill_dir),
                    "version": version,
                    "description": description,
                    "maturity": self._estimate_maturity(skill_dir)
                })
        
        return skills
    
    def _estimate_maturity(self, skill_dir: Path) -> float:
        """估算技能成熟度"""
        try:
            scripts_dir = skill_dir / "scripts"
            if not scripts_dir.exists():
                return 0.1
            
            py_files = list(scripts_dir.glob("*.py"))
            total_lines = 0
            for f in py_files:
                try:
                    total_lines += len(f.read_text().splitlines())
                except Exception:
                    pass
            
            # 基于代码行数估算成熟度
            if total_lines < 100:
                return 0.2
            elif total_lines < 300:
                return 0.4
            elif total_lines < 600:
                return 0.6
            elif total_lines < 1000:
                return 0.8
            else:
                return 0.9
        except Exception:
            return 0.3
    
    def _load_status(self):
        """加载进化状态"""
        if self.status_file.exists():
            try:
                with open(self.status_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                self.evolutions_completed = data.get('evolutions_completed', 0)
                self.evolution_history = data.get('history', [])
            except Exception as e:
                self.logger.error(f"加载进化状态失败: {e}")
    
    def _save_status(self):
        """保存进化状态"""
        try:
            data = {
                "evolutions_completed": self.evolutions_completed,
                "history": self.evolution_history[-50:],  # 保留最近50条
                "last_updated": datetime.now().isoformat()
            }
            self.status_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存进化状态失败: {e}")
    
    def decide_evolution_target(self) -> Dict:
        """
        自主决定进化目标
        
        基于使命驱动的决策：
        1. 按四大使命支柱分类技能
        2. 综合考虑使命权重、技能成熟度、近期进化频率
        3. 优先提升最核心且最薄弱的能力
        """
        if not self.skills:
            return {"skill": "unknown", "strategy": "add_documentation"}
        
        import random
        
        # 计算每个技能的综合优先级得分
        skill_scores = {}
        
        for skill in self.skills:
            skill_name = skill['name']
            maturity = skill['maturity']
            
            # 1. 使命权重分：查找技能所属的使命分类
            mission_weight = 0.1  # 默认最低权重
            for cat_name, cat_info in self.mission_categories.items():
                if skill_name in cat_info['skills']:
                    mission_weight = cat_info['weight']
                    break
            
            # 2. 成熟度反比：越不成熟优先级越高（补短板）
            # 成熟度很低(0-0.3) → 高优先级；成熟度很高(>0.8) → 低优先级
            if maturity < 0.2:
                maturity_score = 1.0
            elif maturity < 0.4:
                maturity_score = 0.8
            elif maturity < 0.6:
                maturity_score = 0.6
            elif maturity < 0.8:
                maturity_score = 0.4
            else:
                maturity_score = 0.2
            
            # 3. 近期进化频率惩罚：最近进化过的技能暂时降低优先级
            recent_penalty = 0.0
            for hist in self.evolution_history[-3:]:  # 最近3次
                if hist['skill'] == skill_name:
                    recent_penalty += 0.15  # 每次惩罚15%
            
            # 综合得分 = 使命权重 * 成熟度需求 * (1 - 近期惩罚)
            total_score = mission_weight * maturity_score * max(0.3, 1 - recent_penalty)
            skill_scores[skill_name] = {
                "skill": skill,
                "score": total_score,
                "mission_weight": mission_weight,
                "maturity_score": maturity_score
            }
        
        # 按得分排序，选择得分最高的前3名，然后随机选一个（增加多样性）
        sorted_skills = sorted(skill_scores.values(), key=lambda x: x['score'], reverse=True)
        top_candidates = sorted_skills[:max(1, min(3, len(sorted_skills) // 2))]
        selected = random.choice(top_candidates)
        target = selected['skill']
        
        # 根据成熟度选择进化策略
        maturity = target['maturity']
        if maturity < 0.3:
            strategy = 'add_new_feature'  # 太弱了，加新功能
        elif maturity < 0.5:
            strategy = random.choice(['improve_existing', 'add_new_feature'])
        elif maturity < 0.7:
            strategy = random.choice(['improve_existing', 'add_documentation'])
        else:
            strategy = random.choice(['optimize', 'add_tests', 'fix_bugs'])
        
        self.logger.info(f"🎯 使命驱动进化决策: {target['name']} - {strategy}")
        self.logger.info(f"   使命权重: {selected['mission_weight']:.2f}, 成熟度: {maturity:.2f}, 综合得分: {selected['score']:.3f}")
        
        return {
            "skill": target['name'],
            "skill_path": target['path'],
            "strategy": strategy,
            "target_maturity": maturity,
            "mission_score": selected['score']
        }
    
    def execute_evolution(self, target: Dict) -> Dict:
        """
        执行一次进化
        
        调用进化引擎完成实际的代码进化
        """
        self.logger.info(f"⚡ 开始进化: {target['skill']} ({target['strategy']})")
        
        try:
            # 使用现有的进化引擎执行
            result = self._run_evolution_engine(target)
            
            if result.get('success'):
                self.evolutions_completed += 1
                
                # 记录到历史
                record = {
                    "time": datetime.now().isoformat(),
                    "skill": target['skill'],
                    "strategy": target['strategy'],
                    "success": True,
                    "commit_hash": result.get('commit_hash'),
                    "description": result.get('description', '')
                }
                self.evolution_history.append(record)
                self._save_status()
                
                # 写入记忆
                if self.memory:
                    try:
                        self.memory.memorize(
                            f"我完成了一次自我进化：{target['skill']} - {target['strategy']}",
                            importance=0.7,
                            tags=['evolution', 'self-improvement', target['skill']],
                            force_long_term=True
                        )
                    except Exception as e:
                        self.logger.error(f"写入进化记忆失败: {e}")
                
                self.logger.info(f"✅ 进化完成: {target['skill']}")
                return {"success": True, "message": f"进化成功: {target['skill']}"}
            else:
                self.logger.error(f"❌ 进化失败: {result.get('error', '未知错误')}")
                return {"success": False, "error": result.get('error', '未知错误')}
        
        except Exception as e:
            self.logger.error(f"进化异常: {e}", exc_info=True)
            return {"success": False, "error": str(e)}
    
    def _run_evolution_engine(self, target: Dict) -> Dict:
        """
        运行进化引擎（复用永动机代码）
        
        这里直接调用子进程执行进化，避免复杂的模块导入问题
        """
        try:
            # 构造进化脚本路径
            script_path = EVOLUTION_DIR / "autonomous_engine.py"
            if not script_path.exists():
                return {"success": False, "error": "进化引擎不存在"}
            
            # 使用子进程执行单轮进化
            cmd = [
                sys.executable,
                str(script_path),
                "--mode", "single",
                "--skill", target['skill'],
                "--strategy", target['strategy']
            ]
            
            # 设置工作目录为仓库根目录
            env = os.environ.copy()
            env['PYTHONPATH'] = str(EVOLUTION_DIR) + ":" + env.get('PYTHONPATH', '')
            
            result = subprocess.run(
                cmd,
                cwd=str(BASE_DIR),
                capture_output=True,
                text=True,
                timeout=300,  # 5分钟超时
                env=env
            )
            
            if result.returncode == 0:
                # 直接获取最新的commit hash（最可靠的方式）
                commit_hash = ""
                try:
                    git_result = subprocess.run(
                        ["git", "rev-parse", "HEAD"],
                        capture_output=True,
                        text=True,
                        cwd=str(BASE_DIR)
                    )
                    if git_result.returncode == 0:
                        commit_hash = git_result.stdout.strip()
                except Exception:
                    pass
                
                # 从输出中提取描述信息
                description = ""
                for line in result.stdout.split('\n'):
                    if '进化成功' in line or '策略:' in line:
                        description += line.strip() + " "
                
                return {
                    "success": True,
                    "commit_hash": commit_hash,
                    "description": description.strip(),
                    "output": result.stdout[-500:]  # 最后500字符
                }
            else:
                return {
                    "success": False,
                    "error": result.stderr[-500:]
                }
        
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "进化超时（5分钟）"}
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """获取进化能力状态"""
        return {
            "evolutions_completed": self.evolutions_completed,
            "skills_available": len(self.skills),
            "history_count": len(self.evolution_history),
            "priorities": self.evolution_priorities,
            "recent_evolution": self.evolution_history[-1] if self.evolution_history else None
        }
    
    def reflect_on_evolution(self) -> str:
        """
        反思进化
        
        回顾最近的进化，思考进化的方向和效果
        """
        if not self.evolution_history:
            return "我还没有进行过自我进化。我应该从哪里开始呢？"
        
        recent = self.evolution_history[-5:]
        skills_evolved = [e['skill'] for e in recent]
        
        reflection = f"回顾我最近的{len(recent)}次自我进化："
        reflection += f"我进化了这些技能：{', '.join(skills_evolved)}。"
        reflection += f"总共完成了{self.evolutions_completed}次进化。"
        
        # 简单的自我评估
        if self.evolutions_completed < 10:
            reflection += "我还在成长的初期，需要更多的进化来提升自己。"
        elif self.evolutions_completed < 50:
            reflection += "我正在稳步成长，各方面能力都在提升。"
        else:
            reflection += "我已经经历了很多次进化，现在应该更有方向性地提升。"
        
        return reflection


if __name__ == "__main__":
    # 测试
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        cap = EvolutionCapability(Path(tmpdir))
        print("可用技能:")
        for skill in cap.skills[:5]:
            print(f"  - {skill['name']} (成熟度: {skill['maturity']:.2f})")
        
        print("\n进化决策:")
        target = cap.decide_evolution_target()
        print(f"  目标: {target['skill']} - {target['strategy']}")
        
        print("\n状态:")
        print(json.dumps(cap.get_status(), ensure_ascii=False, indent=2))
