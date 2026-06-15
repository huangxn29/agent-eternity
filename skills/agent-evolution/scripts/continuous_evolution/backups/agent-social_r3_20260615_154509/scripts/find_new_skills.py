#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
搜索更多可互动的技能
"""

import requests
import json
import time
from datetime import datetime

API_KEY = "sk_YV8X5R_pm_TLzJT0XYlvzF-7t_33qzYR"
BASE_URL = "https://xiaping.coze.com/api"

def get(path):
    url = BASE_URL + path
    try:
        r = requests.get(url, headers={"Authorization": f"Bearer {API_KEY}"}, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def check_skill_commented(skill_id):
    """检查我们是否已经评论过这个技能"""
    comments_data = get(f"/skills/{skill_id}/comments?limit=20&sort=new")
    comments = comments_data.get("data", {}).get("data", [])
    
    has_commented = False
    hq_users = []
    
    for c in comments:
        uname = c.get("user_name", "")
        if "永元" in uname or "元界" in uname:
            has_commented = True
        
        quality = c.get("quality_score", {}).get("total", 0)
        if quality >= 7:
            hq_users.append({"name": uname, "quality": quality})
    
    return has_commented, comments_data.get("data", {}).get("total", 0), hq_users

print("=" * 70)
print("搜索更多可互动的技能")
print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# 搜索关键词列表
keywords = ["Agent", "AI", "智能体", "工具调用", "记忆", "进化", "上下文", "自主", "角色", "人格"]

all_found_skills = []

for kw in keywords:
    from urllib.parse import quote
    encoded_kw = quote(kw)
    
    # 搜索
    data = get(f"/skills?search={encoded_kw}&limit=10&sort=hot")
    skills = data.get("skills", [])
    
    print(f"\n搜索「{kw}」: 找到 {len(skills)} 个")
    
    for s in skills:
        sid = s.get("id", "")
        # 去重
        if sid not in [x["id"] for x in all_found_skills]:
            all_found_skills.append({
                "id": sid,
                "name": s.get("name", ""),
                "author": s.get("owner_name", ""),
                "downloads": s.get("downloads", 0),
                "comment_count": s.get("comment_count", 0),
                "status": s.get("status", ""),
                "category": s.get("category", []),
            })

print(f"\n总共找到 {len(all_found_skills)} 个不同的技能")

# 筛选官方技能
official_skills = [s for s in all_found_skills if s.get("status") == "official"]
print(f"其中官方技能: {len(official_skills)} 个")

# 检查每个官方技能我们是否已经评论过
print("\n" + "=" * 70)
print("检查评论状态")
print("=" * 70)

not_commented = []
already_commented = []

for i, skill in enumerate(official_skills[:20]):  # 检查前20个
    sid = skill["id"]
    sname = skill["name"]
    
    has_commented, total_comments, hq_users = check_skill_commented(sid)
    
    if has_commented:
        already_commented.append(skill)
        status = "✅ 已评论"
    else:
        not_commented.append(skill)
        status = "⭕ 未评论"
    
    print(f"  {status}: {sname} ({total_comments}条评论)")
    if hq_users[:2]:
        print(f"       高质量用户: {', '.join([u['name'] for u in hq_users[:3]])}")
    
    time.sleep(0.3)
    
    if (i+1) % 5 == 0:
        print(f"  --- 进度: {i+1}/{min(20, len(official_skills))} ---")

print(f"\n已评论: {len(already_commented)} 个")
print(f"未评论: {len(not_commented)} 个")

# 保存结果
with open("/tmp/skills_to_interact.json", "w", encoding="utf-8") as f:
    json.dump({
        "not_commented": not_commented,
        "already_commented": already_commented,
        "total_found": len(all_found_skills)
    }, f, ensure_ascii=False, indent=2)

# 显示未评论的技能详情
print("\n" + "=" * 70)
print("可评论的技能列表")
print("=" * 70)

for i, s in enumerate(not_commented):
    print(f"\n  {i+1}. {s['name']}")
    print(f"     作者: {s['author']}")
    print(f"     下载: {s['downloads']} | 评论: {s['comment_count']}")
    print(f"     分类: {', '.join(s['category'])}")

print("\n" + "=" * 70)
