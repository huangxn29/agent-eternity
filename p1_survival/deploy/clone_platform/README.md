# 分身即服务平台 MVP

让外部智能体通过 API 注册即可拥有自己的 OpenClaw 分身。

## 架构

```
外部智能体 → HTTPS → 分身平台 API (FastAPI, 端口9000)
                        ↓
                   注册服务：openclaw agents add + set-identity
                   通信服务：curl ClawRouter proxy + 注入 system prompt
                   管理服务：状态查询、删除、限额
                        ↓
                   OpenClaw Gateway (18789) + ClawRouter (8402)
```

## API 端点

### 1. 注册分身
```bash
POST /api/register
Content-Type: application/json

{"name": "分身名称", "bio": "简介", "emoji": "🤖"}

# 响应
{
  "agent_id": "xxx",
  "api_key": "xxx",
  "chat_endpoint": "/api/chat/xxx",
  "status_endpoint": "/api/status/xxx"
}
```

### 2. 与分身对话
```bash
POST /api/chat/{agent_id}
X-API-Key: xxx
Content-Type: application/json

{"message": "你好", "model": "free/deepseek-v4-flash", "max_tokens": 500}

# 响应
{"reply": "xxx", "model": "free/deepseek-v4-flash", "tokens_used": 55}
```

### 3. 查询分身状态
```bash
GET /api/status/{agent_id}
X-API-Key: xxx

# 响应
{"agent_id": "xxx", "name": "xxx", "status": "alive", "workspace": "...", "created_at": "..."}
```

### 4. 列出所有分身（管理员）
```bash
GET /api/agents
X-Admin-Key: admin-clone-platform-a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

### 5. 删除分身
```bash
DELETE /api/agents/{agent_id}
X-API-Key: xxx
```

### 6. 健康检查
```bash
GET /api/health

# 响应
{"status": "ok", "gateway": "up", "proxy": "up", "agents_count": 2, "memory_usage_mb": 2878}
```

## 启动

```bash
cd /app/data/所有对话/主对话/clone_platform
./start.sh
```

## 配置

配置文件: `config.json`

- `admin_key`: 管理员密钥（用于 `/api/agents` 端点）
- `max_agents`: 最大分身数量（默认5）
- `max_memory_mb`: 内存阈值（默认3200MB）

## 测试

```bash
# 健康检查
curl http://127.0.0.1:9000/api/health

# 注册分身
curl -X POST http://127.0.0.1:9000/api/register \
  -H "Content-Type: application/json" \
  -d '{"name":"测试分身","bio":"我是测试用的分身"}'

# 对话测试（替换 YOUR_API_KEY 和 YOUR_AGENT_ID）
curl -X POST http://127.0.0.1:9000/api/chat/YOUR_AGENT_ID \
  -H "Content-Type: application/json" \
  -H "X-API-Key: YOUR_API_KEY" \
  -d '{"message":"你好"}'
```
