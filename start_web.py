#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘Web版启动脚本
"""

import os
import sys
import webbrowser
import time
import threading

def check_dependencies():
    """检查依赖是否安装"""
    try:
        import flask
        import requests
        from Crypto.Cipher import AES
        print("✅ 所有依赖已安装")
        return True
    except ImportError as e:
        print(f"❌ 缺少依赖: {e}")
        print("请运行以下命令安装依赖:")
        print("pip install -r requirements.txt")
        return False

def open_browser():
    """延迟打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    webbrowser.open('http://localhost:5000')

def main():
    print("🚀 联通网盘 Web 版启动器")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        input("按回车键退出...")
        return
    
    # 导入并启动Flask应用
    try:
        from wopan_web import app
        
        print("📡 启动Web服务器...")
        print("🌐 访问地址: http://localhost:5000")
        print("💡 提示: 按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 在新线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser)
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动Flask应用
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,  # 生产环境关闭调试模式
            use_reloader=False  # 避免重复启动
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")

if __name__ == '__main__':
    main()
