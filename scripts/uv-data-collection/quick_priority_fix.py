#!/usr/bin/env python3
"""
優先度の高い都道府県の迅速修正
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

class QuickPriorityFixer:
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
        
        # 問題のある都道府県（現在のデータが少なすぎる）
        self.priority_prefectures = [
            (1, "北海道"),    # 実際11名 → 現在0名
            (3, "岩手県"),    # 推定6-8名 → 現在0名
            (14, "神奈川県"), # 実際15名 → 現在3名
            (33, "岡山県"),   # 推定6-8名 → 現在0名
            (45, "宮崎県"),   # 推定4-6名 → 現在0名
            (46, "鹿児島県"), # 推定5-7名 → 現在0名
            
            # 1名しかない都道府県（少なすぎる）
            (2, "青森県"),    # 現在1名 → 推定4-6名
            (4, "宮城県"),    # 現在1名 → 推定6-8名
            (5, "秋田県"),    # 現在1名 → 推定3-5名
            (17, "石川県"),   # 現在1名 → 推定3-5名
            (18, "福井県"),   # 現在1名 → 推定3-4名
            (19, "山梨県"),   # 現在1名 → 推定3-4名
            (20, "長野県"),   # 現在1名 → 推定6-8名
            (35, "山口県"),   # 現在1名 → 推定4-6名
            (38, "愛媛県"),   # 現在1名 → 推定4-6名
            (47, "沖縄県"),   # 現在1名 → 推定4-6名
        ]
        
        # 政党マスターリスト
        self.parties = [
            "自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
            "国民民主党", "れいわ新選組", "参政党", "社会民主党", "NHK党",
            "日本保守党", "日本改革党", "無所属", "無所属連合", "日本誠真会",
            "日本の家庭を守る会", "再生の道", "差別撲滅党", "核融合党", "チームみらい",
            "多夫多妻党", "国政ガバナンスの会", "新党やまと", "未分類"
        ]
    
    def extract_all_candidates_robust(self, pref_code: int, pref_name: str):
        """堅牢な候補者抽出"""
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        logger.info(f"🔍 {pref_name} (コード: {pref_code}) 堅牢抽出開始")
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # まず実際のプロフィールリンク数を確認
            profile_links = soup.find_all('a', href=re.compile(r'/seijika/\d+'))
            unique_ids = set()
            for link in profile_links:
                match = re.search(r'/seijika/(\d+)', link.get('href', ''))
                if match:
                    unique_ids.add(match.group(1))
            
            logger.info(f"📊 {pref_name} 発見プロフィール: {len(unique_ids)}個")
            
            candidates = []
            processed_ids = set()
            
            # 各ユニークIDに対して候補者情報を抽出
            for i, candidate_id in enumerate(unique_ids):
                try:
                    # このIDに対応するリンクを再検索
                    target_link = soup.find('a', href=re.compile(f'/seijika/{candidate_id}'))
                    if not target_link:
                        continue
                    
                    candidate = self.extract_candidate_from_context(target_link, pref_name, candidate_id, url)
                    if candidate and candidate_id not in processed_ids:
                        candidates.append(candidate)
                        processed_ids.add(candidate_id)
                        logger.info(f"  ✅ {i+1}: {candidate['name']} ({candidate['party']})")
                
                except Exception as e:
                    logger.debug(f"候補者 {candidate_id} 抽出エラー: {e}")
                    continue
            
            logger.info(f"🎯 {pref_name} 抽出完了: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ {pref_name} データ抽出エラー: {e}")
            return []
    
    def extract_candidate_from_context(self, link, prefecture: str, candidate_id: str, page_url: str):
        """コンテキストから候補者情報抽出"""
        try:
            candidate = {
                "candidate_id": f"go2s_{candidate_id}",
                "name": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "profile_url": f"https://go2senkyo.com{link.get('href')}",
                "source_page": page_url,
                "source": "robust_extraction",
                "collected_at": datetime.now().isoformat()
            }
            
            # 1. 名前抽出（複数方法）
            name = self.extract_name_robust(link)
            if name:
                candidate["name"] = name
            else:
                # 名前が取得できない場合はスキップ
                return None
            
            # 2. 政党抽出
            party = self.extract_party_robust(link)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            return candidate
            
        except Exception as e:
            logger.debug(f"候補者情報抽出エラー: {e}")
            return None
    
    def extract_name_robust(self, link):
        """堅牢な名前抽出"""
        name = ""
        
        try:
            # 方法1: リンクテキスト直接確認
            link_text = link.get_text(strip=True)
            if link_text and link_text not in ['詳細・プロフィール', 'プロフィール', '詳細']:
                if re.match(r'[一-龯ひらがなカタカナ]{2,}', link_text):
                    return link_text
            
            # 方法2: 親要素階層検索
            current = link.parent
            search_levels = 0
            
            while current and search_levels < 8:  # より深く検索
                # クラス名ベース検索
                name_candidates = current.find_all(class_=re.compile(r'name|title|candidate|person'))
                for elem in name_candidates:
                    text = elem.get_text(strip=True)
                    if text and len(text) <= 20:  # 適度な長さ
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', text)
                        if name_match:
                            potential_name = name_match.group(1)
                            if potential_name not in ['詳細', 'プロフィール', '選挙', '候補者', '政治家']:
                                return potential_name
                
                # テキストベース検索
                current_text = current.get_text()
                text_lines = [line.strip() for line in current_text.split('\n') if line.strip()]
                
                for line in text_lines:
                    if len(line) <= 15:  # 短い行に注目
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', line)
                        if name_match:
                            potential_name = name_match.group(1)
                            if (potential_name not in ['詳細', 'プロフィール', '選挙', '候補者', '政治家', '自民党', '民主党'] and
                                len(potential_name) >= 2):
                                return potential_name
                
                current = current.parent
                search_levels += 1
            
            # 方法3: より広範囲の兄弟要素検索
            if link.parent:
                for sibling in link.parent.find_all_next(limit=10):
                    sibling_text = sibling.get_text(strip=True)
                    if sibling_text and len(sibling_text) <= 10:
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', sibling_text)
                        if name_match:
                            potential_name = name_match.group(1)
                            if potential_name not in ['詳細', 'プロフィール']:
                                return potential_name
        
        except Exception as e:
            logger.debug(f"名前抽出エラー: {e}")
        
        return name
    
    def extract_party_robust(self, link):
        """堅牢な政党抽出"""
        try:
            # 広範囲のコンテキスト検索
            current = link.parent
            search_levels = 0
            
            while current and search_levels < 10:
                current_text = current.get_text()
                
                for party in self.parties:
                    if party in current_text:
                        return party
                
                current = current.parent
                search_levels += 1
            
        except Exception as e:
            logger.debug(f"政党抽出エラー: {e}")
        
        return "未分類"

def quick_priority_fix():
    """優先度修正の実行"""
    logger.info("🚀 優先度の高い都道府県の迅速修正開始...")
    
    fixer = QuickPriorityFixer()
    
    # 現在のデータ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    current_candidates = data.get('data', [])
    logger.info(f"📊 現在のデータ: {len(current_candidates)}名")
    
    # 問題のある都道府県を修正
    fixed_candidates = []
    problem_prefectures = set()
    
    for pref_code, pref_name in fixer.priority_prefectures:
        problem_prefectures.add(pref_name)
    
    # 問題のない都道府県のデータは保持
    for candidate in current_candidates:
        if candidate['prefecture'] not in problem_prefectures:
            fixed_candidates.append(candidate)
    
    logger.info(f"📊 保持データ: {len(fixed_candidates)}名")
    
    # 問題のある都道府県を再収集
    for pref_code, pref_name in fixer.priority_prefectures:
        logger.info(f"\n=== {pref_name} 修正処理 ===")
        
        try:
            new_candidates = fixer.extract_all_candidates_robust(pref_code, pref_name)
            if new_candidates:
                fixed_candidates.extend(new_candidates)
                logger.info(f"✅ {pref_name} 修正完了: {len(new_candidates)}名追加")
            else:
                logger.warning(f"⚠️ {pref_name} データ取得失敗")
            
            # レート制限
            time.sleep(1.5)
            
        except Exception as e:
            logger.error(f"❌ {pref_name} 修正エラー: {e}")
            continue
    
    logger.info(f"\n📊 修正後総数: {len(fixed_candidates)}名")
    
    # データ保存
    save_fixed_data(fixed_candidates, data_dir)

def save_fixed_data(candidates, data_dir):
    """修正データの保存"""
    logger.info("💾 修正データの保存...")
    
    # 統計計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    # データ構造
    data = {
        "metadata": {
            "data_type": "go2senkyo_priority_fixed_sangiin_2025",
            "collection_method": "priority_robust_extraction",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
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
    
    priority_file = data_dir / f"go2senkyo_priority_fixed_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(priority_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {priority_file}")
    
    # 統計表示
    logger.info("\n📊 修正後統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    logger.info("\n🗾 都道府県別統計（問題があった都道府県）:")
    problem_prefs = ["北海道", "岩手県", "神奈川県", "岡山県", "宮崎県", "鹿児島県", 
                    "青森県", "宮城県", "秋田県", "石川県", "福井県", "山梨県", 
                    "長野県", "山口県", "愛媛県", "沖縄県"]
    
    for pref in problem_prefs:
        count = prefecture_stats.get(pref, 0)
        logger.info(f"  {pref}: {count}名")

if __name__ == "__main__":
    quick_priority_fix()