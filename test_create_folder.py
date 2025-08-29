#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试创建文件夹功能
"""

import json
from wopan_gui import WoPanAPI

def test_create_folder():
    """测试创建文件夹"""
    print("🧪 测试创建文件夹功能...")
    
    # 获取Token
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
        
        # 测试创建文件夹
        folder_name = "测试文件夹_" + str(int(__import__('time').time()))
        print(f"📂 尝试创建文件夹: {folder_name}")
        
        success, result = api.create_directory("0", "0", folder_name, "")
        
        if success:
            print(f"✅ 文件夹创建成功！ID: {result}")
            
            # 验证文件夹是否真的创建了
            print("🔍 验证文件夹是否创建...")
            success, files = api.get_folder_contents("0")
            if success:
                found = False
                for file in files:
                    if file.is_folder and file.name == folder_name:
                        found = True
                        print(f"✅ 找到创建的文件夹: {file.name} (ID: {file.id})")
                        break
                
                if not found:
                    print("⚠️ 未在文件列表中找到创建的文件夹")
            else:
                print("❌ 验证时获取文件列表失败")
        else:
            print(f"❌ 文件夹创建失败: {result}")
            
            # 尝试分析错误
            if "9999" in result:
                print("\n💡 错误分析:")
                print("- 9999错误通常表示参数问题")
                print("- 可能需要额外的参数如psToken")
                print("- 或者parentDirectoryId格式不正确")
                
                # 尝试不同的参数组合
                print("\n🔄 尝试不同的参数组合...")
                
                # 尝试1: 添加更多参数
                print("尝试1: 添加clientId参数...")
                success2, result2 = test_create_with_different_params(api, folder_name + "_v2")
                if success2:
                    print(f"✅ 方法1成功: {result2}")
                else:
                    print(f"❌ 方法1失败: {result2}")
        
    except Exception as e:
        print(f"💥 测试异常: {e}")

def test_create_with_different_params(api, folder_name):
    """尝试不同的参数组合"""
    # 直接调用底层方法，添加调试信息
    url = f"{api.DEFAULT_BASE_URL}/{api.CHANNEL_WO_HOME}/dispatcher"
    
    headers = api.session.headers.copy()
    headers['Accesstoken'] = api.access_token
    request_header = api._calc_header(api.CHANNEL_WO_HOME, "CreateDirectory")
    
    # 尝试更完整的参数
    param = {
        "spaceType": "0",
        "parentDirectoryId": "0",
        "directoryName": folder_name,
        "clientId": api.DEFAULT_CLIENT_ID,
        "familyId": "",  # 明确设置为空字符串
    }
    
    other = {"secret": True}
    request_body = api._new_body(api.CHANNEL_WO_HOME, param, other)
    
    request_data = {
        "header": request_header,
        "body": request_body
    }
    
    print(f"📤 请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
    
    try:
        response = api.session.post(url, json=request_data, headers=headers, timeout=30)
        
        print(f"📥 响应状态码: {response.status_code}")
        print(f"📥 响应内容: {response.text}")
        
        if response.status_code != 200:
            return False, f"HTTP错误: {response.status_code}"
        
        result = response.json()
        
        if result.get('STATUS') != '200':
            return False, f"API错误: {result.get('STATUS')}"
        
        rsp = result.get('RSP', {})
        if rsp.get('RSP_CODE') != '0000':
            return False, f"响应错误: {rsp.get('RSP_CODE')} - {rsp.get('RSP_DESC', '')}"
        
        return True, "创建成功"
            
    except Exception as e:
        return False, f"请求异常: {e}"

def main():
    """主函数"""
    print("🚀 创建文件夹功能测试")
    print("=" * 40)
    
    test_create_folder()
    
    print("\n🎉 测试完成！")

if __name__ == "__main__":
    main()
