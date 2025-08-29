#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
演示文件夹上传功能的界面
"""

import tkinter as tk
from tkinter import ttk
import time
import threading
import random

class FolderUploadDemo:
    """文件夹上传演示"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("文件夹上传功能演示")
        self.root.geometry("800x600")
        
        self.setup_ui()
    
    def setup_ui(self):
        """设置UI"""
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 标题
        title_label = ttk.Label(frame, text="📁 文件夹上传功能演示", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # 说明
        desc_text = """
这个演示展示了文件夹上传功能的界面特性：

✅ 实时显示每个文件的上传状态
✅ 成功的文件会在3秒后自动消失
✅ 失败的文件用红字保留，显示错误信息
✅ 总体进度条显示整体上传进度
✅ 支持取消和关闭操作

点击下面的按钮开始演示：
        """
        
        desc_label = ttk.Label(frame, text=desc_text.strip(), justify=tk.LEFT)
        desc_label.pack(pady=(0, 20))
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack()
        
        demo_btn = ttk.Button(btn_frame, text="🚀 开始演示", 
                             command=self.start_demo, 
                             style="Accent.TButton")
        demo_btn.pack(side=tk.LEFT, padx=(0, 10))
        
        real_btn = ttk.Button(btn_frame, text="📂 打开真实程序", 
                             command=self.open_real_program)
        real_btn.pack(side=tk.LEFT)
    
    def start_demo(self):
        """开始演示"""
        # 创建模拟的文件列表
        demo_files = [
            {'relative_path': 'document.pdf', 'size': 1024*1024*2},
            {'relative_path': 'images/photo1.jpg', 'size': 1024*500},
            {'relative_path': 'images/photo2.png', 'size': 1024*800},
            {'relative_path': 'videos/demo.mp4', 'size': 1024*1024*50},
            {'relative_path': 'code/main.py', 'size': 1024*10},
            {'relative_path': 'code/utils.py', 'size': 1024*5},
            {'relative_path': 'data/config.json', 'size': 1024*2},
            {'relative_path': 'readme.txt', 'size': 1024*1},
        ]
        
        self.show_demo_upload_dialog("演示文件夹", demo_files)
    
    def show_demo_upload_dialog(self, folder_name: str, file_list: list):
        """显示演示上传对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"上传文件夹 - {folder_name}")
        dialog.geometry("800x600")
        dialog.resizable(True, True)
        
        dialog.transient(self.root)
        dialog.grab_set()
        
        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        # 文件夹信息
        info_frame = ttk.LabelFrame(frame, text="文件夹信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))
        
        total_size = sum(f['size'] for f in file_list)
        
        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)
        
        ttk.Label(info_grid, text="文件夹:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=folder_name).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Label(info_grid, text="文件数量:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=str(len(file_list))).grid(row=0, column=3, sticky=tk.W)
        
        ttk.Label(info_grid, text="总大小:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=self.format_file_size(total_size)).grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Label(info_grid, text="上传到:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text="根目录").grid(row=1, column=3, sticky=tk.W)
        
        # 总体进度
        progress_frame = ttk.LabelFrame(frame, text="总体进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))
        
        overall_progress_var = tk.DoubleVar()
        overall_progress_bar = ttk.Progressbar(progress_frame, variable=overall_progress_var, maximum=100)
        overall_progress_bar.pack(fill=tk.X, pady=(0, 5))
        
        overall_status_var = tk.StringVar(value="准备上传...")
        overall_status_label = ttk.Label(progress_frame, textvariable=overall_status_var)
        overall_status_label.pack(anchor=tk.W)
        
        # 文件列表
        list_frame = ttk.LabelFrame(frame, text="文件上传状态", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)
        
        # 创建Treeview显示文件列表
        columns = ("status", "progress", "size")
        file_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=12)
        
        # 设置列标题
        file_tree.heading("#0", text="文件路径")
        file_tree.heading("status", text="状态")
        file_tree.heading("progress", text="进度")
        file_tree.heading("size", text="大小")
        
        # 设置列宽
        file_tree.column("#0", width=300, minwidth=200)
        file_tree.column("status", width=120, minwidth=80)
        file_tree.column("progress", width=80, minwidth=60)
        file_tree.column("size", width=100, minwidth=80)
        
        # 添加滚动条
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=file_tree.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=file_tree.xview)
        file_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)
        
        file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))
        
        # 初始化文件列表
        file_items = {}
        for file_info in file_list:
            item_id = file_tree.insert("", "end", 
                                     text=file_info['relative_path'],
                                     values=("等待中", "0%", self.format_file_size(file_info['size'])),
                                     tags=("waiting",))
            file_items[file_info['relative_path']] = item_id
        
        # 配置标签颜色
        file_tree.tag_configure("waiting", foreground="gray")
        file_tree.tag_configure("uploading", foreground="blue")
        file_tree.tag_configure("success", foreground="green")
        file_tree.tag_configure("failed", foreground="red")
        
        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)
        
        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)
        
        close_btn = ttk.Button(btn_frame, text="关闭", command=dialog.destroy, state=tk.DISABLED)
        close_btn.pack(side=tk.RIGHT, padx=(0, 5))
        
        # 开始演示上传
        def demo_upload():
            uploaded = 0
            failed = 0
            
            for i, file_info in enumerate(file_list):
                relative_path = file_info['relative_path']
                item_id = file_items[relative_path]
                
                # 模拟上传过程
                dialog.after(i * 1000, lambda p=relative_path, id=item_id: file_tree.item(id, values=("上传中", "0%", self.format_file_size(file_info['size'])), tags=("uploading",)))
                dialog.after(i * 1000, lambda p=relative_path: overall_status_var.set(f"正在上传: {p}"))
                
                # 模拟进度更新
                for progress in [25, 50, 75, 100]:
                    dialog.after(i * 1000 + progress * 5, lambda p=progress, id=item_id: file_tree.item(id, values=("上传中", f"{p}%", self.format_file_size(file_info['size']))))
                
                # 随机决定成功或失败
                will_succeed = random.random() > 0.2  # 80%成功率
                
                if will_succeed:
                    # 成功
                    dialog.after(i * 1000 + 500, lambda id=item_id: file_tree.item(id, values=("✅ 成功", "100%", self.format_file_size(file_info['size'])), tags=("success",)))
                    # 3秒后移除
                    dialog.after(i * 1000 + 3500, lambda id=item_id: self.safe_delete_item(file_tree, id))
                    uploaded += 1
                else:
                    # 失败
                    error_msgs = ["网络超时", "文件过大", "权限不足", "磁盘空间不足", "文件名包含特殊字符"]
                    error_msg = random.choice(error_msgs)
                    dialog.after(i * 1000 + 500, lambda id=item_id, msg=error_msg: file_tree.item(id, values=(f"❌ {msg}", "0%", self.format_file_size(file_info['size'])), tags=("failed",)))
                    failed += 1
                
                # 更新总体进度
                progress = ((i + 1) / len(file_list)) * 100
                dialog.after(i * 1000 + 600, lambda p=progress: overall_progress_var.set(p))
                dialog.after(i * 1000 + 600, lambda u=uploaded, f=failed, t=i+1: overall_status_var.set(f"已处理 {t}/{len(file_list)} 个文件 (成功: {u}, 失败: {f})"))
            
            # 完成
            dialog.after(len(file_list) * 1000 + 1000, lambda: cancel_btn.config(state=tk.DISABLED))
            dialog.after(len(file_list) * 1000 + 1000, lambda: close_btn.config(state=tk.NORMAL))
            dialog.after(len(file_list) * 1000 + 1000, lambda: overall_status_var.set(f"演示完成！成功: {uploaded}, 失败: {failed}"))
        
        threading.Thread(target=demo_upload, daemon=True).start()
    
    def safe_delete_item(self, tree, item_id):
        """安全删除树项目"""
        try:
            tree.delete(item_id)
        except:
            pass  # 忽略错误
    
    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"
    
    def open_real_program(self):
        """打开真实程序"""
        try:
            import subprocess
            import sys
            subprocess.Popen([sys.executable, "wopan_gui.py"])
        except Exception as e:
            tk.messagebox.showerror("错误", f"无法启动程序: {e}")
    
    def run(self):
        """运行演示"""
        self.root.mainloop()

def main():
    """主函数"""
    demo = FolderUploadDemo()
    demo.run()

if __name__ == "__main__":
    main()
