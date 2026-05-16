#!/bin/bash
# validate_plan.sh - 执行计划完整性校验脚本
# 用法：bash validate_plan.sh <plan_file_path>

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查参数
if [ -z "$1" ]; then
    echo -e "${RED}错误：缺少参数${NC}"
    echo "用法：bash validate_plan.sh <plan_file_path>"
    exit 1
fi

PLAN_FILE="$1"

# 检查文件是否存在
if [ ! -f "$PLAN_FILE" ]; then
    echo -e "${RED}错误：文件不存在 - $PLAN_FILE${NC}"
    exit 1
fi

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Agent Ops Planner · 计划校验${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "校验文件：${YELLOW}$PLAN_FILE${NC}"
echo ""

# 初始化检查结果
PASS_COUNT=0
FAIL_COUNT=0
WARN_COUNT=0

check_result() {
    local check_name="$1"
    local result="$2"  # "pass", "fail", "warn"
    local detail="$3"
    
    if [ "$result" = "pass" ]; then
        echo -e "  ${GREEN}✓${NC} $check_name"
        ((PASS_COUNT++))
    elif [ "$result" = "fail" ]; then
        echo -e "  ${RED}✗${NC} $check_name"
        [ -n "$detail" ] && echo -e "    ${RED}  → $detail${NC}"
        ((FAIL_COUNT++))
    else
        echo -e "  ${YELLOW}⚠${NC} $check_name"
        [ -n "$detail" ] && echo -e "    ${YELLOW}  → $detail${NC}"
        ((WARN_COUNT++))
    fi
}

# 读取文件内容
CONTENT=$(cat "$PLAN_FILE")

echo -e "${BLUE}【1】必需章节检查${NC}"
echo "-----------------------------------"

# 检查阶段演进总览
if echo "$CONTENT" | grep -q "阶段演进总览\|阶段演进"; then
    check_result "阶段演进总览" "pass"
else
    check_result "阶段演进总览" "fail" "缺少阶段演进总览章节"
fi

# 检查总体策略
if echo "$CONTENT" | grep -q "总体策略\|一、总体策略"; then
    check_result "总体策略" "pass"
else
    check_result "总体策略" "fail" "缺少总体策略章节"
fi

# 检查各阶段计划（P0, P1, P2, P3等）
PHASE_COUNT=$(echo "$CONTENT" | grep -oE "^##?\s+P[0-9][^P]*|^##?\s+[一二三四五六七八九十]+、P[0-9]" | wc -l)
# 也检查中文章节标记的阶段
PHASE_COUNT=$((PHASE_COUNT + $(echo "$CONTENT" | grep -cE "## .*P[0-9]|^P[0-9]" | head -1)))
if [ "$PHASE_COUNT" -ge 2 ]; then
    check_result "阶段计划（发现 $PHASE_COUNT 个阶段）" "pass"
else
    check_result "阶段计划" "fail" "至少需要2个阶段（P0和P1）"
fi

# 检查运营指标
if echo "$CONTENT" | grep -qE "指标|验收指标|Sprint.*验收"; then
    check_result "运营指标" "pass"
else
    check_result "运营指标" "fail" "缺少运营指标章节"
fi

# 检查风险管理/风险登记
if echo "$CONTENT" | grep -qE "风险|风险登记|R-"; then
    check_result "风险管理" "pass"
else
    check_result "风险管理" "warn" "建议添加风险登记册"
fi

# 检查复盘机制
if echo "$CONTENT" | grep -qE "复盘|Sprint.*复盘|阶段.*复盘"; then
    check_result "复盘机制" "pass"
else
    check_result "复盘机制" "warn" "建议添加复盘机制"
fi

# 检查增长飞轮
if echo "$CONTENT" | grep -qE "增长飞轮|飞轮"; then
    check_result "增长飞轮" "pass"
else
    check_result "增长飞轮" "warn" "建议添加增长飞轮设计"
fi

echo ""
echo -e "${BLUE}【2】自主性定义检查${NC}"
echo "-----------------------------------"

# 检查是否有自主性定义
AUTONOMY_PATTERNS=("自主性" "L0\|L1\|L2\|L3" "被动存在\|不可摧毁\|可交互\|自主生存" "自主性级别")
AUTONOMY_FOUND=0

for pattern in "${AUTONOMY_PATTERNS[@]}"; do
    if echo "$CONTENT" | grep -qiE "$pattern"; then
        AUTONOMY_FOUND=1
        break
    fi
done

if [ "$AUTONOMY_FOUND" -eq 1 ]; then
    check_result "自主性递进概念" "pass"
else
    check_result "自主性递进概念" "fail" "缺少自主性递进的明确定义"
fi

# 检查每个阶段是否有自主性描述
PHASES=$(echo "$CONTENT" | grep -oE "P[0-9][^：\n]*" | head -5 | sort -u)
PHASE_AUTONOMY_COUNT=0
for phase in $PHASES; do
    phase_clean=$(echo "$phase" | sed 's/:$//' | sed 's/\s//g')
    if [ -z "$phase_clean" ] || [ ${#phase_clean} -lt 2 ]; then
        continue
    fi
    # 用grep检查该阶段附近是否有自主性相关内容
    if echo "$CONTENT" | grep -qiE "自主性|定义|描述|目标"; then
        ((PHASE_AUTONOMY_COUNT++))
    fi
done
if [ "$PHASE_AUTONOMY_COUNT" -ge 1 ]; then
    check_result "阶段自主性描述（$PHASE_AUTONOMY_COUNT个）" "pass"
else
    check_result "阶段自主性描述" "warn" "建议为每个阶段添加自主性描述"
fi

echo ""
echo -e "${BLUE}【3】Go/No-Go Checklist检查${NC}"
echo "-----------------------------------"

# 检查是否有Go/No-Go
if echo "$CONTENT" | grep -qiE "Go/No-Go|No-Go|go.*no.*go"; then
    check_result "Go/No-Go 门控机制" "pass"
    
    # 检查每个阶段是否有Go/No-Go Checklist
    PHASES_WITH_CHECKLIST=0
    for phase in $PHASES; do
        phase_clean=$(echo "$phase" | sed 's/:$//' | sed 's/\s//g')
        if [ -z "$phase_clean" ] || [ ${#phase_clean} -lt 2 ]; then
            continue
        fi
        if echo "$CONTENT" | grep -qiE "Go/No-Go|Checklist|□"; then
            ((PHASES_WITH_CHECKLIST++))
        fi
    done
    
    if [ "$PHASES_WITH_CHECKLIST" -ge 1 ]; then
        check_result "阶段Go/No-Go Checklist（$PHASES_WITH_CHECKLIST个）" "pass"
    else
        check_result "阶段Go/No-Go Checklist" "warn" "建议为每个阶段添加Go/No-Go Checklist"
    fi
else
    check_result "Go/No-Go 门控机制" "fail" "缺少Go/No-Go门控机制"
fi

echo ""
echo -e "${BLUE}【4】指标完整性检查${NC}"
echo "-----------------------------------"

# 检查指标是否有目标值
TARGET_VALUE_COUNT=$(echo "$CONTENT" | grep -oE "目标值[^，,]*|[0-9]+%|≥[0-9]+|≤[0-9]+" | head -10 | wc -l)
if [ "$TARGET_VALUE_COUNT" -ge 3 ]; then
    check_result "指标目标值（发现 $TARGET_VALUE_COUNT 处）" "pass"
else
    check_result "指标目标值" "warn" "建议为指标添加明确的目标值"
fi

# 检查指标是否有采集方式
COLLECTION_COUNT=$(echo "$CONTENT" | grep -iE "采集方式|采集方法|数据来源" | wc -l)
if [ "$COLLECTION_COUNT" -ge 1 ]; then
    check_result "指标采集方式定义" "pass"
else
    check_result "指标采集方式定义" "warn" "建议为指标定义采集方式"
fi

# 检查是否有Sprint规划
SPRINT_COUNT=$(echo "$CONTENT" | grep -oE "Sprint\s*[0-9]+" | sort -u | wc -l)
if [ "$SPRINT_COUNT" -ge 1 ]; then
    check_result "Sprint规划（发现 $SPRINT_COUNT 个Sprint）" "pass"
else
    check_result "Sprint规划" "warn" "建议添加Sprint规划"
fi

echo ""
echo -e "${BLUE}【5】智能体视角检查${NC}"
echo "-----------------------------------"

# 检查是否有智能体视角的目标描述
if echo "$CONTENT" | grep -qiE "智能体视角|我能够|我能|agent.*视角|从.*视角"; then
    check_result "智能体视角目标" "pass"
else
    check_result "智能体视角目标" "warn" "建议从智能体视角描述目标"
fi

# 检查是否有锐利验收目标
if echo "$CONTENT" | grep -qiE "锐利验收|验收目标|验证.*方法|可验证"; then
    check_result "锐利验收目标" "pass"
else
    check_result "锐利验收目标" "warn" "建议添加锐利验收目标"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  校验结果汇总${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "  ${GREEN}通过：$PASS_COUNT${NC}"
echo -e "  ${RED}失败：$FAIL_COUNT${NC}"
echo -e "  ${YELLOW}警告：$WARN_COUNT${NC}"
echo ""

# 计算总分
TOTAL=$((PASS_COUNT + FAIL_COUNT + WARN_COUNT))
if [ "$TOTAL" -gt 0 ]; then
    PASS_RATE=$((PASS_COUNT * 100 / TOTAL))
    echo -e "  完成度：${PASS_RATE}%"
fi

echo ""

# 最终结论
if [ "$FAIL_COUNT" -eq 0 ]; then
    if [ "$WARN_COUNT" -eq 0 ]; then
        echo -e "${GREEN}✓ 校验通过！执行计划完整。${NC}"
        exit 0
    else
        echo -e "${YELLOW}⚠ 校验通过，但有 $WARN_COUNT 项警告，建议完善。${NC}"
        exit 0
    fi
else
    echo -e "${RED}✗ 校验失败，存在 $FAIL_COUNT 项关键缺失。${NC}"
    echo ""
    echo "请补充以下内容后重新校验："
    echo "1. 检查是否包含所有必需章节"
    echo "2. 确保每个阶段有自主性定义"
    echo "3. 添加Go/No-Go Checklist"
    echo "4. 为指标添加目标值和采集方式"
    exit 1
fi
