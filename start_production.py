#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
生产环境启动脚本 - 支持高并发
"""

import os
import sys
import logging
import argparse
from simple_unified_service import create_app

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_with_gunicorn(host='0.0.0.0', port=8000, workers=4):
    """使用Gunicorn运行（推荐生产环境）"""
    try:
        import gunicorn.app.wsgiapp as wsgi
        
        logger.info(f"🚀 使用Gunicorn启动服务器")
        logger.info(f"📊 配置: {workers}个Worker进程，监听 {host}:{port}")
        
        # Gunicorn配置
        sys.argv = [
            'gunicorn',
            '--bind', f'{host}:{port}',
            '--workers', str(workers),
            '--worker-class', 'gevent',
            '--worker-connections', '1000',
            '--timeout', '120',
            '--keepalive', '5',
            '--max-requests', '1000',
            '--max-requests-jitter', '100',
            '--preload',
            '--access-logfile', '-',
            '--error-logfile', '-',
            'simple_unified_service:app'
        ]
        
        wsgi.run()
        
    except ImportError:
        logger.error("❌ Gunicorn未安装，请运行: pip install gunicorn")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Gunicorn启动失败: {e}")
        sys.exit(1)


def run_with_waitress(host='0.0.0.0', port=8000, threads=8):
    """使用Waitress运行（Windows友好）"""
    try:
        from waitress import serve
        
        app = create_app()
        logger.info(f"🚀 使用Waitress启动服务器")
        logger.info(f"📊 配置: {threads}个线程，监听 {host}:{port}")
        
        serve(
            app,
            host=host,
            port=port,
            threads=threads,
            connection_limit=1000,
            cleanup_interval=30,
            channel_timeout=120
        )
        
    except ImportError:
        logger.error("❌ Waitress未安装，请运行: pip install waitress")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Waitress启动失败: {e}")
        sys.exit(1)


def run_with_gevent(host='0.0.0.0', port=8000):
    """使用Gevent运行"""
    try:
        from gevent.pywsgi import WSGIServer
        
        app = create_app()
        logger.info(f"🚀 使用Gevent启动服务器")
        logger.info(f"📊 配置: 协程模式，监听 {host}:{port}")
        
        http_server = WSGIServer((host, port), app)
        http_server.serve_forever()
        
    except ImportError:
        logger.error("❌ Gevent未安装，请运行: pip install gevent")
        sys.exit(1)
    except Exception as e:
        logger.error(f"❌ Gevent启动失败: {e}")
        sys.exit(1)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='联通网盘统一服务 - 生产环境启动器')
    parser.add_argument('--host', default='0.0.0.0', help='监听地址 (默认: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=8000, help='监听端口 (默认: 8000)')
    parser.add_argument('--server', choices=['gunicorn', 'waitress', 'gevent'], 
                       default='auto', help='WSGI服务器类型 (默认: auto)')
    parser.add_argument('--workers', type=int, default=4, help='Worker进程数 (仅Gunicorn)')
    parser.add_argument('--threads', type=int, default=8, help='线程数 (仅Waitress)')
    
    args = parser.parse_args()
    
    logger.info("🚀 联通网盘统一服务 - 生产环境启动器")
    logger.info("=" * 60)
    logger.info("🔐 登录信息:")
    logger.info("   用户名: admin")
    logger.info("   密码: 3150261994")
    logger.info("=" * 60)
    logger.info(f"🌐 服务地址: http://{args.host}:{args.port}")
    logger.info("📋 功能: Token管理 + 文件下载API + 高并发处理")
    logger.info("=" * 60)
    
    # 自动选择服务器
    if args.server == 'auto':
        if os.name == 'nt':  # Windows
            logger.info("🖥️ Windows环境，使用Waitress")
            args.server = 'waitress'
        else:  # Linux/Mac
            logger.info("🐧 Unix环境，使用Gunicorn")
            args.server = 'gunicorn'
    
    # 启动对应的服务器
    if args.server == 'gunicorn':
        run_with_gunicorn(args.host, args.port, args.workers)
    elif args.server == 'waitress':
        run_with_waitress(args.host, args.port, args.threads)
    elif args.server == 'gevent':
        run_with_gevent(args.host, args.port)
    else:
        logger.error(f"❌ 未知的服务器类型: {args.server}")
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("👋 服务已停止")
    except Exception as e:
        logger.error(f"💥 启动失败: {e}")
        sys.exit(1)
