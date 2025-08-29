#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试文件夹上传功能
"""

import os
import tempfile
import shutil

def create_test_folder_structure():
    """创建测试文件夹结构"""
    # 创建临时目录
    temp_dir = tempfile.mkdtemp(prefix="wopan_test_")
    
    # 创建测试文件夹结构
    test_folder = os.path.join(temp_dir, "测试文件夹")
    os.makedirs(test_folder)
    
    # 创建子文件夹
    sub_folder1 = os.path.join(test_folder, "子文件夹1")
    sub_folder2 = os.path.join(test_folder, "子文件夹2")
    nested_folder = os.path.join(sub_folder1, "嵌套文件夹")
    
    os.makedirs(sub_folder1)
    os.makedirs(sub_folder2)
    os.makedirs(nested_folder)
    
    # 创建测试文件
    files_to_create = [
        (test_folder, "根目录文件.txt", "这是根目录的文件"),
        (sub_folder1, "子文件夹1文件.txt", "这是子文件夹1的文件"),
        (sub_folder2, "子文件夹2文件.txt", "这是子文件夹2的文件"),
        (nested_folder, "嵌套文件.txt", "这是嵌套文件夹的文件"),
        (test_folder, "README.md", "# 测试文件夹\n\n这是一个测试文件夹结构"),
    ]
    
    for folder, filename, content in files_to_create:
        file_path = os.path.join(folder, filename)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
    
    print(f"✅ 创建测试文件夹结构: {test_folder}")
    print("📁 文件夹结构:")
    for root, dirs, files in os.walk(test_folder):
        level = root.replace(test_folder, '').count(os.sep)
        indent = ' ' * 2 * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = ' ' * 2 * (level + 1)
        for file in files:
            print(f"{subindent}{file}")
    
    return test_folder

def test_folder_structure_parsing():
    """测试文件夹结构解析"""
    print("🧪 测试文件夹结构解析...")
    
    test_folder = create_test_folder_structure()
    
    try:
        # 模拟收集文件列表的过程
        file_list = []
        for root, dirs, files in os.walk(test_folder):
            for file in files:
                file_full_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_full_path, test_folder)
                file_list.append({
                    'full_path': file_full_path,
                    'relative_path': relative_path,
                    'size': os.path.getsize(file_full_path)
                })
        
        print(f"\n📋 收集到 {len(file_list)} 个文件:")
        total_size = 0
        for file_info in file_list:
            print(f"  {file_info['relative_path']} ({file_info['size']} bytes)")
            total_size += file_info['size']
        
        print(f"\n📊 总大小: {total_size} bytes")
        
        # 测试路径解析
        print("\n🔍 测试路径解析:")
        for file_info in file_list:
            relative_path = file_info['relative_path']
            dir_path = os.path.dirname(relative_path)
            
            if dir_path and dir_path != '.':
                path_parts = dir_path.split(os.sep)
                print(f"  {relative_path} -> 需要创建路径: {' -> '.join(path_parts)}")
            else:
                print(f"  {relative_path} -> 根目录文件")
        
        print("✅ 文件夹结构解析测试完成")
        
    finally:
        # 清理测试文件夹
        shutil.rmtree(os.path.dirname(test_folder))
        print(f"🧹 清理测试文件夹: {test_folder}")

def main():
    """主函数"""
    print("🚀 文件夹上传功能测试")
    print("=" * 50)
    
    test_folder_structure_parsing()
    
    print("\n💡 使用提示:")
    print("1. 文件夹上传会自动创建目录结构")
    print("2. 支持多级嵌套文件夹")
    print("3. 会显示详细的上传进度")
    print("4. 失败的文件会跳过，继续上传其他文件")
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
