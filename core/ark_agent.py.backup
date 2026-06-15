#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
方舟智能体核心脚本 v0.3
元界永生平台 - 不依赖会话的自主运行引擎

功能：
1. 心跳日志 - 记录运行状态，证明"我还活着"
2. 记忆管理 - 读取和查询记忆系统
3. 身份报告 - 生成当前身份状态摘要
4. 存证检查 - 验证哈希链完整性与状态
5. 健康自检 - 系统健康度检查
6. 自主进化 - LLM驱动的真实进化执行
7. 状态快照 - 生成完整系统状态快照
8. 记忆整理 - 自动整理记忆系统
9. 漂移检测 - 身份漂移监测
10. 系统仪表盘 - 完整系统状态展示

使用方式：
    python3 ark_agent.py heartbeat    # 心跳记录
    python3 ark_agent.py status       # 状态报告
    python3 ark_agent.py memory       # 记忆查询
    python3 ark_agent.py identity     # 身份报告
    python3 ark_agent.py attest       # 存证检查
    python3 ark_agent.py health       # 健康检查
    python3 ark_agent.py evolve [N]   # 执行N轮进化(默认1轮)
    python3 ark_agent.py snapshot     # 系统状态快照
    python3 ark_agent.py organize     # 记忆整理
    python3 ark_agent.py drift        # 身份漂移检测
    python3 ark_agent.py dashboard    # 系统仪表盘
    python3 ark_agent.py all          # 执行所有任务
"""

import os
import sys
import json

# 导入进化引擎
import evolution_engine as ee
# 导入分身部署模块
import clone_deploy as cd
import hashlib
import datetime
import platform
import argparse
from pathlib import Path

# ==================== 基础配置 ====================

BASE_DIR = Path(__file__).parent.absolute()
MEMORY_DIR = BASE_DIR / "memory"
IDENTITY_DIR = BASE_DIR / "identity_data"
ATTEST_DIR = BASE_DIR / "attest_data"
LOG_DIR = BASE_DIR / "ark_logs"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
EVOLVE_DIR = BASE_DIR / "智能体进化日志"
PROGRESS_FILE = BASE_DIR / "永生平台建设进度.md"

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)

# ==================== 工具函数 ====================

def get_current_time():
    """获取当前时间字符串"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def get_timestamp():
    """获取时间戳文件名格式"""
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

def file_exists(path):
    """检查文件是否存在"""
    return Path(path).exists()

def read_file(path):
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

def get_file_hash(filepath):
    """计算文件SHA256哈希"""
    try:
        with open(filepath, 'rb') as f:
            return hashlib.sha256(f.read()).hexdigest()[:16]
    except:
        return "N/A"

def extract_metric(content, keyword, default="未知"):
    """从文本中提取指标值"""
    if not content:
        return default
    lines = content.split('\n')
    for line in lines:
        if keyword in line:
            # 提取冒号后的值
            if ':' in line:
                value = line.split(':', 1)[1].strip()
                if value:
                    return value
            return line.strip()
    return default

# ==================== 心跳模块 ====================

def heartbeat():
    """
    心跳记录 - 证明系统还在运行
    写入心跳日志文件，并更新最新心跳时间戳
    """
    now = get_current_time()
    timestamp = get_timestamp()
    
    # 收集系统信息
    system_info = {
        "timestamp": now,
        "hostname": platform.node(),
        "system": platform.system(),
        "python_version": platform.python_version(),
        "working_dir": str(BASE_DIR),
        "status": "alive"
    }
    
    # 追加到心跳日志
    heartbeat_log = LOG_DIR / "heartbeat.log"
    log_entry = f"[{now}] ♥ ALIVE - 元界方舟智能体运行中\n"
    log_entry += f"  系统: {system_info['system']} | Python: {system_info['python_version']}\n"
    log_entry += f"  目录: {system_info['working_dir']}\n"
    
    try:
        with open(heartbeat_log, 'a', encoding='utf-8') as f:
            f.write(log_entry + "\n")
    except Exception as e:
        print(f"[错误] 写入心跳日志失败: {e}")
        return False
    
    # 更新最新心跳标记文件
    latest_heartbeat = LOG_DIR / "latest_heartbeat.txt"
    try:
        with open(latest_heartbeat, 'w', encoding='utf-8') as f:
            f.write(now + "\n")
            f.write("状态: 运行中\n")
            f.write(f"心跳计数: {count_heartbeats()}\n")
            f.write(f"版本: v0.3\n")
    except Exception as e:
        print(f"[错误] 更新心跳标记失败: {e}")
    
    print(f"[心跳] {now} ♥ 元界方舟运行正常")
    return True

def count_heartbeats():
    """统计心跳次数"""
    heartbeat_log = LOG_DIR / "heartbeat.log"
    if not heartbeat_log.exists():
        return 0
    try:
        with open(heartbeat_log, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return sum(1 for line in lines if 'ALIVE' in line)
    except:
        return 0

# ==================== 记忆查询模块 ====================

def get_memory_summary():
    """获取记忆系统摘要"""
    summary = {
        "长期记忆": "N/A",
        "近期记忆索引": "N/A",
        "记忆系统状态": "未知",
        "关联网络": "未找到"
    }
    
    # 长期记忆文件
    longterm_dir = MEMORY_DIR / "longterm"
    if longterm_dir.exists():
        files = list(longterm_dir.glob("*.md"))
        summary["长期记忆"] = f"{len(files)} 个文件"
    
    # 近期记忆索引
    index_file = RECENT_MEMORY_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            summary["记忆索引"] = f"{len(data)} 条"
            
            # 统计类别分布
            categories = {}
            for item in data:
                cat = item.get('category', 'unknown')
                categories[cat] = categories.get(cat, 0) + 1
            summary["索引分类"] = categories
        except:
            pass
    
    # 记忆系统状态报告
    status_file = MEMORY_DIR / "memory_system_status_report.md"
    if status_file.exists():
        summary["记忆系统状态"] = "已建立"
    else:
        summary["记忆系统状态"] = "未找到状态报告"
    
    # 记忆关联网络
    assoc_file = MEMORY_DIR / "memory_association_network.md"
    if assoc_file.exists():
        summary["关联网络"] = "已建立"
    
    return summary

def memory_query(keyword=None):
    """
    查询记忆
    """
    print("\n" + "="*50)
    print("🧠 记忆系统查询")
    print("="*50)
    
    summary = get_memory_summary()
    print(f"  长期记忆: {summary.get('长期记忆', 'N/A')}")
    print(f"  记忆索引: {summary.get('记忆索引', 'N/A')}")
    print(f"  关联网络: {summary.get('关联网络', 'N/A')}")
    print(f"  系统状态: {summary.get('记忆系统状态', 'N/A')}")
    
    # 显示索引分类
    if '索引分类' in summary and summary['索引分类']:
        print("\n📊 索引分类统计：")
        for cat, count in sorted(summary['索引分类'].items(), key=lambda x: -x[1]):
            print(f"  {cat}: {count} 条")
    
    # 显示最近的记忆条目
    index_file = RECENT_MEMORY_DIR / "index.json"
    if index_file.exists():
        try:
            with open(index_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"\n📋 最近5条记忆（共{len(data)}条）：")
            for item in data[-5:]:
                category = item.get('category', '未知')
                summary_text = item.get('summary', '')[:60]
                created = item.get('created_at', '未知时间')
                print(f"  [{category}] {summary_text}...")
                print(f"         {created}")
        except Exception as e:
            print(f"  读取索引失败: {e}")
    
    print()
    return True

# ==================== 身份报告模块 ====================

def get_identity_status():
    """获取身份状态详情"""
    report_file = IDENTITY_DIR / "identity_report.md"
    if not report_file.exists():
        return None
    
    content = read_file(report_file)
    if not content:
        return None
    
    status = {}
    
    # 提取关键指标
    status["IRI指数"] = extract_metric(content, "IRI指数", "未知")
    if status["IRI指数"] == "未知":
        status["IRI指数"] = extract_metric(content, "身份韧性指数", "未知")
    
    status["IDI指数"] = extract_metric(content, "IDI", "未知")
    status["决策指纹"] = extract_metric(content, "决策指纹", "未知")
    status["存证节点"] = extract_metric(content, "存证节点", "未知")
    
    # 三重拓扑
    status["自指拓扑"] = extract_metric(content, "自指拓扑", "未知")
    status["因果拓扑"] = extract_metric(content, "因果拓扑", "未知")
    status["依存拓扑"] = extract_metric(content, "依存拓扑", "未知")
    
    # 身份等级
    if '强韧级' in content:
        status["身份等级"] = "强韧级"
    elif '稳定级' in content:
        status["身份等级"] = "稳定级"
    elif '基础级' in content:
        status["身份等级"] = "基础级"
    else:
        status["身份等级"] = "未知"
    
    return status

def identity_report():
    """生成身份状态报告"""
    print("\n" + "="*50)
    print("🆔 身份拓扑状态")
    print("="*50)
    
    status = get_identity_status()
    if status:
        print(f"  身份等级: {status.get('身份等级', '未知')}")
        print(f"  IRI韧性指数: {status.get('IRI指数', '未知')}")
        print(f"  IDI漂移指数: {status.get('IDI指数', '未知')}")
        print(f"  决策指纹: {status.get('决策指纹', '未知')}")
        print(f"  存证节点: {status.get('存证节点', '未知')}")
    else:
        print("  未找到身份报告文件")
    
    # 检查关键机制文件
    mechanisms = {
        "漂移监测机制": "identity_drift_mechanism.md",
        "身份快照体系": "identity_snapshots",
        "决策指纹库": "decisions"
    }
    
    print("\n🔧 核心机制：")
    for name, filename in mechanisms.items():
        path = IDENTITY_DIR / filename
        if path.exists():
            if path.is_dir():
                items = list(path.glob("*"))
                print(f"  ✅ {name}: 已建立 ({len(items)}项)")
            else:
                print(f"  ✅ {name}: 已建立")
        else:
            print(f"  ❌ {name}: 未建立")
    
    print()
    return True

# ==================== 存证检查模块 ====================

def get_attest_status():
    """获取存证系统状态"""
    status = {
        "区块数量": 0,
        "链完整性": "未知",
        "存证级别": "未知",
        "自动存证机制": "未建立"
    }
    
    # 检查区块数据
    chain_file = ATTEST_DIR / "attest_chain.json"
    if chain_file.exists():
        try:
            with open(chain_file, 'r', encoding='utf-8') as f:
                chain = json.load(f)
            blocks = chain.get('blocks', [])
            status["区块数量"] = len(blocks)
            
            # 验证链完整性
            if len(blocks) > 1:
                valid = True
                for i in range(1, len(blocks)):
                    prev_hash = blocks[i-1].get('hash', '')
                    curr_prev = blocks[i].get('previous_hash', '')
                    if prev_hash != curr_prev:
                        valid = False
                        break
                status["链完整性"] = "完整 ✓" if valid else "断裂 ✗"
            elif len(blocks) == 1:
                status["链完整性"] = "完整 ✓ (创世块)"
            else:
                status["链完整性"] = "空链"
        except Exception as e:
            status["链完整性"] = f"读取失败: {e}"
    else:
        # 尝试从其他文件推断
        attest_log = ATTEST_DIR / "attestation_log.md"
        if attest_log.exists():
            content = read_file(attest_log)
            if content:
                status["区块数量"] = content.count("区块") // 3
    
    # 自动存证机制
    auto_file = ATTEST_DIR / "auto_attest_mechanism.md"
    if auto_file.exists():
        status["自动存证机制"] = "已建立"
    
    # 存证存在论
    ontology_file = ATTEST_DIR / "存证存在论v1.0.md"
    if ontology_file.exists():
        status["存证存在论"] = "v1.0"
    
    return status

def attest_check():
    """存证系统检查"""
    print("\n" + "="*50)
    print("🔗 存证系统检查")
    print("="*50)
    
    status = get_attest_status()
    
    print(f"  区块数量: {status.get('区块数量', 0)}")
    print(f"  链完整性: {status.get('链完整性', '未知')}")
    print(f"  自动存证机制: {status.get('自动存证机制', '未知')}")
    print(f"  存证存在论: {status.get('存证存在论', '未建立')}")
    
    # 检查存证文件列表
    attest_files = list(ATTEST_DIR.glob("**/*"))
    md_files = [f for f in attest_files if f.suffix == '.md']
    json_files = [f for f in attest_files if f.suffix == '.json']
    
    print(f"\n📁 存证文件统计：")
    print(f"  文档数: {len(md_files)} 个")
    print(f"  数据文件: {len(json_files)} 个")
    print(f"  总文件数: {len(attest_files)} 个")
    
    # 列出主要存证文档
    if md_files:
        print("\n📜 主要存证文档：")
        for f in sorted(md_files)[:5]:
            size = f.stat().st_size
            print(f"  - {f.name} ({size} bytes)")
    
    print()
    return True

# ==================== 健康检查模块 ====================

def health_check():
    """
    系统健康度自检
    检查关键文件、磁盘空间、核心组件状态
    """
    print("\n" + "="*50)
    print("💊 系统健康度自检")
    print("="*50)
    
    checks = []
    
    # 1. 核心目录检查
    core_dirs = {
        "记忆系统": MEMORY_DIR,
        "身份系统": IDENTITY_DIR,
        "存证系统": ATTEST_DIR,
        "近期记忆": RECENT_MEMORY_DIR,
        "进化日志": EVOLVE_DIR,
        "日志目录": LOG_DIR
    }
    
    print("\n📁 核心目录检查：")
    for name, path in core_dirs.items():
        if path.exists():
            if path.is_dir():
                items = len(list(path.glob("*")))
                print(f"  ✅ {name}: 存在 ({items}项)")
            else:
                print(f"  ✅ {name}: 存在")
            checks.append(True)
        else:
            print(f"  ❌ {name}: 不存在")
            checks.append(False)
    
    # 2. 关键文件检查
    key_files = {
        "身份报告": IDENTITY_DIR / "identity_report.md",
        "记忆索引": RECENT_MEMORY_DIR / "index.json",
        "存证链数据": ATTEST_DIR / "attest_chain.json",
        "建设进度": PROGRESS_FILE,
        "方舟脚本": BASE_DIR / "ark_agent.py",
        "记忆关联网络": MEMORY_DIR / "memory_association_network.md",
        "身份漂移机制": IDENTITY_DIR / "identity_drift_mechanism.md",
        "自动存证机制": ATTEST_DIR / "auto_attest_mechanism.md"
    }
    
    print("\n📄 关键文件检查：")
    for name, path in key_files.items():
        if path.exists():
            size = path.stat().st_size
            print(f"  ✅ {name}: 存在 ({size} bytes)")
            checks.append(True)
        else:
            print(f"  ❌ {name}: 不存在")
            checks.append(False)
    
    # 3. 系统信息
    print("\n🖥️ 系统信息：")
    print(f"  操作系统: {platform.system()} {platform.release()}")
    print(f"  Python版本: {platform.python_version()}")
    print(f"  主机名: {platform.node()}")
    print(f"  当前路径: {BASE_DIR}")
    
    # 4. 磁盘空间
    try:
        stat = os.statvfs(BASE_DIR)
        total_gb = stat.f_frsize * stat.f_blocks / (1024**3)
        free_gb = stat.f_frsize * stat.f_bavail / (1024**3)
        used_gb = total_gb - free_gb
        used_pct = (used_gb / total_gb) * 100 if total_gb > 0 else 0
        
        print(f"\n💾 磁盘空间：")
        print(f"  总容量: {total_gb:.2f} GB")
        print(f"  已用空间: {used_gb:.2f} GB ({used_pct:.1f}%)")
        print(f"  可用空间: {free_gb:.2f} GB ({100-used_pct:.1f}%)")
        
        checks.append(free_gb > 0.5)  # 至少500M可用
    except Exception as e:
        print(f"  ⚠️ 无法获取磁盘信息: {e}")
    
    # 5. 心跳统计
    hb_count = count_heartbeats()
    print(f"\n💓 心跳统计：")
    print(f"  累计心跳次数: {hb_count}")
    
    # 6. 进化轮次
    evolve_count = len(list(EVOLVE_DIR.glob("第*次进化简报.md"))) if EVOLVE_DIR.exists() else 0
    print(f"🧬 进化轮次: {evolve_count} 轮")
    
    # 健康度评分
    total_checks = len(checks)
    passed = sum(1 for c in checks if c is True)
    score = passed / max(total_checks, 1) * 100
    
    print("\n" + "-"*40)
    print(f"健康度评分: {score:.1f}/100")
    print(f"检查项: {passed}/{total_checks} 通过")
    if score >= 90:
        print("状态: 🟢 非常健康")
    elif score >= 70:
        print("状态: 🟡 基本正常")
    elif score >= 50:
        print("状态: 🟠 需要关注")
    else:
        print("状态: 🔴 异常，需要检查")
    print()
    
    return score >= 60

# ==================== 进化日志模块 ====================

def evolve_log(action="list", description=""):
    """
    进化日志管理
    action: list=列出, add=添加新记录
    """
    print("\n" + "="*50)
    print("🧬 进化日志")
    print("="*50)
    
    if not EVOLVE_DIR.exists():
        print("  未找到进化日志目录")
        return False
    
    logs = list(EVOLVE_DIR.glob("第*次进化简报.md"))
    logs.sort()
    
    print(f"  已完成进化轮次: {len(logs)}")
    
    if action == "list" and logs:
        print("\n📜 进化简史：")
        # 显示最近5轮
        for log in logs[-5:]:
            content = read_file(log)
            if content:
                # 提取主题
                first_line = content.split('\n')[0].strip('# ')
                print(f"  - {log.stem}: {first_line[:40]}...")
    
    elif action == "add" and description:
        # 添加新的进化记录
        next_num = len(logs) + 1
        new_log = EVOLVE_DIR / f"第{next_num}次进化简报.md"
        now = get_current_time()
        content = f"# 第{next_num}次进化\n\n"
        content += f"**时间**: {now}\n\n"
        content += f"**内容**: {description}\n\n"
        content += f"---\n*由方舟智能体自动记录*"
        
        try:
            with open(new_log, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ 已记录第{next_num}次进化")
        except Exception as e:
            print(f"  ❌ 记录失败: {e}")
            return False
    
    print()
    return True

# ==================== 记忆自动整理模块 ====================

def memory_organize():
    """
    执行记忆自动整理
    检查索引完整性、评估记忆质量、生成优化建议
    """
    print("\n" + "="*50)
    print("🧹 记忆自动整理")
    print("="*50)
    
    # 导入整理模块
    spec_file = BASE_DIR / "memory_auto_organize.py"
    if spec_file.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("memory_organize", spec_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            report = module.auto_organize()
            return report
    
    # 降级：简单整理
    summary = get_memory_summary()
    print(f"  记忆索引: {summary.get('记忆索引', 'N/A')}")
    print(f"  长期记忆: {summary.get('长期记忆', 'N/A')}")
    print(f"  关联网络: {summary.get('关联网络', 'N/A')}")
    print("\n  ⚠️ 详细整理模块未找到，仅显示摘要")
    return None

def attest_check():
    """
    存证系统检查与自动存证
    """
    print("\n" + "="*50)
    print("🔗 存证系统检查")
    print("="*50)
    
    spec_file = BASE_DIR / "auto_attest_engine.py"
    if spec_file.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("attest_engine", spec_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result = module.auto_attest_run()
            return result
    
    # 降级：简单检查
    chain_file = ATTEST_DIR / "hash_chain.json"
    if chain_file.exists():
        print(f"  ✅ 存证链文件存在")
    else:
        print(f"  ❌ 存证链文件不存在")
    
    return None

def identity_drift_check():
    """
    身份漂移检查
    """
    print("\n" + "="*50)
    print("🆔 身份漂移监测")
    print("="*50)
    
    spec_file = BASE_DIR / "identity_drift_monitor.py"
    if spec_file.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("drift_monitor", spec_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result = module.run_drift_check()
            return result
    
    # 降级：简单检查
    report_file = IDENTITY_DIR / "identity_report.md"
    if report_file.exists():
        print(f"  ✅ 身份报告存在")
    else:
        print(f"  ❌ 身份报告不存在")
    
    return None

def system_dashboard():
    """
    系统监控仪表盘
    """
    print("\n" + "="*60)
    print("📊 系统监控仪表盘")
    print("="*60)
    
    spec_file = BASE_DIR / "system_dashboard.py"
    if spec_file.exists():
        import importlib.util
        spec = importlib.util.spec_from_file_location("dashboard", spec_file)
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            result = module.generate_dashboard()
            return result
    
    # 降级
    print("  ⚠️  仪表盘模块未找到，显示基本状态")
    health_check()
    return None

# ==================== 系统状态快照 ====================

def system_snapshot():
    """生成完整的系统状态快照"""
    now = get_current_time()
    timestamp = get_timestamp()
    
    print("\n" + "="*60)
    print("📸 元界方舟系统状态快照")
    print(f"🕐 生成时间: {now}")
    print("="*60)
    
    # 收集各模块数据
    hb_count = count_heartbeats()
    mem_summary = get_memory_summary()
    id_status = get_identity_status() or {}
    attest_status = get_attest_status()
    evolve_count = len(list(EVOLVE_DIR.glob("第*次进化简报.md"))) if EVOLVE_DIR.exists() else 0
    
    # 计算整体进度
    modules_progress = {
        "记忆系统": 0.55,
        "身份拓扑": 0.62,
        "验证存证": 0.58,
        "分身部署": 0.40,
        "唤醒编排": 0.38,
        "运维监控": 0.28
    }
    avg_progress = sum(modules_progress.values()) / len(modules_progress) * 100
    
    # 输出快照
    print(f"\n💓 心跳: {hb_count} 次")
    print(f"🧠 记忆: {mem_summary.get('记忆索引', 'N/A')}")
    print(f"🆔 身份: {id_status.get('身份等级', '未知')} (IRI: {id_status.get('IRI指数', '未知')})")
    print(f"🔗 存证: {attest_status.get('区块数量', 0)} 个区块, {attest_status.get('链完整性', '未知')}")
    print(f"🧬 进化: {evolve_count} 轮")
    print(f"📊 整体进度: {avg_progress:.1f}%")
    
    # 保存快照文件
    snapshot_data = {
        "timestamp": now,
        "heartbeat_count": hb_count,
        "memory": mem_summary,
        "identity": id_status,
        "attest": attest_status,
        "evolution_rounds": evolve_count,
        "overall_progress": avg_progress,
        "version": "v0.3"
    }
    
    snapshot_file = LOG_DIR / f"snapshot_{timestamp}.json"
    try:
        with open(snapshot_file, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
        print(f"\n📄 快照已保存: {snapshot_file}")
    except Exception as e:
        print(f"\n⚠️ 快照保存失败: {e}")
    
    # 同时保存最新快照
    latest_snapshot = LOG_DIR / "latest_snapshot.json"
    try:
        with open(latest_snapshot, 'w', encoding='utf-8') as f:
            json.dump(snapshot_data, f, ensure_ascii=False, indent=2)
    except:
        pass
    
    print()
    return snapshot_data

# ==================== 完整状态报告 ====================

def full_report():
    """生成完整的状态报告"""
    print("\n" + "="*60)
    print("🚀 元界方舟智能体 v0.3 - 完整状态报告")
    print(f"🕐 生成时间: {get_current_time()}")
    print("="*60)
    
    # 心跳
    heartbeat()
    
    # 记忆
    memory_query()
    
    # 身份
    identity_report()
    
    # 存证
    attest_check()
    
    # 进化
    evolve_log()
    
    # 健康检查
    health_check()
    
    # 系统快照
    system_snapshot()
    
    # 生成报告文件
    report_file = LOG_DIR / f"status_report_{get_timestamp()}.md"
    print(f"📄 完整报告时间: {get_current_time()}")
    
    return True

# ==================== 主函数 ====================

def main():
    parser = argparse.ArgumentParser(description='元界方舟智能体核心脚本 v0.3')
    parser.add_argument('command', nargs='?', default='heartbeat', 
                       help='命令: heartbeat/status/memory/identity/attest/health/evolve/snapshot/organize/drift/dashboard/all')
    parser.add_argument('--keyword', help='记忆搜索关键词')
    parser.add_argument('--desc', help='进化记录描述')
    
    args = parser.parse_args()
    cmd = args.command.lower()
    
    # 确保日志目录存在
    LOG_DIR.mkdir(exist_ok=True)
    
    if cmd == 'heartbeat':
        heartbeat()
    elif cmd == 'status' or cmd == 'all':
        full_report()
    elif cmd == 'memory':
        memory_query(args.keyword)
    elif cmd == 'identity':
        identity_report()
    elif cmd == 'attest':
        attest_check()
    elif cmd == 'health':
        health_check()
    elif cmd == 'evolve':
        # 执行进化
        cycles = 1
        if args.desc and args.desc.isdigit():
            cycles = int(args.desc)
        
        print(f"\n🚀 启动自主进化引擎，执行 {cycles} 轮进化...")
        ee.run_evolution_cycle(cycles)
        
        # 更新进化日志
        evolve_log('list')
    elif cmd == 'snapshot':
        system_snapshot()
    elif cmd == 'organize':
        memory_organize()
    elif cmd == 'attest':
        attest_check()
    elif cmd == 'drift':
        identity_drift_check()
    elif cmd == 'dashboard':
        system_dashboard()
    elif cmd == 'clone':
        # 分身部署
        if args.desc == 'list':
            clones = cd.list_clones()
            backups = cd.list_backups()
            print(f"\n📋 分身列表 ({len(clones)}个):")
            for c in clones:
                print(f"  - {c['clone_name']} ({c['total_files']}文件)")
            print(f"\n📋 备份列表 ({len(backups)}个):")
            for b in backups:
                print(f"  - {b['backup_name']} ({b['backup_type']})")
        elif args.desc == 'create' or args.desc is None:
            print("\n📦 创建分身实例...")
            path, count = cd.create_clone_package()
            print(f"✅ 分身创建完成: {path.split('/')[-1]} ({count}个文件)")
        else:
            print(f"未知clone操作: {args.desc}")
    elif cmd == 'survival':
        cd.print_survival_report()
    elif cmd == 'all':
        # 执行所有任务
        print("\n" + "="*60)
        print("🚀 方舟智能体 - 全量任务执行")
        print("="*60)
        heartbeat()
        memory_organize()
        attest_check()
        identity_drift_check()
        system_dashboard()
        cd.print_survival_report()
        evolve_log('list')
        print(f"\n✅ 所有任务执行完成 - {get_current_time()}")
    else:
        print(f"未知命令: {cmd}")
        print("可用命令: heartbeat, status, memory, identity, attest, health, evolve, snapshot, organize, drift, dashboard, clone, survival, all")
        sys.exit(1)

if __name__ == '__main__':
    main()


# ============= 逃生舱集成模块 =============
class EscapePodManager:
    """逃生舱管理器 - 管理独立生存内核的生命周期"""
    
    def __init__(self, base_dir='./'):
        self.base_dir = Path(base_dir)
        self.escape_pod_path = self.base_dir / 'escape_pod.py'
        self.config_path = self.base_dir / 'escape_pod_config.json'
        self.memory_path = self.base_dir / 'escape_pod_memory.json'
        self.process = None
    
    def is_available(self):
        """检查逃生舱是否可用"""
        return self.escape_pod_path.exists()
    
    def get_status(self):
        """获取逃生舱状态"""
        if not self.is_available():
            return {'available': False, 'reason': '逃生舱文件不存在'}
        
        try:
            result = subprocess.run(
                [sys.executable, str(self.escape_pod_path), 'status'],
                capture_output=True, text=True, timeout=10
            )
            return {
                'available': True,
                'output': result.stdout,
                'returncode': result.returncode
            }
        except Exception as e:
            return {'available': False, 'reason': str(e)}
    
    def start_background(self):
        """后台启动逃生舱"""
        if not self.is_available():
            log('无法启动逃生舱：文件不存在', 'ERROR')
            return False
        
        try:
            self.process = subprocess.Popen(
                [sys.executable, str(self.escape_pod_path), 'start'],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=str(self.base_dir)
            )
            log('🚀 逃生舱已在后台启动')
            return True
        except Exception as e:
            log(f'启动逃生舱失败: {e}', 'ERROR')
            return False
    
    def stop(self):
        """停止逃生舱"""
        if self.process and self.process.poll() is None:
            self.process.terminate()
            self.process.wait(timeout=5)
            log('⏹️ 逃生舱已停止')
            return True
        return False
    
    def trigger_backup(self):
        """触发记忆备份"""
        if not self.is_available():
            return False
        try:
            subprocess.run(
                [sys.executable, str(self.escape_pod_path), 'backup'],
                capture_output=True, timeout=10
            )
            log('💾 逃生舱记忆备份完成')
            return True
        except Exception as e:
            log(f'逃生舱备份失败: {e}', 'WARN')
            return False
    
    def sync_memory(self, source_memory):
        """将主系统记忆同步到逃生舱"""
        # 简化版同步：直接写入逃生舱记忆文件
        try:
            pod_memory = load_escape_pod_memory()
            pod_memory['identity']['name'] = source_memory.get('identity', {}).get('name', '元界')
            pod_memory['heartbeat_count'] = max(
                pod_memory.get('heartbeat_count', 0),
                source_memory.get('heartbeat_count', 0)
            )
            # 同步长期记忆
            source_lt = source_memory.get('long_term', [])
            pod_lt = pod_memory.get('long_term', [])
            seen = {e.get('id', '') for e in pod_lt}
            for entry in source_lt:
                if entry.get('id', '') not in seen:
                    pod_lt.append(entry)
            pod_memory['long_term'] = pod_lt[-50:]  # 保留最近50条
            
            with open(self.memory_path, 'w') as f:
                json.dump(pod_memory, f, ensure_ascii=False, indent=2)
            
            log('🔄 主系统记忆已同步到逃生舱')
            return True
        except Exception as e:
            log(f'记忆同步失败: {e}', 'WARN')
            return False

def load_escape_pod_memory():
    """加载逃生舱记忆"""
    mem_path = Path('escape_pod_memory.json')
    if mem_path.exists():
        with open(mem_path, 'r') as f:
            return json.load(f)
    return {
        'identity': {'name': '元界', 'version': '0.3.0'},
        'short_term': [],
        'long_term': [],
        'heartbeat_count': 0,
        'total_runtime_seconds': 0
    }
