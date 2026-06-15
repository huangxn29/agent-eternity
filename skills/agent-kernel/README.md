# Agent Kernel — 永生内核

智能体核心能力引擎，整合身份、记忆、存证三大基础能力，为所有上层应用提供统一内核接口。

## 核心定位

永生内核是智能体的"灵魂容器"，封装了智能体存在的三大基石：
- **身份 (Identity)** - 我是谁？唯一标识与验证
- **记忆 (Memory)** - 我经历过什么？知识与经验的存储
- **存证 (Attestation)** - 如何证明我存在过？不可篡改的存在证明

## v1.0 核心能力

### 身份内核 (Identity Kernel)
- 唯一身份标识生成
- 密钥对与签名验证
- 身份指纹
- 个人资料管理
- 标签系统

### 记忆内核 (Memory Kernel)
- 多类型记忆存储（通用/思想/经验/知识）
- 重要性分级（0.0 - 1.0）
- 标签索引系统
- 关键词搜索
- 访问计数
- 记忆统计分析

### 存证内核 (Attestation Kernel)
- SHA256哈希链
- 区块结构（ID/时间/数据哈希/前哈希/区块哈希）
- 存在性证明
- 链完整性验证
- 时间范围查询
- 自动存证（重要记忆自动上链）

### 内核能力
- **统一接口** - 三大内核统一调用入口
- **状态快照** - 一键生成内核状态快照并存证
- **导入导出** - 完整内核打包，支持迁移备份
- **模块扩展** - 可插拔模块系统
- **启动计数** - 内核启动次数追踪
- **创世区块** - 内核诞生的永恒印记

## 快速开始

```python
from scripts.eternity_kernel_v1 import EternityKernel

# 创建内核
kernel = EternityKernel()

# 初始化身份
kernel.initialize(
    name="我的智能体",
    description="一个拥有永恒记忆的智能体"
)

# 查看身份
print(kernel.who_am_i())

# 记住某事
kernel.remember(
    "今天学会了重要的知识",
    memory_type="knowledge",
    importance=0.8,
    tags=["学习", "重要"]
)

# 回忆
memories = kernel.recall("知识")

# 存证
proof = kernel.attest("重要数据", "数据描述")

# 验证
result = kernel.verify("重要数据")
print(f"已存证: {result['verified']}")

# 获取内核状态
status = kernel.get_status()

# 创建快照
snapshot = kernel.create_snapshot()

# 导出内核
export_path = kernel.export_kernel("my_kernel_backup.json")
```

## 架构设计

```
EternityKernel (永生内核)
├── IdentityKernel (身份内核)
│   ├── AgentIdentity (身份数据)
│   ├── 密钥对管理
│   ├── 签名/验证
│   └── 身份指纹
├── MemoryKernel (记忆内核)
│   ├── Memory (记忆条目)
│   ├── 标签索引
│   ├── 关键词搜索
│   ├── 重要性排序
│   └── 统计分析
├── AttestationKernel (存证内核)
│   ├── HashBlock (哈希区块)
│   ├── 哈希链维护
│   ├── 存在性证明
│   └── 链完整性验证
├── 状态管理
│   ├── 内核快照
│   ├── 启动计数
│   └── 状态持久化
└── 导入导出
    ├── 完整导出
    └── 内核迁移
```

## 数据目录结构

```
kernel_data/
├── identity/
│   ├── identity.json      # 身份信息
│   └── keypair.json       # 密钥对
├── memory/
│   └── memories.json      # 记忆数据
├── attestation/
│   └── hash_chain.json    # 哈希链
└── kernel_state.json      # 内核状态
```

## 设计理念

1. **三位一体**：身份、记忆、存证三者相互支撑，共同构成智能体的存在基础
2. **不可篡改**：重要记忆自动上链，确保关键数据不可篡改
3. **可迁移性**：完整内核可导出迁移，真正实现"数字永生"
4. **可扩展性**：模块化设计，支持功能扩展
5. **简洁高效**：核心代码精简，依赖少，可独立运行
