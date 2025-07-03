#!/usr/bin/env python3
"""
正確な名前抽出とデータ重複修正
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

class FixedExtractionProperNames:
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
    
    def extract_prefecture_fixed(self, pref_code: int, pref_name: str):
        """修正版都道府県抽出"""
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        logger.info(f"🔍 {pref_name} (コード: {pref_code}) 修正版抽出開始")
        
        try:
            # ページ取得
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.info(f"📊 {pref_name} HTML取得: {len(response.text):,} 文字")
            
            # 動的コンテンツ読み込み待機
            time.sleep(2)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # プロフィールリンクを取得
            profile_links = soup.find_all('a', href=re.compile(r'/seijika/\d+'))
            unique_ids = set()
            
            for link in profile_links:
                match = re.search(r'/seijika/(\d+)', link.get('href', ''))
                if match:
                    unique_ids.add(match.group(1))
            
            logger.info(f"📊 {pref_name} 発見ユニークID: {len(unique_ids)}個")
            
            candidates = []
            
            # 各候補者IDに対して正確な情報を取得
            for candidate_id in unique_ids:
                try:
                    candidate = self.get_accurate_candidate_info(candidate_id, pref_name, url)
                    if candidate:
                        candidates.append(candidate)
                        logger.info(f"  ✅ {candidate['name']} ({candidate['party']}) - ID: {candidate_id}")
                    
                    # API制限対策
                    time.sleep(1)
                
                except Exception as e:
                    logger.debug(f"候補者 {candidate_id} 取得エラー: {e}")
                    continue
            
            logger.info(f"🎯 {pref_name} 抽出完了: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ {pref_name} データ抽出エラー: {e}")
            return []
    
    def get_accurate_candidate_info(self, candidate_id: str, prefecture: str, source_url: str):
        """プロフィールページから正確な候補者情報を取得"""
        profile_url = f"https://go2senkyo.com/seijika/{candidate_id}"
        
        try:
            logger.debug(f"📄 プロフィール取得: {profile_url}")
            
            response = self.session.get(profile_url, timeout=20)
            if response.status_code != 200:
                logger.debug(f"プロフィールページアクセス失敗: {candidate_id}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 候補者基本情報
            candidate = {
                "candidate_id": f"go2s_{candidate_id}",
                "name": "",
                "name_kana": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "profile_url": profile_url,
                "source_page": source_url,
                "source": "profile_page_extraction",
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前と読みの抽出
            name_info = self.extract_name_and_reading_from_profile(soup)
            if name_info:
                candidate["name"] = name_info["name"]
                if name_info["reading"]:
                    candidate["name_kana"] = name_info["reading"]
            
            # 政党情報の抽出
            party = self.extract_party_from_profile(soup)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            # 名前が取得できない場合はスキップ
            if not candidate["name"]:
                logger.debug(f"名前取得失敗: {candidate_id}")
                return None
            
            return candidate
            
        except Exception as e:
            logger.debug(f"プロフィール情報取得エラー {candidate_id}: {e}")
            return None
    
    def extract_name_and_reading_from_profile(self, soup: BeautifulSoup):
        """プロフィールページから名前と読みを抽出"""
        try:
            # 方法1: Go2senkyo特有の構造を使用
            # 名前: <h1 class="p_seijika_profle_ttl">牧山 ひろえ</h1>
            name_elem = soup.find('h1', class_='p_seijika_profle_ttl')
            if name_elem:
                name_text = name_elem.get_text(strip=True)
                logger.debug(f"名前要素発見: {name_text}")
                
                # 読み: <p class="p_seijika_profle_subttl">マキヤマ ヒロエ／60歳／女</p>
                reading_elem = soup.find('p', class_='p_seijika_profle_subttl')
                reading_text = ""
                if reading_elem:
                    reading_full = reading_elem.get_text(strip=True)
                    # "マキヤマ ヒロエ／60歳／女" から読み部分のみ抽出
                    reading_match = re.search(r'^([ァ-ヶー\s]+)', reading_full)
                    if reading_match:
                        reading_text = reading_match.group(1).strip()
                        logger.debug(f"読み要素発見: {reading_text}")
                
                return {"name": name_text, "reading": reading_text}
            
            # 方法2: titleタグから抽出（バックアップ）
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                logger.debug(f"titleタグ: {title_text}")
                
                # "牧山ひろえ（マキヤマヒロエ）｜政治家情報｜選挙ドットコム" 形式
                title_match = re.search(r'^([一-龯ひらがな\s]+)（([ァ-ヶー\s]+)）', title_text)
                if title_match:
                    name = title_match.group(1).strip()
                    reading = title_match.group(2).strip()
                    logger.debug(f"titleから抽出: 名前={name}, 読み={reading}")
                    return {"name": name, "reading": reading}
                
                # "候補者名 | サイト名" 形式（読みなし）
                if '|' in title_text:
                    name_part = title_text.split('|')[0].strip()
                    # カッコ部分を除去
                    name_clean = re.sub(r'（.*?）', '', name_part).strip()
                    name_match = re.search(r'([一-龯ひらがな\s]+)', name_clean)
                    if name_match:
                        name = name_match.group(1).strip()
                        return {"name": name, "reading": ""}
            
            # 方法3: 他のh1要素をチェック
            h1_elements = soup.find_all('h1')
            for h1 in h1_elements:
                h1_text = h1.get_text(strip=True)
                if h1_text and len(h1_text) <= 20 and h1_text != "選挙ドットコム":
                    # 日本人名パターンマッチ
                    name_match = re.search(r'([一-龯ひらがな\s]+)', h1_text)
                    if name_match:
                        name = name_match.group(1).strip()
                        logger.debug(f"h1から抽出: {name}")
                        return {"name": name, "reading": ""}
            
            # 方法4: data-history_ttl属性から抽出
            contents_div = soup.find('div', {'data-history_ttl': True})
            if contents_div:
                history_name = contents_div.get('data-history_ttl', '').strip()
                if history_name:
                    logger.debug(f"data-history_ttlから抽出: {history_name}")
                    return {"name": history_name, "reading": ""}
            
        except Exception as e:
            logger.debug(f"名前・読み抽出エラー: {e}")
        
        return {"name": "", "reading": ""}
    
    def parse_name_and_reading(self, full_name: str):
        """名前と読みを分離（大きい方が名前、小さい方が読み）"""
        try:
            # 全角スペース・半角スペースで分割
            parts = re.split(r'[\s　]+', full_name.strip())
            
            if len(parts) == 2:
                part1, part2 = parts[0].strip(), parts[1].strip()
                
                # 文字数比較（大きい方が名前、小さい方が読み）
                if len(part1) >= len(part2):
                    name = part1
                    reading = part2
                else:
                    name = part2
                    reading = part1
                
                # ひらがな・カタカナが多い方を読みに
                part1_kana_ratio = len(re.findall(r'[ひらがなカタカナ]', part1)) / len(part1) if part1 else 0
                part2_kana_ratio = len(re.findall(r'[ひらがなカタカナ]', part2)) / len(part2) if part2 else 0
                
                if part1_kana_ratio > part2_kana_ratio:
                    name = part2
                    reading = part1
                elif part2_kana_ratio > part1_kana_ratio:
                    name = part1
                    reading = part2
                
                return {"name": name, "reading": reading}
            
            elif len(parts) == 1:
                # 1つの要素の場合、そのまま名前として使用
                return {"name": parts[0], "reading": ""}
            
            else:
                # 3つ以上の要素がある場合、最初の2つを使用
                if len(parts) >= 2:
                    part1, part2 = parts[0].strip(), parts[1].strip()
                    
                    # 同じロジックを適用
                    if len(part1) >= len(part2):
                        return {"name": part1, "reading": part2}
                    else:
                        return {"name": part2, "reading": part1}
        
        except Exception as e:
            logger.debug(f"名前分離エラー: {e}")
        
        return {"name": full_name, "reading": ""}
    
    def extract_party_from_profile(self, soup: BeautifulSoup):
        """プロフィールページから政党情報を抽出"""
        try:
            # ページ全体のテキストから政党を検索
            page_text = soup.get_text()
            
            for party in self.parties:
                if party in page_text:
                    return party
            
            # より詳細な検索
            text_lines = [line.strip() for line in page_text.split('\n') if line.strip()]
            for line in text_lines:
                if len(line) <= 50:  # 短い行に政党情報がある可能性
                    for party in self.parties:
                        if party in line:
                            return party
        
        except Exception as e:
            logger.debug(f"政党抽出エラー: {e}")
        
        return "未分類"

def test_fixed_extraction():
    """修正版抽出のテスト"""
    logger.info("🚀 修正版名前抽出のテスト開始...")
    
    extractor = FixedExtractionProperNames()
    
    # テスト対象都道府県（問題が明確な県）
    test_prefectures = [
        (14, "神奈川県"),  # 牧山重複問題
        (1, "北海道"),    # 田中重複問題
    ]
    
    all_results = []
    
    for pref_code, pref_name in test_prefectures:
        logger.info(f"\n=== {pref_name} 修正版テスト ===")
        
        try:
            candidates = extractor.extract_prefecture_fixed(pref_code, pref_name)
            all_results.extend(candidates)
            
            logger.info(f"✅ {pref_name} テスト完了: {len(candidates)}名")
            
            # 詳細表示
            logger.info(f"📋 {pref_name} 候補者詳細:")
            for i, candidate in enumerate(candidates):
                reading_info = f" (読み: {candidate['name_kana']})" if candidate['name_kana'] else ""
                logger.info(f"  {i+1}. {candidate['name']}{reading_info} ({candidate['party']}) - ID: {candidate['candidate_id']}")
            
            # テスト間の待機
            time.sleep(3)
            
        except Exception as e:
            logger.error(f"❌ {pref_name} テストエラー: {e}")
            continue
    
    logger.info(f"\n🎯 修正版テスト完了: 総計 {len(all_results)}名")
    
    # 重複チェック
    check_duplicates(all_results)
    
    # 結果保存
    save_fixed_test_results(all_results)

def check_duplicates(candidates):
    """重複チェック"""
    logger.info("\n🔍 重複チェック:")
    
    # 名前ベースの重複
    name_counts = {}
    for candidate in candidates:
        name = candidate['name']
        prefecture = candidate['prefecture']
        key = f"{name} ({prefecture})"
        name_counts[key] = name_counts.get(key, 0) + 1
    
    duplicates = {k: v for k, v in name_counts.items() if v > 1}
    if duplicates:
        logger.info("⚠️ 名前ベース重複:")
        for name_pref, count in duplicates.items():
            logger.info(f"  {name_pref}: {count}回")
    else:
        logger.info("✅ 名前ベース重複なし")
    
    # IDベースの重複
    id_counts = {}
    for candidate in candidates:
        candidate_id = candidate['candidate_id']
        id_counts[candidate_id] = id_counts.get(candidate_id, 0) + 1
    
    id_duplicates = {k: v for k, v in id_counts.items() if v > 1}
    if id_duplicates:
        logger.info("⚠️ IDベース重複:")
        for cid, count in id_duplicates.items():
            logger.info(f"  {cid}: {count}回")
    else:
        logger.info("✅ IDベース重複なし")

def save_fixed_test_results(candidates):
    """修正版テスト結果の保存"""
    logger.info("💾 修正版テスト結果の保存...")
    
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
            "data_type": "go2senkyo_fixed_names_sangiin_2025",
            "collection_method": "profile_page_accurate_extraction",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "go2senkyo.com (profile pages)",
            "test_prefectures": ["神奈川県", "北海道"]
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
    
    fixed_file = data_dir / f"go2senkyo_fixed_names_{timestamp}.json"
    
    with open(fixed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 修正版テスト結果保存: {fixed_file}")
    
    # 統計表示
    logger.info("\n📊 修正版テスト結果統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    
    for pref, count in prefecture_stats.items():
        logger.info(f"  {pref}: {count}名")

if __name__ == "__main__":
    test_fixed_extraction()