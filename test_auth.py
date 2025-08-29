#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试Token管理器认证功能
"""

import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def test_auth():
    """测试认证功能"""
    base_url = "http://localhost:8000"
    
    logger.info("🧪 测试Token管理器认证功能...")
    
    # 创建session
    session = requests.Session()
    
    # 1. 测试未登录访问主页（应该重定向到登录页）
    logger.info("1️⃣ 测试未登录访问主页...")
    try:
        response = session.get(f"{base_url}/", allow_redirects=False)
        if response.status_code == 302:
            logger.info("✅ 未登录访问被正确重定向到登录页")
        else:
            logger.warning(f"⚠️ 未登录访问响应异常: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ 测试失败: {e}")
    
    # 2. 测试API端点（应该无需认证）
    logger.info("2️⃣ 测试API端点访问...")
    try:
        response = session.get(f"{base_url}/api/token/stats")
        if response.status_code == 200:
            logger.info("✅ API端点无需认证，访问正常")
        else:
            logger.warning(f"⚠️ API端点访问异常: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ API测试失败: {e}")
    
    # 3. 测试错误登录
    logger.info("3️⃣ 测试错误登录...")
    try:
        login_data = {
            'username': 'wrong_user',
            'password': 'wrong_pass'
        }
        response = session.post(f"{base_url}/login", data=login_data)
        if "用户名或密码错误" in response.text:
            logger.info("✅ 错误登录被正确拒绝")
        else:
            logger.warning("⚠️ 错误登录处理异常")
    except Exception as e:
        logger.error(f"❌ 错误登录测试失败: {e}")
    
    # 4. 测试正确登录
    logger.info("4️⃣ 测试正确登录...")
    try:
        login_data = {
            'username': 'admin',
            'password': '3150261994'
        }
        response = session.post(f"{base_url}/login", data=login_data, allow_redirects=False)
        if response.status_code == 302:
            logger.info("✅ 正确登录成功，重定向到主页")
            
            # 5. 测试登录后访问主页
            logger.info("5️⃣ 测试登录后访问主页...")
            response = session.get(f"{base_url}/")
            if response.status_code == 200 and "Token负载均衡管理器" in response.text:
                logger.info("✅ 登录后可以正常访问主页")
                
                # 6. 测试登出
                logger.info("6️⃣ 测试登出...")
                response = session.get(f"{base_url}/logout", allow_redirects=False)
                if response.status_code == 302:
                    logger.info("✅ 登出成功，重定向到登录页")
                else:
                    logger.warning(f"⚠️ 登出响应异常: {response.status_code}")
            else:
                logger.warning("⚠️ 登录后主页访问异常")
        else:
            logger.warning(f"⚠️ 正确登录响应异常: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ 正确登录测试失败: {e}")
    
    logger.info("🎊 认证功能测试完成！")


def test_api_without_auth():
    """测试API在无认证情况下的访问"""
    base_url = "http://localhost:8000"
    
    logger.info("🔧 测试API端点（无需认证）...")
    
    api_endpoints = [
        "/api/token/get",
        "/api/token/stats", 
        "/health"
    ]
    
    for endpoint in api_endpoints:
        try:
            response = requests.get(f"{base_url}{endpoint}", timeout=5)
            logger.info(f"✅ {endpoint}: {response.status_code}")
        except Exception as e:
            logger.error(f"❌ {endpoint}: {e}")


if __name__ == "__main__":
    logger.info("🚀 开始认证测试...")
    
    # 测试认证功能
    test_auth()
    
    # 测试API访问
    test_api_without_auth()
    
    logger.info("🎉 所有测试完成！")
