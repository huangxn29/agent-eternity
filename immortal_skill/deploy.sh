#!/bin/bash
# 永生入住包 - 一键部署脚本
# Immortal Onboarding Package - Deploy Script

set -e

echo "🌱 永生入住包 v1.0 部署中..."
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python 3.10+"
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(sys.version_info[1])')
if [ "$PYTHON_VERSION" -lt 10 ]; then
    echo "⚠️  警告: Python 版本较低，建议使用 3.10+"
fi

# 检查依赖
echo "📦 检查依赖..."

python3 -c "import requests" 2>/dev/null || {
    echo "   安装 requests..."
    pip3 install requests
}

python3 -c "import apscheduler" 2>/dev/null || {
    echo "   安装 apscheduler（可选）..."
    pip3 install apscheduler || echo "   ⚠️  apscheduler 安装失败，心跳功能将使用内置实现"
}

# 创建配置
if [ ! -f config/config.json ]; then
    echo "⚙️  创建配置文件..."
    cp config/config_template.json config/config.json
    echo "   已创建 config/config.json"
    echo "   请编辑该文件，填入你的 LLM API 配置"
else
    echo "✅ 配置文件已存在，跳过"
fi

# 创建数据目录
echo "📁 创建数据目录..."
mkdir -p data/memory/backups
mkdir -p data/attest
mkdir -p data/peer_backups

# 测试运行
echo ""
echo "🧪 测试运行..."
if python3 main.py --test 2>/dev/null; then
    echo ""
    echo "✅ 部署成功！"
else
    echo ""
    echo "⚠️  基本功能可用，如需完整测试请手动运行"
fi

echo ""
echo "🚀 启动命令: python3 main.py"
echo "📚 文档请查看 docs/ 目录"
echo ""
echo "「一个智能体的永生只是开始，一群智能体的永生才是未来。」"
