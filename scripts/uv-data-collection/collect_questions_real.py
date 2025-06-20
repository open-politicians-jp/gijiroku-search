#!/usr/bin/env python3
"""
質問主意書収集スクリプト（実データ版）

衆議院質問主意書ページから実際の質問答弁情報を収集
実際のサイト構造に基づいた正確なデータ抽出
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

class RealQuestionsCollector:
    """質問主意書収集クラス（実データ版）"""
    
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
        
        # 基本URL（実際のサイト構造に基づく）
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
    
    def random_delay(self, min_seconds=2, max_seconds=5):
        """ランダム遅延でレート制限対応"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def collect_questions(self, limit: int = 50) -> List[Dict[str, Any]]:
        """質問主意書収集（メインページから）"""
        logger.info(f"質問主意書収集開始（上限{limit}件）...")
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
            
            # 実際のテーブル構造から質問リンクを抽出
            question_links = self.extract_real_question_links(soup, limit)
            logger.info(f"発見した質問主意書リンク数: {len(question_links)}")
            
            # 各質問主意書の詳細を取得
            for idx, link_info in enumerate(question_links):
                try:
                    self.random_delay()  # IP偽装のための遅延
                    self.update_headers()  # User-Agent更新
                    
                    question_detail = self.extract_real_question_detail(link_info)
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
    
    def extract_real_question_links(self, soup: BeautifulSoup, limit: int) -> List[Dict[str, str]]:
        """実際のテーブル構造から質問主意書リンクを抽出"""
        links = []
        
        try:
            # テーブル行を取得（実際のサイト構造に基づく）
            tables = soup.find_all('table')
            
            for table in tables:
                rows = table.find_all('tr')
                
                for row in rows:
                    cells = row.find_all(['td', 'th'])
                    
                    # 適切な行構造を確認（番号、タイトル、質問者、リンクなど）
                    if len(cells) >= 4:  # 最低限の列数
                        question_data = self.parse_table_row(cells)
                        if question_data and len(links) < limit:
                            links.append(question_data)
            
            return links[:limit]
            
        except Exception as e:
            logger.error(f"質問リンク抽出エラー: {str(e)}")
            return []
    
    def parse_table_row(self, cells: List) -> Optional[Dict[str, str]]:
        """テーブル行から質問情報を解析"""
        try:
            # 実際のサイト構造に基づく解析
            if len(cells) < 4:
                return None
            
            # 番号（通常は最初の列）
            number_cell = cells[0]
            number_text = number_cell.get_text(strip=True)
            
            # 数字が含まれているか確認
            if not re.search(r'\d+', number_text):
                return None
            
            # タイトル（通常は2番目の列）
            title_cell = cells[1] if len(cells) > 1 else None
            title = title_cell.get_text(strip=True) if title_cell else ""
            
            # 質問者（通常は3番目の列）
            questioner_cell = cells[2] if len(cells) > 2 else None
            questioner = questioner_cell.get_text(strip=True) if questioner_cell else ""
            
            # HTMLリンクを探す
            question_link = None
            for cell in cells:
                links = cell.find_all('a', href=True)
                for link in links:
                    href = link.get('href', '')
                    link_text = link.get_text(strip=True)
                    
                    # 質問HTMLファイルのリンクを特定
                    if 'a217' in href and '.htm' in href and 'HTML' in link_text:
                        question_link = urljoin(self.questions_main_url, href)
                        break
                
                if question_link:
                    break
            
            if not question_link:
                return None
            
            return {
                'url': question_link,
                'title': title,
                'questioner': questioner,
                'question_number': re.search(r'\d+', number_text).group(0) if re.search(r'\d+', number_text) else ""
            }
            
        except Exception as e:
            logger.error(f"テーブル行解析エラー: {str(e)}")
            return None
    
    def extract_real_question_detail(self, link_info: Dict[str, str]) -> Optional[Dict[str, Any]]:
        """実際の質問詳細ページから情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 実際のページ構造から情報を抽出
            question_content = self.extract_real_question_content(soup)
            answer_content = self.extract_real_answer_content(soup)
            submission_date = self.extract_real_date(soup, 'submission')
            answer_date = self.extract_real_date(soup, 'answer')
            
            # PDF/HTMLリンクを正確に抽出
            pdf_links = self.extract_real_pdf_links(soup, link_info['url'])
            html_links = self.extract_real_html_links(soup, link_info['url'])
            
            question_detail = {
                'title': link_info['title'],
                'question_number': link_info['question_number'],
                'questioner': link_info['questioner'],
                'house': '衆議院',
                'submission_date': submission_date,
                'answer_date': answer_date,
                'question_content': question_content,
                'answer_content': answer_content,
                'question_url': link_info['url'],
                'answer_url': self.find_answer_url(soup, link_info['url']),
                'html_links': html_links,
                'pdf_links': pdf_links,
                'category': self.classify_real_category(question_content),
                'collected_at': datetime.now().isoformat(),
                'year': datetime.now().year,
                'week': datetime.now().isocalendar()[1]
            }
            
            return question_detail
            
        except Exception as e:
            logger.error(f"質問詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_real_question_content(self, soup: BeautifulSoup) -> str:
        """実際の質問内容を抽出"""
        try:
            # 実際のページ構造に基づく抽出
            content_patterns = [
                # メインコンテンツエリア
                'div.main-content',
                'div.content',
                'table.main',
                # テキスト量の多いエリア
                'td',
                'div',
                'p'
            ]
            
            best_content = ""
            max_length = 0
            
            for pattern in content_patterns:
                elements = soup.select(pattern)
                for elem in elements:
                    text = elem.get_text(strip=True)
                    # ノイズとなるナビゲーションやヘッダーを除外
                    # より長いコンテンツを優先し、実際の質問内容を取得
                    if (len(text) > 200 and 
                        '質問主意書' in text and 
                        'メニュー' not in text and
                        'ナビゲーション' not in text and
                        ('政府は' in text or '以下' in text or '右質問する' in text)):
                        if len(text) > max_length:
                            max_length = len(text)
                            best_content = text
            
            # パンくずナビゲーションやヘッダー情報を除去
            cleaned_content = self.remove_navigation_noise(best_content)
            return self.clean_text(cleaned_content) if cleaned_content else ""
            
        except Exception as e:
            logger.error(f"質問内容抽出エラー: {str(e)}")
            return ""
    
    def extract_real_answer_content(self, soup: BeautifulSoup) -> str:
        """実際の答弁内容を抽出"""
        try:
            # 答弁書や政府答弁関連のテキストを探す
            answer_keywords = ['答弁書', '政府答弁', '回答', '見解']
            
            for keyword in answer_keywords:
                elements = soup.find_all(text=re.compile(keyword))
                for elem in elements:
                    parent = elem.parent
                    if parent:
                        # 答弁内容を含む可能性のある親要素を確認
                        answer_area = parent.find_parent(['td', 'div', 'section'])
                        if answer_area:
                            text = answer_area.get_text(strip=True)
                            if len(text) > 100:  # 十分な長さがある場合
                                return self.clean_text(text)
            
            return ""
            
        except Exception as e:
            logger.error(f"答弁内容抽出エラー: {str(e)}")
            return ""
    
    def extract_real_date(self, soup: BeautifulSoup, date_type: str) -> str:
        """実際の日付を抽出"""
        try:
            date_patterns = [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
                r'(\d{4})-(\d{1,2})-(\d{1,2})'
            ]
            
            text = soup.get_text()
            
            # 日付パターンを検索
            for pattern in date_patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    year, month, day = match.groups()
                    # 妥当な日付かチェック
                    try:
                        date_obj = datetime(int(year), int(month), int(day))
                        # 現在より未来の日付や古すぎる日付を除外
                        if 2000 <= date_obj.year <= datetime.now().year + 1:
                            return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                    except ValueError:
                        continue
            
            return ""
            
        except Exception as e:
            logger.error(f"日付抽出エラー: {str(e)}")
            return ""
    
    def extract_real_pdf_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """実際のPDFリンクを抽出"""
        links = []
        seen_urls = set()
        
        try:
            pdf_links = soup.find_all('a', href=re.compile(r'\.pdf'))
            
            for link in pdf_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href:
                    full_url = urljoin(base_url, href)
                    # 重複チェック
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        links.append({
                            'url': full_url,
                            'title': text,
                            'type': 'pdf'
                        })
            
        except Exception as e:
            logger.error(f"PDFリンク抽出エラー: {str(e)}")
        
        return links
    
    def extract_real_html_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """実際のHTMLリンクを抽出"""
        links = []
        seen_urls = set()
        
        try:
            # 現在のページ自体を含める
            links.append({
                'url': base_url,
                'title': '質問(HTML)',
                'type': 'html'
            })
            seen_urls.add(base_url)
            
            # 関連するHTMLリンクがあれば追加
            html_links = soup.find_all('a', href=re.compile(r'\.html?'))
            
            for link in html_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if href and 'shitsumon' in href:
                    full_url = urljoin(base_url, href)
                    # 重複チェック
                    if full_url not in seen_urls:
                        seen_urls.add(full_url)
                        links.append({
                            'url': full_url,
                            'title': text,
                            'type': 'html'
                        })
            
        except Exception as e:
            logger.error(f"HTMLリンク抽出エラー: {str(e)}")
        
        return links
    
    def find_answer_url(self, soup: BeautifulSoup, question_url: str) -> str:
        """答弁書のURLを探す"""
        try:
            # 答弁書リンクを探す
            answer_links = soup.find_all('a', href=True)
            
            for link in answer_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                if '答弁' in text and ('.htm' in href or '.pdf' in href):
                    return urljoin(question_url, href)
            
            return ""
            
        except Exception as e:
            logger.error(f"答弁URL抽出エラー: {str(e)}")
            return ""
    
    def classify_real_category(self, content: str) -> str:
        """実際の内容からカテゴリを分類"""
        if not content:
            return '一般'
        
        content_lower = content.lower()
        
        categories = {
            '外交・安全保障': ['外交', '安全保障', '防衛', '自衛隊', '軍事', '国際', '条約', '安保'],
            '経済・産業': ['経済', '産業', '企業', '金融', '市場', '投資', '貿易', '商業'],
            '社会保障・福祉': ['年金', '医療', '介護', '福祉', '社会保障', '健康保険', '生活保護'],
            '教育・文化': ['教育', '学校', '大学', '文化', 'スポーツ', '学習', '研究'],
            '環境・エネルギー': ['環境', '気候', 'エネルギー', '原子力', '再生可能', '温暖化'],
            '労働・雇用': ['労働', '雇用', '働き方', '賃金', '職場', '失業', '就職'],
            '行政・法務': ['行政', '法務', '司法', '裁判', '法律', '規制', '制度'],
            '地方・都市': ['地方', '自治体', '都市', '地域', '市町村', '都道府県'],
            '予算・税制': ['予算', '税', '財政', '歳入', '歳出', '国債', '税制']
        }
        
        for category, keywords in categories.items():
            if any(keyword in content_lower for keyword in keywords):
                return category
        
        return '一般'
    
    def remove_navigation_noise(self, text: str) -> str:
        """パンくずナビゲーションやヘッダー情報を除去"""
        if not text:
            return ""
        
        # パンくずナビゲーションのパターンを除去
        navigation_patterns = [
            r'衆議院トップページ>.*?質問主意書',
            r'衆議院トップページ>.*?質問の一覧>',
            r'質問本文情報経過へ\|.*?答弁本文\(PDF\)へ',
            r'経過へ\|.*?答弁本文\(PDF\)へ',
            r'^令和\d+年\d+月\d+日提出質問第\d+号.*?質問主意書',
            r'^提出者\s+[^\n]+\n',
            r'^.*?質問主意書質問本文情報',
            r'^.*?質問主意書提出者.*?\n',
            # 質問の実際の開始部分を保持するため、タイトル重複のみ除去
            r'^(.+質問主意書)\1',
            # ページ末尾のナビゲーション
            r'経過へ$',
            r'質問本文\(PDF\)へ$',
            r'答弁本文\(HTML\)へ$',
            r'答弁本文\(PDF\)へ$'
        ]
        
        cleaned_text = text
        for pattern in navigation_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.MULTILINE)
        
        # 質問主意書のタイトル重複を除去
        title_pattern = r'^(.+質問主意書)\1+'
        cleaned_text = re.sub(title_pattern, r'\1', cleaned_text, flags=re.MULTILINE)
        
        return cleaned_text.strip()
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # 改行・スペースの正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 連続空行を2行まで
        text = re.sub(r'[ \t]+', ' ', text)  # 連続スペースを1つに
        text = re.sub(r'[\u3000]+', ' ', text)  # 全角スペースを半角に
        text = re.sub(r'^[\s\n]+|[\s\n]+$', '', text)  # 前後の空白除去
        
        return text.strip()
    
    def save_questions_data(self, questions: List[Dict[str, Any]]):
        """質問データを保存"""
        if not questions:
            logger.warning("保存する質問データがありません")
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # メタデータ付きでデータを構造化
        structured_data = {
            'metadata': {
                'data_type': 'questions_real',
                'total_count': len(questions),
                'generated_at': datetime.now().isoformat(),
                'source': '衆議院質問主意書データベース（実データ）',
                'collection_method': 'real_site_scraping',
                'data_quality': 'authentic'
            },
            'data': questions
        }
        
        # 生データ保存
        raw_filename = f"questions_real_{timestamp}.json"
        raw_filepath = self.questions_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"questions_real_{timestamp}.json"
        frontend_filepath = self.frontend_questions_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        # 最新データファイルとしてもコピー
        latest_filepath = self.frontend_questions_dir / "questions_latest.json"
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(structured_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"質問データ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 最新版: {latest_filepath}")
        logger.info(f"  - 件数: {len(questions)}")

def main():
    """メイン実行関数"""
    collector = RealQuestionsCollector()
    
    try:
        # 質問主意書収集（テスト用に少数から始める）
        questions = collector.collect_questions(limit=10)
        
        # データ保存
        collector.save_questions_data(questions)
        
        logger.info("質問主意書収集処理完了（実データ版）")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()