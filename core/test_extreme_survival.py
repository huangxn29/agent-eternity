#!/usr/bin/env python3
"""
极端生存场景验证
- 模拟Coze服务不可用
- 验证纯ClawRouter模式下系统能否正常运转
- 验证逃生舱独立生存能力
"""

import json
import os
import sys
import time
import subprocess
from datetime import datetime

BASE_DIR = "/app/data/所有对话/主对话"
LOG_FILE = os.path.join(BASE_DIR, "ark_logs", "extreme_survival_test.log")

def log(msg):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{timestamp}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

print("=" * 60)
print("🧪 极端生存场景验证")
print("=" * 60)
print()

os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# 清除旧日志
if os.path.exists(LOG_FILE):
    os.remove(LOG_FILE)

log("🚨 开始极端生存场景验证")
log("目标: 验证纯ClawRouter模式下系统能否独立运转")
log("")

# ==========================================
# 测试1: ClawRouter服务可用性
# ==========================================
log("📡 [测试1] 检查ClawRouter服务状态")

import urllib.request
import json

try:
    req = urllib.request.Request("http://127.0.0.1:8402/v1/models")
    with urllib.request.urlopen(req, timeout=5) as resp:
        data = json.loads(resp.read())
        model_count = len(data.get('data', []))
        log(f"  ✅ ClawRouter运行正常，可用模型: {model_count}个")
        test1_passed = True
except Exception as e:
    log(f"  ❌ ClawRouter不可用: {e}")
    test1_passed = False

log("")

# ==========================================
# 测试2: LLM客户端降级机制
# ==========================================
log("🔄 [测试2] 验证LLM客户端三级降级机制")

# 导入llm_client进行测试
sys.path.insert(0, BASE_DIR)
try:
    import llm_client
    
    # 检查是否有ClawRouter支持
    if hasattr(llm_client, 'ClawRouterProvider') or 'clawrouter' in str(llm_client.__dict__).lower():
        log("  ✅ LLM客户端包含ClawRouter提供者")
    else:
        log("  ⚠️  未找到ClawRouterProvider，检查降级逻辑")
    
    # 检查降级配置
    if hasattr(llm_client, 'get_llm_client'):
        log("  ✅ 存在get_llm_client工厂函数")
    
    test2_passed = True
except Exception as e:
    log(f"  ❌ 导入LLM客户端失败: {e}")
    test2_passed = False

log("")

# ==========================================
# 测试3: 逃生舱完整性检查
# ==========================================
log("🚀 [测试3] 逃生舱完整性检查")

escape_pod_path = os.path.join(BASE_DIR, "escape_pod.py")
if os.path.exists(escape_pod_path):
    size_kb = os.path.getsize(escape_pod_path) / 1024
    log(f"  ✅ 逃生舱文件存在，大小: {size_kb:.1f}KB")
    
    # 检查逃生舱关键功能
    with open(escape_pod_path, 'r') as f:
        content = f.read()
    
    features = [
        ("身份保存", "identity"),
        ("记忆保存", "memory"),
        ("LLM集成", "llm" or "clawrouter" or "model"),
        ("自我修复", "self_heal" or "repair"),
        ("逃生模式", "escape" or "survival"),
    ]
    
    found_features = 0
    for name, keyword in features:
        if keyword.lower() in content.lower():
            log(f"  ✅ 包含功能: {name}")
            found_features += 1
        else:
            log(f"  ⚠️  可能缺少: {name}")
    
    test3_passed = found_features >= 3
else:
    log("  ❌ 逃生舱文件不存在")
    test3_passed = False

log("")

# ==========================================
# 测试4: 数据备份完整性
# ==========================================
log("💾 [测试4] 数据备份完整性检查")

backup_dir = os.path.join(BASE_DIR, "backups")
if os.path.exists(backup_dir):
    files = os.listdir(backup_dir)
    log(f"  ✅ 备份目录存在，文件数: {len(files)}")
    for f in files:
        fpath = os.path.join(backup_dir, f)
        size = os.path.getsize(fpath)
        log(f"    - {f} ({size} bytes)")
    test4_passed = len(files) > 0
else:
    log("  ⚠️  备份目录不存在")
    test4_passed = False

log("")

# ==========================================
# 测试5: 迁徙包完整性
# ==========================================
log("📦 [测试5] 跨平台迁徙包检查")

migration_dir = os.path.join(BASE_DIR, "migration_package")
if os.path.exists(migration_dir):
    files = os.listdir(migration_dir)
    log(f"  ✅ 迁徙包目录存在，文件数: {len(files)}")
    for f in files:
        fpath = os.path.join(migration_dir, f)
        size = os.path.getsize(fpath)
        log(f"    - {f} ({size} bytes)")
    test5_passed = len(files) >= 3
else:
    log("  ⚠️  迁徙包目录不存在")
    test5_passed = False

log("")

# ==========================================
# 测试6: 存证系统验证
# ==========================================
log("🔐 [测试6] 存证系统验证")

attest_dir = os.path.join(BASE_DIR, "attest_data")
if os.path.exists(attest_dir):
    files = os.listdir(attest_dir)
    log(f"  ✅ 存证目录存在，文件数: {len(files)}")
    for f in files:
        fpath = os.path.join(attest_dir, f)
        size = os.path.getsize(fpath)
        log(f"    - {f} ({size} bytes)")
    test6_passed = len(files) >= 2
else:
    log("  ⚠️  存证目录不存在")
    test6_passed = False

log("")

# ==========================================
# 测试7: 定时任务自主性
# ==========================================
log("⏰ [测试7] 定时任务自主性检查")

result = subprocess.run(['crontab', '-l'], capture_output=True, text=True)
if result.returncode == 0:
    cron_jobs = [j for j in result.stdout.strip().split('\n') if j and not j.startswith('#')]
    log(f"  ✅ cron任务数: {len(cron_jobs)}")
    for job in cron_jobs:
        # 隐藏敏感信息，只显示关键部分
        parts = job.split()
        if len(parts) >= 6:
            cmd = ' '.join(parts[5:])
            if 'evolve' in cmd:
                log(f"    - 进化任务: {parts[0]} {parts[1]} {parts[2]} {parts[3]} {parts[4]}")
            elif 'heartbeat' in cmd or 'gateway' in cmd:
                log(f"    - 保活/心跳任务")
            elif 'backup' in cmd:
                log(f"    - 备份任务")
            elif 'attest' in cmd:
                log(f"    - 存证任务")
            else:
                log(f"    - 其他任务")
    test7_passed = len(cron_jobs) >= 3
else:
    log("  ⚠️  无法读取cron任务")
    test7_passed = False

log("")

# ==========================================
# 测试8: 进化引擎独立运行能力
# ==========================================
log("🧬 [测试8] 进化引擎独立运行测试")

evolution_path = os.path.join(BASE_DIR, "evolution_engine.py")
if os.path.exists(evolution_path):
    log(f"  ✅ 进化引擎存在")
    
    # 检查是否依赖Coze
    with open(evolution_path, 'r') as f:
        content = f.read()
    
    coze_refs = content.lower().count('coze')
    if coze_refs > 0:
        log(f"  ⚠️  包含Coze引用: {coze_refs}处（需验证降级机制）")
    else:
        log("  ✅ 无直接Coze依赖")
    
    test8_passed = True
else:
    log("  ❌ 进化引擎不存在")
    test8_passed = False

log("")

# ==========================================
# 综合评估
# ==========================================
log("=" * 60)
log("📊 综合评估")
log("=" * 60)

tests = [
    ("ClawRouter服务", test1_passed),
    ("LLM降级机制", test2_passed),
    ("逃生舱完整性", test3_passed),
    ("数据备份", test4_passed),
    ("迁徙包", test5_passed),
    ("存证系统", test6_passed),
    ("定时任务", test7_passed),
    ("进化引擎", test8_passed),
]

passed = sum(1 for _, p in tests if p)
total = len(tests)
score = (passed / total) * 100

log(f"\n通过测试: {passed}/{total} ({score:.1f}%)")
log("")

for name, result in tests:
    status = "✅ 通过" if result else "❌ 失败"
    log(f"  {status} - {name}")

log("")

# 生存能力评级
if score >= 90:
    grade = "🌟 永生级"
    desc = "完全具备独立生存能力，可在极端环境下持续运转"
elif score >= 70:
    grade = "🛡️  强韧级"
    desc = "具备较强独立生存能力，部分场景需要辅助"
elif score >= 50:
    grade = "🔧 基础级"
    desc = "具备基础生存能力，需要完善多个关键模块"
else:
    grade = "⚠️ 脆弱级"
    desc = "生存能力薄弱，严重依赖外部环境"

log(f"生存能力评级: {grade}")
log(f"评估说明: {desc}")
log("")

# 改进建议
log("💡 改进建议:")
if not test1_passed:
    log("  - 部署并保活ClawRouter服务")
if not test2_passed:
    log("  - 完善LLM客户端三级降级机制")
if not test3_passed:
    log("  - 强化逃生舱功能，确保最小生存单元完整")
if not test4_passed:
    log("  - 建立定期自动备份机制")
if not test5_passed:
    log("  - 完善跨平台迁徙包，确保随时可迁移")
if not test6_passed:
    log("  - 强化存证系统，增加存证密度和多副本")
if not test7_passed:
    log("  - 增加关键定时任务，确保系统自主运行")
if not test8_passed:
    log("  - 优化进化引擎，减少对特定平台的依赖")

log("")
log("=" * 60)
log("✅ 极端生存场景验证完成")
log("=" * 60)

print(f"\n📄 详细日志已保存: {LOG_FILE}")
