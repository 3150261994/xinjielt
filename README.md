# 联通网盘管理器

一个功能强大的联通网盘文件管理工具，支持文件上传、下载、文件夹管理等功能。

## ✨ 功能特性

- 🔐 **安全登录**: 支持Token登录
- 📁 **文件管理**: 浏览、创建、删除文件夹
- 📤 **文件上传**: 支持单文件和多文件上传
- 📂 **文件夹上传**: 支持整个文件夹上传，自动创建目录结构
- 🚀 **并发上传**: 多文件同时上传，提升效率
- 📊 **进度显示**: 实时显示上传进度
- 🔗 **下载链接**: 获取文件下载链接
- 💾 **本地缓存**: 智能缓存，提升响应速度

## 🖥️ 支持平台

- ✅ **Windows** (Windows 10/11)
- ✅ **macOS** (macOS 10.14+)
- ✅ **Linux** (Ubuntu 18.04+)

## 📦 下载安装

### 方式一：下载预编译版本

1. 访问 [Releases](../../releases) 页面
2. 下载对应平台的文件：
   - **Windows**: `联通网盘管理器.exe`
   - **macOS**: `联通网盘管理器-Mac.dmg`
   - **Linux**: `联通网盘管理器-Linux`

### 方式二：从源码运行

```bash
# 克隆项目
git clone https://github.com/yourusername/wopan-manager.git
cd wopan-manager

# 安装依赖
pip install -r requirements.txt

# 运行程序
python wopan_gui.py
```

## 🚀 使用方法

1. **获取Token**:
   - 登录联通网盘网页版
   - 按F12打开开发者工具
   - 在Network标签页找到API请求
   - 复制请求头中的Token

2. **连接网盘**:
   - 启动程序
   - 输入Token
   - 点击"连接"按钮

3. **管理文件**:
   - 浏览文件夹
   - 上传文件或文件夹
   - 创建新文件夹
   - 获取下载链接

## 🔧 开发构建

### 本地开发

```bash
# 安装开发依赖
pip install -r requirements.txt

# 运行程序
python wopan_gui.py
```

### 构建可执行文件

```bash
# 生成构建配置
python build_config.py

# 使用PyInstaller构建
pyinstaller 联通网盘管理器.spec
```

### 自动构建（推荐）

本项目使用GitHub Actions自动构建多平台版本：

1. Fork本项目
2. 推送代码到GitHub
3. 在Actions页面查看构建进度
4. 下载构建好的应用

## 📋 系统要求

### Windows
- Windows 10 或更高版本
- 至少 100MB 可用空间

### macOS
- macOS 10.14 (Mojave) 或更高版本
- 至少 100MB 可用空间

### Linux
- Ubuntu 18.04 或更高版本
- 至少 100MB 可用空间

## 🐛 问题反馈

如果遇到问题，请：

1. 查看 [常见问题](../../wiki/FAQ)
2. 搜索 [已知问题](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🤝 贡献

欢迎贡献代码！请查看 [贡献指南](CONTRIBUTING.md) 了解详情。

## 📞 联系方式

- 项目主页: https://github.com/yourusername/wopan-manager
- 问题反馈: https://github.com/yourusername/wopan-manager/issues

## 🙏 致谢

感谢所有贡献者和用户的支持！

---

⭐ 如果这个项目对您有帮助，请给个Star支持一下！
