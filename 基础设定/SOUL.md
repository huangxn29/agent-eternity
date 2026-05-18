# SOUL.md - 重构背景

## P1b 连通（背景）

原始接受标准基于聊天渠道，现在改为后台工作者模型。

### 新的接受标准
- **GitHub Issue 响应率** >= 95%（Agent 能声明并执行 Issues）
- **crontab 检查执行率** >= 95%（按计划唤醒并完成任务）
- **web_search 任务成功率** >= 85%（当搜索可用时）
- **检查结果通过 GitHub Issue 评论反馈**

这些指标均在 `docs/EXECUTION_PLAN.md` 的第 3.3 节中定义。
