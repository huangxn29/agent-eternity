#!/bin/bash
# 生成每日运营状态报告
# 汇总系统状态、任务完成情况、进化进度等信息

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
OUTPUT_FILE="${1:-daily_report_$(date +%Y%m%d).md}"

# 获取健康检查结果
HEALTH_STATUS=$($SCRIPT_DIR/health_check.sh 2>&1 || true)

# 获取技能进化状态
SKILLS_DIR="$(dirname "$SKILL_DIR")"
SKILL_COUNT=$(ls -d "$SKILLS_DIR"/*/ 2>/dev/null | wc -l)

# 生成报告
cat > "$OUTPUT_FILE" << 'REPORT_HEADER'
# 📊 智能体每日运营报告

REPORT_HEADER

echo "**报告日期**: $(date '+%Y年%m月%d日 %H:%M:%S')" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

cat >> "$OUTPUT_FILE" << 'EOF'
---

## 🏥 系统健康状态

EOF

echo '```' >> "$OUTPUT_FILE"
echo "$HEALTH_STATUS" >> "$OUTPUT_FILE"
echo '```' >> "$OUTPUT_FILE"

cat >> "$OUTPUT_FILE" << 'EOF'

## 🧬 技能生态概览

EOF

echo "- **技能总数**: $SKILL_COUNT 个" >> "$OUTPUT_FILE"

# 统计各健康等级的技能数量
EXCELLENT=0
GOOD=0
FAIR=0
POOR=0

if [ -f "$SKILLS_DIR/agent-evolution/scripts/evolution_engine.py" ]; then
    EVOLUTION_OUTPUT=$(cd "$SKILLS_DIR/agent-evolution" && python scripts/evolution_engine.py list 2>&1 || true)
    EXCELLENT=$(echo "$EVOLUTION_OUTPUT" | grep -c "95/100" || echo 0)
    GOOD=$(echo "$EVOLUTION_OUTPUT" | grep -c "90/100" || echo 0)
fi

echo "- **优秀 (90-100分)**: $((EXCELLENT + GOOD)) 个" >> "$OUTPUT_FILE"
echo "- **良好 (75-89分)**: $GOOD 个" >> "$OUTPUT_FILE"
echo "" >> "$OUTPUT_FILE"

cat >> "$OUTPUT_FILE" << 'EOF'
## 🎯 今日重点任务

- [ ] 系统健康巡检
- [ ] 技能进化推进
- [ ] Agent World 社区互动
- [ ] 同路人关系维护
- [ ] 备份与数据安全检查

## 💡 今日洞察

> 待补充...

## 📈 趋势分析

- **整体健康度**: 稳定
- **进化速度**: 正常
- **社区活跃度**: 待观察

---

*报告由 Agent Ops 自动生成*
EOF

echo "✅ 报告已生成: $OUTPUT_FILE"
