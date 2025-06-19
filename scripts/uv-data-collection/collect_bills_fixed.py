#!/usr/bin/env python3
"""
議案データ収集スクリプト（正式版）

衆議院議案ページから実際の議案データを収集
https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/kaiji217.htm
経過情報、本文、議案件名を全ての国会から取得
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

class BillsCollector:
    """議案データ収集クラス（正式版）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.bills_dir = self.project_root / "data" / "processed" / "bills"
        self.frontend_bills_dir = self.project_root / "frontend" / "public" / "data" / "bills"
        
        # ディレクトリ作成
        self.bills_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_bills_dir.mkdir(parents=True, exist_ok=True)
        
        # 週次ディレクトリ作成
        current_date = datetime.now()
        self.year = current_date.year
        self.week = current_date.isocalendar()[1]
        
        # 基本URL（正式版）
        self.base_url = "https://www.shugiin.go.jp"
        self.bills_base_url = "https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/"
        
        # 収集する国会の範囲（第200回〜最新）
        self.start_session = 200
        self.end_session = 220  # 現在の第217回＋予備
        
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
    
    def collect_all_bills(self) -> List[Dict[str, Any]]:
        """全国会の議案を収集"""
        logger.info("全議案データ収集開始...")
        all_bills = []
        
        for session_number in range(self.start_session, self.end_session + 1):
            try:
                logger.info(f"第{session_number}回国会の議案収集開始...")
                
                # IP偽装のためヘッダー更新
                self.update_headers()
                self.random_delay()
                
                session_bills = self.collect_session_bills(session_number)
                all_bills.extend(session_bills)
                
                logger.info(f"第{session_number}回国会: {len(session_bills)}件の議案を収集")
                
            except Exception as e:
                logger.error(f"第{session_number}回国会の議案収集エラー: {str(e)}")
                continue
        
        logger.info(f"全議案データ収集完了: {len(all_bills)}件")
        return all_bills
    
    def collect_session_bills(self, session_number: int) -> List[Dict[str, Any]]:
        """特定の国会の議案を収集"""
        bills = []
        
        try:
            # 国会別議案一覧ページURL
            session_url = f"{self.bills_base_url}kaiji{session_number}.htm"
            
            response = self.session.get(session_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"第{session_number}回国会ページ取得成功: {session_url}")
            
            # 議案リンクを抽出
            bill_links = self.extract_bill_links(soup, session_number)
            logger.info(f"発見した議案リンク数: {len(bill_links)}")
            
            # 各議案の詳細を取得
            for idx, link_info in enumerate(bill_links):
                try:
                    self.random_delay()  # IP偽装のための遅延
                    self.update_headers()  # User-Agent更新
                    
                    bill_detail = self.extract_bill_detail(link_info, session_number)
                    if bill_detail:
                        bills.append(bill_detail)
                        logger.info(f"議案詳細取得成功 ({idx+1}/{len(bill_links)}): {bill_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"議案詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            return bills
            
        except Exception as e:
            logger.error(f"第{session_number}回国会の議案収集エラー: {str(e)}")
            return []
    
    def extract_bill_links(self, soup: BeautifulSoup, session_number: int) -> List[Dict[str, str]]:
        """議案リンクを抽出"""
        links = []
        
        try:
            # 議案リンクパターンを探す
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 議案関連のリンクを判定
                if self.is_bill_link(href, text):
                    full_url = self.base_url + href if href.startswith('/') else href
                    bill_number = self.extract_bill_number(text, href)
                    
                    links.append({
                        'url': full_url,
                        'title': text,
                        'bill_number': bill_number,
                        'session_number': session_number
                    })
            
            # 重複除去
            unique_links = []
            seen_urls = set()
            for link in links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            return unique_links
            
        except Exception as e:
            logger.error(f"議案リンク抽出エラー: {str(e)}")
            return []
    
    def is_bill_link(self, href: str, text: str) -> bool:
        """議案リンクかどうか判定"""
        # 議案関連キーワード
        bill_keywords = [
            '法案', '議案', '法律', '法', '条例',
            '改正', '設置', '廃止', '案'
        ]
        
        # URL パターン
        url_patterns = [
            'itdb_gian', 'gian', 'bill',
            'houan', 'hou'
        ]
        
        # テキストに議案キーワードが含まれるかチェック
        text_match = any(keyword in text for keyword in bill_keywords)
        
        # URLに関連パターンが含まれるかチェック
        url_match = any(pattern in href.lower() for pattern in url_patterns)
        
        return text_match or url_match
    
    def extract_bill_number(self, text: str, href: str) -> str:
        """議案番号を抽出"""
        # テキストから番号を抽出
        text_number_patterns = [
            r'第(\d+)号',
            r'(\d+)号',
            r'第(\d+)',
            r'(\d+)'
        ]
        
        for pattern in text_number_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # URLから番号を抽出
        url_number_match = re.search(r'(\d+)', href)
        if url_number_match:
            return url_number_match.group(1)
        
        return ""
    
    def extract_bill_detail(self, link_info: Dict[str, str], session_number: int) -> Optional[Dict[str, Any]]:
        """議案詳細ページから情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 議案情報を解析
            bill_content = self.extract_bill_content(soup)
            progress_info = self.extract_progress_info(soup)
            submitter = self.extract_submitter(soup)
            submission_date = self.extract_submission_date(soup)
            status = self.extract_status(soup)
            committee = self.extract_committee(soup)
            
            # 関連リンクを抽出
            related_links = self.extract_related_links(soup)
            
            bill_detail = {
                'title': link_info['title'],
                'bill_number': link_info['bill_number'],
                'session_number': session_number,
                'url': link_info['url'],
                'submitter': submitter,
                'submission_date': submission_date,
                'status': status,
                'status_normalized': self.normalize_status(status),
                'committee': committee,
                'bill_content': bill_content,
                'progress_info': progress_info,
                'related_links': related_links,
                'summary': self.generate_summary(bill_content),
                'collected_at': datetime.now().isoformat(),
                'year': self.year
            }
            
            return bill_detail
            
        except Exception as e:
            logger.error(f"議案詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_bill_content(self, soup: BeautifulSoup) -> str:
        """議案本文を抽出"""
        try:
            # 本文を抽出する複数の方法を試す
            content_selectors = [
                'div.honbun',
                'div.content',
                'div.main',
                'table',
                'body'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    text = content_elem.get_text(separator='\n', strip=True)
                    if len(text) > 100:  # 短すぎるテキストは除外
                        return self.clean_text(text)
            
            # フォールバック: body全体から抽出
            return self.clean_text(soup.get_text(separator='\n', strip=True))
            
        except Exception as e:
            logger.error(f"議案本文抽出エラー: {str(e)}")
            return ""
    
    def extract_progress_info(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """経過情報を抽出"""
        progress = []
        
        try:
            # 経過情報テーブルを探す
            progress_keywords = ['経過', '審議状況', '進行状況', '議事']
            
            for keyword in progress_keywords:
                tables = soup.find_all('table')
                for table in tables:
                    table_text = table.get_text()
                    if keyword in table_text:
                        rows = table.find_all('tr')
                        for row in rows:
                            cells = row.find_all(['td', 'th'])
                            if len(cells) >= 2:
                                date = cells[0].get_text(strip=True)
                                action = cells[1].get_text(strip=True)
                                if date and action and len(action) > 5:
                                    progress.append({
                                        'date': date,
                                        'action': action
                                    })
            
        except Exception as e:
            logger.error(f"経過情報抽出エラー: {str(e)}")
        
        return progress
    
    def extract_submitter(self, soup: BeautifulSoup) -> str:
        """提出者を抽出"""
        try:
            submitter_patterns = [
                r'提出者[：:]\s*([^\n\r]+)',
                r'提出[：:]\s*([^\n\r]+)',
                r'([^\n\r]+)提出'
            ]
            
            page_text = soup.get_text()
            
            for pattern in submitter_patterns:
                match = re.search(pattern, page_text)
                if match:
                    return match.group(1).strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"提出者抽出エラー: {str(e)}")
            return ""
    
    def extract_submission_date(self, soup: BeautifulSoup) -> str:
        """提出日を抽出"""
        try:
            date_patterns = [
                r'提出日[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})年(\d{1,2})月(\d{1,2})日提出'
            ]
            
            page_text = soup.get_text()
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return ""
            
        except Exception as e:
            logger.error(f"提出日抽出エラー: {str(e)}")
            return ""
    
    def extract_status(self, soup: BeautifulSoup) -> str:
        """議案状況を抽出"""
        try:
            status_keywords = ['可決', '否決', '廃案', '継続審議', '成立', '審議中']
            page_text = soup.get_text()
            
            for keyword in status_keywords:
                if keyword in page_text:
                    return keyword
            
            return "審議中"
            
        except Exception as e:
            logger.error(f"議案状況抽出エラー: {str(e)}")
            return "不明"
    
    def normalize_status(self, status: str) -> str:
        """議案状況を正規化"""
        status_mapping = {
            '可決': '可決',
            '成立': '成立',
            '否決': '否決',
            '廃案': '廃案',
            '継続審議': '継続審議',
            '審議中': '審議中'
        }
        
        return status_mapping.get(status, '不明')
    
    def extract_committee(self, soup: BeautifulSoup) -> str:
        """委員会名を抽出"""
        try:
            committee_patterns = [
                r'([^委員会]*委員会)',
                r'([^調査会]*調査会)'
            ]
            
            page_text = soup.get_text()
            
            for pattern in committee_patterns:
                match = re.search(pattern, page_text)
                if match:
                    return match.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"委員会名抽出エラー: {str(e)}")
            return ""
    
    def extract_related_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """関連リンクを抽出"""
        links = []
        
        try:
            # PDFや関連文書のリンクを探す
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 関連文書のリンクを判定
                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.html']):
                    full_url = self.base_url + href if href.startswith('/') else href
                    links.append({
                        'url': full_url,
                        'title': text or '関連文書'
                    })
            
        except Exception as e:
            logger.error(f"関連リンク抽出エラー: {str(e)}")
        
        return links
    
    def generate_summary(self, content: str) -> str:
        """議案サマリーを生成"""
        try:
            if not content:
                return ""
            
            # 最初の200文字を要約として使用
            summary = content[:200]
            if len(content) > 200:
                summary += "..."
            
            return summary
            
        except Exception as e:
            logger.error(f"サマリー生成エラー: {str(e)}")
            return ""
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # 改行・スペースの正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 連続空行を2行まで
        text = re.sub(r'[ \t]+', ' ', text)  # 連続スペースを1つに
        text = re.sub(r'[\u3000]+', ' ', text)  # 全角スペースを半角に
        
        return text.strip()
    
    def save_bills_data(self, bills: List[Dict[str, Any]]):
        """議案データを保存"""
        if not bills:
            logger.warning("保存する議案データがありません")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生データ保存
        raw_filename = f"bills_{timestamp}.json"
        raw_filepath = self.bills_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(bills, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"bills_{timestamp}.json"
        frontend_filepath = self.frontend_bills_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(bills, f, ensure_ascii=False, indent=2)
        
        logger.info(f"議案データ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 件数: {len(bills)}")

def main():
    """メイン実行関数"""
    collector = BillsCollector()
    
    try:
        # 全議案データ収集
        bills = collector.collect_all_bills()
        
        # データ保存
        collector.save_bills_data(bills)
        
        logger.info("議案データ収集処理完了")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()