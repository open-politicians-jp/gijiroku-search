#!/usr/bin/env python3
"""
比例代表データ収集
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from collect_go2senkyo_optimized import Go2senkyoOptimizedCollector

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def collect_proportional():
    """比例代表データ収集"""
    logger.info("🚀 比例代表データ収集開始...")
    
    collector = Go2senkyoOptimizedCollector()
    all_proportional_candidates = []
    
    # 比例代表政党リスト（発見されたもの）
    proportional_parties = {
        "全政党": "all",
        "自由民主党": "4",
        "立憲民主党": "616", 
        "公明党": "3",
        "日本維新の会": "19",
        "日本共産党": "2",
        "国民民主党": "617",
        "れいわ新選組": "618",
        "参政党": "619",
        "社会民主党": "1",
        "NHK党": "620"
    }
    
    try:
        # 各政党の比例代表候補者を収集
        for party_name, party_id in proportional_parties.items():
            try:
                logger.info(f"📍 {party_name} 比例代表収集中...")
                
                if party_id == "all":
                    # 全政党ページ
                    url = f"{collector.base_url}/2025/hirei/all"
                else:
                    # 政党別ページ
                    url = f"{collector.base_url}/2025/hirei/{party_id}"
                
                collector.random_delay(1, 2)
                response = collector.session.get(url, timeout=30)
                
                if response.status_code != 200:
                    logger.warning(f"{party_name}: HTTP {response.status_code}")
                    continue
                
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 比例代表候補者ブロック取得
                candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
                
                if not candidate_blocks:
                    # 別のセレクターも試す
                    candidate_blocks = soup.find_all(['div', 'li'], class_=re.compile(r'candidate|person|member'))
                
                logger.info(f"{party_name}: {len(candidate_blocks)}個ブロック発見")
                
                party_candidates = []
                for i, block in enumerate(candidate_blocks):
                    try:
                        # 基本情報抽出（都道府県の代わりに比例代表）
                        candidate_info = extract_proportional_candidate(block, party_name, url, i, collector)
                        if candidate_info:
                            party_candidates.append(candidate_info)
                    except Exception as e:
                        logger.debug(f"{party_name} ブロック{i}エラー: {e}")
                        continue
                
                all_proportional_candidates.extend(party_candidates)
                logger.info(f"✅ {party_name}: {len(party_candidates)}名")
                
                if party_candidates:
                    sample = party_candidates[0]
                    logger.info(f"  サンプル: {sample.get('name')} ({sample.get('party')})")
                
                # 全政党ページから十分なデータが取れた場合、他をスキップ
                if party_id == "all" and len(party_candidates) > 50:
                    logger.info("全政党ページから十分なデータを取得、個別政党をスキップ")
                    break
                
            except Exception as e:
                logger.error(f"❌ {party_name}エラー: {e}")
                continue
        
        logger.info(f"🎯 比例代表収集完了: {len(all_proportional_candidates)}名")
        
        return all_proportional_candidates
        
    except Exception as e:
        logger.error(f"❌ 比例代表収集エラー: {e}")
        raise

def extract_proportional_candidate(block, party_name, page_url, idx, collector):
    """比例代表候補者情報抽出"""
    try:
        # 名前抽出
        name_elem = block.find(class_='p_senkyoku_list_block_text_name')
        if not name_elem:
            # 他のセレクターも試す
            name_elem = block.find(['h2', 'h3', 'h4'], string=re.compile(r'[一-龯ァ-ヶ]+'))
        
        if name_elem:
            full_name = name_elem.get_text(strip=True)
        else:
            # ブロック全体から名前らしきものを探す
            import re
            text = block.get_text()
            name_match = re.search(r'([一-龯]{2,4}[\\s　]*[一-龯]{2,8}[ァ-ヶ]*)', text)
            if name_match:
                full_name = name_match.group(1).strip()
            else:
                return None
        
        # 名前とカタカナを分離
        name, name_kana = collector.separate_name_and_kana(full_name)
        
        # 政党抽出（ページから推測または要素から抽出）
        party_elem = block.find(class_='p_senkyoku_list_block_text_party')
        if party_elem:
            party = party_elem.get_text(strip=True)
        else:
            # ページの政党名を使用
            party = party_name if party_name != "全政党" else "未分類"
        
        # プロフィールリンク抽出
        profile_link = block.find('a', href=re.compile(r'/seijika/\\d+'))
        profile_url = ""
        candidate_id = f"hirei_{party_name}_{idx}"
        
        if profile_link:
            href = profile_link.get('href', '')
            if href.startswith('/'):
                profile_url = f"https://go2senkyo.com{href}"
            else:
                profile_url = href
            
            # 候補者ID抽出
            import re
            match = re.search(r'/seijika/(\\d+)', href)
            if match:
                candidate_id = f"hirei_{match.group(1)}"
        
        candidate_data = {
            "candidate_id": candidate_id,
            "name": name,
            "prefecture": "比例代表",
            "constituency": "全国比例",
            "constituency_type": "proportional",
            "party": party,
            "party_normalized": collector.normalize_party_name(party),
            "profile_url": profile_url,
            "source_page": page_url,
            "source": "go2senkyo_proportional",
            "collected_at": datetime.now().isoformat()
        }
        
        # カタカナ名前が存在する場合のみ追加
        if name_kana:
            candidate_data["name_kana"] = name_kana
        
        return candidate_data
        
    except Exception as e:
        logger.debug(f"比例代表候補者抽出エラー: {e}")
        return None

def merge_with_constituency_data():
    """選挙区データと比例代表データを統合"""
    logger.info("🔗 選挙区データと比例代表データを統合...")
    
    try:
        # 比例代表データ収集
        proportional_candidates = collect_proportional()
        
        # 既存の選挙区データ読み込み
        data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
        latest_file = data_dir / "go2senkyo_optimized_latest.json"
        
        if latest_file.exists():
            with open(latest_file, 'r', encoding='utf-8') as f:
                constituency_data = json.load(f)
                constituency_candidates = constituency_data.get('data', [])
        else:
            constituency_candidates = []
        
        # データ統合
        all_candidates = constituency_candidates + proportional_candidates
        
        logger.info(f"📊 統合結果:")
        logger.info(f"  選挙区候補者: {len(constituency_candidates)}名")
        logger.info(f"  比例代表候補者: {len(proportional_candidates)}名")
        logger.info(f"  総候補者数: {len(all_candidates)}名")
        
        # 統合データ保存
        save_merged_data(all_candidates, data_dir)
        
        return all_candidates
        
    except Exception as e:
        logger.error(f"❌ データ統合エラー: {e}")
        raise

def save_merged_data(candidates, output_dir):
    """統合データの保存"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    main_file = output_dir / f"go2senkyo_merged_{timestamp}.json"
    latest_file = output_dir / "go2senkyo_optimized_latest.json"
    
    # 統計計算
    party_stats = {}
    constituency_stats = {}
    
    for candidate in candidates:
        party = candidate.get('party', '無所属')
        constituency_type = candidate.get('constituency_type', 'unknown')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        constituency_stats[constituency_type] = constituency_stats.get(constituency_type, 0) + 1
    
    save_data = {
        "metadata": {
            "data_type": "go2senkyo_merged_sangiin_2025",
            "collection_method": "constituency_and_proportional_scraping",
            "total_candidates": len(candidates),
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "coverage": {
                "constituency_types": len(constituency_stats),
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
            "by_constituency_type": constituency_stats
        },
        "data": candidates
    }
    
    # ファイル保存
    with open(main_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    with open(latest_file, 'w', encoding='utf-8') as f:
        json.dump(save_data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 統合データ保存完了: {main_file}")

if __name__ == "__main__":
    merge_with_constituency_data()