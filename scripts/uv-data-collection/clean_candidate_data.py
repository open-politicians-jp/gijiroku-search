#!/usr/bin/env python3
"""
候補者データクリーニング
不適切な名前やノイズデータの除去
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CandidateDataCleaner:
    def __init__(self):
        # 除外すべきキーワード（候補者名として不適切）
        self.invalid_keywords = [
            # 組織・団体名
            '支部', '本部', '事務所', '事務局', '委員会', '協会', '団体', '組織',
            '局', '部', '課', '室', '会', '党', '政治', '選挙', '議員',
            
            # 一般的な語句
            'について', 'こちら', 'ページ', 'サイト', 'ホーム', 'トップ',
            'メニュー', 'ナビ', 'リンク', '詳細', '一覧', 'リスト',
            
            # 政治用語
            '政策', '公約', '公報', 'マニフェスト', '投票', '開票', '当選',
            '落選', '比例', '選挙区', '都道府県', '市区町村',
            
            # その他
            '大学', '学校', '研究', '調査', '報告', '発表', '記者',
            '女性', '青年', '学生', '市民', '国民', '県民', '都民'
        ]
        
        # 適切な日本人名のパターン
        self.valid_name_patterns = [
            r'^[一-龯]{1,3}\s*[一-龯]{1,3}$',  # 漢字のみ（姓+名）
            r'^[一-龯ひらがな]{2,10}$',        # 漢字・ひらがな混在
            r'^[ァ-ヶー]{2,10}$',              # カタカナのみ
        ]

    def clean_official_sources_data(self):
        """公式ソースデータのクリーニング"""
        logger.info("🧹 公式ソースデータクリーニング開始...")
        
        # 最新の公式ソースファイルを読み込み
        data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
        
        # 最新ファイルを探す
        official_files = list(data_dir.glob("official_sources_*.json"))
        if not official_files:
            logger.error("❌ 公式ソースファイルが見つかりません")
            return
        
        latest_file = max(official_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"📁 処理対象ファイル: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_candidates = data.get('data', [])
        logger.info(f"📊 元データ: {len(original_candidates)}名")
        
        # データクリーニング実行
        cleaned_candidates = self.clean_candidates(original_candidates)
        
        # 統計再計算
        party_stats = {}
        prefecture_stats = {}
        
        for candidate in cleaned_candidates:
            party = candidate.get('party', '未分類')
            prefecture = candidate.get('prefecture', '未分類')
            
            party_stats[party] = party_stats.get(party, 0) + 1
            if prefecture != '未分類':
                prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
        
        # クリーン版データ作成
        cleaned_data = {
            "metadata": {
                "data_type": "official_sources_cleaned_sangiin_2025",
                "collection_method": "soumu_party_official_sources_cleaned",
                "total_candidates": len(cleaned_candidates),
                "original_candidates": len(original_candidates),
                "removed_candidates": len(original_candidates) - len(cleaned_candidates),
                "generated_at": datetime.now().isoformat(),
                "sources": ["総務省選挙部", "各政党公式サイト"],
                "coverage": {
                    "parties": len(party_stats),
                    "prefectures": len(prefecture_stats) if prefecture_stats else 0
                }
            },
            "statistics": {
                "by_party": party_stats,
                "by_prefecture": prefecture_stats,
                "by_constituency_type": {"single_member": len(cleaned_candidates)}
            },
            "data": cleaned_candidates
        }
        
        # ファイル保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        cleaned_file = data_dir / f"official_sources_cleaned_{timestamp}.json"
        latest_cleaned_file = data_dir / "go2senkyo_optimized_latest.json"
        
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
        
        # 候補者数が合理的な場合のみ最新ファイルを更新
        if len(cleaned_candidates) >= 100:  # 最低100名の候補者が必要
            with open(latest_cleaned_file, 'w', encoding='utf-8') as f:
                json.dump(cleaned_data, f, ensure_ascii=False, indent=2)
            logger.info(f"📁 最新ファイル更新: {latest_cleaned_file}")
        
        logger.info(f"📁 クリーンデータ保存: {cleaned_file}")
        
        # 結果表示
        logger.info("\n📊 データクリーニング結果:")
        logger.info(f"  元データ: {len(original_candidates)}名")
        logger.info(f"  クリーン後: {len(cleaned_candidates)}名")
        logger.info(f"  除去数: {len(original_candidates) - len(cleaned_candidates)}名")
        logger.info(f"  政党数: {len(party_stats)}政党")
        logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
        
        for party, count in party_stats.items():
            logger.info(f"    {party}: {count}名")
        
        return cleaned_file

    def clean_candidates(self, candidates):
        """候補者リストのクリーニング"""
        cleaned = []
        removed_count = 0
        removal_reasons = {}
        
        for candidate in candidates:
            name = candidate.get('name', '').strip()
            
            # クリーニング判定
            is_valid, reason = self.is_valid_candidate(name)
            
            if is_valid:
                # 名前の正規化
                candidate['name'] = self.normalize_name(name)
                cleaned.append(candidate)
            else:
                removed_count += 1
                removal_reasons[reason] = removal_reasons.get(reason, 0) + 1
                logger.debug(f"除去: {name} (理由: {reason})")
        
        logger.info(f"🗑️ 除去詳細:")
        for reason, count in removal_reasons.items():
            logger.info(f"  {reason}: {count}件")
        
        return cleaned

    def is_valid_candidate(self, name):
        """候補者名の妥当性チェック"""
        if not name:
            return False, "空の名前"
        
        if len(name) < 2 or len(name) > 15:
            return False, "名前の長さが不適切"
        
        # 無効キーワードチェック
        for keyword in self.invalid_keywords:
            if keyword in name:
                return False, f"無効キーワード含有: {keyword}"
        
        # 数字や記号のチェック
        if re.search(r'[0-9]', name):
            return False, "数字含有"
        
        if re.search(r'[!@#$%^&*()_+=\[\]{}|;:,.<>?]', name):
            return False, "記号含有"
        
        # URLや英語のチェック
        if re.search(r'[a-zA-Z]', name):
            return False, "英語含有"
        
        if 'http' in name.lower() or 'www' in name.lower():
            return False, "URL含有"
        
        # 日本人名パターンチェック
        for pattern in self.valid_name_patterns:
            if re.match(pattern, name):
                return True, "有効な名前"
        
        # その他の日本語文字チェック
        if re.match(r'^[一-龯ひらがなァ-ヶー\s]+$', name):
            # 特殊なパターンもチェック
            if not self.has_suspicious_patterns(name):
                return True, "有効な名前"
        
        return False, "無効なパターン"

    def has_suspicious_patterns(self, name):
        """疑わしいパターンのチェック"""
        suspicious_patterns = [
            r'.*運営.*',
            r'.*管理.*',
            r'.*代表.*',
            r'.*責任者.*',
            r'.*担当.*',
            r'.*連絡.*',
            r'.*窓口.*',
            r'.*相談.*',
            r'.*問い合わせ.*',
        ]
        
        for pattern in suspicious_patterns:
            if re.search(pattern, name):
                return True
        
        return False

    def normalize_name(self, name):
        """名前の正規化"""
        # 余分なスペースを除去
        name = re.sub(r'\s+', ' ', name).strip()
        
        # 全角スペースを半角スペースに変換
        name = name.replace('　', ' ')
        
        # 連続するスペースを1つに統一
        name = re.sub(r' +', ' ', name)
        
        return name

def main():
    """メイン処理"""
    logger.info("🧹 候補者データクリーニング開始...")
    
    cleaner = CandidateDataCleaner()
    cleaned_file = cleaner.clean_official_sources_data()
    
    if cleaned_file:
        logger.info(f"✅ データクリーニング完了: {cleaned_file}")
    else:
        logger.error("❌ データクリーニング失敗")

if __name__ == "__main__":
    main()