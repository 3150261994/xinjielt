#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘Web API服务
提供RESTful API获取文件下载地址

Author: AI Assistant
Date: 2025-01-26
"""

import json
import logging
import time
import base64
import hashlib
import random
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import Flask, request, jsonify
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
from get_download_url import WoPanDownloader
from token_client import get_token_with_retry, report_success, report_error

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


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


# 创建Flask应用
app = Flask(__name__)

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

        # 设置session - 使用与工作的downloader相同的配置
        import requests
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
        """计算请求头 - 完全匹配工作的downloader"""
        res_time = int(time.time() * 1000)
        req_seq = random.randint(100000, 108999)
        version = ""

        # 计算签名 - 完全匹配工作代码
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
        """构建请求体 - 匹配工作的downloader"""
        if not param:
            return other

        # 加密参数 - 使用紧凑的JSON格式
        param_json = json.dumps(param, separators=(',', ':'))
        encrypted_param = self.crypto.encrypt(param_json, channel)

        body = other.copy()
        body["param"] = encrypted_param
        return body

    def get_folder_contents(self, parent_id: str = "0", space_type: str = "0",
                           page_size: int = 100) -> Tuple[bool, List[WoPanFile]]:
        """获取文件夹内容"""
        logger.info(f"🔍 实时获取文件夹内容 - 目录ID: {parent_id}")

        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"

        # 使用session的默认headers (已包含Accesstoken)
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
            logger.debug(f"请求URL: {url}")
            logger.debug(f"请求头: {json.dumps(dict(headers), indent=2)}")
            logger.debug(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")

            response = self.session.post(url, json=request_data, headers=headers, timeout=30)

            logger.debug(f"响应状态码: {response.status_code}")
            logger.debug(f"响应内容: {response.text[:500]}")

            if response.status_code != 200:
                logger.error(f"HTTP请求失败: {response.status_code}")
                return False, []

            result = response.json()

            if result.get('STATUS') != '200':
                logger.error(f"API请求失败: {result.get('STATUS')} - {result.get('MSG')}")
                return False, []

            rsp = result.get('RSP', {})
            rsp_code = rsp.get('RSP_CODE')

            if rsp_code != '0000':
                logger.error(f"API响应错误: {rsp_code} - {rsp.get('RSP_DESC')}")
                return False, []

            # 获取并解密数据
            data = rsp.get('DATA', '')
            if isinstance(data, str):
                decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)

                try:
                    parsed_data = json.loads(decrypted_text)
                    files_data = parsed_data.get('files', [])

                    files = [WoPanFile(file_data) for file_data in files_data]

                    logger.info(f"✅ 实时获取成功: {len(files)} 个项目")
                    return True, files

                except json.JSONDecodeError as e:
                    logger.error(f"JSON解析失败: {e}")
                    return False, []
            else:
                logger.error("未获取到有效数据")
                return False, []

        except Exception as e:
            logger.error(f"实时请求异常: {e}")
            return False, []

    def find_file_by_name(self, folder_name: str, file_name: str) -> Optional[WoPanFile]:
        """在指定文件夹中查找文件"""
        # 首先获取根目录内容，找到目标文件夹
        success, root_files = self.get_folder_contents("0")
        if not success:
            return None

        # 查找目标文件夹
        target_folder = None
        for file in root_files:
            if file.is_folder and file.name == folder_name:
                target_folder = file
                break

        if not target_folder:
            logger.warning(f"未找到文件夹: {folder_name}")
            return None

        # 获取文件夹内容
        success, folder_files = self.get_folder_contents(target_folder.id)
        if not success:
            return None

        # 查找目标文件
        for file in folder_files:
            if not file.is_folder and file.name == file_name:
                return file

        return None


# 全局配置 - 使用动态token获取
def get_downloader():
    """获取下载器实例（动态token）"""
    token = get_token_with_retry(max_retries=3, strategy="best")
    if not token:
        logger.error("❌ 无法获取可用token")
        return None
    return WoPanDownloader(token)

def get_realtime_api():
    """获取实时API实例（动态token）"""
    token = get_token_with_retry(max_retries=3, strategy="best")
    if not token:
        logger.error("❌ 无法获取可用token")
        return None
    return WoPanRealTimeAPI(token)

# 缓存文件结构
file_structure_cache = None
cache_update_time = None

def load_file_structure():
    """加载文件结构（静默模式，仅作为实时API的备用）"""
    global file_structure_cache, cache_update_time

    try:
        # 检查缓存是否需要更新（每5分钟更新一次）
        if (file_structure_cache is None or
            cache_update_time is None or
            (datetime.now() - cache_update_time).seconds > 300):

            with open("complete_folder_structure.json", "r", encoding="utf-8") as f:
                file_structure_cache = json.load(f)
                cache_update_time = datetime.now()
                logger.debug("✅ 文件结构缓存已更新")

        return file_structure_cache
    except FileNotFoundError:
        # 静默处理，不显示错误信息
        return None
    except Exception as e:
        logger.debug(f"加载文件结构失败: {e}")
        return None

def find_file_in_structure(folder_name: str, file_name: str, structure: Dict) -> Optional[Dict]:
    """在文件结构中查找文件"""
    if not structure:
        return None
    
    folder_structures = structure.get("folder_structures", [])
    
    for folder in folder_structures:
        if folder.get("name") == folder_name:
            files = folder.get("files", [])
            for file in files:
                if file.get("name") == file_name:
                    return file
    
    return None

def list_files_in_folder(folder_name: str, structure: Dict) -> List[Dict]:
    """列出文件夹中的所有文件"""
    if not structure:
        return []
    
    folder_structures = structure.get("folder_structures", [])
    
    for folder in folder_structures:
        if folder.get("name") == folder_name:
            return folder.get("files", [])
    
    return []

def list_all_folders(structure: Dict) -> List[str]:
    """列出所有文件夹名称"""
    if not structure:
        return []
    
    folders = []
    
    # 根目录文件夹
    root_files = structure.get("root_files", [])
    for item in root_files:
        if item.get("is_folder", False):
            folders.append(item.get("name", ""))
    
    return folders





@app.route('/api/download/', methods=['GET'])
def get_download_url():
    """获取文件下载地址"""
    try:
        # 获取url参数并解析
        url_param = request.args.get('url')

        if not url_param:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "缺少必需参数",
                "message": "请提供 url 参数，格式：folder/filename"
            }), 400

        # 解析url参数，分离文件夹和文件名
        url_parts = url_param.split('/')
        if len(url_parts) != 2:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "URL格式错误",
                "message": "url参数格式应为：folder/filename"
            }), 400

        folder_name = url_parts[0]
        file_name = url_parts[1]

        if not folder_name or not file_name:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "缺少必需参数",
                "message": "文件夹名称和文件名不能为空"
            }), 400
        
        # 加载文件结构（仅在实时API失败时需要）
        structure = None
        
        # 首先尝试实时API查找文件
        logger.info(f"🔍 尝试实时查找文件: {folder_name}/{file_name}")

        realtime_api = get_realtime_api()
        file_obj = None
        current_token = None

        if realtime_api:
            current_token = realtime_api.access_token
            try:
                file_obj = realtime_api.find_file_by_name(folder_name, file_name)
                if file_obj:
                    logger.info(f"✅ 实时API找到文件: {file_obj.name}")
                    report_success(current_token)
                    file_info = file_obj.to_dict()
                else:
                    logger.info(f"⚠️ 实时API未找到文件")
            except Exception as e:
                logger.error(f"❌ 实时API查找失败: {e}")
                report_error(str(e), current_token)

        if not file_obj:
            # 实时API失败，回退到缓存
            logger.info(f"⚠️ 回退到缓存查找")

            # 只有在需要时才加载缓存
            if structure is None:
                structure = load_file_structure()

            if structure:
                file_info = find_file_in_structure(folder_name, file_name, structure)
            else:
                file_info = None

            if not file_info:
                return jsonify({
                    "code": 401,
                    "success": False,
                    "error": "文件未找到",
                    "message": f"在文件夹 '{folder_name}' 中未找到文件 '{file_name}' (已尝试实时API和缓存)"
                }), 404
        
        # 获取下载链接
        fid = file_info.get('fid')
        if not fid:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "文件FID为空",
                "message": "无法获取文件的FID"
            }), 500
        
        # 获取下载链接
        downloader = get_downloader()
        if not downloader:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "无法获取下载器",
                "message": "Token服务不可用"
            }), 500

        download_token = downloader.access_token
        try:
            success, download_data = downloader.get_download_url_v2([fid])

            if success:
                report_success(download_token)
            else:
                report_error(str(download_data), download_token)

        except Exception as e:
            report_error(str(e), download_token)
            success = False
            download_data = str(e)

        if not success:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "获取下载链接失败",
                "message": str(download_data)
            }), 500
        
        # 解析下载链接
        download_url = ""
        if isinstance(download_data, dict) and "list" in download_data:
            download_list = download_data["list"]
            if download_list and len(download_list) > 0:
                download_url = download_list[0].get("downloadUrl", "")
        
        if not download_url:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "下载链接为空",
                "message": "API返回了空的下载链接"
            }), 500
        
        # 直接返回下载URL
        return jsonify({
            "code": 200,
            "url": download_url
        })
        
    except Exception as e:
        logger.error(f"获取下载地址异常: {e}")
        return jsonify({
            "code": 401,
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500

@app.route('/api/files', methods=['GET'])
def list_files():
    """列出指定文件夹中的文件 (支持实时和缓存)"""
    try:
        folder_name = request.args.get('folder')
        use_realtime = request.args.get('realtime', 'true').lower() == 'true'

        if not folder_name:
            return jsonify({
                "code": 401,
                "success": False,
                "error": "缺少必需参数",
                "message": "请提供 folder 参数"
            }), 400

        files_data = []
        source = "unknown"

        if use_realtime:
            # 尝试实时API
            logger.info(f"🔍 实时获取文件夹内容: {folder_name}")

            realtime_api = get_realtime_api()
            current_token = None

            if realtime_api:
                current_token = realtime_api.access_token
                try:
                    # 首先获取根目录找到目标文件夹
                    success, root_files = realtime_api.get_folder_contents("0")
                    if success:
                        target_folder = None
                        for file in root_files:
                            if file.is_folder and file.name == folder_name:
                                target_folder = file
                                break

                        if target_folder:
                            # 获取文件夹内容
                            success, folder_files = realtime_api.get_folder_contents(target_folder.id)
                            if success:
                                files_data = [f.to_dict() for f in folder_files]
                                source = "realtime"
                                report_success(current_token)
                                logger.info(f"✅ 实时API成功获取 {len(files_data)} 个文件")
                except Exception as e:
                    logger.error(f"❌ 实时API获取文件失败: {e}")
                    report_error(str(e), current_token)

        # 如果实时API失败，回退到缓存
        if not files_data:
            logger.info(f"⚠️ 实时API失败，使用缓存数据")
            structure = load_file_structure()
            if structure:
                cached_files = list_files_in_folder(folder_name, structure)
                files_data = cached_files
                source = "cache"
            else:
                return jsonify({
                    "code": 401,
                    "success": False,
                    "error": "无法获取文件列表",
                    "message": "实时API和缓存都不可用"
                }), 500

        return jsonify({
            "code": 200,
            "success": True,
            "data": {
                "folder": folder_name,
                "file_count": len(files_data),
                "source": source,
                "files": [
                    {
                        "name": f.get("name", ""),
                        "size": f.get("size", 0),
                        "create_time": f.get("create_time", ""),
                        "file_type": f.get("file_type", ""),
                        "type": f.get("type", "file")
                    } for f in files_data
                ]
            },
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"列出文件异常: {e}")
        return jsonify({
            "code": 401,
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500

@app.route('/api/folders', methods=['GET'])
def list_folders():
    """列出所有文件夹 (支持实时和缓存)"""
    try:
        use_realtime = request.args.get('realtime', 'true').lower() == 'true'

        folders_data = []
        source = "unknown"

        if use_realtime:
            # 尝试实时API获取根目录
            logger.info("🔍 实时获取根目录文件夹列表")

            realtime_api = get_realtime_api()
            current_token = None

            if realtime_api:
                current_token = realtime_api.access_token
                try:
                    success, root_files = realtime_api.get_folder_contents("0")
                    if success:
                        folders_data = [f.name for f in root_files if f.is_folder]
                        source = "realtime"
                        report_success(current_token)
                        logger.info(f"✅ 实时API成功获取 {len(folders_data)} 个文件夹")
                except Exception as e:
                    logger.error(f"❌ 实时API获取文件夹失败: {e}")
                    report_error(str(e), current_token)

        # 如果实时API失败，回退到缓存
        if not folders_data:
            logger.info("⚠️ 实时API失败，使用缓存数据")
            structure = load_file_structure()
            if structure:
                folders_data = list_all_folders(structure)
                source = "cache"
            else:
                return jsonify({
                    "code": 401,
                    "success": False,
                    "error": "无法获取文件夹列表",
                    "message": "实时API和缓存都不可用"
                }), 500

        return jsonify({
            "code": 200,
            "success": True,
            "data": folders_data,
            "count": len(folders_data),
            "source": source,
            "timestamp": datetime.now().isoformat()
        })

    except Exception as e:
        logger.error(f"列出文件夹异常: {e}")
        return jsonify({
            "code": 401,
            "success": False,
            "error": "服务器内部错误",
            "message": str(e)
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        "status": "healthy",
        "service": "WoPan Download API",
        "timestamp": datetime.now().isoformat()
    })

if __name__ == '__main__':
    logger.info("🚀 启动联通网盘Web API服务 (支持实时API)")
    logger.info("=" * 60)
    logger.info("📋 API端点:")
    logger.info("   GET  /api/download/?url=folder/filename    - 获取文件下载地址 (实时+缓存)")
    logger.info("   GET  /api/files?folder=name&realtime=true  - 列出文件夹内容 (实时+缓存)")
    logger.info("   GET  /api/folders?realtime=true            - 列出所有文件夹 (实时+缓存)")
    logger.info("   GET  /health                               - 健康检查")
    logger.info("=" * 60)
    logger.info("🌐 API服务地址: http://localhost:5000")
    logger.info("🔄 实时API: 自动获取最新文件列表")
    logger.info("💾 缓存回退: 实时API失败时使用缓存数据")
    
    # 测试实时API连接
    logger.info("🔍 测试实时API连接...")
    try:
        realtime_api = get_realtime_api()
        if realtime_api:
            success, files = realtime_api.get_folder_contents("0")
            if success:
                logger.info(f"✅ 实时API连接成功，根目录有 {len(files)} 个项目")
                report_success(realtime_api.access_token)
            else:
                logger.warning("⚠️ 实时API连接失败，将依赖缓存数据")
                report_error("API连接失败", realtime_api.access_token)
        else:
            logger.warning("⚠️ 无法获取token，实时API不可用")
    except Exception as e:
        logger.warning(f"⚠️ 实时API测试异常: {e}")

    # 静默检查缓存文件结构作为备用
    structure = load_file_structure()
    if structure:
        logger.info("✅ 缓存文件结构可用 (作为备用)")
    else:
        logger.info("💡 使用纯实时API模式 (无缓存依赖)")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
