#!/usr/bin/env python3
"""
候補者の関連リンク収集 - p_seijika_profle_data_sitelist活用
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

def collect_candidate_links():
    """既存候補者データに関連リンクを追加"""
    logger.info("🔗 候補者関連リンク収集開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    if not latest_file.exists():
        logger.error("最新データファイルが見つかりません")
        return
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('data', [])
    logger.info(f"📊 対象候補者: {len(candidates)}名")
    
    collector = Go2senkyoOptimizedCollector()
    updated_candidates = []
    success_count = 0
    
    for i, candidate in enumerate(candidates):
        try:
            profile_url = candidate.get('profile_url', '')
            name = candidate.get('name', '')
            
            logger.info(f"📍 {i+1}/{len(candidates)}: {name}")
            
            if not profile_url:
                logger.debug(f"  プロフィールURLなし: {name}")
                updated_candidates.append(candidate)
                continue
            
            # 関連リンク取得
            links_info = get_candidate_links(profile_url, collector)
            
            if links_info:
                # 既存データに関連リンク情報を追加
                candidate.update(links_info)
                success_count += 1
                logger.info(f"  ✅ リンク取得成功: {len(links_info.get('websites', []))}個")
            else:
                logger.debug(f"  関連リンクなし: {name}")
            
            updated_candidates.append(candidate)
            
            # 進捗表示
            if (i + 1) % 10 == 0:
                logger.info(f"進捗: {i+1}/{len(candidates)} ({(i+1)/len(candidates)*100:.1f}%)")
            
            # レート制限
            collector.random_delay(0.3, 0.8)
            
        except Exception as e:
            logger.error(f"❌ {name}エラー: {e}")
            updated_candidates.append(candidate)
            continue
    
    # データ更新
    data['data'] = updated_candidates
    data['metadata']['collection_stats']['with_websites'] = success_count
    data['metadata']['quality_metrics']['website_coverage'] = f"{success_count/len(candidates)*100:.1f}%"
    data['metadata']['generated_at'] = datetime.now().isoformat()
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    enhanced_file = data_dir / f"go2senkyo_enhanced_{timestamp}.json"
    
    with open(enhanced_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"🎯 関連リンク収集完了:")
    logger.info(f"  成功: {success_count}/{len(candidates)}名 ({success_count/len(candidates)*100:.1f}%)")
    logger.info(f"📁 保存: {enhanced_file}")

def get_candidate_links(profile_url, collector):
    """個別プロフィールページから関連リンクを取得"""
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
                title = link.get_text(strip=True)
                
                if url and title and url.startswith('http'):
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
        additional_info = get_additional_profile_info(soup)
        links_info.update(additional_info)
        
    except Exception as e:
        logger.debug(f"関連リンク取得エラー: {e}")
    
    return links_info

def get_additional_profile_info(soup):
    """追加のプロフィール情報を取得"""
    info = {}
    
    try:
        # 年齢情報
        age_elem = soup.find(string=re.compile(r'(\d+)歳'))
        if age_elem:
            age_match = re.search(r'(\d+)歳', age_elem)
            if age_match:
                info["age_info"] = age_match.group(1)
        
        # 出身地情報
        birthplace_patterns = [
            r'出身[：:\s]*([都道府県市区町村\w]+)',
            r'生まれ[：:\s]*([都道府県市区町村\w]+)',
        ]
        
        text_content = soup.get_text()
        for pattern in birthplace_patterns:
            match = re.search(pattern, text_content)
            if match:
                birthplace = match.group(1).strip()
                if len(birthplace) <= 20:  # 妥当な長さかチェック
                    info["birthplace"] = birthplace
                break
        
        # 職業・肩書き情報
        occupation_selectors = [
            '.job', '.occupation', '.title', '.position',
            '[class*="job"]', '[class*="occupation"]', '[class*="title"]'
        ]
        
        for selector in occupation_selectors:
            elem = soup.select_one(selector)
            if elem:
                occupation = elem.get_text(strip=True)
                if occupation and len(occupation) <= 50 and len(occupation) >= 2:
                    info["occupation"] = occupation
                    break
        
        # 経歴情報（概要のみ）
        career_selectors = [
            '.profile', '.career', '.history', '.biography',
            '[class*="profile"]', '[class*="career"]', '[class*="history"]'
        ]
        
        for selector in career_selectors:
            elem = soup.select_one(selector)
            if elem:
                career = elem.get_text(strip=True)
                if career and len(career) >= 50:  # 意味のある経歴情報
                    info["career"] = career[:300]  # 300文字まで
                    break
        
    except Exception as e:
        logger.debug(f"追加情報取得エラー: {e}")
    
    return info

if __name__ == "__main__":
    collect_candidate_links()