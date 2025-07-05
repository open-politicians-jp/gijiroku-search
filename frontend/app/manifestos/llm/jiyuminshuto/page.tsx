'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, ExternalLink, Users, Target, FileText, Loader2 } from 'lucide-react';
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

export default function JiyuminshutoDetailPage() {
  const partyName = '自由民主党';

  const [llmData, setLlmData] = useState<LLMSummariesData | null>(null);
  const [partySummary, setPartySummary] = useState<LLMSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadPartyDetail = async () => {
      try {
        setLoading(true);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const response = await fetch(`${basePath}/data/llm_summaries.json`);
        
        if (!response.ok) {
          throw new Error(`AI要約データの取得に失敗しました (HTTP ${response.status})`);
        }
        
        const data = await response.json();
        setLlmData(data);
        
        const summary = data.summaries[partyName];
        if (!summary) {
          throw new Error('指定された政党の要約が見つかりませんでした');
        }
        
        setPartySummary(summary);
      } catch (err) {
        console.error('政党詳細データの読み込みエラー:', err);
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    loadPartyDetail();
  }, []);

  const getPartyColor = () => 'bg-red-50 border-red-200 text-red-900';

  if (loading) {
    return (
      <>
        <Header currentPage="manifestos" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="h-12 w-12 animate-spin text-blue-600 mx-auto mb-4" />
              <p className="text-gray-600">{partyName}の詳細情報を読み込み中...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error || !partySummary) {
    return (
      <>
        <Header currentPage="manifestos" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">エラーが発生しました</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <Link
              href="/manifestos/llm"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
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
      <div className="container mx-auto px-4 py-8 mt-16 max-w-4xl">
        {/* ナビゲーション */}
        <div className="mb-6">
          <Link
            href="/manifestos/llm"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            AI要約マニフェスト一覧に戻る
          </Link>
        </div>

        {/* 政党ヘッダー */}
        <div className={`bg-white rounded-lg shadow-sm border-2 ${getPartyColor()} p-6 mb-8`}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{partySummary.party}</h1>
              <h2 className="text-xl text-gray-700 mb-4">{partySummary.title}</h2>
              <p className="text-gray-800 leading-relaxed mb-4">{partySummary.basic_theme}</p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <a
              href={partySummary.url}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              公式サイトを見る
              <ExternalLink className="h-4 w-4 ml-1" />
            </a>
          </div>
        </div>

        {/* 想定支持層 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Users className="h-5 w-5 text-blue-600 mr-2" />
            想定支持層
          </h3>
          <div className="flex flex-wrap gap-2">
            {partySummary.target_voters.map((voter, index) => (
              <span
                key={index}
                className="px-3 py-1 bg-blue-100 text-blue-800 text-sm rounded-full"
              >
                {voter}
              </span>
            ))}
          </div>
        </div>

        {/* 重点政策 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="h-5 w-5 text-green-600 mr-2" />
            重点政策
          </h3>
          <ul className="space-y-2">
            {partySummary.key_policies.map((policy, index) => (
              <li key={index} className="flex items-start">
                <span className="inline-block w-6 h-6 bg-green-100 text-green-800 text-xs rounded-full flex items-center justify-center mr-3 mt-0.5 flex-shrink-0">
                  {index + 1}
                </span>
                <span className="text-gray-800">{policy}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* 政策詳細 */}
        <div className="space-y-6">
          {Object.entries(partySummary.policy_details).map(([category, details]) => (
            <div key={category} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="h-5 w-5 text-orange-600 mr-2" />
                {category}
              </h3>
              
              {/* 重要ポイント */}
              <div className="mb-4">
                <h4 className="text-sm font-semibold text-gray-700 mb-2">重要ポイント</h4>
                <div className="flex flex-wrap gap-2">
                  {details.key_points.map((point, index) => (
                    <span
                      key={index}
                      className="px-2 py-1 bg-orange-100 text-orange-800 text-xs rounded"
                    >
                      {point}
                    </span>
                  ))}
                </div>
              </div>

              {/* 詳細内容 */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 mb-3">詳細政策</h4>
                <ul className="space-y-2">
                  {details.content.map((item, index) => (
                    <li key={index} className="flex items-start text-sm text-gray-700">
                      <span className="inline-block w-1.5 h-1.5 bg-gray-400 rounded-full mr-3 mt-2 flex-shrink-0"></span>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>
            </div>
          ))}
        </div>

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-2">
            この要約は{partySummary.party}の公式マニフェストをClaude Code Sonnet4、Gemini 2.5 Proが解析して作成したものです。
            政策の詳細や正確な内容については、必ず公式サイトをご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ AI要約は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
          {llmData && (
            <p className="text-xs text-gray-500 mt-2">
              生成日時: {new Date(llmData.metadata.generated_at).toLocaleDateString('ja-JP')} | 
              モデル: {llmData.metadata.llm_model}
            </p>
          )}
        </div>
      </div>
    </>
  );
}