'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, ExternalLink, Users, Calendar, FileText, BookOpen, Target, DollarSign, Heart, Shield, Building, Loader2 } from 'lucide-react';
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

export default function JiyuminshutoLLMPage() {
  const [llmData, setLlmData] = useState<LLMSummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLlmSummary = async () => {
      try {
        setLoading(true);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const response = await fetch(`${basePath}/data/manifestos/llm_summaries_2025.json`);
        
        if (!response.ok) {
          throw new Error(`LLM要約データの取得に失敗しました (HTTP ${response.status})`);
        }
        
        const data = await response.json();
        const summary = data.summaries['自由民主党'];
        
        if (!summary) {
          throw new Error('自由民主党の要約データが見つかりません');
        }
        
        setLlmData(summary);
      } catch (err) {
        console.error('LLM要約データの読み込みエラー:', err);
        setError(err instanceof Error ? err.message : '不明なエラーが発生しました');
      } finally {
        setLoading(false);
      }
    };

    loadLlmSummary();
  }, []);

  const getPolicyIcon = (policyName: string) => {
    const iconMap: { [key: string]: React.ComponentType<any> } = {
      '経済成長戦略': DollarSign,
      '防衛力強化': Shield,
      '社会保障制度改革': Heart,
      '地方創生': Building,
      'エネルギー安全保障': Target
    };
    return iconMap[policyName] || Target;
  };

  if (loading) {
    return (
      <>
        <Header currentPage="manifestos" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="h-12 w-12 animate-spin text-red-600 mx-auto mb-4" />
              <p className="text-gray-600">AI要約を読み込み中...</p>
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
              href="/manifestos/llm"
              className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              AI要約一覧に戻る
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
        {/* 戻るボタン */}
        <div className="mb-6">
          <Link
            href="/manifestos/llm"
            className="inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            AI要約一覧に戻る
          </Link>
        </div>

        {/* ヘッダー */}
        <div className="bg-gradient-to-r from-red-50 to-red-100 rounded-lg p-6 mb-8">
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                {llmData.party} AI要約マニフェスト
              </h1>
              <p className="text-gray-600 mb-4">{llmData.title}</p>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="flex items-center">
                  <Calendar className="h-4 w-4 mr-1" />
                  2025年
                </span>
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  Claude AI による要約
                </span>
              </div>
            </div>
            <div className="ml-6">
              <a
                href={llmData.url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700"
              >
                原文を確認
                <ExternalLink className="h-4 w-4 ml-2" />
              </a>
            </div>
          </div>
        </div>

        {/* 基本テーマ */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">基本テーマ</h2>
          <p className="text-lg text-gray-900 leading-relaxed">{llmData.basic_theme}</p>
        </div>

        {/* 想定支持層 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">想定支持層</h2>
          <div className="flex flex-wrap gap-3">
            {llmData.target_voters.map((voter, index) => (
              <span key={index} className="bg-red-100 text-red-800 px-4 py-2 rounded-full text-sm font-medium">
                <Users className="h-4 w-4 inline mr-2" />
                {voter}
              </span>
            ))}
          </div>
        </div>

        {/* 重点政策一覧 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
          <h2 className="text-xl font-bold text-gray-900 mb-4">重点政策</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
            {llmData.key_policies.map((policy, index) => (
              <div key={index} className="flex items-center p-3 bg-red-50 rounded-lg">
                <Target className="h-5 w-5 text-red-600 mr-3" />
                <span className="text-gray-900 font-medium">{policy}</span>
              </div>
            ))}
          </div>
        </div>

        {/* 政策詳細 */}
        <div className="space-y-6">
          <h2 className="text-2xl font-bold text-gray-900">政策詳細</h2>
          
          {Object.entries(llmData.policy_details).map(([policyName, details]) => {
            const PolicyIcon = getPolicyIcon(policyName);
            return (
              <div key={policyName} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center mb-4">
                  <PolicyIcon className="h-6 w-6 text-red-600 mr-3" />
                  <h3 className="text-xl font-semibold text-gray-900">{policyName}</h3>
                </div>
                
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">政策内容</h4>
                    <ul className="space-y-2">
                      {details.content.map((item, itemIndex) => (
                        <li key={itemIndex} className="flex items-start text-gray-700">
                          <span className="inline-block w-2 h-2 bg-red-600 rounded-full mt-2 mr-3 flex-shrink-0"></span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                  
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 mb-3">重要ポイント</h4>
                    <ul className="space-y-2">
                      {details.key_points.map((point, pointIndex) => (
                        <li key={pointIndex} className="flex items-start text-gray-700">
                          <Target className="h-4 w-4 text-green-600 mt-0.5 mr-2 flex-shrink-0" />
                          {point}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">AI要約について</h3>
          <p className="text-sm text-gray-600">
            この要約は公開されているマニフェストをClaude AIが解析して作成されています。
            詳細な政策内容については、必ず原文をご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}