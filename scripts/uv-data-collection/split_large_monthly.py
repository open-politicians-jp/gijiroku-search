#!/usr/bin/env python3
"""
大きな月次ファイルをさらに分割

26MBの3月データを週別に分割
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

class MonthlyFileSplitter:
    """月次ファイル分割クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "frontend" / "public" / "data"
        self.speeches_dir = self.data_dir / "speeches"
        
        # ファイルサイズ制限（MB）
        self.max_file_size_mb = 15  # 15MBを上限とする
        
    def get_file_size_mb(self, file_path: Path) -> float:
        """ファイルサイズをMBで取得"""
        if not file_path.exists():
            return 0
        return file_path.stat().st_size / (1024 * 1024)
    
    def get_week_of_month(self, date_str: str) -> int:
        """日付から月内の週を取得（1-5）"""
        try:
            date_obj = datetime.strptime(date_str, '%Y-%m-%d')
            day = date_obj.day
            # 月の第何週かを計算（1日から7日は第1週など）
            week = ((day - 1) // 7) + 1
            return min(week, 5)  # 最大5週まで
        except:
            return 1
    
    def split_large_monthly_file(self, file_path: Path):
        """大きな月次ファイルを週別に分割"""
        file_size = self.get_file_size_mb(file_path)
        logger.info(f"処理対象ファイル: {file_path.name} ({file_size:.1f}MB)")
        
        if file_size < self.max_file_size_mb:
            logger.info("ファイルサイズが制限以下のため、分割不要")
            return
            
        try:
            # ファイル読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            speeches = data.get('data', [])
            metadata = data.get('metadata', {})
            period = metadata.get('period', '')
            
            logger.info(f"読み込み完了: {len(speeches)}件のデータ ({period})")
            
            # 週別にグループ化
            weekly_data = defaultdict(list)
            
            for speech in speeches:
                date_str = speech.get('date', '')
                if date_str and period in date_str:  # 同じ月のデータかチェック
                    week = self.get_week_of_month(date_str)
                    weekly_data[week].append(speech)
                else:
                    weekly_data[1].append(speech)  # デフォルトは第1週
            
            # 週別ファイル作成
            for week_num, week_speeches in weekly_data.items():
                if not week_speeches:
                    continue
                    
                filename = f"{file_path.stem}_w{week_num:02d}.json"
                filepath = self.speeches_dir / filename
                
                # メタデータ付きで保存
                weekly_file_data = {
                    "metadata": {
                        "data_type": "speeches",
                        "period": f"{period}-w{week_num:02d}",
                        "total_count": len(week_speeches),
                        "generated_at": datetime.now().isoformat(),
                        "split_from": file_path.name
                    },
                    "data": week_speeches
                }
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    json.dump(weekly_file_data, f, ensure_ascii=False, indent=2)
                
                file_size = self.get_file_size_mb(filepath)
                logger.info(f"週別ファイル作成: {filename} ({len(week_speeches)}件, {file_size:.1f}MB)")
            
            # 元ファイルをバックアップしてから削除
            backup_file = file_path.with_suffix(f'.json.large_backup')
            file_path.rename(backup_file)
            logger.info(f"元ファイルをバックアップ: {backup_file.name}")
            
        except Exception as e:
            logger.error(f"ファイル分割エラー: {e}")
    
    def run(self):
        """メイン処理実行"""
        logger.info("大きな月次ファイル分割処理開始...")
        
        # 制限を超えるファイルを探して分割
        for json_file in self.speeches_dir.glob("speeches_2025_*.json"):
            if json_file.name.endswith('_backup.json') or json_file.name.endswith('.original'):
                continue
            if 'index' in json_file.name or 'latest' in json_file.name:
                continue
                
            file_size = self.get_file_size_mb(json_file)
            if file_size > self.max_file_size_mb:
                self.split_large_monthly_file(json_file)
        
        logger.info("✨ 大きな月次ファイル分割処理完了")

def main():
    """メイン処理"""
    splitter = MonthlyFileSplitter()
    splitter.run()

if __name__ == "__main__":
    main()