@echo off
chcp 65001 >nul
echo 🚀 启动联通网盘统一服务...

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 未找到Python，请先安装Python 3.7+
    pause
    exit /b 1
)

echo ✅ Python检查通过

REM 检查依赖
echo 🔍 检查依赖库...
python -c "import flask, requests, Crypto" >nul 2>&1
if errorlevel 1 (
    echo ⚠️ 缺少依赖库，正在安装...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ❌ 依赖安装失败
        pause
        exit /b 1
    )
    echo ✅ 依赖安装完成
) else (
    echo ✅ 依赖检查通过
)

REM 检查配置文件
if not exist "tokens.json" (
    echo ⚠️ 未找到tokens.json，创建默认配置...
    echo {> tokens.json
    echo   "tokens": [>> tokens.json
    echo     {>> tokens.json
    echo       "token": "c4be61c9-3566-4d18-becd-d99f3d0e949e",>> tokens.json
    echo       "name": "主Token",>> tokens.json
    echo       "is_active": true>> tokens.json
    echo     }>> tokens.json
    echo   ]>> tokens.json
    echo }>> tokens.json
    echo ✅ 默认配置已创建
)

echo ==================================================
echo 🌐 服务信息:
echo    地址: http://localhost:8000
echo    用户名: admin
echo    密码: 3150261994
echo ==================================================

REM 启动服务
echo 🚀 启动服务...
python simple_unified_service.py

pause
