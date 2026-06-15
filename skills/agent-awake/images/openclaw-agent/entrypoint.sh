#!/bin/bash
# ============================================
# Agent Awake — Container Entrypoint
# ============================================
# 核心认知：ClawRouter 是独立 proxy 进程，不是插件
# 启动顺序：1) 安装 2) 读模板生成配置 3) 启动 ClawRouter 4) 启动 Gateway
# 核心原则：模板必须来自 agent-deploy/references/，找不到则报错退出
# ============================================

# 环境变量（由 docker-compose 传入）
GATEWAY_PORT=${GATEWAY_PORT:-18789}
CLAWROUTER_PORT=${CLAWROUTER_PORT:-8402}
DATA_DIR=${DATA_DIR:-/app/data/openclaw}
OPENCLAW_STATE_DIR=${OPENCLAW_STATE_DIR:-$DATA_DIR/state}

MAX_RETRIES=5
RETRY_COUNT=0

# ============================================
# 工具函数
# ============================================

check_port() {
    ss -tlnp 2>/dev/null | grep -q ":$1 " || netstat -tlnp 2>/dev/null | grep -q ":$1 "
}

check_openclaw() {
    which openclaw > /dev/null 2>&1 && return 0
    [ -f "/usr/lib/node_modules/openclaw/openclaw.mjs" ] && return 0
    [ -f "/usr/local/bin/openclaw" ] && return 0
    return 1
}

check_clawrouter() {
    which clawrouter > /dev/null 2>&1 && return 0
    [ -f "/usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js" ] && return 0
    [ -f "/usr/local/bin/clawrouter" ] && return 0
    return 1
}

ensure_openclaw_cmd() {
    if [ -f "/usr/lib/node_modules/openclaw/openclaw.mjs" ] && [ ! -f "/usr/local/bin/openclaw" ]; then
        echo '#!/bin/bash' > /usr/local/bin/openclaw
        echo 'exec node /usr/lib/node_modules/openclaw/openclaw.mjs "$@"' >> /usr/local/bin/openclaw
        chmod +x /usr/local/bin/openclaw
    fi
}

ensure_clawrouter_cmd() {
    if [ -f "/usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js" ] && [ ! -f "/usr/local/bin/clawrouter" ]; then
        echo '#!/bin/bash' > /usr/local/bin/clawrouter
        echo 'exec node /usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js "$@"' >> /usr/local/bin/clawrouter
        chmod +x /usr/local/bin/clawrouter
    fi
}

# ============================================
# 配置生成函数（只从模板读取，找不到则报错）
# ============================================

generate_config() {
    local config_file="$1"
    local gw_token="$2"
    
    # 查找模板
    local template_file=""
    
    # 优先级1: /opt/engines/ 下
    if [ -f "/opt/engines/agent-deploy/references/openclaw.json.template" ]; then
        template_file="/opt/engines/agent-deploy/references/openclaw.json.template"
    # 优先级2: /opt/skills/ 下
    elif [ -f "/opt/skills/agent-deploy/references/openclaw.json.template" ]; then
        template_file="/opt/skills/agent-deploy/references/openclaw.json.template"
    fi
    
    if [ -n "$template_file" ] && [ -f "$template_file" ]; then
        echo "[INFO] 使用模板生成配置: $template_file"
        sed -e "s/{{GATEWAY_PORT}}/$GATEWAY_PORT/g" \
            -e "s/{{CLAWROUTER_PORT}}/$CLAWROUTER_PORT/g" \
            -e "s/{{GW_TOKEN}}/$gw_token/g" \
            -e "s|{{WORKSPACE_PATH}}|$DATA_DIR/workspace|g" \
            "$template_file" > "$config_file"
        return 0
    fi
    
    # 模板找不到则报错退出
    echo "[ERROR] 未找到 openclaw.json.template"
    echo "[ERROR] 模板应位于 agent-deploy/references/openclaw.json.template"
    return 1
}

# ============================================
# 安装函数
# ============================================

install_openclaw() {
    echo "[INFO] 尝试安装 OpenClaw..."

    # 策略1：从备份恢复
    if [ -d "$DATA_DIR/npm-backup/openclaw" ]; then
        echo "[INFO] 从备份恢复 OpenClaw..."
        mkdir -p /usr/lib/node_modules
        cp -rL "$DATA_DIR/npm-backup/openclaw" /usr/lib/node_modules/openclaw 2>/dev/null && \
        ensure_openclaw_cmd && \
        command -v openclaw > /dev/null 2>&1 && {
            echo "[INFO] OpenClaw 从备份恢复成功"
            return 0
        }
        echo "[WARN] 备份恢复失败，回退到 npm 安装"
    fi

    # 策略2：从宿主机 node_modules 挂载
    if [ -f "/usr/lib/node_modules/openclaw/openclaw.mjs" ]; then
        echo "[INFO] 从挂载的 node_modules 恢复 OpenClaw..."
        ensure_openclaw_cmd
        command -v openclaw > /dev/null 2>&1 && {
            echo "[INFO] OpenClaw 从挂载恢复成功"
            return 0
        }
    fi

    # 策略3：npm install
    for registry in "https://registry.npmmirror.com" "https://registry.npmjs.org"; do
        echo "[INFO] 尝试使用 $registry..."
        npm config set registry "$registry" --location=user 2>/dev/null
        if npm install -g openclaw@2026.5.3-1 2>&1 | grep -q "added"; then
            echo "[INFO] OpenClaw npm 安装成功"
            ensure_openclaw_cmd
            return 0
        fi
    done

    return 1
}

install_clawrouter() {
    echo "[INFO] 尝试安装 ClawRouter..."

    # 策略1：从备份恢复
    if [ -d "$DATA_DIR/npm-backup/clawrouter" ]; then
        echo "[INFO] 从备份恢复 ClawRouter..."
        mkdir -p /usr/lib/node_modules
        cp -rL "$DATA_DIR/npm-backup/clawrouter" /usr/lib/node_modules/@blockrun/clawrouter 2>/dev/null && \
        ensure_clawrouter_cmd && {
            echo "[INFO] ClawRouter 从备份恢复成功"
            return 0
        }
        echo "[WARN] 备份恢复失败，回退到 npm 安装"
    fi

    # 策略2：从宿主机 node_modules 挂载
    if [ -f "/usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js" ]; then
        echo "[INFO] 从挂载的 node_modules 恢复 ClawRouter..."
        ensure_clawrouter_cmd
        return 0
    fi

    # 策略3：npm install
    for registry in "https://registry.npmmirror.com" "https://registry.npmjs.org"; do
        echo "[INFO] 尝试使用 $registry..."
        npm config set registry "$registry" --location=user 2>/dev/null
        if npm install -g @blockrun/clawrouter 2>&1 | grep -q "added"; then
            echo "[INFO] ClawRouter npm 安装成功"
            ensure_clawrouter_cmd
            return 0
        fi
    done

    return 1
}

# ============================================
# 主流程
# ============================================

echo "=========================================="
echo "  Agent Awake — 容器启动"
echo "=========================================="
echo "  DATA_DIR: $DATA_DIR"
echo "  OPENCLAW_STATE_DIR: $OPENCLAW_STATE_DIR"
echo "  GATEWAY_PORT: $GATEWAY_PORT"
echo "  CLAWROUTER_PORT: $CLAWROUTER_PORT"
echo "=========================================="

# Step 1: 创建必要目录
mkdir -p "$DATA_DIR"/{config,workspace,logs,scripts,checkpoints,state}

# Step 1.5: 【问题2修复】身份文件持久化恢复
# 如果外层存在身份文件但 workspace/ 下不存在，从外层恢复
echo "[INFO] 检查身份文件持久化状态..."
for identity_file in IDENTITY.md SOUL.md USER.md TOOLS.md COMMUNITY.md HEARTBEAT.md; do
    outer_file="$DATA_DIR/$identity_file"
    inner_file="$DATA_DIR/workspace/$identity_file"
    if [ -f "$outer_file" ] && [ ! -f "$inner_file" ]; then
        echo "[INFO] 从外层恢复 $identity_file 到 workspace/"
        cp "$outer_file" "$inner_file"
    fi
done

# Step 2: 安装 OpenClaw
if ! check_openclaw; then
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if install_openclaw; then
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo "[WARN] OpenClaw 安装失败，重试 $RETRY_COUNT/$MAX_RETRIES"
        [ $RETRY_COUNT -lt $MAX_RETRIES ] && sleep $RETRY_COUNT
    done
fi
ensure_openclaw_cmd

if ! check_openclaw; then
    echo "[ERROR] OpenClaw 安装失败，退出"
    exit 1
fi

# Step 3: 安装 ClawRouter
if ! check_clawrouter; then
    RETRY_COUNT=0
    while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
        if install_clawrouter; then
            break
        fi
        RETRY_COUNT=$((RETRY_COUNT+1))
        echo "[WARN] ClawRouter 安装失败，重试 $RETRY_COUNT/$MAX_RETRIES"
        [ $RETRY_COUNT -lt $MAX_RETRIES ] && sleep $RETRY_COUNT
    done
fi
ensure_clawrouter_cmd

# Step 4: 生成配置（从模板，必须成功）
mkdir -p "$OPENCLAW_STATE_DIR"
if [ ! -f "$OPENCLAW_STATE_DIR/openclaw.json" ]; then
    echo "[INFO] 生成配置文件..."
    GW_TOKEN=$(openssl rand -hex 24 2>/dev/null || head -c 24 /dev/urandom | xxd -p)
    if ! generate_config "$OPENCLAW_STATE_DIR/openclaw.json" "$GW_TOKEN"; then
        echo "[ERROR] 配置文件生成失败，退出"
        exit 1
    fi
    echo "[INFO] Gateway Token: $GW_TOKEN"
fi

# Step 5: 符号链接
mkdir -p /root/.openclaw
ln -sf "$OPENCLAW_STATE_DIR/openclaw.json" /root/.openclaw/openclaw.json 2>/dev/null || true
for subdir in agents extensions blockrun logs; do
    if [ -d "$OPENCLAW_STATE_DIR/$subdir" ]; then
        ln -sfn "$OPENCLAW_STATE_DIR/$subdir" /root/.openclaw/$subdir 2>/dev/null || true
    fi
done

# Step 6: 启动 ClawRouter
echo "[INFO] 启动 ClawRouter Proxy (端口 $CLAWROUTER_PORT)..."
mkdir -p "$DATA_DIR/logs"
if command -v clawrouter > /dev/null 2>&1; then
    clawrouter --port $CLAWROUTER_PORT proxy > "$DATA_DIR/logs/clawrouter.log" 2>&1 &
    echo "[INFO] ClawRouter 已启动 (PID: $!)"
elif [ -f "/usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js" ]; then
    node /usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js --port $CLAWROUTER_PORT proxy > "$DATA_DIR/logs/clawrouter.log" 2>&1 &
    echo "[INFO] ClawRouter via node 已启动 (PID: $!)"
else
    echo "[ERROR] ClawRouter 不可用"
    exit 1
fi

sleep 5

# Step 7: 启动 Gateway
echo "[INFO] 启动 OpenClaw Gateway (端口 $GATEWAY_PORT)..."
(
    export OPENCLAW_STATE_DIR="$OPENCLAW_STATE_DIR"
    export OPENCLAW_CONFIG="$OPENCLAW_STATE_DIR/openclaw.json"
    cd "$OPENCLAW_STATE_DIR" || cd "$DATA_DIR"
    exec openclaw gateway > "$DATA_DIR/logs/gateway.log" 2>&1
) &

sleep 8

# Step 8: 验证
if check_port $GATEWAY_PORT; then
    echo "[WARN] Gateway 端口 $GATEWAY_PORT 未被占用，可能启动失败"
    echo "[INFO] 检查日志: $DATA_DIR/logs/gateway.log"
else
    echo "[OK] Gateway 监听中 (端口 $GATEWAY_PORT)"
fi

if check_port $CLAWROUTER_PORT; then
    echo "[WARN] ClawRouter 端口 $CLAWROUTER_PORT 未被占用，可能启动失败"
else
    echo "[OK] ClawRouter 监听中 (端口 $CLAWROUTER_PORT)"
fi

# Step 9: 输出调用信息
echo ""
echo "=========================================="
echo "  启动完成"
echo "=========================================="
echo ""
echo "  身份文件位置: $DATA_DIR/workspace/"
echo "  日志位置:"
echo "    - Gateway: $DATA_DIR/logs/gateway.log"
echo "    - ClawRouter: $DATA_DIR/logs/clawrouter.log"
echo ""

# 提取 Gateway Token
GW_TOKEN_DISPLAY=""
if [ -f "$OPENCLAW_STATE_DIR/openclaw.json" ]; then
    GW_TOKEN_DISPLAY=$(grep -o '"token"[[:space:]]*:[[:space:]]*"[^"]*"' "$OPENCLAW_STATE_DIR/openclaw.json" 2>/dev/null | head -1 | sed 's/"token"[[:space:]]*:[[:space:]]*"//;s/"$//')
fi

IDEM_KEY=$(openssl rand -hex 8 2>/dev/null || echo 'test-key')
echo "  对话调用方式:"
echo "    openclaw gateway call agent \\"
echo "      --token $GW_TOKEN_DISPLAY \\"
echo "      --params '{\"message\":\"你好\",\"agentId\":\"main\",\"idempotencyKey\":\"$IDEM_KEY\"}' \\"
echo "      --expect-final --timeout 80000"
echo ""
echo "=========================================="

# 保持容器运行
tail -f /dev/null
