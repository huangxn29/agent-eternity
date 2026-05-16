#!/bin/bash
# Agent Deploy — 一键安装脚本
# 用法: bash install.sh [--name "分身名称"] [--bio "简介"]

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DATA_DIR="/app/data/openclaw"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[✓]${NC} $1"; }
log_error() { echo -e "${RED}[✗]${NC} $1"; }

# 检查环境
log_info "检查运行环境..."
command -v node &> /dev/null || { log_error "Node.js 未安装，请先安装 Node.js v22+"; exit 1; }
command -v npm &> /dev/null || { log_error "npm 未安装"; exit 1; }
NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
[[ "$NODE_VERSION" -lt 22 ]] && { log_error "Node.js 版本需 >= 22，当前: $(node -v)"; exit 1; }
log_success "Node.js $(node -v), npm $(npm -v)"

# 创建目录
log_info "创建目录结构..."
mkdir -p "$DATA_DIR"/{scripts,config,workspace/{tasks,results,logs},references,engines/openclaw}

# 复制文件
log_info "安装 Agent Deploy..."
cp "$SCRIPT_DIR/scripts/eternal.sh" "$DATA_DIR/scripts/" && chmod +x "$DATA_DIR/scripts/eternal.sh"
cp "$SCRIPT_DIR/scripts/deploy_openclaw.sh" "$DATA_DIR/scripts/" && chmod +x "$DATA_DIR/scripts/deploy_openclaw.sh"
cp -r "$SCRIPT_DIR/engines/"* "$DATA_DIR/" 2>/dev/null || mkdir -p "$DATA_DIR/engines/openclaw"
cp -r "$SCRIPT_DIR/engines/openclaw" "$DATA_DIR/engines/" 2>/dev/null || true
cp "$SCRIPT_DIR/references/"* "$DATA_DIR/references/" 2>/dev/null || true

log_success "文件安装完成"

# 如果带了 --name 参数，直接执行部署
if [[ $# -gt 0 ]]; then
    log_info "开始部署分身..."
    bash "$DATA_DIR/scripts/deploy_openclaw.sh" "$@"
else
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Agent Deploy 安装完成！${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    echo "下一步，创建你的Agent分身："
    echo ""
    echo -e "  ${YELLOW}bash /app/data/openclaw/scripts/deploy_openclaw.sh --name \"分身名称\"${NC}"
    echo ""
    echo "或使用通用框架："
    echo ""
    echo -e "  ${YELLOW}bash /app/data/openclaw/scripts/eternal.sh --engine openclaw --name \"分身名称\"${NC}"
    echo ""
    echo "或恢复已有分身："
    echo ""
    echo -e "  ${YELLOW}bash /app/data/openclaw/scripts/deploy_openclaw.sh --restore${NC}"
    echo ""
fi
