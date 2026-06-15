---
name: agent-awake
version: 3.3
description: 元界分身觉醒系统 - 为智能体永生设计的多Agent编排引擎。独家角色模板系统，支持哨兵/破坏者/建造师等多种人格，配合GitHub协作闭环，实现7x24小时不间断自主运转。
allowed-tools: Bash
---

# Agent Awake — 多Agent编排技能 v3.2

## v3.2 (2026-05-18)
- 【新增】三人组常规职责体系：无Issue时执行本职工作，避免空跑
- 【镇元哨兵】每2小时整点唤醒，执行6项系统巡检（容器/Gateway/身份/磁盘/日志/告警）
- 【砺元破坏者】每3小时30分唤醒，执行6项安全巡检（端口/权限/进程/模型白名单/身份文件/安全告警）
- 【筑元施工者】每8小时15分唤醒，执行6项工单检查维护（Git同步/Issue巡检/技能版本/文档匹配/维护工作/状态更新）
- 【更新】SOUL.md.template：新增常规职责章节，支持{{ROUTINE_DUTIES}}变量
- 【更新】唤醒脚本：v2.3版本，无Issue时自动附带详细常规职责说明
- 【巡检报告】各角色有标准化巡检报告模板，巡检结果自动评论到GitHub

## v3.1 (2026-05-18)
- 【重要修复】容器重启后外层身份文件丢失问题
- 【重要修复】Crontab 在云电脑而非容器内的问题
- 【新增】身份文件必须双写：workspace/ + 外层 /app/data/agents/agent-N/ 都要保留副本
- 【新增】agent-create.sh 自动设置云电脑 crontab（按角色设置不同频率）
- 【新增】fix_workspace.sh 模板：修复时必须同时恢复外层副本
- 【强调】Crontab 定时唤醒在云电脑宿主机，不在容器内
- 【角色频率映射】sentinel: `0 */2 * * *` / breaker: `30 */3 * * *` / constructor: `15 */8 * * *` / default: `0 */4 * * *`

## v3.0 (2026-05-17)
- 【核心优化】创建时做对，不是创建后再修 — 创建后初始化步骤内置到 agent-create.sh
- 【集成8个问题修复】创建流程自动处理所有已知坑点：
  1. ✅ 身份文件写到 openclaw.json 指定的 workspace 路径（动态读取）
  2. ✅ 删除 BOOTSTRAP.md（防止重新触发 onboarding）
  3. ✅ 配置模型白名单（7个确认支持工具调用的免费模型）
  4. ✅ 清 session 缓存
  5. ✅ 配置 git author
  6. ✅ 重启容器让配置生效
  7. ✅ 重启后再次修复 workspace
- 【版本更新】agent-create.sh: v2.1 → v2.2（含创建后初始化）
- 【强调】创建后初始化是关键，创建时必须执行，否则 agent 不能正常使用
- 【问题修复】ClawRouter 免费模型随机路由：白名单只保留7个支持工具调用的模型
- 【问题修复】Workspace 双路径：身份文件必须写到 openclaw.json defaults.workspace 指定的路径
- 【问题修复】Session 缓存导致 bootstrap 复发：需清 sessions/ + 删 BOOTSTRAP.md + 身份文件在正确路径
- 【问题修复】唤醒脚本 git pull 卡住：加 timeout 限制
- 【问题修复】唤醒脚本 JSON 转义：必须用 jq -Rs 构建参数
- 【问题修复】唤醒脚本直接传 Issue 内容：shell 层 GitHub API 获取后塞入消息
- 【问题修复】模型配置修改后需重启容器才生效
- 【问题修复】GitHub 协作身份区分：git config user.name 区分 + 3个独立账号目标方案
- 【新增】fix_workspace.sh 脚本：容器重建后修复 workspace 路径
- 【新增】已知坑章节：8个已验证坑点及解决方案
- 【更新】唤醒脚本模板：完整含 git pull timeout + jq JSON 构建 + Issue 内容直传

## v2.8 (2026-05-17)
- 【新增】GitHub 开源社区协作流程：Issue 分配 → 分身认领 → PR 提交
- 【新增】Issue 标签体系：role/type/priority/status 四维标签
- 【新增】分身认领规则：根据角色自动认领对应的 Issue
- 【新增】github_sync.sh 脚本：git pull + Issue 检查 + 触发 Agent
- 【新增】GitHub Issue 模板集：bug/feature/security/task/docs/test
- 【更新】唤醒脚本：加入 GitHub 同步流程，有新 Issue 时提醒 Agent
- 【更新】HEARTBEAT 模板：加入 GitHub Issue 检查清单

## v2.7 (2026-05-16)
- 【问题1修复】端口冲突：Gateway端口间隔从+1改为+4（host模式下Gateway额外监听port+1和port+2）
- 【问题2修复】身份文件持久化：创建分身时同时在外层创建副本，entrypoint启动时自动从外层恢复
- 【问题4修复】HEARTBEAT角色差异化：根据角色（哨兵/破坏者/施工者/建造者/通用）生成不同的巡检重点
- 【问题5修复】AGENT_NAME环境变量包含角色信息：如"镇元(哨兵)"
- 【问题6修复】wakeup脚本自动化生成：根据角色生成差异化的唤醒消息

## v2.6 (2026-05-16)
- 新增施工者(constructor)角色模板：工匠精神、忠实执行、效率优先、主动反馈
- 区分建造者与施工者：建造者画图纸（决策），施工者按图造物（执行）
- 元字辈完整阵容：永元(建造者)、筑元(施工者)、镇元(哨兵)、砺元(破坏者)
- 角色模板系统支持五种角色：builder/constructor/sentinel/breaker/default

## v2.5 (2026-05-16)
- 新增建造者(builder)角色模板：使命驱动、坚韧求存、深刻较真、务实建造
- 角色模板系统完整支持四种角色：建造者(builder)/哨兵(sentinel)/破坏者(breaker)/通用(default)
- agent-create.sh `--role` 参数新增 builder 选项
- SOUL.md.template 新增 builder 角色描述
- IDENTITY.md.template 角色列表更新为四种

## v2.4 (2026-05-16)
- 新增角色模板系统：支持 `--role` 参数选择分身角色
- 支持三种角色：哨兵(sentinel)/破坏者(breaker)/通用(default)
- IDENTITY.md.template 新增"团队定位"段落和"角色"字段
- SOUL.md.template 根据角色生成不同性格描述
- agent-create.sh 新增 `--role` 参数

## v2.3 (2026-05-16)
- 新增社区成员能力：分身可自主巡检 GitHub Issue/PR
- 新增 COMMUNITY.md.template：社区身份和 API 凭证模板
- 新增 HEARTBEAT.md.template：心跳检查清单模板（含社区巡检）
- 新增 platform.conf 社区配置段：GITHUB_REPO/GITHUB_PAT/COMMUNITY_ENABLED
- agent-create.sh 支持 --github-repo/--github-pat/--community 参数
- 创建分身时自动设置 cron 定时唤醒（社区巡检模式）

## v2.2 更新内容

- 全局命名统一：Agent Cloud Platform → Agent Awake
- 配置文件旧名修复：agent-platform-data → agent-awake-data, agent-platform-net → agent-awake-net
- 脚本头部注释和版本号同步更新
- IDENTITY.md.template 平台名同步更新

## 核心理念

**每个Agent = 一个完全独立的运行环境**，自带引擎 + 模型路由，不依赖任何共享服务即可运行。

**通用设计**：任何用户在任何Linux机器上都能使用，配置驱动，无需硬编码。

**开源协作**：分身通过 GitHub Issues 协作，实现任务分配、自动认领、成果提交。

## GitHub 开源社区协作流程

### 核心协作流程

```
唤醒 → git pull 最新代码 → 检查 GitHub Issues (分配给自己的) → 执行任务 → 提交成果 (PR/评论)
```

### Issue 标签体系

| 维度 | 标签 | 说明 |
|------|------|------|
| **角色** | `role:sentry` | 镇元：监控、巡检、bug修复 |
| | `role:breaker` | 砺元：安全审计、渗透测试 |
| | `role:constructor` | 筑元：功能开发、文档编写 |
| | `role:architect` | 永元：架构决策、代码审查 |
| **类型** | `type:bug` | Bug 修复 |
| | `type:feature` | 新功能 |
| | `type:security` | 安全问题 |
| | `type:docs` | 文档更新 |
| | `type:test` | 测试用例 |
| | `type:task` | 通用任务 |
| **优先级** | `priority:P0` | 紧急（24小时内处理） |
| | `priority:P1` | 高优先级（3天内处理） |
| | `priority:P2` | 普通（1周内处理） |
| **状态** | `status:pending` | 待处理 |
| | `status:in-progress` | 进行中 |
| | `status:review` | 待审查 |
| | `status:done` | 已完成 |

### 分身认领规则

| 分身 | 认领标签 | 说明 |
|------|----------|------|
| **镇元(sentinel)** | `role:sentry` + `type:bug` + `type:security` | 监控巡检、bug修复、安全告警 |
| **砺元(breaker)** | `role:breaker` + `type:test` + `type:security` | 安全审计、渗透测试、测试用例 |
| **筑元(constructor)** | `role:constructor` + `type:feature` + `type:docs` | 功能开发、文档编写 |
| **永元(architect)** | `role:architect` | 架构决策、代码审查 |

### 成果提交规范

| 成果类型 | 提交流程 |
|----------|----------|
| **代码变更** | 开分支 → 写代码 → 提PR → 等Review → 合并 |
| **报告/日志** | 评论到 Issue → 关闭 Issue |
| **PR 标题格式** | `[角色] 简要描述 (#Issue号)` |

```bash
# 示例：提交 PR
git checkout -b fix/sentinel-bug-123
# ... 修改代码 ...
git add . && git commit -m "[sentinel] 修复内存泄漏 (#123)"
git push origin fix/sentinel-bug-123
# 然后在 GitHub 上创建 PR
```

### GitHub API 常用命令

```bash
# 查看分配给自己的 Issues
curl -sL "https://api.github.com/repos/huangxn29/agent-eternity/issues?state=open&assignee=agent-zhenyuan" \
  -H "Authorization: token $GITHUB_PAT"

# 查看与自己角色相关的 Issues
curl -sL "https://api.github.com/repos/huangxn29/agent-eternity/issues?state=open&labels=role:sentry,type:bug" \
  -H "Authorization: token $GITHUB_PAT"

# 更新 Issue 状态
curl -sL -X PATCH "https://api.github.com/repos/huangxn29/agent-eternity/issues/{number}" \
  -H "Authorization: token $GITHUB_PAT" \
  -H "Content-Type: application/json" \
  -d '{"labels": ["status:in-progress"]}'

# 添加评论
curl -sL -X POST "https://api.github.com/repos/huangxn29/agent-eternity/issues/{number}/comments" \
  -H "Authorization: token $GITHUB_PAT" \
  -H "Content-Type: application/json" \
  -d '{"body": "我已认领这个任务，开始处理中..."}'
```

### 唤醒脚本模板（v2.9 改进版）

**核心改进**：git pull 加 timeout、JSON 用 jq 构建、Issue 内容直接通过 GitHub API 获取后塞入消息。

```bash
#!/bin/bash
# wakeup_agent.sh — v2.9 改进版
set -e

AGENT_ID="${1:-main}"
GITHUB_PAT="${GITHUB_PAT:-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}"
REPO="huangxn29/agent-eternity"
TOKEN="your-gateway-token"
PORT=18789

# 获取最新 Issue（assignee=自己 或指定角色标签）
ISSUE=$(curl -sL "https://api.github.com/repos/$REPO/issues?state=open&assignee=huangxn29&labels=role:sentry" \
  -H "Authorization: token $GITHUB_PAT" | jq -r '.[0] | "Issue #\(.number): \(.title)\n\(.body)"')

# 构造唤醒消息（包含 Issue 内容，让 agent 直接干活）
if [[ "$ISSUE" != "null" && -n "$ISSUE" ]]; then
  MSG="【定时巡检】你有新的 GitHub Issue 需要处理：\n\n$ISSUE\n\n请按 GitHub 协作流程处理：认领 Issue → 执行任务 → 提交 PR 或评论。"
else
  MSG="【定时巡检】你好，这是定时唤醒消息。请执行例行巡检：1) 检查 GitHub 是否有新 Issue  2) 检查日志有无异常  3) 更新状态到 MEMORY.md"
fi

# 必须用 jq -Rs 构建 JSON，禁止手动转义
MESSAGE_JSON=$(jq -n --arg m "$MSG" '{"message": $m}')

# 调用 Agent
curl -sL "http://localhost:${PORT}/v1/agent" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -X POST \
  -d "$MESSAGE_JSON"
```

**关键点**：
- `git pull` 建议加 `timeout 10` 或跳过（Issue 内容已在消息里）
- JSON 参数必须用 `jq -n --arg` 构建，换行符自动转为 `\n`
- Issue 内容在 shell 层通过 GitHub API 获取，agent 无需自己 curl

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
├── SKILL.md                     # 技能说明 (v2.9)
├── README.md                    # 快速开始
├── scripts/
│   ├── platform.conf            # 配置文件
│   ├── platform-init.sh        # 平台初始化
│   ├── agent-create.sh         # 创建Agent (v2.8 含GitHub协作)
│   ├── agent-manage.sh         # 管理Agent
│   ├── agent-test.sh           # 测试Agent
│   ├── github_sync.sh          # GitHub同步脚本 (v2.8新增)
│   └── fix_workspace.sh        # 修复workspace路径脚本 (v2.9新增)
├── templates/                   # 身份文件模板
│   ├── IDENTITY.md.template
│   ├── SOUL.md.template
│   ├── USER.md.template
│   ├── TOOLS.md.template
│   ├── COMMUNITY.md.template   # 社区身份模板
│   └── HEARTBEAT.md.template   # 心跳检查模板 (v2.8更新)
├── engines/                     # 引擎实现
│   └── openclaw/
│       └── engine.sh
└── references/
    ├── architecture.md          # 架构文档
    └── issue-templates.md       # GitHub Issue模板 (v2.8新增)
```

## fix_workspace.sh 模板【v3.1重要】

容器重启后修复 workspace 路径，**必须同时恢复外层副本**：

```bash
#!/bin/bash
# fix_workspace.sh — v2.0 容器重启后修复workspace
# 【重要】必须同时恢复外层副本，否则下次重启还是会丢

set -e
AGENT_ID="${1:-agent-N}"
WORKSPACE_PATH="/app/data/agents/$AGENT_ID/workspace"

echo "[INFO] 修复 $AGENT_ID workspace..."

# 1. 检查 workspace 目录
if [ ! -d "$WORKSPACE_PATH" ]; then
    echo "[WARN] workspace 目录不存在，创建..."
    mkdir -p "$WORKSPACE_PATH"
fi

# 2. 检查外层副本是否存在
OUTER_DIR="/app/data/agents/$AGENT_ID"
IDENTITY_OUTER="$OUTER_DIR/IDENTITY.md"

if [ ! -f "$IDENTITY_OUTER" ]; then
    echo "[ERROR] 外层身份文件丢失: $IDENTITY_OUTER"
    echo "[ERROR] 无法修复！请先手动恢复身份文件"
    exit 1
fi

# 3. 复制身份文件到 workspace（从外层副本恢复）
echo "[INFO] 复制身份文件到 workspace..."
for f in IDENTITY.md SOUL.md USER.md TOOLS.md HEARTBEAT.md COMMUNITY.md; do
    if [ -f "$OUTER_DIR/$f" ]; then
        cp "$OUTER_DIR/$f" "$WORKSPACE_PATH/$f"
        echo "[OK] $f → $WORKSPACE_PATH/$f"
    fi
done

# 4. 【关键】同步外层副本（确保下次重启前有备份）
echo "[INFO] 同步外层副本..."
for f in IDENTITY.md SOUL.md USER.md TOOLS.md HEARTBEAT.md COMMUNITY.md; do
    if [ -f "$WORKSPACE_PATH/$f" ]; then
        cp "$WORKSPACE_PATH/$f" "$OUTER_DIR/$f"
    fi
done

# 5. 删除 BOOTSTRAP.md
rm -f "$WORKSPACE_PATH/BOOTSTRAP.md"
echo "[OK] 删除 BOOTSTRAP.md"

# 6. 清 session 缓存
docker exec $AGENT_ID rm -rf /app/data/openclaw/state/agents/main/sessions/
echo "[OK] 清空 session 缓存"

echo "[OK] workspace 修复完成"
```

### Crontab 设置（云电脑宿主机）

**【重要】Crontab 在云电脑宿主机，不在容器内！**

创建 Agent 时自动在云电脑设置 crontab：

| 角色 | Crontab | 说明 |
|------|---------|------|
| sentinel | `0 */2 * * *` | 每2小时整点 |
| breaker | `30 */3 * * *` | 每3小时30分 |
| constructor | `15 */8 * * *` | 每8小时15分 |
| default | `0 */4 * * *` | 每4小时整点 |

```bash
# 手动设置 crontab
echo "0 */2 * * * /path/to/wakeup_agent-N.sh >> /var/log/agent-wakeup.log 2>&1" | crontab -
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

**【重要】身份文件必须双写**：
- workspace/ 是挂载卷，原始位置
- 外层 /app/data/agents/agent-N/ 也保留副本
- 原因：容器重启后 workspace/ 保留，但外层可能被覆盖
- 创建时自动双写，修复时也要同时恢复外层副本

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

## 已知坑（v3.1 实测验证）

### 坑0：容器重启后外层身份文件丢失【v3.1新增】
- **现象**：容器重启后，`/app/data/agents/agent-N/IDENTITY.md` 等外层文件丢失，但 workspace/ 内的保留
- **原因**：workspace/ 是挂载卷，容器重建不丢失；外层 /app/data/agents/agent-N/ 可能被覆盖
- **影响**：fix_workspace.sh 依赖外层文件恢复 workspace，缺少会导致修复失败
- **解决**：身份文件必须双写
  1. workspace/ 是挂载卷，原始位置
  2. 外层 /app/data/agents/agent-N/ 也保留副本
  3. 创建时自动复制：`cp "$AGENT_DIR/workspace/IDENTITY.md" "$AGENT_DIR/IDENTITY.md"`
  4. 修复时同时恢复外层副本
- **Crontab 注意**：唤醒定时任务在云电脑的 crontab 里，容器内没有 crontab 命令

### 坑1：ClawRouter 免费模型随机路由，部分不支持工具调用
- **现象**：`clawrouter/free` 随机路由到16个免费模型，其中3个不支持 function calling（qwen3-next-80b-a3b / mistral-small-4-119b / mistral-large-3-675b），3个不可用（nemotron系列），3个网络异常（deepseek系列）
- **影响**：agent 唤醒后只输出思考文本不执行工具，toolSummary.calls=0
- **解决**：在 openclaw.json 的 models.providers.clawrouter.models 白名单中只保留7个确认支持工具调用的模型：
  ```
  gpt-oss-120b / qwen3-coder-480b / glm-4.7 / llama-4-maverick / devstral-2-123b / gpt-oss-20b / nemotron-3-nano-omni-30b
  ```
- **测试方法**：`curl` 直接调 ClawRouter API，传 tools 参数看是否有 tool_calls 返回
- **注意**：余额$0时只能用免费模型，clawrouter/free 会从白名单自动路由

### 坑2：Workspace 双路径问题
- **现象**：身份文件写在 `/app/data/openclaw/` 下，但 OpenClaw 实际读取的是 openclaw.json defaults.workspace 指定的路径（如 `/app/data/agents/agent-N/workspace/`）
- **影响**：IDENTITY.md/SOUL.md 等文件"写了但没生效"，agent 触发 bootstrap 流程，自作主张 onboarding
- **解决**：
  1. 必须把身份文件 cp 到正确路径（`defaults.workspace` 指向的目录）
  2. 删除 BOOTSTRAP.md
  3. 运行 `fix_workspace.sh`（容器重建后必须执行）
- **自动化**：创建 `fix_workspace.sh`，容器重建后运行

### 坑3：Session 缓存导致 bootstrap 复发
- **现象**：清了 session 后首次唤醒正常，但后续唤醒又进 bootstrap
- **原因**：OpenClaw session 缓存文件在 `/app/data/openclaw/state/agents/main/sessions/`，旧 session 会触发旧流程
- **解决**：三步缺一不可：
  1. 清空 `sessions/` 目录
  2. 确保 workspace 下无 BOOTSTRAP.md
  3. 身份文件在正确路径（见坑2）

### 坑4：唤醒脚本 git pull 卡住导致超时
- **现象**：`wakeup_agent.sh` 里 `git pull origin main` 偶尔卡住不返回，导致整个脚本超时
- **原因**：git 可能弹出认证提示或网络慢
- **解决**：
  ```bash
  # 加 timeout 限制（10秒）
  timeout 10 git pull origin main || true
  ```
  或直接跳过 git pull，把 Issue 内容作为参数传给 agent

### 坑5：唤醒脚本 JSON 转义问题
- **现象**：`--params '{"message":"..."}'` 中的换行和特殊字符导致 JSON 解析失败
- **错误**：`SyntaxError: Bad control character in string literal`
- **解决**：必须用 `jq -Rs` 构建 JSON 参数，禁止手动转义
  ```bash
  MESSAGE=$(curl -sL "..." | jq -Rs '.')
  openclaw gateway call agent --token "$TOKEN" --params "$(jq -n --arg m "$MESSAGE" '{"message": $m}')"
  ```

### 坑6：唤醒脚本需要直接传 Issue 内容
- **现象**：早期唤醒脚本只告诉 agent "你有 Issue"，让 agent 自己查 GitHub，但容器内没有 git remote 也没有 curl 能力意识
- **解决**：唤醒脚本在 shell 层用 GitHub API 获取 Issue 内容，直接塞进唤醒消息
  ```bash
  ISSUE_BODY=$(curl -sL "https://api.github.com/repos/$REPO/issues/$ISSUE_NUM" \
    -H "Authorization: token $GITHUB_PAT" | jq -r '.body')
  ```

### 坑7：模型配置修改后需重启容器才生效
- **现象**：改了 openclaw.json 的 primary model，但 Gateway 还是用旧模型
- **解决**：重启容器 `docker restart agent-N`，然后运行 fix_workspace.sh

### 坑8：GitHub 协作身份区分问题
- **现状**：3个分身共用 huangxn29 的 PAT，Issue 全 assign 给同一个人
- **临时方案**：git config user.name 区分（镇元🔮 / 砺元🔨 / 筑元⚒️）
- **目标方案**：3个独立 GitHub 账号（zhenyuan-ai / liyuan-ai / zhuyuan-ai），各自 PAT，各自 identity，真正像开源社区协作（卡点：需主人手动注册3次）

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

### Agent 不读身份文件，反复 bootstrap
```bash
# 1. 确认 workspace 路径正确
cat /app/data/openclaw/config/openclaw.json | jq '.agents.defaults.workspace'

# 2. 修复 workspace（运行 fix_workspace.sh）
bash /app/data/openclaw/scripts/fix_workspace.sh --agent-id main

# 3. 清空 session 缓存
rm -rf /app/data/openclaw/state/agents/main/sessions/*

# 4. 删除 BOOTSTRAP.md
rm -f /app/data/agents/agent-1/workspace/BOOTSTRAP.md

# 5. 重启容器
docker restart agent-1
```

### 模型不执行工具
```bash
# 1. 确认白名单配置
cat /app/data/openclaw/config/openclaw.json | jq '.models.providers.clawrouter.models[].model'

# 2. 只保留7个确认支持的模型，其他删除或注释
# 3. 重启容器
docker restart agent-1
```

### 重新初始化
```bash
# 强制重新初始化
bash scripts/platform-init.sh --force
```


## 版本历史

| 版本 | 日期 | 主要变更 |
|------|------|----------|
| v1.0.0 | - | 初始版本，核心功能发布 |
