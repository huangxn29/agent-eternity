#!/bin/bash
# ============================================
# Agent Awake - 测试Agent v2.1
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
AGENT_ID=""
TEST_TYPE="health"
CHAT_MSG=""

# ============ JSON处理函数 ============

# 获取Agent端口
get_agent_port() {
    local agent_id="$1"
    local field="$2"
    local platform_json="$DATA_DIR/platform.json"
    
    if [ ! -f "$platform_json" ]; then
        echo ""
        return
    fi
    
    if command -v jq &> /dev/null; then
        jq -r ".agents[] | select(.id == \"$agent_id\") | .$field // \"\"" "$platform_json" 2>/dev/null
    else
        echo ""
    fi
}

# ============ 参数解析 ============
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --agent-id) AGENT_ID="$2"; shift 2 ;;
            --health) TEST_TYPE="health"; shift ;;
            --models) TEST_TYPE="models"; shift ;;
            --chat)
                TEST_TYPE="chat"
                CHAT_MSG="$2"
                shift 2
                ;;
            --full) TEST_TYPE="full"; shift ;;
            -h|--help)
                echo "用法: $0 [选项]"
                echo "选项:"
                echo "  --agent-id <ID>        Agent ID（必填）"
                echo "  --health               健康检查"
                echo "  --models               模型列表"
                echo "  --chat <消息>          模型调用测试"
                echo "  --full                 全面测试"
                exit 0
                ;;
            *) echo "未知参数: $1"; exit 1 ;;
        esac
    done
}

# ============ 测试函数 ============

# 健康检查
test_health() {
    local agent_id="$1"
    local gw_port="$2"
    local cr_port="$3"
    
    echo "=== 健康检查 ==="
    
    # 容器状态
    if docker ps | grep -q "$agent_id"; then
        echo "  容器: ✅ 运行中"
    else
        echo "  容器: ❌ 已停止"
        return 1
    fi
    
    # Gateway检查
    local gw_response=$(curl -s -w "\n%{http_code}" "http://localhost:$gw_port/health" 2>/dev/null)
    local gw_code=$(echo "$gw_response" | tail -1)
    local gw_body=$(echo "$gw_response" | head -1)
    
    if [ "$gw_code" = "200" ]; then
        echo "  Gateway (:$gw_port): ✅ $gw_body"
    else
        echo "  Gateway (:$gw_port): ❌ HTTP $gw_code"
    fi
    
    # ClawRouter检查
    local cr_response=$(curl -s -w "\n%{http_code}" "http://localhost:$cr_port/health" 2>/dev/null)
    local cr_code=$(echo "$cr_response" | tail -1)
    local cr_body=$(echo "$cr_response" | head -1)
    
    if [ "$cr_code" = "200" ]; then
        echo "  ClawRouter (:$cr_port): ✅ $cr_body"
        
        # 提取钱包地址
        if command -v jq &> /dev/null; then
            local wallet=$(echo "$cr_body" | jq -r '.wallet // empty' 2>/dev/null)
            if [ -n "$wallet" ]; then
                echo "  钱包: $wallet"
            fi
        fi
    else
        echo "  ClawRouter (:$cr_port): ❌ HTTP $cr_code"
    fi
}

# 模型列表
test_models() {
    local cr_port="$1"
    
    echo "=== 模型列表 ==="
    
    local models_json=$(curl -s "http://localhost:$cr_port/v1/models" 2>/dev/null)
    
    if [ -z "$models_json" ]; then
        echo "  ❌ 无法获取模型列表"
        return 1
    fi
    
    local count=0
    if command -v jq &> /dev/null; then
        count=$(echo "$models_json" | jq '.data | length' 2>/dev/null || echo "0")
    fi
    
    echo "  可用模型数: $count"
    
    # 列出前10个模型
    if command -v jq &> /dev/null; then
        echo "  模型列表:"
        echo "$models_json" | jq -r '.data[:10][] | "    - \(.id)"' 2>/dev/null
        
        local total=$(echo "$models_json" | jq '.data | length' 2>/dev/null || echo "0")
        if [ "$total" -gt 10 ]; then
            echo "    ... 还有 $((total - 10)) 个模型"
        fi
    else
        echo "  (安装jq以查看模型详情)"
    fi
}

# 模型调用测试
test_chat() {
    local cr_port="$1"
    local msg="${CHAT_MSG:-1+1等于几？}"
    
    echo "=== 模型调用测试 ==="
    echo "  消息: $msg"
    echo "  模型: free"
    echo ""
    
    local response=$(curl -s -X POST "http://localhost:$cr_port/v1/chat/completions" \
        -H "Content-Type: application/json" \
        -d "{\"model\":\"free\",\"messages\":[{\"role\":\"user\",\"content\":\"$msg\"}]}" \
        --max-time 30 2>/dev/null)
    
    if [ -z "$response" ]; then
        echo "  响应: ❌ 请求失败或超时"
        return 1
    fi
    
    # 提取响应内容
    local content=""
    if command -v jq &> /dev/null; then
        content=$(echo "$response" | jq -r '.choices[0].message.content // empty' 2>/dev/null)
    fi
    
    if [ -n "$content" ]; then
        echo "  响应: $content"
    else
        echo "  响应: (无响应内容)"
        echo "  原始响应: ${response:0:200}..."
    fi
}

# 全面测试
test_full() {
    local agent_id="$1"
    local gw_port="$2"
    local cr_port="$3"
    
    test_health "$agent_id" "$gw_port" "$cr_port"
    echo ""
    test_models "$cr_port"
    echo ""
    test_chat "$cr_port"
}

# ============ 主入口 ============
main() {
    parse_args "$@"
    
    if [ -z "$AGENT_ID" ]; then
        echo "[ERROR] 必须指定 --agent-id"
        echo "用法: $0 --agent-id <ID> [--health|--models|--chat <msg>|--full]"
        exit 1
    fi
    
    # 获取Agent端口
    local gw_port=$(get_agent_port "$AGENT_ID" "gateway_port")
    local cr_port=$(get_agent_port "$AGENT_ID" "clawrouter_port")
    
    if [ -z "$gw_port" ] || [ -z "$cr_port" ]; then
        echo "[ERROR] Agent $AGENT_ID 未找到或配置不完整"
        exit 1
    fi
    
    echo "=========================================="
    echo "  测试 Agent: $AGENT_ID"
    echo "  Gateway: $gw_port | ClawRouter: $cr_port"
    echo "=========================================="
    echo ""
    
    case "$TEST_TYPE" in
        health) test_health "$AGENT_ID" "$gw_port" "$cr_port" ;;
        models) test_models "$cr_port" ;;
        chat) test_chat "$cr_port" ;;
        full) test_full "$AGENT_ID" "$gw_port" "$cr_port" ;;
    esac
    
    echo ""
    echo "=========================================="
}

main "$@"
