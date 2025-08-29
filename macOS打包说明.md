# 联通网盘管理器 macOS 打包说明

## 🍎 **系统要求**

- **macOS**: 10.13 (High Sierra) 或更高版本
- **Python**: 3.8 或更高版本
- **Xcode Command Line Tools**: 用于编译某些依赖

## 📦 **打包方法**

### **方法一：自动打包脚本（推荐）**

1. **准备环境**
   ```bash
   # 确保有 Python 3
   python3 --version
   
   # 安装必要依赖
   pip3 install pyinstaller requests cryptography
   ```

2. **运行打包脚本**
   ```bash
   # 给脚本执行权限
   chmod +x build_simple.sh
   
   # 运行打包
   ./build_simple.sh
   ```

3. **完成**
   - 应用文件：`dist/联通网盘管理器.app`
   - 安装包：`联通网盘管理器-1.0.0.dmg`（可选）

### **方法二：Python 打包脚本**

```bash
# 运行 Python 打包脚本
python3 build_macos.py
```

### **方法三：手动打包**

1. **安装 PyInstaller**
   ```bash
   pip3 install pyinstaller
   ```

2. **创建 spec 文件**
   ```bash
   pyinstaller --name="联通网盘管理器" --windowed --onedir wopan_gui.py
   ```

3. **编辑 spec 文件**（可选，添加图标和元数据）

4. **重新打包**
   ```bash
   pyinstaller 联通网盘管理器.spec
   ```

## 🔧 **打包配置详解**

### **PyInstaller 参数说明**

```bash
pyinstaller \
    --name="联通网盘管理器"           # 应用名称
    --windowed                        # 不显示控制台窗口
    --onedir                          # 创建目录分发（推荐）
    --clean                           # 清理缓存
    --noconfirm                       # 不询问覆盖
    --add-data="*.md:."              # 包含文档文件
    --hidden-import=tkinter           # 显式导入 tkinter
    --osx-bundle-identifier=com.wopan.manager  # Bundle ID
    wopan_gui.py                      # 主程序文件
```

### **重要参数选择**

- **`--onedir` vs `--onefile`**:
  - `--onedir`: 创建文件夹，启动更快，推荐
  - `--onefile`: 单个文件，体积大，启动慢

- **`--windowed`**: 
  - GUI 应用必须使用，隐藏控制台窗口

## 🎨 **应用图标**

### **创建图标文件**

1. **准备图标**
   - 格式：PNG 或 ICNS
   - 尺寸：512x512 像素
   - 命名：`app_icon.icns`

2. **转换图标**
   ```bash
   # 从 PNG 转换为 ICNS
   sips -s format icns app_icon.png --out app_icon.icns
   ```

3. **在 spec 文件中指定**
   ```python
   app = BUNDLE(
       coll,
       name='联通网盘管理器.app',
       icon='app_icon.icns',  # 指定图标
       bundle_identifier='com.wopan.manager',
   )
   ```

## 📋 **应用信息配置**

### **Info.plist 配置**

```python
info_plist={
    'CFBundleName': '联通网盘管理器',
    'CFBundleDisplayName': '联通网盘管理器',
    'CFBundleVersion': '1.0.0',
    'CFBundleShortVersionString': '1.0.0',
    'NSHighResolutionCapable': True,           # 支持高分辨率
    'NSRequiresAquaSystemAppearance': False,   # 支持深色模式
    'LSMinimumSystemVersion': '10.13.0',       # 最低系统版本
    'NSHumanReadableCopyright': 'Copyright © 2024 WoPan Team.',
    'CFBundleDocumentTypes': [                 # 支持的文件类型
        {
            'CFBundleTypeName': 'All Files',
            'CFBundleTypeRole': 'Editor',
            'LSItemContentTypes': ['public.data']
        }
    ]
}
```

## 💿 **创建 DMG 安装包**

### **自动创建**
```bash
# 创建 DMG
hdiutil create -volname "联通网盘管理器" \
               -srcfolder "dist/联通网盘管理器.app" \
               -ov -format UDZO \
               "联通网盘管理器-1.0.0.dmg"
```

### **自定义 DMG**
1. 创建临时文件夹
2. 复制应用和其他文件
3. 添加背景图片和快捷方式
4. 创建 DMG

## 🔐 **代码签名（可选）**

### **获取开发者证书**
1. 注册 Apple Developer 账号
2. 下载开发者证书
3. 安装到钥匙串

### **签名应用**
```bash
# 签名应用
codesign --deep --force --verify --verbose \
         --sign "Developer ID Application: Your Name" \
         "dist/联通网盘管理器.app"

# 验证签名
codesign --verify --deep --strict --verbose=2 \
         "dist/联通网盘管理器.app"
```

### **公证应用**
```bash
# 创建 ZIP 包
ditto -c -k --keepParent "dist/联通网盘管理器.app" "联通网盘管理器.zip"

# 提交公证
xcrun altool --notarize-app \
             --primary-bundle-id "com.wopan.manager" \
             --username "your-apple-id@example.com" \
             --password "@keychain:AC_PASSWORD" \
             --file "联通网盘管理器.zip"
```

## 🚀 **分发和安装**

### **分发方式**
1. **DMG 文件**: 最常见，用户体验好
2. **ZIP 压缩包**: 简单直接
3. **App Store**: 需要开发者账号

### **用户安装步骤**
1. 下载 DMG 文件
2. 双击打开 DMG
3. 将应用拖拽到 Applications 文件夹
4. 首次运行时右键选择"打开"

### **解决安全提示**
如果遇到"无法打开，因为它来自身份不明的开发者"：

1. **方法一**: 右键点击应用，选择"打开"
2. **方法二**: 系统偏好设置 > 安全性与隐私 > 通用 > 点击"仍要打开"
3. **方法三**: 终端执行 `xattr -cr /Applications/联通网盘管理器.app`

## 🐛 **常见问题**

### **打包失败**
- 检查 Python 版本和依赖
- 确保所有导入的模块都已安装
- 查看详细错误信息

### **应用无法启动**
- 检查是否缺少依赖库
- 查看控制台日志
- 尝试在终端中直接运行

### **权限问题**
- 确保应用有必要的权限
- 检查文件访问权限
- 可能需要添加权限请求

## 📊 **性能优化**

### **减小应用体积**
- 使用 `--exclude-module` 排除不需要的模块
- 使用 UPX 压缩可执行文件
- 移除不必要的文件

### **提高启动速度**
- 使用 `--onedir` 而不是 `--onefile`
- 优化导入语句
- 延迟加载大型模块

## 🎯 **最佳实践**

1. **测试充分**: 在不同 macOS 版本上测试
2. **版本管理**: 使用语义化版本号
3. **用户体验**: 提供清晰的安装说明
4. **错误处理**: 添加友好的错误提示
5. **自动更新**: 考虑添加自动更新功能

## 📞 **技术支持**

如果在打包过程中遇到问题：
1. 检查系统要求和依赖
2. 查看 PyInstaller 官方文档
3. 搜索相关错误信息
4. 考虑使用虚拟环境隔离依赖
