#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘统一服务 - Token管理 + Web API
集成Token负载均衡和文件下载API

Author: AI Assistant
Date: 2025-08-27
"""

import json
import logging
import time
import threading
import requests
import hashlib
import secrets
import base64
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify, session, redirect, url_for
from dataclasses import dataclass
from functools import wraps
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


# 认证配置
AUTH_CONFIG = {
    'username': 'admin',
    'password': '3150261994',
    'session_timeout': 3600  # 1小时
}


@dataclass
class TokenInfo:
    """Token信息"""
    token: str
    name: str
    is_active: bool = True
    last_used: datetime = None
    success_count: int = 0
    error_count: int = 0
    last_error: str = ""
    last_check: datetime = None
    
    def to_dict(self):
        return {
            'token': self.token,
            'name': self.name,
            'is_active': self.is_active,
            'last_used': self.last_used.isoformat() if self.last_used else None,
            'success_count': self.success_count,
            'error_count': self.error_count,
            'last_error': self.last_error,
            'last_check': self.last_check.isoformat() if self.last_check else None,
            'success_rate': self.get_success_rate()
        }
    
    def get_success_rate(self) -> float:
        """获取成功率"""
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100


class TokenManager:
    """Token负载均衡管理器"""
    
    def __init__(self):
        self.tokens: List[TokenInfo] = []
        self.current_index = 0
        self.lock = threading.Lock()
        
        # 加载配置
        self.load_tokens()
        
    def load_tokens(self):
        """从配置文件加载tokens"""
        try:
            with open('tokens.json', 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            self.tokens = []
            for token_config in config.get('tokens', []):
                token_info = TokenInfo(
                    token=token_config['token'],
                    name=token_config.get('name', f'Token-{len(self.tokens)+1}'),
                    is_active=token_config.get('is_active', True)
                )
                self.tokens.append(token_info)
                
            logger.info(f"✅ 加载了 {len(self.tokens)} 个token")
            
        except FileNotFoundError:
            # 创建默认配置
            default_config = {
                "tokens": [
                    {
                        "token": "c4be61c9-3566-4d18-becd-d99f3d0e949e",
                        "name": "主Token",
                        "is_active": True
                    }
                ]
            }
            
            with open('tokens.json', 'w', encoding='utf-8') as f:
                json.dump(default_config, f, indent=2, ensure_ascii=False)
                
            logger.info("📝 创建了默认token配置文件")
            self.load_tokens()
            
        except Exception as e:
            logger.error(f"❌ 加载token配置失败: {e}")
    
    def get_best_token(self) -> Optional[TokenInfo]:
        """获取最佳token"""
        with self.lock:
            active_tokens = [t for t in self.tokens if t.is_active]
            if not active_tokens:
                return None
            
            # 按成功率和使用时间排序
            def score_token(token: TokenInfo) -> float:
                success_rate = token.get_success_rate()
                
                if token.last_used is None:
                    return success_rate + 10
                
                time_since_use = (datetime.now() - token.last_used).total_seconds() / 60
                return success_rate + min(time_since_use * 0.1, 5)
            
            best_token = max(active_tokens, key=score_token)
            best_token.last_used = datetime.now()
            
            return best_token
    
    def report_success(self, token: str):
        """报告token使用成功"""
        with self.lock:
            for t in self.tokens:
                if t.token == token:
                    t.success_count += 1
                    break
    
    def report_error(self, token: str, error: str):
        """报告token使用错误"""
        with self.lock:
            for t in self.tokens:
                if t.token == token:
                    t.error_count += 1
                    t.last_error = error
                    
                    if t.error_count > 5 and t.get_success_rate() < 50:
                        t.is_active = False
                        logger.warning(f"⚠️ Token {t.name} 因错误率过高被暂时禁用")
                    break
    
    def get_stats(self) -> Dict:
        """获取统计信息"""
        with self.lock:
            total_tokens = len(self.tokens)
            active_tokens = len([t for t in self.tokens if t.is_active])
            
            total_success = sum(t.success_count for t in self.tokens)
            total_errors = sum(t.error_count for t in self.tokens)
            
            return {
                'total_tokens': total_tokens,
                'active_tokens': active_tokens,
                'total_requests': total_success + total_errors,
                'total_success': total_success,
                'total_errors': total_errors,
                'overall_success_rate': (total_success / (total_success + total_errors) * 100) if (total_success + total_errors) > 0 else 100,
                'tokens': [t.to_dict() for t in self.tokens]
            }


# 创建全局token管理器
token_manager = TokenManager()

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'wopan-unified-service-secret-key-2025'


def require_web_auth(f):
    """Web界面认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API端点跳过认证
        if request.path.startswith('/api/') or request.path == '/health':
            return f(*args, **kwargs)
            
        # 检查session
        if 'logged_in' not in session or not session['logged_in']:
            if request.path == '/login':
                return f(*args, **kwargs)
            return redirect(url_for('login'))
        
        # 检查session是否过期
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if (datetime.now() - login_time).seconds > AUTH_CONFIG['session_timeout']:
                session.clear()
                return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function


@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == AUTH_CONFIG['username'] and password == AUTH_CONFIG['password']:
            session['logged_in'] = True
            session['login_time'] = datetime.now().isoformat()
            session['username'] = username
            logger.info(f"✅ 用户 {username} 登录成功")
            return redirect(url_for('index'))
        else:
            logger.warning(f"⚠️ 用户 {username} 登录失败")
            return render_login_page("用户名或密码错误")
    
    return render_login_page()


def render_login_page(error_msg=None):
    """渲染登录页面"""
    html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>联通网盘统一服务 - 登录</title>
    <style>
        body {{ font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); margin: 0; padding: 0; height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .login-container {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); width: 100%; max-width: 400px; }}
        .login-header {{ text-align: center; margin-bottom: 30px; }}
        .login-header h1 {{ color: #333; margin: 0; }}
        .login-header p {{ color: #666; margin: 10px 0 0 0; }}
        .form-group {{ margin-bottom: 20px; }}
        .form-group label {{ display: block; margin-bottom: 5px; color: #333; font-weight: bold; }}
        .form-group input {{ width: 100%; padding: 12px; border: 1px solid #ddd; border-radius: 5px; font-size: 16px; box-sizing: border-box; }}
        .form-group input:focus {{ outline: none; border-color: #007bff; box-shadow: 0 0 5px rgba(0,123,255,0.3); }}
        .login-btn {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; font-size: 16px; cursor: pointer; transition: background 0.3s; }}
        .login-btn:hover {{ background: #0056b3; }}
        .error-msg {{ background: #f8d7da; color: #721c24; padding: 10px; border-radius: 5px; margin-bottom: 20px; border: 1px solid #f5c6cb; }}
        .footer {{ text-align: center; margin-top: 20px; color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="login-container">
        <div class="login-header">
            <h1>🔑 联通网盘统一服务</h1>
            <p>Token管理 + Web API</p>
        </div>
        
        {f'<div class="error-msg">{error_msg}</div>' if error_msg else ''}
        
        <form method="POST">
            <div class="form-group">
                <label for="username">用户名</label>
                <input type="text" id="username" name="username" required autocomplete="username">
            </div>
            
            <div class="form-group">
                <label for="password">密码</label>
                <input type="password" id="password" name="password" required autocomplete="current-password">
            </div>
            
            <button type="submit" class="login-btn">登录</button>
        </form>
        
        <div class="footer">
            <p>联通网盘Token负载均衡 + 文件下载API</p>
        </div>
    </div>
</body>
</html>
    """
    return html


@app.route('/logout')
@require_web_auth
def logout():
    """登出"""
    username = session.get('username', 'Unknown')
    session.clear()
    logger.info(f"👋 用户 {username} 已登出")
    return redirect(url_for('login'))


# ==================== 联通网盘API相关类 ====================

class WoPanCrypto:
    """联通网盘加密工具"""

    def __init__(self, client_secret: str = "XFmi9GS2hzk98jGX"):
        self.key = client_secret.encode('utf-8')
        self.iv = b"wNSOYIB1k1DjY5lA"
        self.access_key = None

    def set_access_token(self, token: str):
        """设置访问令牌用于加密"""
        if len(token) >= 16:
            self.access_key = token[:16].encode('utf-8')

    def encrypt(self, content: str, channel: str) -> str:
        """加密内容"""
        key = self.key if channel == "api-user" else self.access_key
        if key is None:
            key = self.key

        try:
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            padded_data = pad(content.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.debug(f"加密失败: {e}")
            return content

    def decrypt(self, encrypted_data: str, channel: str) -> str:
        """解密内容"""
        key = self.key if channel == "api-user" else self.access_key
        if key is None:
            key = self.key

        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            decrypted = cipher.decrypt(encrypted_bytes)
            unpadded = unpad(decrypted, AES.block_size)
            return unpadded.decode('utf-8')
        except Exception as e:
            logger.debug(f"解密失败: {e}")
            return encrypted_data


class WoPanFile:
    """联通网盘文件对象"""

    def __init__(self, data: Dict):
        self.fid = data.get('fid', '')
        self.creator = data.get('creator', '')
        self.preview_url = data.get('previewUrl', '')
        self.space_type = data.get('spaceType', '0')
        self.load_info = data.get('loadInfo', '')
        self.shooting_time = data.get('shootingTime', '')
        self.type = data.get('type', 1)  # 0: 文件夹, 1: 文件
        self.family_id = data.get('familyId', 0)
        self.size = data.get('size', 0)
        self.create_time = data.get('createTime', '')
        self.name = data.get('name', '')
        self.id = data.get('id', '')
        self.thumb_url = data.get('thumbUrl', '')
        self.file_type = data.get('fileType', '')
        self.is_collected = data.get('isCollected', 0)

    @property
    def is_folder(self) -> bool:
        """是否为文件夹"""
        return self.type == 0

    @property
    def formatted_create_time(self) -> str:
        """格式化的创建时间"""
        if len(self.create_time) == 14:  # YYYYMMDDHHMMSS
            try:
                dt = datetime.strptime(self.create_time, '%Y%m%d%H%M%S')
                return dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                return self.create_time
        return self.create_time

    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'id': self.id,
            'fid': self.fid,
            'name': self.name,
            'size': self.size,
            'type': 'folder' if self.is_folder else 'file',
            'create_time': self.formatted_create_time,
            'file_type': self.file_type,
            'thumb_url': self.thumb_url
        }


class WoPanRealTimeAPI:
    """联通网盘实时API"""

    DEFAULT_CLIENT_ID = "1001000021"
    DEFAULT_CLIENT_SECRET = "XFmi9GS2hzk98jGX"
    DEFAULT_BASE_URL = "https://panservice.mail.wo.cn"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
    CHANNEL_WO_HOME = "wohome"

    def __init__(self, access_token: str):
        self.access_token = access_token
        self.crypto = WoPanCrypto(self.DEFAULT_CLIENT_SECRET)
        self.crypto.set_access_token(access_token)

        # 设置session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.DEFAULT_UA,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://pan.wo.cn',
            'Referer': 'https://pan.wo.cn/',
            'Accesstoken': self.access_token
        })

    def _calc_header(self, channel: str, key: str) -> Dict:
        """计算请求头"""
        res_time = int(time.time() * 1000)
        req_seq = random.randint(100000, 108999)
        version = ""

        sign_content = f"{key}{res_time}{req_seq}{channel}{version}"
        sign = hashlib.md5(sign_content.encode()).hexdigest()

        return {
            "key": key,
            "resTime": res_time,
            "reqSeq": req_seq,
            "channel": channel,
            "sign": sign,
            "version": version
        }

    def _new_body(self, channel: str, param: Dict, other: Dict) -> Dict:
        """构建请求体"""
        if not param:
            return other

        param_json = json.dumps(param, separators=(',', ':'))
        encrypted_param = self.crypto.encrypt(param_json, channel)

        body = other.copy()
        body["param"] = encrypted_param
        return body

    def get_folder_contents(self, parent_id: str = "0", space_type: str = "0",
                           page_size: int = 100) -> Tuple[bool, List[WoPanFile]]:
        """获取文件夹内容"""
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"

        headers = self.session.headers.copy()
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "QueryAllFiles")

        param = {
            "spaceType": space_type,
            "parentDirectoryId": parent_id,
            "pageNum": 0,
            "pageSize": page_size,
            "sortRule": 1,
            "clientId": self.DEFAULT_CLIENT_ID
        }

        other = {"secret": True}
        request_body = self._new_body(self.CHANNEL_WO_HOME, param, other)

        request_data = {
            "header": request_header,
            "body": request_body
        }

        try:
            response = self.session.post(url, json=request_data, headers=headers, timeout=30)

            if response.status_code != 200:
                return False, []

            result = response.json()

            if result.get('STATUS') != '200':
                return False, []

            rsp = result.get('RSP', {})
            if rsp.get('RSP_CODE') != '0000':
                return False, []

            data = rsp.get('DATA', '')
            if isinstance(data, str):
                decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)

                try:
                    parsed_data = json.loads(decrypted_text)
                    files_data = parsed_data.get('files', [])
                    files = [WoPanFile(file_data) for file_data in files_data]
                    return True, files
                except json.JSONDecodeError:
                    return False, []
            else:
                return False, []

        except Exception as e:
            logger.error(f"实时请求异常: {e}")
            return False, []

    def find_file_by_name(self, folder_name: str, file_name: str) -> Optional[WoPanFile]:
        """在指定文件夹中查找文件"""
        success, root_files = self.get_folder_contents("0")
        if not success:
            return None

        target_folder = None
        for file in root_files:
            if file.is_folder and file.name == folder_name:
                target_folder = file
                break

        if not target_folder:
            return None

        success, folder_files = self.get_folder_contents(target_folder.id)
        if not success:
            return None

        for file in folder_files:
            if not file.is_folder and file.name == file_name:
                return file

        return None


if __name__ == '__main__':
    logger.info("🚀 启动联通网盘统一服务")
    logger.info("=" * 60)
    logger.info("🔐 登录信息:")
    logger.info(f"   用户名: {AUTH_CONFIG['username']}")
    logger.info(f"   密码: {AUTH_CONFIG['password']}")
    logger.info("=" * 60)
    logger.info("🌐 服务地址: http://localhost:8000")
    logger.info("📋 功能:")
    logger.info("   - Token负载均衡管理")
    logger.info("   - 联通网盘文件下载API")
    logger.info("   - 实时文件列表获取")
    logger.info("=" * 60)
    
    app.run(host='0.0.0.0', port=8000, debug=True)
