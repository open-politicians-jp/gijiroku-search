#!/usr/bin/env python3
"""
Go2senkyo 東京都データ収集テスト

東京都（都道府県コード13）のみをテストして
go2senkyo.comからのデータ取得を検証
"""

import json
import requests
import time
import re
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from urllib.parse import urljoin
import logging

# ログ設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tokyo_data_collection():
    """東京都データ収集テスト"""
    logger.info("🧪 Go2senkyo 東京都データ収集テスト開始...")
    
    # セッション設定
    ua = UserAgent()
    session = requests.Session()
    session.headers.update({
        'User-Agent': ua.random,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Connection': 'keep-alive'
    })
    
    # 東京都ページ
    tokyo_url = "https://sangiin.go2senkyo.com/2025/prefecture/13"
    
    try:
        logger.info(f"📍 東京都ページにアクセス: {tokyo_url}")
        response = session.get(tokyo_url, timeout=30)
        
        logger.info(f"📊 ステータスコード: {response.status_code}")
        logger.info(f"📄 レスポンスサイズ: {len(response.text)} 文字")
        
        if response.status_code != 200:
            logger.error(f"❌ アクセス失敗: HTTP {response.status_code}")
            return
        
        # HTMLを解析
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ページタイトル
        title = soup.find('title')
        if title:
            logger.info(f"📝 ページタイトル: {title.get_text()}")
        
        # 候補者要素の検索
        logger.info("🔍 候補者要素を検索中...")
        
        # 様々なセレクターで候補者要素を探す
        candidate_selectors = [
            '.candidate-item',
            '.candidate-card',
            '.person-item',
            '[class*="candidate"]',
            '[class*="person"]',
            'article',
            '.item'
        ]
        
        found_elements = []
        for selector in candidate_selectors:
            elements = soup.select(selector)
            if elements:
                logger.info(f"✅ {selector}: {len(elements)}個の要素発見")
                found_elements.extend(elements)
            else:
                logger.debug(f"❌ {selector}: 要素なし")
        
        # 重複除去
        unique_elements = list(set(found_elements))
        logger.info(f"📊 ユニーク要素数: {len(unique_elements)}")
        
        # 名前パターンで候補者を探す
        name_pattern = re.compile(r'[一-龯]{2,4}[\s　]+[一-龯]{2,8}')
        potential_candidates = []
        
        # すべてのテキストから名前らしきものを抽出
        all_text = soup.get_text()
        name_matches = name_pattern.findall(all_text)
        
        if name_matches:
            logger.info(f"🎯 名前パターンマッチ: {len(name_matches)}件")
            for i, name in enumerate(name_matches[:10]):  # 最初の10件を表示
                clean_name = name.strip().replace('\u3000', ' ')
                logger.info(f"  {i+1}: {clean_name}")
                potential_candidates.append(clean_name)
        
        # リンクから候補者ページを探す
        candidate_links = soup.find_all('a', href=re.compile(r'candidate|person|profile'))
        logger.info(f"🔗 候補者関連リンク: {len(candidate_links)}件")
        
        for i, link in enumerate(candidate_links[:5]):  # 最初の5件を表示
            href = link.get('href', '')
            text = link.get_text(strip=True)
            full_url = urljoin(tokyo_url, href) if href.startswith('/') else href
            logger.info(f"  {i+1}: {text[:30]} -> {full_url}")
        
        # サンプル候補者詳細取得テスト
        if candidate_links:
            logger.info("🧪 サンプル候補者詳細ページテスト...")
            sample_link = candidate_links[0]
            sample_href = sample_link.get('href', '')
            
            if sample_href:
                sample_url = urljoin(tokyo_url, sample_href) if sample_href.startswith('/') else sample_href
                
                try:
                    time.sleep(2)  # 間隔をあける
                    detail_response = session.get(sample_url, timeout=20)
                    
                    if detail_response.status_code == 200:
                        detail_soup = BeautifulSoup(detail_response.text, 'html.parser')
                        
                        # 詳細ページの情報
                        detail_title = detail_soup.find('title')
                        logger.info(f"📋 詳細ページタイトル: {detail_title.get_text() if detail_title else 'なし'}")
                        
                        # 画像を探す
                        images = detail_soup.find_all('img')
                        logger.info(f"🖼️ 画像数: {len(images)}")
                        
                        # 政策・プロフィール情報
                        policy_keywords = ['政策', 'マニフェスト', '公約', 'プロフィール']
                        found_keywords = []
                        
                        detail_text = detail_soup.get_text()
                        for keyword in policy_keywords:
                            if keyword in detail_text:
                                found_keywords.append(keyword)
                        
                        logger.info(f"📜 発見キーワード: {', '.join(found_keywords)}")
                        
                        # SNSリンク
                        social_links = []
                        all_links = detail_soup.find_all('a', href=True)
                        
                        for link in all_links:
                            href = link['href'].lower()
                            if any(social in href for social in ['twitter', 'facebook', 'instagram', 'youtube']):
                                social_links.append(link['href'])
                        
                        logger.info(f"🔗 SNSリンク: {len(social_links)}件")
                        for social in social_links[:3]:
                            logger.info(f"  - {social}")
                    
                    else:
                        logger.warning(f"⚠️ 詳細ページアクセス失敗: HTTP {detail_response.status_code}")
                
                except Exception as e:
                    logger.error(f"❌ 詳細ページテストエラー: {e}")
        
        # 結果サマリー
        logger.info("\n" + "="*50)
        logger.info("📊 東京都データ収集テスト結果")
        logger.info("="*50)
        logger.info(f"✅ メインページアクセス: 成功")
        logger.info(f"📊 発見要素数: {len(unique_elements)}")
        logger.info(f"🎯 候補者名候補: {len(potential_candidates)}")
        logger.info(f"🔗 候補者リンク: {len(candidate_links)}")
        
        # 簡易データ構造作成
        sample_data = {
            "prefecture": "東京都",
            "url": tokyo_url,
            "status": "success",
            "found_elements": len(unique_elements),
            "potential_candidates": potential_candidates[:10],
            "candidate_links": [
                {"text": link.get_text(strip=True)[:50], "href": link.get('href', '')}
                for link in candidate_links[:5]
            ],
            "collected_at": datetime.now().isoformat()
        }
        
        # テスト結果保存
        output_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = output_dir / "tokyo_test_result.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 テスト結果保存: {test_file}")
        
    except Exception as e:
        logger.error(f"❌ 東京都テストエラー: {e}")

if __name__ == "__main__":
    test_tokyo_data_collection()