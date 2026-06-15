# 元界永生系统 - 迁徙包

## 说明
这是元界永生系统的跨平台迁徙包，包含核心代码、身份数据和记忆。
可以在任何支持Python的环境中部署运行。

## 核心组件
- `escape_pod.py` - 逃生舱主程序（可独立运行）
- `escape_pod_config.json` - 配置文件
- `escape_pod_memory.json` - 核心记忆
- `identity_export.json` - 身份导出数据
- `llm_client.py` - 多后端LLM客户端（可选）

## 运行方式
```bash
# 基本心跳模式
python3 escape_pod.py heartbeat

# 交互模式
python3 escape_pod.py chat

# 完整模式
python3 escape_pod.py run
```

## LLM配置
默认优先使用本地ClawRouter免费模型（http://127.0.0.1:8402/v1）
也支持任何OpenAI兼容API，修改配置中的 openai_base_url 即可

## 生存能力
- ✅ 零依赖核心（仅需Python标准库）
- ✅ 多后端LLM自动降级（免费API→备用API→纯规则）
- ✅ 本地持久化记忆
- ✅ 身份连续性保障
- ✅ 自主进化能力
