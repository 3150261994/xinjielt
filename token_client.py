#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Token客户端 - 从Token管理器获取token
"""

import requests
import logging
from typing import Optional, Tuple
import time

logger = logging.getLogger(__name__)


class TokenClient:
    """Token客户端"""
    
    def __init__(self, manager_url: str = "http://localhost:8000"):
        self.manager_url = manager_url.rstrip('/')
        self.current_token = None
        self.current_token_name = None
        
    def get_token(self, strategy: str = "round_robin") -> Optional[str]:
        """
        从管理器获取token
        
        Args:
            strategy: 获取策略 ('round_robin' 或 'best')
            
        Returns:
            token字符串，失败时返回None
        """
        try:
            url = f"{self.manager_url}/api/token/get"
            params = {'strategy': strategy}
            
            response = requests.get(url, params=params, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data.get('success'):
                    token_data = data.get('data', {})
                    self.current_token = token_data.get('token')
                    self.current_token_name = token_data.get('name')
                    
                    logger.debug(f"✅ 获取到token: {self.current_token_name}")
                    return self.current_token
                    
            logger.warning(f"⚠️ 获取token失败: {response.status_code}")
            return None
            
        except Exception as e:
            logger.error(f"❌ 连接token管理器失败: {e}")
            return None
    
    def report_success(self, token: str = None):
        """报告token使用成功"""
        token = token or self.current_token
        if not token:
            return
            
        try:
            url = f"{self.manager_url}/api/token/report"
            data = {
                'token': token,
                'success': True
            }
            
            requests.post(url, json=data, timeout=5)
            logger.debug(f"✅ 报告成功: {self.current_token_name}")
            
        except Exception as e:
            logger.debug(f"报告成功失败: {e}")
    
    def report_error(self, error: str, token: str = None):
        """报告token使用错误"""
        token = token or self.current_token
        if not token:
            return
            
        try:
            url = f"{self.manager_url}/api/token/report"
            data = {
                'token': token,
                'success': False,
                'error': error
            }
            
            requests.post(url, json=data, timeout=5)
            logger.debug(f"⚠️ 报告错误: {self.current_token_name} - {error}")
            
        except Exception as e:
            logger.debug(f"报告错误失败: {e}")
    
    def get_with_retry(self, max_retries: int = 3, strategy: str = "round_robin") -> Optional[str]:
        """
        获取token，支持重试
        
        Args:
            max_retries: 最大重试次数
            strategy: 获取策略
            
        Returns:
            token字符串，失败时返回None
        """
        for attempt in range(max_retries):
            token = self.get_token(strategy)
            if token:
                return token
                
            if attempt < max_retries - 1:
                time.sleep(1)  # 等待1秒后重试
                
        return None


# 创建全局token客户端实例
token_client = TokenClient()


def get_token(strategy: str = "round_robin") -> Optional[str]:
    """便捷函数：获取token"""
    return token_client.get_token(strategy)


def report_success(token: str = None):
    """便捷函数：报告成功"""
    token_client.report_success(token)


def report_error(error: str, token: str = None):
    """便捷函数：报告错误"""
    token_client.report_error(error, token)


def get_token_with_retry(max_retries: int = 3, strategy: str = "round_robin") -> Optional[str]:
    """便捷函数：获取token（带重试）"""
    return token_client.get_with_retry(max_retries, strategy)
