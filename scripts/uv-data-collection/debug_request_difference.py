#!/usr/bin/env python3
"""
リクエスト差分デバッグ
"""

import requests
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_requests():
    """リクエスト方式の比較"""
    logger.info("🔍 リクエスト方式比較...")
    
    tokyo_url = "https://sangiin.go2senkyo.com/2025/prefecture/13"
    
    # 方式1: 独立したセッション（テストメソッド方式）
    logger.info("📡 方式1: 独立セッション")
    ua1 = UserAgent()
    session1 = requests.Session()
    session1.headers.update({
        'User-Agent': ua1.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
    })
    
    try:
        response1 = session1.get(tokyo_url, timeout=30)
        soup1 = BeautifulSoup(response1.text, 'html.parser')
        blocks1 = soup1.find_all('div', class_='p_senkyoku_list_block')
        logger.info(f"  結果: {len(blocks1)}個のブロック")
    except Exception as e:
        logger.error(f"  エラー: {e}")
    
    # 方式2: Collectorクラスのセッション
    logger.info("📡 方式2: Collectorセッション")
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # ヘッダー情報確認
        logger.info(f"  User-Agent: {collector.session.headers.get('User-Agent', 'N/A')[:50]}...")
        logger.info(f"  Referer: {collector.session.headers.get('Referer', 'N/A')}")
        
        response2 = collector.session.get(tokyo_url, timeout=30)
        soup2 = BeautifulSoup(response2.text, 'html.parser')
        blocks2 = soup2.find_all('div', class_='p_senkyoku_list_block')
        logger.info(f"  結果: {len(blocks2)}個のブロック")
        
        # レスポンス比較
        logger.info(f"📊 レスポンス比較:")
        logger.info(f"  方式1 レスポンスサイズ: {len(response1.text)} 文字")
        logger.info(f"  方式2 レスポンスサイズ: {len(response2.text)} 文字")
        logger.info(f"  方式1 ステータス: {response1.status_code}")
        logger.info(f"  方式2 ステータス: {response2.status_code}")
        
        # HTML内容確認
        if len(response1.text) != len(response2.text):
            logger.warning("⚠️ レスポンス内容が異なります")
            
            # 一致しない場合のデバッグ
            title1 = soup1.find('title')
            title2 = soup2.find('title')
            logger.info(f"  方式1 タイトル: {title1.get_text() if title1 else 'N/A'}")
            logger.info(f"  方式2 タイトル: {title2.get_text() if title2 else 'N/A'}")
        else:
            logger.info("✅ レスポンス内容は同じです")
        
    except Exception as e:
        logger.error(f"  エラー: {e}")

if __name__ == "__main__":
    debug_requests()