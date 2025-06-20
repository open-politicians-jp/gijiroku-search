#!/usr/bin/env python3
"""
質問主意書収集スクリプト（正式版）

衆議院質問主意書ページから実際の質問答弁情報を収集
https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/menu_m.htm
提出者、質問件名、HTML/PDFデータを取得
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

class QuestionsCollector:
    """質問主意書収集クラス（正式版）"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.questions_dir = self.project_root / "data" / "processed" / "questions"
        self.frontend_questions_dir = self.project_root / "frontend" / "public" / "data" / "questions"
        
        # ディレクトリ作成
        self.questions_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_questions_dir.mkdir(parents=True, exist_ok=True)
        
        # 週次ディレクトリ作成
        current_date = datetime.now()
        self.year = current_date.year
        self.week = current_date.isocalendar()[1]
        
        # 基本URL（正式版）
        self.base_url = "https://www.shugiin.go.jp"
        self.questions_main_url = "https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/menu_m.htm"
        
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
    
    def collect_questions(self) -> List[Dict[str, Any]]:
        """質問主意書収集（メインページから）"""
        logger.info("質問主意書収集開始...")
        questions = []
        
        try:
            # IP偽装のためヘッダー更新
            self.update_headers()
            self.random_delay()
            
            # メインページ取得
            response = self.session.get(self.questions_main_url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"メインページ取得成功: {self.questions_main_url}")
            
            # 質問主意書のリンクを探す
            question_links = self.extract_question_links(soup)
            logger.info(f"発見した質問主意書リンク数: {len(question_links)}")
            
            # 各質問主意書の詳細を取得
            for idx, link_info in enumerate(question_links):
                try:
                    self.random_delay()  # IP偽装のための遅延
                    self.update_headers()  # User-Agent更新
                    
                    question_detail = self.extract_question_detail(link_info)
                    if question_detail:
                        questions.append(question_detail)
                        logger.info(f"質問詳細取得成功 ({idx+1}/{len(question_links)}): {question_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"質問詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            logger.info(f"質問主意書収集完了: {len(questions)}件")
            return questions
            
        except Exception as e:
            logger.error(f"質問主意書収集エラー: {str(e)}")
            return []
    
    def extract_question_links(self, soup: BeautifulSoup) -> List[Dict[str, str]]:
        """メインページから質問主意書リンクを抽出"""
        links = []
        
        try:
            # 質問主意書のリンクパターンを探す
            link_elements = soup.find_all('a', href=True)
            
            for link in link_elements:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 質問主意書関連のリンクを判定
                if self.is_question_link(href, text):
                    full_url = urljoin(self.questions_main_url, href)
                    links.append({
                        'url': full_url,
                        'title': text,
                        'question_number': self.extract_question_number(text)
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
            logger.error(f"質問リンク抽出エラー: {str(e)}")
            return []
    
    def is_question_link(self, href: str, text: str) -> bool:
        """質問主意書リンクかどうか判定"""
        # 質問主意書関連キーワード
        question_keywords = [
            '質問主意書', '質問', 'question', 'shitsumon',
            '第', '号', '答弁書'
        ]
        
        # URL パターン
        url_patterns = [
            'itdb_shitsumon', 'shitsumon', 'question',
            'syuisyo', 'toushin'
        ]
        
        # テキストに質問キーワードが含まれるかチェック
        text_match = any(keyword in text for keyword in question_keywords)
        
        # URLに関連パターンが含まれるかチェック
        url_match = any(pattern in href.lower() for pattern in url_patterns)
        
        return text_match or url_match
    
    def extract_question_number(self, text: str) -> str:
        """質問番号を抽出"""
        # 「第〇号」パターンを抽出
        number_match = re.search(r'第(\d+)号', text)
        if number_match:
            return number_match.group(1)
        
        # 数字パターンを抽出
        digit_match = re.search(r'(\d+)', text)
        if digit_match:
            return digit_match.group(1)
        
        return ""
    
    def extract_question_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """質問詳細ページから情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 質問内容を解析
            question_content = self.extract_question_content(soup)
            answer_content = self.extract_answer_content(soup)
            questioner = self.extract_questioner(soup)
            submission_date = self.extract_submission_date(soup)
            answer_date = self.extract_answer_date(soup)
            
            # HTML/PDFリンクを探す
            html_links = self.extract_html_links(soup, link_info['url'])
            pdf_links = self.extract_pdf_links(soup, link_info['url'])
            
            question_detail = {
                'title': link_info['title'],
                'question_number': link_info['question_number'],
                'url': link_info['url'],
                'questioner': questioner,
                'submission_date': submission_date,
                'answer_date': answer_date,
                'question_content': question_content,
                'answer_content': answer_content,
                'html_links': html_links,
                'pdf_links': pdf_links,
                'house': '衆議院',
                'category': self.classify_question_category(link_info['title'] + " " + question_content),
                'collected_at': datetime.now().isoformat(),
                'year': self.year,
                'week': self.week
            }
            
            return question_detail
            
        except Exception as e:
            logger.error(f"質問詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_question_content(self, soup: BeautifulSoup) -> str:
        """質問内容を抽出"""
        try:
            # 質問内容を探すパターン
            content_selectors = [
                'div:contains("質問")',
                'td:contains("質問")',
                'p:contains("質問")',
                'div.question',
                'div.content'
            ]
            
            for selector in content_selectors:
                elements = soup.select(selector)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    if len(text) > 50:  # 短すぎるテキストは除外
                        return self.clean_text(text)
            
            # フォールバック: 全テキストから質問部分を抽出
            full_text = soup.get_text()
            question_start = full_text.find('質問')
            if question_start != -1:
                question_text = full_text[question_start:question_start+500]  # 500文字まで
                return self.clean_text(question_text)
            
            return ""
            
        except Exception as e:
            logger.error(f"質問内容抽出エラー: {str(e)}")
            return ""
    
    def extract_answer_content(self, soup: BeautifulSoup) -> str:
        """答弁内容を抽出"""
        try:
            # 答弁内容を探すパターン
            answer_keywords = ['答弁', '回答', '政府答弁書']
            
            for keyword in answer_keywords:
                elements = soup.find_all(text=re.compile(keyword))
                for elem in elements:
                    parent = elem.parent
                    if parent:
                        text = parent.get_text(strip=True)
                        if len(text) > 50:
                            return self.clean_text(text)
            
            return ""
            
        except Exception as e:
            logger.error(f"答弁内容抽出エラー: {str(e)}")
            return ""
    
    def extract_questioner(self, soup: BeautifulSoup) -> str:
        """質問者を抽出"""
        try:
            # 質問者名を探すパターン
            questioner_patterns = [
                r'提出者[：:]\s*([^\s\n]+)',
                r'質問者[：:]\s*([^\s\n]+)',
                r'([^\s\n]+)君提出'
            ]
            
            page_text = soup.get_text()
            
            for pattern in questioner_patterns:
                match = re.search(pattern, page_text)
                if match:
                    return match.group(1).strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"質問者抽出エラー: {str(e)}")
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
    
    def extract_answer_date(self, soup: BeautifulSoup) -> str:
        """答弁日を抽出"""
        try:
            date_patterns = [
                r'答弁日[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})年(\d{1,2})月(\d{1,2})日答弁'
            ]
            
            page_text = soup.get_text()
            
            for pattern in date_patterns:
                match = re.search(pattern, page_text)
                if match:
                    year, month, day = match.groups()
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return ""
            
        except Exception as e:
            logger.error(f"答弁日抽出エラー: {str(e)}")
            return ""
    
    def extract_html_links(self, soup: BeautifulSoup, base_url: str = None) -> List[Dict[str, str]]:
        """HTMLリンクを抽出"""
        links = []
        
        try:
            html_links = soup.find_all('a', href=re.compile(r'\.html?$'))
            
            for link in html_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href:
                    full_url = urljoin(base_url or self.base_url, href)
                    links.append({
                        'url': full_url,
                        'title': text or 'HTML文書'
                    })
            
        except Exception as e:
            logger.error(f"HTMLリンク抽出エラー: {str(e)}")
        
        return links
    
    def extract_pdf_links(self, soup: BeautifulSoup, base_url: str = None) -> List[Dict[str, str]]:
        """PDFリンクを抽出"""
        links = []
        
        try:
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf$'))
            
            for link in pdf_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href:
                    full_url = urljoin(base_url or self.base_url, href)
                    links.append({
                        'url': full_url,
                        'title': text or 'PDF文書'
                    })
            
        except Exception as e:
            logger.error(f"PDFリンク抽出エラー: {str(e)}")
        
        return links
    
    def classify_question_category(self, text: str) -> str:
        """質問カテゴリを分類"""
        text_lower = text.lower()
        
        categories = {
            '外交': ['外交', '外務', '国際', '安保', '安全保障', '条約'],
            '内政': ['内政', '行政', '政府', '省庁', '公務員'],
            '経済': ['経済', '財政', '予算', '税制', '金融', '産業'],
            '社会保障': ['年金', '医療', '介護', '福祉', '社会保障'],
            '教育': ['教育', '学校', '大学', '文部科学'],
            '環境': ['環境', '気候', 'エネルギー', '原子力'],
            '労働': ['労働', '雇用', '働き方', '賃金'],
            '防衛': ['防衛', '自衛隊', '軍事'],
            '司法': ['司法', '裁判', '法務', '刑事'],
            '地方': ['地方', '自治体', '都道府県', '市町村']
        }
        
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
    
    def save_questions_data(self, questions: List[Dict[str, Any]]):
        """質問データを保存"""
        if not questions:
            logger.warning("保存する質問データがありません")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生データ保存
        raw_filename = f"questions_{timestamp}.json"
        raw_filepath = self.questions_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"questions_{timestamp}.json"
        frontend_filepath = self.frontend_questions_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
        
        logger.info(f"質問データ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 件数: {len(questions)}")

def main():
    """メイン実行関数"""
    collector = QuestionsCollector()
    
    try:
        # 質問主意書収集
        questions = collector.collect_questions()
        
        # データ保存
        collector.save_questions_data(questions)
        
        logger.info("質問主意書収集処理完了")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()