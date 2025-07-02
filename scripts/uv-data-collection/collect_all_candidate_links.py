#!/usr/bin/env python3
"""
全候補者の関連リンク収集
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collect_candidate_links_fixed import get_candidate_links_fixed
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_all_candidate_links():
    """全候補者の関連リンクを収集"""
    logger.info("🔗 全候補者関連リンク収集開始...")
    
    # データ読み込み
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    if not latest_file.exists():
        logger.error("最新データファイルが見つかりません")
        return
    
    with open(latest_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    candidates = data.get('data', [])
    logger.info(f"📊 対象候補者: {len(candidates)}名")
    
    collector = Go2senkyoOptimizedCollector()
    updated_candidates = []
    success_count = 0
    
    for i, candidate in enumerate(candidates):
        try:
            profile_url = candidate.get('profile_url', '')
            name = candidate.get('name', '')
            
            if (i + 1) % 10 == 0 or i < 5:
                logger.info(f"📍 {i+1}/{len(candidates)}: {name}")
            
            if not profile_url:
                updated_candidates.append(candidate)
                continue
            
            # 関連リンク取得
            links_info = get_candidate_links_fixed(profile_url, collector)
            
            if links_info:
                # 既存データに関連リンク情報を追加
                candidate.update(links_info)
                success_count += 1
                
                if (i + 1) % 10 == 0 or i < 5:
                    websites_count = len(links_info.get('websites', []))
                    logger.info(f"  ✅ リンク取得成功: {websites_count}個")
            
            updated_candidates.append(candidate)
            
            # 進捗表示
            if (i + 1) % 20 == 0:
                logger.info(f"📈 進捗: {i+1}/{len(candidates)} ({(i+1)/len(candidates)*100:.1f}%) - 成功率: {success_count/(i+1)*100:.1f}%")
            
            # レート制限
            collector.random_delay(0.5, 1.0)
            
        except Exception as e:
            logger.error(f"❌ {name}エラー: {e}")
            updated_candidates.append(candidate)
            continue
    
    # データ更新
    data['data'] = updated_candidates
    data['metadata']['collection_stats']['with_websites'] = success_count
    data['metadata']['quality_metrics']['website_coverage'] = f"{success_count/len(candidates)*100:.1f}%"
    data['metadata']['generated_at'] = datetime.now().isoformat()
    data['metadata']['data_type'] = "go2senkyo_enhanced_sangiin_2025"
    data['metadata']['collection_method'] = "constituency_with_enhanced_links"
    
    # ファイル保存
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    enhanced_file = data_dir / f"go2senkyo_enhanced_{timestamp}.json"
    
    with open(enhanced_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"🎯 関連リンク収集完了:")
    logger.info(f"  成功: {success_count}/{len(candidates)}名 ({success_count/len(candidates)*100:.1f}%)")
    logger.info(f"📁 保存: {enhanced_file}")
    
    # 統計表示
    show_links_statistics(updated_candidates)

def show_links_statistics(candidates):
    """関連リンクの統計を表示"""
    
    site_types = {}
    age_available = 0
    
    for candidate in candidates:
        websites = candidate.get('websites', [])
        
        for site in websites:
            site_type = site['title']
            site_types[site_type] = site_types.get(site_type, 0) + 1
        
        if candidate.get('age_info'):
            age_available += 1
    
    logger.info("📊 関連サイト統計:")
    for site_type, count in sorted(site_types.items(), key=lambda x: x[1], reverse=True):
        logger.info(f"  {site_type}: {count}名")
    
    logger.info(f"📅 年齢情報: {age_available}名 ({age_available/len(candidates)*100:.1f}%)")

if __name__ == "__main__":
    collect_all_candidate_links()