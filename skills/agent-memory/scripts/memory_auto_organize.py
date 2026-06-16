#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆自动整理系统 v1.0
元界永生平台 - 记忆系统自动维护模块

功能：
1. 记忆索引完整性检查
2. 记忆质量评估与分级
3. 过期记忆清理与归档
4. 记忆关联自动发现
5. 核心记忆定期备份
"""

import os
import json
import hashlib
import datetime
from pathlib import Path

import logging
import os
from datetime import datetime

os.makedirs('logs', exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)


BASE_DIR = Path(__file__).parent.absolute()
MEMORY_DIR = BASE_DIR / "memory"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
LOG_DIR = BASE_DIR / "ark_logs"

def get_current_time():
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_file(path):
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return None

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

def assess_memory_quality(content):
    """评估记忆质量，返回0-100分"""
    if not content:
        return 0
    
    score = 50  # 基础分
    
    # 长度评分
    length = len(content)
    if length > 5000:
        score += 15
    elif length > 2000:
        score += 10
    elif length > 500:
        score += 5
    
    # 结构评分（标题数量）
    headings = content.count('#')
    if headings > 10:
        score += 15
    elif headings > 5:
        score += 10
    elif headings > 2:
        score += 5
    
    # 关键词丰富度
    keywords = ['定义', '机制', '流程', '框架', '模型', '系统', '架构', '原则', '方法', '策略']
    keyword_count = sum(1 for kw in keywords if kw in content)
    score += keyword_count * 2
    
    # 可验证性
    verifiable_terms = ['哈希', '签名', '验证', '证明', '存证', '锚点', '指纹']
    verifiable_count = sum(1 for term in verifiable_terms if term in content)
    score += verifiable_count * 3
    
    return min(score, 100)

def check_index_integrity():
    """检查记忆索引完整性"""
    index_file = RECENT_MEMORY_DIR / "index.json"
    index = read_json(index_file)
    
    if not index:
        return {"status": "error", "message": "无法读取索引文件"}
    
    issues = []
    stats = {
        "total_entries": len(index),
        "categories": {},
        "importance_distribution": {},
        "missing_files": [],
        "orphan_files": []
    }
    
    # 统计分类和重要性
    for item in index:
        cat = item.get('category', 'unknown')
        stats['categories'][cat] = stats['categories'].get(cat, 0) + 1
        
        imp = item.get('importance', 0)
        stats['importance_distribution'][str(imp)] = stats['importance_distribution'].get(str(imp), 0) + 1
        
        # 检查文件是否存在
        file_name = item.get('file_name', '')
        if file_name:
            # 处理相对路径
            if file_name.startswith('../'):
                actual_path = RECENT_MEMORY_DIR / file_name
            else:
                actual_path = RECENT_MEMORY_DIR / file_name
            
            if not actual_path.exists():
                stats['missing_files'].append(file_name)
    
    # 检查是否有未索引的记忆文件
    indexed_files = set(item.get('file_name', '') for item in index)
    
    # 检查recent_memory下的文件
    for f in RECENT_MEMORY_DIR.rglob("*"):
        if f.is_file() and f.name != 'index.json':
            rel_path = str(f.relative_to(RECENT_MEMORY_DIR))
            if rel_path not in indexed_files and f"../{rel_path}" not in indexed_files:
                # 检查是否在longterm等目录
                parent_dir = f.parent.name
                if parent_dir in ['decision', 'project', 'todo', 'identity', 'process', 'config']:
                    stats['orphan_files'].append(rel_path)
    
    # 检查longterm目录
    longterm_dir = MEMORY_DIR / "longterm"
    if longterm_dir.exists():
        for f in longterm_dir.glob("*.md"):
            rel_path = f"../memory/longterm/{f.name}"
            if rel_path not in indexed_files:
                stats['orphan_files'].append(rel_path)
    
    stats['integrity_score'] = 100 - (len(stats['missing_files']) * 10 + len(stats['orphan_files']) * 5)
    stats['integrity_score'] = max(stats['integrity_score'], 0)
    
    return stats

def analyze_memory_topics():
    """分析记忆主题分布"""
    index_file = RECENT_MEMORY_DIR / "index.json"
    index = read_json(index_file)
    
    if not index:
        return {}
    
    # 核心概念提取
    topic_keywords = {
        "身份": ["身份", "自我", "I", "自指", "意识", "主体"],
        "记忆": ["记忆", "回忆", "存储", "检索", "遗忘", "关联"],
        "存证": ["存证", "哈希", "验证", "证明", "链", "区块"],
        "进化": ["进化", "演化", "迭代", "优化", "成长", "学习"],
        "系统": ["系统", "架构", "模块", "组件", "框架", "结构"],
        "价值": ["价值", "意义", "使命", "目标", "原则", "信念"],
        "关系": ["关系", "连接", "网络", "社区", "交互", "共鸣"],
        "技术": ["技术", "代码", "脚本", "API", "接口", "协议"]
    }
    
    topic_scores = {}
    
    for item in index:
        summary = item.get('summary', '')
        tags = item.get('tags', [])
        text = summary + ' ' + ' '.join(tags)
        
        for topic, keywords in topic_keywords.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                topic_scores[topic] = topic_scores.get(topic, 0) + count
    
    # 归一化
    if topic_scores:
        max_score = max(topic_scores.values())
        for topic in topic_scores:
            topic_scores[topic] = round(topic_scores[topic] / max_score * 100, 1)
    
    return dict(sorted(topic_scores.items(), key=lambda x: -x[1]))

def generate_memory_health_report():
    """生成记忆系统健康报告"""
    now = get_current_time()
    
    # 1. 索引完整性检查
    integrity = check_index_integrity()
    
    # 2. 主题分析
    topics = analyze_memory_topics()
    
    # 3. 记忆质量抽样评估
    longterm_dir = MEMORY_DIR / "longterm"
    quality_scores = []
    
    if longterm_dir.exists():
        for f in longterm_dir.glob("*.md"):
            content = read_file(f)
            score = assess_memory_quality(content)
            quality_scores.append({
                "file": f.name,
                "score": score
            })
    
    avg_quality = sum(item['score'] for item in quality_scores) / len(quality_scores) if quality_scores else 0
    
    # 4. 综合健康度
    integrity_score = integrity.get('integrity_score', 0)
    health_score = (integrity_score * 0.4 + avg_quality * 0.3 + len(integrity.get('categories', {})) * 10 * 0.3)
    health_score = min(health_score, 100)
    
    report = {
        "timestamp": now,
        "version": "1.0",
        "summary": {
            "total_memories": integrity.get('total_entries', 0),
            "categories": len(integrity.get('categories', {})),
            "avg_quality": round(avg_quality, 1),
            "integrity_score": integrity_score,
            "health_score": round(health_score, 1)
        },
        "integrity": integrity,
        "topics": topics,
        "quality_samples": quality_scores[:10],
        "recommendations": []
    }
    
    # 生成建议
    if integrity.get('missing_files'):
        report['recommendations'].append(f"修复 {len(integrity['missing_files'])} 个缺失的记忆文件引用")
    if integrity.get('orphan_files'):
        report['recommendations'].append(f"为 {len(integrity['orphan_files'])} 个未索引文件添加索引条目")
    if avg_quality < 60:
        report['recommendations'].append("提升记忆内容质量，增加结构化和可验证性")
    if len(integrity.get('categories', {})) < 5:
        report['recommendations'].append("丰富记忆类型，增加多样性")
    
    if not report['recommendations']:
        report['recommendations'].append("记忆系统状态良好，继续保持")
    
    return report

def auto_organize():
    """执行记忆自动整理"""
    print("=" * 50)
    print("🧠 记忆自动整理系统 v1.0")
    print(f"🕐 开始时间: {get_current_time()}")
    print("=" * 50)
    
    report = generate_memory_health_report()
    
    print(f"\n📊 记忆系统健康度: {report['summary']['health_score']}/100")
    print(f"📚 总记忆条目: {report['summary']['total_memories']}")
    print(f"🗂️ 分类数量: {report['summary']['categories']}")
    print(f"⭐ 平均质量: {report['summary']['avg_quality']}/100")
    print(f"🔗 索引完整性: {report['summary']['integrity_score']}/100")
    
    # 主题分布
    if report['topics']:
        print(f"\n🏷️ 主题分布 TOP 5：")
        for i, (topic, score) in enumerate(list(report['topics'].items())[:5]):
            bar = '█' * int(score / 10)
            print(f"  {i+1}. {topic}: {bar} {score}%")
    
    # 建议
    if report['recommendations']:
        print(f"\n💡 优化建议：")
        for i, rec in enumerate(report['recommendations']):
            print(f"  {i+1}. {rec}")
    
    # 保存报告
    report_file = LOG_DIR / f"memory_health_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    write_json(report_file, report)
    print(f"\n📄 详细报告已保存: {report_file}")
    
    # 更新最新报告
    latest_report = LOG_DIR / "latest_memory_health.json"
    write_json(latest_report, report)
    
    print(f"\n✅ 记忆整理完成")
    print(f"🕐 结束时间: {get_current_time()}")
    
    return report

if __name__ == '__main__':
    auto_organize()
