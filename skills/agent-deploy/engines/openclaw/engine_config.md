# OpenClaw 引擎配置

## 概述

OpenClaw 引擎是 Agent Deploy Framework 的默认实现，提供基于 OpenClaw + ClawRouter 的 AI Agent 部署能力。

## 引擎信息

- **引擎名称**: openclaw
- **引擎版本**: 3.0
- **OpenClaw 版本**: 2026.5.3-1

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                     单 Gateway                           │
│  Port: 18789                                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              agents.list                          │  │
│  │  - main (一号🔮) workspace=/app/data/openclaw/    │  │
│  │  - erhao (二号⚡) workspace=/app/data/openclaw-2/ │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
     ┌──────────────┐         ┌──────────────┐
     │  ClawRouter   │         │   Agent 1    │
     │  Port: 8402   │◄────────│   main       │
     │  (共享)       │         │   workspace  │
     └──────────────┘         └──────────────┘
```

## 端口配置

| 服务 | 端口 | 说明 |
|------|------|------|
| Gateway | 18789 | OpenClaw Gateway HTTP 端口 |
| Proxy | 8402 | ClawRouter 代理端口 |

## 目录结构

```
/app/data/openclaw/           # 主数据目录（持久化）
├── config/
│   └── openclaw.json         # 主配置文件
├── scripts/
│   ├── eternal.sh            # Agent Deploy 通用框架
│   ├── deploy_openclaw.sh    # 兼容入口
│   └── auto_restore.sh       # 自动恢复
├── workspace/                # main agent workspace
│   ├── tasks/
│   ├── results/
│   ├── reports/
│   ├── logs/
│   └── *.md                  # 身份文件 4 件套
├── npm-backup/              # npm 包备份
│   ├── openclaw/             # OpenClaw 备份
│   └── clawrouter-npm/       # ClawRouter 备份
└── deploy_state.json         # 部署状态

/root/.openclaw/              # 运行时目录（临时）
├── openclaw.json            # -> /app/data/openclaw/config/openclaw.json
├── npm/                     # 本地 npm 包
└── agents/                  # Agent 数据
    └── <agent-id>/
        └── agent/
```

## Hook 函数实现

| Hook 函数 | 说明 | 必须 |
|-----------|------|------|
| `engine_init()` | 引擎初始化 | 可选 |
| `engine_is_installed()` | 检查引擎是否已安装 | 必须 |
| `engine_get_data_dir()` | 获取数据目录 | 必须 |
| `engine_update_paths()` | 更新路径变量 | 必须 |
| `engine_get_ports()` | 获取引擎端口列表 | 必须 |
| `engine_get_restart_cmd()` | 获取重启命令 | 必须 |
| `engine_get_restore_cmd()` | 获取恢复命令 | 必须 |
| `engine_is_running()` | 检查服务是否运行 | 必须 |
| `engine_needs_restore()` | 检查是否需要恢复 | 必须 |
| `engine_check_environment()` | 检查环境 | 必须 |
| `engine_install()` | 安装引擎 | 必须 |
| `engine_backup()` | 备份关键文件 | 必须 |
| `engine_init_config()` | 初始化配置 | 必须 |
| `engine_configure()` | 配置引擎 | 必须 |
| `engine_configure_model()` | 配置模型 | 必须 |
| `engine_start_services()` | 启动服务 | 必须 |
| `engine_register_agent()` | 注册 Agent | 必须 |
| `engine_restore()` | 从备份恢复 | 必须 |
| `engine_rebuild_agents()` | 重建 agents | 必须 |
| `engine_get_state()` | 获取引擎状态 | 必须 |
| `engine_verify()` | 验证部署 | 必须 |
| `engine_check_status()` | 检查状态 | 必须 |
| `engine_send_message()` | 发送消息 | 必须 |

## 模型配置

### 可用模型

| 模型 ID | 名称 | 用途 |
|---------|------|------|
| deepseek-v4-flash | DeepSeek V4 Flash | 通用（备选） |
| free | Free Auto-Route | **默认**，自动路由到可用免费模型 |
| qwen3-coder-480b | Qwen3 Coder 480B | 代码辅助 |
| nemotron-3-nano-omni | Nemotron 3 Nano Omni | 对话 |
| gpt-oss-120b | GPT OSS 120B | 通用 |
| deepseek-v3 | DeepSeek V3 | 通用 |
| llama-4-scout | Llama 4 Scout | 通用 |

### 添加新模型

修改 `engine_configure_model()` 函数中的 `provider_config` 变量。

## 环境变量

| 变量 | 说明 |
|------|------|
| `OPENCLAW_CONFIG` | 配置文件路径 |
| `DATA_DIR` | 主数据目录 |
| `NPM_GLOBAL_DIR` | npm 全局安装目录 |
| `NPM_DIR` | npm 本地目录 |
| `NPM_BACKUP_DIR` | npm 备份目录 |
| `GATEWAY_PORT` | Gateway 端口 |
| `PROXY_PORT` | ClawRouter 端口 |

## 实战经验

1. **config patch 不可靠**：配置变更建议用 node 直接修改 JSON
2. **symlink 保护**：`$HOME/.openclaw/openclaw.json` 必须是 symlink 指向持久目录
3. **npm 备份**：安装后立即备份到 /app/data/openclaw/npm-backup/
4. **共享 Gateway**：多 Agent 共享一个 Gateway，避免资源浪费
5. **checkpoint 机制**：部署可中断重启，自动跳过已完成步骤

## 故障排查

### Gateway 无法启动
```bash
tail -f /app/data/openclaw/workspace/logs/openclaw.log
```

### ClawRouter 无法启动
```bash
tail -f /app/data/openclaw/workspace/logs/clawrouter.log
```

### 模型调用失败
```bash
# 检查 ClawRouter 是否运行
curl http://127.0.0.1:8402/health

# 检查插件
openclaw plugins list
```

### 完全重置
```bash
rm -rf /root/.openclaw
rm -rf /app/data/openclaw/config/openclaw.json
bash /app/data/openclaw/scripts/deploy_openclaw.sh --name "一号" --agent-id main
```
