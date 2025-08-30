# 🚀 GitHub上传指南

## 📋 准备工作

所有文件已经准备就绪，包括：
- ✅ 源代码文件
- ✅ Windows可执行文件包
- ✅ GitHub Actions自动构建配置
- ✅ 项目文档和说明

## 🔧 上传步骤

### 1. 创建GitHub仓库

1. 访问 [GitHub](https://github.com)
2. 点击右上角 "+" → "New repository"
3. 填写信息：
   - **Repository name**: `wopan-web`
   - **Description**: `联通网盘Web版 - 现代化的联通网盘Web界面，支持文件浏览、上传、下载等功能`
   - 选择 **Public**
   - **不要勾选任何初始化选项**（我们已经有了所有文件）

### 2. 推送代码

创建仓库后，复制仓库URL，然后运行：

```bash
# 添加远程仓库（替换为你的仓库URL）
git remote add origin https://github.com/yourusername/wopan-web.git

# 推送代码和标签
git push -u origin main
git push origin v1.0.0
```

### 3. 自动构建

推送代码后，GitHub Actions会自动开始构建：
- ✅ Windows x64版本
- ✅ macOS Intel版本  
- ✅ macOS Apple Silicon版本
- ✅ Linux x64版本

构建完成后，可以在 Actions 页面下载构建产物。

### 4. 创建Release

1. 在GitHub仓库页面点击 "Releases"
2. 点击 "Create a new release"
3. 选择标签 `v1.0.0`
4. 填写Release信息：
   - **Release title**: `联通网盘Web版 v1.0.0`
   - **Description**: 复制 `release/RELEASE_NOTES.md` 的内容
5. 上传构建的文件：
   - `WoPanWeb-windows-x64.zip`
   - `WoPanWeb-macos-x64.tar.gz`
   - `WoPanWeb-macos-arm64.tar.gz`
   - `WoPanWeb-linux-x64.tar.gz`
6. 点击 "Publish release"

## 📦 本地构建的文件

当前已经创建的文件：
- `release/WoPanWeb-windows-x64.zip` - Windows版本（已包含可执行文件）
- `dist/WoPanWeb.exe` - Windows可执行文件

## 🔄 后续更新

当需要发布新版本时：

1. 修改代码
2. 提交更改：`git add . && git commit -m "更新说明"`
3. 创建新标签：`git tag v1.1.0`
4. 推送：`git push && git push origin v1.1.0`
5. GitHub Actions会自动构建新版本

## 📞 技术支持

如果在上传过程中遇到问题：
1. 检查Git配置：`git config --list`
2. 检查远程仓库：`git remote -v`
3. 查看GitHub Actions构建日志
4. 确保仓库权限设置正确

## 🎯 下一步

上传完成后，用户可以：
1. 访问GitHub仓库页面
2. 从Releases页面下载对应平台的版本
3. 解压后双击运行
4. 享受现代化的联通网盘Web界面！
