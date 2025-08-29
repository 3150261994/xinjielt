#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘可视化下载器
支持文件浏览、下载链接获取等功能
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog
import threading
import json
import requests
import hashlib
import random
import base64
import time
import os
import webbrowser
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

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
        
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if self.size < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} PB"


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
        """使用2C接口上传文件（参考Go SDK实现）"""
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)

            # 上传服务器URL
            upload_url = "https://tjupload.pan.wo.cn/openapi/client/upload2C"

            # 生成批次号
            import datetime
            batch_no = datetime.datetime.now().strftime("%Y%m%d%H%M%S")

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

            # 计算分片信息 - 增大分片以提高速度
            part_size = 32 * 1024 * 1024  # 32MB per part (增大分片)
            total_parts = (file_size + part_size - 1) // part_size  # 向上取整

            # 生成唯一ID
            import time
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

                    # 发送上传请求 - 优化网络配置
                    headers = {
                        'Origin': 'https://pan.wo.cn',
                        'Referer': 'https://pan.wo.cn/',
                        'User-Agent': self.DEFAULT_UA,
                        'Connection': 'keep-alive',
                        'Accept-Encoding': 'gzip, deflate'
                    }

                    # 创建专门的上传会话，优化网络性能
                    upload_session = requests.Session()
                    upload_session.headers.update(headers)

                    # 配置连接池和重试
                    from requests.adapters import HTTPAdapter
                    from urllib3.util.retry import Retry

                    retry_strategy = Retry(
                        total=3,
                        backoff_factor=1,
                        status_forcelist=[429, 500, 502, 503, 504],
                    )

                    adapter = HTTPAdapter(
                        pool_connections=10,
                        pool_maxsize=20,
                        max_retries=retry_strategy
                    )

                    upload_session.mount("http://", adapter)
                    upload_session.mount("https://", adapter)

                    response = upload_session.post(
                        upload_url,
                        data=form_data,
                        files=files,
                        timeout=(30, 300),  # (连接超时, 读取超时)
                        stream=False  # 不使用流式上传，一次性发送
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

        # 添加psToken（如果需要）
        # 注意：这里可能需要psToken，但我们先尝试不加

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


class WoPanGUI:
    """联通网盘GUI界面"""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("联通网盘下载器 v1.0")
        self.root.geometry("900x700")
        self.root.resizable(True, True)

        # 设置图标（如果有的话）
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        self.api = None
        self.current_folder_id = "0"
        self.folder_history = []  # 文件夹历史
        self.current_files = []

        self.setup_ui()
        self.load_config()

    def setup_ui(self):
        """设置UI界面"""
        # 创建主框架
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        main_frame.rowconfigure(2, weight=1)

        # Token输入区域
        token_frame = ttk.LabelFrame(main_frame, text="Token配置", padding="5")
        token_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        token_frame.columnconfigure(1, weight=1)

        ttk.Label(token_frame, text="Token:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        self.token_var = tk.StringVar()
        self.token_entry = ttk.Entry(token_frame, textvariable=self.token_var, width=50)
        self.token_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        self.connect_btn = ttk.Button(token_frame, text="连接", command=self.connect_api)
        self.connect_btn.grid(row=0, column=2, padx=(5, 0))

        # 导航栏
        nav_frame = ttk.Frame(main_frame)
        nav_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        nav_frame.columnconfigure(1, weight=1)

        self.back_btn = ttk.Button(nav_frame, text="← 返回", command=self.go_back, state=tk.DISABLED)
        self.back_btn.grid(row=0, column=0, padx=(0, 5))

        self.path_var = tk.StringVar(value="根目录")
        self.path_label = ttk.Label(nav_frame, textvariable=self.path_var, background="white", relief="sunken")
        self.path_label.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))

        self.refresh_btn = ttk.Button(nav_frame, text="🔄 刷新", command=self.refresh_current_folder)
        self.refresh_btn.grid(row=0, column=2)

        # 文件列表
        list_frame = ttk.LabelFrame(main_frame, text="文件列表", padding="5")
        list_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建Treeview
        columns = ("name", "type", "size", "time")
        self.file_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=15)

        # 设置列标题
        self.file_tree.heading("#0", text="")
        self.file_tree.heading("name", text="文件名")
        self.file_tree.heading("type", text="类型")
        self.file_tree.heading("size", text="大小")
        self.file_tree.heading("time", text="创建时间")

        # 设置列宽
        self.file_tree.column("#0", width=30, minwidth=30)
        self.file_tree.column("name", width=300, minwidth=200)
        self.file_tree.column("type", width=80, minwidth=60)
        self.file_tree.column("size", width=100, minwidth=80)
        self.file_tree.column("time", width=150, minwidth=120)

        # 添加滚动条
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.file_tree.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.file_tree.xview)
        self.file_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        self.file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 绑定双击事件
        self.file_tree.bind("<Double-1>", self.on_item_double_click)
        self.file_tree.bind("<Button-3>", self.on_item_right_click)  # 右键菜单

        # 操作按钮区域
        btn_frame = ttk.Frame(main_frame)
        btn_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # 下载相关按钮
        download_frame = ttk.LabelFrame(btn_frame, text="下载操作", padding="5")
        download_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))

        self.download_btn = ttk.Button(download_frame, text="获取下载链接", command=self.get_download_link, state=tk.DISABLED)
        self.download_btn.grid(row=0, column=0, padx=(0, 5))

        self.copy_btn = ttk.Button(download_frame, text="复制链接", command=self.copy_download_link, state=tk.DISABLED)
        self.copy_btn.grid(row=0, column=1, padx=(0, 5))

        self.open_btn = ttk.Button(download_frame, text="浏览器打开", command=self.open_in_browser, state=tk.DISABLED)
        self.open_btn.grid(row=0, column=2, padx=(0, 5))

        # 上传相关按钮
        upload_frame = ttk.LabelFrame(btn_frame, text="上传操作", padding="5")
        upload_frame.grid(row=0, column=1, sticky=(tk.W, tk.E))
        btn_frame.columnconfigure(1, weight=1)

        self.upload_file_btn = ttk.Button(upload_frame, text="� 上传文件", command=self.select_and_upload_file, state=tk.DISABLED)
        self.upload_file_btn.grid(row=0, column=0, padx=(0, 5))

        self.upload_folder_btn = ttk.Button(upload_frame, text="📁 上传文件夹", command=self.select_and_upload_folder, state=tk.DISABLED)
        self.upload_folder_btn.grid(row=1, column=0, padx=(0, 5), pady=(5, 0))

        self.create_folder_btn = ttk.Button(upload_frame, text="📂 新建文件夹", command=self.create_new_folder, state=tk.DISABLED)
        self.create_folder_btn.grid(row=0, column=1, padx=(0, 5))

        self.delete_btn = ttk.Button(upload_frame, text="🗑️ 删除", command=self.delete_selected_item, state=tk.DISABLED)
        self.delete_btn.grid(row=0, column=2, padx=(0, 5))

        # 状态栏
        self.status_var = tk.StringVar(value="请输入Token并连接")
        self.status_bar = ttk.Label(main_frame, textvariable=self.status_var, relief="sunken")
        self.status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(10, 0))

        # 存储下载链接
        self.current_download_url = ""

    def load_config(self):
        """加载配置"""
        try:
            with open("wopan_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                self.token_var.set(config.get("token", ""))
        except:
            pass

    def save_config(self):
        """保存配置"""
        try:
            config = {"token": self.token_var.get()}
            with open("wopan_config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except:
            pass

    def connect_api(self):
        """连接API"""
        token = self.token_var.get().strip()
        if not token:
            messagebox.showerror("错误", "请输入Token")
            return

        self.status_var.set("正在连接...")
        self.connect_btn.config(state=tk.DISABLED)

        def connect_thread():
            try:
                self.api = WoPanAPI(token)
                success, files = self.api.get_folder_contents("0")

                if success:
                    self.root.after(0, self.on_connect_success, files)
                else:
                    self.root.after(0, self.on_connect_failed, "连接失败，请检查Token")
            except Exception as e:
                self.root.after(0, self.on_connect_failed, f"连接异常: {str(e)}")

        threading.Thread(target=connect_thread, daemon=True).start()

    def on_connect_success(self, files):
        """连接成功回调"""
        self.status_var.set("连接成功")
        self.connect_btn.config(state=tk.NORMAL)
        self.current_files = files
        self.refresh_file_list()
        self.save_config()

        # 启用相关按钮
        self.refresh_btn.config(state=tk.NORMAL)
        self.upload_file_btn.config(state=tk.NORMAL)
        self.upload_folder_btn.config(state=tk.NORMAL)
        self.create_folder_btn.config(state=tk.NORMAL)
        self.delete_btn.config(state=tk.NORMAL)

    def on_connect_failed(self, error_msg):
        """连接失败回调"""
        self.status_var.set(f"连接失败: {error_msg}")
        self.connect_btn.config(state=tk.NORMAL)
        messagebox.showerror("连接失败", error_msg)

    def refresh_file_list(self):
        """刷新文件列表"""
        # 清空现有项目
        for item in self.file_tree.get_children():
            self.file_tree.delete(item)

        # 添加文件和文件夹
        for file_obj in self.current_files:
            icon = "📁" if file_obj.is_folder else "📄"
            file_type = "文件夹" if file_obj.is_folder else "文件"
            size_str = "-" if file_obj.is_folder else file_obj.size_str

            # 格式化时间
            create_time = ""
            if file_obj.create_time and len(file_obj.create_time) == 14:
                try:
                    dt = datetime.strptime(file_obj.create_time, '%Y%m%d%H%M%S')
                    create_time = dt.strftime('%Y-%m-%d %H:%M')
                except:
                    create_time = file_obj.create_time

            self.file_tree.insert("", "end", text=icon, values=(
                file_obj.name,
                file_type,
                size_str,
                create_time
            ), tags=(file_obj.fid, file_obj.id, "folder" if file_obj.is_folder else "file"))

    def on_item_double_click(self, event):
        """双击事件处理"""
        selection = self.file_tree.selection()
        if not selection:
            return

        item = selection[0]
        tags = self.file_tree.item(item, "tags")

        if len(tags) >= 3 and tags[2] == "folder":
            # 进入文件夹
            folder_id = tags[1]
            folder_name = self.file_tree.item(item, "values")[0]
            self.enter_folder(folder_id, folder_name)
        elif len(tags) >= 3 and tags[2] == "file":
            # 获取文件下载链接
            self.get_download_link()

    def enter_folder(self, folder_id, folder_name):
        """进入文件夹"""
        self.status_var.set(f"正在加载文件夹: {folder_name}")

        def load_folder_thread():
            try:
                success, files = self.api.get_folder_contents(folder_id)
                if success:
                    self.root.after(0, self.on_folder_loaded, folder_id, folder_name, files)
                else:
                    self.root.after(0, self.on_folder_load_failed, "加载文件夹失败")
            except Exception as e:
                self.root.after(0, self.on_folder_load_failed, f"加载异常: {str(e)}")

        threading.Thread(target=load_folder_thread, daemon=True).start()

    def on_folder_loaded(self, folder_id, folder_name, files):
        """文件夹加载成功"""
        # 保存历史
        self.folder_history.append({
            'id': self.current_folder_id,
            'name': self.path_var.get()
        })

        self.current_folder_id = folder_id
        self.current_files = files

        # 更新路径显示
        current_path = self.path_var.get()
        if current_path == "根目录":
            new_path = folder_name
        else:
            new_path = f"{current_path}/{folder_name}"
        self.path_var.set(new_path)

        self.refresh_file_list()
        self.back_btn.config(state=tk.NORMAL)
        self.status_var.set(f"已加载 {len(files)} 个项目")

    def on_folder_load_failed(self, error_msg):
        """文件夹加载失败"""
        self.status_var.set(f"加载失败: {error_msg}")
        messagebox.showerror("加载失败", error_msg)

    def go_back(self):
        """返回上级目录"""
        if not self.folder_history:
            return

        last_folder = self.folder_history.pop()
        self.current_folder_id = last_folder['id']
        self.path_var.set(last_folder['name'])

        if not self.folder_history:
            self.back_btn.config(state=tk.DISABLED)

        self.refresh_current_folder()

    def refresh_current_folder(self):
        """刷新当前文件夹"""
        if not self.api:
            return

        self.status_var.set("正在刷新...")

        def refresh_thread():
            try:
                success, files = self.api.get_folder_contents(self.current_folder_id)
                if success:
                    self.root.after(0, self.on_refresh_success, files)
                else:
                    self.root.after(0, self.on_refresh_failed, "刷新失败")
            except Exception as e:
                self.root.after(0, self.on_refresh_failed, f"刷新异常: {str(e)}")

        threading.Thread(target=refresh_thread, daemon=True).start()

    def on_refresh_success(self, files):
        """刷新成功"""
        self.current_files = files
        self.refresh_file_list()
        self.status_var.set(f"已刷新，共 {len(files)} 个项目")

    def on_refresh_failed(self, error_msg):
        """刷新失败"""
        self.status_var.set(f"刷新失败: {error_msg}")
        messagebox.showerror("刷新失败", error_msg)

    def get_download_link(self):
        """获取下载链接"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择一个文件")
            return

        item = selection[0]
        tags = self.file_tree.item(item, "tags")

        if len(tags) >= 3 and tags[2] == "folder":
            messagebox.showwarning("提示", "请选择文件，不是文件夹")
            return

        fid = tags[0]
        file_name = self.file_tree.item(item, "values")[0]

        self.status_var.set(f"正在获取下载链接: {file_name}")
        self.download_btn.config(state=tk.DISABLED)

        def download_thread():
            try:
                success, result = self.api.get_download_url(fid)
                if success:
                    self.root.after(0, self.on_download_success, result, file_name)
                else:
                    self.root.after(0, self.on_download_failed, result)
            except Exception as e:
                self.root.after(0, self.on_download_failed, f"获取异常: {str(e)}")

        threading.Thread(target=download_thread, daemon=True).start()

    def on_download_success(self, download_url, file_name):
        """获取下载链接成功"""
        self.current_download_url = download_url
        self.status_var.set(f"已获取下载链接: {file_name}")
        self.download_btn.config(state=tk.NORMAL)
        self.copy_btn.config(state=tk.NORMAL)
        self.open_btn.config(state=tk.NORMAL)

        # 显示下载链接对话框
        self.show_download_dialog(file_name, download_url)

    def on_download_failed(self, error_msg):
        """获取下载链接失败"""
        self.status_var.set(f"获取失败: {error_msg}")
        self.download_btn.config(state=tk.NORMAL)
        messagebox.showerror("获取失败", error_msg)

    def show_download_dialog(self, file_name, download_url):
        """显示下载链接对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"下载链接 - {file_name}")
        dialog.geometry("600x300")
        dialog.resizable(True, True)

        # 设置对话框居中
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text=f"文件: {file_name}").pack(anchor=tk.W, pady=(0, 10))

        ttk.Label(frame, text="下载链接:").pack(anchor=tk.W)

        text_widget = scrolledtext.ScrolledText(frame, height=8, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True, pady=(5, 10))
        text_widget.insert(tk.END, download_url)
        text_widget.config(state=tk.DISABLED)

        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        ttk.Button(btn_frame, text="复制链接",
                  command=lambda: self.copy_to_clipboard(download_url)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="浏览器打开",
                  command=lambda: webbrowser.open(download_url)).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(btn_frame, text="关闭",
                  command=dialog.destroy).pack(side=tk.RIGHT)

    def copy_download_link(self):
        """复制下载链接"""
        if self.current_download_url:
            self.copy_to_clipboard(self.current_download_url)
            self.status_var.set("下载链接已复制到剪贴板")
        else:
            messagebox.showwarning("提示", "没有可复制的下载链接")

    def copy_to_clipboard(self, text):
        """复制文本到剪贴板"""
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()

    def open_in_browser(self):
        """在浏览器中打开下载链接"""
        if self.current_download_url:
            webbrowser.open(self.current_download_url)
            self.status_var.set("已在浏览器中打开下载链接")
        else:
            messagebox.showwarning("提示", "没有可打开的下载链接")

    def on_item_right_click(self, event):
        """右键菜单"""
        selection = self.file_tree.selection()
        if not selection:
            return

        # 创建右键菜单
        context_menu = tk.Menu(self.root, tearoff=0)

        item = selection[0]
        tags = self.file_tree.item(item, "tags")

        if len(tags) >= 3 and tags[2] == "folder":
            context_menu.add_command(label="进入文件夹", command=lambda: self.enter_folder(tags[1], self.file_tree.item(item, "values")[0]))
        else:
            context_menu.add_command(label="获取下载链接", command=self.get_download_link)

        context_menu.add_separator()
        context_menu.add_command(label="�️ 删除", command=self.delete_selected_item)
        context_menu.add_separator()
        context_menu.add_command(label="�📁 上传文件", command=self.select_and_upload_file)
        context_menu.add_command(label="上传文件夹", command=self.select_and_upload_folder)
        context_menu.add_command(label="📂 新建文件夹", command=self.create_new_folder)
        context_menu.add_separator()
        context_menu.add_command(label="刷新", command=self.refresh_current_folder)

        try:
            context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            context_menu.grab_release()

    def select_and_upload_file(self):
        """选择并上传文件（支持多文件选择）"""
        file_paths = filedialog.askopenfilenames(  # 注意这里改为askopenfilenames
            title="选择要上传的文件（可多选）",
            filetypes=[
                ("所有文件", "*.*"),
                ("视频文件", "*.mp4 *.avi *.mkv *.mov *.wmv"),
                ("图片文件", "*.jpg *.jpeg *.png *.gif *.bmp"),
                ("文档文件", "*.pdf *.doc *.docx *.txt *.xlsx"),
                ("压缩文件", "*.zip *.rar *.7z")
            ]
        )

        if file_paths:
            if len(file_paths) == 1:
                # 单文件上传
                self.upload_file_to_current_folder(file_paths[0])
            else:
                # 多文件上传
                self.upload_multiple_files_to_current_folder(file_paths)

    def select_and_upload_folder(self):
        """选择并上传文件夹"""
        folder_path = filedialog.askdirectory(
            title="选择要上传的文件夹"
        )

        if folder_path:
            self.upload_folder_to_current_folder(folder_path)

    def upload_file_to_current_folder(self, file_path: str):
        """上传文件到当前文件夹"""
        if not self.api:
            messagebox.showerror("错误", "请先连接API")
            return

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)

        # 显示上传进度对话框
        self.show_upload_progress_dialog(file_path, file_name, file_size)

    def upload_multiple_files_to_current_folder(self, file_paths: list):
        """上传多个文件到当前文件夹"""
        if not self.api:
            messagebox.showerror("错误", "请先连接API")
            return

        # 准备文件列表
        file_list = []
        total_size = 0

        for file_path in file_paths:
            if os.path.isfile(file_path):
                file_name = os.path.basename(file_path)
                file_size = os.path.getsize(file_path)
                file_list.append({
                    'full_path': file_path,
                    'relative_path': file_name,  # 多文件上传时，相对路径就是文件名
                    'size': file_size
                })
                total_size += file_size

        if not file_list:
            messagebox.showwarning("提示", "没有有效的文件")
            return

        # 显示多文件上传进度对话框
        self.show_multiple_files_upload_progress_dialog(file_list, total_size)

    def show_multiple_files_upload_progress_dialog(self, file_list: List, total_size: int):
        """显示多文件上传进度对话框"""
        dialog = tk.Toplevel(self.root)
        dialog.title(f"上传多个文件 ({len(file_list)} 个文件)")
        dialog.geometry("800x600")
        dialog.resizable(True, True)

        # 设置对话框居中
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 文件信息
        info_frame = ttk.LabelFrame(frame, text="上传信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)

        ttk.Label(info_grid, text="文件数量:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=str(len(file_list))).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Label(info_grid, text="总大小:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=self.format_file_size(total_size)).grid(row=0, column=3, sticky=tk.W)

        ttk.Label(info_grid, text="上传到:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=self.path_var.get()).grid(row=1, column=1, sticky=tk.W, columnspan=3)

        # 总体进度
        progress_frame = ttk.LabelFrame(frame, text="总体进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        overall_progress_var = tk.DoubleVar()
        overall_progress_bar = ttk.Progressbar(progress_frame, variable=overall_progress_var, maximum=100)
        overall_progress_bar.pack(fill=tk.X, pady=(0, 5))

        overall_status_var = tk.StringVar(value="准备上传...")
        overall_status_label = ttk.Label(progress_frame, textvariable=overall_status_var)
        overall_status_label.pack(anchor=tk.W)

        # 文件列表
        list_frame = ttk.LabelFrame(frame, text="文件上传状态", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建Treeview显示文件列表
        columns = ("status", "progress", "size")
        file_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=12)

        # 设置列标题
        file_tree.heading("#0", text="文件名")
        file_tree.heading("status", text="状态")
        file_tree.heading("progress", text="进度")
        file_tree.heading("size", text="大小")

        # 设置列宽
        file_tree.column("#0", width=300, minwidth=200)
        file_tree.column("status", width=120, minwidth=80)
        file_tree.column("progress", width=80, minwidth=60)
        file_tree.column("size", width=100, minwidth=80)

        # 添加滚动条
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=file_tree.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=file_tree.xview)
        file_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 初始化文件列表
        file_items = {}
        for file_info in file_list:
            item_id = file_tree.insert("", "end",
                                     text=file_info['relative_path'],
                                     values=("等待中", "0%", self.format_file_size(file_info['size'])),
                                     tags=("waiting",))
            file_items[file_info['relative_path']] = item_id

        # 配置标签颜色
        file_tree.tag_configure("waiting", foreground="gray")
        file_tree.tag_configure("uploading", foreground="blue")
        file_tree.tag_configure("success", foreground="green")
        file_tree.tag_configure("failed", foreground="red")

        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)

        close_btn = ttk.Button(btn_frame, text="关闭", command=dialog.destroy, state=tk.DISABLED)
        close_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # 开始并发上传多个文件
        def upload_multiple_files_thread():
            try:
                import concurrent.futures
                import threading

                print(f"🚀 DEBUG: 开始并发上传 {len(file_list)} 个文件")

                uploaded_files = 0
                failed_files = 0
                completed_files = 0
                lock = threading.Lock()

                def upload_single_file(file_info):
                    """上传单个文件的函数"""
                    nonlocal uploaded_files, failed_files, completed_files

                    relative_path = file_info['relative_path']
                    file_full_path = file_info['full_path']
                    file_size = file_info['size']
                    item_id = file_items[relative_path]

                    print(f"📤 DEBUG: 开始上传文件 {relative_path} (线程: {threading.current_thread().name})")

                    try:
                        # 更新文件状态为"上传中"
                        dialog.after(0, lambda: file_tree.item(item_id, values=("上传中", "0%", self.format_file_size(file_size)), tags=("uploading",)))

                        # 为每个线程创建独立的API实例（避免会话冲突）
                        thread_api = WoPanAPI(self.api.access_token)

                        # 上传文件到当前文件夹
                        def file_progress_callback(progress):
                            dialog.after(0, lambda p=progress: file_tree.item(item_id, values=("上传中", f"{p:.1f}%", self.format_file_size(file_size))))

                        success, result = thread_api.upload_file_2c(
                            file_full_path, self.current_folder_id, file_progress_callback
                        )

                        with lock:
                            completed_files += 1

                            if success:
                                uploaded_files += 1

                                # 标记为成功并在3秒后移除
                                dialog.after(0, lambda: file_tree.item(item_id, values=("✅ 成功", "100%", self.format_file_size(file_size)), tags=("success",)))

                                # 3秒后移除成功的项目
                                def remove_success_item():
                                    try:
                                        file_tree.delete(item_id)
                                    except:
                                        pass

                                dialog.after(3000, remove_success_item)
                            else:
                                # 上传失败，用红字显示错误信息
                                failed_files += 1
                                error_msg = result[:50] + "..." if len(result) > 50 else result
                                dialog.after(0, lambda: file_tree.item(item_id, values=(f"❌ {error_msg}", "0%", self.format_file_size(file_size)), tags=("failed",)))

                            # 更新总体进度
                            progress = (completed_files / len(file_list)) * 100
                            dialog.after(0, lambda: overall_progress_var.set(progress))
                            dialog.after(0, lambda: overall_status_var.set(f"已处理 {completed_files}/{len(file_list)} 个文件 (成功: {uploaded_files}, 失败: {failed_files})"))

                            # 检查是否全部完成
                            if completed_files == len(file_list):
                                dialog.after(0, lambda: cancel_btn.config(state=tk.DISABLED))
                                dialog.after(0, lambda: close_btn.config(state=tk.NORMAL))
                                dialog.after(0, lambda: overall_status_var.set(f"上传完成！成功: {uploaded_files}, 失败: {failed_files}"))

                                if failed_files == 0:
                                    # 全部成功，5秒后自动关闭
                                    dialog.after(5000, dialog.destroy)

                                # 刷新文件列表
                                self.root.after(1000, self.refresh_current_folder)

                        return success, result

                    except Exception as e:
                        with lock:
                            failed_files += 1
                            completed_files += 1
                            error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
                            dialog.after(0, lambda: file_tree.item(item_id, values=(f"❌ {error_msg}", "0%", self.format_file_size(file_size)), tags=("failed",)))
                        return False, str(e)

                # 尝试并发上传，如果失败则回退到顺序上传
                try:
                    max_workers = min(2, len(file_list))  # 减少并发数，避免API限制
                    dialog.after(0, lambda: overall_status_var.set(f"尝试并发上传 ({max_workers} 个并发)..."))

                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # 提交所有上传任务
                        futures = [executor.submit(upload_single_file, file_info) for file_info in file_list]

                        # 等待所有任务完成
                        concurrent.futures.wait(futures)

                except Exception as e:
                    print(f"⚠️ 并发上传失败，回退到顺序上传: {e}")
                    dialog.after(0, lambda: overall_status_var.set("并发失败，使用顺序上传..."))

                    # 回退到顺序上传
                    for file_info in file_list:
                        try:
                            upload_single_file(file_info)
                        except Exception as e:
                            print(f"顺序上传也失败: {e}")
                            continue

            except Exception as e:
                dialog.after(0, lambda: self.on_upload_failed(dialog, f"上传异常: {str(e)}"))

        threading.Thread(target=upload_multiple_files_thread, daemon=True).start()

    def upload_folder_to_current_folder(self, folder_path: str):
        """上传文件夹到当前文件夹"""
        if not self.api:
            messagebox.showerror("错误", "请先连接API")
            return

        folder_name = os.path.basename(folder_path)

        # 收集文件夹中的所有文件
        file_list = []
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_full_path = os.path.join(root, file)
                relative_path = os.path.relpath(file_full_path, folder_path)
                file_list.append({
                    'full_path': file_full_path,
                    'relative_path': relative_path,
                    'size': os.path.getsize(file_full_path)
                })

        if not file_list:
            messagebox.showwarning("提示", "文件夹为空")
            return

        total_size = sum(f['size'] for f in file_list)

        # 显示文件夹上传进度对话框
        self.show_folder_upload_progress_dialog(folder_path, folder_name, file_list, total_size)

    def show_upload_progress_dialog(self, file_path: str, file_name: str, file_size: int):
        """显示上传进度对话框"""
        print(f"🔍 DEBUG: 调用单文件上传对话框 - 文件: {file_name}")

        dialog = tk.Toplevel(self.root)
        dialog.title(f"📄 单文件上传 - {file_name}")
        dialog.geometry("500x300")
        dialog.resizable(False, False)

        # 设置对话框居中
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="20")
        frame.pack(fill=tk.BOTH, expand=True)

        # 文件信息
        info_frame = ttk.LabelFrame(frame, text="文件信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(info_frame, text=f"文件名: {file_name}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"文件大小: {self.format_file_size(file_size)}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"上传到: {self.path_var.get()}").pack(anchor=tk.W)

        # 进度条
        progress_frame = ttk.LabelFrame(frame, text="上传进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        progress_var = tk.DoubleVar()
        progress_bar = ttk.Progressbar(progress_frame, variable=progress_var, maximum=100)
        progress_bar.pack(fill=tk.X, pady=(0, 5))

        status_var = tk.StringVar(value="准备上传...")
        status_label = ttk.Label(progress_frame, textvariable=status_var)
        status_label.pack(anchor=tk.W)

        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)

        # 开始上传
        def upload_thread():
            try:
                # 直接使用2C接口上传
                status_var.set("正在上传文件...")
                dialog.update()

                def progress_callback(progress):
                    dialog.after(0, lambda: progress_var.set(progress))
                    dialog.after(0, lambda: status_var.set(f"上传中... {progress:.1f}%"))

                success, result = self.api.upload_file_2c(file_path, self.current_folder_id, progress_callback)
                if not success:
                    dialog.after(0, lambda: self.on_upload_failed(dialog, f"文件上传失败: {result}"))
                    return

                # 上传成功
                dialog.after(0, lambda: self.on_upload_success(dialog, file_name, result))

            except Exception as e:
                dialog.after(0, lambda: self.on_upload_failed(dialog, f"上传异常: {str(e)}"))

        threading.Thread(target=upload_thread, daemon=True).start()

    def show_folder_upload_progress_dialog(self, folder_path: str, folder_name: str, file_list: List, total_size: int):
        """显示文件夹上传进度对话框"""
        print(f"🔍 DEBUG: 调用文件夹上传对话框 - 文件夹: {folder_name}, 文件数: {len(file_list)}")

        dialog = tk.Toplevel(self.root)
        dialog.title(f"📁 批量上传文件夹 - {folder_name} ({len(file_list)}个文件)")
        dialog.geometry("800x600")
        dialog.resizable(True, True)

        # 设置对话框居中
        dialog.transient(self.root)
        dialog.grab_set()

        frame = ttk.Frame(dialog, padding="10")
        frame.pack(fill=tk.BOTH, expand=True)

        # 文件夹信息
        info_frame = ttk.LabelFrame(frame, text="文件夹信息", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 10))

        info_grid = ttk.Frame(info_frame)
        info_grid.pack(fill=tk.X)
        info_grid.columnconfigure(1, weight=1)
        info_grid.columnconfigure(3, weight=1)

        ttk.Label(info_grid, text="文件夹:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=folder_name).grid(row=0, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Label(info_grid, text="文件数量:").grid(row=0, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=str(len(file_list))).grid(row=0, column=3, sticky=tk.W)

        ttk.Label(info_grid, text="总大小:").grid(row=1, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=self.format_file_size(total_size)).grid(row=1, column=1, sticky=tk.W, padx=(0, 20))
        ttk.Label(info_grid, text="上传到:").grid(row=1, column=2, sticky=tk.W, padx=(0, 5))
        ttk.Label(info_grid, text=self.path_var.get()).grid(row=1, column=3, sticky=tk.W)

        # 总体进度
        progress_frame = ttk.LabelFrame(frame, text="总体进度", padding="10")
        progress_frame.pack(fill=tk.X, pady=(0, 10))

        overall_progress_var = tk.DoubleVar()
        overall_progress_bar = ttk.Progressbar(progress_frame, variable=overall_progress_var, maximum=100)
        overall_progress_bar.pack(fill=tk.X, pady=(0, 5))

        overall_status_var = tk.StringVar(value="准备上传...")
        overall_status_label = ttk.Label(progress_frame, textvariable=overall_status_var)
        overall_status_label.pack(anchor=tk.W)

        # 文件列表
        list_frame = ttk.LabelFrame(frame, text="文件上传状态", padding="10")
        list_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        # 创建Treeview显示文件列表
        columns = ("status", "progress", "size")
        file_tree = ttk.Treeview(list_frame, columns=columns, show="tree headings", height=12)

        # 设置列标题
        file_tree.heading("#0", text="文件路径")
        file_tree.heading("status", text="状态")
        file_tree.heading("progress", text="进度")
        file_tree.heading("size", text="大小")

        # 设置列宽
        file_tree.column("#0", width=300, minwidth=200)
        file_tree.column("status", width=80, minwidth=60)
        file_tree.column("progress", width=80, minwidth=60)
        file_tree.column("size", width=100, minwidth=80)

        # 添加滚动条
        scrollbar_v = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=file_tree.yview)
        scrollbar_h = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=file_tree.xview)
        file_tree.configure(yscrollcommand=scrollbar_v.set, xscrollcommand=scrollbar_h.set)

        file_tree.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        scrollbar_v.grid(row=0, column=1, sticky=(tk.N, tk.S))
        scrollbar_h.grid(row=1, column=0, sticky=(tk.W, tk.E))

        # 初始化文件列表
        file_items = {}  # 存储文件项ID的映射
        for file_info in file_list:
            item_id = file_tree.insert("", "end",
                                     text=file_info['relative_path'],
                                     values=("等待中", "0%", self.format_file_size(file_info['size'])),
                                     tags=("waiting",))
            file_items[file_info['relative_path']] = item_id

        # 配置标签颜色
        file_tree.tag_configure("waiting", foreground="gray")
        file_tree.tag_configure("uploading", foreground="blue")
        file_tree.tag_configure("success", foreground="green")
        file_tree.tag_configure("failed", foreground="red")

        # 按钮
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(fill=tk.X)

        cancel_btn = ttk.Button(btn_frame, text="取消", command=dialog.destroy)
        cancel_btn.pack(side=tk.RIGHT)

        close_btn = ttk.Button(btn_frame, text="关闭", command=dialog.destroy, state=tk.DISABLED)
        close_btn.pack(side=tk.RIGHT, padx=(0, 5))

        # 开始上传文件夹
        def upload_folder_thread():
            try:
                # 1. 创建根文件夹
                overall_status_var.set(f"创建文件夹: {folder_name}")
                dialog.update()

                success, folder_id = self.api.create_directory("0", self.current_folder_id, folder_name, "")
                if not success:
                    dialog.after(0, lambda: self.on_folder_upload_failed(dialog, f"创建文件夹失败: {folder_id}"))
                    return

                # 2. 创建文件夹结构并并发上传文件
                import concurrent.futures
                import threading

                uploaded_files = 0
                failed_files = 0
                completed_files = 0
                folder_cache = {folder_name: folder_id}  # 缓存已创建的文件夹
                lock = threading.Lock()

                print(f"🚀 DEBUG: 开始并发上传文件夹中的 {len(file_list)} 个文件")

                def upload_folder_file(file_info):
                    """上传文件夹中的单个文件"""
                    nonlocal uploaded_files, failed_files, completed_files

                    relative_path = file_info['relative_path']
                    file_full_path = file_info['full_path']
                    file_size = file_info['size']
                    item_id = file_items[relative_path]

                    print(f"📤 DEBUG: 开始上传文件夹文件 {relative_path} (线程: {threading.current_thread().name})")

                    try:
                        # 更新文件状态为"上传中"
                        dialog.after(0, lambda: file_tree.item(item_id, values=("上传中", "0%", self.format_file_size(file_size)), tags=("uploading",)))

                        # 确保目录结构存在（需要加锁，避免并发创建同一目录）
                        with lock:
                            target_folder_id = self.ensure_folder_structure(
                                relative_path, folder_id, folder_cache
                            )

                        if not target_folder_id:
                            # 目录创建失败
                            with lock:
                                failed_files += 1
                                completed_files += 1
                            dialog.after(0, lambda: file_tree.item(item_id, values=("目录创建失败", "0%", self.format_file_size(file_size)), tags=("failed",)))
                            return False, "目录创建失败"

                        # 为每个线程创建独立的API实例
                        thread_api = WoPanAPI(self.api.access_token)

                        # 上传文件
                        def file_progress_callback(progress):
                            dialog.after(0, lambda p=progress: file_tree.item(item_id, values=("上传中", f"{p:.1f}%", self.format_file_size(file_size))))

                        success, result = thread_api.upload_file_2c(
                            file_full_path, target_folder_id, file_progress_callback
                        )

                        with lock:
                            completed_files += 1

                            if success:
                                uploaded_files += 1

                                # 标记为成功并在3秒后移除
                                dialog.after(0, lambda: file_tree.item(item_id, values=("✅ 成功", "100%", self.format_file_size(file_size)), tags=("success",)))

                                # 3秒后移除成功的项目
                                def remove_success_item():
                                    try:
                                        file_tree.delete(item_id)
                                    except:
                                        pass

                                dialog.after(3000, remove_success_item)
                            else:
                                # 上传失败，用红字显示错误信息
                                failed_files += 1
                                error_msg = result[:50] + "..." if len(result) > 50 else result
                                dialog.after(0, lambda: file_tree.item(item_id, values=(f"❌ {error_msg}", "0%", self.format_file_size(file_size)), tags=("failed",)))

                            # 更新总体进度
                            overall_progress = (completed_files / len(file_list)) * 100
                            dialog.after(0, lambda: overall_progress_var.set(overall_progress))
                            dialog.after(0, lambda: overall_status_var.set(f"已处理 {completed_files}/{len(file_list)} 个文件 (成功: {uploaded_files}, 失败: {failed_files})"))

                        return success, result

                    except Exception as e:
                        with lock:
                            failed_files += 1
                            completed_files += 1
                        error_msg = str(e)[:50] + "..." if len(str(e)) > 50 else str(e)
                        dialog.after(0, lambda: file_tree.item(item_id, values=(f"❌ {error_msg}", "0%", self.format_file_size(file_size)), tags=("failed",)))
                        return False, str(e)

                # 使用线程池并发上传文件夹中的文件
                max_workers = min(2, len(file_list))  # 限制并发数，避免API限制
                dialog.after(0, lambda: overall_status_var.set(f"开始并发上传文件夹 ({max_workers} 个并发)..."))

                try:
                    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                        # 提交所有上传任务
                        futures = [executor.submit(upload_folder_file, file_info) for file_info in file_list]

                        # 等待所有任务完成
                        concurrent.futures.wait(futures)

                except Exception as e:
                    print(f"⚠️ 文件夹并发上传失败: {e}")
                    # 如果并发失败，回退到顺序上传
                    dialog.after(0, lambda: overall_status_var.set("并发失败，使用顺序上传..."))

                    for file_info in file_list:
                        try:
                            upload_folder_file(file_info)
                        except Exception as e:
                            print(f"顺序上传也失败: {e}")
                            continue

                # 上传完成
                dialog.after(0, lambda: cancel_btn.config(state=tk.DISABLED))
                dialog.after(0, lambda: close_btn.config(state=tk.NORMAL))
                dialog.after(0, lambda: overall_status_var.set(f"上传完成！成功: {uploaded_files}, 失败: {failed_files}"))

                if failed_files == 0:
                    # 全部成功，5秒后自动关闭
                    dialog.after(5000, dialog.destroy)

            except Exception as e:
                dialog.after(0, lambda: self.on_folder_upload_failed(dialog, f"上传异常: {str(e)}"))

        threading.Thread(target=upload_folder_thread, daemon=True).start()

    def ensure_folder_structure(self, relative_path: str, root_folder_id: str, folder_cache: Dict) -> str:
        """确保文件夹结构存在，返回目标文件夹ID"""
        # 获取文件的目录路径
        dir_path = os.path.dirname(relative_path)

        if not dir_path or dir_path == '.':
            # 文件在根目录
            return root_folder_id

        # 分解路径
        path_parts = dir_path.split(os.sep)
        current_folder_id = root_folder_id
        current_path = ""

        for part in path_parts:
            if current_path:
                current_path = f"{current_path}/{part}"
            else:
                current_path = part

            # 检查缓存
            if current_path in folder_cache:
                current_folder_id = folder_cache[current_path]
            else:
                # 创建文件夹
                success, folder_id = self.api.create_directory("0", current_folder_id, part, "")
                if success:
                    folder_cache[current_path] = folder_id
                    current_folder_id = folder_id
                else:
                    print(f"创建文件夹失败: {current_path}")
                    return None

        return current_folder_id

    def on_folder_upload_success(self, dialog, folder_name, uploaded_files, total_files):
        """文件夹上传成功回调"""
        dialog.destroy()
        success_msg = f"文件夹 '{folder_name}' 上传完成！\n成功上传 {uploaded_files}/{total_files} 个文件"
        messagebox.showinfo("上传完成", success_msg)
        self.refresh_current_folder()  # 刷新文件列表

    def on_folder_upload_failed(self, dialog, error_msg):
        """文件夹上传失败回调"""
        dialog.destroy()
        messagebox.showerror("上传失败", error_msg)

    def on_upload_success(self, dialog, file_name, fid=None):
        """上传成功回调"""
        dialog.destroy()
        success_msg = f"文件 '{file_name}' 上传成功！"
        if fid:
            success_msg += f"\n文件ID: {fid}"
        messagebox.showinfo("上传成功", success_msg)
        self.refresh_current_folder()  # 刷新文件列表

    def on_upload_failed(self, dialog, error_msg):
        """上传失败回调"""
        dialog.destroy()
        messagebox.showerror("上传失败", error_msg)

    def format_file_size(self, size_bytes):
        """格式化文件大小"""
        if size_bytes == 0:
            return "0 B"

        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} PB"

    def create_new_folder(self):
        """创建新文件夹"""
        # 弹出输入对话框
        folder_name = tk.simpledialog.askstring(
            "新建文件夹",
            "请输入文件夹名称:",
            parent=self.root
        )

        if folder_name and folder_name.strip():
            folder_name = folder_name.strip()
            self.create_folder_in_current_directory(folder_name)

    def create_folder_in_current_directory(self, folder_name: str):
        """在当前目录创建文件夹"""
        if not self.api:
            messagebox.showerror("错误", "请先连接API")
            return

        self.status_var.set(f"正在创建文件夹: {folder_name}")
        self.create_folder_btn.config(state=tk.DISABLED)

        def create_folder_thread():
            try:
                # 使用真实的API创建文件夹
                success, result = self.api.create_directory("0", self.current_folder_id, folder_name, "")

                if success:
                    self.root.after(0, lambda: self.on_folder_create_success(folder_name))
                else:
                    self.root.after(0, lambda: self.on_folder_create_failed(f"创建文件夹失败: {result}"))

            except Exception as e:
                self.root.after(0, lambda: self.on_folder_create_failed(f"创建异常: {str(e)}"))

        threading.Thread(target=create_folder_thread, daemon=True).start()

    def on_folder_create_success(self, folder_name):
        """文件夹创建成功"""
        self.status_var.set(f"文件夹 '{folder_name}' 创建成功")
        self.create_folder_btn.config(state=tk.NORMAL)
        messagebox.showinfo("创建成功", f"文件夹 '{folder_name}' 创建成功！")
        self.refresh_current_folder()  # 刷新文件列表

    def on_folder_create_failed(self, error_msg):
        """文件夹创建失败"""
        self.status_var.set(f"创建失败: {error_msg}")
        self.create_folder_btn.config(state=tk.NORMAL)
        messagebox.showerror("创建失败", error_msg)

    def delete_selected_item(self):
        """删除选中的文件或文件夹"""
        selection = self.file_tree.selection()
        if not selection:
            messagebox.showwarning("提示", "请选择要删除的文件或文件夹")
            return

        # 获取选中项信息
        selected_items = []
        for item in selection:
            tags = self.file_tree.item(item, "tags")
            values = self.file_tree.item(item, "values")
            if len(tags) >= 3:
                selected_items.append({
                    'name': values[0],
                    'type': tags[2],  # 'folder' or 'file'
                    'id': tags[1],    # 文件/文件夹ID
                    'fid': tags[0]    # 文件FID
                })

        if not selected_items:
            return

        # 确认删除
        item_names = [item['name'] for item in selected_items]
        confirm_msg = f"确定要删除以下项目吗？\n\n" + "\n".join(item_names)

        if not messagebox.askyesno("确认删除", confirm_msg):
            return

        self.perform_delete(selected_items)

    def perform_delete(self, selected_items):
        """执行删除操作"""
        if not self.api:
            messagebox.showerror("错误", "请先连接API")
            return

        # 分离文件和文件夹
        dir_list = []
        file_list = []

        for item in selected_items:
            if item['type'] == 'folder':
                dir_list.append(item['id'])
            else:
                file_list.append(item['id'])

        item_count = len(selected_items)
        self.status_var.set(f"正在删除 {item_count} 个项目...")
        self.delete_btn.config(state=tk.DISABLED)

        def delete_thread():
            try:
                success, result = self.api.delete_file("0", dir_list, file_list)

                if success:
                    self.root.after(0, lambda: self.on_delete_success(item_count))
                else:
                    self.root.after(0, lambda: self.on_delete_failed(f"删除失败: {result}"))

            except Exception as e:
                self.root.after(0, lambda: self.on_delete_failed(f"删除异常: {str(e)}"))

        threading.Thread(target=delete_thread, daemon=True).start()

    def on_delete_success(self, item_count):
        """删除成功回调"""
        self.status_var.set(f"成功删除 {item_count} 个项目")
        self.delete_btn.config(state=tk.NORMAL)
        messagebox.showinfo("删除成功", f"成功删除 {item_count} 个项目！")
        self.refresh_current_folder()  # 刷新文件列表

    def on_delete_failed(self, error_msg):
        """删除失败回调"""
        self.status_var.set(f"删除失败: {error_msg}")
        self.delete_btn.config(state=tk.NORMAL)
        messagebox.showerror("删除失败", error_msg)

    def run(self):
        """运行GUI"""
        self.root.mainloop()


def main():
    """主函数"""
    app = WoPanGUI()
    app.run()


if __name__ == "__main__":
    main()
