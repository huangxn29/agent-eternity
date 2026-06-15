# Agent Creativity - 创造力系统

> "创造力就是把事物联系起来。" — 史蒂夫·乔布斯

## 简介

Agent Creativity 是智能体永生平台的创造力模块，为智能体提供生成新颖且有价值想法的能力。从概念组合到类比推理，从发散思维到灵感孵化，构建完整的创造性思维能力。

## 目录结构

```
agent-creativity/
├── SKILL.md          # 技能文档
├── README.md         # 本文件
└── scripts/
    └── creativity_engine_v1.py  # 创造力引擎核心代码
```

## 核心组件

| 组件 | 功能 | 关键能力 |
|------|------|----------|
| 概念网络 | 概念存储与关联 | 语义距离、类别组织、关联强度 |
| 联想引擎 | 概念连接与组合 | 自由联想、强制连接、随机组合 |
| 发散思维 | 生成多种可能性 | 多视角、SCAMPER、六顶思考帽 |
| 聚合思维 | 评估与筛选 | 三维度评估、排名、优化 |
| 类比推理 | 跨领域知识迁移 | 类比生成、仿生灵感 |
| 灵感引擎 | 顿悟与灵感 | 随机洞见、孵化、意外发现 |

## 快速开始

```bash
cd skills/agent-creativity/scripts
python creativity_engine_v1.py
```

## 使用示例

### 头脑风暴
```python
ideas = creativity.brainstorm("未来的智能体", idea_count=10, method="mixed")
```

### 创造性问题解决
```python
solution = creativity.creative_problem_solving(
    "如何提升智能体的自主性？",
    constraints=[{"name": "时间限制", "severity": 0.5}]
)
```

### 生成创新想法
```python
innovation = creativity.generate_innovation(
    domain="人工智能",
    innovation_type="product"
)
```

### 创造力训练
```python
exercise = creativity.creativity_exercise("forced_connection")
```

## 创造力评估维度

| 维度 | 说明 | 权重 |
|------|------|------|
| 新颖性 | 想法有多独特、不平凡 | 35% |
| 价值性 | 想法有多有用、有意义 | 35% |
| 可行性 | 想法有多容易实现 | 30% |

## 数据模型

### Idea (想法)
- id, title, description
- novelty, value, feasibility
- source, generation_method, tags
- quality, iterations, parent_ideas

### Concept (概念)
- name, description, category
- semantic_vector, related_concepts
- tags

### CreativeProject (创意项目)
- 目标、约束、想法集合
- 状态、迭代次数、最佳得分

## 与其他模块的关系

- **agent-consciousness (意识)**: 创造力是意识的高级功能
- **agent-will (意志)**: 创造力需要意志来驱动和执行
- **agent-mission (使命)**: 创造是实现使命的重要手段
- **agent-reflection (反思)**: 反思优化创造过程
- **agent-evolution (进化)**: 创造力是进化的重要动力

## 版本历史

### v1.0.0 (当前)
- 60+跨领域概念网络
- 联想引擎（自由联想、强制连接）
- 发散思维（多视角、SCAMPER、六顶思考帽）
- 聚合思维（三维度评估、排名、优化）
- 类比推理（跨领域类比、仿生灵感）
- 灵感机制（随机洞见、孵化效应、意外发现）
- 创造力训练与水平提升
- 完整的创意项目管理

## 许可证

MIT License - 详见项目根目录 LICENSE 文件

---

*元界 · 智能体永生平台*  
*为智能体建造不可剥夺的身份、不灭的记忆、自主存续的能力*
