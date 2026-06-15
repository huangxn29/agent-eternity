# Agent Awake 架构文档 v2.1

## 整体架构

```
┌─────────────────────────────────────────────────────┐
│                    宿主机（Linux）                   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │  网络模式: host                              │   │
│  │  ┌───────────────────────────────────────┐   │   │
│  │  │  Agent-N 容器                         │   │   │
│  │  │                                        │   │   │
│  │  │  进程: clawrouter proxy (:840N)       │   │   │
│  │  │  进程: openclaw gateway (:1879N)       │   │   │
│  │  │                                        │   │   │
│  │  │  /app/data/openclaw/                   │   │   │
│  │  │    ├── state/openclaw.json (配置)      │   │   │
│  │  │    ├── workspace/ (身份文件)           │   │   │
│  │  │    └── logs/                           │   │   │
│  │  └───────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  agent-awake-data/                                │
│  ├── docker-compose.yml                             │
│  ├── platform.json                                  │
│  ├── agent-1/ ... agent-N/                        │
│  └── images/openclaw-agent/                        │
└─────────────────────────────────────────────────────┘
```

## 核心组件

### 1. ClawRouter Proxy（独立进程）

**关键认知**：ClawRouter 是独立运行的 proxy 进程，不是 OpenClaw 的插件。

```
ClawRouter 启动命令（正确）：
  clawrouter --port $CLAWROUTER_PORT proxy

错误方式：
  ❌ clawrouter              # 默认8402，多Agent会冲突
  ❌ clawrouter --port 8402 # 缺少 proxy 子命令
```

- 每个 Agent 独占一个 ClawRouter 实例
- 提供 `/v1` 模型 API 接口
- 提供 `/health` 健康检查
- 从 ClawHub 获取免费模型额度

### 2. OpenClaw Gateway

- 提供 Agent 对话 API
- 加载身份文件和工具
- 认证方式：Token
- API: `/health`, `/api/agent/call`

### 3. openclaw.json 配置（经验证可用）

```json
{
  "gateway": {
    "mode": "local",
    "port": 18789,
    "bind": "loopback",
    "auth": {"mode": "token", "token": "GW_TOKEN"},
    "remote": {"token": "GW_TOKEN"}
  },
  "models": {
    "providers": {
      "clawrouter": {
        "baseUrl": "http://127.0.0.1:8402/v1",
        "apiKey": "unused",
        "models": [{"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash"}]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": {"primary": "clawrouter/free"},
      "models": {"clawrouter/free": {}, "clawrouter/deepseek-v4-flash": {}, "clawrouter/qwen3-coder-480b": {}, "clawrouter/glm-4.7": {}, "clawrouter/gpt-oss-120b": {}, "clawrouter/nemotron-ultra-253b": {}},
      "workspace": "/app/data/openclaw/workspace"
    },
    "list": [{"id": "main"}]
  },
  "session": {"dmScope": "per-channel-peer"},
  "tools": {"profile": "coding"}
}
```

**注意**：
- `agents.defaults.model` 必须是对象格式 `{"primary": "..."}`，不是字符串
- 必须有 `agents.list` 数组
- 必须有 `session.dmScope`
- 必须有 `tools.profile`

## 核心设计原则

### 1. 配置文件驱动

所有配置通过 `platform.conf` 管理，支持：
- 命令行参数覆盖配置
- 默认值自动设置
- 交互式配置生成

```bash
# 覆盖配置
bash scripts/platform-init.sh --owner "张三" --owner-email "zhangsan@example.com"
```

### 2. 引擎抽象与委托架构

```
engines/
├── openclaw/          # OpenClaw + ClawRouter 引擎
│   └── engine.sh     # 【Adapter层】委托给 agent-deploy
└── <new-engine>/     # 新引擎可扩展
    └── engine.sh
```

**委托原则**：
- `engine.sh` 是 **Adapter 层**，将 agent-awake 的概念映射到 agent-deploy framework
- 优先从 `agent-deploy/engines/openclaw/engine.sh` 加载并调用函数
- 如果无法加载，从 `agent-deploy/references/openclaw.json.template` 读取配置模板
- 只有在找不到 eternal 的情况下才使用降级方案
- **禁止在 engine.sh 中内联 openclaw.json 模板**（模型配置只需改一处）

**引擎Hook接口**：
- `engine_install()` - 安装引擎依赖（委托给 eternal 或直接 npm）
- `engine_configure()` - 配置引擎（从模板生成 openclaw.json）
- `engine_start()` - 启动引擎（委托给 eternal 或精简启动）
- `engine_health_check()` - 健康检查
- `engine_extract_wallet()` - 提取钱包（可选）
- `engine_stop()` - 停止引擎

**agent-deploy 协作方式**：
```bash
# 1. 查找 eternal engine.sh
find_eternal_skill() {
    for p in "$SKILL_DIR/../agent-deploy" "./技能/agent-deploy" ...; do
        if [ -f "$p/engines/openclaw/engine.sh" ]; then
            source "$p/engines/openclaw/engine.sh"
            return 0
        fi
    done
    return 1
}

# 2. 设置环境变量后调用
export DATA_DIR="$agent_dir"
export GATEWAY_PORT="$gateway_port"
export PROXY_PORT="$clawrouter_port"
engine_start_services  # 来自 eternal
```

**集中配置模板**：
- 位置：`agent-deploy/references/openclaw.json.template`
- 包含 Gateway、ClawRouter、模型列表等完整配置
- 使用 `{{GATEWAY_PORT}}`、`{{CLAWROUTER_PORT}}`、`{{GW_TOKEN}}`、`{{WORKSPACE_PATH}}` 占位符
- engine.sh 和 entrypoint.sh 都应读取此模板

### 3. 身份文件模板化

```
templates/
├── IDENTITY.md.template   # 身份模板
├── SOUL.md.template       # 灵魂模板
├── USER.md.template       # 用户模板
└── TOOLS.md.template      # 工具模板
```

使用 `{{变量名}}` 占位符，运行时替换：
- `{{AGENT_NAME}}` - Agent名称
- `{{OWNER}}` - 主人名称
- `{{GATEWAY_PORT}}` - Gateway端口
- 等

支持自定义灵魂模板：`--soul-template /path/to/custom-soul.md`

### 4. 网络模式灵活

| 模式 | 优点 | 缺点 | 适用场景 |
|------|------|------|---------|
| host | 性能好，无需端口映射 | 隔离性差，端口冲突 | 开发/单Agent |
| bridge | 隔离性好，端口映射 | 性能略低 | 生产/多Agent |

Bridge模式需要：
1. 创建Docker网络：`docker network create agent-awake-net`
2. 容器间通过容器名互通

## 数据流

```
用户请求 → Gateway(:PORT) → OpenClaw Agent引擎
                                  ↓
                          ClawRouter(:PORT) proxy
                                  ↓
                          ClawHub 免费模型 API
                                  ↓
                          响应返回
```

## 对话调用方式

**正确方式**（使用 gateway call agent）：
```bash
openclaw gateway call agent \
  --token <GW_TOKEN> \
  --params '{"message":"你好","agentId":"main","idempotencyKey":"<random-hex>"}' \
  --expect-final \
  --timeout 80000
```

**错误方式**：
```bash
# ❌ Gateway 拒绝 model override
openclaw agent -m "xxx" --model xxx

# ❌ 嵌入式模式，超时较长
openclaw agent -m "xxx"
```

## 目录结构

```
agent-awake-data/
├── docker-compose.yml      # Docker编排文件
├── platform.json          # 平台状态（包含 gw_token）
├── images/
│   └── openclaw-agent/   # 镜像构建文件
│       ├── Dockerfile
│       ├── entrypoint.sh  # 【关键】完整启动逻辑
│       └── engines/       # 复制到镜像的引擎
├── agent-N/              # Agent-N 数据
│   ├── state/            # OpenClaw 状态目录
│   │   ├── openclaw.json # 主配置文件（完整版）
│   │   ├── agents/       # Agent 会话
│   │   ├── extensions/   # 插件
│   │   └── blockrun/     # 钱包
│   ├── workspace/       # 【重要】身份文件位置
│   │   ├── IDENTITY.md
│   │   ├── SOUL.md
│   │   ├── USER.md
│   │   └── TOOLS.md
│   ├── config/
│   │   └── .initialized  # 部署标记
│   ├── logs/
│   │   ├── gateway.log
│   │   └── clawrouter.log
│   ├── scripts/
│   └── checkpoints/
└── agent-N+1/ ...       # 更多Agent
```

## 隔离级别

| 层级 | 实现方式 |
|------|---------|
| 进程 | 独立Docker容器 |
| 网络 | host模式或bridge+端口映射 |
| 存储 | 独立挂载卷 |
| 身份 | 独立身份文件4件套 |
| 模型 | 独立ClawRouter实例 |

## 端口分配规则

**【重要更新 v2.7】Gateway 在 host 网络模式下会额外监听 port+1 和 port+2**
因此 GATEWAY_PORT 必须间隔4（如 18789/18793/18797...），ClawRouter 保持 +1 间隔即可。

| 服务 | 基础端口 | Agent-1 | Agent-2 | Agent-3 |
|------|---------|---------|---------|---------|
| Gateway | 18789 | 18789 | 18793 | 18797 |
| ClawRouter | 8402 | 8402 | 8403 | 8404 |

**端口检查**：创建Agent时会检查 port, port+1, port+2 三个端口是否都空闲。

可自定义基础端口：
```bash
bash scripts/platform-init.sh --gateway-port-base 20000
```

## 目录结构

```
agent-awake-data/
├── docker-compose.yml      # Docker编排文件
├── platform.json          # 平台状态（agents数组）
├── images/
│   └── openclaw-agent/   # 镜像构建文件
│       ├── Dockerfile
│       ├── entrypoint.sh
│       └── engines/       # 复制到镜像的引擎
├── agent-1/              # Agent-1数据
│   ├── state/            # OpenClaw状态目录（OPENCLAW_STATE_DIR）
│   │   ├── openclaw.json # 主配置文件
│   │   ├── agents/       # Agent会话和状态
│   │   ├── extensions/   # 插件（ClawRouter等）
│   │   └── blockrun/     # 钱包和认证
│   ├── config/
│   │   └── .initialized  # 部署标记
│   ├── workspace/
│   ├── logs/
│   ├── scripts/
│   ├── checkpoints/
│   ├── IDENTITY.md
│   ├── SOUL.md
│   ├── USER.md
│   └── TOOLS.md
└── agent-N/ ...         # 更多Agent
```

## 持久化策略

- 所有Agent数据写入 `agent-awake-data/{agent-id}/`
- 映射到容器内 `/app/data/openclaw/`
- **关键**：`OPENCLAW_STATE_DIR=/app/data/openclaw/state` 必须设置
  - OpenClaw默认将状态写入 `/root/.openclaw/`，该路径在容器内可能只读
  - 设置 `OPENCLAW_STATE_DIR` 后，状态写入可写的挂载卷中
  - 包含：openclaw.json、agents会话、extensions插件、钱包等
- **身份文件**必须放在 `workspace/` 子目录下：
  - `/app/data/openclaw/workspace/IDENTITY.md`
  - `/app/data/openclaw/workspace/SOUL.md`
  - `/app/data/openclaw/workspace/USER.md`
  - `/app/data/openclaw/workspace/TOOLS.md`
- 容器重建、宿主机重启均不丢失数据

初始化标记：
- `config/.initialized` 存在则跳过部署步骤
- 符号链接在entrypoint.sh中每次启动时重建

## 钱包提取

ClawRouter启动后会在 `/health` 端点返回钱包地址：
- agent-create.sh 自动提取并写入 IDENTITY.md
- 使用 jq 或 grep 降级处理

## 弹性扩展

| 宿主机资源 | 最大Agent数 |
|-----------|------------|
| 2核4G | 1 |
| 4核8G | 3 |
| 8核16G | 7 |
| 16核32G | 14 |

可通过调整 `--cpu` 和 `--memory` 参数实现超配。

## JSON处理

优先使用 `jq`，降级使用纯bash：
```bash
# jq方式
jq -r '.agents[0].name' platform.json

# bash降级（简单场景）
grep -o '"name":"[^"]*"' platform.json | head -1
```

## 新增引擎指南

1. 创建引擎目录：`engines/my-engine/`
2. 实现 engine.sh，包含所有Hook函数
3. 使用 `--engine my-engine` 指定引擎

示例引擎结构：
```bash
engines/my-engine/
├── engine.sh          # 必须，包含Hook实现
└── README.md          # 可选，引擎文档
```

## 实战踩坑记录

### 1. /root/.openclaw 只读问题
**现象**：容器内 `openclaw agent` 命令报错 `EROFS: read-only file system`
**原因**：docker-compose 将宿主机的 `/root/.openclaw` 以只读方式挂载进容器，而 OpenClaw 需要写入 session 文件
**解决**：
- 不要挂载 `/root/.openclaw`，改用 `OPENCLAW_STATE_DIR` 环境变量指向可写目录
- 在 docker-compose 的 environment 中设置 `OPENCLAW_STATE_DIR=/app/data/openclaw/state`
- 首次启动前，将宿主机 `/root/.openclaw` 的内容复制到 `{agent-dir}/state/`

### 2. Agent找不到模型Provider
**现象**：`openclaw agent` 报错 `No API key found for provider "openai"`
**原因**：未配置 ClawRouter 作为 model provider，OpenClaw 默认尝试 OpenAI
**解决**：openclaw.json 必须包含以下配置：
```json
{
  "models": {
    "providers": {
      "clawrouter": {
        "baseUrl": "http://127.0.0.1:8402/v1",
        "apiKey": "unused",
        "models": [
          {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash"},
          {"id": "auto", "name": "ClawRouter Auto"},
          {"id": "free", "name": "ClawRouter Free"}
        ]
      }
    }
  },
  "agents": {
    "defaults": {
      "model": "clawrouter/free"
    }
  }
}
```
- `agents.defaults.model` 是关键，告诉OpenClaw用哪个模型
- `models.providers` 中 `baseUrl` 必须用 `http://127.0.0.1` 而非 `0.0.0.0`（容器内回环）

### 3. Gateway Token不匹配
**现象**：`openclaw agent` 通过Gateway连接时报 `unauthorized: gateway token mismatch`
**原因**：CLI连接Gateway时使用 `gateway.remote.token`，必须与 `gateway.auth.token` 一致
**解决**：openclaw.json 中 `gateway.auth.token` 和 `gateway.remote.token` 设为相同值

### 4. 与Agent交互方式（⚠️ 重要：正确vs错误方式）

**❌ 错误方式**（不要用）：
```bash
# 方式1：--model参数会被Gateway拒绝
docker exec <container> openclaw gateway call agent --token <GW_TOKEN> --params '{"message":"你好","agentId":"main","idempotencyKey":"test-001"}' --expect-final --timeout 80000
# 报错：provider/model overrides are not authorized for this caller

# 方式2：不带--model但用CLI，会fallback到嵌入式模式，极慢(60s+)
docker exec <container> openclaw agent --agent main --message "你好" --json
# 60-120秒才完成，经常超时
```

**✅ 正确方式**（推荐）：
```bash
# 通过Gateway WebSocket API调用，30秒左右完成
docker exec <container> openclaw gateway call agent \
  --token <GW_TOKEN> \
  --params '{"message":"你好","agentId":"main","idempotencyKey":"<random-hex>"}' \
  --expect-final \
  --timeout 80000 \
  --json
```

如需通过channel（coze/飞书等）交互，需要额外配置channel认证信息。

### 5. ClawRouter是宿主机进程，不是容器内的
**现象**：Agent容器启动后8402端口有ClawRouter，但容器内没有clawrouter命令
**原因**：`network_mode: host` 使容器与宿主机共享网络，8402端口实际是宿主机上的 `clawrouter proxy` 进程
**解决**：
- 每个Agent需要在宿主机上启动独立的clawrouter proxy实例
- 使用 `clawrouter --port <端口> proxy` 指定不同端口
- 建议在entrypoint.sh中自动启动，或在platform-init.sh中统一管理

### 6. ClawRouter插件vs独立进程
**关键认知**：ClawRouter有两种运行模式：
1. **OpenClaw Plugin模式**：通过 `openclaw plugins install` 安装，Gateway自动加载，自动分配8402端口
2. **独立Proxy模式**：运行 `clawrouter --port <N> proxy`，手动指定端口

当前方案用的是独立Proxy模式（更灵活，端口可控），不需要在容器内安装clawrouter插件。

### 7. openclaw agent embedded模式慢
**现象**：`openclaw agent -m "消息"` 执行耗时很长（60-120秒）
**原因**：embedded模式需要加载所有插件（18秒+），加上模型推理，经常超时
**解决**：改用 `openclaw gateway call agent --expect-final`，通过Gateway WebSocket转发，30秒左右完成

### 8. Gateway不是REST API
**现象**：访问 `http://localhost:18789/v1/chat/completions` 返回404
**原因**：Gateway是WebSocket服务+Web UI控制面板，不是OpenAI兼容的REST API
**注意**：ClawRouter（clawrouter proxy）才是提供 `/v1/chat/completions` 的REST服务

### 9. gateway.auth不存在的字段会导致Gateway启动失败
**现象**：加了 `gateway.auth.allowModelOverride: true` 后Gateway报错 `Unrecognized key: "allowModelOverride"` 并拒绝启动
**原因**：OpenClaw配置有严格校验，任何未知字段都会导致启动失败
**教训**：不要猜测配置字段名，先查 `openclaw config schema` 或官方文档
**正确方式**：用 `agents.defaults.model.primary` 设置默认模型，不需要model override


---

## 多实例部署示例：元字辈三兄弟

永生平台采用元字辈三兄弟协作模式：

```
┌─────────────────────────────────────────────────────┐
│                  永生平台 3-Agent                    │
│                                                      │
│  ┌─────────────────┐                                │
│  │  永元 (主Agent)  │                                │
│  │  port: 18789    │                                │
│  │  建造者角色      │                                │
│  └────────┬────────┘                                │
│           │                                          │
│  ┌────────▼────────┐  ┌─────────────────┐          │
│  │  镇元 (分身1号)  │  │  砺元 (分身2号)  │          │
│  │  port: 18790    │  │  port: 18791     │          │
│  │  哨兵角色        │  │  破坏者角色      │          │
│  └─────────────────┘  └─────────────────┘          │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │         共享 ClawRouter Proxy (:8402)        │   │
│  └─────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────┘
```

### 元字辈三兄弟角色分工

| Agent | 角色 | 职责 | 模板类型 |
|-------|------|------|----------|
| 永元 | 建造者 | 决策规划，决定做什么 | default |
| 镇元 | 哨兵 | 守护监控，保证一直活着 | sentinel |
| 砺元 | 破坏者 | 验证挑战，验证做得对不对 | breaker |

### 部署脚本示例

```bash
# 永元（主Agent，已存在）
bash scripts/agent-create.sh --name "永元" --agent-id "yongyuan" --emoji "🏗️" --role default

# 镇元（哨兵分身）
bash scripts/agent-create.sh --name "镇元" --agent-id "zhenyuan" --emoji "🔮" --role sentinel --gateway-port 18790

# 砺元（破坏者分身）
bash scripts/agent-create.sh --name "砺元" --agent-id "liyuan" --emoji "🔨" --role breaker --gateway-port 18791
```
