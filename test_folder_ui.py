#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件夹上传UI
"""

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import tempfile

def create_test_folder():
    """创建测试文件夹"""
    temp_dir = tempfile.mkdtemp(prefix="test_folder_")
    
    # 创建一些测试文件
    files = [
        "file1.txt",
        "file2.pdf", 
        "subfolder/file3.jpg",
        "subfolder/file4.mp4",
        "subfolder/nested/file5.doc"
    ]
    
    for file_path in files:
        full_path = os.path.join(temp_dir, file_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        
        with open(full_path, 'w') as f:
            f.write(f"Test content for {file_path}")
    
    return temp_dir

def test_folder_selection():
    """测试文件夹选择"""
    print("🧪 测试文件夹选择功能...")
    
    root = tk.Tk()
    root.withdraw()  # 隐藏主窗口
    
    # 创建测试文件夹
    test_folder = create_test_folder()
    print(f"📁 创建测试文件夹: {test_folder}")
    
    # 显示文件夹内容
    print("📋 文件夹内容:")
    for root_dir, dirs, files in os.walk(test_folder):
        level = root_dir.replace(test_folder, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root_dir)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    # 模拟文件夹选择
    print(f"\n🔍 模拟选择文件夹: {os.path.basename(test_folder)}")
    
    # 收集文件列表（模拟upload_folder_to_current_folder的逻辑）
    file_list = []
    for root_dir, dirs, files in os.walk(test_folder):
        for file in files:
            file_full_path = os.path.join(root_dir, file)
            relative_path = os.path.relpath(file_full_path, test_folder)
            file_list.append({
                'full_path': file_full_path,
                'relative_path': relative_path,
                'size': os.path.getsize(file_full_path)
            })
    
    print(f"\n📊 收集到 {len(file_list)} 个文件:")
    total_size = 0
    for file_info in file_list:
        print(f"  {file_info['relative_path']} ({file_info['size']} bytes)")
        total_size += file_info['size']
    
    print(f"\n📈 总大小: {total_size} bytes")
    
    # 显示应该调用的对话框类型
    if len(file_list) > 1:
        print("✅ 应该显示: 文件夹上传进度对话框（多文件列表）")
    else:
        print("⚠️ 应该显示: 单文件上传对话框")
    
    # 清理
    import shutil
    shutil.rmtree(test_folder)
    print(f"🧹 清理测试文件夹")
    
    root.destroy()

def show_folder_selection_dialog():
    """显示文件夹选择对话框"""
    root = tk.Tk()
    root.title("文件夹选择测试")
    root.geometry("400x300")
    
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)
    
    ttk.Label(frame, text="测试文件夹上传功能", font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    result_text = tk.Text(frame, height=10, width=50)
    result_text.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
    
    def select_folder():
        folder_path = filedialog.askdirectory(title="选择要上传的文件夹")
        
        if folder_path:
            result_text.delete(1.0, tk.END)
            result_text.insert(tk.END, f"选择的文件夹: {folder_path}\n\n")
            
            # 分析文件夹
            file_count = 0
            total_size = 0
            
            for root_dir, dirs, files in os.walk(folder_path):
                for file in files:
                    file_path = os.path.join(root_dir, file)
                    relative_path = os.path.relpath(file_path, folder_path)
                    size = os.path.getsize(file_path)
                    
                    result_text.insert(tk.END, f"{relative_path} ({size} bytes)\n")
                    file_count += 1
                    total_size += size
            
            result_text.insert(tk.END, f"\n总计: {file_count} 个文件, {total_size} bytes\n")
            
            if file_count > 1:
                result_text.insert(tk.END, "✅ 应该显示多文件上传界面\n")
            else:
                result_text.insert(tk.END, "⚠️ 只有1个文件，显示单文件界面\n")
    
    ttk.Button(frame, text="选择文件夹", command=select_folder).pack()
    
    root.mainloop()

def main():
    """主函数"""
    print("🚀 文件夹上传UI测试")
    print("=" * 40)
    
    choice = input("选择测试方式:\n1. 自动测试\n2. 手动选择文件夹\n请输入 (1/2): ").strip()
    
    if choice == "1":
        test_folder_selection()
    elif choice == "2":
        show_folder_selection_dialog()
    else:
        print("无效选择")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
