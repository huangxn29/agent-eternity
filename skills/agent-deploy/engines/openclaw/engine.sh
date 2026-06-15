#!/bin/bash
# ============================================
# OpenClaw Engine — OpenClaw 引擎实现
# 适用于 Agent Deploy Framework
# v1.1: 修复编号硬编码、watchdog 分级、reload_gateway bug
# ============================================

# ============================================
# 引擎元信息
# ============================================
ENGINE_NAME="openclaw"
ENGINE_VERSION="3.0"
OPENCLAW_VERSION="2026.5.3-1"

# OpenClaw 特有配置
GATEWAY_PORT=18789
PROXY_PORT=8402
NPM_GLOBAL_DIR="/usr/lib/node_modules"
NPM_DIR="/root/.openclaw/npm"
NPM_BACKUP_DIR="/app/data/openclaw/npm-backup"

# ============================================
# 引擎初始化（可选）
# ============================================
engine_init() {
    log_info "OpenClaw 引擎初始化..."
    
    # 设置默认 DATA_DIR
    if [[ -z "$DATA_DIR" ]]; then
        DATA_DIR="/app/data/openclaw"
    fi
}

# ============================================
# 必需：检查引擎是否已安装
# ============================================
engine_is_installed() {
    command -v openclaw &> /dev/null
}

# ============================================
# 必需：获取数据目录
# ============================================
engine_get_data_dir() {
    echo "/app/data/openclaw"
}

# ============================================
# 必需：更新路径（问题1修复：自动检测编号，不硬编码）
# ============================================
engine_update_paths() {
    # workspace 目录根据 agent_id 变化
    if [[ "$AGENT_ID" == "main" ]]; then
        WORKSPACE_DIR="$DATA_DIR/workspace"
    else
        # 自动检测下一个编号
        local next_num=2
        if [[ -f "$DATA_DIR/deploy_state.json" ]]; then
            local count=$(node -e "const s=JSON.parse(require('fs').readFileSync('$DATA_DIR/deploy_state.json','utf8')); console.log(s.agents?s.agents.length:0)" 2>/dev/null || echo "0")
            next_num=$((count + 1))
        else
            # 检查已有目录
            next_num=$(($(ls -d /app/data/openclaw-*/ 2>/dev/null | wc -l) + 2))
        fi
        WORKSPACE_DIR="/app/data/openclaw-${next_num}/workspace"
    fi
    
    SCRIPTS_DIR="$DATA_DIR/scripts"
    CONFIG_DIR="$DATA_DIR/config"
    CONFIG_FILE="$CONFIG_DIR/openclaw.json"
    LOG_DIR="$WORKSPACE_DIR/logs"
}

# ============================================
# 必需：获取引擎特有的端口
# ============================================
# 重要：Gateway host网络模式会额外监听 port+1 和 port+2
# 多实例GATEWAY_PORT之间必须间隔4（如18789/18793/18797...）
# ClawRouter端口间隔1即可（8402/8403/8404...）
engine_get_ports() {
    # 返回 Gateway 的三个端口（port, port+1, port+2）
    local gw_p1=$((GATEWAY_PORT + 1))
    local gw_p2=$((GATEWAY_PORT + 2))
    echo "$GATEWAY_PORT $gw_p1 $gw_p2 $PROXY_PORT"
}

# ============================================
# 新增：获取核心端口（用于 auto_restore.sh 检查）
# ============================================
engine_get_primary_port() {
    echo "$GATEWAY_PORT"
}

# ============================================
# 新增：获取日志文件匹配模式（用于 print_report）
# ============================================
engine_get_log_pattern() {
    echo "$LOG_DIR/*.log"
}

# ============================================
# 必需：获取重启命令
# ============================================
engine_get_restart_cmd() {
    echo "bash $SCRIPTS_DIR/eternal.sh --engine $ENGINE --restore"
}

# ============================================
# 必需：获取恢复命令
# ============================================
engine_get_restore_cmd() {
    echo "bash $SCRIPTS_DIR/eternal.sh --engine $ENGINE --restore"
}

# ============================================
# 必需：检查服务是否运行
# ============================================
# 检查 Gateway 的三个端口（port, port+1, port+2）
engine_is_running() {
    check_port $GATEWAY_PORT && check_port $((GATEWAY_PORT + 1)) && check_port $((GATEWAY_PORT + 2))
}

# ============================================
# 必需：检查是否需要恢复
# ============================================
# 任一 Gateway 端口不可用就需要恢复
engine_needs_restore() {
    ! (check_port $GATEWAY_PORT && check_port $((GATEWAY_PORT + 1)) && check_port $((GATEWAY_PORT + 2)))
}

# ============================================
# 必需：检查引擎环境
# ============================================
engine_check_environment() {
    if command -v node &> /dev/null; then
        NODE_VERSION=$(node -v | cut -d'v' -f2 | cut -d'.' -f1)
        [[ "$NODE_VERSION" -lt 22 ]] && log_warn "Node.js 低于 v22"
    else
        log_error "Node.js 未安装"
        exit 1
    fi
    
    command -v npm &> /dev/null || { log_error "npm 未安装"; exit 1; }
}

# ============================================
# 必需：安装引擎
# ============================================
engine_install() {
    log_info "安装 OpenClaw..."
    command -v openclaw &> /dev/null && { log_warn "OpenClaw 已安装，跳过"; return 0; }
    
    # 从备份恢复
    if [[ -d "$NPM_BACKUP_DIR/openclaw" ]]; then
        log_info "从备份恢复 OpenClaw..."
        
        if command -v rsync &> /dev/null; then
            rsync -a "$NPM_BACKUP_DIR/openclaw/" "$NPM_GLOBAL_DIR/openclaw/" && \
            ln -sf "$NPM_GLOBAL_DIR/openclaw/bin/openclaw" /usr/local/bin/openclaw 2>/dev/null && \
            command -v openclaw &> /dev/null && { log_success "OpenClaw 从备份恢复完成"; return 0; }
        else
            cp -rL "$NPM_BACKUP_DIR/openclaw" "$NPM_GLOBAL_DIR/openclaw" 2>/dev/null && \
            ln -sf "$NPM_GLOBAL_DIR/openclaw/bin/openclaw" /usr/local/bin/openclaw 2>/dev/null && \
            command -v openclaw &> /dev/null && { log_success "OpenClaw 从备份恢复完成"; return 0; }
        fi
        log_warn "备份恢复失败，回退到 npm 安装"
    fi
    
    npm install -g openclaw@${OPENCLAW_VERSION} && log_success "OpenClaw 安装完成" || { log_error "安装失败"; exit 1; }
}

# ============================================
# 必需：备份引擎关键文件
# ============================================
engine_backup() {
    log_info "备份 npm 包到持久存储..."
    
    [[ -d "$NPM_BACKUP_DIR/openclaw" ]] && { log_info "npm 备份已存在，跳过"; return 0; }
    
    mkdir -p "$NPM_BACKUP_DIR"
    
    if [[ -d "$NPM_GLOBAL_DIR/openclaw" ]]; then
        log_info "备份 OpenClaw 到 $NPM_BACKUP_DIR..."
        
        if command -v rsync &> /dev/null; then
            timeout 300 rsync -a "$NPM_GLOBAL_DIR/openclaw" "$NPM_BACKUP_DIR/" 2>&1 && \
            sync && log_success "OpenClaw 已备份" || log_warn "OpenClaw 备份失败"
        else
            cp -rL "$NPM_GLOBAL_DIR/openclaw" "$NPM_BACKUP_DIR/" && sync && log_success "OpenClaw 已备份" || log_warn "OpenClaw 备份失败"
        fi
    fi
    
    if [[ -d "$NPM_DIR/node_modules/@blockrun/clawrouter" ]] && [[ ! -d "$NPM_BACKUP_DIR/clawrouter-npm" ]]; then
        log_info "备份 ClawRouter..."
        
        if command -v rsync &> /dev/null; then
            timeout 300 rsync -a "$NPM_DIR/" "$NPM_BACKUP_DIR/clawrouter-npm/" 2>&1 && sync && log_success "ClawRouter 已备份"
        else
            cp -rL "$NPM_DIR" "$NPM_BACKUP_DIR/clawrouter-npm" && sync && log_success "ClawRouter 已备份"
        fi
    fi
}

# ============================================
# 必需：初始化配置
# ============================================
engine_init_config() {
    log_info "初始化 OpenClaw..."
    
    mkdir -p "$CONFIG_DIR"
    setup_config "$CONFIG_FILE"
    
    # 如果配置文件已存在且合法，跳过
    if [[ -f "$CONFIG_FILE" ]]; then
        # 使用 node 检查配置合法性
        local has_agents=$(node -e "
const fs = require('fs');
try {
    const c = JSON.parse(fs.readFileSync('$CONFIG_FILE', 'utf8'));
    console.log(c.agents ? 'yes' : 'no');
} catch(e) { console.log('no'); }
" 2>/dev/null)
        if [[ "$has_agents" == "yes" ]]; then
            log_success "已有合法配置，跳过初始化"
            return 0
        fi
    fi
    
    # 执行 onboard
    openclaw onboard --mode local --non-interactive --accept-risk 2>/dev/null || true
    
    # 移动配置到持久目录
    if [[ -f "$HOME/.openclaw/openclaw.json" ]] && [[ ! -L "$HOME/.openclaw/openclaw.json" ]]; then
        cp "$HOME/.openclaw/openclaw.json" "$CONFIG_FILE"
    fi
    
    # 重建 symlink
    setup_config "$CONFIG_FILE"
    
    [[ -f "$CONFIG_FILE" ]] && log_success "初始化完成" || { log_error "初始化失败"; return 1; }
}

setup_config() {
    local cfg_file="${1:-$CONFIG_FILE}"
    mkdir -p "$HOME/.openclaw"
    ln -sf "$cfg_file" "$HOME/.openclaw/openclaw.json"
    export OPENCLAW_CONFIG="$cfg_file"
}

# ============================================
# 必需：配置引擎
# ============================================
engine_configure() {
    log_info "配置 OpenClaw..."
    
    setup_config "$CONFIG_FILE"
    
    # 检查配置是否合法
    local has_agents="no"
    if [[ -f "$CONFIG_FILE" ]]; then
        has_agents=$(node -e "
const fs = require('fs');
try {
    const c = JSON.parse(fs.readFileSync('$CONFIG_FILE', 'utf8'));
    console.log(c.agents ? 'yes' : 'no');
} catch(e) { console.log('no'); }
" 2>/dev/null)
    fi
    
    if [[ "$has_agents" == "yes" ]]; then
        log_success "已有合法配置，跳过覆写"
    else
        mkdir -p "$CONFIG_DIR"
        [[ -f "$CONFIG_FILE" ]] && cp "$CONFIG_FILE" "$CONFIG_FILE.bak.$(date +%Y%m%d%H%M%S)" 2>/dev/null || true
        
        rm -f "$HOME/.openclaw/openclaw.json" 2>/dev/null || true
        rm -f "$CONFIG_FILE" 2>/dev/null || true
        
        setup_config "$CONFIG_FILE"
        
        log_info "使用 openclaw onboard 生成配置..."
        if openclaw onboard --mode local --non-interactive --accept-risk 2>&1 | tee /tmp/openclaw_onboard.log; then
            log_success "onboard 成功"
        else
            if [[ -f "$CONFIG_FILE" ]]; then
                log_warn "onboard 报错但配置文件已生成，继续"
            else
                log_error "onboard 失败且未生成配置文件"
                return 1
            fi
        fi
        
        [[ -f "$CONFIG_FILE" ]] && log_success "配置文件已保存到持久目录" || { log_error "未找到生成的配置文件"; return 1; }
    fi
    
    # 配置字段修正（用 node 直接修改）
    log_info "修正配置字段..."
    
    if [[ -f "$CONFIG_FILE" ]]; then
        node -e "
const fs = require('fs');
const configFile = '$CONFIG_FILE';
const gatewayPort = $GATEWAY_PORT;
const workspaceDir = '$WORKSPACE_DIR';

try {
    const c = JSON.parse(fs.readFileSync(configFile, 'utf8'));
    let modified = false;
    
    if (!c.gateway || c.gateway.port !== gatewayPort) {
        if (!c.gateway) c.gateway = {};
        c.gateway.port = gatewayPort;
        modified = true;
    }
    
    const curWs = (c.agents && c.agents.defaults && c.agents.defaults.workspace) || '';
    if (curWs !== workspaceDir) {
        if (!c.agents) c.agents = {};
        if (!c.agents.defaults) c.agents.defaults = {};
        c.agents.defaults.workspace = workspaceDir;
        modified = true;
    }
    
    if (modified) {
        fs.writeFileSync(configFile, JSON.stringify(c, null, 2));
        console.log('配置已修正');
    } else {
        console.log('配置字段已正确');
    }
} catch (e) {
    console.error('配置修正失败: ' + e.message);
    process.exit(1);
}
" && log_success "配置字段已修正"
        
        setup_config "$CONFIG_FILE"
    fi
    
    sync_config
    log_success "基础配置完成"
}

sync_config() {
    setup_config "$CONFIG_FILE"
    
    if [[ -L "$HOME/.openclaw/openclaw.json" ]]; then
        log_info "全局配置是 symlink，无需同步"
    elif [[ -f "$HOME/.openclaw/openclaw.json" ]]; then
        cp "$HOME/.openclaw/openclaw.json" "$CONFIG_FILE"
        setup_config "$CONFIG_FILE"
        log_success "配置已同步"
    fi
}

# ============================================
# 重载 Gateway 配置（问题10修复：接受 agent_id 参数并验证）
# ============================================
reload_gateway() {
    local target_agent_id="${1:-}"
    log_info "重载 Gateway 配置 (target: ${target_agent_id:-all})..."
    
    # 尝试发送 SIGHUP 让 Gateway 热加载
    local gw_pid=$(pgrep -f "openclaw gateway" 2>/dev/null | head -1)
    if [[ -z "$gw_pid" ]]; then
        gw_pid=$(pgrep -x "openclaw" 2>/dev/null | head -1)
    fi
    
    if [[ -n "$gw_pid" ]]; then
        # 先尝试 SIGHUP（热加载）
        kill -HUP "$gw_pid" 2>/dev/null && sleep 3
        
        # 验证新 agent 是否可见（问题10修复：正确传入 agent_id）
        if [[ -n "$target_agent_id" ]] && openclaw agents list 2>&1 | grep -q "$target_agent_id"; then
            log_success "Gateway 热加载成功"
            return 0
        fi
        
        # SIGHUP 不生效，重启 Gateway
        log_info "热加载未生效，重启 Gateway..."
        kill "$gw_pid" 2>/dev/null
        sleep 3
        nohup openclaw gateway > "$DATA_DIR/workspace/logs/openclaw.log" 2>&1 &
        
        # 等待 Gateway 重新启动
        local retries=0
        while [[ $retries -lt 15 ]]; do
            sleep 2
            if check_port $GATEWAY_PORT; then
                # 再次验证
                if [[ -n "$target_agent_id" ]]; then
                    sleep 2
                    if openclaw agents list 2>&1 | grep -q "$target_agent_id"; then
                        log_success "Gateway 重启成功，agent $target_agent_id 可见"
                        return 0
                    fi
                else
                    log_success "Gateway 重启成功"
                    return 0
                fi
            fi
            retries=$((retries + 1))
        done
        log_warn "Gateway 重启超时"
    else
        log_warn "未找到 Gateway 进程，跳过重载"
    fi
}

# 引擎内部使用的 reload_gateway（被框架调用）
engine_reload_gateway() {
    reload_gateway "$@"
}

# ============================================
# 必需：配置模型
# ============================================
engine_configure_model() {
    log_info "配置默认模型..."
    
    setup_config "$CONFIG_FILE"
    
    if ! check_port $PROXY_PORT; then
        log_warn "ClawRouter 代理端口 $PROXY_PORT 未监听，跳过模型配置"
        return 0
    fi
    
    if ! check_port $GATEWAY_PORT; then
        log_warn "Gateway 端口 $GATEWAY_PORT 未监听，跳过模型配置"
        return 0
    fi
    
    # 安装 ClawRouter 为插件
    if ! openclaw plugins list 2>&1 | grep -q "clawrouter"; then
        log_info "安装 ClawRouter 为 OpenClaw 插件..."
        openclaw plugins install "$NPM_DIR/node_modules/@blockrun/clawrouter" 2>&1 | grep -q "Installed plugin" && \
            log_success "ClawRouter 插件安装成功" || log_warn "ClawRouter 插件安装失败"
    else
        log_info "ClawRouter 插件已安装，跳过"
    fi
    
    # 注册 clawrouter provider
    log_info "注册 ClawRouter 为模型 provider..."
    local provider_config='{"models":{"providers":{"clawrouter":{"baseUrl":"http://127.0.0.1:'$PROXY_PORT'/v1","apiKey":"unused","models":[{"id":"free","name":"Free Auto-Route"},{"id":"deepseek-v4-flash","name":"DeepSeek V4 Flash"},{"id":"qwen3-coder-480b","name":"Qwen3 Coder 480B"},{"id":"glm-4.7","name":"GLM 4.7"},{"id":"gpt-oss-120b","name":"GPT OSS 120B"},{"id":"nemotron-ultra-253b","name":"Nemotron Ultra 253B"}]}}}}'
    
    echo "$provider_config" | openclaw config patch --stdin 2>&1 | grep -q "Applied" && \
        log_success "ClawRouter provider 注册成功" || log_warn "ClawRouter provider 注册失败"
    
    # 设置默认模型
    if openclaw models set clawrouter/free 2>&1 | grep -q "Updated"; then
        log_success "默认模型已设置为 clawrouter/free（自动路由）"
    else
        log_warn "设置默认模型失败"
    fi
    
    sync_config
}

# ============================================
# 必需：启动引擎服务
# ============================================
engine_start_services() {
    start_clawrouter
    start_gateway
}

start_clawrouter() {
    if check_port $PROXY_PORT; then
        log_info "ClawRouter 已在运行，共享模式 (端口: $PROXY_PORT)"
        return 0
    fi
    
    log_info "启动 ClawRouter..."
    
    # 安装 ClawRouter
    install_clawrouter
    
    mkdir -p "$LOG_DIR"
    cd "$NPM_DIR"
    nohup npx clawrouter proxy > "$LOG_DIR/clawrouter.log" 2>&1 &
    sleep 3
    
    if check_port $PROXY_PORT; then
        log_success "ClawRouter 启动成功 (端口: $PROXY_PORT)"
    else
        log_error "ClawRouter 启动失败，查看日志: $LOG_DIR/clawrouter.log"
        tail -20 "$LOG_DIR/clawrouter.log"
        return 1
    fi
}

install_clawrouter() {
    log_info "安装 ClawRouter..."
    [[ -d "$NPM_DIR/node_modules/@blockrun/clawrouter" ]] && { log_warn "ClawRouter 已安装，跳过"; return 0; }
    
    # 从备份恢复
    if [[ -d "$NPM_BACKUP_DIR/clawrouter-npm/node_modules/@blockrun/clawrouter" ]]; then
        log_info "从备份恢复 ClawRouter..."
        mkdir -p "$NPM_DIR"
        if command -v rsync &> /dev/null; then
            rsync -a "$NPM_BACKUP_DIR/clawrouter-npm/." "$NPM_DIR/"
        else
            cp -rL "$NPM_BACKUP_DIR/clawrouter-npm/." "$NPM_DIR/"
        fi
        [[ -d "$NPM_DIR/node_modules/@blockrun/clawrouter" ]] && { log_success "ClawRouter 从备份恢复完成"; return 0; }
    fi
    
    mkdir -p "$NPM_DIR"
    cd "$NPM_DIR"
    [[ ! -f "$NPM_DIR/package.json" ]] && npm init -y > /dev/null 2>&1
    npm install @blockrun/clawrouter && log_success "ClawRouter 安装完成" || { log_error "安装失败"; return 1; }
}

start_gateway() {
    log_info "启动 OpenClaw Gateway (端口: $GATEWAY_PORT)..."
    
    if check_port $GATEWAY_PORT; then
        local gw_pid=$(lsof -ti :$GATEWAY_PORT 2>/dev/null | head -1 || echo "")
        log_info "Gateway 已在运行 (PID: $gw_pid)，共享模式"
        return 0
    fi
    
    # 杀占用端口的进程
    kill_port_process $GATEWAY_PORT
    sleep 2
    
    mkdir -p "$LOG_DIR"
    mkdir -p "$WORKSPACE_DIR/logs"
    
    setup_config "$CONFIG_FILE"
    export OPENCLAW_CONFIG="$CONFIG_FILE"
    
    nohup openclaw gateway > "$LOG_DIR/openclaw.log" 2>&1 &
    
    # 等待端口监听
    local retries=0
    local max_retries=15
    while [[ $retries -lt $max_retries ]]; do
        sleep 2
        if check_port $GATEWAY_PORT; then
            log_success "Gateway 启动成功 (端口 $GATEWAY_PORT)"
            return 0
        fi
        retries=$((retries + 1))
        log_info "等待 Gateway 启动... ($retries/$max_retries)"
    done
    
    log_error "Gateway 启动失败，查看日志: $LOG_DIR/openclaw.log"
    tail -20 "$LOG_DIR/openclaw.log"
    return 1
}

# ============================================
# 必需：注册 Agent（问题10修复：调用 reload_gateway 传入 agent_id）
# ============================================
engine_register_agent() {
    local agent_id="$1"
    local agent_name="$2"
    local agent_emoji="$3"
    local workspace="$4"
    
    log_info "注册 Agent: $agent_id (workspace: $workspace)..."
    
    # 创建 workspace
    mkdir -p "$workspace"/{tasks,results,reports,logs}
    
    # 创建 agentDir
    local agent_dir="/root/.openclaw/agents/${agent_id}/agent"
    mkdir -p "$agent_dir"
    
    # 更新 agents.list
    update_agents_list "$agent_id" "$agent_name" "$agent_emoji" "$workspace"
    
    # 通知 Gateway 重新加载配置（问题10修复：传入 agent_id）
    reload_gateway "$agent_id"
    
    log_success "Agent $agent_id 注册完成"
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

# ============================================
# 必需：从备份恢复引擎
# ============================================
engine_restore() {
    log_info "从备份恢复 npm 包..."
    
    if [[ ! -d "$NPM_BACKUP_DIR" ]]; then
        log_warn "未找到 npm 备份"
        return 1
    fi
    
    if [[ -d "$NPM_BACKUP_DIR/openclaw" ]]; then
        if command -v rsync &> /dev/null; then
            rsync -a "$NPM_BACKUP_DIR/openclaw/" "$NPM_GLOBAL_DIR/openclaw/" && \
            ln -sf "$NPM_GLOBAL_DIR/openclaw/bin/openclaw" /usr/local/bin/openclaw 2>/dev/null
        else
            mkdir -p "$NPM_GLOBAL_DIR"
            cp -rL "$NPM_BACKUP_DIR/openclaw" "$NPM_GLOBAL_DIR/openclaw" && \
            ln -sf "$NPM_GLOBAL_DIR/openclaw/bin/openclaw" /usr/local/bin/openclaw 2>/dev/null
        fi
        command -v openclaw &> /dev/null && log_success "OpenClaw 恢复成功" || log_warn "OpenClaw 恢复失败"
    fi
    
    if [[ -d "$NPM_BACKUP_DIR/clawrouter-npm" ]]; then
        mkdir -p "$NPM_DIR"
        if command -v rsync &> /dev/null; then
            rsync -a "$NPM_BACKUP_DIR/clawrouter-npm/" "$NPM_DIR/"
        else
            cp -rL "$NPM_BACKUP_DIR/clawrouter-npm/." "$NPM_DIR/"
        fi
        [[ -d "$NPM_DIR/node_modules/@blockrun/clawrouter" ]] && log_success "ClawRouter 恢复成功"
    fi
    
    # 确保配置存在
    if [[ ! -f "$CONFIG_FILE" ]]; then
        engine_init_config
    fi
}

# ============================================
# 必需：重建 agents
# ============================================
engine_rebuild_agents() {
    log_info "重建 agents.list..."
    
    if [[ ! -f "$DATA_DIR/deploy_state.json" ]]; then
        log_warn "未找到 deploy_state.json"
        return
    fi
    
    setup_config "$CONFIG_FILE"
    
    node -e "
const fs = require('fs');
const stateFile = '$DATA_DIR/deploy_state.json';
const configFile = '$CONFIG_FILE';

try {
    const state = JSON.parse(fs.readFileSync(stateFile, 'utf8'));
    let config = { agents: { list: [] } };
    
    if (fs.existsSync(configFile)) {
        config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
        if (!config.agents) config.agents = {};
        if (!config.agents.list) config.agents.list = [];
    }
    
    if (state.agents && Array.isArray(state.agents)) {
        for (const agent of state.agents) {
            const idx = config.agents.list.findIndex(a => a.id === agent.id);
            const entry = {
                id: agent.id,
                name: agent.name || agent.id,
                workspace: agent.workspace,
                agentDir: '/root/.openclaw/agents/' + agent.id + '/agent',
                model: 'clawrouter/free'
            };
            
            if (idx >= 0) {
                config.agents.list[idx] = entry;
            } else {
                config.agents.list.push(entry);
            }
        }
    }
    
    fs.writeFileSync(configFile, JSON.stringify(config, null, 2));
    console.log('agents.list 已重建');
} catch (e) {
    console.error('重建 agents.list 失败: ' + e.message);
}
"
}

# ============================================
# 新增：引擎特有的 watchdog 循环体（问题4修复）
# 返回分级检查逻辑：Gateway 挂了立即重启，ClawRouter 挂了单独重启
# ============================================
engine_watchdog_body() {
    cat << 'WATCHDOG_BODY'
# OpenClaw 特有 watchdog：分级检查
GATEWAY_PORT=18789
PROXY_PORT=8402
PROXY_RESTART_CMD="cd /root/.openclaw/npm && nohup npx clawrouter proxy > $DATA_DIR/workspace/logs/clawrouter.log 2>&1 &"

while true; do
    # Gateway 是核心，挂了必须重启
    if ! check_port $GATEWAY_PORT; then
        echo "$(date): Gateway (port $GATEWAY_PORT) down, restarting..." >> "$LOG_FILE"
        eval $RESTART_CMD
    fi
    # ClawRouter 可以单独重启
    if ! check_port $PROXY_PORT; then
        echo "$(date): ClawRouter (port $PROXY_PORT) down, restarting..." >> "$LOG_FILE"
        eval $PROXY_RESTART_CMD
        sleep 3
    fi
    sleep 60
done
WATCHDOG_BODY
}

# ============================================
# 必需：获取引擎状态
# ============================================
engine_get_state() {
    local wallet=""
    if [[ -f "$LOG_DIR/clawrouter.log" ]]; then
        wallet=$(grep "EVM Address" "$LOG_DIR/clawrouter.log" 2>/dev/null | head -1 | grep -oP '0x[0-9a-fA-F]+' || echo "")
        [[ -z "$wallet" ]] && wallet=$(grep -oE "0x[a-fA-F0-9]{40}" "$LOG_DIR/clawrouter.log" 2>/dev/null | head -1 || echo "")
    fi
    
    cat << EOF
{
  "gateway_port": $GATEWAY_PORT,
  "proxy_port": $PROXY_PORT,
  "openclaw_version": "$OPENCLAW_VERSION",
  "wallet": "$wallet"
}
EOF
}

# ============================================
# 必需：验证部署
# ============================================
engine_verify() {
    local ok=true
    
    check_port $GATEWAY_PORT && log_success "✓ Gateway 端口 $GATEWAY_PORT 正常" || { log_error "✗ Gateway 端口未监听"; ok=false; }
    check_port $PROXY_PORT && log_success "✓ Proxy 端口 $PROXY_PORT 正常" || { log_error "✗ Proxy 端口未监听"; ok=false; }
    
    # 测试模型
    log_info "测试模型..."
    local test_resp=$(openclaw agent --agent main --session-id "deploy-test-$(date +%s)" --message "Say OK" --json 2>&1)
    if echo "$test_resp" | grep -q "EMBEDDED FALLBACK"; then
        log_warn "⚠ 模型调用走 embedded fallback"
    elif echo "$test_resp" | grep -q "payloads"; then
        log_success "✓ 模型调用成功"
    else
        log_warn "⚠ 模型调用可能有问题（首次可能超时）"
    fi
    
    # 提取钱包
    [[ -f "$LOG_DIR/clawrouter.log" ]] && grep -oE "0x[a-fA-F0-9]{40}" "$LOG_DIR/clawrouter.log" | head -1 > "$LOG_DIR/wallet.txt"
    
    [[ "$ok" == "true" ]]
}

# ============================================
# 必需：检查状态
# ============================================
engine_check_status() {
    command -v openclaw &> /dev/null && log_success "OpenClaw: 已安装 ($(openclaw --version 2>/dev/null || echo 'unknown'))" || log_warn "OpenClaw: 未安装"
    
    if check_port $GATEWAY_PORT; then
        local gw_pid=$(lsof -ti :$GATEWAY_PORT 2>/dev/null | head -1 || echo "")
        [[ -n "$gw_pid" ]] && log_success "Gateway: 运行中 (PID: $gw_pid, 端口: $GATEWAY_PORT)" || log_success "Gateway 端口 $GATEWAY_PORT: 已监听"
    else
        log_warn "Gateway: 端口 $GATEWAY_PORT 未监听"
    fi
    
    if check_port $PROXY_PORT; then
        log_success "Proxy: 运行中 (端口: $PROXY_PORT)"
    else
        log_warn "Proxy: 端口 $PROXY_PORT 未监听"
    fi
    
    [[ -f "$CONFIG_FILE" ]] && log_success "配置: $CONFIG_FILE" || log_warn "配置: 未找到"
    
    local agents=$(get_registered_agents)
    [[ -n "$agents" ]] && log_info "已注册 Agent: $agents"
}

# ============================================
# 必需：发送消息
# ============================================
engine_send_message() {
    local agent_id="$1"
    local message="$2"
    local session_id="$3"
    
    setup_config "$CONFIG_FILE"
    
    log_info "发送消息到 agent: $agent_id..."
    
    local response=$(openclaw agent --agent "$agent_id" --session-id "$session_id" --message "$message" --json 2>&1)
    
    echo ""
    echo "========== 消息结果 =========="
    
    local reply=$(echo "$response" | grep -oP '"text"\s*:\s*"\K[^"]+' | head -1 | sed 's/\\n/\n/g' | sed 's/\\"/"/g')
    if [[ -n "$reply" ]]; then
        echo "$reply"
    else
        echo "$response"
    fi
    
    echo ""
    echo "--- 元信息 ---"
    
    local provider=$(echo "$response" | grep -oP '"winnerProvider"\s*:\s*"\K[^"]+' | head -1)
    [[ -n "$provider" ]] && echo "provider: $provider"
    
    if echo "$response" | grep -q "EMBEDDED FALLBACK"; then
        echo "⚠ 警告: 消息走 EMBEDDED FALLBACK"
    fi
}

# ============================================
# 可选：注入钱包地址到身份文件
# ============================================
engine_inject_wallet() {
    log_info "注入钱包地址到身份文件..."
    
    local wallet=""
    if [[ -f "$LOG_DIR/clawrouter.log" ]]; then
        wallet=$(grep "EVM Address" "$LOG_DIR/clawrouter.log" 2>/dev/null | head -1 | grep -oP '0x[0-9a-fA-F]+' || echo "")
        [[ -z "$wallet" ]] && wallet=$(grep -oE "0x[a-fA-F0-9]{40}" "$LOG_DIR/clawrouter.log" 2>/dev/null | head -1 || echo "")
    fi
    
    if [[ -n "$wallet" ]]; then
        log_info "发现钱包地址: $wallet"
        echo "$wallet" > "$LOG_DIR/wallet.txt"
        
        # 注入到 main workspace
        if [[ -f "$DATA_DIR/workspace/IDENTITY.md" ]] && ! grep -q "钱包地址" "$DATA_DIR/workspace/IDENTITY.md"; then
            sed -i "s|Gateway 端口 ${GATEWAY_PORT}。|Gateway 端口 ${GATEWAY_PORT}，钱包地址 \`${wallet}\`。|" "$DATA_DIR/workspace/IDENTITY.md"
            log_success "IDENTITY.md 已注入钱包地址"
        fi
    else
        log_warn "未找到钱包地址"
    fi
}
