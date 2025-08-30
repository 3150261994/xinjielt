#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
发布脚本 - 创建GitHub Release
"""

import os
import sys
import json
import subprocess
import zipfile
import tarfile
from datetime import datetime

def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"🔧 执行命令: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(result.stdout.strip())
        return True, result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False, str(e)

def get_version():
    """获取版本号"""
    # 尝试从git tag获取版本
    success, output = run_command("git describe --tags --abbrev=0")
    if success and output:
        return output
    
    # 如果没有tag，使用日期作为版本
    return f"v{datetime.now().strftime('%Y.%m.%d')}"

def create_release_notes():
    """创建发布说明"""
    version = get_version()
    
    notes = f"""# 联通网盘 Web 版 {version}

## 🎉 功能特性

- 🌐 **现代化Web界面** - 基于Bootstrap 5的响应式设计
- 📁 **文件浏览** - 支持文件夹导航和面包屑
- ⬆️ **多种上传方式**:
  - 单文件上传
  - 多文件批量上传
  - 文件夹上传（保持目录结构）
  - 拖拽上传
- ⬇️ **文件下载** - 获取直链下载文件
- 🗂️ **文件管理** - 创建文件夹、删除文件
- 📱 **跨平台支持** - Windows、macOS、Linux
- 🚀 **一键启动** - 双击即用，无需安装

## 📦 下载说明

请根据你的操作系统下载对应版本：

- **Windows 64位**: `WoPanWeb-windows-x64.zip`
- **macOS Intel**: `WoPanWeb-macos-x64.tar.gz`
- **macOS Apple Silicon**: `WoPanWeb-macos-arm64.tar.gz`
- **Linux 64位**: `WoPanWeb-linux-x64.tar.gz`

## 🚀 使用方法

1. 下载对应平台的压缩包
2. 解压到任意目录
3. 双击运行可执行文件
4. 程序会自动打开浏览器
5. 输入联通网盘Token开始使用

## ⚠️ 注意事项

- 首次运行可能需要几秒钟启动时间
- 请确保防火墙允许程序访问网络
- Token请妥善保管，不要泄露给他人

## 🐛 问题反馈

如有问题请提交 [Issue](https://github.com/yourusername/wopan-web/issues)
"""
    
    return notes

def create_windows_package():
    """创建Windows发布包"""
    print("📦 创建Windows发布包...")
    
    if not os.path.exists('dist/WoPanWeb.exe'):
        print("❌ 找不到Windows可执行文件")
        return False
    
    package_dir = "release/windows"
    os.makedirs(package_dir, exist_ok=True)
    
    # 复制文件
    import shutil
    shutil.copy2('dist/WoPanWeb.exe', package_dir)
    shutil.copy2('README_WEB.md', package_dir)
    shutil.copy2('LICENSE', package_dir)
    
    # 创建使用说明
    with open(f"{package_dir}/使用说明.txt", "w", encoding="utf-8") as f:
        f.write("""# 联通网盘Web版 - Windows版本

## 快速开始

1. 双击运行 WoPanWeb.exe
2. 程序会自动打开浏览器
3. 输入你的联通网盘Token
4. 开始使用！

## 功能特性

- 文件浏览和下载
- 文件上传（支持拖拽）
- 文件夹上传
- 多文件批量上传
- 文件删除和新建文件夹

## 注意事项

- 首次运行可能需要几秒钟启动时间
- 请确保防火墙允许程序访问网络
- 如果浏览器没有自动打开，请手动访问显示的地址

## 技术支持

如有问题，请访问项目主页获取帮助。
""")
    
    # 创建ZIP包
    zip_path = "release/WoPanWeb-windows-x64.zip"
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(package_dir):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, package_dir)
                zipf.write(file_path, arcname)
    
    print(f"✅ Windows包已创建: {zip_path}")
    return True

def main():
    print("🚀 联通网盘Web版发布工具")
    print("=" * 50)
    
    version = get_version()
    print(f"📋 版本: {version}")
    
    # 创建发布目录
    os.makedirs("release", exist_ok=True)
    
    # 创建Windows包
    if os.path.exists('dist/WoPanWeb.exe'):
        create_windows_package()
    else:
        print("⚠️ 未找到Windows可执行文件，请先运行构建")
    
    # 创建发布说明
    notes = create_release_notes()
    with open("release/RELEASE_NOTES.md", "w", encoding="utf-8") as f:
        f.write(notes)
    
    print("📝 发布说明已创建: release/RELEASE_NOTES.md")
    print("🎉 发布准备完成！")
    print("\n📋 下一步操作:")
    print("1. 将代码推送到GitHub")
    print("2. 创建新的Git标签: git tag v1.0.0")
    print("3. 推送标签: git push origin v1.0.0")
    print("4. GitHub Actions会自动构建多平台版本")
    print("5. 在GitHub上创建Release并上传文件")

if __name__ == '__main__':
    main()
