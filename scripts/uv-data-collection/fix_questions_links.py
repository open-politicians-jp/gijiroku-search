#!/usr/bin/env python3
"""
質問主意書リンク修正スクリプト

既存の質問データのquestion_urlとanswer_urlフィールドを修正し、
フロントエンドで適切にリンクが表示されるようにする
"""

import json
import requests
import time
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from fake_useragent import UserAgent
from bs4 import BeautifulSoup
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class QuestionsLinksFixture:
    """質問主意書リンク修正クラス"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_questions_dir = self.project_root / "frontend" / "public" / "data" / "questions"
        
        # 基本URL
        self.base_url = "https://www.shugiin.go.jp"
        
    def update_headers(self):
        """User-Agent更新"""
        self.session.headers.update({
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        })
    
    def normalize_url(self, url: str) -> str:
        """URLを絶対URLに変換"""
        if not url:
            return url
        
        if url.startswith('http'):
            return url
        
        # 相対URLを絶対URLに変換
        if url.startswith('/'):
            return f"https://www.shugiin.go.jp{url}"
        elif url.startswith('../'):
            # ../../../itdb_shitsumon_pdf_s.nsf/html/shitsumon/pdfS/a217001.pdf/$File/a217001.pdf
            # を https://www.shugiin.go.jp/internet/itdb_shitsumon_pdf_s.nsf/html/shitsumon/pdfS/a217001.pdf/$File/a217001.pdf に変換
            clean_url = url.replace('../../../', '')
            return f"https://www.shugiin.go.jp/internet/{clean_url}"
        else:
            # 相対パスの場合は基本パスに追加
            return f"https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/{url}"

    def fix_question_links(self, question: Dict[str, Any]) -> Dict[str, Any]:
        """質問データのリンクを修正"""
        try:
            # 既存のurlを正規化してquestion_urlに設定
            if question.get('url'):
                normalized_url = self.normalize_url(question['url'])
                question['question_url'] = normalized_url
                question['url'] = normalized_url  # 元のurlも修正
            
            # タイトルがHTMLの場合、HTML版のリンクとして扱う
            title = question.get('title', '')
            if 'HTML' in title and question.get('question_url'):
                # HTMLリンクリストに追加
                if not question.get('html_links'):
                    question['html_links'] = []
                
                # 重複チェック
                existing_urls = [link.get('url') for link in question.get('html_links', [])]
                if question['question_url'] not in existing_urls:
                    question['html_links'].append({
                        'url': question['question_url'],
                        'title': title
                    })
            
            # PDFの場合、PDFリンクとして追加し、対応するHTMLも生成
            if 'PDF' in title and question.get('question_url'):
                # PDFリンクリストに追加
                if not question.get('pdf_links'):
                    question['pdf_links'] = []
                
                # 重複チェック
                existing_urls = [link.get('url') for link in question.get('pdf_links', [])]
                if question['question_url'] not in existing_urls:
                    question['pdf_links'].append({
                        'url': question['question_url'],
                        'title': title
                    })
                
                # PDFからHTMLリンクを生成
                pdf_url = question['question_url']
                match = re.search(r'(a\d+)\.pdf', pdf_url)
                if match:
                    question_id = match.group(1)
                    html_url = f"https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/{question_id}.htm"
                    
                    # HTML版リンクを別途追加
                    if not question.get('html_links'):
                        question['html_links'] = []
                    
                    # 重複チェック
                    existing_html_urls = [link.get('url') for link in question.get('html_links', [])]
                    if html_url not in existing_html_urls:
                        question['html_links'].append({
                            'url': html_url,
                            'title': '質問(HTML)'
                        })
                        
                        # HTML版をquestion_urlとして優先設定
                        question['question_url'] = html_url
            
            # 答弁URLの設定
            if not question.get('answer_url'):
                # PDFリンクから答弁書を探す
                for pdf_link in question.get('pdf_links', []):
                    if '答弁' in pdf_link.get('title', ''):
                        pdf_url = pdf_link.get('url', '')
                        # 答弁PDFから答弁HTMLを生成
                        match = re.search(r'(b\d+)\.pdf', pdf_url)
                        if match:
                            answer_id = match.group(1)
                            answer_html_url = f"https://www.shugiin.go.jp/internet/itdb_shitsumon.nsf/html/shitsumon/{answer_id}.htm"
                            question['answer_url'] = answer_html_url
                            break
            
            return question
            
        except Exception as e:
            logger.error(f"質問リンク修正エラー: {e}")
            return question
    
    def process_questions_file(self, file_path: Path) -> bool:
        """質問ファイルを処理"""
        try:
            logger.info(f"処理開始: {file_path.name}")
            
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # データ構造を確認
            if isinstance(data, dict) and 'data' in data:
                questions = data['data']
                metadata = data.get('metadata', {})
            elif isinstance(data, list):
                questions = data
                metadata = {}
            else:
                logger.error(f"不明なデータ構造: {file_path.name}")
                return False
            
            # 各質問のリンクを修正
            fixed_questions = []
            fix_count = 0
            
            for question in questions:
                if isinstance(question, dict):
                    original_question_url = question.get('question_url', '')
                    fixed_question = self.fix_question_links(question)
                    fixed_questions.append(fixed_question)
                    
                    # 修正されたかチェック
                    if fixed_question.get('question_url') != original_question_url:
                        fix_count += 1
                else:
                    fixed_questions.append(question)
            
            # 修正したデータを保存
            if isinstance(data, dict):
                # メタデータを更新
                metadata['fixed_at'] = datetime.now().isoformat()
                metadata['fixes_applied'] = fix_count
                
                fixed_data = {
                    'metadata': metadata,
                    'data': fixed_questions
                }
            else:
                fixed_data = fixed_questions
            
            # バックアップは作成しない（不要なため）
            
            # 修正データを保存
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(fixed_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"✅ 修正完了: {file_path.name} ({fix_count}件修正)")
            return True
            
        except Exception as e:
            logger.error(f"❌ ファイル処理エラー ({file_path.name}): {e}")
            return False
    
    def fix_all_questions(self):
        """全質問データファイルのリンクを修正"""
        logger.info("質問データリンク修正開始...")
        
        # 質問データファイルを探す
        question_files = list(self.frontend_questions_dir.glob("questions_*.json"))
        
        if not question_files:
            logger.warning("質問データファイルが見つかりません")
            return
        
        logger.info(f"発見した質問データファイル数: {len(question_files)}")
        
        # 各ファイルを処理
        success_count = 0
        for file_path in question_files:
            if self.process_questions_file(file_path):
                success_count += 1
            time.sleep(1)  # レート制限
        
        logger.info(f"✨ 質問データリンク修正完了: {success_count}/{len(question_files)}件成功")

def main():
    """メイン処理"""
    fixture = QuestionsLinksFixture()
    fixture.fix_all_questions()

if __name__ == "__main__":
    main()