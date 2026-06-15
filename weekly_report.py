#!/usr/bin/env python3
import json

status_file = '/app/data/所有对话/主对话/技能/agent-evolution/scripts/continuous_evolution/status.json'
with open(status_file) as f:
    s = json.load(f)

print('=== 永生平台进化周报 ===')
print(f'总轮次: {s.get("total_rounds")}')
print(f'当前轮: {s.get("current_round")}')
print(f'运行状态: {s.get("running")}')
print(f'平台特性数: {len(s.get("platform_features", {}))}')
print('技能评分:')
for skill, score in sorted(s.get('skill_scores', {}).items(), key=lambda x: -x[1]):
    print(f'  {skill}: {score}')
