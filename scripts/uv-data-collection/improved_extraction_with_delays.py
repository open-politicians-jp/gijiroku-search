#!/usr/bin/env python3
"""
遅延を考慮した改良版データ抽出
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

class ImprovedExtractionWithDelays:
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
        
        # テスト用優先都道府県
        self.test_prefectures = [
            (14, "神奈川県"),  # 牧山問題の確認
            (1, "北海道"),    # 大きな県でのテスト
            (13, "東京都"),   # 最大数でのテスト
        ]
        
        # 政党マスターリスト
        self.parties = [
            "自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
            "国民民主党", "れいわ新選組", "参政党", "社会民主党", "NHK党",
            "日本保守党", "日本改革党", "無所属", "無所属連合", "日本誠真会",
            "日本の家庭を守る会", "再生の道", "差別撲滅党", "核融合党", "チームみらい",
            "多夫多妻党", "国政ガバナンスの会", "新党やまと", "未分類"
        ]
    
    def extract_with_proper_delays(self, pref_code: int, pref_name: str):
        """適切な遅延を考慮した抽出"""
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        logger.info(f"🔍 {pref_name} (コード: {pref_code}) 遅延考慮抽出開始")
        
        try:
            # 初回リクエスト
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.info(f"📊 {pref_name} 初回HTML取得: {len(response.text):,} 文字")
            
            # 動的コンテンツの読み込み待機
            logger.info(f"⏳ {pref_name} 動的コンテンツ読み込み待機中...")
            time.sleep(3)  # 3秒待機
            
            # 再リクエストでフルコンテンツ取得
            response2 = self.session.get(url, timeout=30)
            logger.info(f"📊 {pref_name} 再取得HTML: {len(response2.text):,} 文字")
            
            soup = BeautifulSoup(response2.text, 'html.parser')
            
            # プロフィールリンク検索
            profile_links = soup.find_all('a', href=re.compile(r'/seijika/\d+'))
            unique_ids = set()
            for link in profile_links:
                match = re.search(r'/seijika/(\d+)', link.get('href', ''))
                if match:
                    unique_ids.add(match.group(1))
            
            logger.info(f"📊 {pref_name} 発見プロフィール: {len(unique_ids)}個")
            
            candidates = []
            processed_ids = set()
            
            # 各候補者の詳細情報を順次取得
            for i, candidate_id in enumerate(unique_ids):
                try:
                    # 候補者詳細取得（さらに遅延）
                    candidate = self.extract_candidate_detailed(soup, candidate_id, pref_name, url, i)
                    if candidate and candidate_id not in processed_ids:
                        candidates.append(candidate)
                        processed_ids.add(candidate_id)
                        logger.info(f"  ✅ {i+1}: {candidate['name']} ({candidate['party']}) - ID: {candidate_id}")
                    
                    # 個別候補者間の遅延
                    time.sleep(0.5)
                
                except Exception as e:
                    logger.debug(f"候補者 {candidate_id} 抽出エラー: {e}")
                    continue
            
            logger.info(f"🎯 {pref_name} 遅延考慮抽出完了: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ {pref_name} データ抽出エラー: {e}")
            return []
    
    def extract_candidate_detailed(self, soup: BeautifulSoup, candidate_id: str, prefecture: str, page_url: str, index: int):
        """詳細な候補者情報抽出"""
        try:
            candidate = {
                "candidate_id": f"go2s_{candidate_id}",
                "name": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "profile_url": f"https://go2senkyo.com/seijika/{candidate_id}",
                "source_page": page_url,
                "source": "delayed_extraction",
                "collected_at": datetime.now().isoformat()
            }
            
            # 該当するプロフィールリンクを検索
            target_links = soup.find_all('a', href=re.compile(f'/seijika/{candidate_id}'))
            
            if not target_links:
                return None
            
            # 最も情報が豊富なリンクを選択
            best_link = None
            max_context_length = 0
            
            for link in target_links:
                context_text = ""
                if link.parent:
                    context_text = link.parent.get_text()
                if len(context_text) > max_context_length:
                    max_context_length = len(context_text)
                    best_link = link
            
            if not best_link:
                best_link = target_links[0]
            
            # 名前抽出（複数方法を組み合わせ）
            name = self.extract_name_comprehensive(best_link)
            if name:
                candidate["name"] = name
            else:
                # 名前が取得できない場合は詳細プロフィールページから取得
                name = self.fetch_name_from_profile_page(candidate_id)
                if name:
                    candidate["name"] = name
                else:
                    return None
            
            # 政党抽出
            party = self.extract_party_comprehensive(best_link)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            return candidate
            
        except Exception as e:
            logger.debug(f"詳細候補者抽出エラー: {e}")
            return None
    
    def extract_name_comprehensive(self, link):
        """包括的な名前抽出"""
        name = ""
        
        try:
            # 方法1: リンクテキスト
            link_text = link.get_text(strip=True)
            if link_text and link_text not in ['詳細・プロフィール', 'プロフィール', '詳細']:
                if re.match(r'[一-龯ひらがなカタカナ]{2,}', link_text):
                    return link_text
            
            # 方法2: 特定クラス名での検索
            current = link.parent
            search_depth = 0
            
            while current and search_depth < 10:
                # 候補者名を含みそうなクラス
                name_elements = current.find_all(class_=re.compile(r'name|title|candidate|person|profile'))
                for elem in name_elements:
                    text = elem.get_text(strip=True)
                    if text and len(text) <= 20:
                        # 日本人名パターン
                        name_patterns = [
                            r'([一-龯]{2,4}[ひらがな]{0,4})',  # 漢字＋ひらがな
                            r'([一-龯]{2,6})',                 # 漢字のみ
                            r'([一-龯ひらがなカタカナ]{2,8})',  # 混合
                        ]
                        
                        for pattern in name_patterns:
                            matches = re.findall(pattern, text)
                            for match in matches:
                                if match not in ['詳細', 'プロフィール', '選挙', '候補', '政党', '議員']:
                                    return match
                
                current = current.parent
                search_depth += 1
            
            # 方法3: より広範囲のテキスト解析
            if link.parent:
                parent_text = link.parent.get_text()
                text_lines = [line.strip() for line in parent_text.split('\n') if line.strip()]
                
                for line in text_lines:
                    if len(line) <= 15 and '詳細' not in line and 'プロフィール' not in line:
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', line)
                        if name_match:
                            potential_name = name_match.group(1)
                            if len(potential_name) >= 2:
                                return potential_name
        
        except Exception as e:
            logger.debug(f"包括的名前抽出エラー: {e}")
        
        return name
    
    def fetch_name_from_profile_page(self, candidate_id: str):
        """プロフィールページから名前を直接取得"""
        try:
            profile_url = f"https://go2senkyo.com/seijika/{candidate_id}"
            logger.debug(f"プロフィールページから名前取得: {profile_url}")
            
            response = self.session.get(profile_url, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # プロフィールページの名前要素を検索
                name_selectors = [
                    'h1',
                    '.candidate-name',
                    '.profile-name',
                    '.person-name',
                    'title'
                ]
                
                for selector in name_selectors:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(strip=True)
                        if text and len(text) <= 20:
                            name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', text)
                            if name_match:
                                return name_match.group(1)
            
            # 少し待機してから次の処理へ
            time.sleep(1)
        
        except Exception as e:
            logger.debug(f"プロフィールページ名前取得エラー: {e}")
        
        return ""
    
    def extract_party_comprehensive(self, link):
        """包括的な政党抽出"""
        try:
            current = link.parent
            search_depth = 0
            
            while current and search_depth < 12:
                current_text = current.get_text()
                
                for party in self.parties:
                    if party in current_text:
                        return party
                
                current = current.parent
                search_depth += 1
            
        except Exception as e:
            logger.debug(f"包括的政党抽出エラー: {e}")
        
        return "未分類"

def test_improved_extraction():
    """改良版抽出のテスト"""
    logger.info("🚀 遅延考慮改良版抽出のテスト開始...")
    
    extractor = ImprovedExtractionWithDelays()
    
    # テスト対象都道府県
    test_results = []
    
    for pref_code, pref_name in extractor.test_prefectures:
        logger.info(f"\n=== {pref_name} テスト ===")
        
        try:
            candidates = extractor.extract_with_proper_delays(pref_code, pref_name)
            test_results.extend(candidates)
            
            logger.info(f"✅ {pref_name} テスト完了: {len(candidates)}名")
            
            # 詳細表示
            logger.info(f"📋 {pref_name} 候補者一覧:")
            for i, candidate in enumerate(candidates):
                logger.info(f"  {i+1}. {candidate['name']} ({candidate['party']}) - ID: {candidate['candidate_id']}")
            
            # テスト間の待機
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"❌ {pref_name} テストエラー: {e}")
            continue
    
    logger.info(f"\n🎯 テスト完了: 総計 {len(test_results)}名")
    
    # 結果保存
    save_test_results(test_results)

def save_test_results(candidates):
    """テスト結果の保存"""
    logger.info("💾 テスト結果の保存...")
    
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
            "data_type": "go2senkyo_delayed_test_sangiin_2025",
            "collection_method": "delayed_comprehensive_extraction",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "test_prefectures": ["神奈川県", "北海道", "東京都"]
        },
        "statistics": {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_constituency_type": {"single_member": len(candidates)}
        },
        "data": candidates
    }
    
    # ファイル保存
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    test_file = data_dir / f"go2senkyo_delayed_test_{timestamp}.json"
    
    with open(test_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 テスト結果保存: {test_file}")
    
    # 統計表示
    logger.info("\n📊 テスト結果統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    
    for pref, count in prefecture_stats.items():
        logger.info(f"  {pref}: {count}名")
    
    # 重複チェック
    name_counts = {}
    for candidate in candidates:
        name = candidate['name']
        prefecture = candidate['prefecture']
        key = f"{name} ({prefecture})"
        name_counts[key] = name_counts.get(key, 0) + 1
    
    duplicates = {k: v for k, v in name_counts.items() if v > 1}
    if duplicates:
        logger.info("\n⚠️ 重複候補者:")
        for name_pref, count in duplicates.items():
            logger.info(f"  {name_pref}: {count}回")

if __name__ == "__main__":
    test_improved_extraction()