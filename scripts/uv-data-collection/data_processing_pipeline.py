#!/usr/bin/env python3
"""
データ加工パイプライン

生データを以下の流れで処理：
1. data/raw/ から生データを読み込み
2. テキストクリーニング（改行・スペース整理）
3. フロントエンド用フォーマットに変換
4. data/processed/ に保存
5. 必要に応じてフロントエンドディレクトリにコピー
"""

import os
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataProcessingPipeline:
    """データ加工パイプライン"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        
        # ディレクトリ設定
        self.raw_dir = self.project_root / "data" / "raw"
        self.processed_dir = self.project_root / "data" / "processed"
        self.frontend_dir = self.project_root / "frontend" / "public" / "data"
        
        # ディレクトリ作成
        for dir_path in [self.processed_dir, self.frontend_dir]:
            for subdir in ["speeches", "manifestos", "analysis"]:
                (dir_path / subdir).mkdir(parents=True, exist_ok=True)
                
    def enhanced_text_cleaning(self, text: str) -> str:
        """
        強化されたテキストクリーニング
        
        - 全角スペースを完全除去または半角1個に統一
        - 連続する空白を1つに統一
        - 過度な改行を整理
        - 日本語文の自然な改行は保持
        - タブ文字の除去
        - 議事録特有の罫線・記号の整理
        """
        if not text:
            return text
            
        # 議事録特有の罫線文字を削除または簡略化
        text = re.sub(r'─{3,}', '---', text)  # 長い罫線を短く
        text = re.sub(r'…{3,}', '...', text)  # 長い点線を短く
        
        # 全角スペースの処理：
        # 1. 連続する全角スペースを1つの半角スペースに変換
        text = re.sub(r'　+', ' ', text)
        
        # 2. 日本語文字間の全角スペースは除去（名前の間など）
        text = re.sub(r'([あ-ん一-龯])\s+([あ-ん一-龯])', r'\1\2', text)
        
        # タブ文字を半角スペースに変換
        text = text.replace('\t', ' ')
        
        # 連続する半角スペースを1つに統一
        text = re.sub(r'[ ]+', ' ', text)
        
        # 行頭・行末のスペースを削除
        lines = []
        for line in text.split('\n'):
            # 各行の前後空白除去
            cleaned_line = line.strip()
            # 行内の過度なスペースも整理
            cleaned_line = re.sub(r'\s+', ' ', cleaned_line)
            lines.append(cleaned_line)
        
        # 空行の整理
        cleaned_lines = []
        prev_empty = False
        for line in lines:
            if line == '':
                # 連続する空行は1つだけ保持
                if not prev_empty:
                    cleaned_lines.append(line)
                prev_empty = True
            else:
                cleaned_lines.append(line)
                prev_empty = False
        
        # 最終結果の組み立て
        result = '\n'.join(cleaned_lines).strip()
        
        # 最終的な細かい調整
        # 改行前後の不要な空白除去
        result = re.sub(r'\s*\n\s*', '\n', result)
        
        # 記号と文字の間の過度な空白調整
        result = re.sub(r'([。、])\s+', r'\1', result)  # 句読点後の不要空白
        result = re.sub(r'\s+([。、])', r'\1', result)  # 句読点前の不要空白
        
        # 括弧と内容の間の空白調整
        result = re.sub(r'(\()\s+', r'\1', result)
        result = re.sub(r'\s+(\))', r'\1', result)
        result = re.sub(r'(（)\s+', r'\1', result)
        result = re.sub(r'\s+(）)', r'\1', result)
        
        return result
        
    def process_speech_data(self, speech_data: Dict[str, Any]) -> Dict[str, Any]:
        """個別の発言データを処理"""
        processed_data = speech_data.copy()
        
        # テキストフィールドをクリーンアップ
        if 'text' in processed_data and processed_data['text']:
            processed_data['text'] = self.enhanced_text_cleaning(processed_data['text'])
            
        # その他のテキストフィールドも処理
        text_fields = ['speaker', 'committee', 'party', 'position']
        for field in text_fields:
            if field in processed_data and processed_data[field]:
                processed_data[field] = self.enhanced_text_cleaning(processed_data[field])
        
        return processed_data
        
    def process_raw_file(self, raw_file_path: Path) -> Optional[Dict[str, Any]]:
        """生ファイルを処理"""
        logger.info(f"📝 処理中: {raw_file_path.name}")
        
        try:
            with open(raw_file_path, 'r', encoding='utf-8') as f:
                raw_data = json.load(f)
                
            if 'data' not in raw_data:
                logger.warning(f"⚠️ 'data' フィールドが見つかりません: {raw_file_path.name}")
                return None
                
            speeches = raw_data['data']
            original_count = len(speeches)
            
            # 各発言データを処理
            processed_speeches = []
            for speech in speeches:
                processed_speech = self.process_speech_data(speech)
                processed_speeches.append(processed_speech)
                
            # 処理済みメタデータ作成
            processed_data = {
                "metadata": {
                    "data_type": "speeches_processed",
                    "total_count": len(processed_speeches),
                    "generated_at": datetime.now().isoformat(),
                    "source": "https://kokkai.ndl.go.jp/api.html",
                    "processed_from": str(raw_file_path),
                    "processing_method": "enhanced_text_cleaning_pipeline",
                    "original_count": original_count
                },
                "data": processed_speeches
            }
            
            logger.info(f"✅ 処理完了: {original_count}件")
            return processed_data
            
        except Exception as e:
            logger.error(f"❌ 処理エラー: {raw_file_path.name} - {e}")
            return None
            
    def save_processed_data(self, processed_data: Dict[str, Any], output_path: Path):
        """処理済みデータを保存"""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(processed_data, f, ensure_ascii=False, indent=2)
            
        file_size = output_path.stat().st_size / (1024 * 1024)
        logger.info(f"💾 保存: {output_path.name} ({file_size:.1f} MB)")
        
    def process_speeches(self) -> List[Path]:
        """議事録データを処理"""
        logger.info("🎯 議事録データ処理開始...")
        
        speeches_raw_dir = self.raw_dir / "speeches"
        speeches_processed_dir = self.processed_dir / "speeches"
        
        if not speeches_raw_dir.exists():
            logger.warning(f"⚠️ 生データディレクトリが存在しません: {speeches_raw_dir}")
            return []
            
        raw_files = list(speeches_raw_dir.glob("speeches_*.json"))
        if not raw_files:
            logger.warning(f"⚠️ 処理対象の生ファイルが見つかりません")
            return []
            
        logger.info(f"📊 処理対象: {len(raw_files)}ファイル")
        
        processed_files = []
        for raw_file in sorted(raw_files):
            # 既存の処理済みファイルチェック
            processed_filename = f"processed_{raw_file.name}"
            processed_filepath = speeches_processed_dir / processed_filename
            
            process_all = os.getenv('PROCESS_ALL', 'false').lower() == 'true'
            
            if processed_filepath.exists() and not process_all:
                logger.info(f"⏭️ スキップ（既存）: {processed_filename}")
                processed_files.append(processed_filepath)
                continue
                
            # データ処理
            processed_data = self.process_raw_file(raw_file)
            if processed_data:
                self.save_processed_data(processed_data, processed_filepath)
                processed_files.append(processed_filepath)
                
        logger.info(f"🎉 議事録処理完了: {len(processed_files)}ファイル")
        return processed_files
        
    def create_unified_dataset(self, processed_files: List[Path]) -> Optional[Path]:
        """統合データセットを作成"""
        if not processed_files:
            logger.warning("⚠️ 統合対象ファイルがありません")
            return None
            
        logger.info("🔗 統合データセット作成中...")
        
        all_speeches = []
        total_files = 0
        
        for processed_file in processed_files:
            try:
                with open(processed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                if 'data' in data:
                    all_speeches.extend(data['data'])
                    total_files += 1
                    
            except Exception as e:
                logger.error(f"❌ 統合エラー: {processed_file.name} - {e}")
                
        if not all_speeches:
            logger.warning("⚠️ 統合データが空です")
            return None
            
        # 日付順にソート
        all_speeches.sort(key=lambda x: x.get('date', ''), reverse=True)
        
        # 現在の年月を取得
        current_date = datetime.now()
        year_month = current_date.strftime("%Y%m")
        
        # 統合データセット作成
        unified_data = {
            "metadata": {
                "data_type": "speeches_unified_processed",
                "total_count": len(all_speeches),
                "generated_at": current_date.isoformat(),
                "source": "https://kokkai.ndl.go.jp/api.html",
                "processing_method": "enhanced_text_cleaning_pipeline",
                "source_files": total_files,
                "filename_format": f"speeches_unified_{year_month}.json"
            },
            "data": all_speeches
        }
        
        # 保存
        unified_filename = f"speeches_unified_{year_month}.json"
        unified_filepath = self.processed_dir / "speeches" / unified_filename
        
        self.save_processed_data(unified_data, unified_filepath)
        
        logger.info(f"🎉 統合完了: {len(all_speeches)}件 -> {unified_filename}")
        return unified_filepath
        
    def deploy_to_frontend(self, unified_file: Optional[Path]):
        """フロントエンドに配置"""
        if not unified_file or not unified_file.exists():
            logger.warning("⚠️ 配置対象ファイルがありません")
            return
            
        logger.info("🚀 フロントエンドに配置中...")
        
        # メインの統合ファイルをコピー
        frontend_main_file = self.frontend_dir / "speeches" / "speeches_latest.json"
        shutil.copy2(unified_file, frontend_main_file)
        logger.info(f"📁 メインファイル配置: {frontend_main_file.name}")
        
        # 下位互換性のため、旧ファイル名でもコピー
        frontend_compat_file = self.frontend_dir / "speeches_processed.json"
        shutil.copy2(unified_file, frontend_compat_file)
        logger.info(f"📁 互換ファイル配置: {frontend_compat_file.name}")
        
        logger.info("✅ フロントエンド配置完了")

def main():
    """メイン処理"""
    logger.info("🚀 データ加工パイプライン開始...")
    
    pipeline = DataProcessingPipeline()
    
    # 1. 議事録データ処理
    processed_files = pipeline.process_speeches()
    
    # 2. 統合データセット作成
    unified_file = pipeline.create_unified_dataset(processed_files)
    
    # 3. フロントエンドに配置
    pipeline.deploy_to_frontend(unified_file)
    
    logger.info("✨ データ加工パイプライン完了!")

if __name__ == "__main__":
    main()