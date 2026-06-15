#!/usr/bin/env python3
"""
进化同步流水线 - 每轮进化后自动同步代码到GitHub并更新状态
"""
import json
import os
import subprocess
import sys
from datetime import datetime

BASE_DIR = '/app/data/所有对话/主对话'
SKILLS_DIR = os.path.join(BASE_DIR, '技能')
ETERNITY_DIR = os.path.join(BASE_DIR, '永生平台')
STATUS_FILE = os.path.join(SKILLS_DIR, 'agent-evolution/scripts/continuous_evolution/status.json')
LOG_FILE = os.path.join(BASE_DIR, 'ark_logs/evolution_sync.log')

def log(msg):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def sync_skills_to_eternity():
    """同步技能代码到永生平台仓库"""
    skills_dest = os.path.join(ETERNITY_DIR, 'skills')
    os.makedirs(skills_dest, exist_ok=True)
    
    skills = ['agent-attest', 'agent-awake', 'agent-deploy', 'agent-eternity', 
              'agent-evolution', 'agent-identity', 'agent-memory', 'agent-ops', 'agent-social']
    
    for skill in skills:
        src = os.path.join(SKILLS_DIR, skill)
        dst = os.path.join(skills_dest, skill)
        if os.path.isdir(src):
            subprocess.run(['rm', '-rf', dst], check=False)
            subprocess.run(['cp', '-r', src, dst], check=False)
            log(f"同步技能: {skill}")

def get_current_round():
    """获取当前进化轮次"""
    try:
        with open(STATUS_FILE) as f:
            status = json.load(f)
        return status.get('current_round', 0), status.get('total_rounds', 0)
    except:
        return 0, 0

def git_commit_and_push():
    """提交并推送到GitHub"""
    try:
        os.chdir(ETERNITY_DIR)
        subprocess.run(['git', 'add', '-A'], check=True)
        current_round, total_rounds = get_current_round()
        
        # 检查是否有变更
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        if not result.stdout.strip():
            log("代码无变更，跳过提交")
            return False
        
        commit_msg = f"进化第{total_rounds}轮: 多智能体平台能力升级"
        subprocess.run(['git', 'commit', '-m', commit_msg], check=True)
        subprocess.run(['git', 'push', 'origin', 'master'], check=True, timeout=60)
        log(f"GitHub同步成功: {commit_msg}")
        return True
    except subprocess.TimeoutExpired:
        log("GitHub推送超时")
        return False
    except Exception as e:
        log(f"GitHub同步失败: {e}")
        return False

def main():
    log("=== 进化同步流水线启动 ===")
    
    # 同步技能代码
    sync_skills_to_eternity()
    
    # 同步状态文件
    status_dest = os.path.join(ETERNITY_DIR, 'docs/evolution_status.json')
    if os.path.exists(STATUS_FILE):
        os.makedirs(os.path.dirname(status_dest), exist_ok=True)
        import shutil
        shutil.copy2(STATUS_FILE, status_dest)
        log("同步进化状态文件")
    
    # 提交到GitHub
    git_commit_and_push()
    
    log("=== 进化同步流水线完成 ===")

if __name__ == '__main__':
    main()
