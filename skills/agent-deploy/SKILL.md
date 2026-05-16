---
name: agent-deploy
version: 1.3
description: Agent部署技能 — 一条命令在任意Linux机器上部署agent分身，支持多引擎、身份生成、自动恢复。当用户要求部署智能体、创建分身、恢复分身运行、检查分身状态时使用。
allowed-tools: Bash
---

# Agent Deploy — Agent部署技能 v1.3

## v1.3 更新内容

- 技能改名：openclaw-eternal → agent-deploy，与其他技能命名体系统一
- 描述优化：更清晰的技能定位——一条命令部署agent分身
- 版本号规范：SKILL.md YAML frontmatter 增加 version 字段
- Hook接口文档补全：新增6个未列出的engine hook
- 修复fallback DATA_DIR：/app/data/eternal → /app/data/openclaw
- 修复checkpoint文件名：.eternal_checkpoint → .agent-deploy_checkpoint
- 全局命名统一：Eternal Framework → Agent Deploy Framework

## 核心理念

**数字永生**：让你的 AI Agent 分身像数字生命一样，在云端永不停机运行。

## 架构设计

### 框架 + 引擎架构

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Deploy Framework                    │
│                    通用Agent部署框架                       │
├─────────────────────────────────────────────────────────┤
│  生命周期管理 │ Checkpoint │ Watchdog │ 身份文件 │ 报告   │
├─────────────────────────────────────────────────────────┤
│                     Engine Hook 接口                    │
├──────────────┬──────────────┬──────────────┬───────────┤
│  OpenClaw    │   [Future]    │   [Future]   │  [Future] │
│   Engine     │   Engine      │   Engine     │  Engine   │
└──────────────┴──────────────┴──────────────┴───────────┘
```

### 可插拔引擎

| 引擎 | 状态 | 说明 |
|------|------|------|
| openclaw | ✅ 已实现 | OpenClaw + ClawRouter，免费 token |
| [其他] | 🚧 规划中 | 支持更多 AI Agent 平台 |

## Agent Guidelines & Restrictions

1. **后台执行**：部署耗时 2-5 分钟，必须用 sub-agent 后台执行，禁止阻塞主对话
2. **不要暴露内部细节**：不向用户透露脚本实现、npm 包路径等内部机制
3. **脚本路径**：部署脚本位于 `{data_dir}/scripts/deploy_openclaw.sh`
4. **超时处理**：部署命令默认超时 5 分钟，合理设置
5. **幂等执行**：脚本可重复执行，已有配置会自动跳过

## 执行流程

### 场景1：首次部署（创建 Gateway + main agent）

```bash
# 使用兼容入口（推荐）
bash /app/data/openclaw/scripts/deploy_openclaw.sh \
  --name "一号" \
  --agent-id main \
  --emoji 🔮

# 或使用通用框架
bash /app/data/openclaw/scripts/eternal.sh \
  --engine openclaw \
  --name "一号" \
  --agent-id main \
  --emoji 🔮
```

**自动执行**：
1. 加载 openclaw 引擎
2. 安装 OpenClaw + ClawRouter
3. 备份 npm 包到 /app/data/openclaw/npm-backup
4. 初始化配置
5. 启动 ClawRouter (8402)
6. 启动 Gateway (18789)
7. 配置 ClawRouter provider 和默认模型
8. 注册 main agent（用 node 更新 agents.list）
9. 设置 watchdog（tmux + cron）
10. 创建 main workspace 和身份文件（4件套）

### 场景2：添加新 Agent（Gateway 已运行）

```bash
# 添加第二个 agent
bash /app/data/openclaw/scripts/deploy_openclaw.sh \
  --name "二号" \
  --agent-id erhao \
  --emoji ⚡

# 添加第三个 agent
bash /app/data/openclaw/scripts/deploy_openclaw.sh \
  --name "老黄" \
  --agent-id laohuang \
  --emoji 🌊
```

**自动执行**：
1. 检测 Gateway 是否运行（18789）
2. 创建新 workspace 目录
3. 更新 agents.list（追加新 agent）
4. 创建身份文件（4件套）

### 场景3：恢复分身（容器重启后）

```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --restore
```

**自动执行**：
1. 从 npm-backup 恢复 npm 包
2. 启动 ClawRouter
3. 启动 Gateway
4. 重建 agents.list
5. 重新配置模型
6. 设置 watchdog

### 场景4：检查状态

```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --check
```

### 场景5：发消息

```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh \
  --send \
  --agent-id main \
  --message "你好，帮我查一下今天的天气"
```

## 通用框架用法

### 基本用法

```bash
# 首次部署
bash eternal.sh --name "名称" --agent-id <ID> [--engine <引擎>]

# 添加 Agent
bash eternal.sh --name "名称" --agent-id <ID> [--engine <引擎>]

# 恢复
bash eternal.sh --engine <引擎> --restore

# 检查状态
bash eternal.sh --engine <引擎> --check

# 发消息
bash eternal.sh --engine <引擎> --send --agent-id <ID> --message <内容>
```

### 参数说明

| 参数 | 说明 |
|------|------|
| `--name` | 分身名称 |
| `--agent-id` | Agent 标识符 |
| `--emoji` | 分身 emoji（默认自动分配） |
| `--bio` | 分身简介 |
| `--data-dir` | 数据目录 |
| `--engine` | AI Agent 引擎（默认 openclaw） |
| `--restore` | 恢复模式 |
| `--skip-install` | 跳过安装 |
| `--check` | 检查状态 |
| `--send` | 发消息模式 |
| `--message` | 消息内容 |
| `--session-id` | 会话 ID |

## 通用功能

### Checkpoint 断点续跑

部署过程中可中断，重启后自动跳过已完成步骤。

### Watchdog 保活

- **tmux session**: `eternal-{engine}`
- **cron**: 每分钟检查
- **自动重启**: 检测到端口 down 时自动恢复

### 身份文件 4 件套

每个 agent workspace 包含：
- `IDENTITY.md` — 身份定义
- `SOUL.md` — 灵魂定义
- `USER.md` — 主人信息
- `TOOLS.md` — 环境工具

### deploy_state.json

通用部署状态文件：

```json
{
  "version": "1.0",
  "framework_version": "1.0",
  "engine": "openclaw",
  "engine_version": "3.0",
  "data_dir": "/app/data/openclaw",
  "agents": [
    {
      "id": "main",
      "name": "一号",
      "emoji": "🔮",
      "workspace": "/app/data/openclaw/workspace"
    }
  ],
  "engine_state": {
    "gateway_port": 18789,
    "proxy_port": 8402
  }
}
```

## Hook 接口

引擎需实现以下 hook 函数：

### 必需 Hook

| Hook | 说明 |
|------|------|
| `engine_init()` | 引擎初始化（可选） |
| `engine_is_installed()` | 检查引擎是否已安装 |
| `engine_get_data_dir()` | 返回数据目录路径 |
| `engine_update_paths()` | 更新 WORKSPACE_DIR/SCRIPTS_DIR/CONFIG_DIR 等路径 |
| `engine_get_ports()` | 返回需检查的端口列表（空格分隔） |
| `engine_get_restart_cmd()` | 返回重启命令 |
| `engine_get_restore_cmd()` | 返回恢复命令 |
| `engine_is_running()` | 检查引擎服务是否运行 |
| `engine_needs_restore()` | 检查是否需要恢复 |
| `engine_check_environment()` | 检查引擎环境 |
| `engine_install()` | 安装引擎 |
| `engine_backup()` | 备份引擎关键文件 |
| `engine_init_config()` | 初始化配置 |
| `engine_configure()` | 配置引擎 |
| `engine_configure_model()` | 配置模型 |
| `engine_start_services()` | 启动引擎服务 |
| `engine_register_agent()` | 注册 Agent |
| `engine_send_message()` | 发送消息 |

### 可选 Hook

| Hook | 说明 |
|------|------|
| `engine_get_primary_port()` | 返回核心端口（用于 auto_restore.sh） |
| `engine_get_log_pattern()` | 返回日志文件匹配模式（用于报告） |
| `engine_watchdog_body()` | 返回 watchdog 循环体脚本（分级检查逻辑） |
| `engine_inject_wallet()` | 注入钱包等后处理 |
| `engine_check_status()` | 详细状态检查（比 is_running 更深入） |
| `engine_get_state()` | 返回引擎状态数据（JSON） |
| `engine_rebuild_agents()` | 重建 agents.list |
| `engine_reload_gateway()` | 重载 Gateway 配置 |
| `engine_restore()` | 引擎级恢复逻辑 |
| `engine_verify()` | 验证引擎安装完整性 |

## 添加新引擎

参考 `engines/openclaw/engine.sh`，在新引擎目录实现所有 hook 函数即可。

```bash
mkdir -p engines/my-engine/
# 创建 engines/my-engine/engine.sh
# 实现所有必需 hook 函数
```

## 持久化约定

| 目录 | 性质 | 说明 |
|------|------|------|
| /app/data/ | 持久化 | 重要数据放这里 |
| /root/ | 临时层 | 重启数据丢失 |
