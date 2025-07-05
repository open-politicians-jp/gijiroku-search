'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, ExternalLink, Users, Calendar, FileText, BookOpen, Target, Loader2 } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';

interface LLMSummary {
  party: string;
  title: string;
  url: string;
  basic_theme: string;
  target_voters: string[];
  key_policies: string[];
  policy_details: {
    [key: string]: {
      content: string[];
      key_points: string[];
    }
  };
}

interface LLMSummariesData {
  metadata: {
    title: string;
    description: string;
    generated_at: string;
    llm_model: string;
  };
  summaries: {
    [key: string]: LLMSummary;
  };
}

export default function LLMManifestosPage() {
  const [llmData, setLlmData] = useState<LLMSummariesData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLlmSummaries = async () => {
      try {
        setLoading(true);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const dataUrl = `${basePath}/data/llm_summaries.json`;
        
        const response = await fetch(dataUrl);
        
        if (!response.ok) {
          throw new Error(`LLM要約データの取得に失敗しました (HTTP ${response.status})`);
        }
        
        const data = await response.json();
        setLlmData(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';
        
        // GitHub Pages でのデータ読み込み失敗の場合、代替手段を試行
        if (errorMessage.includes('404') || errorMessage.includes('Failed to fetch')) {
          try {
            // 代替パスでの試行
            const altResponse = await fetch('./data/llm_summaries.json');
            if (altResponse.ok) {
              const altData = await altResponse.json();
              setLlmData(altData);
              setLoading(false);
              return;
            }
          } catch (altErr) {
            // 代替手段も失敗した場合は元のエラーを表示
          }
        }
        
        setError(`データ読み込みエラー: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    loadLlmSummaries();
  }, []);

  const getPartyColor = (party: string) => {
    const colors: { [key: string]: string } = {
      '自由民主党': 'bg-red-50 border-red-200 text-red-900',
      '公明党': 'bg-yellow-50 border-yellow-200 text-yellow-900',
      '立憲民主党': 'bg-blue-50 border-blue-200 text-blue-900',
      '日本維新の会': 'bg-orange-50 border-orange-200 text-orange-900',
      '参政党': 'bg-indigo-50 border-indigo-200 text-indigo-900',
      '国民民主党': 'bg-green-50 border-green-200 text-green-900',
      'れいわ新選組': 'bg-purple-50 border-purple-200 text-purple-900',
      '日本共産党': 'bg-red-50 border-red-200 text-red-900'
    };
    return colors[party] || 'bg-gray-50 border-gray-200 text-gray-900';
  };

  const getPartySlug = (party: string) => {
    const slugs: { [key: string]: string } = {
      '自由民主党': 'jiyuminshuto',
      '公明党': 'komeito', 
      '立憲民主党': 'rikkenminshuto',
      '日本維新の会': 'nipponishin',
      '参政党': 'sanseito',
      '国民民主党': 'kokuminminshuto',
      'れいわ新選組': 'reiwa',
      '日本共産党': 'kyosanto'
    };
    return slugs[party] || party.toLowerCase();
  };

  if (loading) {
    return (
      <>
        <Header currentPage="manifestos" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
              <p className="text-gray-600">LLMマニフェスト要約を読み込み中...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error || !llmData) {
    return (
      <>
        <Header currentPage="manifestos" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">エラーが発生しました</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <Link
              href="/manifestos"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              マニフェスト一覧に戻る
            </Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header currentPage="manifestos" />
      <div className="container mx-auto px-4 py-8 mt-16">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">AI要約マニフェスト</h1>
          <p className="text-gray-600 mb-4">LLMが各政党のマニフェストを有権者向けに分かりやすく要約しました</p>
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="h-5 w-5 text-blue-600" />
              <h2 className="text-sm font-semibold text-blue-900">AI による自動要約</h2>
            </div>
            <p className="text-sm text-blue-700">
              各政党の公式マニフェストをClaude Code Sonnet4、Gemini 2.5 Proが解析し、有権者にとって分かりやすい形で要約しています。
              詳細は原文もご確認ください。
            </p>
            <div className="mt-2 text-xs text-blue-600">
              生成日時: {new Date(llmData.metadata.generated_at).toLocaleDateString('ja-JP')} | 
              モデル: {llmData.metadata.llm_model}
            </div>
          </div>
        </div>

        {/* マニフェスト要約カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {Object.values(llmData.summaries).map((summary) => (
            <div key={summary.party} className={`bg-white rounded-lg shadow-sm border-2 ${getPartyColor(summary.party)} p-6 hover:shadow-md transition-shadow`}>
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {summary.party}
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  {summary.title}
                </p>
                <p className="text-sm text-gray-700 mb-4 line-clamp-3">
                  {summary.basic_theme}
                </p>
              </div>

              {/* 想定支持層 */}
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-600 mb-2">想定支持層</h4>
                <div className="flex flex-wrap gap-1">
                  {summary.target_voters.slice(0, 3).map((voter, index) => (
                    <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                      {voter}
                    </span>
                  ))}
                </div>
              </div>

              {/* 重点政策 */}
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-600 mb-2">重点政策</h4>
                <ul className="space-y-1">
                  {summary.key_policies.slice(0, 3).map((policy, index) => (
                    <li key={index} className="flex items-center text-xs text-gray-700">
                      <Target className="h-3 w-3 text-blue-600 mr-2 flex-shrink-0" />
                      {policy}
                    </li>
                  ))}
                </ul>
              </div>
              
              <div className="flex flex-col space-y-2">
                <Link
                  href={`/manifestos/llm/${getPartySlug(summary.party)}`}
                  className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                >
                  詳細AI要約を見る
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
                <a
                  href={summary.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center justify-center px-4 py-2 bg-gray-100 text-gray-700 rounded-md hover:bg-gray-200 text-sm font-medium"
                >
                  原文を確認
                  <ExternalLink className="h-4 w-4 ml-1" />
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">AI要約について</h3>
          <p className="text-sm text-gray-600 mb-2">
            この要約は各政党の公式マニフェストをClaude Code Sonnet4、Gemini 2.5 Proが解析して作成したものです。
            政策の詳細や正確な内容については、必ず原文をご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ AI要約は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}