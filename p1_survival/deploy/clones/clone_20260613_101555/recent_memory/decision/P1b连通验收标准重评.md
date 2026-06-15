# P1b 连通验收标准重评（2026-05-16）

## 背景
P1b连通阶段原定验收标准包括Channel接入（Coze/飞书/Email）和外部消息60秒可达，但这套标准是按永元（聊天型agent）的思路写的，套在分身身上不合适。

## 核心决策
**分身是"自主工人"而非聊天助手**，P1b验收标准应重新定义：

| 原标准 | 结论 | 原因 |
|--------|------|------|
| Channel接入（Coze/飞书/Email） | ❌ 不需要 | 分身是后台工人，不需要人类直接对话 |
| 外部消息60秒可达 | ❌ 不需要 | 没人要跟分身聊天 |
| 主动搜索互联网 | ⬜ 可选 | OpenClaw内置web.search/web.fetch，coding profile自带 |
| GitHub Issue响应 | ✅ 已实现 | 这才是分身的"消息通道" |
| crontab定时巡检 | ✅ 已实现 | 这才是分身的"主动行动" |

## P1b新验收标准建议
- 任务可达：GitHub Issue → 认领 → 执行 → 关闭（✅ 已验证）
- 主动执行：crontab定时唤醒 → 无Issue时执行常规巡检（✅ 已实现）
- 主动联网：OpenClaw web.search/web.fetch（⬜ 待验证LLM工具调用）

## OpenClaw内置联网能力
- `openclaw capability web search` — 搜索
- `openclaw capability web fetch` — 抓取网页
- coding profile自带，容器内无需额外安装
- 查看provider：`openclaw capability web providers`

## web_search配置实测结果（2026-05-16）
- ❌ `tools.web.search.provider: "duckduckgo"` 写入openclaw.json报错："unknown web_search provider: duckduckgo"
- ❌ 该配置残留在state文件会导致Gateway启动失败（Invalid config）
- ⬜ 正确方式应使用 `openclaw configure --section web` 交互式配置（未验证）
- 当前状态：web_search provider仍为selected=false，功能不可用
