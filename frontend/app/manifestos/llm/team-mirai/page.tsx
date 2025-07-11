'use client';

import { useState, useEffect } from 'react';
import { ArrowLeft, ExternalLink, Users, Target, FileText, Loader2 } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';
import { PolicySummaryData, PartyPolicy } from '@/types/policy';
import PolicyReferences from '@/components/PolicyReferences';

export default function TeamMiraiDetailPage() {
  const partyName = 'チームみらい';

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

  const getPartyColor = () => 'bg-cyan-50 border-cyan-200 text-cyan-900';

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
      <div className="container mx-auto px-4 py-8 mt-16">
        {/* 戻るボタン */}
        <div className="mb-6">
          <Link
            href="/manifestos/llm"
            className="inline-flex items-center text-blue-600 hover:text-blue-800"
          >
            <ArrowLeft className="h-4 w-4 mr-2" />
            政策要約一覧に戻る
          </Link>
        </div>

        {/* 政党ヘッダー */}
        <div className={`rounded-lg border-2 ${getPartyColor()} p-6 mb-8`}>
          <div className="flex items-center justify-between">
            <div className="flex-1">
              <h1 className="text-3xl font-bold text-gray-900 mb-2">{partyName}</h1>
              <p className="text-gray-600 mb-2">政策要約詳細</p>
              <div className="flex items-center space-x-4 text-sm text-gray-600">
                <span className="flex items-center">
                  <FileText className="h-4 w-4 mr-1" />
                  政策カテゴリー: {partyPolicies.categories?.length || 0}件
                </span>
                <span className="bg-cyan-100 text-cyan-800 px-2 py-1 rounded-full text-xs font-medium">
                  新党
                </span>
              </div>
            </div>
          </div>
        </div>

        {/* 政策カテゴリー */}
        <div className="space-y-8">
          {partyPolicies.categories?.map((category, categoryIndex) => (
            <div key={categoryIndex} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <h2 className="text-2xl font-bold text-gray-900 mb-6 border-b border-gray-200 pb-3">
                {category.category}
              </h2>
              
              <div className="space-y-6">
                {category.policies.map((policy, policyIndex) => (
                  <div key={policyIndex} className="border-l-4 border-cyan-500 pl-4">
                    <h3 className="text-lg font-semibold text-gray-900 mb-3">
                      {policy.title}
                    </h3>
                    <div className="text-gray-700 leading-relaxed whitespace-pre-wrap">
                      {policy.description}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* 参考情報 */}
        {partyPolicies.party_references && partyPolicies.party_references.length > 0 && (
          <div className="mt-8">
            <PolicyReferences 
              references={partyPolicies.party_references}
            />
          </div>
        )}

        {/* フッター情報 */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <p className="text-sm text-gray-600 text-center">
            この情報は公開されている政策資料を基に要約されています。
            最新の情報については各政党の公式サイトをご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}