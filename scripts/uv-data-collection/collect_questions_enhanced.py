#!/usr/bin/env python3
"""
質問主意書収集スクリプト（強化版）

衆議院質問主意書データベースから実際の質問主意書情報を収集
https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/menu_m.htm
実際のデータベース構造に基づいた効果的な収集を実装
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
from urllib.parse import urljoin, urlparse, parse_qs

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuestionsCollectorEnhanced:
    """質問主意書収集クラス（強化版）"""
    
    def __init__(self, days_back: int = 90, max_questions: int = 200):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 収集パラメータ設定
        self.days_back = days_back
        self.max_questions = max_questions
        self.start_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        self.end_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"収集期間: {self.start_date} から {self.end_date}")
        logger.info(f"最大収集件数: {self.max_questions}件")
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.questions_dir = self.project_root / "data" / "processed" / "questions"
        self.frontend_questions_dir = self.project_root / "frontend" / "public" / "data" / "questions"
        
        # ディレクトリ作成
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_questions_dir.mkdir(parents=True, exist_ok=True)
        
        # 既存データロード
        self.existing_questions = self.load_existing_questions()
        
        # 基本URL設定
        self.base_url = "https://www.shugiin.go.jp"
        self.questions_main_url = "https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/menu_m.htm"
        self.questions_search_url = "https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/menu_s.htm"
        
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
    
    def load_existing_questions(self) -> set:
        """既存の質問主意書データから質問URLセットを読み込み"""
        existing_urls = set()
        
        # フロントエンド用最新ファイルから読み込み
        latest_file = self.frontend_questions_dir / "questions_latest.json"
        if latest_file.exists():
            try:
                with open(latest_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'data' in data:
                        for question in data['data']:
                            if 'question_url' in question:
                                existing_urls.add(question['question_url'])
                            elif 'url' in question:
                                existing_urls.add(question['url'])
                logger.info(f"既存質問データ読み込み完了: {len(existing_urls)}件")
            except Exception as e:
                logger.warning(f"既存データ読み込みエラー: {e}")
        
        # 他のファイルからも読み込み
        for file_path in self.frontend_questions_dir.glob("questions_*.json"):
            if file_path.name == "questions_latest.json":
                continue
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'data' in data:
                        for question in data['data']:
                            if 'question_url' in question:
                                existing_urls.add(question['question_url'])
                            elif 'url' in question:
                                existing_urls.add(question['url'])
            except Exception as e:
                logger.warning(f"ファイル読み込みエラー {file_path}: {e}")
        
        logger.info(f"既存質問総数: {len(existing_urls)}件")
        return existing_urls
    
    def discover_question_pages(self) -> List[str]:
        """質問主意書の利用可能なページを発見"""
        question_urls = []
        
        try:
            # メインページから情報を収集
            self.update_headers()
            self.random_delay()
            
            response = self.session.get(self.questions_main_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'  # 日本語エンコーディング対応
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"メインページ取得成功: {self.questions_main_url}")
            
            # 質問主意書のリンクを探索
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 質問主意書関連のリンクを特定
                if self.is_question_page_link(href, text):
                    full_url = urljoin(self.questions_main_url, href)
                    if full_url not in question_urls:
                        question_urls.append(full_url)
            
            # さらに詳細な検索ページもチェック
            self.random_delay()
            search_response = self.session.get(self.questions_search_url, timeout=30)
            search_response.raise_for_status()
            search_response.encoding = 'shift_jis'
            
            search_soup = BeautifulSoup(search_response.text, 'html.parser')
            search_links = search_soup.find_all('a', href=True)
            
            for link in search_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if self.is_question_page_link(href, text):
                    full_url = urljoin(self.questions_search_url, href)
                    if full_url not in question_urls:
                        question_urls.append(full_url)
            
            # 直接的な質問ページの番号による推測も試す
            for session_num in range(215, 220):  # 第215回から第219回まで
                for page_type in ['ka', 'a']:
                    test_url = f"https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/{page_type}{session_num}.htm"
                    if test_url not in question_urls:
                        question_urls.append(test_url)
            
            logger.info(f"発見した質問ページ候補: {len(question_urls)}件")
            return question_urls
            
        except Exception as e:
            logger.error(f"質問ページ発見エラー: {str(e)}")
            return []
    
    def is_question_page_link(self, href: str, text: str) -> bool:
        """質問主意書のページリンクかどうか判定"""
        # 質問関連キーワード
        question_keywords = [
            '質問', 'question', 'shitsumon', '第', '号',
            '答弁', '提出', '一覧'
        ]
        
        # URL パターン
        url_patterns = [
            'shitsumon', 'question', 'itdb_shitsumon',
            '.htm', '.html'
        ]
        
        # テキストに質問キーワードが含まれるかチェック
        text_match = any(keyword in text for keyword in question_keywords)
        
        # URLに関連パターンが含まれるかチェック
        url_match = any(pattern in href.lower() for pattern in url_patterns)
        
        # 無効なリンクを除外
        invalid_patterns = ['#', 'javascript:', 'mailto:', 'index.nsf', 'menu']
        invalid_match = any(pattern in href.lower() for pattern in invalid_patterns)
        
        return (text_match or url_match) and not invalid_match and len(href) > 5
    
    def collect_questions_from_page(self, page_url: str) -> List[Dict[str, Any]]:
        """特定のページから質問主意書を収集"""
        questions = []
        
        try:
            self.update_headers()
            self.random_delay()
            
            response = self.session.get(page_url, timeout=30)
            if response.status_code == 404:
                logger.debug(f"ページが見つかりません: {page_url}")
                return []
            
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"ページ取得成功: {page_url}")
            
            # 質問主意書の個別リンクを抽出
            question_links = self.extract_individual_question_links(soup, page_url)
            
            # 各質問の詳細を取得
            for i, link_info in enumerate(question_links):
                if len(questions) >= self.max_questions:
                    logger.info(f"最大収集件数({self.max_questions})に到達しました")
                    break
                
                try:
                    # 既存データのチェック
                    if link_info['url'] in self.existing_questions:
                        logger.debug(f"既存質問をスキップ: {link_info['url']}")
                        continue
                    
                    self.random_delay()
                    question_detail = self.extract_question_detail(link_info)
                    
                    if question_detail:
                        questions.append(question_detail)
                        logger.info(f"質問詳細取得成功 ({i+1}/{len(question_links)}): {question_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"質問詳細取得エラー ({i+1}): {str(e)}")
                    continue
            
            return questions
            
        except Exception as e:
            logger.error(f"ページからの質問収集エラー {page_url}: {str(e)}")
            return []
    
    def extract_individual_question_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """個別の質問主意書リンクを抽出"""
        links = []
        
        try:
            # より幅広いパターンで質問リンクを探す
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 個別の質問主意書かどうかを判定
                if self.is_individual_question_link(href, text):
                    full_url = urljoin(base_url, href)
                    
                    # 質問番号を抽出
                    question_number = self.extract_question_number_from_url(href) or self.extract_question_number_from_text(text)
                    
                    links.append({
                        'url': full_url,
                        'title': text,
                        'question_number': question_number
                    })
            
            # 重複除去
            unique_links = []
            seen_urls = set()
            for link in links:
                if link['url'] not in seen_urls:
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            logger.info(f"個別質問リンク発見: {len(unique_links)}件")
            return unique_links
            
        except Exception as e:
            logger.error(f"個別質問リンク抽出エラー: {str(e)}")
            return []
    
    def is_individual_question_link(self, href: str, text: str) -> bool:
        """個別の質問主意書リンクかどうか判定"""
        # 個別質問のURLパターン
        individual_patterns = [
            r'a\d+\.htm',  # a217001.htm のようなパターン
            r'/shitsumon/a\d+',
            r'question.*\d+',
        ]
        
        # URLパターンマッチ
        url_match = any(re.search(pattern, href, re.IGNORECASE) for pattern in individual_patterns)
        
        # テキストが質問主意書のタイトルっぽいか
        title_indicators = ['に関する質問主意書', '質問主意書', '第', '号']
        text_match = any(indicator in text for indicator in title_indicators) and len(text) > 10
        
        # 除外パターン
        exclude_patterns = ['menu', 'index', 'search', 'help', 'top']
        exclude_match = any(pattern in href.lower() for pattern in exclude_patterns)
        
        return (url_match or text_match) and not exclude_match
    
    def extract_question_number_from_url(self, url: str) -> str:
        """URLから質問番号を抽出"""
        # a217001.htm -> 1
        match = re.search(r'a\d*(\d{3})\.htm', url)
        if match:
            return str(int(match.group(1)))  # 先頭の0を除去
        
        # その他の数字パターン
        match = re.search(r'(\d+)', url)
        if match:
            return match.group(1)
        
        return ""
    
    def extract_question_number_from_text(self, text: str) -> str:
        """テキストから質問番号を抽出"""
        # 「第〇号」パターン
        match = re.search(r'第(\d+)号', text)
        if match:
            return match.group(1)
        
        # 「質問第〇号」パターン
        match = re.search(r'質問第(\d+)号', text)
        if match:
            return match.group(1)
        
        return ""
    
    def extract_question_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """質問詳細ページから情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 質問内容を解析
            question_content = self.extract_question_content(soup)
            answer_content = self.extract_answer_content(soup)
            questioner = self.extract_questioner(soup)
            submission_date = self.extract_date(soup, 'submission')
            answer_date = self.extract_date(soup, 'answer')
            
            # HTML/PDFリンクを探す
            html_links = self.extract_document_links(soup, link_info['url'], 'html')
            pdf_links = self.extract_document_links(soup, link_info['url'], 'pdf')
            
            # 回答URLを構築
            answer_url = self.build_answer_url(link_info['url'])
            
            question_detail = {
                'title': link_info['title'],
                'question_number': link_info['question_number'],
                'questioner': questioner,
                'house': '衆議院',
                'submission_date': submission_date,
                'answer_date': answer_date,
                'question_content': question_content,
                'answer_content': answer_content,
                'question_url': link_info['url'],
                'answer_url': answer_url,
                'html_links': html_links,
                'pdf_links': pdf_links,
                'category': self.classify_question_category(link_info['title'] + " " + question_content),
                'collected_at': datetime.now().isoformat(),
                'year': datetime.now().year,
                'week': datetime.now().isocalendar()[1]
            }
            
            return question_detail
            
        except Exception as e:
            logger.error(f"質問詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_question_content(self, soup: BeautifulSoup) -> str:
        """質問内容を抽出"""
        try:
            # より広範囲からテキストを抽出
            full_text = soup.get_text(separator='\n', strip=True)
            
            # 質問部分を特定する様々なパターンを試す
            patterns = [
                r'質問主意書(.+?)右質問する',
                r'質問主意書(.+?)以上',
                r'提出者\s+.+?(.+?)右質問する',
                r'(.+?)右質問する'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, full_text, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if len(content) > 50:  # 十分な長さがある場合
                        return self.clean_text(content)
            
            # フォールバック: 全テキストの一部を返す
            if len(full_text) > 100:
                return self.clean_text(full_text[:1000])
            
            return ""
            
        except Exception as e:
            logger.error(f"質問内容抽出エラー: {str(e)}")
            return ""
    
    def extract_answer_content(self, soup: BeautifulSoup) -> str:
        """答弁内容を抽出"""
        try:
            # 答弁内容は質問と同じページにない場合が多いため、基本的に空文字を返す
            return ""
        except Exception as e:
            logger.error(f"答弁内容抽出エラー: {str(e)}")
            return ""
    
    def extract_questioner(self, soup: BeautifulSoup) -> str:
        """質問者を抽出"""
        try:
            page_text = soup.get_text()
            
            # 質問者名を探すパターン
            patterns = [
                r'提出者\s+([^\s\n]+)',
                r'提出者[：:]\s*([^\s\n]+)',
                r'([^\s\n]+)君提出',
                r'質問主意書提出者\s+([^\s\n]+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    questioner = match.group(1).strip()
                    # 名前の末尾調整
                    questioner = re.sub(r'君$', '君', questioner)
                    return questioner
            
            return ""
            
        except Exception as e:
            logger.error(f"質問者抽出エラー: {str(e)}")
            return ""
    
    def extract_date(self, soup: BeautifulSoup, date_type: str) -> str:
        """日付を抽出（提出日または答弁日）"""
        try:
            page_text = soup.get_text()
            
            if date_type == 'submission':
                patterns = [
                    r'(\d{4})年(\d{1,2})月(\d{1,2})日提出',
                    r'提出.*?(\d{4})年(\d{1,2})月(\d{1,2})日'
                ]
            else:  # answer
                patterns = [
                    r'(\d{4})年(\d{1,2})月(\d{1,2})日答弁',
                    r'答弁.*?(\d{4})年(\d{1,2})月(\d{1,2})日'
                ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return ""
            
        except Exception as e:
            logger.error(f"日付抽出エラー ({date_type}): {str(e)}")
            return ""
    
    def extract_document_links(self, soup: BeautifulSoup, base_url: str, doc_type: str) -> List[Dict[str, str]]:
        """HTML/PDFリンクを抽出"""
        links = []
        
        try:
            if doc_type == 'html':
                extensions = ['.htm', '.html']
                link_texts = ['質問(HTML)', 'HTML', '質問本文']
            else:  # pdf
                extensions = ['.pdf']
                link_texts = ['PDF', '質問本文(PDF)', '答弁本文(PDF)']
            
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 拡張子またはテキストでマッチ
                extension_match = any(ext in href.lower() for ext in extensions)
                text_match = any(link_text in text for link_text in link_texts)
                
                if extension_match or text_match:
                    full_url = urljoin(base_url, href)
                    links.append({
                        'url': full_url,
                        'title': text or f'{doc_type.upper()}文書',
                        'type': doc_type
                    })
            
        except Exception as e:
            logger.error(f"{doc_type}リンク抽出エラー: {str(e)}")
        
        return links
    
    def build_answer_url(self, question_url: str) -> str:
        """質問URLから答弁URLを構築"""
        try:
            # a217001.htm -> b217001.htm
            answer_url = question_url.replace('/a', '/b')
            if answer_url != question_url:
                return answer_url
            
            # フォールバック
            return question_url.replace('shitsumon', 'toushin')
            
        except Exception:
            return ""
    
    def classify_question_category(self, text: str) -> str:
        """質問カテゴリを分類"""
        categories = {
            '外交・安全保障': ['外交', '外務', '国際', '安保', '安全保障', '条約', '防衛', '自衛隊'],
            '経済・産業': ['経済', '財政', '予算', '税制', '金融', '産業', '企業', '投資'],
            '社会保障': ['年金', '医療', '介護', '福祉', '社会保障', '健康'],
            '教育・文化': ['教育', '学校', '大学', '文化', '文部科学'],
            '環境・エネルギー': ['環境', '気候', 'エネルギー', '原子力', '再生可能'],
            '労働・雇用': ['労働', '雇用', '働き方', '賃金', '職業'],
            '地方・都市': ['地方', '自治体', '都道府県', '市町村'],
            '司法・法務': ['司法', '裁判', '法務', '刑事', '民事'],
            '交通・国土': ['交通', '道路', '鉄道', '航空', '国土', '港湾']
        }
        
        text_lower = text.lower()
        
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        
        return '一般'
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # 改行・スペースの正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 連続空行を2行まで
        text = re.sub(r'[ \t]+', ' ', text)  # 連続スペースを1つに
        text = re.sub(r'[\u3000]+', ' ', text)  # 全角スペースを半角に
        
        return text.strip()
    
    def collect_all_questions(self) -> List[Dict[str, Any]]:
        """すべての質問主意書を収集"""
        logger.info("質問主意書収集開始...")
        all_questions = []
        
        try:
            # 利用可能なページを発見
            question_pages = self.discover_question_pages()
            
            if not question_pages:
                logger.warning("質問ページが見つかりませんでした")
                return []
            
            # 各ページから質問を収集
            for page_url in question_pages:
                if len(all_questions) >= self.max_questions:
                    logger.info(f"最大収集件数({self.max_questions})に到達しました")
                    break
                
                try:
                    questions_from_page = self.collect_questions_from_page(page_url)
                    all_questions.extend(questions_from_page)
                    logger.info(f"ページから{len(questions_from_page)}件の質問を収集: {page_url}")
                    
                    # レート制限対応
                    self.random_delay(2, 4)
                    
                except Exception as e:
                    logger.error(f"ページ収集エラー {page_url}: {str(e)}")
                    continue
            
            logger.info(f"質問主意書収集完了: {len(all_questions)}件")
            return all_questions
            
        except Exception as e:
            logger.error(f"質問主意書収集エラー: {str(e)}")
            return []
    
    def save_questions_data(self, questions: List[Dict[str, Any]]):
        """質問データを保存"""
        if not questions:
            logger.warning("保存する質問データがありません")
            return
        
        # データ期間を基準としたファイル名
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m%d')
        timestamp = current_date.strftime('%H%M%S')
        
        # 統一されたデータ構造
        data_structure = {
            "metadata": {
                "data_type": "shugiin_questions_enhanced",
                "collection_method": "enhanced_scraping",
                "total_questions": len(questions),
                "generated_at": current_date.isoformat(),
                "source_site": "www.shugiin.go.jp",
                "collection_period": {
                    "start_date": self.start_date,
                    "end_date": self.end_date,
                    "days_back": self.days_back
                },
                "data_quality": "enhanced_collection",
                "version": "2.0"
            },
            "data": questions
        }
        
        # 生データ保存
        raw_filename = f"questions_{data_period}_{timestamp}.json"
        raw_filepath = self.questions_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"questions_{data_period}_{timestamp}.json"
        frontend_filepath = self.frontend_questions_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        
        # 最新ファイル更新（データが正常な場合のみ）
        if len(questions) >= 10:  # 最低限の件数チェック
            latest_file = self.frontend_questions_dir / "questions_latest.json"
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(data_structure, f, ensure_ascii=False, indent=2)
            logger.info(f"📁 最新ファイル更新: {latest_file}")
        
        logger.info(f"質問データ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 件数: {len(questions)}")

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='質問主意書収集スクリプト（強化版）')
    parser.add_argument('--days', type=int, default=90, help='過去何日分を収集するか (デフォルト: 90日)')
    parser.add_argument('--max-questions', type=int, default=200, help='最大収集件数 (デフォルト: 200件)')
    
    args = parser.parse_args()
    
    collector = QuestionsCollectorEnhanced(
        days_back=args.days, 
        max_questions=args.max_questions
    )
    
    try:
        # 質問主意書収集
        questions = collector.collect_all_questions()
        
        if questions:
            # データ保存
            collector.save_questions_data(questions)
            logger.info(f"新規質問主意書収集完了: {len(questions)}件")
        else:
            logger.info("新規質問主意書は見つかりませんでした")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()