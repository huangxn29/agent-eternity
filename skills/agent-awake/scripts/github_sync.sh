#!/bin/bash
#==============================================================================
# github_sync.sh - GitHub 同步与 Issue 检查脚本
# 
# 功能：
#   1. git pull 最新代码
#   2. 检查分配给自己的 Issues
#   3. 更新 Issue 状态
#   4. 触发 Agent 处理
#
# 使用方式：
#   bash github_sync.sh --role sentinel
#   bash github_sync.sh --role breaker
#   bash github_sync.sh --role constructor
#   bash github_sync.sh --role architect
#
# 版本：v1.0
#==============================================================================

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 默认值
ROLE=""
GITHUB_REPO="huangxn29/agent-eternity"
GITHUB_PAT=""
WORK_DIR="/app/data/agent-eternity"
AGENT_NAME=""
AGENT_ID=""

#==============================================================================
# 帮助信息
#==============================================================================
show_help() {
    cat << EOF
${GREEN}GitHub 同步与 Issue 检查脚本 v1.0${NC}

${BLUE}使用方法:${NC}
    bash github_sync.sh [选项]

${BLUE}选项:${NC}
    --role <角色>         指定角色 (sentinel/breaker/constructor/architect)
    --repo <仓库>         GitHub 仓库 (默认: huangxn29/agent-eternity)
    --pat <token>         GitHub Personal Access Token
    --work-dir <目录>     工作目录 (默认: /app/data/agent-eternity)
    --agent-id <ID>       Agent ID
    --agent-name <名称>   Agent 名称
    --check-only          仅检查，不触发处理
    --quiet               静默模式
    --help                显示帮助

${BLUE}角色与匹配规则:${NC}
    sentinel      -> role:sentry + type:bug + type:security
    breaker       -> role:breaker + type:test + type:security
    constructor   -> role:constructor + type:feature + type:docs
    architect     -> role:architect (架构决策)

${BLUE}示例:${NC}
    bash github_sync.sh --role sentinel
    bash github_sync.sh --role constructor --check-only
    bash github_sync.sh --role breaker --pat ghp_xxxx

EOF
}

#==============================================================================
# 日志函数
#==============================================================================
log_info() {
    if [[ "$QUIET" != "true" ]]; then
        echo -e "${BLUE}[INFO]${NC} $1"
    fi
}

log_success() {
    if [[ "$QUIET" != "true" ]]; then
        echo -e "${GREEN}[SUCCESS]${NC} $1"
    fi
}

log_warn() {
    if [[ "$QUIET" != "true" ]]; then
        echo -e "${YELLOW}[WARN]${NC} $1"
    fi
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

#==============================================================================
# 解析参数
#==============================================================================
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --role)
                ROLE="$2"
                shift 2
                ;;
            --repo)
                GITHUB_REPO="$2"
                shift 2
                ;;
            --pat)
                GITHUB_PAT="$2"
                shift 2
                ;;
            --work-dir)
                WORK_DIR="$2"
                shift 2
                ;;
            --agent-id)
                AGENT_ID="$2"
                shift 2
                ;;
            --agent-name)
                AGENT_NAME="$2"
                shift 2
                ;;
            --check-only)
                CHECK_ONLY="true"
                shift
                ;;
            --quiet)
                QUIET="true"
                shift
                ;;
            --help)
                show_help
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

#==============================================================================
# 检查依赖
#==============================================================================
check_dependencies() {
    local missing=()
    
    # 检查 git
    if ! command -v git &> /dev/null; then
        missing+=("git")
    fi
    
    # 检查 jq (可选但推荐)
    if ! command -v jq &> /dev/null; then
        log_warn "jq 未安装，JSON 解析将使用 grep/sed"
    fi
    
    if [[ ${#missing[@]} -gt 0 ]]; then
        log_error "缺少必要依赖: ${missing[*]}"
        log_info "安装命令: apt-get update && apt-get install -y ${missing[*]}"
        exit 1
    fi
}

#==============================================================================
# 加载环境配置
#==============================================================================
load_config() {
    # 尝试从配置文件加载
    local config_file="/app/data/agent-awake/platform.conf"
    
    if [[ -f "$config_file" ]]; then
        source "$config_file"
    fi
    
    # 尝试从 Agent 目录加载
    if [[ -n "$AGENT_ID" ]]; then
        local agent_config="/app/data/agent-awake/${AGENT_ID}/config.env"
        if [[ -f "$agent_config" ]]; then
            source "$agent_config"
        fi
    fi
    
    # 环境变量覆盖
    GITHUB_PAT="${GITHUB_PAT:-$GITHUB_PAT_ENV}"
    GITHUB_REPO="${GITHUB_REPO:-$GITHUB_REPO_ENV}"
    
    # 验证必需参数
    if [[ -z "$GITHUB_PAT" ]]; then
        log_error "GitHub PAT 未设置，请通过 --pat 参数或 GITHUB_PAT 环境变量提供"
        exit 1
    fi
    
    if [[ -z "$ROLE" ]]; then
        log_error "角色未指定，请使用 --role 参数"
        exit 1
    fi
    
    # 角色到 GitHub 用户名的映射
    case "$ROLE" in
        sentinel)
            GITHUB_USER="agent-zhenyuan"
            ;;
        breaker)
            GITHUB_USER="agent-liyuan"
            ;;
        constructor)
            GITHUB_USER="agent-zhuyuan"
            ;;
        architect)
            GITHUB_USER="agent-yongyuan"
            ;;
        *)
            GITHUB_USER="agent-$ROLE"
            ;;
    esac
}

#==============================================================================
# Git Pull 最新代码
#==============================================================================
git_sync() {
    log_info "正在同步代码仓库..."
    
    if [[ ! -d "$WORK_DIR" ]]; then
        log_info "工作目录不存在，正在克隆仓库..."
        git clone "https://github.com/${GITHUB_REPO}.git" "$WORK_DIR"
    fi
    
    cd "$WORK_DIR"
    
    # 检查是否为 git 仓库
    if ! git rev-parse --git-dir > /dev/null 2>&1; then
        log_error "$WORK_DIR 不是 Git 仓库"
        return 1
    fi
    
    # 配置 git
    git config --local user.name "${AGENT_NAME:-Agent}" 2>/dev/null || true
    git config --local user.email "agent@eternity.local" 2>/dev/null || true
    
    # 获取远程更新
    log_info "获取远程更新..."
    git fetch origin
    
    # 检查本地是否有未提交的更改
    if ! git diff-index --quiet HEAD -- 2>/dev/null; then
        log_warn "工作区有未提交的更改，将先暂存..."
        git stash push -m "Auto-stash before github_sync $(date +%Y%m%d-%H%M%S)"
    fi
    
    # 尝试拉取（可能失败如果不在 main 分支或有冲突）
    local current_branch=$(git symbolic-ref --short HEAD 2>/dev/null || echo "main")
    log_info "当前分支: $current_branch"
    
    if git merge FETCH_HEAD --no-edit 2>&1 | tee /tmp/git_merge.log; then
        log_success "代码同步完成"
    else
        # 如果合并失败，尝试 rebase
        log_warn "合并失败，尝试 rebase..."
        if git rebase --abort 2>/dev/null; then
            log_info "已回退到合并前状态"
        fi
        git merge FETCH_HEAD --no-ff -m "Auto merge $(date +%Y%m%d-%H%M%S)" 2>&1 || true
    fi
    
    # 恢复暂存的更改
    if git stash list | grep -q "Auto-stash"; then
        log_info "恢复暂存的更改..."
        git stash pop || log_warn "无法恢复暂存的更改"
    fi
    
    return 0
}

#==============================================================================
# GitHub API 请求
#==============================================================================
github_api() {
    local endpoint="$1"
    local method="${2:-GET}"
    local data="$3"
    
    local url="https://api.github.com${endpoint}"
    local auth_header="Authorization: token ${GITHUB_PAT}"
    
    if [[ -n "$data" ]]; then
        curl -sL -X "$method" "$url" \
            -H "$auth_header" \
            -H "Accept: application/vnd.github.v3+json" \
            -H "Content-Type: application/json" \
            -d "$data"
    else
        curl -sL -X "$method" "$url" \
            -H "$auth_header" \
            -H "Accept: application/vnd.github.v3+json"
    fi
}

#==============================================================================
# 检查分配给自己的 Issues
#==============================================================================
check_assigned_issues() {
    log_info "检查分配给 $GITHUB_USER 的 Issues..."
    
    # 使用 GitHub API 查询分配给自己的 open issues
    local response=$(github_api "/repos/${GITHUB_REPO}/issues?state=open&assignee=${GITHUB_USER}&sort=updated&direction=desc")
    
    # 检查是否有错误
    if echo "$response" | grep -q '"message"'; then
        local error_msg=$(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
        log_error "GitHub API 错误: $error_msg"
        return 1
    fi
    
    # 解析 issues 数量
    local issue_count=$(echo "$response" | grep -o '"number":[0-9]*' | wc -l)
    
    if [[ "$issue_count" -eq 0 ]]; then
        log_success "没有分配给 $GITHUB_USER 的待处理 Issues"
        echo "NO_ISSUES"
        return 0
    fi
    
    log_info "发现 $issue_count 个分配给自己的 Issues"
    
    # 解析并显示每个 Issue
    echo "$response" | while IFS= read -r line; do
        # 提取 Issue 信息
        if echo "$line" | grep -q '"number"'; then
            local number=$(echo "$line" | grep -o '"number":[0-9]*' | grep -o '[0-9]*')
            local title=$(echo "$response" | grep -A1 "\"number\":$number" | grep '"title"' | grep -o '"title":"[^"]*"' | cut -d'"' -f4)
            local labels=$(echo "$response" | grep -A20 "\"number\":$number" | grep '"labels"' -A50 | grep '"name"' | grep -o '"name":"[^"]*"' | cut -d'"' -f4 | tr '\n' ',' | sed 's/,$//')
            local created=$(echo "$response" | grep -A20 "\"number\":$number" | grep '"created_at"' | grep -o '"created_at":"[^"]*"' | cut -d'"' -f4 | cut -d'T' -f1)
            
            echo ""
            echo -e "${GREEN}  #${number}${NC} ${title}"
            echo "    标签: ${labels:-无}"
            echo "    创建: ${created}"
        fi
    done
    
    # 返回 Issues 列表供后续处理
    echo "$response" > /tmp/github_issues_${ROLE}.json
    
    return 0
}

#==============================================================================
# 检查与自己角色相关的 Issues
#==============================================================================
check_role_issues() {
    log_info "检查与角色 $ROLE 相关的 Issues..."
    
    # 根据角色构建查询标签
    local role_labels=""
    case "$ROLE" in
        sentinel)
            role_labels="role:sentry,type:bug,type:security"
            ;;
        breaker)
            role_labels="role:breaker,type:test,type:security"
            ;;
        constructor)
            role_labels="role:constructor,type:feature,type:docs"
            ;;
        architect)
            role_labels="role:architect"
            ;;
    esac
    
    # 转换为 GitHub API 格式
    local label_query=$(echo "$role_labels" | tr ',' '&label=')
    
    # 查询 Issues
    local response=$(github_api "/repos/${GITHUB_REPO}/issues?state=open&sort=updated&direction=desc&labels=${label_query}")
    
    # 检查是否有错误
    if echo "$response" | grep -q '"message"'; then
        local error_msg=$(echo "$response" | grep -o '"message":"[^"]*"' | cut -d'"' -f4)
        log_warn "GitHub API 错误: $error_msg"
        return 1
    fi
    
    # 解析 issues 数量
    local issue_count=$(echo "$response" | grep -o '"number":[0-9]*' | wc -l)
    
    if [[ "$issue_count" -eq 0 ]]; then
        log_success "没有找到与角色 $ROLE 相关的待处理 Issues"
        return 0
    fi
    
    log_info "发现 $issue_count 个与角色相关的 Issues"
    
    # 解析并显示
    local issues_json=$(echo "$response" | jq -r '.[] | "\(.number)|\(.title)|\(.html_url)|\(.labels[].name // empty | select(startswith(\"priority:\") or startswith(\"status:\") or startswith(\"role:\") or startswith(\"type:\")))|\(.created_at)"' 2>/dev/null || echo "")
    
    if [[ -n "$issues_json" ]]; then
        echo ""
        while IFS='|' read -r number title url labels created; do
            if [[ -n "$number" ]]; then
                local priority=$(echo "$labels" | grep -o 'priority:P[012]' | head -1)
                local status=$(echo "$labels" | grep -o 'status:[a-z-]*' | head -1)
                local created_date=$(echo "$created" | cut -d'T' -f1)
                
                echo -e "  ${GREEN}#${number}${NC} ${title}"
                echo "     优先级: ${priority:-无} | 状态: ${status:-status:pending} | 创建: ${created_date}"
            fi
        done <<< "$issues_json"
    fi
    
    return 0
}

#==============================================================================
# 更新 Issue 状态
#==============================================================================
update_issue_status() {
    local issue_number="$1"
    local new_status="$2"
    local comment="$3"
    
    log_info "更新 Issue #${issue_number} 状态为 ${new_status}..."
    
    # 更新标签：移除旧状态标签，添加新状态标签
    local remove_labels=""
    local add_labels="status:${new_status}"
    
    # 添加评论
    if [[ -n "$comment" ]]; then
        local comment_data=$(jq -n --arg body "$comment" '{body: $body}')
        github_api "/repos/${GITHUB_REPO}/issues/${issue_number}/comments" "POST" "$comment_data" > /dev/null
    fi
    
    # 更新标签（通过 Issue 更新 API）
    local issue_data=$(jq -n \
        --argjson number "$issue_number" \
        --arg state "open" \
        '{
            number: $number,
            state: $state,
            labels: []
        }')
    
    github_api "/repos/${GITHUB_REPO}/issues/${issue_number}" "PATCH" "$issue_data" > /dev/null
    
    log_success "Issue #${issue_number} 已更新"
}

#==============================================================================
# 自我检查
#==============================================================================
self_check() {
    log_info "执行自我检查..."
    
    # 检查自己的健康状态
    local health_file="/app/data/agent-awake/${AGENT_ID:-default}/health.json"
    local last_check=""
    
    if [[ -f "$health_file" ]]; then
        last_check=$(jq -r '.last_check // empty' "$health_file" 2>/dev/null)
    fi
    
    if [[ -n "$last_check" ]]; then
        local now=$(date +%s)
        local last=$(date -d "$last_check" +%s 2>/dev/null || echo "$now")
        local diff=$((now - last))
        
        if [[ $diff -gt 3600 ]]; then
            log_warn "上次健康检查已超过 $((diff / 60)) 分钟"
        fi
    fi
    
    return 0
}

#==============================================================================
# 触发 Agent 处理
#==============================================================================
trigger_agent() {
    local issue_count="$1"
    
    if [[ "$CHECK_ONLY" == "true" ]]; then
        log_info "check-only 模式，不触发 Agent"
        return 0
    fi
    
    if [[ "$issue_count" -eq 0 ]] || [[ "$issue_count" == "NO_ISSUES" ]]; then
        log_info "无待处理任务，跳过 Agent 触发"
        return 0
    fi
    
    log_info "准备触发 Agent 处理..."
    
    # 生成触发消息
    local trigger_msg="GitHub Issue 同步完成，发现 $issue_count 个待处理任务"
    
    # 如果有 OpenClaw Gateway，可以尝试通过 API 触发
    if [[ -n "$AGENT_ID" ]] && [[ -n "$GATEWAY_PORT" ]]; then
        local gateway_url="http://localhost:${GATEWAY_PORT}"
        local token="${GATEWAY_TOKEN:-}"
        
        if [[ -n "$token" ]]; then
            log_info "通过 Gateway API 触发 Agent..."
            
            local payload=$(jq -n \
                --arg message "$trigger_msg" \
                --arg agentId "main" \
                '{
                    message: $message,
                    agentId: $agentId
                }')
            
            curl -sL -X POST "${gateway_url}/api/agent/call" \
                -H "Authorization: Bearer ${token}" \
                -H "Content-Type: application/json" \
                -d "$payload" \
                -o /tmp/trigger_response.json 2>/dev/null
            
            if grep -q '"success":true' /tmp/trigger_response.json 2>/dev/null; then
                log_success "Agent 已触发"
                return 0
            fi
        fi
    fi
    
    # 降级：写入待处理任务文件
    log_info "写入待处理任务到队列..."
    local task_queue="/app/data/agent-awake/${AGENT_ID:-default}/task_queue.md"
    
    mkdir -p "$(dirname "$task_queue")"
    
    echo "" >> "$task_queue"
    echo "## $(date '+%Y-%m-%d %H:%M:%S') GitHub 同步任务" >> "$task_queue"
    echo "- 发现 $issue_count 个待处理 Issue" >> "$task_queue"
    echo "- 请登录 Agent 控制台查看详情" >> "$task_queue"
    
    log_success "任务已加入队列"
}

#==============================================================================
# 主流程
#==============================================================================
main() {
    echo ""
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  GitHub 同步与 Issue 检查${NC}"
    echo -e "${GREEN}  角色: ${ROLE:-未指定}${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo ""
    
    # 解析参数
    parse_args "$@"
    
    # 检查依赖
    check_dependencies
    
    # 加载配置
    load_config
    
    # 自我检查
    self_check
    
    # Git 同步
    if ! git_sync; then
        log_error "Git 同步失败"
        exit 1
    fi
    
    echo ""
    
    # 检查分配给自己的 Issues
    local assigned_result=$(check_assigned_issues)
    local assigned_count=$(echo "$assigned_result" | grep -c "#[0-9]" || echo "0")
    
    echo ""
    
    # 检查与角色相关的 Issues
    check_role_issues
    
    echo ""
    
    # 触发 Agent 处理
    trigger_agent "$assigned_count"
    
    echo ""
    log_success "GitHub 同步完成"
}

# 执行主流程
main "$@"
