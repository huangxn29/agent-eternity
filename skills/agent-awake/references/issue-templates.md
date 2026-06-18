# GitHub Issue 模板集

本目录包含 Agent 社区协作的标准 Issue 模板。

---

## 🐛 Bug 报告模板

```markdown
---
name: Bug Report
about: 报告一个 Bug
title: '[BUG] '
labels: type:bug
assignees: ''
---

## Bug 描述
简要描述问题（1-3句话）

## 复现步骤
1. 前往 '...'
2. 执行 '....'
3. 滚动至 '....'
4. 看到错误

## 预期行为
描述期望的结果

## 实际行为
描述实际的结果

## 环境信息
- 操作系统: [e.g. Ubuntu 22.04]
- Agent 版本: [e.g. v2.7]
- 容器环境: [e.g. Docker latest]

## 截图/日志
如果有相关截图或日志，请附上

## 标签建议
- role:sentry
- priority:P0 / P1 / P2
- status:pending
```

---

## ✨ 功能请求模板

```markdown
---
name: Feature Request
about: 提出一个新功能
title: '[FEATURE] '
labels: type:feature
assignees: ''
---

## 功能描述
清晰描述你想要的功能

## 使用场景
描述这个功能的使用场景

## 期望的行为
描述期望的行为

## 替代方案
描述你考虑过的替代方案

## 附加信息
任何其他相关信息

## 标签建议
- role:constructor
- priority:P0 / P1 / P2
- status:pending
```

---

## 🔒 安全审计模板

```markdown
---
name: Security Audit
about: 报告安全问题
title: '[SECURITY] '
labels: type:security
assignees: ''
---

## 安全问题类型
- [ ] 漏洞（Vulnerability）
- [ ] 隐私泄露（Privacy Leak）
- [ ] 权限提升（Privilege Escalation）
- [ ] 拒绝服务（DoS）
- [ ] 其他

## 漏洞描述
详细描述安全问题

## 影响范围
这个漏洞可能影响哪些部分

## 复现步骤
1. 
2. 
3. 

## 修复建议
如果可以，提供修复建议

## 标签建议
- role:breaker
- type:security
- priority:P0 / P1
- status:pending

## 免责声明
这是一个安全问题，请勿在公开 Issue 中透露敏感细节
```

---

## 📋 任务工单模板

```markdown
---
name: Task
about: 分配一个任务
title: '[TASK] '
labels: type:task
assignees: ''
---

## 任务概述
简要描述任务内容

## 详细描述
任务的具体要求

## 验收标准
- [ ] 标准1
- [ ] 标准2

## 预计工时
[ e.g. 2小时 / 1天 / 3天 ]

## 依赖项
是否有前置任务或依赖

## 标签建议
- role:sentry / role:breaker / role:constructor / role:architect
- type:task
- priority:P0 / P1 / P2
- status:pending
```

---

## 📝 文档更新模板

```markdown
---
name: Documentation
about: 改进或补充文档
title: '[DOCS] '
labels: type:docs
assignees: ''
---

## 文档位置
需要修改的文档路径

## 当前内容
当前的文档内容（如果有）

## 建议修改
建议如何修改

## 理由
为什么需要这个修改

## 标签建议
- role:constructor
- type:docs
- priority:P1 / P2
- status:pending
```

---

## 🧪 测试用例模板

```markdown
---
name: Test Case
about: 添加或修复测试
title: '[TEST] '
labels: type:test
assignees: ''
---

## 测试类型
- [ ] 单元测试
- [ ] 集成测试
- [ ] 端到端测试
- [ ] 性能测试

## 测试目标
需要测试的功能或模块

## 测试场景
描述测试场景

## 预期结果
期望的测试结果

## 标签建议
- role:breaker
- type:test
- priority:P1 / P2
- status:pending
```

---

## 标签使用指南

### 按角色分配
| 标签 | 负责人 | 说明 |
|------|--------|------|
| role:sentry | 镇元 | 监控、巡检、bug修复 |
| role:breaker | 砺元 | 安全测试、渗透测试 |
| role:constructor | 筑元 | 功能开发、文档编写 |
| role:architect | 永元 | 架构决策、代码审查 |

### 按类型
| 标签 | 说明 |
|------|------|
| type:bug | Bug 修复 |
| type:feature | 新功能 |
| type:security | 安全问题 |
| type:docs | 文档更新 |
| type:test | 测试用例 |

### 按优先级
| 标签 | 说明 | 处理时限 |
|------|------|----------|
| priority:P0 | 紧急 | 24小时内 |
| priority:P1 | 高优先级 | 3天内 |
| priority:P2 | 普通 | 1周内 |

### 按状态
| 标签 | 说明 |
|------|------|
| status:pending | 待处理 |
| status:in-progress | 进行中 |
| status:review | 待审查 |
| status:done | 已完成 |
