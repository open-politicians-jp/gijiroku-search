#!/usr/bin/env python3
"""
週次データ整理スクリプト

既存の月次データを週次に再編成し、軽量化
FlexSearchへの影響を最小化しつつファイルサイズを削減
"""

import json
import csv
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class WeeklyDataOrganizer:
    """週次データ整理クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        
        # 既存ディレクトリ
        self.speeches_dir = self.project_root / "frontend" / "public" / "data" / "speeches"
        self.manifestos_dir = self.project_root / "frontend" / "public" / "data" / "manifestos"
        self.bills_dir = self.project_root / "frontend" / "public" / "data" / "bills"
        self.questions_dir = self.project_root / "frontend" / "public" / "data" / "questions"
        self.petitions_dir = self.project_root / "frontend" / "public" / "data" / "petitions"
        self.legislators_dir = self.project_root / "frontend" / "public" / "data" / "legislators"
        
        # 週次整理済みディレクトリ
        self.weekly_data_dir = self.project_root / "frontend" / "public" / "data" / "weekly"
        self.weekly_data_dir.mkdir(parents=True, exist_ok=True)
        
    def get_week_info(self, date_str: str) -> tuple:
        """日付文字列から年・週番号を取得"""
        try:
            date_obj = datetime.strptime(date_str[:10], "%Y-%m-%d")
            year = date_obj.year
            week = date_obj.isocalendar()[1]
            return year, week
        except:
            current = datetime.now()
            return current.year, current.isocalendar()[1]
            
    def organize_speeches_by_week(self):
        """議事録データを週次で整理"""
        logger.info("📝 議事録データを週次整理中...")
        
        weekly_speeches = {}
        
        # 既存の議事録ファイルを読み込み
        for json_file in self.speeches_dir.glob("*.json"):
            if json_file.name.endswith('.backup'):
                continue
                
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                speeches = data.get('data', [])
                for speech in speeches:
                    date = speech.get('date', '')
                    if date:
                        year, week = self.get_week_info(date)
                        week_key = f"{year}_w{week:02d}"
                        
                        if week_key not in weekly_speeches:
                            weekly_speeches[week_key] = []
                        weekly_speeches[week_key].append(speech)
                        
            except Exception as e:
                logger.error(f"❌ {json_file.name} 読み込みエラー: {e}")
                
        # 週次ファイルとして保存
        for week_key, speeches in weekly_speeches.items():
            if speeches:
                self.save_weekly_speeches(week_key, speeches)
                
        logger.info(f"✅ 議事録: {len(weekly_speeches)}週分を整理")
        
    def save_weekly_speeches(self, week_key: str, speeches: List[Dict[str, Any]]):
        """週次議事録データを保存"""
        year, week_num = week_key.split('_w')
        year_dir = self.weekly_data_dir / year
        year_dir.mkdir(exist_ok=True)
        
        # JSON形式（FlexSearch用）
        json_filepath = year_dir / f"speeches_{week_key}.json"
        json_data = {
            "metadata": {
                "data_type": "speeches_weekly",
                "year": int(year),
                "week": int(week_num),
                "total_count": len(speeches),
                "generated_at": datetime.now().isoformat(),
                "file_size_kb": 0  # 後で計算
            },
            "data": speeches
        }
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        # ファイルサイズを更新
        file_size_kb = json_filepath.stat().st_size / 1024
        json_data["metadata"]["file_size_kb"] = round(file_size_kb, 1)
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        # CSV形式（軽量版）
        csv_filepath = year_dir / f"speeches_{week_key}.csv"
        if speeches:
            # 必要最小限のフィールドのみ
            csv_speeches = []
            for speech in speeches:
                csv_speech = {
                    "date": speech.get("date", ""),
                    "speaker": speech.get("speaker", ""),
                    "party": speech.get("party", ""),
                    "committee": speech.get("committee", ""),
                    "text": speech.get("text", "")[:500] + "..." if len(speech.get("text", "")) > 500 else speech.get("text", ""),  # 500文字制限
                    "url": speech.get("url", "")
                }
                csv_speeches.append(csv_speech)
                
            fieldnames = ["date", "speaker", "party", "committee", "text", "url"]
            with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_speeches)
                
        csv_size_kb = csv_filepath.stat().st_size / 1024
        logger.info(f"💾 {week_key}: JSON {file_size_kb:.1f}KB, CSV {csv_size_kb:.1f}KB")
        
    def organize_parliamentary_by_week(self):
        """国会データを週次で整理"""
        logger.info("🏛️ 国会データを週次整理中...")
        
        data_types = ["bills", "questions", "petitions"]
        
        for data_type in data_types:
            data_dir = getattr(self, f"{data_type}_dir")
            if not data_dir.exists():
                continue
                
            weekly_data = {}
            
            for json_file in data_dir.glob("*.json"):
                if json_file.name.endswith('.backup'):
                    continue
                    
                try:
                    with open(json_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    items = data.get('data', [])
                    for item in items:
                        collected_at = item.get('collected_at', '')
                        if collected_at:
                            year, week = self.get_week_info(collected_at)
                            week_key = f"{year}_w{week:02d}"
                            
                            if week_key not in weekly_data:
                                weekly_data[week_key] = []
                            weekly_data[week_key].append(item)
                            
                except Exception as e:
                    logger.error(f"❌ {json_file.name} 読み込みエラー: {e}")
                    
            # 週次ファイルとして保存
            for week_key, items in weekly_data.items():
                if items:
                    self.save_weekly_parliamentary(week_key, data_type, items)
                    
            logger.info(f"✅ {data_type}: {len(weekly_data)}週分を整理")
            
    def save_weekly_parliamentary(self, week_key: str, data_type: str, items: List[Dict[str, Any]]):
        """週次国会データを保存"""
        year, week_num = week_key.split('_w')
        year_dir = self.weekly_data_dir / year
        year_dir.mkdir(exist_ok=True)
        
        # JSON形式
        json_filepath = year_dir / f"{data_type}_{week_key}.json"
        json_data = {
            "metadata": {
                "data_type": f"{data_type}_weekly",
                "year": int(year),
                "week": int(week_num),
                "total_count": len(items),
                "generated_at": datetime.now().isoformat()
            },
            "data": items
        }
        
        with open(json_filepath, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
            
        # CSV形式（軽量版）
        csv_filepath = year_dir / f"{data_type}_{week_key}.csv"
        if items:
            # データタイプに応じたフィールド選択
            if data_type == "bills":
                fieldnames = ["house", "bill_number", "bill_name", "status", "submission_date"]
            elif data_type == "questions":
                fieldnames = ["house", "title", "question_number", "url"]
            elif data_type == "petitions":
                fieldnames = ["house", "petition_number", "title", "petitioner", "status"]
            else:
                fieldnames = list(items[0].keys()) if items else []
                
            with open(csv_filepath, 'w', encoding='utf-8', newline='') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
                writer.writeheader()
                writer.writerows(items)
                
    def create_weekly_index(self):
        """週次インデックスファイルを作成"""
        logger.info("📋 週次インデックス作成中...")
        
        index_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "description": "週次データファイルのインデックス"
            },
            "weeks": {}
        }
        
        for year_dir in self.weekly_data_dir.glob("*/"):
            if year_dir.is_dir():
                year = year_dir.name
                
                for data_file in year_dir.glob("*.json"):
                    if "_w" in data_file.stem:
                        parts = data_file.stem.split('_')
                        if len(parts) >= 2:
                            data_type = parts[0]
                            week_info = f"{year}_{parts[1]}"
                            
                            if week_info not in index_data["weeks"]:
                                index_data["weeks"][week_info] = {
                                    "year": int(year),
                                    "week": int(parts[1][1:]),
                                    "files": {}
                                }
                                
                            file_size = data_file.stat().st_size / 1024
                            index_data["weeks"][week_info]["files"][data_type] = {
                                "json_file": data_file.name,
                                "csv_file": data_file.with_suffix('.csv').name,
                                "size_kb": round(file_size, 1)
                            }
                            
        # インデックス保存
        index_filepath = self.weekly_data_dir / "weekly_index.json"
        with open(index_filepath, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
            
        logger.info(f"📋 インデックス作成完了: {len(index_data['weeks'])}週分")
        
    def generate_summary_stats(self):
        """週次データの統計サマリー生成"""
        total_weeks = 0
        total_files = 0
        total_size_mb = 0
        
        for year_dir in self.weekly_data_dir.glob("*/"):
            if year_dir.is_dir():
                json_files = list(year_dir.glob("*.json"))
                total_files += len(json_files)
                
                for json_file in json_files:
                    if "_w" in json_file.name:
                        total_size_mb += json_file.stat().st_size / (1024 * 1024)
                        
        unique_weeks = set()
        for year_dir in self.weekly_data_dir.glob("*/"):
            for json_file in year_dir.glob("*_w*.json"):
                week_part = json_file.stem.split('_')[-1]
                unique_weeks.add(f"{year_dir.name}_{week_part}")
                
        total_weeks = len(unique_weeks)
        
        logger.info(f"📊 週次データ統計:")
        logger.info(f"   - 総週数: {total_weeks}週")
        logger.info(f"   - 総ファイル数: {total_files}個")
        logger.info(f"   - 総サイズ: {total_size_mb:.1f}MB")
        logger.info(f"   - 週平均サイズ: {(total_size_mb/total_weeks if total_weeks > 0 else 0):.1f}MB")

def main():
    """メイン処理"""
    organizer = WeeklyDataOrganizer()
    
    # 議事録データを週次整理
    organizer.organize_speeches_by_week()
    
    # 国会データを週次整理
    organizer.organize_parliamentary_by_week()
    
    # インデックス作成
    organizer.create_weekly_index()
    
    # 統計表示
    organizer.generate_summary_stats()
    
    logger.info("✨ 週次データ整理完了!")

if __name__ == "__main__":
    main()