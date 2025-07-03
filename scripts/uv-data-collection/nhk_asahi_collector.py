#!/usr/bin/env python3
"""
NHK・朝日新聞選挙データベースからの候補者収集
IP偽装機能付き
"""

import json
import logging
import requests
import time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class NHKAsahiCollector:
    def __init__(self):
        self.session = requests.Session()
        
        # 日本のプロキシIPリスト（例）- 実際は有効なプロキシサービスを使用
        self.japanese_proxies = [
            # 実際のプロキシサービスのIPを設定
            # {"http": "http://proxy1:port", "https": "https://proxy1:port"},
            # {"http": "http://proxy2:port", "https": "https://proxy2:port"},
        ]
        
        # 日本のUser-Agentリスト
        self.japanese_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        
        self.setup_session()
        
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

    def setup_session(self):
        """セッション設定とIP偽装"""
        # ランダムなUser-Agent設定
        user_agent = random.choice(self.japanese_user_agents)
        
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'ja,ja-JP;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.co.jp/',
        })
        
        # プロキシ設定（利用可能な場合）
        if self.japanese_proxies:
            proxy = random.choice(self.japanese_proxies)
            self.session.proxies.update(proxy)
            logger.info(f"プロキシ設定: {proxy}")

    def collect_nhk_candidates(self):
        """NHK選挙データベースから候補者収集"""
        logger.info("🔍 NHK選挙データベース収集開始...")
        
        base_url = "https://www.nhk.or.jp/senkyo/database/sangiin/2025/expected-candidates/"
        all_candidates = []
        
        try:
            # メインページへアクセス
            logger.info("📊 NHKメインページアクセス中...")
            response = self.session.get(base_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ NHKメインページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.info(f"✅ NHKメインページ取得成功: {len(response.text):,} 文字")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 都道府県リンクを探索
            prefecture_links = self.extract_nhk_prefecture_links(soup)
            logger.info(f"📋 NHK都道府県リンク発見: {len(prefecture_links)}件")
            
            # 各都道府県の候補者を収集
            for i, (pref_name, pref_url) in enumerate(prefecture_links):
                logger.info(f"\n=== [{i+1}/{len(prefecture_links)}] {pref_name} NHK収集 ===")
                
                try:
                    pref_candidates = self.collect_nhk_prefecture(pref_name, pref_url)
                    all_candidates.extend(pref_candidates)
                    logger.info(f"✅ {pref_name} NHK収集完了: {len(pref_candidates)}名")
                    
                    # レート制限
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"❌ {pref_name} NHK収集エラー: {e}")
                    continue
            
            logger.info(f"🎯 NHK収集完了: 総計 {len(all_candidates)}名")
            return all_candidates
            
        except Exception as e:
            logger.error(f"❌ NHK収集エラー: {e}")
            return []

    def extract_nhk_prefecture_links(self, soup):
        """NHKページから都道府県リンクを抽出"""
        links = []
        
        try:
            # NHKの典型的な構造を探索
            # 都道府県選択エリアやリンクリストを探す
            prefecture_elements = soup.find_all(['a', 'li', 'div'], text=re.compile(r'[都道府県]'))
            
            for element in prefecture_elements:
                if element.name == 'a' and element.get('href'):
                    href = element.get('href')
                    text = element.get_text(strip=True)
                    
                    # 都道府県名の抽出
                    pref_match = re.search(r'([一-龯ひらがな]+[都道府県])', text)
                    if pref_match:
                        pref_name = pref_match.group(1)
                        full_url = self.resolve_url(href, "https://www.nhk.or.jp")
                        links.append((pref_name, full_url))
            
            # 重複除去
            unique_links = list(dict(links).items())
            return unique_links
            
        except Exception as e:
            logger.error(f"NHK都道府県リンク抽出エラー: {e}")
            return []

    def collect_nhk_prefecture(self, pref_name, pref_url):
        """NHK都道府県ページから候補者収集"""
        candidates = []
        
        try:
            response = self.session.get(pref_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} NHKページアクセス失敗: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 候補者情報の抽出
            candidate_elements = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'candidate|koho|person'))
            
            for element in candidate_elements:
                try:
                    candidate = self.extract_nhk_candidate_info(element, pref_name, pref_url)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.debug(f"候補者抽出エラー: {e}")
                    continue
            
            return candidates
            
        except Exception as e:
            logger.error(f"{pref_name} NHK収集エラー: {e}")
            return []

    def extract_nhk_candidate_info(self, element, pref_name, source_url):
        """NHK候補者要素から情報抽出"""
        try:
            candidate = {
                "candidate_id": "",
                "name": "",
                "name_kana": "",
                "prefecture": pref_name,
                "constituency": pref_name.replace('県', '').replace('府', '').replace('都', '').replace('道', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "age": "",
                "profile_url": "",
                "source_page": source_url,
                "source": "nhk_database",
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前の抽出
            name_elem = element.find(['h3', 'h4', 'span', 'div'], class_=re.compile(r'name|名前'))
            if name_elem:
                candidate["name"] = name_elem.get_text(strip=True)
            
            # 読みの抽出
            kana_elem = element.find(['span', 'div'], class_=re.compile(r'kana|読み|ふりがな'))
            if kana_elem:
                candidate["name_kana"] = kana_elem.get_text(strip=True)
            
            # 政党の抽出
            party_elem = element.find(['span', 'div'], class_=re.compile(r'party|政党|所属'))
            if party_elem:
                candidate["party"] = party_elem.get_text(strip=True)
                candidate["party_normalized"] = candidate["party"]
            
            # 年齢の抽出
            age_elem = element.find(['span', 'div'], text=re.compile(r'\d+歳'))
            if age_elem:
                age_match = re.search(r'(\d+)歳', age_elem.get_text())
                if age_match:
                    candidate["age"] = age_match.group(1)
            
            # 候補者IDの生成
            if candidate["name"]:
                candidate["candidate_id"] = f"nhk_{hash(candidate['name'] + pref_name) % 1000000}"
                return candidate
            
        except Exception as e:
            logger.debug(f"NHK候補者情報抽出エラー: {e}")
        
        return None

    def collect_asahi_candidates(self):
        """朝日新聞選挙データベースから候補者収集"""
        logger.info("🔍 朝日新聞選挙データベース収集開始...")
        
        base_url = "https://www.asahi.com/senkyo/saninsen/koho/"
        all_candidates = []
        
        try:
            # メインページへアクセス
            logger.info("📊 朝日新聞メインページアクセス中...")
            response = self.session.get(base_url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ 朝日新聞メインページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.info(f"✅ 朝日新聞メインページ取得成功: {len(response.text):,} 文字")
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 都道府県リンクを探索
            prefecture_links = self.extract_asahi_prefecture_links(soup)
            logger.info(f"📋 朝日新聞都道府県リンク発見: {len(prefecture_links)}件")
            
            # 各都道府県の候補者を収集
            for i, (pref_name, pref_url) in enumerate(prefecture_links):
                logger.info(f"\n=== [{i+1}/{len(prefecture_links)}] {pref_name} 朝日新聞収集 ===")
                
                try:
                    pref_candidates = self.collect_asahi_prefecture(pref_name, pref_url)
                    all_candidates.extend(pref_candidates)
                    logger.info(f"✅ {pref_name} 朝日新聞収集完了: {len(pref_candidates)}名")
                    
                    # レート制限
                    time.sleep(random.uniform(2, 4))
                    
                except Exception as e:
                    logger.error(f"❌ {pref_name} 朝日新聞収集エラー: {e}")
                    continue
            
            logger.info(f"🎯 朝日新聞収集完了: 総計 {len(all_candidates)}名")
            return all_candidates
            
        except Exception as e:
            logger.error(f"❌ 朝日新聞収集エラー: {e}")
            return []

    def extract_asahi_prefecture_links(self, soup):
        """朝日新聞ページから都道府県リンクを抽出"""
        links = []
        
        try:
            # 朝日新聞の典型的な構造を探索
            prefecture_elements = soup.find_all(['a', 'li', 'div'], text=re.compile(r'[都道府県]'))
            
            for element in prefecture_elements:
                if element.name == 'a' and element.get('href'):
                    href = element.get('href')
                    text = element.get_text(strip=True)
                    
                    pref_match = re.search(r'([一-龯ひらがな]+[都道府県])', text)
                    if pref_match:
                        pref_name = pref_match.group(1)
                        full_url = self.resolve_url(href, "https://www.asahi.com")
                        links.append((pref_name, full_url))
            
            unique_links = list(dict(links).items())
            return unique_links
            
        except Exception as e:
            logger.error(f"朝日新聞都道府県リンク抽出エラー: {e}")
            return []

    def collect_asahi_prefecture(self, pref_name, pref_url):
        """朝日新聞都道府県ページから候補者収集"""
        candidates = []
        
        try:
            response = self.session.get(pref_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} 朝日新聞ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 候補者情報の抽出
            candidate_elements = soup.find_all(['div', 'li', 'tr'], class_=re.compile(r'candidate|koho|person'))
            
            for element in candidate_elements:
                try:
                    candidate = self.extract_asahi_candidate_info(element, pref_name, pref_url)
                    if candidate:
                        candidates.append(candidate)
                except Exception as e:
                    logger.debug(f"候補者抽出エラー: {e}")
                    continue
            
            return candidates
            
        except Exception as e:
            logger.error(f"{pref_name} 朝日新聞収集エラー: {e}")
            return []

    def extract_asahi_candidate_info(self, element, pref_name, source_url):
        """朝日新聞候補者要素から情報抽出"""
        try:
            candidate = {
                "candidate_id": "",
                "name": "",
                "name_kana": "",
                "prefecture": pref_name,
                "constituency": pref_name.replace('県', '').replace('府', '').replace('都', '').replace('道', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "age": "",
                "profile_url": "",
                "source_page": source_url,
                "source": "asahi_database",
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前の抽出
            name_elem = element.find(['h3', 'h4', 'span', 'div'], class_=re.compile(r'name|名前'))
            if name_elem:
                candidate["name"] = name_elem.get_text(strip=True)
            
            # 読みの抽出  
            kana_elem = element.find(['span', 'div'], class_=re.compile(r'kana|読み|ふりがな'))
            if kana_elem:
                candidate["name_kana"] = kana_elem.get_text(strip=True)
            
            # 政党の抽出
            party_elem = element.find(['span', 'div'], class_=re.compile(r'party|政党|所属'))
            if party_elem:
                candidate["party"] = party_elem.get_text(strip=True)
                candidate["party_normalized"] = candidate["party"]
            
            # 年齢の抽出
            age_elem = element.find(['span', 'div'], text=re.compile(r'\d+歳'))
            if age_elem:
                age_match = re.search(r'(\d+)歳', age_elem.get_text())
                if age_match:
                    candidate["age"] = age_match.group(1)
            
            # 候補者IDの生成
            if candidate["name"]:
                candidate["candidate_id"] = f"asahi_{hash(candidate['name'] + pref_name) % 1000000}"
                return candidate
            
        except Exception as e:
            logger.debug(f"朝日新聞候補者情報抽出エラー: {e}")
        
        return None

    def resolve_url(self, href, base_url):
        """相対URLを絶対URLに変換"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            return base_url + href
        else:
            return base_url + '/' + href

    def merge_and_deduplicate(self, nhk_candidates, asahi_candidates):
        """NHKと朝日新聞のデータを統合・重複除去"""
        logger.info("🔧 データ統合・重複除去開始...")
        
        all_candidates = nhk_candidates + asahi_candidates
        logger.info(f"📊 統合前総数: {len(all_candidates)}名")
        
        # 重複除去（名前+都道府県で判定）
        seen = set()
        unique_candidates = []
        
        for candidate in all_candidates:
            key = f"{candidate['name']}_{candidate['prefecture']}"
            if key not in seen:
                seen.add(key)
                unique_candidates.append(candidate)
        
        logger.info(f"📊 重複除去後: {len(unique_candidates)}名")
        return unique_candidates

def main():
    """メイン処理"""
    logger.info("🚀 NHK・朝日新聞選挙データ収集開始...")
    
    collector = NHKAsahiCollector()
    
    # NHKデータ収集
    nhk_candidates = collector.collect_nhk_candidates()
    
    # 朝日新聞データ収集
    asahi_candidates = collector.collect_asahi_candidates()
    
    # データ統合
    all_candidates = collector.merge_and_deduplicate(nhk_candidates, asahi_candidates)
    
    # 結果保存
    save_merged_results(all_candidates, nhk_candidates, asahi_candidates)

def save_merged_results(all_candidates, nhk_candidates, asahi_candidates):
    """統合結果の保存"""
    logger.info("💾 統合結果の保存...")
    
    # 統計計算
    party_stats = {}
    prefecture_stats = {}
    source_stats = {"nhk_database": 0, "asahi_database": 0}
    
    for candidate in all_candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        source = candidate.get('source', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
        source_stats[source] = source_stats.get(source, 0) + 1
    
    # データ構造
    data = {
        "metadata": {
            "data_type": "nhk_asahi_merged_sangiin_2025",
            "collection_method": "official_databases_with_ip_masking",
            "total_candidates": len(all_candidates),
            "nhk_candidates": len(nhk_candidates),
            "asahi_candidates": len(asahi_candidates),
            "generated_at": datetime.now().isoformat(),
            "sources": ["NHK選挙データベース", "朝日新聞選挙データベース"],
            "coverage": {
                "constituency_types": 1,
                "parties": len(party_stats),
                "prefectures": len(prefecture_stats)
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_source": source_stats,
            "by_constituency_type": {"single_member": len(all_candidates)}
        },
        "data": all_candidates
    }
    
    # ファイル保存
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    merged_file = data_dir / f"nhk_asahi_merged_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(merged_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    # 統合データが成功した場合のみ最新ファイルを更新
    if len(all_candidates) > 200:  # 合理的な候補者数の閾値
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"📁 最新ファイル更新: {latest_file}")
    
    logger.info(f"📁 統合結果保存: {merged_file}")
    
    # 統計表示
    logger.info("\n📊 NHK・朝日新聞統合収集統計:")
    logger.info(f"  総候補者: {len(all_candidates)}名")
    logger.info(f"  NHKデータ: {len(nhk_candidates)}名")
    logger.info(f"  朝日新聞データ: {len(asahi_candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    # 主要県の確認
    major_prefs = ["神奈川県", "京都府", "三重県", "東京都", "大阪府"]
    logger.info(f"\n🔍 主要県確認:")
    for pref in major_prefs:
        count = prefecture_stats.get(pref, 0)
        logger.info(f"  {pref}: {count}名")

if __name__ == "__main__":
    main()