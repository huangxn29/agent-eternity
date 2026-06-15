#!/usr/bin/env python3
import json, os, datetime

log_dir = '/app/data/所有对话/主对话/ark_logs'
os.makedirs(log_dir, exist_ok=True)

status_file = '/app/data/所有对话/主对话/技能/agent-evolution/scripts/continuous_evolution/status.json'

now = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
try:
    with open(status_file) as f:
        s = json.load(f)
    print(f'[{now}] Evolution: round={s.get("current_round")}, running={s.get("running")}, skill={s.get("current_skill")}')
except Exception as e:
    print(f'[{now}] Status check failed: {e}')
