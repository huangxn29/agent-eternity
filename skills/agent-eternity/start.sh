#!/bin/bash
# 启动 Agent Eternity 服务

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${PORT:-8002}

echo "Starting Agent Eternity on port $PORT..."
exec python -m uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
