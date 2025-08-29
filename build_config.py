#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PyInstaller构建配置
"""

import os
import sys
from pathlib import Path

# 应用信息
APP_NAME = "联通网盘管理器"
APP_VERSION = "1.0.0"
APP_DESCRIPTION = "联通网盘文件管理工具"
APP_AUTHOR = "Your Name"

# 构建配置
BUILD_CONFIG = {
    # 基本配置
    'name': APP_NAME,
    'script': 'wopan_gui.py',
    'onefile': True,
    'windowed': True,  # 无控制台窗口
    'clean': True,
    'noconfirm': True,
    
    # 路径配置
    'distpath': 'dist',
    'workpath': 'build',
    'specpath': '.',
    
    # 数据文件
    'datas': [
        # 添加需要的数据文件
        # ('source_path', 'dest_path')
    ],
    
    # 隐藏导入
    'hiddenimports': [
        'tkinter',
        'tkinter.ttk',
        'tkinter.filedialog',
        'tkinter.messagebox',
        'requests',
        'cryptography',
        'json',
        'threading',
        'concurrent.futures',
        'os',
        'sys',
        'time',
    ],
    
    # 排除模块
    'excludes': [
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'PIL',
        'cv2',
        'tensorflow',
        'torch',
    ],
    
    # 优化选项
    'optimize': 2,  # Python字节码优化级别
    'strip': False,  # 不剥离符号（调试用）
    'upx': False,    # 不使用UPX压缩（可能导致问题）
}

# 平台特定配置
if sys.platform == 'darwin':  # macOS
    BUILD_CONFIG.update({
        'icon': 'app_icon.icns' if Path('app_icon.icns').exists() else None,
        'bundle_identifier': 'com.yourcompany.wopan',
    })
elif sys.platform == 'win32':  # Windows
    BUILD_CONFIG.update({
        'icon': 'app_icon.ico' if Path('app_icon.ico').exists() else None,
        'version_file': 'version_info.txt' if Path('version_info.txt').exists() else None,
    })

def generate_spec_file():
    """生成PyInstaller spec文件"""
    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['{BUILD_CONFIG["script"]}'],
    pathex=[],
    binaries=[],
    datas={BUILD_CONFIG["datas"]},
    hiddenimports={BUILD_CONFIG["hiddenimports"]},
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes={BUILD_CONFIG["excludes"]},
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{BUILD_CONFIG["name"]}',
    debug=False,
    bootloader_ignore_signals=False,
    strip={BUILD_CONFIG["strip"]},
    upx={BUILD_CONFIG["upx"]},
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 无控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
'''

    # 添加图标配置
    if BUILD_CONFIG.get('icon'):
        spec_content += f"    icon='{BUILD_CONFIG['icon']}',\n"
    
    spec_content += ")\n"
    
    # macOS特定配置
    if sys.platform == 'darwin':
        spec_content += f'''
app = BUNDLE(
    exe,
    name='{BUILD_CONFIG["name"]}.app',
    icon='{BUILD_CONFIG.get("icon", "")}',
    bundle_identifier='{BUILD_CONFIG.get("bundle_identifier", "com.example.app")}',
    info_plist={{
        'NSHighResolutionCapable': 'True',
        'CFBundleShortVersionString': '{APP_VERSION}',
        'CFBundleVersion': '{APP_VERSION}',
        'CFBundleDisplayName': '{APP_NAME}',
        'NSHumanReadableCopyright': 'Copyright © 2024 {APP_AUTHOR}',
    }},
)
'''
    
    return spec_content

def create_version_info():
    """创建Windows版本信息文件"""
    if sys.platform != 'win32':
        return
    
    version_info = f'''# UTF-8
#
# For more details about fixed file info 'ffi' see:
# http://msdn.microsoft.com/en-us/library/ms646997.aspx
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(1,0,0,0),
    prodvers=(1,0,0,0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          u'040904B0',
          [StringStruct(u'CompanyName', u'{APP_AUTHOR}'),
           StringStruct(u'FileDescription', u'{APP_DESCRIPTION}'),
           StringStruct(u'FileVersion', u'{APP_VERSION}'),
           StringStruct(u'InternalName', u'{APP_NAME}'),
           StringStruct(u'LegalCopyright', u'Copyright © 2024 {APP_AUTHOR}'),
           StringStruct(u'OriginalFilename', u'{APP_NAME}.exe'),
           StringStruct(u'ProductName', u'{APP_NAME}'),
           StringStruct(u'ProductVersion', u'{APP_VERSION}')])
      ]), 
    VarFileInfo([VarStruct(u'Translation', [1033, 1200])])
  ]
)
'''
    
    with open('version_info.txt', 'w', encoding='utf-8') as f:
        f.write(version_info)

def main():
    """主函数"""
    print(f"🔧 生成 {APP_NAME} 构建配置")
    print("=" * 50)
    
    # 生成spec文件
    spec_content = generate_spec_file()
    spec_filename = f"{APP_NAME}.spec"
    
    with open(spec_filename, 'w', encoding='utf-8') as f:
        f.write(spec_content)
    
    print(f"✅ 生成spec文件: {spec_filename}")
    
    # 生成版本信息（Windows）
    if sys.platform == 'win32':
        create_version_info()
        print("✅ 生成版本信息文件: version_info.txt")
    
    print(f"\n📋 构建命令:")
    print(f"pyinstaller {spec_filename}")
    
    print(f"\n📁 输出目录: {BUILD_CONFIG['distpath']}")
    print(f"🎯 目标平台: {sys.platform}")

if __name__ == "__main__":
    main()
