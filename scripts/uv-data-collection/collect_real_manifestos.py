#!/usr/bin/env python3
"""
実際の政党マニフェスト収集スクリプト

主要政党の公式サイトから最新マニフェストを収集
週次実行対応・過去データアーカイブ機能付き
"""

import json
import requests
import time
import re
import argparse
from datetime import datetime, timedelta
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

class ManifestoCollector:
    """政党マニフェスト収集クラス"""
    
    def __init__(self, weekly_mode=False, archive_mode=False):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        self.weekly_mode = weekly_mode
        self.archive_mode = archive_mode
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_manifestos_dir = self.project_root / "frontend" / "public" / "data" / "manifestos"
        self.frontend_manifestos_dir.mkdir(parents=True, exist_ok=True)
        
        # アーカイブディレクトリ設定
        if self.archive_mode:
            self.archive_dir = self.frontend_manifestos_dir / "archive"
            self.archive_dir.mkdir(parents=True, exist_ok=True)
        
        # 政党情報
        self.parties = {
            "自由民主党": {
                "url": "https://www.jimin.jp/policy/pamphlet/",
                "backup_url": "https://www.jimin.jp/policy/manifest/",
                "aliases": ["自民党", "自民", "LDP"]
            },
            "立憲民主党": {
                "url": "https://cdp-japan.jp/policies/5pillars",
                "backup_url": "https://cdp-japan.jp/",
                "aliases": ["立民", "立憲"]
            },
            "日本維新の会": {
                "url": "https://o-ishin.jp/policy/",
                "backup_url": "https://o-ishin.jp/",
                "aliases": ["維新", "維新の会", "大阪維新"]
            },
            "公明党": {
                "url": "https://www.komei.or.jp/policy/",
                "backup_url": "https://www.komei.or.jp/",
                "aliases": ["公明"]
            },
            "日本共産党": {
                "url": "https://www.jcp.or.jp/web_policy/",
                "backup_url": "https://www.jcp.or.jp/",
                "aliases": ["共産党", "共産", "JCP"]
            },
            "国民民主党": {
                "url": "https://new-kokumin.jp/policies",
                "backup_url": "https://new-kokumin.jp/",
                "aliases": ["国民"]
            },
            "れいわ新選組": {
                "url": "https://reiwa-shinsengumi.com/policy/",
                "backup_url": "https://reiwa-shinsengumi.com/",
                "aliases": ["れいわ"]
            },
            "参政党": {
                "url": "https://www.sanseito.jp/policy/",
                "backup_url": "https://www.sanseito.jp/",
                "aliases": ["参政"]
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
        
    def fetch_page_content(self, url: str) -> Optional[str]:
        """ページコンテンツを取得"""
        try:
            time.sleep(2)  # レート制限
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # 文字エンコーディングを自動検出・修正
            response.encoding = response.apparent_encoding or 'utf-8'
            
            return response.text
        except Exception as e:
            logger.error(f"❌ ページ取得エラー ({url}): {e}")
            return None
            
    def extract_policy_content(self, html: str, party_name: str) -> List[Dict[str, Any]]:
        """HTMLから政策内容を抽出"""
        soup = BeautifulSoup(html, 'html.parser')
        policies = []
        
        # 共通的な政策セクションを探す
        policy_selectors = [
            'div.policy', 'div.manifesto', 'div.content',
            'section.policy', 'section.manifesto',
            'article', 'main', '.policy-content',
            'h2, h3, h4',  # 見出しベース
            'p'  # パラグラフベース
        ]
        
        content_text = ""
        
        # タイトルを抽出
        title_elem = soup.find('title')
        page_title = title_elem.text.strip() if title_elem else f"{party_name}政策"
        
        # メイン内容を抽出
        for selector in policy_selectors:
            elements = soup.select(selector)
            if elements:
                for elem in elements[:10]:  # 最初の10要素まで
                    text = elem.get_text(strip=True)
                    if text and len(text) > 20:  # 短すぎるものは除外
                        content_text += text + "\n\n"
                        
        # 内容が少ない場合はbody全体から抽出
        if len(content_text) < 200:
            body = soup.find('body')
            if body:
                content_text = body.get_text(separator='\n', strip=True)
                
        # 不要な部分を除去
        content_text = self.clean_policy_text(content_text)
        
        if content_text:
            policies.append({
                "party": party_name,
                "title": page_title,
                "year": datetime.now().year,
                "category": "政策綱領",
                "content": content_text[:2000],  # 2000文字まで
                "url": "",  # 後で設定
                "collected_at": datetime.now().isoformat()
            })
            
        return policies
        
    def clean_policy_text(self, text: str) -> str:
        """政策テキストをクリーンアップ"""
        if not text:
            return text
            
        # 文字化け修復（主にUTF-8関連）
        try:
            # よくある文字化けパターンを修正
            text = text.encode('latin1').decode('utf-8')
        except (UnicodeDecodeError, UnicodeEncodeError):
            # 既に正しいエンコーディングの場合はそのまま
            pass
            
        # 改行を整理
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # 不要な文字列を除去
        remove_patterns = [
            r'Copyright.*?All Rights Reserved',
            r'プライバシーポリシー',
            r'サイトマップ',
            r'お問い合わせ',
            r'メニュー',
            r'ナビゲーション',
            r'フッター',
            r'ヘッダー',
            r'検索',
            r'SNS.*?follow',
            r'JavaScript.*?有効',
        ]
        
        for pattern in remove_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
            
        # 連続する空白を整理
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        return text.strip()
        
    def collect_party_manifesto(self, party_name: str, party_info: Dict[str, Any]) -> List[Dict[str, Any]]:
        """個別政党のマニフェストを収集"""
        logger.info(f"📄 {party_name}の政策を収集中...")
        
        manifestos = []
        
        # メインURLを試行
        html = self.fetch_page_content(party_info["url"])
        if not html:
            # バックアップURLを試行
            logger.info(f"⚠️ メインURL失敗、バックアップURLを試行: {party_name}")
            html = self.fetch_page_content(party_info["backup_url"])
            
        if html:
            policies = self.extract_policy_content(html, party_name)
            for policy in policies:
                policy["url"] = party_info["url"]
                policy["party_aliases"] = party_info["aliases"]
                manifestos.append(policy)
                
        if manifestos:
            logger.info(f"✅ {party_name}: {len(manifestos)}件の政策を収集")
        else:
            logger.warning(f"⚠️ {party_name}: 政策データを取得できませんでした")
            
        return manifestos
        
    def collect_all_manifestos(self) -> List[Dict[str, Any]]:
        """全政党のマニフェストを収集"""
        logger.info("🚀 政党マニフェスト収集開始...")
        
        all_manifestos = []
        
        for party_name, party_info in self.parties.items():
            try:
                manifestos = self.collect_party_manifesto(party_name, party_info)
                all_manifestos.extend(manifestos)
                
                # レート制限
                time.sleep(3)
                
            except Exception as e:
                logger.error(f"❌ {party_name}の収集でエラー: {e}")
                
        logger.info(f"🎉 収集完了: 合計 {len(all_manifestos)}件")
        return all_manifestos
        
    def save_manifestos(self, manifestos: List[Dict[str, Any]]):
        """マニフェストを保存"""
        if not manifestos:
            logger.warning("⚠️ 保存するマニフェストデータがありません")
            return
            
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_date = datetime.now()
        
        # 週次モードの場合は週番号を含むファイル名
        if self.weekly_mode:
            year = current_date.year
            week = current_date.isocalendar()[1]
            weekly_filename = f"manifestos_{year}_w{week:02d}.json"
            weekly_filepath = self.frontend_manifestos_dir / weekly_filename
        
        # 通常のタイムスタンプファイル名
        filename = f"manifestos_{timestamp}.json"
        filepath = self.frontend_manifestos_dir / filename
        
        # メタデータ準備
        metadata = {
            "data_type": "manifestos",
            "total_count": len(manifestos),
            "generated_at": current_date.isoformat(),
            "source": "各政党公式サイト",
            "collection_method": "weekly_automated_collection" if self.weekly_mode else "real_party_scraping"
        }
        
        if self.weekly_mode:
            metadata.update({
                "collection_week": f"{current_date.year}-W{current_date.isocalendar()[1]:02d}",
                "archive_enabled": self.archive_mode
            })
        
        data = {
            "metadata": metadata,
            "data": manifestos
        }
        
        # 通常ファイル保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        file_size = filepath.stat().st_size / 1024
        logger.info(f"💾 保存完了: {filename} ({file_size:.1f} KB)")
        
        # 週次モードの場合は週次ファイルも保存
        if self.weekly_mode and weekly_filepath != filepath:
            with open(weekly_filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"📅 週次ファイル保存: {weekly_filename}")
        
        # アーカイブモードの場合は過去のファイルを保持
        if self.archive_mode:
            self.archive_old_files()
            logger.info("📚 アーカイブ機能有効: 過去データを保持")
        
        # latest ファイルを更新
        latest_filepath = self.frontend_manifestos_dir / "manifestos_latest.json"
        with open(latest_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info("🔄 latest ファイル更新完了")
        
    def archive_old_files(self):
        """古いファイルをアーカイブディレクトリに移動"""
        if not self.archive_mode:
            return
            
        # 2日以上古いファイルをアーカイブに移動
        cutoff_date = datetime.now() - timedelta(days=2)
        archived_count = 0
        
        all_files = list(self.frontend_manifestos_dir.glob("manifestos_*.json"))
        
        for file in all_files:
            # latest ファイルと週次ファイルは除外
            if file.name in ["manifestos_latest.json"] or "_w" in file.name:
                continue
                
            # ファイルの作成日時をチェック
            try:
                file_mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if file_mtime < cutoff_date:
                    # アーカイブディレクトリに移動
                    archive_path = self.archive_dir / file.name
                    file.rename(archive_path)
                    logger.info(f"📚 アーカイブ移動: {file.name}")
                    archived_count += 1
            except Exception as e:
                logger.error(f"❌ アーカイブエラー {file.name}: {e}")
        
        if archived_count > 0:
            logger.info(f"📚 {archived_count}件のファイルをアーカイブしました")

def main():
    """メイン処理"""
    # コマンドライン引数解析
    parser = argparse.ArgumentParser(description='政党マニフェスト収集スクリプト')
    parser.add_argument('--weekly', action='store_true', help='週次モード（週番号付きファイル生成）')
    parser.add_argument('--archive', action='store_true', help='アーカイブモード（過去データ保持）')
    parser.add_argument('--no-cleanup', action='store_true', help='ファイル削除を無効化（非推奨）')
    
    args = parser.parse_args()
    
    # 収集器を初期化
    collector = ManifestoCollector(
        weekly_mode=args.weekly,
        archive_mode=args.archive
    )
    
    logger.info(f"📄 マニフェスト収集開始...")
    logger.info(f"📅 週次モード: {'有効' if args.weekly else '無効'}")
    logger.info(f"📚 アーカイブモード: {'有効' if args.archive else '無効'}")
    
    # 全政党のマニフェストを収集
    manifestos = collector.collect_all_manifestos()
    
    # 保存
    collector.save_manifestos(manifestos)
    
    logger.info("✨ 政党マニフェスト収集完了!")

if __name__ == "__main__":
    main()