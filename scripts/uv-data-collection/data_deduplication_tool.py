#!/usr/bin/env python3
"""
データ重複検出・排除ツール (Issue #86対応)

質問主意書・提出法案データの重複ファイルを検出・削除し、
データ収集処理時間を40分→5-10分に短縮するためのツール

機能:
- 重複ファイルの自動検出
- SHA256ハッシュによる高速重複比較
- 安全な重複ファイル削除
- データ統合・最適化
- 処理結果レポート生成
"""

import json
import hashlib
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Tuple, Any
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataDeduplicationTool:
    """データ重複検出・排除ツール"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.data_dir = self.project_root / "frontend" / "public" / "data"
        self.backup_dir = self.project_root / "data" / "backup" / f"dedup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # 対象ディレクトリ
        self.target_dirs = {
            "questions": self.data_dir / "questions",
            "bills": self.data_dir / "bills"
        }
        
        # 除外ファイル（削除対象外）
        self.excluded_files = {
            "questions_latest.json",
            "bills_latest.json"
        }
        
        self.duplicate_stats = {
            "questions": {"files_analyzed": 0, "duplicates_found": 0, "space_saved": 0},
            "bills": {"files_analyzed": 0, "duplicates_found": 0, "space_saved": 0}
        }
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """ファイルのSHA256ハッシュを計算"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # collected_atなどのタイムスタンプを除外したハッシュ計算
            normalized_data = self.normalize_data_for_hash(data)
            data_str = json.dumps(normalized_data, sort_keys=True, ensure_ascii=False)
            
            return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
        
        except Exception as e:
            logger.error(f"ハッシュ計算エラー ({file_path}): {e}")
            return ""
    
    def normalize_data_for_hash(self, data: Any) -> Any:
        """ハッシュ計算用にデータを正規化（タイムスタンプ除去）"""
        if isinstance(data, dict):
            normalized = {}
            for key, value in data.items():
                # タイムスタンプ系フィールドを除外
                if key in ['collected_at', 'generated_at', 'created_at', 'updated_at']:
                    continue
                normalized[key] = self.normalize_data_for_hash(value)
            return normalized
        elif isinstance(data, list):
            return [self.normalize_data_for_hash(item) for item in data]
        else:
            return data
    
    def find_duplicates_in_directory(self, dir_name: str) -> Dict[str, List[Path]]:
        """ディレクトリ内の重複ファイルを検出"""
        directory = self.target_dirs[dir_name]
        
        if not directory.exists():
            logger.warning(f"ディレクトリが存在しません: {directory}")
            return {}
        
        logger.info(f"🔍 {dir_name}ディレクトリの重複検出開始...")
        
        hash_to_files = {}
        json_files = list(directory.glob("*.json"))
        
        for file_path in json_files:
            # 除外ファイルをスキップ
            if file_path.name in self.excluded_files:
                continue
            
            file_hash = self.calculate_file_hash(file_path)
            
            if file_hash:
                if file_hash not in hash_to_files:
                    hash_to_files[file_hash] = []
                hash_to_files[file_hash].append(file_path)
        
        # 重複ファイル（同じハッシュで複数ファイル）のみ抽出
        duplicates = {h: files for h, files in hash_to_files.items() if len(files) > 1}
        
        self.duplicate_stats[dir_name]["files_analyzed"] = len(json_files)
        self.duplicate_stats[dir_name]["duplicates_found"] = sum(len(files) - 1 for files in duplicates.values())
        
        logger.info(f"📊 {dir_name}: {len(json_files)}ファイル分析, {len(duplicates)}グループの重複発見")
        
        return duplicates
    
    def backup_file(self, file_path: Path) -> Path:
        """ファイルをバックアップ"""
        relative_path = file_path.relative_to(self.data_dir)
        backup_path = self.backup_dir / relative_path
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(file_path, backup_path)
        return backup_path
    
    def select_files_to_keep(self, duplicate_files: List[Path]) -> Tuple[Path, List[Path]]:
        """重複ファイル群から保持するファイルと削除するファイルを選択"""
        if not duplicate_files:
            return None, []
        
        # 選択基準の優先順位:
        # 1. _latest.jsonファイル（存在する場合）
        # 2. ファイルサイズが最大
        # 3. 最新のタイムスタンプ
        
        latest_files = [f for f in duplicate_files if f.name.endswith('_latest.json')]
        if latest_files:
            keep_file = latest_files[0]
        else:
            # ファイルサイズでソート（降順）
            files_by_size = sorted(duplicate_files, key=lambda f: f.stat().st_size, reverse=True)
            keep_file = files_by_size[0]
        
        files_to_remove = [f for f in duplicate_files if f != keep_file]
        
        return keep_file, files_to_remove
    
    def remove_duplicate_files(self, dir_name: str, duplicates: Dict[str, List[Path]], dry_run: bool = False) -> int:
        """重複ファイルを削除"""
        total_space_saved = 0
        files_removed = 0
        
        logger.info(f"🗑️ {dir_name}の重複ファイル削除開始...")
        
        for file_hash, duplicate_files in duplicates.items():
            keep_file, files_to_remove = self.select_files_to_keep(duplicate_files)
            
            if not keep_file or not files_to_remove:
                continue
            
            logger.info(f"📁 保持: {keep_file.name}")
            
            for file_to_remove in files_to_remove:
                file_size = file_to_remove.stat().st_size
                total_space_saved += file_size
                files_removed += 1
                
                if dry_run:
                    logger.info(f"🧪 [DRY RUN] 削除予定: {file_to_remove.name} ({file_size:,} bytes)")
                else:
                    # バックアップ作成
                    backup_path = self.backup_file(file_to_remove)
                    logger.info(f"💾 バックアップ: {backup_path}")
                    
                    # ファイル削除
                    file_to_remove.unlink()
                    logger.info(f"✅ 削除完了: {file_to_remove.name} ({file_size:,} bytes)")
        
        self.duplicate_stats[dir_name]["space_saved"] = total_space_saved
        
        action = "削除予定" if dry_run else "削除完了"
        logger.info(f"🎉 {dir_name}: {files_removed}ファイル{action}, {total_space_saved:,} bytes節約")
        
        return files_removed
    
    def generate_deduplication_report(self) -> str:
        """重複除去レポートを生成"""
        current_time = datetime.now().isoformat()
        
        report = f"""
📊 データ重複除去レポート
生成日時: {current_time}

=== 処理結果サマリー ===
"""
        
        total_files_analyzed = 0
        total_duplicates_found = 0
        total_space_saved = 0
        
        for dir_name, stats in self.duplicate_stats.items():
            total_files_analyzed += stats["files_analyzed"]
            total_duplicates_found += stats["duplicates_found"]
            total_space_saved += stats["space_saved"]
            
            report += f"""
{dir_name.upper()}:
  - 分析ファイル数: {stats["files_analyzed"]}
  - 重複ファイル数: {stats["duplicates_found"]}
  - 節約容量: {stats["space_saved"]:,} bytes ({stats["space_saved"]/1024/1024:.2f} MB)
"""
        
        report += f"""
=== 総合結果 ===
総分析ファイル数: {total_files_analyzed}
総重複ファイル数: {total_duplicates_found}
総節約容量: {total_space_saved:,} bytes ({total_space_saved/1024/1024:.2f} MB)

削除率: {(total_duplicates_found/total_files_analyzed*100):.1f}%
容量削減効果: {(total_space_saved/(total_space_saved+10*1024*1024)*100):.1f}%

=== バックアップ場所 ===
{self.backup_dir}

=== 処理完了時刻 ===
{datetime.now().isoformat()}
"""
        
        return report
    
    def save_report(self, report: str):
        """レポートをファイルに保存"""
        report_path = self.backup_dir / "deduplication_report.txt"
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📄 レポート保存: {report_path}")
    
    def run_deduplication(self, dry_run: bool = False):
        """重複除去処理の実行"""
        logger.info("🚀 データ重複除去処理開始...")
        
        if dry_run:
            logger.info("🧪 DRY RUNモード: 実際の削除は行いません")
        
        total_removed = 0
        
        for dir_name in self.target_dirs.keys():
            try:
                # 重複検出
                duplicates = self.find_duplicates_in_directory(dir_name)
                
                if duplicates:
                    # 重複ファイル削除
                    removed_count = self.remove_duplicate_files(dir_name, duplicates, dry_run)
                    total_removed += removed_count
                else:
                    logger.info(f"✨ {dir_name}: 重複ファイルなし")
            
            except Exception as e:
                logger.error(f"❌ {dir_name}処理エラー: {str(e)}")
                continue
        
        # レポート生成・保存
        report = self.generate_deduplication_report()
        
        if not dry_run:
            self.save_report(report)
        
        logger.info(report)
        logger.info(f"✨ 重複除去処理完了: {total_removed}ファイル処理")

def main():
    """メイン実行関数"""
    import sys
    
    logger.info("🔧 データ重複検出・排除ツール (Issue #86)")
    
    tool = DataDeduplicationTool()
    
    # コマンドライン引数で動作モード決定
    force_run = "--force" in sys.argv
    dry_run_only = "--dry-run" in sys.argv
    
    try:
        # まずDRY RUNで確認
        logger.info("=== DRY RUN 実行 ===")
        tool.run_deduplication(dry_run=True)
        
        if dry_run_only:
            logger.info("DRY RUNのみで終了します")
            return
        
        if force_run:
            logger.info("\n=== 自動実行モード：重複ファイル削除実行 ===")
            tool.run_deduplication(dry_run=False)
        else:
            # インタラクティブモード（CI環境では使用不可）
            try:
                user_input = input("\n実際に重複ファイルを削除しますか？ (y/N): ")
                
                if user_input.lower() in ['y', 'yes']:
                    logger.info("\n=== 実際の削除実行 ===")
                    tool.run_deduplication(dry_run=False)
                else:
                    logger.info("重複削除をキャンセルしました")
            except EOFError:
                logger.info("CI環境detected: --forceオプションを使用してください")
        
    except KeyboardInterrupt:
        logger.info("処理が中断されました")
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()