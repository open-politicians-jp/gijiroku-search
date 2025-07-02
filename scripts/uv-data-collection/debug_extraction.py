#!/usr/bin/env python3
"""
候補者抽出デバッグスクリプト
"""

import requests
import logging
import re
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def debug_extraction():
    """候補者抽出の詳細デバッグ"""
    logger.info("🔍 候補者抽出デバッグ...")
    
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3'
    })
    
    tokyo_url = "https://sangiin.go2senkyo.com/2025/prefecture/13"
    profile_base_url = "https://go2senkyo.com"
    
    try:
        response = session.get(tokyo_url, timeout=30)
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 候補者ブロック取得
        candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
        logger.info(f"📊 候補者ブロック数: {len(candidate_blocks)}")
        
        candidates = []
        
        for i, block in enumerate(candidate_blocks[:5]):  # 最初の5個をテスト
            logger.info(f"\n--- ブロック {i+1} ---")
            
            try:
                # 名前抽出
                name_elem = block.find(class_='p_senkyoku_list_block_text_name')
                name = name_elem.get_text(strip=True) if name_elem else f"候補者{i+1}"
                logger.info(f"名前: {name}")
                
                # 政党抽出
                party_elem = block.find(class_='p_senkyoku_list_block_text_party')
                party = party_elem.get_text(strip=True) if party_elem else "未分類"
                logger.info(f"政党: {party}")
                
                # プロフィールリンク抽出
                profile_link = block.find('a', href=re.compile(r'/seijika/\d+'))
                profile_url = ""
                candidate_id = f"東京都_{i}"
                
                if profile_link:
                    href = profile_link.get('href', '')
                    logger.info(f"リンクhref: {href}")
                    
                    if href.startswith('/'):
                        profile_url = urljoin(profile_base_url, href)
                    else:
                        profile_url = href
                    
                    # 候補者ID抽出
                    match = re.search(r'/seijika/(\d+)', href)
                    if match:
                        candidate_id = f"go2s_{match.group(1)}"
                        logger.info(f"候補者ID: {candidate_id}")
                else:
                    logger.warning("プロフィールリンクが見つかりません")
                
                logger.info(f"プロフィールURL: {profile_url}")
                
                # 候補者データ作成
                candidate_data = {
                    "candidate_id": candidate_id,
                    "name": name,
                    "prefecture": "東京都",
                    "constituency": "東京",
                    "constituency_type": "single_member",
                    "party": party,
                    "profile_url": profile_url,
                    "source_page": tokyo_url,
                    "source": "go2senkyo_debug"
                }
                
                # 検証
                if name and name != f"候補者{i+1}" and profile_url:
                    candidates.append(candidate_data)
                    logger.info("✅ 候補者データ作成成功")
                else:
                    logger.warning("❌ 候補者データ検証失敗")
                    logger.warning(f"  名前: {name}")
                    logger.warning(f"  プロフィールURL: {profile_url}")
                
            except Exception as e:
                logger.error(f"❌ ブロック{i+1}エラー: {e}")
                continue
        
        logger.info(f"\n🎯 総抽出候補者数: {len(candidates)}")
        
        # サンプル候補者表示
        if candidates:
            sample = candidates[0]
            logger.info("📋 サンプル候補者:")
            for key, value in sample.items():
                logger.info(f"  {key}: {value}")
        
        return candidates
        
    except Exception as e:
        logger.error(f"❌ デバッグエラー: {e}")
        return []

if __name__ == "__main__":
    debug_extraction()