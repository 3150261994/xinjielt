#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通网盘文件下载地址获取器
获取指定文件的下载链接

Author: AI Assistant
Date: 2025-01-26
"""

import json
import logging
import time
import base64
import hashlib
import random
from typing import Dict, List, Optional, Tuple, Any
import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
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
            logger.warning(f"参数加密失败，使用明文: {e}")
            return content
    
    def decrypt(self, encrypted_data: str, channel: str) -> str:
        """解密内容"""
        key = self.key if channel == "api-user" else self.access_key
        if key is None:
            key = self.key
        
        try:
            # 修正Base64填充
            missing_padding = len(encrypted_data) % 4
            if missing_padding:
                padded_data = encrypted_data + '=' * (4 - missing_padding)
            else:
                padded_data = encrypted_data
            
            # Base64解码
            encrypted_bytes = base64.b64decode(padded_data)
            
            # AES解密
            cipher = AES.new(key, AES.MODE_CBC, self.iv)
            decrypted = cipher.decrypt(encrypted_bytes)
            
            # 去除填充
            unpadded = unpad(decrypted, AES.block_size)
            
            # 转换为字符串
            return unpadded.decode('utf-8')
                
        except Exception as e:
            logger.debug(f"解密失败: {e}")
            return encrypted_data


class WoPanDownloader:
    """联通网盘下载地址获取器"""
    
    DEFAULT_CLIENT_ID = "1001000021"
    DEFAULT_CLIENT_SECRET = "XFmi9GS2hzk98jGX"
    DEFAULT_BASE_URL = "https://panservice.mail.wo.cn"
    DEFAULT_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36 Edg/114.0.1823.37"
    
    CHANNEL_WO_HOME = "wohome"
    
    def __init__(self, token: str):
        self.token = token
        self.access_token = token
        
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.DEFAULT_UA,
            'Content-Type': 'application/json',
            'Accept': 'application/json',
            'Origin': 'https://pan.wo.cn',
            'Referer': 'https://pan.wo.cn/',
            'Accesstoken': self.access_token
        })
        
        self.crypto = WoPanCrypto(self.DEFAULT_CLIENT_SECRET)
        self.crypto.set_access_token(self.token)
    
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
        """创建请求体"""
        if not param:
            return other
        
        # 加密参数
        param_json = json.dumps(param, separators=(',', ':'))
        try:
            encrypted_param = self.crypto.encrypt(param_json, channel)
        except Exception as e:
            logger.warning(f"参数加密失败，使用明文: {e}")
            encrypted_param = param_json
        
        body = other.copy()
        body["param"] = encrypted_param
        return body
    
    def get_download_url_v2(self, fid_list: List[str]) -> Tuple[bool, Any]:
        """
        获取下载链接V2
        
        Args:
            fid_list: 文件FID列表
        
        Returns:
            tuple: (是否成功, 下载链接数据)
        """
        logger.info(f"🔗 获取下载链接 - 文件数量: {len(fid_list)}")
        
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"
        
        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "GetDownloadUrlV2")
        
        # 请求参数
        param = {
            "type": "1",
            "fidList": fid_list,
            "clientId": self.DEFAULT_CLIENT_ID
        }
        
        other = {"secret": True}
        
        request_body = self._new_body(self.CHANNEL_WO_HOME, param, other)
        
        request_data = {
            "header": request_header,
            "body": request_body
        }
        
        logger.info("发起下载链接请求...")
        logger.debug(f"请求数据: {json.dumps(request_data, indent=2, ensure_ascii=False)}")
        
        try:
            response = self.session.post(url, json=request_data, headers=headers, timeout=30)
            
            logger.info(f"HTTP状态码: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"HTTP请求失败: {response.status_code} - {response.text}")
                return False, {"error": f"HTTP {response.status_code}", "response": response.text}
            
            result = response.json()
            logger.debug(f"原始响应: {json.dumps(result, indent=2, ensure_ascii=False)}")
            
            if result.get('STATUS') != '200':
                logger.error(f"API请求失败: {result.get('STATUS')} - {result.get('MSG')}")
                return False, result
            
            rsp = result.get('RSP', {})
            rsp_code = rsp.get('RSP_CODE')
            rsp_desc = rsp.get('RSP_DESC')
            
            logger.info(f"API响应: {rsp_code} - {rsp_desc}")
            
            if rsp_code == '0000':
                # 成功获取数据
                data = rsp.get('DATA', '')
                logger.info("✅ 成功获取下载链接数据")
                
                if isinstance(data, str):
                    # 解密数据
                    decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)
                    
                    try:
                        parsed_data = json.loads(decrypted_text)
                        logger.info("✅ 下载链接数据解析成功")
                        return True, parsed_data
                    except json.JSONDecodeError as e:
                        logger.error(f"JSON解析失败: {e}")
                        logger.info(f"原始解密数据: {decrypted_text}")
                        return True, {"decrypted_text": decrypted_text}
                else:
                    logger.info(f"数据内容: {data}")
                    return True, data
            else:
                logger.error(f"API响应错误: {rsp_code} - {rsp_desc}")
                return False, rsp
            
        except Exception as e:
            logger.error(f"请求异常: {e}")
            return False, {"error": str(e)}
    
    def get_download_url(self, fid_list: List[str], space_type: str = "0") -> Tuple[bool, Any]:
        """
        获取下载链接（旧版本API）
        
        Args:
            fid_list: 文件FID列表
            space_type: 空间类型
        
        Returns:
            tuple: (是否成功, 下载链接数据)
        """
        logger.info(f"🔗 获取下载链接(旧版) - 文件数量: {len(fid_list)}")
        
        url = f"{self.DEFAULT_BASE_URL}/{self.CHANNEL_WO_HOME}/dispatcher"
        
        headers = self.session.headers.copy()
        headers['Accesstoken'] = self.access_token
        
        request_header = self._calc_header(self.CHANNEL_WO_HOME, "GetDownloadUrl")
        
        # 请求参数
        param = {
            "fidList": fid_list,
            "clientId": self.DEFAULT_CLIENT_ID,
            "spaceType": space_type
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
                return False, result.get('MSG', 'API请求失败')
            
            rsp = result.get('RSP', {})
            if rsp.get('RSP_CODE') != '0000':
                return False, rsp.get('RSP_DESC', '未知错误')
            
            # 获取并解密数据
            data = rsp.get('DATA', '')
            if isinstance(data, str):
                decrypted_text = self.crypto.decrypt(data, self.CHANNEL_WO_HOME)
                try:
                    return True, json.loads(decrypted_text)
                except:
                    return True, {"decrypted_text": decrypted_text}
            else:
                return True, data
                
        except Exception as e:
            return False, str(e)
    
    def load_file_info_from_json(self, filename: str = "complete_folder_structure.json") -> Dict:
        """从JSON文件加载文件信息"""
        try:
            with open(filename, "r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error(f"❌ 找不到文件: {filename}")
            logger.info("请先运行 get_folder_contents.py 获取文件结构")
            return {}
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON解析失败: {e}")
            return {}
    
    def find_file_by_name(self, file_name: str, structure: Dict) -> Optional[Dict]:
        """根据文件名查找文件信息"""
        folder_structures = structure.get("folder_structures", [])
        
        for folder in folder_structures:
            files = folder.get("files", [])
            for file in files:
                if file.get("name") == file_name:
                    return file
        
        return None


def main():
    """主函数"""
    logger.info("🚀 联通网盘下载地址获取器 (支持Token负载均衡)")
    logger.info("=" * 50)

    # 从Token管理器获取令牌
    token = get_token_with_retry(max_retries=3, strategy="best")
    if not token:
        logger.error("❌ 无法获取可用token，请确保Token管理器正在运行")
        return

    logger.info(f"✅ 获取到token: {token[:20]}...")

    # 创建下载器
    downloader = WoPanDownloader(token)
    
    # 加载文件结构
    logger.info("📋 加载文件结构...")
    structure = downloader.load_file_info_from_json()
    
    if not structure:
        return
    
    # 查找01.mp4文件
    target_file = "01.mp4"
    logger.info(f"🔍 查找文件: {target_file}")
    
    file_info = downloader.find_file_by_name(target_file, structure)
    
    if not file_info:
        logger.error(f"❌ 找不到文件: {target_file}")
        return
    
    logger.info(f"✅ 找到文件: {target_file}")
    logger.info(f"   文件ID: {file_info.get('id')}")
    logger.info(f"   文件FID: {file_info.get('fid')}")
    logger.info(f"   文件大小: {file_info.get('size')} bytes")
    logger.info(f"   创建时间: {file_info.get('create_time')}")
    
    # 获取下载链接
    fid = file_info.get('fid')
    if not fid:
        logger.error("❌ 文件FID为空")
        return
    
    logger.info(f"\n🔗 获取下载链接...")
    
    # 方法1: 使用GetDownloadUrlV2
    logger.info("方法1: GetDownloadUrlV2")
    success, download_data = downloader.get_download_url_v2([fid])
    
    if success:
        logger.info("✅ 方法1成功获取下载数据")
        report_success(token)  # 报告成功

        # 保存下载数据
        with open("download_data_v2.json", "w", encoding="utf-8") as f:
            json.dump(download_data, f, ensure_ascii=False, indent=2)
        logger.info("💾 下载数据已保存到 download_data_v2.json")
        
        # 解析下载链接
        if isinstance(download_data, dict):
            if "list" in download_data:
                download_list = download_data["list"]
                if download_list:
                    for item in download_list:
                        item_fid = item.get("fid", "")
                        download_url = item.get("downloadUrl", "")
                        
                        logger.info(f"🎯 文件: {target_file}")
                        logger.info(f"   FID: {item_fid}")
                        logger.info(f"   下载链接: {download_url}")
                        
                        if download_url:
                            logger.info(f"\n✅ 成功获取 {target_file} 的下载链接!")
                            logger.info(f"🔗 下载地址: {download_url}")
                        else:
                            logger.warning("⚠️ 下载链接为空")
                else:
                    logger.warning("⚠️ 下载列表为空")
            else:
                logger.info(f"📄 下载数据结构: {list(download_data.keys()) if isinstance(download_data, dict) else type(download_data)}")
        else:
            logger.info(f"📄 下载数据: {download_data}")
    else:
        logger.error(f"❌ 方法1失败: {download_data}")
        report_error(f"方法1失败: {download_data}", token)  # 报告失败

        # 方法2: 使用GetDownloadUrl
        logger.info("\n方法2: GetDownloadUrl")
        success2, download_data2 = downloader.get_download_url([fid])

        if success2:
            logger.info("✅ 方法2成功获取下载数据")
            report_success(token)  # 报告成功

            # 保存下载数据
            with open("download_data.json", "w", encoding="utf-8") as f:
                json.dump(download_data2, f, ensure_ascii=False, indent=2)
            logger.info("💾 下载数据已保存到 download_data.json")

            logger.info(f"📄 下载数据: {download_data2}")
        else:
            logger.error(f"❌ 方法2也失败: {download_data2}")
            report_error(f"方法2失败: {download_data2}", token)  # 报告失败
    
    logger.info("\n" + "=" * 50)
    logger.info("🏁 下载链接获取完成")


if __name__ == "__main__":
    main()
