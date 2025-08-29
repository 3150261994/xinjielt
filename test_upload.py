#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试上传功能
"""

import os
import tempfile
from wopan_gui import WoPanAPI

def create_test_file():
    """创建测试文件"""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
        f.write("这是一个测试文件\n")
        f.write("用于测试联通网盘上传功能\n")
        f.write(f"创建时间: {os.path.getctime}")
        return f.name

def test_upload_api():
    """测试上传API"""
    print("🧪 测试上传API功能...")
    
    # 这里需要一个有效的Token
    token = input("请输入您的联通网盘Token: ").strip()
    if not token:
        print("❌ Token不能为空")
        return
    
    try:
        # 创建API实例
        api = WoPanAPI(token)
        print("✅ API实例创建成功")
        
        # 测试连接
        print("🔍 测试连接...")
        success, files = api.get_folder_contents("0")
        if not success:
            print("❌ 连接失败，请检查Token")
            return
        
        print(f"✅ 连接成功，根目录有 {len(files)} 个项目")
        
        # 创建测试文件
        print("📝 创建测试文件...")
        test_file = create_test_file()
        file_name = os.path.basename(test_file)
        file_size = os.path.getsize(test_file)
        
        print(f"✅ 测试文件创建成功: {file_name} ({file_size} bytes)")
        
        # 测试获取上传URL
        print("🔗 获取上传URL...")
        success, upload_info = api.get_upload_url(file_name, file_size, "0")
        
        if success:
            print("✅ 获取上传URL成功")
            print(f"   上传信息: {upload_info}")
            
            # 这里可以继续测试实际上传
            # 但为了安全起见，我们只测试到获取URL
            print("💡 上传URL获取测试完成")
            
        else:
            print(f"❌ 获取上传URL失败: {upload_info}")
        
        # 清理测试文件
        os.unlink(test_file)
        print("🧹 清理测试文件完成")
        
    except Exception as e:
        print(f"💥 测试异常: {e}")

def main():
    """主函数"""
    print("🚀 联通网盘上传功能测试")
    print("=" * 40)
    
    # 检查依赖
    try:
        from wopan_gui import WoPanAPI
        print("✅ 导入WoPanAPI成功")
    except ImportError as e:
        print(f"❌ 导入失败: {e}")
        return
    
    # 测试上传API
    test_upload_api()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
