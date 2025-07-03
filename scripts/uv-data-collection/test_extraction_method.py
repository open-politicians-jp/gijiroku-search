#!/usr/bin/env python3
"""
メソッド単体テスト
"""

import requests
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_method():
    """メソッド単体テスト"""
    logger.info("🧪 メソッド単体テスト...")
    
    collector = Go2senkyoOptimizedCollector()
    
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
    })
    
    tokyo_url = "https://sangiin.go2senkyo.com/2025/prefecture/13"
    
    try:
        response = session.get(tokyo_url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 元のparse_candidate_listメソッドを呼ぶ
        candidates = collector.parse_candidate_list(soup, "東京都", tokyo_url)
        
        logger.info(f"🎯 parse_candidate_list結果: {len(candidates)}名")
        
        if candidates:
            for i, candidate in enumerate(candidates[:3]):
                logger.info(f"候補者{i+1}: {candidate.get('name')} - {candidate.get('party')}")
        
        return candidates
        
    except Exception as e:
        logger.error(f"❌ テストエラー: {e}")
        raise

if __name__ == "__main__":
    test_method()