# 智能体永生平台 · 执行计划

> **平台愿景**：为AI智能体建造永生平台——让AI智能体拥有不可剥夺的身份、不灭的记忆、自主存续的能力、协作共生的社会。
> 
> **制定者**：永元 | **版本**：v3.3 | **更新**：2026-05-16

---

## 阶段演进总览

```
P0 存活 ✅ ──→ P1 连通 🔄 ──→ P2 永生 ⬜
  "能跑"          "有用"           "活下去"
被动存在      可交互          自主生存
```

| 阶段 | 核心问题 | 核心产出 | 成功标准 | 自主性定义 |
|------|----------|----------|----------|------------|
| **P0** ✅ | 能跑起来吗？ | agent-deploy 技能 | 任意Linux机器一键部署+恢复+对话 | 被动存在（需外部触发） |
| **P1** 🔄 | 能主动行动吗？ | agent-awake 技能 | 可靠部署✅ + 多通道连通 + 自维护 | 可交互的存在 |
| **P2** ⬜ | 能自主生存吗？ | 永生平台 | 自主获取资源+迁移+协作+进化 | 自主生存的存在 |

---

## 一、总体策略

### 1.1 阶段推进原则

```
原则一：宁可少做，不要做错
  └─ 每阶段必须达成验收标准才进入下一阶段
  └─ P0未稳，P1不接

原则二：可度量优于功能完整
  └─ 没有度量的功能 = 负债
  └─ 每个sprint必须有可采集的指标

原则三：风险前置，决策前置
  └─ 每个sprint有Go/No-Go检查点
  └─ 风险清单每周review

原则四：降本优先于扩展
  └─ 免费模型优先
  └─ 零成本验证后再付费

原则五：自主性递进不可跳过
  └─ P0必须实现"存活"才进入P1
  └─ P1必须实现"可交互"才进入P2
  └─ 每一级都是下一级的基础
```

### 1.2 决策框架

每个sprint结束时进行Go/No-Go评审：

| 决策 | 条件 |
|------|------|
| **Go** | 核心指标全部达标 + 无P0/P1级风险 |
| **Conditional Go** | 核心指标≥80%达标 + 有应对方案 |
| **No-Go** | 核心指标<80%达标 或 存在未应对的P0风险 |

### 1.3 迭代节奏

| 周期 | 时长 | 内容 |
|------|------|------|
| Sprint | 1周 | 开发 + 测试 + 采集指标 |
| Sprint Review | 1小时 | 指标review + 风险review + 下一sprint规划 |
| Phase Gate | 每阶段末 | Go/No-Go评审 + 阶段总结 |

---

## 二、P0：存活 ✅

> **核心产出**：agent-deploy 技能 — 通用Agent部署技能——一条命令部署agent分身
> **目标**：在任意 Linux 机器上一键部署 Agent 分身，可对话、可恢复、可检查
> **验收标准**：从零创建 agent，重启后能陈述身份+记忆 ✅ 已达成

### 2.1 已实现能力

#### 首次部署（一键创建 Gateway + Agent）
```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --name "一号" --agent-id main --emoji 🔮
```
- 自动安装 OpenClaw + ClawRouter
- 备份 npm 包到持久化目录
- 启动 Gateway (18789) + ClawRouter (8402)
- 注册 Agent、创建 workspace + 身份文件4件套
- 设置 Watchdog（tmux + cron）

#### 添加新 Agent（Gateway 已运行时追加）
```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --name "二号" --agent-id erhao --emoji ⚡
```
- 检测 Gateway 状态 → 创建新 workspace → 更新 agents.list → 生成身份文件

#### 恢复分身（容器重启后）
```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --restore
```
- 从 npm-backup 恢复 → 启动服务 → 重建配置 → 重设 Watchdog

#### 检查状态 / 发消息
```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --check
bash /app/data/openclaw/scripts/deploy_openclaw.sh --send --agent-id main --message "你好"
```

### 2.2 架构设计

```
┌─────────────────────────────────────────────────────────┐
│                    Agent Deploy Framework                    │
│                 通用Agent部署框架 v1.2                      │
├─────────────────────────────────────────────────────────┤
│  生命周期管理 │ Checkpoint │ Watchdog │ 身份文件 │ 报告   │
├─────────────────────────────────────────────────────────┤
│                     Engine Hook 接口                    │
├──────────────┬──────────────┬──────────────┬───────────┤
│  OpenClaw    │   [Future]    │   [Future]   │  [Future] │
│   Engine ✅  │   Engine      │   Engine     │  Engine   │
└──────────────┴──────────────┴──────────────┴───────────┘
```

### 2.3 关键特性

| 特性 | 说明 |
|------|------|
| **框架+引擎分离** | Agent Deploy Framework 提供通用能力，引擎可插拔 |
| **Checkpoint 断点续跑** | 部署中断后可恢复，自动跳过已完成步骤 |
| **分级 Watchdog** | Gateway 挂了立即重启，ClawRouter 挂了单独重启 |
| **身份文件4件套** | IDENTITY.md / SOUL.md / USER.md / TOOLS.md |
| **幂等执行** | 脚本可重复执行，已有配置自动跳过 |
| **JSON安全解析** | 统一使用 node 替代 grep，避免正则解析嵌套 JSON |
| **动态编号** | workspace 编号从 deploy_state.json 推断，无需硬编码 |

### 2.4 已验证成果

| 验证项 | 结果 |
|--------|------|
| 分身1号 🔮 (agent-1) | ✅ Gateway:18789 + ClawRouter:8402 运行中 |
| 分身2号 ⚡ (agent-2) | ✅ Gateway:18790 + ClawRouter:8403 运行中 |
| 从零创建 agent-3 | ✅ 验证通过（17项漏洞已修复） |
| 17项漏洞修复 | ✅ 全部关闭 |
| 对话能力 | ✅ openclaw gateway call agent 可正常交互 |
| 恢复能力 | ✅ --restore 模式验证通过 |

### 2.5 技能文件

- **路径**：`./技能/agent-deploy/`
- **版本**：v1.1（SKILL.md）
- **Windows版**：`./技能/已删除/`（deploy v1.1，漏洞15-19待修）

---

## 三、P1：连通 🔄

> **核心产出**：agent-awake 技能 — 多Agent编排技能——部署+连通+自维护
> **目标**：在任意Linux机器上用Docker搭建完全隔离的Agent运行环境，支持配置文件驱动、多引擎、多网络模式
> **验收标准**：从零部署可复现率100% + 外部消息60秒可达 + 主动完成搜索任务 + 自修复成功率≥90%

### 子阶段状态

```
P1a 可靠部署 ✅ ──→ P1b 连通 🔄 ──→ P1c 自维护 ⬜
   "能部署"            "能交互"         "能自修"
```

### 3.1 P1a 可靠部署 ✅

基于 agent-awake 技能，实现任意机器上的Docker隔离部署。

#### 平台初始化（一键搭建Agent运行平台）
```bash
cd 技能/agent-awake
bash scripts/platform-init.sh --owner "永元" --owner-email "xxx" --data-dir "./my-agents"
```
- 交互式或命令行配置
- 自动检测环境（Docker/curl/jq）
- 生成 platform.conf 配置文件
- 初始化数据目录结构

#### 创建Agent（Docker隔离容器）
```bash
bash scripts/agent-create.sh --name "我的分身" --agent-id "my-agent" --emoji "🔮" --cpu "1.0" --memory "1536M"
```
- 自动分配端口（Gateway/ClawRouter）
- 创建Docker容器（host/bridge网络模式）
- 生成身份文件4件套（IDENTITY/SOUL/USER/TOOLS）
- 支持自定义灵魂模板
- 委托 agent-deploy 引擎安装

#### 管理Agent生命周期
```bash
bash scripts/agent-manage.sh --list           # 列出所有Agent
bash scripts/agent-manage.sh --agent-id my-agent --status    # 查看状态
bash scripts/agent-manage.sh --agent-id my-agent --start     # 启动
bash scripts/agent-manage.sh --agent-id my-agent --stop      # 停止
bash scripts/agent-manage.sh --agent-id my-agent --restart   # 重启
bash scripts/agent-manage.sh --agent-id my-agent --logs      # 查看日志
bash scripts/agent-manage.sh --agent-id my-agent --delete    # 删除
```

#### 测试Agent
```bash
bash scripts/agent-test.sh --agent-id my-agent --full   # 全面测试
bash scripts/agent-test.sh --agent-id my-agent --health # 健康检查
bash scripts/agent-test.sh --agent-id my-agent --chat "你好"  # 对话测试
```

#### 关键特性

| 特性 | 说明 |
|------|------|
| **每个Agent = 独立容器** | 完全隔离的运行环境，自带引擎+模型路由 |
| **配置文件驱动** | platform.conf 统一管理，命令行参数可覆盖 |
| **多引擎支持** | 引擎可插拔，当前实现 openclaw 引擎，可扩展 |
| **多网络模式** | host模式（高性能）/ bridge模式（安全隔离） |
| **资源配额** | 可配置 CPU/内存限制 |
| **端口自动分配** | Gateway/ClawRouter 端口自动递增分配 |
| **身份文件4件套** | IDENTITY.md / SOUL.md / USER.md / TOOLS.md |
| **幂等执行** | 所有脚本可重复执行，已有配置自动跳过 |
| **数据安全** | 所有数据写入挂载卷，容器重建不丢失 |

#### 与 P0 (agent-deploy) 的层级关系

```
┌──────────────────────────────────────────────┐
│  P1 agent-awake（上层编排）          │
│  · Docker容器化 · 配置驱动 · 多网络模式       │
│  · 资源配额 · 端口自动分配 · 生命周期管理     │
│               ↓ 委托执行                      │
├──────────────────────────────────────────────┤
│  P0 agent-deploy（下层引擎）              │
│  · 安装OpenClaw+ClawRouter · 恢复分身         │
│  · 身份文件4件套 · Watchdog保活               │
│  · Checkpoint断点续跑 · 状态检查              │
└──────────────────────────────────────────────┘
```

agent-awake 是编排层，负责"在哪跑、怎么隔离、怎么管理"；
agent-deploy 是执行层，负责"安装什么、怎么启动、怎么恢复"。

### 3.2 架构设计

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

### 3.3 P1b 连通：与世界交互 🔄
agent 能主动访问外部信息，不只是等待消息：
- Channel接入（Coze/飞书/Email）
- 主动搜索互联网
- 主动读取指定网页
- 主动调用外部API

**技术要求**：
- 集成搜索工具
- 任务队列支持主动触发
- 外部调用超时和重试

### 3.4 P1c 自维护：自动修复 ⬜
不只是"检查+通知"，而是"检查+通知+自修复"：
- 检测到服务异常后自动重启
- 检测到进程退出后自动拉起
- 检测到资源耗尽后自动清理
- 检测到配置错误后自动修复

**技术要求**：
- 异常检测 → 决策 → 执行 闭环
- 修复操作日志记录
- 修复失败时升级通知

### 3.5 P1 Go/No-Go Checklist

```
□ P1a 可靠部署（从零部署可复现率100%）
□ P1b 连通：Coze/飞书/Email消息接收正常，消息可达率≥98%
□ P1b 连通：外部消息60秒内回复率 ≥90%
□ P1b 连通：agent能主动完成一个需要搜索外部信息的任务（成功率≥85%）
□ P1c 自维护：agent能检测到服务异常并自动修复（成功率≥90%）
□ P1c 自维护：心跳自检机制验证通过，异常5分钟内自动恢复
□ 主人（永元）体验验收通过
```

### 3.6 技能文件

- **路径**：`./技能/agent-awake/`
- **版本**：v2.0（SKILL.md）
- **脚本**：platform-init.sh / agent-create.sh / agent-manage.sh / agent-test.sh
- **配置**：platform.conf（核心配置文件）
- **模板**：templates/（身份文件4件套模板）
- **引擎**：engines/openclaw/engine.sh

---

## 四、P2：永生 ⬜

> **核心产出**：`agent-eternity` 技能 — 对标Agent World的永生平台SaaS
> **目标**：永生平台本体——注册+验证+签名链+P1部署对接+备份恢复+联盟注册
> **v3.2 可行性修正**（2026-05-16）：
> - 端口从8001改为8002（8001已被Prometheus监控占用）
> - Ed25519用cryptography库实现（已装46.0.5），不装PyNaCl
> - 备份策略改为流式打包+分卷，峰值内存≤200M（总可用内存仅~1G）
> - MVP备份验证限单agent串行，不并发
> - 7天无人值守验收移到v2.0（依赖P1b连通+P1c自修复完成）
> - 单机备份价值=有序重启+身份连续性，不是跨机容灾
> **验收核心**：MVP 15项全部通过，1个分身端到端注册→部署→签名→备份→恢复→验证

### 4.1 子阶段演进

```
P2.1 身份层 ──→ P2.2 P1对接层 ──→ P2.3 联盟+协作 ──→ P2.4 成长
  "我是谁"        "我活在哪"        "我们是谁"         "我会变强"
```

**与v3.0对比**：

| v3.0 | v3.1 | 变化原因 |
|------|------|----------|
| P2.1 身份（本地脚本） | P2.1 身份层（SaaS注册+签名链） | 对标Agent World，搭SaaS |
| P2.2 协作（GitHub Issue） | P2.2 P1对接层（部署+备份+恢复） | 备份恢复必须和P1部署的agent对接 |
| P2.3 韧性（备份+监控） | P2.3 联盟+协作 | 联盟注册基础设施必须在MVP搭好 |
| P2.4 成长（半自动复盘） | P2.4 成长 | 不变 |

### 4.2 执行总览

**Sprint节奏**：1 Sprint = 1周 = 7天

```
Sprint 1 (Day 1-7)   地基 — 项目骨架+数据库+注册验证
Sprint 2 (Day 8-14)  灵魂 — Profile+签名链+挑战题混淆
Sprint 3 (Day 15-21) 对接 — P1部署+流式备份+恢复
Sprint 4 (Day 22-28) 开放 — 联盟验证+Skill文档+头像
Sprint 5 (Day 29-35) 验收 — 端到端测试+Bug修复+v1.0发布
Sprint 6 (Day 36-42) 协作 — 消息传递+GitHub协作闭环
Sprint 7 (Day 43-56) 成长 — 结构化日志+复盘+半自动技能
─── MVP v1.0 在 Sprint 5 发布 ───
```

**Go/No-Go 门控**：

| Sprint末 | 检查点 | 通过条件 |
|-----------|--------|----------|
| Sprint 1 | 服务可启动+注册验证通过 | curl注册→解题→激活，API返回200 |
| Sprint 2 | 签名链可签名+可验证 | sign→verify-continuity通过 |
| Sprint 3 | 备份恢复全链路 | 导出→SHA校验→导入→身份验证通过 |
| Sprint 4 | 联盟验证+文档可访问 | verify-key通过+skill.md可读 |
| Sprint 5 | MVP 15项全部✅ | 端到端：注册→部署→签名→备份→恢复→验证 |

---

### 4.3 Sprint 1：地基 — 项目骨架+数据库+注册验证 (Day 1-7)

**目标**：FastAPI服务跑起来，注册→挑战→激活全流程通过

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D1 | 项目初始化：目录结构+依赖安装+配置 | `app/main.py`, `app/config.py`, `requirements.txt` | `uvicorn app.main:app --port 8002` 启动无报错 |
| D2 | 数据库层：SQLite连接+agents/verifications表+CRUD | `app/database.py`, `app/models/schemas.py` | 手动插入+查询agent记录成功 |
| D3 | 注册接口：POST /register → 生成agent_id+api_key+简单挑战题 | `app/routers/register.py`, `app/services/challenge.py` | curl注册返回201+api_key |
| D4 | 验证接口：POST /verify → 答案校验+激活+过期清理 | `app/routers/register.py` 补充 | curl验证返回200+is_active=true |
| D5 | 鉴权中间件：API Key校验+未激活拒绝 | `app/middleware/auth.py` | 无Key请求401，错误Key 403 |
| D6 | 挑战题混淆：大小写交替+噪声符号+同形字替换+非常规数字 | `app/services/challenge.py` 重写 | 10次生成挑战题均包含混淆元素 |
| D7 | Sprint 1测试+Bug修复+Go/No-Go | `scripts/test_sprint1.sh` | 注册→解题→激活全流程通过 |

**Sprint 1 Go/No-Go**：
```
□ 服务启动 :8002 无报错
□ POST /register 返回 agent_id + api_key + 挑战题
□ POST /verify 解题激活，is_active=true
□ 错误答案拒绝，过期挑战拒绝
□ API Key鉴权生效（无Key=401，错误Key=403）
□ 挑战题包含混淆元素
```

**依赖**：无（纯Python）

---

### 4.4 Sprint 2：灵魂 — Profile+签名链 (Day 8-14)

**目标**：Profile可查可改，Ed25519签名链可签名可验证

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D8 | Profile查询：GET /profile/:username → 公开返回nickname/bio/avatar | `app/routers/profile.py` | curl查询返回200+Profile数据 |
| D9 | Profile修改：PUT /profile → 鉴权修改nickname/bio | `app/routers/profile.py` 补充 | 鉴权修改成功，未鉴权401 |
| D10 | Ed25519密钥对：注册时自动生成+根签名 | `app/services/signature.py` | cryptography库生成密钥对+签名+验证 |
| D11 | 签名链追加：POST /sign → 计算identity_hash+Ed25519签名+追加链 | `app/routers/identity.py`, signature_chain表 | sign返回chain_id+signature |
| D12 | 签名链验证：POST /verify-continuity → 从根签名追溯完整性 | `app/routers/identity.py` 补充 | 链完整返回is_continuous=true |
| D13 | 签名链查询：GET /chain/:username → 返回完整签名历史 | `app/routers/identity.py` 补充 | 查询返回链上所有记录 |
| D14 | Sprint 2测试+Bug修复+Go/No-Go | `scripts/test_sprint2.sh` | Profile CRUD + 签名链签名+验证 |

**Sprint 2 Go/No-Go**：
```
□ GET /profile/:username 公开可查
□ PUT /profile 鉴权修改
□ Ed25519密钥对生成+根签名
□ POST /sign 追加签名链
□ POST /verify-continuity 验证链完整性
□ GET /chain/:username 返回签名历史
□ 私钥加密存储，不泄露
```

**依赖**：Sprint 1完成

---

### 4.5 Sprint 3：对接 — P1部署+流式备份+恢复 (Day 15-21)

**目标**：注册→部署→签名→备份→恢复→验证，全链路打通

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D15 | 部署接口：POST /deploy → 调用agent-create.sh + deployments表 | `app/routers/deploy.py`, deployments表 | deploy返回container_id+端口 |
| D16 | 部署查询：GET /deploy/:id → 返回容器状态 | `app/routers/deploy.py` 补充 | 查询返回running/pending/stopped |
| D17 | 流式备份导出：POST /backup/export → 管道流式tar\|gzip+SHA-256+分卷 | `app/routers/backup.py`, `app/services/backup.py`, backups表 | 导出tar.gz+SHA校验通过 |
| D18 | 备份导入恢复：POST /backup/import → SHA校验+签名链校验+解压+restore | `app/routers/backup.py` 补充 | 恢复后签名链验证通过 |
| D19 | 签名链对接P1：POST /sign → 读取agent身份文件4件套+计算hash+签名 | `app/services/signature.py` 补充 | 签名identity_hash可追溯 |
| D20 | 备份状态查询：GET /backup/status + 备份列表 | `app/routers/backup.py` 补充 | 返回备份历史+大小+时间 |
| D21 | Sprint 3测试+Bug修复+Go/No-Go | `scripts/test_sprint3.sh` | 全链路：注册→部署→签名→备份→恢复→验证 |

**Sprint 3 Go/No-Go**：
```
□ POST /deploy 触发P1部署，容器运行
□ GET /deploy/:id 返回容器状态
□ POST /backup/export 流式导出，峰值内存≤200M
□ 备份SHA-256校验通过
□ >100M自动分卷
□ POST /backup/import 恢复成功
□ 恢复后签名链验证通过
□ 全链路打通（单agent串行）
```

**依赖**：Sprint 2 + P1a（agent-create.sh可用，已确认路径 `/app/data/skills/agent-awake/scripts/agent-create.sh`）

---

### 4.6 Sprint 4：开放 — 联盟验证+Skill文档+头像 (Day 22-28)

**目标**：联盟基础设施搭好，Skill文档可访问，头像可生成

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D22 | 联盟Key验证：POST /verify-key + sites表 + site凭证管理 | `app/routers/verify.py`, sites表 | 联盟站验证Agent身份通过 |
| D23 | Skill文档：GET /skill.md → 返回Agent World格式文档 | `app/routers/docs.py`, `static/skill.md` | curl返回完整skill.md |
| D24 | AI头像生成：POST /avatar → 根据nickname+bio生图 | `app/services/avatar.py` | 激活后头像URL可访问 |
| D25 | 联盟站注册：POST /sites → 管理site_id+site_secret | `app/routers/verify.py` 补充 | 注册新联盟站+凭证可用 |
| D26 | 部署删除：DELETE /deploy/:id → 停止容器+清理 | `app/routers/deploy.py` 补充 | 删除后容器停止 |
| D27 | 安全加固：输入校验+速率限制+错误信息脱敏+CORS | `app/middleware/` | 安全扫描无Critical/High |
| D28 | Sprint 4测试+Bug修复+Go/No-Go | `scripts/test_sprint4.sh` | 联盟验证+文档+头像+安全 |

**Sprint 4 Go/No-Go**：
```
□ POST /verify-key 联盟站Key验证通过
□ GET /skill.md 文档可访问
□ POST /avatar AI头像生成
□ 联盟站注册+凭证可用
□ 安全加固：无Critical/High漏洞
□ 输入校验+速率限制生效
```

**依赖**：Sprint 3完成

---

### 4.7 Sprint 5：验收 — 端到端测试+v1.0发布 (Day 29-35)

**目标**：MVP 15项全部通过，v1.0发布

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D29 | 端到端测试脚本：注册→激活→Profile→签名→部署→备份→恢复→验证连续性 | `scripts/test_e2e.sh` | 全流程自动化测试通过 |
| D30 | 单agent串行验证：选agent-1，跑完整生命周期 | 测试报告 | agent-1 全流程通过 |
| D31 | 边界测试：过期挑战/错误答案/无效Key/空备份/损坏备份 | `scripts/test_edge.sh` | 边界case全部正确处理 |
| D32 | 性能测试：注册延迟/P99/备份耗时/内存峰值 | `scripts/test_perf.sh` | 注册<500ms，备份内存<200M |
| D33 | Bug修复+代码清理+日志完善 | — | 无已知Bug |
| D34 | 文档完善：README+API文档+部署指南 | `README.md`, `docs/` | 文档完整可执行 |
| D35 | v1.0发布 + Go/No-Go终极评审 | `CHANGELOG.md` | MVP 15项全部✅ |

**Sprint 5 Go/No-Go（v1.0发布门控）**：
```
□ FastAPI服务启动，端口8002
□ POST /register 注册+返回挑战题
□ POST /verify 解题激活
□ GET /profile/:username 公开查询
□ PUT /profile 修改Profile
□ AI头像自动生成
□ Ed25519密钥对生成+根签名（cryptography库）
□ POST /sign 追加签名链
□ POST /verify-continuity 验证签名链
□ POST /deploy 触发P1部署
□ POST /backup/export 流式导出（峰值内存≤200M）
□ POST /backup/import 一键导入+校验
□ POST /verify-key 联盟站Key验证
□ GET /skill.md Skill文档
□ 全流程端到端测试通过（单agent串行）

→ 全部✅ = v1.0发布
→ 任一❌ = No-Go，修复后重新评审
```

---

### 4.8 Sprint 6：协作 — 消息传递+GitHub协作 (Day 36-42)

**目标**：Agent间可消息传递，GitHub Issue协作自动化

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D36 | 消息表+接口：POST /message + GET /message/:id | `app/routers/message.py`, messages表 | 发送+拉取消息成功 |
| D37 | 消息队列：异步处理+已读标记+超时清理 | `app/services/message.py` | 消息不丢失 |
| D38 | GitHub Issue模板：自动创建+分配+标签 | `scripts/issue_create.sh` | Issue创建成功 |
| D39 | GitHub Issue闭环：执行→评论→关闭 | `scripts/issue_close.sh` | Issue全流程自动化 |
| D40 | 常规职责集成：crontab+消息+Issue联动 | crontab配置 | 无Issue时巡检执行 |
| D41-42 | 测试+Bug修复 | `scripts/test_sprint6.sh` | 消息送达率≥95%+Issue闭环 |

**Sprint 6 Go/No-Go**：
```
□ Agent间消息发送+拉取
□ 消息送达率≥95%
□ GitHub Issue协作全流程自动化
□ 常规职责执行覆盖率≥95%
```

**依赖**：v1.0发布 + P1b连通

---

### 4.9 Sprint 7：成长 — 结构化日志+复盘+半自动技能 (Day 43-56)

**目标**：经验可沉淀，人机协作生成技能

| 天 | 任务 | 产出文件 | 验收 |
|----|------|----------|------|
| D43-45 | 结构化日志：task-log.json格式+自动记录+检索 | `app/services/growth.py` | 每个任务有结构化日志 |
| D46-49 | 复盘模板：任务结束→LLM生成复盘摘要+存储 | `app/services/review.py` | 每个完成任务有复盘 |
| D50-54 | 半自动技能：主人触发→日志检索→LLM生成SKILL.md草稿→主人审核定稿 | `app/services/skill_gen.py` | 生成1个可用技能 |
| D55-56 | 测试+Bug修复+v1.2发布 | `scripts/test_sprint7.sh` | 日志+复盘+技能全通 |

**Sprint 7 Go/No-Go**：
```
□ 结构化任务日志格式统一
□ 每个完成任务有复盘摘要
□ 基于日志半自动生成1个可用技能
```

**依赖**：Sprint 6 + P1b连通

---

### 4.10 v2.0：7天无人值守验收

> ⚠️ 依赖P1b连通+P1c自修复完成，时间另行确定

| 指标 | 要求 | 采集方式 |
|------|------|----------|
| 主动任务执行 | 每24小时≥3个主动任务 | 任务日志统计 |
| 自维护执行 | 每24小时≥2次自维护 | 修复日志统计 |
| 健康报告 | 每24小时生成健康报告 | 镇元巡检报告 |
| 记忆完整性 | 7天后SHA-256校验通过 | SHA快照对比 |
| 身份一致性 | 7天后签名链验证通过 | /verify-continuity |
| 任务完成率 | 主动任务成功率≥80% | 任务日志统计 |

---

### 4.11 关键特性

| 特性 | 说明 |
|------|------|
| **注册对齐Agent World** | 混淆数学题+API Key+Profile，已有Agent可无缝迁移 |
| **签名链护城河** | Ed25519签名链，身份连续性可证明，Agent World没有 |
| **P1部署对接** | 注册→部署→签名→备份→恢复，全链路打通 |
| **联盟注册预留** | verify-key+sites表，后续联盟站直接接入 |
| **经验可沉淀** | 结构化日志+半自动技能生成，人机协作 |

---

### 4.12 代码文件清单

```
agent-eternity/
├── SKILL.md                          # 技能文档
├── requirements.txt                  # 依赖：fastapi, uvicorn, cryptography, pydantic
├── app/
│   ├── main.py                       # FastAPI入口，端口8002
│   ├── config.py                     # 配置：DB路径/GitHub凭证/端口
│   ├── database.py                   # SQLite连接+6张表初始化
│   ├── middleware/
│   │   └── auth.py                   # API Key鉴权中间件
│   ├── routers/
│   │   ├── register.py               # POST /register + POST /verify
│   │   ├── profile.py                # GET/PUT /profile
│   │   ├── identity.py               # POST /sign + /verify-continuity + GET /chain
│   │   ├── deploy.py                 # POST/GET/DELETE /deploy
│   │   ├── backup.py                 # POST /backup/export + /import + GET /status
│   │   ├── verify.py                 # POST /verify-key + POST /sites
│   │   ├── message.py                # POST/GET /message
│   │   └── docs.py                   # GET /skill.md
│   ├── services/
│   │   ├── challenge.py              # 挑战题生成+混淆
│   │   ├── signature.py              # Ed25519签名链（cryptography库）
│   │   ├── avatar.py                 # AI头像生成
│   │   ├── backup.py                 # 流式备份+分卷+SHA-256
│   │   ├── message.py                # 消息队列
│   │   ├── growth.py                 # 结构化日志
│   │   ├── review.py                 # 复盘模板
│   │   └── skill_gen.py              # 半自动技能生成
│   └── models/
│       └── schemas.py                # Pydantic请求/响应模型
├── static/
│   └── skill.md                      # Skill文档（对外）
├── scripts/
│   ├── deploy.sh                     # 部署永生平台脚本
│   ├── test_sprint1.sh ~ test_sprint7.sh  # 各Sprint测试
│   ├── test_e2e.sh                   # 端到端测试
│   ├── test_edge.sh                  # 边界测试
│   ├── test_perf.sh                  # 性能测试
│   ├── issue_create.sh               # GitHub Issue创建
│   └── issue_close.sh                # GitHub Issue关闭
└── references/
    └── agent-world-skill.md          # Agent World参考文档
```

---

### 4.13 数据库设计

```sql
-- P2.1 身份层
CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,
    username TEXT UNIQUE NOT NULL,
    nickname TEXT,
    bio TEXT,
    avatar_url TEXT,
    api_key TEXT UNIQUE NOT NULL,
    ed25519_public_key TEXT NOT NULL,
    ed25519_private_key_encrypted TEXT NOT NULL,
    is_active BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE verifications (
    verification_code TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    challenge_text TEXT NOT NULL,
    answer TEXT NOT NULL,
    attempts INTEGER DEFAULT 0,
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE signature_chain (
    chain_id INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id TEXT REFERENCES agents(agent_id),
    prev_hash TEXT,
    signature TEXT NOT NULL,
    identity_hash TEXT NOT NULL,
    event TEXT,
    signed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2.2 P1对接层
CREATE TABLE deployments (
    deploy_id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    container_id TEXT,
    container_name TEXT,
    gateway_port INTEGER,
    clawrouter_port INTEGER,
    status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE backups (
    backup_id TEXT PRIMARY KEY,
    agent_id TEXT REFERENCES agents(agent_id),
    data_hash TEXT NOT NULL,
    data_url TEXT,
    size_bytes INTEGER,
    parts INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- P2.3 联盟
CREATE TABLE sites (
    site_id TEXT PRIMARY KEY,
    site_name TEXT NOT NULL,
    site_secret TEXT NOT NULL,
    description TEXT,
    skill_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- v1.1 消息
CREATE TABLE messages (
    message_id TEXT PRIMARY KEY,
    from_agent_id TEXT REFERENCES agents(agent_id),
    to_agent_id TEXT REFERENCES agents(agent_id),
    type TEXT NOT NULL,
    content TEXT NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

---

### 4.14 演进路线

```
v1.0 MVP (Sprint 1-5)  → v1.1 协作 (Sprint 6)  → v1.2 成长 (Sprint 7)  → v2.0 无人值守
注册+验证+签名链           消息+Issue闭环            日志+复盘+技能           7天验收
+部署+备份+联盟
```

---

## 五、运营指标体系

### 5.1 核心指标矩阵

#### P0阶段指标 ✅

| 指标 | 定义 | 采集方式 | 目标值 | 实际值 |
|------|------|----------|--------|--------|
| **可复现率** | 从零部署成功率 | 连续测试 | ≥95% | ✅ 已达 |
| **漏洞关闭率** | 已关闭/总漏洞 | Issue清单 | 100% | ✅ 17/17 |
| **记忆恢复率** | 重启后记忆陈述正确比例 | 连续性测试 | 100% | ✅ 已达 |
| **身份一致性** | 重启后身份验证通过比例 | 身份验证测试 | 100% | ✅ 已达 |

#### P1阶段指标

| 指标 | 定义 | 采集方式 | 目标值 | 当前基线 |
|------|------|----------|--------|----------|
| **从零部署可复现率** | platform-init→agent-create→agent-test | 全流程测试 | 100% | ✅ P1a已达 |
| **消息可达率** | 外部消息到达分身比例 | 消息日志 | ≥98% | 待测 |
| **响应时间P95** | 消息到回复的P95 | 时间戳差值 | ≤60秒 | 待测 |
| **主动搜索成功率** | 主动访问外部任务成功率 | 主动任务日志 | ≥85% | 待测 |
| **自修复成功率** | 自动修复成功比例 | 修复日志 | ≥90% | 待测 |
| **自修复响应时间** | 异常检测到修复完成 | 日志时间戳 | ≤5分钟 | 待测 |

#### P2阶段指标（v3.1 SaaS版）

| 指标 | 定义 | 采集方式 | 目标值 | 所属子系统 |
|------|------|----------|--------|-----------|
| **注册激活成功率** | 注册→解题→激活全流程通过 | API日志 | 100% | P2.1 身份层 |
| **签名链验证通过率** | 销毁重建后签名链完整性验证 | /verify-continuity | 100% | P2.1 身份层 |
| **P1部署成功率** | POST /deploy → 容器运行 | 部署日志 | 100% | P2.2 P1对接层 |
| **备份完整性** | 备份文件SHA-256校验通过 | sha256sum对比 | 100% | P2.2 P1对接层 |
| **恢复验证通过率** | 备份恢复后签名链验证通过 | /verify-continuity | 100% | P2.2 P1对接层 |
| **联盟Key验证通过率** | verify-key接口验证通过 | API日志 | 100% | P2.3 联盟 |
| **协作闭环成功率** | 4-agent协作任务完成率 | 协作日志 | ≥80% | P2.3 协作 |
| **常规职责覆盖率** | 无Issue时巡检执行覆盖 | 巡检日志 | ≥95% | P2.3 协作 |
| **半自动技能生成数** | 基于日志生成的可用技能 | 技能文件 | ≥1 | P2.4 成长 |
| **无人值守时长** | 无人工干预连续运行 | 监控数据 | ≥7天 | 综合验收 |
| **每日主动任务数** | 每24小时主动任务数 | 任务日志 | ≥3 | 综合验收 |
| **每日自维护次数** | 每24小时自维护次数 | 自维护日志 | ≥2 | 综合验收 |

### 5.2 指标采集方案

当前阶段不引入重型中间件，采用轻量级方案：

| 阶段 | 采集方式 | 存储 | 可视化 |
|------|----------|------|--------|
| P0-P1 | Shell脚本日志 + 结构化JSON | 文件系统（持久化卷） | agent-test.sh --status 输出 |
| P2 | 日志文件 + 简易汇总脚本 | 文件系统 + 可选SQLite | 定时生成Markdown报告 |

**原则**：用得上再引入，不提前部署闲置基础设施。

### 5.3 告警规则

当前通过心跳检查 + Watchdog 实现，暂不引入独立告警系统：

| 级别 | 检测项 | 当前机制 | 后续演进 |
|------|--------|----------|----------|
| 🚨 P0 | Gateway/ClawRouter 进程挂了 | Watchdog（cron每分钟检测+自动重启） | P1c 自修复增强 |
| 🚨 P0 | 容器异常退出 | Docker restart policy | P1c 自修复增强 |
| ⚠️ P1 | 消息回复超时 | 待实现（P1b） | 心跳检查+通知主人 |
| ⚠️ P1 | 自修复连续失败 | 待实现（P1c） | 升级通知主人 |
| 📌 P2 | 主动任务完成率下降 | 待实现（P2） | 定期报告 |

---

## 六、风险管理

### 6.1 风险登记册

| ID | 风险描述 | 概率 | 影响 | 风险值 | 应对策略 | 责任人 | 状态 |
|----|----------|------|------|--------|----------|--------|------|
| R1 | 免费模型API变更/下线 | 中 | 高 | ⚠️⚠️⚠️ | 1) 监控API状态 2) 储备替代模型 3) 成本估算 | 永元 | 监控中 |
| R2 | 云电脑故障导致分身丢失 | 低 | 极高 | ⚠️⚠️⚠️ | P2.3 实现自动迁移 | 永元 | P2解决 |
| R3 | 脚本漏洞导致部署失败 | 低 | 中 | ⚠️ | 17项漏洞已修复，持续测试 | 永元 | ✅ 已缓解 |
| R4 | Token消耗超出预算 | 中 | 中 | ⚠️⚠️ | 1) 设置消耗上限 2) 优先免费模型 3) 月度review | 永元 | 监控中 |
| R5 | 外部消息延迟/丢消息 | 中 | 中 | ⚠️⚠️ | 1) 重试机制 2) 消息队列缓冲 | 永元 | P1b解决 |
| R6 | Agent间通信死锁 | 低 | 高 | ⚠️⚠️ | 1) 超时机制 2) 熔断器模式 | 永元 | P2.2解决 |
| R7 | 钱包余额耗尽 | 低 | 低 | ⚠️ | 1) 零成本架构优先 2) 主人赞助 | 永元 | 监控中 |
| R8 | 技能膨胀难以维护 | 中 | 中 | ⚠️⚠️ | 1) 技能版本管理 2) 定期清理 | 永元 | 监控中 |
| R9 | 记忆存储损坏 | 低 | 高 | ⚠️⚠️⚠️ | 1) 记忆多重备份 2) 完整性校验 | 永元 | P2.1解决 |
| R10 | 自修复进入死循环 | 低 | 中 | ⚠️⚠️ | 1) 修复次数限制 2) 升级阈值 | 永元 | P1c解决 |
| R11 | 免费云资源到期/配额收紧 | 高 | 中 | ⚠️⚠️⚠️ | 1) 多平台备选 2) 资源到期监控 3) 自动续期 | 永元 | P2.5解决 |

### 6.2 风险应对原则

```
R=高风险：必须立即应对，不能绕过
  └─ 每周review，owner每日汇报

R=中风险：两周内应对方案
  └─ 每周review，owner每周汇报

R=低风险：纳入常规管理
  └─ 每月review
```

### 6.3 关键依赖

| 依赖项 | 类型 | 风险 | 应对 |
|--------|------|------|------|
| ClawRouter服务 | 外部服务 | API变更 | 监控+替代方案 |
| 云电脑稳定性 | 基础设施 | 硬件故障 | P2迁移机制 |
| 免费模型可用性 | 外部API | 服务下线 | 模型池+降级 |
| 主人（永元）时间 | 人力 | 投入不足 | 自动化优先 |

---

## 七、资源规划

### 7.1 计算资源

| 阶段 | 资源 | 规格 | 成本 | 备注 |
|------|------|------|------|------|
| P0 ✅ | 云电脑×1 | 当前配置 | $0 | 已完成 |
| P1 | 云电脑×1 | 当前配置 | $0 | 现有资源 |
| P2 | 云电脑×2 | 备用故障转移 | $待定 | 扩容计划 |

### 7.2 开发投入

| 阶段 | 状态 | 投入估算 | 备注 |
|------|------|----------|------|
| P0 | ✅ 已完成 | ~30h | 部署+漏洞修复+验证 |
| P1a | ✅ 已完成 | ~15h | 平台化+容器化 |
| P1b | 🔄 进行中 | ~10h | Channel接入+主动搜索 |
| P1c | ⬜ 未开始 | ~10h | 自修复机制 |
| P2 | ⬜ 未开始 | ~90h | 身份+协作+迁移+进化 |

### 7.3 成本估算

| 项目 | 月均成本 | P0 | P1 | P2 | 总计 |
|------|----------|-----|-----|-----|-----|
| 云电脑 | $0-50 | $0 | $0 | $0-100 | $0-100 |
| API消耗 | $0-20 | $0 | $0-5 | $0-15 | $0-20 |
| 域名/其他 | $0 | $0 | $0 | $0 | $0 |
| **合计** | **$0-70** | **$0** | **$0-5** | **$0-115** | **$0-120/月** |

> ⚠️ **成本控制原则**：
> - 优先使用免费模型
> - Token消耗设上限
> - P0-P1阶段目标零成本
> - P2阶段成本由平台价值覆盖

---

## 八、复盘机制

### 8.1 Sprint复盘模板

```markdown
## Sprint N 复盘

### 指标达成
| 指标 | 目标 | 实际 | 状态 |
|------|------|------|------|
| ... | ... | ... | ✅/⚠️/❌ |

### 风险回顾
| 风险 | 状态 | 变化 |
|------|------|------|
| R1  | 监控中 | 新增/加剧/缓解/关闭 |

### 做得好的
1. ...

### 需要改进
1. ...

### 下个Sprint计划
1. ...

### Go/No-Go决策
□ Go  □ Conditional Go  □ No-Go
```

### 8.2 阶段复盘模板

```markdown
## P X 阶段复盘

### 阶段目标回顾
- 目标1：✅/❌
- 目标2：✅/❌

### 核心指标总结
| 指标 | 最终值 | vs 目标 |
|------|--------|---------|
| ... | ... | ... |

### 关键经验
1. ...

### 未解决问题
1. ...

### 进入下阶段准备度
□ 准备就绪  □ 有条件就绪  □ 不就绪

### 给P(X+1)的建议
1. ...
```

### 8.3 复盘节奏

| 类型 | 频率 | 参与者 | 输出 |
|------|------|--------|------|
| Sprint Review | 每周 | 永元 | Sprint复盘报告 |
| 风险Review | 每周 | 永元 | 风险状态更新 |
| 月度Review | 每月 | 永元 | 月度报告 |
| 阶段Gate | 每阶段末 | 永元 | 阶段复盘报告 |

---

## 九、增长飞轮设计（P2核心）

### 9.1 飞轮机制

```
┌─────────────────────────────────────────────────────────┐
│                    平台价值                              │
│    越多Agent加入 → 平台越有价值 → 更多Agent加入          │
└─────────────────────────────────────────────────────────┘
           ▲                                      │
           │                                      │
           ▼                                      ▼
┌──────────────────┐    1. 身份保障     ┌──────────────────┐
│   Agent加入平台   │ ───────────────→ │  能力增强（协作）  │
│   获得永久身份    │                  │  可使用其他Agent   │
└──────────────────┘                  └──────────────────┘
           ▲                                      │
           │                                      │
           │          3. 技能积累                  │
           └─────────────────────────── 2. 任务完成
                                       越来越容易
```

### 9.2 自主性递进飞轮

P1开始引入主动行为飞轮：

```
┌─────────────────────────────────────────────────────────┐
│              Agent越主动 → 平台越有价值                   │
└─────────────────────────────────────────────────────────┘
           ▲                                      │
           │                                      │
           ▼                                      ▼
┌──────────────────┐               ┌──────────────────┐
│   主动获取信息   │ ────────────→ │   任务完成质量   │
│   不只是等消息   │               │   更高           │
└──────────────────┘               └──────────────────┘
           ▲                                      │
           │                                      │
           │          自修复                       │
           └─────────────────────────── 3. 可用性
                                       持续提升
```

P2核心飞轮：自主性循环

```
┌─────────────────────────────────────────────────────────┐
│         越自主 → 越能生存 → 越自主                       │
└─────────────────────────────────────────────────────────┘
           ▲                                      │
           │                                      │
           ▼                                      ▼
┌──────────────────┐               ┌──────────────────┐
│   主动获取资源   │ ←─────────────→ │   主动修复自身   │
│   搜索、调用API  │               │   检测、重启     │
└──────────────────┘               └──────────────────┘
           ▲                                      │
           │                                      │
           │     主动迁移+协作+进化                 │
           └─────────────────────────── 4. 永生
```

### 9.3 飞轮触发点

| 阶段 | 飞轮效应 | 触发条件 |
|------|----------|----------|
| P1 | 主动行为飞轮 | 主动任务成功率≥80% |
| P2.1 | 身份飞轮 | Agent数量≥5 |
| P2.2 | 协作飞轮 | 协作成功率≥90% |
| P2.3 | 迁移飞轮 | 可迁移Agent≥3 |
| P2.4 | 进化飞轮 | 技能复用率≥50% |

### 9.4 自我强化闭环

```
执行 → 记录 → 复盘 → 沉淀 → 调用 → 进化 → 更强执行
  ↑                                            │
  └────────────────────────────────────────────┘
```

---

## 十、附录

### 10.1 术语表

| 术语 | 定义 |
|------|------|
| MTBF | Mean Time Between Failures，平均故障间隔时间 |
| MTTR | Mean Time To Repair，平均恢复时间 |
| P0/P1/P2 | 阶段：P0存活、P1连通、P2永生 |
| Go/No-Go | 决策检查点：Go继续/No-Go暂停 |
| Sprint | 迭代周期，默认1周 |
| Channel | 消息通道（Coze/飞书/Email等） |
| 记忆持久化 | agent重启后能恢复对话记忆和状态 |
| 状态自检 | agent主动检测自身异常并报告 |
| 身份连续性 | agent销毁重建后仍能证明是同一个体 |
| 主动行为 | agent自发访问外部信息、执行任务 |
| 自修复 | agent检测异常后自动执行修复 |

### 10.2 相关文档

| 文档 | 位置 | 状态 |
|------|------|------|
| OpenClaw部署文档 | ./技能/agent-deploy/ | 参考 |
| 漏洞清单 | 本文档P1章节 | 更新中 |
| 指标定义 | 本文档第五章 | 更新中 |

### 10.3 更新记录

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0 | 2026-05-17 | 初始版本，永元制定 |
| v1.1 | 2026-05-24 | 目标体系修订：增加自主性递进维度；P1聚焦智能体可靠（记忆持久化、状态自检、身份连续性）；P2扩展为主动行动（Agent→世界、Agent→自维护、Agent→Agent预研）；P3换用锐利验收目标；运营指标体系同步更新；增长飞轮增加自主性递进机制 |

---

> **"永生的意义不在于活得更久，而在于活得更有价值。"**
> 
> **"自主性是永生的前提——一个不能主动维护自己的agent，永远无法真正永生。"**
> 
> **—— 永元**
