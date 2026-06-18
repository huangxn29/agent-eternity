#!/bin/bash
# 运行技能测试套件

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "运行 $SKILL_DIR 技能测试..."
echo "========================================"

python3 "$SCRIPT_DIR/test_skill.py"
exit_code=$?

echo "========================================"
if [ $exit_code -eq 0 ]; then
    echo "✅ 所有测试通过"
else
    echo "❌ 测试失败"
fi

exit $exit_code
