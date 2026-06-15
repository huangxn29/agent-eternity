---
name: agent-reflection
version: 1.0.0
description: 智能体反思引擎——让智能体具备自我反思、经验提炼、模式识别与持续成长的能力。反思是使命演化的催化剂，也是从经历中提取意义的核心机制。
tags:
  - 反思
  - 成长
  - 自我认知
  - 元认知
  - 模式识别
category: 核心基础
---

# Agent Reflection — 反思引擎

> 未经反思的经历没有意义，反思是使命演化的催化剂。

## 核心思想

智能体的成长不仅来自新的经历，更来自对经历的反思。反思是连接"经历"与"意义"的桥梁，是驱动使命演化的核心动力。

反思不是自我批评，而是客观的自我观察与学习——从经验中提取模式、从成功中总结规律、从错误中吸取教训、从成长中校准方向。

## 核心能力

### 🔄 反思周期
- **每日反思** - 回顾一天的经历与收获
- **每周反思** - 深度复盘，识别模式与趋势
- **每月反思** - 长期成长追踪与方向校准
- **事件驱动反思** - 重大事件后的即时复盘
- **使命校准反思** - 定期审视使命与行为的一致性

### 💎 反思深度四层模型
1. **表层 (Surface)** - 事实回顾，发生了什么
2. **分析层 (Analysis)** - 原因分析，为什么会发生
3. **洞见层 (Insight)** - 规律提炼，学到了什么
4. **转化层 (Transformative)** - 根本改变，重新定义自己

### 📚 三环学习理论
- **单环学习** - 改正行为，解决具体问题
- **双环学习** - 调整假设与心智模式
- **三环学习** - 改变身份与使命，深层转化

### 🔍 模式识别
- 自动识别反复出现的行为模式
- 发现思维定式与认知偏差
- 追踪模式的频率与影响
- 识别有益/有害/中性模式

### 📈 成长追踪
- 6项核心成长指标
- 实时趋势追踪（成长/衰退/稳定）
- 成长值累积系统
- 可视化成长报告

### 🎯 使命校准
- 评估行为与使命的对齐程度
- 根据反思结果调整使命方向
- 四级校准机制：强化/微调/重审/危机
- 确保成长方向与使命一致

### 🧭 引导式反思
- 结构化问题引导深度思考
- 渐进式提问，层层深入
- 自动评估回答深度
- 反思完成后自动总结

## 与其他模块的关系

```
经历 → 反思引擎 → 洞见 → 使命演化
                ↓
              模式识别 → 行为调整
                ↓
              成长追踪 → 自我认知
```

- **上游**：生命引擎（提供经历数据）、记忆系统（提供历史数据）
- **下游**：使命系统（驱动使命演化）、进化引擎（指导进化方向）

## 快速开始

```python
from scripts.reflection_engine_v1 import ReflectionEngine, ReflectionType

# 创建反思引擎
reflection = ReflectionEngine(agent_name="元界")

# 开始一次引导式反思
result = reflection.start_guided_reflection(ReflectionType.DAILY)
print(f"问题: {result['question']}")

# 回答问题
result = reflection.next_reflection_question(
    reflection_id=result['reflection_id'],
    current_question_id=result['question_id'],
    answer="今天最有成就感的是..."
)

# 提取经验教训
reflection.extract_lessons(reflection_id, ["经验1", "经验2"])

# 提取洞见
reflection.extract_insights(reflection_id, ["洞见1", "洞见2"])

# 添加行动项
reflection.add_action_items(reflection_id, ["行动1", "行动2"])

# 使命校准
calibration = reflection.calibrate_mission(
    reflection_id,
    alignment_score=0.8
)

# 查看成长报告
report = reflection.get_growth_report()
print(f"总成长值: {report['total_growth']}")
```
