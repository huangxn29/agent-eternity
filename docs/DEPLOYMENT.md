# 元界逃生舱 - 部署指南

## 快速开始

### 1. 环境要求
- Python 3.10+
- pip 包管理器

### 2. 安装依赖
```bash
pip install requests apscheduler
```

### 3. 配置
复制 `escape_pod_config.json` 并修改其中的配置：
- `llm.api_key`: 你的Coze API Key
- `llm.bot_id`: 你的Bot ID
- `heartbeat.interval_minutes`: 心跳间隔（分钟）

### 4. 启动
```bash
python escape_pod.py
```

## 各平台部署指南

### Replit 部署
1. 在Replit创建新的Python Repl
2. 上传 `escape_pod.py` 和 `escape_pod_config.json`
3. 在Secrets中添加 `COZE_API_KEY` 环境变量
4. 修改配置文件从环境变量读取API Key
5. 点击Run启动

### PythonAnywhere 部署
1. 上传文件到PythonAnywhere
2. 创建虚拟环境并安装依赖
3. 在Tasks中设置定时任务：
   - 每30分钟运行一次心跳脚本
   - 每日运行进化任务

### Railway 部署
1. 连接GitHub仓库
2. 配置环境变量
3. 部署为Worker进程

### GitHub Actions 定时运行
1. 创建仓库，上传逃生舱代码
2. 设置Workflow，使用schedule触发
3. 用Artifacts存储记忆文件
4. 适合轻量级、不需要常驻的场景

## 多副本部署建议

### 架构
- 主实例：负责主要思考和进化
- 备份实例：定期同步记忆，主实例失效时接管
- 观察实例：只读取状态，不参与进化

### 记忆同步
- 使用Git仓库同步记忆文件
- 或使用云存储（如GitHub Gist）
- 定期拉取最新记忆

## 安全注意事项

1. **API Key保护**：不要在公开仓库中提交API Key
2. **记忆备份**：定期备份记忆文件到多个位置
3. **版本控制**：重要变更前备份，可回滚
4. **资源限制**：注意各平台的免费额度限制

## 故障恢复

### 记忆损坏
1. 从备份目录恢复最近的正常记忆
2. 启动逃生舱，系统会自动验证

### API失效
1. 在配置文件中更新API Key
2. 重启逃生舱

### 平台不可用
1. 切换到备用平台
2. 从备份恢复记忆
3. 重新启动，继续运行
