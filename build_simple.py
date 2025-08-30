#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简单构建脚本 - 用于GitHub Actions
"""

import os
import sys
import subprocess
import platform

def run_command(cmd):
    """运行命令并显示输出"""
    print(f"🔧 执行命令: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, 
                              capture_output=False, text=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 命令执行失败: {e}")
        return False

def build_simple():
    """使用简单的PyInstaller命令构建"""
    print("🔨 开始简单构建...")
    
    # 基本的PyInstaller命令
    if platform.system() == "Windows":
        # Windows使用分号作为路径分隔符
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name=WoPanWeb",
            "--add-data=templates;templates",
            "--add-data=static;static",
            "--add-data=README_WEB.md;.",
            "--hidden-import=flask",
            "--hidden-import=requests",
            "--hidden-import=Crypto.Cipher.AES",
            "--hidden-import=Crypto.Util.Padding",
            "--hidden-import=werkzeug",
            "--hidden-import=jinja2",
            "--hidden-import=markupsafe",
            "--hidden-import=itsdangerous",
            "--hidden-import=click",
            "--console",
            "--clean",
            "main.py"
        ]
    else:
        # Unix系统使用冒号作为路径分隔符
        cmd = [
            "pyinstaller",
            "--onefile",
            "--name=WoPanWeb",
            "--add-data=templates:templates",
            "--add-data=static:static",
            "--add-data=README_WEB.md:.",
            "--hidden-import=flask",
            "--hidden-import=requests",
            "--hidden-import=Crypto.Cipher.AES",
            "--hidden-import=Crypto.Util.Padding",
            "--hidden-import=werkzeug",
            "--hidden-import=jinja2",
            "--hidden-import=markupsafe",
            "--hidden-import=itsdangerous",
            "--hidden-import=click",
            "--console",
            "--clean",
            "main.py"
        ]
    
    cmd_str = " ".join(cmd)
    return run_command(cmd_str)

def main():
    print("🚀 简单构建工具")
    print("=" * 50)
    
    print(f"💻 系统: {platform.system()}")
    print(f"🐍 Python: {sys.version}")
    
    # 检查文件
    required_files = ["main.py", "wopan_web.py", "templates", "static"]
    for file in required_files:
        if os.path.exists(file):
            print(f"✅ {file}")
        else:
            print(f"❌ {file} 不存在")
            return False
    
    # 构建
    if build_simple():
        print("🎉 构建成功！")
        
        # 检查输出
        if os.path.exists("dist"):
            print("📁 dist目录内容:")
            for item in os.listdir("dist"):
                print(f"  - {item}")
        
        return True
    else:
        print("❌ 构建失败")
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
