#!/usr/bin/env python3
"""
参議院議案データ収集スクリプト (Issue #25対応)

参議院議案ページから実際の議案データを収集
https://www.sangiin.go.jp/japanese/joho1/kousei/gian/217/gian.htm
法律案、予算案、条約案等を全て収集
"""

import json
import requests
import time
import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging
import random

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SangiinBillsCollector:
    """参議院議案データ収集クラス (Issue #25対応)"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.bills_dir = self.project_root / "data" / "processed" / "sangiin_bills"
        self.frontend_bills_dir = self.project_root / "frontend" / "public" / "data" / "bills"
        
        # ディレクトリ作成
        self.bills_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_bills_dir.mkdir(parents=True, exist_ok=True)
        
        # 基本URL（参議院）
        self.base_url = "https://www.sangiin.go.jp"
        self.bills_base_url = "https://www.sangiin.go.jp/japanese/joho1/kousei/gian/"
        
        # 収集する国会の範囲（第217回を重点的に）
        self.start_session = 217
        self.end_session = 217
        
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
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """ランダム遅延でレート制限対応"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def build_absolute_url(self, href: str, base_page_url: str) -> Optional[str]:
        """相対URLを絶対URLに変換"""
        if not href or href.strip() == '':
            return None
        
        # アンカーリンク（#で始まる）は無効
        if href.startswith('#'):
            return None
        
        # 既に絶対URLの場合
        if href.startswith('http'):
            return href
        
        # 相対URL処理
        if href.startswith('./'):
            # ./youshi/s217001y.htm → https://www.sangiin.go.jp/japanese/joho1/kousei/gian/217/youshi/s217001y.htm
            relative_path = href[2:]  # ./ を除去
            base_dir = '/'.join(base_page_url.split('/')[:-1])  # ファイル名を除去
            return f"{base_dir}/{relative_path}"
        
        elif href.startswith('/'):
            # 絶対パス
            return f"{self.base_url}{href}"
        
        else:
            # 相対パス
            base_dir = '/'.join(base_page_url.split('/')[:-1])
            return f"{base_dir}/{href}"
    
    def collect_all_bills(self) -> List[Dict[str, Any]]:
        """全国会の参議院議案を収集"""
        logger.info("参議院議案データ収集開始...")
        all_bills = []
        
        for session_number in range(self.start_session, self.end_session + 1):
            try:
                logger.info(f"第{session_number}回国会の参議院議案収集開始...")
                
                # IP偽装のためヘッダー更新
                self.update_headers()
                self.random_delay()
                
                session_bills = self.collect_session_bills(session_number)
                all_bills.extend(session_bills)
                
                logger.info(f"第{session_number}回国会: {len(session_bills)}件の参議院議案を収集")
                
            except Exception as e:
                logger.error(f"第{session_number}回国会の参議院議案収集エラー: {str(e)}")
                continue
        
        logger.info(f"参議院議案データ収集完了: {len(all_bills)}件")
        return all_bills
    
    def collect_session_bills(self, session_number: int) -> List[Dict[str, Any]]:
        """特定の国会の参議院議案を収集"""
        bills = []
        
        try:
            # 参議院国会別議案一覧ページURL
            session_url = f"{self.bills_base_url}{session_number}/gian.htm"
            
            response = self.session.get(session_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"第{session_number}回国会参議院ページ取得成功: {session_url}")
            
            # 議案セクション別に収集
            bills.extend(self.extract_houritsuann_bills(soup, session_number, session_url))  # 法律案
            bills.extend(self.extract_yosan_bills(soup, session_number, session_url))        # 予算案
            bills.extend(self.extract_joyaku_bills(soup, session_number, session_url))       # 条約案
            bills.extend(self.extract_other_bills(soup, session_number, session_url))        # その他案件
            
            return bills
            
        except Exception as e:
            logger.error(f"第{session_number}回国会の参議院議案収集エラー: {str(e)}")
            return []
    
    def extract_houritsuann_bills(self, soup: BeautifulSoup, session_number: int, session_url: str) -> List[Dict[str, Any]]:
        """法律案セクションから議案を抽出（テーブル形式対応）"""
        bills = []
        
        try:
            # 法律案セクションをテーブルベースで探す
            law_section_headers = ['法律案（内閣提出）', '法律案（衆法）', '法律案（参法）']
            
            for section_name in law_section_headers:
                # セクションヘッダーを探す
                section_header = soup.find('h2', string=re.compile(section_name))
                if section_header:
                    # ヘッダーの次にあるテーブルを探す
                    table = section_header.find_next_sibling('table')
                    if table:
                        section_bills = self.parse_bill_table(table, session_number, session_url, section_name)
                        bills.extend(section_bills)
                        logger.info(f"{section_name}: {len(section_bills)}件")
            
            # すべてのテーブルからも法律案を抽出（ヘッダーが見つからない場合のフォールバック）
            if not bills:
                logger.info("ヘッダーベースの抽出失敗、全テーブル解析にフォールバック")
                tables = soup.find_all('table')
                for i, table in enumerate(tables):
                    rows = table.find_all('tr')
                    if len(rows) > 10:  # 実質的なデータを持つテーブル
                        # ヘッダーをチェック
                        if rows and len(rows[0].find_all(['th', 'td'])) >= 3:
                            table_bills = self.parse_bill_table(table, session_number, session_url, f'法律案テーブル{i+1}')
                            bills.extend(table_bills)
                            logger.info(f"テーブル{i+1}: {len(table_bills)}件")
            
            logger.info(f"法律案セクション合計: {len(bills)}件")
            return bills
            
        except Exception as e:
            logger.error(f"法律案抽出エラー: {str(e)}")
            return []
    
    def extract_yosan_bills(self, soup: BeautifulSoup, session_number: int, session_url: str) -> List[Dict[str, Any]]:
        """予算案セクションから議案を抽出"""
        bills = []
        
        try:
            # 予算関連のセクションを探す
            yosan_section = soup.find(text=re.compile('予算'))
            if yosan_section:
                # 予算テーブルを探す
                parent = yosan_section.parent
                while parent and parent.name != 'table':
                    parent = parent.find_next_sibling()
                    if parent and parent.name == 'table':
                        bills.extend(self.parse_bill_table(parent, session_number, session_url, '予算'))
                        break
            
            logger.info(f"予算案セクション: {len(bills)}件")
            return bills
            
        except Exception as e:
            logger.error(f"予算案抽出エラー: {str(e)}")
            return []
    
    def extract_joyaku_bills(self, soup: BeautifulSoup, session_number: int, session_url: str) -> List[Dict[str, Any]]:
        """条約案セクションから議案を抽出"""
        bills = []
        
        try:
            # 条約関連のセクションを探す
            joyaku_section = soup.find(text=re.compile('条約'))
            if joyaku_section:
                # 条約テーブルを探す
                parent = joyaku_section.parent
                while parent and parent.name != 'table':
                    parent = parent.find_next_sibling()
                    if parent and parent.name == 'table':
                        bills.extend(self.parse_bill_table(parent, session_number, session_url, '条約'))
                        break
            
            logger.info(f"条約案セクション: {len(bills)}件")
            return bills
            
        except Exception as e:
            logger.error(f"条約案抽出エラー: {str(e)}")
            return []
    
    def extract_other_bills(self, soup: BeautifulSoup, session_number: int, session_url: str) -> List[Dict[str, Any]]:
        """その他案件セクションから議案を抽出"""
        bills = []
        
        try:
            # その他の案件（決議案、人事案件等）
            other_keywords = ['決議案', '人事案件', '規則案', '規程案', '承認', '承諾']
            
            for keyword in other_keywords:
                section = soup.find(text=re.compile(keyword))
                if section:
                    parent = section.parent
                    while parent and parent.name != 'table':
                        parent = parent.find_next_sibling()
                        if parent and parent.name == 'table':
                            bills.extend(self.parse_bill_table(parent, session_number, session_url, keyword))
                            break
            
            logger.info(f"その他案件セクション: {len(bills)}件")
            return bills
            
        except Exception as e:
            logger.error(f"その他案件抽出エラー: {str(e)}")
            return []
    
    def parse_bill_table(self, table: BeautifulSoup, session_number: int, session_url: str, bill_type: str) -> List[Dict[str, Any]]:
        """議案テーブルを解析（参議院形式対応）"""
        bills = []
        
        try:
            rows = table.find_all('tr')
            logger.info(f"テーブル解析開始: {len(rows)}行")
            
            for row_idx, row in enumerate(rows[1:]):  # ヘッダー行をスキップ
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 3:  # 提出回次、提出番号、件名の3列
                    
                    # 議案情報を抽出（参議院形式：提出回次、提出番号、件名）
                    submission_session = cells[0].get_text(strip=True) if len(cells) > 0 else ""
                    bill_number = cells[1].get_text(strip=True) if len(cells) > 1 else ""
                    bill_title = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    
                    # リンクを抽出
                    links = []
                    for cell in cells:
                        for link in cell.find_all('a', href=True):
                            href = link.get('href')
                            link_text = link.get_text(strip=True)
                            full_url = self.build_absolute_url(href, session_url)
                            
                            if full_url:
                                links.append({
                                    'url': full_url,
                                    'title': link_text if link_text else self.classify_link_type_from_url(href),
                                    'type': self.classify_link_type_from_url(href)
                                })
                    
                    if bill_title and bill_title != '' and bill_title != '件名':  # ヘッダー行除外
                        bill_detail = {
                            'title': bill_title,
                            'bill_number': bill_number,
                            'submission_session': submission_session,
                            'bill_type': bill_type,
                            'session_number': session_number,
                            'house': '参議院',
                            'submitter': self.extract_submitter_from_type(bill_type, bill_number),
                            'links': links,
                            'collected_at': datetime.now().isoformat(),
                            'source_url': session_url
                        }
                        
                        bills.append(bill_detail)
                        logger.debug(f"議案追加: {bill_title[:30]}... ({len(links)}リンク)")
            
            logger.info(f"テーブル解析完了: {len(bills)}件の議案を抽出")
            return bills
            
        except Exception as e:
            logger.error(f"議案テーブル解析エラー: {str(e)}")
            return []
    
    def classify_link_type(self, link_text: str, href: str) -> str:
        """リンクの種類を分類"""
        if '要旨' in link_text:
            return '議案要旨'
        elif 'PDF' in link_text or '.pdf' in href.lower():
            return 'PDF文書'
        elif '経過' in link_text:
            return '審議経過'
        elif '本文' in link_text:
            return '議案本文'
        else:
            return '関連文書'
    
    def classify_link_type_from_url(self, href: str) -> str:
        """URLから リンクの種類を分類"""
        if not href:
            return '不明'
        
        # PDF文書
        if '.pdf' in href.lower():
            if 't0' in href:  # t0XXXXXXXパターン
                return '議案本文PDF'
            elif 's' in href:  # sXXXXXXXパターン
                return '審議資料PDF'
            else:
                return 'PDF文書'
        
        # 詳細ページ
        elif '/meisai/' in href:
            return '議案詳細'
        
        # その他
        elif '.htm' in href.lower():
            return 'HTML文書'
        
        else:
            return '関連文書'
    
    def extract_bills_from_section(self, header, session_number: int, session_url: str, section_name: str) -> List[Dict[str, Any]]:
        """セクションから議案を抽出する汎用メソッド"""
        bills = []
        
        try:
            # ヘッダーの次の要素から議案リストを探す
            current = header
            max_siblings = 20  # 無限ループ防止
            sibling_count = 0
            
            while current and sibling_count < max_siblings:
                current = current.find_next_sibling()
                sibling_count += 1
                
                if not current:
                    break
                
                # 次のセクションヘッダーに到達したら停止
                if current.name in ['h1', 'h2', 'h3'] and '法律案' in current.get_text():
                    break
                
                # リンクを含む要素を探す
                links = current.find_all('a', href=True)
                for link in links:
                    href = link.get('href')
                    link_text = link.get_text(strip=True)
                    
                    # 議案関連のリンクかチェック
                    if self.is_bill_related_link(link_text, href):
                        full_url = self.build_absolute_url(href, session_url)
                        if full_url:
                            # 議案情報を構築
                            bill_info = {
                                'title': link_text,
                                'bill_number': self.extract_bill_number_from_text(link_text),
                                'bill_type': section_name,
                                'session_number': session_number,
                                'house': '参議院',
                                'submitter': self.extract_submitter_from_section(section_name),
                                'url': full_url,
                                'link_type': self.classify_link_type(link_text, href),
                                'collected_at': datetime.now().isoformat(),
                                'source_url': session_url
                            }
                            bills.append(bill_info)
            
            return bills
            
        except Exception as e:
            logger.error(f"セクション抽出エラー ({section_name}): {str(e)}")
            return []
    
    def is_bill_related_link(self, link_text: str, href: str) -> bool:
        """議案関連のリンクかどうか判定"""
        # 議案関連キーワード
        bill_keywords = ['法律案', '議案', '要旨', '法案', '改正', '設置', '廃止']
        
        # 無関係なリンクを除外
        exclude_keywords = ['トップページ', 'サイトマップ', 'ヘルプ', '読み上げ']
        
        # 除外キーワードチェック
        if any(keyword in link_text for keyword in exclude_keywords):
            return False
        
        # 議案関連キーワードチェック
        return any(keyword in link_text for keyword in bill_keywords) or '.pdf' in href.lower()
    
    def extract_bill_number_from_text(self, text: str) -> str:
        """テキストから議案番号を抽出"""
        # 番号パターンを探す
        patterns = [
            r'第(\d+)号',
            r'(\d+)号',
            r'第(\d+)',
            r'令和\d+年.*第(\d+)号'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        return ""
    
    def extract_submitter_from_section(self, section_name: str) -> str:
        """セクション名から提出者を推定"""
        if '内閣提出' in section_name:
            return '内閣'
        elif '衆法' in section_name:
            return '衆議院'
        elif '参法' in section_name:
            return '参議院'
        else:
            return '不明'
    
    def extract_submitter_from_type(self, bill_type: str, bill_number: str) -> str:
        """議案種別から提出者を推定"""
        if '内閣' in bill_number or bill_type == '法律案':
            return '内閣'
        elif '衆法' in bill_number:
            return '衆議院'
        elif '参法' in bill_number:
            return '参議院'
        elif bill_type == '予算':
            return '内閣'
        elif bill_type == '条約':
            return '内閣'
        else:
            return '不明'
    
    def save_bills_data(self, bills: List[Dict[str, Any]]):
        """参議院議案データを保存"""
        if not bills:
            logger.warning("保存する参議院議案データがありません")
            return
        
        # データ期間を基準としたファイル名（現在の年月 + 時刻）
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m01')  # 当月のデータとして保存
        timestamp = current_date.strftime('%H%M%S')
        
        # 参議院専用ファイル名
        raw_filename = f"sangiin_bills_{data_period}_{timestamp}.json"
        raw_filepath = self.bills_dir / raw_filename
        
        # 統合ファイル名（衆参統合用）
        unified_filename = f"bills_{data_period}_{timestamp}.json"
        
        # 既存の衆議院データを読み込み
        existing_bills = []
        existing_files = list(self.frontend_bills_dir.glob("bills_*.json"))
        if existing_files:
            # 最新のファイルを読み込み
            latest_file = sorted(existing_files)[-1]
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                    if isinstance(existing_data, list):
                        existing_bills = existing_data
                    elif isinstance(existing_data, dict) and 'data' in existing_data:
                        existing_bills = existing_data['data']
            except Exception as e:
                logger.warning(f"既存データ読み込みエラー: {e}")
        
        # 衆参統合データ
        unified_bills = existing_bills + bills
        
        # 参議院専用データ保存
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(bills, f, ensure_ascii=False, indent=2)
        
        # 統合データ保存（フロントエンド用）
        unified_filepath = self.frontend_bills_dir / unified_filename
        with open(unified_filepath, 'w', encoding='utf-8') as f:
            json.dump(unified_bills, f, ensure_ascii=False, indent=2)
        
        logger.info(f"参議院議案データ保存完了:")
        logger.info(f"  - 参議院専用: {raw_filepath}")
        logger.info(f"  - 衆参統合: {unified_filepath}")
        logger.info(f"  - 参議院件数: {len(bills)}")
        logger.info(f"  - 統合件数: {len(unified_bills)}")

def main():
    """メイン実行関数"""
    collector = SangiinBillsCollector()
    
    try:
        # 参議院議案データ収集
        bills = collector.collect_all_bills()
        
        # データ保存
        collector.save_bills_data(bills)
        
        logger.info("参議院議案データ収集処理完了")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()