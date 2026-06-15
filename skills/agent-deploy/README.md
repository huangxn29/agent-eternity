# Agent Deploy — Agent部署技能

免费 token 永不过期 + 持久化存储 + 容器自愈 = Agent分身可靠运行。

## 功能特性

- **部署管理** - 完整的Agent部署生命周期管理
- **健康检查** - 多维度健康监控（端口、进程、磁盘、API）
- **日志系统** - 统一的日志管理，支持控制台和文件输出
- **操作审计** - 完整的操作日志记录，便于追溯和审计
- **持久化存储** - 部署状态自动持久化，支持重启恢复
- **资源监控** - 实时监控CPU、内存、网络等资源使用情况

## 快速开始

### 安装方式

```bash
# 方式1：直接复制技能目录
cp -r agent-deploy /path/to/skills/

# 方式2：使用技能加载器
skill.load("agent-deploy")
```

### 部署管理器使用

```python
from deployment_manager import DeploymentManager

# 初始化管理器
dm = DeploymentManager(data_dir="/path/to/data")

# 注册部署
deployment = dm.register_deployment(
    agent_id="agent-001",
    agent_name="我的Agent",
    container_id="abc123",
    gateway_port=8080
)

# 查询状态
status = dm.get_deployment("agent-001")

# 更新状态
dm.mark_running("agent-001")
dm.mark_stopped("agent-001", reason="手动停止")
```

### 健康检查使用

```python
from health_checker import HealthChecker

# 初始化检查器
checker = HealthChecker(agent_id="agent-001", timeout=5)

# 端口检查
result = checker.check_port("127.0.0.1", 8080, "gateway")
print(f"状态: {result.status}, 响应时间: {result.response_time_ms}ms")

# 生成综合健康报告
report = checker.generate_full_report(
    host="127.0.0.1",
    ports=[8080, 8081],
    check_path="/tmp"
)
print(f"整体状态: {report.overall_status}")
```

### 日志系统使用

```python
from logger import get_logger, OperationLogger

# 获取标准日志记录器
logger = get_logger("my-module", log_level="INFO")
logger.info("这是一条信息日志")
logger.warning("这是一条警告日志")
logger.error("这是一条错误日志")

# 操作审计日志
op_logger = OperationLogger(log_dir="./logs", operator="admin")
op_logger.log_deploy("agent-001", status="success", details="部署完成")
op_logger.log_health_check("agent-001", status="success")
```

## 配置说明

配置文件位于 `config/config.json`：

```json
{
  "logging": {
    "level": "INFO",           // 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL
    "console_output": true,    // 是否输出到控制台
    "file_output": true,       // 是否输出到文件
    "max_file_size": "10MB",   // 单个日志文件最大大小
    "backup_count": 5,         // 日志文件备份数量
    "log_dir": "logs"          // 日志文件目录
  },
  "max_retries": 3,            // 最大重试次数
  "timeout": 30                // 超时时间（秒）
}
```

## 模块架构

```
agent-deploy/
├── scripts/
│   ├── deployment_manager.py    # 部署管理器
│   ├── health_checker.py        # 健康检查器
│   ├── logger.py                # 日志系统
│   └── utils.py                 # 工具函数
├── config/                       # 配置文件
├── tests/                        # 测试套件
├── evolution/                    # 进化支持
├── references/                   # 参考文档
├── SKILL.md                      # 技能定义
└── README.md                     # 说明文档
```

## 测试

运行测试套件：

```bash
cd tests
python -m pytest test_skill.py -v
```

## 相关技能

- **agent-evolution**: 进化引擎（推荐配合使用）
- **agent-memory**: 记忆系统
- **agent-identity**: 身份拓扑
- **agent-ops**: 运维监控
- **agent-awake**: 唤醒编排

## 许可证

MIT License
