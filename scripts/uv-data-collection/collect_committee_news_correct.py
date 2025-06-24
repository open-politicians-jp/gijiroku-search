#!/usr/bin/env python3
"""
委員会ニュース収集スクリプト（修正版）

正しい方法で個別委員会ニュースページから情報を収集
1. 各委員会の個別ニュースページ (例: naikaku217.htm) を探す
2. 個別ページから具体的なニュース項目 (naikaku21720250606026_m.htm) にアクセス
3. 詳細情報を抽出してJSON化
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

class CommitteeNewsCollectorCorrect:
    """委員会ニュース収集クラス（修正版）"""
    
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
        
        # 基本URL
        self.base_url = "https://www.shugiin.go.jp"
        self.news_base_url = "https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/News/"
        
        # 第217回国会用の委員会一覧
        self.committees = {
            'naikaku': '内閣委員会',
            'somu': '総務委員会',
            'houmu': '法務委員会',
            'gaimu': '外務委員会',
            'zaimu': '財務金融委員会',
            'bunka': '文部科学委員会',
            'kouse': '厚生労働委員会',
            'nosan': '農林水産委員会',
            'keisan': '経済産業委員会',
            'kokudo': '国土交通委員会',
            'kankyo': '環境委員会',
            'anzen': '安全保障委員会',
            'yosan': '予算委員会',
            'ketsusan': '決算行政監視委員会',
            'sensyo': '議院運営委員会',
            'kouki': '懲罰委員会'
        }
        
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
    
    def random_delay(self, min_seconds=1, max_seconds=3):
        """ランダム遅延でレート制限対応"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def collect_all_committee_news(self) -> List[Dict[str, Any]]:
        """全委員会のニュースを収集"""
        logger.info("全委員会ニュース収集開始...")
        all_news = []
        
        for committee_key, committee_name in self.committees.items():
            try:
                logger.info(f"{committee_name}のニュース収集開始...")
                committee_news = self.collect_committee_specific_news(committee_key, committee_name)
                all_news.extend(committee_news)
                logger.info(f"{committee_name}のニュース収集完了: {len(committee_news)}件")
                
                # レート制限対応
                self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"{committee_name}のニュース収集エラー: {str(e)}")
                continue
        
        logger.info(f"全委員会ニュース収集完了: {len(all_news)}件")
        return all_news
    
    def collect_committee_specific_news(self, committee_key: str, committee_name: str) -> List[Dict[str, Any]]:
        """特定委員会のニュースを収集"""
        news_items = []
        
        try:
            # 委員会ニュース一覧ページのURL (例: naikaku217.htm)
            committee_url = f"{self.news_base_url}{committee_key}217.htm"
            
            self.update_headers()
            self.random_delay()
            
            response = self.session.get(committee_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"委員会ページアクセス失敗: {committee_url} (Status: {response.status_code})")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 個別ニュースリンクを抽出
            news_links = self.extract_individual_news_links(soup, committee_key, committee_name)
            logger.info(f"{committee_name}で発見したニュースリンク: {len(news_links)}件")
            
            # 各ニュースリンクの詳細を取得
            for idx, link_info in enumerate(news_links):
                try:
                    self.random_delay(1, 2)
                    self.update_headers()
                    
                    news_detail = self.extract_individual_news_detail(link_info)
                    if news_detail:
                        news_items.append(news_detail)
                        logger.info(f"詳細取得成功 ({idx+1}/{len(news_links)}): {news_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"個別ニュース詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"{committee_name}の特定ニュース収集エラー: {str(e)}")
            return []
    
    def extract_individual_news_links(self, soup: BeautifulSoup, committee_key: str, committee_name: str) -> List[Dict[str, str]]:
        """個別ニュースリンクを抽出"""
        links = []
        
        try:
            # 実際の委員会ニュースページのリンクパターンを探す
            # 例: naikaku21720250530025_m.htm のようなパターン
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 個別ニュースページのパターンをチェック
                if self.is_individual_news_link(href, committee_key):
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
                    date = self.extract_date_from_filename(href)
                    
                    links.append({
                        'url': full_url,
                        'title': text or f"【{committee_name}】ニュース",
                        'committee': committee_name,
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
            logger.error(f"個別ニュースリンク抽出エラー: {str(e)}")
            return []
    
    def is_individual_news_link(self, href: str, committee_key: str) -> bool:
        """個別ニュースリンクかどうか判定"""
        # 個別ニュースページのパターン: [committee]217[date][number]_m.htm
        pattern = f"{committee_key}217\\d{{8}}\\d{{3}}_m\\.htm"
        return bool(re.search(pattern, href))
    
    def extract_date_from_filename(self, filename: str) -> str:
        """ファイル名から日付を抽出"""
        # ファイル名から日付パターンを抽出: committee217YYYYMMDDNNN_m.htm
        date_match = re.search(r'217(\d{4})(\d{2})(\d{2})\d{3}_m\.htm', filename)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_individual_news_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """個別ニュースページから詳細情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # ページ内容を詳細に解析
            content_info = self.parse_news_page_content(soup)
            
            # 法案情報の抽出
            bill_info = self.extract_bill_info(soup)
            
            # PDF情報の抽出  
            pdf_info = self.extract_pdf_info(soup)
            
            news_detail = {
                'title': self.generate_news_title(link_info, content_info),
                'url': link_info['url'],
                'committee': link_info['committee'],
                'date': link_info['date'],
                'news_type': self.classify_news_type_from_content(content_info),
                'content': self.format_content(content_info, bill_info, pdf_info),
                'content_length': len(content_info.get('raw_text', '')),
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
            logger.error(f"個別ニュース詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def parse_news_page_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """ニュースページの内容を詳細解析"""
        content_info = {
            'raw_text': '',
            'tables': [],
            'lists': [],
            'agenda_items': []
        }
        
        try:
            # メインコンテンツエリアを特定
            main_content = soup.find('body') or soup
            
            # テーブル情報の抽出
            tables = main_content.find_all('table')
            for table in tables:
                table_text = table.get_text(separator='\n', strip=True)
                if table_text:
                    content_info['tables'].append(table_text)
            
            # リスト項目の抽出
            lists = main_content.find_all(['ul', 'ol'])
            for list_elem in lists:
                list_text = list_elem.get_text(separator='\n', strip=True)
                if list_text:
                    content_info['lists'].append(list_text)
            
            # 全体テキスト
            content_info['raw_text'] = self.clean_text(main_content.get_text(separator='\n', strip=True))
            
            return content_info
            
        except Exception as e:
            logger.error(f"ページ内容解析エラー: {str(e)}")
            return content_info
    
    def extract_bill_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """法案情報を抽出"""
        try:
            bill_info = {}
            
            # 法案タイトルの抽出
            page_text = soup.get_text()
            
            # 法案パターンの検索
            bill_patterns = [
                r'(.+?法律案)（(.+?)）',
                r'(.+?法案)（(.+?)）',
                r'(.+?法律案)',
                r'(.+?法案)'
            ]
            
            for pattern in bill_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    if isinstance(matches[0], tuple):
                        bill_info['bill_title'] = matches[0][0]
                        if len(matches[0]) > 1:
                            bill_info['bill_number'] = matches[0][1]
                    else:
                        bill_info['bill_title'] = matches[0]
                    bill_info['bill_keyword'] = '法律案'
                    bill_info['bill_source'] = 'page_content'
                    break
            
            return bill_info if bill_info else None
            
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
    
    def generate_news_title(self, link_info: Dict[str, str], content_info: Dict[str, Any]) -> str:
        """ニュースタイトルを生成"""
        # 既存のタイトルがある場合
        if link_info.get('title') and link_info['title'] != f"【{link_info['committee']}】ニュース":
            return link_info['title']
        
        # 内容から法案名を抽出してタイトル作成
        raw_text = content_info.get('raw_text', '')
        
        # 法案タイトル抽出
        bill_match = re.search(r'(.+?法律?案)（', raw_text)
        if bill_match:
            bill_title = bill_match.group(1)
            return f"【{link_info['committee']}】{bill_title}"
        
        # 日付ベースのタイトル
        date_str = link_info['date'].replace('-', '')
        if '202505' in date_str:
            date_display = link_info['date'].replace('-', '年').replace('年0', '年') + '日'
        else:
            date_display = link_info['date']
        
        return f"【{link_info['committee']}】第217回国会{date_display}{link_info['committee']}ニュース"
    
    def classify_news_type_from_content(self, content_info: Dict[str, Any]) -> str:
        """内容からニュースタイプを分類"""
        raw_text = content_info.get('raw_text', '').lower()
        
        if any(keyword in raw_text for keyword in ['法案', '議案', '法律案']):
            return '法案審議'
        elif any(keyword in raw_text for keyword in ['pdf', '資料', 'ニュース']):
            return '委員会資料'
        elif any(keyword in raw_text for keyword in ['質疑', '質問', '答弁']):
            return '質疑応答'
        elif any(keyword in raw_text for keyword in ['開催', '予定']):
            return '委員会開催'
        else:
            return '一般ニュース'
    
    def format_content(self, content_info: Dict[str, Any], bill_info: Optional[Dict], pdf_info: Optional[Dict]) -> str:
        """内容をフォーマット"""
        formatted_parts = []
        
        # 法案情報
        if bill_info:
            formatted_parts.append(f"議案名: {bill_info.get('bill_title', '')}")
            if bill_info.get('bill_number'):
                formatted_parts.append(f"議案番号: {bill_info['bill_number']}")
        
        # 基本情報
        if content_info.get('raw_text'):
            # 簡潔な内容説明
            clean_text = content_info['raw_text'][:200] + '...' if len(content_info['raw_text']) > 200 else content_info['raw_text']
            formatted_parts.append(f"内容: {clean_text}")
        
        # PDF情報
        if pdf_info:
            formatted_parts.append(f"関連資料:")
            formatted_parts.append(f"- {pdf_info['pdf_title']} ({pdf_info['pdf_url']})")
        
        return '\n'.join(formatted_parts)
    
    def clean_text(self, text: str) -> str:
        """テキスト整形（JavaScript除去対応）"""
        if not text:
            return ""
        
        # JavaScript無効メッセージの除去
        js_messages = [
            'ブラウザのJavaScriptが無効のため、サイト内検索はご利用いただけません。',
            'JavaScriptが無効です',
            'JavaScript を有効にしてください',
            'JavaScriptを有効にしてください',
            'ブラウザのJavaScriptが無効のため',
            'サイト内検索はご利用いただけません'
        ]
        
        for msg in js_messages:
            text = text.replace(msg, '')
        
        # 不要な定型文除去
        unwanted_phrases = [
            'ホーム', 'サイトマップ', 'プライバシーポリシー',
            'ご利用案内', '国会に関するお問い合わせ', '文字サイズ変更',
            'Foreign Language', 'トップページ', 'ページの先頭'
        ]
        
        for phrase in unwanted_phrases:
            text = text.replace(phrase, '')
        
        # 正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'[\u3000]+', ' ', text)
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        return '\n'.join(lines).strip()
    
    def save_news_data(self, news_items: List[Dict[str, Any]]):
        """ニュースデータを保存"""
        if not news_items:
            logger.warning("保存するニュースデータがありません")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # フロントエンド用データ保存
        frontend_filename = f"committee_news_{timestamp}.json"
        frontend_filepath = self.frontend_news_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        # latest.jsonも更新
        latest_filepath = self.frontend_news_dir / "committee_news_latest.json"
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(news_items, f, ensure_ascii=False, indent=2)
        
        logger.info(f"委員会ニュースデータ保存完了:")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 最新版: {latest_filepath}")
        logger.info(f"  - 件数: {len(news_items)}")

def main():
    """メイン実行関数"""
    collector = CommitteeNewsCollectorCorrect()
    
    try:
        # 全委員会ニュース収集
        news_items = collector.collect_all_committee_news()
        
        # データ保存
        collector.save_news_data(news_items)
        
        logger.info("委員会ニュース収集処理完了")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()