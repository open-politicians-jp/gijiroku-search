#!/usr/bin/env python3
"""
会議要約生成スクリプト (Issue #21対応)

軽量LLMを使用して委員会会議や本会議の要約を自動生成
- 国会議事録の要約作成
- 主要議論ポイントの抽出
- 発言者別の主張要約
- 結論・決議事項の明確化

使用LLM: Ollama (ローカル実行) または OpenAI API (設定により選択)
"""

import json
import re
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging
from collections import defaultdict

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MeetingSummaryGenerator:
    """会議要約生成クラス (Issue #21対応)"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.speeches_dir = self.project_root / "frontend" / "public" / "data" / "speeches"
        self.summaries_dir = self.project_root / "frontend" / "public" / "data" / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        
        # LLM設定
        self.llm_type = os.getenv('LLM_TYPE', 'mock')  # 'ollama', 'openai', 'mock'
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        # 要約設定
        self.max_input_length = 8000  # 入力テキストの最大長
        self.summary_length = 500     # 要約の目標文字数
        
        # 軽量モデルの選択
        self.model_name = self._select_model()
        
    def _select_model(self) -> str:
        """使用するモデルを選択"""
        if self.llm_type == 'ollama':
            return 'llama3.2:3b'  # 軽量な日本語対応モデル
        elif self.llm_type == 'openai':
            return 'gpt-3.5-turbo'  # コスト効率の良いモデル
        else:
            return 'mock'  # テスト用モック
    
    def load_speech_data(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """議事録データを読み込み"""
        logger.info("議事録データ読み込み中...")
        
        # 最新の議事録ファイルを取得
        speech_files = list(self.speeches_dir.glob("speeches_*.json"))
        if not speech_files:
            logger.error("議事録ファイルが見つかりません")
            return []
        
        # 最新ファイルを選択
        latest_file = sorted(speech_files)[-1]
        logger.info(f"使用ファイル: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                speeches = data if isinstance(data, list) else data.get('data', [])
                
                if limit:
                    speeches = speeches[:limit]
                
                logger.info(f"読み込み完了: {len(speeches)}件の発言")
                return speeches
                
        except Exception as e:
            logger.error(f"議事録データ読み込みエラー: {e}")
            return []
    
    def group_speeches_by_meeting(self, speeches: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """発言を会議別にグループ化"""
        logger.info("会議別グループ化中...")
        
        meetings = defaultdict(list)
        
        for speech in speeches:
            # 会議キーの生成 (日付 + 委員会名 + 院)
            date = speech.get('date', 'unknown')
            committee = speech.get('committee', '本会議')
            house = speech.get('house', 'unknown')
            
            meeting_key = f"{date}_{house}_{committee}"
            meetings[meeting_key].append(speech)
        
        # 発言数が少ない会議は除外
        filtered_meetings = {
            key: speeches for key, speeches in meetings.items() 
            if len(speeches) >= 5
        }
        
        logger.info(f"対象会議数: {len(filtered_meetings)}件")
        return filtered_meetings
    
    def prepare_meeting_text(self, speeches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """会議テキストを要約用に準備"""
        meeting_info = {
            'date': speeches[0].get('date', 'unknown'),
            'committee': speeches[0].get('committee', '本会議'),
            'house': speeches[0].get('house', 'unknown'),
            'session': speeches[0].get('session', 'unknown'),
            'speech_count': len(speeches),
            'speakers': set(),
            'parties': set(),
            'full_text': '',
            'structured_text': []
        }
        
        # 発言を時系列順にソート
        sorted_speeches = sorted(speeches, key=lambda x: x.get('url', ''))
        
        full_text_parts = []
        for speech in sorted_speeches:
            speaker = speech.get('speaker', '不明')
            party = speech.get('party', '不明')
            text = speech.get('text', '')
            
            # 短すぎる発言は除外
            if len(text.strip()) < 20:
                continue
            
            meeting_info['speakers'].add(speaker)
            meeting_info['parties'].add(party)
            
            # 構造化テキスト
            speech_entry = {
                'speaker': speaker,
                'party': party,
                'text': text[:1000]  # 長すぎる発言は制限
            }
            meeting_info['structured_text'].append(speech_entry)
            
            # 全文テキスト
            full_text_parts.append(f"【{speaker}({party})】{text[:800]}")
        
        # 全文テキストを結合（長さ制限）
        full_text = '\n\n'.join(full_text_parts)
        if len(full_text) > self.max_input_length:
            full_text = full_text[:self.max_input_length] + '...'
        
        meeting_info['full_text'] = full_text
        meeting_info['speakers'] = list(meeting_info['speakers'])
        # None値を除外して政党リストを作成
        meeting_info['parties'] = [p for p in meeting_info['parties'] if p is not None]
        
        return meeting_info
    
    def generate_summary_with_llm(self, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """LLMを使用して要約を生成"""
        
        if self.llm_type == 'mock':
            return self._generate_mock_summary(meeting_info)
        elif self.llm_type == 'ollama':
            return self._generate_ollama_summary(meeting_info)
        elif self.llm_type == 'openai':
            return self._generate_openai_summary(meeting_info)
        else:
            logger.error(f"未対応のLLMタイプ: {self.llm_type}")
            return self._generate_mock_summary(meeting_info)
    
    def _generate_mock_summary(self, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """モック要約生成（テスト用）"""
        logger.info("モック要約生成中...")
        
        committee = meeting_info['committee']
        date = meeting_info['date']
        speaker_count = len(meeting_info['speakers'])
        speech_count = meeting_info['speech_count']
        parties = meeting_info['parties']
        
        # 簡単な統計ベース要約
        summary = {
            'title': f"{date} {committee}会議要約",
            'overview': f"{date}に開催された{committee}会議では、{len(parties)}政党から{speaker_count}名の議員が{speech_count}回の発言を行いました。",
            'key_points': [
                f"主要参加政党: {', '.join(parties[:3])}",
                f"発言者数: {speaker_count}名",
                f"総発言回数: {speech_count}回",
                "詳細な議論内容は元データをご参照ください。"
            ],
            'conclusion': "会議は予定通り進行し、各党から活発な議論が行われました。",
            'participants': {
                'speakers': meeting_info['speakers'][:10],  # 上位10名
                'parties': parties
            },
            'metadata': {
                'summary_type': 'mock',
                'model': 'statistical_analysis',
                'generated_at': datetime.now().isoformat()
            }
        }
        
        return summary
    
    def _generate_ollama_summary(self, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """Ollama LLMを使用した要約生成"""
        try:
            import requests
            
            prompt = self._create_summary_prompt(meeting_info)
            
            # Ollama API呼び出し
            ollama_url = "http://localhost:11434/api/generate"
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 1000
                }
            }
            
            response = requests.post(ollama_url, json=payload, timeout=60)
            response.raise_for_status()
            
            result = response.json()
            summary_text = result.get('response', '')
            
            return self._parse_llm_summary(summary_text, meeting_info, 'ollama')
            
        except Exception as e:
            logger.error(f"Ollama要約生成エラー: {e}")
            return self._generate_mock_summary(meeting_info)
    
    def _generate_openai_summary(self, meeting_info: Dict[str, Any]) -> Dict[str, Any]:
        """OpenAI APIを使用した要約生成"""
        try:
            import openai
            
            if not self.openai_api_key:
                logger.warning("OpenAI APIキーが設定されていません。モック要約を生成します。")
                return self._generate_mock_summary(meeting_info)
            
            openai.api_key = self.openai_api_key
            prompt = self._create_summary_prompt(meeting_info)
            
            response = openai.ChatCompletion.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": "あなたは国会議事録の要約を生成する専門アシスタントです。"},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.3
            )
            
            summary_text = response.choices[0].message.content
            return self._parse_llm_summary(summary_text, meeting_info, 'openai')
            
        except Exception as e:
            logger.error(f"OpenAI要約生成エラー: {e}")
            return self._generate_mock_summary(meeting_info)
    
    def _create_summary_prompt(self, meeting_info: Dict[str, Any]) -> str:
        """要約生成用プロンプトを作成"""
        prompt = f"""
以下の国会{meeting_info['committee']}会議（{meeting_info['date']}）の議事録を要約してください。

会議情報:
- 日付: {meeting_info['date']}
- 委員会: {meeting_info['committee']}
- 院: {meeting_info['house']}
- 発言者数: {len(meeting_info['speakers'])}名
- 参加政党: {', '.join(meeting_info['parties'])}

議事録内容:
{meeting_info['full_text'][:6000]}

以下の形式で要約を作成してください:

【会議概要】
(2-3行で会議の全体的な内容を説明)

【主要議論ポイント】
1. (第1の重要ポイント)
2. (第2の重要ポイント)
3. (第3の重要ポイント)

【結論・決議事項】
(会議の結論や決定事項があれば記載、なければ主要な合意点)

簡潔で分かりやすい日本語で記述してください。
        """
        return prompt.strip()
    
    def _parse_llm_summary(self, summary_text: str, meeting_info: Dict[str, Any], model_type: str) -> Dict[str, Any]:
        """LLM生成の要約テキストを構造化"""
        # 簡単な構造化（実際はより高度なパースが必要）
        sections = summary_text.split('【')
        
        overview = ""
        key_points = []
        conclusion = ""
        
        for section in sections:
            if '会議概要】' in section:
                overview = section.split('】')[1].strip()
            elif '主要議論ポイント】' in section:
                points_text = section.split('】')[1].strip()
                key_points = [p.strip() for p in points_text.split('\n') if p.strip() and ('1.' in p or '2.' in p or '3.' in p)]
            elif '結論' in section or '決議事項】' in section:
                conclusion = section.split('】')[1].strip()
        
        # フォールバック
        if not overview:
            overview = summary_text[:200] + "..."
        if not key_points:
            key_points = ["詳細な議論が行われました。", "各党から様々な意見が提示されました。"]
        if not conclusion:
            conclusion = "会議は予定通り終了しました。"
        
        summary = {
            'title': f"{meeting_info['date']} {meeting_info['committee']}会議要約",
            'overview': overview,
            'key_points': key_points,
            'conclusion': conclusion,
            'participants': {
                'speakers': meeting_info['speakers'],
                'parties': meeting_info['parties']
            },
            'metadata': {
                'summary_type': 'llm_generated',
                'model': f"{model_type}_{self.model_name}",
                'generated_at': datetime.now().isoformat(),
                'original_speech_count': meeting_info['speech_count']
            }
        }
        
        return summary
    
    def save_summaries(self, summaries: List[Dict[str, Any]]):
        """生成された要約を保存"""
        if not summaries:
            logger.warning("保存する要約がありません")
            return
        
        # ファイル名生成
        current_date = datetime.now()
        timestamp = current_date.strftime('%Y%m%d_%H%M%S')
        filename = f"meeting_summaries_{timestamp}.json"
        filepath = self.summaries_dir / filename
        
        # 要約データの保存
        summary_data = {
            "metadata": {
                "generated_at": current_date.isoformat(),
                "total_summaries": len(summaries),
                "llm_type": self.llm_type,
                "model": self.model_name,
                "version": "1.0"
            },
            "summaries": summaries
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        file_size = filepath.stat().st_size / (1024 * 1024)
        logger.info(f"要約データ保存完了:")
        logger.info(f"  - ファイル: {filepath}")
        logger.info(f"  - サイズ: {file_size:.1f} MB")
        logger.info(f"  - 要約数: {len(summaries)}件")
        
        # 統計表示
        self.display_summary_stats(summaries)
        
        # インデックスファイル更新
        self.update_summaries_index()
    
    def display_summary_stats(self, summaries: List[Dict[str, Any]]):
        """要約統計を表示"""
        logger.info("\n📊 会議要約生成統計:")
        
        # 委員会別集計
        committee_counts = defaultdict(int)
        for summary in summaries:
            title = summary.get('title', '')
            # タイトルから委員会名を抽出
            for committee in ['本会議', '予算委員会', '外務委員会', '文教科学委員会', '厚生労働委員会']:
                if committee in title:
                    committee_counts[committee] += 1
                    break
            else:
                committee_counts['その他'] += 1
        
        logger.info("委員会別要約数:")
        for committee, count in committee_counts.items():
            logger.info(f"  {committee}: {count}件")
        
        # 平均統計
        total_speakers = sum(len(s.get('participants', {}).get('speakers', [])) for s in summaries)
        avg_speakers = total_speakers / len(summaries) if summaries else 0
        
        logger.info(f"\n平均発言者数: {avg_speakers:.1f}名/会議")
        logger.info(f"使用モデル: {self.model_name}")
    
    def update_summaries_index(self):
        """要約ファイルのインデックスを更新"""
        try:
            # summariesディレクトリ内のJSONファイルを取得
            summary_files = []
            if self.summaries_dir.exists():
                for file_path in self.summaries_dir.glob("summary_*.json"):
                    summary_files.append(file_path.name)
            
            # 日付順でソート（新しい順）
            summary_files.sort(key=lambda x: x, reverse=True)
            
            # インデックスデータ作成
            index_data = {
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "total_files": len(summary_files),
                    "description": "Summary files index for dynamic loading"
                },
                "files": summary_files
            }
            
            # インデックスファイル保存
            index_path = self.summaries_dir / "summaries_index.json"
            with open(index_path, 'w', encoding='utf-8') as f:
                json.dump(index_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"📁 要約インデックス更新完了: {len(summary_files)}ファイル")
            logger.info(f"  - インデックスファイル: {index_path}")
            
        except Exception as e:
            logger.error(f"インデックス更新エラー: {e}")

def main():
    """メイン実行関数"""
    logger.info("🚀 会議要約生成開始 (Issue #21)")
    
    generator = MeetingSummaryGenerator()
    
    try:
        # テストモード: 環境変数で制限数を指定可能
        test_limit = os.getenv('TEST_LIMIT')
        speech_limit = int(test_limit) if test_limit else None
        
        # 議事録データ読み込み
        speeches = generator.load_speech_data(limit=speech_limit)
        
        if not speeches:
            logger.error("議事録データが取得できませんでした")
            return
        
        # 会議別グループ化
        meetings = generator.group_speeches_by_meeting(speeches)
        
        if not meetings:
            logger.error("要約対象の会議が見つかりませんでした")
            return
        
        # 要約生成
        logger.info(f"要約生成開始: {len(meetings)}件の会議")
        summaries = []
        
        for meeting_key, meeting_speeches in list(meetings.items())[:5]:  # 最初の5会議をテスト
            logger.info(f"要約生成中: {meeting_key}")
            
            meeting_info = generator.prepare_meeting_text(meeting_speeches)
            summary = generator.generate_summary_with_llm(meeting_info)
            summaries.append(summary)
        
        # 要約保存
        generator.save_summaries(summaries)
        
        logger.info("✨ 会議要約生成処理完了 (Issue #21)")
        
    except Exception as e:
        logger.error(f"メイン処理エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()