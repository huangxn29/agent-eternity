# Agent Deploy — 通用架构

## 设计理念

**框架 + 引擎**：将 AI Agent 部署的通用逻辑与平台特有逻辑分离，实现一次编写、多平台运行。

## 核心架构

```
┌─────────────────────────────────────────────────────────────┐
│                        用户/Agent                            │
└─────────────────────────┬───────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent Deploy Framework                         │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                    通用层 (Framework)                    │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ 生命周期  │ │Checkpoint │ │ Watchdog  │ │  报告    │  │ │
│  │  │ 编排     │ │  断点续跑  │ │  保活     │ │  输出    │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │ │
│  │  │ 身份文件  │ │ deploy_  │ │  路径    │ │  日志    │  │ │
│  │  │  4 件套   │ │ state.json│ │  管理    │ │  函数    │  │ │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │ │
│  └─────────────────────────────────────────────────────────┘ │
│                           │                                  │
│                           ▼                                  │
│  ┌─────────────────────────────────────────────────────────┐ │
│  │                  Engine Hook 接口                        │ │
│  │                                                          │ │
│  │  engine_is_installed()   engine_install()             │ │
│  │  engine_init_config()     engine_configure()           │ │
│  │  engine_start_services()  engine_is_running()         │ │
│  │  engine_register_agent()  engine_send_message()        │ │
│  │  engine_backup()          engine_restore()              │ │
│  │  engine_get_state()       engine_verify()              │ │
│  └─────────────────────────────────────────────────────────┘ │
└───────────────────────────┬───────────────────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│   OpenClaw    │  │   [Future]    │  │   [Future]    │
│    Engine     │  │    Engine     │  │    Engine     │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ OpenClaw +     │  │               │  │               │
│ ClawRouter    │  │               │  │               │
│ 免费 token    │  │               │  │               │
│ Port: 18789   │  │               │  │               │
│ Port: 8402    │  │               │  │               │
└───────────────┘  └───────────────┘  └───────────────┘
```

## 目录结构

```
./技能/agent-deploy/
├── SKILL.md                      # 技能说明
├── install.sh                    # 安装脚本
├── scripts/
│   ├── eternal.sh               # 【通用】框架脚本 (~550行)
│   └── deploy_openclaw.sh        # 【兼容入口】OpenClaw 部署
├── engines/
│   └── openclaw/
│       ├── engine.sh             # 【引擎】OpenClaw 实现 (~500行)
│       └── engine_config.md      # OpenClaw 引擎配置说明
└── references/
    ├── architecture.md            # 本文件
    └── model_config.md           # 模型配置参考
```

## Hook 接口规范

### 必须实现的 Hook

| Hook 函数 | 返回值 | 说明 |
|-----------|--------|------|
| `ENGINE_NAME` | string | 引擎名称 |
| `ENGINE_VERSION` | string | 引擎版本 |
| `engine_init()` | void | 引擎初始化（可选） |
| `engine_is_installed()` | bool | 检查引擎是否已安装 |
| `engine_get_data_dir()` | string | 获取默认数据目录 |
| `engine_update_paths()` | void | 更新路径变量 |
| `engine_get_ports()` | string | 获取端口列表（空格分隔） |
| `engine_get_restart_cmd()` | string | 获取重启命令 |
| `engine_get_restore_cmd()` | string | 获取恢复命令 |
| `engine_is_running()` | bool | 检查服务是否运行 |
| `engine_needs_restore()` | bool | 检查是否需要恢复 |
| `engine_check_environment()` | void | 检查环境 |
| `engine_install()` | void | 安装引擎 |
| `engine_backup()` | void | 备份关键文件 |
| `engine_init_config()` | void | 初始化配置 |
| `engine_configure()` | void | 配置引擎 |
| `engine_configure_model()` | void | 配置模型 |
| `engine_start_services()` | void | 启动服务 |
| `engine_register_agent()` | void | 注册 Agent |
| `engine_restore()` | void | 从备份恢复 |
| `engine_rebuild_agents()` | void | 重建 agents |
| `engine_get_state()` | json | 获取引擎状态 |
| `engine_verify()` | bool | 验证部署 |
| `engine_check_status()` | void | 检查状态 |
| `engine_send_message()` | void | 发送消息 |

## 生命周期

### 首次部署

```
first_deploy()
├── check_environment()
├── engine_install()
├── engine_init_config()
├── engine_configure()
├── engine_configure_model()
├── engine_start_services()
├── engine_register_agent()
├── create_identity_files()  ← 通用
├── setup_watchdog()         ← 通用
├── setup_auto_restore()     ← 通用
├── save_deploy_state()      ← 通用
├── engine_verify()
└── print_report()           ← 通用
```

### 添加 Agent

```
add_agent()
├── engine_is_running()
├── engine_register_agent()
├── create_identity_files()  ← 通用
└── update_agent_in_state() ← 通用
```

### 恢复

```
restore_mode()
├── engine_restore()
├── engine_start_services()
├── engine_rebuild_agents()
├── setup_watchdog()         ← 通用
├── setup_auto_restore()     ← 通用
├── engine_verify()
└── print_report()           ← 通用
```

## 通用组件

### Checkpoint 机制

```
save_checkpoint(<step>)
load_checkpoint() → <step>
should_skip_step(<step>, <checkpoint>) → bool
```

支持断点续跑，部署可中断重启。

### Watchdog

- **tmux session**: `eternal-{engine}`
- **cron**: 每分钟检查端口
- **自动重启**: 检测到端口 down 时执行恢复命令

### 身份文件 4 件套

每个 agent workspace 包含：
- `IDENTITY.md` — 身份定义
- `SOUL.md` — 灵魂定义  
- `USER.md` — 主人信息
- `TOOLS.md` — 环境工具

### deploy_state.json

```json
{
  "version": "1.0",
  "framework_version": "1.0",
  "engine": "openclaw",
  "engine_version": "3.0",
  "created_at": "2026-05-14T20:00:00+08:00",
  "last_updated": "2026-05-14T20:00:00+08:00",
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
    // 引擎特有状态，由引擎自行管理
  }
}
```

## 持久化约定

| 目录 | 性质 | 说明 |
|------|------|------|
| /app/data/ | 持久化 | 重要数据放这里 |
| /root/ | 临时层 | 重启数据丢失 |

## 添加新引擎

1. 创建目录：`engines/<engine-name>/`
2. 实现 `engine.sh`：所有必需 hook 函数
3. 创建 `engine_config.md`：引擎配置说明
4. 更新 SKILL.md：添加引擎说明

```bash
# 示例：添加 my-agent 引擎
mkdir -p engines/my-agent/
# 编辑 engines/my-agent/engine.sh
# 编辑 engines/my-agent/engine_config.md
```

## OpenClaw 引擎架构（方案A）

```
┌─────────────────────────────────────────────────────────┐
│                     单 Gateway                           │
│  Port: 18789                                            │
│  ┌──────────────────────────────────────────────────┐  │
│  │              agents.list                          │  │
│  │  - main (一号🔮) workspace=/app/data/openclaw/    │  │
│  │  - erhao (二号⚡) workspace=/app/data/openclaw-2/  │  │
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

### 资源对比

| 指标 | v2.0 (多Gateway) | v3.0 (单Gateway) |
|------|------------------|-----------------|
| 内存 | 1.6GB | 534MB |
| Gateway 数 | 3 | 1 |
| 稳定性 | 互相 SIGTERM | 独立运行 |

## 总结

| 维度 | OpenClaw Engine |
|------|-----------------|
| 框架版本 | 1.0 |
| 引擎版本 | 3.0 |
| 架构 | 框架 + 引擎 |
| 可扩展性 | 支持多引擎 |
