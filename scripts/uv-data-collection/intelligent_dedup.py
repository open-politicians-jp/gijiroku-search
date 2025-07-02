#!/usr/bin/env python3
"""
インテリジェント重複除去
同一人物の複数県登録を適切に処理
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def intelligent_dedup():
    """インテリジェント重複除去"""
    logger.info("🧠 インテリジェント重複除去開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    input_file = data_dir / "go2senkyo_complete_structured_20250702_133412.json"
    
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_count = len(data['data'])
    logger.info(f"📊 元データ: {original_count}名")
    
    # 候補者を名前でグループ化
    name_groups = {}
    for candidate in data['data']:
        name = candidate.get('name', '')
        if name not in name_groups:
            name_groups[name] = []
        name_groups[name].append(candidate)
    
    # 重複除去処理
    unique_candidates = []
    removed_duplicates = []
    
    for name, candidates in name_groups.items():
        if len(candidates) == 1:
            # 重複なし - そのまま追加
            unique_candidates.append(candidates[0])
        else:
            # 重複あり - 最適な候補者を選択
            logger.info(f"🔍 重複検出: {name} ({len(candidates)}件)")
            
            # 同一人物の判定（URLが同じ場合）
            urls = [c.get('profile_url', '') for c in candidates]
            unique_urls = set(url for url in urls if url)
            
            if len(unique_urls) <= 1:
                # 同一人物の複数県登録 - 最初に収集された都道府県を採用
                selected = candidates[0]
                for candidate in candidates[1:]:
                    removed_duplicates.append(candidate)
                    logger.info(f"  🗑️ 除去: {candidate['prefecture']}")
                
                unique_candidates.append(selected)
                logger.info(f"  ✅ 採用: {selected['prefecture']}")
            else:
                # 異なる人物（同名異人） - 全て保持
                unique_candidates.extend(candidates)
                logger.info(f"  👥 同名異人として全て保持")
    
    # 統計再計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in unique_candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    # 最終データ構造
    final_data = {
        "metadata": {
            "data_type": "go2senkyo_complete_structured_sangiin_2025_intelligent_dedup",
            "collection_method": "structured_html_extraction_all_47_prefectures_intelligent_dedup",
            "total_candidates": len(unique_candidates),
            "candidates_with_kana": len([c for c in unique_candidates if c.get('name_kana')]),
            "successful_prefectures": 47,
            "failed_prefectures": 0,
            "intelligent_duplicates_removed": len(removed_duplicates),
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
    output_file = data_dir / f"go2senkyo_intelligent_dedup_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 インテリジェントファイル保存: {output_file}")
    logger.info(f"📁 最新ファイル更新: {latest_file}")
    
    # 結果報告
    logger.info(f"\n✅ インテリジェント重複除去完了:")
    logger.info(f"  元データ: {original_count}名")
    logger.info(f"  インテリジェント除去数: {len(removed_duplicates)}名")
    logger.info(f"  最終データ: {len(unique_candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    if removed_duplicates:
        logger.info(f"\n🗑️ 除去された重複（同一人物の複数県登録）:")
        for candidate in removed_duplicates:
            logger.info(f"  - {candidate['name']} ({candidate.get('prefecture', '不明')})")
    
    return output_file

if __name__ == "__main__":
    intelligent_dedup()