#!/usr/bin/env python3
"""
委員会ニュース収集テスト（内閣委員会のみ）
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

class CommitteeNewsTest:
    """委員会ニューステスト（内閣委員会のみ）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_news_dir = self.project_root / "frontend" / "public" / "data" / "committee_news"
        self.frontend_news_dir.mkdir(parents=True, exist_ok=True)
        
        # 基本URL
        self.base_url = "https://www.shugiin.go.jp"
        self.news_base_url = "https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/News/"
        
        # 現在日時
        current_date = datetime.now()
        self.year = current_date.year
        self.week = current_date.isocalendar()[1]
        
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
    
    def test_naikaku_committee(self) -> List[Dict[str, Any]]:
        """内閣委員会ニューステスト"""
        logger.info("内閣委員会ニューステスト開始...")
        news_items = []
        
        try:
            # 内閣委員会ニュース一覧ページ
            committee_url = f"{self.news_base_url}naikaku217.htm"
            
            self.update_headers()
            time.sleep(1)
            
            response = self.session.get(committee_url, timeout=30)
            if response.status_code != 200:
                logger.error(f"委員会ページアクセス失敗: {committee_url} (Status: {response.status_code})")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 個別ニュースリンクを抽出（最初の3件のみテスト）
            news_links = self.extract_news_links(soup)[:3]
            logger.info(f"テスト用ニュースリンク: {len(news_links)}件")
            
            # 各ニュースリンクの詳細を取得
            for idx, link_info in enumerate(news_links):
                try:
                    time.sleep(1)
                    self.update_headers()
                    
                    news_detail = self.extract_news_detail(link_info)
                    if news_detail:
                        news_items.append(news_detail)
                        logger.info(f"詳細取得成功 ({idx+1}/{len(news_links)}): {news_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"個別ニュース詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"内閣委員会テストエラー: {str(e)}")
            return []
    
    def extract_news_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """個別ニュースリンクを抽出"""
        links = []
        
        try:
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 内閣委員会の個別ニュースページパターン: naikaku217YYYYMMDDNNN_m.htm
                if re.search(r'naikaku217\d{8}\d{3}_m\.htm', href):
                    # URL正規化
                    if href.startswith('./'):
                        full_url = f"{self.news_base_url}{href[2:]}"
                    elif href.startswith('/'):
                        full_url = f"{self.base_url}{href}"
                    elif not href.startswith('http'):
                        full_url = f"{self.news_base_url}{href}"
                    else:
                        full_url = href
                    
                    # 日付抽出
                    date_match = re.search(r'naikaku217(\d{4})(\d{2})(\d{2})\d{3}_m\.htm', href)
                    if date_match:
                        year, month, day = date_match.groups()
                        date = f"{year}-{month}-{day}"
                    else:
                        date = datetime.now().strftime('%Y-%m-%d')
                    
                    links.append({
                        'url': full_url,
                        'title': text or f"【内閣委員会】ニュース",
                        'committee': '内閣委員会',
                        'date': date,
                        'filename': href
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
            logger.error(f"ニュースリンク抽出エラー: {str(e)}")
            return []
    
    def extract_news_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """個別ニュースページから詳細情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ページ内容解析
            content = self.extract_content(soup)
            bill_info = self.extract_bill_info(soup)
            pdf_info = self.extract_pdf_info(soup)
            
            news_detail = {
                'title': self.generate_title(link_info, content, bill_info),
                'url': link_info['url'],
                'committee': link_info['committee'],
                'date': link_info['date'],
                'news_type': self.classify_news_type(content, bill_info, pdf_info),
                'content': self.format_content(link_info, content, bill_info, pdf_info),
                'content_length': len(content),
                'collected_at': datetime.now().isoformat(),
                'year': self.year,
                'week': self.week,
                'source': 'committee_news'
            }
            
            # 追加情報
            if bill_info:
                news_detail['bill_info'] = bill_info
            if pdf_info:
                news_detail['pdf_info'] = pdf_info
            
            return news_detail
            
        except Exception as e:
            logger.error(f"ニュース詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_content(self, soup: BeautifulSoup) -> str:
        """ページ内容を抽出"""
        try:
            # メインコンテンツから抽出
            main_content = soup.find('body') or soup
            text = main_content.get_text(separator='\n', strip=True)
            return self.clean_text(text)
        except Exception as e:
            logger.error(f"内容抽出エラー: {str(e)}")
            return ""
    
    def extract_bill_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """法案情報を抽出"""
        try:
            page_text = soup.get_text()
            
            # 法案パターンの検索
            bill_match = re.search(r'(.+?法律?案)（(.+?)）', page_text)
            if bill_match:
                return {
                    'bill_title': bill_match.group(1),
                    'bill_number': bill_match.group(2),
                    'bill_keyword': '法律案',
                    'bill_source': 'page_content'
                }
            
            # 簡易法案パターン
            simple_bill_match = re.search(r'(.+?法律?案)', page_text)
            if simple_bill_match:
                return {
                    'bill_title': simple_bill_match.group(1),
                    'bill_keyword': '法律案',
                    'bill_source': 'page_content'
                }
            
            return None
        except Exception as e:
            logger.error(f"法案情報抽出エラー: {str(e)}")
            return None
    
    def extract_pdf_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """PDF情報を抽出"""
        try:
            pdf_links = soup.find_all('a', href=lambda href: href and '.pdf' in href.lower())
            
            if pdf_links:
                pdf_link = pdf_links[0]
                href = pdf_link.get('href', '')
                title = pdf_link.get_text(strip=True)
                
                # URL正規化
                if href.startswith('./'):
                    pdf_url = f"{self.news_base_url}{href[2:]}"
                elif href.startswith('/'):
                    pdf_url = f"{self.base_url}{href}"
                elif not href.startswith('http'):
                    pdf_url = f"{self.news_base_url}{href}"
                else:
                    pdf_url = href
                
                return {
                    'pdf_url': pdf_url,
                    'pdf_title': title,
                    'original_href': href
                }
            
            return None
        except Exception as e:
            logger.error(f"PDF情報抽出エラー: {str(e)}")
            return None
    
    def generate_title(self, link_info: Dict[str, str], content: str, bill_info: Optional[Dict]) -> str:
        """タイトル生成"""
        # 法案がある場合
        if bill_info and bill_info.get('bill_title'):
            return f"【{link_info['committee']}】{bill_info['bill_title']}"
        
        # 日付ベースのタイトル
        date_parts = link_info['date'].split('-')
        if len(date_parts) == 3:
            year, month, day = date_parts
            date_str = f"令和{int(year)-2018}年{int(month)}月{int(day)}日"
        else:
            date_str = link_info['date']
        
        return f"【{link_info['committee']}】{date_str}"
    
    def classify_news_type(self, content: str, bill_info: Optional[Dict], pdf_info: Optional[Dict]) -> str:
        """ニュースタイプ分類"""
        if bill_info:
            return '法案審議'
        elif pdf_info:
            return '委員会資料'
        elif any(keyword in content.lower() for keyword in ['質疑', '質問']):
            return '質疑応答'
        else:
            return '委員会開催'
    
    def format_content(self, link_info: Dict[str, str], content: str, bill_info: Optional[Dict], pdf_info: Optional[Dict]) -> str:
        """内容フォーマット"""
        parts = []
        
        # 法案情報
        if bill_info:
            parts.append(f"議案名: {bill_info.get('bill_title', '')}")
        
        # 基本情報
        parts.append(f"委員会: {link_info['committee']}")
        parts.append(f"開催日: {link_info['date']}")
        
        if bill_info:
            parts.append(f"議案キーワード: {bill_info.get('bill_keyword', '')}")
            parts.append(f"データソース: {bill_info.get('bill_source', '')}")
        
        # PDF情報
        if pdf_info:
            parts.append("関連資料:")
            parts.append(f"- {pdf_info['pdf_title']} ({pdf_info['pdf_url']})")
        
        return '\n'.join(parts)
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # JavaScript無効メッセージの除去
        js_messages = [
            'ブラウザのJavaScriptが無効のため、サイト内検索はご利用いただけません。',
            'JavaScriptが無効です',
            'JavaScript を有効にしてください'
        ]
        
        for msg in js_messages:
            text = text.replace(msg, '')
        
        # 正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'[\u3000]+', ' ', text)
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines).strip()
    
    def save_test_data(self, news_items: List[Dict[str, Any]]):
        """テストデータ保存"""
        if not news_items:
            logger.warning("保存するテストデータがありません")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        test_filename = f"committee_news_test_{timestamp}.json"
        test_filepath = self.frontend_news_dir / test_filename
        
        with open(test_filepath, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        logger.info(f"テストデータ保存完了: {test_filepath} ({len(news_items)}件)")
        
        # 結果表示
        for item in news_items:
            print(f"\nタイトル: {item['title']}")
            print(f"URL: {item['url']}")
            print(f"日付: {item['date']}")
            print(f"タイプ: {item['news_type']}")
            if item.get('bill_info'):
                print(f"法案: {item['bill_info'].get('bill_title', 'N/A')}")
            print(f"内容: {item['content'][:100]}...")

def main():
    """テスト実行"""
    tester = CommitteeNewsTest()
    
    try:
        # 内閣委員会ニューステスト
        news_items = tester.test_naikaku_committee()
        
        # テストデータ保存
        tester.save_test_data(news_items)
        
        logger.info("委員会ニューステスト完了")
        
    except Exception as e:
        logger.error(f"テスト処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()