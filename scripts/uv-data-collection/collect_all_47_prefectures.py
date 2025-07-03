#!/usr/bin/env python3
"""
全47都道府県 + 比例代表データ収集
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_all_japan():
    """全日本のデータ収集（47都道府県 + 比例代表）"""
    logger.info("🚀 全47都道府県 + 比例代表データ収集開始...")
    
    # 全都道府県（Go2senkyoのコード順）
    all_prefectures = {
        "北海道": 1, "青森県": 2, "岩手県": 3, "宮城県": 4, "秋田県": 5,
        "山形県": 6, "福島県": 7, "茨城県": 8, "栃木県": 9, "群馬県": 10,
        "埼玉県": 11, "千葉県": 12, "東京都": 13, "神奈川県": 14, "新潟県": 15,
        "富山県": 16, "石川県": 17, "福井県": 18, "山梨県": 19, "長野県": 20,
        "岐阜県": 21, "静岡県": 22, "愛知県": 23, "三重県": 24, "滋賀県": 25,
        "京都府": 26, "大阪府": 27, "兵庫県": 28, "奈良県": 29, "和歌山県": 30,
        "鳥取県": 31, "島根県": 32, "岡山県": 33, "広島県": 34, "山口県": 35,
        "徳島県": 36, "香川県": 37, "愛媛県": 38, "高知県": 39, "福岡県": 40,
        "佐賀県": 41, "長崎県": 42, "熊本県": 43, "大分県": 44, "宮崎県": 45,
        "鹿児島県": 46, "沖縄県": 47
    }
    
    collector = Go2senkyoOptimizedCollector()
    all_candidates = []
    success_count = 0
    error_count = 0
    
    try:
        # 各都道府県を順次処理
        for prefecture, code in all_prefectures.items():
            try:
                logger.info(f"📍 {prefecture} (コード: {code}) 収集中...")
                
                # 基本情報収集（詳細プロフィールなし）
                url = f"{collector.base_url}/2025/prefecture/{code}"
                collector.random_delay(0.5, 1.5)  # 短い間隔
                
                response = collector.session.get(url, timeout=30)
                if response.status_code != 200:
                    logger.warning(f"{prefecture}: HTTP {response.status_code}")
                    error_count += 1
                    continue
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 候補者ブロック取得
                candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
                
                if not candidate_blocks:
                    logger.warning(f"{prefecture}: 候補者ブロックが見つかりません")
                    error_count += 1
                    continue
                
                prefecture_candidates = []
                for i, block in enumerate(candidate_blocks):
                    try:
                        candidate_info = collector.extract_candidate_from_block(block, prefecture, url, i)
                        if candidate_info:
                            prefecture_candidates.append(candidate_info)
                    except Exception as e:
                        logger.debug(f"{prefecture} ブロック{i}エラー: {e}")
                        continue
                
                all_candidates.extend(prefecture_candidates)
                success_count += 1
                
                logger.info(f"✅ {prefecture}: {len(prefecture_candidates)}名")
                
                # 進捗表示
                progress = success_count + error_count
                logger.info(f"進捗: {progress}/47 ({progress/47*100:.1f}%)")
                
            except Exception as e:
                logger.error(f"❌ {prefecture}エラー: {e}")
                error_count += 1
                continue
        
        # 比例代表も収集（URL確認が必要）
        logger.info("📍 比例代表データ収集を試行...")
        try:
            # 比例代表のURL（推測）
            proportional_urls = [
                f"{collector.base_url}/2025/seitou",  # 政党ページ
                f"{collector.base_url}/2025/hirei",   # 比例代表ページ（推測）
            ]
            
            for i, prop_url in enumerate(proportional_urls):
                try:
                    response = collector.session.get(prop_url, timeout=30)
                    if response.status_code == 200:
                        logger.info(f"✅ 比例代表ページ発見: {prop_url}")
                        # 比例代表データの処理は今後実装
                        break
                except:
                    continue
        except Exception as e:
            logger.debug(f"比例代表収集エラー: {e}")
        
        logger.info(f"🎯 全都道府県収集完了:")
        logger.info(f"  成功: {success_count}都道府県")
        logger.info(f"  失敗: {error_count}都道府県")
        logger.info(f"  総候補者数: {len(all_candidates)}名")
        
        # データ保存
        if all_candidates:
            save_complete_data(all_candidates, collector.output_dir)
            
            # 統計表示
            show_statistics(all_candidates)
        
        return all_candidates
        
    except Exception as e:
        logger.error(f"❌ 全体エラー: {e}")
        raise

def save_complete_data(candidates, output_dir):
    """完全データの保存"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    main_file = output_dir / f"go2senkyo_complete_{timestamp}.json"
    latest_file = output_dir / "go2senkyo_optimized_latest.json"
    
    # 統計計算
    party_stats = {}
    pref_stats = {}
    
    for candidate in candidates:
        party = candidate.get('party', '無所属')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        pref_stats[prefecture] = pref_stats.get(prefecture, 0) + 1
    
    save_data = {
        "metadata": {
            "data_type": "go2senkyo_complete_sangiin_2025",
            "collection_method": "complete_47_prefectures_scraping",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "coverage": {
                "prefectures": len(pref_stats),
                "parties": len(party_stats)
            },
            "collection_stats": {
                "total_candidates": len(candidates),
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
        "data": candidates
    }
    
    # ファイル保存
    with open(main_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 完全データ保存完了: {main_file}")

def show_statistics(candidates):
    """統計表示"""
    prefectures = {}
    parties = {}
    
    for candidate in candidates:
        pref = candidate.get('prefecture', '未分類')
        party = candidate.get('party', '無所属')
        
        prefectures[pref] = prefectures.get(pref, 0) + 1
        parties[party] = parties.get(party, 0) + 1
    
    logger.info("📊 都道府県別統計（上位20）:")
    top_prefs = sorted(prefectures.items(), key=lambda x: x[1], reverse=True)[:20]
    for pref, count in top_prefs:
        logger.info(f"  {pref}: {count}名")
    
    logger.info("🏛️ 政党別統計（上位15）:")
    top_parties = sorted(parties.items(), key=lambda x: x[1], reverse=True)[:15]
    for party, count in top_parties:
        logger.info(f"  {party}: {count}名")
    
    # 地域別統計
    regions = {
        "関東": ["東京都", "神奈川県", "埼玉県", "千葉県", "茨城県", "栃木県", "群馬県"],
        "関西": ["大阪府", "兵庫県", "京都府", "奈良県", "和歌山県", "滋賀県"],
        "中部": ["愛知県", "静岡県", "岐阜県", "三重県", "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県"],
        "九州": ["福岡県", "佐賀県", "長崎県", "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県"],
        "東北": ["青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県"],
        "中国": ["広島県", "岡山県", "鳥取県", "島根県", "山口県"],
        "四国": ["徳島県", "香川県", "愛媛県", "高知県"],
        "北海道": ["北海道"]
    }
    
    logger.info("🗾 地域別統計:")
    for region, prefs in regions.items():
        region_count = sum(prefectures.get(pref, 0) for pref in prefs)
        logger.info(f"  {region}: {region_count}名")

if __name__ == "__main__":
    collect_all_japan()