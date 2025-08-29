#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试GUI程序
"""

import sys
import os

def test_imports():
    """测试导入"""
    print("🧪 测试依赖导入...")
    
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox
        print("✅ tkinter 导入成功")
    except ImportError as e:
        print(f"❌ tkinter 导入失败: {e}")
        return False
    
    try:
        import requests
        print("✅ requests 导入成功")
    except ImportError as e:
        print(f"❌ requests 导入失败: {e}")
        return False
    
    try:
        from Crypto.Cipher import AES
        print("✅ pycryptodome 导入成功")
    except ImportError as e:
        print(f"❌ pycryptodome 导入失败: {e}")
        return False
    
    return True

def test_gui_creation():
    """测试GUI创建"""
    print("🖼️ 测试GUI创建...")
    
    try:
        from wopan_gui import WoPanGUI
        
        # 创建GUI实例但不运行
        app = WoPanGUI()
        print("✅ GUI创建成功")
        
        # 销毁窗口
        app.root.destroy()
        return True
        
    except Exception as e:
        print(f"❌ GUI创建失败: {e}")
        return False

def main():
    """主函数"""
    print("🚀 联通网盘GUI程序测试")
    print("=" * 40)
    
    # 检查源文件
    if not os.path.exists("wopan_gui.py"):
        print("❌ 未找到源文件 wopan_gui.py")
        return
    
    # 测试导入
    if not test_imports():
        print("\n💡 请安装缺失的依赖:")
        print("pip install -r requirements_gui.txt")
        return
    
    # 测试GUI创建
    if not test_gui_creation():
        print("\n❌ GUI测试失败")
        return
    
    print("\n🎉 所有测试通过！")
    print("💡 可以运行以下命令:")
    print("   python wopan_gui.py  # 运行GUI程序")
    print("   python build_exe.py  # 打包成exe")

if __name__ == "__main__":
    main()
