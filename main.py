#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘Web版主启动文件
用于PyInstaller打包
"""

import os
import sys
import webbrowser
import time
import threading
import socket
from contextlib import closing

# 添加当前目录到Python路径
if hasattr(sys, '_MEIPASS'):
    # PyInstaller打包后的临时目录
    base_path = sys._MEIPASS
else:
    # 开发环境
    base_path = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, base_path)

def find_free_port():
    """查找可用端口"""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
    return port

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
        return False

def open_browser(port):
    """延迟打开浏览器"""
    time.sleep(2)  # 等待服务器启动
    url = f'http://localhost:{port}'
    print(f"🌐 正在打开浏览器: {url}")
    webbrowser.open(url)

def main():
    print("🚀 联通网盘 Web 版")
    print("=" * 50)
    
    # 检查依赖
    if not check_dependencies():
        print("请安装必要的依赖包")
        input("按回车键退出...")
        return
    
    # 查找可用端口
    port = find_free_port()
    
    try:
        # 导入Flask应用
        from wopan_web import app
        
        print(f"📡 启动Web服务器...")
        print(f"🌐 访问地址: http://localhost:{port}")
        print("💡 提示: 按 Ctrl+C 停止服务器")
        print("=" * 50)
        
        # 在新线程中打开浏览器
        browser_thread = threading.Thread(target=open_browser, args=(port,))
        browser_thread.daemon = True
        browser_thread.start()
        
        # 启动Flask应用
        app.run(
            host='127.0.0.1',  # 只监听本地
            port=port,
            debug=False,
            use_reloader=False,
            threaded=True
        )
        
    except KeyboardInterrupt:
        print("\n👋 服务器已停止")
    except Exception as e:
        print(f"❌ 启动失败: {e}")
        input("按回车键退出...")

if __name__ == '__main__':
    main()
