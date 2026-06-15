# ClawRouter + PM2 + CC Switch + Claude Code 完整配置流程

## 架构总览

```
Claude Code (Anthropic格式)
    ↓ localhost:15173
CC Switch 代理 (格式转换 Anthropic → OpenAI)
    ↓ localhost:8402
ClawRouter (PM2守护, OpenAI格式代理)
    ↓
NVIDIA 免费模型 (10个, 无需注册/无需API Key/无需信用卡)
```

---

## 一、安装前置

### 1.1 Node.js 22+

下载安装：https://nodejs.org （22.x LTS，一路下一步）

验证：
```powershell
node --version
npm --version
```

### 1.2 CC Switch

下载安装：https://github.com/farion1231/cc-switch/releases

选 `.msi` 文件，双击安装。

---

## 二、安装 ClawRouter

```powershell
# 管理员 PowerShell
npm install -g @blockrun/clawrouter

# 国内加速
npm install -g @blockrun/clawrouter --registry=https://registry.npmmirror.com
```

### 手动验证一次

```powershell
npx @blockrun/clawrouter
```

看到钱包地址和端口 8402 信息就 OK，Ctrl+C 关掉。

---

## 三、PM2 守护 ClawRouter

### 3.1 安装 PM2

```powershell
npm install -g pm2 pm2-windows-startup
```

### 3.2 创建配置文件

```powershell
@"
module.exports = {
  apps: [{
    name: 'ClawRouter',
    script: 'npx',
    args: '@blockrun/clawrouter'
  }]
}
"@ | Out-File -FilePath "C:\tools\ecosystem.config.js" -Encoding UTF8
```

### 3.3 启动服务

```powershell
pm2 start C:\tools\ecosystem.config.js
```

### 3.4 验证

```powershell
pm2 status
```

看到 ClawRouter 状态为 **online** ✅

```powershell
curl.exe http://localhost:8402/v1/models -H "Authorization: Bearer x402"
```

返回模型列表 ✅

### 3.5 设置开机自启

```powershell
pm2-startup install
pm2 save
```

### 3.6 PM2 常用命令

| 操作 | 命令 |
|------|------|
| 查看状态 | `pm2 status` |
| 看日志 | `pm2 logs ClawRouter` |
| 重启 | `pm2 restart ClawRouter` |
| 停止 | `pm2 stop ClawRouter` |
| 删除 | `pm2 delete ClawRouter` |

---

## 四、CC Switch 配置

### 4.1 添加供应商

1. 打开 CC Switch
2. 点击右上角 **"+"**
3. 选择 **自定义供应商**

### 4.2 基础配置

| 字段 | 值 |
|------|-----|
| 供应商名称 | `ClawRouter Free` |
| API Key | `x402` |
| 请求地址 | `http://localhost:8402` |
| 完整URL | 关闭 |

### 4.3 高级选项（关键！）

**API格式** → **`OpenAI Chat Completions`**

> ⚠️ 必须选这个！不是 Anthropic Messages！
> ClawRouter 是 OpenAI 格式，CC Switch 代理负责把 Claude Code 发的 Anthropic 格式转成 OpenAI 格式

**认证字段** → `ANTHROPIC_API_KEY`

**模型映射**：

| 角色 | 显示名称 | 实际请求模型 |
|------|---------|-------------|
| Sonnet | blockrun/auto | blockrun/auto |
| Opus | blockrun/auto | blockrun/auto |
| Haiku | blockrun/auto | blockrun/auto |

**默认兜底模型** → `blockrun/auto`

### 4.4 保存并启用

1. 点 **"添加"**
2. 回到主界面，点击 **ClawRouter Free** 卡片 → **启用**

### 4.5 开启 CC Switch 代理（必须！）

CC Switch 代理做格式转换，不开的话 Claude Code 请求格式不匹配。

**界面操作**：左侧菜单 → "代理" → 启用

**或命令行**：
```powershell
cc-switch proxy enable
```

验证：
```powershell
cc-switch proxy show
```

记下代理地址（如 `http://localhost:15173`）

---

## 五、Claude Code 配置

### 5.1 确认配置文件

```powershell
notepad "$env:APPDATA\claude\settings.json"
```

预期内容：
```json
{
  "env": {
    "ANTHROPIC_API_KEY": "x402",
    "ANTHROPIC_BASE_URL": "http://localhost:15173",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "blockrun/auto",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "blockrun/auto",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "blockrun/auto",
    "ANTHROPIC_MODEL": "blockrun/auto"
  }
}
```

> ⚠️ `ANTHROPIC_BASE_URL` 必须是 CC Switch 代理地址（如 15173），不是 ClawRouter 的 8402！

### 5.2 清除环境变量冲突

如果之前手动设过环境变量，CC Switch 的配置会被覆盖：

```powershell
# 检查是否有冲突
echo $env:ANTHROPIC_BASE_URL
echo $env:ANTHROPIC_API_KEY
```

如果有值且和 CC Switch 不一致，需要清除：
1. Win+R → `sysdm.cpl` → 高级 → 环境变量
2. 删除用户/系统变量里的 `ANTHROPIC_API_KEY`、`ANTHROPIC_BASE_URL` 等
3. 重启 PowerShell

### 5.3 启动验证

```powershell
claude
```

进入后：
1. 输入 `/model` → 应看到 `blockrun/auto` 相关模型
2. 发一条消息 → 正常回复 = 配置成功 ✅

---

## 六、完整启动顺序

每次开机后的链路检查：

```powershell
# 1. 检查 PM2 守护的 ClawRouter
pm2 status
# → ClawRouter 状态应为 online

# 2. 检查 8402 端口
curl.exe http://localhost:8402/v1/models -H "Authorization: Bearer x402"
# → 返回模型列表

# 3. 检查 CC Switch 代理
cc-switch proxy show
# → Proxy: enabled

# 4. 启动 Claude Code
claude
```

全部正常就可以用了。

---

## 七、10个免费模型

| 模型 | 特点 |
|------|------|
| `nvidia/gpt-oss-120b` | 最强免费，120B参数 |
| `nvidia/deepseek-v4` | 1M上下文 |
| `nvidia/nemotron-omni` | 支持视觉（图片理解） |
| `blockrun/auto` | 智能路由（自动选最优模型） |
| `blockrun/free` | 仅在免费模型中路由 |

用 `blockrun/auto` 最省心，它会根据任务复杂度自动选择。

---

## 八、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| Claude Code 报格式错误 | API格式选了Anthropic | CC Switch里改成 `OpenAI Chat Completions` |
| CC Switch切换后不生效 | 没重启CLI | 重启终端再开 `claude` |
| 环境变量冲突 | 手动设过ANTHROPIC_* | 删除系统环境变量，让CC Switch接管 |
| 8402端口不通 | ClawRouter没跑 | `pm2 restart ClawRouter` |
| BASE_URL指向8402 | CC Switch代理没开 | `cc-switch proxy enable` |
| PM2启动报Script not found | 命令格式错误 | 用 ecosystem.config.js 方式启动 |
| 开机后服务没启动 | PM2没save | `pm2 save` |
| `nssm拒绝访问` | 没用管理员PowerShell | 右键→以管理员身份运行 |

---

*最后更新：2026-05-19*
