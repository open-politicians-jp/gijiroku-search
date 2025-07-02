#!/usr/bin/env python3
"""
シンプルな重複除去
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def simple_deduplication():
    """シンプルな重複除去の実行"""
    logger.info("🔧 シンプル重複除去開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    original_candidates = data.get('data', [])
    logger.info(f"📊 元データ: {len(original_candidates)}名")
    
    # 重複の確認と報告
    duplicates = find_all_duplicates(original_candidates)
    
    # 重複除去の実行
    unique_candidates = remove_duplicates(original_candidates)
    
    removed_count = len(original_candidates) - len(unique_candidates)
    logger.info(f"🎯 重複除去完了:")
    logger.info(f"  元データ: {len(original_candidates)}名")
    logger.info(f"  重複除去後: {len(unique_candidates)}名")
    logger.info(f"  削除数: {removed_count}名")
    
    # 統計再計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in unique_candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    # データ更新
    data['data'] = unique_candidates
    data['metadata']['total_candidates'] = len(unique_candidates)
    data['metadata']['generated_at'] = datetime.now().isoformat()
    data['metadata']['data_type'] = "go2senkyo_simple_deduplicated_sangiin_2025"
    data['metadata']['collection_method'] = "simple_deduplication_only"
    
    data['statistics'] = {
        "by_party": party_stats,
        "by_prefecture": prefecture_stats,
        "by_constituency_type": {"single_member": len(unique_candidates)}
    }
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    deduplicated_file = data_dir / f"go2senkyo_simple_deduplicated_{timestamp}.json"
    
    with open(deduplicated_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {deduplicated_file}")
    
    # 最終確認
    verify_no_duplicates(unique_candidates)

def find_all_duplicates(candidates):
    """全ての重複を検索"""
    logger.info("🔍 重複候補者の検索...")
    
    # candidate_id ベースの重複
    id_groups = defaultdict(list)
    # 名前+都道府県ベースの重複  
    name_groups = defaultdict(list)
    
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', '')
        name = candidate.get('name', '')
        prefecture = candidate.get('prefecture', '')
        
        if candidate_id:
            id_groups[candidate_id].append(candidate)
        
        if name and prefecture:
            key = f"{name}_{prefecture}"
            name_groups[key].append(candidate)
    
    duplicates = {}
    
    # candidate_idで重複しているもの
    for candidate_id, entries in id_groups.items():
        if len(entries) > 1:
            duplicates[f"ID重複: {candidate_id}"] = entries
            logger.info(f"🚨 ID重複: {candidate_id} - {len(entries)}件")
            for entry in entries:
                logger.info(f"    {entry['name']} ({entry['prefecture']})")
    
    # 名前+都道府県で重複しているもの
    for key, entries in name_groups.items():
        if len(entries) > 1:
            # candidate_idが異なる場合のみ重複として扱う
            ids = [entry.get('candidate_id') for entry in entries]
            if len(set(ids)) > 1:  # 異なるIDがある場合
                duplicates[f"名前重複: {key}"] = entries
                logger.info(f"🚨 名前重複: {key} - {len(entries)}件")
                for entry in entries:
                    logger.info(f"    ID: {entry['candidate_id']} - {entry['name']} ({entry['party']})")
    
    return duplicates

def remove_duplicates(candidates):
    """重複候補者を除去"""
    logger.info("🗑️ 重複除去実行...")
    
    seen_ids = set()
    seen_name_pref = set()
    unique_candidates = []
    
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', '')
        name = candidate.get('name', '')
        prefecture = candidate.get('prefecture', '')
        
        # 重複判定キー
        name_pref_key = f"{name}_{prefecture}"
        
        # candidate_idを最優先で重複チェック
        if candidate_id in seen_ids:
            logger.debug(f"ID重複スキップ: {candidate_id} - {name} ({prefecture})")
            continue
        
        # 名前+都道府県での重複チェック
        if name_pref_key in seen_name_pref:
            logger.debug(f"名前重複スキップ: {name_pref_key}")
            continue
        
        # 重複していない場合は追加
        unique_candidates.append(candidate)
        
        if candidate_id:
            seen_ids.add(candidate_id)
        if name and prefecture:
            seen_name_pref.add(name_pref_key)
    
    return unique_candidates

def verify_no_duplicates(candidates):
    """重複が除去されたか確認"""
    logger.info("✅ 重複除去確認...")
    
    # candidate_id チェック
    ids = [c.get('candidate_id') for c in candidates if c.get('candidate_id')]
    if len(ids) != len(set(ids)):
        logger.error("❌ candidate_id重複が残っています")
        return False
    
    # 名前+都道府県チェック
    name_prefs = [f"{c.get('name', '')}_{c.get('prefecture', '')}" for c in candidates]
    if len(name_prefs) != len(set(name_prefs)):
        logger.error("❌ 名前+都道府県重複が残っています")
        return False
    
    logger.info("✅ 重複除去完了 - 重複なし確認")
    return True

if __name__ == "__main__":
    simple_deduplication()