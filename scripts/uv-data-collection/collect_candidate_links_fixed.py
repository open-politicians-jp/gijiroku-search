#!/usr/bin/env python3
"""
候補者の関連リンク収集 - 修正版
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_candidate_links_sample():
    """サンプル候補者の関連リンクを取得"""
    logger.info("🔗 サンプル候補者関連リンク収集...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('data', [])[:10]  # 最初の10名のみテスト
    logger.info(f"📊 テスト対象候補者: {len(candidates)}名")
    
    collector = Go2senkyoOptimizedCollector()
    
    for i, candidate in enumerate(candidates):
        try:
            profile_url = candidate.get('profile_url', '')
            name = candidate.get('name', '')
            
            logger.info(f"📍 {i+1}/{len(candidates)}: {name}")
            logger.info(f"  URL: {profile_url}")
            
            if not profile_url:
                continue
            
            # 関連リンク取得
            links_info = get_candidate_links_fixed(profile_url, collector)
            
            if links_info:
                logger.info(f"  ✅ 取得成功:")
                for key, value in links_info.items():
                    if key == 'websites':
                        logger.info(f"    {key}: {len(value)}個")
                        for site in value:
                            logger.info(f"      - {site['title']}: {site['url']}")
                    else:
                        logger.info(f"    {key}: {value}")
            else:
                logger.info(f"  ❌ 関連リンクなし")
            
            collector.random_delay(1, 2)
            
        except Exception as e:
            logger.error(f"❌ {name}エラー: {e}")
            continue

def get_candidate_links_fixed(profile_url, collector):
    """個別プロフィールページから関連リンクを取得 - 修正版"""
    links_info = {}
    
    try:
        if not profile_url or not profile_url.startswith('http'):
            return links_info
        
        response = collector.session.get(profile_url, timeout=15)
        if response.status_code != 200:
            logger.debug(f"プロフィールページアクセス失敗: {response.status_code}")
            return links_info
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # p_seijika_profle_data_sitelist クラスから関連サイトを取得
        sitelist_elem = soup.find(class_='p_seijika_profle_data_sitelist')
        if sitelist_elem:
            websites = []
            site_links = sitelist_elem.find_all('a', href=True)
            
            for link in site_links:
                url = link.get('href', '').strip()
                
                if url and url.startswith('http'):
                    # 画像から種類を判定
                    img = link.find('img')
                    title = get_site_title_from_image(img, url)
                    
                    websites.append({
                        "url": url,
                        "title": title
                    })
            
            if websites:
                links_info["websites"] = websites
                # 最初のリンクを公式サイトとして設定
                links_info["official_website"] = websites[0]["url"]
                logger.debug(f"関連サイト取得: {len(websites)}個")
        
        # その他の詳細情報も取得
        additional_info = get_additional_profile_info_fixed(soup)
        links_info.update(additional_info)
        
    except Exception as e:
        logger.debug(f"関連リンク取得エラー: {e}")
    
    return links_info

def get_site_title_from_image(img_elem, url):
    """画像のsrcからサイトの種類を判定"""
    if not img_elem:
        return "公式サイト"
    
    src = img_elem.get('src', '').lower()
    
    if 'facebook' in src or 'fb' in src:
        return "Facebook"
    elif 'twitter' in src or 'tw' in src:
        return "Twitter"
    elif 'instagram' in src or 'insta' in src:
        return "Instagram"
    elif 'youtube' in src:
        return "YouTube"
    elif 'home' in src or 'hp' in src:
        return "公式サイト"
    elif 'blog' in src:
        return "ブログ"
    else:
        # URLから判定を試行
        if 'facebook.com' in url:
            return "Facebook"
        elif 'twitter.com' in url or 'x.com' in url:
            return "Twitter"
        elif 'instagram.com' in url:
            return "Instagram"
        elif 'youtube.com' in url:
            return "YouTube"
        else:
            return "公式サイト"

def get_additional_profile_info_fixed(soup):
    """追加のプロフィール情報を取得 - 修正版"""
    info = {}
    
    try:
        # 年齢情報
        text_content = soup.get_text()
        age_match = re.search(r'(\d+)歳', text_content)
        if age_match:
            info["age_info"] = age_match.group(1)
        
        # 出身地情報
        birthplace_patterns = [
            r'出身[：:\s]*([都道府県市区町村\w]+)',
            r'([都道府県][市区町村]\w*)出身',
        ]
        
        for pattern in birthplace_patterns:
            match = re.search(pattern, text_content)
            if match:
                birthplace = match.group(1).strip()
                if 2 <= len(birthplace) <= 10:  # 妥当な長さかチェック
                    info["birthplace"] = birthplace
                break
        
        # 職業・経歴情報をプロフィール文から抽出
        profile_section = soup.find('div', class_=re.compile(r'profile|career|history'))
        if profile_section:
            career_text = profile_section.get_text(strip=True)
            if career_text and len(career_text) >= 20:
                info["career"] = career_text[:200]  # 200文字まで
        
    except Exception as e:
        logger.debug(f"追加情報取得エラー: {e}")
    
    return info

if __name__ == "__main__":
    collect_candidate_links_sample()