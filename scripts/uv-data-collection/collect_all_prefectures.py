#!/usr/bin/env python3
"""
全都道府県データ収集スクリプト
"""

import logging
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_all_prefectures():
    """全都道府県データ収集"""
    logger.info("🚀 全都道府県データ収集開始...")
    
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # 全都道府県収集
        all_candidates = collector.collect_priority_prefectures()
        
        if all_candidates:
            logger.info(f"✅ 全都道府県収集完了: {len(all_candidates)}名")
            
            # データ保存
            collector.save_optimized_data(all_candidates)
            
            # 統計表示
            prefectures = {}
            parties = {}
            
            for candidate in all_candidates:
                pref = candidate.get('prefecture', '未分類')
                party = candidate.get('party', '無所属')
                
                prefectures[pref] = prefectures.get(pref, 0) + 1
                parties[party] = parties.get(party, 0) + 1
            
            logger.info("📊 都道府県別統計:")
            for pref, count in sorted(prefectures.items()):
                logger.info(f"  {pref}: {count}名")
            
            logger.info("🏛️ 政党別統計 (上位10):")
            top_parties = sorted(parties.items(), key=lambda x: x[1], reverse=True)[:10]
            for party, count in top_parties:
                logger.info(f"  {party}: {count}名")
        
        else:
            logger.error("❌ データ収集に失敗しました")
        
        return all_candidates
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    collect_all_prefectures()