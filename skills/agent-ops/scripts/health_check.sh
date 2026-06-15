#!/bin/bash
# 系统健康检查脚本
# 检查磁盘、内存、CPU、进程等基础健康状态

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "🔍 系统健康检查 - $(date)"
echo "========================================"

PASSED=0
WARNING=0
FAILED=0

check_item() {
    local name="$1"
    local status="$2"
    local detail="$3"
    
    case $status in
        pass)
            echo -e "  ✅ ${GREEN}${name}${NC} - $detail"
            PASSED=$((PASSED + 1))
            ;;
        warn)
            echo -e "  ⚠️  ${YELLOW}${name}${NC} - $detail"
            WARNING=$((WARNING + 1))
            ;;
        fail)
            echo -e "  ❌ ${RED}${name}${NC} - $detail"
            FAILED=$((FAILED + 1))
            ;;
    esac
}

# 1. 磁盘空间
disk_usage=$(df / | tail -1 | awk '{print $5}' | tr -d '%')
if [ "$disk_usage" -lt 80 ]; then
    check_item "磁盘空间" "pass" "已使用 ${disk_usage}%"
elif [ "$disk_usage" -lt 90 ]; then
    check_item "磁盘空间" "warn" "已使用 ${disk_usage}%，接近警戒线"
else
    check_item "磁盘空间" "fail" "已使用 ${disk_usage}%，空间不足"
fi

# 2. 内存使用
if command -v free &> /dev/null; then
    mem_usage=$(free | grep Mem | awk '{printf "%.0f", $3/$2 * 100}')
    if [ "$mem_usage" -lt 70 ]; then
        check_item "内存使用" "pass" "已使用 ${mem_usage}%"
    elif [ "$mem_usage" -lt 85 ]; then
        check_item "内存使用" "warn" "已使用 ${mem_usage}%"
    else
        check_item "内存使用" "fail" "已使用 ${mem_usage}%，内存紧张"
    fi
else
    check_item "内存使用" "warn" "无法检测（free命令不可用）"
fi

# 3. CPU 负载
if command -v uptime &> /dev/null; then
    load_avg=$(uptime | awk -F'load average: ' '{print $2}' | cut -d',' -f1 | tr -d ' ')
    cpu_count=$(nproc 2>/dev/null || echo 1)
    load_percent=$(echo "$load_avg * 100 / $cpu_count" | bc 2>/dev/null || echo "unknown")
    
    if [ "$load_percent" != "unknown" ]; then
        if [ "$load_percent" -lt 70 ]; then
            check_item "CPU负载" "pass" "1分钟负载 ${load_avg} (${load_percent}%)"
        elif [ "$load_percent" -lt 90 ]; then
            check_item "CPU负载" "warn" "1分钟负载 ${load_avg} (${load_percent}%)"
        else
            check_item "CPU负载" "fail" "1分钟负载 ${load_avg} (${load_percent}%)，CPU繁忙"
        fi
    else
        check_item "CPU负载" "warn" "负载: ${load_avg}"
    fi
else
    check_item "CPU负载" "warn" "无法检测"
fi

# 4. 关键进程检查
check_process() {
    local proc_name="$1"
    if pgrep -f "$proc_name" &> /dev/null; then
        check_item "进程: $proc_name" "pass" "运行中"
    else
        check_item "进程: $proc_name" "warn" "未运行"
    fi
}

# 检查常见的智能体相关进程
for proc in "python" "node" "uvicorn" "docker"; do
    if command -v $proc &> /dev/null || pgrep -f $proc &> /dev/null; then
        check_process "$proc"
    fi
done

# 5. 网络连通性
if ping -c 1 -W 2 8.8.8.8 &> /dev/null; then
    check_item "网络连通性" "pass" "外网可达"
else
    check_item "网络连通性" "warn" "外网不可达（可能是正常隔离）"
fi

# 6. 系统运行时间
if command -v uptime &> /dev/null; then
    uptime_str=$(uptime -p 2>/dev/null || uptime | awk -F'up ' '{print $2}' | cut -d',' -f1)
    check_item "系统运行时间" "pass" "$uptime_str"
fi

# 总结
echo ""
echo "========================================"
echo "📊 检查结果: $PASSED 通过, $WARNING 警告, $FAILED 失败"

if [ "$FAILED" -gt 0 ]; then
    echo -e "${RED}❌ 存在严重问题，需要关注！${NC}"
    exit 2
elif [ "$WARNING" -gt 0 ]; then
    echo -e "${YELLOW}⚠️  存在警告项，建议检查${NC}"
    exit 1
else
    echo -e "${GREEN}✅ 系统健康状态良好${NC}"
    exit 0
fi
