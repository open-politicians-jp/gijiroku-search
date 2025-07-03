#!/usr/bin/env python3
"""
最終データクリーニング - 無効データの完全除去
"""

import json
import logging
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def clean_candidate_data():
    """候補者データから無効なエントリを完全に除去"""
    logger.info("🧹 候補者データクリーニング開始...")
    
    # データディレクトリ
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    
    # 既存の選挙区データのみを読み込み（比例代表は除外）
    for file_path in data_dir.glob("go2senkyo_*.json"):
        if "latest" in file_path.name:
            continue
        
        logger.info(f"📂 処理中: {file_path.name}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_count = len(data.get('data', []))
        logger.info(f"  元データ: {original_count}名")
        
        # 無効なデータをフィルタリング
        valid_candidates = []
        invalid_names = [
            '会員登録', '比例代表予想', 'ログイン', 'サインアップ', 
            'MY選挙', '選挙区', 'この', 'コンテンツ', '予想される顔ぶれ',
            'について', 'シェア', 'ページ', '政党', '全政党',
            '自由民主党', '立憲民主党', '公明党', '日本維新の会', '日本共産党',
            '国民民主党', 'れいわ新選組', '参政党', '社会民主党', 
            '日本保守党', 'みんなでつくる党', 'NHK党', 'チームみらい',
            '再生の道', '日本改革党', '無所属連合', '日本誠真会',
            '比例代表', '全国比例', '代表者', '百田尚樹', '石濱哲信',
            'このページ', 'をシェア', 'する', 'このコンテンツ'
        ]
        
        for candidate in data.get('data', []):
            name = candidate.get('name', '')
            
            # 基本的なバリデーション
            if len(name) < 2 or len(name) > 10:
                logger.debug(f"  除外(長さ): {name}")
                continue
            
            # 無効名のチェック
            if any(invalid in name for invalid in invalid_names):
                logger.debug(f"  除外(無効名): {name}")
                continue
            
            # 漢字が含まれているかチェック
            if not any(ord(char) >= 0x4e00 and ord(char) <= 0x9fff for char in name):
                logger.debug(f"  除外(漢字なし): {name}")
                continue
            
            # 選挙区候補者のみ（比例代表を除外）
            if candidate.get('constituency_type') == 'proportional':
                logger.debug(f"  除外(比例代表): {name}")
                continue
            
            # 都道府県が正常かチェック
            prefecture = candidate.get('prefecture', '')
            if not prefecture or prefecture in ['比例代表', '全国比例']:
                logger.debug(f"  除外(都道府県無効): {name} - {prefecture}")
                continue
            
            valid_candidates.append(candidate)
        
        logger.info(f"  有効データ: {len(valid_candidates)}名")
        logger.info(f"  除去数: {original_count - len(valid_candidates)}名")
        
        # 統計を再計算
        party_stats = {}
        prefecture_stats = {}
        
        for candidate in valid_candidates:
            party = candidate.get('party', '無所属')
            prefecture = candidate.get('prefecture', '未分類')
            
            party_stats[party] = party_stats.get(party, 0) + 1
            prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
        
        # データ更新
        data['data'] = valid_candidates
        data['metadata']['total_candidates'] = len(valid_candidates)
        data['metadata']['data_type'] = "go2senkyo_clean_sangiin_2025"
        data['metadata']['collection_method'] = "constituency_only_cleaned"
        data['metadata']['generated_at'] = datetime.now().isoformat()
        
        data['statistics'] = {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_constituency_type": {"single_member": len(valid_candidates)}
        }
        
        # ファイルを更新
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ 更新完了: {file_path.name}")
    
    # 最新ファイルも更新
    clean_latest_file(data_dir, valid_candidates, party_stats, prefecture_stats)

def clean_latest_file(data_dir, valid_candidates, party_stats, prefecture_stats):
    """最新ファイルをクリーンなデータで更新"""
    
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    clean_data = {
        "metadata": {
            "data_type": "go2senkyo_clean_sangiin_2025",
            "collection_method": "constituency_only_cleaned",
            "total_candidates": len(valid_candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "coverage": {
                "constituency_types": 1,
                "parties": len(party_stats),
                "prefectures": len(prefecture_stats)
            },
            "collection_stats": {
                "total_candidates": len(valid_candidates),
                "detailed_profiles": 0,
                "with_photos": 0,
                "with_policies": 0,
                "errors": 0
            },
            "quality_metrics": {
                "detail_coverage": "0%",
                "photo_coverage": "0%",
                "policy_coverage": "0%"
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_constituency_type": {"single_member": len(valid_candidates)}
        },
        "data": valid_candidates
    }
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(clean_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 最新ファイル更新: {latest_file}")
    logger.info(f"🎯 最終結果:")
    logger.info(f"  総候補者数: {len(valid_candidates)}名")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    # 統計表示
    logger.info("📊 政党別統計（上位10）:")
    top_parties = sorted(party_stats.items(), key=lambda x: x[1], reverse=True)[:10]
    for party, count in top_parties:
        logger.info(f"  {party}: {count}名")

if __name__ == "__main__":
    clean_candidate_data()