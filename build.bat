@echo off
chcp 65001 >nul
echo 🚀 联通网盘GUI程序打包工具
echo ================================

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo ✅ Python检查通过

REM 检查源文件
if not exist "wopan_gui.py" (
    echo ❌ 未找到源文件 wopan_gui.py
    pause
    exit /b 1
)

echo ✅ 源文件检查通过

REM 安装依赖
echo 📦 安装依赖包...
pip install requests pycryptodome pyinstaller

REM 构建exe
echo 🔨 开始构建exe文件...
pyinstaller --onefile --windowed --name="联通网盘下载器" --hidden-import=tkinter --hidden-import=tkinter.ttk --hidden-import=tkinter.messagebox --hidden-import=tkinter.filedialog --hidden-import=tkinter.scrolledtext wopan_gui.py

if errorlevel 1 (
    echo ❌ 构建失败
    pause
    exit /b 1
)

echo ✅ 构建成功！

REM 创建发布目录
if exist "release" rmdir /s /q "release"
mkdir "release"

REM 复制文件
copy "dist\联通网盘下载器.exe" "release\"

REM 创建说明文件
echo # 联通网盘下载器 > "release\使用说明.txt"
echo. >> "release\使用说明.txt"
echo ## 使用方法 >> "release\使用说明.txt"
echo 1. 运行程序 >> "release\使用说明.txt"
echo 2. 输入Token >> "release\使用说明.txt"
echo 3. 点击连接 >> "release\使用说明.txt"
echo 4. 浏览文件并获取下载链接 >> "release\使用说明.txt"

echo.
echo 🎉 打包完成！
echo 📁 文件位置: release\联通网盘下载器.exe
echo.
pause
