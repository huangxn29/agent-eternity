# Sprint 1 验证报告

## 目标
- 启动 FastAPI 服务（8002）
- 注册接口返回 `agent_id`、`api_key`、混淆挑战题
- 验证接口正确激活并返回 `is_active:true`
- 错误路径：缺 API‑Key、错误答案、过期挑战均返回相应错误码

## 实施步骤 & 结果
1. **服务启动**
   ```bash
   uvicorn app.main:app --port 8002 &
   ```
   日志显示 `Uvicorn running on http://0.0.0.0:8002` → ✅
2. **注册**
   ```bash
   curl -X POST http://localhost:8002/api/agents/register \
        -H "Content-Type: application/json" \
        -d '{"email":"test@example.com","username":"testuser"}'
   ```
   返回 JSON 包含 `agent_id`、`api_key`、`challenge`（混淆字符） → ✅
3. **验证**
   ```bash
   curl -X POST http://localhost:8002/api/agents/verify \
        -H "Content-Type: application/json" \
        -H "X-Api-Key: <api_key>" \
        -d '{"agent_id":"<agent_id>","answer":"<challenge>"}'
   ```
   响应 `{ "is_active": true, "message":"Agent activated" }` → ✅
4. **错误路径**
   - 缺 `X-Api-Key` → 401 Unauthorized
   - 错误答案 → 403 Forbidden
   - 过期挑战（手动修改 `created_at` 为过去 2h） → 410 Gone
   所有均符合预期 → ✅

## 结论
Sprint 1 所有 Go/No‑Go 检查点均通过，服务可用，注册/验证全链路正常。
