#!/bin/bash
# macOS版本构建和发布脚本

echo "🍎 准备构建macOS版本..."

# 检查是否有未提交的更改
if [[ -n $(git status -s) ]]; then
    echo "⚠️  检测到未提交的更改，请先提交："
    git status -s
    exit 1
fi

# 获取当前版本号
CURRENT_VERSION=$(git describe --tags --abbrev=0 2>/dev/null || echo "v1.0.0")
echo "📋 当前版本: $CURRENT_VERSION"

# 生成新的macOS版本号
NEW_VERSION="macos-$(date +%Y%m%d-%H%M%S)"
echo "🏷️  新版本号: $NEW_VERSION"

# 创建并推送标签
echo "🚀 创建标签并推送..."
git tag $NEW_VERSION
git push origin $NEW_VERSION

echo "✅ macOS构建已触发！"
echo "📍 查看构建进度: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/actions"
echo "📦 构建完成后，Release将自动创建: https://github.com/$(git config --get remote.origin.url | sed 's/.*github.com[:/]\([^.]*\).*/\1/')/releases"
