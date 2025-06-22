#!/usr/bin/env python3
"""
データ更新チェッカー（Smart Skip機能）

GitHub Actions用に設計されたデータ更新の必要性判定システム：
- 最終処理日時の管理
- データタイプ別の更新頻度制御
- 強制実行オプション対応
"""

import os
import json
import sys
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, Any
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class UpdateChecker:
    """データ更新チェッカークラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = Path(__file__).parent / "data"
        self.data_dir.mkdir(exist_ok=True)
        
        # 最終処理日時ファイル
        self.last_processed_file = self.data_dir / "last_processed.json"
        
        # データタイプ別の更新間隔設定
        self.update_intervals = {
            'speeches': timedelta(days=1),        # 議事録: 毎日
            'committee_news': timedelta(days=1),  # 委員会ニュース: 毎日
            'manifestos': timedelta(days=7),      # マニフェスト: 週1回
            'bills': timedelta(days=1),           # 法案: 毎日
            'questions': timedelta(days=1),       # 質問主意書: 毎日
            'legislators': timedelta(days=30),    # 議員データ: 月1回
        }
    
    def load_last_processed(self) -> Dict[str, str]:
        """最終処理日時を読み込み"""
        try:
            if self.last_processed_file.exists():
                with open(self.last_processed_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            logger.warning(f"最終処理日時読み込みエラー: {e}")
            return {}
    
    def save_last_processed(self, data: Dict[str, str]):
        """最終処理日時を保存"""
        try:
            with open(self.last_processed_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"最終処理日時保存エラー: {e}")
    
    def update_last_processed(self, data_type: str):
        """指定データタイプの最終処理日時を更新"""
        last_processed = self.load_last_processed()
        last_processed[data_type] = datetime.now().isoformat()
        self.save_last_processed(last_processed)
        logger.info(f"最終処理日時更新: {data_type} = {last_processed[data_type]}")
    
    def should_update(self, data_type: str) -> bool:
        """データ更新が必要かチェック"""
        # 強制実行フラグチェック
        if os.getenv('FORCE_UPDATE', 'false').lower() == 'true':
            logger.info(f"強制更新モード: {data_type}")
            return True
        
        # データタイプの有効性チェック
        if data_type not in self.update_intervals:
            logger.warning(f"未知のデータタイプ: {data_type}")
            return False
        
        # 最終処理日時チェック
        last_processed = self.load_last_processed()
        if data_type not in last_processed:
            logger.info(f"初回実行: {data_type}")
            return True
        
        try:
            last_time = datetime.fromisoformat(last_processed[data_type])
            interval = self.update_intervals[data_type]
            next_update = last_time + interval
            
            if datetime.now() >= next_update:
                logger.info(f"更新時期到達: {data_type} (前回: {last_time.strftime('%Y-%m-%d %H:%M')})")
                return True
            else:
                logger.info(f"更新不要: {data_type} (次回: {next_update.strftime('%Y-%m-%d %H:%M')})")
                return False
                
        except ValueError as e:
            logger.error(f"日時解析エラー: {data_type} - {e}")
            return True  # エラー時は更新実行
    
    def get_summary(self) -> str:
        """現在の状況サマリーを生成"""
        last_processed = self.load_last_processed()
        current_time = datetime.now()
        
        summary_lines = ["## 📊 データ更新状況サマリー", ""]
        
        for data_type, interval in self.update_intervals.items():
            if data_type in last_processed:
                try:
                    last_time = datetime.fromisoformat(last_processed[data_type])
                    next_update = last_time + interval
                    status = "⏰ 更新予定" if current_time >= next_update else "✅ 最新"
                    
                    summary_lines.append(
                        f"- **{data_type}**: {status} "
                        f"(前回: {last_time.strftime('%m/%d %H:%M')}, "
                        f"次回: {next_update.strftime('%m/%d %H:%M')})"
                    )
                except ValueError:
                    summary_lines.append(f"- **{data_type}**: ❌ 日時解析エラー")
            else:
                summary_lines.append(f"- **{data_type}**: 🆕 未実行")
        
        summary_lines.extend([
            "",
            f"**最終確認**: {current_time.strftime('%Y-%m-%d %H:%M:%S JST')}"
        ])
        
        return "\n".join(summary_lines)

def main():
    """メイン処理"""
    parser = argparse.ArgumentParser(description='データ更新チェッカー')
    parser.add_argument('--data-type', type=str, help='チェック対象のデータタイプ')
    parser.add_argument('--summary', action='store_true', help='サマリー表示')
    parser.add_argument('--update', type=str, help='指定データタイプの最終処理日時を更新')
    
    args = parser.parse_args()
    checker = UpdateChecker()
    
    if args.summary:
        # サマリー表示
        print(checker.get_summary())
        sys.exit(0)
    
    if args.update:
        # 最終処理日時更新
        checker.update_last_processed(args.update)
        sys.exit(0)
    
    if args.data_type:
        # 更新チェック
        should_update = checker.should_update(args.data_type)
        sys.exit(0 if should_update else 1)
    
    # 引数なしの場合はヘルプ表示
    parser.print_help()
    sys.exit(1)

if __name__ == "__main__":
    main()