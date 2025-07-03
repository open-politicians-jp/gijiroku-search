#!/usr/bin/env python3
"""
比例代表データ調査
"""

import requests
import logging
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def investigate_proportional():
    """比例代表ページを調査"""
    logger.info("🔍 比例代表ページ調査開始...")
    
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
    })
    
    base_url = "https://sangiin.go2senkyo.com"
    
    # 調査するURL候補
    candidate_urls = [
        f"{base_url}/2025",
        f"{base_url}/2025/seitou",
        f"{base_url}/2025/hirei",
        f"{base_url}/2025/proportional",
        f"{base_url}/2025/party",
        f"{base_url}/2025/list"
    ]
    
    for url in candidate_urls:
        try:
            logger.info(f"📍 調査中: {url}")
            response = session.get(url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                title = soup.find('title')
                
                logger.info(f"✅ アクセス成功: {url}")
                logger.info(f"  タイトル: {title.get_text() if title else 'N/A'}")
                
                # 比例代表関連のリンクを探す
                proportional_links = []
                all_links = soup.find_all('a', href=True)
                
                for link in all_links:
                    href = link.get('href', '').lower()
                    text = link.get_text(strip=True).lower()
                    
                    if any(keyword in href or keyword in text for keyword in 
                          ['hirei', 'proportional', 'seitou', 'party', 'list', '比例', '政党']):
                        proportional_links.append({
                            'text': link.get_text(strip=True),
                            'href': link.get('href')
                        })
                
                if proportional_links:
                    logger.info(f"  比例代表関連リンク: {len(proportional_links)}個")
                    for i, link in enumerate(proportional_links[:5]):
                        logger.info(f"    {i+1}: {link['text']} -> {link['href']}")
                
                # ページ構造の分析
                candidate_blocks = soup.find_all(['div', 'li', 'article'], class_=True)
                relevant_blocks = []
                
                for block in candidate_blocks[:20]:  # 最初の20個のみチェック
                    class_names = ' '.join(block.get('class', []))
                    if any(keyword in class_names.lower() for keyword in 
                          ['candidate', 'person', 'member', 'seitou', 'party']):
                        relevant_blocks.append({
                            'tag': block.name,
                            'class': class_names,
                            'text': block.get_text(strip=True)[:100]
                        })
                
                if relevant_blocks:
                    logger.info(f"  関連ブロック: {len(relevant_blocks)}個")
                    for i, block in enumerate(relevant_blocks[:3]):
                        logger.info(f"    {i+1}: {block['tag']}.{block['class']} - {block['text']}...")
                
                logger.info("")  # 区切り
                
            else:
                logger.debug(f"❌ アクセス失敗: {url} (HTTP {response.status_code})")
                
        except Exception as e:
            logger.debug(f"❌ エラー: {url} - {e}")
            continue
    
    # 政党一覧ページの詳細調査
    logger.info("🔍 政党ページ詳細調査...")
    seitou_url = f"{base_url}/2025/seitou"
    
    try:
        response = session.get(seitou_url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 政党リンクを探す
            party_links = soup.find_all('a', href=True)
            party_candidates = []
            
            for link in party_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 政党IDが含まれているリンクを探す
                if '/seitou/' in href and text:
                    party_candidates.append({
                        'party_name': text,
                        'url': href if href.startswith('http') else f"{base_url}{href}"
                    })
            
            logger.info(f"📋 発見された政党: {len(party_candidates)}個")
            for i, party in enumerate(party_candidates[:10]):
                logger.info(f"  {i+1}: {party['party_name']} -> {party['url']}")
        
    except Exception as e:
        logger.error(f"政党ページ調査エラー: {e}")

if __name__ == "__main__":
    investigate_proportional()