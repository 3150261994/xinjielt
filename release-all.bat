@echo off
echo 🚀 准备构建Windows和macOS版本...

REM 检查Git状态
git status --porcelain > nul 2>&1
if errorlevel 1 (
    echo ❌ 请确保在Git仓库中运行此脚本
    pause
    exit /b 1
)

REM 检查是否有未提交的更改
for /f %%i in ('git status --porcelain') do (
    echo ⚠️  检测到未提交的更改，请先提交所有更改
    git status -s
    pause
    exit /b 1
)

REM 获取当前日期时间作为版本号
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%"
set "NEW_VERSION=v%YYYY%.%MM%.%DD%-%HH%%Min%"

echo 🏷️  新版本号: %NEW_VERSION%
echo.

REM 确认发布
set /p confirm="确认创建新版本并触发构建? (y/N): "
if /i not "%confirm%"=="y" (
    echo 取消发布
    pause
    exit /b 0
)

REM 创建并推送标签
echo 🚀 创建标签并推送...
git tag %NEW_VERSION%
git push origin %NEW_VERSION%

if errorlevel 1 (
    echo ❌ 推送失败
    pause
    exit /b 1
)

echo.
echo ✅ 跨平台构建已触发！
echo 📍 查看构建进度: https://github.com/3150261994/xinjielt/actions
echo 📦 构建完成后，Release将自动创建: https://github.com/3150261994/xinjielt/releases
echo.
echo 🎯 将同时构建:
echo    - Windows版本: WoPanWeb-windows-x64.zip
echo    - macOS版本: WoPanWeb-macos-x64.tar.gz
echo.

pause
