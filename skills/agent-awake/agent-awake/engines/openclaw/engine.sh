#!/bin/bash
# ============================================
# Agent Awake — OpenClaw Engine Adapter
# ============================================
# 本文件是 adapter 层，将 agent-awake 的概念映射到 agent-deploy framework
# 核心原则：只保留必要的适配逻辑，模板必须来自 agent-deploy/references/
# ============================================

ENGINE_ID="openclaw"
ENGINE_NAME="OpenClaw + ClawRouter"
ENGINE_VERSION="2026.5.3-1"

# 引擎目录
ENGINE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$ENGINE_DIR/../.." && pwd)"

# agent-deploy 技能路径
ETERNAL_SKILL_DIR=""
ETERNAL_ENGINE_SCRIPT=""
ETERNAL_REFERENCES_DIR=""

# ============================================
# 辅助函数
# ============================================

# 查找 agent-deploy 技能
find_eternal_skill() {
    local search_paths=(
        "$SKILL_DIR/../agent-deploy"
        "$SKILL_DIR/../../agent-deploy"
        "$(dirname "$SKILL_DIR")/agent-deploy"
        "./技能/agent-deploy"
        "../技能/agent-deploy"
        "/opt/skills/agent-deploy"
    )
    
    for p in "${search_paths[@]}"; do
        if [ -f "$p/engines/openclaw/engine.sh" ]; then
            ETERNAL_SKILL_DIR="$p"
            ETERNAL_ENGINE_SCRIPT="$p/engines/openclaw/engine.sh"
            ETERNAL_REFERENCES_DIR="$p/references"
            return 0
        fi
    done
    
    # 从环境变量查找
    if [ -n "$OPENCLAW_ETERNAL_DIR" ] && [ -f "$OPENCLAW_ETERNAL_DIR/engines/openclaw/engine.sh" ]; then
        ETERNAL_SKILL_DIR="$OPENCLAW_ETERNAL_DIR"
        ETERNAL_ENGINE_SCRIPT="$OPENCLAW_ETERNAL_DIR/engines/openclaw/engine.sh"
        ETERNAL_REFERENCES_DIR="$OPENCLAW_ETERNAL_DIR/references"
        return 0
    fi
    
    return 1
}

# ============================================
# 引擎Hook函数 — 适配 agent-awake
# ============================================

# 安装引擎（在容器首次启动时调用）
engine_install() {
    echo "[ENGINE] 安装 OpenClaw 引擎..."
    
    if command -v openclaw &> /dev/null; then
        echo "[ENGINE] OpenClaw 已安装，跳过"
        return 0
    fi
    
    local registries=("https://registry.npmmirror.com" "https://registry.npmjs.org")
    for registry in "${registries[@]}"; do
        echo "[ENGINE] 尝试 registry: $registry"
        if npm install -g openclaw@$ENGINE_VERSION --registry "$registry" 2>&1 | grep -q "added"; then
            echo "[ENGINE] OpenClaw 安装成功"
            
            # 确保命令可用
            if [ -f "/usr/lib/node_modules/openclaw/openclaw.mjs" ] && [ ! -f "/usr/local/bin/openclaw" ]; then
                echo '#!/bin/bash' > /usr/local/bin/openclaw
                echo 'exec node /usr/lib/node_modules/openclaw/openclaw.mjs "$@"' >> /usr/local/bin/openclaw
                chmod +x /usr/local/bin/openclaw
            fi
            return 0
        fi
    done
    
    echo "[ERROR] OpenClaw 安装失败"
    return 1
}

# 配置引擎（创建 openclaw.json）
# 在 agent-create.sh 中调用，生成配置文件到 state/ 目录
engine_configure() {
    local agent_dir="${1:-}"
    local gateway_port="${2:-18789}"
    local clawrouter_port="${3:-8402}"
    
    if [ -z "$agent_dir" ]; then
        echo "[ENGINE] 错误: 缺少 agent_dir 参数"
        return 1
    fi
    
    echo "[ENGINE] 配置 OpenClaw 引擎..."
    echo "[ENGINE]   agent_dir: $agent_dir"
    echo "[ENGINE]   gateway_port: $gateway_port"
    echo "[ENGINE]   clawrouter_port: $clawrouter_port"
    
    # 创建必要目录
    mkdir -p "$agent_dir/state"
    mkdir -p "$agent_dir/workspace"
    
    # 生成 Gateway Token
    local gw_token
    gw_token=$(openssl rand -hex 24 2>/dev/null || head -c 24 /dev/urandom | xxd -p)
    
    # 变量替换模板
    local workspace_path="$agent_dir/workspace"
    
    # 从 eternal references/ 读取模板（必须存在）
    echo "[ENGINE] 从 agent-deploy/references/ 读取配置模板..."
    local template_file=""
    
    # 搜索模板文件路径
    local search_paths=(
        "$SKILL_DIR/../agent-deploy/references/openclaw.json.template"
        "$SKILL_DIR/../../agent-deploy/references/openclaw.json.template"
        "$(dirname "$SKILL_DIR")/agent-deploy/references/openclaw.json.template"
        "./技能/agent-deploy/references/openclaw.json.template"
        "/app/data/skills/agent-deploy/references/openclaw.json.template"
    )
    
    for p in "${search_paths[@]}"; do
        if [ -f "$p" ]; then
            template_file="$p"
            break
        fi
    done
    
    if [ -n "$template_file" ] && [ -f "$template_file" ]; then
        echo "[ENGINE] 使用模板: $template_file"
        # 替换占位符
        sed -e "s/{{GATEWAY_PORT}}/$gateway_port/g" \
            -e "s/{{CLAWROUTER_PORT}}/$clawrouter_port/g" \
            -e "s/{{GW_TOKEN}}/$gw_token/g" \
            -e "s|{{WORKSPACE_PATH}}|$workspace_path|g" \
            "$template_file" > "$agent_dir/state/openclaw.json"
        
        echo "[ENGINE] OpenClaw 配置完成"
        echo "[ENGINE]   - Gateway Token: $gw_token"
        echo "[ENGINE]   - Config: $agent_dir/state/openclaw.json"
        echo "$gw_token"
        return 0
    fi
    
    # 模板找不到则报错退出
    echo "[ERROR] 未找到 openclaw.json.template"
    echo "[ERROR] 模板应位于 agent-deploy/references/openclaw.json.template"
    return 1
}

# 启动引擎（在容器内由 entrypoint.sh 调用）
engine_start() {
    local agent_dir="${1:-}"
    local gateway_port="${2:-18789}"
    local clawrouter_port="${3:-8402}"
    
    if [ -z "$agent_dir" ]; then
        echo "[ENGINE] 错误: 缺少 agent_dir 参数"
        return 1
    fi
    
    echo "[ENGINE] 启动引擎服务..."
    
    # 设置状态目录
    local state_dir="$agent_dir/state"
    local workspace_dir="$agent_dir/workspace"
    mkdir -p "$state_dir" "$workspace_dir" "$agent_dir/logs"
    
    # 确保 openclaw 命令可用
    if [ -f "/usr/lib/node_modules/openclaw/openclaw.mjs" ] && [ ! -f "/usr/local/bin/openclaw" ]; then
        echo '#!/bin/bash' > /usr/local/bin/openclaw
        echo 'exec node /usr/lib/node_modules/openclaw/openclaw.mjs "$@"' >> /usr/local/bin/openclaw
        chmod +x /usr/local/bin/openclaw
    fi
    
    # 创建符号链接
    mkdir -p /root/.openclaw
    rm -f /root/.openclaw/openclaw.json
    ln -sf "$state_dir/openclaw.json" /root/.openclaw/openclaw.json
    for subdir in agents extensions blockrun logs; do
        if [ -d "$state_dir/$subdir" ]; then
            rm -f "/root/.openclaw/$subdir"
            ln -sfn "$state_dir/$subdir" "/root/.openclaw/$subdir"
        fi
    done
    
    # 启动 ClawRouter
    local clawrouter_log="$agent_dir/logs/clawrouter.log"
    if command -v clawrouter &> /dev/null 2>&1; then
        echo "[ENGINE] 启动 ClawRouter (端口 $clawrouter_port)..."
        nohup clawrouter --port $clawrouter_port proxy > "$clawrouter_log" 2>&1 &
    elif [ -f "/usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js" ]; then
        echo "[ENGINE] 启动 ClawRouter via node (端口 $clawrouter_port)..."
        nohup node /usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js --port $clawrouter_port proxy > "$clawrouter_log" 2>&1 &
    else
        echo "[WARN] ClawRouter 未找到，尝试 npm 安装..."
        for registry in "https://registry.npmmirror.com" "https://registry.npmjs.org"; do
            npm install -g @blockrun/clawrouter --registry "$registry" 2>&1 | grep -q "added" && break
        done
        if command -v clawrouter &> /dev/null 2>&1; then
            nohup clawrouter --port $clawrouter_port proxy > "$clawrouter_log" 2>&1 &
        fi
    fi
    
    sleep 3
    
    # 启动 Gateway
    local gateway_log="$agent_dir/logs/gateway.log"
    if command -v openclaw &> /dev/null 2>&1; then
        echo "[ENGINE] 启动 OpenClaw Gateway (端口 $gateway_port)..."
        (
            export OPENCLAW_STATE_DIR="$state_dir"
            export OPENCLAW_CONFIG="$state_dir/openclaw.json"
            cd "$state_dir" || cd "$agent_dir"
            nohup openclaw gateway > "$gateway_log" 2>&1 &
        )
    else
        echo "[ERROR] OpenClaw 未找到"
        return 1
    fi
    
    sleep 5
    
    # 验证
    if curl -s "http://localhost:$gateway_port/health" 2>/dev/null | grep -q "ok"; then
        echo "[ENGINE] Gateway 健康检查通过"
    else
        echo "[WARN] Gateway 可能未就绪，请检查日志: $gateway_log"
    fi
    
    return 0
}

# 健康检查
engine_health_check() {
    local gateway_port="${1:-18789}"
    local clawrouter_port="${2:-8402}"
    local healthy=true
    
    # 检查 Gateway
    local gw_response
    gw_response=$(curl -s -w "\n%{http_code}" "http://localhost:$gateway_port/health" 2>/dev/null)
    local gw_code=$(echo "$gw_response" | tail -1)
    if [ "$gw_code" = "200" ]; then
        echo "[OK] Gateway (:$gateway_port): 健康"
    else
        echo "[FAIL] Gateway (:$gateway_port): HTTP $gw_code"
        healthy=false
    fi
    
    # 检查 ClawRouter
    local cr_response
    cr_response=$(curl -s -w "\n%{http_code}" "http://localhost:$clawrouter_port/health" 2>/dev/null)
    local cr_code=$(echo "$cr_response" | tail -1)
    if [ "$cr_code" = "200" ]; then
        echo "[OK] ClawRouter (:$clawrouter_port): 健康"
    else
        echo "[FAIL] ClawRouter (:$clawrouter_port): HTTP $cr_code"
        healthy=false
    fi
    
    [ "$healthy" = true ]
}

# 提取钱包地址（可选）
engine_extract_wallet() {
    local clawrouter_port="${1:-8402}"
    local wallet=""
    local solana=""
    
    local response
    response=$(curl -s "http://localhost:$clawrouter_port/health" 2>/dev/null)
    
    if command -v jq &> /dev/null; then
        wallet=$(echo "$response" | jq -r '.wallet // empty' 2>/dev/null)
        solana=$(echo "$response" | jq -r '.solana // empty' 2>/dev/null)
    else
        wallet=$(echo "$response" | grep -o '"wallet":"[^"]*"' | sed 's/"wallet":"//;s/"$//')
        solana=$(echo "$response" | grep -o '"solana":"[^"]*"' | sed 's/"solana":"//;s/"$//')
    fi
    
    if [ -n "$wallet" ]; then
        echo "ETH=$wallet"
        [ -n "$solana" ] && echo "SOL=$solana"
        return 0
    fi
    
    return 1
}

# 停止引擎
engine_stop() {
    local gateway_port="${1:-18789}"
    
    # 通过 Gateway API 优雅停止
    curl -s -X POST "http://localhost:$gateway_port/api/shutdown" 2>/dev/null
    
    # 强制停止端口进程
    if command -v lsof &> /dev/null; then
        lsof -ti :$gateway_port 2>/dev/null | xargs kill 2>/dev/null || true
    fi
    
    echo "[ENGINE] 引擎已停止"
    return 0
}
