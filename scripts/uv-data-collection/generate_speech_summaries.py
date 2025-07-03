#!/usr/bin/env python3
"""
議事録要約生成スクリプト

議事録データから要約を生成し、検索・分析しやすい形式で保存する
- 委員会ごとの重要な議論をピックアップ
- 政策分野別の議論動向をまとめ
- 主要発言者の発言要約を作成
"""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import re

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SpeechSummarizer:
    """議事録要約生成クラス"""
    
    def __init__(self, period: str = "recent_week", force_regenerate: bool = False):
        self.period = period
        self.force_regenerate = force_regenerate
        
        # ディレクトリ設定
        self.project_root = Path(__file__).parent.parent.parent
        self.speeches_dir = self.project_root / "frontend" / "public" / "data" / "speeches"
        self.summaries_dir = self.project_root / "frontend" / "public" / "data" / "summaries"
        
        # 出力ディレクトリ作成
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        
        # 政策分野キーワード
        self.policy_keywords = {
            "外交・安全保障": ["外交", "安全保障", "防衛", "自衛隊", "同盟", "条約", "外務", "国際"],
            "経済・財政": ["経済", "財政", "予算", "税制", "金融", "GDP", "財務", "経済産業"],
            "社会保障": ["年金", "医療", "介護", "福祉", "社会保障", "厚生労働"],
            "教育・文化": ["教育", "学校", "大学", "文化", "スポーツ", "文部科学"],
            "環境・エネルギー": ["環境", "気候", "エネルギー", "原子力", "再生可能", "CO2"],
            "労働・雇用": ["労働", "雇用", "働き方", "賃金", "就職", "職業"],
            "地方・都市": ["地方", "自治体", "都市", "地域", "まちづくり"],
            "デジタル・科学技術": ["デジタル", "IT", "AI", "科学技術", "イノベーション", "DX"],
            "農林水産": ["農業", "林業", "水産", "食料", "農林水産"],
            "国土・交通": ["国土", "交通", "道路", "鉄道", "航空", "港湾", "国土交通"]
        }
        
    def load_speech_data(self) -> List[Dict[str, Any]]:
        """議事録データを読み込み"""
        all_speeches = []
        
        try:
            # 期間に基づいてファイルを選択
            target_files = self.get_target_files()
            
            for file_path in target_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        
                    # データ構造を正規化
                    speeches = []
                    if isinstance(data, list):
                        speeches = data
                    elif isinstance(data, dict) and 'data' in data:
                        speeches = data['data']
                    
                    all_speeches.extend(speeches)
                    logger.info(f"読み込み完了: {file_path.name} ({len(speeches)}件)")
                    
                except Exception as e:
                    logger.error(f"ファイル読み込みエラー {file_path}: {e}")
                    continue
            
            logger.info(f"総議事録数: {len(all_speeches)}件")
            return all_speeches
            
        except Exception as e:
            logger.error(f"議事録データ読み込みエラー: {e}")
            return []
    
    def get_target_files(self) -> List[Path]:
        """対象ファイルを取得"""
        all_files = list(self.speeches_dir.glob("*.json"))
        
        if self.period == "all":
            return sorted(all_files, key=lambda x: x.stat().st_mtime, reverse=True)
        elif self.period == "recent_month":
            cutoff_date = datetime.now() - timedelta(days=30)
        else:  # recent_week
            cutoff_date = datetime.now() - timedelta(days=7)
        
        # 最近の期間のファイルのみ選択
        recent_files = [
            f for f in all_files 
            if datetime.fromtimestamp(f.stat().st_mtime) >= cutoff_date
        ]
        
        return sorted(recent_files, key=lambda x: x.stat().st_mtime, reverse=True)
    
    def categorize_by_policy(self, speeches: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """政策分野別に議事録を分類"""
        categorized = {policy: [] for policy in self.policy_keywords.keys()}
        categorized["その他"] = []
        
        for speech in speeches:
            text = speech.get('text', '') + ' ' + speech.get('committee', '')
            assigned = False
            
            for policy, keywords in self.policy_keywords.items():
                if any(keyword in text for keyword in keywords):
                    categorized[policy].append(speech)
                    assigned = True
                    break
            
            if not assigned:
                categorized["その他"].append(speech)
        
        return categorized
    
    def generate_committee_summary(self, speeches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """委員会別の要約を生成"""
        committee_groups = {}
        
        # 委員会別にグループ化
        for speech in speeches:
            committee = speech.get('committee', '未分類')
            if committee not in committee_groups:
                committee_groups[committee] = []
            committee_groups[committee].append(speech)
        
        summaries = {}
        for committee, committee_speeches in committee_groups.items():
            if len(committee_speeches) < 3:  # 最低限の件数
                continue
                
            # 主要な発言者を抽出
            speakers = {}
            for speech in committee_speeches:
                speaker = speech.get('speaker', '不明')
                if speaker not in speakers:
                    speakers[speaker] = []
                speakers[speaker].append(speech)
            
            # 上位発言者を選択
            top_speakers = sorted(speakers.items(), key=lambda x: len(x[1]), reverse=True)[:5]
            
            summaries[committee] = {
                "total_speeches": len(committee_speeches),
                "unique_speakers": len(speakers),
                "top_speakers": [
                    {
                        "name": speaker,
                        "speech_count": len(speeches_list),
                        "party": speeches_list[0].get('party', '不明') if speeches_list else '不明'
                    }
                    for speaker, speeches_list in top_speakers
                ],
                "date_range": self.get_date_range(committee_speeches),
                "summary_text": self.create_committee_summary_text(committee_speeches)
            }
        
        return summaries
    
    def generate_policy_summary(self, categorized_speeches: Dict[str, List[Dict[str, Any]]]) -> Dict[str, Any]:
        """政策分野別の要約を生成"""
        policy_summaries = {}
        
        for policy, speeches in categorized_speeches.items():
            if len(speeches) < 5:  # 最低限の件数
                continue
            
            # 主要な議論点を抽出
            discussion_points = self.extract_discussion_points(speeches)
            
            # 政党別の発言傾向
            party_positions = self.analyze_party_positions(speeches)
            
            policy_summaries[policy] = {
                "total_speeches": len(speeches),
                "discussion_points": discussion_points,
                "party_positions": party_positions,
                "date_range": self.get_date_range(speeches),
                "summary_text": self.create_policy_summary_text(policy, speeches)
            }
        
        return policy_summaries
    
    def extract_discussion_points(self, speeches: List[Dict[str, Any]]) -> List[str]:
        """主要な議論点を抽出"""
        # 頻出キーワードを基に議論点を推定
        all_text = ' '.join([speech.get('text', '') for speech in speeches])
        
        # 重要そうなフレーズを抽出
        important_phrases = []
        
        # 質問・答弁パターン
        question_patterns = [
            r'について(お|御)聞きします',
            r'についてお答えください',
            r'について質問いたします',
            r'について伺います'
        ]
        
        for pattern in question_patterns:
            matches = re.findall(r'(.{10,50})' + pattern, all_text)
            important_phrases.extend(matches[:3])  # 上位3件
        
        return important_phrases[:10]  # 最大10件
    
    def analyze_party_positions(self, speeches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """政党別の発言傾向を分析"""
        party_stats = {}
        
        for speech in speeches:
            party = speech.get('party', '不明')
            if party not in party_stats:
                party_stats[party] = {
                    "speech_count": 0,
                    "speakers": set()
                }
            
            party_stats[party]["speech_count"] += 1
            party_stats[party]["speakers"].add(speech.get('speaker', '不明'))
        
        # setをlistに変換
        for party in party_stats:
            party_stats[party]["speakers"] = list(party_stats[party]["speakers"])
            party_stats[party]["unique_speakers"] = len(party_stats[party]["speakers"])
        
        return party_stats
    
    def get_date_range(self, speeches: List[Dict[str, Any]]) -> Dict[str, str]:
        """議事録の日付範囲を取得"""
        dates = [speech.get('date') for speech in speeches if speech.get('date')]
        dates = [d for d in dates if d]  # Noneを除外
        
        if not dates:
            return {"start": "", "end": ""}
        
        dates.sort()
        return {
            "start": dates[0],
            "end": dates[-1]
        }
    
    def create_committee_summary_text(self, speeches: List[Dict[str, Any]]) -> str:
        """委員会要約テキストを生成"""
        if not speeches:
            return ""
        
        # 議論の概要を簡潔にまとめる
        sample_speeches = speeches[:3]  # 代表的な発言
        topics = [speech.get('text', '')[:100] for speech in sample_speeches]
        
        return f"主な議論: {', '.join(topics)}"
    
    def create_policy_summary_text(self, policy: str, speeches: List[Dict[str, Any]]) -> str:
        """政策分野要約テキストを生成"""
        if not speeches:
            return ""
        
        return f"{policy}分野で{len(speeches)}件の議論が行われました。"
    
    def generate_weekly_highlights(self, speeches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """週間ハイライトを生成"""
        # 今週の重要な動き
        this_week = datetime.now() - timedelta(days=7)
        recent_speeches = [
            s for s in speeches 
            if s.get('date') and datetime.strptime(s['date'], '%Y-%m-%d') >= this_week
        ]
        
        if not recent_speeches:
            return {}
        
        # 注目の委員会
        committee_activity = {}
        for speech in recent_speeches:
            committee = speech.get('committee', '未分類')
            committee_activity[committee] = committee_activity.get(committee, 0) + 1
        
        top_committees = sorted(committee_activity.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "period": f"{this_week.strftime('%Y-%m-%d')} - {datetime.now().strftime('%Y-%m-%d')}",
            "total_speeches": len(recent_speeches),
            "active_committees": [
                {"name": name, "activity_count": count} 
                for name, count in top_committees
            ],
            "summary": f"今週は{len(recent_speeches)}件の議事録が記録されました。"
        }
    
    def save_summaries(self, summaries: Dict[str, Any]) -> str:
        """要約データを保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # ファイル名を期間に基づいて決定
        if self.period == "all":
            filename = f"speech_summaries_all_{timestamp}.json"
        elif self.period == "recent_month":
            filename = f"speech_summaries_month_{timestamp}.json"
        else:  # recent_week
            filename = f"speech_summaries_week_{timestamp}.json"
        
        output_file = self.summaries_dir / filename
        latest_file = self.summaries_dir / "speech_summaries_latest.json"
        
        # メタデータ付きで保存
        output_data = {
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "period": self.period,
                "force_regenerate": self.force_regenerate,
                "summary_types": list(summaries.keys()),
                "total_categories": len(summaries)
            },
            "summaries": summaries
        }
        
        # タイムスタンプ付きファイル
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        # 最新ファイル
        with open(latest_file, 'w', encoding='utf-8') as f:
            json.dump(output_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"要約保存完了: {output_file}")
        logger.info(f"最新ファイル更新: {latest_file}")
        
        return str(output_file)

def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(description='議事録要約生成スクリプト')
    parser.add_argument('--period', choices=['recent_week', 'recent_month', 'all'], 
                       default='recent_week', help='要約対象期間')
    parser.add_argument('--force-regenerate', action='store_true', 
                       help='既存要約の強制再生成')
    parser.add_argument('--max-speeches', type=int, default=1000,
                       help='最大処理議事録数')
    
    args = parser.parse_args()
    
    logger.info(f"議事録要約生成開始: period={args.period}, force={args.force_regenerate}")
    
    try:
        # 要約生成器初期化
        summarizer = SpeechSummarizer(
            period=args.period,
            force_regenerate=args.force_regenerate
        )
        
        # 議事録データ読み込み
        speeches = summarizer.load_speech_data()
        
        if not speeches:
            logger.warning("処理対象の議事録データがありません")
            return
        
        # 最大件数制限
        if len(speeches) > args.max_speeches:
            speeches = speeches[:args.max_speeches]
            logger.info(f"処理件数制限: {args.max_speeches}件")
        
        # 各種要約生成
        all_summaries = {}
        
        # 1. 委員会別要約
        logger.info("委員会別要約生成中...")
        committee_summaries = summarizer.generate_committee_summary(speeches)
        all_summaries["committees"] = committee_summaries
        
        # 2. 政策分野別要約
        logger.info("政策分野別要約生成中...")
        categorized = summarizer.categorize_by_policy(speeches)
        policy_summaries = summarizer.generate_policy_summary(categorized)
        all_summaries["policies"] = policy_summaries
        
        # 3. 週間ハイライト
        logger.info("週間ハイライト生成中...")
        weekly_highlights = summarizer.generate_weekly_highlights(speeches)
        if weekly_highlights:
            all_summaries["weekly_highlights"] = weekly_highlights
        
        # 要約保存
        output_file = summarizer.save_summaries(all_summaries)
        
        logger.info(f"議事録要約生成完了: {output_file}")
        logger.info(f"委員会要約: {len(committee_summaries)}件")
        logger.info(f"政策要約: {len(policy_summaries)}件")
        
    except Exception as e:
        logger.error(f"要約生成エラー: {e}")
        raise

if __name__ == "__main__":
    main()