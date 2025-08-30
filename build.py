#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
构建脚本 - 用于打包联通网盘Web版
"""

import os
import sys
import shutil
import subprocess
import platform

def run_command(cmd, cwd=None):
    """运行命令"""
    print(f"🔧 执行命令: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, check=True, 
                              capture_output=True, text=True, encoding='utf-8')
        if result.stdout:
            print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        if e.stdout:
            print(f"标准输出: {e.stdout}")
        if e.stderr:
            print(f"错误输出: {e.stderr}")
        return False

def install_dependencies():
    """安装依赖"""
    print("📦 安装构建依赖...")
    
    # 安装PyInstaller
    if not run_command("pip install pyinstaller"):
        return False
    
    # 安装项目依赖
    if not run_command("pip install -r requirements.txt"):
        return False
    
    return True

def build_executable():
    """构建可执行文件"""
    print("🔨 开始构建可执行文件...")
    
    # 清理之前的构建
    if os.path.exists('dist'):
        shutil.rmtree('dist')
    if os.path.exists('build'):
        shutil.rmtree('build')
    
    # 使用spec文件构建
    if not run_command("pyinstaller build.spec"):
        return False
    
    return True

def create_release_package():
    """创建发布包"""
    print("📦 创建发布包...")
    
    system = platform.system().lower()
    arch = platform.machine().lower()
    
    if arch == 'amd64':
        arch = 'x64'
    elif arch in ['i386', 'i686']:
        arch = 'x86'
    elif arch in ['aarch64', 'arm64']:
        arch = 'arm64'
    
    package_name = f"WoPanWeb-{system}-{arch}"
    package_dir = f"dist/{package_name}"
    
    # 创建发布目录
    if os.path.exists(package_dir):
        shutil.rmtree(package_dir)
    os.makedirs(package_dir)
    
    # 复制可执行文件
    exe_name = "WoPanWeb.exe" if system == "windows" else "WoPanWeb"
    exe_path = f"dist/{exe_name}"
    
    if os.path.exists(exe_path):
        shutil.copy2(exe_path, package_dir)
    else:
        print(f"❌ 找不到可执行文件: {exe_path}")
        return False
    
    # 复制说明文件
    files_to_copy = [
        "README_WEB.md",
        "requirements.txt"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, package_dir)
    
    # 创建启动说明
    start_guide = f"""# 联通网盘Web版 - 使用说明

## 快速开始

1. 双击运行 `{exe_name}`
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
"""
    
    with open(f"{package_dir}/使用说明.txt", "w", encoding="utf-8") as f:
        f.write(start_guide)
    
    print(f"✅ 发布包已创建: {package_dir}")
    return True

def main():
    print("🚀 联通网盘Web版构建工具")
    print("=" * 50)
    
    # 检查Python版本
    if sys.version_info < (3, 7):
        print("❌ 需要Python 3.7或更高版本")
        return
    
    print(f"🐍 Python版本: {sys.version}")
    print(f"💻 系统平台: {platform.system()} {platform.machine()}")
    
    # 安装依赖
    if not install_dependencies():
        print("❌ 依赖安装失败")
        return
    
    # 构建可执行文件
    if not build_executable():
        print("❌ 构建失败")
        return
    
    # 创建发布包
    if not create_release_package():
        print("❌ 发布包创建失败")
        return
    
    print("🎉 构建完成！")
    print("📁 可执行文件位于 dist/ 目录")

if __name__ == '__main__':
    main()
