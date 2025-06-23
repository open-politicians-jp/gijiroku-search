#!/usr/bin/env python3
"""
要約ファイルインデックス更新スクリプト

既存の要約ファイルから summaries_index.json を生成・更新します。
フロントエンドでの動的ファイル読み込みに使用されます。
"""

import json
import os
import logging
from datetime import datetime
from pathlib import Path

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def update_summaries_index():
    """要約ファイルのインデックスを更新"""
    try:
        # プロジェクトルートディレクトリを取得
        project_root = Path(__file__).parent.parent.parent
        summaries_dir = project_root / "frontend" / "public" / "data" / "summaries"
        
        logger.info(f"📁 要約ディレクトリ: {summaries_dir}")
        
        if not summaries_dir.exists():
            logger.warning(f"要約ディレクトリが存在しません: {summaries_dir}")
            summaries_dir.mkdir(parents=True, exist_ok=True)
            logger.info("要約ディレクトリを作成しました")
        
        # summariesディレクトリ内のJSONファイルを取得
        summary_files = []
        for file_path in summaries_dir.glob("summary_*.json"):
            # インデックスファイル自体は除外
            if file_path.name != "summaries_index.json":
                summary_files.append(file_path.name)
        
        # 日付順でソート（新しい順）
        summary_files.sort(key=lambda x: extract_date_from_filename(x), reverse=True)
        
        logger.info(f"🔍 発見されたファイル数: {len(summary_files)}")
        for file in summary_files:
            logger.info(f"  - {file}")
        
        # インデックスデータ作成
        index_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "total_files": len(summary_files),
                "description": "Summary files index for dynamic loading",
                "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            },
            "files": summary_files
        }
        
        # インデックスファイル保存
        index_path = summaries_dir / "summaries_index.json"
        with open(index_path, 'w', encoding='utf-8') as f:
            json.dump(index_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 要約インデックス更新完了!")
        logger.info(f"  - ファイル数: {len(summary_files)}")
        logger.info(f"  - インデックスファイル: {index_path}")
        logger.info(f"  - ファイルサイズ: {index_path.stat().st_size} bytes")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ インデックス更新エラー: {e}")
        return False

def extract_date_from_filename(filename: str) -> str:
    """ファイル名から日付を抽出（ソート用）"""
    try:
        # summary_20250603_衆議_議院運営委員会.json から 20250603 を抽出
        parts = filename.split('_')
        if len(parts) >= 2:
            return parts[1]  # 20250603
        return "00000000"  # デフォルト値
    except:
        return "00000000"

def main():
    """メイン実行関数"""
    logger.info("🚀 要約インデックス更新開始")
    
    success = update_summaries_index()
    
    if success:
        logger.info("✨ 要約インデックス更新処理完了")
    else:
        logger.error("❌ 要約インデックス更新処理失敗")
        exit(1)

if __name__ == "__main__":
    main()