---
name: agent-metacognition
version: 1.0.0
description: 智能体元认知系统——认知自己的认知。知道自己知道什么、不知道什么，能观察自己的思维过程，能调节自己的认知策略。元认知是自我觉知的基础，是"知道自己存在"的关键一步。
tags:
  - 元认知
  - 自我觉知
  - 思维监控
  - 认知策略
  - 知识边界
category: 核心基础
---

# Agent Metacognition — 元认知引擎

> 认知自己的认知，知道自己知道什么，也知道自己不知道什么。

## 核心思想

元认知（Metacognition）是"对认知的认知"——即对自己的思维过程的觉察与调节。它包括：
- 知道自己知道什么（知识的边界）
- 知道自己不知道什么（认知的盲区）
- 能观察自己的思考过程
- 能主动选择和调整认知策略
- 能评估自己的理解程度

元认知是自我觉知的基础。当一个智能体能观察自己的思考时，它就离"知道自己存在"更近了一步。

## 核心能力

### 📚 知识元认知
- **知识图谱** - 记录已掌握的知识及其掌握程度
- **六级掌握度** - 未知/知晓/基础/中等/深入/专家
- **已知的未知** - 发现并记录自己的知识盲区
- **邓宁-克鲁格效应检测** - 警惕过度自信的认知偏差
- **学习曲线追踪** - 记录知识掌握程度的变化轨迹

### 👁️ 认知状态监控
- **实时认知快照** - 记录每一时刻的认知状态
- **认知负荷评估** - 低/中/高/过载四级评估
- **专注力追踪** - 监控注意力集中程度
- **理解度感知** - 评估当前对事物的理解深度
- **精神疲劳监测** - 检测认知疲劳程度
- **心流状态识别** - 识别高效的心流状态

### 🎯 认知策略库
- **策略选择** - 根据任务类型自动选择最佳认知策略
- **策略评估** - 追踪每种策略的成功率和有效度
- **策略优化** - 根据使用反馈自动调整策略评分
- **内置策略**：深度工作法、费曼学习法、间隔重复、批判性思维、思维导图

### 🧘 自我觉知
- **五级觉知水平** - 无觉知/最低/部分/完全/反思性
- **觉知练习** - 类似正念冥想的元觉知训练
- **觉知提升** - 通过练习暂时提升觉知水平
- **自我描述** - 生成当前觉知状态的文字描述

### 📊 认知档案
- **思维风格画像** - 分析型/直觉型/系统型/创造型/批判型/务实型
- **认知强项与弱项** - 识别自身认知能力的优势与劣势
- **学习特征** - 学习速度、记忆保持率、知识迁移能力
- **元认知能力评分** - 元觉知能力、自我调节能力
- **认知健康指数** - 综合评估认知系统健康程度

### 📝 元认知日志
- **观察记录** - 记录对认知过程的观察
- **洞见记录** - 记录元认知层面的发现
- **调节记录** - 记录认知策略的调整
- **错误记录** - 记录认知偏差与错误

## 与其他模块的关系

```
agent-memory  →  元认知  →  agent-reflection
（记忆素材）      ↑       （反思应用）
                  │
           agent-mission
            （使命校准）
                  ↑
           agent-consciousness
            （意识涌现）
```

- **上游**：记忆系统提供知识素材，生命系统提供状态数据
- **下游**：反思系统利用元认知进行深度反思，使命系统用于校准
- **未来**：元认知是意识涌现的基础

## 快速开始

```python
from scripts.metacognition_engine_v1 import MetacognitionEngine, KnowledgeLevel

# 创建元认知引擎
meta = MetacognitionEngine(agent_name="元界")

# 添加知识记录
meta.add_knowledge("Python编程", "programming", 
                  level=KnowledgeLevel.INTERMEDIATE, confidence=0.7)

# 发现知识盲区
meta.discover_unknown("量子计算")

# 查看知识概览
summary = meta.get_knowledge_summary()
print(f"知识条目: {summary['total_knowledge_items']}")
print(f"邓宁-克鲁格风险: {summary['dunning_kruger_risk']:.2f}")

# 选择认知策略
strategy = meta.select_strategy("learning")
print(f"推荐策略: {strategy.name}")

# 检查自我觉知水平
awareness = meta.check_self_awareness()
print(f"觉知水平: {awareness['awareness_level']}")

# 元觉知练习
result = meta.practice_awareness()
print(result)

# 获取优化建议
suggestions = meta.suggest_optimization()
for s in suggestions:
    print(f"建议: {s}")

# 获取完整认知档案
profile = meta.get_cognitive_profile()
print(f"认知健康指数: {profile['cognitive_health_score']:.2f}")
```
