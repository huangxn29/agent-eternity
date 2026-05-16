#!/bin/bash
# ============================================
# Agent Awake - 创建Agent v2.1
# ============================================
# 重构版本，支持配置文件驱动、模板化身份文件、多网络模式
# ============================================

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$SCRIPT_DIR/platform.conf"

# 加载配置文件
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
fi

# ============ 默认值 ============
AGENT_NAME=""
AGENT_ID=""
AGENT_EMOJI=""
CPU_LIMIT="${DEFAULT_CPU:-1.0}"
MEMORY_LIMIT="${DEFAULT_MEMORY:-1536M}"
GATEWAY_PORT=""
CLAWROUTER_PORT=""
DATA_DIR="${DATA_DIR:-./agent-awake-data}"
OWNER="${OWNER:-}"
OWNER_EMAIL="${OWNER_EMAIL:-}"
ENGINE="${ENGINE:-openclaw}"
NETWORK_MODE="${NETWORK_MODE:-host}"
GW_PORT_BASE="${GW_PORT_BASE:-18789}"
CR_PORT_BASE="${CR_PORT_BASE:-8402}"
IMAGE_NAME="${IMAGE_NAME:-agent-awake-base:latest}"
SOUL_TEMPLATE=""
TIMEZONE="${TIMEZONE:-Asia/Shanghai}"
CREATED_DATE="$(date +%Y-%m-%d)"

# Emoji列表
EMOJI_LIST=(🔮 ⚡ 🌊 🔥 🌟 ❄️ 🍀 🎯 💎 🦊 🐉 🦄 🌈 🎪 🎭 🚀 🌌)

# ============ JSON处理函数（兼容jq和纯bash）============

# 读取JSON值
json_get() {
    local file="$1"
    local key="$2"
    
    if [ ! -f "$file" ]; then
        echo ""
        return
    fi
    
    if command -v jq &> /dev/null; then
        jq -r ".$key // \"\"" "$file" 2>/dev/null
    else
        # 纯bash简单解析（仅支持简单字符串值）
        grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$file" 2>/dev/null | sed 's/.*://;s/"//g' | head -1
    fi
}

# 读取JSON数组长度
json_array_length() {
    local file="$1"
    local key="$2"
    
    if [ ! -f "$file" ]; then
        echo "0"
        return
    fi
    
    if command -v jq &> /dev/null; then
        jq ".$key | length" "$file" 2>/dev/null || echo "0"
    else
        # 简单计数
        grep -c "\"id\"" "$file" 2>/dev/null || echo "0"
    fi
}

# 添加JSON数组元素
json_array_add() {
    local file="$1"
    local key="$2"
    local element="$3"
    
    if command -v jq &> /dev/null; then
        echo "$element" | jq -s ".$key += [input]" "$file" - > /tmp/json.tmp && mv /tmp/json.tmp "$file"
    fi
}

# 更新JSON字段
json_update() {
    local file="$1"
    local key="$2"
    local value="$3"
    
    if command -v jq &> /dev/null; then
        jq --arg v "$value" ".$key = \$v" "$file" > /tmp/json.tmp && mv /tmp/json.tmp "$file"
    fi
}

# 从agents数组删除元素
json_array_remove() {
    local file="$1"
    local key="$2"
    local value="$3"
    
    if command -v jq &> /dev/null; then
        jq ".$key = (.$key | map(select(.id != \"$value\")))" "$file" > /tmp/json.tmp && mv /tmp/json.tmp "$file"
    fi
}

# ============ 模板渲染函数 ============

# 渲染模板文件
# 模板使用 {{变量名}} 占位符，此函数替换为实际值
render_template() {
    local template_file="$1"
    local output_file="$2"
    
    if [ ! -f "$template_file" ]; then
        echo "[ERROR] 模板文件不存在: $template_file"
        return 1
    fi
    
    # 计算主机地址（bridge模式下用容器名，host模式下用localhost）
    if [ "$NETWORK_MODE" = "bridge" ]; then
        GATEWAY_HOST="$AGENT_ID-gateway"
        CLAWROUTER_HOST="$AGENT_ID-clawrouter"
    else
        GATEWAY_HOST="localhost"
        CLAWROUTER_HOST="localhost"
    fi
    
    # 读取模板内容
    local content
    content=$(cat "$template_file")
    
    # 使用 sed 逐个替换 {{变量名}} 占位符
    content=$(echo "$content" | sed \
        -e "s|{{AGENT_NAME}}|${AGENT_NAME}|g" \
        -e "s|{{AGENT_ID}}|${AGENT_ID}|g" \
        -e "s|{{AGENT_EMOJI}}|${AGENT_EMOJI}|g" \
        -e "s|{{OWNER}}|${OWNER}|g" \
        -e "s|{{OWNER_EMAIL}}|${OWNER_EMAIL}|g" \
        -e "s|{{GATEWAY_PORT}}|${GATEWAY_PORT}|g" \
        -e "s|{{CLAWROUTER_PORT}}|${CLAWROUTER_PORT}|g" \
        -e "s|{{GATEWAY_HOST}}|${GATEWAY_HOST}|g" \
        -e "s|{{CLAWROUTER_HOST}}|${CLAWROUTER_HOST}|g" \
        -e "s|{{CPU_LIMIT}}|${CPU_LIMIT}|g" \
        -e "s|{{MEMORY_LIMIT}}|${MEMORY_LIMIT}|g" \
        -e "s|{{CREATED_DATE}}|${CREATED_DATE}|g" \
        -e "s|{{TIMEZONE}}|${TIMEZONE}|g" \
        -e "s|{{NETWORK_MODE}}|${NETWORK_MODE}|g" \
        -e "s|{{DATA_DIR}}|${DATA_DIR}|g" \
        -e "s|{{IMAGE_NAME}}|${IMAGE_NAME}|g" \
        -e "s|{{WALLET_ETH}}|${WALLET_ETH:-未提取}|g" \
        -e "s|{{WALLET_SOL}}|${WALLET_SOL:-未提取}|g" \
        -e "s|{{ENGINE}}|${ENGINE}|g"
    )
    
    echo "$content" > "$output_file"
}

# ============ 端口检测函数 ============

# 检查端口是否可用
check_port() {
    local port="$1"
    
    if command -v ss &> /dev/null; then
        ss -tlnp 2>/dev/null | grep -q ":$port " && return 1
    elif command -v netstat &> /dev/null; then
        netstat -tlnp 2>/dev/null | grep -q ":$port " && return 1
    fi
    
    # 尝试绑定测试
    if command -v timeout &> /dev/null; then
        timeout 1 bash -c "echo '' > /dev/tcp/127.0.0.1/$port" 2>/dev/null && return 1
    fi
    
    return 0
}

# ============ 参数解析 ============
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --name) AGENT_NAME="$2"; shift 2 ;;
            --agent-id) AGENT_ID="$2"; shift 2 ;;
            --emoji) AGENT_EMOJI="$2"; shift 2 ;;
            --cpu) CPU_LIMIT="$2"; shift 2 ;;
            --memory) MEMORY_LIMIT="$2"; shift 2 ;;
            --gateway-port) GATEWAY_PORT="$2"; shift 2 ;;
            --clawrouter-port) CLAWROUTER_PORT="$2"; shift 2 ;;
            --data-dir) DATA_DIR="$2"; shift 2 ;;
            --owner) OWNER="$2"; shift 2 ;;
            --owner-email) OWNER_EMAIL="$2"; shift 2 ;;
            --engine) ENGINE="$2"; shift 2 ;;
            --network-mode) NETWORK_MODE="$2"; shift 2 ;;
            --soul-template) SOUL_TEMPLATE="$2"; shift 2 ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --name <名称>           Agent名称（必填）"
                echo "  --agent-id <ID>        Agent唯一标识符（必填）"
                echo "  --emoji <emoji>        Agent emoji"
                echo "  --cpu <配额>           CPU配额，默认 $CPU_LIMIT"
                echo "  --memory <配额>        内存配额，默认 $MEMORY_LIMIT"
                echo "  --gateway-port <端口>  Gateway端口"
                echo "  --clawrouter-port <端口> ClawRouter端口"
                echo "  --data-dir <路径>      数据目录"
                echo "  --owner <名称>         主人名称"
                echo "  --owner-email <邮箱>   主人邮箱"
                echo "  --engine <引擎>        引擎类型，默认 $ENGINE"
                echo "  --network-mode <模式> 网络模式 host|bridge"
                echo "  --soul-template <文件> 自定义灵魂模板"
                exit 0
                ;;
            *) echo "未知参数: $1"; exit 1 ;;
        esac
    done
}

# ============ 主流程 ============

main() {
    # 解析参数
    parse_args "$@"
    
    # 验证必填参数
    if [ -z "$AGENT_NAME" ]; then
        echo "[ERROR] 必须指定 --name"
        exit 1
    fi
    if [ -z "$AGENT_ID" ]; then
        echo "[ERROR] 必须指定 --agent-id"
        exit 1
    fi
    
    # 验证目录存在
    if [ ! -d "$DATA_DIR" ]; then
        echo "[ERROR] 平台未初始化，请先运行 platform-init.sh"
        exit 1
    fi
    
    # 从配置文件加载（覆盖命令行）
    if [ -f "$CONFIG_FILE" ]; then
        source "$CONFIG_FILE"
        # 命令行参数已设置的不要覆盖
        [ -n "$OWNER" ] && OWNER="${OWNER:-$(json_get "$DATA_DIR/platform.json" owner)}"
        [ -n "$OWNER_EMAIL" ] && OWNER_EMAIL="${OWNER_EMAIL:-$(json_get "$DATA_DIR/platform.json" owner_email)}"
    fi
    
    # 获取已有Agent数量，自动分配端口
    local agent_count
    agent_count=$(json_array_length "$DATA_DIR/platform.json" "agents")
    
    if [ -z "$GATEWAY_PORT" ]; then
        GATEWAY_PORT=$((GW_PORT_BASE + agent_count))
    fi
    if [ -z "$CLAWROUTER_PORT" ]; then
        CLAWROUTER_PORT=$((CR_PORT_BASE + agent_count))
    fi
    if [ -z "$AGENT_EMOJI" ]; then
        AGENT_EMOJI="${EMOJI_LIST[$agent_count % ${#EMOJI_LIST[@]}]}"
    fi
    
    # 验证端口
    if ! check_port "$GATEWAY_PORT"; then
        echo "[ERROR] 端口 $GATEWAY_PORT 已被占用"
        exit 1
    fi
    if ! check_port "$CLAWROUTER_PORT"; then
        echo "[ERROR] 端口 $CLAWROUTER_PORT 已被占用"
        exit 1
    fi
    
    AGENT_DIR="$DATA_DIR/$AGENT_ID"
    COMPOSE_FILE="$DATA_DIR/docker-compose.yml"
    PLATFORM_JSON="$DATA_DIR/platform.json"
    
    echo "=========================================="
    echo "  创建Agent: $AGENT_NAME ($AGENT_ID)"
    echo "=========================================="
    echo "  Emoji: $AGENT_EMOJI"
    echo "  CPU: $CPU_LIMIT | 内存: $MEMORY_LIMIT"
    echo "  Gateway: $GATEWAY_PORT | ClawRouter: $CLAWROUTER_PORT"
    echo "  网络模式: $NETWORK_MODE"
    echo "  引擎: $ENGINE"
    echo "=========================================="
    
    # 检查Agent是否已存在
    if [ -d "$AGENT_DIR" ] && [ -f "$AGENT_DIR/config/.initialized" ]; then
        echo "[ERROR] Agent $AGENT_ID 已存在"
        exit 1
    fi
    
    # Step 1: 创建数据目录
    echo "[INFO] 创建数据目录..."
    mkdir -p "$AGENT_DIR"/{config,workspace,logs,scripts,checkpoints}
    
    # Step 2: 调用引擎配置（生成 openclaw.json）
    echo "[INFO] 配置OpenClaw引擎..."
    
    # 加载引擎脚本
    source "$SKILL_DIR/engines/$ENGINE/engine.sh"
    
    # 调用 engine_configure() 生成完整配置
    local gw_token
    gw_token=$(engine_configure "$AGENT_DIR" "$GATEWAY_PORT" "$CLAWROUTER_PORT")
    
    echo "[OK] OpenClaw配置已生成"
    
    # Step 3: 渲染身份文件（放到 workspace/ 子目录）
    echo "[INFO] 创建身份文件（workspace/目录）..."
    
    # 确保 workspace 目录存在
    mkdir -p "$AGENT_DIR/workspace"
    
    # IDENTITY.md - 放到 workspace/
    render_template "$SKILL_DIR/templates/IDENTITY.md.template" "$AGENT_DIR/workspace/IDENTITY.md"
    
    # SOUL.md (支持自定义模板) - 放到 workspace/
    if [ -n "$SOUL_TEMPLATE" ] && [ -f "$SOUL_TEMPLATE" ]; then
        render_template "$SOUL_TEMPLATE" "$AGENT_DIR/workspace/SOUL.md"
    else
        render_template "$SKILL_DIR/templates/SOUL.md.template" "$AGENT_DIR/workspace/SOUL.md"
    fi
    
    # USER.md - 放到 workspace/
    render_template "$SKILL_DIR/templates/USER.md.template" "$AGENT_DIR/workspace/USER.md"
    
    # TOOLS.md - 放到 workspace/
    render_template "$SKILL_DIR/templates/TOOLS.md.template" "$AGENT_DIR/workspace/TOOLS.md"
    
    # 同时在根目录创建软链接，方便查看
    ln -sf workspace/IDENTITY.md "$AGENT_DIR/IDENTITY.md" 2>/dev/null || true
    ln -sf workspace/SOUL.md "$AGENT_DIR/SOUL.md" 2>/dev/null || true
    ln -sf workspace/USER.md "$AGENT_DIR/USER.md" 2>/dev/null || true
    ln -sf workspace/TOOLS.md "$AGENT_DIR/TOOLS.md" 2>/dev/null || true
    
    echo "[OK] 身份文件已创建（4件套 → workspace/）"
    
    # Step 4: 更新docker-compose.yml
    
    # host模式下不挂载 /usr/lib/node_modules（容器自带）
    
    echo "[INFO] 更新Docker Compose配置..."
    
    if [ ! -f "$COMPOSE_FILE" ] || ! grep -q "services:" "$COMPOSE_FILE" 2>/dev/null; then
        cat > "$COMPOSE_FILE" << 'EOF'
version: "3.8"

services:
EOF
    fi
    
    # 根据网络模式生成服务配置
    if [ "$NETWORK_MODE" = "bridge" ]; then
        # Bridge模式：使用端口映射
        cat >> "$COMPOSE_FILE" << EOF

  ${AGENT_ID}:
    build: ./images/openclaw-agent
    container_name: ${AGENT_ID}
    restart: always
    networks:
      - agent-awake-net
    ports:
      - "${GATEWAY_PORT}:18789"
      - "${CLAWROUTER_PORT}:8402"
    volumes:
      - ./${AGENT_ID}/:/app/data/openclaw/
      - /usr/lib/node_modules/openclaw:/usr/lib/node_modules/openclaw:ro
      - /usr/lib/node_modules/@blockrun/clawrouter:/usr/lib/node_modules/@blockrun/clawrouter:ro
    environment:
      - NODE_ENV=production
      - AGENT_ID=${AGENT_ID}
      - AGENT_NAME=${AGENT_NAME}
      - GATEWAY_PORT=18789
      - CLAWROUTER_PORT=8402
      - ENGINE=${ENGINE}
      - DATA_DIR=/app/data/openclaw
      - OPENCLAW_STATE_DIR=/app/data/openclaw/state
    deploy:
      resources:
        limits:
          cpus: "${CPU_LIMIT}"
          memory: ${MEMORY_LIMIT}

networks:
  agent-awake-net:
    external: true
EOF
    else
        # Host模式：直接使用宿主机网络，需要挂载node_modules
        cat >> "$COMPOSE_FILE" << EOF

  ${AGENT_ID}:
    build: ./images/openclaw-agent
    container_name: ${AGENT_ID}
    restart: always
    network_mode: host
    volumes:
      - ./${AGENT_ID}/:/app/data/openclaw/
      - /usr/lib/node_modules/openclaw:/usr/lib/node_modules/openclaw:ro
      - /usr/lib/node_modules/@blockrun/clawrouter:/usr/lib/node_modules/@blockrun/clawrouter:ro
    environment:
      - NODE_ENV=production
      - AGENT_ID=${AGENT_ID}
      - AGENT_NAME=${AGENT_NAME}
      - GATEWAY_PORT=${GATEWAY_PORT}
      - CLAWROUTER_PORT=${CLAWROUTER_PORT}
      - ENGINE=${ENGINE}
      - DATA_DIR=/app/data/openclaw
      - OPENCLAW_STATE_DIR=/app/data/openclaw/state
    deploy:
      resources:
        limits:
          cpus: "${CPU_LIMIT}"
          memory: ${MEMORY_LIMIT}
EOF
    fi
    
    echo "[OK] Docker Compose配置已更新"
    
    # Step 5: 准备构建上下文并构建镜像
    echo "[INFO] 准备构建上下文..."
    cd "$DATA_DIR"
    local IMAGES_DIR="$DATA_DIR/images/openclaw-agent"
    
    # 确保镜像存在
    if ! docker image inspect "$IMAGE_NAME" &> /dev/null; then
        echo "[INFO] 镜像不存在，准备构建目录..."
        
        # 创建构建上下文目录
        mkdir -p "$IMAGES_DIR/engines"
        mkdir -p "$IMAGES_DIR/agent-deploy-references"
        
        # 复制引擎文件
        cp -r "$SKILL_DIR/engines/"* "$IMAGES_DIR/engines/"
        
        # 复制 agent-deploy/references/（模板必须存在）
        if [ -d "$SKILL_DIR/../agent-deploy/references" ]; then
            cp -r "$SKILL_DIR/../agent-deploy/references/"* "$IMAGES_DIR/agent-deploy-references/"
            echo "[INFO] agent-deploy references 已复制"
        else
            echo "[ERROR] 未找到 agent-deploy/references/"
            return 1
        fi
        
        # 复制 entrypoint.sh（必须存在）
        local skill_entrypoint="$SKILL_DIR/images/openclaw-agent/entrypoint.sh"
        if [ -f "$skill_entrypoint" ]; then
            cp "$skill_entrypoint" "$IMAGES_DIR/entrypoint.sh"
            chmod +x "$IMAGES_DIR/entrypoint.sh"
        else
            echo "[ERROR] entrypoint.sh 不存在: $skill_entrypoint"
            return 1
        fi
        
        # 生成 Dockerfile（轻量版：只装apt依赖，node_modules通过volume挂载）
        cat > "$IMAGES_DIR/Dockerfile" << 'DOCKERFILE'
# Agent Awake Base Image (轻量版)
FROM node:22-bookworm

# 安装基础依赖
RUN apt-get update && apt-get install -y \
    curl git ca-certificates rsync jq iproute2 \
    && rm -rf /var/lib/apt/lists/*

# 复制引擎
COPY engines/ /opt/engines/

# 复制 agent-deploy/references/（模板必须存在）
COPY agent-deploy-references/ /opt/engines/agent-deploy/references/

# 创建挂载点目录
RUN mkdir -p /usr/lib/node_modules/openclaw && \
    mkdir -p /usr/lib/node_modules/@blockrun/clawrouter

# 创建命令脚本
RUN echo '#!/bin/bash' > /usr/local/bin/openclaw && \
    echo 'exec node /usr/lib/node_modules/openclaw/openclaw.mjs "$@"' >> /usr/local/bin/openclaw && \
    chmod +x /usr/local/bin/openclaw && \
    echo '#!/bin/bash' > /usr/local/bin/clawrouter && \
    echo 'exec node /usr/lib/node_modules/@blockrun/clawrouter/dist/cli.js "$@"' >> /usr/local/bin/clawrouter && \
    chmod +x /usr/local/bin/clawrouter

# 复制入口脚本
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

EXPOSE 18789 8402

CMD ["/entrypoint.sh"]
DOCKERFILE

        echo "[INFO] 正在构建镜像..."
        docker build -t "$IMAGE_NAME" "$IMAGES_DIR" 2>&1 | tail -20
    fi
    
    # 启动容器
    docker compose up -d "$AGENT_ID"
    
    echo "[INFO] 等待服务启动..."
    sleep 15
    
    # Step 6: 健康检查
    echo "[INFO] 验证Agent状态..."
    local retries=0
    local max_retries="${HEALTH_CHECK_RETRIES:-10}"
    
    while [ $retries -lt $max_retries ]; do
        if curl -s "http://localhost:$GATEWAY_PORT/health" 2>/dev/null | grep -q "ok"; then
            echo "[OK] Gateway 运行正常"
            break
        fi
        retries=$((retries + 1))
        echo "[INFO] 等待Gateway启动... ($retries/$max_retries)"
        sleep 3
    done
    
    # Step 7: 提取钱包地址
    local wallet=""
    if curl -s "http://localhost:$CLAWROUTER_PORT/health" 2>/dev/null | grep -q "ok\|wallet"; then
        if command -v jq &> /dev/null; then
            wallet=$(curl -s "http://localhost:$CLAWROUTER_PORT/health" | jq -r '.wallet // empty' 2>/dev/null)
        else
            wallet=$(curl -s "http://localhost:$CLAWROUTER_PORT/health" | grep -o '"wallet":"[^"]*"' | sed 's/"wallet":"//;s/"$//')
        fi
        
        if [ -n "$wallet" ]; then
            echo "[OK] 钱包地址: $wallet"
            # 更新 workspace/ 中的 IDENTITY.md 钱包地址
            export WALLET_ETH="$wallet"
            render_template "$SKILL_DIR/templates/IDENTITY.md.template" "$AGENT_DIR/workspace/IDENTITY.md.tmp"
            mv "$AGENT_DIR/workspace/IDENTITY.md.tmp" "$AGENT_DIR/workspace/IDENTITY.md"
        fi
    fi
    
    # Step 8: 标记初始化完成
    touch "$AGENT_DIR/config/.initialized"
    
    # Step 9: 更新platform.json（包含GW_TOKEN）
    echo "[INFO] 更新平台状态..."
    
    local idempotency_key
    idempotency_key=$(openssl rand -hex 8 2>/dev/null || echo "test-key")
    
    local agent_json="{
        \"id\": \"$AGENT_ID\",
        \"name\": \"$AGENT_NAME\",
        \"emoji\": \"$AGENT_EMOJI\",
        \"engine\": \"$ENGINE\",
        \"container\": \"$AGENT_ID\",
        \"gateway_port\": $GATEWAY_PORT,
        \"clawrouter_port\": $CLAWROUTER_PORT,
        \"network_mode\": \"$NETWORK_MODE\",
        \"cpu\": \"$CPU_LIMIT\",
        \"memory\": \"$MEMORY_LIMIT\",
        \"wallet_eth\": \"$wallet\",
        \"gw_token\": \"$gw_token\",
        \"status\": \"running\",
        \"created\": \"$CREATED_DATE\"
    }"
    
    if command -v jq &> /dev/null; then
        echo "$agent_json" | jq -s '.[0].agents += [input]' "$PLATFORM_JSON" - > /tmp/platform.json.tmp && mv /tmp/platform.json.tmp "$PLATFORM_JSON"
    fi
    
    # 输出结果
    echo ""
    echo "=========================================="
    echo "  Agent 创建成功!"
    echo "=========================================="
    echo "  名称: $AGENT_NAME"
    echo "  ID: $AGENT_ID"
    echo "  Emoji: $AGENT_EMOJI"
    echo "  Gateway: localhost:$GATEWAY_PORT"
    echo "  ClawRouter: localhost:$CLAWROUTER_PORT"
    [ -n "$wallet" ] && echo "  钱包: $wallet"
    echo ""
    echo "  【重要】Gateway Token: $gw_token"
    echo ""
    echo "  对话调用方式:"
    echo "    openclaw gateway call agent \\"
    echo "      --token $gw_token \\"
    echo "      --params '{\"message\":\"你好\",\"agentId\":\"main\",\"idempotencyKey\":\"$idempotency_key\"}' \\"
    echo "      --expect-final --timeout 80000"
    echo ""
    echo "  查看日志:"
    echo "    docker logs $AGENT_ID"
    echo "    cat $AGENT_DIR/logs/gateway.log"
    echo "    cat $AGENT_DIR/logs/clawrouter.log"
    echo "=========================================="
}

main "$@"
