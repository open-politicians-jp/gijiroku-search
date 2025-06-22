#!/usr/bin/env python3
"""
議会単位要約システム

議事録データを議会（会議）単位でグループ化し、
軽量LLMを使用して議会の要約を生成する

機能:
- 議会単位でのデータグループ化（日付+院+委員会）
- Llama3.2:3bを使用した要約生成
- 要約データの専用ディレクトリ保存
- 既存データとのリンク情報追加
"""

import json
import time
import os
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class MeetingSummarizer:
    """議会単位要約クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.speeches_dir = self.project_root / "frontend" / "public" / "data" / "speeches"
        self.summaries_dir = self.project_root / "frontend" / "public" / "data" / "summaries"
        self.summaries_dir.mkdir(parents=True, exist_ok=True)
        
        # Ollama設定（テスト結果からLlama3.2:3bを使用）
        self.ollama_url = "http://localhost:11434/api/generate"
        self.model_name = "llama3.2:3b"
        
        # 要約設定
        self.max_meeting_speeches = 50  # 1議会あたりの最大発言数
        self.max_text_length = 8000     # 要約対象テキストの最大長
        
    def check_ollama_availability(self) -> bool:
        """Ollama接続確認"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                models = [model['name'] for model in response.json().get('models', [])]
                if self.model_name in models:
                    logger.info(f"✅ Ollama利用可能 - {self.model_name}モデル確認")
                    return True
                else:
                    logger.error(f"❌ {self.model_name}モデルが見つかりません")
                    logger.info(f"利用可能モデル: {', '.join(models)}")
                    return False
            return False
        except Exception as e:
            logger.error(f"❌ Ollama接続失敗: {e}")
            return False
    
    def load_speeches_data(self, target_month: str = "2025-06") -> List[Dict[str, Any]]:
        """指定月の議事録データ読み込み"""
        logger.info(f"📄 {target_month}の議事録データ読み込み中...")
        
        all_speeches = []
        speech_files = list(self.speeches_dir.glob(f"speeches_{target_month.replace('-', '')}*.json"))
        
        if not speech_files:
            logger.warning(f"⚠️ {target_month}のデータファイルが見つかりません")
            return []
        
        for file_path in speech_files:
            try:
                logger.info(f"読み込み中: {file_path.name}")
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    speeches = data.get('data', []) if isinstance(data, dict) else data
                    all_speeches.extend(speeches)
                    
            except Exception as e:
                logger.error(f"❌ ファイル読み込みエラー {file_path}: {e}")
                continue
        
        logger.info(f"✅ {len(all_speeches)}件の発言データを読み込み")
        return all_speeches
    
    def group_speeches_by_meeting(self, speeches: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """議会（会議）単位でのデータグループ化"""
        logger.info("🗂️ 議会単位でのデータグループ化中...")
        
        meetings = defaultdict(lambda: {
            'speeches': [],
            'meeting_info': {},
            'speakers': set(),
            'parties': set()
        })
        
        for speech in speeches:
            # 議会キー生成（日付+院+委員会）
            meeting_key = f"{speech.get('date', 'unknown')}_{speech.get('house', 'unknown')}_{speech.get('committee', '本会議')}"
            
            meetings[meeting_key]['speeches'].append(speech)
            meetings[meeting_key]['speakers'].add(speech.get('speaker', '不明'))
            if speech.get('party'):
                meetings[meeting_key]['parties'].add(speech.get('party'))
            
            # 会議基本情報を初回のみ設定
            if not meetings[meeting_key]['meeting_info']:
                meetings[meeting_key]['meeting_info'] = {
                    'date': speech.get('date', 'unknown'),
                    'house': speech.get('house', 'unknown'),
                    'committee': speech.get('committee', '本会議'),
                    'session': speech.get('session', 0),
                    'meeting_key': meeting_key
                }
        
        # set を list に変換
        for meeting_key in meetings:
            meetings[meeting_key]['speakers'] = list(meetings[meeting_key]['speakers'])
            meetings[meeting_key]['parties'] = list(meetings[meeting_key]['parties'])
            meetings[meeting_key]['speech_count'] = len(meetings[meeting_key]['speeches'])
        
        logger.info(f"✅ {len(meetings)}の議会にグループ化完了")
        for meeting_key, meeting_data in meetings.items():
            logger.info(f"  📋 {meeting_key}: {meeting_data['speech_count']}発言, {len(meeting_data['speakers'])}名")
        
        return dict(meetings)
    
    def prepare_meeting_text_for_summary(self, meeting_data: Dict[str, Any]) -> str:
        """議会テキストを要約用に準備"""
        speeches = meeting_data['speeches'][:self.max_meeting_speeches]  # 発言数制限
        text_parts = []
        
        for speech in speeches:
            speaker = speech.get('speaker', '不明')
            party = speech.get('party', '')
            party_info = f"({party})" if party else ""
            text = speech.get('text', '')
            
            if len(text.strip()) > 30:  # 短すぎる発言は除外
                # 発言テキストを整形
                clean_text = text.replace('○', '').replace('君）', '）').strip()
                text_parts.append(f"【{speaker}{party_info}】{clean_text}")
        
        full_text = '\n\n'.join(text_parts)
        
        # 長すぎる場合は制限
        if len(full_text) > self.max_text_length:
            full_text = full_text[:self.max_text_length] + '\n[...以下省略...]'
            logger.info(f"⚠️ テキスト長制限: {self.max_text_length}文字に切り詰め")
        
        return full_text
    
    def create_meeting_summary_prompt(self, meeting_info: Dict[str, Any], meeting_text: str) -> str:
        """議会要約用プロンプト作成"""
        prompt = f"""以下の{meeting_info['house']}{meeting_info['committee']}会議（{meeting_info['date']}）の議事録を要約してください。

会議情報:
- 日付: {meeting_info['date']}
- 院: {meeting_info['house']}
- 委員会: {meeting_info['committee']}
- 会期: 第{meeting_info['session']}回国会

議事録内容:
{meeting_text}

以下の形式で簡潔に要約してください:

【会議概要】
(この会議の目的と主要な議題を2-3行で説明)

【主要な議論・審議内容】
1. (第1の重要な議論内容)
2. (第2の重要な議論内容)
3. (第3の重要な議論内容)

【決定事項・結論】
(会議で決定された事項や主要な結論)

【発言者・政党】
(主要な発言者と所属政党)

【備考】
(その他の重要な情報や特記事項)

要約は正確で分かりやすい日本語で記述してください。"""
        
        return prompt
    
    def generate_meeting_summary(self, meeting_info: Dict[str, Any], meeting_text: str) -> Optional[str]:
        """議会要約生成"""
        meeting_key = meeting_info['meeting_key']
        logger.info(f"🧠 {meeting_key} の要約生成開始...")
        
        try:
            prompt = self.create_meeting_summary_prompt(meeting_info, meeting_text)
            
            payload = {
                "model": self.model_name,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 1500,
                    "num_predict": 1500
                }
            }
            
            start_time = time.time()
            response = requests.post(self.ollama_url, json=payload, timeout=300)
            response.raise_for_status()
            end_time = time.time()
            
            result = response.json()
            summary = result.get('response', '')
            
            processing_time = round(end_time - start_time, 2)
            logger.info(f"✅ {meeting_key} 要約完了 ({processing_time}秒)")
            logger.info(f"📊 要約長: {len(summary)}文字")
            
            return summary
            
        except Exception as e:
            logger.error(f"❌ {meeting_key} 要約生成失敗: {e}")
            return None
    
    def save_meeting_summary(self, meeting_key: str, meeting_info: Dict[str, Any], 
                           meeting_data: Dict[str, Any], summary: str):
        """議会要約データ保存"""
        
        # 要約ファイル名生成
        date_str = meeting_info['date'].replace('-', '')
        house_short = meeting_info['house'][:2]  # 衆議院→衆議, 参議院→参議
        committee_short = meeting_info['committee'][:10]  # 委員会名を短縮
        
        filename = f"summary_{date_str}_{house_short}_{committee_short}.json"
        filepath = self.summaries_dir / filename
        
        # 要約データ構造
        summary_data = {
            "metadata": {
                "summary_type": "meeting_summary",
                "meeting_key": meeting_key,
                "generated_at": datetime.now().isoformat(),
                "model_used": self.model_name,
                "speech_count": meeting_data['speech_count'],
                "speakers_count": len(meeting_data['speakers']),
                "parties_count": len(meeting_data['parties'])
            },
            "meeting_info": meeting_info,
            "summary": {
                "text": summary,
                "length": len(summary),
                "keywords": self.extract_keywords_from_summary(summary)
            },
            "participants": {
                "speakers": meeting_data['speakers'],
                "parties": meeting_data['parties']
            },
            "speeches_references": [
                {
                    "speech_id": speech.get('id'),
                    "speaker": speech.get('speaker'),
                    "url": speech.get('url')
                }
                for speech in meeting_data['speeches'][:10]  # 最初の10発言のリンク
            ]
        }
        
        # ファイル保存
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 要約保存完了: {filename}")
        return filepath
    
    def extract_keywords_from_summary(self, summary: str) -> List[str]:
        """要約からキーワード抽出（簡易版）"""
        # 簡易キーワード抽出（実際にはより高度な形態素解析を使用可能）
        keywords = []
        
        # 政策関連キーワード
        policy_keywords = ['法案', '改正', '予算', '税制', '年金', '医療', '教育', '経済', '外交', '防衛', '環境']
        for keyword in policy_keywords:
            if keyword in summary:
                keywords.append(keyword)
        
        # 手続き関連キーワード
        procedure_keywords = ['審議', '質疑', '採決', '可決', '否決', '継続', '委員会', '本会議']
        for keyword in procedure_keywords:
            if keyword in summary:
                keywords.append(keyword)
        
        return list(set(keywords))  # 重複除去
    
    def summarize_meetings(self, target_month: str = "2025-06", limit: int = None) -> Dict[str, Any]:
        """メイン要約処理"""
        logger.info(f"🚀 {target_month}議会要約処理開始")
        
        if not self.check_ollama_availability():
            return {'error': 'Ollama not available'}
        
        # データ読み込み
        speeches = self.load_speeches_data(target_month)
        if not speeches:
            return {'error': 'No speech data found'}
        
        # 議会単位グループ化
        meetings = self.group_speeches_by_meeting(speeches)
        
        # 制限がある場合は最初のN個のみ処理
        if limit:
            meeting_keys = list(meetings.keys())[:limit]
            meetings = {k: meetings[k] for k in meeting_keys}
            logger.info(f"📋 処理制限: {limit}議会のみ処理")
        
        # 各議会の要約生成
        results = {
            'target_month': target_month,
            'total_meetings': len(meetings),
            'processed_meetings': 0,
            'successful_summaries': 0,
            'failed_summaries': 0,
            'processing_details': []
        }
        
        for meeting_key, meeting_data in meetings.items():
            try:
                meeting_info = meeting_data['meeting_info']
                meeting_text = self.prepare_meeting_text_for_summary(meeting_data)
                
                logger.info(f"📝 処理中: {meeting_key} ({meeting_data['speech_count']}発言)")
                
                # 要約生成
                summary = self.generate_meeting_summary(meeting_info, meeting_text)
                
                if summary:
                    # 要約保存
                    summary_file = self.save_meeting_summary(meeting_key, meeting_info, meeting_data, summary)
                    results['successful_summaries'] += 1
                    results['processing_details'].append({
                        'meeting_key': meeting_key,
                        'status': 'success',
                        'summary_file': str(summary_file),
                        'speech_count': meeting_data['speech_count']
                    })
                else:
                    results['failed_summaries'] += 1
                    results['processing_details'].append({
                        'meeting_key': meeting_key,
                        'status': 'failed',
                        'error': 'Summary generation failed'
                    })
                
                results['processed_meetings'] += 1
                
                # 処理間隔（APIレート制限対応）
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"❌ {meeting_key} 処理エラー: {e}")
                results['failed_summaries'] += 1
                results['processing_details'].append({
                    'meeting_key': meeting_key,
                    'status': 'error',
                    'error': str(e)
                })
        
        # 結果サマリー
        logger.info("=" * 60)
        logger.info(f"📊 {target_month}議会要約処理完了")
        logger.info(f"✅ 成功: {results['successful_summaries']}/{results['total_meetings']}議会")
        logger.info(f"❌ 失敗: {results['failed_summaries']}/{results['total_meetings']}議会")
        logger.info("=" * 60)
        
        return results

def main():
    """メイン実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='議会単位要約システム')
    parser.add_argument('--month', default='2025-06', help='対象月 (YYYY-MM)')
    parser.add_argument('--limit', type=int, help='処理議会数制限（テスト用）')
    parser.add_argument('--test', action='store_true', help='テストモード（limit=2）')
    
    args = parser.parse_args()
    
    if args.test:
        args.limit = 2
        logger.info("🧪 テストモード: 最初の2議会のみ処理")
    
    summarizer = MeetingSummarizer()
    results = summarizer.summarize_meetings(args.month, args.limit)
    
    if 'error' in results:
        logger.error(f"❌ 処理失敗: {results['error']}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())