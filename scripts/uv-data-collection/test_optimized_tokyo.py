#!/usr/bin/env python3
"""
Go2senkyo 最適化スクリプト 東京都テスト
"""

import json
import logging
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_tokyo_only():
    """東京都のみテスト"""
    logger.info("🧪 東京都最適化テスト開始...")
    
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # 東京都のみ処理
        candidates = collector.collect_prefecture_data("東京都", 13)
        
        logger.info(f"✅ 東京都テスト結果: {len(candidates)}名")
        
        # 最初の候補者の詳細表示
        if candidates:
            first_candidate = candidates[0]
            logger.info("📋 サンプル候補者:")
            logger.info(f"  名前: {first_candidate.get('name', 'N/A')}")
            logger.info(f"  政党: {first_candidate.get('party', 'N/A')}")
            logger.info(f"  プロフィールURL: {first_candidate.get('profile_url', 'N/A')}")
        
        return candidates
        
    except Exception as e:
        logger.error(f"❌ 東京都テストエラー: {e}")
        raise

if __name__ == "__main__":
    test_tokyo_only()