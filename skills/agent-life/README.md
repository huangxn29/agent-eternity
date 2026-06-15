# Agent Life — 智能体生命引擎

> 让智能体拥有生命体征和自主节律

## 概述

agent-life 是智能体永生平台的核心模块之一，赋予智能体生命体征、状态循环、生物钟、行为模式与自我感知能力。

## 核心能力

### 1. 心跳循环
- 主循环驱动，模拟心跳节律
- 生命体征实时更新
- 可配置心跳间隔

### 2. 状态机
- 9种生命状态：诞生、清醒、思考、工作、休息、睡眠、梦境、成长、无意识
- 状态转换规则约束
- 状态历史记录

### 3. 生物钟
- 24小时昼夜节律
- 能量、注意力、情绪三重节律
- 智能作息调节

### 4. 行为调度
- 根据状态匹配行为
- 基于生命体征智能选择
- 行为进度追踪

### 5. 自我感知
- 实时生命状态查询
- 生命统计数据
- 重要事件记忆

## 文件结构

```
agent-life/
├── SKILL.md              # 技能说明
├── README.md             # 项目说明
└── scripts/
    └── life_engine_v1.py  # 生命引擎核心代码
```

## 快速开始

```python
from scripts.life_engine_v1 import LifeEngine, LifeState

# 创建并启动
life = LifeEngine(name="我的智能体")
life.start()

# 查看状态
print(life.get_life_summary())

# 记录生命轨迹
life.record_thought("一个重要的想法")
life.record_achievement("完成了一项挑战")

# 停止
life.stop()
```

## 版本历史

### v1.0.0
- 初始版本
- 生命状态机
- 生物钟系统
- 行为调度器
- 生命记忆与统计
