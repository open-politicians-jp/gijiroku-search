#!/usr/bin/env python3
"""
委員会ニュース収集スクリプト（正式版）

衆議院委員会ニュースページから実際の委員会活動を収集
https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/IinkaiNews_m.htm
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

class CommitteeNewsCollector:
    """委員会ニュース収集クラス（正式版）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.news_dir = self.project_root / "data" / "processed" / "committee_news"
        self.frontend_news_dir = self.project_root / "frontend" / "public" / "data" / "committee_news"
        
        # ディレクトリ作成
        self.news_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_news_dir.mkdir(parents=True, exist_ok=True)
        
        # 週次ディレクトリ作成
        current_date = datetime.now()
        self.year = current_date.year
        self.week = current_date.isocalendar()[1]
        
        # 基本URL（正式版）
        self.base_url = "https://www.shugiin.go.jp"
        self.news_main_url = "https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/IinkaiNews_m.htm"
        
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
    
    def collect_committee_news(self) -> List[Dict[str, Any]]:
        """委員会ニュース収集（メインページから）"""
        logger.info("委員会ニュース収集開始...")
        news_items = []
        
        try:
            # IP偽装のためヘッダー更新
            self.update_headers()
            self.random_delay()
            
            # メインページ取得
            response = self.session.get(self.news_main_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"メインページ取得成功: {self.news_main_url}")
            
            # 委員会ニュースのリンクを探す
            news_links = self.extract_news_links(soup)
            logger.info(f"発見したニュースリンク数: {len(news_links)}")
            
            # 各ニュースリンクの詳細を取得
            for idx, link_info in enumerate(news_links):
                try:
                    self.random_delay()  # IP偽装のための遅延
                    self.update_headers()  # User-Agent更新
                    
                    news_detail = self.extract_news_detail(link_info)
                    if news_detail:
                        news_items.append(news_detail)
                        logger.info(f"ニュース詳細取得成功 ({idx+1}/{len(news_links)}): {news_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"ニュース詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            logger.info(f"委員会ニュース収集完了: {len(news_items)}件")
            return news_items
            
        except Exception as e:
            logger.error(f"委員会ニュース収集エラー: {str(e)}")
            return []
    
    def extract_news_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """メインページからニュースリンクを抽出"""
        links = []
        
        try:
            # 委員会ニュースのリンクパターンを探す
            # 一般的に「〇〇委員会」や「特別委員会」などのリンクを探す
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 委員会関連のリンクを判定
                if self.is_committee_news_link(href, text):
                    # 相対URLの処理を修正
                    if href.startswith('./'):
                        full_url = "https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/" + href[2:]
                    elif href.startswith('/'):
                        full_url = self.base_url + href
                    elif not href.startswith('http'):
                        full_url = "https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/" + href
                    else:
                        full_url = href
                    links.append({
                        'url': full_url,
                        'title': text,
                        'committee': self.extract_committee_name(text)
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
    
    def is_committee_news_link(self, href: str, text: str) -> bool:
        """委員会ニュースリンクかどうか判定"""
        # 委員会関連キーワード
        committee_keywords = [
            '委員会', 'committee', 'iinkai', 
            '特別委員会', '常任委員会', '調査会'
        ]
        
        # URL パターン
        url_patterns = [
            'itdb_rchome', 'itdb_iinkai', 'committee', 
            'news', 'ニュース'
        ]
        
        # テキストに委員会キーワードが含まれるかチェック
        text_match = any(keyword in text for keyword in committee_keywords)
        
        # URLに関連パターンが含まれるかチェック
        url_match = any(pattern in href.lower() for pattern in url_patterns)
        
        return text_match or url_match
    
    def extract_committee_name(self, text: str) -> str:
        """委員会名を抽出"""
        # 「〇〇委員会」パターンを抽出
        committee_match = re.search(r'(.+?委員会)', text)
        if committee_match:
            return committee_match.group(1)
        
        # 「〇〇調査会」パターンを抽出
        investigation_match = re.search(r'(.+?調査会)', text)
        if investigation_match:
            return investigation_match.group(1)
        
        return text.strip()
    
    def extract_news_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """ニュース詳細ページから情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ページ内容を解析
            content = self.extract_page_content(soup)
            
            news_detail = {
                'title': link_info['title'],
                'url': link_info['url'],
                'committee': link_info['committee'],
                'content': content,
                'date': self.extract_date(soup),
                'news_type': self.classify_news_type(content),
                'collected_at': datetime.now().isoformat(),
                'year': self.year,
                'week': self.week
            }
            
            return news_detail
            
        except Exception as e:
            logger.error(f"ニュース詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_page_content(self, soup: BeautifulSoup) -> str:
        """ページ内容を抽出"""
        try:
            # 本文を抽出する複数の方法を試す
            content_selectors = [
                'div.contents',
                'div.main',
                'div.content',
                'table',
                'body'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # テキストを抽出して整形
                    text = content_elem.get_text(separator='\n', strip=True)
                    return self.clean_text(text)
            
            # フォールバック: body全体から抽出
            return self.clean_text(soup.get_text(separator='\n', strip=True))
            
        except Exception as e:
            logger.error(f"ページ内容抽出エラー: {str(e)}")
            return ""
    
    def extract_date(self, soup: BeautifulSoup) -> str:
        """ページから日付を抽出"""
        try:
            # 日付パターンを探す
            date_patterns = [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
                r'(\d{4}-\d{2}-\d{2})'
            ]
            
            page_text = soup.get_text()
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    else:
                        return match.group(1)
            
            # 日付が見つからない場合は現在日付
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception as e:
            logger.error(f"日付抽出エラー: {str(e)}")
            return datetime.now().strftime('%Y-%m-%d')
    
    def classify_news_type(self, content: str) -> str:
        """ニュースタイプを分類"""
        content_lower = content.lower()
        
        if any(keyword in content_lower for keyword in ['法案', '議案', 'bill']):
            return '法案審議'
        elif any(keyword in content_lower for keyword in ['開催', '予定', 'schedule']):
            return '委員会開催'
        elif any(keyword in content_lower for keyword in ['報告', 'report']):
            return '委員会報告'
        elif any(keyword in content_lower for keyword in ['質疑', '質問']):
            return '質疑応答'
        else:
            return '一般ニュース'
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # 改行・スペースの正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 連続空行を2行まで
        text = re.sub(r'[ \t]+', ' ', text)  # 連続スペースを1つに
        text = re.sub(r'[\u3000]+', ' ', text)  # 全角スペースを半角に
        
        return text.strip()
    
    def save_news_data(self, news_items: List[Dict[str, Any]]):
        """ニュースデータを保存"""
        if not news_items:
            logger.warning("保存するニュースデータがありません")
            return
        
        # データ期間を基準としたファイル名（現在の年月 + 時刻）
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m01')  # 当月のデータとして保存
        timestamp = current_date.strftime('%H%M%S')
        
        # 生データ保存
        raw_filename = f"committee_news_{data_period}_{timestamp}.json"
        raw_filepath = self.news_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"committee_news_{data_period}_{timestamp}.json"
        frontend_filepath = self.frontend_news_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        logger.info(f"ニュースデータ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 件数: {len(news_items)}")

def main():
    """メイン実行関数"""
    collector = CommitteeNewsCollector()
    
    try:
        # 委員会ニュース収集
        news_items = collector.collect_committee_news()
        
        # データ保存
        collector.save_news_data(news_items)
        
        logger.info("委員会ニュース収集処理完了")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()