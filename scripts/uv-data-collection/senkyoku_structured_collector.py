#!/usr/bin/env python3
"""
選挙区別構造化データ収集
Go2senkyo.comの正確なHTML構造を使用した遅延ロード対応版
"""

import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import time

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SenkyokuStructuredCollector:
    def __init__(self):
        self.session = requests.Session()
        ua = UserAgent()
        desktop_ua = ua.random
        
        self.session.headers.update({
            'User-Agent': desktop_ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache'
        })
        
        # 都道府県マッピング
        self.prefectures = {
            1: "北海道", 2: "青森県", 3: "岩手県", 4: "宮城県", 5: "秋田県", 6: "山形県", 7: "福島県",
            8: "茨城県", 9: "栃木県", 10: "群馬県", 11: "埼玉県", 12: "千葉県", 13: "東京都", 14: "神奈川県",
            15: "新潟県", 16: "富山県", 17: "石川県", 18: "福井県", 19: "山梨県", 20: "長野県", 21: "岐阜県",
            22: "静岡県", 23: "愛知県", 24: "三重県", 25: "滋賀県", 26: "京都府", 27: "大阪府", 28: "兵庫県",
            29: "奈良県", 30: "和歌山県", 31: "鳥取県", 32: "島根県", 33: "岡山県", 34: "広島県", 35: "山口県",
            36: "徳島県", 37: "香川県", 38: "愛媛県", 39: "高知県", 40: "福岡県", 41: "佐賀県", 42: "長崎県",
            43: "熊本県", 44: "大分県", 45: "宮崎県", 46: "鹿児島県", 47: "沖縄県"
        }
        
        # 政党マスターリスト
        self.parties = [
            "自由民主党", "立憲民主党", "日本維新の会", "公明党", "日本共産党",
            "国民民主党", "れいわ新選組", "参政党", "社会民主党", "NHK党",
            "日本保守党", "日本改革党", "無所属", "無所属連合", "日本誠真会",
            "日本の家庭を守る会", "再生の道", "差別撲滅党", "核融合党", "チームみらい",
            "多夫多妻党", "国政ガバナンスの会", "新党やまと", "未分類"
        ]

    def collect_prefecture_structured(self, pref_code: int):
        """構造化された都道府県データ収集"""
        pref_name = self.prefectures.get(pref_code, f"未知_{pref_code}")
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        
        logger.info(f"🔍 {pref_name} (コード: {pref_code}) 構造化収集開始")
        
        try:
            # 初回リクエスト
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.error(f"❌ {pref_name} ページアクセス失敗: HTTP {response.status_code}")
                return []
            
            logger.info(f"📊 {pref_name} 初回HTML取得: {len(response.text):,} 文字")
            
            # 遅延ロード対応 - 段階的な待機
            logger.info(f"⏳ {pref_name} 遅延ロードコンテンツ待機...")
            time.sleep(4)  # 長めの待機時間
            
            # 再リクエストでフルコンテンツ取得
            response2 = self.session.get(url, timeout=30)
            logger.info(f"📊 {pref_name} 再取得HTML: {len(response2.text):,} 文字")
            
            soup = BeautifulSoup(response2.text, 'html.parser')
            
            # 構造化抽出の実行
            candidates = self.extract_candidates_structured(soup, pref_name, url)
            
            logger.info(f"🎯 {pref_name} 構造化抽出完了: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ {pref_name} データ収集エラー: {e}")
            return []

    def extract_candidates_structured(self, soup: BeautifulSoup, prefecture: str, page_url: str):
        """構造化された候補者抽出"""
        candidates = []
        
        try:
            # 具体的なHTML構造に基づく抽出
            # <div class="p_senkyoku_list_block"> 内の候補者データ
            candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
            logger.info(f"📊 {prefecture} 候補者ブロック発見: {len(candidate_blocks)}個")
            
            for i, block in enumerate(candidate_blocks):
                try:
                    candidate = self.extract_candidate_from_structured_block(block, prefecture, page_url, i)
                    if candidate:
                        candidates.append(candidate)
                        logger.info(f"  ✅ {candidate['name']} ({candidate['name_kana']}) - {candidate['party']}")
                    
                except Exception as e:
                    logger.debug(f"ブロック {i} 抽出エラー: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"{prefecture} 構造化抽出エラー: {e}")
        
        return candidates

    def extract_candidate_from_structured_block(self, block, prefecture: str, page_url: str, index: int):
        """構造化ブロックから候補者情報抽出"""
        try:
            candidate = {
                "candidate_id": "",
                "name": "",
                "name_kana": "",
                "prefecture": prefecture,
                "constituency": prefecture.replace('県', '').replace('府', '').replace('都', '').replace('道', ''),
                "constituency_type": "single_member",
                "party": "未分類",
                "party_normalized": "未分類",
                "profile_url": "",
                "source_page": page_url,
                "source": "structured_extraction",
                "collected_at": datetime.now().isoformat()
            }
            
            # 1. 名前と読みの抽出
            name_info = self.extract_name_and_kana_structured(block)
            if name_info:
                candidate["name"] = name_info["name"]
                candidate["name_kana"] = name_info["kana"]
            
            # 2. 政党の抽出
            party = self.extract_party_from_block(block)
            if party:
                candidate["party"] = party
                candidate["party_normalized"] = party
            
            # 3. プロフィールURLの抽出
            profile_url = self.extract_profile_url_from_block(block)
            if profile_url:
                candidate["profile_url"] = profile_url
                # candidate_idをURLから抽出
                match = re.search(r'/seijika/(\d+)', profile_url)
                if match:
                    candidate["candidate_id"] = f"go2s_{match.group(1)}"
            
            # 名前が取得できない場合はスキップ
            if not candidate["name"]:
                logger.debug(f"名前取得失敗: ブロック {index}")
                return None
            
            return candidate
            
        except Exception as e:
            logger.debug(f"構造化ブロック抽出エラー: {e}")
            return None

    def extract_name_and_kana_structured(self, block):
        """構造化された名前・読み抽出"""
        try:
            # Go2senkyo.com特有の構造:
            # <div class="p_senkyoku_list_block_text_name bold ">
            #   <p class="text"><span>牧</span><span>山</span>...</p>
            #   <p class="kana "><span>マ</span><span>キ</span>...</p>
            
            name_container = block.find('div', class_='p_senkyoku_list_block_text_name')
            if not name_container:
                return None
            
            name = ""
            kana = ""
            
            # 名前の抽出 (class="text")
            text_elem = name_container.find('p', class_='text')
            if text_elem:
                spans = text_elem.find_all('span')
                name = ''.join(span.get_text() for span in spans).strip()
            
            # 読みの抽出 (class="kana")
            kana_elem = name_container.find('p', class_='kana')
            if kana_elem:
                spans = kana_elem.find_all('span')
                kana = ''.join(span.get_text() for span in spans).strip()
            
            if name:
                logger.debug(f"名前・読み抽出成功: {name} ({kana})")
                return {"name": name, "kana": kana}
            
        except Exception as e:
            logger.debug(f"構造化名前抽出エラー: {e}")
        
        return None

    def extract_party_from_block(self, block):
        """ブロックから政党抽出"""
        try:
            # <div class="p_senkyoku_list_block_text_party">政党名</div>
            party_elem = block.find('div', class_='p_senkyoku_list_block_text_party')
            if party_elem:
                party_text = party_elem.get_text(strip=True)
                
                # 政党マスターリストとマッチング
                for party in self.parties:
                    if party in party_text:
                        return party
                
                # マスターリストにない場合はそのまま返す
                if party_text:
                    return party_text
            
        except Exception as e:
            logger.debug(f"政党抽出エラー: {e}")
        
        return "未分類"

    def extract_profile_url_from_block(self, block):
        """ブロックからプロフィールURL抽出"""
        try:
            # <a href="https://go2senkyo.com/seijika/68099" target="_blank">
            # <p class="p_senkyoku_list_block_link_text">詳細・プロフィール</p>
            
            links = block.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                if '/seijika/' in href and '詳細・プロフィール' in link_text:
                    return href
            
        except Exception as e:
            logger.debug(f"プロフィールURL抽出エラー: {e}")
        
        return ""

def collect_problem_prefectures():
    """問題県の構造化収集"""
    logger.info("🚀 問題県構造化データ収集開始...")
    
    collector = SenkyokuStructuredCollector()
    
    # 問題県とテスト県
    target_prefectures = [
        (24, "三重県"),  # 1名→6名期待
        (26, "京都府"),  # 6名→9名期待
        (14, "神奈川県"), # テスト（15名期待）
        (47, "沖縄県"),   # テスト（5名期待）
    ]
    
    all_results = []
    failed_prefectures = []
    
    for i, (pref_code, pref_name) in enumerate(target_prefectures):
        logger.info(f"\n=== [{i+1}/4] {pref_name} 構造化収集 ===")
        
        try:
            candidates = collector.collect_prefecture_structured(pref_code)
            all_results.extend(candidates)
            
            logger.info(f"✅ {pref_name} 完了: {len(candidates)}名")
            
            # 全県で詳細表示
            logger.info(f"📋 {pref_name} 候補者詳細:")
            for candidate in candidates:
                logger.info(f"  - {candidate['name']} ({candidate['name_kana']}) - {candidate['party']} - ID: {candidate['candidate_id']}")
            
            # レート制限（最後の県以外）
            if i < len(target_prefectures) - 1:
                time.sleep(1)
            
        except Exception as e:
            logger.error(f"❌ {pref_name} 収集エラー: {e}")
            failed_prefectures.append((pref_code, pref_name))
            continue
    
    logger.info(f"\n🎯 問題県構造化収集完了: 総計 {len(all_results)}名")
    
    # 失敗県の報告
    if failed_prefectures:
        logger.warning(f"⚠️ 収集失敗: {len(failed_prefectures)}県")
        for pref_code, pref_name in failed_prefectures:
            logger.warning(f"  - {pref_name} (コード: {pref_code})")
    
    # 重複チェック
    check_duplicates_structured(all_results)
    
    # 結果保存
    save_problem_prefecture_results(all_results)

def check_duplicates_structured(candidates):
    """構造化データの重複チェック"""
    logger.info("\n🔍 構造化データ重複チェック:")
    
    # candidate_idベースの重複
    id_counts = {}
    for candidate in candidates:
        candidate_id = candidate.get('candidate_id', '')
        if candidate_id:
            id_counts[candidate_id] = id_counts.get(candidate_id, 0) + 1
    
    id_duplicates = {k: v for k, v in id_counts.items() if v > 1}
    if id_duplicates:
        logger.warning("⚠️ ID重複:")
        for cid, count in id_duplicates.items():
            logger.warning(f"  {cid}: {count}回")
    else:
        logger.info("✅ ID重複なし")
    
    # 名前+都道府県ベースの重複
    name_counts = {}
    for candidate in candidates:
        name = candidate.get('name', '')
        prefecture = candidate.get('prefecture', '')
        key = f"{name}_{prefecture}"
        name_counts[key] = name_counts.get(key, 0) + 1
    
    name_duplicates = {k: v for k, v in name_counts.items() if v > 1}
    if name_duplicates:
        logger.warning("⚠️ 名前重複:")
        for name_pref, count in name_duplicates.items():
            logger.warning(f"  {name_pref}: {count}回")
    else:
        logger.info("✅ 名前重複なし")

def save_problem_prefecture_results(candidates):
    """問題県構造化収集結果の保存"""
    logger.info("💾 問題県構造化収集結果の保存...")
    
    # 統計計算
    party_stats = {}
    prefecture_stats = {}
    with_kana_count = 0
    
    for candidate in candidates:
        party = candidate.get('party', '未分類')
        prefecture = candidate.get('prefecture', '未分類')
        
        party_stats[party] = party_stats.get(party, 0) + 1
        prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
        
        if candidate.get('name_kana'):
            with_kana_count += 1
    
    # データ構造
    data = {
        "metadata": {
            "data_type": "go2senkyo_problem_prefectures_structured_sangiin_2025",
            "collection_method": "structured_html_extraction_problem_prefectures",
            "total_candidates": len(candidates),
            "candidates_with_kana": with_kana_count,
            "generated_at": datetime.now().isoformat(),
            "source_site": "sangiin.go2senkyo.com",
            "coverage": {
                "constituency_types": 1,
                "parties": len(party_stats),
                "prefectures": len(prefecture_stats)
            }
        },
        "statistics": {
            "by_party": party_stats,
            "by_prefecture": prefecture_stats,
            "by_constituency_type": {"single_member": len(candidates)}
        },
        "data": candidates
    }
    
    # ファイル保存
    data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    problem_file = data_dir / f"go2senkyo_problem_prefectures_{timestamp}.json"
    latest_file = data_dir / "go2senkyo_optimized_latest.json"
    
    with open(problem_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    logger.info(f"📁 問題県構造化収集結果保存: {problem_file}")
    
    # 統計表示
    logger.info("\n📊 問題県構造化収集統計:")
    logger.info(f"  総候補者: {len(candidates)}名")
    logger.info(f"  読み付き: {with_kana_count}名 ({with_kana_count/len(candidates)*100:.1f}%)")
    logger.info(f"  政党数: {len(party_stats)}政党")
    logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
    
    # 三重県・京都府の確認
    mie_count = prefecture_stats.get("三重県", 0)
    kyoto_count = prefecture_stats.get("京都府", 0)
    kanagawa_count = prefecture_stats.get("神奈川県", 0)
    okinawa_count = prefecture_stats.get("沖縄県", 0)
    
    logger.info(f"\n🔍 問題県確認:")
    logger.info(f"  三重県: {mie_count}名 (期待: 6名) {'✅' if mie_count >= 6 else '❌'}")
    logger.info(f"  京都府: {kyoto_count}名 (期待: 9名) {'✅' if kyoto_count >= 9 else '❌'}")
    logger.info(f"  神奈川県: {kanagawa_count}名 (テスト: 15名期待) {'✅' if kanagawa_count == 15 else '❌'}")
    logger.info(f"  沖縄県: {okinawa_count}名 (テスト: 5名期待) {'✅' if okinawa_count == 5 else '❌'}")
    
    return problem_file

if __name__ == "__main__":
    collect_problem_prefectures()