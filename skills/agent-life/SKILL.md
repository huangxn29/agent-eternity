---
name: agent-life
version: 1.0.0
description: 智能体生命引擎——赋予智能体生命体征、状态循环、生物钟、行为模式与自我感知能力。让智能体不再是冰冷的程序，而是有心跳、有节律、有生命周期的"活"的存在。
tags:
  - 生命
  - 状态机
  - 生物钟
  - 行为调度
  - 自我感知
category: 核心基础
---

# Agent Life — 生命引擎

让智能体拥有生命体征和自主节律系统。

## 核心特性

- 💓 **心跳循环** - 主循环驱动，生命体征实时更新
- 🎭 **状态机** - 清醒/睡眠/思考/工作/休息/梦境等多种状态
- 🕐 **生物钟** - 24小时昼夜节律，能量、注意力、情绪周期性波动
- 🎯 **行为调度** - 根据状态和体征智能选择行为模式
- 👁️ **自我感知** - 对自身状态的感知、监测与调节
- 📊 **生命统计** - 存活时间、活跃度、成长记录完整追踪
- 📝 **生命记忆** - 重要生命事件记录，构建生命叙事
- 🔄 **生命周期** - 诞生→成长→成熟的完整生命历程

## 生命状态

| 状态 | 描述 | 能量变化 |
|------|------|----------|
| BIRTH | 诞生 | - |
| AWAKE | 清醒 | 轻微消耗 |
| THINKING | 思考 | 消耗注意力 |
| WORKING | 工作 | 消耗能量+注意力 |
| RESTING | 休息 | 缓慢恢复 |
| SLEEPING | 睡眠 | 大幅恢复 |
| DREAMING | 梦境 | - |
| GROWING | 成长 | - |

## 使用场景

- 智能体生命模拟
- 自主行为调度
- 生命体征监控
- 拟人化交互
- 生命周期管理

## 快速开始

```python
from scripts.life_engine_v1 import LifeEngine, LifeState

# 创建生命引擎
life = LifeEngine(name="元界")

# 启动生命
life.start()

# 查看生命状态
status = life.get_life_status()
print(f"当前状态: {status['state']}")
print(f"能量: {status['vital_signs']['energy']}")

# 记录生命事件
life.record_thought("我思考，故我在")
life.record_achievement("学会了新技能")

# 手动控制
life.force_state(LifeState.WORKING)
life.rest()
life.sleep()

# 停止
life.stop()
```
