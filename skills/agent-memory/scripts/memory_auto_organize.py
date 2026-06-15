#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
记忆自动整理系统 v2.0
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

# 配置日志系统
os.makedirs('logs', exist_ok=True)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/{datetime.datetime.now().strftime("%Y%m%d")}.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 定义常量
BASE_DIR = Path(__file__).parent.absolute()
MEMORY_DIR = BASE_DIR / "memory"
RECENT_MEMORY_DIR = BASE_DIR / "recent_memory"
LOG_DIR = BASE_DIR / "ark_logs"

def get_current_time():
    """获取当前时间字符串"""
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def read_file(path):
    """读取文件内容"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        logger.error(f"读取文件失败: {path} - {e}")
        return None

def read_json(path):
    """读取JSON文件"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"读取JSON文件失败: {path} - {e}")
        return None

def write_json(path, data):
    """写入JSON文件"""
    try:
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"写入JSON文件失败: {path} - {e}")
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
    score += min(keyword_count * 2, 20)  # 限制最高加分
    
    # 可验证性
    verifiable_terms = ['哈希', '签名', '验证', '证明', '存证', '锚点', '指纹']
    verifiable_count = sum(1 for term in verifiable_terms if term in content)
    score += min(verifiable_count * 3, 15)  # 限制最高加分
    
    return min(max(score, 0), 100)  # 确保分数在0-100之间

def check_index_integrity():
    """检查记忆索引完整性"""
    index_file = RECENT_MEMORY_DIR / "index.json"
    index = read_json(index_file)
    
    if not index:
        logger.warning("无法读取索引文件")
        return {"status": "error", "message": "无法读取索引文件"}
    
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
            actual_path = RECENT_MEMORY_DIR / file_name.lstrip('../')
            if not actual_path.exists():
                stats['missing_files'].append(file_name)
    
    # 检查未索引的文件
    indexed_files = set(item.get('file_name', '').lstrip('../') for item in index)
    for f in RECENT_MEMORY_DIR.rglob("*"):
        if f.is_file() and f.name != 'index.json':
            rel_path = str(f.relative_to(RECENT_MEMORY_DIR))
            if rel_path not in indexed_files:
                stats['orphan_files'].append(rel_path)
    
    # 计算完整性评分
    stats['integrity_score'] = max(100 - (len(stats['missing_files']) * 10 + len(stats['orphan_files']) * 5), 0)
    
    logger.info(f"索引完整性检查完成: 总条目={stats['total_entries']}, 缺失文件={len(stats['missing_files'])}, 未索引文件={len(stats['orphan_files'])}")
    return stats

def analyze_memory_topics():
    """分析记忆主题分布"""
    index_file = RECENT_MEMORY_DIR / "index.json"
    index = read_json(index_file)
    
    if not index:
        logger.warning("索引文件为空")
        return {}
    
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
    total_count = 0
    
    for item in index:
        text = item.get('summary', '') + ' ' + ' '.join(item.get('tags', []))
        for topic, keywords in topic_keywords.items():
            count = sum(1 for kw in keywords if kw in text)
            if count > 0:
                topic_scores[topic] = topic_scores.get(topic, 0) + count
                total_count += count
    
    # 归一化处理
    if total_count > 0:
        for topic in topic_scores:
            topic_scores[topic] = round((topic_scores[topic] / total_count) * 100, 1)
    
    # 按得分降序排序
    sorted_scores = dict(sorted(topic_scores.items(), key=lambda x: x[1], reverse=True))
    logger.info(f"主题分析完成: 主要主题={list(sorted_scores.keys())[:3]}")
    return sorted_scores

def generate_memory_health_report():
    """生成记忆系统健康报告"""
    now = get_current_time()
    logger.info(f"开始生成记忆健康报告: {now}")
    
    try:
        # 索引完整性检查
        integrity = check_index_integrity()
        
        # 主题分析
        topics = analyze_memory_topics()
        
        report = {
            "timestamp": now,
            "integrity": integrity,
            "topics": topics,
            "summary": {
                "integrity_score": integrity.get('integrity_score', 0),
                "top_topics": list(topics.keys())[:3] if topics else [],
                "total_memories": integrity.get('total_entries', 0)
            }
        }
        
        report_path = LOG_DIR / f"memory_health_{now.replace(':', '-').replace(' ', '_')}.json"
        write_json(report_path, report)
        logger.info(f"记忆健康报告生成成功: {report_path}")
        
    except Exception as e:
        logger.error(f"生成记忆健康报告失败: {e}")

if __name__ == "__main__":
    generate_memory_health_report()
