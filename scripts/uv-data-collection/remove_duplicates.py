#!/usr/bin/env python3
"""
重複データの削除
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collections import defaultdict

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def remove_duplicates():
    """重複データを削除"""
    logger.info("🔍 重複データチェック開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('data', [])
    logger.info(f"📊 元データ: {len(candidates)}名")
    
    # 重複チェック
    duplicates = find_duplicates(candidates)
    
    if duplicates:
        logger.info(f"🚨 重複発見: {len(duplicates)}パターン")
        for key, entries in duplicates.items():
            logger.info(f"  {key}: {len(entries)}個")
            for i, entry in enumerate(entries):
                logger.info(f"    {i+1}: {entry['prefecture']} - {entry['constituency']} (ID: {entry['candidate_id']})")
    
    # 重複削除
    unique_candidates = deduplicate_candidates(candidates)
    
    removed_count = len(candidates) - len(unique_candidates)
    logger.info(f"🎯 重複削除完了:")
    logger.info(f"  削除数: {removed_count}名")
    logger.info(f"  残存数: {len(unique_candidates)}名")
    
    # 統計を再計算
    party_stats = {}
    prefecture_stats = {}
    
    for candidate in unique_candidates:
        party = candidate.get('party', '無所属')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
    
    # データ更新
    data['data'] = unique_candidates
    data['metadata']['total_candidates'] = len(unique_candidates)
    data['metadata']['generated_at'] = datetime.now().isoformat()
    data['metadata']['data_type'] = "go2senkyo_deduplicated_sangiin_2025"
    data['metadata']['collection_method'] = "constituency_deduplicated"
    
    data['statistics'] = {
        "by_party": party_stats,
        "by_prefecture": prefecture_stats,
        "by_constituency_type": {"single_member": len(unique_candidates)}
    }
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    dedup_file = data_dir / f"go2senkyo_deduplicated_{timestamp}.json"
    
    with open(dedup_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 保存完了: {dedup_file}")
    
    # 最終統計表示
    show_final_statistics(unique_candidates)

def find_duplicates(candidates):
    """重複データを検索"""
    
    # candidate_idベースの重複チェック
    id_groups = defaultdict(list)
    # 名前ベースの重複チェック
    name_groups = defaultdict(list)
    
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', '')
        name = candidate.get('name', '')
        
        if candidate_id:
            id_groups[candidate_id].append(candidate)
        
        if name:
            name_groups[name].append(candidate)
    
    duplicates = {}
    
    # candidate_idで重複しているもの
    for candidate_id, entries in id_groups.items():
        if len(entries) > 1:
            duplicates[f"ID重複: {candidate_id}"] = entries
    
    # 名前で重複しているもの（candidate_idが異なる場合）
    for name, entries in name_groups.items():
        if len(entries) > 1:
            # candidate_idが全て異なる場合のみ報告
            ids = [entry.get('candidate_id') for entry in entries]
            if len(set(ids)) == len(ids):  # 全てのIDが異なる
                duplicates[f"名前重複: {name}"] = entries
    
    return duplicates

def deduplicate_candidates(candidates):
    """重複候補者を削除"""
    
    seen_ids = set()
    seen_names = set()
    unique_candidates = []
    
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', '')
        name = candidate.get('name', '')
        prefecture = candidate.get('prefecture', '')
        
        # 優先度判定のためのキー
        priority_key = (candidate_id, name)
        
        # candidate_idベースの重複チェック
        if candidate_id and candidate_id in seen_ids:
            logger.debug(f"ID重複スキップ: {name} ({candidate_id}) - {prefecture}")
            continue
        
        # 名前と都道府県の組み合わせで重複チェック
        name_pref_key = (name, prefecture)
        if name and name_pref_key in seen_names:
            logger.debug(f"名前+都道府県重複スキップ: {name} - {prefecture}")
            continue
        
        # 重複していない場合は追加
        unique_candidates.append(candidate)
        
        if candidate_id:
            seen_ids.add(candidate_id)
        if name:
            seen_names.add(name_pref_key)
    
    return unique_candidates

def show_final_statistics(candidates):
    """最終統計を表示"""
    
    party_count = defaultdict(int)
    prefecture_count = defaultdict(int)
    
    for candidate in candidates:
        party = candidate.get('party', '無所属')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_count[party] += 1
        prefecture_count[prefecture] += 1
    
    logger.info("📊 最終統計:")
    logger.info(f"  総候補者数: {len(candidates)}名")
    logger.info(f"  政党数: {len(party_count)}政党")
    logger.info(f"  都道府県数: {len(prefecture_count)}都道府県")
    
    logger.info("🏛️ 政党別統計（上位10）:")
    top_parties = sorted(party_count.items(), key=lambda x: x[1], reverse=True)[:10]
    for party, count in top_parties:
        logger.info(f"  {party}: {count}名")
    
    logger.info("🗾 都道府県別統計（上位10）:")
    top_prefectures = sorted(prefecture_count.items(), key=lambda x: x[1], reverse=True)[:10]
    for prefecture, count in top_prefectures:
        logger.info(f"  {prefecture}: {count}名")

if __name__ == "__main__":
    remove_duplicates()