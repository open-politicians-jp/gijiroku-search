#!/usr/bin/env python3
"""
質問主意書収集スクリプト（増分収集版）

衆議院質問主意書データベースから実際の質問主意書情報を増分収集
既知のURL構造 a217001.htm, a217002.htm, ... を利用して効率的に収集
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

class QuestionsIncrementalCollector:
    """質問主意書増分収集クラス"""
    
    def __init__(self, max_questions: int = 100):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 収集パラメータ
        self.max_questions = max_questions
        
        # 対象となる国会回次（最近の3つの国会）
        self.target_sessions = [217, 216, 215]
        
        logger.info(f"最大収集件数: {self.max_questions}件")
        logger.info(f"対象国会: {', '.join(f'第{s}回' for s in self.target_sessions)}")
        
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
        existing_numbers = set()
        
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
                                # URLから質問番号を抽出
                                number = self.extract_question_number_from_url(question['question_url'])
                                if number:
                                    existing_numbers.add(number)
                            elif 'url' in question:
                                existing_urls.add(question['url'])
                                number = self.extract_question_number_from_url(question['url'])
                                if number:
                                    existing_numbers.add(number)
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
                            url = question.get('question_url') or question.get('url')
                            if url:
                                existing_urls.add(url)
                                number = self.extract_question_number_from_url(url)
                                if number:
                                    existing_numbers.add(number)
            except Exception as e:
                logger.warning(f"ファイル読み込みエラー {file_path}: {e}")
        
        logger.info(f"既存質問総数: {len(existing_urls)}件")
        logger.info(f"既存質問番号: {sorted(existing_numbers)[:10]}...等")
        return existing_urls
    
    def extract_question_number_from_url(self, url: str) -> Optional[str]:
        """URLから質問番号を抽出（国会+番号の組み合わせ）"""
        # a217001.htm -> 217001
        match = re.search(r'a(\d{6})\.htm', url)
        if match:
            return match.group(1)
        
        # より柔軟なパターン
        match = re.search(r'a(\d+)\.htm', url)
        if match:
            return match.group(1)
        
        return None
    
    def build_question_url(self, session: int, question_num: int) -> str:
        """質問URLを構築"""
        # 3桁の質問番号にフォーマット
        question_str = f"{question_num:03d}"
        filename = f"a{session}{question_str}.htm"
        return f"{self.base_url}/internet/itdb_shitsumon.nsf/html/shitsumon/{filename}"
    
    def check_question_exists(self, url: str) -> bool:
        """質問ページが存在するかチェック"""
        try:
            response = self.session.head(url, timeout=10)
            return response.status_code == 200
        except Exception:
            return False
    
    def collect_questions_incrementally(self) -> List[Dict[str, Any]]:
        """増分的に質問主意書を収集"""
        logger.info("質問主意書増分収集開始...")
        all_questions = []
        
        try:
            for session in self.target_sessions:
                logger.info(f"第{session}回国会の質問収集開始...")
                
                # 各セッションで1から順番にチェック
                question_num = 1
                consecutive_not_found = 0
                max_consecutive_not_found = 10  # 連続で見つからない場合の上限
                
                while len(all_questions) < self.max_questions and consecutive_not_found < max_consecutive_not_found:
                    question_url = self.build_question_url(session, question_num)
                    
                    # 既存データのチェック
                    if question_url in self.existing_questions:
                        logger.debug(f"既存質問をスキップ: {question_url}")
                        question_num += 1
                        consecutive_not_found = 0
                        continue
                    
                    # レート制限対応
                    self.random_delay()
                    self.update_headers()
                    
                    # 質問が存在するかチェック
                    if not self.check_question_exists(question_url):
                        logger.debug(f"質問が見つかりません: {question_url}")
                        consecutive_not_found += 1
                        question_num += 1
                        continue
                    
                    # 質問詳細を取得
                    try:
                        question_detail = self.extract_question_detail(question_url, session, question_num)
                        if question_detail:
                            all_questions.append(question_detail)
                            logger.info(f"質問取得成功 ({len(all_questions)}/{self.max_questions}): 第{session}回第{question_num}号 - {question_detail['title'][:50]}...")
                            consecutive_not_found = 0
                        else:
                            consecutive_not_found += 1
                    
                    except Exception as e:
                        logger.error(f"質問詳細取得エラー {question_url}: {str(e)}")
                        consecutive_not_found += 1
                    
                    question_num += 1
                    
                    # 最大番号チェック（通常は質問番号は100を超えることは稀）
                    if question_num > 200:
                        logger.info(f"第{session}回国会の質問番号が200を超えました。次の国会に移行します。")
                        break
                
                logger.info(f"第{session}回国会から{sum(1 for q in all_questions if q.get('session') == session)}件の質問を収集")
                
                # 最大収集件数に到達した場合は終了
                if len(all_questions) >= self.max_questions:
                    logger.info(f"最大収集件数({self.max_questions})に到達しました")
                    break
            
            logger.info(f"質問主意書増分収集完了: {len(all_questions)}件")
            return all_questions
            
        except Exception as e:
            logger.error(f"質問主意書増分収集エラー: {str(e)}")
            return all_questions
    
    def extract_question_detail(self, question_url: str, session: int, question_num: int) -> Optional[Dict[str, Any]]:
        """質問詳細ページから情報を抽出"""
        try:
            response = self.session.get(question_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 質問タイトルを抽出
            title = self.extract_title(soup)
            if not title:
                title = f"第{session}回国会質問第{question_num}号"
            
            # 質問内容を解析
            question_content = self.extract_question_content(soup)
            questioner = self.extract_questioner(soup)
            submission_date = self.extract_date(soup, 'submission')
            
            # HTML/PDFリンクを探す
            html_links = self.extract_document_links(soup, question_url, 'html')
            pdf_links = self.extract_document_links(soup, question_url, 'pdf')
            
            # 回答URLを構築
            answer_url = self.build_answer_url(question_url)
            
            question_detail = {
                'title': title,
                'question_number': str(question_num),
                'session': session,
                'questioner': questioner,
                'house': '衆議院',
                'submission_date': submission_date,
                'answer_date': '',  # 答弁日は別途取得が必要
                'question_content': question_content,
                'answer_content': '',  # 答弁内容は別途取得が必要
                'question_url': question_url,
                'answer_url': answer_url,
                'html_links': html_links,
                'pdf_links': pdf_links,
                'category': self.classify_question_category(title + " " + question_content),
                'collected_at': datetime.now().isoformat(),
                'year': datetime.now().year,
                'week': datetime.now().isocalendar()[1]
            }
            
            return question_detail
            
        except Exception as e:
            logger.error(f"質問詳細抽出エラー ({question_url}): {str(e)}")
            return None
    
    def extract_title(self, soup: BeautifulSoup) -> str:
        """質問タイトルを抽出"""
        try:
            # タイトルタグから抽出
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title and len(title) > 5:
                    return title
            
            # h1, h2タグから抽出
            for tag_name in ['h1', 'h2', 'h3']:
                header_tag = soup.find(tag_name)
                if header_tag:
                    title = header_tag.get_text(strip=True)
                    if title and len(title) > 5:
                        return title
            
            # 質問主意書のパターンを探す
            page_text = soup.get_text()
            title_patterns = [
                r'(.+?に関する質問主意書)',
                r'(.+?について.*?質問主意書)',
                r'(.+?)質問主意書'
            ]
            
            for pattern in title_patterns:
                match = re.search(pattern, page_text)
                if match:
                    title = match.group(1).strip()
                    if len(title) > 5:
                        return title + "に関する質問主意書"
            
            return ""
            
        except Exception as e:
            logger.error(f"タイトル抽出エラー: {str(e)}")
            return ""
    
    def extract_question_content(self, soup: BeautifulSoup) -> str:
        """質問内容を抽出"""
        try:
            full_text = soup.get_text(separator='\n', strip=True)
            
            # まずナビゲーション文言を除去
            cleaned_text = self.remove_navigation_text(full_text)
            
            # 質問部分を特定する様々なパターンを試す
            patterns = [
                r'質問主意書(.+?)右質問する',
                r'提出者\s+.+?(.+?)右質問する',
                r'(.{100,}?)右質問する'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, cleaned_text, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if len(content) > 50:
                        return self.clean_text(content)
            
            # フォールバック: 全テキストの一部を返す（ナビゲーション除去後）
            if len(cleaned_text) > 100:
                return self.clean_text(cleaned_text[:1000])
            
            return ""
            
        except Exception as e:
            logger.error(f"質問内容抽出エラー: {str(e)}")
            return ""
    
    def extract_questioner(self, soup: BeautifulSoup) -> str:
        """質問者を抽出"""
        try:
            page_text = soup.get_text()
            
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
                    if not questioner.endswith('君'):
                        questioner += '君'
                    return questioner
            
            return ""
            
        except Exception as e:
            logger.error(f"質問者抽出エラー: {str(e)}")
            return ""
    
    def extract_date(self, soup: BeautifulSoup, date_type: str) -> str:
        """日付を抽出"""
        try:
            page_text = soup.get_text()
            
            if date_type == 'submission':
                patterns = [
                    r'(\d{4})年(\d{1,2})月(\d{1,2})日提出',
                    r'提出.*?(\d{4})年(\d{1,2})月(\d{1,2})日',
                    r'令和(\d+)年(\d{1,2})月(\d{1,2})日提出'
                ]
            else:  # answer
                patterns = [
                    r'(\d{4})年(\d{1,2})月(\d{1,2})日答弁',
                    r'答弁.*?(\d{4})年(\d{1,2})月(\d{1,2})日'
                ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    groups = match.groups()
                    if len(groups) == 3:
                        year, month, day = groups
                        # 令和年号の処理
                        if len(year) <= 2:
                            year = str(2018 + int(year))
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return ""
            
        except Exception as e:
            logger.error(f"日付抽出エラー ({date_type}): {str(e)}")
            return ""
    
    def extract_document_links(self, soup: BeautifulSoup, base_url: str, doc_type: str) -> List[Dict[str, str]]:
        """質問主意書関連のHTML/PDFリンクを抽出（ナビゲーション系リンクのみ除外）"""
        links = []
        
        try:
            # 明確に除外すべきナビゲーション系のリンクテキストのみ
            excluded_texts = [
                'サイトマップ', 'ヘルプ', 'メインへスキップ', 'ホーム',
                '衆議院トップページ', '立法情報', '質問答弁情報',
                '質問の一覧', 'トップページ'
            ]
            
            # 明確に除外すべきURLパターンのみ
            excluded_url_patterns = [
                'sitemap', 'help', 'index.nsf', 'honkai_top', 
                'rippo_top', 'giin_top', 'shiryo_top', 'tetsuzuki_top', 
                'index_e', 'menu_m'
            ]
            
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 明確にナビゲーション系とわかるもののみ除外
                is_excluded = False
                
                # 除外すべきテキストかチェック
                for excluded_text in excluded_texts:
                    if excluded_text in text:
                        is_excluded = True
                        break
                
                if is_excluded:
                    continue
                
                # 除外すべきURLパターンかチェック
                for pattern in excluded_url_patterns:
                    if pattern in href.lower():
                        is_excluded = True
                        break
                
                if is_excluded:
                    continue
                
                # ドキュメントタイプに応じたフィルタリング
                if doc_type == 'html':
                    # HTMLリンク: .htm/.html拡張子 または 質問関連のキーワード
                    is_target = ('.htm' in href.lower() or 
                               '.html' in href.lower() or
                               'shitsumon' in href.lower() or
                               '経過' in text or
                               '質問本文' in text or
                               '答弁本文' in text)
                else:  # pdf
                    # PDFリンク: .pdf拡張子 または PDF関連のキーワード
                    is_target = ('.pdf' in href.lower() or
                               'PDF' in text)
                
                if is_target:
                    full_url = urljoin(base_url, href)
                    
                    # 重複チェック
                    if not any(existing['url'] == full_url for existing in links):
                        # 「HTML文書」などの汎用的すぎるタイトルは改善
                        display_title = text
                        if text == 'HTML文書' and 'shitsumon' in href:
                            if '/a' in href:
                                display_title = '質問本文'
                            elif '/b' in href:
                                display_title = '答弁本文'
                        
                        links.append({
                            'url': full_url,
                            'title': display_title or f'{doc_type.upper()}文書',
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
            return ""
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
    
    def remove_navigation_text(self, text: str) -> str:
        """ナビゲーション文言を除去"""
        if not text:
            return ""
        
        # 除去するナビゲーション文言のパターン
        navigation_patterns = [
            r'メインへスキップ',
            r'サイトマップ',
            r'ヘルプ',
            r'ブラウザのJavaScriptが無効のため、サイト内検索はご利用いただけません。',
            r'音声読み上げ',
            r'サイト内検索',
            r'衆議院トップページ\s*>',
            r'立法情報\s*>',
            r'質問答弁情報\s*>',
            r'第\d+回国会\s+質問の一覧\s*>',
            r'質問本文情報',
            r'経過へ\s*\|',
            r'質問本文\(PDF\)へ\s*\|',
            r'答弁本文\(HTML\)へ\s*\|',
            r'答弁本文\(PDF\)へ',
            r'読み上げ機能をご利用の場合は.*?をご一読ください。',
            r'なお、読み上げ機能利用の注意事項.*?BR',
            r'<[^>]+>',  # HTMLタグ
            r'&[a-zA-Z]+;',  # HTMLエンティティ
        ]
        
        # パターンに基づいて除去
        cleaned_text = text
        for pattern in navigation_patterns:
            cleaned_text = re.sub(pattern, '', cleaned_text, flags=re.IGNORECASE | re.MULTILINE)
        
        # 連続する改行やスペースを整理
        cleaned_text = re.sub(r'\n\s*\n\s*\n+', '\n\n', cleaned_text)
        cleaned_text = re.sub(r'^\s*[\|>\s]+', '', cleaned_text, flags=re.MULTILINE)
        
        return cleaned_text.strip()
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # 改行・スペースの正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)  # 連続空行を2行まで
        text = re.sub(r'[ \t]+', ' ', text)  # 連続スペースを1つに
        text = re.sub(r'[\u3000]+', ' ', text)  # 全角スペースを半角に
        
        # 追加のクリーニング
        text = re.sub(r'^\s*[\|>\s]+', '', text, flags=re.MULTILINE)  # 行頭の記号除去
        text = re.sub(r'\s*\|\s*', ' ', text)  # パイプ記号周辺の整理
        
        return text.strip()
    
    def save_questions_data(self, questions: List[Dict[str, Any]]):
        """質問データを保存"""
        if not questions:
            logger.warning("保存する質問データがありません")
            return
        
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m%d')
        timestamp = current_date.strftime('%H%M%S')
        
        data_structure = {
            "metadata": {
                "data_type": "shugiin_questions_incremental",
                "collection_method": "incremental_url_scanning",
                "total_questions": len(questions),
                "generated_at": current_date.isoformat(),
                "source_site": "www.shugiin.go.jp",
                "target_sessions": self.target_sessions,
                "data_quality": "incremental_collection",
                "version": "3.0"
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
        
        # 最新ファイル更新
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
    
    parser = argparse.ArgumentParser(description='質問主意書収集スクリプト（増分収集版）')
    parser.add_argument('--max-questions', type=int, default=100, help='最大収集件数 (デフォルト: 100件)')
    
    args = parser.parse_args()
    
    collector = QuestionsIncrementalCollector(max_questions=args.max_questions)
    
    try:
        # 質問主意書収集
        questions = collector.collect_questions_incrementally()
        
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