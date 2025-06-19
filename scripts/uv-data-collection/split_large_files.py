#!/usr/bin/env python3
"""
大きなデータファイル分割スクリプト

GitHubの100MB制限に対応するため、大きなJSONファイルを分割する
- 66MBの speeches_2025_processed.json を月別に分割
- 10MB以上の週次ファイルも必要に応じて分割
"""

import json
import os
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LargeFileSplitter:
    """大きなファイル分割クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "frontend" / "public" / "data"
        self.speeches_dir = self.data_dir / "speeches"
        
        # ファイルサイズ制限（MB）
        self.max_file_size_mb = 25  # 25MBを上限とする
        
    def get_file_size_mb(self, file_path: Path) -> float:
        """ファイルサイズをMBで取得"""
        if not file_path.exists():
            return 0
        return file_path.stat().st_size / (1024 * 1024)
    
    def split_processed_speeches(self):
        """speeches_2025_processed.json を月別に分割"""
        processed_file = self.speeches_dir / "speeches_2025_processed.json"
        
        if not processed_file.exists():
            logger.warning(f"ファイルが見つかりません: {processed_file}")
            return
            
        file_size = self.get_file_size_mb(processed_file)
        logger.info(f"処理対象ファイル: {processed_file.name} ({file_size:.1f}MB)")
        
        if file_size < self.max_file_size_mb:
            logger.info("ファイルサイズが制限以下のため、分割不要")
            return
            
        try:
            # ファイル読み込み
            with open(processed_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            speeches = data.get('data', []) if isinstance(data, dict) else data
            logger.info(f"読み込み完了: {len(speeches)}件のデータ")
            
            # 月別にグループ化
            monthly_data = defaultdict(list)
            
            for speech in speeches:
                date_str = speech.get('date', '')
                if date_str:
                    try:
                        # YYYY-MM-DD形式からYYYY-MMを抽出
                        year_month = date_str[:7]  # YYYY-MM
                        monthly_data[year_month].append(speech)
                    except Exception as e:
                        logger.warning(f"日付解析エラー: {date_str} - {e}")
                        monthly_data['unknown'].append(speech)
                else:
                    monthly_data['unknown'].append(speech)
            
            # 月別ファイル作成
            for year_month, month_speeches in monthly_data.items():
                if not month_speeches:
                    continue
                    
                filename = f"speeches_{year_month.replace('-', '_')}.json"
                filepath = self.speeches_dir / filename
                
                # メタデータ付きで保存
                monthly_file_data = {
                    "metadata": {
                        "data_type": "speeches",
                        "period": year_month,
                        "total_count": len(month_speeches),
                        "generated_at": datetime.now().isoformat(),
                        "split_from": "speeches_2025_processed.json"
                    },
                    "data": month_speeches
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(monthly_file_data, f, ensure_ascii=False, indent=2)
                
                file_size = self.get_file_size_mb(filepath)
                logger.info(f"月別ファイル作成: {filename} ({len(month_speeches)}件, {file_size:.1f}MB)")
            
            # 元ファイルをバックアップしてから削除
            backup_file = processed_file.with_suffix('.json.original')
            processed_file.rename(backup_file)
            logger.info(f"元ファイルをバックアップ: {backup_file.name}")
            
            # 最新ファイルとして最新月のファイルをコピー
            if monthly_data:
                latest_month = max(k for k in monthly_data.keys() if k != 'unknown')
                latest_file = self.speeches_dir / f"speeches_{latest_month.replace('-', '_')}.json"
                latest_link = self.speeches_dir / "speeches_latest.json"
                
                if latest_file.exists():
                    with open(latest_file, 'r', encoding='utf-8') as f:
                        latest_data = json.load(f)
                    with open(latest_link, 'w', encoding='utf-8') as f:
                        json.dump(latest_data, f, ensure_ascii=False, indent=2)
                    logger.info(f"最新ファイル作成: speeches_latest.json ({latest_month})")
            
        except Exception as e:
            logger.error(f"ファイル分割エラー: {e}")
    
    def check_weekly_files(self):
        """週次ファイルのサイズをチェック"""
        weekly_dir = self.data_dir / "weekly" / "2025"
        
        if not weekly_dir.exists():
            return
            
        large_files = []
        for json_file in weekly_dir.glob("*.json"):
            file_size = self.get_file_size_mb(json_file)
            if file_size > self.max_file_size_mb:
                large_files.append((json_file, file_size))
        
        if large_files:
            logger.warning("制限を超える週次ファイル:")
            for file_path, size in large_files:
                logger.warning(f"  {file_path.name}: {size:.1f}MB")
        else:
            logger.info("週次ファイルはすべて制限内")
    
    def create_file_index(self):
        """分割されたファイルのインデックスを作成"""
        speeches_files = list(self.speeches_dir.glob("speeches_2025_*.json"))
        speeches_files = [f for f in speeches_files if f.name != "speeches_2025_processed.json"]
        
        if not speeches_files:
            return
            
        index_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_files": len(speeches_files),
                "description": "分割された議事録ファイルのインデックス"
            },
            "files": []
        }
        
        for file_path in sorted(speeches_files):
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                metadata = data.get('metadata', {})
                file_info = {
                    "filename": file_path.name,
                    "period": metadata.get('period', 'unknown'),
                    "count": metadata.get('total_count', 0),
                    "size_mb": round(self.get_file_size_mb(file_path), 1)
                }
                index_data["files"].append(file_info)
                
            except Exception as e:
                logger.error(f"インデックス作成エラー ({file_path.name}): {e}")
        
        index_file = self.speeches_dir / "speeches_index.json"
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"インデックスファイル作成: {index_file.name}")
    
    def run(self):
        """メイン処理実行"""
        logger.info("大きなファイル分割処理開始...")
        
        # 1. processed ファイルを分割
        self.split_processed_speeches()
        
        # 2. 週次ファイルサイズチェック
        self.check_weekly_files()
        
        # 3. インデックス作成
        self.create_file_index()
        
        logger.info("✨ 大きなファイル分割処理完了")

def main():
    """メイン処理"""
    splitter = LargeFileSplitter()
    splitter.run()

if __name__ == "__main__":
    main()