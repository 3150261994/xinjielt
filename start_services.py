#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动所有服务的脚本
"""

import subprocess
import time
import sys
import os
import requests
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_service(url, name, timeout=5):
    """检查服务是否运行"""
    try:
        response = requests.get(url, timeout=timeout)
        if response.status_code == 200:
            logger.info(f"✅ {name} 运行正常")
            return True
        else:
            logger.warning(f"⚠️ {name} 响应异常: {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"⚠️ {name} 不可访问: {e}")
        return False


def start_token_manager():
    """启动Token管理器"""
    logger.info("🚀 启动Token管理器...")
    
    # 检查是否已经运行
    if check_service("http://localhost:8000/health", "Token管理器"):
        logger.info("Token管理器已在运行")
        return True
    
    try:
        # 启动Token管理器
        subprocess.Popen([
            sys.executable, "token_manager.py"
        ], cwd=os.getcwd())
        
        # 等待启动
        for i in range(10):
            time.sleep(2)
            if check_service("http://localhost:8000/health", "Token管理器"):
                logger.info("✅ Token管理器启动成功")
                return True
            logger.info(f"等待Token管理器启动... ({i+1}/10)")
        
        logger.error("❌ Token管理器启动超时")
        return False
        
    except Exception as e:
        logger.error(f"❌ 启动Token管理器失败: {e}")
        return False


def start_web_api():
    """启动Web API"""
    logger.info("🚀 启动Web API...")
    
    # 检查是否已经运行
    if check_service("http://localhost:5000/health", "Web API"):
        logger.info("Web API已在运行")
        return True
    
    try:
        # 启动Web API
        subprocess.Popen([
            sys.executable, "wopan_web_api.py"
        ], cwd=os.getcwd())
        
        # 等待启动
        for i in range(10):
            time.sleep(2)
            if check_service("http://localhost:5000/health", "Web API"):
                logger.info("✅ Web API启动成功")
                return True
            logger.info(f"等待Web API启动... ({i+1}/10)")
        
        logger.error("❌ Web API启动超时")
        return False
        
    except Exception as e:
        logger.error(f"❌ 启动Web API失败: {e}")
        return False


def main():
    """主函数"""
    logger.info("🎯 联通网盘服务启动器")
    logger.info("=" * 50)
    
    # 1. 启动Token管理器
    if not start_token_manager():
        logger.error("💥 Token管理器启动失败，退出")
        sys.exit(1)
    
    # 2. 启动Web API
    if not start_web_api():
        logger.error("💥 Web API启动失败，退出")
        sys.exit(1)
    
    # 3. 显示服务状态
    logger.info("\n" + "=" * 60)
    logger.info("🎉 所有服务启动完成！")
    logger.info("=" * 60)
    logger.info("📋 服务地址:")
    logger.info("   Token管理器: http://localhost:8000 (需要登录)")
    logger.info("   Web API:    http://localhost:5000")
    logger.info("=" * 60)
    logger.info("🔐 Token管理器登录信息:")
    logger.info("   用户名: admin")
    logger.info("   密码: 3150261994")
    logger.info("=" * 60)
    logger.info("📊 Token管理器API:")
    logger.info("   GET  /api/token/get     - 获取token")
    logger.info("   GET  /api/token/stats   - 查看统计")
    logger.info("   POST /api/token/add     - 添加token")
    logger.info("   DELETE /api/token/remove - 删除token")
    logger.info("=" * 50)
    logger.info("📊 Web API:")
    logger.info("   GET  /api/download/?url=folder/filename")
    logger.info("   GET  /api/files?folder=name&realtime=true")
    logger.info("   GET  /api/folders?realtime=true")
    logger.info("=" * 50)
    
    # 4. 测试Token获取
    logger.info("🧪 测试Token获取...")
    try:
        response = requests.get("http://localhost:8000/api/token/get", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                token_name = data.get('data', {}).get('name', 'Unknown')
                logger.info(f"✅ Token获取测试成功: {token_name}")
            else:
                logger.warning(f"⚠️ Token获取失败: {data.get('error')}")
        else:
            logger.warning(f"⚠️ Token服务响应异常: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Token获取测试失败: {e}")
    
    # 5. 测试Web API
    logger.info("🧪 测试Web API...")
    try:
        response = requests.get("http://localhost:5000/api/folders?realtime=true", timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                folder_count = data.get('count', 0)
                source = data.get('data', {}).get('source', 'unknown') if isinstance(data.get('data'), dict) else data.get('source', 'unknown')
                logger.info(f"✅ Web API测试成功: 找到{folder_count}个文件夹 (数据源: {source})")
            else:
                logger.warning(f"⚠️ Web API响应失败: {data.get('error')}")
        else:
            logger.warning(f"⚠️ Web API响应异常: {response.status_code}")
    except Exception as e:
        logger.error(f"❌ Web API测试失败: {e}")
    
    logger.info("\n🎊 服务启动完成！按Ctrl+C退出")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n👋 正在退出...")


if __name__ == "__main__":
    main()
