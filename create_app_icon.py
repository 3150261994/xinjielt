#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建应用图标
"""

from PIL import Image, ImageDraw, ImageFont
import os

def create_simple_icon():
    """创建一个简单的应用图标"""
    # 创建512x512的图像
    size = 512
    img = Image.new('RGBA', (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    
    # 绘制背景圆形
    margin = 20
    draw.ellipse([margin, margin, size-margin, size-margin], 
                fill=(52, 152, 219, 255),  # 蓝色背景
                outline=(41, 128, 185, 255), width=8)
    
    # 绘制云朵图标
    cloud_color = (255, 255, 255, 255)
    
    # 主云朵
    center_x, center_y = size // 2, size // 2
    cloud_size = 120
    
    # 绘制云朵的几个圆形组成
    circles = [
        (center_x - 40, center_y, 60),
        (center_x + 20, center_y, 50),
        (center_x - 10, center_y - 30, 45),
        (center_x + 30, center_y - 20, 40),
        (center_x - 30, center_y - 15, 35),
    ]
    
    for x, y, r in circles:
        draw.ellipse([x-r, y-r, x+r, y+r], fill=cloud_color)
    
    # 绘制上传箭头
    arrow_color = (52, 152, 219, 255)
    arrow_x = center_x
    arrow_y = center_y + 40
    arrow_size = 30
    
    # 箭头主体
    draw.rectangle([arrow_x - 8, arrow_y - arrow_size, 
                   arrow_x + 8, arrow_y + 10], fill=arrow_color)
    
    # 箭头头部
    arrow_points = [
        (arrow_x, arrow_y - arrow_size - 15),
        (arrow_x - 20, arrow_y - arrow_size + 5),
        (arrow_x + 20, arrow_y - arrow_size + 5)
    ]
    draw.polygon(arrow_points, fill=arrow_color)
    
    return img

def save_icon_formats(img):
    """保存不同格式的图标"""
    # 保存PNG格式
    img.save('app_icon.png', 'PNG')
    print("✅ 创建 app_icon.png")
    
    # 创建ICO格式（Windows）
    ico_sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    ico_images = []
    for size in ico_sizes:
        ico_img = img.resize(size, Image.Resampling.LANCZOS)
        ico_images.append(ico_img)
    
    ico_images[0].save('app_icon.ico', format='ICO', 
                      sizes=[(img.width, img.height) for img in ico_images])
    print("✅ 创建 app_icon.ico (Windows)")
    
    # 创建ICNS格式（Mac）
    try:
        # 需要安装 pillow-icns: pip install pillow-icns
        img.save('app_icon.icns', format='ICNS')
        print("✅ 创建 app_icon.icns (Mac)")
    except Exception as e:
        print(f"⚠️  无法创建ICNS格式: {e}")
        print("💡 可以使用在线转换工具将PNG转换为ICNS")

def main():
    """主函数"""
    print("🎨 创建联通网盘管理器应用图标")
    print("=" * 40)
    
    try:
        # 创建图标
        icon = create_simple_icon()
        
        # 保存不同格式
        save_icon_formats(icon)
        
        print("\n🎉 图标创建完成！")
        print("📁 生成的文件:")
        print("  - app_icon.png (通用)")
        print("  - app_icon.ico (Windows)")
        print("  - app_icon.icns (Mac, 如果支持)")
        
        print("\n💡 使用方法:")
        print("1. 将图标文件上传到GitHub仓库")
        print("2. 重新触发GitHub Actions构建")
        print("3. 新版本将包含自定义图标")
        
    except ImportError:
        print("❌ 需要安装PIL库: pip install Pillow")
    except Exception as e:
        print(f"❌ 创建图标失败: {e}")

if __name__ == "__main__":
    main()
