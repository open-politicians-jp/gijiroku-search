#!/usr/bin/env python3
"""
主要都道府県高速収集（基本情報のみ）
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def quick_collect():
    """高速収集（詳細プロフィールなし）"""
    logger.info("🚀 主要都道府県高速収集開始...")
    
    # 主要都道府県
    prefectures = {
        "東京都": 13, "大阪府": 27, "神奈川県": 14, "愛知県": 23,
        "埼玉県": 11, "千葉県": 12, "兵庫県": 28, "福岡県": 40,
        "北海道": 1, "静岡県": 22, "広島県": 34, "京都府": 26
    }
    
    collector = Go2senkyoOptimizedCollector()
    all_candidates = []
    
    try:
        for prefecture, code in prefectures.items():
            try:
                logger.info(f"📍 {prefecture} 収集中...")
                
                # 基本情報のみ収集（詳細プロフィールスキップ）
                url = f"{collector.base_url}/2025/prefecture/{code}"
                collector.random_delay(1, 2)
                
                response = collector.session.get(url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"{prefecture}: HTTP {response.status_code}")
                    continue
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 基本候補者情報のみ抽出
                candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
                logger.info(f"{prefecture}: {len(candidate_blocks)}個ブロック発見")
                
                prefecture_candidates = []
                for i, block in enumerate(candidate_blocks):
                    try:
                        candidate_info = collector.extract_candidate_from_block(block, prefecture, url, i)
                        if candidate_info:
                            # 詳細プロフィール収集をスキップして基本情報のみ
                            prefecture_candidates.append(candidate_info)
                    except Exception as e:
                        logger.debug(f"ブロック{i}エラー: {e}")
                        continue
                
                all_candidates.extend(prefecture_candidates)
                logger.info(f"✅ {prefecture}: {len(prefecture_candidates)}名")
                
                # サンプル表示
                if prefecture_candidates:
                    sample = prefecture_candidates[0]
                    logger.info(f"  サンプル: {sample.get('name')} ({sample.get('party')})")
                
            except Exception as e:
                logger.error(f"❌ {prefecture}エラー: {e}")
                continue
        
        logger.info(f"🎯 収集完了: {len(all_candidates)}名")
        
        # データ保存
        if all_candidates:
            # 手動で保存データを作成
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            output_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
            main_file = output_dir / f"go2senkyo_quick_{timestamp}.json"
            latest_file = output_dir / "go2senkyo_optimized_latest.json"
            
            # 統計計算
            party_stats = {}
            pref_stats = {}
            
            for candidate in all_candidates:
                party = candidate.get('party', '無所属')
                prefecture = candidate.get('prefecture', '未分類')
                
                party_stats[party] = party_stats.get(party, 0) + 1
                pref_stats[prefecture] = pref_stats.get(prefecture, 0) + 1
            
            save_data = {
                "metadata": {
                    "data_type": "go2senkyo_quick_sangiin_2025",
                    "collection_method": "quick_basic_scraping",
                    "total_candidates": len(all_candidates),
                    "generated_at": datetime.now().isoformat(),
                    "source_site": "sangiin.go2senkyo.com",
                    "collection_stats": {
                        "total_candidates": len(all_candidates),
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
                    "by_prefecture": pref_stats
                },
                "data": all_candidates
            }
            
            # ファイル保存
            with open(main_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📁 データ保存完了: {main_file}")
            logger.info(f"📊 統計:")
            logger.info(f"  総候補者数: {len(all_candidates)}名")
            logger.info(f"  都道府県数: {len(pref_stats)}")
            logger.info(f"  政党数: {len(party_stats)}")
            
            # 上位政党表示
            top_parties = sorted(party_stats.items(), key=lambda x: x[1], reverse=True)[:5]
            logger.info("  主要政党:")
            for party, count in top_parties:
                logger.info(f"    {party}: {count}名")
        
        return all_candidates
        
    except Exception as e:
        logger.error(f"❌ エラー: {e}")
        raise

if __name__ == "__main__":
    quick_collect()