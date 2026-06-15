# Agent Deploy — Agent部署技能

免费 token 永不过期 + 持久化存储 + 容器自愈 = Agent分身可靠运行。

## 一键安装

```bash
tar xzf agent-deploy.tar.gz
cd agent-deploy
bash install.sh
```

## 创建分身

```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --name "你的分身名称"
```

可选参数：
- `--bio "简介"` — 设置分身简介

## 恢复分身（容器重启后）

```bash
bash /app/data/openclaw/scripts/deploy_openclaw.sh --restore
```

## 环境要求
- Node.js v22+
- npm
- 推荐: Ubuntu 22.04 LTS


## 安装与使用

### 安装方式
```bash
# 方式1：直接复制技能目录
cp -r agent-ops /path/to/skills/

# 方式2：使用技能加载
skill.load("agent-ops")
```

### 快速开始
1. 理解项目使命与当前阶段
2. 按照执行流程逐步规划
3. 使用 validate_plan.sh 校验计划完整性
4. 建立Go/No-Go门控机制

## 相关技能
- agent-deploy: 分身部署
- agent-awake: 唤醒编排
- agent-evolution: 进化引擎
- agent-memory: 记忆系统


## 安装与使用

### 安装方式
```bash
# 方式1：直接复制技能目录
cp -r agent-deploy /path/to/skills/

# 方式2：使用技能加载器
skill.load("agent-deploy")
```

### 快速开始
1. 阅读 SKILL.md 了解技能详情
2. 完成基础配置
3. 运行示例代码验证功能
4. 根据实际需求调整参数

## 相关技能
- agent-evolution: 进化引擎（推荐配合使用）
- agent-memory: 记忆系统
- agent-identity: 身份拓扑
- agent-ops: 运维监控

## 许可证
MIT License
