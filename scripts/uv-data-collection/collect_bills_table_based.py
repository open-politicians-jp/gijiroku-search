#!/usr/bin/env python3
"""
提出法案収集スクリプト（テーブルベース版）

衆議院議案データベースのテーブル構造に基づいた効率的な収集
https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/kaiji217.htm
実際のテーブル構造を解析して正確なデータを取得
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
from urllib.parse import urljoin

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BillsTableCollector:
    """提出法案収集クラス（テーブルベース版）"""
    
    def __init__(self, max_bills: int = 50):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 収集パラメータ
        self.max_bills = max_bills
        
        # 対象となる国会回次
        self.target_sessions = [217, 216, 215]
        
        logger.info(f"最大収集件数: {self.max_bills}件")
        logger.info(f"対象国会: {', '.join(f'第{s}回' for s in self.target_sessions)}")
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.bills_dir = self.project_root / "data" / "processed" / "bills"
        self.frontend_bills_dir = self.project_root / "frontend" / "public" / "data" / "bills"
        
        # ディレクトリ作成
        self.bills_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_bills_dir.mkdir(parents=True, exist_ok=True)
        
        # 基本URL設定
        self.base_url = "https://www.shugiin.go.jp"
        
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
        
        # 相対URL処理
        if href.startswith('./'):
            # ./keika/1DDDDAA.htm -> https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/keika/1DDDDAA.htm
            relative_path = href[2:]
            base_dir = '/'.join(base_page_url.split('/')[:-1])
            return f"{base_dir}/{relative_path}"
        
        elif href.startswith('/'):
            # 絶対パス
            return f"{self.base_url}{href}"
        
        else:
            # 相対パス
            base_dir = '/'.join(base_page_url.split('/')[:-1])
            return f"{base_dir}/{href}"
    
    def collect_bills_from_session(self, session_number: int) -> List[Dict[str, Any]]:
        """特定の国会からテーブルベースで議案を収集"""
        bills = []
        
        try:
            # 国会別議案一覧ページURL
            session_url = f"{self.base_url}/internet/itdb_gian.nsf/html/gian/kaiji{session_number}.htm"
            
            self.update_headers()
            self.random_delay()
            
            response = self.session.get(session_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"第{session_number}回国会ページ取得成功: {session_url}")
            
            # テーブル行を抽出
            table_rows = self.extract_table_rows(soup)
            logger.info(f"発見したテーブル行数: {len(table_rows)}")
            
            # 各行から議案情報を抽出
            collected_count = 0
            for idx, row in enumerate(table_rows):
                if collected_count >= self.max_bills // len(self.target_sessions):
                    logger.info(f"第{session_number}回国会の収集上限に到達")
                    break
                
                try:
                    bill_info = self.extract_bill_from_row(row, session_url, session_number)
                    if bill_info and self.validate_bill_data(bill_info):
                        bills.append(bill_info)
                        collected_count += 1
                        logger.info(f"議案取得成功 ({collected_count}): {bill_info['title'][:50]}...")
                    
                except Exception as e:
                        logger.error(f"行の解析エラー ({idx+1}): {str(e)}")
                        continue
            
            return bills
            
        except Exception as e:
            logger.error(f"第{session_number}回国会の議案収集エラー: {str(e)}")
            return []
    
    def extract_table_rows(self, soup: BeautifulSoup) -> List:
        """テーブル行を抽出"""
        try:
            # trタグでテーブル行を検索
            rows = soup.find_all('tr', {'valign': 'top'})
            
            # データが含まれる行のみをフィルタリング
            valid_rows = []
            for row in rows:
                cells = row.find_all('td')
                if len(cells) >= 6:  # 6列（回次、番号、タイトル、状況、経過、本文）
                    # 最初のセルが数字（国会回次）かチェック
                    first_cell_text = cells[0].get_text(strip=True)
                    if first_cell_text.isdigit():
                        valid_rows.append(row)
            
            logger.info(f"有効なテーブル行: {len(valid_rows)}件")
            return valid_rows
            
        except Exception as e:
            logger.error(f"テーブル行抽出エラー: {str(e)}")
            return []
    
    def extract_bill_from_row(self, row, base_url: str, session_number: int) -> Optional[Dict[str, Any]]:
        """テーブル行から議案情報を抽出"""
        try:
            cells = row.find_all('td')
            if len(cells) < 6:
                return None
            
            # セルから情報を抽出
            # cells[0]: 国会回次
            # cells[1]: 議案番号
            # cells[2]: 議案名
            # cells[3]: 状況
            # cells[4]: 経過リンク
            # cells[5]: 本文リンク
            
            diet_session = cells[0].get_text(strip=True)
            bill_number = cells[1].get_text(strip=True)
            title = cells[2].get_text(strip=True)
            status = cells[3].get_text(strip=True)
            
            # 経過リンクを取得
            progress_link = None
            progress_a = cells[4].find('a')
            if progress_a and progress_a.get('href'):
                progress_link = self.build_absolute_url(progress_a.get('href'), base_url)
            
            # 本文リンクを取得
            content_link = None
            content_a = cells[5].find('a')
            if content_a and content_a.get('href'):
                content_link = self.build_absolute_url(content_a.get('href'), base_url)
            
            # データ検証
            if not title or len(title) < 5:
                return None
            
            # 議案情報を構築
            bill_info = {
                'title': title,
                'bill_number': bill_number,
                'session_number': int(diet_session) if diet_session.isdigit() else session_number,
                'url': content_link or progress_link,
                'content_url': content_link,
                'progress_url': progress_link,
                'submitter': self.infer_submitter(title),
                'submission_date': '',  # テーブルには含まれていない
                'status': status,
                'status_normalized': self.normalize_status(status),
                'committee': '',  # テーブルには含まれていない
                'bill_content': '',  # 後で本文リンクから取得可能
                'related_links': [
                    {'url': content_link, 'title': '本文'} if content_link else None,
                    {'url': progress_link, 'title': '経過'} if progress_link else None
                ],
                'summary': self.generate_summary(title),
                'category': self.classify_bill_category(title),
                'collected_at': datetime.now().isoformat(),
                'year': datetime.now().year
            }
            
            # Noneを除去
            bill_info['related_links'] = [link for link in bill_info['related_links'] if link]
            
            return bill_info
            
        except Exception as e:
            logger.error(f"行からの議案抽出エラー: {str(e)}")
            return None
    
    def infer_submitter(self, title: str) -> str:
        """議案タイトルから提出者を推測"""
        # 一般的に内閣提出法案が多い
        if any(keyword in title for keyword in ['税', '予算', '行政', '改正', '設置', '廃止']):
            return '内閣'
        else:
            return '議員'
    
    def normalize_status(self, status: str) -> str:
        """議案状況を正規化"""
        status_mapping = {
            '可決': '可決',
            '成立': '成立',
            '否決': '否決',
            '廃案': '廃案',
            '撤回': '撤回',
            '継続審議': '継続審議',
            '審議中': '審議中',
            '衆議院で審議中': '審議中',
            '参議院で審議中': '審議中',
            '衆議院で閉会中審査': '継続審議',
            '参議院で閉会中審査': '継続審議'
        }
        
        for key, value in status_mapping.items():
            if key in status:
                return value
        
        return '不明'
    
    def generate_summary(self, title: str) -> str:
        """議案サマリーを生成"""
        try:
            if len(title) > 100:
                return title[:100] + "..."
            else:
                return title
            
        except Exception as e:
            logger.error(f"サマリー生成エラー: {str(e)}")
            return title
    
    def classify_bill_category(self, title: str) -> str:
        """議案カテゴリを分類"""
        categories = {
            '外交・安全保障': ['外交', '条約', '防衛', '自衛隊', '安全保障', '日米'],
            '経済・財政': ['経済', '財政', '予算', '税制', '金融', '産業', '税', '関税'],
            '社会保障': ['年金', '医療', '介護', '福祉', '社会保障', '健康保険'],
            '教育・文化': ['教育', '学校', '大学', '文化', '文部科学', 'スポーツ'],
            '環境・エネルギー': ['環境', 'エネルギー', '原子力', '再生可能', '気候'],
            '労働・雇用': ['労働', '雇用', '働き方', '賃金', '職業'],
            '司法・行政': ['司法', '行政', '公務員', '裁判', '法務', '手続'],
            '地方・都市': ['地方', '自治体', '都市', '市町村', '地域'],
            '交通・国土': ['交通', '道路', '国土', '鉄道', '航空', '港湾'],
            'デジタル・IT': ['デジタル', 'IT', '情報', 'マイナンバー', '番号']
        }
        
        title_lower = title.lower()
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return '一般'
    
    def validate_bill_data(self, bill: Dict[str, Any]) -> bool:
        """議案データの妥当性をチェック"""
        # 必須フィールドのチェック
        if not bill.get('title') or not bill.get('bill_number'):
            return False
        
        # タイトルが意味のあるものかチェック
        title = bill.get('title', '')
        if len(title) < 5:
            return False
        
        # URLの妥当性チェック（少なくとも1つは必要）
        if not bill.get('url') and not bill.get('content_url') and not bill.get('progress_url'):
            return False
        
        return True
    
    def collect_all_bills(self) -> List[Dict[str, Any]]:
        """すべての議案を収集"""
        logger.info("提出法案収集開始...")
        all_bills = []
        seen_bills = set()  # 重複チェック用
        
        try:
            for session in self.target_sessions:
                if len(all_bills) >= self.max_bills:
                    logger.info(f"最大収集件数({self.max_bills})に到達しました")
                    break
                
                session_bills = self.collect_bills_from_session(session)
                
                # 重複除去処理
                unique_bills = []
                for bill in session_bills:
                    # 法案の一意性を判定するキー（タイトル + 法案番号）
                    bill_key = f"{bill.get('title', '')}#{bill.get('bill_number', '')}#{bill.get('submitter', '')}"
                    
                    if bill_key not in seen_bills:
                        seen_bills.add(bill_key)
                        unique_bills.append(bill)
                    else:
                        logger.debug(f"重複法案をスキップ: {bill.get('title', '')[:50]}...")
                
                all_bills.extend(unique_bills)
                logger.info(f"第{session}回国会から{len(unique_bills)}件の議案を収集（重複除去後）")
            
            logger.info(f"提出法案収集完了: {len(all_bills)}件（重複除去済み）")
            return all_bills
            
        except Exception as e:
            logger.error(f"提出法案収集エラー: {str(e)}")
            return []
    
    def save_bills_data(self, bills: List[Dict[str, Any]]):
        """議案データを保存"""
        if not bills:
            logger.warning("保存する議案データがありません")
            return
        
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m%d')
        timestamp = current_date.strftime('%H%M%S')
        
        data_structure = {
            "metadata": {
                "data_type": "shugiin_bills_table_based",
                "collection_method": "table_extraction",
                "total_bills": len(bills),
                "generated_at": current_date.isoformat(),
                "source_site": "www.shugiin.go.jp",
                "target_sessions": self.target_sessions,
                "data_quality": "table_based_collection",
                "version": "3.0"
            },
            "data": bills
        }
        
        # 生データ保存
        raw_filename = f"bills_{data_period}_{timestamp}.json"
        raw_filepath = self.bills_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"bills_{data_period}_{timestamp}.json"
        frontend_filepath = self.frontend_bills_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        
        # 最新ファイル更新
        latest_file = self.frontend_bills_dir / "bills_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        logger.info(f"📁 最新ファイル更新: {latest_file}")
        
        logger.info(f"議案データ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 件数: {len(bills)}")
        
        # データ品質レポート
        logger.info("データ品質レポート:")
        logger.info(f"  - 有効URL付き議案: {sum(1 for b in bills if b.get('url'))}件")
        logger.info(f"  - 本文リンク付き議案: {sum(1 for b in bills if b.get('content_url'))}件")
        logger.info(f"  - 経過リンク付き議案: {sum(1 for b in bills if b.get('progress_url'))}件")

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='提出法案収集スクリプト（テーブルベース版）')
    parser.add_argument('--max-bills', type=int, default=50, help='最大収集件数 (デフォルト: 50件)')
    
    args = parser.parse_args()
    
    collector = BillsTableCollector(max_bills=args.max_bills)
    
    try:
        # 提出法案収集
        bills = collector.collect_all_bills()
        
        if bills:
            # データ保存
            collector.save_bills_data(bills)
            logger.info(f"新規提出法案収集完了: {len(bills)}件")
        else:
            logger.info("新規提出法案は見つかりませんでした")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()