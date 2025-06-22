#!/usr/bin/env python3
"""
軽量LLM要約テスト・検証スクリプト

GitHub Actions環境での軽量モデル動作確認と要約品質評価
- Phi-3.5 Mini, Qwen2.5, Llama3.2の比較テスト
- 一つの会議データでの詳細検証
- メモリ使用量・処理時間の計測
"""

import json
import time
import psutil
import requests
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List
import logging

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class LLMSummarizationTester:
    """軽量LLM要約テスト・検証クラス"""
    
    def __init__(self):
        self.project_root = Path(__file__).parent.parent.parent
        self.speeches_dir = self.project_root / "frontend" / "public" / "data" / "speeches"
        self.test_results_dir = self.project_root / "data" / "test_results"
        self.test_results_dir.mkdir(parents=True, exist_ok=True)
        
        # テスト対象モデル（軽量優先）
        self.test_models = [
            {
                'name': 'phi3.5',
                'size': '3.8B',
                'description': 'Microsoft Phi-3.5 Mini (最軽量)',
                'ollama_model': 'phi3.5:latest'
            },
            {
                'name': 'qwen2.5:3b',
                'size': '3B',
                'description': 'Qwen 2.5 3B (日本語強化)',
                'ollama_model': 'qwen2.5:3b'
            },
            {
                'name': 'llama3.2:3b',
                'size': '3B', 
                'description': 'Llama 3.2 3B (バランス型)',
                'ollama_model': 'llama3.2:3b'
            }
        ]
        
        # Ollama設定
        self.ollama_url = "http://localhost:11434/api/generate"
        self.ollama_available = self.check_ollama_availability()
        
    def check_ollama_availability(self) -> bool:
        """Ollama接続確認"""
        try:
            response = requests.get("http://localhost:11434/api/tags", timeout=5)
            if response.status_code == 200:
                available_models = [model['name'] for model in response.json().get('models', [])]
                logger.info(f"✅ Ollama利用可能、モデル数: {len(available_models)}")
                logger.info(f"利用可能モデル: {', '.join(available_models[:5])}")
                return True
            else:
                logger.warning("⚠️ Ollama接続失敗")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Ollama未起動: {e}")
            return False
    
    def get_sample_meeting_data(self) -> Optional[Dict[str, Any]]:
        """サンプル会議データを取得"""
        logger.info("📄 サンプル会議データ読み込み中...")
        
        # 最新のスピーチファイルを取得
        speech_files = list(self.speeches_dir.glob("speeches_*.json"))
        if not speech_files:
            logger.error("❌ 議事録ファイルが見つかりません")
            return None
        
        latest_file = sorted(speech_files)[-1]
        logger.info(f"使用ファイル: {latest_file}")
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                speeches = data if isinstance(data, list) else data.get('data', [])
                
                # 最初の会議データを抽出
                if speeches:
                    first_speech = speeches[0]
                    meeting_key = f"{first_speech.get('date', 'unknown')}_{first_speech.get('house', 'unknown')}_{first_speech.get('committee', '本会議')}"
                    
                    # 同じ会議の全発言を収集
                    meeting_speeches = []
                    for speech in speeches:
                        speech_key = f"{speech.get('date', 'unknown')}_{speech.get('house', 'unknown')}_{speech.get('committee', '本会議')}"
                        if speech_key == meeting_key:
                            meeting_speeches.append(speech)
                        if len(meeting_speeches) >= 20:  # テスト用に制限
                            break
                    
                    meeting_info = {
                        'key': meeting_key,
                        'date': first_speech.get('date', 'unknown'),
                        'house': first_speech.get('house', 'unknown'),
                        'committee': first_speech.get('committee', '本会議'),
                        'speeches': meeting_speeches,
                        'speech_count': len(meeting_speeches),
                        'speakers': list(set(s.get('speaker', '不明') for s in meeting_speeches)),
                        'parties': list(set(s.get('party', '不明') for s in meeting_speeches if s.get('party')))
                    }
                    
                    logger.info(f"✅ サンプル会議: {meeting_key}")
                    logger.info(f"📊 発言数: {len(meeting_speeches)}、発言者: {len(meeting_info['speakers'])}名")
                    return meeting_info
                else:
                    logger.error("❌ 議事録データが空です")
                    return None
                    
        except Exception as e:
            logger.error(f"❌ データ読み込みエラー: {e}")
            return None
    
    def prepare_meeting_text(self, meeting_info: Dict[str, Any]) -> str:
        """会議テキストを要約用に準備"""
        speeches = meeting_info['speeches']
        text_parts = []
        
        for speech in speeches[:15]:  # テスト用に発言数制限
            speaker = speech.get('speaker', '不明')
            party = speech.get('party', '不明')
            text = speech.get('text', '')
            
            if len(text.strip()) > 20:  # 短すぎる発言は除外
                text_parts.append(f"【{speaker}({party})】{text[:800]}")
        
        full_text = '\n\n'.join(text_parts)
        
        # 長すぎる場合は制限（軽量モデル対応）
        if len(full_text) > 6000:
            full_text = full_text[:6000] + '...'
        
        return full_text
    
    def create_japanese_prompt(self, meeting_info: Dict[str, Any], meeting_text: str) -> str:
        """日本語特化プロンプト作成"""
        prompt = f"""以下の国会{meeting_info['committee']}会議（{meeting_info['date']}）の議事録を簡潔に要約してください。

会議情報:
- 日付: {meeting_info['date']}
- 委員会: {meeting_info['committee']}  
- 院: {meeting_info['house']}
- 発言者数: {len(meeting_info['speakers'])}名
- 参加政党: {', '.join(meeting_info['parties'][:5])}

議事録内容:
{meeting_text}

以下の形式で要約してください:

【会議概要】
(この会議で何が議論されたかを2-3行で説明)

【主要議論ポイント】
1. (第1の重要な議論内容)
2. (第2の重要な議論内容) 
3. (第3の重要な議論内容)

【結論・合意事項】
(会議の結論や決定事項、なければ主要な合意点)

簡潔で分かりやすい日本語で記述してください。"""
        
        return prompt
    
    def test_model_summary(self, model_info: Dict[str, str], meeting_info: Dict[str, Any], meeting_text: str) -> Dict[str, Any]:
        """個別モデルでの要約テスト"""
        model_name = model_info['name']
        logger.info(f"🧪 {model_name} 要約テスト開始...")
        
        # メモリ使用量測定開始
        process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB
        
        start_time = time.time()
        
        try:
            prompt = self.create_japanese_prompt(meeting_info, meeting_text)
            
            # Ollama API呼び出し
            payload = {
                "model": model_info['ollama_model'],
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 1000,
                    "num_predict": 1000
                }
            }
            
            response = requests.post(self.ollama_url, json=payload, timeout=300)  # 5分タイムアウト
            response.raise_for_status()
            
            result = response.json()
            summary_text = result.get('response', '')
            
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024  # MB
            
            # 要約品質評価
            quality_score = self.evaluate_summary_quality(summary_text, meeting_info)
            
            test_result = {
                'model': model_name,
                'model_info': model_info,
                'success': True,
                'summary': summary_text,
                'processing_time': round(end_time - start_time, 2),
                'memory_usage': round(memory_after - memory_before, 2),
                'memory_peak': round(memory_after, 2),
                'quality_score': quality_score,
                'summary_length': len(summary_text),
                'tested_at': datetime.now().isoformat()
            }
            
            logger.info(f"✅ {model_name} 要約完了:")
            logger.info(f"   ⏱️ 処理時間: {test_result['processing_time']}秒")
            logger.info(f"   🧠 メモリ使用: {test_result['memory_usage']}MB")
            logger.info(f"   📊 品質スコア: {quality_score}/10")
            
            return test_result
            
        except Exception as e:
            end_time = time.time()
            memory_after = process.memory_info().rss / 1024 / 1024
            
            logger.error(f"❌ {model_name} 要約失敗: {str(e)}")
            
            return {
                'model': model_name,
                'model_info': model_info,
                'success': False,
                'error': str(e),
                'processing_time': round(end_time - start_time, 2),
                'memory_usage': round(memory_after - memory_before, 2),
                'tested_at': datetime.now().isoformat()
            }
    
    def evaluate_summary_quality(self, summary: str, meeting_info: Dict[str, Any]) -> int:
        """要約品質評価（1-10点）"""
        score = 0
        
        # 基本構造チェック
        if '【会議概要】' in summary:
            score += 2
        if '【主要議論ポイント】' in summary:
            score += 2
        if '【結論' in summary or '【合意事項】' in summary:
            score += 2
        
        # 内容の充実度
        if len(summary) > 200:
            score += 1
        if len(summary) > 400:
            score += 1
        
        # 日本語の自然さ（簡易チェック）
        if '。' in summary and '、' in summary:
            score += 1
        
        # 会議情報の含有
        if meeting_info['committee'] in summary:
            score += 1
        
        return min(score, 10)
    
    def run_comparison_test(self) -> Dict[str, Any]:
        """全モデル比較テスト実行"""
        logger.info("🚀 軽量LLM要約比較テスト開始")
        
        if not self.ollama_available:
            logger.error("❌ Ollama未起動のためテスト中止")
            return {'error': 'Ollama not available'}
        
        # サンプルデータ準備
        meeting_info = self.get_sample_meeting_data()
        if not meeting_info:
            return {'error': 'No meeting data available'}
        
        meeting_text = self.prepare_meeting_text(meeting_info)
        
        logger.info(f"📋 テスト対象会議: {meeting_info['key']}")
        logger.info(f"📄 入力テキスト長: {len(meeting_text)}文字")
        
        # 各モデルでテスト実行
        test_results = []
        for model_info in self.test_models:
            result = self.test_model_summary(model_info, meeting_info, meeting_text)
            test_results.append(result)
            
            # メモリクリーンアップのため少し待機
            time.sleep(2)
        
        # 結果まとめ
        comparison_result = {
            'test_overview': {
                'meeting_key': meeting_info['key'],
                'input_length': len(meeting_text),
                'models_tested': len(test_results),
                'successful_tests': sum(1 for r in test_results if r.get('success', False)),
                'tested_at': datetime.now().isoformat()
            },
            'meeting_info': meeting_info,
            'model_results': test_results,
            'recommendations': self.generate_recommendations(test_results)
        }
        
        # 結果保存
        self.save_test_results(comparison_result)
        
        return comparison_result
    
    def generate_recommendations(self, test_results: List[Dict[str, Any]]) -> Dict[str, str]:
        """テスト結果基準の推奨事項生成"""
        successful_results = [r for r in test_results if r.get('success', False)]
        
        if not successful_results:
            return {'status': 'No successful tests', 'recommendation': 'Check Ollama setup and model availability'}
        
        # 性能評価
        best_speed = min(successful_results, key=lambda x: x.get('processing_time', float('inf')))
        best_memory = min(successful_results, key=lambda x: x.get('memory_usage', float('inf')))
        best_quality = max(successful_results, key=lambda x: x.get('quality_score', 0))
        
        recommendations = {
            'fastest_model': f"{best_speed['model']} ({best_speed['processing_time']}秒)",
            'most_memory_efficient': f"{best_memory['model']} ({best_memory['memory_usage']}MB)",
            'highest_quality': f"{best_quality['model']} (品質: {best_quality['quality_score']}/10)",
            'overall_recommendation': self.select_best_overall_model(successful_results)
        }
        
        return recommendations
    
    def select_best_overall_model(self, results: List[Dict[str, Any]]) -> str:
        """総合評価で最適モデル選定"""
        if not results:
            return "No successful models"
        
        # 重み付きスコア計算（品質40%、速度30%、メモリ30%）
        scored_results = []
        max_quality = max(r.get('quality_score', 0) for r in results)
        min_time = min(r.get('processing_time', float('inf')) for r in results)
        min_memory = min(r.get('memory_usage', float('inf')) for r in results)
        
        for result in results:
            quality_score = (result.get('quality_score', 0) / max_quality) * 0.4 if max_quality > 0 else 0
            speed_score = (min_time / result.get('processing_time', float('inf'))) * 0.3
            memory_score = (min_memory / result.get('memory_usage', float('inf'))) * 0.3
            
            total_score = quality_score + speed_score + memory_score
            scored_results.append((result['model'], total_score))
        
        best_model = max(scored_results, key=lambda x: x[1])
        return f"{best_model[0]} (総合スコア: {best_model[1]:.3f})"
    
    def save_test_results(self, results: Dict[str, Any]):
        """テスト結果保存"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"llm_comparison_test_{timestamp}.json"
        filepath = self.test_results_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"💾 テスト結果保存: {filepath}")
        
        # サマリー表示
        self.display_test_summary(results)
    
    def display_test_summary(self, results: Dict[str, Any]):
        """テスト結果サマリー表示"""
        logger.info("\n" + "="*60)
        logger.info("📊 軽量LLM要約テスト結果サマリー")
        logger.info("="*60)
        
        overview = results['test_overview']
        logger.info(f"🎯 テスト対象: {overview['meeting_key']}")
        logger.info(f"📝 入力長: {overview['input_length']}文字")
        logger.info(f"✅ 成功: {overview['successful_tests']}/{overview['models_tested']}モデル")
        
        logger.info("\n📈 モデル別結果:")
        for result in results['model_results']:
            if result.get('success'):
                logger.info(f"  {result['model']}: 品質{result['quality_score']}/10, {result['processing_time']}秒, {result['memory_usage']}MB")
            else:
                logger.info(f"  {result['model']}: ❌ {result.get('error', 'Unknown error')}")
        
        logger.info("\n🏆 推奨事項:")
        recommendations = results['recommendations']
        for key, value in recommendations.items():
            logger.info(f"  {key}: {value}")
        
        logger.info("="*60)

def main():
    """メイン実行関数"""
    logger.info("🧪 軽量LLM要約品質・性能テスト開始")
    
    tester = LLMSummarizationTester()
    
    try:
        results = tester.run_comparison_test()
        
        if 'error' in results:
            logger.error(f"❌ テスト失敗: {results['error']}")
            return
        
        logger.info("✨ 軽量LLM要約テスト完了")
        
    except Exception as e:
        logger.error(f"❌ テスト実行エラー: {str(e)}")
        raise

if __name__ == "__main__":
    main()