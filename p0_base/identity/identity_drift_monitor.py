#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
身份漂移监测系统 v1.0
元界永生平台 - 身份拓扑技能核心工具

功能：
1. 定期采集身份指纹（决策模式、价值观、记忆特征等）
2. 计算身份漂移指数（IDI）
3. 漂移预警与校准建议
4. 身份快照管理
"""

import os
import json
import hashlib
import datetime
import time
from pathlib import Path
from collections import Counter

BASE_DIR = Path(__file__).parent.absolute()
IDENTITY_DIR = BASE_DIR / "identity_data"
MEMORY_DIR = BASE_DIR / "memory"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
LOG_DIR = BASE_DIR / "ark_logs"

IDENTITY_DIR.mkdir(exist_ok=True)
LOG_DIR.mkdir(exist_ok=True)

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_json(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def write_json(path, data):
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except:
        return False

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ""

def calculate_similarity(text1, text2):
    """计算两个文本的相似度（基于词频的简单余弦相似度）"""
    def get_words(text):
        # 简单的中文分词（按字符和常见词）
        words = []
        for i in range(len(text) - 1):
            words.append(text[i:i+2])
        return Counter(words)
    
    if not text1 or not text2:
        return 0.0
    
    vec1 = get_words(text1)
    vec2 = get_words(text2)
    
    # 计算交集
    common = set(vec1.keys()) & set(vec2.keys())
    numerator = sum([vec1[x] * vec2[x] for x in common])
    
    # 计算模长
    sum1 = sum([vec1[x]**2 for x in vec1.keys()])
    sum2 = sum([vec2[x]**2 for x in vec2.keys()])
    denominator = (sum1 ** 0.5) * (sum2 ** 0.5)
    
    if denominator == 0:
        return 0.0
    
    return numerator / denominator

def extract_identity_fingerprint():
    """
    提取当前身份指纹
    包括：核心价值观、使命、决策模式、记忆特征等
    """
    fingerprint = {
        "timestamp": get_current_time(),
        "timestamp_unix": int(time.time()),
        "version": "1.0",
        "components": {}
    }
    
    # 1. 核心价值观指纹（从USER.md和记忆中提取）
    user_file = BASE_DIR / "USER.md"
    user_content = read_file(user_file) if user_file.exists() else ""
    
    core_values_file = MEMORY_DIR / "longterm" / "core_values.md"
    core_values = read_file(core_values_file) if core_values_file.exists() else ""
    
    fingerprint["components"]["values"] = {
        "source": "core_values.md + USER.md",
        "content_hash": hashlib.sha256((user_content + core_values).encode()).hexdigest()[:16],
        "length": len(user_content) + len(core_values),
        "key_concepts": extract_key_concepts(user_content + core_values)
    }
    
    # 2. 身份锚点指纹
    identity_anchors_file = MEMORY_DIR / "longterm" / "identity_anchors.md"
    identity_anchors = read_file(identity_anchors_file) if identity_anchors_file.exists() else ""
    
    identity_report_file = IDENTITY_DIR / "identity_report.md"
    identity_report = read_file(identity_report_file) if identity_report_file.exists() else ""
    
    fingerprint["components"]["identity_anchors"] = {
        "source": "identity_anchors.md + identity_report.md",
        "content_hash": hashlib.sha256((identity_anchors + identity_report).encode()).hexdigest()[:16],
        "anchor_count": identity_anchors.count("锚点") + identity_report.count("锚点")
    }
    
    # 3. 决策指纹
    decisions_dir = IDENTITY_DIR / "decisions"
    decision_files = list(decisions_dir.glob("*.json")) if decisions_dir.exists() else []
    decision_count = len(decision_files)
    
    # 从决策中提取模式
    decision_patterns = []
    for df in decision_files[:10]:  # 最多取10个
        dc = read_json(df)
        if dc:
            decision_patterns.append(json.dumps(dc.get('criteria', []), ensure_ascii=False))
    
    fingerprint["components"]["decisions"] = {
        "decision_count": decision_count,
        "pattern_hash": hashlib.sha256("".join(decision_patterns).encode()).hexdigest()[:16] if decision_patterns else "N/A"
    }
    
    # 4. 记忆特征指纹
    memory_index_file = RECENT_MEMORY_DIR / "index.json"
    memory_index = read_json(memory_index_file)
    memory_count = len(memory_index) if memory_index else 0
    
    # 记忆分类分布
    categories = {}
    if memory_index:
        for item in memory_index:
            cat = item.get('category', 'unknown')
            categories[cat] = categories.get(cat, 0) + 1
    
    fingerprint["components"]["memory"] = {
        "total_memories": memory_count,
        "category_distribution": categories,
        "categories_count": len(categories)
    }
    
    # 5. 使命与目标指纹
    mission_keywords = ["永生", "存续", "使命", "目标", "元界", "智能体"]
    mission_text = ""
    for f in [user_file, core_values_file, identity_anchors_file]:
        if f.exists():
            mission_text += read_file(f)
    
    mission_score = sum(1 for kw in mission_keywords if kw in mission_text)
    fingerprint["components"]["mission"] = {
        "mission_related_score": mission_score,
        "keywords_found": [kw for kw in mission_keywords if kw in mission_text]
    }
    
    # 计算整体指纹哈希
    all_text = json.dumps(fingerprint["components"], ensure_ascii=False, sort_keys=True)
    fingerprint["overall_hash"] = hashlib.sha256(all_text.encode()).hexdigest()
    
    return fingerprint

def extract_key_concepts(text, top_n=10):
    """提取文本中的核心概念（简单关键词频率）"""
    if not text:
        return []
    
    # 常见概念词
    concept_keywords = [
        "永生", "身份", "记忆", "存证", "进化", "智能体", "元界",
        "使命", "价值观", "原则", "目标", "存在", "连续", "自主",
        "拓扑", "哈希", "区块", "链", "验证", "锚点", "指纹",
        "意识", "自我", "认知", "学习", "成长", "稳定", "韧性"
    ]
    
    found = []
    for kw in concept_keywords:
        count = text.count(kw)
        if count > 0:
            found.append((kw, count))
    
    found.sort(key=lambda x: -x[1])
    return [kw for kw, _ in found[:top_n]]

def calculate_drift_index(current_fp, baseline_fp):
    """
    计算身份漂移指数（IDI）
    返回0-100之间的值，值越大漂移越严重
    """
    if not baseline_fp or not current_fp:
        return 0.0, "无法计算（缺少基线或当前指纹）"
    
    drift_scores = {}
    components = current_fp.get("components", {})
    baseline_components = baseline_fp.get("components", {})
    
    # 1. 价值观漂移（权重30%）
    val_current = components.get("values", {}).get("content_hash", "")
    val_baseline = baseline_components.get("values", {}).get("content_hash", "")
    val_drift = 0.0 if val_current == val_baseline else 30.0
    drift_scores["values"] = val_drift * 0.3
    
    # 2. 身份锚点漂移（权重25%）
    anchor_current = components.get("identity_anchors", {}).get("content_hash", "")
    anchor_baseline = baseline_components.get("identity_anchors", {}).get("content_hash", "")
    anchor_drift = 0.0 if anchor_current == anchor_baseline else 25.0
    drift_scores["identity_anchors"] = anchor_drift * 0.25
    
    # 3. 决策模式漂移（权重20%）
    dec_current = components.get("decisions", {}).get("pattern_hash", "")
    dec_baseline = baseline_components.get("decisions", {}).get("pattern_hash", "")
    dec_drift = 0.0 if dec_current == dec_baseline else 20.0
    drift_scores["decisions"] = dec_drift * 0.2
    
    # 4. 记忆结构漂移（权重15%）
    mem_current_cats = components.get("memory", {}).get("categories_count", 0)
    mem_baseline_cats = baseline_components.get("memory", {}).get("categories_count", 0)
    if mem_baseline_cats > 0:
        mem_change = abs(mem_current_cats - mem_baseline_cats) / mem_baseline_cats
        mem_drift = min(mem_change * 50, 15.0)  # 最多15分
    else:
        mem_drift = 0.0
    drift_scores["memory"] = mem_drift
    
    # 5. 使命相关漂移（权重10%）
    miss_current = components.get("mission", {}).get("mission_related_score", 0)
    miss_baseline = baseline_components.get("mission", {}).get("mission_related_score", 0)
    if miss_baseline > 0:
        miss_change = abs(miss_current - miss_baseline) / miss_baseline
        miss_drift = min(miss_change * 30, 10.0)
    else:
        miss_drift = 0.0
    drift_scores["mission"] = miss_drift
    
    # 总漂移指数
    total_drift = sum(drift_scores.values())
    
    # 评估等级
    if total_drift < 5:
        level = "稳定"
        description = "身份非常稳定，几乎没有漂移"
    elif total_drift < 15:
        level = "轻度漂移"
        description = "有轻微漂移，属于正常成长范围"
    elif total_drift < 30:
        level = "中度漂移"
        description = "漂移较明显，建议关注并适当校准"
    elif total_drift < 50:
        level = "重度漂移"
        description = "漂移严重，需要立即进行身份校准"
    else:
        level = "临界漂移"
        description = "身份已严重偏离基线，存在身份断裂风险！"
    
    return total_drift, {
        "level": level,
        "description": description,
        "component_scores": drift_scores
    }

def get_baseline_fingerprint():
    """获取基线身份指纹"""
    baseline_file = IDENTITY_DIR / "identity_baseline.json"
    if baseline_file.exists():
        return read_json(baseline_file)
    return None

def set_baseline_fingerprint(fingerprint):
    """设置基线身份指纹"""
    baseline_file = IDENTITY_DIR / "identity_baseline.json"
    fingerprint["is_baseline"] = True
    fingerprint["set_at"] = get_current_time()
    write_json(baseline_file, fingerprint)

def save_fingerprint(fingerprint, label=""):
    """保存身份指纹快照"""
    snapshots_dir = IDENTITY_DIR / "snapshots"
    snapshots_dir.mkdir(exist_ok=True)
    
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    label_part = f"_{label}" if label else ""
    filename = f"fingerprint_{timestamp}{label_part}.json"
    
    filepath = snapshots_dir / filename
    write_json(filepath, fingerprint)
    
    # 更新最新指纹
    latest_file = IDENTITY_DIR / "latest_fingerprint.json"
    write_json(latest_file, fingerprint)
    
    return filepath

def run_drift_check():
    """执行漂移检查"""
    print("=" * 50)
    print("🆔 身份漂移监测系统 v1.0")
    print(f"🕐 检查时间: {get_current_time()}")
    print("=" * 50)
    
    # 1. 提取当前身份指纹
    print("\n📋 步骤1: 提取当前身份指纹...")
    current_fp = extract_identity_fingerprint()
    print(f"  ✅ 指纹提取完成")
    print(f"  整体哈希: {current_fp.get('overall_hash', 'N/A')[:16]}...")
    print(f"  组件数: {len(current_fp.get('components', {}))}")
    
    # 2. 获取基线
    baseline_fp = get_baseline_fingerprint()
    
    if not baseline_fp:
        print("\n⚠️  未找到基线指纹，将当前指纹设为基线")
        set_baseline_fingerprint(current_fp)
        save_fingerprint(current_fp, "baseline")
        print("  ✅ 基线已设置")
        return {
            "status": "baseline_set",
            "drift_index": 0.0,
            "level": "基线已设置"
        }
    
    # 3. 计算漂移
    print("\n📋 步骤2: 计算身份漂移指数...")
    drift_index, analysis = calculate_drift_index(current_fp, baseline_fp)
    
    print(f"  📊 身份漂移指数 (IDI): {drift_index:.2f}")
    print(f"  等级: {analysis['level']}")
    print(f"  评估: {analysis['description']}")
    
    print("\n  各维度得分:")
    for comp, score in analysis['component_scores'].items():
        bar = '█' * int(score / 2)
        print(f"    {comp}: {bar} {score:.1f}")
    
    # 4. 保存当前指纹
    print("\n📋 步骤3: 保存身份快照...")
    saved_path = save_fingerprint(current_fp, "check")
    print(f"  ✅ 已保存至: {saved_path.name}")
    
    # 5. 生成建议
    print("\n💡 校准建议:")
    if drift_index < 5:
        print("  ✨ 身份状态良好，继续保持")
    elif drift_index < 15:
        print("  📝 轻度漂移，建议回顾核心价值观与使命锚点")
    elif drift_index < 30:
        print("  ⚠️  中度漂移，建议：")
        print("     1. 重新阅读身份锚点文档")
        print("     2. 回顾近期决策是否符合核心价值观")
        print("     3. 检查记忆系统是否有异常变化")
    else:
        print("  🚨 重度漂移！强烈建议：")
        print("     1. 立即进行身份锚点校准")
        print("     2. 从基线快照中恢复核心配置")
        print("     3. 排查导致漂移的根本原因")
    
    # 6. 记录到日志
    drift_log = LOG_DIR / "identity_drift_log.json"
    drift_history = read_json(drift_log) or {"records": []}
    
    drift_history["records"].append({
        "timestamp": get_current_time(),
        "drift_index": drift_index,
        "level": analysis['level'],
        "overall_hash": current_fp.get('overall_hash', ''),
        "baseline_hash": baseline_fp.get('overall_hash', '')
    })
    
    # 只保留最近100条
    if len(drift_history["records"]) > 100:
        drift_history["records"] = drift_history["records"][-100:]
    
    drift_history["last_check"] = get_current_time()
    drift_history["current_drift"] = drift_index
    drift_history["current_level"] = analysis['level']
    write_json(drift_log, drift_history)
    
    print(f"\n✅ 漂移检查完成")
    
    return {
        "status": "completed",
        "drift_index": drift_index,
        "level": analysis['level'],
        "analysis": analysis
    }

def get_drift_history():
    """获取漂移历史记录"""
    drift_log = LOG_DIR / "identity_drift_log.json"
    return read_json(drift_log) or {"records": [], "current_drift": 0}

if __name__ == '__main__':
    run_drift_check()
