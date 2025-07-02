#!/usr/bin/env python3
"""
Go2senkyo.com全47都道府県完全収集
構造化抽出で高品質データを取得
"""

import json
import logging
import requests
import time
from datetime import datetime
from pathlib import Path
from bs4 import BeautifulSoup
import re
from fake_useragent import UserAgent
import random

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class CompleteGo2senkyoCollector:
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
        
        # 全都道府県マッピング
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

    def collect_all_prefectures_complete(self):
        """全47都道府県の完全収集"""
        logger.info("🚀 Go2senkyo.com全47都道府県完全収集開始...")
        
        all_results = []
        failed_prefectures = []
        success_count = 0
        
        # 効率化のため、10県ずつバッチ処理
        batch_size = 10
        prefecture_items = list(self.prefectures.items())
        
        for batch_start in range(0, len(prefecture_items), batch_size):
            batch_end = min(batch_start + batch_size, len(prefecture_items))
            current_batch = prefecture_items[batch_start:batch_end]
            
            logger.info(f"\n🔄 バッチ {batch_start//batch_size + 1}/{(len(prefecture_items)-1)//batch_size + 1}: {batch_start+1}-{batch_end}県")
            
            for pref_code, pref_name in current_batch:
                try:
                    logger.info(f"📍 [{pref_code}/47] {pref_name} 収集中...")
                    
                    candidates = self.collect_prefecture_structured(pref_code)
                    
                    if candidates:
                        all_results.extend(candidates)
                        success_count += 1
                        logger.info(f"✅ {pref_name}: {len(candidates)}名")
                    else:
                        logger.warning(f"⚠️ {pref_name}: 候補者なし")
                    
                    # レート制限（最後の県以外）
                    if pref_code < 47:
                        time.sleep(1.5)
                    
                except Exception as e:
                    logger.error(f"❌ {pref_name} 収集エラー: {e}")
                    failed_prefectures.append((pref_code, pref_name))
                    continue
            
            # バッチ間の休憩
            if batch_end < len(prefecture_items):
                logger.info(f"⏸️ バッチ間休憩（3秒）...")
                time.sleep(3)
        
        logger.info(f"\n🎯 全都道府県収集完了:")
        logger.info(f"  成功: {success_count}/47県")
        logger.info(f"  総候補者: {len(all_results)}名")
        
        if failed_prefectures:
            logger.warning(f"⚠️ 収集失敗県: {len(failed_prefectures)}県")
            for pref_code, pref_name in failed_prefectures:
                logger.warning(f"  - {pref_name}")
        
        # 重複チェック
        self.check_duplicates_structured(all_results)
        
        # 結果保存
        saved_file = self.save_complete_results(all_results, success_count, failed_prefectures)
        
        return saved_file

    def collect_prefecture_structured(self, pref_code: int):
        """構造化された都道府県データ収集"""
        pref_name = self.prefectures.get(pref_code, f"未知_{pref_code}")
        url = f"https://sangiin.go2senkyo.com/2025/prefecture/{pref_code}"
        
        try:
            # 初回リクエスト
            response = self.session.get(url, timeout=30)
            
            if response.status_code != 200:
                logger.debug(f"❌ {pref_name} アクセス失敗: HTTP {response.status_code}")
                return []
            
            # 遅延ロード対応
            time.sleep(2)  # 短縮版
            
            # 再リクエストでフルコンテンツ取得
            response2 = self.session.get(url, timeout=30)
            soup = BeautifulSoup(response2.text, 'html.parser')
            
            # 構造化抽出の実行
            candidates = self.extract_candidates_structured(soup, pref_name, url)
            
            return candidates
            
        except Exception as e:
            logger.debug(f"❌ {pref_name} データ収集エラー: {e}")
            return []

    def extract_candidates_structured(self, soup: BeautifulSoup, prefecture: str, page_url: str):
        """構造化された候補者抽出"""
        candidates = []
        
        try:
            # 候補者ブロックを探索
            candidate_blocks = soup.find_all('div', class_='p_senkyoku_list_block')
            
            for i, block in enumerate(candidate_blocks):
                try:
                    candidate = self.extract_candidate_from_structured_block(block, prefecture, page_url, i)
                    if candidate:
                        candidates.append(candidate)
                    
                except Exception as e:
                    logger.debug(f"ブロック {i} 抽出エラー: {e}")
                    continue
            
        except Exception as e:
            logger.debug(f"{prefecture} 構造化抽出エラー: {e}")
        
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
                "source": "go2senkyo_structured_complete",
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
                match = re.search(r'/seijika/(\\d+)', profile_url)
                if match:
                    candidate["candidate_id"] = f"go2s_{match.group(1)}"
            
            # 名前が取得できない場合はスキップ
            if not candidate["name"]:
                return None
            
            return candidate
            
        except Exception as e:
            logger.debug(f"構造化ブロック抽出エラー: {e}")
            return None

    def extract_name_and_kana_structured(self, block):
        """構造化された名前・読み抽出"""
        try:
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
                return {"name": name, "kana": kana}
            
        except Exception as e:
            logger.debug(f"構造化名前抽出エラー: {e}")
        
        return None

    def extract_party_from_block(self, block):
        """ブロックから政党抽出"""
        try:
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
            links = block.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                link_text = link.get_text(strip=True)
                
                if '/seijika/' in href and '詳細・プロフィール' in link_text:
                    return href
            
        except Exception as e:
            logger.debug(f"プロフィールURL抽出エラー: {e}")
        
        return ""

    def check_duplicates_structured(self, candidates):
        """構造化データの重複チェック"""
        logger.info("🔍 重複チェック:")
        
        # candidate_idベースの重複
        id_counts = {}
        for candidate in candidates:
            candidate_id = candidate.get('candidate_id', '')
            if candidate_id:
                id_counts[candidate_id] = id_counts.get(candidate_id, 0) + 1
        
        id_duplicates = {k: v for k, v in id_counts.items() if v > 1}
        if id_duplicates:
            logger.warning("⚠️ ID重複発見:")
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
            logger.warning("⚠️ 名前重複発見:")
            for name_pref, count in name_duplicates.items():
                logger.warning(f"  {name_pref}: {count}回")
        else:
            logger.info("✅ 名前重複なし")

    def save_complete_results(self, candidates, success_count, failed_prefectures):
        """完全収集結果の保存"""
        logger.info("💾 完全収集結果の保存...")
        
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
                "data_type": "go2senkyo_complete_structured_sangiin_2025",
                "collection_method": "structured_html_extraction_all_47_prefectures",
                "total_candidates": len(candidates),
                "candidates_with_kana": with_kana_count,
                "successful_prefectures": success_count,
                "failed_prefectures": len(failed_prefectures),
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
        
        complete_file = data_dir / f"go2senkyo_complete_structured_{timestamp}.json"
        latest_file = data_dir / "go2senkyo_optimized_latest.json"
        
        with open(complete_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        # 合理的な候補者数の場合のみ最新ファイルを更新
        if len(candidates) >= 100 and len(prefecture_stats) >= 30:
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"📁 最新ファイル更新: {latest_file}")
        
        logger.info(f"📁 完全収集結果保存: {complete_file}")
        
        # 統計表示
        logger.info("\n📊 Go2senkyo完全収集統計:")
        logger.info(f"  総候補者: {len(candidates)}名")
        logger.info(f"  読み付き: {with_kana_count}名 ({with_kana_count/len(candidates)*100:.1f}%)")
        logger.info(f"  成功県: {success_count}/47県 ({success_count/47*100:.1f}%)")
        logger.info(f"  政党数: {len(party_stats)}政党")
        logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
        
        # 主要政党の確認
        major_parties = dict(sorted(party_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        logger.info("\n📈 主要政党別候補者数:")
        for party, count in major_parties.items():
            logger.info(f"  {party}: {count}名")
        
        # 主要都道府県の確認
        major_prefs = dict(sorted(prefecture_stats.items(), key=lambda x: x[1], reverse=True)[:15])
        logger.info("\n📍 主要都道府県別候補者数:")
        for pref, count in major_prefs.items():
            logger.info(f"  {pref}: {count}名")
        
        return complete_file

    def check_if_update_needed(self) -> bool:
        """7日間隔での更新必要性チェック"""
        try:
            data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
            latest_file = data_dir / "go2senkyo_optimized_latest.json"
            
            if not latest_file.exists():
                logger.info("📅 最新ファイルが存在しないため更新実行")
                return True
            
            # ファイルの最終更新日を取得
            last_modified = datetime.fromtimestamp(latest_file.stat().st_mtime)
            now = datetime.now()
            days_since_update = (now - last_modified).days
            
            if days_since_update >= 7:
                logger.info(f"📅 前回更新から{days_since_update}日経過: 更新実行")
                return True
            else:
                logger.info(f"⏭️ 前回更新から{days_since_update}日: 更新スキップ")
                return False
                
        except Exception as e:
            logger.warning(f"更新チェックエラー: {e}, デフォルトで更新実行")
            return True

def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Go2senkyo.com全47都道府県完全収集')
    parser.add_argument('--force-update', action='store_true', help='7日間隔を無視して強制更新')
    parser.add_argument('--test-mode', action='store_true', help='テストモード（東京・大阪・神奈川のみ）')
    parser.add_argument('--max-candidates', type=int, default=1000, help='最大候補者数制限')
    
    args = parser.parse_args()
    
    logger.info("🚀 Go2senkyo.com参院選候補者データ収集開始...")
    
    collector = CompleteGo2senkyoCollector()
    
    # 強制更新フラグがない場合は7日間隔チェック
    if not args.force_update and not collector.check_if_update_needed():
        logger.info("📝 7日間隔チェックによりスキップ")
        return
    
    # テストモードの場合は対象都道府県を限定
    if args.test_mode:
        logger.info("🧪 テストモード: 東京・大阪・神奈川のみ収集")
        original_prefectures = collector.prefectures.copy()
        collector.prefectures = {13: "東京都", 27: "大阪府", 14: "神奈川県"}
    
    result_file = collector.collect_all_prefectures_complete()
    
    if result_file:
        logger.info(f"✅ 全47都道府県収集完了: {result_file}")
    else:
        logger.error("❌ 収集失敗")

if __name__ == "__main__":
    main()