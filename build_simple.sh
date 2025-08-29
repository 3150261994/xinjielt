#!/bin/bash

# 联通网盘管理器 macOS 打包脚本
# 使用方法: chmod +x build_simple.sh && ./build_simple.sh

echo "🍎 联通网盘管理器 macOS 打包工具"
echo "=================================="

# 检查 Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 未找到 Python3，请先安装 Python"
    exit 1
fi

echo "✅ Python 版本: $(python3 --version)"

# 安装依赖
echo "📦 安装构建依赖..."
pip3 install pyinstaller requests cryptography

# 检查主程序文件
if [ ! -f "wopan_gui.py" ]; then
    echo "❌ 未找到 wopan_gui.py 文件"
    exit 1
fi

echo "✅ 找到主程序文件"

# 创建图标（可选）
echo "🎨 创建应用图标..."
cat > create_icon.py << 'EOF'
import tkinter as tk
from tkinter import Canvas

try:
    root = tk.Tk()
    root.withdraw()
    
    canvas = Canvas(root, width=512, height=512, bg='#2E86AB')
    canvas.create_oval(50, 50, 462, 462, fill='#A23B72', outline='#F18F01', width=8)
    canvas.create_text(256, 200, text='联通', font=('Arial', 60, 'bold'), fill='white')
    canvas.create_text(256, 300, text='网盘', font=('Arial', 60, 'bold'), fill='white')
    
    canvas.postscript(file="icon.eps")
    print("✅ 图标创建成功")
    
    root.destroy()
except Exception as e:
    print(f"⚠️ 图标创建失败: {e}")
EOF

python3 create_icon.py
rm create_icon.py

# 使用 PyInstaller 打包
echo "🔨 开始打包应用..."

pyinstaller \
    --name="联通网盘管理器" \
    --windowed \
    --onedir \
    --clean \
    --noconfirm \
    --add-data="*.md:." \
    --hidden-import=tkinter \
    --hidden-import=tkinter.ttk \
    --hidden-import=tkinter.filedialog \
    --hidden-import=tkinter.messagebox \
    --hidden-import=requests \
    --hidden-import=cryptography \
    --hidden-import=json \
    --hidden-import=threading \
    --hidden-import=concurrent.futures \
    --osx-bundle-identifier=com.wopan.manager \
    wopan_gui.py

if [ $? -eq 0 ]; then
    echo "✅ 打包成功!"
    echo "📱 应用位置: dist/联通网盘管理器.app"
    
    # 创建 DMG（可选）
    read -p "是否创建 DMG 安装包? (y/n): " create_dmg
    if [ "$create_dmg" = "y" ] || [ "$create_dmg" = "Y" ]; then
        echo "💿 创建 DMG 安装包..."
        
        mkdir -p dmg_temp
        cp -R "dist/联通网盘管理器.app" dmg_temp/
        
        hdiutil create -volname "联通网盘管理器" -srcfolder dmg_temp -ov -format UDZO "联通网盘管理器-1.0.0.dmg"
        
        rm -rf dmg_temp
        
        if [ $? -eq 0 ]; then
            echo "✅ DMG 创建成功: 联通网盘管理器-1.0.0.dmg"
        else
            echo "❌ DMG 创建失败"
        fi
    fi
    
    # 清理临时文件
    read -p "是否清理构建文件? (y/n): " cleanup
    if [ "$cleanup" = "y" ] || [ "$cleanup" = "Y" ]; then
        echo "🧹 清理临时文件..."
        rm -rf build
        rm -rf __pycache__
        rm -f *.spec
        rm -f icon.eps
        echo "✅ 清理完成"
    fi
    
    echo ""
    echo "🎉 打包完成!"
    echo "📋 使用说明:"
    echo "1. 将 .app 文件拖拽到 Applications 文件夹"
    echo "2. 首次运行时，右键点击应用选择'打开'"
    echo "3. 如果遇到安全提示，请在系统偏好设置中允许"
    echo ""
    echo "📁 文件位置:"
    echo "   应用: dist/联通网盘管理器.app"
    if [ -f "联通网盘管理器-1.0.0.dmg" ]; then
        echo "   安装包: 联通网盘管理器-1.0.0.dmg"
    fi
    
else
    echo "❌ 打包失败"
    exit 1
fi
