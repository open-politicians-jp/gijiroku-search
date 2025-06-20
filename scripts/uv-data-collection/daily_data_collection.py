#!/usr/bin/env python3
"""
毎日実行される過去2ヶ月分データ収集スクリプト

GitHub Actions用に設計：
- 過去2ヶ月分の議事録データを毎日収集
- IP偽装とレート制限対応
- 新ファイル名形式: speeches_YYYYMMDD_DD.json
- 生データを data/raw/speeches/ に保存
"""

import os
import json
import time
import random
import requests
import calendar
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
    """毎日実行用の国会API収集クライアント"""
    
    def __init__(self):
        self.base_url = "https://kokkai.ndl.go.jp/api/speech"
        self.session = requests.Session()
        self.ua = UserAgent()
        self.request_count = 0
        self.update_headers()
        
        # 出力ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.raw_data_dir = self.project_root / "data" / "raw" / "speeches"
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)
        
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
                
                # 安全制限: 月間5000件まで
                if len(all_speeches) >= 5000:
                    logger.warning(f"⚠️ 月間制限(5000件)に達したため終了")
                    break
                    
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
        """新しいファイル名形式で生成: speeches_YYYYMMDD_DD.json"""
        return f"speeches_{year}{month:02d}01_{day_range}.json"
        
    def save_monthly_data(self, speeches: List[Dict[str, Any]], year: int, month: int):
        """月次データを保存"""
        if not speeches:
            logger.warning(f"⚠️ {year}年{month}月: データが空のためスキップ")
            return
            
        # 日付範囲の計算
        dates = [s['date'] for s in speeches if s['date']]
        if dates:
            dates.sort()
            first_day = dates[0].split('-')[2]
            last_day = dates[-1].split('-')[2]
            day_range = f"{first_day}_{last_day}" if first_day != last_day else first_day
        else:
            # データがない場合は月の最終日を使用
            last_day_of_month = self.get_last_day_of_month(year, month)
            day_range = f"{last_day_of_month:02d}"
            
        filename = self.generate_filename(year, month, day_range)
        filepath = self.raw_data_dir / filename
        
        # メタデータ付きで保存
        data = {
            "metadata": {
                "data_type": "speeches_raw",
                "year": year,
                "month": month,
                "total_count": len(speeches),
                "generated_at": datetime.now().isoformat(),
                "source": "https://kokkai.ndl.go.jp/api.html",
                "collection_method": "daily_automated_collection",
                "filename_format": "speeches_YYYYMMDD_DD.json"
            },
            "data": speeches
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            
        file_size = filepath.stat().st_size / (1024 * 1024)
        logger.info(f"💾 保存完了: {filename} ({file_size:.1f} MB)")

def main():
    """メイン処理"""
    logger.info("🚀 毎日データ収集開始...")
    
    # 環境変数から設定取得
    months_back = float(os.getenv('MONTHS_BACK', '2'))
    force_update = os.getenv('FORCE_UPDATE', 'false').lower() == 'true'
    
    logger.info(f"📋 設定: 過去{months_back}ヶ月分のデータを収集")
    logger.info(f"📋 強制更新: {force_update}")
    
    client = DailyKokkaiAPIClient()
    
    # 小数点月数を適切に処理
    current_date = datetime.now()
    target_months = []
    
    if months_back < 1:
        # 1ヶ月未満の場合は現在の月のみ
        target_months.append((current_date.year, current_date.month))
        logger.info(f"📅 小数点月数({months_back})のため現在月のみ収集: {current_date.year}年{current_date.month}月")
    else:
        # 1ヶ月以上の場合は整数部分の月数分を収集
        months_to_collect = int(months_back) + (1 if months_back % 1 > 0 else 0)
        logger.info(f"📅 小数点月数({months_back})から{months_to_collect}ヶ月分を収集対象とします")
        
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