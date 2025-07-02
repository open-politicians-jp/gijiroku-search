#!/usr/bin/env python3
"""
HTML内容デバッグスクリプト
"""

import requests
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_html():
    """HTML内容のデバッグ"""
    logger.info("🔍 HTML内容デバッグ...")
    
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
        
        # 様々なセレクターをテスト
        selectors_to_test = [
            '.p_senkyoku_list_block',
            'div[class*="p_senkyoku"]',
            'div[class*="senkyoku"]',
            'div[class*="list_block"]',
            '[class*="candidate"]',
            '[class*="person"]'
        ]
        
        for selector in selectors_to_test:
            elements = soup.select(selector)
            logger.info(f"✅ {selector}: {len(elements)}個要素")
            
            if elements and len(elements) > 0:
                # 最初の要素の詳細
                first_elem = elements[0]
                logger.info(f"  最初の要素クラス: {first_elem.get('class', [])}")
                logger.info(f"  最初の要素テキスト: {first_elem.get_text()[:100]}...")
        
        # プロフィールリンクをチェック
        profile_links = soup.find_all('a', href=True)
        seijika_links = [link for link in profile_links if 'seijika' in link.get('href', '')]
        
        logger.info(f"🔗 政治家リンク: {len(seijika_links)}個")
        
        if seijika_links:
            for i, link in enumerate(seijika_links[:5]):
                logger.info(f"  {i+1}: {link.get_text()[:30]} -> {link.get('href')}")
        
        # クラス名一覧
        all_classes = set()
        for element in soup.find_all(class_=True):
            if isinstance(element['class'], list):
                all_classes.update(element['class'])
            else:
                all_classes.add(element['class'])
        
        relevant_classes = [cls for cls in all_classes if 
                          any(keyword in cls.lower() for keyword in ['senkyoku', 'list', 'block', 'candidate', 'person'])]
        
        logger.info(f"📋 関連クラス: {sorted(relevant_classes)}")
        
    except Exception as e:
        logger.error(f"❌ デバッグエラー: {e}")

if __name__ == "__main__":
    debug_html()