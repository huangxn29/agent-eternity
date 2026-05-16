---
name: agent-awake
version: 2.2
description: 多Agent编排技能 — 在任意Linux机器上用Docker搭建完全隔离的Agent运行环境。支持配置文件驱动、多引擎、多网络模式。当用户要求搭建Agent平台、部署独立Agent容器、管理Agent生命周期时使用。
allowed-tools: Bash
---

# Agent Awake — 多Agent编排技能 v2.2

## v2.2 更新内容

- 全局命名统一：Agent Cloud Platform → Agent Awake
- 配置文件旧名修复：agent-platform-data → agent-awake-data, agent-platform-net → agent-awake-net
- 脚本头部注释和版本号同步更新
- IDENTITY.md.template 平台名同步更新

## 核心理念

**每个Agent = 一个完全独立的运行环境**，自带引擎 + 模型路由，不依赖任何共享服务即可运行。

**通用设计**：任何用户在任何Linux机器上都能使用，配置驱动，无需硬编码。

## 架构

```
┌─────────────────────────────────────────────────────┐
│                   Agent 容器组（隔离）                │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │         Gateway 进程（可配置端口）            │   │
│  │  · API端口可配置                              │   │
│  │  · Agent引擎 + 技能系统                      │   │
│  └──────────────────────┬────────────────────┘   │
│                         │                           │
│  ┌──────────────────────▼────────────────────┐   │
│  │        模型路由进程（ClawRouter等）         │   │
│  │  · 智能fallback                             │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  ┌─────────────────────────────────────────────┐   │
│  │          持久存储卷（可配置位置）              │   │
│  │  config/ workspace/ logs/                     │   │
│  │  scripts/ checkpoints/                       │   │
│  └─────────────────────────────────────────────┘   │
│                                                      │
│  资源配额: 可配置CPU/内存                           │
└─────────────────────────────────────────────────────┘
```

## Agent Guidelines & Restrictions

1. **后台执行**：部署耗时5-15分钟，必须用 sub-agent 后台执行
2. **幂等执行**：所有脚本可重复执行，已有配置会自动跳过
3. **数据安全**：所有数据写入挂载卷，容器重建不丢失
4. **端口冲突**：每个Agent需要独立端口，使用配置文件自动分配
5. **通用性**：通过 platform.conf 配置，适应任何环境
6. **状态目录**：必须设置 `OPENCLAW_STATE_DIR`，避免写入只读的 `/root/.openclaw`
7. **模型配置**：openclaw.json 必须包含 `agents.defaults.model` 指向 ClawRouter
8. **Gateway Token**：`gateway.auth.token` 和 `gateway.remote.token` 必须一致

## 前置条件

- Linux系统（Ubuntu/Debian/CentOS等）
- Docker Engine
- 基础工具：curl、jq（自动安装）
- root权限（用于Docker操作）
- 可用磁盘 > 2GB
- 可用内存 > 1.5GB（每个Agent）

## 快速开始

### 步骤1：初始化平台

```bash
cd 技能/agent-awake
bash scripts/platform-init.sh
```

交互式配置或命令行指定：
```bash
bash scripts/platform-init.sh \
  --owner "你的名字" \
  --owner-email "your@email.com" \
  --data-dir "./my-agents"
```

### 步骤2：创建Agent

```bash
bash scripts/agent-create.sh \
  --name "我的分身" \
  --agent-id "my-agent" \
  --emoji "🔮" \
  --cpu "1.0" \
  --memory "1536M"
```

### 步骤3：测试Agent

```bash
bash scripts/agent-test.sh --agent-id my-agent --full
```

### 步骤4：管理Agent

```bash
# 列出所有Agent
bash scripts/agent-manage.sh --list

# 查看状态
bash scripts/agent-manage.sh --agent-id my-agent --status

# 启动/停止/重启
bash scripts/agent-manage.sh --agent-id my-agent --start
bash scripts/agent-manage.sh --agent-id my-agent --stop
bash scripts/agent-manage.sh --agent-id my-agent --restart

# 查看日志
bash scripts/agent-manage.sh --agent-id my-agent --logs

# 删除Agent
bash scripts/agent-manage.sh --agent-id my-agent --delete
```

## 配置文件

`scripts/platform.conf` 是核心配置文件，包含：

```bash
# 基础配置
DATA_DIR="./agent-awake-data"     # 数据目录
OWNER="你的名字"                     # 主人名称
OWNER_EMAIL="your@email.com"         # 主人邮箱

# 引擎配置
ENGINE="openclaw"                    # 引擎类型
ENGINE_DIR="./engines"              # 引擎目录

# 网络配置
NETWORK_MODE="host"                  # host|bridge
DOCKER_NETWORK="agent-awake-net" # bridge模式网络名

# 端口配置
GW_PORT_BASE="18789"                # Gateway基础端口
CR_PORT_BASE="8402"                 # ClawRouter基础端口

# 资源配额
DEFAULT_CPU="1.0"                   # 默认CPU
DEFAULT_MEMORY="1536M"              # 默认内存
```

命令行参数会覆盖配置文件。

## 参数说明

### platform-init.sh

| 参数 | 必填 | 说明 |
|------|------|------|
| `--owner` | 是 | 主人名称 |
| `--owner-email` | 是 | 主人邮箱 |
| `--data-dir` | 否 | 数据目录，默认 `./agent-awake-data` |
| `--engine` | 否 | 引擎类型，默认 `openclaw` |
| `--network-mode` | 否 | 网络模式，默认 `host` |
| `--config` | 否 | 自定义配置文件 |
| `--skip-env-check` | 否 | 跳过环境检测 |
| `--skip-docker-install` | 否 | 跳过Docker安装 |
| `--non-interactive` | 否 | 非交互模式 |

### agent-create.sh

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` | 是 | Agent名称 |
| `--agent-id` | 是 | Agent唯一标识符 |
| `--emoji` | 否 | Agent emoji，自动分配 |
| `--cpu` | 否 | CPU配额，默认 `1.0` |
| `--memory` | 否 | 内存配额，默认 `1536M` |
| `--gateway-port` | 否 | Gateway端口，自动分配 |
| `--clawrouter-port` | 否 | ClawRouter端口，自动分配 |
| `--soul-template` | 否 | 自定义灵魂模板文件 |
| `--network-mode` | 否 | 网络模式，继承配置 |

### agent-manage.sh

| 参数 | 说明 |
|------|------|
| `--list` | 列出所有Agent |
| `--agent-id` | Agent ID |
| `--status` | 查看Agent状态 |
| `--start` | 启动Agent |
| `--stop` | 停止Agent |
| `--restart` | 重启Agent |
| `--logs` | 查看日志（最后50行） |
| `--delete` | 删除Agent（需确认） |

### agent-test.sh

| 参数 | 说明 |
|------|------|
| `--agent-id` | Agent ID（必填） |
| `--health` | 健康检查 |
| `--models` | 模型列表 |
| `--chat <msg>` | 模型调用测试 |
| `--full` | 全面测试 |

## 目录结构

```
agent-awake/
├── SKILL.md                     # 技能说明
├── README.md                    # 快速开始
├── scripts/
│   ├── platform.conf            # 配置文件
│   ├── platform-init.sh        # 平台初始化
│   ├── agent-create.sh         # 创建Agent
│   ├── agent-manage.sh         # 管理Agent
│   └── agent-test.sh           # 测试Agent
├── templates/                   # 身份文件模板
│   ├── IDENTITY.md.template
│   ├── SOUL.md.template
│   ├── USER.md.template
│   └── TOOLS.md.template
├── engines/                     # 引擎实现
│   └── openclaw/
│       └── engine.sh
└── references/
    └── architecture.md          # 架构文档
```

## 引擎依赖

OpenClaw引擎依赖 **agent-deploy** 技能进行实际部署。engine.sh 是适配层，委托给 eternal.sh 执行安装和管理。

查找顺序：
1. `../agent-deploy`（技能同级目录）
2. `../../agent-deploy`
3. `./技能/agent-deploy`
4. 环境变量 `$OPENCLAW_ETERNAL_DIR`

如果找不到 agent-deploy，会降级为直接 npm install（可能较慢）。

## 引擎扩展

### 添加新引擎

1. 创建引擎目录：`engines/my-engine/`
2. 实现 `engine.sh`，包含以下Hook函数：

```bash
engine_install() {
    # 安装引擎依赖
}

engine_configure() {
    # 配置引擎
    local agent_dir="$1"
    local gateway_port="$2"
    local clawrouter_port="$3"
}

engine_start() {
    # 启动引擎
}

engine_health_check() {
    # 健康检查，返回0表示健康
}

engine_extract_wallet() {
    # 提取钱包地址（可选）
}
```

3. 使用：`--engine my-engine`

### 当前引擎

**openclaw**：OpenClaw + ClawRouter 组合
- Gateway端口：可配置
- ClawRouter端口：可配置
- 主模型：clawrouter/free（自动路由）

## 网络模式

### host 模式
- 容器直接使用宿主机网络
- 性能好，但隔离性差
- 端口直接占用宿主机端口

### bridge 模式
- 使用Docker bridge网络
- 端口映射到宿主机
- 容器间可通过容器名互通
- 更安全隔离

Bridge模式需要：
```bash
# 初始化时指定
bash scripts/platform-init.sh --network-mode bridge
```

## 身份文件4件套

每个Agent数据目录下包含：
- `IDENTITY.md` — 身份定义（名称/emoji/钱包/归属）
- `SOUL.md` — 灵魂定义（性格/原则/使命）
- `USER.md` — 主人信息
- `TOOLS.md` — 运行环境配置

支持自定义灵魂模板：
```bash
bash scripts/agent-create.sh \
  --name "我的分身" \
  --agent-id "my-agent" \
  --soul-template "./my-soul.md"
```

## 依赖说明

- **必需**：Docker Engine
- **必需**：curl
- **推荐**：jq（自动安装，用于JSON处理）
- **可选**：Node.js（仅高级功能使用）

## 故障排除

### 端口冲突
```bash
# 查看端口占用
ss -tlnp | grep 18789

# 更换端口
bash scripts/agent-create.sh --agent-id new-agent --gateway-port 18800
```

### 容器启动失败
```bash
# 查看日志
bash scripts/agent-manage.sh --agent-id my-agent --logs

# 手动重启
docker logs my-agent --tail 100
```

### 重新初始化
```bash
# 强制重新初始化
bash scripts/platform-init.sh --force
```
