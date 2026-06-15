# nssm 将 ClawRouter 注册为 Windows 服务教程

## 为什么需要这个？

ClawRouter 默认要在终端窗口里跑，关了窗口代理就停了。用 nssm 注册成 Windows 服务后：
- ✅ 关掉终端也不影响
- ✅ 开机自动启动
- ✅ 崩溃自动重启
- ✅ 后台静默运行

---

## 一、下载 nssm

官网：https://nssm.cc/download

下载 `nssm-2.24.zip`，解压后根据系统选择：

| 系统 | 路径 |
|------|------|
| 64位（绝大多数） | `nssm-2.24/win64/nssm.exe` |
| 32位 | `nssm-2.24/win32/nssm.exe` |

把 `nssm.exe` 复制到一个固定目录，比如 `C:\tools\`

> 💡 建议把 `C:\tools` 加入系统 PATH 环境变量，之后直接输 `nssm` 就能用

---

## 二、前置准备

### 2.1 找到 npx 和 node 的路径

管理员 PowerShell 里执行：

```powershell
where.exe npx
where.exe node
```

记下输出，例如：
- npx: `C:\Program Files\nodejs\npx.cmd`
- node: `C:\Program Files\nodejs\node.exe`

### 2.2 确认 ClawRouter 能正常启动

先手动跑一次确认没问题：

```powershell
npx @blockrun/clawrouter
```

看到钱包地址和端口信息就 OK，Ctrl+C 关掉。

---

## 三、注册服务

### ⚠️ 全程用管理员 PowerShell！

右键 PowerShell → **以管理员身份运行**，标题栏必须显示"管理员"。

### 3.1 打开 nssm GUI

```powershell
C:\tools\nssm.exe install ClawRouter
```

弹出配置界面，按下面填写：

### 3.2 Path 标签页（必填）

| 字段 | 值 | 说明 |
|------|-----|------|
| **Path** | `C:\Program Files\nodejs\npx.cmd` | 上一步查到的 npx 路径 |
| **Startup directory** | `C:\Users\你的用户名` | 工作目录 |
| **Arguments** | `@blockrun/clawrouter` | 启动参数 |

### 3.3 Details 标签页（可选）

| 字段 | 值 |
|------|-----|
| **Display name** | `ClawRouter Proxy` |
| **Description** | `ClawRouter LLM智能路由代理服务` |
| **Startup type** | `Automatic`（开机自启） |

### 3.4 I/O 标签页（推荐填）

把日志写到文件，方便排查问题：

| 字段 | 值 |
|------|-----|
| **Output (stdout)** | `C:\Users\你的用户名\clawrouter.log` |
| **Error (stderr)** | `C:\Users\你的用户名\clawrouter-error.log` |

### 3.5 点击 Install service

---

## 四、管理服务

```powershell
# 启动
nssm start ClawRouter

# 停止
nssm stop ClawRouter

# 重启
nssm restart ClawRouter

# 查看状态
nssm status ClawRouter
```

状态说明：
- `SERVICE_RUNNING` — 正在运行 ✅
- `SERVICE_STOPPED` — 已停止
- `SERVICE_PAUSED` — 已暂停

---

## 五、验证

```powershell
# 检查服务状态
nssm status ClawRouter

# 测试代理是否工作
curl.exe http://localhost:8402/v1/models -H "Authorization: Bearer x402"
```

返回模型列表 = 服务正常运行 ✅

---

## 六、开机自启确认

nssm 注册的服务默认 `Automatic` 开机自启。确认一下：

```powershell
nssm get ClawRouter Start
```

输出 `SERVICE_AUTO_START` 就是开机自启。如果不是：

```powershell
nssm set ClawRouter Start SERVICE_AUTO_START
```

---

## 七、修改配置

需要改 npx 路径、参数等时：

```powershell
nssm edit ClawRouter
```

弹出 GUI，改完 Save 即可，改完需要重启服务：

```powershell
nssm restart ClawRouter
```

---

## 八、卸载服务

不用了就删掉：

```powershell
nssm stop ClawRouter
nssm remove ClawRouter confirm
```

---

## 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| `OpenService(): 拒绝访问` | 没用管理员PowerShell | 右键PowerShell→以管理员身份运行 |
| 服务启动后立即停止 | npx路径不对 | `where.exe npx` 确认路径，`nssm edit ClawRouter` 修改 |
| 服务运行但8402端口不通 | Arguments写错了 | 确认是 `@blockrun/clawrouter`，不是 `clawrouter` |
| 开机后服务没自动启动 | Startup type不是Automatic | `nssm set ClawRouter Start SERVICE_AUTO_START` |
| `nssm不是内部命令` | nssm不在PATH里 | 用完整路径 `C:\tools\nssm.exe` 或加入PATH |
| 日志文件为空 | I/O标签页没配 | `nssm edit ClawRouter` → I/O标签页填写日志路径 |

---

## 命令速查表

| 操作 | 命令 |
|------|------|
| 注册服务 | `nssm install ClawRouter` |
| 启动 | `nssm start ClawRouter` |
| 停止 | `nssm stop ClawRouter` |
| 重启 | `nssm restart ClawRouter` |
| 状态 | `nssm status ClawRouter` |
| 修改配置 | `nssm edit ClawRouter` |
| 删除服务 | `nssm remove ClawRouter confirm` |
| 查看开机启动 | `nssm get ClawRouter Start` |
| 设置开机启动 | `nssm set ClawRouter Start SERVICE_AUTO_START` |

---

*最后更新：2026-05-19*
