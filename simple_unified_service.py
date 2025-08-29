#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘简化统一服务
Token管理 + 文件下载API 一体化服务

Author: AI Assistant
Date: 2025-08-27
"""

import json
import logging
import time
import requests
import hashlib
import random
import base64
import threading
import os
from datetime import datetime
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
    'session_timeout': 3600
}

@dataclass
class TokenInfo:
    """Token信息"""
    token: str
    name: str
    is_active: bool = True
    success_count: int = 0
    error_count: int = 0
    
    def get_success_rate(self) -> float:
        total = self.success_count + self.error_count
        if total == 0:
            return 100.0
        return (self.success_count / total) * 100

class SimpleTokenManager:
    """简化Token管理器 - 线程安全版本"""

    def __init__(self):
        self.tokens: List[TokenInfo] = []
        self.current_index = 0
        self.lock = threading.RLock()  # 可重入锁，支持并发
        self.load_tokens()
        
    def load_tokens(self):
        """加载tokens"""
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
    
    def get_best_token(self) -> Optional[str]:
        """获取最佳token - 线程安全"""
        with self.lock:
            active_tokens = [t for t in self.tokens if t.is_active]
            if not active_tokens:
                return None

            # 简单轮询
            token = active_tokens[self.current_index % len(active_tokens)]
            self.current_index += 1
            return token.token
    
    def report_success(self, token: str):
        """报告成功 - 线程安全"""
        with self.lock:
            for t in self.tokens:
                if t.token == token:
                    t.success_count += 1
                    break

    def report_error(self, token: str, error: str):
        """报告错误 - 线程安全"""
        with self.lock:
            for t in self.tokens:
                if t.token == token:
                    t.error_count += 1
                    if t.error_count > 10:
                        t.is_active = False
                        logger.warning(f"⚠️ Token {t.name} 被禁用")
                    break

    def add_token(self, token: str, name: str = None) -> bool:
        """添加新token - 线程安全"""
        with self.lock:
            # 检查是否已存在
            for t in self.tokens:
                if t.token == token:
                    return False

            token_info = TokenInfo(
                token=token,
                name=name or f"Token-{len(self.tokens)+1}"
            )
            self.tokens.append(token_info)
            self.save_tokens()

            logger.info(f"✅ 添加新token: {token_info.name}")
            return True

    def remove_token(self, token: str) -> bool:
        """删除token - 线程安全"""
        with self.lock:
            for i, t in enumerate(self.tokens):
                if t.token == token:
                    removed = self.tokens.pop(i)
                    self.save_tokens()
                    logger.info(f"🗑️ 删除token: {removed.name}")
                    return True
            return False

    def save_tokens(self):
        """保存tokens到配置文件"""
        try:
            config = {
                "tokens": [
                    {
                        "token": token.token,
                        "name": token.name,
                        "is_active": token.is_active
                    }
                    for token in self.tokens
                ]
            }

            with open('tokens.json', 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)

        except Exception as e:
            logger.error(f"❌ 保存token配置失败: {e}")

    def get_stats(self) -> Dict:
        """获取统计信息 - 线程安全"""
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
                'tokens': [
                    {
                        'token': t.token,
                        'name': t.name,
                        'is_active': t.is_active,
                        'success_count': t.success_count,
                        'error_count': t.error_count,
                        'success_rate': t.get_success_rate()
                    }
                    for t in self.tokens
                ]
            }

# ==================== 联通网盘API核心类 ====================

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
        headers['Accesstoken'] = self.access_token
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
        """在指定文件夹中查找文件（兼容旧版本）"""
        return self.find_file_by_path([folder_name], file_name)

    def find_file_by_path(self, folder_path: List[str], file_name: str) -> Optional[WoPanFile]:
        """在指定路径中查找文件 - 支持多级目录"""
        current_folder_id = "0"  # 从根目录开始

        # 逐级查找文件夹
        for folder_name in folder_path:
            logger.debug(f"🔍 查找文件夹: {folder_name} (当前ID: {current_folder_id})")

            success, files = self.get_folder_contents(current_folder_id)
            if not success:
                logger.error(f"❌ 获取文件夹内容失败: {current_folder_id}")
                return None

            # 在当前级别查找目标文件夹
            target_folder = None
            for file in files:
                if file.is_folder and file.name == folder_name:
                    target_folder = file
                    break

            if not target_folder:
                logger.warning(f"⚠️ 未找到文件夹: {folder_name}")
                return None

            current_folder_id = target_folder.id
            logger.debug(f"✅ 找到文件夹: {folder_name} (ID: {current_folder_id})")

        # 在最终文件夹中查找文件
        logger.debug(f"🔍 在最终文件夹中查找文件: {file_name} (文件夹ID: {current_folder_id})")
        success, folder_files = self.get_folder_contents(current_folder_id)
        if not success:
            logger.error(f"❌ 获取最终文件夹内容失败: {current_folder_id}")
            return None

        for file in folder_files:
            if not file.is_folder and file.name == file_name:
                logger.info(f"✅ 找到文件: {file_name} (FID: {file.fid})")
                return file

        logger.warning(f"⚠️ 未找到文件: {file_name}")
        return None


class WoPanDownloader:
    """联通网盘下载器"""

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

    def get_download_url_v2(self, fids: List[str]) -> Tuple[bool, any]:
        """获取下载链接V2"""
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"

        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "GetDownloadUrlV2")

        param = {
            "type": "1",
            "fidList": fids,
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
                return False, f"HTTP错误: {response.status_code}"

            result = response.json()

            if result.get('STATUS') != '200':
                return False, f"API错误: {result.get('STATUS')} - {result.get('MSG')}"

            rsp = result.get('RSP', {})
            if rsp.get('RSP_CODE') != '0000':
                return False, f"响应错误: {rsp.get('RSP_CODE')} - {rsp.get('RSP_DESC')}"

            data = rsp.get('DATA', '')
            if isinstance(data, str):
                decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)

                try:
                    parsed_data = json.loads(decrypted_text)
                    return True, parsed_data
                except json.JSONDecodeError as e:
                    return False, f"JSON解析失败: {e}"
            else:
                return False, "未获取到有效数据"

        except Exception as e:
            return False, f"请求异常: {e}"


# 创建全局管理器
token_manager = SimpleTokenManager()

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'simple-unified-service-2025'

def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API端点跳过认证
        if request.path.startswith('/api/') or request.path == '/health':
            return f(*args, **kwargs)
        
        if 'logged_in' not in session or not session['logged_in']:
            if request.path == '/login':
                return f(*args, **kwargs)
            return redirect(url_for('login'))
        
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        if username == AUTH_CONFIG['username'] and password == AUTH_CONFIG['password']:
            session['logged_in'] = True
            session['username'] = username
            logger.info(f"✅ 用户 {username} 登录成功")
            return redirect(url_for('index'))
        else:
            error = "用户名或密码错误"
    else:
        error = None
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>统一服务 - 登录</title>
    <style>
        body {{ font-family: Arial; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
               margin: 0; height: 100vh; display: flex; align-items: center; justify-content: center; }}
        .login {{ background: white; padding: 40px; border-radius: 10px; box-shadow: 0 10px 30px rgba(0,0,0,0.3); }}
        .login h1 {{ text-align: center; color: #333; }}
        .form-group {{ margin: 20px 0; }}
        .form-group label {{ display: block; margin-bottom: 5px; }}
        .form-group input {{ width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px; }}
        .btn {{ width: 100%; padding: 12px; background: #007bff; color: white; border: none; border-radius: 5px; cursor: pointer; }}
        .error {{ color: red; margin: 10px 0; }}
    </style>
</head>
<body>
    <div class="login">
        <h1>统一服务</h1>
        {f'<div class="error">{error}</div>' if error else ''}
        <form method="POST">
            <div class="form-group">
                <label>用户名</label>
                <input type="text" name="username" required>
            </div>
            <div class="form-group">
                <label>密码</label>
                <input type="password" name="password" required>
            </div>
            <button type="submit" class="btn">登录</button>
        </form>
    </div>
</body>
</html>
    """

@app.route('/')
@require_auth
def index():
    """主页"""
    username = session.get('username', 'Unknown')
    stats = token_manager.get_stats()
    
    return f"""
<!DOCTYPE html>
<html>
<head>
    <title>统一服务</title>
    <style>
        body {{ font-family: Arial; margin: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1000px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; }}
        .header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }}
        .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 20px; margin: 20px 0; }}
        .stat {{ background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }}
        .stat-number {{ font-size: 2em; font-weight: bold; color: #007bff; }}
        .api-section {{ background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .token-section {{ background: #f8f9fa; padding: 20px; border-radius: 5px; margin: 20px 0; }}
        .token-item {{ background: white; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }}
        .token-active {{ border-left-color: #28a745; }}
        .token-inactive {{ border-left-color: #dc3545; }}
        .add-token {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; }}
        .btn {{ padding: 8px 15px; background: #dc3545; color: white; text-decoration: none; border-radius: 5px; border: none; cursor: pointer; }}
        .btn-primary {{ background: #007bff; }}
        .btn-success {{ background: #28a745; }}
        .btn-danger {{ background: #dc3545; }}
        input {{ padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; width: 200px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>统一服务</h1>
            <div>
                <span>👤 {username}</span>
                <a href="/logout" class="btn">登出</a>
            </div>
        </div>
        
        <div class="stats">
            <div class="stat">
                <div class="stat-number">{stats['total_tokens']}</div>
                <div>总Token数</div>
            </div>
            <div class="stat">
                <div class="stat-number">{stats['active_tokens']}</div>
                <div>活跃Token</div>
            </div>
            <div class="stat">
                <div class="stat-number">{stats['total_success']}</div>
                <div>成功请求</div>
            </div>
            <div class="stat">
                <div class="stat-number">{stats['total_errors']}</div>
                <div>失败请求</div>
            </div>
        </div>

        <div class="token-section">
            <h3>🔑 Token管理</h3>

            <div class="add-token">
                <h4>➕ 添加新Token</h4>
                <form method="POST" action="/add_token">
                    <input type="text" name="token" placeholder="输入Token" required>
                    <input type="text" name="name" placeholder="Token名称">
                    <button type="submit" class="btn btn-success">添加Token</button>
                </form>
            </div>

            <div id="tokenList">
                <!-- Token列表将在这里显示 -->
            </div>
        </div>
        
        <div class="api-section">
            <h3>📋 API端点</h3>
            <p><strong>GET /api/download/?url=folder/filename</strong> - 获取文件下载地址</p>
            <p><strong>GET /api/folders</strong> - 获取文件夹列表</p>
            <p><strong>GET /api/files?folder=name</strong> - 获取文件列表</p>
            <p><strong>GET /health</strong> - 健康检查</p>
        </div>

    <script>
        // 页面加载时获取Token列表
        window.onload = function() {{
            refreshTokenList();
        }};

        function refreshTokenList() {{
            fetch('/api/token/stats')
                .then(response => response.json())
                .then(data => {{
                    if (data.success) {{
                        updateTokenList(data.data.tokens);
                    }}
                }})
                .catch(error => console.error('Error:', error));
        }}

        function updateTokenList(tokens) {{
            const listDiv = document.getElementById('tokenList');
            listDiv.innerHTML = tokens.map(token => `
                <div class="token-item ${{token.is_active ? 'token-active' : 'token-inactive'}}">
                    <strong>${{token.name}}</strong>
                    <span style="color: ${{token.is_active ? '#28a745' : '#dc3545'}};">
                        ${{token.is_active ? '🟢 活跃' : '🔴 禁用'}}
                    </span>
                    <br>
                    <small>Token: ${{token.token.substring(0, 20)}}...</small><br>
                    <small>成功: ${{token.success_count}} | 失败: ${{token.error_count}} | 成功率: ${{token.success_rate.toFixed(1)}}%</small>
                    <div style="margin-top: 10px;">
                        <button class="btn btn-danger" onclick="removeToken('${{token.token}}')">删除</button>
                    </div>
                </div>
            `).join('');
        }}

        function removeToken(token) {{
            if (!confirm('确定要删除这个Token吗？')) return;

            fetch('/remove_token', {{
                method: 'POST',
                headers: {{ 'Content-Type': 'application/x-www-form-urlencoded' }},
                body: 'token=' + encodeURIComponent(token)
            }})
            .then(response => {{
                if (response.ok) {{
                    alert('Token删除成功');
                    refreshTokenList();
                    location.reload(); // 刷新页面更新统计
                }} else {{
                    alert('删除失败');
                }}
            }})
            .catch(error => {{
                console.error('Error:', error);
                alert('删除失败');
            }});
        }}

        // 每30秒自动刷新Token列表
        setInterval(refreshTokenList, 30000);
    </script>
</body>
</html>
    """

@app.route('/logout')
@require_auth
def logout():
    """登出"""
    session.clear()
    return redirect(url_for('login'))


@app.route('/add_token', methods=['POST'])
@require_auth
def add_token():
    """添加Token"""
    token = request.form.get('token')
    name = request.form.get('name')

    if not token:
        return "Token不能为空", 400

    if token_manager.add_token(token, name):
        return redirect(url_for('index'))
    else:
        return "Token已存在", 400


@app.route('/remove_token', methods=['POST'])
@require_auth
def remove_token():
    """删除Token"""
    token = request.form.get('token')

    if not token:
        return "Token不能为空", 400

    if token_manager.remove_token(token):
        return "删除成功", 200
    else:
        return "Token不存在", 404

# ==================== API端点 ====================

@app.route('/api/token/get')
def api_get_token():
    """获取Token"""
    token = token_manager.get_best_token()
    if token:
        return jsonify({
            'code': 200,
            'success': True,
            'data': {'token': token}
        })
    else:
        return jsonify({
            'code': 404,
            'success': False,
            'error': '没有可用的token'
        }), 404


@app.route('/api/token/stats')
def api_token_stats():
    """获取Token统计信息"""
    stats = token_manager.get_stats()
    return jsonify({
        'code': 200,
        'success': True,
        'data': stats
    })


@app.route('/api/download/')
def api_download():
    """获取下载地址 - 集成真实下载逻辑"""
    url_param = request.args.get('url')
    if not url_param:
        return jsonify({
            'code': 401,
            'success': False,
            'error': '缺少url参数'
        }), 400

    # 解析url参数 - 支持多级目录
    url_parts = url_param.split('/')
    if len(url_parts) < 2:
        return jsonify({
            'code': 401,
            'success': False,
            'error': 'URL格式错误，至少需要：folder/filename'
        }), 400

    # 最后一个是文件名，前面的都是文件夹路径
    file_name = url_parts[-1]
    folder_path = url_parts[:-1]  # 文件夹路径数组

    # 获取Token
    token = token_manager.get_best_token()
    if not token:
        return jsonify({
            'code': 401,
            'success': False,
            'error': '没有可用的Token'
        }), 500

    try:
        # 创建实时API实例
        realtime_api = WoPanRealTimeAPI(token)

        # 查找文件 - 支持多级目录
        folder_path_str = '/'.join(folder_path)
        logger.info(f"🔍 查找文件: {folder_path_str}/{file_name}")
        file_obj = realtime_api.find_file_by_path(folder_path, file_name)

        if not file_obj:
            token_manager.report_error(token, f"文件未找到: {folder_path_str}/{file_name}")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '文件未找到',
                'message': f"在路径 '{folder_path_str}' 中未找到文件 '{file_name}'"
            }), 404

        # 获取文件FID
        fid = file_obj.fid
        if not fid:
            token_manager.report_error(token, "文件FID为空")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '文件FID为空'
            }), 500

        # 创建下载器实例
        downloader = WoPanDownloader(token)

        # 获取下载链接
        logger.info(f"📥 获取下载链接: FID={fid}")
        success, download_data = downloader.get_download_url_v2([fid])

        # 添加详细的调试日志
        logger.info(f"🔍 下载API调用结果: success={success}")
        logger.info(f"🔍 下载API响应数据: {download_data}")

        if not success:
            token_manager.report_error(token, f"获取下载链接失败: {download_data}")
            logger.error(f"❌ 下载链接获取失败: {download_data}")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '获取下载链接失败',
                'message': str(download_data)
            }), 500

        # 提取下载URL - 根据实际响应结构
        download_url = None
        if isinstance(download_data, dict):
            # 检查是否有list字段
            file_list = download_data.get('list', [])
            if file_list and len(file_list) > 0:
                # 从第一个文件项中获取downloadUrl
                first_file = file_list[0]
                download_url = first_file.get('downloadUrl')
            else:
                # 备用方案：直接从根级别查找
                download_url = (download_data.get('downloadUrl') or
                              download_data.get('url') or
                              download_data.get('download_url'))

        if not download_url:
            token_manager.report_error(token, "下载链接为空")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '下载链接为空',
                'message': '无法从API响应中提取下载链接'
            }), 500

        # 报告成功
        token_manager.report_success(token)
        logger.info(f"✅ 成功获取下载链接: {file_name}")

        return jsonify({
            'code': 200,
            'information': 'xinjie',
            'url': download_url
        })

    except Exception as e:
        token_manager.report_error(token, f"下载API异常: {str(e)}")
        logger.error(f"❌ 下载API异常: {e}")
        return jsonify({
            'code': 401,
            'success': False,
            'error': '服务器内部错误',
            'message': str(e)
        }), 500


@app.route('/api/folders')
def api_folders():
    """获取文件夹列表"""
    # 获取Token
    token = token_manager.get_best_token()
    if not token:
        return jsonify({
            'code': 401,
            'success': False,
            'error': '没有可用的Token'
        }), 500

    try:
        # 创建实时API实例
        realtime_api = WoPanRealTimeAPI(token)

        # 获取根目录内容
        logger.info("🔍 获取文件夹列表")
        success, root_files = realtime_api.get_folder_contents("0")

        if not success:
            token_manager.report_error(token, "获取文件夹列表失败")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '获取文件夹列表失败'
            }), 500

        # 过滤出文件夹
        folders = [f.name for f in root_files if f.is_folder]

        token_manager.report_success(token)
        logger.info(f"✅ 成功获取 {len(folders)} 个文件夹")

        return jsonify({
            'code': 200,
            'success': True,
            'data': folders,
            'count': len(folders),
            'source': 'realtime'
        })

    except Exception as e:
        token_manager.report_error(token, f"文件夹API异常: {str(e)}")
        logger.error(f"❌ 文件夹API异常: {e}")
        return jsonify({
            'code': 401,
            'success': False,
            'error': '服务器内部错误',
            'message': str(e)
        }), 500


@app.route('/api/files')
def api_files():
    """获取文件列表"""
    folder_name = request.args.get('folder')
    if not folder_name:
        return jsonify({
            'code': 401,
            'success': False,
            'error': '缺少folder参数'
        }), 400

    # 获取Token
    token = token_manager.get_best_token()
    if not token:
        return jsonify({
            'code': 401,
            'success': False,
            'error': '没有可用的Token'
        }), 500

    try:
        # 创建实时API实例
        realtime_api = WoPanRealTimeAPI(token)

        # 获取根目录内容，找到目标文件夹
        logger.info(f"🔍 获取文件夹内容: {folder_name}")
        success, root_files = realtime_api.get_folder_contents("0")

        if not success:
            token_manager.report_error(token, "获取根目录失败")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '获取根目录失败'
            }), 500

        # 查找目标文件夹
        target_folder = None
        for file in root_files:
            if file.is_folder and file.name == folder_name:
                target_folder = file
                break

        if not target_folder:
            token_manager.report_error(token, f"文件夹未找到: {folder_name}")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '文件夹未找到',
                'message': f"未找到文件夹 '{folder_name}'"
            }), 404

        # 获取文件夹内容
        success, folder_files = realtime_api.get_folder_contents(target_folder.id)

        if not success:
            token_manager.report_error(token, f"获取文件夹内容失败: {folder_name}")
            return jsonify({
                'code': 401,
                'success': False,
                'error': '获取文件夹内容失败'
            }), 500

        # 转换为字典格式
        files_data = [f.to_dict() for f in folder_files]

        token_manager.report_success(token)
        logger.info(f"✅ 成功获取 {len(files_data)} 个文件")

        return jsonify({
            'code': 200,
            'success': True,
            'data': {
                'folder': folder_name,
                'file_count': len(files_data),
                'source': 'realtime',
                'files': files_data
            }
        })

    except Exception as e:
        token_manager.report_error(token, f"文件API异常: {str(e)}")
        logger.error(f"❌ 文件API异常: {e}")
        return jsonify({
            'code': 401,
            'success': False,
            'error': '服务器内部错误',
            'message': str(e)
        }), 500


@app.route('/health')
def health():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'Unified WoPan Service',
        'timestamp': datetime.now().isoformat()
    })

def create_app():
    """应用工厂函数"""
    return app


def run_with_gevent():
    """使用gevent运行服务器（支持并发）"""
    try:
        from gevent.pywsgi import WSGIServer
        logger.info("✅ 使用Gevent WSGI服务器（支持并发）")
        http_server = WSGIServer(('0.0.0.0', 8000), app)
        http_server.serve_forever()
    except ImportError:
        logger.warning("⚠️ Gevent未安装，使用Flask开发服务器")
        app.run(host='0.0.0.0', port=8000, threaded=True)


def run_with_waitress():
    """使用waitress运行服务器（Windows友好）"""
    try:
        from waitress import serve
        logger.info("✅ 使用Waitress WSGI服务器（支持并发）")
        serve(app, host='0.0.0.0', port=8000, threads=8)
    except ImportError:
        logger.warning("⚠️ Waitress未安装，回退到其他方式")
        run_with_gevent()


if __name__ == '__main__':
    logger.info("🚀 启动联通网盘统一服务（并发优化版）")
    logger.info("=" * 60)
    logger.info("🔐 登录信息:")
    logger.info(f"   用户名: {AUTH_CONFIG['username']}")
    logger.info(f"   密码: {AUTH_CONFIG['password']}")
    logger.info("=" * 60)
    logger.info("🌐 服务地址: http://localhost:8000")
    logger.info("📋 功能: Token管理 + 文件下载API + 并发处理")
    logger.info("=" * 60)

    # 检测运行环境并选择最佳服务器
    if os.name == 'nt':  # Windows
        logger.info("🖥️ 检测到Windows环境，优先使用Waitress")
        run_with_waitress()
    else:  # Linux/Mac
        logger.info("🐧 检测到Unix环境，优先使用Gevent")
        run_with_gevent()
