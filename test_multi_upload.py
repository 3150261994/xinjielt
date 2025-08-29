#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试多文件上传功能
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import tempfile
import threading
import time

def create_test_files():
    """创建测试文件"""
    temp_dir = tempfile.mkdtemp(prefix="multi_upload_test_")
    
    files = []
    for i in range(3):
        file_path = os.path.join(temp_dir, f"test_file_{i+1}.txt")
        with open(file_path, 'w') as f:
            f.write(f"This is test file {i+1}\n" * 1000)  # 创建一些内容
        files.append(file_path)
    
    return files

def simulate_upload_with_progress(file_path, progress_callback):
    """模拟上传过程"""
    file_name = os.path.basename(file_path)
    print(f"开始上传: {file_name} (线程: {threading.current_thread().name})")
    
    # 模拟上传进度
    for i in range(11):
        time.sleep(0.2)  # 模拟网络延迟
        progress = i * 10
        progress_callback(progress)
        print(f"{file_name}: {progress}%")
    
    print(f"完成上传: {file_name}")
    return True, "上传成功"

class MultiUploadTest:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("多文件上传测试")
        self.root.geometry("600x400")
        
        self.setup_ui()
    
    def setup_ui(self):
        frame = ttk.Frame(self.root, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)
        
        ttk.Label(frame, text="多文件上传并发测试", font=("Arial", 14, "bold")).pack(pady=(0, 20))
        
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=(0, 20))
        
        ttk.Button(btn_frame, text="创建测试文件并上传", command=self.test_upload).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(btn_frame, text="选择文件上传", command=self.select_files).pack(side=tk.LEFT)
        
        # 日志区域
        self.log_text = tk.Text(frame, height=20)
        self.log_text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(frame, orient=tk.VERTICAL, command=self.log_text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.log_text.configure(yscrollcommand=scrollbar.set)
    
    def log(self, message):
        """添加日志"""
        self.log_text.insert(tk.END, f"{message}\n")
        self.log_text.see(tk.END)
        self.root.update()
    
    def test_upload(self):
        """测试上传"""
        self.log("创建测试文件...")
        files = create_test_files()
        
        self.log(f"创建了 {len(files)} 个测试文件:")
        for file_path in files:
            self.log(f"  - {os.path.basename(file_path)}")
        
        self.upload_files(files)
    
    def select_files(self):
        """选择文件"""
        files = filedialog.askopenfilenames(
            title="选择多个文件进行测试",
            filetypes=[("所有文件", "*.*")]
        )
        
        if files:
            self.log(f"选择了 {len(files)} 个文件:")
            for file_path in files:
                self.log(f"  - {os.path.basename(file_path)}")
            
            self.upload_files(files)
    
    def upload_files(self, files):
        """上传文件"""
        self.log("\n" + "="*50)
        self.log("开始测试并发上传...")
        self.log("="*50)
        
        start_time = time.time()
        
        def upload_thread():
            try:
                import concurrent.futures
                
                completed = 0
                total = len(files)
                
                def upload_single_file(file_path):
                    def progress_callback(progress):
                        self.root.after(0, lambda: self.log(f"{os.path.basename(file_path)}: {progress}%"))
                    
                    return simulate_upload_with_progress(file_path, progress_callback)
                
                # 并发上传
                with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                    futures = [executor.submit(upload_single_file, file_path) for file_path in files]
                    
                    for future in concurrent.futures.as_completed(futures):
                        success, result = future.result()
                        completed += 1
                        
                        self.root.after(0, lambda: self.log(f"✅ 完成 {completed}/{total}: {result}"))
                
                total_time = time.time() - start_time
                self.root.after(0, lambda: self.log(f"\n🎉 全部完成！总耗时: {total_time:.2f}秒"))
                
            except Exception as e:
                self.root.after(0, lambda: self.log(f"❌ 上传失败: {e}"))
        
        threading.Thread(target=upload_thread, daemon=True).start()
    
    def run(self):
        self.root.mainloop()

def main():
    app = MultiUploadTest()
    app.run()

if __name__ == "__main__":
    main()
