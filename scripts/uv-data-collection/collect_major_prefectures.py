#!/usr/bin/env python3
"""
主要都道府県データ収集（高速版）
"""

import logging
import json
from datetime import datetime
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_major_prefectures():
    """主要都道府県データ収集"""
    logger.info("🚀 主要都道府県データ収集開始...")
    
    # 主要都道府県（人口順・注目度順）
    major_prefectures = {
        "東京都": 13, "大阪府": 27, "神奈川県": 14, "愛知県": 23,
        "埼玉県": 11, "千葉県": 12, "兵庫県": 28, "福岡県": 40,
        "北海道": 1, "静岡県": 22, "茨城県": 8, "京都府": 26,
        "広島県": 34, "宮城県": 4, "新潟県": 15, "長野県": 20
    }
    
    collector = Go2senkyoOptimizedCollector()
    all_candidates = []
    
    try:
        for prefecture, code in major_prefectures.items():
            try:
                logger.info(f"📍 {prefecture} 収集中...")
                candidates = collector.collect_prefecture_data(prefecture, code)
                
                if candidates:
                    all_candidates.extend(candidates)
                    logger.info(f"✅ {prefecture}: {len(candidates)}名")
                    
                    # 名前分離テスト
                    sample_names = [c.get('name', '') for c in candidates[:3]]
                    logger.info(f"  サンプル: {', '.join(sample_names)}")
                else:
                    logger.warning(f"⚠️ {prefecture}: データなし")
                
                # 次の都道府県まで短い間隔
                collector.random_delay(1, 2)
                
            except Exception as e:
                logger.error(f"❌ {prefecture}エラー: {e}")
                continue
        
        logger.info(f"🎯 主要都道府県収集完了: {len(all_candidates)}名")
        
        # データ保存
        if all_candidates:
            collector.save_optimized_data(all_candidates)
            
            # 統計表示
            prefectures = {}
            parties = {}
            name_kana_count = 0
            
            for candidate in all_candidates:
                pref = candidate.get('prefecture', '未分類')
                party = candidate.get('party', '無所属')
                
                prefectures[pref] = prefectures.get(pref, 0) + 1
                parties[party] = parties.get(party, 0) + 1
                
                if candidate.get('name_kana'):
                    name_kana_count += 1
            
            logger.info("📊 都道府県別統計:")
            for pref, count in sorted(prefectures.items()):
                logger.info(f"  {pref}: {count}名")
            
            logger.info("🏛️ 政党別統計 (上位10):")
            top_parties = sorted(parties.items(), key=lambda x: x[1], reverse=True)[:10]
            for party, count in top_parties:
                logger.info(f"  {party}: {count}名")
            
            logger.info(f"📝 カタカナ読み付き: {name_kana_count}名 ({name_kana_count/len(all_candidates)*100:.1f}%)")
        
        return all_candidates
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    collect_major_prefectures()