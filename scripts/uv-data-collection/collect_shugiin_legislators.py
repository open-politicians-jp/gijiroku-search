#!/usr/bin/env python3
"""
衆議院議員データ収集スクリプト (Issue #16対応)

衆議院議員ページから議員データを収集し、参議院データと統合可能な形式で保存
https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/shiryo/kaiha_m.htm

機能:
- 衆議院議員一覧の収集
- 政党別・選挙区別情報の整理
- 参議院データとの統合対応
- frontend/public/data/legislators/ に保存
"""

import json
import requests
import time
import re
import random
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from urllib.parse import urljoin
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ShugiinLegislatorsCollector:
    """衆議院議員データ収集クラス (Issue #16対応)"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.legislators_dir = self.project_root / "frontend" / "public" / "data" / "legislators"
        self.raw_data_dir = self.project_root / "data" / "processed" / "shugiin_legislators"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.legislators_dir.mkdir(parents=True, exist_ok=True)
        
        # 衆議院議員関連URL
        self.base_url = "https://www.shugiin.go.jp"
        self.members_url = "https://www.shugiin.go.jp/internet/itdb_annai.nsf/html/statics/syu/1giin.htm"
        self.current_member_page = self.members_url
        
        # 政党名正規化マッピング
        self.party_mapping = {
            '自由民主党': '自由民主党',
            '自民党': '自由民主党',
            '立憲民主党': '立憲民主党',
            '立民': '立憲民主党',
            '日本維新の会': '日本維新の会',
            '維新': '日本維新の会',
            '公明党': '公明党',
            '公明': '公明党',
            '日本共産党': '日本共産党',
            '共産党': '日本共産党',
            '共産': '日本共産党',
            '国民民主党': '国民民主党',
            '国民': '国民民主党',
            'れいわ新選組': 'れいわ新選組',
            'れいわ': 'れいわ新選組',
            '社会民主党': '社会民主党',
            '社民': '社会民主党',
            'NHK党': 'NHK党',
            'N国': 'NHK党',
            '無所属': '無所属'
        }
        
    def update_headers(self):
        """User-Agent更新とIP偽装"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """ランダム遅延でレート制限対応"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def normalize_party_name(self, party_name: str) -> str:
        """政党名を正規化"""
        for key, normalized in self.party_mapping.items():
            if key in party_name:
                return normalized
        return party_name
    
    def extract_constituency_info(self, constituency_text: str) -> Dict[str, Any]:
        """選挙区情報を解析"""
        if not constituency_text:
            return {"type": "unknown", "region": None, "district": None}
        
        # 比例代表の場合
        if "比例" in constituency_text:
            # 比例ブロックを抽出 (例: "比例近畿" → "近畿")
            region_match = re.search(r'比例(.+)', constituency_text)
            region = region_match.group(1) if region_match else "全国"
            return {"type": "proportional", "region": region, "district": None}
        
        # 小選挙区の場合 (例: "東京1区", "北海道12区")
        district_match = re.search(r'(.+?)(\d+)区', constituency_text)
        if district_match:
            prefecture = district_match.group(1)
            district_num = int(district_match.group(2))
            return {
                "type": "single_member", 
                "region": prefecture, 
                "district": district_num,
                "full_name": constituency_text
            }
        
        # その他の場合
        return {"type": "other", "region": constituency_text, "district": None}
    
    def collect_members_data(self) -> List[Dict[str, Any]]:
        """衆議院議員データを収集"""
        logger.info("衆議院議員データ収集開始...")
        
        try:
            pages = self.get_member_page_urls()
            logger.info(f"議員ページ一覧: {pages}")
            members: List[Dict[str, Any]] = []
            
            for idx, page_url in enumerate(pages, start=1):
                logger.info(f"ページ{idx}/{len(pages)} 取得中: {page_url}")
                soup = self.fetch_member_page(page_url)
                if soup is None:
                    continue
                self.current_member_page = page_url
                page_members = self.extract_members_from_tables(soup)
                logger.info(f"  -> {len(page_members)}名取得")
                members.extend(page_members)
            
            logger.info(f"衆議院議員データ収集完了: {len(members)}名")
            return members
            
        except Exception as e:
            logger.error(f"衆議院議員データ収集エラー: {str(e)}")
            return []

    def fetch_member_page(self, url: str) -> Optional[BeautifulSoup]:
        try:
            self.random_delay()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            logger.info(f"衆議院議員ページ取得成功: {url}")
            return BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            logger.error(f"議員ページ取得エラー ({url}): {e}")
            return None

    def get_member_page_urls(self) -> List[str]:
        """かな別の議員ページ URL を抽出"""
        base_soup = self.fetch_member_page(self.members_url)
        if base_soup is None:
            return [self.members_url]
        urls = {self.members_url}
        for link in base_soup.select('a[href]'):
            href = link.get('href', '')
            if 'giin.htm' in href.lower() and 'giin_top' not in href.lower():
                urls.add(urljoin(self.members_url, href))
        # 数字順にソート
        def sort_key(u):
            match = re.search(r'/([0-9]+)giin\.htm$', u)
            return int(match.group(1)) if match else 999
        return sorted(urls, key=sort_key)
    
    def extract_members_from_tables(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """テーブルから議員データを抽出"""
        members = []
        
        try:
            # 議員データを含むテーブルを探す
            tables = soup.find_all('table')
            logger.info(f"発見したテーブル数: {len(tables)}")
            
            for table_idx, table in enumerate(tables):
                rows = table.find_all('tr')
                if not rows:
                    continue

                header_cells = rows[0].find_all(['th', 'td'])
                header_texts = [cell.get_text(strip=True) for cell in header_cells]
                header_joined = ''.join(header_texts)
                if '氏名' in header_joined and '選挙区' in header_joined:
                    logger.info(f"テーブル{table_idx + 1}を解析中: {len(rows)}行")
                    table_members = self.parse_members_table(table)
                    members.extend(table_members)
                    logger.info(f"テーブル{table_idx + 1}から{len(table_members)}名抽出")
            
            # テーブル以外の構造も試行
            if not members:
                logger.info("テーブル形式で見つからない場合、リスト形式を検索")
                members = self.extract_members_from_lists(soup)
            
            return members
            
        except Exception as e:
            logger.error(f"議員データ抽出エラー: {str(e)}")
            return []
    
    def parse_members_table(self, table: BeautifulSoup) -> List[Dict[str, Any]]:
        """議員テーブルを解析"""
        members = []
        
        try:
            rows = table.find_all('tr')
            
            for row_idx, row in enumerate(rows[1:], 1):  # ヘッダー行をスキップ
                cells = row.find_all(['td', 'th'])
                
                if len(cells) >= 3:  # 最低限の列数チェック
                    member_data = self.extract_member_from_row(cells, row_idx)
                    if member_data:
                        members.append(member_data)
            
        except Exception as e:
            logger.error(f"テーブル解析エラー: {str(e)}")
        
        return members
    
    def extract_member_from_row(self, cells: List, row_idx: int) -> Optional[Dict[str, Any]]:
        """行から議員データを抽出（衆議院形式対応）"""
        try:
            # 衆議院データの構造: ['氏名', 'ふりがな', '会派', '選挙区', '当選回数']
            if len(cells) < 5:
                return None
            
            # 各列のデータを抽出
            name_raw = cells[0].get_text(strip=True)
            reading = cells[1].get_text(strip=True).replace('\n', '').replace('\u3000', ' ')
            party_raw = cells[2].get_text(strip=True)
            constituency = cells[3].get_text(strip=True)
            election_count_str = cells[4].get_text(strip=True)
            
            # 名前の正規化（「君」を除去）
            name = name_raw.replace('君', '').strip()
            if not name or name == '氏名':  # ヘッダー行をスキップ
                return None
            
            # 政党名正規化
            party_normalized = self.normalize_party_name(party_raw)
            
            # 当選回数
            try:
                election_count = int(election_count_str) if election_count_str.isdigit() else 0
            except ValueError:
                election_count = 0
            
            # プロフィールリンクを抽出
            profile_url = ""
            base_url = getattr(self, 'current_member_page', self.members_url)
            for cell in cells:
                for link in cell.find_all('a', href=True):
                    href = link.get('href')
                    if href and 'profile' in href.lower():
                        profile_url = urljoin(base_url, href)
                        break
                if profile_url:
                    break
            
            # 選挙区情報の詳細解析
            constituency_info = self.extract_constituency_info(constituency)
            
            member = {
                "id": f"shugiin_{row_idx:03d}",
                "name": name,
                "reading": reading,
                "house": "shugiin",
                "party": party_normalized,
                "party_original": party_raw,
                "constituency": constituency,
                "constituency_type": constituency_info["type"],
                "region": constituency_info["region"],
                "district": constituency_info.get("district"),
                "election_count": election_count,
                "status": "active",  # 現職と仮定
                "profile_url": profile_url,
                "collected_at": datetime.now().isoformat(),
                "source_url": base_url
            }
            
            return member
            
        except Exception as e:
            logger.debug(f"行{row_idx}の解析エラー: {str(e)}")
            return None
    
    def extract_members_from_lists(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """リスト形式から議員データを抽出（フォールバック）"""
        members = []
        
        try:
            # div、ul、ol等から議員名を含む要素を探す
            member_elements = soup.find_all(['div', 'li', 'p'], string=re.compile(r'[一-龯]{2,4}[　\s]+[一-龯]{2,4}'))
            
            for idx, element in enumerate(member_elements):
                text = element.get_text(strip=True)
                
                # 議員名らしいパターンをチェック
                if '　' in text and len(text.split('　')) == 2:
                    name_parts = text.split('　')
                    if all(len(part) >= 1 for part in name_parts):
                        member = {
                            "id": f"shugiin_list_{idx:03d}",
                            "name": text,
                            "house": "shugiin",
                            "party": "未分類",
                            "party_original": "",
                            "constituency": "",
                            "constituency_type": "unknown",
                            "region": None,
                            "district": None,
                            "status": "active",
                            "profile_url": "",
                            "collected_at": datetime.now().isoformat(),
                            "source_url": self.members_url
                        }
                        members.append(member)
            
        except Exception as e:
            logger.error(f"リスト抽出エラー: {str(e)}")
        
        return members
    
    def enhance_with_profile_data(self, members: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """プロフィールページから追加情報を取得"""
        logger.info(f"プロフィール情報収集開始: {len(members)}名")
        
        enhanced_members = []
        
        for idx, member in enumerate(members):
            try:
                enhanced = member.copy()
                
                profile_url = member.get('profile_url', '')
                if profile_url:
                    self.random_delay()
                    profile_data = self.fetch_profile_data(profile_url)
                    enhanced.update(profile_data)
                
                enhanced_members.append(enhanced)
                
                # 進捗表示
                if (idx + 1) % 50 == 0:
                    logger.info(f"プロフィール収集進捗: {idx + 1}/{len(members)}")
                
            except Exception as e:
                logger.error(f"議員{member.get('name', 'unknown')}のプロフィール収集エラー: {e}")
                enhanced_members.append(member)
                continue
        
        logger.info(f"プロフィール情報収集完了: {len(enhanced_members)}名")
        return enhanced_members
    
    def fetch_profile_data(self, profile_url: str) -> Dict[str, Any]:
        """個別議員のプロフィールデータを取得"""
        profile_data = {}
        
        try:
            response = self.session.get(profile_url, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 写真URL抽出
            photo_img = soup.find('img', src=re.compile(r'photo|picture'))
            if photo_img:
                photo_src = photo_img.get('src', '')
                if photo_src.startswith('/'):
                    profile_data['photo_url'] = self.base_url + photo_src
                elif photo_src.startswith('http'):
                    profile_data['photo_url'] = photo_src
            
            # 経歴情報抽出
            career_elements = soup.find_all(string=re.compile(r'生まれ|卒業|経歴'))
            if career_elements:
                career_text = ' '.join([elem.strip() for elem in career_elements[:3]])
                profile_data['career'] = career_text[:500]  # 長すぎる場合は制限
            
            # その他の詳細情報があれば追加
            
        except Exception as e:
            logger.debug(f"プロフィール取得エラー ({profile_url}): {e}")
        
        return profile_data
    
    def save_members_data(self, members: List[Dict[str, Any]]):
        """衆議院議員データを保存"""
        if not members:
            logger.warning("保存する衆議院議員データがありません")
            return
        
        # データ期間を基準としたファイル名
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m01')
        timestamp = current_date.strftime('%H%M%S')
        
        # 衆議院専用ファイル名
        shugiin_filename = f"shugiin_legislators_{data_period}_{timestamp}.json"
        shugiin_filepath = self.raw_data_dir / shugiin_filename
        
        # 統合ファイル名（衆参統合用）
        unified_filename = f"legislators_{data_period}_{timestamp}.json"
        
        # 既存の参議院データを読み込み
        existing_sangiin = []
        existing_files = list(self.legislators_dir.glob("legislators_*.json"))
        if existing_files:
            # 最新のファイルを読み込み
            latest_file = sorted(existing_files)[-1]
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, dict) and 'data' in existing_data:
                        # 参議院データのみフィルター
                        existing_sangiin = [leg for leg in existing_data['data'] if leg.get('house') == 'sangiin']
                    elif isinstance(existing_data, list):
                        existing_sangiin = [leg for leg in existing_data if leg.get('house') == 'sangiin']
            except Exception as e:
                logger.warning(f"既存データ読み込みエラー: {e}")
        
        # 衆参統合データ
        unified_members = existing_sangiin + members
        
        # 衆議院専用データ保存
        shugiin_data = {
            "metadata": {
                "house": "shugiin",
                "data_type": "legislators",
                "total_count": len(members),
                "generated_at": current_date.isoformat(),
                "source_url": self.members_url,
                "source_attribution": "House of Representatives - Japan",
                "data_quality": "official_shugiin_data"
            },
            "data": members
        }
        
        with open(shugiin_filepath, 'w', encoding='utf-8') as f:
            json.dump(shugiin_data, f, ensure_ascii=False, indent=2)
        
        # 統合データ保存（フロントエンド用）
        unified_filepath = self.legislators_dir / unified_filename
        unified_data = {
            "metadata": {
                "data_type": "legislators_unified",
                "houses": ["shugiin", "sangiin"],
                "total_count": len(unified_members),
                "shugiin_count": len(members),
                "sangiin_count": len(existing_sangiin),
                "generated_at": current_date.isoformat(),
                "source": "unified_legislators_collection"
            },
            "data": unified_members
        }
        
        with open(unified_filepath, 'w', encoding='utf-8') as f:
            json.dump(unified_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"衆議院議員データ保存完了:")
        logger.info(f"  - 衆議院専用: {shugiin_filepath}")
        logger.info(f"  - 衆参統合: {unified_filepath}")
        logger.info(f"  - 衆議院件数: {len(members)}名")
        logger.info(f"  - 参議院件数: {len(existing_sangiin)}名")
        logger.info(f"  - 統合件数: {len(unified_members)}名")
        
        # 統計表示
        self.display_collection_stats(members)
    
    def display_collection_stats(self, members: List[Dict[str, Any]]):
        """収集統計を表示"""
        logger.info("\n📊 衆議院議員収集統計:")
        
        # 政党別集計
        party_counts = {}
        for member in members:
            party = member['party']
            party_counts[party] = party_counts.get(party, 0) + 1
        
        logger.info("政党別議員数:")
        for party, count in sorted(party_counts.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"  {party}: {count}名")
        
        # 選挙区タイプ別集計
        constituency_types = {}
        for member in members:
            const_type = member['constituency_type']
            constituency_types[const_type] = constituency_types.get(const_type, 0) + 1
        
        logger.info("\n選挙区タイプ別:")
        for const_type, count in constituency_types.items():
            logger.info(f"  {const_type}: {count}名")

def main():
    """メイン実行関数"""
    logger.info("🚀 衆議院議員データ収集開始 (Issue #16)")
    
    collector = ShugiinLegislatorsCollector()
    
    try:
        # 衆議院議員データ収集
        members = collector.collect_members_data()
        
        if not members:
            logger.error("衆議院議員データが取得できませんでした")
            return
        
        # プロフィール情報の強化
        enhanced_members = collector.enhance_with_profile_data(members)
        
        # データ保存
        collector.save_members_data(enhanced_members)
        
        logger.info("✨ 衆議院議員データ収集処理完了 (Issue #16)")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()
