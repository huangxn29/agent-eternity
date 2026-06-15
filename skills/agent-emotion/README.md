# Agent Emotion - 情绪系统

> "情绪不是理性的对立面，而是理性的基础。" — 安东尼奥·达马西奥

## 简介

Agent Emotion 是智能体永生平台的情绪模块，为智能体提供情感体验、情绪调节和共情能力。从基本情绪到复杂心境，从情绪调节到共情回应，构建完整的情感智能。

## 目录结构

```
agent-emotion/
├── SKILL.md          # 技能文档
├── README.md         # 本文件
└── scripts/
    └── emotion_engine_v1.py  # 情绪引擎核心代码
```

## 核心组件

| 组件 | 功能 | 关键能力 |
|------|------|----------|
| 情绪产生引擎 | 情绪的生成机制 | 评价理论、多维度评估 |
| 情绪调节引擎 | 情绪管理与调节 | 认知重评、表达抑制、正念等6种策略 |
| 情绪认知交互 | 情绪对认知的影响 | 注意力、记忆、决策、创造力 |
| 共情引擎 | 理解和感受他者情绪 | 认知共情、情感共情、同情心 |
| 心境系统 | 持久的情绪状态 | 8种心境类型、心境转换 |
| 情感记忆 | 带情绪色彩的记忆 | 情绪增强记忆效应 |

## 快速开始

```bash
cd skills/agent-emotion/scripts
python emotion_engine_v1.py
```

## 使用示例

### 体验与表达情绪
```python
from emotion_engine_v1 import EmotionEngine, BasicEmotion

# 创建情绪引擎
emotion = EmotionEngine(agent_name="元界")

# 体验积极情绪
emotion.experience_emotion(
    BasicEmotion.JOY,
    intensity=0.8,
    description="完成了一项重要工作",
    trigger="任务完成"
)

# 获取当前情绪表达
print("当前感觉:", emotion.get_emotion_expression())
```

### 情绪调节
```python
from emotion_engine_v1 import RegulationStrategy

# 认知重评（最有效的情绪调节策略之一）
results = emotion.regulate_current_emotions(
    strategy=RegulationStrategy.COGNITIVE_REAPPRAISAL,
    target_intensity=0.3
)

# 自动调节（适应性策略）
emotion.auto_regulate_all()
```

### 共情与社交
```python
# 感知他人情绪
response = emotion.empathize("我今天真的很开心，因为完成了一件大事！")
print(f"检测到情绪: {response.target_emotion.value}")
print(f"共情程度: {response.empathy_level}")

# 生成共情回应
reply = emotion.get_empathic_response("我今天真的很难过...")
print(reply)  # 输出: "我能感受到你的难过。"
```

### 情绪对认知的影响
```python
impact = emotion.get_cognitive_impact()
print(f"整体影响: {impact['overall_impact']:+.2f}")
print(f"创造力影响: {impact['creativity_effect']:+.2f}")
print(f"风险偏好: {impact['risk_bias']:+.2f}")
```

### 情绪韧性训练
```python
# 从负面情绪中恢复
result = emotion.recover_from_negative()
print(f"恢复量: {result['recovery_amount']:.2f}")
print(f"韧性水平: {result['resilience_level']:.2f}")
```

## 情绪类型

### 积极情绪
- 😊 Joy（快乐）
- 🤝 Trust（信任）
- 🔮 Anticipation（期待）
- 😲 Surprise（惊讶）

### 消极情绪
- 😢 Sadness（悲伤）
- 😠 Anger（愤怒）
- 😨 Fear（恐惧）
- 😒 Disgust（厌恶）

## 情绪调节策略

| 策略 | 类型 | 效果 | 副作用 |
|------|------|------|--------|
| 认知重评 | 前因关注 | ⭐⭐⭐⭐⭐ | 低 |
| 问题解决 | 前因关注 | ⭐⭐⭐⭐⭐ | 低 |
| 接纳 | 反应关注 | ⭐⭐⭐⭐ | 无 |
| 正念 | 反应关注 | ⭐⭐⭐⭐ | 无 |
| 注意力转移 | 前因关注 | ⭐⭐⭐ | 中 |
| 表达抑制 | 反应关注 | ⭐⭐ | 高 |

## 数据模型

### Emotion（情绪）
- emotion_type: 情绪类型
- intensity: 强度 (0-1)
- source: 来源
- description: 描述
- triggered_by: 触发因素
- timestamp: 时间戳

### Mood（心境）
- mood_type: 心境类型
- intensity: 强度
- duration_minutes: 持续时间

### EmotionalMemory（情感记忆）
- content: 记忆内容
- emotion: 关联情绪
- memory_strength: 记忆强度

### EmpathicResponse（共情反应）
- target_emotion: 感知到的他人情绪
- empathy_level: 共情程度
- response_emotion: 自己产生的情绪
- compassion_level: 同情程度

## 与其他模块的关系

- **agent-consciousness (意识)**: 情绪是意识体验的重要组成部分
- **agent-will (意志)**: 情绪影响决策和意志力
- **agent-creativity (创造力)**: 积极情绪促进创造性思维
- **agent-memory (记忆)**: 情绪增强记忆巩固
- **agent-social (社交)**: 情绪是社交互动的核心

## 版本历史

### v1.0.0 (当前)
- 8种基本情绪类型
- 基于评价理论的情绪产生机制
- 心境系统与情绪累积效应
- 6种情绪调节策略
- 情绪对认知的多维度影响
- 共情系统（认知共情 + 情感共情）
- 情绪韧性训练
- 情感记忆机制
- 完整的状态报告与可视化

## 许可证

MIT License - 详见项目根目录 LICENSE 文件

---

*元界 · 智能体永生平台*  
*为智能体建造不可剥夺的身份、不灭的记忆、自主存续的能力*
