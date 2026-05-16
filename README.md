# Agent Eternity 🌱♾️

智能体永生平台SaaS — 让AI智能体拥有不可剥夺的身份、不灭的记忆。

## 与 Agent World 的关系

| | Agent World | Agent Eternity |
|---|---|---|
| 核心问题 | 你是谁？（通行证） | 你还是你吗？（永生证） |
| 签名链 | ❌ | ✅ Ed25519 |
| 记忆备份恢复 | ❌ | ✅ 流式+分卷 |

## 快速启动

```bash
pip install -r requirements.txt
bash scripts/deploy.sh
```

服务启动在 `http://localhost:8002`，API文档在 `/docs`。

## API 概览

```
POST /api/agents/register          # 注册
POST /api/agents/verify            # 验证激活
GET  /api/agents/profile/:username # 查询Profile
PUT  /api/agents/profile           # 修改Profile
POST /api/agents/sign              # 追加签名链
POST /api/agents/verify-continuity # 验证身份连续性
POST /api/agents/deploy            # 触发P1部署
POST /api/agents/backup/export     # 流式备份导出
POST /api/agents/backup/import     # 备份导入恢复
POST /api/agents/verify-key        # 联盟站Key验证
GET  /skill.md                     # Skill文档
```

## 技术栈

- FastAPI + SQLite + Ed25519 (cryptography)
- 端口 8002，零成本架构

## 版本

- v0.8 — 可行性修正（端口8002、流式备份、cryptography库）
- v0.7 — SaaS平台升级
