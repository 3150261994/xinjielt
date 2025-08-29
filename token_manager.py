#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘Token负载均衡管理器
提供token轮询、健康检查、故障转移等功能

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
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify, session, redirect, url_for
from dataclasses import dataclass, asdict
import random
from functools import wraps

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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
        self.health_check_interval = 300  # 5分钟检查一次
        self.health_check_thread = None
        self.running = False
        
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
    
    def get_next_token(self) -> Optional[TokenInfo]:
        """获取下一个可用token（轮询算法）"""
        with self.lock:
            if not self.tokens:
                return None
                
            # 过滤出活跃的tokens
            active_tokens = [t for t in self.tokens if t.is_active]
            if not active_tokens:
                return None
            
            # 轮询选择
            if self.current_index >= len(active_tokens):
                self.current_index = 0
                
            token = active_tokens[self.current_index]
            self.current_index = (self.current_index + 1) % len(active_tokens)
            
            # 更新使用时间
            token.last_used = datetime.now()
            
            return token
    
    def get_best_token(self) -> Optional[TokenInfo]:
        """获取最佳token（基于成功率和最近使用时间）"""
        with self.lock:
            active_tokens = [t for t in self.tokens if t.is_active]
            if not active_tokens:
                return None
            
            # 按成功率和使用时间排序
            def score_token(token: TokenInfo) -> float:
                success_rate = token.get_success_rate()
                
                # 如果从未使用过，给予较高分数
                if token.last_used is None:
                    return success_rate + 10
                
                # 计算距离上次使用的时间（分钟）
                time_since_use = (datetime.now() - token.last_used).total_seconds() / 60
                
                # 成功率 + 时间加分（最近使用的减分）
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
                    
                    # 如果错误率过高，暂时禁用
                    if t.error_count > 5 and t.get_success_rate() < 50:
                        t.is_active = False
                        logger.warning(f"⚠️ Token {t.name} 因错误率过高被暂时禁用")
                    break
    
    def add_token(self, token: str, name: str = None) -> bool:
        """添加新token"""
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
        """删除token"""
        with self.lock:
            for i, t in enumerate(self.tokens):
                if t.token == token:
                    removed = self.tokens.pop(i)
                    self.save_tokens()
                    logger.info(f"🗑️ 删除token: {removed.name}")
                    return True
            return False
    
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

# 认证配置
AUTH_CONFIG = {
    'username': 'admin',
    'password': '3150261994',
    'session_timeout': 3600  # 1小时
}

# 创建Flask应用
app = Flask(__name__)
app.secret_key = 'wopan-token-manager-secret-key-2025'  # 用于session加密


def require_auth(f):
    """认证装饰器"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # API端点跳过认证（用于服务间调用）
        if request.path.startswith('/api/') or request.path == '/health':
            return f(*args, **kwargs)

        # 检查session
        if 'logged_in' not in session or not session['logged_in']:
            if request.path == '/login' or request.path.startswith('/static'):
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


def require_web_auth(f):
    """Web界面认证装饰器（仅用于管理界面）"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # 检查session
        if 'logged_in' not in session or not session['logged_in']:
            return redirect(url_for('login'))

        # 检查session是否过期
        if 'login_time' in session:
            login_time = datetime.fromisoformat(session['login_time'])
            if (datetime.now() - login_time).seconds > AUTH_CONFIG['session_timeout']:
                session.clear()
                return redirect(url_for('login'))

        return f(*args, **kwargs)
    return decorated_function


@app.route('/api/token/get', methods=['GET'])
def get_token():
    """获取可用token"""
    strategy = request.args.get('strategy', 'round_robin')  # round_robin 或 best
    
    if strategy == 'best':
        token_info = token_manager.get_best_token()
    else:
        token_info = token_manager.get_next_token()
    
    if token_info:
        return jsonify({
            'code': 200,
            'success': True,
            'data': {
                'token': token_info.token,
                'name': token_info.name
            }
        })
    else:
        return jsonify({
            'code': 404,
            'success': False,
            'error': '没有可用的token'
        }), 404


@app.route('/api/token/report', methods=['POST'])
def report_usage():
    """报告token使用结果"""
    data = request.get_json()
    
    token = data.get('token')
    success = data.get('success', False)
    error = data.get('error', '')
    
    if not token:
        return jsonify({
            'code': 400,
            'success': False,
            'error': '缺少token参数'
        }), 400
    
    if success:
        token_manager.report_success(token)
    else:
        token_manager.report_error(token, error)
    
    return jsonify({
        'code': 200,
        'success': True,
        'message': '报告已记录'
    })


@app.route('/api/token/stats', methods=['GET'])
def get_stats():
    """获取统计信息"""
    stats = token_manager.get_stats()
    return jsonify({
        'code': 200,
        'success': True,
        'data': stats
    })


@app.route('/api/token/add', methods=['POST'])
def add_token():
    """添加新token"""
    data = request.get_json()
    
    token = data.get('token')
    name = data.get('name')
    
    if not token:
        return jsonify({
            'code': 400,
            'success': False,
            'error': '缺少token参数'
        }), 400
    
    if token_manager.add_token(token, name):
        return jsonify({
            'code': 200,
            'success': True,
            'message': 'Token添加成功'
        })
    else:
        return jsonify({
            'code': 409,
            'success': False,
            'error': 'Token已存在'
        }), 409


@app.route('/api/token/remove', methods=['DELETE'])
def remove_token():
    """删除token"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({
            'code': 400,
            'success': False,
            'error': '缺少token参数'
        }), 400
    
    if token_manager.remove_token(token):
        return jsonify({
            'code': 200,
            'success': True,
            'message': 'Token删除成功'
        })
    else:
        return jsonify({
            'code': 404,
            'success': False,
            'error': 'Token不存在'
        }), 404


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
    <title>Token管理器 - 登录</title>
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
            <h1>🔑 Token管理器</h1>
            <p>请登录以继续</p>
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
            <p>联通网盘Token负载均衡管理系统</p>
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


@app.route('/')
@require_web_auth
def index():
    """Token管理Web界面"""
    username = session.get('username', 'Unknown')
    html = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Token负载均衡管理器</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; padding-bottom: 15px; border-bottom: 1px solid #eee; }
        .header h1 { color: #333; margin: 0; }
        .user-info { display: flex; align-items: center; gap: 15px; }
        .user-info span { color: #666; }
        .logout-btn { background: #dc3545; color: white; padding: 8px 15px; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; }
        .logout-btn:hover { background: #c82333; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
        .stat-card { background: #f8f9fa; padding: 15px; border-radius: 5px; text-align: center; }
        .stat-number { font-size: 2em; font-weight: bold; color: #007bff; }
        .token-list { margin: 20px 0; }
        .token-item { background: #f8f9fa; margin: 10px 0; padding: 15px; border-radius: 5px; border-left: 4px solid #007bff; }
        .token-active { border-left-color: #28a745; }
        .token-inactive { border-left-color: #dc3545; }
        .token-actions { margin-top: 10px; }
        button { padding: 5px 10px; margin: 2px; border: none; border-radius: 3px; cursor: pointer; }
        .btn-success { background: #28a745; color: white; }
        .btn-danger { background: #dc3545; color: white; }
        .btn-primary { background: #007bff; color: white; }
        .add-token { background: #e3f2fd; padding: 20px; border-radius: 5px; margin: 20px 0; }
        input { padding: 8px; margin: 5px; border: 1px solid #ddd; border-radius: 3px; width: 300px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🔑 Token负载均衡管理器</h1>
            <div class="user-info">
                <span>👤 欢迎, """ + username + """</span>
                <a href="/logout" class="logout-btn">登出</a>
            </div>
        </div>

        <div class="stats" id="stats">
            <!-- 统计信息将在这里显示 -->
        </div>

        <div class="add-token">
            <h3>➕ 添加新Token</h3>
            <input type="text" id="newToken" placeholder="输入Token">
            <input type="text" id="newTokenName" placeholder="Token名称">
            <button class="btn-primary" onclick="addToken()">添加Token</button>
        </div>

        <div class="token-list">
            <h3>📋 Token列表</h3>
            <div id="tokenList">
                <!-- Token列表将在这里显示 -->
            </div>
        </div>

        <div style="text-align: center; margin-top: 20px;">
            <button class="btn-primary" onclick="refreshData()">🔄 刷新数据</button>
        </div>
    </div>

    <script>
        function refreshData() {
            fetch('/api/token/stats')
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        updateStats(data.data);
                        updateTokenList(data.data.tokens);
                    }
                })
                .catch(error => console.error('Error:', error));
        }

        function updateStats(stats) {
            const statsDiv = document.getElementById('stats');
            statsDiv.innerHTML = `
                <div class="stat-card">
                    <div class="stat-number">${stats.total_tokens}</div>
                    <div>总Token数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.active_tokens}</div>
                    <div>活跃Token</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.total_requests}</div>
                    <div>总请求数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">${stats.overall_success_rate.toFixed(1)}%</div>
                    <div>总成功率</div>
                </div>
            `;
        }

        function updateTokenList(tokens) {
            const listDiv = document.getElementById('tokenList');
            listDiv.innerHTML = tokens.map(token => `
                <div class="token-item ${token.is_active ? 'token-active' : 'token-inactive'}">
                    <strong>${token.name}</strong>
                    <span style="color: ${token.is_active ? '#28a745' : '#dc3545'};">
                        ${token.is_active ? '🟢 活跃' : '🔴 禁用'}
                    </span>
                    <br>
                    <small>Token: ${token.token.substring(0, 20)}...</small><br>
                    <small>成功: ${token.success_count} | 失败: ${token.error_count} | 成功率: ${token.success_rate.toFixed(1)}%</small>
                    <div class="token-actions">
                        <button class="btn-danger" onclick="removeToken('${token.token}')">删除</button>
                    </div>
                </div>
            `).join('');
        }

        function addToken() {
            const token = document.getElementById('newToken').value;
            const name = document.getElementById('newTokenName').value;

            if (!token) {
                alert('请输入Token');
                return;
            }

            fetch('/api/token/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token, name: name || undefined })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Token添加成功');
                    document.getElementById('newToken').value = '';
                    document.getElementById('newTokenName').value = '';
                    refreshData();
                } else {
                    alert('添加失败: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('添加失败');
            });
        }

        function removeToken(token) {
            if (!confirm('确定要删除这个Token吗？')) return;

            fetch('/api/token/remove', {
                method: 'DELETE',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: token })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('Token删除成功');
                    refreshData();
                } else {
                    alert('删除失败: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('删除失败');
            });
        }

        // 页面加载时刷新数据
        window.onload = refreshData;

        // 每30秒自动刷新
        setInterval(refreshData, 30000);
    </script>
</body>
</html>
    """
    return html


@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'Token Manager',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    logger.info("🚀 启动Token负载均衡管理器 (需要登录)")
    logger.info("=" * 60)
    logger.info("🔐 登录信息:")
    logger.info(f"   用户名: {AUTH_CONFIG['username']}")
    logger.info(f"   密码: {AUTH_CONFIG['password']}")
    logger.info("=" * 60)
    logger.info("📋 API端点:")
    logger.info("   GET  /api/token/get           - 获取可用token")
    logger.info("   POST /api/token/report        - 报告使用结果")
    logger.info("   GET  /api/token/stats         - 获取统计信息")
    logger.info("   POST /api/token/add           - 添加新token")
    logger.info("   DELETE /api/token/remove      - 删除token")
    logger.info("   GET  /health                  - 健康检查")
    logger.info("=" * 60)
    logger.info("🌐 管理界面: http://localhost:8000 (需要登录)")
    logger.info("🔧 API服务: http://localhost:8000/api/ (无需认证)")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
