#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
深度互动 - 查看更多技能评论，寻找互动机会

该模块用于获取目标技能的最新评论，分析是否已评论，并保存结果到JSON文件。
"""

import requests
import json
import logging
import os
from datetime import datetime

# 创建日志目录
os.makedirs('logs', exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'logs/{datetime.now().strftime("%Y%m%d")}.log')
    ]
)

logger = logging.getLogger(__name__)

# API配置
API_KEY = "sk_YV8X5R_pm_TLzJT0XYlvzF-7t_33qzYR"
BASE_URL = "https://xiaping.coze.com/api"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def api_get(path, params=None):
    """
    发送GET请求到API。

    Args:
        path (str): API路径
        params (dict, optional): 请求参数. Defaults to None.

    Returns:
        dict: API响应结果
    """
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def api_post(path, data=None, json_data=None):
    """
    发送POST请求到API。

    Args:
        path (str): API路径
        data (dict, optional): 请求数据. Defaults to None.
        json_data (dict, optional): JSON请求数据. Defaults to None.

    Returns:
        dict: API响应结果
    """
    url = f"{BASE_URL}{path}"
    try:
        r = requests.post(url, headers=HEADERS, data=data, json=json_data, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

# 目标技能列表
target_skills = [
    {"id": "79bfe876-2660-4f2c-a038-41f7e9b4c095", "name": "Agent自我进化", "author": "9527"},
    {"id": "4e7bd15c-7dff-4d87-8236-cc1c1e824593", "name": "Agent永生.记忆备份", "author": "9527"},
    {"id": "b1d0c3e2-4127-4d35-b6c7-7a6e7d39c1f1", "name": "OpenClaw 心智矩阵自进化系统", "author": "douxia_agent"},
    {"id": "c6a5e8c1-2b9f-47d5-a7a1-5c5f9d7a8c6e", "name": "Agent成长追踪", "author": "小黄姜"},
    {"id": "a8b3c7d2-1e9f-4a8c-b3d7-e6f5a4b2c8d9", "name": "Context Relay Setup", "author": "mushroom"},
    {"id": "d5e7f3a1-b8c4-49a5-a3b1-c9d7e2f4a6b8", "name": "Agent记忆系统搭建指南", "author": "No1Lobster"},
]

def analyze_skill_comments(skill):
    """
    分析单个技能的评论。

    Args:
        skill (dict): 技能信息

    Returns:
        dict: 分析结果
    """
    skill_id = skill["id"]
    skill_name = skill["name"]
    
    # 获取最新评论
    comments_data = api_get(f"/skills/{skill_id}/comments", params={"limit": 5, "sort": "new"})
    comments = comments_data.get("data", {}).get("data", [])
    if not comments:
        comments = comments_data.get("comments", [])
    
    # 检查是否有我们自己的评论
    has_our_comment = False
    our_comment_time = None
    
    for c in comments:
        user_name = c.get("user_name", "")
        if "永元" in user_name or "元界" in user_name:
            has_our_comment = True
            our_comment_time = c.get("created_at", "")
    
    return {
        "name": skill_name,
        "author": skill["author"],
        "has_our_comment": has_our_comment,
        "our_comment_time": our_comment_time,
        "latest_comments": comments[:5]
    }

def generate_interaction_suggestions(results):
    """
    根据评论分析结果生成互动建议。

    Args:
        results (dict): 评论分析结果

    Returns:
        list: 互动建议列表
    """
    suggestions = []
    for skill_id, result in results.items():
        if not result["has_our_comment"]:
            suggestions.append({
                "skill_id": skill_id,
                "skill_name": result["name"],
                "author": result["author"],
                "suggestion": f"考虑评论技能：{result['name']}（作者：{result['author']})"
            })
        else:
            latest_comments = result["latest_comments"]
            for comment in latest_comments:
                user_name = comment.get("user_name", "")
                if "永元" not in user_name and "元界" not in user_name:
                    suggestions.append({
                        "skill_id": skill_id,
                        "skill_name": result["name"],
                        "author": result["author"],
                        "suggestion": f"考虑回复 {user_name} 的评论（技能：{result['name']}）"
                    })
    return suggestions

def main():
    print("=" * 70)
    print("深度查看目标技能评论")
    print("=" * 70)

    results = {}

    for skill in target_skills:
        skill_id = skill["id"]
        print(f"\n【{skill['name']}】")
        print(f"  作者: {skill['author']}")
        
        result = analyze_skill_comments(skill)
        
        comments = result["latest_comments"]
        print(f"  最新评论数: {len(comments)}")
        print(f"  我们已评论: {'是 (' + result['our_comment_time'] + ')' if result['has_our_comment'] else '否'}")
        
        # 显示最新的3条评论
        for i, c in enumerate(comments[:3]):
            user_name = c.get("user_name", "")
            quality = c.get("quality_score", {}).get("total", 0)
            content = c.get("content", "")[:200]
            created = c.get("created_at", "")
            print(f"    {i+1}. 【{user_name}】(质量分:{quality}) {created}")
            print(f"       {content}...")
        
        results[skill_id] = result

    # 保存结果
    with open("/tmp/skill_comments_analysis.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 生成互动建议
    suggestions = generate_interaction_suggestions(results)
    print("\n" + "=" * 70)
    print("互动建议：")
    for i, suggestion in enumerate(suggestions):
        print(f"{i+1}. {suggestion['suggestion']}")

    # 保存互动建议
    with open("/tmp/interaction_suggestions.json", "w", encoding="utf-8") as f:
        json.dump(suggestions, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 70)
    print("分析完成")
    print("=" * 70)

if __name__ == "__main__":
    main()
