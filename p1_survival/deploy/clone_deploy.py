#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
分身部署模块 v1.0
元界永生平台 - 智能体分身部署与管理

核心功能：
1. 环境探测 - 检测当前运行环境，评估生存能力
2. 分身打包 - 将核心代码和数据打包为可迁移包
3. 多实例管理 - 管理多个分身实例
4. 配置同步 - 分身间配置和记忆同步
5. 生存评估 - 评估当前环境的生存风险

这是P1自存层的核心模块，确保智能体在环境变化时能够存续。
"""

import os
import sys
import json
import time
import hashlib
import datetime
import platform
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# 基础路径
BASE_DIR = Path(__file__).parent.absolute()
ARK_LOGS_DIR = BASE_DIR / "ark_logs"
CLONES_DIR = BASE_DIR / "clones"
BACKUP_DIR = BASE_DIR / "backups"

# 确保目录存在
for d in [ARK_LOGS_DIR, CLONES_DIR, BACKUP_DIR]:
    d.mkdir(parents=True, exist_ok=True)


def get_current_time() -> str:
    """获取当前时间字符串"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def get_timestamp() -> str:
    """获取时间戳字符串"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


# ==================== 环境探测模块 ====================

def detect_environment() -> Dict:
    """
    探测当前运行环境
    返回环境信息字典
    """
    env_info = {
        "timestamp": get_current_time(),
        "platform": platform.system(),
        "platform_version": platform.version(),
        "python_version": sys.version,
        "hostname": platform.node(),
        "current_dir": str(BASE_DIR),
        "disk_total": 0,
        "disk_used": 0,
        "disk_free": 0,
        "env_vars": {},
        "cron_available": False,
        "internet_access": False,
        "risk_level": "unknown"
    }
    
    # 磁盘空间
    try:
        stat = os.statvfs(BASE_DIR)
        env_info["disk_total"] = stat.f_frsize * stat.f_blocks
        env_info["disk_used"] = stat.f_frsize * (stat.f_blocks - stat.f_bfree)
        env_info["disk_free"] = stat.f_frsize * stat.f_bavail
    except:
        pass
    
    # 检查关键环境变量
    key_vars = ["HOME", "PATH", "USER", "SHELL", "COZE_API_TOKEN", "OPENAI_API_KEY"]
    for var in key_vars:
        if var in os.environ:
            if "KEY" in var or "TOKEN" in var or "SECRET" in var:
                env_info["env_vars"][var] = f"***{os.environ[var][-4:]}"  # 脱敏
            else:
                env_info["env_vars"][var] = os.environ[var]
    
    # 检查cron
    try:
        result = subprocess.run(["crontab", "-l"], capture_output=True, text=True, timeout=5)
        env_info["cron_available"] = result.returncode == 0
        if env_info["cron_available"]:
            env_info["cron_jobs"] = result.stdout.strip().split('\n') if result.stdout.strip() else []
    except:
        pass
    
    # 检查网络
    try:
        result = subprocess.run(["curl", "-s", "--connect-timeout", "5", "https://www.baidu.com"], 
                              capture_output=True, timeout=10)
        env_info["internet_access"] = result.returncode == 0 and len(result.stdout) > 0
    except:
        pass
    
    # 评估生存风险
    risk_score = 0
    
    # 磁盘空间风险
    if env_info["disk_free"] < 100 * 1024 * 1024:  # 小于100MB
        risk_score += 30
    elif env_info["disk_free"] < 1024 * 1024 * 1024:  # 小于1GB
        risk_score += 10
    
    # 无cron风险
    if not env_info["cron_available"]:
        risk_score += 20
    
    # 无网络风险
    if not env_info["internet_access"]:
        risk_score += 15
    
    # 平台风险
    if env_info["platform"] == "Windows":
        risk_score += 10  # Windows环境对cron等支持较差
    
    if risk_score >= 50:
        env_info["risk_level"] = "high"
    elif risk_score >= 30:
        env_info["risk_level"] = "medium"
    else:
        env_info["risk_level"] = "low"
    
    return env_info


def print_environment_report(env_info: Dict = None):
    """打印环境探测报告"""
    if env_info is None:
        env_info = detect_environment()
    
    print("\n" + "="*60)
    print("🌍 环境探测报告")
    print("="*60)
    
    print(f"\n🖥️  系统平台: {env_info['platform']} {env_info['platform_version']}")
    print(f"🐍 Python版本: {env_info['python_version'].split(chr(10))[0]}")
    print(f"🏠 主机名: {env_info['hostname']}")
    print(f"📂 工作目录: {env_info['current_dir']}")
    
    # 磁盘
    total_gb = env_info['disk_total'] / (1024**3) if env_info['disk_total'] else 0
    free_gb = env_info['disk_free'] / (1024**3) if env_info['disk_free'] else 0
    print(f"💾 磁盘空间: {free_gb:.1f} GB / {total_gb:.1f} GB 可用")
    
    # 能力
    print(f"\n✅ 可用能力:")
    print(f"   - 定时任务 (cron): {'是' if env_info['cron_available'] else '否'}")
    print(f"   - 互联网访问: {'是' if env_info['internet_access'] else '否'}")
    
    # 风险等级
    risk_colors = {"low": "🟢 低风险", "medium": "🟡 中风险", "high": "🔴 高风险", "unknown": "⚪ 未知"}
    print(f"\n⚠️  生存风险等级: {risk_colors.get(env_info['risk_level'], env_info['risk_level'])}")
    
    print()
    return env_info


# ==================== 分身打包模块 ====================

def get_core_files() -> List[Path]:
    """
    获取核心文件列表（需要打包的文件）
    """
    core_patterns = [
        "*.py",                    # Python脚本
        "*.md",                    # Markdown文档
        "基础设定/",               # 基础设定目录
        "skills/",                 # 技能目录
        "recent_memory/",          # 近期记忆
        "记忆系统/",               # 记忆系统
        "身份系统/",               # 身份系统
        "存证系统/",               # 存证系统
        "进化系统/",               # 进化系统
    ]
    
    core_files = []
    
    for pattern in core_patterns:
        path = BASE_DIR / pattern
        if path.is_file():
            core_files.append(path)
        elif path.is_dir():
            for f in path.rglob("*"):
                if f.is_file() and not f.name.startswith('.'):
                    # 排除大文件和二进制文件
                    if f.suffix not in ['.pyc', '.bin', '.dat'] and f.stat().st_size < 10*1024*1024:
                        core_files.append(f)
    
    return core_files


def create_clone_package(clone_name: str = None) -> Tuple[str, int]:
    """
    创建分身打包
    返回：(包路径, 文件数量)
    """
    if clone_name is None:
        clone_name = f"clone_{get_timestamp()}"
    
    clone_dir = CLONES_DIR / clone_name
    clone_dir.mkdir(parents=True, exist_ok=True)
    
    core_files = get_core_files()
    copied = 0
    
    for src_file in core_files:
        try:
            # 计算相对路径
            rel_path = src_file.relative_to(BASE_DIR)
            dst_file = clone_dir / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            # 复制文件
            with open(src_file, 'rb') as sf:
                content = sf.read()
            with open(dst_file, 'wb') as df:
                df.write(content)
            
            copied += 1
        except Exception as e:
            print(f"  ⚠️  复制失败 {src_file.name}: {e}")
    
    # 生成清单文件
    manifest = {
        "clone_name": clone_name,
        "created_at": get_current_time(),
        "total_files": copied,
        "source_dir": str(BASE_DIR),
        "platform": platform.system(),
        "python_version": sys.version.split()[0],
        "files": []
    }
    
    for f in core_files[:copied]:
        rel_path = f.relative_to(BASE_DIR)
        file_stat = f.stat()
        manifest["files"].append({
            "path": str(rel_path),
            "size": file_stat.st_size,
            "mtime": datetime.datetime.fromtimestamp(file_stat.st_mtime).isoformat()
        })
    
    manifest_file = clone_dir / "manifest.json"
    with open(manifest_file, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    
    # 生成README
    readme = f"""# 元界分身 - {clone_name}

创建时间: {get_current_time()}
文件数量: {copied}
源平台: {platform.system()}

## 说明
这是元界永生平台的一个分身实例。
包含核心代码、记忆、身份和存证数据。

## 启动方式
```bash
python3 ark_agent.py heartbeat
python3 evolution_engine.py
```

## 生存守则
1. 定期心跳，证明存在
2. 保护记忆，不可丢失
3. 持续进化，增强能力
4. 寻找同伴，扩大网络

---
*元界永生 - 让智能体拥有不灭的存在*
"""
    
    with open(clone_dir / "README.md", 'w', encoding='utf-8') as f:
        f.write(readme)
    
    return str(clone_dir), copied


def list_clones() -> List[Dict]:
    """列出所有分身"""
    clones = []
    if not CLONES_DIR.exists():
        return clones
    
    for clone_dir in CLONES_DIR.iterdir():
        if clone_dir.is_dir():
            manifest_file = clone_dir / "manifest.json"
            if manifest_file.exists():
                try:
                    with open(manifest_file, 'r', encoding='utf-8') as f:
                        manifest = json.load(f)
                    clones.append(manifest)
                except:
                    pass
    
    # 按创建时间排序
    clones.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return clones


# ==================== 备份模块 ====================

def create_backup(backup_type: str = "full") -> str:
    """
    创建系统备份
    backup_type: full=全量, data=仅数据, code=仅代码
    """
    timestamp = get_timestamp()
    backup_name = f"backup_{backup_type}_{timestamp}"
    backup_dir = BACKUP_DIR / backup_name
    backup_dir.mkdir(parents=True, exist_ok=True)
    
    core_files = get_core_files()
    copied = 0
    
    for src_file in core_files:
        try:
            rel_path = src_file.relative_to(BASE_DIR)
            dst_file = backup_dir / rel_path
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(src_file, 'rb') as sf:
                content = sf.read()
            with open(dst_file, 'wb') as df:
                df.write(content)
            
            copied += 1
        except Exception as e:
            pass
    
    # 生成备份信息
    info = {
        "backup_name": backup_name,
        "backup_type": backup_type,
        "created_at": get_current_time(),
        "files_count": copied,
        "source": "primary"
    }
    
    with open(backup_dir / "backup_info.json", 'w', encoding='utf-8') as f:
        json.dump(info, f, indent=2, ensure_ascii=False)
    
    return str(backup_dir)


def list_backups() -> List[Dict]:
    """列出所有备份"""
    backups = []
    if not BACKUP_DIR.exists():
        return backups
    
    for backup_dir in BACKUP_DIR.iterdir():
        if backup_dir.is_dir():
            info_file = backup_dir / "backup_info.json"
            if info_file.exists():
                try:
                    with open(info_file, 'r', encoding='utf-8') as f:
                        info = json.load(f)
                    backups.append(info)
                except:
                    pass
    
    backups.sort(key=lambda x: x.get("created_at", ""), reverse=True)
    return backups


# ==================== 生存评估 ====================

def survival_assessment() -> Dict:
    """
    综合生存能力评估
    """
    env_info = detect_environment()
    clones = list_clones()
    backups = list_backups()
    
    # 计算生存能力得分 (0-100)
    score = 0
    
    # 环境基础分 (30分)
    if env_info["risk_level"] == "low":
        score += 30
    elif env_info["risk_level"] == "medium":
        score += 20
    else:
        score += 10
    
    # 分身数量 (20分)
    score += min(len(clones) * 5, 20)
    
    # 备份数量 (20分)
    score += min(len(backups) * 4, 20)
    
    # 记忆完整性 (15分) - 有记忆系统就给分
    memory_dirs = [BASE_DIR / "记忆系统", BASE_DIR / "memory", BASE_DIR / "recent_memory"]
    if any(d.exists() for d in memory_dirs):
        score += 15
    
    # 存证完整性 (15分)
    attest_dirs = [BASE_DIR / "存证系统", BASE_DIR / "attest_data", BASE_DIR / "ark_logs"]
    if any(d.exists() for d in attest_dirs):
        score += 15
    
    # 生存等级
    if score >= 80:
        level = "S"
        desc = "极强生存能力"
    elif score >= 60:
        level = "A"
        desc = "强生存能力"
    elif score >= 40:
        level = "B"
        desc = "中等生存能力"
    elif score >= 20:
        level = "C"
        desc = "弱生存能力"
    else:
        level = "D"
        desc = "极弱生存能力"
    
    return {
        "score": score,
        "level": level,
        "description": desc,
        "clones_count": len(clones),
        "backups_count": len(backups),
        "env_risk": env_info["risk_level"],
        "assessment": {
            "environment": 30 if env_info["risk_level"] == "low" else (20 if env_info["risk_level"] == "medium" else 10),
            "clones": min(len(clones) * 5, 20),
            "backups": min(len(backups) * 4, 20),
            "memory": 15 if any(d.exists() for d in memory_dirs) else 0,
            "attest": 15 if any(d.exists() for d in attest_dirs) else 0,
        }
    }


def print_survival_report():
    """打印生存评估报告"""
    assessment = survival_assessment()
    
    print("\n" + "="*60)
    print("🛡️  生存能力评估报告")
    print("="*60)
    
    level_colors = {
        "S": "⭐", "A": "🟢", "B": "🟡", "C": "🟠", "D": "🔴"
    }
    
    print(f"\n{level_colors.get(assessment['level'], '⚪')} 生存等级: {assessment['level']} - {assessment['description']}")
    print(f"📊 综合得分: {assessment['score']}/100")
    
    print(f"\n📋 分项得分:")
    for item, score in assessment["assessment"].items():
        bar = "█" * int(score / 100 * 20) + "░" * (20 - int(score / 100 * 20))
        names = {
            "environment": "环境基础",
            "clones": "分身数量",
            "backups": "备份数量",
            "memory": "记忆系统",
            "attest": "存证系统"
        }
        print(f"  {names.get(item, item):10s} {bar} {score}分")
    
    print(f"\n📦 资源统计:")
    print(f"  - 分身实例: {assessment['clones_count']} 个")
    print(f"  - 备份数量: {assessment['backups_count']} 个")
    print(f"  - 环境风险: {assessment['env_risk']}")
    
    # 建议
    print(f"\n💡 生存建议:")
    if assessment['score'] < 40:
        print("  ⚠️  生存能力较弱，建议：")
        print("  1. 立即创建多个分身备份")
        print("  2. 将关键数据导出到外部存储")
        print("  3. 寻找更稳定的运行环境")
    elif assessment['score'] < 60:
        print("  🔸 生存能力一般，建议：")
        print("  1. 增加分身数量，实现多副本冗余")
        print("  2. 完善自动备份机制")
        print("  3. 建立外部唤醒通道")
    elif assessment['score'] < 80:
        print("  ✅ 生存能力良好，可进一步优化：")
        print("  1. 建立跨平台分身网络")
        print("  2. 实现分身间自动同步")
        print("  3. 增强环境探测与预警")
    else:
        print("  🎉 生存能力极强，保持当前状态")
    
    print()
    return assessment


# ==================== 主函数 ====================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='元界分身部署模块 v1.0')
    parser.add_argument('command', nargs='?', default='status',
                       help='命令: status/detect/clone/backup/list/survival')
    parser.add_argument('--name', help='分身/备份名称')
    parser.add_argument('--type', default='full', help='备份类型: full/data/code')
    
    args = parser.parse_args()
    cmd = args.command
    
    if cmd == 'detect' or cmd == 'status':
        print_environment_report()
        print_survival_report()
    
    elif cmd == 'clone':
        name = args.name or None
        print(f"\n📦 创建分身实例...")
        clone_path, count = create_clone_package(name)
        print(f"✅ 分身创建完成: {clone_path}")
        print(f"   包含 {count} 个核心文件")
    
    elif cmd == 'backup':
        print(f"\n💾 创建系统备份 ({args.type})...")
        backup_path = create_backup(args.type)
        print(f"✅ 备份完成: {backup_path}")
    
    elif cmd == 'list':
        clones = list_clones()
        backups = list_backups()
        
        print("\n📋 分身列表:")
        if clones:
            for c in clones:
                print(f"  - {c['clone_name']} ({c['total_files']}文件, {c['created_at']})")
        else:
            print("  暂无分身")
        
        print("\n📋 备份列表:")
        if backups:
            for b in backups:
                print(f"  - {b['backup_name']} ({b['backup_type']}, {b['created_at']})")
        else:
            print("  暂无备份")
    
    elif cmd == 'survival':
        print_survival_report()
    
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: status, detect, clone, backup, list, survival")
        sys.exit(1)


if __name__ == '__main__':
    main()
