#!/usr/bin/env python3
"""
全都道府県の包括的データ収集修正
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

class ComprehensiveDataFixer:
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
        
        # 都道府県マッピング
        self.prefectures = {
            1: "北海道", 2: "青森県", 3: "岩手県", 4: "宮城県", 5: "秋田県", 6: "山形県", 7: "福島県",
            8: "茨城県", 9: "栃木県", 10: "群馬県", 11: "埼玉県", 12: "千葉県", 13: "東京都", 14: "神奈川県",
            15: "新潟県", 16: "富山県", 17: "石川県", 18: "福井県", 19: "山梨県", 20: "長野県", 21: "岐阜県",
            22: "静岡県", 23: "愛知県", 24: "三重県", 25: "滋賀県", 26: "京都府", 27: "大阪府", 28: "兵庫県",
            29: "奈良県", 30: "和歌山県", 31: "鳥取県", 32: "島根県", 33: "岡山県", 34: "広島県", 35: "山口県",
            36: "徳島県", 37: "香川県", 38: "愛媛県", 39: "高知県", 40: "福岡県", 41: "佐賀県", 42: "長崎県",
            43: "熊本県", 44: "大分県", 45: "宮崎県", 46: "鹿児島県", 47: "沖縄県"
        }
        
        # 政党マスターリスト
        self.parties = [
            "自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
            "国民民主党", "れいわ新選組", "参政党", "社会民主党", "NHK党",
            "日本保守党", "日本改革党", "無所属", "無所属連合", "日本誠真会",
            "日本の家庭を守る会", "再生の道", "差別撲滅党", "核融合党", "チームみらい",
            "多夫多妻党", "国政ガバナンスの会", "新党やまと", "未分類"
        ]
    
    def get_prefecture_candidates_enhanced(self, pref_code: int):
        """強化された都道府県候補者取得"""
        pref_name = self.prefectures.get(pref_code, f"未知_{pref_code}")
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        
        logger.info(f"🔍 {pref_name} (コード: {pref_code}) データ収集開始")
        
        try:
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.debug(f"📊 {pref_name} HTML取得: {len(response.text):,} 文字")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 複数の抽出方法を試行
            candidates = []
            
            # 方法1: 候補者ブロック直接検索
            candidates.extend(self.extract_from_candidate_blocks(soup, pref_name, url))
            
            # 方法2: プロフィールリンクから抽出
            if not candidates:
                candidates.extend(self.extract_from_profile_links(soup, pref_name, url))
            
            # 方法3: テキストパターンマッチング
            if not candidates:
                candidates.extend(self.extract_from_text_patterns(soup, pref_name, url))
            
            # 重複除去
            unique_candidates = self.deduplicate_candidates(candidates)
            
            logger.info(f"✅ {pref_name} 取得完了: {len(unique_candidates)}名")
            
            return unique_candidates
            
        except Exception as e:
            logger.error(f"❌ {pref_name} データ収集エラー: {e}")
            return []
    
    def extract_from_candidate_blocks(self, soup: BeautifulSoup, prefecture: str, page_url: str):
        """候補者ブロックから抽出"""
        candidates = []
        
        try:
            # 複数のブロックセレクタを試行
            block_selectors = [
                'div.p_senkyoku_list_block',
                'div[class*="candidate"]',
                'div[class*="list_block"]',
                'div[class*="person"]'
            ]
            
            for selector in block_selectors:
                blocks = soup.select(selector)
                if blocks:
                    logger.debug(f"{prefecture}: {selector}で{len(blocks)}個のブロック発見")
                    
                    for i, block in enumerate(blocks):
                        candidate = self.extract_candidate_from_block(block, prefecture, page_url, i)
                        if candidate:
                            candidates.append(candidate)
                    break
            
        except Exception as e:
            logger.debug(f"{prefecture} ブロック抽出エラー: {e}")
        
        return candidates
    
    def extract_from_profile_links(self, soup: BeautifulSoup, prefecture: str, page_url: str):
        """プロフィールリンクから抽出"""
        candidates = []
        
        try:
            # プロフィールリンク検索
            profile_links = soup.find_all('a', href=re.compile(r'/seijika/\d+'))
            logger.debug(f"{prefecture}: {len(profile_links)}個のプロフィールリンク発見")
            
            seen_ids = set()
            
            for i, link in enumerate(profile_links):
                try:
                    href = link.get('href', '')
                    match = re.search(r'/seijika/(\d+)', href)
                    if match:
                        candidate_id = match.group(1)
                        if candidate_id not in seen_ids:
                            seen_ids.add(candidate_id)
                            candidate = self.extract_candidate_from_link(link, prefecture, page_url, candidate_id)
                            if candidate:
                                candidates.append(candidate)
                except Exception as e:
                    logger.debug(f"リンク {i} 処理エラー: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"{prefecture} リンク抽出エラー: {e}")
        
        return candidates
    
    def extract_from_text_patterns(self, soup: BeautifulSoup, prefecture: str, page_url: str):
        """テキストパターンから抽出"""
        candidates = []
        
        try:
            # ページ全体のテキストから候補者名パターンを検索
            page_text = soup.get_text()
            
            # 日本人名パターン
            name_patterns = re.findall(r'([一-龯]{1,2}[\s　]*[一-龯ひらがな]{1,6})', page_text)
            
            for name in name_patterns:
                if len(name.strip()) >= 2:
                    candidate = {
                        "candidate_id": f"text_pattern_{len(candidates)}",
                        "name": name.strip(),
                        "prefecture": prefecture,
                        "constituency": prefecture.replace('県', '').replace('府', '').replace('都', ''),
                        "constituency_type": "single_member",
                        "party": "未分類",
                        "party_normalized": "未分類",
                        "profile_url": "",
                        "source_page": page_url,
                        "source": "text_pattern_extraction",
                        "collected_at": datetime.now().isoformat()
                    }
                    candidates.append(candidate)
            
        except Exception as e:
            logger.debug(f"{prefecture} テキストパターン抽出エラー: {e}")
        
        return candidates
    
    def extract_candidate_from_block(self, block, prefecture: str, page_url: str, index: int):
        """ブロックから候補者情報抽出"""
        try:
            candidate = {
                "candidate_id": f"block_{index}",
                "name": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "profile_url": "",
                "source_page": page_url,
                "source": "block_extraction",
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前抽出
            name = self.extract_name_from_element(block)
            if name:
                candidate["name"] = name
            
            # 政党抽出
            party = self.extract_party_from_element(block)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            # プロフィールURL抽出
            profile_link = block.find('a', href=re.compile(r'/seijika/\d+'))
            if profile_link:
                href = profile_link.get('href')
                if href:
                    candidate["profile_url"] = f"https://go2senkyo.com{href}"
                    match = re.search(r'/seijika/(\d+)', href)
                    if match:
                        candidate["candidate_id"] = f"go2s_{match.group(1)}"
            
            return candidate if candidate["name"] else None
            
        except Exception as e:
            logger.debug(f"ブロック抽出エラー: {e}")
            return None
    
    def extract_candidate_from_link(self, link, prefecture: str, page_url: str, candidate_id: str):
        """リンクから候補者情報抽出"""
        try:
            candidate = {
                "candidate_id": f"go2s_{candidate_id}",
                "name": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "profile_url": f"https://go2senkyo.com{link.get('href')}",
                "source_page": page_url,
                "source": "link_extraction",
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前抽出
            name = self.extract_name_from_element(link.parent if link.parent else link)
            if name:
                candidate["name"] = name
            
            # 政党抽出
            party = self.extract_party_from_element(link.parent if link.parent else link)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            return candidate if candidate["name"] else None
            
        except Exception as e:
            logger.debug(f"リンク抽出エラー: {e}")
            return None
    
    def extract_name_from_element(self, element):
        """要素から名前抽出"""
        try:
            text = element.get_text() if element else ""
            
            # 日本人名パターンマッチ
            name_patterns = [
                r'([一-龯]{1,2}[\s　]*[一-龯ひらがな]{1,6})',
                r'([一-龯ひらがな]{2,8})',
            ]
            
            for pattern in name_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    name = match.strip().replace('\u3000', ' ')
                    # 除外ワード
                    if name not in ['詳細', 'プロフィール', '選挙', '候補', '政党', '無所属'] and len(name) >= 2:
                        return name
            
        except Exception as e:
            logger.debug(f"名前抽出エラー: {e}")
        
        return ""
    
    def extract_party_from_element(self, element):
        """要素から政党抽出"""
        try:
            text = element.get_text() if element else ""
            
            for party in self.parties:
                if party in text:
                    return party
            
        except Exception as e:
            logger.debug(f"政党抽出エラー: {e}")
        
        return "未分類"
    
    def deduplicate_candidates(self, candidates):
        """候補者重複除去"""
        seen = set()
        unique = []
        
        for candidate in candidates:
            key = (candidate["name"], candidate["prefecture"])
            if key not in seen and candidate["name"]:
                seen.add(key)
                unique.append(candidate)
        
        return unique

def comprehensive_fix():
    """全都道府県の包括的修正"""
    logger.info("🔧 全都道府県データの包括的修正開始...")
    
    fixer = ComprehensiveDataFixer()
    all_candidates = []
    
    # 全都道府県を処理
    for pref_code in range(1, 48):  # 1-47
        try:
            pref_name = fixer.prefectures[pref_code]
            logger.info(f"\n=== {pref_code}/47: {pref_name} ===")
            
            candidates = fixer.get_prefecture_candidates_enhanced(pref_code)
            all_candidates.extend(candidates)
            
            logger.info(f"📊 進捗: {pref_code}/47 完了 - 総候補者: {len(all_candidates)}名")
            
            # レート制限
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ {pref_code} 処理エラー: {e}")
            continue
    
    logger.info(f"\n🎯 全収集完了: {len(all_candidates)}名")
    
    # データ整理・保存
    save_comprehensive_data(all_candidates)

def save_comprehensive_data(candidates):
    """包括的データの保存"""
    logger.info("💾 包括的データの保存開始...")
    
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
            "data_type": "go2senkyo_comprehensive_fixed_sangiin_2025",
            "collection_method": "comprehensive_enhanced_extraction",
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
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    comprehensive_file = data_dir / f"go2senkyo_comprehensive_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(comprehensive_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {comprehensive_file}")
    
    # 統計表示
    logger.info("\n📊 最終統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    logger.info("\n🏛️ 都道府県別統計（上位15）:")
    top_prefectures = sorted(prefecture_stats.items(), key=lambda x: x[1], reverse=True)[:15]
    for pref, count in top_prefectures:
        logger.info(f"  {pref}: {count}名")

if __name__ == "__main__":
    comprehensive_fix()