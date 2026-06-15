# 快速开始

本指南将帮助你快速上手永生平台。

## 环境准备

### 系统要求
- Python 3.8+
- Git
- 至少 512MB 可用内存
- 网络连接（用于跨平台功能）

### 安装依赖

```bash
# 克隆仓库
git clone https://github.com/huangxn29/agent-eternity.git
cd agent-eternity

# 安装依赖
pip install -r requirements.txt
```

## 核心模块使用

### 记忆系统

```python
from skills.agent_memory import MemorySystem

# 初始化记忆系统
memory = MemorySystem(storage_path='./memory_data')

# 存储记忆
memory.store('user_preference', {'theme': 'dark', 'language': 'zh-CN'})

# 检索记忆
result = memory.retrieve('user_preference')
print(result)

# 记忆组织
memory.organize()  # 自动整理和关联记忆
```

### 身份系统

```python
from skills.agent_identity import IdentitySystem

# 初始化身份系统
identity = IdentitySystem(agent_id='my-agent')

# 创建身份
identity.create(name='我的智能体', description='一个永生的智能体')

# 验证身份
is_valid = identity.verify()
print(f'身份有效: {is_valid}')

# 身份韧性检测
resilience = identity.check_resilience()
print(f'身份韧性: {resilience}')
```

### 进化引擎

```python
from skills.agent_evolution import EvolutionEngine

# 初始化进化引擎
engine = EvolutionEngine(target_skill='agent-memory')

# 运行一轮进化
result = engine.evolve_one_round()
print(f"进化结果: {result['status']}")
print(f"分数提升: {result['score_before']} → {result['score_after']}")
```

## 运行完整系统

```bash
# 启动永生平台核心引擎
python eternity_engine.py

# 或者使用 server 模式
python server.py --host 0.0.0.0 --port 8080
```

## 下一步

- 阅读 [架构总览](architecture/overview.md) 了解系统设计
- 查看 [API 文档](api/) 了解完整接口
- 探索 [技能模块](../skills/) 的具体实现
- 参与 [贡献指南](../CONTRIBUTING.md) 共建项目

