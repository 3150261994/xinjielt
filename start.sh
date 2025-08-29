#!/bin/bash
# 联通网盘统一服务启动脚本

echo "🚀 启动联通网盘统一服务..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.7"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python版本过低，需要Python 3.7+，当前版本: $python_version"
    exit 1
fi

echo "✅ Python版本检查通过: $python_version"

# 检查依赖
echo "🔍 检查依赖库..."
if ! python3 -c "import flask, requests, Crypto" 2>/dev/null; then
    echo "⚠️ 缺少依赖库，正在安装..."
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo "❌ 依赖安装失败"
        exit 1
    fi
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖检查通过"
fi

# 检查配置文件
if [ ! -f "tokens.json" ]; then
    echo "⚠️ 未找到tokens.json，创建默认配置..."
    cat > tokens.json << EOF
{
  "tokens": [
    {
      "token": "c4be61c9-3566-4d18-becd-d99f3d0e949e",
      "name": "主Token",
      "is_active": true
    }
  ]
}
EOF
    echo "✅ 默认配置已创建"
fi

# 检查端口
PORT=8000
if lsof -Pi :$PORT -sTCP:LISTEN -t >/dev/null ; then
    echo "⚠️ 端口 $PORT 已被占用"
    read -p "是否使用其他端口？(y/n): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        PORT=8001
        echo "✅ 使用端口 $PORT"
    else
        echo "❌ 启动取消"
        exit 1
    fi
fi

echo "=" * 50
echo "🌐 服务信息:"
echo "   地址: http://localhost:$PORT"
echo "   用户名: admin"
echo "   密码: 3150261994"
echo "=" * 50

# 启动服务
echo "🚀 启动服务..."
if command -v gunicorn &> /dev/null; then
    echo "✅ 使用Gunicorn启动（生产模式）"
    gunicorn -w 4 -b 0.0.0.0:$PORT simple_unified_service:app
else
    echo "✅ 使用Flask启动（开发模式）"
    python3 simple_unified_service.py
fi
