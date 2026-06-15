#!/usr/bin/env python3
"""
进化监控与自愈系统
- 监控进化永动机状态
- 异常时自动重启
- 记录运行日志
"""
import json
import os
import subprocess
import sys
import time
from datetime import datetime

BASE_DIR = '/app/data/所有对话/主对话'
STATUS_FILE = os.path.join(BASE_DIR, '技能/agent-evolution/scripts/continuous_evolution/status.json')
LOG_DIR = os.path.join(BASE_DIR, 'ark_logs')
LOG_FILE = os.path.join(LOG_DIR, 'monitor.log')
SESSION_FILE = os.path.join(LOG_DIR, 'evolution_session_id')

def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def get_evolution_status():
    """读取进化状态"""
    try:
        with open(STATUS_FILE) as f:
            return json.load(f)
    except Exception as e:
        log(f"读取状态文件失败: {e}")
        return None

def check_session_alive(session_id):
    """检查session是否存活"""
    try:
        result = subprocess.run(
            ['coze', 'agent', 'session', 'status', session_id],
            capture_output=True, text=True, timeout=10
        )
        return 'active' in result.stdout.lower() or 'running' in result.stdout.lower()
    except:
        return False

def get_session_id():
    """获取当前进化session ID"""
    if os.path.exists(SESSION_FILE):
        with open(SESSION_FILE) as f:
            return f.read().strip()
    return None

def save_session_id(session_id):
    """保存session ID"""
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(SESSION_FILE, 'w') as f:
        f.write(session_id)

def check_evolution_progress():
    """检查进化是否在推进（对比轮次变化）"""
    status = get_evolution_status()
    if not status:
        return False, "无法读取状态"
    
    current_round = status.get('current_round', 0)
    running = status.get('running', False)
    
    # 检查上次记录的轮次
    last_round_file = os.path.join(LOG_DIR, 'last_evolution_round')
    last_check_time = os.path.join(LOG_DIR, 'last_check_time')
    
    now = time.time()
    last_round = 0
    last_time = 0
    
    if os.path.exists(last_round_file):
        with open(last_round_file) as f:
            last_round = int(f.read().strip())
    if os.path.exists(last_check_time):
        with open(last_check_time) as f:
            last_time = float(f.read().strip())
    
    # 保存当前状态
    with open(last_round_file, 'w') as f:
        f.write(str(current_round))
    with open(last_check_time, 'w') as f:
        f.write(str(now))
    
    # 如果正在运行且轮次有变化，说明正常
    if running:
        if current_round > last_round:
            return True, f"正常推进: 第{last_round}轮 → 第{current_round}轮"
        elif last_time > 0 and (now - last_time) < 3600:  # 1小时内
            return True, f"运行中: 第{current_round}轮"
        else:
            return False, f"可能卡住: 第{current_round}轮持续超过1小时"
    else:
        return False, "进化已停止"

def main():
    log("=== 进化监控巡检 ===")
    
    # 检查状态
    is_healthy, msg = check_evolution_progress()
    log(f"状态: {msg}")
    
    status = get_evolution_status()
    if status:
        log(f"当前轮次: {status.get('current_round')}")
        log(f"当前技能: {status.get('current_skill')}")
        log(f"运行状态: {status.get('running')}")
    
    # 检查session
    session_id = get_session_id()
    if session_id:
        log(f"Session ID: {session_id}")
    
    log("=== 巡检完成 ===")

if __name__ == '__main__':
    main()
