#!/bin/bash
# 运行 agent-memory 技能测试套件
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
echo "运行 agent-memory 技能测试..."
python3 "$SCRIPT_DIR/test_skill.py"
