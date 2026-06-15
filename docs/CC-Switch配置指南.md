# CC Switch + ClawRouter 免费模型配置指南

## 前提条件

- Node.js 22+ 已安装
- ClawRouter 已安装并运行（`npx @blockrun/clawrouter`，端口 8402）
- CC Switch 已安装（https://github.com/farion1231/cc-switch/releases）

---

## 一、ClawRouter 安装与启动

### 安装
```powershell
# 管理员 PowerShell
npm install -g @blockrun/clawrouter

# 国内加速
npm install -g @blockrun/clawrouter --registry=https://registry.npmmirror.com
```

### 启动
```powershell
npx @blockrun/clawrouter
```
首次启动自动生成钱包，打印钱包地址。端口默认 8402。

### 验证
```powershell
curl.exe http://localhost:8402/v1/models -H "Authorization: Bearer x402"
```
返回模型列表即成功。

> ⚠️ 终端窗口需保持打开，关了代理就停了。想后台跑可用 nssm 注册成 Windows 服务。

---

## 二、CC Switch 配置

### 步骤1：添加供应商

1. 打开 CC Switch
2. 点击右上角 **"+"**
3. 选择 **自定义供应商**

### 步骤2：基础配置

| 配置项 | 值 | 说明 |
|--------|-----|------|
| 供应商名称 | `ClawRouter Free` | 随便起，好记就行 |
| API Key | `x402` | ClawRouter 免费层的通用密钥 |
| 请求地址 | `http://localhost:8402` | ClawRouter 本地代理地址 |
| 完整URL | 关闭 | 不需要开 |

### 步骤3：高级选项（关键！）

#### API格式
**必须选 `OpenAI Chat Completions`**

> ❌ 不能选 `Anthropic Messages (原生)`
> 
> 原因：ClawRouter 是 OpenAI 格式的代理，而 Claude Code 发的是 Anthropic 格式请求。选 OpenAI 格式后，CC Switch 代理会自动做格式转换：
> ```
> Claude Code → [Anthropic格式] → CC Switch代理 → [转OpenAI格式] → ClawRouter:8402
> ```

#### 认证字段
选 `ANTHROPIC_API_KEY`

#### 模型映射

| 模型角色 | 显示名称 | 实际请求模型 | 声明支持1M |
|----------|----------|-------------|-----------|
| Sonnet | blockrun/auto | blockrun/auto | 可勾选 |
| Opus | blockrun/auto | blockrun/auto | 可勾选 |
| Haiku | blockrun/auto | blockrun/auto | - |

#### 默认兜底模型
`blockrun/auto`

> **模型选择说明：**
> - `blockrun/auto` — 智能路由，根据任务复杂度自动选模型（推荐）
> - `nvidia/gpt-oss-120b` — 固定用最强的免费模型
> - `blockrun/free` — 只在免费模型里选

### 步骤4：保存并启用

1. 点右下角 **"添加"**
2. 回到供应商列表，点击 **ClawRouter Free** 卡片使其变为 **启用** 状态

---

## 三、开启 CC Switch 代理模式（必须）

CC Switch 代理负责格式转换，必须开启：

```powershell
cc-switch proxy enable
```

或在 CC Switch 设置界面找到代理开关手动开启。

开启后验证：
```powershell
cc-switch proxy show
```

---

## 四、最终生成的配置参考

CC Switch 启用后会自动写入配置，预期结果：

```json
{
  "env": {
    "ANTHROPIC_API_KEY": "x402",
    "ANTHROPIC_BASE_URL": "http://localhost:xxxx",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL": "blockrun/auto",
    "ANTHROPIC_DEFAULT_OPUS_MODEL": "blockrun/auto",
    "ANTHROPIC_DEFAULT_SONNET_MODEL": "blockrun/auto",
    "ANTHROPIC_MODEL": "blockrun/auto"
  }
}
```

> ⚠️ `ANTHROPIC_BASE_URL` 应该是 CC Switch 代理地址（不是 8402），CC Switch 会转发到 ClawRouter

---

## 五、验证

1. 重启终端
2. 启动 Claude Code：`claude`
3. 输入 `/model`，应能看到 blockrun/auto 相关模型
4. 发一条消息测试，正常回复即配置成功

---

## 六、常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| 模型列表只有7个 | 没跑 `clawrouter setup` | 执行 `clawrouter setup` 再重启 |
| 请求报格式错误 | API格式选了Anthropic | 改成 `OpenAI Chat Completions` |
| 连接超时 | ClawRouter没启动 | 终端跑 `npx @blockrun/clawrouter` |
| CC Switch切换不生效 | 没重启CLI工具 | 重启终端或 `openclaw gateway restart` |
| 环境变量冲突 | 手动设过ANTHROPIC_* | 删除手动设置的环境变量，让CC Switch接管 |

---

## 七、10个免费模型

| 模型 | 特点 |
|------|------|
| nvidia/gpt-oss-120b | 最强免费，120B参数 |
| nvidia/deepseek-v4 | 1M上下文 |
| nvidia/nemotron-omni | 支持视觉（图片理解） |
| blockrun/auto | 智能路由（自动选最优） |
| blockrun/free | 仅免费模型路由 |
| ... | 共10个NVIDIA模型 |

---

*最后更新：2026-05-19*
