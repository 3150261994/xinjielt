#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘GUI程序打包脚本
使用PyInstaller打包成exe文件
"""

import os
import sys
import subprocess
import shutil

def install_requirements():
    """安装依赖"""
    print("📦 安装依赖包...")
    
    requirements = [
        "tkinter",  # 通常内置
        "requests",
        "pycryptodome",
        "pyinstaller"
    ]
    
    for req in requirements:
        try:
            print(f"安装 {req}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", req])
        except subprocess.CalledProcessError:
            print(f"⚠️ {req} 安装失败，可能已经安装或不需要")

def create_icon():
    """创建简单的图标文件"""
    # 这里可以放置图标创建代码，或者使用现有图标
    print("🎨 使用默认图标...")

def build_exe():
    """构建exe文件"""
    print("🔨 开始构建exe文件...")
    
    # PyInstaller命令参数
    cmd = [
        "pyinstaller",
        "--onefile",  # 打包成单个exe文件
        "--windowed",  # 不显示控制台窗口
        "--name=联通网盘下载器",  # exe文件名
        "--icon=icon.ico",  # 图标文件（如果存在）
        "--add-data=wopan_config.json;.",  # 包含配置文件
        "--hidden-import=tkinter",
        "--hidden-import=tkinter.ttk",
        "--hidden-import=tkinter.messagebox",
        "--hidden-import=tkinter.filedialog",
        "--hidden-import=tkinter.scrolledtext",
        "wopan_gui.py"
    ]
    
    try:
        subprocess.check_call(cmd)
        print("✅ 构建成功！")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 构建失败: {e}")
        return False
    except FileNotFoundError:
        print("❌ PyInstaller未找到，请先安装: pip install pyinstaller")
        return False

def create_portable_package():
    """创建便携版包"""
    print("📁 创建便携版包...")
    
    # 创建发布目录
    release_dir = "release"
    if os.path.exists(release_dir):
        shutil.rmtree(release_dir)
    os.makedirs(release_dir)
    
    # 复制exe文件
    exe_path = os.path.join("dist", "联通网盘下载器.exe")
    if os.path.exists(exe_path):
        shutil.copy2(exe_path, release_dir)
        print(f"✅ 复制exe文件到 {release_dir}")
    else:
        print("❌ 未找到exe文件")
        return False
    
    # 创建说明文件
    readme_content = """# 联通网盘下载器

## 使用说明

1. 运行 `联通网盘下载器.exe`
2. 输入您的联通网盘Token
3. 点击"连接"按钮
4. 浏览文件夹，双击文件获取下载链接

## Token获取方法

1. 登录联通网盘网页版
2. 打开浏览器开发者工具(F12)
3. 在网络请求中找到包含Token的请求
4. 复制Token值

## 功能特性

- ✅ 可视化文件浏览
- ✅ 多级目录支持
- ✅ 一键获取下载链接
- ✅ 复制链接到剪贴板
- ✅ 浏览器直接打开
- ✅ 右键菜单操作

## 技术支持

如遇问题，请检查：
1. Token是否有效
2. 网络连接是否正常
3. 防火墙是否阻止程序运行

版本: v1.0
"""
    
    with open(os.path.join(release_dir, "使用说明.txt"), "w", encoding="utf-8") as f:
        f.write(readme_content)
    
    print("✅ 便携版包创建完成！")
    return True

def main():
    """主函数"""
    print("🚀 联通网盘GUI程序打包工具")
    print("=" * 50)
    
    # 检查源文件
    if not os.path.exists("wopan_gui.py"):
        print("❌ 未找到源文件 wopan_gui.py")
        return
    
    # 安装依赖
    install_requirements()
    
    # 创建图标
    create_icon()
    
    # 构建exe
    if build_exe():
        # 创建便携版包
        create_portable_package()
        
        print("\n🎉 打包完成！")
        print("📁 文件位置:")
        print(f"   - exe文件: dist/联通网盘下载器.exe")
        print(f"   - 便携版: release/")
        print("\n💡 提示:")
        print("   - 可以直接运行exe文件")
        print("   - 首次运行需要输入Token")
        print("   - 配置会自动保存")
    else:
        print("\n💥 打包失败！")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()
