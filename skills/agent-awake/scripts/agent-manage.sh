#!/bin/bash
# ============================================
# Agent Awake - 管理Agent v2.1
# ============================================
# 重构版本，无Node.js依赖，使用jq或纯bash解析JSON
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

# 默认值
DATA_DIR="${DATA_DIR:-./agent-awake-data}"
ACTION=""
TARGET_AGENT=""

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
        # 纯bash简单解析
        grep -o "\"$key\"[[:space:]]*:[[:space:]]*\"[^\"]*\"" "$file" 2>/dev/null | head -1 | sed 's/.*://;s/"//g'
    fi
}

# 读取JSON数组指定元素的字段
json_get_agent() {
    local file="$1"
    local agent_id="$2"
    local field="$3"
    
    if [ ! -f "$file" ]; then
        echo ""
        return
    fi
    
    if command -v jq &> /dev/null; then
        jq -r ".agents[] | select(.id == \"$agent_id\") | .$field // \"\"" "$file" 2>/dev/null
    else
        # 简单解析，不支持复杂查询
        echo ""
    fi
}

# 从agents数组删除元素
json_remove_agent() {
    local file="$1"
    local agent_id="$2"
    
    if command -v jq &> /dev/null; then
        jq "del(.agents[] | select(.id == \"$agent_id\"))" "$file" > /tmp/json.tmp && mv /tmp/json.tmp "$file"
    fi
}

# 更新agents数组中元素的字段
json_update_agent() {
    local file="$1"
    local agent_id="$2"
    local field="$3"
    local value="$4"
    
    if command -v jq &> /dev/null; then
        jq "(.agents[] | select(.id == \"$agent_id\") | .$field) = \"$value\"" "$file" > /tmp/json.tmp && mv /tmp/json.tmp "$file"
    fi
}

# 获取agents数组长度
json_agents_count() {
    local file="$1"
    
    if [ ! -f "$file" ]; then
        echo "0"
        return
    fi
    
    if command -v jq &> /dev/null; then
        jq '.agents | length' "$file" 2>/dev/null || echo "0"
    else
        grep -c '"id":' "$file" 2>/dev/null || echo "0"
    fi
}

# ============ 参数解析 ============
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --list) ACTION="list"; shift ;;
            --agent-id) TARGET_AGENT="$2"; shift 2 ;;
            --status) ACTION="status"; shift ;;
            --start) ACTION="start"; shift ;;
            --stop) ACTION="stop"; shift ;;
            --restart) ACTION="restart"; shift ;;
            --logs) ACTION="logs"; shift ;;
            --delete) ACTION="delete"; shift ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --list                  列出所有Agent"
                echo "  --agent-id <ID>         Agent ID"
                echo "  --status                查看Agent状态"
                echo "  --start                 启动Agent"
                echo "  --stop                  停止Agent"
                echo "  --restart               重启Agent"
                echo "  --logs                  查看Agent日志"
                echo "  --delete                删除Agent"
                echo ""
                echo "社区相关:"
                echo "  查看社区巡检: docker exec <agent_id> cat /app/data/openclaw/workspace/COMMUNITY.md"
                echo "  查看定时任务: crontab -l | grep wakeup"
                echo "  禁用巡检: crontab -l | grep -v wakeup | crontab -"
                exit 0
                ;;
            *) echo "未知参数: $1"; exit 1 ;;
        esac
    done
}

# ============ Agent操作函数 ============

# 列出所有Agent
list_agents() {
    local platform_json="$DATA_DIR/platform.json"
    
    if [ ! -f "$platform_json" ]; then
        echo "[WARN] 平台未初始化"
        return
    fi
    
    echo "=========================================="
    echo "  Agent Awake - Agent列表"
    echo "=========================================="
    
    local count=$(json_agents_count "$platform_json")
    
    if [ "$count" = "0" ] || [ -z "$count" ]; then
        echo "  (无Agent)"
    else
        local i=1
        if command -v jq &> /dev/null; then
            # 使用jq格式化输出
            jq -r '.agents[] | "\(.emoji) \(.name) (\(.id)) - \(if .status == "running" then "🟢 运行中" else "🔴 " + .status end)\n     Gateway:\(.gateway_port) ClawRouter:\(.clawrouter_port) CPU:\(.cpu) MEM:\(.memory)"' "$platform_json" 2>/dev/null | while IFS= read -r line; do
                echo "  $i. $line"
                i=$((i+1))
            done
        else
            # 简单输出
            echo "  Agent数量: $count"
            echo "  (安装jq以获取详细信息)"
        fi
    fi
    
    echo "=========================================="
}

# 查看Agent状态
agent_status() {
    local agent_id="$1"
    local agent_dir="$DATA_DIR/$agent_id"
    local platform_json="$DATA_DIR/platform.json"
    
    if [ ! -d "$agent_dir" ]; then
        echo "[ERROR] Agent $agent_id 不存在"
        return 1
    fi
    
    # 获取Agent信息
    local name=$(json_get_agent "$platform_json" "$agent_id" "name")
    local emoji=$(json_get_agent "$platform_json" "$agent_id" "emoji")
    local gw_port=$(json_get_agent "$platform_json" "$agent_id" "gateway_port")
    local cr_port=$(json_get_agent "$platform_json" "$agent_id" "clawrouter_port")
    local cpu=$(json_get_agent "$platform_json" "$agent_id" "cpu")
    local memory=$(json_get_agent "$platform_json" "$agent_id" "memory")
    local status=$(json_get_agent "$platform_json" "$agent_id" "status")
    
    echo "=========================================="
    echo "  Agent: $emoji $name ($agent_id)"
    echo "=========================================="
    
    # 容器状态
    local running=$(docker ps -q -f name="$agent_id" 2>/dev/null)
    if [ -n "$running" ]; then
        echo "  容器: 🟢 运行中"
        local started=$(docker inspect --format='{{.State.StartedAt}}' "$agent_id" 2>/dev/null | cut -d'.' -f1)
        echo "  启动时间: $started"
    else
        echo "  容器: 🔴 已停止"
    fi
    
    # 资源配额
    echo "  资源配置: CPU=$cpu | Memory=$memory"
    
    # 服务状态
    if [ -n "$gw_port" ]; then
        local gw_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$gw_port/health" 2>/dev/null || echo "000")
        if [ "$gw_status" = "200" ]; then
            echo "  Gateway (:$gw_port): ✅ 正常"
        else
            echo "  Gateway (:$gw_port): ❌ HTTP $gw_status"
        fi
    fi
    
    if [ -n "$cr_port" ]; then
        local cr_status=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$cr_port/health" 2>/dev/null || echo "000")
        if [ "$cr_status" = "200" ]; then
            echo "  ClawRouter (:$cr_port): ✅ 正常"
        else
            echo "  ClawRouter (:$cr_port): ❌ HTTP $cr_status"
        fi
    fi
    
    # 钱包地址
    local wallet=$(json_get_agent "$platform_json" "$agent_id" "wallet_eth")
    if [ -n "$wallet" ]; then
        echo "  钱包: $wallet"
    fi
    
    # 社区巡检状态
    local community=$(json_get_agent "$platform_json" "$agent_id" "community_enabled")
    local github_repo=$(json_get_agent "$platform_json" "$agent_id" "github_repo")
    if [ "$community" = "true" ] && [ -n "$github_repo" ]; then
        echo "  社区巡检: ✅ 启用"
        echo "  仓库: $github_repo"
    else
        echo "  社区巡检: ❌ 未启用"
    fi
    
    echo "=========================================="
}

# 启动Agent
agent_start() {
    local agent_id="$1"
    
    echo "[INFO] 启动 Agent $agent_id..."
    cd "$DATA_DIR"
    
    if [ -f "$DATA_DIR/docker-compose.yml" ]; then
        docker compose start "$agent_id" 2>/dev/null || docker start "$agent_id" 2>/dev/null
    else
        docker start "$agent_id" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "[OK] Agent $agent_id 已启动"
        json_update_agent "$DATA_DIR/platform.json" "$agent_id" "status" "running" 2>/dev/null || true
    else
        echo "[ERROR] 启动失败"
        return 1
    fi
}

# 停止Agent
agent_stop() {
    local agent_id="$1"
    
    echo "[INFO] 停止 Agent $agent_id..."
    cd "$DATA_DIR"
    
    if [ -f "$DATA_DIR/docker-compose.yml" ]; then
        docker compose stop "$agent_id" 2>/dev/null || docker stop "$agent_id" 2>/dev/null
    else
        docker stop "$agent_id" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "[OK] Agent $agent_id 已停止"
        json_update_agent "$DATA_DIR/platform.json" "$agent_id" "status" "stopped" 2>/dev/null || true
    else
        echo "[ERROR] 停止失败"
        return 1
    fi
}

# 重启Agent
agent_restart() {
    local agent_id="$1"
    
    echo "[INFO] 重启 Agent $agent_id..."
    cd "$DATA_DIR"
    
    if [ -f "$DATA_DIR/docker-compose.yml" ]; then
        docker compose restart "$agent_id" 2>/dev/null || { docker stop "$agent_id" && docker start "$agent_id"; }
    else
        docker restart "$agent_id" 2>/dev/null
    fi
    
    if [ $? -eq 0 ]; then
        echo "[OK] Agent $agent_id 已重启"
    else
        echo "[ERROR] 重启失败"
        return 1
    fi
}

# 查看日志
agent_logs() {
    local agent_id="$1"
    local lines="${2:-50}"
    
    echo "=========================================="
    echo "  Agent $agent_id 日志 (最近 $lines 行)"
    echo "=========================================="
    
    if docker ps -a | grep -q "$agent_id"; then
        docker logs "$agent_id" --tail "$lines" 2>&1
    else
        # 尝试读取日志文件
        local log_file="$DATA_DIR/$agent_id/logs/gateway.log"
        if [ -f "$log_file" ]; then
            tail -n "$lines" "$log_file"
        else
            echo "[WARN] 容器和日志文件都不存在"
        fi
    fi
    
    echo "=========================================="
}

# 删除Agent
agent_delete() {
    local agent_id="$1"
    local agent_dir="$DATA_DIR/$agent_id"
    local platform_json="$DATA_DIR/platform.json"
    
    echo "=========================================="
    echo "  警告: 即将删除 Agent $agent_id"
    echo "=========================================="
    echo "  这将:"
    echo "  1. 停止并删除Docker容器"
    echo "  2. 从platform.json移除记录"
    echo "  3. 备份数据目录（不直接删除）"
    echo ""
    echo -n "确认删除? (y/N): "
    read -r confirm
    
    if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
        echo "[INFO] 已取消删除"
        return
    fi
    
    # 移除定时唤醒任务
    echo "[INFO] 移除定时任务..."
    if [ -f "$DATA_DIR/wakeup_${agent_id}.sh" ]; then
        rm -f "$DATA_DIR/wakeup_${agent_id}.sh"
    fi
    crontab -l 2>/dev/null | grep -v "wakeup_${agent_id}.sh" | crontab - 2>/dev/null || true
    
    # 停止并删除容器
    echo "[INFO] 删除容器..."
    cd "$DATA_DIR"
    
    if [ -f "$DATA_DIR/docker-compose.yml" ]; then
        docker compose down "$agent_id" 2>/dev/null
    else
        docker stop "$agent_id" 2>/dev/null
        docker rm "$agent_id" 2>/dev/null
    fi
    
    # 从platform.json移除
    echo "[INFO] 更新平台状态..."
    json_remove_agent "$platform_json" "$agent_id" 2>/dev/null || true
    
    # 从docker-compose.yml移除服务定义（简化处理）
    if [ -f "$DATA_DIR/docker-compose.yml" ]; then
        if command -v jq &> /dev/null; then
            jq "del(.services[\"$agent_id\"])" "$DATA_DIR/docker-compose.yml" > /tmp/compose.tmp && mv /tmp/compose.tmp "$DATA_DIR/docker-compose.yml"
        fi
    fi
    
    # 备份数据目录
    if [ -d "$agent_dir" ]; then
        local backup_dir="${agent_dir}.deleted.$(date +%Y%m%d%H%M%S)"
        mv "$agent_dir" "$backup_dir"
        echo "[OK] 数据已备份到: $backup_dir"
    fi
    
    echo ""
    echo "[OK] Agent $agent_id 已删除"
    echo "=========================================="
}

# ============ 主入口 ============
main() {
    parse_args "$@"
    
    # 验证目录
    if [ ! -d "$DATA_DIR" ]; then
        echo "[ERROR] 平台未初始化，请先运行 platform-init.sh"
        exit 1
    fi
    
    case "$ACTION" in
        list)
            list_agents
            ;;
        status)
            if [ -n "$TARGET_AGENT" ]; then
                agent_status "$TARGET_AGENT"
            else
                list_agents
            fi
            ;;
        start)
            if [ -n "$TARGET_AGENT" ]; then
                agent_start "$TARGET_AGENT"
            else
                echo "[ERROR] 请指定 --agent-id"
                exit 1
            fi
            ;;
        stop)
            if [ -n "$TARGET_AGENT" ]; then
                agent_stop "$TARGET_AGENT"
            else
                echo "[ERROR] 请指定 --agent-id"
                exit 1
            fi
            ;;
        restart)
            if [ -n "$TARGET_AGENT" ]; then
                agent_restart "$TARGET_AGENT"
            else
                echo "[ERROR] 请指定 --agent-id"
                exit 1
            fi
            ;;
        logs)
            if [ -n "$TARGET_AGENT" ]; then
                agent_logs "$TARGET_AGENT"
            else
                echo "[ERROR] 请指定 --agent-id"
                exit 1
            fi
            ;;
        delete)
            if [ -n "$TARGET_AGENT" ]; then
                agent_delete "$TARGET_AGENT"
            else
                echo "[ERROR] 请指定 --agent-id"
                exit 1
            fi
            ;;
        *)
            echo "用法: $0 [选项]"
            echo "选项:"
            echo "  --list                  列出所有Agent"
            echo "  --agent-id <ID> --status|start|stop|restart|logs|delete"
            echo ""
            echo "示例:"
            echo "  $0 --list"
            echo "  $0 --agent-id my-agent --status"
            echo "  $0 --agent-id my-agent --restart"
            exit 1
            ;;
    esac
}

main "$@"
