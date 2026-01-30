'use client';

import { useState, useEffect } from 'react';
import { ArrowRight, BookOpen, Target, Loader2, Vote, Building2, Users, ExternalLink, Calendar } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';
import { PolicySummaryData } from '@/types/policy';

interface PartyCandidateInfo {
  name: string;
  candidateUrl: string;
  electionUrl: string;
}

const partyCandidateLinks: PartyCandidateInfo[] = [
  {
    name: '自由民主党',
    candidateUrl: 'https://www.jimin.jp/election/',
    electionUrl: 'https://www.jimin.jp/policy/pamphlet/',
  },
  {
    name: '日本維新の会',
    candidateUrl: 'https://o-ishin.jp/election/',
    electionUrl: 'https://o-ishin.jp/policy/',
  },
  {
    name: '中道改革連合',
    candidateUrl: 'https://craj.jp/',
    electionUrl: 'https://craj.jp/party/policies/',
  },
  {
    name: '日本共産党',
    candidateUrl: 'https://www.jcp.or.jp/giin/',
    electionUrl: 'https://www.jcp.or.jp/web_policy/',
  },
  {
    name: '国民民主党',
    candidateUrl: 'https://new-kokumin.jp/policies',
    electionUrl: 'https://new-kokumin.jp/policies',
  },
  {
    name: 'れいわ新選組',
    candidateUrl: 'https://reiwa-shinsengumi.com/election/',
    electionUrl: 'https://reiwa-shinsengumi.com/policy/',
  },
  {
    name: '参政党',
    candidateUrl: 'https://www.sanseito.jp/',
    electionUrl: 'https://www.sanseito.jp/policy/',
  },
];

export default function ShugiinManifestosPage() {
  const [policyData, setPolicyData] = useState<PolicySummaryData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadLlmSummaries = async () => {
      try {
        setLoading(true);
        const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
        const dataUrl = `${basePath}/data/shugiin_policy_summaries.json`;

        const response = await fetch(dataUrl);

        if (!response.ok) {
          throw new Error(`政策要約データの取得に失敗しました (HTTP ${response.status})`);
        }

        const data: PolicySummaryData = await response.json();
        setPolicyData(data);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';

        if (errorMessage.includes('404') || errorMessage.includes('Failed to fetch')) {
          try {
            const altResponse = await fetch('./data/shugiin_policy_summaries.json');
            if (altResponse.ok) {
              const altData: PolicySummaryData = await altResponse.json();
              setPolicyData(altData);
              setLoading(false);
              return;
            }
          } catch {
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
      '中道改革連合': 'bg-blue-50 border-blue-200 text-blue-900',
      '日本維新の会': 'bg-orange-50 border-orange-200 text-orange-900',
      '参政党': 'bg-indigo-50 border-indigo-200 text-indigo-900',
      '国民民主党': 'bg-green-50 border-green-200 text-green-900',
      'れいわ新選組': 'bg-purple-50 border-purple-200 text-purple-900',
      '日本共産党': 'bg-red-50 border-red-200 text-red-900',
    };
    return colors[party] || 'bg-gray-50 border-gray-200 text-gray-900';
  };

  const getPartySlug = (party: string) => {
    const slugs: { [key: string]: string } = {
      '自由民主党': 'jiyuminshuto',
      '中道改革連合': 'chudokaikakuren',
      '日本維新の会': 'nipponishin',
      '参政党': 'sanseito',
      '国民民主党': 'kokuminminshuto',
      'れいわ新選組': 'reiwa',
      '日本共産党': 'kyosanto',
    };
    return slugs[party] || party.toLowerCase();
  };

  if (loading) {
    return (
      <>
        <Header currentPage="shugiin2026" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <Loader2 className="h-12 w-12 animate-spin text-red-600 mx-auto mb-4" />
              <p className="text-gray-600">2026年衆議院選 政策要約を読み込み中...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error || !policyData) {
    return (
      <>
        <Header currentPage="shugiin2026" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">エラーが発生しました</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <Link
              href="/"
              className="inline-flex items-center px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              トップページに戻る
            </Link>
          </div>
        </div>
      </>
    );
  }

  return (
    <>
      <Header currentPage="shugiin2026" />
      <div className="container mx-auto px-4 py-8 mt-16">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-2">
            <Vote className="h-8 w-8 text-red-600" />
            <h1 className="text-3xl font-bold text-gray-900">衆院選2026</h1>
          </div>
          <p className="text-gray-600 mb-4">第51回衆議院議員総選挙 各政党の政策・候補者情報</p>

          {/* 選挙情報バナー */}
          <div className="mt-4 p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-2 mb-2">
              <Calendar className="h-5 w-5 text-red-600" />
              <h2 className="text-sm font-semibold text-red-900">第51回衆議院議員総選挙</h2>
            </div>
            <div className="grid grid-cols-2 gap-4 mt-2">
              <div>
                <span className="text-xs text-red-600 font-medium">公示日</span>
                <p className="text-sm font-bold text-red-900">2026年1月27日（火）</p>
              </div>
              <div>
                <span className="text-xs text-red-600 font-medium">投票日</span>
                <p className="text-sm font-bold text-red-900">2026年2月8日（日）</p>
              </div>
            </div>
            <div className="mt-2 text-xs text-red-600">
              最終更新: {new Date(policyData.generated_at).toLocaleDateString('ja-JP')} |
              掲載政党数: {policyData.total_parties}政党
            </div>
          </div>

          {/* ナビゲーションリンク */}
          <div className="mt-4 flex flex-wrap gap-3">
            <Link
              href="/shugiin-candidates"
              className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
            >
              <Users className="h-4 w-4 mr-2 text-red-600" />
              候補者一覧を見る
            </Link>
            <Link
              href="/shugiin-comparison"
              className="inline-flex items-center px-4 py-2 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 text-sm"
            >
              <Target className="h-4 w-4 mr-2 text-red-600" />
              政策比較表を見る
            </Link>
          </div>
        </div>

        {/* 候補者情報セクション */}
        <div className="mb-8">
          <div className="flex items-center gap-2 mb-4">
            <Users className="h-6 w-6 text-red-600" />
            <h2 className="text-xl font-bold text-gray-900">各政党の候補者情報</h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            各政党の公式サイトで候補者一覧をご確認いただけます。
          </p>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {partyCandidateLinks.map((party) => (
              <a
                key={party.name}
                href={party.candidateUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center justify-between p-3 bg-white border border-gray-200 rounded-lg hover:bg-gray-50 hover:border-red-300 transition-colors"
              >
                <span className="text-sm font-medium text-gray-900">{party.name}</span>
                <ExternalLink className="h-4 w-4 text-gray-400 flex-shrink-0" />
              </a>
            ))}
          </div>
        </div>

        {/* マニフェスト要約セクション */}
        <div className="mb-4">
          <div className="flex items-center gap-2 mb-4">
            <BookOpen className="h-6 w-6 text-red-600" />
            <h2 className="text-xl font-bold text-gray-900">各政党の政策要約</h2>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            各政党の公式マニフェストを分析し、有権者にとって分かりやすい形で政策をまとめています。
          </p>
        </div>

        {/* マニフェスト要約カード */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {policyData.parties.map((party) => (
            <div key={party.name} className={`bg-white rounded-lg shadow-sm border-2 ${getPartyColor(party.name)} p-6 hover:shadow-md transition-shadow`}>
              <div className="mb-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-2">
                  {party.name}
                </h3>
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
                        <Target className="h-3 w-3 text-red-600 mr-2 flex-shrink-0" />
                        {policy.title}
                      </li>
                    ))
                  ))}
                </ul>
              </div>

              <div className="flex flex-col space-y-2">
                <Link
                  href={`/shugiin-manifestos/${getPartySlug(party.name)}`}
                  className="inline-flex items-center justify-center px-4 py-2 bg-red-600 text-white rounded-md hover:bg-red-700 text-sm font-medium"
                >
                  詳細政策を見る
                  <ArrowRight className="h-4 w-4 ml-1" />
                </Link>
                {party.official_url && (
                  <a
                    href={party.official_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center justify-center px-4 py-2 bg-white border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 text-sm"
                  >
                    公式サイト
                    <ExternalLink className="h-4 w-4 ml-1" />
                  </a>
                )}
              </div>
            </div>
          ))}
        </div>

        {/* フッター */}
        <div className="mt-8 p-4 bg-gray-50 rounded-lg">
          <h3 className="text-sm font-semibold text-gray-700 mb-2">政策要約について</h3>
          <p className="text-sm text-gray-600 mb-2">
            この要約は各政党の公式マニフェスト・政策ページを分析して作成された政策要約です。
            政策の詳細や正確な内容については、必ず各政党の公式サイトをご確認ください。
          </p>
          <p className="text-xs text-gray-500">
            ※ 政策要約は参考情報として提供されています。投票の際は公式情報を必ずご確認ください。
          </p>
        </div>
      </div>
    </>
  );
}
