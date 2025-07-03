#!/usr/bin/env python3
"""
大阪府テスト収集
"""

import logging
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_osaka():
    """大阪府テスト"""
    logger.info("🧪 大阪府テスト開始...")
    
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # 大阪府のみ収集
        candidates = collector.collect_prefecture_data("大阪府", 27)
        
        logger.info(f"✅ 大阪府結果: {len(candidates)}名")
        
        if candidates:
            for i, candidate in enumerate(candidates[:3]):
                logger.info(f"  {i+1}. {candidate.get('name')} ({candidate.get('party')})")
                if candidate.get('name_kana'):
                    logger.info(f"      読み: {candidate.get('name_kana')}")
        
        return candidates
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    test_osaka()