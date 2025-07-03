#!/usr/bin/env python3
"""
提出法案収集スクリプト（強化版）

衆議院議案データベースから実際の議案データを効率的に収集
https://www.shugiin.go.jp/internet/itdb_gian.nsf/html/gian/kaiji217.htm
適切なデータ構造とリンク修正を実装
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
from urllib.parse import urljoin, urlparse

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class BillsEnhancedCollector:
    """提出法案収集クラス（強化版）"""
    
    def __init__(self, max_bills: int = 50):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 収集パラメータ
        self.max_bills = max_bills
        
        # 対象となる国会回次
        self.target_sessions = [217, 216]
        
        logger.info(f"最大収集件数: {self.max_bills}件")
        logger.info(f"対象国会: {', '.join(f'第{s}回' for s in self.target_sessions)}")
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.bills_dir = self.project_root / "data" / "processed" / "bills"
        self.frontend_bills_dir = self.project_root / "frontend" / "public" / "data" / "bills"
        
        # ディレクトリ作成
        self.bills_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_bills_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    def build_absolute_url(self, href: str, base_page_url: str) -> Optional[str]:
        """相対URLを絶対URLに変換"""
        if not href or href.strip() == '':
            return None
        
        # アンカーリンク（#で始まる）は無効
        if href.startswith('#'):
            return None
        
        # 既に絶対URLの場合
        if href.startswith('http'):
            return href
        
        # 相対URL処理
        if href.startswith('./'):
            # ./honbun/g20009011.htm
            relative_path = href[2:]
            base_dir = '/'.join(base_page_url.split('/')[:-1])
            return f"{base_dir}/{relative_path}"
        
        elif href.startswith('/'):
            # 絶対パス
            return f"{self.base_url}{href}"
        
        else:
            # 相対パス
            base_dir = '/'.join(base_page_url.split('/')[:-1])
            return f"{base_dir}/{href}"
    
    def collect_bills_from_session(self, session_number: int) -> List[Dict[str, Any]]:
        """特定の国会から議案を収集"""
        bills = []
        
        try:
            # 国会別議案一覧ページURL
            session_url = f"{self.base_url}/internet/itdb_gian.nsf/html/gian/kaiji{session_number}.htm"
            
            self.update_headers()
            self.random_delay()
            
            response = self.session.get(session_url, timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            logger.info(f"第{session_number}回国会ページ取得成功: {session_url}")
            
            # 議案リンクを抽出（より厳密に）
            bill_links = self.extract_bill_links(soup, session_url, session_number)
            logger.info(f"有効な議案リンク数: {len(bill_links)}")
            
            # 各議案の詳細を取得（制限付き）
            collected_count = 0
            for idx, link_info in enumerate(bill_links):
                if collected_count >= self.max_bills // len(self.target_sessions):
                    logger.info(f"第{session_number}回国会の収集上限({self.max_bills // len(self.target_sessions)})に到達")
                    break
                
                try:
                    self.random_delay()
                    self.update_headers()
                    
                    bill_detail = self.extract_bill_detail(link_info, session_number)
                    if bill_detail and self.validate_bill_data(bill_detail):
                        bills.append(bill_detail)
                        collected_count += 1
                        logger.info(f"議案取得成功 ({collected_count}): {bill_detail['title'][:50]}...")
                    
                except Exception as e:
                    logger.error(f"議案詳細取得エラー ({idx+1}): {str(e)}")
                    continue
            
            return bills
            
        except Exception as e:
            logger.error(f"第{session_number}回国会の議案収集エラー: {str(e)}")
            return []
    
    def extract_bill_links(self, soup: BeautifulSoup, base_url: str, session_number: int) -> List[Dict[str, str]]:
        """議案リンクを抽出（より厳密なフィルタリング）"""
        links = []
        
        try:
            # より厳密な議案リンクの判定
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 実際の議案ページかどうかを厳密に判定
                if self.is_valid_bill_link(href, text):
                    full_url = self.build_absolute_url(href, base_url)
                    if not full_url:
                        continue
                    
                    bill_number = self.extract_bill_number(text, href)
                    
                    links.append({
                        'url': full_url,
                        'title': text,
                        'bill_number': bill_number,
                        'session_number': session_number
                    })
            
            # 重複除去とフィルタリング
            unique_links = []
            seen_urls = set()
            
            for link in links:
                # 無効なリンクを除外
                if (link['url'] not in seen_urls and 
                    len(link['title']) > 10 and  # タイトルが短すぎるものを除外
                    not any(invalid in link['title'].lower() for invalid in ['メニュー', 'トップ', 'リンク', 'ページ'])):
                    unique_links.append(link)
                    seen_urls.add(link['url'])
            
            return unique_links[:50]  # 最大50件に制限
            
        except Exception as e:
            logger.error(f"議案リンク抽出エラー: {str(e)}")
            return []
    
    def is_valid_bill_link(self, href: str, text: str) -> bool:
        """有効な議案リンクかどうか判定"""
        # 無効なリンクを除外
        if not href or href.startswith('#') or href.strip() == '':
            return False
        
        # 除外すべきパターン
        exclude_patterns = [
            'menu', 'index', 'top', 'search', 'help', 'site',
            'javascript:', 'mailto:', 'pdf', 'doc'
        ]
        
        for pattern in exclude_patterns:
            if pattern in href.lower() or pattern in text.lower():
                return False
        
        # 議案関連キーワード（より厳密）
        bill_keywords = [
            '法案', '法律案', '改正案', '設置法', '廃止法',
            '予算', '決算', '条約', '承認', '議決',
            '第.*号', '案'
        ]
        
        # URLパターン（議案本文や経過情報）
        url_patterns = [
            'honbun/', 'keika/', 'gian', '.htm'
        ]
        
        # テキストまたはURLに議案関連要素が含まれているか
        text_match = any(re.search(keyword, text) for keyword in bill_keywords)
        url_match = any(pattern in href.lower() for pattern in url_patterns)
        
        return text_match and url_match and len(text) > 5
    
    def extract_bill_number(self, text: str, href: str) -> str:
        """議案番号を抽出"""
        # テキストから番号を抽出
        patterns = [
            r'第(\d+)号',
            r'(\d+)号',
            r'第(\d+)',
            r'(\d+)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1)
        
        # URLから番号を抽出
        url_match = re.search(r'(\d+)', href)
        if url_match:
            return url_match.group(1)
        
        return ""
    
    def extract_bill_detail(self, link_info: Dict[str, str], session_number: int) -> Optional[Dict[str, Any]]:
        """議案詳細ページから情報を抽出"""
        try:
            response = self.session.get(link_info['url'], timeout=30)
            response.raise_for_status()
            response.encoding = 'shift_jis'
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 議案情報を解析
            title = self.extract_bill_title(soup, link_info['title'])
            bill_content = self.extract_bill_content(soup)
            submitter = self.extract_submitter(soup)
            submission_date = self.extract_submission_date(soup)
            status = self.extract_status(soup)
            committee = self.extract_committee(soup)
            
            # 関連リンクを抽出
            related_links = self.extract_related_links(soup, link_info['url'])
            
            bill_detail = {
                'title': title,
                'bill_number': link_info['bill_number'],
                'session_number': session_number,
                'url': link_info['url'],
                'submitter': submitter,
                'submission_date': submission_date,
                'status': status,
                'status_normalized': self.normalize_status(status),
                'committee': committee,
                'bill_content': bill_content,
                'related_links': related_links,
                'summary': self.generate_summary(bill_content, title),
                'category': self.classify_bill_category(title),
                'collected_at': datetime.now().isoformat(),
                'year': datetime.now().year
            }
            
            return bill_detail
            
        except Exception as e:
            logger.error(f"議案詳細抽出エラー ({link_info['url']}): {str(e)}")
            return None
    
    def extract_bill_title(self, soup: BeautifulSoup, fallback_title: str) -> str:
        """議案タイトルを抽出"""
        try:
            # titleタグから抽出
            title_tag = soup.find('title')
            if title_tag:
                title = title_tag.get_text(strip=True)
                if title and len(title) > 10 and '議案' not in title:
                    return title
            
            # h1, h2タグから抽出
            for tag_name in ['h1', 'h2', 'h3']:
                header_tag = soup.find(tag_name)
                if header_tag:
                    title = header_tag.get_text(strip=True)
                    if title and len(title) > 10:
                        return title
            
            # ページテキストから法案名を抽出
            page_text = soup.get_text()
            
            # 法案名パターン
            title_patterns = [
                r'(.+?法案)',
                r'(.+?法律案)',
                r'(.+?改正案)',
                r'(.+?設置法)',
                r'(.+?廃止法)'
            ]
            
            for pattern in title_patterns:
                matches = re.findall(pattern, page_text)
                for match in matches:
                    if len(match) > 10 and len(match) < 100:
                        return match.strip()
            
            # フォールバック
            if fallback_title and len(fallback_title) > 10:
                return fallback_title
            
            return "法案タイトル未取得"
            
        except Exception as e:
            logger.error(f"議案タイトル抽出エラー: {str(e)}")
            return fallback_title or "タイトル抽出エラー"
    
    def extract_bill_content(self, soup: BeautifulSoup) -> str:
        """議案本文を抽出"""
        try:
            # より広範囲からテキストを抽出
            full_text = soup.get_text(separator='\n', strip=True)
            
            # 法案本文部分を特定
            content_patterns = [
                r'第一条(.+?)附則',
                r'（目的）(.+?)附則',
                r'この法律は(.+?)。',
                r'(.{200,1000})'
            ]
            
            for pattern in content_patterns:
                match = re.search(pattern, full_text, re.DOTALL)
                if match:
                    content = match.group(1).strip()
                    if len(content) > 50:
                        return self.clean_text(content)
            
            # フォールバック: 全テキストの一部
            if len(full_text) > 100:
                return self.clean_text(full_text[:500])
            
            return ""
            
        except Exception as e:
            logger.error(f"議案本文抽出エラー: {str(e)}")
            return ""
    
    def extract_submitter(self, soup: BeautifulSoup) -> str:
        """提出者を抽出"""
        try:
            page_text = soup.get_text()
            
            patterns = [
                r'提出者[：:]\s*([^\n\r]+)',
                r'提出[：:]\s*([^\n\r]+)',
                r'([^\n\r]+)提出',
                r'内閣提出',
                r'議員提出'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    submitter = match.group(1) if len(match.groups()) > 0 else match.group(0)
                    return submitter.strip()
            
            return ""
            
        except Exception as e:
            logger.error(f"提出者抽出エラー: {str(e)}")
            return ""
    
    def extract_submission_date(self, soup: BeautifulSoup) -> str:
        """提出日を抽出"""
        try:
            page_text = soup.get_text()
            
            patterns = [
                r'提出日[：:]\s*(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'(\d{4})年(\d{1,2})月(\d{1,2})日提出',
                r'令和(\d+)年(\d{1,2})月(\d{1,2})日'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, page_text)
                if match:
                    groups = match.groups()
                    if len(groups) >= 3:
                        year, month, day = groups[:3]
                        # 令和年号の処理
                        if len(year) <= 2:
                            year = str(2018 + int(year))
                        return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            
            return ""
            
        except Exception as e:
            logger.error(f"提出日抽出エラー: {str(e)}")
            return ""
    
    def extract_status(self, soup: BeautifulSoup) -> str:
        """議案状況を抽出"""
        try:
            page_text = soup.get_text()
            
            status_keywords = ['可決', '否決', '廃案', '継続審議', '成立', '審議中', '委員会審査中']
            
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
            '審議中': '審議中',
            '委員会審査中': '審議中'
        }
        
        return status_mapping.get(status, '不明')
    
    def extract_committee(self, soup: BeautifulSoup) -> str:
        """委員会名を抽出"""
        try:
            page_text = soup.get_text()
            
            committee_patterns = [
                r'([^委員会]*委員会)',
                r'([^調査会]*調査会)'
            ]
            
            for pattern in committee_patterns:
                match = re.search(pattern, page_text)
                if match:
                    return match.group(1)
            
            return ""
            
        except Exception as e:
            logger.error(f"委員会名抽出エラー: {str(e)}")
            return ""
    
    def extract_related_links(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, str]]:
        """関連リンクを抽出"""
        links = []
        
        try:
            all_links = soup.find_all('a', href=True)
            
            for link in all_links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # 関連文書のリンクを判定
                if any(ext in href.lower() for ext in ['.pdf', '.doc', '.html', '.htm']):
                    full_url = self.build_absolute_url(href, base_url)
                    if full_url and 'menu' not in href.lower():
                        links.append({
                            'url': full_url,
                            'title': text or '関連文書'
                        })
            
        except Exception as e:
            logger.error(f"関連リンク抽出エラー: {str(e)}")
        
        return links[:5]  # 最大5件に制限
    
    def generate_summary(self, content: str, title: str) -> str:
        """議案サマリーを生成"""
        try:
            if content and len(content) > 100:
                summary = content[:200]
                if len(content) > 200:
                    summary += "..."
                return summary
            elif title:
                return f"{title}に関する法案"
            else:
                return "議案の概要"
            
        except Exception as e:
            logger.error(f"サマリー生成エラー: {str(e)}")
            return ""
    
    def classify_bill_category(self, title: str) -> str:
        """議案カテゴリを分類"""
        categories = {
            '外交・安全保障': ['外交', '条約', '防衛', '自衛隊', '安全保障'],
            '経済・財政': ['経済', '財政', '予算', '税制', '金融', '産業'],
            '社会保障': ['年金', '医療', '介護', '福祉', '社会保障'],
            '教育・文化': ['教育', '学校', '大学', '文化', '文部科学'],
            '環境・エネルギー': ['環境', 'エネルギー', '原子力'],
            '労働・雇用': ['労働', '雇用', '働き方'],
            '司法・行政': ['司法', '行政', '公務員', '裁判'],
            '地方・都市': ['地方', '自治体', '都市'],
            '交通・国土': ['交通', '道路', '国土']
        }
        
        title_lower = title.lower()
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return '一般'
    
    def clean_text(self, text: str) -> str:
        """テキスト整形"""
        if not text:
            return ""
        
        # 改行・スペースの正規化
        text = re.sub(r'\n\s*\n', '\n\n', text)
        text = re.sub(r'[ \t]+', ' ', text)
        text = re.sub(r'[\u3000]+', ' ', text)
        
        return text.strip()
    
    def validate_bill_data(self, bill: Dict[str, Any]) -> bool:
        """議案データの妥当性をチェック"""
        required_fields = ['title', 'session_number']
        
        # 必須フィールドのチェック
        for field in required_fields:
            if not bill.get(field):
                return False
        
        # タイトルが意味のあるものかチェック
        title = bill.get('title', '')
        if title in ['本文', 'メイン', 'エラー', '', '経過', '議案情報', '立法情報']:
            return False
        
        # URLの妥当性チェック
        url = bill.get('url', '')
        if not url or 'menu.htm' in url or 'index.nsf' in url:
            return False
        
        # タイトルの長さチェック
        if len(title) < 10:
            return False
        
        return True
    
    def collect_all_bills(self) -> List[Dict[str, Any]]:
        """すべての議案を収集"""
        logger.info("提出法案収集開始...")
        all_bills = []
        
        try:
            for session in self.target_sessions:
                if len(all_bills) >= self.max_bills:
                    logger.info(f"最大収集件数({self.max_bills})に到達しました")
                    break
                
                session_bills = self.collect_bills_from_session(session)
                all_bills.extend(session_bills)
                logger.info(f"第{session}回国会から{len(session_bills)}件の議案を収集")
            
            logger.info(f"提出法案収集完了: {len(all_bills)}件")
            return all_bills
            
        except Exception as e:
            logger.error(f"提出法案収集エラー: {str(e)}")
            return []
    
    def save_bills_data(self, bills: List[Dict[str, Any]]):
        """議案データを保存"""
        if not bills:
            logger.warning("保存する議案データがありません")
            return
        
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m%d')
        timestamp = current_date.strftime('%H%M%S')
        
        data_structure = {
            "metadata": {
                "data_type": "shugiin_bills_enhanced",
                "collection_method": "enhanced_scraping",
                "total_bills": len(bills),
                "generated_at": current_date.isoformat(),
                "source_site": "www.shugiin.go.jp",
                "target_sessions": self.target_sessions,
                "data_quality": "enhanced_collection",
                "version": "2.0"
            },
            "data": bills
        }
        
        # 生データ保存
        raw_filename = f"bills_{data_period}_{timestamp}.json"
        raw_filepath = self.bills_dir / raw_filename
        
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        frontend_filename = f"bills_{data_period}_{timestamp}.json"
        frontend_filepath = self.frontend_bills_dir / frontend_filename
        
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        
        # 最新ファイル更新
        latest_file = self.frontend_bills_dir / "bills_latest.json"
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(data_structure, f, ensure_ascii=False, indent=2)
        logger.info(f"📁 最新ファイル更新: {latest_file}")
        
        logger.info(f"議案データ保存完了:")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")
        logger.info(f"  - 件数: {len(bills)}")

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='提出法案収集スクリプト（強化版）')
    parser.add_argument('--max-bills', type=int, default=50, help='最大収集件数 (デフォルト: 50件)')
    
    args = parser.parse_args()
    
    collector = BillsEnhancedCollector(max_bills=args.max_bills)
    
    try:
        # 提出法案収集
        bills = collector.collect_all_bills()
        
        if bills:
            # データ保存
            collector.save_bills_data(bills)
            logger.info(f"新規提出法案収集完了: {len(bills)}件")
        else:
            logger.info("新規提出法案は見つかりませんでした")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()