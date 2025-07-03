#!/usr/bin/env python3
"""
ヘッダー詳細デバッグ
"""

import requests
import logging
from fake_useragent import UserAgent
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_headers():
    """ヘッダー詳細比較"""
    logger.info("🔍 ヘッダー詳細比較...")
    
    tokyo_url = "https://sangiin.go2senkyo.com/2025/prefecture/13"
    
    # 方式1: シンプルなセッション（動作する）
    logger.info("📡 方式1: シンプルセッション")
    ua1 = UserAgent()
    session1 = requests.Session()
    session1.headers.update({
        'User-Agent': ua1.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
    })
    
    logger.info("📋 方式1ヘッダー:")
    for key, value in session1.headers.items():
        logger.info(f"  {key}: {value}")
    
    # 方式2: Collectorセッション（動作しない）
    logger.info("📡 方式2: Collectorセッション")
    collector = Go2senkyoOptimizedCollector()
    
    logger.info("📋 方式2ヘッダー:")
    for key, value in collector.session.headers.items():
        logger.info(f"  {key}: {value}")
    
    # 方式3: Collectorと同じヘッダーで独立セッション
    logger.info("📡 方式3: Collector模倣セッション")
    session3 = requests.Session()
    
    # Collectorと同じヘッダーを設定
    for key, value in collector.session.headers.items():
        session3.headers[key] = value
    
    try:
        response3 = session3.get(tokyo_url, timeout=30)
        logger.info(f"  方式3結果: {response3.status_code}, {len(response3.text)}文字")
        
        # 方式4: Refererなしでテスト
        logger.info("📡 方式4: Refererなし")
        session4 = requests.Session()
        session4.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
            # Refererを設定しない
        })
        
        response4 = session4.get(tokyo_url, timeout=30)
        logger.info(f"  方式4結果: {response4.status_code}, {len(response4.text)}文字")
        
    except Exception as e:
        logger.error(f"  エラー: {e}")

if __name__ == "__main__":
    debug_headers()