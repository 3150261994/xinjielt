#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘Web版本
基于Flask的Web界面，支持文件浏览、下载链接获取、文件上传等功能
"""

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_file
from werkzeug.utils import secure_filename
import os
import json
import threading
import time
from datetime import datetime
import uuid
import tempfile
import shutil

# 导入原有的API类
import requests
import hashlib
import random
import base64
from typing import Dict, List, Optional, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

# 复制原有的类定义
class WoPanCrypto:
    """联通网盘加密工具"""
    
    def __init__(self, client_secret: str = "XFmi9GS2hzk98jGX"):
        self.key = client_secret.encode('utf-8')
        self.iv = b"wNSOYIB1k1DjY5lA"
        self.access_key = None
    
    def set_access_token(self, token: str):
        if len(token) >= 16:
            self.access_key = token[:16].encode('utf-8')
    
    def encrypt(self, content: str, channel: str) -> str:
        key = self.key if channel == "api-user" else self.access_key
        if key is None:
            key = self.key
        
        try:
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            padded_data = pad(content.encode('utf-8'), AES.block_size)
            encrypted = cipher.encrypt(padded_data)
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception:
            return content
    
    def decrypt(self, encrypted_data: str, channel: str) -> str:
        key = self.key if channel == "api-user" else self.access_key
        if key is None:
            key = self.key
        
        try:
            encrypted_bytes = base64.b64decode(encrypted_data)
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            decrypted = cipher.decrypt(encrypted_bytes)
            unpadded = unpad(decrypted, AES.block_size)
            return unpadded.decode('utf-8')
        except Exception:
            return encrypted_data


class WoPanFile:
    """联通网盘文件对象"""
    
    def __init__(self, data: Dict):
        self.fid = data.get('fid', '')
        self.name = data.get('name', '')
        self.size = data.get('size', 0)
        self.type = data.get('type', 1)  # 0: 文件夹, 1: 文件
        self.id = data.get('id', '')
        self.create_time = data.get('createTime', '')
        self.file_type = data.get('fileType', '')
    
    @property
    def is_folder(self) -> bool:
        return self.type == 0
    
    @property
    def size_str(self) -> str:
        """格式化文件大小"""
        if self.size == 0:
            return "-"
        
        size = self.size
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} PB"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            'fid': self.fid,
            'name': self.name,
            'size': self.size,
            'size_str': self.size_str,
            'type': self.type,
            'id': self.id,
            'create_time': self.create_time,
            'file_type': self.file_type,
            'is_folder': self.is_folder
        }


class WoPanAPI:
    """联通网盘API"""
    
    DEFAULT_CLIENT_ID = "1001000021"
    DEFAULT_CLIENT_SECRET = "XFmi9GS2hzk98jGX"
    DEFAULT_BASE_URL = "https://panservice.mail.wo.cn"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    CHANNEL_WO_HOME = "wohome"
    
    def __init__(self, access_token: str):
        self.access_token = access_token
        self.crypto = WoPanCrypto(self.DEFAULT_CLIENT_SECRET)
        self.crypto.set_access_token(access_token)
        
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
        if not param:
            return other
        
        param_json = json.dumps(param, separators=(',', ':'))
        encrypted_param = self.crypto.encrypt(param_json, channel)
        
        body = other.copy()
        body["param"] = encrypted_param
        return body
    
    def get_folder_contents(self, parent_id: str = "0") -> Tuple[bool, List[WoPanFile]]:
        """获取文件夹内容"""
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"
        
        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "QueryAllFiles")
        
        param = {
            "spaceType": "0",
            "parentDirectoryId": parent_id,
            "pageNum": 0,
            "pageSize": 100,
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
                
        except Exception:
            return False, []
    
    def get_download_url(self, fid: str) -> Tuple[bool, str]:
        """获取下载链接"""
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"
        
        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "GetDownloadUrlV2")
        
        param = {
            "type": "1",
            "fidList": [fid],
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
                return False, f"API错误: {result.get('STATUS')}"
            
            rsp = result.get('RSP', {})
            if rsp.get('RSP_CODE') != '0000':
                return False, f"响应错误: {rsp.get('RSP_CODE')}"
            
            data = rsp.get('DATA', '')
            if isinstance(data, str):
                decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)
                
                try:
                    parsed_data = json.loads(decrypted_text)
                    file_list = parsed_data.get('list', [])
                    if file_list and len(file_list) > 0:
                        download_url = file_list[0].get('downloadUrl')
                        if download_url:
                            return True, download_url
                    return False, "未获取到下载链接"
                except json.JSONDecodeError:
                    return False, "JSON解析失败"
            else:
                return False, "未获取到有效数据"
                
        except Exception as e:
            return False, f"请求异常: {e}"

    def get_file_type(self, file_name: str) -> str:
        """根据文件名获取文件类型"""
        ext = os.path.splitext(file_name)[1].lower()

        # 视频文件
        if ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.webm']:
            return 'video'
        # 图片文件
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp']:
            return 'image'
        # 音频文件
        elif ext in ['.mp3', '.wav', '.flac', '.aac', '.ogg']:
            return 'audio'
        # 文档文件
        elif ext in ['.pdf', '.doc', '.docx', '.txt', '.xlsx', '.ppt', '.pptx']:
            return 'text'
        # 压缩文件
        elif ext in ['.zip', '.rar', '.7z', '.tar', '.gz']:
            return 'zip'
        else:
            return 'other'

    def upload_file_2c(self, file_path: str, target_dir_id: str = "0", progress_callback=None) -> Tuple[bool, str]:
        """使用2C接口上传文件"""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 上传服务器URL
            upload_url = "https://tjupload.pan.wo.cn/openapi/client/upload2C"

            # 生成批次号
            from datetime import datetime
            batch_no = datetime.now().strftime("%Y%m%d%H%M%S")

            # 准备文件信息
            file_info = {
                "spaceType": "0",  # 个人空间
                "directoryId": target_dir_id,
                "batchNo": batch_no,
                "fileName": file_name,
                "fileSize": file_size,
                "fileType": self.get_file_type(file_name)
            }

            # 加密文件信息
            file_info_str = self.crypto.encrypt(json.dumps(file_info, separators=(',', ':')), self.CHANNEL_WO_HOME)

            # 计算分片信息
            part_size = 32 * 1024 * 1024  # 32MB per part
            total_parts = (file_size + part_size - 1) // part_size  # 向上取整

            # 生成唯一ID
            unique_id = f"{int(time.time() * 1000)}_{self._random_chars(6)}"

            # 基础表单数据
            base_form_data = {
                "uniqueId": unique_id,
                "accessToken": self.access_token,
                "fileName": file_name,
                "psToken": "undefined",
                "fileSize": str(file_size),
                "totalPart": str(total_parts),
                "channel": "wocloud",
                "directoryId": target_dir_id,
                "fileInfo": file_info_str
            }

            fid = ""
            uploaded_size = 0

            # 分片上传
            with open(file_path, 'rb') as f:
                for part_index in range(1, total_parts + 1):
                    # 计算当前分片大小
                    current_part_size = min(part_size, file_size - uploaded_size)

                    # 读取分片数据
                    chunk_data = f.read(current_part_size)

                    # 准备表单数据
                    form_data = base_form_data.copy()
                    form_data["partSize"] = str(current_part_size)
                    form_data["partIndex"] = str(part_index)

                    # 准备文件数据
                    files = {
                        'file': (file_name, chunk_data, 'application/octet-stream')
                    }

                    # 发送上传请求
                    headers = {
                        'Origin': 'https://pan.wo.cn',
                        'Referer': 'https://pan.wo.cn/',
                        'User-Agent': self.DEFAULT_UA,
                        'Connection': 'keep-alive',
                        'Accept-Encoding': 'gzip, deflate'
                    }

                    # 创建专门的上传会话
                    upload_session = requests.Session()
                    upload_session.headers.update(headers)

                    response = upload_session.post(
                        upload_url,
                        data=form_data,
                        files=files,
                        timeout=(30, 300)
                    )

                    if response.status_code != 200:
                        return False, f"上传分片{part_index}失败: HTTP {response.status_code}"

                    try:
                        result = response.json()
                        if result.get('code') != '0000':
                            return False, f"上传分片{part_index}失败: {result.get('msg', '未知错误')}"

                        # 获取FID
                        if result.get('data', {}).get('fid'):
                            fid = result['data']['fid']

                    except json.JSONDecodeError:
                        return False, f"上传分片{part_index}响应解析失败"

                    uploaded_size += current_part_size

                    # 调用进度回调
                    if progress_callback:
                        progress = (uploaded_size / file_size) * 100
                        progress_callback(progress)

            if fid:
                return True, fid
            else:
                return False, "上传完成但未获取到文件ID"

        except Exception as e:
            return False, f"上传异常: {e}"

    def _random_chars(self, length: int) -> str:
        """生成随机字符串"""
        import string
        import random
        chars = string.ascii_letters
        return ''.join(random.choice(chars) for _ in range(length))

    def delete_file(self, space_type: str = "0", dir_list: List[str] = None, file_list: List[str] = None) -> Tuple[bool, str]:
        """删除文件或文件夹"""
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"

        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "DeleteFile")

        param = {
            "spaceType": space_type,
            "vipLevel": "0",
            "dirList": dir_list or [],
            "fileList": file_list or [],
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
                return False, f"API错误: {result.get('STATUS')}"

            rsp = result.get('RSP', {})
            if rsp.get('RSP_CODE') != '0000':
                return False, f"响应错误: {rsp.get('RSP_CODE')} - {rsp.get('RSP_DESC', '')}"

            return True, "删除成功"

        except Exception as e:
            return False, f"请求异常: {e}"

    def create_directory(self, space_type: str = "0", parent_directory_id: str = "0",
                        directory_name: str = "", family_id: str = "") -> Tuple[bool, str]:
        """创建文件夹"""
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"

        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "CreateDirectory")

        param = {
            "spaceType": space_type,
            "parentDirectoryId": parent_directory_id,
            "directoryName": directory_name,
            "clientId": self.DEFAULT_CLIENT_ID
        }

        # 添加familyId（如果是家庭空间）
        if family_id:
            param["familyId"] = family_id

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
                return False, f"API错误: {result.get('STATUS')}"

            rsp = result.get('RSP', {})
            if rsp.get('RSP_CODE') != '0000':
                return False, f"响应错误: {rsp.get('RSP_CODE')} - {rsp.get('RSP_DESC', '')}"

            # 解密响应数据获取新文件夹ID
            data = rsp.get('DATA', '')
            if isinstance(data, str):
                decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)
                try:
                    parsed_data = json.loads(decrypted_text)
                    folder_id = parsed_data.get('id', '')
                    return True, folder_id
                except json.JSONDecodeError:
                    return True, "创建成功"

            return True, "创建成功"

        except Exception as e:
            return False, f"请求异常: {e}"


# Flask应用
app = Flask(__name__)
app.secret_key = 'wopan_web_secret_key_' + str(uuid.uuid4())

# 配置上传文件夹
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024 * 1024  # 16GB max file size

# 全局变量存储API实例
api_instances = {}

def get_api_instance():
    """获取当前会话的API实例"""
    session_id = session.get('session_id')
    if session_id and session_id in api_instances:
        return api_instances[session_id]
    return None

@app.route('/')
def index():
    """主页"""
    return render_template('index.html')

@app.route('/api/test')
def test_api():
    """测试API接口"""
    return jsonify({
        'success': True,
        'message': 'API正常工作',
        'timestamp': time.time()
    })

@app.route('/api/connect', methods=['POST'])
def connect_api():
    """连接API"""
    data = request.get_json()
    token = data.get('token', '').strip()
    
    if not token:
        return jsonify({'success': False, 'message': '请输入Token'})
    
    try:
        api = WoPanAPI(token)
        success, files = api.get_folder_contents("0")
        
        if success:
            # 生成会话ID
            session_id = str(uuid.uuid4())
            session['session_id'] = session_id
            session['token'] = token
            
            # 存储API实例
            api_instances[session_id] = api
            
            # 转换文件列表为字典格式
            files_data = [file.to_dict() for file in files]
            
            return jsonify({
                'success': True,
                'message': '连接成功',
                'files': files_data,
                'current_folder_id': '0',
                'current_path': '根目录'
            })
        else:
            return jsonify({'success': False, 'message': '连接失败，请检查Token'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': f'连接异常: {str(e)}'})

@app.route('/api/browse/<folder_id>')
def browse_folder(folder_id):
    """浏览文件夹"""
    api = get_api_instance()
    if not api:
        return jsonify({'success': False, 'message': '请先连接API'})
    
    try:
        success, files = api.get_folder_contents(folder_id)
        if success:
            files_data = [file.to_dict() for file in files]
            return jsonify({
                'success': True,
                'files': files_data,
                'current_folder_id': folder_id
            })
        else:
            return jsonify({'success': False, 'message': '获取文件夹内容失败'})
    except Exception as e:
        return jsonify({'success': False, 'message': f'浏览异常: {str(e)}'})

@app.route('/api/download/<fid>')
def get_download_link(fid):
    """获取下载链接"""
    api = get_api_instance()
    if not api:
        return jsonify({'success': False, 'message': '请先连接API'})

    try:
        success, result = api.get_download_url(fid)
        if success:
            return jsonify({
                'success': True,
                'download_url': result
            })
        else:
            return jsonify({'success': False, 'message': result})
    except Exception as e:
        return jsonify({'success': False, 'message': f'获取下载链接异常: {str(e)}'})

@app.route('/api/upload', methods=['POST'])
def upload_files():
    """上传文件"""
    print("📤 收到上传请求")

    api = get_api_instance()
    if not api:
        print("❌ 未找到API实例")
        return jsonify({'success': False, 'message': '请先连接API'})

    if 'files' not in request.files:
        print("❌ 请求中没有文件")
        return jsonify({'success': False, 'message': '没有选择文件'})

    files = request.files.getlist('files')
    folder_id = request.form.get('folder_id', '0')

    print(f"📁 目标文件夹ID: {folder_id}")
    print(f"📄 文件数量: {len(files)}")

    if not files or files[0].filename == '':
        print("❌ 文件列表为空")
        return jsonify({'success': False, 'message': '没有选择文件'})

    results = []
    for i, file in enumerate(files):
        if file and file.filename:
            try:
                print(f"🔄 处理文件 {i+1}/{len(files)}: {file.filename}")

                # 保存临时文件
                filename = secure_filename(file.filename)
                temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                print(f"💾 保存临时文件: {temp_path}")
                file.save(temp_path)

                # 上传到网盘
                print(f"☁️ 开始上传到网盘...")
                file_size = os.path.getsize(temp_path)
                print(f"📏 文件大小: {file_size} bytes ({file_size/1024/1024:.2f} MB)")

                def progress_callback(progress):
                    print(f"📊 上传进度: {progress:.1f}%")

                success, result = api.upload_file_2c(temp_path, folder_id, progress_callback)
                print(f"📤 上传结果: {success}, {result}")

                if success:
                    print(f"✅ 文件 {filename} 上传成功!")
                else:
                    print(f"❌ 文件 {filename} 上传失败: {result}")

                # 删除临时文件
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    print(f"🗑️ 已删除临时文件")

                results.append({
                    'filename': filename,
                    'success': success,
                    'message': result if not success else '上传成功'
                })

            except Exception as e:
                print(f"❌ 处理文件异常: {str(e)}")
                import traceback
                traceback.print_exc()
                results.append({
                    'filename': file.filename,
                    'success': False,
                    'message': f'上传异常: {str(e)}'
                })

    # 统计结果
    success_count = sum(1 for r in results if r['success'])
    total_count = len(results)

    print(f"📊 上传统计: 成功 {success_count}/{total_count}")

    response_data = {
        'success': success_count > 0,
        'message': f'上传完成: 成功 {success_count}/{total_count}',
        'results': results
    }

    print(f"📤 返回响应: {response_data}")
    return jsonify(response_data)

@app.route('/api/upload_test', methods=['POST'])
def upload_test():
    """简单的上传测试接口"""
    print("🧪 收到测试上传请求")

    try:
        if 'files' not in request.files:
            return jsonify({'success': False, 'message': '没有文件'})

        files = request.files.getlist('files')
        print(f"📄 收到 {len(files)} 个文件")

        for file in files:
            print(f"📄 文件: {file.filename}, 大小: {len(file.read())} bytes")
            file.seek(0)  # 重置文件指针

        return jsonify({
            'success': True,
            'message': f'测试成功，收到 {len(files)} 个文件',
            'files': [f.filename for f in files]
        })

    except Exception as e:
        print(f"❌ 测试上传异常: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'message': f'测试异常: {str(e)}'
        })

@app.route('/api/delete', methods=['POST'])
def delete_file():
    """删除文件"""
    api = get_api_instance()
    if not api:
        return jsonify({'success': False, 'message': '请先连接API'})

    data = request.get_json()
    file_id = data.get('file_id')
    is_folder = data.get('is_folder', False)

    if not file_id:
        return jsonify({'success': False, 'message': '缺少文件ID'})

    try:
        if is_folder:
            success, result = api.delete_file(dir_list=[file_id])
        else:
            success, result = api.delete_file(file_list=[file_id])

        return jsonify({
            'success': success,
            'message': result
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'删除异常: {str(e)}'})

@app.route('/api/create_folder', methods=['POST'])
def create_folder():
    """创建文件夹"""
    api = get_api_instance()
    if not api:
        return jsonify({'success': False, 'message': '请先连接API'})

    data = request.get_json()
    folder_name = data.get('folder_name', '').strip()
    parent_id = data.get('parent_id', '0')

    if not folder_name:
        return jsonify({'success': False, 'message': '请输入文件夹名称'})

    try:
        success, result = api.create_directory(
            space_type="0",
            parent_directory_id=parent_id,
            directory_name=folder_name
        )

        return jsonify({
            'success': success,
            'message': result if not success else '创建成功',
            'folder_id': result if success else None
        })
    except Exception as e:
        return jsonify({'success': False, 'message': f'创建异常: {str(e)}'})

if __name__ == '__main__':
    print("🚀 启动联通网盘Web服务...")
    print("📡 访问地址: http://localhost:5000")
    app.run(debug=True, host='0.0.0.0', port=5000, use_reloader=False)
