#!/usr/bin/env python3
"""
全都道府県の完全修正版データ生成
既存の不完全データを修正版手法で補完
"""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteFixedDataGenerator:
    def __init__(self):
        self.session = requests.Session()
        ua = UserAgent()
        desktop_ua = ua.random
        
        self.session.headers.update({
            'User-Agent': desktop_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        # 政党マスターリスト
        self.parties = [
            "自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
            "国民民主党", "れいわ新選組", "参政党", "社会民主党", "NHK党",
            "日本保守党", "日本改革党", "無所属", "無所属連合", "日本誠真会",
            "日本の家庭を守る会", "再生の道", "差別撲滅党", "核融合党", "チームみらい",
            "多夫多妻党", "国政ガバナンスの会", "新党やまと", "未分類"
        ]

    def enhance_existing_candidate(self, candidate):
        """既存候補者データを修正版手法で強化"""
        candidate_id = candidate.get('candidate_id', '').replace('go2s_', '')
        if not candidate_id:
            return candidate
        
        try:
            logger.debug(f"候補者強化中: {candidate.get('name', 'unknown')} (ID: {candidate_id})")
            
            # プロフィールページから正確な情報を取得
            enhanced_info = self.get_accurate_candidate_info(candidate_id)
            if enhanced_info:
                # 既存データを強化
                candidate.update({
                    'name': enhanced_info.get('name', candidate.get('name', '')),
                    'name_kana': enhanced_info.get('name_kana', ''),
                    'party': enhanced_info.get('party', candidate.get('party', '未分類')),
                    'party_normalized': enhanced_info.get('party', candidate.get('party', '未分類')),
                    'profile_url': f"https://go2senkyo.com/seijika/{candidate_id}",
                    'source': 'enhanced_extraction',
                    'enhanced_at': datetime.now().isoformat()
                })
                
                return candidate
            
            # 強化に失敗した場合は元のデータを返す
            return candidate
            
        except Exception as e:
            logger.debug(f"候補者強化エラー {candidate_id}: {e}")
            return candidate

    def get_accurate_candidate_info(self, candidate_id: str):
        """プロフィールページから正確な候補者情報を取得"""
        profile_url = f"https://go2senkyo.com/seijika/{candidate_id}"
        
        try:
            response = self.session.get(profile_url, timeout=15)
            if response.status_code != 200:
                logger.debug(f"プロフィールページアクセス失敗: {candidate_id}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 名前と読みの抽出
            name_info = self.extract_name_and_reading_from_profile(soup)
            if not name_info or not name_info.get('name'):
                return None
            
            # 政党情報の抽出
            party = self.extract_party_from_profile(soup)
            
            return {
                'name': name_info['name'],
                'name_kana': name_info.get('reading', ''),
                'party': party
            }
            
        except Exception as e:
            logger.debug(f"プロフィール情報取得エラー {candidate_id}: {e}")
            return None

    def extract_name_and_reading_from_profile(self, soup: BeautifulSoup):
        """プロフィールページから名前と読みを抽出"""
        try:
            # 方法1: Go2senkyo特有の構造を使用
            name_elem = soup.find('h1', class_='p_seijika_profle_ttl')
            if name_elem:
                name_text = name_elem.get_text(strip=True)
                
                # 読み取得
                reading_elem = soup.find('p', class_='p_seijika_profle_subttl')
                reading_text = ""
                if reading_elem:
                    reading_full = reading_elem.get_text(strip=True)
                    reading_match = re.search(r'^([ァ-ヶー\s]+)', reading_full)
                    if reading_match:
                        reading_text = reading_match.group(1).strip()
                
                return {"name": name_text, "reading": reading_text}
            
            # 方法2: titleタグから抽出
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                
                # "牧山ひろえ（マキヤマヒロエ）｜政治家情報｜選挙ドットコム" 形式
                title_match = re.search(r'^([一-龯ひらがな\s]+)（([ァ-ヶー\s]+)）', title_text)
                if title_match:
                    name = title_match.group(1).strip()
                    reading = title_match.group(2).strip()
                    return {"name": name, "reading": reading}
                
                # "候補者名 | サイト名" 形式
                if '|' in title_text:
                    name_part = title_text.split('|')[0].strip()
                    name_clean = re.sub(r'（.*?）', '', name_part).strip()
                    name_match = re.search(r'([一-龯ひらがな\s]+)', name_clean)
                    if name_match:
                        name = name_match.group(1).strip()
                        return {"name": name, "reading": ""}
            
        except Exception as e:
            logger.debug(f"名前・読み抽出エラー: {e}")
        
        return {"name": "", "reading": ""}

    def extract_party_from_profile(self, soup: BeautifulSoup):
        """プロフィールページから政党情報を抽出"""
        try:
            page_text = soup.get_text()
            
            for party in self.parties:
                if party in page_text:
                    return party
            
        except Exception as e:
            logger.debug(f"政党抽出エラー: {e}")
        
        return "未分類"

def generate_complete_fixed_data():
    """完全修正版データの生成"""
    logger.info("🚀 全都道府県完全修正版データ生成開始...")
    
    generator = CompleteFixedDataGenerator()
    
    # 既存データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_candidates = data.get('data', [])
    logger.info(f"📊 元データ: {len(original_candidates)}名")
    
    # 重複除去
    unique_candidates = deduplicate_candidates(original_candidates)
    logger.info(f"📊 重複除去後: {len(unique_candidates)}名")
    
    # 各候補者を強化
    enhanced_candidates = []
    
    for i, candidate in enumerate(unique_candidates):
        try:
            # 進捗表示
            if (i + 1) % 20 == 0 or (i + 1) <= 5:
                logger.info(f"📍 進捗: {i+1}/{len(unique_candidates)} - {candidate.get('name', 'unknown')}")
            
            # 候補者強化
            enhanced = generator.enhance_existing_candidate(candidate)
            enhanced_candidates.append(enhanced)
            
            # レート制限
            time.sleep(0.8)
            
        except Exception as e:
            logger.error(f"❌ 候補者 {i+1} 強化エラー: {e}")
            enhanced_candidates.append(candidate)
            continue
    
    logger.info(f"🎯 強化完了: {len(enhanced_candidates)}名")
    
    # データ保存
    save_complete_fixed_data(enhanced_candidates, data_dir)

def deduplicate_candidates(candidates):
    """候補者重複除去"""
    seen_ids = set()
    unique_candidates = []
    
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', '')
        if candidate_id and candidate_id not in seen_ids:
            seen_ids.add(candidate_id)
            unique_candidates.append(candidate)
    
    return unique_candidates

def save_complete_fixed_data(candidates, data_dir):
    """完全修正版データの保存"""
    logger.info("💾 完全修正版データの保存...")
    
    # 統計計算
    party_stats = {}
    prefecture_stats = {}
    enhanced_count = 0
    
    for candidate in candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
        
        if candidate.get('name_kana'):
            enhanced_count += 1
    
    # データ構造
    data = {
        "metadata": {
            "data_type": "go2senkyo_complete_fixed_sangiin_2025",
            "collection_method": "existing_data_profile_enhancement",
            "total_candidates": len(candidates),
            "enhanced_candidates": enhanced_count,
            "generated_at": datetime.now().isoformat(),
            "source_site": "go2senkyo.com (profile pages)",
            "coverage": {
                "constituency_types": 1,
                "parties": len(party_stats),
                "prefectures": len(prefecture_stats)
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_constituency_type": {"single_member": len(candidates)}
        },
        "data": candidates
    }
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    complete_file = data_dir / f"go2senkyo_complete_fixed_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(complete_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {complete_file}")
    
    # 統計表示
    logger.info("\n📊 完全修正版統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    logger.info(f"  強化成功: {enhanced_count}名 ({enhanced_count/len(candidates)*100:.1f}%)")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")

if __name__ == "__main__":
    generate_complete_fixed_data()