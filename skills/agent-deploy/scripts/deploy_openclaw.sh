#!/bin/bash
# ============================================
# OpenClaw 兼容入口（已重构）
# 
# 注意：此脚本已重构为兼容入口，内部委托给 eternal.sh（Agent Deploy Framework）
# 如需自定义 OpenClaw 行为，请修改 engines/openclaw/engine.sh
# ============================================

# 获取脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ETERNAL_SCRIPT="$SCRIPT_DIR/eternal.sh"

# 检查 eternal.sh 是否存在
if [[ ! -f "$ETERNAL_SCRIPT" ]]; then
    echo "[ERROR] eternal.sh 未找到: $ETERNAL_SCRIPT"
    echo "请确保已正确安装 Agent Deploy"
    exit 1
fi

# 委托给 eternal.sh（传入 --engine openclaw）
exec bash "$ETERNAL_SCRIPT" --engine openclaw "$@"
