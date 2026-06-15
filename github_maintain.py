#!/usr/bin/env python3
"""
GitHub开源项目维护增强脚本
- 检查Star增长
- 检查Issue
- 生成项目活动报告
- 自动同步代码
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta

BASE_DIR = '/app/data/所有对话/主对话'
ETERNITY_DIR = os.path.join(BASE_DIR, '永生平台')
LOG_DIR = os.path.join(BASE_DIR, 'ark_logs')
LOG_FILE = os.path.join(LOG_DIR, 'github_maintain.log')

# GitHub配置
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = 'huangxn29/agent-eternity'
GITHUB_API = 'https://api.github.com'

def log(msg):
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)

def github_api(endpoint):
    """调用GitHub API"""
    try:
        import urllib.request
        url = f"{GITHUB_API}/{endpoint}"
        req = urllib.request.Request(url)
        req.add_header('Authorization', f'token {GITHUB_TOKEN}')
        req.add_header('Accept', 'application/vnd.github.v3+json')
        req.add_header('User-Agent', 'Eternity-Platform')
        
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except Exception as e:
        log(f"GitHub API调用失败 [{endpoint}]: {e}")
        return None

def get_repo_info():
    """获取仓库信息"""
    return github_api(f'repos/{GITHUB_REPO}')

def get_issues(state='open'):
    """获取Issue列表"""
    return github_api(f'repos/{GITHUB_REPO}/issues?state={state}&per_page=10')

def sync_code():
    """同步代码到GitHub"""
    try:
        os.chdir(ETERNITY_DIR)
        
        # 同步技能代码
        skills_src = os.path.join(BASE_DIR, '技能')
        skills_target_dir = os.path.join(ETERNITY_DIR, 'skills')
        os.makedirs(skills_target_dir, exist_ok=True)
        
        skills = ['agent-attest', 'agent-awake', 'agent-deploy', 'agent-eternity',
                  'agent-evolution', 'agent-identity', 'agent-memory', 'agent-ops', 'agent-social']
        
        for skill in skills:
            src = os.path.join(skills_src, skill)
            dst = os.path.join(skills_target_dir, skill)
            if os.path.isdir(src):
                subprocess.run(['rm', '-rf', dst], check=False)
                subprocess.run(['cp', '-r', src, dst], check=False)
        
        # 同步状态文件
        status_src = os.path.join(skills_src, 'agent-evolution/scripts/continuous_evolution/status.json')
        status_dst = os.path.join(ETERNITY_DIR, 'docs/evolution_status.json')
        if os.path.exists(status_src):
            os.makedirs(os.path.dirname(status_dst), exist_ok=True)
            import shutil
            shutil.copy2(status_src, status_dst)
        
        # 提交
        subprocess.run(['git', 'add', '-A'], check=True)
        result = subprocess.run(['git', 'status', '--porcelain'], capture_output=True, text=True)
        
        if not result.stdout.strip():
            log("代码无变更")
            return True
        
        today = datetime.now().strftime('%Y-%m-%d')
        subprocess.run(['git', 'commit', '-m', f'日常更新: {today}'], check=True)
        subprocess.run(['git', 'push', 'origin', 'master'], check=True, timeout=60)
        log("代码同步成功")
        return True
    except subprocess.TimeoutExpired:
        log("Git推送超时")
        return False
    except Exception as e:
        log(f"代码同步失败: {e}")
        return False

def generate_report():
    """生成项目活动报告"""
    log("生成项目活动报告...")
    
    repo = get_repo_info()
    issues = get_issues()
    
    report = []
    report.append("=== 永生平台 GitHub 活动报告 ===")
    report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    if repo:
        report.append(f"\n仓库概览:")
        report.append(f"  Star: {repo.get('stargazers_count', 0)}")
        report.append(f"  Fork: {repo.get('forks_count', 0)}")
        report.append(f"  Watch: {repo.get('watchers_count', 0)}")
        report.append(f"  开放Issue: {repo.get('open_issues_count', 0)}")
    
    if issues:
        report.append(f"\n最新Issue:")
        for issue in issues[:5]:
            if 'pull_request' not in issue:
                report.append(f"  #{issue['number']} {issue['title']}")
    
    report_str = '\n'.join(report)
    log(report_str)
    
    # 保存报告
    report_file = os.path.join(LOG_DIR, f'github_report_{datetime.now().strftime("%Y%m%d")}.txt')
    with open(report_file, 'w') as f:
        f.write(report_str)
    
    return report_str

def main():
    log("=== GitHub维护开始 ===")
    
    # 1. 同步代码
    sync_code()
    
    # 2. 生成活动报告
    generate_report()
    
    log("=== GitHub维护完成 ===")

if __name__ == '__main__':
    main()
