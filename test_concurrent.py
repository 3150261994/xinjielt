#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试并发上传功能
"""

import time
import threading
import concurrent.futures

def simulate_upload(file_id, duration):
    """模拟上传过程"""
    print(f"开始上传文件 {file_id}")
    
    for i in range(10):
        time.sleep(duration / 10)
        progress = (i + 1) * 10
        print(f"文件 {file_id}: {progress}%")
    
    print(f"文件 {file_id} 上传完成!")
    return f"文件 {file_id} 成功"

def test_sequential():
    """测试顺序上传"""
    print("=" * 50)
    print("🔄 测试顺序上传")
    print("=" * 50)
    
    start_time = time.time()
    
    files = [("文件1", 2), ("文件2", 2), ("文件3", 2)]
    
    for file_id, duration in files:
        result = simulate_upload(file_id, duration)
        print(f"✅ {result}")
    
    total_time = time.time() - start_time
    print(f"\n⏱️ 顺序上传总耗时: {total_time:.2f}秒")

def test_concurrent():
    """测试并发上传"""
    print("=" * 50)
    print("🚀 测试并发上传")
    print("=" * 50)
    
    start_time = time.time()
    
    files = [("文件1", 2), ("文件2", 2), ("文件3", 2)]
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            # 提交所有任务
            futures = [executor.submit(simulate_upload, file_id, duration) for file_id, duration in files]
            
            # 等待所有任务完成
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                print(f"✅ {result}")
        
        total_time = time.time() - start_time
        print(f"\n⏱️ 并发上传总耗时: {total_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 并发上传失败: {e}")

def test_api_session():
    """测试API会话是否支持并发"""
    import requests
    
    print("=" * 50)
    print("🔍 测试API会话并发")
    print("=" * 50)
    
    def make_request(url, session_id):
        try:
            session = requests.Session()
            response = session.get(url, timeout=10)
            print(f"会话 {session_id}: 状态码 {response.status_code}")
            return f"会话 {session_id} 成功"
        except Exception as e:
            print(f"会话 {session_id}: 失败 - {e}")
            return f"会话 {session_id} 失败"
    
    urls = [
        "https://httpbin.org/delay/1",
        "https://httpbin.org/delay/1", 
        "https://httpbin.org/delay/1"
    ]
    
    start_time = time.time()
    
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(make_request, url, i+1) for i, url in enumerate(urls)]
            
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                print(f"✅ {result}")
        
        total_time = time.time() - start_time
        print(f"\n⏱️ 并发请求总耗时: {total_time:.2f}秒")
        
    except Exception as e:
        print(f"❌ 并发请求失败: {e}")

def main():
    """主函数"""
    print("🧪 并发上传功能测试")
    
    # 测试顺序上传
    test_sequential()
    
    print("\n" + "=" * 50)
    time.sleep(1)
    
    # 测试并发上传
    test_concurrent()
    
    print("\n" + "=" * 50)
    time.sleep(1)
    
    # 测试API并发
    test_api_session()
    
    print("\n🎉 测试完成!")

if __name__ == "__main__":
    main()
