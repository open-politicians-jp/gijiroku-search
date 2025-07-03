#!/usr/bin/env python3
"""
最終重複除去スクリプト
同一人物の重複を削除し、最新データを生成
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def fix_duplicates_final():
    """最終的な重複除去"""
    logger.info("🔧 最終重複除去開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    input_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data['data'])
    logger.info(f"📊 元データ: {original_count}名")
    
    # 重複検出と除去
    seen_urls = set()
    seen_names = set()
    unique_candidates = []
    removed_duplicates = []
    
    for candidate in data['data']:
        name = candidate.get('name', '')
        prefecture = candidate.get('prefecture', '')
        profile_url = candidate.get('profile_url', '')
        
        is_duplicate = False
        
        # 1. URLベースの重複チェック（最優先）
        if profile_url and profile_url in seen_urls:
            is_duplicate = True
            reason = f"同一URL ({profile_url})"
        
        # 2. 同名候補者の重複チェック
        elif name in seen_names:
            is_duplicate = True
            reason = f"同名候補者"
        
        if is_duplicate:
            removed_duplicates.append(candidate)
            logger.info(f"🗑️ 重複除去: {name} ({prefecture}) - {reason}")
        else:
            unique_candidates.append(candidate)
            if profile_url:
                seen_urls.add(profile_url)
            seen_names.add(name)
    
    # 統計再計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in unique_candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    # 新しいデータ構造
    fixed_data = {
        "metadata": {
            "data_type": "go2senkyo_complete_structured_sangiin_2025_fixed",
            "collection_method": "structured_html_extraction_all_47_prefectures_deduplicated",
            "total_candidates": len(unique_candidates),
            "candidates_with_kana": len([c for c in unique_candidates if c.get('name_kana')]),
            "successful_prefectures": 47,
            "failed_prefectures": 0,
            "duplicates_removed": len(removed_duplicates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "coverage": {
                "constituency_types": 1,
                "parties": len(party_stats),
                "prefectures": len(prefecture_stats)
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_constituency_type": {"single_member": len(unique_candidates)}
        },
        "data": unique_candidates
    }
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = data_dir / f"go2senkyo_complete_fixed_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(fixed_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 固定ファイル保存: {output_file}")
    logger.info(f"📁 最新ファイル更新: {latest_file}")
    
    # 結果報告
    logger.info(f"\n✅ 重複除去完了:")
    logger.info(f"  元データ: {original_count}名")
    logger.info(f"  除去数: {len(removed_duplicates)}名")
    logger.info(f"  最終データ: {len(unique_candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    if removed_duplicates:
        logger.info(f"\n🗑️ 除去された重複:")
        for candidate in removed_duplicates:
            logger.info(f"  - {candidate['name']} ({candidate.get('prefecture', '不明')})")
    
    return output_file

if __name__ == "__main__":
    fix_duplicates_final()