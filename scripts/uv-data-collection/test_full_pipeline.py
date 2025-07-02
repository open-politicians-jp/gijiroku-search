#!/usr/bin/env python3
"""
フルパイプラインテスト
"""

import logging
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_full_pipeline():
    """フルパイプラインテスト（東京のみ）"""
    logger.info("🧪 フルパイプラインテスト（東京のみ）...")
    
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # collect_prefecture_dataメソッドを直接呼ぶ
        logger.info("📍 collect_prefecture_dataを実行...")
        candidates = collector.collect_prefecture_data("東京都", 13)
        
        logger.info(f"🎯 collect_prefecture_data結果: {len(candidates)}名")
        
        if candidates:
            logger.info("✅ 成功！サンプル候補者:")
            for i, candidate in enumerate(candidates[:3]):
                logger.info(f"  {i+1}: {candidate.get('name')} ({candidate.get('party')})")
                logger.info(f"      プロフィール: {candidate.get('profile_url', 'N/A')}")
        else:
            logger.error("❌ 候補者データが空です")
        
        return candidates
        
    except Exception as e:
        logger.error(f"❌ パイプラインテストエラー: {e}")
        raise

if __name__ == "__main__":
    test_full_pipeline()