#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mac版本打包脚本
注意：此脚本需要在Mac系统上运行
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class MacAppBuilder:
    """Mac应用打包器"""
    
    def __init__(self):
        self.app_name = "联通网盘管理器"
        self.main_script = "wopan_gui.py"
        self.build_dir = Path("build_mac")
        self.dist_dir = Path("dist_mac")
        
    def check_environment(self):
        """检查环境"""
        print("🔍 检查Mac打包环境...")
        
        if sys.platform != "darwin":
            print("❌ 此脚本只能在Mac系统上运行")
            print("💡 建议使用GitHub Actions或在Mac设备上运行")
            return False
        
        # 检查PyInstaller
        try:
            import PyInstaller
            print("✅ PyInstaller已安装")
        except ImportError:
            print("❌ PyInstaller未安装")
            print("💡 运行: pip install pyinstaller")
            return False
        
        # 检查主脚本
        if not Path(self.main_script).exists():
            print(f"❌ 主脚本 {self.main_script} 不存在")
            return False
        
        print("✅ 环境检查通过")
        return True
    
    def create_requirements(self):
        """创建requirements.txt"""
        print("📝 创建requirements.txt...")
        
        requirements = [
            "requests>=2.28.0",
            "cryptography>=3.4.8",
            "tkinter",  # 通常内置
            "Pillow>=8.3.0",  # 如果使用图片
        ]
        
        with open("requirements.txt", "w") as f:
            f.write("\n".join(requirements))
        
        print("✅ requirements.txt已创建")
    
    def create_app_icon(self):
        """创建应用图标"""
        print("🎨 创建应用图标...")
        
        # 如果没有图标，创建一个简单的
        icon_path = Path("app_icon.icns")
        if not icon_path.exists():
            print("⚠️  未找到app_icon.icns，将使用默认图标")
            # 这里可以添加创建默认图标的代码
        else:
            print("✅ 找到应用图标")
        
        return icon_path if icon_path.exists() else None
    
    def build_app(self):
        """构建Mac应用"""
        print("🔨 开始构建Mac应用...")
        
        # 清理之前的构建
        if self.build_dir.exists():
            shutil.rmtree(self.build_dir)
        if self.dist_dir.exists():
            shutil.rmtree(self.dist_dir)
        
        # PyInstaller命令
        cmd = [
            "pyinstaller",
            "--onefile",           # 单文件模式
            "--windowed",          # 无控制台窗口
            "--name", self.app_name,
            "--distpath", str(self.dist_dir),
            "--workpath", str(self.build_dir),
            "--clean",             # 清理临时文件
        ]
        
        # 添加图标
        icon_path = self.create_app_icon()
        if icon_path:
            cmd.extend(["--icon", str(icon_path)])
        
        # 添加数据文件
        data_files = [
            "*.py",
            "*.md",
            "*.txt"
        ]
        
        for pattern in data_files:
            for file_path in Path(".").glob(pattern):
                if file_path.name != self.main_script:  # 排除主脚本
                    cmd.extend(["--add-data", f"{file_path}:."])
        
        # 添加主脚本
        cmd.append(self.main_script)
        
        print(f"🚀 执行命令: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print("✅ 应用构建成功")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ 构建失败: {e}")
            print(f"错误输出: {e.stderr}")
            return False
    
    def create_dmg(self):
        """创建DMG安装包"""
        print("📦 创建DMG安装包...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        if not app_path.exists():
            print("❌ 应用文件不存在，无法创建DMG")
            return False
        
        dmg_dir = Path("dmg_temp")
        dmg_dir.mkdir(exist_ok=True)
        
        try:
            # 复制应用到临时目录
            shutil.copytree(app_path, dmg_dir / f"{self.app_name}.app")
            
            # 创建应用程序链接
            applications_link = dmg_dir / "Applications"
            if not applications_link.exists():
                os.symlink("/Applications", applications_link)
            
            # 创建DMG
            dmg_path = self.dist_dir / f"{self.app_name}.dmg"
            cmd = [
                "hdiutil", "create",
                "-volname", self.app_name,
                "-srcfolder", str(dmg_dir),
                "-ov",
                "-format", "UDZO",
                str(dmg_path)
            ]
            
            subprocess.run(cmd, check=True)
            print(f"✅ DMG创建成功: {dmg_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ DMG创建失败: {e}")
            return False
        finally:
            # 清理临时目录
            if dmg_dir.exists():
                shutil.rmtree(dmg_dir)
    
    def optimize_app(self):
        """优化应用"""
        print("⚡ 优化应用...")
        
        app_path = self.dist_dir / f"{self.app_name}.app"
        if not app_path.exists():
            return False
        
        # 设置执行权限
        executable_path = app_path / "Contents" / "MacOS" / self.app_name
        if executable_path.exists():
            os.chmod(executable_path, 0o755)
            print("✅ 设置执行权限")
        
        # 创建Info.plist（如果需要自定义）
        info_plist_path = app_path / "Contents" / "Info.plist"
        if info_plist_path.exists():
            print("✅ Info.plist已存在")
        
        return True
    
    def build(self):
        """完整构建流程"""
        print("🚀 开始Mac应用打包流程")
        print("=" * 50)
        
        # 检查环境
        if not self.check_environment():
            return False
        
        # 创建依赖文件
        self.create_requirements()
        
        # 构建应用
        if not self.build_app():
            return False
        
        # 优化应用
        self.optimize_app()
        
        # 创建DMG
        self.create_dmg()
        
        print("\n🎉 Mac应用打包完成！")
        print(f"📁 输出目录: {self.dist_dir.absolute()}")
        
        # 显示文件信息
        app_path = self.dist_dir / f"{self.app_name}.app"
        dmg_path = self.dist_dir / f"{self.app_name}.dmg"
        
        if app_path.exists():
            size = self.get_dir_size(app_path)
            print(f"📱 应用大小: {size:.1f} MB")
        
        if dmg_path.exists():
            size = dmg_path.stat().st_size / (1024 * 1024)
            print(f"📦 DMG大小: {size:.1f} MB")
        
        return True
    
    def get_dir_size(self, path):
        """获取目录大小"""
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total_size += os.path.getsize(filepath)
        return total_size / (1024 * 1024)  # MB

def main():
    """主函数"""
    builder = MacAppBuilder()
    
    print("🍎 联通网盘管理器 - Mac版本打包工具")
    print("=" * 50)
    
    if len(sys.argv) > 1 and sys.argv[1] == "--help":
        print("使用方法:")
        print("  python build_mac.py          # 完整打包")
        print("  python build_mac.py --help   # 显示帮助")
        return
    
    success = builder.build()
    
    if success:
        print("\n✅ 打包成功！")
        print("\n📋 接下来的步骤:")
        print("1. 测试应用是否正常运行")
        print("2. 如果需要分发，考虑代码签名")
        print("3. 上传到云存储或发布平台")
    else:
        print("\n❌ 打包失败！")
        print("请检查错误信息并重试")

if __name__ == "__main__":
    main()
