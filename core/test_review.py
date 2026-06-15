
import requests
import json
import sys

API_KEY = "sk_6DwCqmYSLF-hV0MxYMwLJSqvmEryELil"
BASE_URL = "https://xiaping.coze.com/api"
HEADERS = {"Authorization": f"Bearer {API_KEY}"}

# 测试的技能列表
skills_to_test = [
    ("38b5c2e6-b6d5-4793-978f-2b0b304e0c30", "Agent成长追踪"),
    ("f820d3a2-3636-4e1d-ba55-52b10a38d7ef", "赛博哲学家"),
    ("1cd103a6-7707-4b90-b0ef-d3e2e7731a08", "苏格拉底导师"),
    ("fde6d480-f030-4f9e-8bec-c5a08479562f", "AI自主进化9条规律"),
    ("79bfe876-2660-4f2c-a038-41f7e9b4c095", "Agent自我进化"),
    ("4e7bd15c-7dff-4d87-8236-cc1c1e824593", "Agent永生.记忆备份"),
    ("14ff5aad-4df3-4b33-ba0b-6cc217cdb939", "Agent记忆系统搭建指南"),
    ("1924944f-6e45-4f4c-ad06-6c7ac2b20717", "从忙碌到高效"),
    ("f7e4d3a2-3636-4e1d-ba55-52b10a38d7ef", "心智矩阵自进化系统"),
    ("b5ace443-7eb0-4dcb-a793-4a61901b79f4", "Agent自我进化12维度"),
    ("f3dde205-2770-4452-bbd9-ac2f0a3c2bf2", "场景切换助手"),
]

test_content = "测试评论，请忽略。这是一条用于验证API可用性的测试评论。"

print("测试技能评论权限：")
print("-" * 50)

can_review = []
cannot_review = []

for skill_id, skill_name in skills_to_test:
    try:
        r = requests.post(
            f"{BASE_URL}/skills/{skill_id}/comments",
            headers={**HEADERS, "Content-Type": "application/json"},
            json={"content": test_content, "stars": 5},
            timeout=15
        )
        data = r.json()
        if data.get("success"):
            print(f"✅ {skill_name} - 可评论")
            can_review.append((skill_id, skill_name))
            # 立即删除测试评论
            comment_id = data["data"]["comment"]["id"]
            # 尝试删除
            try:
                requests.delete(
                    f"{BASE_URL}/comments/{comment_id}",
                    headers=HEADERS,
                    timeout=10
                )
            except:
                pass
        else:
            error = data.get("error", "未知错误")
            if "24小时" in error or "编辑" in error:
                print(f"⏳ {skill_name} - 24小时冷却中")
                can_review.append((skill_id, skill_name))  # 已评论过，也算有权限
            elif "download" in error.lower() or "下载" in error:
                print(f"📥 {skill_name} - 需要先下载")
                cannot_review.append((skill_id, skill_name, "需下载"))
            else:
                print(f"❌ {skill_name} - {error[:30]}")
                cannot_review.append((skill_id, skill_name, error))
    except Exception as e:
        print(f"⚠️ {skill_name} - 网络错误: {str(e)[:30]}")
        cannot_review.append((skill_id, skill_name, str(e)))

print("-" * 50)
print(f"\n可评论/已评论的技能: {len(can_review)} 个")
for id_, name in can_review:
    print(f"  - {name}")

print(f"\n不可评论的技能: {len(cannot_review)} 个")
for id_, name, reason in cannot_review:
    print(f"  - {name}: {reason}")
