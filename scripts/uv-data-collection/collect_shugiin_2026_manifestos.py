#!/usr/bin/env python3
"""
2026年衆議院選マニフェスト収集スクリプト

公示日以降の各政党の選挙公約・マニフェストを収集
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


class Shugiin2026ManifestoCollector:
    """2026年衆議院選マニフェスト収集クラス"""

    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()

        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.output_dir = self.project_root / "frontend" / "public" / "data"
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # 2026年衆議院選向け政党情報
        # 選挙特設ページや公約ページを優先
        self.parties = {
            "自由民主党": {
                "election_urls": [
                    "https://www.jimin.jp/election/",
                    "https://www.jimin.jp/policy/pamphlet/",
                    "https://www.jimin.jp/policy/manifest/",
                    "https://special.jimin.jp/",
                ],
                "official_url": "https://www.jimin.jp/policy/pamphlet/",
                "aliases": ["自民党", "自民", "LDP"],
                "color": "#e60012"
            },
            "立憲民主党": {
                "election_urls": [
                    "https://cdp-japan.jp/election/",
                    "https://cdp-japan.jp/campaign/",
                    "https://cdp-japan.jp/policies/",
                    "https://cdp-japan.jp/policies/5pillars",
                ],
                "official_url": "https://cdp-japan.jp/",
                "aliases": ["立民", "立憲"],
                "color": "#004098"
            },
            "日本維新の会": {
                "election_urls": [
                    "https://o-ishin.jp/election/",
                    "https://o-ishin.jp/policy/",
                    "https://o-ishin.jp/election2026/",
                ],
                "official_url": "https://o-ishin.jp/policy/",
                "aliases": ["維新", "維新の会"],
                "color": "#00a63c"
            },
            "公明党": {
                "election_urls": [
                    "https://www.komei.or.jp/campaign/shugiin2026/",
                    "https://www.komei.or.jp/campaign/",
                    "https://www.komei.or.jp/policy/",
                ],
                "official_url": "https://www.komei.or.jp/policy/",
                "aliases": ["公明"],
                "color": "#f39800"
            },
            "日本共産党": {
                "election_urls": [
                    "https://www.jcp.or.jp/web_policy/",
                    "https://www.jcp.or.jp/akahata/",
                    "https://www.jcp.or.jp/",
                ],
                "official_url": "https://www.jcp.or.jp/web_policy/",
                "aliases": ["共産党", "共産", "JCP"],
                "color": "#c8000a"
            },
            "国民民主党": {
                "election_urls": [
                    "https://new-kokumin.jp/election/",
                    "https://new-kokumin.jp/policies",
                    "https://new-kokumin.jp/news/policy/",
                ],
                "official_url": "https://new-kokumin.jp/policies",
                "aliases": ["国民"],
                "color": "#ffd700"
            },
            "れいわ新選組": {
                "election_urls": [
                    "https://reiwa-shinsengumi.com/sousenkyo2026/",
                    "https://reiwa-shinsengumi.com/election/",
                    "https://reiwa-shinsengumi.com/policy/",
                ],
                "official_url": "https://reiwa-shinsengumi.com/policy/",
                "aliases": ["れいわ"],
                "color": "#ed6d00"
            },
            "参政党": {
                "election_urls": [
                    "https://www.sanseito.jp/election/",
                    "https://www.sanseito.jp/policy/",
                ],
                "official_url": "https://www.sanseito.jp/policy/",
                "aliases": ["参政"],
                "color": "#ff8c00"
            }
        }

    def update_headers(self):
        """リクエストヘッダーを更新"""
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }
        self.session.headers.update(headers)

    def fetch_page(self, url: str) -> Optional[str]:
        """ページを取得"""
        try:
            self.update_headers()
            time.sleep(2)
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            response.encoding = response.apparent_encoding or 'utf-8'
            return response.text
        except Exception as e:
            logger.warning(f"⚠️ ページ取得失敗 ({url}): {e}")
            return None

    def extract_policy_sections(self, html: str, party_name: str) -> List[Dict[str, Any]]:
        """HTMLから政策セクションを抽出"""
        soup = BeautifulSoup(html, 'html.parser')

        # スクリプト、スタイル、ナビゲーションを除去
        for element in soup.find_all(['script', 'style', 'nav', 'footer', 'header']):
            element.decompose()

        categories = []

        # 見出しと内容のペアを抽出
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'])

        for heading in headings:
            title = heading.get_text(strip=True)
            if not title or len(title) < 2 or len(title) > 100:
                continue

            # 見出し以降のコンテンツを取得
            content_parts = []
            sibling = heading.find_next_sibling()

            while sibling and sibling.name not in ['h1', 'h2', 'h3', 'h4']:
                text = sibling.get_text(strip=True)
                if text and len(text) > 10:
                    content_parts.append(text)
                sibling = sibling.find_next_sibling()
                if len(content_parts) > 10:  # 最大10要素まで
                    break

            if content_parts:
                content = ' '.join(content_parts)
                # 不要な文字列を除去
                content = self.clean_text(content)

                if len(content) > 50:  # 50文字以上のみ採用
                    categories.append({
                        "category": self.categorize_policy(title),
                        "policies": [{
                            "title": title[:100],
                            "description": content[:500]
                        }]
                    })

        # 重複カテゴリをマージ
        merged = {}
        for cat in categories:
            cat_name = cat["category"]
            if cat_name in merged:
                merged[cat_name]["policies"].extend(cat["policies"])
            else:
                merged[cat_name] = cat

        return list(merged.values())[:10]  # 最大10カテゴリ

    def categorize_policy(self, title: str) -> str:
        """政策タイトルからカテゴリを推測"""
        title_lower = title.lower()

        category_keywords = {
            "経済・財政": ["経済", "財政", "成長", "賃上げ", "物価", "景気", "税", "減税", "増税", "財源"],
            "社会保障": ["年金", "医療", "介護", "福祉", "社会保障", "保険", "子育て", "少子化", "高齢"],
            "外交・安全保障": ["外交", "安全保障", "防衛", "安保", "国防", "自衛隊", "米国", "中国", "北朝鮮"],
            "教育": ["教育", "学校", "大学", "奨学金", "教員", "学費", "無償化"],
            "憲法": ["憲法", "改憲", "9条", "緊急事態"],
            "エネルギー・環境": ["エネルギー", "原発", "再生可能", "脱炭素", "環境", "気候", "カーボン"],
            "政治改革": ["政治改革", "政治資金", "選挙制度", "議員", "定数", "身を切る"],
            "地方創生": ["地方", "地域", "過疎", "創生", "分散", "農業", "漁業"],
            "デジタル": ["デジタル", "DX", "IT", "AI", "マイナンバー"],
            "ジェンダー・人権": ["ジェンダー", "女性", "LGBT", "同性婚", "夫婦別姓", "人権"],
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category

        return "その他"

    def clean_text(self, text: str) -> str:
        """テキストをクリーンアップ"""
        if not text:
            return text

        # 不要なパターンを除去
        patterns_to_remove = [
            r'Copyright.*',
            r'All Rights Reserved.*',
            r'プライバシーポリシー',
            r'サイトマップ',
            r'お問い合わせ',
            r'ページトップ',
            r'トップページ',
            r'メニュー',
            r'検索',
            r'シェア',
            r'ツイート',
            r'いいね',
        ]

        for pattern in patterns_to_remove:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # 連続する空白を整理
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    def collect_party_manifesto(self, party_name: str, party_info: Dict) -> Optional[Dict]:
        """政党のマニフェストを収集"""
        logger.info(f"📄 {party_name}のマニフェストを収集中...")

        all_categories = []
        successful_url = None

        # 複数のURLを試行
        for url in party_info["election_urls"]:
            html = self.fetch_page(url)
            if html:
                categories = self.extract_policy_sections(html, party_name)
                if categories:
                    all_categories.extend(categories)
                    if not successful_url:
                        successful_url = url
                    logger.info(f"  ✅ {url} から {len(categories)} カテゴリ取得")

            time.sleep(1)

        if not all_categories:
            logger.warning(f"⚠️ {party_name}: 政策データを取得できませんでした")
            return None

        # 重複カテゴリをマージ
        merged = {}
        for cat in all_categories:
            cat_name = cat["category"]
            if cat_name in merged:
                # 既存のポリシーと重複しないものだけ追加
                existing_titles = {p["title"] for p in merged[cat_name]["policies"]}
                for policy in cat["policies"]:
                    if policy["title"] not in existing_titles:
                        merged[cat_name]["policies"].append(policy)
            else:
                merged[cat_name] = cat

        return {
            "name": party_name,
            "categories": list(merged.values()),
            "official_url": successful_url or party_info["official_url"],
            "aliases": party_info["aliases"],
            "collected_at": datetime.now().isoformat()
        }

    def collect_all(self) -> Dict:
        """全政党のマニフェストを収集"""
        logger.info("🚀 2026年衆議院選マニフェスト収集開始...")

        parties_data = []

        for party_name, party_info in self.parties.items():
            try:
                result = self.collect_party_manifesto(party_name, party_info)
                if result:
                    parties_data.append(result)
                time.sleep(3)
            except Exception as e:
                logger.error(f"❌ {party_name}の収集でエラー: {e}")

        return {
            "generated_at": datetime.now().isoformat(),
            "description": "2026年衆議院選 各政党の政策要約 - 公示日以降の最新マニフェスト",
            "election_type": "shugiin",
            "election_year": 2026,
            "total_parties": len(parties_data),
            "parties": parties_data
        }

    def save(self, data: Dict):
        """データを保存"""
        # shugiin_policy_summaries.json として保存
        output_path = self.output_dir / "shugiin_policy_summaries.json"

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        file_size = output_path.stat().st_size / 1024
        logger.info(f"💾 保存完了: {output_path.name} ({file_size:.1f} KB)")

        # バックアップも保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.output_dir / f"shugiin_policy_summaries_{timestamp}.json"
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 バックアップ保存: {backup_path.name}")


def main():
    """メイン処理"""
    collector = Shugiin2026ManifestoCollector()

    # 収集
    data = collector.collect_all()

    # 保存
    if data["parties"]:
        collector.save(data)
        logger.info(f"✨ 収集完了: {data['total_parties']}政党")
    else:
        logger.error("❌ マニフェストを収集できませんでした")


if __name__ == "__main__":
    main()
