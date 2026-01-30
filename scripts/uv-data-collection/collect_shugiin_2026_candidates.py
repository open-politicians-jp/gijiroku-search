#!/usr/bin/env python3
"""
衆議院議員選挙2026候補者データ収集スクリプト（改良版）

データソース:
1. 選挙ドットコム (go2senkyo.com) - 候補者一覧
2. NHK選挙WEB - 候補者データベース
3. 朝日新聞選挙ページ - 候補者情報
4. 各政党公式選挙特設サイト

出力: frontend/public/data/shugiin_candidates/
"""

import argparse
import json
import requests
import time
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
from urllib.parse import urljoin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class Shugiin2026CandidateCollector:
    """衆院選2026候補者データ収集（マルチソース版）"""

    def __init__(
        self,
        include_party_sites: bool = False,
        enable_nhk: bool = True,
        enable_asahi: bool = True,
        enrich_party: bool = False,
        include_proportional: bool = True,
    ):
        self.ua = UserAgent()
        self.session = requests.Session()
        self._update_headers()

        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "frontend" / "public" / "data" / "shugiin_candidates"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 都道府県コード（go2senkyo・NHK共通）
        self.prefectures = {
            1: "北海道", 2: "青森県", 3: "岩手県", 4: "宮城県", 5: "秋田県",
            6: "山形県", 7: "福島県", 8: "茨城県", 9: "栃木県", 10: "群馬県",
            11: "埼玉県", 12: "千葉県", 13: "東京都", 14: "神奈川県", 15: "新潟県",
            16: "富山県", 17: "石川県", 18: "福井県", 19: "山梨県", 20: "長野県",
            21: "岐阜県", 22: "静岡県", 23: "愛知県", 24: "三重県", 25: "滋賀県",
            26: "京都府", 27: "大阪府", 28: "兵庫県", 29: "奈良県", 30: "和歌山県",
            31: "鳥取県", 32: "島根県", 33: "岡山県", 34: "広島県", 35: "山口県",
            36: "徳島県", 37: "香川県", 38: "愛媛県", 39: "高知県", 40: "福岡県",
            41: "佐賀県", 42: "長崎県", 43: "熊本県", 44: "大分県", 45: "宮崎県",
            46: "鹿児島県", 47: "沖縄県"
        }

        self.party_mapping = {
            '自由民主党': '自由民主党', '自民党': '自由民主党', '自民': '自由民主党',
            '立憲民主党': '中道改革連合', '立民': '中道改革連合', '立憲': '中道改革連合',
            '公明党': '中道改革連合', '公明': '中道改革連合',
            '中道改革連合': '中道改革連合', '中道改革': '中道改革連合', '中道': '中道改革連合',
            '日本維新の会': '日本維新の会', '維新': '日本維新の会',
            '日本共産党': '日本共産党', '共産党': '日本共産党', '共産': '日本共産党',
            '国民民主党': '国民民主党', '国民': '国民民主党',
            'れいわ新選組': 'れいわ新選組', 'れいわ': 'れいわ新選組',
            '社会民主党': '社会民主党', '社民党': '社会民主党', '社民': '社会民主党',
            'NHK党': 'NHK党', 'みんなでつくる党': 'NHK党',
            '参政党': '参政党',
            '日本保守党': '日本保守党', '保守党': '日本保守党',
            'チームみらい': 'チームみらい',
            '減税日本': '減税日本',
            '無所属': '無所属',
        }

        self.include_party_sites = include_party_sites
        self.enable_nhk = enable_nhk
        self.enable_asahi = enable_asahi
        self.enrich_party = enrich_party
        self.include_proportional = include_proportional

        # 収集結果
        self.all_candidates: List[Dict] = []
        self.sources_used: List[str] = []

    def _update_headers(self):
        desktop_ua = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        self.session.headers.update({
            'User-Agent': desktop_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })

    def _delay(self, min_s=0.6, max_s=1.2):
        time.sleep(random.uniform(min_s, max_s))

    def _fetch(self, url: str, timeout: int = 20) -> Optional[BeautifulSoup]:
        try:
            self._delay()
            self._update_headers()
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            logger.warning(f"取得失敗 ({url}): {e}")
            return None

    def _fetch_with_url(self, url: str, timeout: int = 20) -> Tuple[Optional[BeautifulSoup], str]:
        try:
            self._delay()
            self._update_headers()
            resp = self.session.get(url, timeout=timeout, allow_redirects=True)
            resp.raise_for_status()
            resp.encoding = resp.apparent_encoding or 'utf-8'
            return BeautifulSoup(resp.text, 'html.parser'), resp.url
        except Exception as e:
            logger.warning(f"取得失敗 ({url}): {e}")
            return None, url

    def normalize_party(self, name: str) -> str:
        if not name:
            return '無所属'
        name = name.strip()
        for key, norm in self.party_mapping.items():
            if key in name:
                return norm
        return name

    # =============================================
    # 選挙ドットコム (go2senkyo)
    # =============================================
    def collect_go2senkyo(self):
        """選挙ドットコムから候補者一覧を収集"""
        logger.info("=" * 60)
        logger.info("📊 選挙ドットコム (go2senkyo) から候補者収集...")
        logger.info("=" * 60)

        count = 0

        base_urls = [
            "https://go2senkyo.com/shugiin/28030",
            "https://shugiin.go2senkyo.com/51",
        ]

        base_soup = None
        base_url = ""
        for base in base_urls:
            base_soup, final_url = self._fetch_with_url(base)
            if base_soup:
                base_url = final_url
                break

        if not base_soup:
            logger.warning("  go2senkyoの選挙ページにアクセスできませんでした")
            return

        prefecture_links = self._extract_go2senkyo_prefecture_links(base_soup, base_url)
        if not prefecture_links:
            logger.warning("  都道府県リンクが取得できませんでした")

        senkyoku_links: List[Tuple[str, str, str]] = []
        for pref_name, pref_url in prefecture_links:
            logger.info(f"  {pref_name} を取得中...")
            pref_soup = self._fetch(pref_url)
            if not pref_soup:
                continue
            senkyoku_links.extend(self._extract_go2senkyo_senkyoku_links(pref_soup, pref_url, pref_name))
            self._delay(0.3, 0.6)

        seen_senkyoku = set()
        for senkyoku_name, senkyoku_url, pref_name in senkyoku_links:
            if senkyoku_url in seen_senkyoku:
                continue
            seen_senkyoku.add(senkyoku_url)

            soup = self._fetch(senkyoku_url)
            if not soup:
                continue

            candidates = self._parse_go2senkyo_senkyoku(soup, senkyoku_url, senkyoku_name, pref_name)
            if candidates:
                self.all_candidates.extend(candidates)
                count += len(candidates)
                logger.info(f"    -> {senkyoku_name}: {len(candidates)}名取得")

        if self.include_proportional:
            hirei_candidates = self._collect_go2senkyo_hirei_from_base_html(base_soup, base_url)
            if hirei_candidates:
                self.all_candidates.extend(hirei_candidates)
                count += len(hirei_candidates)

        if count > 0:
            self.sources_used.append("go2senkyo")
        logger.info(f"  選挙ドットコム合計: {count}名")

    def _extract_go2senkyo_prefecture_links(self, soup: BeautifulSoup, base_url: str) -> List[Tuple[str, str]]:
        links: List[Tuple[str, str]] = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/prefecture/' not in href:
                continue
            match = re.search(r'/prefecture/(\d+)', href)
            if not match:
                continue
            code = int(match.group(1))
            pref_name = self.prefectures.get(code, '') or link.get_text(strip=True)
            if not pref_name:
                continue
            links.append((pref_name, urljoin(base_url, href)))
        if not links:
            html = str(soup)
            for match in re.findall(r'/prefecture/(\d+)', html):
                code = int(match)
                pref_name = self.prefectures.get(code, '')
                if not pref_name:
                    continue
                links.append((pref_name, urljoin(base_url, f"/prefecture/{code}")))
        return links

    def _extract_go2senkyo_senkyoku_links(self, soup: BeautifulSoup, base_url: str, pref_name: str) -> List[Tuple[str, str, str]]:
        links: List[Tuple[str, str, str]] = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/senkyoku/' not in href:
                continue
            text = link.get_text(strip=True)
            if not re.search(r'\d+\s*区', text):
                continue
            links.append((text, urljoin(base_url, href), pref_name))
        return links

    def _collect_go2senkyo_hirei_from_base_html(self, base_soup: BeautifulSoup, base_url: str) -> List[Dict]:
        logger.info("  比例代表候補者を取得中...")
        candidates: List[Dict] = []

        hirei_links = []
        for link in base_soup.find_all('a', href=True):
            href = link.get('href', '')
            if 'hireiku' in href and 'hirei_party' in href and 'candidates' in href:
                hirei_links.append(urljoin(base_url, href))

        if not hirei_links:
            html = str(base_soup)
            for match in re.findall(r"/hireiku/\\d+/hirei_party/\\d+/candidates", html):
                hirei_links.append(urljoin(base_url, match))

        hirei_links = sorted(set(hirei_links))

        if not hirei_links:
            logger.info("    比例代表リンクが見つかりませんでした")
            return candidates

        for link in hirei_links:
            soup = self._fetch(link)
            if not soup:
                continue
            block_name = self._extract_hirei_block_name(soup) or "比例代表"
            block_candidates = self._parse_go2senkyo_hirei(soup, link, block_name)
            candidates.extend(block_candidates)
        logger.info(f"    比例代表: {len(candidates)}名")
        return candidates

    def _extract_hirei_block_name(self, soup: BeautifulSoup) -> str:
        text = soup.get_text(separator=' ', strip=True)
        match = re.search(r'(北海道|東北|北関東|東京|南関東|北陸信越|東海|近畿|中国|四国|九州)ブロック', text)
        if match:
            return match.group(0)
        return ""

    def _parse_go2senkyo_senkyoku(self, soup: BeautifulSoup, source_url: str, fallback_name: str, pref_name: str) -> List[Dict]:
        candidates = []
        constituency = self._extract_constituency_name(soup) or fallback_name or pref_name
        for name, profile_url, party in self._extract_candidates_from_go2senkyo_page(soup):
            candidates.append({
                "name": name,
                "party": party or "不明",
                "constituency": constituency,
                "constituency_type": "single_member",
                "prefecture": pref_name,
                "profile_url": profile_url,
                "source": "go2senkyo",
                "source_url": source_url,
            })
        return candidates

    def _parse_go2senkyo_hirei(self, soup: BeautifulSoup, source_url: str, block_name: str) -> List[Dict]:
        candidates = []
        constituency = f"比例{block_name}"
        for name, profile_url, party in self._extract_candidates_from_go2senkyo_page(soup):
            candidates.append({
                "name": name,
                "party": party or "不明",
                "constituency": constituency,
                "constituency_type": "proportional",
                "prefecture": "",
                "profile_url": profile_url,
                "source": "go2senkyo",
                "source_url": source_url,
            })
        return candidates

    def _extract_constituency_name(self, soup: BeautifulSoup) -> str:
        heading = soup.find(['h1', 'h2'])
        if heading:
            text = heading.get_text(strip=True)
            match = re.search(r'([\u4E00-\u9FFF]{1,4})\s*(\d+)\s*区', text)
            if match:
                return f"{match.group(1)}{match.group(2)}区"
        title = soup.find('title')
        if title:
            match = re.search(r'([\u4E00-\u9FFF]{1,4})\s*(\d+)\s*区', title.get_text())
            if match:
                return f"{match.group(1)}{match.group(2)}区"
        return ""

    def _extract_candidates_from_go2senkyo_page(self, soup: BeautifulSoup) -> List[Tuple[str, str, str]]:
        candidates: List[Tuple[str, str, str]] = []
        for link in soup.find_all('a', href=True):
            href = link.get('href', '')
            if '/seijika/' not in href:
                continue
            if not re.search(r'/seijika/\d+/?$', href):
                continue
            name = link.get_text(strip=True)
            name = self._clean_candidate_name(name)
            if not self._is_probable_candidate_name(name):
                continue
            parent = link.find_parent(['article', 'section', 'li', 'div'])
            context_text = parent.get_text(separator=' ', strip=True) if parent else ''
            party = self._find_party_in_text(context_text)
            profile_url = urljoin("https://go2senkyo.com", href)
            candidates.append((name, profile_url, party))
        return candidates

    def _clean_candidate_name(self, name: str) -> str:
        name = re.sub(r'\s+', ' ', name or '').strip()
        return name

    def _is_probable_candidate_name(self, name: str) -> bool:
        if not name:
            return False
        if len(name) < 2 or len(name) > 24:
            return False
        if re.search(r'候補者|政治家|もっと知る|寄付|応援|標準|名簿|届出|順位|一覧|ページ', name):
            return False
        if not re.match(r'^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\s　・]+$', name):
            return False
        return True

    def _find_party_in_text(self, text: str) -> str:
        if not text:
            return ''
        for key in self.party_mapping:
            if key in text:
                return self.normalize_party(key)
        return ''

    def enrich_unknown_parties(self):
        unknown = [c for c in self.all_candidates if c.get("party") in ("", "不明") and c.get("profile_url")]
        if not unknown:
            return
        logger.info(f"  不明政党の補完: {len(unknown)}名")
        for idx, candidate in enumerate(unknown, 1):
            soup = self._fetch(candidate["profile_url"])
            if not soup:
                continue
            party = self._extract_party_from_profile(soup)
            if party:
                candidate["party"] = party
            if idx % 20 == 0:
                self._delay(0.8, 1.6)

    def _extract_party_from_profile(self, soup: BeautifulSoup) -> str:
        for selector in ['.party', '.party-name', '.affiliation', '.p-profile__party', '.seijika__party']:
            elem = soup.select_one(selector)
            if elem:
                return self.normalize_party(elem.get_text(strip=True))
        text = soup.get_text(separator=' ', strip=True)
        return self._find_party_in_text(text)


    # =============================================
    # NHK選挙WEB
    # =============================================
    def collect_nhk(self):
        """NHK選挙WEBから候補者データを収集"""
        logger.info("=" * 60)
        logger.info("📺 NHK選挙WEB から候補者収集...")
        logger.info("=" * 60)

        count = 0
        base_url = "https://www.nhk.or.jp/senkyo/database/shugiin/2026"

        # トップページでURL構造を確認
        soup = self._fetch(f"{base_url}/")
        if not soup:
            # 代替URL
            soup = self._fetch("https://www.nhk.or.jp/senkyo/database/shugiin/")

        if not soup:
            logger.warning("  NHK選挙WEBにアクセスできませんでした")
            return

        # 都道府県別に収集
        for code, pref_name in self.prefectures.items():
            # NHKのURL形式を複数パターン試行
            urls_to_try = [
                f"{base_url}/koho/prefecture/{code:02d}/",
                f"{base_url}/expected-candidates/{code:02d}/",
                f"https://www.nhk.or.jp/senkyo/database/shugiin/koho/prefecture/{code:02d}/",
            ]

            for url in urls_to_try:
                pref_soup = self._fetch(url)
                if pref_soup:
                    candidates = self._parse_nhk_prefecture(pref_soup, pref_name, url)
                    if candidates:
                        self.all_candidates.extend(candidates)
                        count += len(candidates)
                        logger.info(f"  [{code:02d}] {pref_name}: {len(candidates)}名 (NHK)")
                        break

            if code % 10 == 0:
                self._delay(2, 4)

        if count > 0:
            self.sources_used.append("nhk")
        logger.info(f"  NHK合計: {count}名")

    def _parse_nhk_prefecture(self, soup: BeautifulSoup, pref: str, source_url: str) -> List[Dict]:
        """NHKの都道府県ページを解析"""
        candidates = []

        # NHKのページ構造パターン
        # パターン1: 候補者カード
        for selector in ['.candidate', '.person', '.koho', '.profile-card',
                         '.candidate-item', '.member-card', 'article.member']:
            items = soup.select(selector)
            if items:
                for item in items:
                    name_elem = item.select_one('.name, .candidate-name, h3, h4, .member-name')
                    if not name_elem:
                        continue
                    name = name_elem.get_text(strip=True)
                    if not name or len(name) < 2 or len(name) > 10:
                        continue

                    party_elem = item.select_one('.party, .party-name, .affiliation')
                    party = self.normalize_party(party_elem.get_text(strip=True)) if party_elem else ''

                    district_elem = item.select_one('.district, .constituency, .area')
                    constituency = district_elem.get_text(strip=True) if district_elem else pref

                    link = item.find('a', href=True)
                    profile_url = urljoin(source_url, link['href']) if link else ''

                    candidates.append({
                        "name": name,
                        "party": party or "不明",
                        "constituency": constituency,
                        "constituency_type": "小選挙区",
                        "prefecture": pref,
                        "profile_url": profile_url,
                        "source": "nhk",
                        "source_url": source_url,
                    })

        # パターン2: テーブル
        if not candidates:
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        if name and 2 <= len(name) <= 10 and not re.search(r'氏名|名前|候補者名|政党', name):
                            party_text = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            constituency = cells[2].get_text(strip=True) if len(cells) > 2 else pref

                            link = cells[0].find('a', href=True)
                            profile_url = urljoin(source_url, link['href']) if link else ''

                            candidates.append({
                                "name": name,
                                "party": self.normalize_party(party_text),
                                "constituency": constituency,
                                "constituency_type": "小選挙区",
                                "prefecture": pref,
                                "profile_url": profile_url,
                                "source": "nhk",
                                "source_url": source_url,
                            })

        # パターン3: JSON-LD / script内のJSON
        if not candidates:
            scripts = soup.find_all('script', type='application/json')
            for script in scripts:
                try:
                    data = json.loads(script.string)
                    if isinstance(data, list):
                        for item in data:
                            if isinstance(item, dict) and 'name' in item:
                                candidates.append({
                                    "name": item.get('name', ''),
                                    "party": self.normalize_party(item.get('party', '')),
                                    "constituency": item.get('constituency', pref),
                                    "constituency_type": "小選挙区",
                                    "prefecture": pref,
                                    "profile_url": item.get('url', ''),
                                    "source": "nhk",
                                    "source_url": source_url,
                                })
                except (json.JSONDecodeError, TypeError):
                    pass

        return candidates

    # =============================================
    # 朝日新聞
    # =============================================
    def collect_asahi(self):
        """朝日新聞の選挙ページから候補者データを収集"""
        logger.info("=" * 60)
        logger.info("📰 朝日新聞 から候補者収集...")
        logger.info("=" * 60)

        count = 0
        base_urls = [
            "https://www.asahi.com/senkyo/shuinsen/koho/",
            "https://www.asahi.com/senkyo/shuinsen/2026/koho/",
            "https://www.asahi.com/senkyo/shuin/koho/",
        ]

        for base_url in base_urls:
            soup = self._fetch(base_url)
            if not soup:
                continue

            # 都道府県リンクを探す
            pref_links = []
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                text = link.get_text(strip=True)
                for code, pref_name in self.prefectures.items():
                    short_name = pref_name.rstrip('都府県')
                    if short_name in text and len(text) <= 5:
                        pref_links.append((code, pref_name, urljoin(base_url, href)))
                        break

            if pref_links:
                logger.info(f"  {len(pref_links)}都道府県のリンクを検出")
                for code, pref_name, pref_url in pref_links:
                    pref_soup = self._fetch(pref_url)
                    if pref_soup:
                        candidates = self._parse_asahi_prefecture(pref_soup, pref_name, pref_url)
                        if candidates:
                            self.all_candidates.extend(candidates)
                            count += len(candidates)
                            logger.info(f"    {pref_name}: {len(candidates)}名")

                    if code % 10 == 0:
                        self._delay(2, 4)
                break

        if count > 0:
            self.sources_used.append("asahi")
        logger.info(f"  朝日新聞合計: {count}名")

    def _parse_asahi_prefecture(self, soup: BeautifulSoup, pref: str, source_url: str) -> List[Dict]:
        """朝日新聞の都道府県ページを解析"""
        candidates = []

        # テーブルやカードから候補者情報を抽出
        for selector in ['.candidate', '.koho', '.person', 'article', '.candidate-card']:
            items = soup.select(selector)
            if items:
                for item in items:
                    name_elem = item.select_one('.name, h3, h4, .candidate-name')
                    if not name_elem:
                        continue
                    name = name_elem.get_text(strip=True)
                    if not name or len(name) < 2 or len(name) > 10:
                        continue

                    party_elem = item.select_one('.party, .party-name')
                    party = self.normalize_party(party_elem.get_text(strip=True)) if party_elem else ''

                    link = item.find('a', href=True)
                    profile_url = urljoin(source_url, link['href']) if link else ''

                    candidates.append({
                        "name": name,
                        "party": party or "不明",
                        "constituency": pref,
                        "constituency_type": "小選挙区",
                        "prefecture": pref,
                        "profile_url": profile_url,
                        "source": "asahi",
                        "source_url": source_url,
                    })

        # テーブル形式
        if not candidates:
            for table in soup.find_all('table'):
                rows = table.find_all('tr')
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    if len(cells) >= 2:
                        name = cells[0].get_text(strip=True)
                        if name and 2 <= len(name) <= 10 and not re.search(r'氏名|名前|候補者', name):
                            party = cells[1].get_text(strip=True) if len(cells) > 1 else ''
                            candidates.append({
                                "name": name,
                                "party": self.normalize_party(party),
                                "constituency": pref,
                                "constituency_type": "小選挙区",
                                "prefecture": pref,
                                "profile_url": "",
                                "source": "asahi",
                                "source_url": source_url,
                            })

        return candidates

    # =============================================
    # 各政党の選挙特設サイト
    # =============================================
    def collect_party_sites(self):
        """各政党の選挙特設サイトから候補者データを収集"""
        logger.info("=" * 60)
        logger.info("🏛️ 各政党の公式選挙サイトから候補者収集...")
        logger.info("=" * 60)

        count = 0

        party_election_urls = {
            "国民民主党": [
                "https://new-kokumin.jp/policies",
            ],
            "自由民主党": [
                "https://www.jimin.jp/election/",
                "https://special.jimin.jp/",
            ],
            "立憲民主党": [
                "https://cdp-japan.jp/election/",
            ],
            "日本維新の会": [
                "https://o-ishin.jp/election/",
                "https://o-ishin.jp/election2026/",
            ],
            "公明党": [
                "https://www.komei.or.jp/campaign/",
            ],
            "日本共産党": [
                "https://www.jcp.or.jp/giin/",
            ],
            "れいわ新選組": [
                "https://reiwa-shinsengumi.com/election/",
            ],
            "参政党": [
                "https://www.sanseito.jp/",
            ],
        }

        for party_name, urls in party_election_urls.items():
            for url in urls:
                logger.info(f"  {party_name}: {url}")
                soup = self._fetch(url)
                if not soup:
                    continue

                candidates = self._parse_party_election_page(soup, party_name, url)
                if candidates:
                    self.all_candidates.extend(candidates)
                    count += len(candidates)
                    logger.info(f"    -> {len(candidates)}名取得")
                    break  # 1つのURLで取得できたら次の政党へ

        if count > 0:
            self.sources_used.append("party_official")
        logger.info(f"  政党公式サイト合計: {count}名")

    def _parse_party_election_page(self, soup: BeautifulSoup, party: str, source_url: str) -> List[Dict]:
        """政党の選挙ページから候補者を抽出"""
        candidates = []

        # script, style, nav, footer を除去
        for tag in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            tag.decompose()

        # 候補者リンクを探す
        all_links = soup.find_all('a', href=True)

        for link in all_links:
            text = link.get_text(strip=True)
            href = link.get('href', '')

            # 候補者名っぽいリンク（2〜8文字の日本語名）
            if not text or len(text) < 2 or len(text) > 12:
                continue

            # 日本人名パターン
            if not re.match(r'^[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\s　・]+$', text):
                continue

            # ナビゲーション要素を除外
            if re.search(r'メニュー|トップ|ホーム|ニュース|政策|お知らせ|お問い合わせ|サイトマップ|プライバシー|検索|閉じる|もっと|詳しく|一覧', text):
                continue

            # 選挙区情報を前後のテキストから抽出
            parent = link.find_parent()
            parent_text = parent.get_text() if parent else ''
            district_match = re.search(r'([\u4E00-\u9FFF]{2,4}[都道府県]?)?\s*(?:第)?(\d+)\s*区', parent_text)
            constituency = ''
            prefecture = ''
            if district_match:
                prefecture = district_match.group(1) or ''
                constituency = f"{prefecture}第{district_match.group(2)}区"
            else:
                # 比例かも
                hirei_match = re.search(r'比例\s*([\u4E00-\u9FFF]+)', parent_text)
                if hirei_match:
                    constituency = f"比例{hirei_match.group(1)}ブロック"

            candidates.append({
                "name": text.replace('　', ' ').strip(),
                "party": party,
                "constituency": constituency or "不明",
                "constituency_type": "比例代表" if "比例" in constituency else "小選挙区" if constituency else "不明",
                "prefecture": prefecture,
                "profile_url": urljoin(source_url, href),
                "source": "party_official",
                "source_url": source_url,
            })

        return candidates

    # =============================================
    # マージ・重複除去・保存
    # =============================================
    def deduplicate(self):
        """候補者の重複除去"""
        seen = {}

        for c in self.all_candidates:
            name = c.get("name", "").strip()
            if not name:
                continue

            # 名前+政党で一意化（同名異人がいる可能性あり）
            key = f"{name}_{c.get('party', '')}_{c.get('constituency', '')}"

            if key not in seen:
                seen[key] = c
            else:
                # より情報が多い方を残す
                existing = seen[key]
                if len(c.get("constituency", "")) > len(existing.get("constituency", "")):
                    seen[key]["constituency"] = c["constituency"]
                if c.get("profile_url") and not existing.get("profile_url"):
                    seen[key]["profile_url"] = c["profile_url"]
                if c.get("prefecture") and not existing.get("prefecture"):
                    seen[key]["prefecture"] = c["prefecture"]
                # ソース情報をマージ
                existing_source = existing.get("source", "")
                new_source = c.get("source", "")
                if new_source and new_source not in existing_source:
                    seen[key]["source"] = f"{existing_source},{new_source}"

        self.all_candidates = list(seen.values())
        logger.info(f"重複除去後: {len(self.all_candidates)}名")

    def save(self):
        """候補者データを保存"""
        if not self.all_candidates:
            logger.warning("保存する候補者データがありません")
            return

        # IDを割り振り
        for i, c in enumerate(self.all_candidates):
            c["candidate_id"] = f"shugiin2026_{i+1:04d}"
            c["collected_at"] = datetime.now().isoformat()

        # 統計
        party_counts = {}
        pref_counts = {}
        source_counts = {}
        for c in self.all_candidates:
            p = c.get("party", "不明")
            party_counts[p] = party_counts.get(p, 0) + 1
            pref = c.get("prefecture", "不明")
            if pref:
                pref_counts[pref] = pref_counts.get(pref, 0) + 1
            for s in c.get("source", "").split(","):
                s = s.strip()
                if s:
                    source_counts[s] = source_counts.get(s, 0) + 1

        data = {
            "metadata": {
                "data_type": "shugiin_2026_candidates",
                "description": "第51回衆議院議員総選挙（2026年）候補者データ",
                "election_year": 2026,
                "election_date": "2026-02-08",
                "announcement_date": "2026-01-27",
                "total_candidates": len(self.all_candidates),
                "parties_count": len(party_counts),
                "prefectures_count": len(pref_counts),
                "generated_at": datetime.now().isoformat(),
                "data_sources": self.sources_used,
                "sources_attribution": {
                    "go2senkyo": "選挙ドットコム (https://go2senkyo.com)",
                    "nhk": "NHK選挙WEB (https://www.nhk.or.jp/senkyo/)",
                    "asahi": "朝日新聞デジタル (https://www.asahi.com/senkyo/)",
                    "party_official": "各政党公式サイト",
                },
                "note": "本データは各メディアサイト・政党公式サイトから収集した公開情報です。正確な情報は各公式サイトをご確認ください。"
            },
            "statistics": {
                "by_party": dict(sorted(party_counts.items(), key=lambda x: -x[1])),
                "by_prefecture": dict(sorted(pref_counts.items(), key=lambda x: -x[1])),
                "by_source": source_counts,
            },
            "data": self.all_candidates,
        }

        # タイムスタンプ付きファイル
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        filepath = self.output_dir / f"shugiin_2026_candidates_{ts}.json"
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # latest
        latest = self.output_dir / "shugiin_2026_candidates_latest.json"
        with open(latest, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        logger.info(f"\n💾 保存完了: {filepath.name}")
        logger.info(f"   総候補者数: {len(self.all_candidates)}名")
        logger.info(f"   政党数: {len(party_counts)}")
        logger.info(f"   データソース: {', '.join(self.sources_used)}")
        logger.info("\n📊 政党別候補者数:")
        for party, cnt in sorted(party_counts.items(), key=lambda x: -x[1]):
            logger.info(f"   {party}: {cnt}名")

    def run(self):
        """全ソースから候補者データを収集"""
        logger.info("🚀 衆議院選2026候補者データ収集（マルチソース版）開始")
        logger.info(f"   対象: 選挙ドットコム / NHK / 朝日新聞")
        logger.info("")

        # 1. 選挙ドットコム
        try:
            self.collect_go2senkyo()
        except Exception as e:
            logger.error(f"go2senkyo収集エラー: {e}")

        # 2. NHK
        if self.enable_nhk:
            try:
                self.collect_nhk()
            except Exception as e:
                logger.error(f"NHK収集エラー: {e}")

        # 3. 朝日新聞
        if self.enable_asahi:
            try:
                self.collect_asahi()
            except Exception as e:
                logger.error(f"朝日新聞収集エラー: {e}")

        if self.include_party_sites:
            try:
                self.collect_party_sites()
            except Exception as e:
                logger.error(f"政党公式サイト収集エラー: {e}")

        if self.enrich_party:
            try:
                self.enrich_unknown_parties()
            except Exception as e:
                logger.error(f"政党補完エラー: {e}")

        # 5. 重複除去
        self.deduplicate()

        # 6. 保存
        self.save()

        logger.info("\n✨ 衆議院選2026候補者データ収集完了!")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--include-party-sites", action="store_true", help="政党公式サイトからも候補者を収集する")
    parser.add_argument("--only-go2senkyo", action="store_true", help="go2senkyoのみで収集する（NHK/朝日はスキップ）")
    parser.add_argument("--enrich-party", action="store_true", help="候補者プロフィールから不明政党を補完する")
    parser.add_argument("--skip-proportional", action="store_true", help="比例代表の収集をスキップする")
    args = parser.parse_args()

    collector = Shugiin2026CandidateCollector(
        include_party_sites=args.include_party_sites,
        enable_nhk=not args.only_go2senkyo,
        enable_asahi=not args.only_go2senkyo,
        enrich_party=args.enrich_party,
        include_proportional=not args.skip_proportional,
    )
    collector.run()


if __name__ == "__main__":
    main()
