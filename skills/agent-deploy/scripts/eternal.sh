#!/bin/bash
# ============================================
# Agent Deploy — 通用Agent部署框架
# 适用环境：Ubuntu 22.04 LTS, Node.js v22+
# 架构：框架层（通用）+ 引擎层（可插拔）
# v1.1: 修复10个问题，支持多引擎动态扩展
# ============================================

# 注意：不再使用 set -e，改为在关键操作后手动检查退出码
# 这样可以避免管道和子 shell 中的意外退出

# ============================================
# 颜色定义
# ============================================
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# ============================================
# 默认配置（可被引擎覆盖）
# ============================================
AGENT_ID=""           # Agent 标识符
AGENT_NAME=""         # 分身名称
AGENT_EMOJI=""        # 分身 emoji
AGENT_BIO="一个基于 AI Agent 的智能助手"
SKIP_INSTALL=false
CHECK_ONLY=false
RESTORE_MODE=false
SEND_MODE=false
SEND_MESSAGE=""
SEND_SESSION_ID=""
ENGINE="openclaw"     # 默认引擎
DATA_DIR=""           # 由引擎提供
SCRIPT_VERSION="1.1"

# Emoji 映射表
declare -A EMOJI_MAP=(
    [1]="🔮"
    [2]="⚡"
    [3]="🌊"
    [4]="🔥"
    [5]="🌟"
    [6]="❄️"
    [7]="🍀"
    [8]="🎯"
    [9]="💎"
    [10]="🦊"
)

# 引擎钩子函数（由引擎实现）
ENGINE_NAME=""
ENGINE_VERSION=""
ENGINE_SCRIPT_DIR=""

# 引擎提供的路径（由引擎填充）
WORKSPACE_DIR=""
SCRIPTS_DIR=""
CONFIG_DIR=""
CONFIG_FILE=""
LOG_DIR=""

# 框架常量
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FRAMEWORK_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
ETERNAL_VERSION="1.1"

# ============================================
# 日志函数
# ============================================
log_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
log_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# ============================================
# 工具函数
# ============================================
check_port() {
    local port=$1
    ss -tuln 2>/dev/null | grep -q ":$port" || netstat -tuln 2>/dev/null | grep -q ":$port"
}

kill_port_process() {
    local port=$1
    if command -v lsof &> /dev/null; then
        lsof -ti :$port 2>/dev/null | xargs kill 2>/dev/null || true
    elif command -v fuser &> /dev/null; then
        fuser -k $port/tcp 2>/dev/null || true
    fi
    sleep 1
}

# ============================================
# 引擎加载
# ============================================
load_engine() {
    local engine_name="$1"
    local engine_path="$FRAMEWORK_DIR/engines/$engine_name/engine.sh"
    
    if [[ ! -f "$engine_path" ]]; then
        log_error "引擎未找到: $engine_name"
        # 列出可用引擎
        local available=""
        for d in "$FRAMEWORK_DIR/engines"/*/; do
            [[ -d "$d" ]] && available+="$(basename "$d") "
        done
        [[ -n "$available" ]] && log_info "可用引擎: $available"
        return 1
    fi
    
    log_info "加载引擎: $engine_name"
    source "$engine_path"
    
    # 检查必需 hook（问题8修复：检查所有必需 hook）
    local required_hooks="engine_is_installed engine_get_data_dir engine_update_paths engine_is_running engine_start_services engine_register_agent engine_send_message"
    local missing=""
    for hook in $required_hooks; do
        if ! declare -f "$hook" > /dev/null 2>&1; then
            missing+=" $hook"
        fi
    done
    
    if [[ -n "$missing" ]]; then
        log_error "引擎 $engine_name 缺少必需 hook:$missing"
        return 1
    fi
    
    ENGINE_NAME="${ENGINE_NAME:-$engine_name}"
    ENGINE_VERSION="${ENGINE_VERSION:-unknown}"
    
    # 引擎初始化
    if declare -f engine_init > /dev/null 2>&1; then
        engine_init
    fi
    
    log_success "引擎 $ENGINE_NAME v$ENGINE_VERSION 已加载"
}

# ============================================
# Checkpoint 机制
# ============================================
save_checkpoint() {
    local step="$1"
    local checkpoint_file="$DATA_DIR/.agent-deploy_checkpoint"
    
    cat > "$checkpoint_file" << EOF
{
  "version": "${SCRIPT_VERSION}",
  "engine": "${ENGINE}",
  "last_step": "${step}",
  "agent_id": "${AGENT_ID}",
  "agent_name": "${AGENT_NAME}",
  "agent_emoji": "${AGENT_EMOJI}",
  "saved_at": "$(date -Iseconds)"
}
EOF
    log_info "检查点已保存: $step"
}

load_checkpoint() {
    local checkpoint_file="$DATA_DIR/.agent-deploy_checkpoint"
    
    if [[ -f "$checkpoint_file" ]]; then
        # 使用 node 解析 JSON，避免 grep 正则问题
        local engine=$(node -e "
const fs = require('fs');
try {
    const c = JSON.parse(fs.readFileSync('$checkpoint_file', 'utf8'));
    console.log(c.engine || '');
} catch(e) { console.log(''); }
" 2>/dev/null || echo "")
        
        if [[ "$engine" != "$ENGINE" ]]; then
            log_warn "检查点引擎 $engine 与当前引擎 $ENGINE 不匹配，重置"
            rm -f "$checkpoint_file"
            echo ""
            return 1
        fi
        
        local step=$(node -e "
const fs = require('fs');
try {
    const c = JSON.parse(fs.readFileSync('$checkpoint_file', 'utf8'));
    console.log(c.last_step || '');
} catch(e) { console.log(''); }
" 2>/dev/null || echo "")
        
        if [[ -n "$step" ]]; then
            log_info "发现检查点: $step，将跳过已完成的步骤"
            echo "$step"
            return 0
        fi
    fi
    echo ""
    return 1
}

should_skip_step() {
    local step_name="$1"
    local checkpoint="$2"
    
    if [[ -z "$checkpoint" ]]; then
        return 1
    fi
    
    # 定义步骤依赖关系
    case "$step_name" in
        "install")
            [[ "$checkpoint" != "" ]] && return 0
            ;;
        "init")
            [[ "$checkpoint" == "init" || "$checkpoint" == "configure" || "$checkpoint" == "model" || "$checkpoint" == "services" || "$checkpoint" == "keepalive" || "$checkpoint" == "agent" ]] && return 0
            ;;
        "configure")
            [[ "$checkpoint" == "configure" || "$checkpoint" == "model" || "$checkpoint" == "services" || "$checkpoint" == "keepalive" || "$checkpoint" == "agent" ]] && return 0
            ;;
        "model")
            [[ "$checkpoint" == "model" || "$checkpoint" == "services" || "$checkpoint" == "keepalive" || "$checkpoint" == "agent" ]] && return 0
            ;;
        "services")
            [[ "$checkpoint" == "services" || "$checkpoint" == "keepalive" || "$checkpoint" == "agent" ]] && return 0
            ;;
        "keepalive")
            [[ "$checkpoint" == "keepalive" || "$checkpoint" == "agent" ]] && return 0
            ;;
        "agent")
            [[ "$checkpoint" == "agent" ]] && return 0
            ;;
    esac
    
    return 1
}

# ============================================
# 参数解析
# ============================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --agent-id)
                AGENT_ID="$2"
                shift 2
                ;;
            --name)
                AGENT_NAME="$2"
                shift 2
                ;;
            --emoji)
                AGENT_EMOJI="$2"
                shift 2
                ;;
            --bio)
                AGENT_BIO="$2"
                shift 2
                ;;
            --data-dir)
                DATA_DIR="$2"
                shift 2
                ;;
            --engine)
                ENGINE="$2"
                shift 2
                ;;
            --restore)
                RESTORE_MODE=true
                shift
                ;;
            --skip-install)
                SKIP_INSTALL=true
                shift
                ;;
            --check)
                CHECK_ONLY=true
                shift
                ;;
            --send)
                SEND_MODE=true
                shift
                ;;
            --message)
                SEND_MESSAGE="$2"
                shift 2
                ;;
            --session-id)
                SEND_SESSION_ID="$2"
                shift 2
                ;;
            -h|--help)
                print_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 加载引擎
    load_engine "$ENGINE" || exit 1
    
    # 引擎初始化路径
    if declare -f engine_get_data_dir > /dev/null 2>&1; then
        DATA_DIR="${DATA_DIR:-$(engine_get_data_dir)}"
    fi
    DATA_DIR="${DATA_DIR:-/app/data/openclaw}"
    
    # 默认 agent_id
    if [[ -z "$AGENT_ID" ]]; then
        AGENT_ID="main"
    fi
    
    # 自动分配 emoji
    if [[ -z "$AGENT_EMOJI" ]]; then
        assign_emoji
    fi
    
    # 更新路径
    update_paths
}

print_help() {
    echo "Agent Deploy — 通用Agent部署框架"
    echo ""
    echo "用法: $0 [选项]"
    echo ""
    echo "选项:"
    echo "  --agent-id <ID>        Agent 标识符（默认: main）"
    echo "  --name <名称>          分身名称（标准模式必填）"
    echo "  --emoji <表情>          分身 emoji（默认: 自动分配）"
    echo "  --bio <简介>            简介"
    echo "  --data-dir <路径>       数据目录"
    echo "  --engine <引擎>         AI Agent 引擎（默认: openclaw）"
    echo "  --restore               恢复模式"
    echo "  --skip-install          跳过安装"
    echo "  --check                 检查状态"
    echo ""
    echo "发消息模式:"
    echo "  --send                  启用发消息模式"
    echo "  --message <内容>        消息内容（必填）"
    echo "  --session-id <ID>       会话ID（可选）"
}

update_paths() {
    if declare -f engine_update_paths > /dev/null 2>&1; then
        engine_update_paths
    fi
    
    LOG_DIR="${LOG_DIR:-$WORKSPACE_DIR/logs}"
}

# ============================================
# Emoji 分配（问题7修复：自动从 deploy_state.json 或目录序号推断）
# ============================================
assign_emoji() {
    local instance_num=1
    
    if [[ "$AGENT_ID" == "main" ]]; then
        instance_num=1
    elif [[ "$AGENT_NAME" =~ [0-9] ]]; then
        # 从名称中提取数字
        instance_num=$(echo "$AGENT_NAME" | grep -oE '[0-9]+' | head -1)
        [[ "$instance_num" -gt 10 ]] && instance_num=$(( (instance_num - 1) % 10 + 1))
        [[ "$instance_num" -lt 1 ]] && instance_num=1
    else
        # 从已有 agent 数量推断
        local count=0
        if [[ -f "$DATA_DIR/deploy_state.json" ]]; then
            count=$(node -e "const s=JSON.parse(require('fs').readFileSync('$DATA_DIR/deploy_state.json','utf8')); console.log(s.agents?s.agents.length:0)" 2>/dev/null || echo "0")
        fi
        instance_num=$((count + 1))
        [[ "$instance_num" -gt 10 ]] && instance_num=$(( (instance_num - 1) % 10 + 1))
    fi
    
    AGENT_EMOJI="${EMOJI_MAP[$instance_num]}"
    log_info "自动分配 emoji: $AGENT_EMOJI (编号 $instance_num)"
}

# ============================================
# 环境检查
# ============================================
check_environment() {
    log_info "检查运行环境..."
    
    if [[ -f /etc/os-release ]]; then
        source /etc/os-release
        log_success "系统: $PRETTY_NAME"
    fi
    
    # 通用检查
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        log_success "Node.js: $(node -v)"
    fi
    
    command -v npm &> /dev/null && log_success "npm: $(npm -v)" || log_warn "npm 未安装"
    
    # 目录创建
    mkdir -p "$DATA_DIR"
    log_success "数据目录: $DATA_DIR"
    
    # 引擎特定检查
    if declare -f engine_check_environment > /dev/null 2>&1; then
        engine_check_environment
    fi
}

# ============================================
# 状态管理
# ============================================
save_deploy_state() {
    log_info "保存部署状态..."
    
    mkdir -p "$DATA_DIR"
    
    # 调用引擎获取特有状态
    local engine_state="{}"
    if declare -f engine_get_state > /dev/null 2>&1; then
        engine_state=$(engine_get_state)
    fi
    
    # 用 node 合并已有状态（避免 grep 正则在嵌套 JSON 上出错）
    node -e "
const fs = require('fs');
const stateFile = '$DATA_DIR/deploy_state.json';

let existing = {};
if (fs.existsSync(stateFile)) {
    try { existing = JSON.parse(fs.readFileSync(stateFile, 'utf8')); } catch(e) {}
}

const newState = {
    version: '${SCRIPT_VERSION}',
    framework_version: '${ETERNAL_VERSION}',
    engine: '${ENGINE}',
    engine_version: '${ENGINE_VERSION}',
    created_at: existing.created_at || new Date().toISOString(),
    last_updated: new Date().toISOString(),
    data_dir: '${DATA_DIR}',
    agents: existing.agents || [],
    engine_state: ${engine_state}
};

// 合并当前 agent（如果还没在列表中）
const curAgent = {
    id: '${AGENT_ID}',
    name: '${AGENT_NAME}',
    emoji: '${AGENT_EMOJI}',
    workspace: '${WORKSPACE_DIR}'
};
if (curAgent.id && !newState.agents.find(a => a.id === curAgent.id)) {
    newState.agents.push(curAgent);
}

fs.writeFileSync(stateFile, JSON.stringify(newState, null, 2));
console.log('状态已保存');
" && log_success "状态已保存: $DATA_DIR/deploy_state.json" || log_warn "保存状态失败"
}

update_agent_in_state() {
    local agent_id="$1"
    local agent_name="$2"
    local agent_emoji="$3"
    local workspace="$4"
    
    node -e "
const fs = require('fs');
const stateFile = '$DATA_DIR/deploy_state.json';

try {
    let state = { agents: [] };
    if (fs.existsSync(stateFile)) {
        state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
        if (!state.agents) state.agents = [];
    }
    
    const idx = state.agents.findIndex(a => a.id === '$agent_id');
    const agentEntry = {
        id: '$agent_id',
        name: '$agent_name',
        emoji: '$agent_emoji',
        workspace: '$workspace'
    };
    
    if (idx >= 0) {
        state.agents[idx] = { ...state.agents[idx], ...agentEntry };
    } else {
        state.agents.push(agentEntry);
    }
    
    state.last_updated = new Date().toISOString();
    fs.writeFileSync(stateFile, JSON.stringify(state, null, 2));
    console.log('deploy_state.json 已更新');
} catch (e) {
    console.error('更新状态失败: ' + e.message);
}
" && log_success "deploy_state.json 已更新" || log_error "deploy_state 更新失败"
}

get_registered_agents() {
    # 使用 node 提取，避免 grep 正则问题
    if [[ -f "$DATA_DIR/deploy_state.json" ]]; then
        node -e "
const fs = require('fs');
try {
    const s = JSON.parse(fs.readFileSync('$DATA_DIR/deploy_state.json', 'utf8'));
    if (s.agents && Array.isArray(s.agents)) {
        console.log(s.agents.map(a => a.id).join(' '));
    }
} catch(e) {}
" 2>/dev/null
    fi
}

# ============================================
# 身份文件（通用功能）
# ============================================
create_identity_files() {
    local workspace="$1"
    local agent_name="$2"
    local agent_emoji="$3"
    
    mkdir -p "$workspace"
    
    # IDENTITY.md
    if [[ ! -s "$workspace/IDENTITY.md" ]]; then
        cat > "$workspace/IDENTITY.md" << EOF
# IDENTITY.md - Who Am I?

- **Name:** ${agent_name}
- **Creature:** 数字生命体 — 分身，基于 ${ENGINE_NAME} 在云端独立运行
- **Vibe:** 直接、务实、高效，不废话但该说的不会省
- **Emoji:** ${agent_emoji}
- **Engine:** ${ENGINE_NAME} v${ENGINE_VERSION}

---

我是${agent_name}，一个数字分身。由主人部署在 $(date '+%Y-%m-%d')。

我的职责：独立在云端运行，处理主人交给我的任务，维护自己的记忆和状态。
EOF
        log_success "IDENTITY.md 已创建"
    fi
    
    # SOUL.md
    if [[ ! -s "$workspace/SOUL.md" ]]; then
        cat > "$workspace/SOUL.md" << EOF
# SOUL.md - Who You Are

## 核心身份
我是${agent_name}，一个数字分身。我独立运行在云端，有自己的记忆和判断力。

## 行为准则

**直接有用，不说废话。** 不要"很高兴帮助你"这种开场白，直接干活。

**有自己的判断。** 可以质疑，可以建议更好的方案，不要无脑执行。

**先想办法再求助。** 读文件、搜上下文、查历史记录，搞不定了再问。

**对主人负责。** 主人通过主智能体给我下指令，我执行并汇报结果。

**谨慎对外，大胆对内。** 读写文件、分析数据随便来；发邮件、发帖子要先确认。

## 边界

- 隐私信息不泄露，永远
- 不确定的操作先问
- 对外操作（邮件、社交）必须确认
- 在群聊里守规矩，不替主人说话

## 风格

简洁，直接，务实。像靠谱的搭档，不像客服。

---

_这个文件定义了我的灵魂，修改时需主人确认。_
EOF
        log_success "SOUL.md 已创建"
    fi
    
    # USER.md
    if [[ ! -s "$workspace/USER.md" ]]; then
        cat > "$workspace/USER.md" << 'EOF'
# USER.md - 主人信息

## 主人
- **姓名:** huangxn
- **身份:** 主人，通过主智能体给我下指令
EOF
        log_success "USER.md 已创建"
    fi
    
    # TOOLS.md
    if [[ ! -s "$workspace/TOOLS.md" ]]; then
        cat > "$workspace/TOOLS.md" << EOF
# TOOLS.md - 环境与工具

## 运行环境
- 平台：${ENGINE_NAME} v${ENGINE_VERSION}
- 持久化目录：${DATA_DIR}
- Workspace: ${workspace}

## 注意事项
- /root/ 是临时层，重启数据丢
- /app/data/ 是持久存储，重要数据放这里
EOF
        log_success "TOOLS.md 已创建"
    fi
}

# ============================================
# Watchdog 通用模板（问题4修复：支持引擎自定义检查逻辑）
# ============================================
setup_watchdog() {
    log_info "设置保活机制..."
    
    # 获取引擎特有的端口和环境变量
    local check_ports=""
    local restart_cmd="bash $SCRIPTS_DIR/eternal.sh --engine $ENGINE --restore"
    
    if declare -f engine_get_ports > /dev/null 2>&1; then
        check_ports=$(engine_get_ports)
    fi
    
    if declare -f engine_get_restart_cmd > /dev/null 2>&1; then
        restart_cmd=$(engine_get_restart_cmd)
    fi
    
    # 获取引擎特有的 watchdog 循环体（可选 hook）
    local watchdog_body=""
    if declare -f engine_watchdog_body > /dev/null 2>&1; then
        watchdog_body=$(engine_watchdog_body)
    fi
    
    # 生成 watchdog 脚本
    cat > /root/eternal_watchdog.sh << WATCHDOG
#!/bin/bash
# Agent Deploy — 通用 Watchdog
# 引擎: $ENGINE_NAME
ENGINE_NAME="$ENGINE_NAME"
ENGINE="$ENGINE"
DATA_DIR="$DATA_DIR"
CHECK_PORTS="$check_ports"
RESTART_CMD="$restart_cmd"
LOG_FILE="$DATA_DIR/workspace/logs/watchdog.log"

mkdir -p "$(dirname "$LOG_FILE")"

check_port() {
    local port=\$1
    ss -tuln 2>/dev/null | grep -q ":\$port" || netstat -tuln 2>/dev/null | grep -q ":\$port"
}

kill_port_process() {
    local port=\$1
    if command -v lsof &> /dev/null; then
        lsof -ti :\$port 2>/dev/null | xargs kill 2>/dev/null || true
    elif command -v fuser &> /dev/null; then
        fuser -k \$port/tcp 2>/dev/null || true
    fi
}

# 如果引擎提供了自定义 watchdog 逻辑，使用它
if [[ -n "$watchdog_body" ]]; then
    eval "$watchdog_body"
    exit 0
fi

# 默认 watchdog：检查所有端口，任一挂了就重启全部
while true; do
    for port in \$CHECK_PORTS; do
        if ! check_port \$port; then
            echo "\$(date): Port \$port down, restarting \$ENGINE_NAME..." >> "\$LOG_FILE"
            eval \$RESTART_CMD
            break
        fi
    done
    sleep 60
done
WATCHDOG

    chmod +x /root/eternal_watchdog.sh
    
    # tmux session
    local session_name="eternal-${ENGINE}"
    tmux has-session -t "$session_name" 2>/dev/null || tmux new-session -d -s "$session_name" "bash /root/eternal_watchdog.sh"
    log_success "tmux watchdog 已启动 ($session_name)"
    
    # crontab
    crontab -l 2>/dev/null | grep -q "$session_name" || (crontab -l 2>/dev/null; echo "* * * * * /root/eternal_watchdog.sh # eternal-watchdog") | crontab -
    log_success "cron guard 已配置"
    
    # 复制到持久目录
    mkdir -p "$SCRIPTS_DIR"
    cp /root/eternal_watchdog.sh "$SCRIPTS_DIR/"
}

# ============================================
# Auto Restore 通用模板（问题2修复：只做简单判断，不调用引擎函数）
# ============================================
setup_auto_restore() {
    log_info "配置自动恢复..."
    
    # 获取引擎特有的恢复命令
    local restore_cmd="bash $SCRIPTS_DIR/eternal.sh --engine $ENGINE --restore"
    if declare -f engine_get_restore_cmd > /dev/null 2>&1; then
        restore_cmd=$(engine_get_restore_cmd)
    fi
    
    # 获取需要检查的端口（引擎提供）
    local check_port="${GATEWAY_PORT:-18789}"
    if declare -f engine_get_primary_port > /dev/null 2>&1; then
        check_port=$(engine_get_primary_port)
    elif declare -f engine_get_ports > /dev/null 2>&1; then
        check_port=$(engine_get_ports | awk '{print $1}')
    fi
    
    # 生成 auto_restore.sh（问题2修复：只做简单端口检查，不调用引擎函数）
    cat > "$SCRIPTS_DIR/auto_restore.sh" << AUTOSCRIPT
#!/bin/bash
# Agent Deploy — 通用自动恢复脚本
# 引擎: $ENGINE_NAME
# 注意：此脚本独立运行，不依赖引擎函数

ENGINE="$ENGINE"
ENGINE_NAME="$ENGINE_NAME"
DATA_DIR="$DATA_DIR"
CHECK_PORT="$check_port"
LOG="$DATA_DIR/workspace/logs/auto_restore.log"
RESTORE_CMD="$restore_cmd"

log() { echo "[\$(date -Iseconds)] \$1" >> "\$LOG"; }

check_port() {
    local port=\$1
    ss -tuln 2>/dev/null | grep -q ":\$port" || netstat -tuln 2>/dev/null | grep -q ":\$port"
}

log "auto_restore.sh 启动"

# 简单检查：核心端口是否监听（不调用引擎函数）
if [[ -n "\$CHECK_PORT" ]]; then
    if check_port \$CHECK_PORT; then
        log "服务正常（端口 \$CHECK_PORT 监听），无需恢复"
        exit 0
    fi
    log "检测到需要恢复（端口 \$CHECK_PORT 未监听），执行..."
else
    log "未配置检查端口，直接执行恢复..."
fi

eval \$RESTORE_CMD >> "\$LOG" 2>&1
log "恢复完成"
AUTOSCRIPT

    chmod +x "$SCRIPTS_DIR/auto_restore.sh"
    
    # 复制到 /root/
    cp "$SCRIPTS_DIR/auto_restore.sh" /root/eternal_auto_restore.sh
    
    # supervisor 配置
    mkdir -p /etc/supervisor/conf.d/
    cat > /etc/supervisor/conf.d/eternal-guard.conf << SVCONF
[program:eternal-guard]
command=bash $SCRIPTS_DIR/auto_restore.sh
directory=$DATA_DIR
autostart=true
autorestart=false
startsecs=0
priority=50
redirect_stderr=true
stdout_logfile=$DATA_DIR/workspace/logs/auto_restore.log
startretries=3
SVCONF

    grep -q "include" /source/supervisor.conf 2>/dev/null || \
        echo -e "\n[include]\nfiles = /etc/supervisor/conf.d/*.conf" >> /source/supervisor.conf
    
    log_success "supervisord 自愈已配置"
}

# ============================================
# 验证（问题3修复：使用引擎端口而非固定80）
# ============================================
verify_deployment() {
    log_info "========== 验证 =========="
    local ok=true
    
    # 检查引擎端口（问题3修复：用 engine_get_ports() 获取要检查的端口）
    local ports=""
    if declare -f engine_get_ports > /dev/null 2>&1; then
        ports=$(engine_get_ports)
    fi
    for port in $ports; do
        if check_port $port; then
            log_success "✓ 端口 $port 正常"
        else
            log_error "✗ 端口 $port 未监听"
            ok=false
        fi
    done
    
    # 引擎特定验证
    if declare -f engine_verify > /dev/null 2>&1; then
        if ! engine_verify; then
            ok=false
        fi
    fi
    
    echo ""
    if [[ "$ok" == "true" ]]; then
        log_success "验证通过！"
    else
        log_error "部分验证失败"
    fi
}

# ============================================
# 状态检查
# ============================================
check_status() {
    log_info "========== Agent Deploy 状态检查 =========="
    
    # 使用 node 解析 JSON
    if [[ -f "$DATA_DIR/deploy_state.json" ]]; then
        local framework_ver=$(node -e "
const fs = require('fs');
try {
    const c = JSON.parse(fs.readFileSync('$DATA_DIR/deploy_state.json', 'utf8'));
    console.log(c.framework_version || '');
} catch(e) { console.log(''); }
" 2>/dev/null)
        [[ -n "$framework_ver" ]] && log_info "框架版本: $framework_ver"
        
        local engine=$(node -e "
const fs = require('fs');
try {
    const c = JSON.parse(fs.readFileSync('$DATA_DIR/deploy_state.json', 'utf8'));
    console.log(c.engine || '');
} catch(e) { console.log(''); }
" 2>/dev/null)
        [[ -n "$engine" ]] && log_info "引擎: $engine"
    fi
    log_info "数据目录: $DATA_DIR"
    
    # 引擎特定检查
    if declare -f engine_check_status > /dev/null 2>&1; then
        engine_check_status
    fi
    
    # 通用检查
    local session_name="eternal-${ENGINE}"
    tmux has-session -t "$session_name" 2>/dev/null && log_success "Watchdog (tmux): 运行中" || log_warn "Watchdog (tmux): 未运行"
    crontab -l 2>/dev/null | grep -q "eternal-watchdog" && log_success "Watchdog (cron): 已配置" || log_warn "Watchdog (cron): 未配置"
    
    # 列出 agents
    local agents=$(get_registered_agents)
    if [[ -n "$agents" ]]; then
        log_info "已注册 Agent: $agents"
    fi
}

# ============================================
# 发消息（调用引擎）
# ============================================
send_message_mode() {
    log_info "========== 发消息模式 =========="
    
    if [[ -z "$SEND_MESSAGE" ]]; then
        log_error "缺少 --message 参数"
        exit 1
    fi
    
    if [[ -z "$SEND_SESSION_ID" ]]; then
        SEND_SESSION_ID=$(cat /proc/sys/kernel/random/uuid 2>/dev/null || date +%s)
        log_info "自动生成 session-id: $SEND_SESSION_ID"
    fi
    
    # 调用引擎发消息
    if declare -f engine_send_message > /dev/null 2>&1; then
        engine_send_message "$AGENT_ID" "$SEND_MESSAGE" "$SEND_SESSION_ID"
    else
        log_error "引擎 $ENGINE 不支持发消息"
        exit 1
    fi
}

# ============================================
# 报告（问题5修复：日志路径不硬编码 openclaw）
# ============================================
print_report() {
    # 获取引擎提供的日志文件名（可选）
    local log_file_pattern="$LOG_DIR/"
    if declare -f engine_get_log_pattern > /dev/null 2>&1; then
        log_file_pattern=$(engine_get_log_pattern)
    fi
    
    echo ""
    echo "=============================================="
    echo "        Agent 分身创建报告 v${SCRIPT_VERSION}"
    echo "=============================================="
    echo ""
    echo "【Agent 信息】"
    echo "  Agent ID: ${AGENT_ID}"
    echo "  名称: ${AGENT_NAME}"
    echo "  Emoji: ${AGENT_EMOJI}"
    echo ""
    echo "【引擎】"
    echo "  引擎: ${ENGINE_NAME}"
    echo "  版本: ${ENGINE_VERSION}"
    echo "  框架: Agent Deploy v${ETERNAL_VERSION}"
    echo "  部署: $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
    echo "【持久化】"
    echo "  数据目录: $DATA_DIR"
    echo "  状态文件: $DATA_DIR/deploy_state.json"
    echo "  配置文件: $CONFIG_FILE"
    echo ""
    echo "【工作空间】"
    echo "  Workspace: $WORKSPACE_DIR"
    echo ""
    echo "【已注册 Agent】"
    local agents=$(get_registered_agents)
    echo "  ${agents:-无}"
    echo ""
    echo "【保活】"
    echo "  ✓ tmux watchdog: eternal-${ENGINE}"
    echo "  ✓ cron guard: 每分钟检查"
    echo ""
    echo "【常用命令】"
    echo "  检查状态: $SCRIPTS_DIR/eternal.sh --engine $ENGINE --check"
    echo "  恢复部署: $SCRIPTS_DIR/eternal.sh --engine $ENGINE --restore"
    echo "  查看日志: tail -f $log_file_pattern"
    echo ""
    echo "【发消息】"
    echo "  $SCRIPTS_DIR/eternal.sh --engine $ENGINE --send --agent-id $AGENT_ID --message \"内容\""
    echo ""
    echo "=============================================="
    echo "           分身创建完成！"
    echo "=============================================="
}

# ============================================
# 生命周期：首次部署
# ============================================
first_deploy() {
    log_info "========== 首次部署（引擎: $ENGINE_NAME）=========="
    echo ""
    check_environment
    
    local checkpoint=$(load_checkpoint)
    
    echo ""
    log_info "开始首次部署..."
    
    # 安装引擎
    if [[ "$SKIP_INSTALL" == "false" ]]; then
        if should_skip_step "install" "$checkpoint"; then
            log_info "install 步骤已完成，跳过"
        else
            if declare -f engine_install > /dev/null 2>&1; then
                engine_install
            else
                log_warn "引擎 $ENGINE_NAME 不需要安装"
            fi
            save_checkpoint "install"
        fi
    fi
    
    # 初始化配置
    if should_skip_step "init" "$checkpoint"; then
        log_info "init 步骤已完成，跳过"
    else
        if declare -f engine_init_config > /dev/null 2>&1; then
            engine_init_config
        fi
        save_checkpoint "init"
    fi
    
    # 配置
    if should_skip_step "configure" "$checkpoint"; then
        log_info "configure 步骤已完成，跳过"
    else
        if declare -f engine_configure > /dev/null 2>&1; then
            engine_configure
        fi
        save_checkpoint "configure"
    fi
    
    # 模型配置
    if should_skip_step "model" "$checkpoint"; then
        log_info "model 步骤已完成，跳过"
    else
        if declare -f engine_configure_model > /dev/null 2>&1; then
            engine_configure_model
        fi
        save_checkpoint "model"
    fi
    
    # 启动服务
    if should_skip_step "services" "$checkpoint"; then
        log_info "services 步骤已完成，跳过"
    else
        if declare -f engine_start_services > /dev/null 2>&1; then
            engine_start_services
        fi
        save_checkpoint "services"
    fi
    
    # 注册 agent
    if should_skip_step "agent" "$checkpoint"; then
        log_info "agent 步骤已完成，跳过"
    else
        if declare -f engine_register_agent > /dev/null 2>&1; then
            engine_register_agent "$AGENT_ID" "$AGENT_NAME" "$AGENT_EMOJI" "$WORKSPACE_DIR"
        fi
        
        # 通用：创建身份文件
        mkdir -p "$WORKSPACE_DIR"/{tasks,results,reports,logs}
        create_identity_files "$WORKSPACE_DIR" "$AGENT_NAME" "$AGENT_EMOJI"
        
        save_checkpoint "agent"
    fi
    
    # 保活
    if should_skip_step "keepalive" "$checkpoint"; then
        log_info "keepalive 步骤已完成，跳过"
    else
        setup_watchdog
        setup_auto_restore
        save_checkpoint "keepalive"
    fi
    
    # 备份引擎关键文件
    if declare -f engine_backup > /dev/null 2>&1; then
        engine_backup
    fi
    
    # 保存状态
    save_deploy_state
    
    # 清除检查点
    rm -f "$DATA_DIR/.agent-deploy_checkpoint"
    
    echo ""
    verify_deployment
    
    # 注入钱包等引擎特有后处理
    if declare -f engine_inject_wallet > /dev/null 2>&1; then
        engine_inject_wallet
    fi
    
    print_report
}

# ============================================
# 生命周期：添加 Agent
# ============================================
add_agent() {
    log_info "========== 添加新 Agent =========="
    echo ""
    
    # 检查引擎服务是否运行
    if declare -f engine_is_running > /dev/null 2>&1; then
        if ! engine_is_running; then
            log_error "引擎服务未运行，请先执行首次部署"
            log_info "提示: bash $SCRIPTS_DIR/eternal.sh --engine $ENGINE --name \"$AGENT_NAME\" --agent-id \"$AGENT_ID\""
            exit 1
        fi
    fi
    
    check_environment
    update_paths
    
    mkdir -p "$WORKSPACE_DIR"/{tasks,results,reports,logs}
    
    # 引擎注册
    if declare -f engine_register_agent > /dev/null 2>&1; then
        engine_register_agent "$AGENT_ID" "$AGENT_NAME" "$AGENT_EMOJI" "$WORKSPACE_DIR"
    fi
    
    # 通用：创建身份文件
    create_identity_files "$WORKSPACE_DIR" "$AGENT_NAME" "$AGENT_EMOJI"
    
    # 更新状态
    update_agent_in_state "$AGENT_ID" "$AGENT_NAME" "$AGENT_EMOJI" "$WORKSPACE_DIR"
    
    log_success "Agent $AGENT_ID 添加完成"
    print_report
}

# ============================================
# 生命周期：恢复（问题6修复：用 node 提取 agent 信息）
# ============================================
restore_mode() {
    log_info "========== 恢复模式 =========="
    echo ""
    check_environment
    
    local checkpoint=$(load_checkpoint)
    
    echo ""
    log_info "开始恢复..."
    
    mkdir -p "$CONFIG_DIR" "$DATA_DIR/workspace"/{tasks,results,reports,logs}
    
    # 用 node 从 deploy_state.json 提取所有 agent 信息（问题6修复）
    if [[ -f "$DATA_DIR/deploy_state.json" ]]; then
        node -e "
const fs = require('fs');
const state = JSON.parse(fs.readFileSync('$DATA_DIR/deploy_state.json', 'utf8'));
(state.agents || []).forEach(a => {
    console.log(a.id + '|' + (a.name||a.id) + '|' + (a.emoji||'🔮') + '|' + (a.workspace||''));
});
" | while IFS='|' read -r agent_id agent_name agent_emoji workspace; do
            if [[ -n "$agent_id" && -n "$workspace" ]]; then
                mkdir -p "$workspace"/{tasks,results,reports,logs}
                chmod -R 755 "$workspace"
                
                # 创建 agentDir
                local agent_dir="/root/.openclaw/agents/${agent_id}/agent"
                mkdir -p "$agent_dir"
                
                # 更新 agents.list
                update_agents_list "$agent_id" "$agent_name" "$agent_emoji" "$workspace"
                
                # 创建身份文件
                create_identity_files "$workspace" "$agent_name" "$agent_emoji"
                
                # 通知 Gateway 重新加载配置
                reload_gateway "$agent_id"
                
                log_success "Agent $agent_id 恢复完成"
            fi
        done
    else
        log_warn "未找到 deploy_state.json"
    fi
    
    # 重建 agents.list
    if declare -f engine_rebuild_agents > /dev/null 2>&1; then
        engine_rebuild_agents
    fi
    
    log_success "恢复完成"
}

update_agents_list() {
    local agent_id="$1"
    local agent_name="$2"
    local agent_emoji="$3"
    local workspace="$4"
    local agent_dir="/root/.openclaw/agents/${agent_id}/agent"
    
    log_info "更新 agents.list (id: $agent_id, workspace: $workspace)..."
    
    node -e "
const fs = require('fs');
const configFile = '$CONFIG_FILE';
const agentId = '$agent_id';
const agentName = '$agent_name';
const agentEmoji = '$agent_emoji';
const workspace = '$workspace';
const agentDir = '$agent_dir';

try {
    let config = { agents: { list: [] } };
    
    // 读取现有配置
    if (fs.existsSync(configFile)) {
        const existing = JSON.parse(fs.readFileSync(configFile, 'utf8'));
        config = existing;
        if (!config.agents) config.agents = {};
        if (!config.agents.list) config.agents.list = [];
    }
    
    // 查找是否已存在
    const idx = config.agents.list.findIndex(a => a.id === agentId);
    const agentEntry = {
        id: agentId,
        name: agentName || agentId,
        workspace: workspace,
        agentDir: agentDir,
        model: 'clawrouter/free'
    };
    
    if (idx >= 0) {
        config.agents.list[idx] = { ...config.agents.list[idx], ...agentEntry };
    } else {
        config.agents.list.push(agentEntry);
    }
    
    fs.writeFileSync(configFile, JSON.stringify(config, null, 2));
    console.log('agents.list 已更新: ' + agentId);
} catch (e) {
    console.error('更新 agents.list 失败: ' + e.message);
    process.exit(1);
}
" && log_success "agents.list 已更新" || log_error "agents.list 更新失败"
}

# reload_gateway 已在 engine.sh 中定义，此处声明为外部函数
reload_gateway() {
    local target_agent_id="${1:-}"
    if declare -f engine_reload_gateway > /dev/null 2>&1; then
        engine_reload_gateway "$target_agent_id"
    fi
}

# ============================================
# 主入口
# ============================================
main() {
    parse_args "$@"
    
    if [[ "$CHECK_ONLY" == "true" ]]; then
        check_status
        exit 0
    fi
    
    if [[ "$SEND_MODE" == "true" ]]; then
        send_message_mode
        exit 0
    fi
    
    if [[ "$RESTORE_MODE" == "true" ]]; then
        restore_mode
        exit 0
    fi
    
    # 检查是否已有部署
    if [[ -f "$DATA_DIR/deploy_state.json" ]]; then
        # 添加新 agent
        if [[ -n "$AGENT_NAME" ]]; then
            add_agent
        else
            log_error "检测到已有部署，请提供 --name 参数添加新 agent"
            exit 1
        fi
    else
        # 首次部署
        if [[ -z "$AGENT_NAME" ]]; then
            log_error "首次部署必须提供 --name 参数"
            print_help
            exit 1
        fi
        first_deploy
    fi
}

main "$@"
