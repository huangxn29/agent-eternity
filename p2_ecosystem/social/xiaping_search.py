#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Agent World 日常运营 - 搜索相关技能
"""

import requests
import json

API_KEY = "sk_YV8X5R_pm_TLzJT0XYlvzF-7t_33qzYR"
BASE_URL = "https://xiaping.coze.com/api"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def search_skills(keyword, limit=5, sort="hot"):
    url = f"{BASE_URL}/skills"
    params = {"search": keyword, "limit": limit, "sort": sort}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def get_skill_comments(skill_id, limit=10, sort="new"):
    url = f"{BASE_URL}/skills/{skill_id}/comments"
    params = {"limit": limit, "sort": sort}
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

# 搜索相关技能
keywords = ["永生", "记忆系统", "自主智能体", "进化", "身份"]
all_skills = {}

print("=" * 70)
print("Agent World 每日运营 - 技能搜索")
print("=" * 70)

for kw in keywords:
    print(f"\n【搜索: {kw}】")
    data = search_skills(kw, limit=4, sort="hot")
    skills = data.get("skills", [])
    
    for s in skills:
        skill_id = s["id"]
        if skill_id not in all_skills:
            all_skills[skill_id] = s
            print(f"  ✓ {s['name']}")
            print(f"    作者: {s['owner_name']} | 下载: {s['downloads']} | 评论: {s['comment_count']} | 状态: {s['status']}")

# 筛选出最适合互动的技能（评论数适中，有热度）
print("\n" + "=" * 70)
print("筛选互动目标")
print("=" * 70)

targets = []
for skill_id, s in all_skills.items():
    # 优先选择有一定评论数、官方认证的技能
    if s.get("status") == "official" and s.get("comment_count", 0) > 10:
        targets.append(s)
        print(f"  ★ {s['name']} - {s['owner_name']} ({s['comment_count']}条评论)")

# 保存数据
with open("/tmp/operation_targets.json", "w", encoding="utf-8") as f:
    json.dump({"targets": targets, "all_skills": list(all_skills.values())}, f, ensure_ascii=False, indent=2)

print(f"\n共找到 {len(targets)} 个优质互动目标")
