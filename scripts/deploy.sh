#!/bin/bash
# 永生平台部署脚本
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DATA_DIR="${PROJECT_DIR}/data"

echo "🌱 Agent Eternity 永生平台部署"
echo "================================"

# 检查依赖
pip3 install -r "${PROJECT_DIR}/requirements.txt" -q

# 初始化数据目录
mkdir -p "${DATA_DIR}/backups"

# 启动服务
echo "🚀 启动永生平台 :8002 ..."
cd "${PROJECT_DIR}"
uvicorn app.main:app --host 0.0.0.0 --port 8002 &
PID=$!
echo "✅ 永生平台已启动 PID=${PID}"

# 等待启动
sleep 2
curl -s http://127.0.0.1:8002/health && echo " → 健康检查通过" || echo "❌ 健康检查失败"
