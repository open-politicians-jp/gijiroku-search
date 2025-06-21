#!/usr/bin/env python3
"""
実際の政党マニフェスト収集スクリプト

主要政党の公式サイトから最新マニフェストを収集
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

class ManifestoCollector:
    """政党マニフェスト収集クラス"""
    
    def __init__(self):
        self.ua = UserAgent()
        self.session = requests.Session()
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.frontend_manifestos_dir = self.project_root / "frontend" / "public" / "data" / "manifestos"
        self.frontend_manifestos_dir.mkdir(parents=True, exist_ok=True)
        
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
            
        # データ期間を基準としたファイル名（現在の年月 + 時刻）
        current_date = datetime.now()
        data_period = current_date.strftime('%Y%m01')  # 当月のデータとして保存
        timestamp = current_date.strftime('%H%M%S')
        filename = f"manifestos_{data_period}_{timestamp}.json"
        filepath = self.frontend_manifestos_dir / filename
        
        data = {
            "metadata": {
                "data_type": "manifestos",
                "total_count": len(manifestos),
                "generated_at": datetime.now().isoformat(),
                "source": "各政党公式サイト",
                "collection_method": "real_party_scraping"
            },
            "data": manifestos
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        file_size = filepath.stat().st_size / 1024
        logger.info(f"💾 保存完了: {filename} ({file_size:.1f} KB)")
        
        # 古いサンプルファイルを削除
        self.remove_sample_files()
        
    def remove_sample_files(self):
        """サンプルファイルを削除"""
        # 古いサンプルファイルパターン（今日作成した新しいファイルは除外）
        current_date = datetime.now().strftime("%Y%m%d")
        
        all_files = list(self.frontend_manifestos_dir.glob("manifestos_*.json"))
        sample_files = []
        
        for file in all_files:
            filename = file.name
            # 今日より前のファイル、またはsampleという文字列を含むファイルを削除対象とする
            if ("sample" in filename.lower() or 
                (filename.startswith("manifestos_202506") and current_date not in filename)):
                sample_files.append(file)
        
        for sample_file in sample_files:
            try:
                sample_file.unlink()
                logger.info(f"🗑️ サンプルファイル削除: {sample_file.name}")
            except Exception as e:
                logger.error(f"❌ ファイル削除エラー: {e}")

def main():
    """メイン処理"""
    collector = ManifestoCollector()
    
    # 全政党のマニフェストを収集
    manifestos = collector.collect_all_manifestos()
    
    # 保存
    collector.save_manifestos(manifestos)
    
    logger.info("✨ 政党マニフェスト収集完了!")

if __name__ == "__main__":
    main()