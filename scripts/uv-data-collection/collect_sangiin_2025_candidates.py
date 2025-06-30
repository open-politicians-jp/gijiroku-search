#!/usr/bin/env python3
"""
参議院議員選挙2025候補者データ収集スクリプト (Issue #83対応)

2025年参議院議員選挙の候補者データを包括的に収集し、マニフェスト・政策情報を抽出
対応データソース:
- 総務省選挙管理委員会
- 都道府県選挙管理委員会
- 各政党公式サイト
- Go2senkyo（可能な場合）
- 候補者個人サイト・SNS

機能:
- 候補者基本情報収集
- 政党別マニフェスト抽出
- 政策立場・主張の構造化
- 既存議員データとの紐付け
- frontend/public/data/sangiin_candidates/ に保存
"""

import json
import requests
import time
import re
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin, urlparse
import csv

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class Sangiin2025CandidatesCollector:
    """参院選2025候補者データ収集クラス (Issue #83対応)"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.candidates_dir = self.project_root / "frontend" / "public" / "data" / "sangiin_candidates"
        self.raw_data_dir = self.project_root / "data" / "processed" / "sangiin_2025_candidates"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.candidates_dir.mkdir(parents=True, exist_ok=True)
        
        # データソースURL設定
        self.data_sources = {
            "soumu": "https://www.soumu.go.jp/senkyo/",
            "go2senkyo": "https://sangiin.go2senkyo.com/2025",
            "parties": {
                "自由民主党": {
                    "url": "https://www.jimin.jp/",
                    "candidates_path": "/senkyo/sangiin2025/",
                    "manifesto_path": "/policy/manifesto/"
                },
                "立憲民主党": {
                    "url": "https://cdp-japan.jp/",
                    "candidates_path": "/senkyo/2025-sangiin/",
                    "manifesto_path": "/manifesto/"
                },
                "日本維新の会": {
                    "url": "https://o-ishin.jp/",
                    "candidates_path": "/sangiin2025/",
                    "manifesto_path": "/policy/"
                },
                "公明党": {
                    "url": "https://www.komei.or.jp/",
                    "candidates_path": "/senkyo/sangiin/2025/",
                    "manifesto_path": "/policy/"
                },
                "日本共産党": {
                    "url": "https://www.jcp.or.jp/",
                    "candidates_path": "/sangiin-senkyo/2025/",
                    "manifesto_path": "/manifesto/"
                },
                "国民民主党": {
                    "url": "https://new-kokumin.jp/",
                    "candidates_path": "/sangiin2025/",
                    "manifesto_path": "/policy/"
                },
                "れいわ新選組": {
                    "url": "https://reiwa-shinsengumi.com/",
                    "candidates_path": "/sangiin2025/",
                    "manifesto_path": "/policy/"
                }
            }
        }
        
        # 政党名正規化マッピング
        self.party_mapping = {
            '自由民主党': '自由民主党', '自民党': '自由民主党', 'LDP': '自由民主党',
            '立憲民主党': '立憲民主党', '立民': '立憲民主党', 'CDP': '立憲民主党',
            '日本維新の会': '日本維新の会', '維新': '日本維新の会', '維新の会': '日本維新の会',
            '公明党': '公明党', '公明': '公明党',
            '日本共産党': '日本共産党', '共産党': '日本共産党', '共産': '日本共産党', 'JCP': '日本共産党',
            '国民民主党': '国民民主党', '国民': '国民民主党', 'DPFP': '国民民主党',
            'れいわ新選組': 'れいわ新選組', 'れいわ': 'れいわ新選組',
            '社会民主党': '社会民主党', '社民': '社会民主党', 'SDP': '社会民主党',
            'NHK党': 'NHK党', 'N国': 'NHK党',
            '無所属': '無所属'
        }
        
        # 都道府県コード（参院選選挙区）
        self.prefecture_codes = {
            "北海道": "hokkaido", "青森": "aomori", "岩手": "iwate", "宮城": "miyagi",
            "秋田": "akita", "山形": "yamagata", "福島": "fukushima", "茨城": "ibaraki",
            "栃木": "tochigi", "群馬": "gunma", "埼玉": "saitama", "千葉": "chiba",
            "東京": "tokyo", "神奈川": "kanagawa", "新潟": "niigata", "富山": "toyama",
            "石川": "ishikawa", "福井": "fukui", "山梨": "yamanashi", "長野": "nagano",
            "岐阜": "gifu", "静岡": "shizuoka", "愛知": "aichi", "三重": "mie",
            "滋賀": "shiga", "京都": "kyoto", "大阪": "osaka", "兵庫": "hyogo",
            "奈良": "nara", "和歌山": "wakayama", "鳥取": "tottori", "島根": "shimane",
            "岡山": "okayama", "広島": "hiroshima", "山口": "yamaguchi", "徳島": "tokushima",
            "香川": "kagawa", "愛媛": "ehime", "高知": "kochi", "福岡": "fukuoka",
            "佐賀": "saga", "長崎": "nagasaki", "熊本": "kumamoto", "大分": "oita",
            "宮崎": "miyazaki", "鹿児島": "kagoshima", "沖縄": "okinawa"
        }
        
        # 2025年参院選改選議席（仮）
        self.sangiin_seats_2025 = {
            "北海道": 1, "青森": 1, "岩手": 1, "宮城": 1, "秋田": 1, "山形": 1,
            "福島": 1, "茨城": 2, "栃木": 1, "群馬": 1, "埼玉": 3, "千葉": 3,
            "東京": 6, "神奈川": 4, "新潟": 1, "富山": 1, "石川": 1, "福井": 1,
            "山梨": 1, "長野": 1, "岐阜": 1, "静岡": 2, "愛知": 4, "三重": 1,
            "滋賀": 1, "京都": 2, "大阪": 4, "兵庫": 3, "奈良": 1, "和歌山": 1,
            "鳥取": 1, "島根": 1, "岡山": 1, "広島": 2, "山口": 1, "徳島": 1,
            "香川": 1, "愛媛": 1, "高知": 1, "福岡": 3, "佐賀": 1, "長崎": 1,
            "熊本": 1, "大分": 1, "宮崎": 1, "鹿児島": 1, "沖縄": 1,
            "比例代表": 48  # 全国比例
        }
    
    def update_headers(self):
        """User-Agent更新とIP偽装"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
    
    def random_delay(self, min_seconds=2, max_seconds=5):
        """ランダム遅延でレート制限対応（参院選用に長めに設定）"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def normalize_party_name(self, party_name: str) -> str:
        """政党名を正規化"""
        if not party_name:
            return "無所属"
        
        for key, normalized in self.party_mapping.items():
            if key in party_name:
                return normalized
        return party_name
    
    def collect_all_candidates(self) -> List[Dict[str, Any]]:
        """全データソースから候補者データを収集"""
        logger.info("🚀 参院選2025候補者データ収集開始...")
        
        all_candidates = []
        
        # 1. 政党公式サイトから収集
        party_candidates = self.collect_from_party_sites()
        all_candidates.extend(party_candidates)
        
        # 2. Go2senkyoから収集（可能な場合）
        go2senkyo_candidates = self.collect_from_go2senkyo()
        all_candidates.extend(go2senkyo_candidates)
        
        # 3. 総務省・地方選管から収集
        official_candidates = self.collect_from_official_sources()
        all_candidates.extend(official_candidates)
        
        # 4. 重複除去と統合
        unified_candidates = self.unify_candidate_data(all_candidates)
        
        # 5. 政策・マニフェスト情報の付与
        enhanced_candidates = self.enhance_with_policy_data(unified_candidates)
        
        logger.info(f"✨ 候補者データ収集完了: {len(enhanced_candidates)}名")
        return enhanced_candidates
    
    def collect_from_party_sites(self) -> List[Dict[str, Any]]:
        """各政党公式サイトから候補者データを収集"""
        logger.info("📊 政党公式サイトから候補者データ収集開始...")
        
        party_candidates = []
        
        for party_name, party_info in self.data_sources["parties"].items():
            try:
                logger.info(f"🔍 {party_name}の候補者データ収集中...")
                
                candidates = self.extract_party_candidates(party_name, party_info)
                party_candidates.extend(candidates)
                
                logger.info(f"✅ {party_name}: {len(candidates)}名収集")
                self.random_delay()
                
            except Exception as e:
                logger.error(f"❌ {party_name}の収集エラー: {str(e)}")
                continue
        
        logger.info(f"📊 政党サイト収集完了: {len(party_candidates)}名")
        return party_candidates
    
    def extract_party_candidates(self, party_name: str, party_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個別政党サイトから候補者情報を抽出"""
        candidates = []
        
        try:
            # 候補者一覧ページのURL構築
            base_url = party_info["url"]
            candidates_path = party_info.get("candidates_path", "/")
            candidates_url = urljoin(base_url, candidates_path)
            
            self.random_delay()
            response = self.session.get(candidates_url, timeout=30)
            
            # アクセス可能性チェック
            if response.status_code == 404:
                # 2025年ページがまだない場合、一般的なパスを試行
                alternative_paths = ["/senkyo/", "/candidates/", "/member/"]
                for alt_path in alternative_paths:
                    try:
                        alt_url = urljoin(base_url, alt_path)
                        response = self.session.get(alt_url, timeout=15)
                        if response.status_code == 200:
                            candidates_url = alt_url
                            break
                    except:
                        continue
            
            if response.status_code != 200:
                logger.warning(f"{party_name}の候補者ページにアクセスできません: {candidates_url}")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 政党ごとの構造に応じた候補者抽出
            if party_name == "自由民主党":
                candidates = self.extract_ldp_candidates(soup, base_url)
            elif party_name == "立憲民主党":
                candidates = self.extract_cdp_candidates(soup, base_url)
            elif party_name == "日本維新の会":
                candidates = self.extract_ishin_candidates(soup, base_url)
            elif party_name == "公明党":
                candidates = self.extract_komei_candidates(soup, base_url)
            elif party_name == "日本共産党":
                candidates = self.extract_jcp_candidates(soup, base_url)
            elif party_name == "国民民主党":
                candidates = self.extract_dpfp_candidates(soup, base_url)
            elif party_name == "れいわ新選組":
                candidates = self.extract_reiwa_candidates(soup, base_url)
            else:
                # 汎用的な抽出
                candidates = self.extract_generic_candidates(soup, base_url, party_name)
            
            # 候補者データにメタデータ追加
            for candidate in candidates:
                candidate.update({
                    "party": party_name,
                    "party_normalized": self.normalize_party_name(party_name),
                    "source": "party_official",
                    "source_url": candidates_url,
                    "collected_at": datetime.now().isoformat()
                })
        
        except Exception as e:
            logger.error(f"{party_name}候補者抽出エラー: {str(e)}")
        
        return candidates
    
    def extract_generic_candidates(self, soup: BeautifulSoup, base_url: str, party: str) -> List[Dict[str, Any]]:
        """汎用的な候補者情報抽出（全政党対応）"""
        candidates = []
        
        try:
            # 候補者名を含む要素を探す
            candidate_patterns = [
                # リンクから抽出
                soup.find_all('a', href=re.compile(r'candidate|member|profile')),
                # 見出しから抽出
                soup.find_all(['h2', 'h3', 'h4'], string=re.compile(r'[一-龯]{2,4}[　\s]+[一-龯]{2,4}')),
                # リスト項目から抽出
                soup.find_all('li', string=re.compile(r'[一-龯]{2,4}[　\s]+[一-龯]{2,4}')),
                # テーブルから抽出
                soup.find_all('td', string=re.compile(r'[一-龯]{2,4}[　\s]+[一-龯]{2,4}'))
            ]
            
            for pattern in candidate_patterns:
                for element in pattern:
                    try:
                        name_text = element.get_text(strip=True) if hasattr(element, 'get_text') else str(element)
                        
                        # 候補者名の抽出と正規化
                        name_match = re.search(r'([一-龯]{2,4}[　\s]+[一-龯]{2,4})', name_text)
                        if name_match:
                            candidate_name = name_match.group(1).replace('\u3000', ' ').strip()
                            
                            # 既存チェック
                            if any(c['name'] == candidate_name for c in candidates):
                                continue
                            
                            # プロフィールURL抽出
                            profile_url = ""
                            if hasattr(element, 'get') and element.get('href'):
                                href = element.get('href')
                                if href.startswith('/'):
                                    profile_url = urljoin(base_url, href)
                                elif href.startswith('http'):
                                    profile_url = href
                            
                            candidate = {
                                "candidate_id": f"{party.lower().replace(' ', '_')}_{len(candidates)+1:03d}",
                                "name": candidate_name,
                                "constituency": "未分類",
                                "constituency_type": "unknown",
                                "region": None,
                                "profile_url": profile_url,
                                "manifesto_summary": "",
                                "policy_positions": [],
                                "sns_accounts": {},
                                "status": "candidate"
                            }
                            
                            candidates.append(candidate)
                    
                    except Exception as e:
                        logger.debug(f"候補者抽出エラー: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"汎用候補者抽出エラー: {str(e)}")
        
        return candidates[:50]  # 最大50名に制限
    
    def extract_ldp_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """自由民主党候補者抽出"""
        # 自民党特有の構造に対応した抽出ロジック
        return self.extract_generic_candidates(soup, base_url, "自由民主党")
    
    def extract_cdp_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """立憲民主党候補者抽出"""
        return self.extract_generic_candidates(soup, base_url, "立憲民主党")
    
    def extract_ishin_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """日本維新の会候補者抽出"""
        return self.extract_generic_candidates(soup, base_url, "日本維新の会")
    
    def extract_komei_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """公明党候補者抽出"""
        return self.extract_generic_candidates(soup, base_url, "公明党")
    
    def extract_jcp_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """日本共産党候補者抽出"""
        return self.extract_generic_candidates(soup, base_url, "日本共産党")
    
    def extract_dpfp_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """国民民主党候補者抽出"""
        return self.extract_generic_candidates(soup, base_url, "国民民主党")
    
    def extract_reiwa_candidates(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """れいわ新選組候補者抽出"""
        return self.extract_generic_candidates(soup, base_url, "れいわ新選組")
    
    def collect_from_go2senkyo(self) -> List[Dict[str, Any]]:
        """Go2senkyoから候補者データを収集"""
        logger.info("🔍 Go2senkyo参院選データ収集中...")
        
        candidates = []
        
        try:
            self.random_delay()
            response = self.session.get(self.data_sources["go2senkyo"], timeout=30)
            
            if response.status_code != 200:
                logger.warning("Go2senkyoにアクセスできません")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Go2senkyo特有の構造から候補者情報を抽出
            # （現時点では詳細データが少ないため、将来的に拡張）
            candidate_elements = soup.find_all(['div', 'article'], class_=re.compile(r'candidate|member'))
            
            for element in candidate_elements:
                try:
                    candidate_data = self.parse_go2senkyo_candidate(element)
                    if candidate_data:
                        candidates.append(candidate_data)
                except Exception as e:
                    logger.debug(f"Go2senkyo候補者解析エラー: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"Go2senkyo収集エラー: {str(e)}")
        
        logger.info(f"📊 Go2senkyo収集完了: {len(candidates)}名")
        return candidates
    
    def parse_go2senkyo_candidate(self, element) -> Optional[Dict[str, Any]]:
        """Go2senkyo候補者要素の解析"""
        try:
            name_elem = element.find(['h2', 'h3', 'a'], string=re.compile(r'[一-龯]{2,4}'))
            if not name_elem:
                return None
            
            name = name_elem.get_text(strip=True)
            
            # 政党情報
            party_elem = element.find(class_=re.compile(r'party|political'))
            party = party_elem.get_text(strip=True) if party_elem else "未分類"
            
            # 選挙区情報
            constituency_elem = element.find(class_=re.compile(r'constituency|district'))
            constituency = constituency_elem.get_text(strip=True) if constituency_elem else "未分類"
            
            return {
                "candidate_id": f"go2senkyo_{hash(name) % 1000:03d}",
                "name": name,
                "party": self.normalize_party_name(party),
                "constituency": constituency,
                "constituency_type": "proportional" if "比例" in constituency else "single_member",
                "source": "go2senkyo",
                "collected_at": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.debug(f"Go2senkyo要素解析エラー: {e}")
            return None
    
    def collect_from_official_sources(self) -> List[Dict[str, Any]]:
        """総務省・都道府県選管から公式データを収集"""
        logger.info("🏛️ 総務省・地方選管から公式データ収集中...")
        
        official_candidates = []
        
        try:
            # 総務省選挙管理委員会
            soumu_candidates = self.collect_from_soumu()
            official_candidates.extend(soumu_candidates)
            
            # 都道府県選管（主要県のみ）
            major_prefectures = ["東京", "大阪", "愛知", "神奈川", "埼玉", "千葉"]
            for prefecture in major_prefectures:
                try:
                    pref_candidates = self.collect_from_prefecture(prefecture)
                    official_candidates.extend(pref_candidates)
                    self.random_delay()
                except Exception as e:
                    logger.debug(f"{prefecture}県データ収集エラー: {e}")
                    continue
        
        except Exception as e:
            logger.error(f"公式データ収集エラー: {str(e)}")
        
        logger.info(f"🏛️ 公式データ収集完了: {len(official_candidates)}名")
        return official_candidates
    
    def collect_from_soumu(self) -> List[Dict[str, Any]]:
        """総務省選挙管理委員会からデータ収集"""
        candidates = []
        
        try:
            soumu_url = self.data_sources["soumu"]
            self.random_delay()
            response = self.session.get(soumu_url, timeout=30)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 選挙関連リンクを探す
                election_links = soup.find_all('a', href=re.compile(r'sangiin|election|senkyo'))
                
                for link in election_links[:5]:  # 最大5つのリンクをチェック
                    try:
                        href = link.get('href')
                        if href:
                            full_url = urljoin(soumu_url, href)
                            self.random_delay()
                            sub_response = self.session.get(full_url, timeout=15)
                            
                            if sub_response.status_code == 200:
                                sub_soup = BeautifulSoup(sub_response.text, 'html.parser')
                                sub_candidates = self.extract_generic_candidates(sub_soup, full_url, "総務省データ")
                                candidates.extend(sub_candidates)
                    except Exception as e:
                        logger.debug(f"総務省サブページエラー: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"総務省データ収集エラー: {str(e)}")
        
        return candidates
    
    def collect_from_prefecture(self, prefecture: str) -> List[Dict[str, Any]]:
        """都道府県選管からデータ収集"""
        candidates = []
        
        try:
            # 都道府県選管URLの推定
            pref_code = self.prefecture_codes.get(prefecture, prefecture.lower())
            pref_urls = [
                f"https://www.pref.{pref_code}.lg.jp/senkyo/",
                f"https://{pref_code}.jp/senkyo/",
                f"https://www.{pref_code}-senkan.jp/"
            ]
            
            for url in pref_urls:
                try:
                    self.random_delay()
                    response = self.session.get(url, timeout=15)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.text, 'html.parser')
                        pref_candidates = self.extract_generic_candidates(soup, url, f"{prefecture}選管")
                        candidates.extend(pref_candidates)
                        break
                
                except Exception as e:
                    logger.debug(f"{prefecture}選管URL試行エラー ({url}): {e}")
                    continue
        
        except Exception as e:
            logger.error(f"{prefecture}データ収集エラー: {str(e)}")
        
        return candidates
    
    def unify_candidate_data(self, all_candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """候補者データの重複除去と統合"""
        logger.info("🔄 候補者データ統合中...")
        
        unified = {}
        
        for candidate in all_candidates:
            name = candidate.get('name', '').strip()
            party = candidate.get('party', '')
            
            # 名前と政党の組み合わせで重複チェック
            key = f"{name}_{party}"
            
            if key not in unified:
                unified[key] = candidate
            else:
                # より詳細な情報で上書き
                existing = unified[key]
                if len(candidate.get('profile_url', '')) > len(existing.get('profile_url', '')):
                    unified[key] = candidate
                elif candidate.get('source') == 'party_official' and existing.get('source') != 'party_official':
                    unified[key] = candidate
        
        unified_list = list(unified.values())
        logger.info(f"🔄 統合完了: {len(all_candidates)}名 → {len(unified_list)}名")
        
        return unified_list
    
    def enhance_with_policy_data(self, candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """政策・マニフェスト情報で候補者データを強化"""
        logger.info("📋 政策・マニフェスト情報付与中...")
        
        enhanced_candidates = []
        
        for candidate in candidates:
            try:
                enhanced = candidate.copy()
                
                # 政党マニフェスト情報の付与
                party_manifesto = self.get_party_manifesto(candidate.get('party', ''))
                if party_manifesto:
                    enhanced['party_manifesto'] = party_manifesto
                
                # 個人プロフィール・政策の収集
                profile_url = candidate.get('profile_url', '')
                if profile_url:
                    profile_data = self.extract_candidate_profile(profile_url)
                    enhanced.update(profile_data)
                
                # SNSアカウント検索
                sns_accounts = self.find_candidate_sns(candidate.get('name', ''))
                if sns_accounts:
                    enhanced['sns_accounts'] = sns_accounts
                
                enhanced_candidates.append(enhanced)
                
            except Exception as e:
                logger.debug(f"候補者{candidate.get('name', 'unknown')}の強化エラー: {e}")
                enhanced_candidates.append(candidate)
                continue
        
        logger.info("📋 政策情報付与完了")
        return enhanced_candidates
    
    def get_party_manifesto(self, party: str) -> Dict[str, Any]:
        """政党マニフェスト情報を取得"""
        if not party or party == "無所属":
            return {}
        
        try:
            party_info = self.data_sources["parties"].get(party, {})
            if not party_info:
                return {}
            
            manifesto_url = urljoin(party_info["url"], party_info.get("manifesto_path", "/"))
            
            self.random_delay()
            response = self.session.get(manifesto_url, timeout=20)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # マニフェスト本文抽出
                content_selectors = ['main', 'article', '.content', '#content', '.manifesto']
                manifesto_text = ""
                
                for selector in content_selectors:
                    elements = soup.select(selector)
                    if elements:
                        manifesto_text = elements[0].get_text(strip=True)[:2000]  # 2000文字まで
                        break
                
                return {
                    "party": party,
                    "url": manifesto_url,
                    "summary": manifesto_text,
                    "collected_at": datetime.now().isoformat()
                }
        
        except Exception as e:
            logger.debug(f"{party}マニフェスト取得エラー: {e}")
        
        return {}
    
    def extract_candidate_profile(self, profile_url: str) -> Dict[str, Any]:
        """候補者個人プロフィール・政策を抽出"""
        profile_data = {}
        
        try:
            self.random_delay()
            response = self.session.get(profile_url, timeout=15)
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 政策・主張の抽出
                policy_keywords = ['政策', '主張', '公約', 'マニフェスト', '政治信条', '取り組み']
                policy_text = ""
                
                for keyword in policy_keywords:
                    elements = soup.find_all(string=re.compile(keyword))
                    for element in elements:
                        parent = element.parent
                        if parent:
                            policy_text += parent.get_text(strip=True) + " "
                    
                    if len(policy_text) > 500:
                        break
                
                if policy_text:
                    profile_data['manifesto_summary'] = policy_text[:1000]
                
                # 経歴情報
                career_keywords = ['経歴', 'プロフィール', '略歴', '生い立ち']
                for keyword in career_keywords:
                    career_elem = soup.find(string=re.compile(keyword))
                    if career_elem and career_elem.parent:
                        career_text = career_elem.parent.get_text(strip=True)[:500]
                        profile_data['career'] = career_text
                        break
                
                # 写真URL
                img_elements = soup.find_all('img', alt=re.compile(r'プロフィール|写真|候補者'))
                for img in img_elements:
                    src = img.get('src', '')
                    if src:
                        if src.startswith('/'):
                            photo_url = urljoin(profile_url, src)
                        elif src.startswith('http'):
                            photo_url = src
                        else:
                            continue
                        profile_data['photo_url'] = photo_url
                        break
        
        except Exception as e:
            logger.debug(f"プロフィール抽出エラー ({profile_url}): {e}")
        
        return profile_data
    
    def find_candidate_sns(self, candidate_name: str) -> Dict[str, str]:
        """候補者のSNSアカウントを検索（制限的）"""
        # 実装は簡易版（APIキーが必要な本格検索は後日実装）
        sns_accounts = {}
        
        try:
            # 候補者名からSNSアカウント推定（非常に制限的）
            name_clean = re.sub(r'[　\s]+', '', candidate_name)
            
            # Twitterアカウント推定パターン
            twitter_patterns = [
                f"https://twitter.com/{name_clean}",
                f"https://twitter.com/{name_clean}_official",
                f"https://x.com/{name_clean}"
            ]
            
            # 実際のSNS検索は別途API実装が必要
            # ここでは構造のみ定義
            
        except Exception as e:
            logger.debug(f"SNS検索エラー: {e}")
        
        return sns_accounts
    
    def save_candidates_data(self, candidates: List[Dict[str, Any]]):
        """参院選候補者データを保存"""
        if not candidates:
            logger.warning("保存する候補者データがありません")
            return
        
        current_date = datetime.now()
        timestamp = current_date.strftime('%Y%m%d_%H%M%S')
        
        # メインデータファイル
        main_filename = f"sangiin_2025_candidates_{timestamp}.json"
        main_filepath = self.candidates_dir / main_filename
        
        # 最新データファイル
        latest_filepath = self.candidates_dir / "sangiin_2025_candidates_latest.json"
        
        # 政党別統計
        party_stats = {}
        constituency_stats = {}
        
        for candidate in candidates:
            party = candidate.get('party', '無所属')
            constituency = candidate.get('constituency', '未分類')
            
            party_stats[party] = party_stats.get(party, 0) + 1
            constituency_stats[constituency] = constituency_stats.get(constituency, 0) + 1
        
        # 保存データ構造
        save_data = {
            "metadata": {
                "data_type": "sangiin_2025_candidates",
                "election_year": 2025,
                "total_candidates": len(candidates),
                "parties_count": len(party_stats),
                "generated_at": current_date.isoformat(),
                "data_sources": list(self.data_sources.keys()),
                "collection_version": "1.0.0",
                "next_update": (current_date + timedelta(days=7)).isoformat()
            },
            "statistics": {
                "by_party": party_stats,
                "by_constituency": constituency_stats
            },
            "data": candidates
        }
        
        # メインファイル保存
        with open(main_filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        # 最新ファイル保存
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(save_data, f, ensure_ascii=False, indent=2)
        
        # CSV形式でも保存
        csv_filepath = self.candidates_dir / f"sangiin_2025_candidates_{timestamp}.csv"
        self.save_candidates_csv(candidates, csv_filepath)
        
        logger.info(f"📁 参院選候補者データ保存完了:")
        logger.info(f"  - メイン: {main_filepath}")
        logger.info(f"  - 最新: {latest_filepath}")
        logger.info(f"  - CSV: {csv_filepath}")
        logger.info(f"  - 候補者数: {len(candidates)}名")
        
        # 統計表示
        self.display_collection_stats(candidates, party_stats, constituency_stats)
    
    def save_candidates_csv(self, candidates: List[Dict[str, Any]], filepath: Path):
        """候補者データをCSV形式で保存"""
        try:
            with open(filepath, 'w', newline='', encoding='utf-8') as f:
                if not candidates:
                    return
                
                # CSVヘッダー
                fieldnames = [
                    'candidate_id', 'name', 'party', 'constituency', 'constituency_type',
                    'region', 'profile_url', 'manifesto_summary', 'career', 'photo_url',
                    'source', 'collected_at'
                ]
                
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                
                for candidate in candidates:
                    # CSV用データの準備
                    csv_row = {}
                    for field in fieldnames:
                        value = candidate.get(field, '')
                        # 複雑なオブジェクトは文字列化
                        if isinstance(value, (dict, list)):
                            value = str(value)
                        csv_row[field] = value
                    
                    writer.writerow(csv_row)
                    
        except Exception as e:
            logger.error(f"CSV保存エラー: {str(e)}")
    
    def display_collection_stats(self, candidates: List[Dict[str, Any]], 
                                party_stats: Dict[str, int], 
                                constituency_stats: Dict[str, int]):
        """収集統計の表示"""
        logger.info("\n📊 参院選2025候補者収集統計:")
        logger.info(f"総候補者数: {len(candidates)}名")
        
        # 政党別統計
        logger.info("\n🏛️ 政党別候補者数:")
        for party, count in sorted(party_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {party}: {count}名")
        
        # 選挙区別統計（上位10選挙区）
        logger.info("\n🗾 選挙区別候補者数（上位10）:")
        top_constituencies = sorted(constituency_stats.items(), key=lambda x: x[1], reverse=True)[:10]
        for constituency, count in top_constituencies:
            logger.info(f"  {constituency}: {count}名")
        
        # データソース別統計
        source_stats = {}
        for candidate in candidates:
            source = candidate.get('source', 'unknown')
            source_stats[source] = source_stats.get(source, 0) + 1
        
        logger.info("\n📡 データソース別:")
        for source, count in sorted(source_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {source}: {count}名")

def main():
    """メイン実行関数"""
    logger.info("🚀 参院選2025候補者データ収集開始 (Issue #83)")
    
    collector = Sangiin2025CandidatesCollector()
    
    try:
        # 全候補者データ収集
        candidates = collector.collect_all_candidates()
        
        if not candidates:
            logger.error("候補者データが取得できませんでした")
            return
        
        # データ保存
        collector.save_candidates_data(candidates)
        
        logger.info("✨ 参院選2025候補者データ収集処理完了 (Issue #83)")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()