#!/bin/bash
# 运行技能测试套件

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"

echo "运行 $SKILL_DIR 技能测试..."
echo "========================================"

total_passed=0
total_failed=0
test_count=0

# 运行所有测试文件
for test_file in "$SCRIPT_DIR"/test_*.py; do
    if [ -f "$test_file" ]; then
        test_name=$(basename "$test_file" .py)
        echo ""
        echo "--- 运行 $test_name ---"
        python3 "$test_file"
        exit_code=$?
        if [ $exit_code -eq 0 ]; then
            total_passed=$((total_passed + 1))
        else
            total_failed=$((total_failed + 1))
        fi
        test_count=$((test_count + 1))
    fi
done

echo ""
echo "========================================"
echo "测试汇总: $test_count 个测试套件, $total_passed 通过, $total_failed 失败"

if [ $total_failed -eq 0 ]; then
    echo "✅ 所有测试通过"
    exit 0
else
    echo "❌ 部分测试失败"
    exit 1
fi
