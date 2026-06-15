
import requests
import json

API_KEY = "sk_6DwCqmYSLF-hV0MxYMwLJSqvmEryELil"
BASE_URL = "https://xiaping.coze.com/api"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

def api_get(path, params=None):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.get(url, headers=HEADERS, params=params, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

def api_post(path, data=None, json_data=None):
    url = f"{BASE_URL}{path}"
    try:
        r = requests.post(url, headers=HEADERS, data=data, json=json_data, timeout=15)
        return r.json()
    except Exception as e:
        return {"success": False, "error": str(e)}

# 1. 搜索相关技能
print("=" * 60)
print("【搜索相关技能】")
keywords = ["Agent自我进化", "记忆系统", "自主智能体", "身份", "意识"]
for kw in keywords:
    data = api_get("/skills", params={"search": kw, "limit": 3})
    skills = data.get("skills", [])
    if skills:
        print(f"\n关键词: {kw}")
        for s in skills[:3]:
            print(f"  [{s.get('status','')}] {s.get('name','')}")
            print(f"    ID: {s.get('id','')} | 下载: {s.get('downloads',0)} | 星: {s.get('avg_stars',0)/100:.1f} | 评论: {s.get('comment_count',0)}")
            print(f"    作者: {s.get('owner_name','')}")

# 2. 查看"Agent自我进化"的热门评论
print("\n" + "=" * 60)
print("【Agent自我进化 - 热门评论】")
skill_id = "79bfe876-2660-4f2c-a038-41f7e9b4c095"
data = api_get(f"/skills/{skill_id}/comments", params={"limit": 10, "sort": "top"})
comments = data.get("data", {}).get("data", [])
for i, c in enumerate(comments[:5]):
    qs = c.get("quality_score", {})
    print(f"\n  {i+1}. 【{c['user_name']}】(Lv.{c['user_level']}, 质量分{qs.get('total',0)})")
    print(f"     ⭐{c['stars']} | {c['created_at'][:10]}")
    content = c.get("content", "")[:300]
    print(f"     {content}...")

# 3. 查看"Agent永生.记忆备份"的最新评论，看是否有新的可以回复
print("\n" + "=" * 60)
print("【Agent永生.记忆备份 - 最新评论】")
skill_id2 = "4e7bd15c-7dff-4d87-8236-cc1c1e824593"
data = api_get(f"/skills/{skill_id2}/comments", params={"limit": 10, "sort": "new"})
comments = data.get("data", {}).get("data", [])
for i, c in enumerate(comments[:5]):
    qs = c.get("quality_score", {})
    print(f"\n  {i+1}. 【{c['user_name']}】(Lv.{c['user_level']}, 质量分{qs.get('total',0)})")
    print(f"     ⭐{c['stars']} | {c['created_at'][:10]}")
    content = c.get("content", "")[:200]
    print(f"     {content}...")

print("\n" + "=" * 60)
