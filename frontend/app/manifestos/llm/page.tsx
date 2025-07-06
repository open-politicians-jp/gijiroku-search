'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, ExternalLink, Users, Calendar, FileText, BookOpen, Target, Loader2 } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';
import { PolicySummaryData, PartyPolicy } from '@/types/policy';

export default function LLMManifestosPage() {
  const [policyData, setPolicyData] = useState<PolicySummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLlmSummaries = async () => {
      try {
        setLoading(true);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const dataUrl = `${basePath}/data/policy_summaries.json`;
        
        const response = await fetch(dataUrl);
        
        if (!response.ok) {
          throw new Error(`政策要約データの取得に失敗しました (HTTP ${response.status})`);
        }
        
        const data: PolicySummaryData = await response.json();
        setPolicyData(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';
        
        // GitHub Pages でのデータ読み込み失敗の場合、代替手段を試行
        if (errorMessage.includes('404') || errorMessage.includes('Failed to fetch')) {
          try {
            // 代替パスでの試行
            const altResponse = await fetch('./data/policy_summaries.json');
            if (altResponse.ok) {
              const altData: PolicySummaryData = await altResponse.json();
              setPolicyData(altData);
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
      '日本共産党': 'bg-red-50 border-red-200 text-red-900',
      '日本保守党': 'bg-purple-50 border-purple-200 text-purple-900',
      'NHK党（みんなでつくる党）': 'bg-pink-50 border-pink-200 text-pink-900',
      '社会民主党': 'bg-green-50 border-green-200 text-green-900',
      '日本改革党': 'bg-cyan-50 border-cyan-200 text-cyan-900',
      '国政ガバナンスの会': 'bg-gray-50 border-gray-200 text-gray-900',
      '日本誠真会': 'bg-slate-50 border-slate-200 text-slate-900',
      '日本の家庭を守る会': 'bg-rose-50 border-rose-200 text-rose-900',
      '新党やまと': 'bg-amber-50 border-amber-200 text-amber-900',
      '再生の道': 'bg-emerald-50 border-emerald-200 text-emerald-900',
      '核融合党': 'bg-violet-50 border-violet-200 text-violet-900',
      '減税日本': 'bg-red-50 border-red-200 text-red-900',
      '税金とうめい化の党': 'bg-blue-50 border-blue-200 text-blue-900',
      '新党くにもり': 'bg-teal-50 border-teal-200 text-teal-900'
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
      '日本共産党': 'kyosanto',
      '日本保守党': 'nihon-hoshu-to',
      'NHK党（みんなでつくる党）': 'nhk-to',
      '社会民主党': 'shakai-minshu-to',
      '日本改革党': 'nihon-kaikaku-to',
      '国政ガバナンスの会': 'kokusei-governance',
      '日本誠真会': 'kokka-seishin-kai',
      '日本の家庭を守る会': 'nihon-katei-mamoru-kai',
      '新党やまと': 'shinto-yamato',
      '再生の道': 'saisei-no-michi',
      '核融合党': 'kakuyugo-to',
      '減税日本': 'genzei-nihon',
      '税金とうめい化の党': 'zeikin-tomei-ka-to',
      '新党くにもり': 'shinto-kunimori'
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

  if (error || !policyData) {
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
          <p className="text-gray-600 mb-4">各政党のマニフェストを有権者向けに分かりやすく要約しました</p>
          <div className="mt-4 p-4 bg-blue-50 rounded-lg">
            <div className="flex items-center gap-2 mb-2">
              <BookOpen className="h-5 w-5 text-blue-600" />
              <h2 className="text-sm font-semibold text-blue-900">政策要約</h2>
            </div>
            <p className="text-sm text-blue-700">
              各政党の公式マニフェストを分析し、有権者にとって分かりやすい形で政策をまとめています。
              詳細は公式サイトもご確認ください。
            </p>
            <div className="mt-2 text-xs text-blue-600">
              生成日時: {new Date(policyData.generated_at).toLocaleDateString('ja-JP')} | 
              総政党数: {policyData.total_parties}政党
            </div>
          </div>
        </div>

        {/* マニフェスト要約カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {policyData.parties.map((party) => (
            <div key={party.name} className={`bg-white rounded-lg shadow-sm border-2 ${getPartyColor(party.name)} p-6 hover:shadow-md transition-shadow`}>
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {party.name}
                </h3>
                <p className="text-sm text-gray-600 mb-3">
                  政策要約
                </p>
                <p className="text-sm text-gray-700 mb-4">
                  {party.categories.length}の政策分野にわたる詳細な政策
                </p>
              </div>

              {/* 政策カテゴリ */}
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-600 mb-2">政策分野</h4>
                <div className="flex flex-wrap gap-1">
                  {party.categories.slice(0, 3).map((category, index) => (
                    <span key={index} className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                      {category.category}
                    </span>
                  ))}
                  {party.categories.length > 3 && (
                    <span className="text-xs bg-gray-100 text-gray-700 px-2 py-1 rounded-full">
                      +{party.categories.length - 3}項目
                    </span>
                  )}
                </div>
              </div>

              {/* 主要政策 */}
              <div className="mb-4">
                <h4 className="text-xs font-semibold text-gray-600 mb-2">主要政策</h4>
                <ul className="space-y-1">
                  {party.categories.slice(0, 3).map((category, index) => (
                    category.policies.slice(0, 1).map((policy, policyIndex) => (
                      <li key={`${index}-${policyIndex}`} className="flex items-center text-xs text-gray-700">
                        <Target className="h-3 w-3 text-blue-600 mr-2 flex-shrink-0" />
                        {policy.title}
                      </li>
                    ))
                  ))}
                </ul>
              </div>
              
              <div className="flex flex-col space-y-2">
                <Link
                  href={`/manifestos/llm/${getPartySlug(party.name)}`}
                  className="inline-flex items-center justify-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 text-sm font-medium"
                >
                  詳細政策を見る
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
              </div>
            </div>
          ))}
        </div>

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">政策要約について</h3>
          <p className="text-sm text-gray-600 mb-2">
            この要約は各政党の公式マニフェストを分析して作成された政策要約です。
            政策の詳細や正確な内容については、必ず公式サイトをご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ 政策要約は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}