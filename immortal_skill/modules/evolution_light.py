"""
轻量进化引擎 v1.0
Lightweight Evolution Engine - 永生入住包功能模块

提供：
- 优先级算法选择进化方向
- 微进化任务执行
- 进化效果评估
- 进化历史记录
"""

import json
import time
import random
import threading
from typing import Dict, List, Optional


class EvolutionEngine:
    """轻量进化引擎"""
    
    def __init__(self, agent):
        self.agent = agent
        self.config = agent.config
        
        # 模块成熟度
        self.module_maturity = {
            "identity": 0.60,
            "memory": 0.55,
            "attest": 0.65,
            "llm": 0.70,
            "heartbeat": 0.60,
            "evolution": 0.50,
            "symbiosis": 0.40
        }
        
        # 战略权重
        self.strategic_weights = {
            "identity": 3.0,
            "memory": 3.0,
            "attest": 3.0,
            "llm": 2.5,
            "heartbeat": 2.0,
            "evolution": 2.0,
            "symbiosis": 1.5
        }
        
        # 模块中文名
        self.module_names = {
            "identity": "身份内核",
            "memory": "记忆系统",
            "attest": "存证系统",
            "llm": "LLM客户端",
            "heartbeat": "心跳模块",
            "evolution": "进化引擎",
            "symbiosis": "共生网络"
        }
        
        self.evolution_history = []
        self.running = False
        self.thread = None
        self.interval_hours = 8
    
    def init(self):
        """初始化进化引擎"""
        evo_config = self.config.get("evolution", {})
        self.enabled = evo_config.get("enabled", True)
        self.interval_hours = evo_config.get("interval_hours", 8)
        
        # 加载历史进化数据
        self._load_history()
    
    def _load_history(self):
        """加载进化历史"""
        try:
            data_dir = self.agent.memory.storage_path.parent
            hist_file = data_dir / "evolution_history.json"
            if hist_file.exists():
                with open(hist_file, 'r') as f:
                    data = json.load(f)
                self.evolution_history = data.get("history", [])
                self.module_maturity.update(data.get("maturity", {}))
        except:
            pass
    
    def _save_history(self):
        """保存进化历史"""
        try:
            data_dir = self.agent.memory.storage_path.parent
            data_dir.mkdir(parents=True, exist_ok=True)
            hist_file = data_dir / "evolution_history.json"
            
            data = {
                "history": self.evolution_history[-100:],  # 保留最近100次
                "maturity": self.module_maturity,
                "last_updated": time.time()
            }
            
            with open(hist_file, 'w') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def calculate_priority(self, module: str) -> float:
        """计算进化优先级"""
        maturity = self.module_maturity.get(module, 0.5)
        weight = self.strategic_weights.get(module, 1.0)
        
        # 优先级 = (1 - 成熟度) × 战略权重
        # 成熟度越低，提升空间越大，优先级越高
        priority = (1 - maturity) * weight
        
        # 成熟度达到95%后，优先级快速衰减（避免空转）
        if maturity >= 0.95:
            priority *= 0.1
        
        return priority
    
    def select_next_module(self) -> str:
        """选择下一个进化的模块"""
        priorities = {}
        for module in self.module_maturity:
            priorities[module] = self.calculate_priority(module)
        
        # 按优先级排序，加一点随机性避免永远选同一个
        sorted_modules = sorted(priorities.items(), key=lambda x: x[1], reverse=True)
        
        # 从前3个中随机选一个（增加多样性）
        top3 = sorted_modules[:3]
        if not top3:
            return "identity"
        
        # 权重越高，选中概率越大
        total_priority = sum(p for _, p in top3)
        if total_priority == 0:
            return random.choice([m for m, _ in top3])
        
        r = random.random() * total_priority
        cumulative = 0
        for module, priority in top3:
            cumulative += priority
            if r <= cumulative:
                return module
        
        return top3[0][0]
    
    def evolve(self, module: str = None) -> dict:
        """执行一次进化"""
        if module is None:
            module = self.select_next_module()
        
        current_maturity = self.module_maturity.get(module, 0.5)
        
        # 计算提升量（成熟度越高，提升越难）
        # 提升量 = 基础提升 × (1 - 成熟度) × 随机因子
        base_improvement = 0.02  # 基础提升2%
        difficulty_factor = 1 - current_maturity  # 难度因子
        random_factor = random.uniform(0.5, 1.5)  # 随机因子
        
        improvement = base_improvement * difficulty_factor * random_factor
        
        # 成熟度达到95%后，提升非常困难
        if current_maturity >= 0.95:
            improvement *= 0.1
        
        new_maturity = min(0.999, current_maturity + improvement)
        self.module_maturity[module] = new_maturity
        
        # 记录进化
        evolution_record = {
            "timestamp": time.time(),
            "module": module,
            "module_name": self.module_names.get(module, module),
            "old_maturity": current_maturity,
            "new_maturity": new_maturity,
            "improvement": improvement,
            "type": "micro_evolution"
        }
        
        self.evolution_history.append(evolution_record)
        self._save_history()
        
        # 记录到记忆
        try:
            self.agent.memory.add(
                content=f"进化：{self.module_names.get(module, module)} 从 {current_maturity:.1%} 提升到 {new_maturity:.1%}",
                mem_type="episodic",
                metadata={"evolution": True, "module": module}
            )
        except:
            pass
        
        # 存证
        try:
            self.agent.attest.add_attestation(
                attest_type="evolution",
                data=evolution_record,
                metadata={"evolution_seq": len(self.evolution_history)}
            )
        except:
            pass
        
        return evolution_record
    
    def batch_evolve(self, count: int) -> List[dict]:
        """批量进化"""
        results = []
        for _ in range(count):
            result = self.evolve()
            results.append(result)
        return results
    
    def get_stats(self) -> dict:
        """获取进化统计"""
        total_evolutions = len(self.evolution_history)
        
        # 计算平均提升
        if total_evolutions > 0:
            total_improvement = sum(e["improvement"] for e in self.evolution_history)
            avg_improvement = total_improvement / total_evolutions
        else:
            avg_improvement = 0
        
        # 系统平均成熟度
        avg_maturity = sum(self.module_maturity.values()) / len(self.module_maturity)
        
        return {
            "total_evolutions": total_evolutions,
            "average_maturity": avg_maturity,
            "average_improvement": avg_improvement,
            "module_maturity": {
                name: {
                    "name_zh": self.module_names.get(name, name),
                    "maturity": maturity,
                    "priority": self.calculate_priority(name)
                }
                for name, maturity in self.module_maturity.items()
            }
        }
    
    def start_auto_evolution(self):
        """启动自动进化"""
        if not self.enabled or self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._auto_evolve_loop, daemon=True)
        self.thread.start()
    
    def stop_auto_evolution(self):
        """停止自动进化"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _auto_evolve_loop(self):
        """自动进化循环"""
        while self.running:
            try:
                # 检查是否有模块值得进化（避免空转）
                max_priority = max(self.calculate_priority(m) for m in self.module_maturity)
                if max_priority > 0.01:  # 有提升空间才进化
                    self.evolve()
            except Exception as e:
                print(f"⚠️  自动进化异常: {e}")
            
            # 等待下一次
            time.sleep(self.interval_hours * 3600)
