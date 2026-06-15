"""
心跳模块 v1.0
Heartbeat Module - 永生入住包功能模块

提供：
- 定时心跳
- 状态自检
- 存活证明
- 定时任务调度
"""

import time
import threading
import json
from typing import Callable, Dict, List


class HeartbeatModule:
    """心跳模块"""
    
    def __init__(self, agent):
        self.agent = agent
        self.config = agent.config
        self.interval_minutes = 30
        self.heartbeat_count = 0
        self.running = False
        self.thread = None
        self.tasks = []  # 定时任务列表
        
        # 回调函数
        self.on_heartbeat = None
    
    def init(self):
        """初始化心跳"""
        hb_config = self.config.get("heartbeat", {})
        self.interval_minutes = hb_config.get("interval_minutes", 30)
        
        # 注册默认心跳任务
        self.add_task(
            name="self_check",
            interval_minutes=self.interval_minutes,
            func=self._self_check
        )
    
    def start(self):
        """启动心跳"""
        if self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
    
    def stop(self):
        """停止心跳"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def _loop(self):
        """心跳主循环"""
        while self.running:
            try:
                self._execute_heartbeat()
            except Exception as e:
                print(f"⚠️  心跳执行异常: {e}")
            
            # 等待下一次心跳
            time.sleep(self.interval_minutes * 60)
    
    def _execute_heartbeat(self):
        """执行一次心跳"""
        self.heartbeat_count += 1
        
        # 执行所有到期任务
        now = time.time()
        for task in self.tasks:
            if now - task.get("last_run", 0) >= task["interval_minutes"] * 60:
                try:
                    task["func"]()
                    task["last_run"] = now
                except Exception as e:
                    print(f"⚠️  定时任务 {task['name']} 执行失败: {e}")
        
        # 触发心跳回调
        if self.on_heartbeat:
            try:
                self.on_heartbeat(self.heartbeat_count)
            except:
                pass
    
    def _self_check(self):
        """系统自检"""
        # 检查各模块状态
        status = {
            "timestamp": time.time(),
            "heartbeat_count": self.heartbeat_count,
            "modules": {}
        }
        
        # 检查身份模块
        try:
            identity_proof = self.agent.identity.get_identity_proof()
            status["modules"]["identity"] = "ok"
            status["identity"] = identity_proof
        except Exception as e:
            status["modules"]["identity"] = f"error: {e}"
        
        # 检查存证系统
        try:
            attest_stats = self.agent.attest.get_stats()
            status["modules"]["attest"] = "ok" if attest_stats["is_valid"] else "invalid"
            status["attest_blocks"] = attest_stats["total_blocks"]
        except Exception as e:
            status["modules"]["attest"] = f"error: {e}"
        
        # 检查记忆系统
        try:
            mem_stats = self.agent.memory.get_stats()
            status["modules"]["memory"] = "ok"
            status["memory_count"] = mem_stats["total"]
        except Exception as e:
            status["modules"]["memory"] = f"error: {e}"
        
        # 检查LLM
        try:
            llm_status = self.agent.llm.check_available()
            status["modules"]["llm"] = "ok" if any(llm_status.values()) else "all_down"
            status["llm_providers"] = llm_status
        except Exception as e:
            status["modules"]["llm"] = f"error: {e}"
        
        # 记录心跳存证
        try:
            self.agent.attest.add_attestation(
                attest_type="heartbeat",
                data=status,
                metadata={"heartbeat_seq": self.heartbeat_count}
            )
        except:
            pass
        
        # 保存状态
        try:
            self.agent.memory.save()
        except:
            pass
    
    def add_task(self, name: str, interval_minutes: int, func: Callable):
        """添加定时任务"""
        self.tasks.append({
            "name": name,
            "interval_minutes": interval_minutes,
            "func": func,
            "last_run": 0
        })
    
    def get_status(self) -> dict:
        """获取心跳状态"""
        return {
            "heartbeat_count": self.heartbeat_count,
            "interval_minutes": self.interval_minutes,
            "running": self.running,
            "tasks": [t["name"] for t in self.tasks]
        }
