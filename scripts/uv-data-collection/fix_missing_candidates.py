#!/usr/bin/env python3
"""
不足している候補者の修正収集
"""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class MissingCandidatesFixer:
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
    
    def get_all_candidates_for_prefecture(self, pref_code: int, pref_name: str):
        """都道府県の全候補者を取得"""
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        logger.info(f"🔍 {pref_name} (コード: {pref_code}) データ取得: {url}")
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.info(f"📊 {pref_name} HTML取得成功: {len(response.text):,} 文字")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 全ての候補者プロフィールリンクを検索
            profile_links = soup.find_all('a', href=re.compile(r'/seijika/\d+'))
            logger.info(f"🔗 {pref_name} プロフィールリンク発見: {len(profile_links)}個")
            
            candidates = []
            seen_ids = set()
            
            for i, link in enumerate(profile_links):
                try:
                    href = link.get('href', '')
                    if not href:
                        continue
                    
                    # 候補者ID抽出
                    match = re.search(r'/seijika/(\d+)', href)
                    if not match:
                        continue
                    
                    candidate_id = match.group(1)
                    if candidate_id in seen_ids:
                        continue
                    seen_ids.add(candidate_id)
                    
                    # 候補者情報抽出
                    candidate_info = self.extract_candidate_info(link, pref_name, candidate_id, url)
                    if candidate_info:
                        candidates.append(candidate_info)
                        logger.info(f"  ✅ {i+1}: {candidate_info['name']} ({candidate_info['party']})")
                    
                except Exception as e:
                    logger.debug(f"リンク {i} 処理エラー: {e}")
                    continue
            
            logger.info(f"🎯 {pref_name} 取得完了: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ {pref_name} データ取得エラー: {e}")
            return []
    
    def extract_candidate_info(self, link, prefecture: str, candidate_id: str, page_url: str):
        """候補者情報を抽出"""
        try:
            # 基本情報
            candidate = {
                "candidate_id": f"go2s_{candidate_id}",
                "name": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', ''),
                "constituency_type": "single_member",
                "party": "",
                "party_normalized": "",
                "profile_url": f"https://go2senkyo.com{link.get('href')}",
                "source_page": page_url,
                "source": "go2senkyo_fixed",
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前の抽出（複数方法試行）
            name = self.extract_name_from_context(link)
            if name:
                candidate["name"] = name
            
            # 政党の抽出
            party = self.extract_party_from_context(link)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            # 名前が取得できない場合はスキップ
            if not candidate["name"]:
                return None
            
            return candidate
            
        except Exception as e:
            logger.debug(f"候補者情報抽出エラー: {e}")
            return None
    
    def extract_name_from_context(self, link):
        """リンク周辺から名前を抽出"""
        name = ""
        
        try:
            # 1. リンクテキスト確認
            link_text = link.get_text(strip=True)
            if link_text and link_text not in ['詳細・プロフィール', 'プロフィール', '詳細']:
                if re.match(r'[一-龯ひらがなカタカナ]{2,}', link_text):
                    name = link_text
                    return name
            
            # 2. 親要素から検索
            parent = link.parent
            search_depth = 0
            while parent and search_depth < 5:
                # クラス名でのターゲット検索
                name_elements = parent.find_all(class_=re.compile(r'name|title|candidate'))
                for elem in name_elements:
                    text = elem.get_text(strip=True)
                    if text and text not in ['詳細・プロフィール', 'プロフィール']:
                        # 日本人名パターンマッチ
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', text)
                        if name_match:
                            potential_name = name_match.group(1)
                            if len(potential_name) >= 2:
                                name = potential_name
                                return name
                
                # テキストコンテンツ全体から検索
                parent_text = parent.get_text(strip=True)
                lines = parent_text.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and len(line) < 30:  # 短いテキスト行
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', line)
                        if name_match:
                            potential_name = name_match.group(1)
                            if len(potential_name) >= 2 and potential_name not in ['詳細', 'プロフィール', '選挙', '候補']:
                                name = potential_name
                                return name
                
                parent = parent.parent
                search_depth += 1
            
            # 3. 兄弟要素から検索
            if link.parent:
                siblings = link.parent.find_all(text=True)
                for sibling in siblings:
                    text = sibling.strip()
                    if text:
                        name_match = re.search(r'([一-龯ひらがなカタカナ]{2,8})', text)
                        if name_match:
                            potential_name = name_match.group(1)
                            if len(potential_name) >= 2:
                                name = potential_name
                                return name
        
        except Exception as e:
            logger.debug(f"名前抽出エラー: {e}")
        
        return name
    
    def extract_party_from_context(self, link):
        """リンク周辺から政党を抽出"""
        party = ""
        
        try:
            # 政党リスト
            parties = [
                "自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
                "国民民主党", "れいわ新選組", "参政党", "社会民主党", "NHK党",
                "日本保守党", "日本改革党", "無所属", "無所属連合", "日本誠真会",
                "日本の家庭を守る会", "再生の道", "差別撲滅党", "核融合党", "チームみらい",
                "多夫多妻党", "国政ガバナンスの会"
            ]
            
            # 親要素から検索
            parent = link.parent
            search_depth = 0
            while parent and search_depth < 5:
                parent_text = parent.get_text()
                
                for p in parties:
                    if p in parent_text:
                        party = p
                        return party
                
                parent = parent.parent
                search_depth += 1
            
            # デフォルト値
            party = "未分類"
        
        except Exception as e:
            logger.debug(f"政党抽出エラー: {e}")
            party = "未分類"
        
        return party

def fix_missing_candidates():
    """不足候補者の修正"""
    logger.info("🔧 不足候補者の修正開始...")
    
    # 問題のある都道府県をチェック
    problem_prefectures = [
        (24, "三重県"),  # 実際4名 → 現在1名
        (26, "京都府"),  # 実際9名 → 現在6名
    ]
    
    fixer = MissingCandidatesFixer()
    
    # 現在のデータ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    current_candidates = data.get('data', [])
    logger.info(f"📊 現在のデータ: {len(current_candidates)}名")
    
    # 各都道府県の修正
    new_candidates = []
    
    for pref_code, pref_name in problem_prefectures:
        logger.info(f"\n=== {pref_name} 修正処理 ===")
        
        # 現在のデータを除去
        existing_candidates = [c for c in current_candidates if c['prefecture'] != pref_name]
        logger.info(f"🗑️ {pref_name} 既存データ削除")
        
        # 新データ取得
        fresh_candidates = fixer.get_all_candidates_for_prefecture(pref_code, pref_name)
        if fresh_candidates:
            new_candidates.extend(fresh_candidates)
            logger.info(f"✅ {pref_name} 新データ追加: {len(fresh_candidates)}名")
        
        # 進行状況の休憩
        import time
        time.sleep(2)
    
    # 他の都道府県データと統合
    other_prefectures = [c for c in current_candidates 
                        if c['prefecture'] not in ['三重県', '京都府']]
    
    final_candidates = other_prefectures + new_candidates
    logger.info(f"📊 最終統合データ: {len(final_candidates)}名")
    
    # データ更新
    data['data'] = final_candidates
    data['metadata']['total_candidates'] = len(final_candidates)
    data['metadata']['generated_at'] = datetime.now().isoformat()
    data['metadata']['data_type'] = "go2senkyo_missing_fixed_sangiin_2025"
    
    # 統計再計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in final_candidates:
        party = candidate.get('party', '無所属')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    data['statistics'] = {
        "by_party": party_stats,
        "by_prefecture": prefecture_stats,
        "by_constituency_type": {"single_member": len(final_candidates)}
    }
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    fixed_file = data_dir / f"go2senkyo_missing_fixed_{timestamp}.json"
    
    with open(fixed_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {fixed_file}")
    
    # 最終統計
    logger.info("\n📊 修正後統計:")
    logger.info(f"  総候補者: {len(final_candidates)}名")
    logger.info(f"  三重県: {prefecture_stats.get('三重県', 0)}名")
    logger.info(f"  京都府: {prefecture_stats.get('京都府', 0)}名")

if __name__ == "__main__":
    fix_missing_candidates()