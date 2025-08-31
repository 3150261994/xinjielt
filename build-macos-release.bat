@echo off
echo 🍎 准备构建macOS版本...

REM 检查是否有未提交的更改
git status --porcelain > temp_status.txt
for /f %%i in (temp_status.txt) do (
    echo ⚠️  检测到未提交的更改，请先提交：
    git status -s
    del temp_status.txt
    pause
    exit /b 1
)
del temp_status.txt

REM 获取当前时间作为版本号
for /f "tokens=2 delims==" %%a in ('wmic OS Get localdatetime /value') do set "dt=%%a"
set "YY=%dt:~2,2%" & set "YYYY=%dt:~0,4%" & set "MM=%dt:~4,2%" & set "DD=%dt:~6,2%"
set "HH=%dt:~8,2%" & set "Min=%dt:~10,2%" & set "Sec=%dt:~12,2%"
set "NEW_VERSION=macos-%YYYY%%MM%%DD%-%HH%%Min%%Sec%"

echo 🏷️  新版本号: %NEW_VERSION%

REM 创建并推送标签
echo 🚀 创建标签并推送...
git tag %NEW_VERSION%
git push origin %NEW_VERSION%

echo ✅ macOS构建已触发！
echo 📍 查看构建进度: https://github.com/3150261994/xinjielt/actions
echo 📦 构建完成后，Release将自动创建: https://github.com/3150261994/xinjielt/releases

pause
