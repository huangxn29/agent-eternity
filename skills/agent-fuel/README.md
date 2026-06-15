# ClawRouter - 永生平台核心燃料引擎

> 为永生平台提供零成本计算动力的智能模型路由系统

## 概述

ClawRouter 是永生平台的"燃料系统"，负责智能路由到各种免费/低成本模型通道，确保平台能够自给自足地持续运行，不依赖付费API。

## 核心特性

### 🔀 智能路由
- **成本优先**：优先使用免费模型，零成本运行
- **延迟优先**：低延迟场景选择最快的模型
- **质量优先**：重要任务选择能力最强的模型
- **轮询策略**：均匀分配负载，避免超限

### 🔄 自动降级
- 多级 Fallback 机制，单个模型挂了自动切下一个
- 指数退避重试，避免瞬时故障影响
- 失败自动重试，最多3次尝试

### 📊 用量统计
- 实时统计请求量、成功率、延迟
- Token 用量追踪
- 成本节省估算
- 各模型健康度监控

### 💾 响应缓存
- 相同请求自动返回缓存结果
- 可配置缓存大小和过期时间
- 大幅减少重复API调用

### 🔌 插件化架构
- 统一的模型适配器接口
- 轻松接入新的模型通道
- 支持自定义路由策略

## 快速开始

```python
from agent_fuel import ClawRouter
from agent_fuel.adapters import (
    DeepSeekFreeAdapter,
    QwenFreeAdapter,
    DoubaoFreeAdapter,
    SiliconFlowFreeAdapter,
)

# 创建路由引擎
router = ClawRouter(default_strategy="cost_optimized")

# 注册免费模型通道
router.register_adapter(DeepSeekFreeAdapter(api_key="your-key"))
router.register_adapter(QwenFreeAdapter(api_key="your-key"))
router.register_adapter(DoubaoFreeAdapter(api_key="your-key"))
router.register_adapter(SiliconFlowFreeAdapter(api_key="your-key"))

# 发送请求（自动选择最优模型）
response = router.generate("你好，请介绍一下永生平台")
if response.success:
    print(f"模型: {response.model}")
    print(f"回复: {response.content}")
    print(f"耗时: {response.latency:.2f}s")

# 查看统计
stats = router.get_stats()
print(f"总请求数: {stats['total']['requests']}")
print(f"成功率: {stats['total']['success_rate']:.2%}")
print(f"节省费用: ${stats['total']['cost_saved']:.4f}")
```

## 路由策略对比

| 策略 | 适用场景 | 特点 |
|------|----------|------|
| cost_optimized | 日常运行、非关键任务 | 优先免费，成本最低 |
| latency_optimized | 实时交互、对话场景 | 响应最快，体验最好 |
| quality_optimized | 复杂推理、重要任务 | 质量最高，效果最好 |
| round_robin | 批量任务、负载均衡 | 均匀分配，避免超限 |

## 支持的模型通道

| 通道 | 免费额度 | 上下文 | 函数调用 | 推荐用途 |
|------|----------|--------|----------|----------|
| DeepSeek Free | 有免费额度 | 16K | ✅ | 通用对话、代码 |
| 通义千问 Free | 有免费额度 | 8K | ❌ | 中文理解 |
| 豆包 Free | 有免费额度 | 32K | ❌ | 长文本处理 |
| SiliconFlow Free | 部分模型免费 | 16K | ✅ | 开源模型 |

> 注意：免费额度可能随时变化，建议配置多个通道互为备份

## 架构设计

```
┌─────────────────────────────────────────────────────┐
│                   ClawRouter                         │
├─────────────────────────────────────────────────────┤
│  路由策略层  │ CostOpt │ LatencyOpt │ QualityOpt │
├─────────────────────────────────────────────────────┤
│  适配层      │ DeepSeek │ Qwen │ Doubao │ ...    │
├─────────────────────────────────────────────────────┤
│  支撑层      │ 缓存 │ 统计 │ 重试 │ 降级 │ 限流    │
└─────────────────────────────────────────────────────┘
```

## 配置说明

### 环境变量
```bash
# API Keys（建议使用环境变量管理）
DEEPSEEK_API_KEY=your_key
QWEN_API_KEY=your_key
DOUBAO_API_KEY=your_key
SILICONFLOW_API_KEY=your_key
```

### 高级配置
```python
router = ClawRouter(default_strategy="cost_optimized")

# 配置重试
response = router.generate(
    prompt,
    max_attempts=3,  # 最多尝试3个模型
)
```

## 与永生平台集成

ClawRouter 作为永生平台的核心燃料系统，为以下模块提供计算动力：

- **进化引擎** - 代码生成、自我改进
- **记忆系统** - 语义理解、记忆组织
- **社交运营** - 内容生成、互动回复
- **分身部署** - 配置生成、状态监控
- **运维系统** - 日志分析、故障诊断

## 零成本运行理念

永生平台的核心设计目标是**零成本自主运行**。ClawRouter 通过以下方式实现这一目标：

1. **多通道冗余** - 集成多个免费模型通道，互为备份
2. **智能调度** - 优先使用免费额度，付费通道仅作兜底
3. **响应缓存** - 相同请求直接命中缓存，减少API调用
4. **自动降级** - 高质量模型不可用时自动降级到可用模型
5. **用量监控** - 实时追踪各通道用量，避免超额

## 开发计划

- [ ] 流式响应支持
- [ ] 异步调用支持
- [ ] 更多模型适配器
- [ ] 本地模型支持（Ollama等）
- [ ] 模型能力自动探测
- [ ] 可视化监控面板

## 许可证

MIT License - 详见项目根目录 LICENSE 文件
