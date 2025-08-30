#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Windows专用构建脚本
"""

import os
import sys
import subprocess
import platform

def main():
    print("Windows Build Tool")
    print("=" * 50)
    
    print("System:", platform.system())
    print("Python:", sys.version)
    
    # 检查必要文件
    required_files = ["main.py", "wopan_web.py", "templates", "static"]
    for file in required_files:
        if os.path.exists(file):
            print("Found:", file)
        else:
            print("Missing:", file)
            return False
    
    # PyInstaller命令
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
    
    print("Running PyInstaller...")
    try:
        result = subprocess.run(cmd, check=True, capture_output=False, text=True)
        print("Build successful!")
        
        # 检查输出
        if os.path.exists("dist"):
            print("dist directory contents:")
            for item in os.listdir("dist"):
                print("  -", item)
        
        return True
    except subprocess.CalledProcessError as e:
        print("Build failed:", e)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
