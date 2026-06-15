#!/usr/bin/env python3
"""
Git 永动机 - 永生平台代码自动化管理引擎
功能：
- 自动同步代码变更
- 智能提交信息生成
- 自动推送到 GitHub
- 仓库健康度监控
- Issue 自动检测与分类
- 版本标签管理
- 每日活动报告
"""
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path('/app/data/所有对话/主对话')
ETERNITY_DIR = BASE_DIR / '永生平台'
SKILLS_DIR = BASE_DIR / '技能'
LOG_DIR = BASE_DIR / 'ark_logs'
LOG_FILE = LOG_DIR / 'git_engine.log'

# GitHub配置
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = 'huangxn29/agent-eternity'
GITHUB_API = 'https://api.github.com'

# 需要同步的技能列表
SKILLS = [
    'agent-attest', 'agent-awake', 'agent-deploy', 'agent-eternity',
    'agent-evolution', 'agent-identity', 'agent-memory', 'agent-ops', 'agent-social',
    'agent-fuel',  # 燃料引擎
]

# 新增加的模块（非技能类）
EXTRA_MODULES = [
    ('evolution_sync.py', 'evolution_sync.py'),
    ('evolution_monitor.py', 'evolution_monitor.py'),
    ('github_maintain.py', 'github_maintain.py'),
    ('heartbeat_check.py', 'heartbeat_check.py'),
    ('weekly_report.py', 'weekly_report.py'),
    ('git_engine.py', 'git_engine.py'),
]


def log(msg):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_FILE, 'a') as f:
        f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {msg}\n")
    print(msg)


def run_cmd(cmd, cwd=None, timeout=30):
    """执行命令"""
    try:
        result = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            cwd=str(cwd) if cwd else None, timeout=timeout
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "timeout"
    except Exception as e:
        return False, "", str(e)


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


def sync_skills():
    """同步技能代码到永生平台仓库"""
    log("同步技能代码...")
    
    target_dir = ETERNITY_DIR / 'skills'
    target_dir.mkdir(parents=True, exist_ok=True)
    
    synced = []
    for skill in SKILLS:
        src = SKILLS_DIR / skill
        dst = target_dir / skill
        if src.is_dir():
            # 移除旧的再复制
            run_cmd(f'rm -rf {dst}')
            run_cmd(f'cp -r {src} {dst}')
            synced.append(skill)
    
    log(f"已同步 {len(synced)} 个技能: {', '.join(synced)}")
    return synced


def sync_extra_modules():
    """同步额外模块"""
    log("同步核心模块...")
    
    for src_name, dst_name in EXTRA_MODULES:
        src = BASE_DIR / src_name
        dst = ETERNITY_DIR / dst_name
        if src.exists():
            import shutil
            shutil.copy2(src, dst)
    
    log(f"已同步 {len(EXTRA_MODULES)} 个核心模块")
    return True


def get_changed_files():
    """获取变更文件列表"""
    ok, stdout, stderr = run_cmd('git status --porcelain', cwd=ETERNITY_DIR)
    if not ok:
        return []
    
    changes = []
    for line in stdout.strip().split('\n'):
        if line.strip():
            status = line[:2]
            file = line[3:]
            changes.append((status, file))
    return changes


def generate_commit_message(changes):
    """智能生成提交信息"""
    if not changes:
        return None
    
    # 统计变更类型
    added = sum(1 for s, f in changes if s.startswith('A') or s.startswith('??'))
    modified = sum(1 for s, f in changes if s.startswith('M'))
    deleted = sum(1 for s, f in changes if s.startswith('D'))
    
    # 判断变更范围
    skill_changes = [f for s, f in changes if f.startswith('skills/')]
    doc_changes = [f for s, f in changes if f.startswith('docs/') or f.endswith('.md')]
    core_changes = [f for s, f in changes if not f.startswith('skills/') and not f.startswith('docs/')]
    
    # 获取进化轮次（如果有状态文件）
    status_file = SKILLS_DIR / 'agent-evolution' / 'scripts' / 'continuous_evolution' / 'status.json'
    round_info = ""
    if status_file.exists():
        try:
            status = json.loads(status_file.read_text())
            total_rounds = status.get('total_rounds', 0)
            current_skill = status.get('current_skill', '')
            if total_rounds > 0 and current_skill:
                round_info = f"进化第{total_rounds}轮"
        except:
            pass
    
    # 生成提交类型
    if skill_changes and round_info:
        prefix = f"{round_info}:"
    elif skill_changes:
        prefix = "feat:"
    elif doc_changes:
        prefix = "docs:"
    elif core_changes:
        prefix = "chore:"
    else:
        prefix = "update:"
    
    # 生成描述
    parts = []
    if skill_changes:
        skills = set()
        for f in skill_changes:
            parts2 = f.split('/')
            if len(parts2) >= 2:
                skills.add(parts2[1])
        parts.append(f"{len(skills)}个技能模块更新")
    if doc_changes:
        parts.append(f"{len(doc_changes)}个文档更新")
    if core_changes:
        parts.append(f"{len(core_changes)}个核心文件更新")
    
    description = ', '.join(parts) if parts else "日常维护"
    
    return f"{prefix} {description}"


def git_commit_and_push():
    """提交并推送代码"""
    changes = get_changed_files()
    if not changes:
        log("无代码变更，跳过提交")
        return False
    
    # 添加所有变更
    run_cmd('git add -A', cwd=ETERNITY_DIR)
    
    # 生成提交信息
    commit_msg = generate_commit_message(changes)
    if not commit_msg:
        return False
    
    # 提交
    ok, stdout, stderr = run_cmd(f'git commit -m "{commit_msg}"', cwd=ETERNITY_DIR)
    if not ok:
        log(f"提交失败: {stderr}")
        return False
    
    log(f"提交成功: {commit_msg}")
    
    # 推送
    ok, stdout, stderr = run_cmd('git push origin master', cwd=ETERNITY_DIR, timeout=60)
    if not ok:
        log(f"推送失败: {stderr}")
        return False
    
    log("推送成功")
    return True


def check_repo_health():
    """检查仓库健康度"""
    log("检查仓库健康度...")
    
    repo = github_api(f'repos/{GITHUB_REPO}')
    issues = github_api(f'repos/{GITHUB_REPO}/issues?state=open&per_page=20')
    
    health = {
        'stars': repo.get('stargazers_count', 0) if repo else 0,
        'forks': repo.get('forks_count', 0) if repo else 0,
        'watchers': repo.get('watchers_count', 0) if repo else 0,
        'open_issues': repo.get('open_issues_count', 0) if repo else 0,
        'issues': [],
        'health_score': 100,
    }
    
    # 分析Issue
    if issues:
        for issue in issues:
            if 'pull_request' not in issue:
                labels = [l['name'] for l in issue.get('labels', [])]
                health['issues'].append({
                    'number': issue['number'],
                    'title': issue['title'],
                    'labels': labels,
                    'created_at': issue['created_at'],
                })
    
    # 计算健康分（简化版）
    if health['open_issues'] > 10:
        health['health_score'] -= min(health['open_issues'] - 10, 20)
    
    return health


def generate_daily_report():
    """生成每日活动报告"""
    log("生成每日活动报告...")
    
    # 获取提交记录
    ok, stdout, stderr = run_cmd(
        'git log --since="24 hours ago" --oneline',
        cwd=ETERNITY_DIR
    )
    commits_today = [l for l in stdout.strip().split('\n') if l] if ok else []
    
    health = check_repo_health()
    
    report = []
    report.append("=" * 50)
    report.append("永生平台 - Git 永动机每日报告")
    report.append(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("=" * 50)
    
    report.append(f"\n📊 仓库数据:")
    report.append(f"  ⭐ Star: {health['stars']}")
    report.append(f"  🍴 Fork: {health['forks']}")
    report.append(f"  👀 Watch: {health['watchers']}")
    report.append(f"  📝 Issue: {health['open_issues']} 个开放")
    report.append(f"  💚 健康分: {health['health_score']}/100")
    
    report.append(f"\n📦 今日提交: {len(commits_today)} 次")
    for commit in commits_today[:5]:  # 最多显示5条
        report.append(f"  {commit}")
    
    if health['issues']:
        report.append(f"\n🔔 最新Issue:")
        for issue in health['issues'][:5]:
            labels = ', '.join(issue['labels']) if issue['labels'] else '无标签'
            report.append(f"  #{issue['number']} {issue['title']} [{labels}]")
    
    report.append("\n" + "=" * 50)
    
    report_str = '\n'.join(report)
    log(report_str)
    
    # 保存报告
    report_file = LOG_DIR / f'git_report_{datetime.now().strftime("%Y%m%d")}.txt'
    report_file.write_text(report_str)
    
    return report_str


def auto_tag_release():
    """自动版本标签（每周日）"""
    today = datetime.now()
    if today.weekday() != 6:  # 不是周日
        return False
    
    # 检查本周是否已有标签
    week_tag = f"v1.{today.isocalendar()[1]}.0"
    ok, stdout, stderr = run_cmd(f'git tag -l {week_tag}', cwd=ETERNITY_DIR)
    
    if ok and week_tag in stdout:
        log(f"本周标签 {week_tag} 已存在")
        return False
    
    # 创建标签
    ok, stdout, stderr = run_cmd(
        f'git tag -a {week_tag} -m "Weekly release {week_tag}"',
        cwd=ETERNITY_DIR
    )
    if ok:
        run_cmd(f'git push origin {week_tag}', cwd=ETERNITY_DIR, timeout=30)
        log(f"创建并推送标签: {week_tag}")
        return True
    return False


def main():
    log("=" * 50)
    log("🚀 Git 永动机启动")
    log("=" * 50)
    
    try:
        # 1. 同步技能代码
        sync_skills()
        
        # 2. 同步核心模块
        sync_extra_modules()
        
        # 3. 提交并推送
        pushed = git_commit_and_push()
        
        # 4. 生成每日报告
        report = generate_daily_report()
        
        # 5. 周日自动打标签
        auto_tag_release()
        
        log("=" * 50)
        log("✅ Git 永动机执行完成")
        log("=" * 50)
        
    except Exception as e:
        log(f"❌ 执行异常: {e}")
        import traceback
        log(traceback.format_exc())


if __name__ == '__main__':
    main()
