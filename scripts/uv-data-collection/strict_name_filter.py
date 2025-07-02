#!/usr/bin/env python3
"""
厳格な候補者名フィルタリング
実際の人名のみを抽出
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class StrictNameFilter:
    def __init__(self):
        # 一般的な日本人の姓
        self.common_surnames = [
            '佐藤', '鈴木', '高橋', '田中', '渡辺', '伊藤', '山本', '中村', '小林', '加藤',
            '吉田', '山田', '佐々木', '山口', '松本', '井上', '木村', '林', '清水', '森',
            '池田', '橋本', '山崎', '石川', '斎藤', '前田', '藤田', '近藤', '後藤', '長谷川',
            '石田', '石井', '上田', '原田', '和田', '武田', '小川', '村田', '小野', '中島',
            '中野', '中山', '川口', '古川', '浜田', '本田', '三浦', '平野', '福田', '太田',
            '岡田', '西村', '小島', '小松', '川崎', '大野', '大塚', '河野', '菅原', '金子',
            '竹内', '阿部', '高木', '西田', '岡本', '松田', '松井', '今井', '五十嵐', '青木',
            '大橋', '坂本', '安田', '石原', '内田', '山下', '菊地', '小山', '松尾', '田村',
            '増田', '水野', '村上', '杉山', '大久保', '新井', '工藤', '酒井', '原', '柴田',
            '谷口', '関', '野口', '野村', '西川', '千葉', '神田', '松岡', '岩田', '小池',
            '遠藤', '宮崎', '久保', '宮本', '熊谷', '横山', '藤井', '岡崎', '三宅', '飯田',
            '野田', '大谷', '丸山', '中川', '北村', '長野', '宮田', '小沢', '長田', '細川',
            '片山', '古田', '平田', '堀', '安藤', '黒田', '桜井', '丹羽', '永田', '市川',
            '高田', '大森', '川村', '金田', '吉川', '松村', '上野', '森田', '柳', '石塚',
            '大島', '吉野', '松原', '木下', '大山', '山内', '田口', '菅野', '杉田', '村松',
            '望月', '田辺', '小田', '星野', '秋田', '菊池', '藤原', '岩崎', '中田', '白石',
            '飯塚', '小林', '矢野', '長井', '川田', '井口', '沢田', '大沢', '佐野', '木田',
            '荒木', '新田', '高野', '水田', '田島', '浅野', '岩本', '横田', '宮地', '土屋',
            '森本', '椎名', '大西', '榊原', '渡部', '野沢', '青山', '富田', '中尾', '多田',
        ]
        
        # 一般的な日本人の名
        self.common_given_names = [
            '太郎', '次郎', '三郎', '四郎', '五郎', '六郎', '七郎', '八郎', '九郎', '十郎',
            '一', '二', '三', '四', '五', '六', '七', '八', '九', '十',
            '正', '和', '明', '博', '誠', '清', '健', '武', '勇', '強',
            '光', '輝', '進', '豊', '茂', '薫', '隆', '昭', '雄', '男',
            '子', '美', '恵', '愛', '花', '香', '里', '奈', '代', '江',
            '治', '弘', '浩', '寛', '広', '宏', '大', '巨', '高', '長',
            '忠', '孝', '信', '義', '仁', '礼', '智', '勇', '克', '勝',
            '幸', '好', '良', '優', '成', '栄', '繁', '昌', '盛', '興',
            'ひろし', 'たかし', 'けんじ', 'ゆうじ', 'しんじ', 'はじめ',
            'まさし', 'あきら', 'つよし', 'みのる', 'いさむ', 'たけし',
            'ゆき', 'みき', 'あき', 'なお', 'とも', 'さち', 'みど', 'かず',
            'さとし', 'ひでき', 'のぶ', 'かつ', 'みつ', 'よし', 'のり', 'しげ',
        ]
        
        # 政治・行政関連の除外ワード（より包括的）
        self.political_keywords = [
            '改革', '推進', '実現', '震災', '復興', '対策', '政策', '公約',
            '動画', '写真', '画像', '記事', '報告', '発表', '会見', '演説',
            '参議院', '衆議院', '国会', '議会', '委員会', '小委員会', '部会',
            '憲法', '法案', '条例', '規則', '要綱', '指針', '方針', '計画',
            '予算', '決算', '税制', '財政', '経済', '産業', '農業', '漁業',
            '教育', '文化', '科学', '技術', '環境', 'エネルギー', '交通',
            '厚生', '労働', '社会', '保障', '年金', '医療', '介護', '福祉',
            '安全', '保安', '防災', '消防', '警察', '自衛', '外交', '防衛',
            '地域', '地方', '都市', '農村', '過疎', '高齢', '少子', '人口',
            '情報', '通信', 'デジタル', 'ＤＸ', 'ＡＩ', 'ＩＣＴ', 'ＩＴ',
        ]

    def apply_strict_filtering(self):
        """厳格フィルタリングの適用"""
        logger.info("🔍 厳格な候補者名フィルタリング開始...")
        
        # 最新のクリーンファイルを読み込み
        data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
        
        cleaned_files = list(data_dir.glob("official_sources_cleaned_*.json"))
        if not cleaned_files:
            logger.error("❌ クリーンファイルが見つかりません")
            return
        
        latest_file = max(cleaned_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"📁 処理対象ファイル: {latest_file}")
        
        with open(latest_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        original_candidates = data.get('data', [])
        logger.info(f"📊 元データ: {len(original_candidates)}名")
        
        # 厳格フィルタリング実行
        strict_filtered = self.filter_candidates_strictly(original_candidates)
        
        # Go2senkyo.comの構造化データも統合
        go2s_candidates = self.load_go2senkyo_structured_data()
        
        # データ統合
        final_candidates = self.merge_candidate_sources(strict_filtered, go2s_candidates)
        
        # 統計再計算
        party_stats = {}
        prefecture_stats = {}
        source_stats = {}
        
        for candidate in final_candidates:
            party = candidate.get('party', '未分類')
            prefecture = candidate.get('prefecture', '未分類')
            source = candidate.get('source', '未分類')
            
            party_stats[party] = party_stats.get(party, 0) + 1
            if prefecture and prefecture != '未分類':
                prefecture_stats[prefecture] = prefecture_stats.get(prefecture, 0) + 1
            source_stats[source] = source_stats.get(source, 0) + 1
        
        # 最終統合データ作成
        final_data = {
            "metadata": {
                "data_type": "comprehensive_strict_filtered_sangiin_2025",
                "collection_method": "official_sources_go2senkyo_merged_strict_filtered",
                "total_candidates": len(final_candidates),
                "official_sources_candidates": len(strict_filtered),
                "go2senkyo_candidates": len(go2s_candidates),
                "generated_at": datetime.now().isoformat(),
                "sources": ["総務省選挙部", "各政党公式サイト", "Go2senkyo.com構造化抽出"],
                "coverage": {
                    "parties": len(party_stats),
                    "prefectures": len(prefecture_stats),
                    "sources": len(source_stats)
                }
            },
            "statistics": {
                "by_party": party_stats,
                "by_prefecture": prefecture_stats,
                "by_source": source_stats,
                "by_constituency_type": {"single_member": len(final_candidates)}
            },
            "data": final_candidates
        }
        
        # ファイル保存
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        final_file = data_dir / f"comprehensive_strict_filtered_{timestamp}.json"
        latest_optimized_file = data_dir / "go2senkyo_optimized_latest.json"
        
        with open(final_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        with open(latest_optimized_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"📁 最終統合データ保存: {final_file}")
        logger.info(f"📁 最新ファイル更新: {latest_optimized_file}")
        
        # 結果表示
        logger.info("\n📊 厳格フィルタリング＋統合結果:")
        logger.info(f"  最終候補者数: {len(final_candidates)}名")
        logger.info(f"  公式ソース（厳格）: {len(strict_filtered)}名")
        logger.info(f"  Go2senkyo構造化: {len(go2s_candidates)}名")
        logger.info(f"  政党数: {len(party_stats)}政党")
        logger.info(f"  都道府県数: {len(prefecture_stats)}都道府県")
        
        logger.info("\n📈 政党別候補者数:")
        for party, count in sorted(party_stats.items(), key=lambda x: x[1], reverse=True):
            logger.info(f"    {party}: {count}名")
        
        logger.info("\n📍 主要都道府県:")
        major_prefs = dict(sorted(prefecture_stats.items(), key=lambda x: x[1], reverse=True)[:10])
        for pref, count in major_prefs.items():
            logger.info(f"    {pref}: {count}名")
        
        return final_file

    def filter_candidates_strictly(self, candidates):
        """厳格な候補者フィルタリング"""
        filtered = []
        removed_count = 0
        removal_reasons = {}
        
        for candidate in candidates:
            name = candidate.get('name', '').strip()
            
            # 厳格な人名チェック
            is_valid, reason = self.is_strict_valid_person_name(name)
            
            if is_valid:
                filtered.append(candidate)
            else:
                removed_count += 1
                removal_reasons[reason] = removal_reasons.get(reason, 0) + 1
                logger.debug(f"厳格除去: {name} (理由: {reason})")
        
        logger.info(f"🗑️ 厳格除去詳細:")
        for reason, count in removal_reasons.items():
            logger.info(f"  {reason}: {count}件")
        
        return filtered

    def is_strict_valid_person_name(self, name):
        """厳格な人名妥当性チェック"""
        if not name or len(name) < 2 or len(name) > 8:
            return False, "名前の長さが不適切"
        
        # 政治・行政キーワードのチェック
        for keyword in self.political_keywords:
            if keyword in name:
                return False, f"政治キーワード含有: {keyword}"
        
        # 人名らしきパターンのチェック
        if self.looks_like_person_name(name):
            return True, "有効な人名"
        
        return False, "人名パターンに該当しない"

    def looks_like_person_name(self, name):
        """人名らしきパターンかチェック"""
        # パターン1: 一般的な姓＋名の組み合わせ
        for surname in self.common_surnames:
            if name.startswith(surname):
                remaining = name[len(surname):]
                if len(remaining) >= 1 and len(remaining) <= 3:
                    # 残りの部分が名前らしいかチェック
                    if any(given in remaining for given in self.common_given_names):
                        return True
                    # または漢字・ひらがなの組み合わせ
                    if re.match(r'^[一-龯ひらがな]+$', remaining):
                        return True
        
        # パターン2: 一般的な名前成分を含む
        for given_name in self.common_given_names:
            if given_name in name and len(name) <= 6:
                return True
        
        # パターン3: 適切な漢字・ひらがな構成
        if re.match(r'^[一-龯]{1,3}[ひらがな]{1,3}$', name):
            return True
        
        if re.match(r'^[一-龯]{2,4}$', name):
            # 2-4文字の漢字のみ（一般的な日本人名パターン）
            return True
        
        # パターン4: ひらがな名前
        if re.match(r'^[ひらがな]{2,5}$', name):
            return True
        
        # パターン5: カタカナ名前（外国系候補者）
        if re.match(r'^[ァ-ヶー]{2,8}$', name):
            return True
        
        return False

    def load_go2senkyo_structured_data(self):
        """Go2senkyo.com構造化データの読み込み"""
        logger.info("📊 Go2senkyo構造化データ読み込み...")
        
        data_dir = Path(__file__).parent.parent.parent / "frontend" / "public" / "data" / "sangiin_candidates"
        
        # 構造化テストファイルを探す
        structured_files = list(data_dir.glob("go2senkyo_structured_test_*.json"))
        if not structured_files:
            logger.warning("⚠️ Go2senkyo構造化ファイルが見つかりません")
            return []
        
        latest_structured = max(structured_files, key=lambda f: f.stat().st_mtime)
        logger.info(f"📁 Go2senkyo構造化ファイル: {latest_structured}")
        
        try:
            with open(latest_structured, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            candidates = data.get('data', [])
            logger.info(f"📋 Go2senkyo構造化データ: {len(candidates)}名")
            return candidates
            
        except Exception as e:
            logger.error(f"❌ Go2senkyo構造化データ読み込みエラー: {e}")
            return []

    def merge_candidate_sources(self, official_candidates, go2s_candidates):
        """複数ソースの候補者データ統合"""
        logger.info("🔗 候補者データソース統合...")
        
        # 重複除去用のセット
        seen_names = set()
        merged_candidates = []
        
        # 公式ソース候補者を優先
        for candidate in official_candidates:
            name = candidate.get('name', '')
            if name and name not in seen_names:
                seen_names.add(name)
                merged_candidates.append(candidate)
        
        # Go2senkyo.com候補者を追加（重複しない場合のみ）
        for candidate in go2s_candidates:
            name = candidate.get('name', '')
            if name and name not in seen_names:
                seen_names.add(name)
                merged_candidates.append(candidate)
        
        logger.info(f"🎯 統合結果: {len(merged_candidates)}名")
        logger.info(f"  公式ソース: {len(official_candidates)}名")
        logger.info(f"  Go2senkyo追加: {len(merged_candidates) - len(official_candidates)}名")
        
        return merged_candidates

def main():
    """メイン処理"""
    logger.info("🔍 厳格候補者名フィルタリング開始...")
    
    filter_obj = StrictNameFilter()
    final_file = filter_obj.apply_strict_filtering()
    
    if final_file:
        logger.info(f"✅ 厳格フィルタリング＋統合完了: {final_file}")
    else:
        logger.error("❌ 厳格フィルタリング失敗")

if __name__ == "__main__":
    main()