#!/bin/bash
# ============================================
# Agent Awake - 平台初始化 v2.1
# ============================================
# 重构版本，支持配置文件驱动、多引擎、多网络模式
# ============================================

set -e

# 脚本目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CONFIG_FILE="$SCRIPT_DIR/platform.conf"

# 加载配置文件
if [ -f "$CONFIG_FILE" ]; then
    source "$CONFIG_FILE"
else
    echo "[WARN] 配置文件不存在: $CONFIG_FILE"
fi

# ============ 默认值 ============
DATA_DIR="${DATA_DIR:-./agent-awake-data}"
OWNER="${OWNER:-}"
OWNER_EMAIL="${OWNER_EMAIL:-}"
ENGINE="${ENGINE:-openclaw}"
NETWORK_MODE="${NETWORK_MODE:-host}"
GW_PORT_BASE="${GW_PORT_BASE:-18789}"
CR_PORT_BASE="${CR_PORT_BASE:-8402}"
DEFAULT_CPU="${DEFAULT_CPU:-1.0}"
DEFAULT_MEMORY="${DEFAULT_MEMORY:-1536M}"
IMAGE_NAME="${IMAGE_NAME:-agent-awake-base:latest}"
IMAGES_DIR="${IMAGES_DIR:-$DATA_DIR/images/openclaw-agent}"

# ============ 命令行参数 ============
SKIP_ENV_CHECK=false
SKIP_DOCKER_INSTALL=false
FORCE_REINIT=false
INTERACTIVE=true
CUSTOM_CONFIG=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --data-dir) DATA_DIR="$2"; shift 2 ;;
        --owner) OWNER="$2"; shift 2 ;;
        --owner-email) OWNER_EMAIL="$2"; shift 2 ;;
        --engine) ENGINE="$2"; shift 2 ;;
        --network-mode) NETWORK_MODE="$2"; shift 2 ;;
        --config) CUSTOM_CONFIG="$2"; shift 2 ;;
        --skip-env-check) SKIP_ENV_CHECK=true; shift ;;
        --skip-docker-install) SKIP_DOCKER_INSTALL=true; shift ;;
        --force) FORCE_REINIT=true; shift ;;
        --non-interactive) INTERACTIVE=false; shift ;;
        -h|--help) 
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --data-dir <路径>         平台数据目录"
            echo "  --owner <名称>           主人名称（必填）"
            echo "  --owner-email <邮箱>     主人邮箱（必填）"
            echo "  --engine <引擎>          引擎类型，默认 openclaw"
            echo "  --network-mode <模式>    网络模式 host|bridge，默认 host"
            echo "  --config <文件>          使用自定义配置文件"
            echo "  --skip-env-check         跳过环境检测"
            echo "  --skip-docker-install    跳过Docker安装"
            echo "  --force                  强制重新初始化"
            echo "  --non-interactive        非交互模式"
            exit 0
            ;;
        *) echo "未知参数: $1"; exit 1 ;;
    esac
done

# 使用自定义配置文件
if [ -n "$CUSTOM_CONFIG" ] && [ -f "$CUSTOM_CONFIG" ]; then
    source "$CUSTOM_CONFIG"
fi

# ============ 环境检测 ============
echo "=========================================="
echo "  Agent Awake - 初始化 v2.1"
echo "=========================================="

detect_environment() {
    echo ""
    echo ">>> 环境检测"
    echo "------------------------------------------"
    
    # OS信息
    if [ -f /etc/os-release ]; then
        source /etc/os-release
        echo "  操作系统: $PRETTY_NAME"
    elif [ -f /etc/redhat-release ]; then
        echo "  操作系统: $(cat /etc/redhat-release)"
    else
        echo "  操作系统: $(uname -s) $(uname -r)"
    fi
    
    # Docker检测
    if command -v docker &> /dev/null; then
        DOCKER_VERSION=$(docker --version 2>/dev/null | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
        echo "  Docker: ✅ 已安装 ($DOCKER_VERSION)"
        DOCKER_INSTALLED=true
    else
        echo "  Docker: ❌ 未安装"
        DOCKER_INSTALLED=false
    fi
    
    # CPU核心数
    CPU_CORES=$(nproc 2>/dev/null || grep -c ^processor /proc/cpuinfo 2>/dev/null || echo "1")
    echo "  CPU核心: $CPU_CORES"
    
    # 内存信息
    if command -v free &> /dev/null; then
        TOTAL_MEM=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')
        AVAIL_MEM=$(free -m 2>/dev/null | awk '/^Mem:/{print $7}')
        echo "  内存: 总计 ${TOTAL_MEM}M / 可用 ${AVAIL_MEM}M"
    fi
    
    # 磁盘空间
    DISK_AVAIL=$(df -BG "$PWD" 2>/dev/null | awk 'NR==2 {print $4}' | sed 's/G//')
    echo "  磁盘空间: 可用 ${DISK_AVAIL}G"
    
    # jq检测
    if command -v jq &> /dev/null; then
        echo "  jq: ✅ 可用"
        HAS_JQ=true
    else
        echo "  jq: ❌ 未安装（将尝试自动安装）"
        HAS_JQ=false
    fi
    
    # curl检测
    if command -v curl &> /dev/null; then
        echo "  curl: ✅ 可用"
    else
        echo "  curl: ❌ 未安装"
    fi
    
    # Node.js检测（可选）
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node --version 2>/dev/null)
        echo "  Node.js: ✅ $NODE_VERSION (可选)"
    else
        echo "  Node.js: ❌ 未安装 (可选，用于高级JSON处理)"
    fi
    
    echo "------------------------------------------"
    
    # 根据资源推荐配置
    echo ""
    echo ">>> 资源配置建议"
    if [ "$AVAIL_MEM" -lt 1536 ]; then
        echo "  ⚠️  内存较低，建议减少Agent数量"
        echo "  推荐配置: CPU=0.5, MEMORY=1024M"
    elif [ "$AVAIL_MEM" -gt 8192 ]; then
        echo "  ✅ 内存充足，最多可运行 $((AVAIL_MEM / 1536)) 个Agent"
    fi
    
    if [ "$CPU_CORES" -ge 4 ]; then
        echo "  ✅ CPU充足，支持多Agent并行"
    fi
}

# 安装jq
install_jq() {
    if [ "$HAS_JQ" = true ]; then
        return 0
    fi
    
    echo ""
    echo ">>> 安装 jq..."
    
    if command -v apt-get &> /dev/null; then
        apt-get update -qq && apt-get install -y jq 2>/dev/null && HAS_JQ=true && return 0
    elif command -v yum &> /dev/null; then
        yum install -y jq 2>/dev/null && HAS_JQ=true && return 0
    elif command -v apk &> /dev/null; then
        apk add jq 2>/dev/null && HAS_JQ=true && return 0
    fi
    
    # 尝试下载二进制
    if command -v curl &> /dev/null; then
        local arch=$(uname -m)
        local jq_url="https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-linux-${arch}"
        if [ "$arch" = "x86_64" ]; then
            jq_url="https://github.com/jqlang/jq/releases/download/jq-1.7.1/jq-linux-amd64"
        fi
        curl -sL "$jq_url" -o /usr/local/bin/jq && chmod +x /usr/local/bin/jq && HAS_JQ=true && return 0
    fi
    
    echo "[WARN] jq安装失败，部分功能可能受限"
    return 1
}

# 安装Docker
install_docker() {
    if [ "$DOCKER_INSTALLED" = true ]; then
        return 0
    fi
    
    echo ""
    echo ">>> 安装 Docker..."
    
    # 尝试多种安装方式
    if command -v curl &> /dev/null; then
        # 阿里云镜像
        if curl -fsSL https://get.docker.com | bash -s docker --mirror Aliyun 2>/dev/null; then
            echo "[OK] Docker 安装成功(阿里云镜像)"
            systemctl start docker 2>/dev/null || true
            return 0
        fi
        # 官方脚本
        if curl -fsSL https://get.docker.com | sh 2>/dev/null; then
            echo "[OK] Docker 安装成功(官方脚本)"
            systemctl start docker 2>/dev/null || true
            return 0
        fi
    fi
    
    # apt安装
    if command -v apt-get &> /dev/null; then
        if apt-get update -qq && apt-get install -y docker.io 2>/dev/null; then
            echo "[OK] Docker 安装成功(apt)"
            systemctl start docker 2>/dev/null || true
            return 0
        fi
    fi
    
    echo "[ERROR] Docker 安装失败"
    return 1
}

# 交互式配置
interactive_config() {
    if [ "$INTERACTIVE" = false ]; then
        return 0
    fi
    
    echo ""
    echo ">>> 交互式配置"
    echo "------------------------------------------"
    
    # 主人名称
    if [ -z "$OWNER" ]; then
        read -p "请输入主人名称: " OWNER
    fi
    
    # 主人邮箱
    if [ -z "$OWNER_EMAIL" ]; then
        read -p "请输入主人邮箱: " OWNER_EMAIL
    fi
    
    # 数据目录
    read -p "数据目录 [$DATA_DIR]: " input
    [ -n "$input" ] && DATA_DIR="$input"
    
    # 网络模式
    echo "网络模式: 1) host (性能优先) 2) bridge (隔离优先)"
    read -p "选择 [1]: " net_choice
    [ "$net_choice" = "2" ] && NETWORK_MODE="bridge"
    
    echo "------------------------------------------"
}

# 保存配置
save_config() {
    echo ""
    echo ">>> 保存配置文件..."
    
    cat > "$CONFIG_FILE" << EOF
# ============================================
# Agent Awake 配置文件
# ============================================
# 由 platform-init.sh 自动生成
# $(date +%Y-%m-%d)
# ============================================

# ============ 基础配置 ============
DATA_DIR="$DATA_DIR"
OWNER="$OWNER"
OWNER_EMAIL="$OWNER_EMAIL"
TIMEZONE="${TIMEZONE:-Asia/Shanghai}"

# ============ 引擎配置 ============
ENGINE="$ENGINE"
ENGINE_DIR="$SKILL_DIR/engines"

# ============ 网络配置 ============
NETWORK_MODE="$NETWORK_MODE"
DOCKER_NETWORK="agent-awake-net"

# ============ 端口配置 ============
GW_PORT_BASE="$GW_PORT_BASE"
CR_PORT_BASE="$CR_PORT_BASE"

# ============ 资源配额 ============
DEFAULT_CPU="$DEFAULT_CPU"
DEFAULT_MEMORY="$DEFAULT_MEMORY"

# ============ 镜像配置 ============
IMAGE_NAME="$IMAGE_NAME"
IMAGES_DIR="$DATA_DIR/images/openclaw-agent"

# ============ 功能开关 ============
AUTO_INSTALL_DOCKER="true"
AUTO_BUILD_IMAGE="true"
STARTUP_WAIT="15"
HEALTH_CHECK_RETRIES="10"
HEALTH_CHECK_INTERVAL="3"

# ============ Emoji配置 ============
EMOJI_LIST=(🔮 ⚡ 🌊 🔥 🌟 ❄️ 🍀 🎯 💎 🦊 🐉 🦄 🌈 🎪 🎭 🚀 🌌)

# ============ 引擎配置 ============
OPENCLAW_VERSION="${OPENCLAW_VERSION:-2026.5.3-1}"
CLAWROUTER_PACKAGE="@blockrun/clawrouter"
PRIMARY_MODEL="clawrouter/free"
EOF
    
    echo "[OK] 配置文件已保存: $CONFIG_FILE"
}

# 创建目录结构
create_dirs() {
    echo ""
    echo ">>> 创建目录结构..."
    
    mkdir -p "$DATA_DIR"
    mkdir -p "$IMAGES_DIR"
    mkdir -p "$DATA_DIR/scripts"
    
    # 创建 platform.json
    if [ ! -f "$DATA_DIR/platform.json" ]; then
        cat > "$DATA_DIR/platform.json" << 'EOF'
{
  "version": "2.0",
  "created": "",
  "owner": "",
  "owner_email": "",
  "agents": [],
  "config": {}
}
EOF
    fi
    
    # 更新 platform.json
    update_platform_json() {
        local key="$1"
        local value="$2"
        
        if command -v jq &> /dev/null; then
            jq --arg v "$value" ".$key = \$v" "$DATA_DIR/platform.json" > /tmp/platform.json.tmp && mv /tmp/platform.json.tmp "$DATA_DIR/platform.json"
        fi
    }
    
    update_platform_json "created" "$(date +%Y-%m-%d)"
    update_platform_json "owner" "$OWNER"
    update_platform_json "owner_email" "$OWNER_EMAIL"
    
    echo "[OK] 目录创建完成: $DATA_DIR"
}

# 创建Docker网络
create_docker_network() {
    if [ "$NETWORK_MODE" != "bridge" ]; then
        return 0
    fi
    
    echo ""
    echo ">>> 创建Docker网络..."
    
    if docker network inspect "$DOCKER_NETWORK" &> /dev/null; then
        echo "[OK] 网络已存在: $DOCKER_NETWORK"
    else
        docker network create "$DOCKER_NETWORK" 2>/dev/null || true
        echo "[OK] 网络已创建: $DOCKER_NETWORK"
    fi
}

# 构建镜像（轻量版：只装apt依赖，node_modules通过volume挂载）
build_image() {
    echo ""
    echo ">>> 构建Agent镜像（轻量版）..."
    
    # 检查引擎是否存在
    local engine_script="$SKILL_DIR/engines/$ENGINE/engine.sh"
    if [ ! -f "$engine_script" ]; then
        echo "[ERROR] 引擎不存在: $ENGINE"
        echo "可用引擎: openclaw"
        return 1
    fi
    
    # 前置检查：宿主机必须已安装 openclaw 和 clawrouter
    if [ ! -d "/usr/lib/node_modules/openclaw" ]; then
        echo "[ERROR] 宿主机未安装 openclaw，请先: npm install -g openclaw@2026.5.3-1"
        return 1
    fi
    if [ ! -d "/usr/lib/node_modules/@blockrun/clawrouter" ]; then
        echo "[ERROR] 宿主机未安装 clawrouter，请先: npm install -g @blockrun/clawrouter"
        return 1
    fi
    
    # 前置检查：entrypoint.sh 必须存在
    local skill_entrypoint="$SKILL_DIR/images/openclaw-agent/entrypoint.sh"
    if [ ! -f "$skill_entrypoint" ]; then
        echo "[ERROR] entrypoint.sh 不存在: $skill_entrypoint"
        return 1
    fi
    
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
    
    # 复制 entrypoint.sh
    cp "$skill_entrypoint" "$IMAGES_DIR/entrypoint.sh"
    chmod +x "$IMAGES_DIR/entrypoint.sh"
    echo "[INFO] entrypoint.sh 已复制"
    
    # 生成 Dockerfile（轻量版：node_modules 通过 volume 挂载，不 COPY 进镜像）
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
    
    # 构建镜像
    cd "$DATA_DIR"
    if docker build --network host -t "$IMAGE_NAME" ./images/openclaw-agent 2>&1 | tail -10; then
        echo "[OK] 镜像构建成功: $IMAGE_NAME"
    else
        echo "[ERROR] 镜像构建失败"
        return 1
    fi
}

# 验证环境
verify_environment() {
    echo ""
    echo ">>> 验证环境..."
    
    # 验证Docker
    if ! docker ps &> /dev/null; then
        echo "[ERROR] Docker 未运行，请执行: systemctl start docker"
        return 1
    fi
    echo "  Docker: ✅ 正常"
    
    # 验证镜像
    if docker image inspect "$IMAGE_NAME" &> /dev/null; then
        echo "  镜像: ✅ $IMAGE_NAME"
    else
        echo "  镜像: ⚠️  未构建（将在创建Agent时构建）"
    fi
    
    # 验证目录
    if [ -d "$DATA_DIR" ]; then
        echo "  数据目录: ✅ $DATA_DIR"
    else
        echo "  数据目录: ⚠️  未创建"
    fi
    
    return 0
}

# 主流程
main() {
    # 环境检测
    if [ "$SKIP_ENV_CHECK" = false ]; then
        detect_environment
        install_jq
    fi
    
    # 安装Docker
    if [ "$SKIP_DOCKER_INSTALL" = false ] && [ "$DOCKER_INSTALLED" = false ]; then
        install_docker
    fi
    
    # 交互式配置
    if [ -z "$OWNER" ] || [ -z "$OWNER_EMAIL" ]; then
        interactive_config
    fi
    
    # 验证必填参数
    if [ -z "$OWNER" ]; then
        echo "[ERROR] 必须指定 --owner 或在交互式配置中输入"
        exit 1
    fi
    if [ -z "$OWNER_EMAIL" ]; then
        echo "[ERROR] 必须指定 --owner-email 或在交互式配置中输入"
        exit 1
    fi
    
    # 保存配置
    save_config
    
    # 创建目录
    create_dirs
    
    # 创建Docker网络
    create_docker_network
    
    # 构建镜像（可选，agent-create时会构建）
    # 构建镜像
    build_image
    
    # 验证
    verify_environment
    
    echo ""
    echo "=========================================="
    echo "  初始化完成!"
    echo "=========================================="
    echo ""
    echo "下一步操作:"
    echo "  1. 创建Agent: bash scripts/agent-create.sh \\"
    echo "       --name \"你的分身\" \\"
    echo "       --agent-id \"my-agent\""
    echo ""
    echo "配置文件: $CONFIG_FILE"
    echo "数据目录: $DATA_DIR"
    echo "=========================================="
}

main "$@"
