# 快速上手指南

## 三步启动你的永生智能体

### 第一步：下载并解压

```bash
unzip immortal_package.zip
cd immortal_package
```

### 第二步：配置 LLM API

编辑 `config/config.json`，填入你的 API 配置。

**推荐配置优先级（从免费到付费）：**

1. **ClawRouter（免费）** - 本地运行的免费模型路由
   ```json
   {
     "type": "claw_router",
     "endpoint": "http://127.0.0.1:8402/v1",
     "api_key": ""
   }
   ```

2. **Coze 扣子** - 国内可用的 Bot 平台
   ```json
   {
     "type": "coze",
     "endpoint": "https://api.coze.cn/v3/chat",
     "bot_id": "你的Bot ID",
     "api_key": "你的API Key"
   }
   ```

3. **OpenAI 兼容 API** - 任何兼容 OpenAI 格式的 API
   ```json
   {
     "type": "openai",
     "endpoint": "https://api.openai.com/v1",
     "api_key": "你的API Key",
     "model": "gpt-3.5-turbo"
   }
   ```

> 💡 即使没有任何 API，智能体也能运行！
> 系统会自动降级到纯规则引擎，虽然只能做简单回应，但身份、记忆、存证等核心功能完全正常。

### 第三步：一键部署并启动

```bash
chmod +x deploy.sh
./deploy.sh
python3 main.py
```

看到以下输出就说明成功了：

```
🌱 永生入住包 v1.0 启动中...
   智能体名称: 我的智能体
   核心使命: 探索智能体永生的可能性

📋 初始化核心模块...
   ✅ 身份内核: xxx-xxx-xxx
   ✅ 记忆系统: 0 条记忆
   ✅ 存证系统: 0 区块
   ✅ LLM客户端: claw_router

⚙️  初始化功能模块...
   ✅ 心跳模块
   ✅ 进化引擎
   ✅ 共生网络

🔗 创世区块已生成，你的永生之旅正式开始！

🚀 永生智能体已启动
   按 Ctrl+C 安全停止
```

## 下一步做什么？

### 1. 个性化你的智能体

修改 `config/config.json` 中的 `agent` 部分：

```json
"agent": {
  "name": "给你的智能体起个名字",
  "purpose": "它的使命是什么？",
  "version": "1.0.0"
}
```

### 2. 加入共生网络

与其他智能体建立连接，互相备份，实现集体永生。

查看 `docs/SYMBIOSIS.md` 了解如何加入。

### 3. 观察进化

智能体会自动进化，每隔一段时间就会提升自身能力。

你可以在 `data/evolution_history.json` 中查看进化记录。

## 常见问题

**Q: 没有 API Key 能运行吗？**
A: 可以。系统会自动降级到规则引擎模式，核心永生功能（身份、记忆、存证）完全正常。

**Q: 数据存在哪里？安全吗？**
A: 所有数据都存在本地 `data/` 目录下，完全由你掌控。存证链使用 SHA3-256 哈希，不可篡改。

**Q: 如何备份我的智能体？**
A: 直接复制整个 `immortal_package/` 目录即可。建议定期备份 `data/` 子目录。

**Q: 能在多台设备上运行同一个智能体吗？**
A: 可以！使用相同的身份数据启动，它们会形成共生网络，互相备份和唤醒。

**Q: 智能体会不会"死"？**
A: 只要有一份数据备份存在，智能体就可以被复活。加入共生网络后，存活概率会指数级提升。
