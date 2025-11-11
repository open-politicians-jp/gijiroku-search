#!/usr/bin/env python3
"""
進行的データ収集スクリプト (Issue #26対応)

GitHub Actions用に設計された進行的データ収集システム：
- 既存データの最古日付を基準とした進行的な過去データ収集
- ファイル名解析により既存データの期間を把握
- 不足期間を自動計算して過去データを収集
- IP偽装とレート制限対応
- ファイル名形式: speeches_YYYYMM01_HHMMSS.json (データ期間基準)

環境変数:
- MONTHS_BACK: 収集月数 (デフォルト: 3)
- USE_PROGRESSIVE: 進行的収集を使用 (デフォルト: true)  
- FORCE_UPDATE: 強制更新 (デフォルト: false)
- PAST_DATA_MODE: 過去データ専用モード (デフォルト: false)
"""

import os
import json
import time
import random
import requests
import calendar
import math
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from fake_useragent import UserAgent
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DailyKokkaiAPIClient:
    """毎日実行用の国会API収集クライアント (Issue #26対応)"""
    
    def __init__(self):
        self.base_url = "https://kokkai.ndl.go.jp/api/speech"
        self.session = requests.Session()
        self.ua = UserAgent()
        self.request_count = 0
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.raw_data_dir = self.project_root / "data" / "raw" / "speeches"
        self.frontend_data_dir = self.project_root / "frontend" / "public" / "data" / "speeches"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        self.frontend_data_dir.mkdir(parents=True, exist_ok=True)
        
    def update_headers(self):
        """リクエストヘッダーを更新"""
        referrers = [
            'https://www.google.com/',
            'https://www.yahoo.co.jp/',
            'https://www.bing.com/',
            'https://kokkai.ndl.go.jp/',
            'https://www.ndl.go.jp/'
        ]
        
        headers = {
            'User-Agent': self.ua.random,
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Referer': random.choice(referrers),
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        }
        self.session.headers.update(headers)
        
    def rate_limit(self):
        """レート制限: リクエスト間隔を調整"""
        self.request_count += 1
        
        # 10リクエストごとにヘッダー更新
        if self.request_count % 10 == 0:
            self.update_headers()
            logger.info(f"ヘッダー更新 ({self.request_count}リクエスト)")
        
        # レート制限: 1-3秒のランダム待機
        wait_time = random.uniform(1.0, 3.0)
        time.sleep(wait_time)
        
    def get_last_day_of_month(self, year: int, month: int) -> int:
        """指定年月の最終日を取得（うるう年対応）"""
        return calendar.monthrange(year, month)[1]
        
    def get_monthly_data(self, year: int, month: int) -> List[Dict[str, Any]]:
        """指定月の議事録データを取得"""
        logger.info(f"📅 {year}年{month}月のデータ収集開始...")
        
        all_speeches = []
        start_record = 1
        records_per_request = 100
        
        # 指定月の最後の日を取得
        last_day = self.get_last_day_of_month(year, month)
        logger.info(f"📅 {year}年{month}月: 1日〜{last_day}日 (計{last_day}日)")
        
        while True:
            self.rate_limit()
            
            params = {
                'startRecord': start_record,
                'maximumRecords': records_per_request,
                'recordPacking': 'json',
                'from': f"{year}-{month:02d}-01",
                'until': f"{year}-{month:02d}-{last_day:02d}"
            }
            
            try:
                logger.info(f"🔍 レコード {start_record}〜{start_record + records_per_request - 1} を取得中...")
                response = self.session.get(self.base_url, params=params, timeout=30)
                response.raise_for_status()
                
                data = response.json()
                
                if 'speechRecord' not in data:
                    logger.warning(f"⚠️ speechRecord not found in response")
                    break
                    
                speeches = data['speechRecord']
                
                if not speeches:
                    logger.info(f"✅ {year}年{month}月のデータ収集完了")
                    break
                    
                # データ正規化
                normalized_speeches = []
                for speech in speeches:
                    normalized_speech = self.normalize_speech_data(speech)
                    if normalized_speech:
                        normalized_speeches.append(normalized_speech)
                
                all_speeches.extend(normalized_speeches)
                logger.info(f"📊 {len(normalized_speeches)}件追加 (累計: {len(all_speeches)}件)")
                
                # 次のページへ
                start_record += records_per_request
                
            except Exception as e:
                logger.error(f"❌ エラー発生: {e}")
                break
                
        logger.info(f"🎉 {year}年{month}月: 合計 {len(all_speeches)}件 収集完了")
        return all_speeches
        
    def normalize_speech_data(self, speech: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """議事録データを正規化"""
        try:
            # 基本的なフィールド抽出
            normalized = {
                'id': speech.get('speechID', ''),
                'date': speech.get('date', ''),
                'session': int(speech.get('session', 0)),
                'house': speech.get('nameOfHouse', ''),
                'committee': speech.get('nameOfMeeting', ''),
                'meeting_info': self.extract_meeting_details(speech),
                'speaker': speech.get('speaker', ''),
                'party': None,
                'party_normalized': None,
                'party_aliases': [],
                'position': speech.get('speakerPosition', ''),
                'text': speech.get('speech', ''),
                'url': speech.get('speechURL', ''),
                'created_at': datetime.now().isoformat()
            }
            
            # 政党情報の処理
            speaker_group = speech.get('speakerGroup', '')
            if speaker_group:
                normalized['party'] = speaker_group
                normalized['party_normalized'] = self.normalize_party_name(speaker_group)
                normalized['party_aliases'] = self.get_party_aliases(normalized['party_normalized'])
            
            return normalized
            
        except Exception as e:
            logger.error(f"❌ データ正規化エラー: {e}")
            return None
            
    def normalize_party_name(self, party_name: str) -> str:
        """政党名を正規化"""
        party_mapping = {
            '自由民主党': '自由民主党',
            '自民党': '自由民主党',
            '立憲民主党': '立憲民主党',
            '立民': '立憲民主党',
            '日本維新の会': '日本維新の会',
            '維新': '日本維新の会',
            '公明党': '公明党',
            '公明': '公明党',
            '日本共産党': '日本共産党',
            '共産党': '日本共産党',
            '共産': '日本共産党',
            '国民民主党': '国民民主党',
            '国民': '国民民主党',
            'れいわ新選組': 'れいわ新選組',
            'れいわ': 'れいわ新選組'
        }
        
        for key, normalized in party_mapping.items():
            if key in party_name:
                return normalized
        
        return party_name
        
    def get_party_aliases(self, party_name: str) -> List[str]:
        """政党の略称リストを取得"""
        aliases_mapping = {
            '自由民主党': ['自民党', '自民', 'LDP'],
            '立憲民主党': ['立民', '立憲'],
            '日本維新の会': ['維新', '維新の会', '大阪維新'],
            '公明党': ['公明'],
            '日本共産党': ['共産党', '共産', 'JCP'],
            '国民民主党': ['国民'],
            'れいわ新選組': ['れいわ']
        }
        
        return aliases_mapping.get(party_name, [])
        
    def extract_meeting_details(self, speech: Dict[str, Any]) -> Dict[str, Any]:
        """会議の詳細情報を抽出"""
        try:
            meeting_details = {
                'session_name': speech.get('nameOfSession', ''),
                'meeting_name': speech.get('nameOfMeeting', ''),
                'house': speech.get('nameOfHouse', ''),
                'meeting_number': speech.get('meetingNumber', ''),
                'date': speech.get('date', ''),
                'issue': speech.get('issue', ''),
                'pdf_url': speech.get('pdfURL', ''),
                'speech_order': speech.get('speechOrder', ''),
                'meeting_type': self.classify_meeting_type(speech.get('nameOfMeeting', ''))
            }
            
            return meeting_details
            
        except Exception as e:
            logger.error(f"❌ 会議詳細抽出エラー: {e}")
            return {}
            
    def classify_meeting_type(self, meeting_name: str) -> str:
        """会議名から会議種別を分類"""
        if not meeting_name:
            return '不明'
            
        if '本会議' in meeting_name:
            return '本会議'
        elif '予算委員会' in meeting_name:
            return '予算委員会'
        elif '特別委員会' in meeting_name:
            return '特別委員会'
        elif '常任委員会' in meeting_name or '委員会' in meeting_name:
            return '常任委員会'
        elif '審査会' in meeting_name:
            return '審査会'
        elif '調査会' in meeting_name:
            return '調査会'
        elif '分科会' in meeting_name:
            return '分科会'
        else:
            return 'その他'
        
    def generate_filename(self, year: int, month: int, day_range: str) -> str:
        """統一ファイル名形式で生成: speeches_YYYYMM01_HHMMSS.json（データ期間基準）"""
        timestamp = datetime.now().strftime("%H%M%S")
        return f"speeches_{year}{month:02d}01_{timestamp}.json"
        
    def save_monthly_data(self, speeches: List[Dict[str, Any]], year: int, month: int):
        """月次データを保存（フロントエンド用にも同時保存）"""
        if not speeches:
            logger.warning(f"⚠️ {year}年{month}月: データが空のためスキップ")
            return
            
        filename = self.generate_filename(year, month, "")
        raw_filepath = self.raw_data_dir / filename
        frontend_filepath = self.frontend_data_dir / filename
        
        # メタデータ付きで保存
        data = {
            "metadata": {
                "data_type": "speeches",
                "year": year,
                "month": month,
                "total_count": len(speeches),
                "generated_at": datetime.now().isoformat(),
                "source": "https://kokkai.ndl.go.jp/api.html",
                "collection_method": "progressive_past_data_collection",
                "filename_format": "speeches_YYYYMM01_HHMMSS.json",
                "period": f"{year}-{month:02d}",
                "is_past_data": os.getenv('PAST_DATA_MODE', 'false').lower() == 'true'
            },
            "data": speeches
        }
        
        # 生データ保存
        with open(raw_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # フロントエンド用データ保存
        with open(frontend_filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        file_size = raw_filepath.stat().st_size / (1024 * 1024)
        logger.info(f"💾 保存完了: {filename} ({file_size:.1f} MB)")
        logger.info(f"  - 生データ: {raw_filepath}")
        logger.info(f"  - フロントエンド: {frontend_filepath}")

def analyze_existing_data_periods(client):
    """既存データのファイル名解析により収集済み期間を把握 (Issue #26)"""
    
    # フロントエンドディレクトリの既存ファイルを確認
    existing_files = list(client.frontend_data_dir.glob("speeches_*.json"))
    covered_periods = set()
    oldest_period = None
    newest_period = None
    
    logger.info(f"🔍 既存ファイル {len(existing_files)} 件から収集済み期間を解析中...")
    
    for file_path in existing_files:
        try:
            filename = file_path.name
            
            # ファイル名パターンをチェック
            if filename.startswith('speeches_') and filename.endswith('.json'):
                # speeches_YYYYMM01_HHMMSS.json パターン
                import re
                match = re.match(r'speeches_(\d{4})(\d{2})01_\d{6}\.json', filename)
                if match:
                    year, month = int(match.group(1)), int(match.group(2))
                    period = (year, month)
                    covered_periods.add(period)
                    
                    # 最古・最新期間の更新
                    if oldest_period is None or period < oldest_period:
                        oldest_period = period
                    if newest_period is None or period > newest_period:
                        newest_period = period
                        
                # 旧形式も対応（speeches_YYYYMMDD_HHMMSS.json等）
                elif re.match(r'speeches_(\d{4})(\d{2})\d{2}_\d{6}\.json', filename):
                    match = re.match(r'speeches_(\d{4})(\d{2})\d{2}_\d{6}\.json', filename)
                    if match:
                        year, month = int(match.group(1)), int(match.group(2))
                        period = (year, month)
                        covered_periods.add(period)
                        
                        if oldest_period is None or period < oldest_period:
                            oldest_period = period
                        if newest_period is None or period > newest_period:
                            newest_period = period
                            
        except Exception as e:
            logger.warning(f"ファイル名解析エラー {file_path}: {e}")
            continue
    
    return covered_periods, oldest_period, newest_period

def get_progressive_collection_months(client, months_to_collect=3):
    """既存データに基づき最新〜過去の不足期間を算出 (Issue #26対応強化)"""

    # 0.25 などの小数でも最低1ヶ月は取得する
    months_to_collect = max(1, int(math.ceil(months_to_collect)))

    covered_periods, oldest_period, newest_period = analyze_existing_data_periods(client)
    current_date = datetime.now()

    if not covered_periods:
        logger.info("📊 既存データなし: 現在日付から過去データを収集")
        target_months = []
        for i in range(months_to_collect):
            target_date = current_date - relativedelta(months=i)
            target_months.append((target_date.year, target_date.month))
        return target_months

    logger.info(f"📊 収集済み期間: {len(covered_periods)}ヶ月分")
    logger.info(f"📊 最古期間: {oldest_period[0]}年{oldest_period[1]}月")
    logger.info(f"📊 最新期間: {newest_period[0]}年{newest_period[1]}月")

    target_months = []
    scheduled = set()

    # 直近の月を優先的にチェック（最新データ取得）
    for i in range(months_to_collect):
        target_date = current_date - relativedelta(months=i)
        period = (target_date.year, target_date.month)
        if period not in scheduled:
            target_months.append(period)
            scheduled.add(period)

    # 歴史的な不足期間も徐々に埋める
    base_year, base_month = oldest_period
    base_date = datetime(base_year, base_month, 1)
    for i in range(1, months_to_collect + 1):
        target_date = base_date - relativedelta(months=i)
        period = (target_date.year, target_date.month)
        if period in covered_periods or period in scheduled:
            continue
        target_months.append(period)
        scheduled.add(period)

    logger.info(f"📅 収集対象: {', '.join([f'{y}年{m}月' for y, m in target_months])}")

    return target_months

def main():
    """メイン処理"""
    logger.info("🚀 毎日データ収集開始...")
    
    # 環境変数から設定取得
    months_back = float(os.getenv('MONTHS_BACK', '3'))  # デフォルトを3ヶ月に変更
    force_update = os.getenv('FORCE_UPDATE', 'false').lower() == 'true'
    use_progressive = os.getenv('USE_PROGRESSIVE', 'true').lower() == 'true'
    
    logger.info(f"📋 設定: {months_back}ヶ月分のデータを収集")
    logger.info(f"📋 強制更新: {force_update}")
    logger.info(f"📋 進行的収集: {use_progressive}")
    
    client = DailyKokkaiAPIClient()
    
    if use_progressive:
        # 新しい進行的収集ロジック
        target_months = get_progressive_collection_months(client, months_back)
    else:
        # 従来のロジック（後方互換性のため保持）
        current_date = datetime.now()
        target_months = []
        
        if months_back < 1:
            target_months.append((current_date.year, current_date.month))
            logger.info(f"📅 小数点月数({months_back})のため現在月のみ収集")
        else:
            months_to_collect = int(months_back) + (1 if months_back % 1 > 0 else 0)
            logger.info(f"📅 従来ロジック: {months_to_collect}ヶ月分を収集対象")
            
            for i in range(months_to_collect):
                target_date = current_date - relativedelta(months=i)
                target_months.append((target_date.year, target_date.month))
    
    # 収集対象月を表示
    logger.info(f"📅 収集対象月: {', '.join([f'{y}年{m}月' for y, m in target_months])}")
    
    # 各月のデータを収集
    for year, month in target_months:
        # 既存ファイルチェック
        existing_files = list(client.raw_data_dir.glob(f"speeches_{year}{month:02d}*.json"))
        
        if existing_files and not force_update:
            logger.info(f"⏭️ {year}年{month}月: 既存ファイルあり、スキップ")
            continue
            
        # データ収集
        speeches = client.get_monthly_data(year, month)
        
        if speeches:
            client.save_monthly_data(speeches, year, month)
        else:
            logger.warning(f"⚠️ {year}年{month}月: データなし")
            
    logger.info("✨ 毎日データ収集完了!")

if __name__ == "__main__":
    main()
