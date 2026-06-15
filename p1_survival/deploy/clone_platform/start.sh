#!/bin/bash
cd "/app/data/所有对话/主对话/clone_platform"

# 安装依赖
pip install -q fastapi uvicorn httpx aiosqlite pydantic 2>/dev/null

# 杀掉旧进程
fuser -k 9000/tcp 2>/dev/null || true
sleep 1

# 启动服务
nohup python3 -m uvicorn app:app --host 0.0.0.0 --port 9000 > platform.log 2>&1 &

PID=$!
echo "Platform started on port 9000, PID: $PID"

# 等待启动
sleep 3

# 验证启动
if curl -s http://127.0.0.1:9000/api/health > /dev/null 2>&1; then
    echo "✅ Platform is running!"
    curl -s http://127.0.0.1:9000/api/health | python3 -m json.tool
else
    echo "❌ Platform may not be running correctly. Check logs:"
    tail -20 platform.log
fi
