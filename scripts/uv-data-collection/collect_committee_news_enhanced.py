#!/usr/bin/env python3
"""
委員会ニュース収集スクリプト（強化版）

個別委員会ニュースページから実際の委員会活動内容を詳細抽出
- ナビゲーション要素を除去
- 実際の委員会議事内容を抽出
- 法案審議・質疑応答の詳細を収集
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

class CommitteeNewsEnhanced:
    """委員会ニュース収集クラス（強化版）"""
    
    def __init__(self, date_from: Optional[str] = None, date_to: Optional[str] = None, session_number: int = 217):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 国会回次設定
        self.session_number = session_number
        
        # 日付範囲設定
        self.date_from = date_from  # YYYY-MM-DD
        self.date_to = date_to or datetime.now().strftime('%Y-%m-%d')
        
        # 出力ディレクトリ設定（国会回次別）
        self.project_root = Path(__file__).parent.parent.parent
        self.news_dir = self.project_root / "data" / "processed" / "committee_news" / f"session_{session_number}"
        self.frontend_news_dir = self.project_root / "frontend" / "public" / "data" / "committee_news" / f"session_{session_number}"
        
        # ディレクトリ作成
        self.news_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_news_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存データを読み込み（重複防止用）
        self.existing_news = self.load_existing_data()
        
        # 基本URL
        self.base_url = "https://www.shugiin.go.jp"
        self.news_base_url = "https://www.shugiin.go.jp/internet/itdb_rchome.nsf/html/rchome/News/"
        
        # 委員会一覧（常任委員会 + 特別委員会）
        self.standing_committees = {
            'naikaku': '内閣委員会',
            'soumu': '総務委員会', 
            'houmu': '法務委員会',
            'gaimu': '外務委員会',
            'zaimu': '財務金融委員会',
            'monka': '文部科学委員会',
            'kourou': '厚生労働委員会',
            'nousui': '農林水産委員会',
            'keizai': '経済産業委員会',
            'kokudo': '国土交通委員会',
            'kankyou': '環境委員会',
            'ampo': '安全保障委員会',
            'kihon': '基本政策委員会',
            'yosan': '予算委員会',
            'kessan': '決算行政監視委員会'
        }
        
        self.special_committees = {
            'fukkosaigai': '復興災害特別委員会',
            'seijikaikaku': '政治改革特別委員会',
            'okihoku': '沖縄北方特別委員会',
            'rachi': '拉致問題特別委員会',
            'shohisha': '消費者特別委員会',
            'genshiryoku': '原子力特別委員会',
            'chikodigi': '地方デジタル特別委員会'
        }
        
        self.committees = {**self.standing_committees, **self.special_committees}
        
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
    
    def load_existing_data(self) -> dict:
        """既存データを読み込み（日付ベース重複防止用）"""
        existing_data = {
            'urls': set(),
            'committee_dates': {}  # {committee_key: [dates]}
        }
        try:
            latest_file = self.frontend_news_dir / "committee_news_latest.json"
            if latest_file.exists():
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for item in data:
                        if 'url' in item:
                            existing_data['urls'].add(item['url'])
                        
                        # 委員会別日付を記録
                        if 'committee' in item and 'date' in item:
                            committee = item['committee']
                            date = item['date']
                            if committee not in existing_data['committee_dates']:
                                existing_data['committee_dates'][committee] = set()
                            existing_data['committee_dates'][committee].add(date)
                
                logger.info(f"既存データ読み込み完了: {len(existing_data['urls'])}件のURL")
                logger.info(f"委員会別日付: {len(existing_data['committee_dates'])}委員会")
            else:
                logger.info("既存データファイルが見つかりません。新規収集を開始します。")
        except Exception as e:
            logger.warning(f"既存データ読み込みエラー: {str(e)}")
        
        return existing_data
    
    def is_date_in_range(self, date_str: str) -> bool:
        """日付が指定範囲内かチェック"""
        if not self.date_from:
            return True  # 開始日未指定なら全て対象
        
        try:
            return self.date_from <= date_str <= self.date_to
        except:
            return True  # 日付比較エラーなら対象とする
    
    def collect_enhanced_committee_news(self) -> List[Dict[str, Any]]:
        """強化版委員会ニュース収集"""
        logger.info("強化版委員会ニュース収集開始...")
        all_news = []
        
        for committee_key, committee_name in self.committees.items():
            try:
                logger.info(f"{committee_name}の強化版ニュース収集開始...")
                committee_news = self.collect_committee_specific_news(committee_key, committee_name)
                all_news.extend(committee_news)
                logger.info(f"{committee_name}の強化版ニュース収集完了: {len(committee_news)}件")
                
                # レート制限対応
                self.random_delay(2, 4)
                
            except Exception as e:
                logger.error(f"{committee_name}の強化版ニュース収集エラー: {str(e)}")
                continue
        
        logger.info(f"強化版委員会ニュース収集完了: {len(all_news)}件")
        return all_news
    
    def collect_committee_specific_news(self, committee_key: str, committee_name: str) -> List[Dict[str, Any]]:
        """特定委員会の強化版ニュース収集"""
        news_items = []
        
        try:
            # 委員会ニュース一覧ページのURL
            committee_url = f"{self.news_base_url}{committee_key}{self.session_number}.htm"
            
            self.update_headers()
            self.random_delay()
            
            response = self.session.get(committee_url, timeout=30)
            if response.status_code != 200:
                logger.warning(f"委員会ページアクセス失敗: {committee_url} (Status: {response.status_code})")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 個別ニュースリンクを抽出（217回全データ）
            news_links = self.extract_individual_news_links(soup, committee_key, committee_name)
            logger.info(f"{committee_name}で発見したニュースリンク: {len(news_links)}件（217回全データ）")
            
            # 各ニュースリンクの詳細を取得
            for idx, link_info in enumerate(news_links):
                try:
                    self.random_delay(1, 2)
                    self.update_headers()
                    
                    # 重複チェック（URL + 日付ベース）
                    if link_info['url'] in self.existing_news['urls']:
                        logger.info(f"既存URLのためスキップ ({idx+1}/{len(news_links)}): {link_info['url']}")
                        continue
                    
                    # 委員会別日付重複チェック
                    committee_dates = self.existing_news['committee_dates'].get(committee_name, set())
                    if link_info['date'] in committee_dates:
                        logger.info(f"既存日付のためスキップ ({idx+1}/{len(news_links)}): {committee_name} {link_info['date']}")
                        continue
                    
                    # 日付範囲チェック
                    if not self.is_date_in_range(link_info['date']):
                        logger.info(f"日付範囲外のためスキップ ({idx+1}/{len(news_links)}): {link_info['date']}")
                        continue
                    
                    news_detail = self.extract_enhanced_news_detail(link_info)
                    if news_detail:
                        news_items.append(news_detail)
                        # 新規URLと日付を既存セットに追加
                        self.existing_news['urls'].add(news_detail['url'])
                        if committee_name not in self.existing_news['committee_dates']:
                            self.existing_news['committee_dates'][committee_name] = set()
                        self.existing_news['committee_dates'][committee_name].add(news_detail['date'])
                        logger.info(f"強化版詳細取得成功 ({idx+1}/{len(news_links)}): {news_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"強化版ニュース詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            return news_items
            
        except Exception as e:
            logger.error(f"{committee_name}の強化版ニュース収集エラー: {str(e)}")
            return []
    
    def extract_individual_news_links(self, soup: BeautifulSoup, committee_key: str, committee_name: str) -> List[Dict[str, str]]:
        """個別ニュースリンクを抽出"""
        links = []
        
        try:
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
            
            # 重複除去して日付順ソート（新しい順）
            unique_links = []
            seen_urls = set()
            for link in links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            # 日付順ソート
            unique_links.sort(key=lambda x: x['date'], reverse=True)
            
            return unique_links
            
        except Exception as e:
            logger.error(f"個別ニュースリンク抽出エラー: {str(e)}")
            return []
    
    def is_individual_news_link(self, href: str, committee_key: str) -> bool:
        """個別ニュースリンクかどうか判定"""
        # 個別ニュースページのパターン: [committee][session][date][number]_m.htm
        pattern = f"{committee_key}{self.session_number}\\d{{8}}\\d{{3}}_m\\.htm"
        return bool(re.search(pattern, href))
    
    def extract_date_from_filename(self, filename: str) -> str:
        """ファイル名から日付を抽出"""
        # ファイル名から日付パターンを抽出: committee[session]YYYYMMDDNNN_m.htm
        date_match = re.search(rf'{self.session_number}(\d{{4}})(\d{{2}})(\d{{2}})\d{{3}}_m\.htm', filename)
        if date_match:
            year, month, day = date_match.groups()
            return f"{year}-{month}-{day}"
        
        return datetime.now().strftime('%Y-%m-%d')
    
    def extract_enhanced_news_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """強化版個別ニュースページから詳細情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 強化版ページ内容解析
            content_info = self.parse_enhanced_news_content(soup)
            
            # 法案情報の抽出
            bill_info = self.extract_enhanced_bill_info(soup)
            
            # PDF情報の抽出  
            pdf_info = self.extract_pdf_info(soup)
            
            # 議事内容の抽出
            meeting_content = self.extract_meeting_content(soup)
            
            news_detail = {
                'title': self.generate_enhanced_title(link_info, content_info, bill_info),
                'url': link_info['url'],
                'committee': link_info['committee'],
                'date': link_info['date'],
                'news_type': self.classify_enhanced_news_type(content_info, bill_info, meeting_content),
                'content': self.format_enhanced_content(link_info, content_info, bill_info, pdf_info, meeting_content),
                'content_length': len(content_info.get('clean_text', '')),
                'collected_at': datetime.now().isoformat(),
                'year': self.year,
                'week': self.week,
                'source': 'committee_news_enhanced'
            }
            
            # 追加情報
            if bill_info:
                news_detail['bill_info'] = bill_info
            if pdf_info:
                news_detail['pdf_info'] = pdf_info
            if meeting_content:
                news_detail['meeting_info'] = meeting_content
            
            return news_detail
            
        except Exception as e:
            logger.error(f"強化版ニュース詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def parse_enhanced_news_content(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """強化版ニュースページの内容解析"""
        content_info = {
            'clean_text': '',
            'main_content': '',
            'agenda_items': [],
            'bills_discussed': []
        }
        
        try:
            # メインコンテンツエリアを特定
            # ナビゲーション要素を除去
            self.remove_navigation_elements(soup)
            
            # メインコンテンツを抽出
            main_content = soup.find('body') or soup
            
            # 実際の委員会内容を抽出
            content_info['clean_text'] = self.extract_clean_content(main_content)
            
            # 議題項目を抽出
            content_info['agenda_items'] = self.extract_agenda_items(soup)
            
            # 審議された法案を抽出
            content_info['bills_discussed'] = self.extract_bills_discussed(soup)
            
            return content_info
            
        except Exception as e:
            logger.error(f"強化版ページ内容解析エラー: {str(e)}")
            return content_info
    
    def remove_navigation_elements(self, soup: BeautifulSoup):
        """ナビゲーション要素を除去"""
        # 除去対象の要素
        remove_selectors = [
            '#HeaderBlock',
            '#HeaderBack', 
            '#HeaderBody',
            '#MapandHelp',
            '#TalkBox',
            '#SearchBox',
            '.mf_finder_container',
            'script',
            'style',
            'noscript'
        ]
        
        for selector in remove_selectors:
            elements = soup.select(selector)
            for element in elements:
                element.decompose()
        
        # 特定のテキストを含む要素を除去
        unwanted_texts = [
            'メインへスキップ',
            'サイトマップ',
            'ヘルプ',
            '音声読み上げ',
            'サイト内検索',
            'ブラウザのJavaScriptが無効のため',
            'Foreign Language'
        ]
        
        for text in unwanted_texts:
            elements = soup.find_all(string=re.compile(text))
            for element in elements:
                if element.parent:
                    element.parent.decompose()
    
    def extract_clean_content(self, soup: BeautifulSoup) -> str:
        """クリーンな内容を抽出"""
        try:
            # テキストを抽出
            text = soup.get_text(separator='\n', strip=True)
            
            # 不要な行を除去
            lines = text.split('\n')
            clean_lines = []
            
            for line in lines:
                line = line.strip()
                if self.is_useful_content_line(line):
                    clean_lines.append(line)
            
            return '\n'.join(clean_lines)
            
        except Exception as e:
            logger.error(f"クリーン内容抽出エラー: {str(e)}")
            return ""
    
    def is_useful_content_line(self, line: str) -> bool:
        """有用な内容の行かどうか判定"""
        if not line or len(line) < 3:
            return False
        
        # 除外する行のパターン
        exclude_patterns = [
            r'^[\s\u3000]*$',  # 空行
            r'^[>\s]*$',        # > のみ
            r'^衆議院$',        # 単独の「衆議院」
            r'^本会議・委員会等$',
            r'^委員会ニュース$',
            r'^第\d+回国会.*委員会ニュース$',
            r'^関連情報$',
            r'^（会議録は、現在作成中です。）$',
            r'^\(PDF \d+KB\)$'
        ]
        
        for pattern in exclude_patterns:
            if re.match(pattern, line):
                return False
        
        # 有用な内容を示すパターン
        useful_patterns = [
            r'法案',
            r'法律案',
            r'議案',
            r'審議',
            r'質疑',
            r'答弁',
            r'採決',
            r'可決',
            r'否決',
            r'修正',
            r'附帯決議'
        ]
        
        for pattern in useful_patterns:
            if re.search(pattern, line):
                return True
        
        # 文章として成立している場合は有用
        return len(line) > 10 and ('。' in line or '、' in line)
    
    def extract_agenda_items(self, soup: BeautifulSoup) -> List[str]:
        """議題項目を抽出"""
        agenda_items = []
        
        try:
            # リスト要素から議題を抽出
            list_elements = soup.find_all(['ul', 'ol', 'li'])
            
            for element in list_elements:
                text = element.get_text(strip=True)
                if self.is_agenda_item(text):
                    agenda_items.append(text)
            
        except Exception as e:
            logger.error(f"議題項目抽出エラー: {str(e)}")
        
        return agenda_items
    
    def is_agenda_item(self, text: str) -> bool:
        """議題項目かどうか判定"""
        if not text or len(text) < 5:
            return False
        
        agenda_keywords = [
            '法案',
            '法律案',
            '議案',
            '承認',
            '同意',
            '報告',
            '質疑',
            '一般質疑'
        ]
        
        return any(keyword in text for keyword in agenda_keywords)
    
    def extract_bills_discussed(self, soup: BeautifulSoup) -> List[str]:
        """審議された法案を抽出"""
        bills = []
        
        try:
            text = soup.get_text()
            
            # 法案タイトルのパターン
            bill_patterns = [
                r'(.{5,50}法案)（[^）]+）',
                r'(.{5,50}法律案)（[^）]+）',
                r'(.{5,50}法案)',
                r'(.{5,50}法律案)'
            ]
            
            for pattern in bill_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    bill_title = match if isinstance(match, str) else match[0]
                    if bill_title not in bills and len(bill_title) > 5:
                        bills.append(bill_title)
            
        except Exception as e:
            logger.error(f"法案抽出エラー: {str(e)}")
        
        return bills[:10]  # 最大10件まで
    
    def extract_meeting_content(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """議事内容を抽出"""
        try:
            meeting_info = {
                'meeting_type': self.determine_meeting_type(soup),
                'participants': self.extract_participants(soup),
                'decisions': self.extract_decisions(soup)
            }
            
            return meeting_info if any(meeting_info.values()) else None
            
        except Exception as e:
            logger.error(f"議事内容抽出エラー: {str(e)}")
            return None
    
    def determine_meeting_type(self, soup: BeautifulSoup) -> str:
        """会議種別を判定"""
        text = soup.get_text().lower()
        
        if '公聴会' in text:
            return '公聴会'
        elif '参考人' in text:
            return '参考人質疑'
        elif '連合審査会' in text:
            return '連合審査会'
        elif '分科会' in text:
            return '分科会'
        else:
            return '委員会'
    
    def extract_participants(self, soup: BeautifulSoup) -> List[str]:
        """参加者を抽出"""
        participants = []
        
        try:
            text = soup.get_text()
            
            # 参加者のパターン
            participant_patterns = [
                r'委員長\s*([^\s]+)',
                r'理事\s*([^\s]+)',
                r'委員\s*([^\s]+)',
                r'参考人\s*([^\s]+)'
            ]
            
            for pattern in participant_patterns:
                matches = re.findall(pattern, text)
                participants.extend(matches)
            
        except Exception as e:
            logger.error(f"参加者抽出エラー: {str(e)}")
        
        return list(set(participants))[:10]  # 重複除去、最大10人
    
    def extract_decisions(self, soup: BeautifulSoup) -> List[str]:
        """決定事項を抽出"""
        decisions = []
        
        try:
            text = soup.get_text()
            
            # 決定事項のパターン
            decision_patterns = [
                r'(.*可決.*)',
                r'(.*否決.*)',
                r'(.*修正.*)',
                r'(.*附帯決議.*)',
                r'(.*採決.*)'
            ]
            
            for pattern in decision_patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if len(match) > 5 and len(match) < 100:
                        decisions.append(match.strip())
            
        except Exception as e:
            logger.error(f"決定事項抽出エラー: {str(e)}")
        
        return decisions[:5]  # 最大5件
    
    def extract_enhanced_bill_info(self, soup: BeautifulSoup) -> Optional[Dict[str, Any]]:
        """強化版法案情報を抽出"""
        try:
            bill_info = {}
            page_text = soup.get_text()
            
            # 法案パターンの検索（より詳細）
            bill_patterns = [
                r'(.+?法律案)（(.+?)）',
                r'(.+?法案)（(.+?)）',
                r'(.+?法律案)',
                r'(.+?法案)'
            ]
            
            for pattern in bill_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    if isinstance(matches[0], tuple) and len(matches[0]) > 1:
                        bill_info['bill_title'] = matches[0][0].strip()
                        bill_info['bill_number'] = matches[0][1].strip()
                    else:
                        title = matches[0] if isinstance(matches[0], str) else matches[0][0]
                        bill_info['bill_title'] = title.strip()
                    
                    bill_info['bill_keyword'] = '法律案'
                    bill_info['bill_source'] = 'enhanced_extraction'
                    
                    # 法案の状況を抽出
                    bill_info['status'] = self.extract_bill_status(page_text, bill_info['bill_title'])
                    break
            
            return bill_info if bill_info else None
            
        except Exception as e:
            logger.error(f"強化版法案情報抽出エラー: {str(e)}")
            return None
    
    def extract_bill_status(self, text: str, bill_title: str) -> str:
        """法案の状況を抽出"""
        status_keywords = {
            '可決': '可決',
            '否決': '否決', 
            '修正': '修正可決',
            '審議': '審議中',
            '質疑': '質疑中',
            '採決': '採決済み'
        }
        
        for keyword, status in status_keywords.items():
            if keyword in text:
                return status
        
        return '審議中'
    
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
    
    def generate_enhanced_title(self, link_info: Dict[str, str], content_info: Dict[str, Any], bill_info: Optional[Dict]) -> str:
        """強化版タイトル生成"""
        # 法案がある場合は法案名を使用
        if bill_info and bill_info.get('bill_title'):
            bill_title = bill_info['bill_title']
            if len(bill_title) > 30:
                bill_title = bill_title[:30] + '...'
            return f"【{link_info['committee']}】{bill_title}"
        
        # 日付ベースのタイトル
        date_parts = link_info['date'].split('-')
        if len(date_parts) == 3:
            year, month, day = date_parts
            reiwa_year = int(year) - 2018
            date_str = f"令和{reiwa_year}年{int(month)}月{int(day)}日"
        else:
            date_str = link_info['date']
        
        return f"【{link_info['committee']}】{date_str}委員会"
    
    def classify_enhanced_news_type(self, content_info: Dict[str, Any], bill_info: Optional[Dict], meeting_content: Optional[Dict]) -> str:
        """強化版ニュースタイプ分類"""
        if bill_info:
            status = bill_info.get('status', '')
            if '可決' in status:
                return '法案可決'
            elif '否決' in status:
                return '法案否決'
            elif '修正' in status:
                return '法案修正'
            else:
                return '法案審議'
        
        if meeting_content:
            meeting_type = meeting_content.get('meeting_type', '')
            if meeting_type != '委員会':
                return meeting_type
        
        clean_text = content_info.get('clean_text', '').lower()
        
        if any(keyword in clean_text for keyword in ['質疑', '質問', '答弁']):
            return '質疑応答'
        elif any(keyword in clean_text for keyword in ['採決', '可決', '否決']):
            return '採決'
        else:
            return '委員会開催'
    
    def format_enhanced_content(self, link_info: Dict[str, str], content_info: Dict[str, Any], 
                               bill_info: Optional[Dict], pdf_info: Optional[Dict], 
                               meeting_content: Optional[Dict]) -> str:
        """強化版内容フォーマット"""
        formatted_parts = []
        
        # 基本情報
        formatted_parts.append(f"委員会: {link_info['committee']}")
        
        # 日付変換
        date_parts = link_info['date'].split('-')
        if len(date_parts) == 3:
            year, month, day = date_parts
            reiwa_year = int(year) - 2018
            date_display = f"令和{reiwa_year}年{int(month)}月{int(day)}日"
        else:
            date_display = link_info['date']
        formatted_parts.append(f"開催日: {date_display}")
        
        # 法案情報
        if bill_info:
            formatted_parts.append(f"議案名: {bill_info.get('bill_title', '')}")
            if bill_info.get('bill_number'):
                formatted_parts.append(f"議案番号: {bill_info['bill_number']}")
            if bill_info.get('status'):
                formatted_parts.append(f"審議状況: {bill_info['status']}")
        
        # 議事内容
        if meeting_content:
            if meeting_content.get('meeting_type'):
                formatted_parts.append(f"会議種別: {meeting_content['meeting_type']}")
            if meeting_content.get('decisions'):
                formatted_parts.append("決定事項:")
                for decision in meeting_content['decisions'][:3]:
                    formatted_parts.append(f"- {decision}")
        
        # 議題
        if content_info.get('agenda_items'):
            formatted_parts.append("主な議題:")
            for agenda in content_info['agenda_items'][:3]:
                formatted_parts.append(f"- {agenda}")
        
        # PDF情報
        if pdf_info:
            formatted_parts.append("関連資料:")
            formatted_parts.append(f"- {pdf_info['pdf_title']} ({pdf_info['pdf_url']})")
        
        # 実際の内容（抜粋）
        clean_text = content_info.get('clean_text', '')
        if clean_text and len(clean_text) > 50:
            summary = clean_text[:200] + '...' if len(clean_text) > 200 else clean_text
            formatted_parts.append(f"内容抜粋: {summary}")
        
        return '\n'.join(formatted_parts)
    
    def save_enhanced_news_data(self, news_items: List[Dict[str, Any]]):
        """強化版ニュースデータを保存（増分対応）"""
        # 既存データを読み込み
        existing_data = []
        latest_filepath = self.frontend_news_dir / "committee_news_latest.json"
        
        if latest_filepath.exists():
            try:
                with open(latest_filepath, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
                logger.info(f"既存データ: {len(existing_data)}件")
            except Exception as e:
                logger.warning(f"既存データ読み込みエラー: {str(e)}")
        
        # 新規データがある場合のみ更新
        if news_items:
            # 既存データと新規データを統合
            all_data = existing_data + news_items
            
            # URL重複除去
            seen_urls = set()
            unique_data = []
            for item in all_data:
                if item['url'] not in seen_urls:
                    unique_data.append(item)
                    seen_urls.add(item['url'])
            
            # 日付順でソート（新しい順）
            unique_data.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # フロントエンド用データ保存（国会回次別）
            frontend_filename = f"committee_news_session_{self.session_number}_{timestamp}.json"
            frontend_filepath = self.frontend_news_dir / frontend_filename
            
            with open(frontend_filepath, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)
            
            # latest.jsonも更新
            with open(latest_filepath, 'w', encoding='utf-8') as f:
                json.dump(unique_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"強化版委員会ニュースデータ保存完了:")
            logger.info(f"  - 新規データ: {len(news_items)}件")
            logger.info(f"  - 総データ: {len(unique_data)}件")
            logger.info(f"  - フロントエンド: {frontend_filepath}")
            logger.info(f"  - 最新版: {latest_filepath}")
        else:
            logger.info("新規データがないため、ファイル更新をスキップしました")

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='強化版委員会ニュース収集')
    parser.add_argument('--start-date', type=str, help='開始日 (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, help='終了日 (YYYY-MM-DD)')
    parser.add_argument('--days', type=int, help='過去N日分のデータを収集')
    parser.add_argument('--session', type=int, default=217, help='国会回次 (デフォルト: 217)')
    parser.add_argument('--sessions', type=str, help='複数国会回次 (例: 217,216,215)')
    parser.add_argument('--session-range', type=str, help='国会回次範囲 (例: 215-217)')
    
    args = parser.parse_args()
    
    # 国会回次の設定
    session_numbers = []
    if args.sessions:
        session_numbers = [int(s.strip()) for s in args.sessions.split(',')]
    elif args.session_range:
        start, end = map(int, args.session_range.split('-'))
        session_numbers = list(range(start, end + 1))
    else:
        session_numbers = [args.session]
    
    # 日付範囲の設定
    date_from = args.start_date
    date_to = args.end_date
    
    if args.days:
        # 過去N日分の場合
        end_date = datetime.now()
        start_date = end_date - timedelta(days=args.days)
        date_from = start_date.strftime('%Y-%m-%d')
        date_to = end_date.strftime('%Y-%m-%d')
        logger.info(f"過去{args.days}日分のデータを収集: {date_from} ~ {date_to}")
    elif date_from or date_to:
        logger.info(f"日付範囲指定: {date_from or '開始なし'} ~ {date_to or '本日まで'}")
    else:
        logger.info("全期間対象（増分収集モード）")
    
    # 各国会回次を処理
    for session_num in session_numbers:
        logger.info(f"=== 第{session_num}回国会の処理開始 ===")
        
        try:
            collector = CommitteeNewsEnhanced(
                date_from=date_from, 
                date_to=date_to, 
                session_number=session_num
            )
            
            # 強化版委員会ニュース収集
            news_items = collector.collect_enhanced_committee_news()
            
            # データ保存
            collector.save_enhanced_news_data(news_items)
            
            logger.info(f"第{session_num}回国会の処理完了")
            
        except Exception as e:
            logger.error(f"第{session_num}回国会の処理エラー: {str(e)}")
            continue
    
    logger.info("全ての国会回次の処理完了")

if __name__ == "__main__":
    main()