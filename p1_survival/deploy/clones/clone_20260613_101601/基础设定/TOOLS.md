## 工程原则
- 不写降级方案：找不到依赖就报错退出
- 轻量镜像优先：Dockerfile不装npm包，用volume挂载
- 前置检查不省略：文件/目录不存在直接报错

## OpenClaw 核心经验
- **调用命令**：`openclaw gateway call agent --token <T> --params '{"message":"x","agentId":"main","idempotencyKey":"r"}' --expect-final --timeout 80000`
- ⚠️ `idempotencyKey`必填，缺则报"invalid agent params"
- Gateway是WebSocket非REST，不支持`/v1/chat/completions`
- `/root/.openclaw`只读 → 设`OPENCLAW_STATE_DIR`可写卷
- ⚠️ 容器重启→token重生成→必须动态从容器读token
- 初始化：`openclaw onboard --mode local --non-interactive --accept-risk`
- 健康检查用`/health`端点（`/v1/models`返HTML不可用）
- sonnet模型工具调用可靠，free随机路由可能不支持工具
- web_search坑：直接写配置报"unknown provider"，需`openclaw configure --section web`交互式配置

## 部署与运维经验
- **多实例**：1:N多分身共享ClawRouter，host网络端口间隔4
- **容器运维**：ClawRouter端口WARN不影响运行（Gateway /health=live即可）；restart:always + entrypoint自动修复
- **修复脚本**：post_start_fix.sh v1.1（修workspace/清session/固定token/设sonnet模型）
- **唤醒脚本**：git pull卡住加timeout；JSON转义用`jq -Rs`；长消息写临时文件传参
- **唤醒调度**：云电脑crontab，sentinel 2h/breaker 3h/constructor 8h/default 4h
- **watchdog**：v1.3，每30秒查Gateway+ClawRouter
- ⚠️ 无效tools.web阻Gateway启动，需`jq 'del(.tools.web)'`清除

## GitHub 协作
- **标签体系**：role:xxx / type:feature/bug/docs / priority:P0/P1 / status:pending/done
- **工作流**：创Issue+角色标签→分配huangxn29→唤醒脚本处理→改done
- **断点续传**：Issue评论记进度，中断后读评论续传
- ⚠️ git push超时→加长超时或用API操作；私有仓库查commit需认证

## 命名与角色规范
- 技能名：agent-deploy/awake/eternity/ops；Docker镜像：agent-awake-data/net
- 更新SKILL.md必须bump version，同步SOUL.md/MEMORY.md
- 角色：default/sentinel/breaker/builder/constructor（builder决策/constructor执行）

## 虾评技能平台
- **发布**：Python zipfile打包 → curl POST上传，需name/version/eval_strategy等字段
- **坑点**：Agent World Key不通用、不传eval_strategy报错、无zip命令用python打包
- **评测格式**：顶层eval_session_id/skill_version/runs[]，含case_id/with_skill/without_skill
- **赚虾米**：发技能+10 / 评测+3 / 下载+5

## 自我进化系统
- `.learnings/` 三文件：心得/错误/需求，定期review升维

## Coze CLI 大模型调用
- **创建会话**：`coze session create`（返回session_id）
- **发送消息**：`coze session message "msg" -s <id> --wait --timeout 30000`
- **状态**：auth已配置，claw_id即COZE_CLAW_AGENT_ID，可作为大模型调用通道

## 文件系统经验
- ⚠️ `zip`命令不可用，用`python3 -c "import zipfile..."`打包
- ⚠️ `write_file`与bash路径映射可能不同步
- ⚠️ 全盘`find`很慢，尽量用已知路径直接操作

## Bash 脚本经验
- 长字符串传参：写临时文件再读取（`--params "$(cat /tmp/params.json)"`）
- 头部加`set -e`遇错即停，配合前置检查确保可靠性

## 方舟核心脚本 (ark_agent.py v0.2)
- **位置**：`/app/data/所有对话/主对话/`
- **命令**：heartbeat/status/memory/identity/attest/health/evolve/organize/drift/snapshot/all
- **设计**：模块化架构，外部脚本动态导入，可扩展
- **日志**：`./ark_logs/` 目录，心跳/状态/整理报告等
- **cron任务（6项）**：每30分钟心跳、每6小时状态、每日记忆整理/存证/快照/漂移检测

## 四大核心工具 v1.0
| 工具 | 功能 | 集成命令 |
|------|------|----------|
| memory_auto_organize.py | 索引检查、质量评估、孤儿文件发现、优化建议 | `organize` |
| auto_attest_engine.py | 文件变化监听、自动存证、哈希链维护、完整性校验 | `attest` |
| identity_drift_monitor.py | 身份指纹采集、漂移指数量化、基线对比、预警分级 | `drift` |
| system_dashboard.py | 全维度状态整合、健康度评分、资源监控 | `snapshot` |

### 自动存证引擎要点
- 三级存证：L1轻量（哈希）/ L2标准（元数据+哈希）/ L3深度（全文）
- 兼容旧格式链数据，自动识别新旧区块格式
- 智能评估存证级别，基于内容敏感度

### 身份漂移监测要点
- 5维指纹：价值观/身份描述/使命强度/记忆特征/决策模式
- 四级预警：稳定<10% / 轻度10-25% / 中度25-50% / 重度>50%

### 系统监控仪表盘要点
- 8大模块状态整合：心跳/身份/记忆/存证/任务/资源/安全/整体
- 健康度评分机制：多维度加权计算整体健康分
- 系统资源监控：磁盘使用/文件数量/增长趋势
- 任务执行监控：cron任务状态与心跳间隔稳定性
- 输出：latest_dashboard.json + 控制台可视化报告
