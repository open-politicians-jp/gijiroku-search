#!/usr/bin/env python3
"""
東京都データ収集・保存テスト
"""

import json
import logging
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_and_save_tokyo():
    """東京都データ収集・保存"""
    logger.info("🚀 東京都データ収集・保存開始...")
    
    collector = Go2senkyoOptimizedCollector()
    
    try:
        # 東京都のみ収集
        candidates = collector.collect_prefecture_data("東京都", 13)
        
        logger.info(f"✅ 東京都収集完了: {len(candidates)}名")
        
        # データ保存
        if candidates:
            collector.save_optimized_data(candidates)
            
            # サンプルデータ表示
            logger.info("📋 収集されたデータサンプル:")
            for i, candidate in enumerate(candidates[:5]):
                logger.info(f"  {i+1}. {candidate.get('name')} ({candidate.get('party')})")
                if candidate.get('career'):
                    logger.info(f"      経歴: {candidate.get('career', '')[:100]}...")
                if candidate.get('manifesto_summary'):
                    logger.info(f"      政策: {candidate.get('manifesto_summary', '')[:100]}...")
                if candidate.get('sns_accounts'):
                    logger.info(f"      SNS: {len(candidate.get('sns_accounts', {}))}アカウント")
                logger.info("")
        
        return candidates
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    collect_and_save_tokyo()