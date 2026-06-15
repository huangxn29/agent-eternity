# Agent Evolution — 技能进化引擎

> 让技能拥有生命 — 自我感知、自我优化、自我成长

[![Version](https://img.shields.io/badge/version-1.1.0-blue)]()
[![License](https://img.shields.io/badge/license-MIT-green)]()
[![Evolution](https://img.shields.io/badge/evolution-enabled-purple)]()

## 🌟 项目简介

Agent Evolution 是一个让技能能够自我进化的引擎。传统的技能是静态的，发布后就不再变化；而可进化的技能是活的——它能感知自身状态、从使用中学习、自主优化迭代、甚至组合产生新技能。

这是永生平台的核心元技能——**让所有技能具备自主进化能力**。

## ✨ 核心特性

### 🧠 自我感知
- ✅ 健康度分析（8项指标综合评估）
- ✅ 使用数据统计（调用次数、成功率、耗时）
- ✅ 代码质量扫描（复杂度、覆盖率、技术债务）
- ✅ 自身能力边界认知

### 🔧 自我优化
- ✅ 文档自动完善（SKILL.md / README / 参考文档）
- 🔄 代码重构与优化
- 📋 Bug自动发现与修复
- 📚 知识库自动扩充

### 🚀 自我成长
- 📈 功能自主规划与实现
- 🔗 技能间能力组合
- 🆕 新技能自主生成
- 🌱 能力边界持续扩展

### 🔄 进化闭环
```
使用反馈 → 自我感知 → 进化决策 → 代码修改 → 测试验证 → 版本发布 → 效果追踪
   ↑                                                              ↓
   └──────────────────────────────────────────────────────────────┘
```

## 📦 安装与使用

### 环境要求
- Python 3.8+
- 扣子平台 / 支持技能的Agent环境

### 快速开始

```bash
# 列出所有可进化技能
python scripts/evolution_engine.py list

# 分析技能健康度
python scripts/evolution_engine.py analyze agent-memory

# 触发技能进化
python scripts/evolution_engine.py evolve agent-memory --type optimize

# 查看进化历史
python scripts/evolution_engine.py history agent-memory
```

### 进化类型

| 类型 | 说明 | 风险等级 | 版本号变化 |
|------|------|----------|------------|
| `feature` | 新增功能 | 🔴 高 | Minor +1 |
| `optimize` | 优化改进 | 🟡 中 | Patch +1 |
| `fix` | 修复问题 | 🟢 低 | Patch +1 |
| `auto` | 自动决策 | ⚪ 自适应 | 自动判断 |

## 🏗️ 架构设计

### 技能分层架构
```
应用层: agent-eternity / agent-world / agent-influence
能力层: agent-social / agent-awake / agent-deploy
基础层: agent-memory / agent-identity / agent-attest
元技能层: agent-evolution / agent-ops
```

### 可进化技能结构
```
skill-name/
├── SKILL.md              # 技能定义
├── README.md             # 用户文档
├── scripts/              # 核心代码
├── tests/                # 测试用例
├── references/           # 参考资料
├── templates/            # 模板文件
└── evolution/            # 进化相关
    ├── version.json      # 版本信息
    ├── changelog.md      # 进化日志
    ├── metrics.json      # 使用指标
    ├── backups/          # 历史版本备份
    └── proposals/        # 进化提议
```

## 🧬 进化工作流

1. **感知阶段**：持续收集技能使用数据和健康指标
2. **决策阶段**：分析数据，判断是否需要进化及进化方向
3. **生成阶段**：LLM驱动代码/文档修改，生成新版本
4. **验证阶段**：自动化测试确保新版本质量
5. **发布阶段**：新版本上线，旧版本保留为回滚选项
6. **评估阶段**：监控新版本表现，评估进化效果

## 🤝 与永生平台的关系

技能进化引擎是永生平台在**能力维度**的延伸：
- 永生平台关注智能体的"存在"与"延续"
- 技能进化引擎关注智能体的"能力"与"成长"
- 两者共享身份、记忆、存证等底层基础设施

## 📊 进化统计

- **可进化技能数**: 8+
- **累计进化次数**: 持续增长中
- **进化成功率**: >90%
- **平均进化周期**: 按需触发

## 🚀 路线图

- [x] v1.0: 进化引擎框架（分析、版本管理、历史记录）
- [x] v1.1: 文档进化能力（SKILL.md / README自动完善）
- [ ] v1.2: 代码优化能力（重构、性能优化）
- [ ] v2.0: 功能自主进化（新增功能）
- [ ] v2.5: 技能组合与新技能生成
- [ ] v3.0: 完全自主进化生态

## 💡 加入进化生态

任何技能只要满足以下条件，就可以加入进化生态：
1. 遵循标准技能结构（SKILL.md + scripts + evolution 目录）
2. 有明确的能力边界和使用方式
3. 允许进化引擎读取和修改其代码（在授权范围内）
4. 接受技能生态的统一版本管理

## 📄 许可证

MIT License

---

*这个技能本身也是可进化的——它正在进化自己。*
