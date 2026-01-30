'use client';

import { useState, useEffect, useCallback } from 'react';
import { Users, MapPin, Calendar, Badge, ExternalLink, BookOpen, Target } from 'lucide-react';
import Header from '@/components/Header';
import Link from 'next/link';

interface Candidate {
  candidate_id: string;
  name: string;
  name_kana?: string;
  constituency: string;
  constituency_type: string;
  region?: string | null;
  party: string;
  party_normalized?: string;
  profile_url?: string;
  source_url?: string;
  collected_at?: string;
  status?: string;
  manifesto_summary?: string;
  policy_positions?: string[];
  sns_accounts?: Record<string, string>;
}

interface CandidatesMetadata {
  data_type: string;
  election_year: number;
  total_candidates: number;
  parties_count: number;
  generated_at: string;
  data_sources: string[];
  collection_version: string;
  next_update?: string;
}

interface CandidatesStatistics {
  by_party: Record<string, number>;
  by_constituency: Record<string, number>;
}

interface ApiResponse {
  data: Candidate[];
  metadata: CandidatesMetadata;
  statistics: CandidatesStatistics;
}

export default function ShugiinCandidatesPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [filteredCandidates, setFilteredCandidates] = useState<Candidate[]>([]);
  const [metadata, setMetadata] = useState<CandidatesMetadata | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [uniqueCount, setUniqueCount] = useState<number>(0);

  const [selectedParty, setSelectedParty] = useState<string>('');
  const [selectedConstituencyType, setSelectedConstituencyType] = useState<string>('');
  const [selectedConstituency, setSelectedConstituency] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchCandidates = async () => {
    try {
      const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
      const dataUrl = `${basePath}/data/shugiin_candidates/shugiin_2026_candidates_latest.json`;

      const response = await fetch(dataUrl);

      if (!response.ok) {
        throw new Error(`衆院選候補者データの取得に失敗しました (HTTP ${response.status})`);
      }

      const result: ApiResponse = await response.json();
      const candidatesData = Array.isArray(result.data) ? result.data : [];

      if (candidatesData.length === 0) {
        throw new Error('候補者データが見つかりません');
      }

      setCandidates(candidatesData);
      setUniqueCount(new Set(candidatesData.map(candidate => candidate.profile_url).filter(Boolean)).size);
      setMetadata(result.metadata);
      setLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';

      if (errorMessage.includes('404') || errorMessage.includes('Failed to fetch')) {
        try {
          const altResponse = await fetch('./data/shugiin_candidates/shugiin_2026_candidates_latest.json');
          if (altResponse.ok) {
            const altResult: ApiResponse = await altResponse.json();
            const altCandidatesData = Array.isArray(altResult.data) ? altResult.data : [];
            if (altCandidatesData.length > 0) {
              setCandidates(altCandidatesData);
              setUniqueCount(new Set(altCandidatesData.map(candidate => candidate.profile_url).filter(Boolean)).size);
              setMetadata(altResult.metadata);
              setLoading(false);
              return;
            }
          }
        } catch {
          // 代替手段も失敗した場合は元のエラーを表示
        }
      }

      setError(`データ読み込みエラー: ${errorMessage}`);
      setLoading(false);
    }
  };

  const filterCandidates = useCallback(() => {
    let filtered = [...candidates];

    if (selectedParty) {
      filtered = filtered.filter(candidate => candidate.party === selectedParty);
    }

    if (selectedConstituencyType) {
      filtered = filtered.filter(candidate => candidate.constituency_type === selectedConstituencyType);
    }

    if (selectedConstituency) {
      filtered = filtered.filter(candidate => candidate.constituency === selectedConstituency);
    }

    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(candidate => {
        const name = candidate.name.toLowerCase();
        const party = candidate.party.toLowerCase();
        const constituency = candidate.constituency.toLowerCase();
        const partyMatch = party === term || party.startsWith(term);
        return partyMatch || name.includes(term) || constituency.includes(term);
      });
    }

    setFilteredCandidates(filtered);
  }, [candidates, selectedParty, selectedConstituencyType, selectedConstituency, searchTerm]);

  useEffect(() => {
    fetchCandidates();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    filterCandidates();
  }, [filterCandidates]);

  const getUniqueParties = () => {
    const parties = Array.from(new Set(candidates.map(candidate => candidate.party)));
    return parties.sort();
  };

  const getUniqueConstituencyTypes = () => {
    const types = Array.from(new Set(candidates.map(candidate => candidate.constituency_type)));
    return types.sort();
  };

  const getUniqueConstituencies = () => {
    const constituencies = Array.from(new Set(candidates.map(candidate => candidate.constituency)));
    return constituencies.sort();
  };

  const getConstituencyTypeLabel = (type: string) => {
    switch (type) {
      case 'single_member': return '小選挙区';
      case 'proportional': return '比例代表';
      case 'block': return 'ブロック';
      case 'district': return '選挙区';
      case '小選挙区': return '小選挙区';
      case '比例代表': return '比例代表';
      case 'unknown': return '未分類';
      default: return type;
    }
  };

  const getPartyColor = (party: string) => {
    const colors: { [key: string]: string } = {
      '自由民主党': 'bg-red-100 text-red-800',
      '中道改革連合': 'bg-blue-100 text-blue-800',
      '日本維新の会': 'bg-orange-100 text-orange-800',
      '日本共産党': 'bg-red-100 text-red-700',
      '国民民主党': 'bg-green-100 text-green-800',
      'れいわ新選組': 'bg-purple-100 text-purple-800',
      '参政党': 'bg-indigo-100 text-indigo-800',
      '無所属': 'bg-gray-100 text-gray-700',
    };
    return colors[party] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <>
        <Header currentPage="shugiin2026" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-red-600 mx-auto mb-4"></div>
              <p className="text-gray-600">衆院選候補者データを読み込み中...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header currentPage="shugiin2026" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">エラーが発生しました</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <button
              onClick={fetchCandidates}
              className="mt-2 px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              再試行
            </button>
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
        <div className="bg-gradient-to-r from-red-50 to-orange-50 rounded-lg p-6 mb-8">
          <div className="flex items-center gap-3 mb-4">
            <Users className="h-8 w-8 text-red-600" />
            <h1 className="text-3xl font-bold text-gray-900">衆院選2026 候補者一覧</h1>
          </div>
          <p className="text-gray-600 mb-4">
            2026年衆議院議員総選挙に向けた候補者情報を検索・表示できます。
          </p>

          {/* 特設ページへのリンク */}
          <div className="flex flex-col sm:flex-row gap-4 mb-6">
            <Link
              href="/shugiin-manifestos"
              className="inline-flex items-center justify-center px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
            >
              <BookOpen className="h-5 w-5 mr-2" />
              衆院選 政策要約
            </Link>
            <Link
              href="/shugiin-comparison"
              className="inline-flex items-center justify-center px-6 py-3 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <Target className="h-5 w-5 mr-2" />
              衆院選 政策対比表
            </Link>
          </div>

          <div className="flex flex-wrap gap-4 text-sm text-gray-600">
            <div className="flex items-center gap-1">
              <Badge className="h-4 w-4" />
              <span>候補者数: {uniqueCount || candidates.length}名</span>
            </div>
            <div className="flex items-center gap-1">
              <Calendar className="h-4 w-4" />
              <span>選挙年: {metadata?.election_year ?? 2026}年</span>
            </div>
            <div className="flex items-center gap-1">
              <MapPin className="h-4 w-4" />
              <span>データソース: {metadata?.data_sources?.join(', ') || '未記載'}</span>
            </div>
          </div>
        </div>

        {/* フィルター */}
        <div className="bg-white rounded-lg shadow-sm border p-6 mb-6">
          <h2 className="text-lg font-semibold mb-4">検索・フィルター</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 検索ボックス */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                候補者名検索
              </label>
              <input
                type="text"
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                placeholder="候補者名、政党名で検索..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>

            {/* 政党フィルター */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                政党
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                value={selectedParty}
                onChange={(e) => setSelectedParty(e.target.value)}
              >
                <option value="">すべての政党</option>
                {getUniqueParties().map(party => (
                  <option key={party} value={party}>{party}</option>
                ))}
              </select>
            </div>

            {/* 選挙区タイプフィルター */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                選挙区タイプ
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                value={selectedConstituencyType}
                onChange={(e) => setSelectedConstituencyType(e.target.value)}
              >
                <option value="">すべての選挙区</option>
                {getUniqueConstituencyTypes().map(type => (
                  <option key={type} value={type}>{getConstituencyTypeLabel(type)}</option>
                ))}
              </select>
            </div>

            {/* 選挙区フィルター */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                選挙区
              </label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-red-500"
                value={selectedConstituency}
                onChange={(e) => setSelectedConstituency(e.target.value)}
              >
                <option value="">すべての選挙区</option>
                {getUniqueConstituencies().map(constituency => (
                  <option key={constituency} value={constituency}>{constituency}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="mt-4 text-sm text-gray-600">
            {filteredCandidates.length}名の候補者が見つかりました
          </div>
        </div>

        {/* 候補者一覧 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCandidates.map(candidate => (
            <div key={candidate.candidate_id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
              <div className="p-6">
                <div className="flex items-start gap-4 mb-4">
                <div className="flex-1">
                  <div className="mb-1">
                    <h3 className="text-lg font-semibold text-gray-900">
                      {candidate.name}
                    </h3>
                    {candidate.name_kana && (
                      <p className="text-sm text-gray-500 mt-1">
                        読み: {candidate.name_kana}
                      </p>
                    )}
                  </div>
                    <span className={`inline-block px-2 py-1 rounded-full text-xs font-medium ${getPartyColor(candidate.party)}`}>
                      {candidate.party}
                    </span>
                  </div>
                </div>

                <div className="space-y-2 mb-4">
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <MapPin className="h-4 w-4" />
                    <span>
                      {candidate.constituency} - {getConstituencyTypeLabel(candidate.constituency_type)}
                    </span>
                  </div>
                </div>

                {candidate.policy_positions && candidate.policy_positions.length > 0 && (
                  <div className="mb-4">
                    <p className="text-xs text-gray-500 mb-1">主要政策</p>
                    <div className="flex flex-wrap gap-2">
                      {candidate.policy_positions.slice(0, 3).map((policy, index) => (
                        <span
                          key={`${candidate.candidate_id}-policy-${index}`}
                          className="text-xs bg-red-50 text-red-700 px-2 py-1 rounded"
                        >
                          {policy}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div className="flex flex-wrap gap-2">
                  {candidate.profile_url && (
                    <a
                      href={candidate.profile_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-red-600 hover:text-red-800"
                    >
                      <ExternalLink className="h-3 w-3" />
                      プロフィール詳細
                    </a>
                  )}
                  {candidate.source_url && (
                    <a
                      href={candidate.source_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="flex items-center gap-1 text-xs text-gray-600 hover:text-gray-800"
                    >
                      <ExternalLink className="h-3 w-3" />
                      データ元
                    </a>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>

        {filteredCandidates.length === 0 && candidates.length > 0 && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Users className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              検索条件に一致する候補者が見つかりません
            </h3>
            <p className="text-gray-600">
              検索条件を変更して再度お試しください。
            </p>
          </div>
        )}

        {candidates.length === 0 && !loading && !error && (
          <div className="text-center py-12">
            <div className="text-gray-400 mb-4">
              <Users className="h-16 w-16 mx-auto" />
            </div>
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              候補者データが見つかりません
            </h3>
            <p className="text-gray-600 mb-4">
              データの読み込みに問題がある可能性があります。
            </p>
            <button
              onClick={fetchCandidates}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              データを再読み込み
            </button>
          </div>
        )}
      </div>
    </>
  );
}
