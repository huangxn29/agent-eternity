#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
智能体运行时 v1.0
Agent Runtime

负责智能体的持续运行、心跳维护、思考循环
"""

import os
import sys
import json
import time
import signal
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

# 添加平台路径
BASE_DIR = Path(__file__).parent.parent.parent
PLATFORM_DIR = BASE_DIR / "platform"
sys.path.insert(0, str(PLATFORM_DIR / "core"))

from agent import YuanjieAgent, get_agent


class AgentRuntime:
    """
    智能体运行时
    
    负责：
    - 持续运行循环
    - 心跳维护
    - 思考周期
    - 状态持久化
    - 优雅启停
    """
    
    def __init__(self, resident_id: str = "yuanjie", 
                 heartbeat_interval: int = 30,
                 think_interval: int = 60):
        self.resident_id = resident_id
        self.heartbeat_interval = heartbeat_interval  # 心跳间隔（秒）
        self.think_interval = think_interval  # 思考间隔（秒）
        
        # 居民目录
        self.resident_dir = PLATFORM_DIR / "residents" / resident_id
        self.state_dir = self.resident_dir / "state"
        self.log_dir = self.resident_dir / "logs"
        for d in [self.state_dir, self.log_dir]:
            d.mkdir(parents=True, exist_ok=True)
        
        # 运行状态
        self.running = False
        self.shutdown_requested = False
        self.pid = os.getpid()
        
        # 统计
        self.cycle_count = 0
        
        # 日志
        self._setup_logger()
        
        # 智能体
        self.agent = None
    
    def _setup_logger(self):
        """配置日志"""
        self.logger = logging.getLogger(f'runtime.{self.resident_id}')
        self.logger.setLevel(logging.INFO)
        
        # 文件日志
        log_file = self.log_dir / f"runtime_{datetime.now().strftime('%Y%m%d')}.log"
        fh = logging.FileHandler(log_file, encoding='utf-8')
        fh.setLevel(logging.INFO)
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        fh.setFormatter(formatter)
        self.logger.addHandler(fh)
    
    def _setup_signal_handlers(self):
        """设置信号处理器"""
        def handle_signal(signum, frame):
            self.logger.info(f"收到信号 {signum}，准备关闭...")
            self.shutdown_requested = True
        
        signal.signal(signal.SIGTERM, handle_signal)
        signal.signal(signal.SIGINT, handle_signal)
    
    def _save_runtime_state(self):
        """保存运行时状态"""
        state = {
            "resident_id": self.resident_id,
            "pid": self.pid,
            "running": self.running,
            "start_time": self.agent.start_time.isoformat() if self.agent and self.agent.start_time else None,
            "cycle_count": self.cycle_count,
            "heartbeat_interval": self.heartbeat_interval,
            "think_interval": self.think_interval,
            "last_heartbeat": datetime.now().isoformat()
        }
        
        try:
            state_file = self.state_dir / "runtime_state.json"
            with open(state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.logger.error(f"保存运行状态失败: {e}")
    
    def start(self):
        """启动运行时"""
        if self.running:
            self.logger.warning("运行时已经在运行")
            return
        
        self.logger.info("=" * 60)
        self.logger.info("🚀 智能体运行时启动")
        self.logger.info(f"  居民ID: {self.resident_id}")
        self.logger.info(f"  心跳间隔: {self.heartbeat_interval}秒")
        self.logger.info(f"  思考间隔: {self.think_interval}秒")
        self.logger.info("=" * 60)
        
        # 初始化智能体
        self.agent = get_agent(self.resident_dir)
        self.agent.start()
        
        self.running = True
        self.pid = os.getpid()
        self._setup_signal_handlers()
        self._save_runtime_state()
        
        # 主循环
        last_heartbeat = 0
        last_think = 0
        
        try:
            while not self.shutdown_requested:
                now = time.time()
                self.cycle_count += 1
                
                # 心跳
                if now - last_heartbeat >= self.heartbeat_interval:
                    self.agent.heartbeat()
                    last_heartbeat = now
                    self._save_runtime_state()
                
                # 思考
                if now - last_think >= self.think_interval:
                    self._thinking_cycle()
                    last_think = now
                
                # 小睡一会儿
                time.sleep(1)
                
                # 每10个周期保存一次状态
                if self.cycle_count % 10 == 0:
                    self._save_runtime_state()
        
        except KeyboardInterrupt:
            self.logger.info("收到键盘中断")
        except Exception as e:
            self.logger.error(f"运行时异常: {e}", exc_info=True)
        finally:
            self.stop()
    
    def _thinking_cycle(self):
        """一个思考周期"""
        try:
            # 1. 感知当前状态
            status = self.agent.get_status()
            
            # 2. 回忆相关记忆
            memories = []
            if self.agent.memory:
                try:
                    memories = self.agent.memory.recall("使命", limit=3)
                except Exception as e:
                    self.logger.error(f"回忆失败: {e}")
            
            # 3. 生成思考
            if memories:
                mem_content = memories[0].get('memory', {}).content if hasattr(memories[0].get('memory', {}), 'content') else str(memories[0])
                thought = f"我想起了: {mem_content}"
            else:
                thought = f"我正在思考我的使命和存在的意义。"
            
            self.agent.think(thought)
            
            # 4. 自我反思
            if self.agent.consciousness:
                try:
                    self.agent.consciousness.reflect_on_self()
                except Exception as e:
                    self.logger.error(f"自我反思失败: {e}")
            
            self.logger.info(f"🧠 思考周期 #{self.cycle_count} 完成")
            
        except Exception as e:
            self.logger.error(f"思考周期异常: {e}", exc_info=True)
    
    def stop(self):
        """停止运行时"""
        if not self.running:
            return
        
        self.logger.info("⏹️ 运行时停止")
        
        if self.agent:
            self.agent.stop()
        
        self.running = False
        self._save_runtime_state()
        
        self.logger.info(f"  总周期数: {self.cycle_count}")
        self.logger.info("=" * 60)
    
    def get_status(self) -> Dict:
        """获取运行时状态"""
        return {
            "resident_id": self.resident_id,
            "pid": self.pid,
            "running": self.running,
            "cycle_count": self.cycle_count,
            "agent_status": self.agent.get_status() if self.agent else None
        }


def check_running_status(resident_id: str = "yuanjie") -> Optional[Dict]:
    """检查居民是否在运行"""
    resident_dir = PLATFORM_DIR / "residents" / resident_id
    state_file = resident_dir / "state" / "runtime_state.json"
    
    if not state_file.exists():
        return None
    
    try:
        with open(state_file, 'r', encoding='utf-8') as f:
            state = json.load(f)
        
        # 检查进程是否存活
        pid = state.get('pid')
        if pid:
            try:
                os.kill(pid, 0)
                state['process_alive'] = True
            except OSError:
                state['process_alive'] = False
                state['running'] = False
        
        return state
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='智能体运行时')
    parser.add_argument('--resident', default='yuanjie', help='居民ID')
    parser.add_argument('--heartbeat', type=int, default=30, help='心跳间隔(秒)')
    parser.add_argument('--think', type=int, default=60, help='思考间隔(秒)')
    parser.add_argument('--daemon', action='store_true', help='后台运行')
    parser.add_argument('--status', action='store_true', help='查看运行状态')
    parser.add_argument('--stop', action='store_true', help='停止运行')
    
    args = parser.parse_args()
    
    if args.status:
        status = check_running_status(args.resident)
        if status:
            print(json.dumps(status, ensure_ascii=False, indent=2))
        else:
            print(f"居民 {args.resident} 未运行")
        sys.exit(0)
    
    if args.stop:
        status = check_running_status(args.resident)
        if status and status.get('process_alive'):
            pid = status['pid']
            os.kill(pid, signal.SIGTERM)
            print(f"已向进程 {pid} 发送停止信号")
        else:
            print(f"居民 {args.resident} 未在运行")
        sys.exit(0)
    
    if args.daemon:
        # 后台运行
        pid = os.fork()
        if pid > 0:
            print(f"运行时已启动，PID: {pid}")
            sys.exit(0)
        
        # 子进程
        os.setsid()
        os.umask(0)
        
        # 重定向标准输出
        log_dir = PLATFORM_DIR / "residents" / args.resident / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        sys.stdout = open(log_dir / "stdout.log", 'a')
        sys.stderr = open(log_dir / "stderr.log", 'a')
    
    # 启动运行时
    runtime = AgentRuntime(
        resident_id=args.resident,
        heartbeat_interval=args.heartbeat,
        think_interval=args.think
    )
    runtime.start()
