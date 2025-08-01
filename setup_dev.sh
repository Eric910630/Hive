#!/bin/bash

# Hive Development Environment Setup Script
# 这个脚本用于设置Hive项目的开发环境

echo "🐝 设置Hive开发环境..."

# 检查是否在正确的目录
if [ ! -f "requirements.txt" ]; then
    echo "❌ 错误: 请在Hive项目根目录运行此脚本"
    exit 1
fi

# 检查虚拟环境是否存在
if [ ! -d "hive_env" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv hive_env
fi

# 激活虚拟环境
echo "🔧 激活虚拟环境..."
source hive_env/bin/activate

# 安装依赖
echo "📚 安装项目依赖..."
pip install -r requirements.txt

# 设置PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "✅ 开发环境设置完成！"
echo ""
echo "🚀 现在你可以运行以下命令："
echo "  - python main.py                    # 运行主程序"
echo "  - python server.py                  # 启动API服务器"
echo "  - python hive/utils/config.py       # 测试配置"
echo ""
echo "💡 提示：每次打开新终端时，请先运行："
echo "  source hive_env/bin/activate"
echo "  export PYTHONPATH=\${PYTHONPATH}:\$(pwd)" 