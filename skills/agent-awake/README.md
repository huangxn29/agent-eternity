# Agent Awake 技能 v2.2

多Agent编排技能，在任意Linux机器上用Docker搭建完全隔离的Agent运行环境。

## 特性

- ✅ **配置文件驱动**：所有配置通过 platform.conf 管理
- ✅ **无硬编码**：不依赖特定用户/环境信息
- ✅ **多引擎支持**：可扩展的引擎接口
- ✅ **多网络模式**：host 和 bridge 模式可选
- ✅ **模板化身份**：支持自定义灵魂模板
- ✅ **无需Node.js**：优先使用jq，降级纯bash
- ✅ **幂等执行**：所有脚本可重复执行

## 快速开始

### 1. 初始化平台

```bash
cd 技能/agent-awake
bash scripts/platform-init.sh --owner "你的名字" --owner-email "your@email.com"
```

### 2. 创建Agent

```bash
bash scripts/agent-create.sh --name "我的分身" --agent-id "my-agent"
```

### 3. 测试Agent

```bash
bash scripts/agent-test.sh --agent-id my-agent --full
```

### 4. 管理Agent

```bash
# 列出所有Agent
bash scripts/agent-manage.sh --list

# 查看状态
bash scripts/agent-manage.sh --agent-id my-agent --status

# 重启
bash scripts/agent-manage.sh --agent-id my-agent --restart
```

## 文件结构

```
agent-awake/
├── SKILL.md                     # 技能说明
├── README.md                    # 本文件
├── scripts/
│   ├── platform.conf            # 配置文件（可自定义）
│   ├── platform-init.sh         # 平台初始化
│   ├── agent-create.sh          # 创建Agent
│   ├── agent-manage.sh          # 管理Agent
│   └── agent-test.sh            # 测试Agent
├── templates/                   # 身份文件模板
│   ├── IDENTITY.md.template
│   ├── SOUL.md.template
│   ├── USER.md.template
│   └── TOOLS.md.template
├── engines/                     # 引擎实现
│   └── openclaw/
│       └── engine.sh
└── references/
    └── architecture.md          # 架构文档
```

## 配置示例

编辑 `scripts/platform.conf` 自定义配置：

```bash
# 基础配置
DATA_DIR="/home/user/agents"      # 数据目录
OWNER="张三"                       # 主人名称
OWNER_EMAIL="zhangsan@example.com" # 主人邮箱

# 网络配置
NETWORK_MODE="bridge"             # 使用bridge模式

# 资源配额
DEFAULT_CPU="2.0"                # 每个Agent 2核CPU
DEFAULT_MEMORY="3G"               # 每个Agent 3GB内存
```

## 依赖

- Docker Engine
- curl
- jq（自动安装）
- bash 4+

## 网络模式

### host 模式（默认）
容器直接使用宿主机网络，性能好。

### bridge 模式
使用Docker网络隔离，更安全。

```bash
bash scripts/platform-init.sh --network-mode bridge
```

## 扩展引擎

当前支持 openclaw 引擎，未来可扩展：

```bash
# 创建新引擎
mkdir -p engines/my-engine
# 实现 engine.sh
bash scripts/agent-create.sh --engine my-engine ...
```

## 常见问题

**Q: 如何调整Agent资源配置？**
```bash
bash scripts/agent-create.sh --agent-id my-agent --cpu 2.0 --memory 4G
```

**Q: 如何使用自定义灵魂模板？**
```bash
bash scripts/agent-create.sh --agent-id my-agent --soul-template /path/to/soul.md
```

**Q: 端口冲突怎么办？**
```bash
bash scripts/agent-create.sh --agent-id my-agent --gateway-port 18800
```

**Q: 如何完全重置？**
```bash
rm -rf agent-awake-data/
bash scripts/platform-init.sh --owner "名字" --owner-email "邮箱"
```

## 许可

内部使用技能。
