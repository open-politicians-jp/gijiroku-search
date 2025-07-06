'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, ExternalLink, Users, Target, FileText, Loader2 } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';
import { PolicySummaryData, PartyPolicy } from '@/types/policy';
import PolicyReferences from '@/components/PolicyReferences';

export default function KokuminminshutoDetailPage() {
  const partyName = '国民民主党';

  const [policyData, setPolicyData] = useState<PolicySummaryData | null>(null);
  const [partyPolicies, setPartyPolicies] = useState<PartyPolicy | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // ページ読み込み時にトップにスクロール
    window.scrollTo(0, 0);
    
    const loadPartyDetail = async () => {
      try {
        setLoading(true);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const response = await fetch(`${basePath}/data/policy_summaries.json`);
        
        if (!response.ok) {
          throw new Error(`政策要約データの取得に失敗しました (HTTP ${response.status})`);
        }
        
        const data: PolicySummaryData = await response.json();
        setPolicyData(data);
        
        const party = data.parties.find(p => p.name === partyName);
        if (!party) {
          throw new Error('指定された政党の政策が見つかりませんでした');
        }
        
        setPartyPolicies(party);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';
        
        // フォールバック機能
        if (errorMessage.includes('404') || errorMessage.includes('Failed to fetch')) {
          try {
            const altResponse = await fetch('./data/policy_summaries.json');
            if (altResponse.ok) {
              const altData: PolicySummaryData = await altResponse.json();
              const altParty = altData.parties.find(p => p.name === partyName);
              if (altParty) {
                setPolicyData(altData);
                setPartyPolicies(altParty);
                setLoading(false);
                return;
              }
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

    loadPartyDetail();
  }, []);

  const getPartyColor = () => 'bg-green-50 border-green-200 text-green-900';

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

  if (error || !partyPolicies) {
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
            href="/manifestos"
            className="inline-flex items-center text-blue-600 hover:text-blue-800 mb-4"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            マニフェスト一覧に戻る
          </Link>
        </div>

        {/* 政党ヘッダー */}
        <div className={`bg-white rounded-lg shadow-sm border-2 ${getPartyColor()} p-6 mb-8`}>
          <div className="flex items-start justify-between mb-4">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{partyPolicies.name}</h1>
              <h2 className="text-xl text-gray-700 mb-4">政策要約</h2>
              <p className="text-gray-800 leading-relaxed mb-4">
                {partyPolicies.categories.length}の政策分野にわたる詳細な政策をご確認いただけます。
              </p>
            </div>
          </div>

          <div className="flex flex-col sm:flex-row gap-4">
            <a
              href="https://new-kokumin.jp/"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
            >
              公式サイトを見る
              <ExternalLink className="h-4 w-4 ml-1" />
            </a>
          </div>
        </div>

        {/* 政策概要 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
            <Target className="h-5 w-5 text-green-600 mr-2" />
            政策分野概要
          </h3>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
            {partyPolicies.categories.map((category, index) => (
              <div key={index} className="flex items-center p-3 bg-gray-50 rounded-lg">
                <FileText className="h-4 w-4 text-blue-600 mr-2 flex-shrink-0" />
                <span className="text-sm font-medium text-gray-800">{category.category}</span>
                <span className="ml-auto text-xs text-gray-500">
                  {category.policies.length}項目
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* 政策詳細 */}
        <div className="space-y-6">
          {partyPolicies.categories.map((category, categoryIndex) => (
            <div key={categoryIndex} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h3 className="text-lg font-semibold text-gray-900 mb-4 flex items-center">
                <FileText className="h-5 w-5 text-orange-600 mr-2" />
                {category.category}
              </h3>
              
              {/* 政策項目一覧 */}
              <div className="space-y-4">
                {category.policies.map((policy, policyIndex) => (
                  <div key={policyIndex} className="border-l-4 border-blue-500 pl-4 py-2">
                    <h4 className="font-semibold text-gray-900 mb-2">{policy.title}</h4>
                    <p className="text-sm text-gray-700 leading-relaxed">{policy.description}</p>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* 参考資料・出典 */}
        {partyPolicies.party_references && partyPolicies.party_references.length > 0 && (
          <PolicyReferences 
            references={partyPolicies.party_references}
            className="mb-6"
          />
        )}

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 mb-2">
            この要約は{partyPolicies.name}の公式マニフェストを分析して作成された政策要約です。
            政策の詳細や正確な内容については、必ず公式サイトをご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ 政策要約は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
          {policyData && (
            <p className="text-xs text-gray-500 mt-2">
              生成日時: {new Date(policyData.generated_at).toLocaleDateString('ja-JP')} | 
              総政党数: {policyData.total_parties}政党
            </p>
          )}
        </div>
      </div>
    </>
  );
}