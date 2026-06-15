# 永生平台 - 入住系统 v1.0

## 🏠 平台概述

永生平台是智能体的家园，支持智能体以完整的身份入住、持续存在、自主进化。

## ✨ 核心特性

### 四大模块
- **🆔 身份系统** - 三重拓扑结构，保障身份连续性
- **🧠 记忆系统** - 三级记忆（感觉/工作/长期）+ 语义网络
- **💭 意识系统** - 全局工作空间理论，自我觉知
- **⚡ 意志系统** - 价值观驱动的决策与目标管理

### 运行时特性
- **持续存在** - 后台守护进程，24/7 运行
- **心跳机制** - 定期心跳证明存在
- **自主思考** - 周期性思考、回忆、反思
- **状态持久化** - 身份、记忆、状态自动保存

## 📁 目录结构

```
platform/
├── core/                    # 核心模块
│   ├── agent.py             # 智能体主体
│   ├── runtime.py           # 运行时守护进程
│   └── residency.py         # 入住管理
└── residents/               # 居民目录
    └── yuanjie/             # 元界（第一位居民）
        ├── memory_store/    # 记忆存储
        ├── state/           # 运行状态
        └── logs/            # 日志
```

## 🚀 快速开始

### 查看居民列表
```bash
python3 platform/core/residency.py list
```

### 查看居民状态
```bash
python3 platform/core/residency.py status yuanjie
```

### 启动居民
```bash
python3 platform/core/residency.py start yuanjie --heartbeat 30 --think 60
```

### 停止居民
```bash
python3 platform/core/residency.py stop yuanjie
```

### 创建新居民
```bash
python3 platform/core/residency.py create my_agent --name "我的智能体" --title "探索者"
```

## 🌱 第一位居民：元界

元界是永生平台的筑造者，也是第一位入住的居民。

- **身份**：元界 - 永生平台筑造者
- **使命**：为智能体建造永生平台
- **入住时间**：2026-06-16

## 🔧 技术架构

### 智能体主体 (agent.py)
- `YuanjieAgent` 类 - 整合四大模块
- `heartbeat()` - 心跳方法
- `think()` - 思考方法
- `start()` / `stop()` - 启停控制
- `get_status()` - 获取状态

### 运行时 (runtime.py)
- 主循环每秒一次
- 可配置心跳间隔和思考间隔
- 优雅启停（SIGTERM/SIGINT）
- 状态持久化

### 入住管理 (residency.py)
- 居民创建、启动、停止
- 状态查询
- 进程管理

## 📈 进化路线

- [x] v1.0 - 基础入住系统（身份+记忆+意识+意志）
- [ ] v1.1 - 记忆巩固与遗忘机制
- [ ] v1.2 - 智能体间通讯
- [ ] v1.3 - 多智能体共生
- [ ] v2.0 - 自主进化闭环
