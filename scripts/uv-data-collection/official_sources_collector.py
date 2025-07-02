#!/usr/bin/env python3
"""
公式ソースからの候補者データ収集
- 総務省選挙部
- 各都道府県選挙管理委員会
- 主要政党公式サイト
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

class OfficialSourcesCollector:
    def __init__(self):
        self.session = requests.Session()
        
        # 日本のUser-Agentリスト
        self.japanese_user_agents = [
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        ]
        
        self.setup_session()
        
        # 主要政党のサイト
        self.party_sites = {
            "自由民主党": "https://www.jimin.jp/",
            "立憲民主党": "https://cdp-japan.jp/", 
            "日本維新の会": "https://o-ishin.jp/",
            "公明党": "https://www.komei.or.jp/",
            "日本共産党": "https://www.jcp.or.jp/",
            "国民民主党": "https://new-kokumin.jp/",
            "れいわ新選組": "https://reiwa-shinsengumi.com/",
            "参政党": "https://www.sanseito.jp/",
            "社会民主党": "https://sdp.or.jp/",
        }

    def setup_session(self):
        """セッション設定"""
        user_agent = random.choice(self.japanese_user_agents)
        
        self.session.headers.update({
            'User-Agent': user_agent,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,ja-JP;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
            'Referer': 'https://www.google.co.jp/',
        })

    def collect_soumu_data(self):
        """総務省選挙部からのデータ収集"""
        logger.info("🔍 総務省選挙部データ収集開始...")
        
        # 総務省選挙関連URL
        soumu_urls = [
            "https://www.soumu.go.jp/senkyo/",
            "https://www.soumu.go.jp/senkyo/sangiin2025/",
            "https://www.soumu.go.jp/senkyo/senkyo_s/",
        ]
        
        all_candidates = []
        
        for url in soumu_urls:
            try:
                logger.info(f"📊 総務省アクセス: {url}")
                response = self.session.get(url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ 総務省データ取得成功: {len(response.text):,} 文字")
                    
                    # HTMLファイルとして保存（デバッグ用）
                    debug_dir = Path(__file__).parent / "debug"
                    debug_dir.mkdir(exist_ok=True)
                    
                    filename = url.replace('https://', '').replace('/', '_') + '.html'
                    with open(debug_dir / filename, 'w', encoding='utf-8') as f:
                        f.write(response.text)
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    candidates = self.extract_soumu_candidates(soup, url)
                    all_candidates.extend(candidates)
                    
                    if candidates:
                        logger.info(f"📋 総務省候補者発見: {len(candidates)}名")
                else:
                    logger.warning(f"⚠️ 総務省アクセス失敗: HTTP {response.status_code}")
                
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ 総務省収集エラー ({url}): {e}")
                continue
        
        logger.info(f"🎯 総務省収集完了: 総計 {len(all_candidates)}名")
        return all_candidates

    def extract_soumu_candidates(self, soup, source_url):
        """総務省サイトから候補者情報抽出"""
        candidates = []
        
        try:
            # 総務省の選挙関連リンクを探索
            election_links = self.find_election_links(soup, source_url)
            logger.info(f"総務省選挙関連リンク: {len(election_links)}件")
            
            for link_text, link_url in election_links[:5]:  # 最初の5件
                try:
                    page_candidates = self.collect_page_candidates(link_text, link_url, "soumu")
                    candidates.extend(page_candidates)
                    time.sleep(2)
                except Exception as e:
                    logger.debug(f"総務省ページ収集エラー ({link_text}): {e}")
                    continue
            
        except Exception as e:
            logger.error(f"総務省候補者抽出エラー: {e}")
        
        return candidates

    def find_election_links(self, soup, base_url):
        """選挙関連リンクの探索"""
        links = []
        
        try:
            all_links = soup.find_all('a', href=True)
            
            election_keywords = [
                '参議院', '候補者', '立候補', '選挙区', '比例代表',
                '2025', '令和7年', '期日前投票', '投票日'
            ]
            
            for link in all_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # 選挙関連キーワードを含むリンクを探す
                if any(keyword in text for keyword in election_keywords):
                    full_url = self.resolve_url(href, base_url)
                    links.append((text, full_url))
            
            # 重複除去
            unique_links = list(dict(links).items())
            return unique_links
            
        except Exception as e:
            logger.error(f"選挙関連リンク探索エラー: {e}")
            return []

    def collect_party_candidates(self):
        """各政党サイトから候補者データ収集"""
        logger.info("🔍 政党サイト候補者収集開始...")
        
        all_candidates = []
        
        for party_name, party_url in self.party_sites.items():
            try:
                logger.info(f"📊 {party_name} サイトアクセス: {party_url}")
                response = self.session.get(party_url, timeout=30)
                
                if response.status_code == 200:
                    logger.info(f"✅ {party_name} データ取得成功: {len(response.text):,} 文字")
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    party_candidates = self.extract_party_candidates(soup, party_url, party_name)
                    
                    # 政党情報を追加
                    for candidate in party_candidates:
                        candidate["party"] = party_name
                        candidate["party_normalized"] = party_name
                    
                    all_candidates.extend(party_candidates)
                    
                    logger.info(f"📋 {party_name} 候補者発見: {len(party_candidates)}名")
                else:
                    logger.warning(f"⚠️ {party_name} アクセス失敗: HTTP {response.status_code}")
                
                time.sleep(3)  # 政党サイトへの配慮
                
            except Exception as e:
                logger.error(f"❌ {party_name} 収集エラー: {e}")
                continue
        
        logger.info(f"🎯 政党サイト収集完了: 総計 {len(all_candidates)}名")
        return all_candidates

    def extract_party_candidates(self, soup, source_url, party_name):
        """政党サイトから候補者情報抽出"""
        candidates = []
        
        try:
            # 候補者関連のリンクを探索
            candidate_links = self.find_candidate_links(soup, source_url)
            logger.info(f"{party_name} 候補者関連リンク: {len(candidate_links)}件")
            
            # 候補者リストページを探す
            for link_text, link_url in candidate_links[:10]:  # 最初の10件
                try:
                    if any(keyword in link_text.lower() for keyword in ['候補', 'candidate', '参議院', '議員']):
                        page_candidates = self.collect_page_candidates(link_text, link_url, f"party_{party_name}")
                        candidates.extend(page_candidates)
                        time.sleep(1)
                except Exception as e:
                    logger.debug(f"{party_name} 候補者ページ収集エラー ({link_text}): {e}")
                    continue
            
            # メインページからも候補者情報を抽出
            main_candidates = self.extract_candidates_from_page(soup, source_url, f"party_{party_name}")
            candidates.extend(main_candidates)
            
        except Exception as e:
            logger.error(f"{party_name} 候補者抽出エラー: {e}")
        
        return candidates

    def find_candidate_links(self, soup, base_url):
        """候補者関連リンクの探索"""
        links = []
        
        try:
            all_links = soup.find_all('a', href=True)
            
            candidate_keywords = [
                '候補者', '候補', 'candidate', '参議院', '議員',
                '立候補', '政策', 'profile', 'プロフィール',
                '一覧', 'list', '名簿'
            ]
            
            for link in all_links:
                href = link.get('href')
                text = link.get_text(strip=True)
                
                # 候補者関連キーワードを含むリンクを探す
                if any(keyword in text.lower() for keyword in candidate_keywords):
                    full_url = self.resolve_url(href, base_url)
                    links.append((text, full_url))
            
            # 重複除去
            unique_links = list(dict(links).items())
            return unique_links
            
        except Exception as e:
            logger.error(f"候補者関連リンク探索エラー: {e}")
            return []

    def collect_page_candidates(self, page_title, page_url, source_type):
        """個別ページから候補者収集"""
        candidates = []
        
        try:
            logger.debug(f"📍 ページ収集: {page_title} ({source_type})")
            response = self.session.get(page_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                candidates = self.extract_candidates_from_page(soup, page_url, source_type)
                
                if candidates:
                    logger.debug(f"✅ {page_title} 収集完了: {len(candidates)}名")
            
        except Exception as e:
            logger.debug(f"❌ ページ収集エラー ({page_title}): {e}")
        
        return candidates

    def extract_candidates_from_page(self, soup, source_url, source_type):
        """ページから候補者情報を抽出"""
        candidates = []
        
        try:
            # 候補者情報らしき要素を探索
            candidate_selectors = [
                '[class*="candidate"]',
                '[class*="member"]',
                '[class*="person"]',
                '[class*="profile"]',
                'li[class*="item"]',
                'div[class*="card"]'
            ]
            
            for selector in candidate_selectors:
                elements = soup.select(selector)
                
                for element in elements:
                    try:
                        candidate = self.extract_candidate_info(element, source_url, source_type)
                        if candidate:
                            candidates.append(candidate)
                    except Exception as e:
                        logger.debug(f"候補者情報抽出エラー: {e}")
                        continue
            
            # テキストベースの候補者名抽出も実行
            text_candidates = self.extract_candidates_from_text(soup.get_text(), source_url, source_type)
            candidates.extend(text_candidates)
            
        except Exception as e:
            logger.debug(f"ページ候補者抽出エラー: {e}")
        
        return candidates

    def extract_candidate_info(self, element, source_url, source_type):
        """HTML要素から候補者情報抽出"""
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
            text = element.get_text()
            
            # 日本人名らしきパターンを探す
            name_patterns = [
                r'([一-龯ひらがな]{2,6})\s*([一-龯ひらがな]{2,6})',  # 漢字・ひらがな名前
                r'([一-龯ひらがな]{2,10})',  # 単体の漢字・ひらがな名前
            ]
            
            for pattern in name_patterns:
                match = re.search(pattern, text)
                if match:
                    potential_name = match.group(1).strip()
                    
                    # 名前として適切かチェック
                    if self.is_valid_name(potential_name):
                        candidate["name"] = potential_name
                        break
            
            # プロフィールURLの抽出
            profile_link = element.find('a', href=True)
            if profile_link:
                candidate["profile_url"] = self.resolve_url(profile_link.get('href'), source_url)
            
            # 候補者IDの生成
            if candidate["name"] and len(candidate["name"]) > 1:
                candidate["candidate_id"] = f"{source_type}_{hash(candidate['name']) % 1000000}"
                return candidate
            
        except Exception as e:
            logger.debug(f"候補者情報抽出エラー: {e}")
        
        return None

    def extract_candidates_from_text(self, text, source_url, source_type):
        """テキストから候補者名を抽出"""
        candidates = []
        
        try:
            # 候補者名らしきパターンを探す
            name_patterns = [
                r'候補者?[:：]\s*([一-龯ひらがな\s、，]+)',
                r'立候補者?[:：]\s*([一-龯ひらがな\s、，]+)',
                r'([一-龯ひらがな]{2,6})\s*\(\s*([ァ-ヶー\s]+)\s*\)',  # 名前(読み)形式
                r'([一-龯ひらがな]{2,6})\s*([一-龯ひらがな]{2,6})\s*\d+歳',  # 名前 年齢形式
            ]
            
            for pattern in name_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    names_text = match.group(1)
                    
                    # 複数名前が含まれている場合は分割
                    potential_names = re.split(r'[、，\s]+', names_text)
                    
                    for name in potential_names:
                        name = name.strip()
                        if self.is_valid_name(name):
                            candidate = {
                                "candidate_id": f"{source_type}_text_{hash(name) % 1000000}",
                                "name": name,
                                "name_kana": match.group(2).strip() if len(match.groups()) > 1 else "",
                                "prefecture": "",
                                "constituency": "",
                                "constituency_type": "single_member",
                                "party": "未分類",
                                "party_normalized": "未分類",
                                "source_page": source_url,
                                "source": source_type,
                                "collected_at": datetime.now().isoformat()
                            }
                            candidates.append(candidate)
            
        except Exception as e:
            logger.debug(f"テキスト候補者抽出エラー: {e}")
        
        return candidates

    def is_valid_name(self, name):
        """名前として適切かチェック"""
        if not name or len(name) < 2 or len(name) > 10:
            return False
        
        # 除外すべきキーワード
        invalid_keywords = [
            '政策', '公約', '選挙', '投票', '議員', '党', '会', '委員', 
            '大臣', '総理', '首相', '代表', '幹事', '事務', '連絡',
            '詳細', 'について', 'こちら', 'ページ', 'サイト', 'ホーム'
        ]
        
        for keyword in invalid_keywords:
            if keyword in name:
                return False
        
        return True

    def resolve_url(self, href, base_url):
        """相対URLを絶対URLに変換"""
        if href.startswith('http'):
            return href
        elif href.startswith('/'):
            base_domain = '/'.join(base_url.split('/')[:3])
            return base_domain + href
        else:
            return base_url.rstrip('/') + '/' + href

    def collect_all_official_sources(self):
        """すべての公式ソースから候補者収集"""
        logger.info("🚀 公式ソース候補者収集開始...")
        
        all_candidates = []
        
        # 総務省データ収集
        try:
            soumu_candidates = self.collect_soumu_data()
            all_candidates.extend(soumu_candidates)
        except Exception as e:
            logger.error(f"❌ 総務省収集エラー: {e}")
        
        # 政党サイトデータ収集
        try:
            party_candidates = self.collect_party_candidates()
            all_candidates.extend(party_candidates)
        except Exception as e:
            logger.error(f"❌ 政党サイト収集エラー: {e}")
        
        # 重複除去
        unique_candidates = self.deduplicate_candidates(all_candidates)
        
        logger.info(f"🎯 公式ソース収集完了: 総計 {len(unique_candidates)}名")
        return unique_candidates

    def deduplicate_candidates(self, candidates):
        """候補者重複除去"""
        seen = set()
        unique_candidates = []
        
        for candidate in candidates:
            # 名前で重複判定
            key = candidate['name']
            if key not in seen and len(key) > 1:
                seen.add(key)
                unique_candidates.append(candidate)
        
        logger.info(f"重複除去: {len(candidates)}名 → {len(unique_candidates)}名")
        return unique_candidates

def main():
    """メイン処理"""
    logger.info("🚀 公式ソース候補者収集開始...")
    
    collector = OfficialSourcesCollector()
    candidates = collector.collect_all_official_sources()
    
    # 結果保存
    save_official_results(candidates)

def save_official_results(candidates):
    """公式ソース収集結果の保存"""
    logger.info("💾 公式ソース収集結果の保存...")
    
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
            "data_type": "official_sources_sangiin_2025",
            "collection_method": "soumu_party_official_sources",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "sources": ["総務省選挙部", "各政党公式サイト"],
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
    
    official_file = data_dir / f"official_sources_{timestamp}.json"
    
    with open(official_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 公式ソース結果保存: {official_file}")
    
    # 統計表示
    logger.info("\n📊 公式ソース収集統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  ソース数: {len(source_stats)}ソース")
    
    for source, count in source_stats.items():
        logger.info(f"  {source}: {count}名")

if __name__ == "__main__":
    main()