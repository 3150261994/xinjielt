#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘GUI程序功能演示
"""

import tkinter as tk
from tkinter import ttk, messagebox
import webbrowser

class DemoWindow:
    """演示窗口"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("联通网盘下载器 - 功能演示")
        self.root.geometry("800x600")
        self.root.resizable(True, True)
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        # 主框架
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(main_frame, text="🔑 联通网盘可视化下载器", 
                               font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 功能介绍
        features_frame = ttk.LabelFrame(main_frame, text="✨ 主要功能", padding="15")
        features_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        features_text = """
🔐 Token管理 - 安全保存和管理联通网盘Token
📁 文件浏览 - 可视化浏览网盘文件夹结构  
🔍 多级目录 - 支持深层目录结构浏览
📥 下载链接 - 一键获取文件真实下载地址
📤 文件上传 - 支持文件上传到当前文件夹
📂 文件夹管理 - 创建新文件夹
📋 链接管理 - 复制链接到剪贴板或浏览器打开
🖱️ 右键菜单 - 便捷的右键操作菜单
📊 上传进度 - 实时显示上传进度
💾 配置保存 - 自动保存Token配置
        """
        
        features_label = ttk.Label(features_frame, text=features_text.strip(), 
                                  justify=tk.LEFT, font=("Consolas", 10))
        features_label.pack(anchor=tk.W)
        
        # 使用说明
        usage_frame = ttk.LabelFrame(main_frame, text="📋 使用说明", padding="15")
        usage_frame.pack(fill=tk.X, pady=(0, 20))
        
        usage_text = """
1. 获取Token: 登录联通网盘网页版，从开发者工具中获取Token
2. 启动程序: 运行程序并输入Token
3. 浏览文件: 双击文件夹进入，双击文件获取下载链接
4. 上传文件: 点击"选择文件上传"按钮上传本地文件
5. 管理文件: 使用右键菜单进行各种操作
        """
        
        usage_label = ttk.Label(usage_frame, text=usage_text.strip(), 
                               justify=tk.LEFT, font=("Arial", 9))
        usage_label.pack(anchor=tk.W)
        
        # 按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.pack(fill=tk.X)
        
        # 启动程序按钮
        start_btn = ttk.Button(btn_frame, text="🚀 启动程序", 
                              command=self.start_main_program, 
                              style="Accent.TButton")
        start_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 查看文档按钮
        doc_btn = ttk.Button(btn_frame, text="📖 查看文档", 
                            command=self.open_documentation)
        doc_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 测试功能按钮
        test_btn = ttk.Button(btn_frame, text="🧪 测试功能", 
                             command=self.test_features)
        test_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        # 关于按钮
        about_btn = ttk.Button(btn_frame, text="ℹ️ 关于", 
                              command=self.show_about)
        about_btn.pack(side=tk.RIGHT)
    
    def start_main_program(self):
        """启动主程序"""
        try:
            from wopan_gui import WoPanGUI
            
            # 关闭演示窗口
            self.root.destroy()
            
            # 启动主程序
            app = WoPanGUI()
            app.run()
            
        except ImportError:
            messagebox.showerror("错误", "未找到主程序文件 wopan_gui.py")
        except Exception as e:
            messagebox.showerror("错误", f"启动失败: {e}")
    
    def open_documentation(self):
        """打开文档"""
        try:
            import os
            if os.path.exists("GUI程序说明.md"):
                os.startfile("GUI程序说明.md")
            else:
                messagebox.showinfo("提示", "文档文件不存在")
        except Exception as e:
            messagebox.showerror("错误", f"打开文档失败: {e}")
    
    def test_features(self):
        """测试功能"""
        try:
            import subprocess
            import sys
            
            # 运行测试脚本
            subprocess.Popen([sys.executable, "test_gui.py"])
            messagebox.showinfo("提示", "测试脚本已启动，请查看控制台输出")
            
        except Exception as e:
            messagebox.showerror("错误", f"启动测试失败: {e}")
    
    def show_about(self):
        """显示关于信息"""
        about_text = """
联通网盘可视化下载器 v1.1

🎯 功能特性:
• 可视化文件浏览和管理
• 文件上传和下载
• Token安全管理
• 多级目录支持

🔧 技术栈:
• Python 3.7+
• tkinter GUI框架
• requests HTTP库
• pycryptodome 加密库

📅 更新日期: 2025-08-27

💡 使用提示:
1. 需要有效的联通网盘Token
2. 确保网络连接正常
3. 支持多种文件格式上传下载

🔗 获取Token方法:
登录联通网盘网页版 → F12开发者工具 → 
网络标签 → 找到包含Token的请求头

⚠️ 注意事项:
• 仅供个人学习使用
• 请遵守相关服务条款
• 注意保护个人隐私
        """
        
        messagebox.showinfo("关于程序", about_text.strip())
    
    def run(self):
        """运行演示窗口"""
        self.root.mainloop()

def main():
    """主函数"""
    demo = DemoWindow()
    demo.run()

if __name__ == "__main__":
    main()
