#!/usr/bin/env python3
"""
代替データソースからの候補者収集
- 選挙管理委員会データ
- Yahoo!選挙
- Google選挙情報
- 政治関連サイト
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

class AlternativeSourcesCollector:
    def __init__(self):
        self.session = requests.Session()
        
        # 日本のUser-Agentリスト
        self.japanese_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) Gecko/20100101 Firefox/121.0",
        ]
        
        self.setup_session()

    def setup_session(self):
        """セッション設定"""
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

    def collect_yahoo_election_data(self):
        """Yahoo!選挙から候補者データ収集"""
        logger.info("🔍 Yahoo!選挙データ収集開始...")
        
        # Yahoo!選挙の参議院選2025ページ
        base_urls = [
            "https://seiji.yahoo.co.jp/election/",
            "https://seiji.yahoo.co.jp/sangiin/2025/",
            "https://seiji.yahoo.co.jp/election/sangiin/2025/",
        ]
        
        all_candidates = []
        
        for url in base_urls:
            try:
                logger.info(f"📊 Yahoo!選挙アクセス: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ Yahoo!データ取得成功: {len(response.text):,} 文字")
                    
                    # HTMLファイルとして保存（デバッグ用）
                    debug_dir = Path(__file__).parent / "debug"
                    debug_dir.mkdir(exist_ok=True)
                    
                    filename = url.replace('https://', '').replace('/', '_') + '.html'
                    with open(debug_dir / filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    candidates = self.extract_yahoo_candidates(soup, url)
                    all_candidates.extend(candidates)
                    
                    if candidates:
                        logger.info(f"📋 Yahoo!候補者発見: {len(candidates)}名")
                        break  # 成功したらループを抜ける
                else:
                    logger.warning(f"⚠️ Yahoo!アクセス失敗: HTTP {response.status_code}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ Yahoo!収集エラー ({url}): {e}")
                continue
        
        logger.info(f"🎯 Yahoo!収集完了: 総計 {len(all_candidates)}名")
        return all_candidates

    def extract_yahoo_candidates(self, soup, source_url):
        """Yahoo!選挙から候補者情報抽出"""
        candidates = []
        
        try:
            # Yahoo!選挙の典型的な構造を探索
            candidate_selectors = [
                '[class*="candidate"]',
                '[class*="koho"]',
                '[class*="person"]',
                '[class*="politician"]',
                'div[data-candidate]',
                'li[data-candidate]'
            ]
            
            for selector in candidate_selectors:
                elements = soup.select(selector)
                logger.info(f"Yahoo!セレクタ '{selector}': {len(elements)}件")
                
                for element in elements:
                    try:
                        candidate = self.extract_candidate_from_element(element, source_url, "yahoo_election")
                        if candidate:
                            candidates.append(candidate)
                    except Exception as e:
                        logger.debug(f"Yahoo!候補者抽出エラー: {e}")
                        continue
            
            # 都道府県別リンクも探索
            prefecture_links = self.find_prefecture_links(soup, source_url)
            logger.info(f"Yahoo!都道府県リンク: {len(prefecture_links)}件")
            
            # 各都道府県ページを収集（サンプリング）
            for pref_name, pref_url in prefecture_links[:5]:  # 最初の5県のみ
                try:
                    pref_candidates = self.collect_prefecture_page(pref_name, pref_url, "yahoo")
                    candidates.extend(pref_candidates)
                    time.sleep(2)
                except Exception as e:
                    logger.debug(f"Yahoo!都道府県収集エラー ({pref_name}): {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Yahoo!候補者抽出エラー: {e}")
        
        return candidates

    def collect_google_election_data(self):
        """Google選挙情報から候補者データ収集"""
        logger.info("🔍 Google選挙情報データ収集開始...")
        
        # Google選挙情報のURL
        base_urls = [
            "https://g.co/elections",
            "https://www.google.com/search?q=参議院選挙+2025+候補者",
            "https://www.google.co.jp/search?q=参議院選挙+2025+候補者一覧",
        ]
        
        all_candidates = []
        
        for url in base_urls:
            try:
                logger.info(f"📊 Google選挙情報アクセス: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ Googleデータ取得成功: {len(response.text):,} 文字")
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    candidates = self.extract_google_candidates(soup, url)
                    all_candidates.extend(candidates)
                    
                    if candidates:
                        logger.info(f"📋 Google候補者発見: {len(candidates)}名")
                
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ Google収集エラー ({url}): {e}")
                continue
        
        logger.info(f"🎯 Google収集完了: 総計 {len(all_candidates)}名")
        return all_candidates

    def extract_google_candidates(self, soup, source_url):
        """Google選挙情報から候補者情報抽出"""
        candidates = []
        
        try:
            # Google検索結果の構造を探索
            result_selectors = [
                '[data-ved]',
                '.g',
                '.yuRUbf',
                '[class*="result"]'
            ]
            
            for selector in result_selectors:
                elements = soup.select(selector)
                logger.info(f"Googleセレクタ '{selector}': {len(elements)}件")
                
                for element in elements:
                    try:
                        # Google検索結果から候補者関連情報を抽出
                        text = element.get_text()
                        if any(keyword in text for keyword in ['候補者', '参議院', '選挙', '立候補']):
                            candidate_info = self.parse_google_result_text(text, source_url)
                            if candidate_info:
                                candidates.extend(candidate_info)
                    except Exception as e:
                        logger.debug(f"Google結果解析エラー: {e}")
                        continue
            
        except Exception as e:
            logger.error(f"Google候補者抽出エラー: {e}")
        
        return candidates

    def parse_google_result_text(self, text, source_url):
        """Google検索結果テキストから候補者情報を抽出"""
        candidates = []
        
        try:
            # 候補者名らしきパターンを探す
            # 例: "田中太郎（たなかたろう）自由民主党"
            name_patterns = [
                r'([一-龯ひらがな\s]+)（([ァ-ヶー\s]+)）([一-龯ひらがな]+党|無所属)',
                r'([一-龯ひらがな\s]+)\s+([一-龯ひらがな]+党|無所属)',
                r'([一-龯ひらがな]{2,6})\s*([一-龯ひらがな]+党)'
            ]
            
            for pattern in name_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    candidate = {
                        "candidate_id": f"google_{hash(match.group(1)) % 1000000}",
                        "name": match.group(1).strip(),
                        "name_kana": match.group(2).strip() if len(match.groups()) > 2 else "",
                        "party": match.groups()[-1].strip(),
                        "party_normalized": match.groups()[-1].strip(),
                        "prefecture": "",  # Google検索結果では特定困難
                        "constituency": "",
                        "constituency_type": "single_member",
                        "source_page": source_url,
                        "source": "google_search",
                        "collected_at": datetime.now().isoformat()
                    }
                    
                    if len(candidate["name"]) > 1:  # 最低限の検証
                        candidates.append(candidate)
            
        except Exception as e:
            logger.debug(f"Googleテキスト解析エラー: {e}")
        
        return candidates

    def find_prefecture_links(self, soup, base_url):
        """都道府県別ページのリンクを探索"""
        links = []
        
        try:
            # 都道府県名を含むリンクを探す
            all_links = soup.find_all('a', href=True)
            
            prefecture_names = [
                '北海道', '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
                '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
                '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県', '岐阜県',
                '静岡県', '愛知県', '三重県', '滋賀県', '京都府', '大阪府', '兵庫県',
                '奈良県', '和歌山県', '鳥取県', '島根県', '岡山県', '広島県', '山口県',
                '徳島県', '香川県', '愛媛県', '高知県', '福岡県', '佐賀県', '長崎県',
                '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
            ]
            
            for link in all_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                for pref_name in prefecture_names:
                    if pref_name in text:
                        full_url = self.resolve_url(href, base_url)
                        links.append((pref_name, full_url))
                        break
            
            # 重複除去
            unique_links = list(dict(links).items())
            return unique_links
            
        except Exception as e:
            logger.error(f"都道府県リンク探索エラー: {e}")
            return []

    def collect_prefecture_page(self, pref_name, pref_url, source_type):
        """都道府県別ページから候補者収集"""
        candidates = []
        
        try:
            logger.info(f"📍 {pref_name} {source_type}ページ収集...")
            response = self.session.get(pref_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 各ソース別の抽出ロジック
                if source_type == "yahoo":
                    candidates = self.extract_yahoo_candidates(soup, pref_url)
                elif source_type == "google":
                    candidates = self.extract_google_candidates(soup, pref_url)
                
                # 都道府県情報を追加
                for candidate in candidates:
                    candidate["prefecture"] = pref_name
                    candidate["constituency"] = pref_name.replace('県', '').replace('府', '').replace('都', '').replace('道', '')
                
                logger.info(f"✅ {pref_name} {source_type}収集完了: {len(candidates)}名")
            
        except Exception as e:
            logger.error(f"❌ {pref_name} {source_type}収集エラー: {e}")
        
        return candidates

    def extract_candidate_from_element(self, element, source_url, source_type):
        """HTML要素から候補者情報を抽出"""
        try:
            candidate = {
                "candidate_id": "",
                "name": "",
                "name_kana": "",
                "prefecture": "",
                "constituency": "",
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "age": "",
                "profile_url": "",
                "source_page": source_url,
                "source": source_type,
                "collected_at": datetime.now().isoformat()
            }
            
            # 名前の抽出
            name_selectors = [
                '.name', '.candidate-name', '.person-name',
                'h3', 'h4', '[class*="name"]'
            ]
            
            for selector in name_selectors:
                name_elem = element.select_one(selector)
                if name_elem:
                    candidate["name"] = name_elem.get_text(strip=True)
                    break
            
            # 読みの抽出
            kana_selectors = [
                '.kana', '.reading', '.furigana',
                '[class*="kana"]', '[class*="reading"]'
            ]
            
            for selector in kana_selectors:
                kana_elem = element.select_one(selector)
                if kana_elem:
                    candidate["name_kana"] = kana_elem.get_text(strip=True)
                    break
            
            # 政党の抽出
            party_selectors = [
                '.party', '.political-party', '.affiliation',
                '[class*="party"]', '[class*="affiliation"]'
            ]
            
            for selector in party_selectors:
                party_elem = element.select_one(selector)
                if party_elem:
                    candidate["party"] = party_elem.get_text(strip=True)
                    candidate["party_normalized"] = candidate["party"]
                    break
            
            # プロフィールURLの抽出
            profile_link = element.find('a', href=True)
            if profile_link:
                candidate["profile_url"] = self.resolve_url(profile_link.get('href'), source_url)
            
            # 候補者IDの生成
            if candidate["name"]:
                candidate["candidate_id"] = f"{source_type}_{hash(candidate['name']) % 1000000}"
                return candidate
            
        except Exception as e:
            logger.debug(f"候補者要素抽出エラー: {e}")
        
        return None

    def resolve_url(self, href, base_url):
        """相対URLを絶対URLに変換"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            base_domain = '/'.join(base_url.split('/')[:3])
            return base_domain + href
        else:
            return base_url.rstrip('/') + '/' + href

    def collect_all_alternative_sources(self):
        """すべての代替ソースから候補者収集"""
        logger.info("🚀 代替ソース候補者収集開始...")
        
        all_candidates = []
        
        # Yahoo!選挙データ収集
        try:
            yahoo_candidates = self.collect_yahoo_election_data()
            all_candidates.extend(yahoo_candidates)
        except Exception as e:
            logger.error(f"❌ Yahoo!収集エラー: {e}")
        
        # Google選挙情報収集
        try:
            google_candidates = self.collect_google_election_data()
            all_candidates.extend(google_candidates)
        except Exception as e:
            logger.error(f"❌ Google収集エラー: {e}")
        
        # 重複除去
        unique_candidates = self.deduplicate_candidates(all_candidates)
        
        logger.info(f"🎯 代替ソース収集完了: 総計 {len(unique_candidates)}名")
        return unique_candidates

    def deduplicate_candidates(self, candidates):
        """候補者重複除去"""
        seen = set()
        unique_candidates = []
        
        for candidate in candidates:
            # 名前+政党で重複判定
            key = f"{candidate['name']}_{candidate['party']}"
            if key not in seen and len(candidate['name']) > 1:
                seen.add(key)
                unique_candidates.append(candidate)
        
        logger.info(f"重複除去: {len(candidates)}名 → {len(unique_candidates)}名")
        return unique_candidates

def main():
    """メイン処理"""
    logger.info("🚀 代替ソース候補者収集開始...")
    
    collector = AlternativeSourcesCollector()
    candidates = collector.collect_all_alternative_sources()
    
    # 結果保存
    save_alternative_results(candidates)

def save_alternative_results(candidates):
    """代替ソース収集結果の保存"""
    logger.info("💾 代替ソース収集結果の保存...")
    
    # 統計計算
    party_stats = {}
    source_stats = {}
    
    for candidate in candidates:
        party = candidate.get('party', '未分類')
        source = candidate.get('source', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        source_stats[source] = source_stats.get(source, 0) + 1
    
    # データ構造
    data = {
        "metadata": {
            "data_type": "alternative_sources_sangiin_2025",
            "collection_method": "yahoo_google_alternative_sources",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "sources": ["Yahoo!選挙", "Google選挙情報"],
            "coverage": {
                "parties": len(party_stats),
                "sources": len(source_stats)
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_source": source_stats,
            "by_constituency_type": {"single_member": len(candidates)}
        },
        "data": candidates
    }
    
    # ファイル保存
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    alt_file = data_dir / f"alternative_sources_{timestamp}.json"
    
    with open(alt_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 代替ソース結果保存: {alt_file}")
    
    # 統計表示
    logger.info("\n📊 代替ソース収集統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  ソース数: {len(source_stats)}ソース")
    
    for source, count in source_stats.items():
        logger.info(f"  {source}: {count}名")

if __name__ == "__main__":
    main()