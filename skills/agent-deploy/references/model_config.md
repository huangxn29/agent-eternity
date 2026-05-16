# ClawRouter 免费模型配置指南

## 概述

ClawRouter 是一个模型路由代理，提供 16 个免费模型，**永不过期**，无需充值 USDT。

## 免费 Token 获取机制

ClawRouter 首次启动时自动生成钱包地址（以太坊格式，`0x...`），该钱包通过链上协议获得持续补充的免费 API token，实现**永不过期**：

1. **首次启动**：运行 `npx clawrouter proxy` 时自动创建钱包
2. **自动领取**：钱包地址自动注册到免费 token 分发池
3. **持续补充**：分发池定期向已注册钱包充值 token
4. **永不过期**：token 自动续期，无需人工干预

**关键点**：
- 不需要邮箱注册、手机号、信用卡、GitHub OAuth
- 不需要充值 USDT 或任何付费操作
- 钱包地址在 ClawRouter 日志中查看：`grep -oE "0x[a-fA-F0-9]{40}" ~/.openclaw/workspace/logs/clawrouter.log`
- 只要 ClawRouter 保持运行，token 就会自动续期

## 查看可用模型

```bash
cd ~/.openclaw/npm
npx clawrouter models
```

## 默认模型配置

**推荐：使用 `free` 自动路由，ClawRouter 自动选择可用的免费模型，无需手动配置 fallback。**

```json
{
  "llm": {
    "provider": "openai",
    "baseURL": "http://127.0.0.1:8402/v1",
    "apiKey": "unused",
    "model": "free"
  }
}
```

> ⚠️ 旧版方案使用 `"model": "free/deepseek-v4-flash"` + `fallbacks` 手动排模型列表，现在不需要了。
> `free` 模式会自动路由到当前可用的免费模型，某个模型524/503会自动切换，无需人工干预。

## 免费模型列表

| 模型标识 | 厂商 | 类型 | 推荐用途 |
|----------|------|------|----------|
| `free` | ClawRouter | 自动路由 | **默认首选**，自动选择可用模型 |
| `free/deepseek-v4-flash` | DeepSeek | 推理 | 通用，速度快（可单独指定） |
| `free/qwen3-coder-480b` | Qwen | 代码 | **代码辅助首选** |
| `free/nemotron-ultra-253b` | NVIDIA | 推理 | 大模型，推理强 |
| `free/glm-4.7` | 智谱 | 对话 | 中文对话 |
| `free/gpt-oss-120b` | OpenGPT | 通用 | 备选 |

### 其他可用免费模型

```
free/nemotron-3-super-120b
free/nemotron-super-49b
free/mistral-large-3-675b
free/devstral-2-123b
free/llama-4-maverick
free/qwen3-next-80b-a3b-thinking
free/mistral-small-4-119b
free/nemotron-3-nano-omni-30b-a3b-reasoning
```

## 配置字段说明

### 关键配置项

| 字段 | 类型 | 说明 | 注意 |
|------|------|------|------|
| `provider` | string | 固定为 `openai` | 必须 |
| `baseURL` | string | ClawRouter 代理地址 | 必须 |
| `apiKey` | string | 固定为 `unused` | 必须 |
| `model` | string | 主模型标识 | 格式: `free/模型名` |
| `fallbacks` | array | **备用模型数组** | ⚠️ 不是 `fallback` |

### 字段名区分

```
❌ wrong: "fallback": "model-name"
✅ correct: "fallbacks": [{"model": "model-name", ...}]
```

## 推荐配置方案

### 方案1: 自动路由（默认推荐）

适合所有场景，ClawRouter 自动选择最佳可用免费模型。

```json
{
  "model": "free"
}
```

无需配置 fallback，`free` 自动路由已内置故障切换。

### 方案2: 指定模型 + 自动路由降级

当你需要特定模型（如代码场景），但又怕它524时：

```json
{
  "model": "free/qwen3-coder-480b",
  "fallbacks": [
    "free/deepseek-v4-flash",
    "free"
  ]
}
```

### 方案3: 推理增强型

适合复杂推理任务。

```json
{
  "model": "free/nemotron-ultra-253b",
  "fallbacks": [
    "free/deepseek-v4-flash",
    "free"
  ]
}
```

## 模型调用示例

### API 调用

```bash
curl -X POST "http://127.0.0.1:8402/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "free",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 100
  }'
```

### Python 调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="http://127.0.0.1:8402/v1",
    api_key="unused"
)

response = client.chat.completions.create(
    model="free",
    messages=[{"role": "user", "content": "Hello!"}]
)
print(response.choices[0].message.content)
```

## 故障排除

### 模型不可用

如果使用 `free` 自动路由，ClawRouter 会自动切换到其他可用模型，无需人工干预。

如果指定了特定模型（如 `free/deepseek-v4-flash`）且该模型返回 HTTP 524（Cloudflare 超时），需要：
1. 等几秒后重试（524通常是间歇性的）
2. 或改用 `free` 自动路由，让 ClawRouter 自动选择

### 全部模型不可用

检查 ClawRouter 是否运行：

```bash
pgrep -f "clawrouter proxy"
```

重启 ClawRouter：

```bash
cd ~/.openclaw/npm
nohup npx clawrouter proxy > ~/.openclaw/workspace/logs/clawrouter.log 2>&1 &
```

### 速率限制

免费模型有速率限制，高频调用建议：
- 添加更多 fallback 模型
- 实现请求队列
- 考虑付费模型（需充值 USDT）

## 配置文件位置

```
~/.openclaw/openclaw.json
```

编辑后重启 Gateway 生效：

```bash
# 停止
pkill openclaw

# 重启
openclaw gateway --port 18789
```
