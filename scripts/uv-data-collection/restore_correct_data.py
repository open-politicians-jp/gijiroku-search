#!/usr/bin/env python3
"""
正しいデータ復元スクリプト
誤って除去された候補者を復元し、真の重複のみを除去
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def restore_correct_data():
    """正しいデータ復元"""
    logger.info("🔧 正しいデータ復元開始...")
    
    # 元の完全データを読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    complete_file = data_dir / "go2senkyo_complete_structured_20250702_133412.json"
    
    with open(complete_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data['data'])
    logger.info(f"📊 元の完全データ: {original_count}名")
    
    # 真の重複のみを検出（同一人物が完全に同じ情報で重複している場合のみ）
    seen = set()
    unique_candidates = []
    removed_duplicates = []
    
    for candidate in data['data']:
        name = candidate.get('name', '')
        prefecture = candidate.get('prefecture', '')
        party = candidate.get('party', '')
        profile_url = candidate.get('profile_url', '')
        
        # 重複判定キー: 名前 + 都道府県 + 政党 + URL
        # これにより真の重複のみを検出
        key = f"{name}_{prefecture}_{party}_{profile_url}"
        
        if key not in seen:
            seen.add(key)
            unique_candidates.append(candidate)
        else:
            removed_duplicates.append(candidate)
            logger.info(f"🗑️ 真の重複除去: {name} ({prefecture}, {party})")
    
    # 統計再計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in unique_candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    # 正しいデータ構造
    correct_data = {
        "metadata": {
            "data_type": "go2senkyo_complete_structured_sangiin_2025_correct",
            "collection_method": "structured_html_extraction_all_47_prefectures_correct_dedup",
            "total_candidates": len(unique_candidates),
            "candidates_with_kana": len([c for c in unique_candidates if c.get('name_kana')]),
            "successful_prefectures": 47,
            "failed_prefectures": 0,
            "true_duplicates_removed": len(removed_duplicates),
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
    output_file = data_dir / f"go2senkyo_complete_correct_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(correct_data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(correct_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 正しいファイル保存: {output_file}")
    logger.info(f"📁 最新ファイル更新: {latest_file}")
    
    # 結果報告
    logger.info(f"\n✅ 正しいデータ復元完了:")
    logger.info(f"  元データ: {original_count}名")
    logger.info(f"  真の重複除去数: {len(removed_duplicates)}名")
    logger.info(f"  最終データ: {len(unique_candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    # 主要都道府県の確認
    logger.info(f"\n📍 主要都道府県:")
    major_prefs = sorted(prefecture_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    for pref, count in major_prefs:
        logger.info(f"  {pref}: {count}名")
    
    # 島根県・高知県の復元確認
    shimane_count = prefecture_stats.get('島根県', 0)
    kochi_count = prefecture_stats.get('高知県', 0)
    logger.info(f"\n🔍 復元確認:")
    logger.info(f"  島根県: {shimane_count}名")
    logger.info(f"  高知県: {kochi_count}名")
    
    if removed_duplicates:
        logger.info(f"\n🗑️ 除去された真の重複:")
        for candidate in removed_duplicates:
            logger.info(f"  - {candidate['name']} ({candidate.get('prefecture', '不明')})")
    
    return output_file

if __name__ == "__main__":
    restore_correct_data()