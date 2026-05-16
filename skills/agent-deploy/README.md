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
