'use client';

import { useState, useEffect, useCallback } from 'react';
import { Users, MapPin, Calendar, Badge, ExternalLink, BookOpen, Target } from 'lucide-react';
import Header from '@/components/Header';
import Image from 'next/image';
import Link from 'next/link';

interface Candidate {
  candidate_id: string;
  name: string;
  name_kana?: string; // カタカナ名前を分離
  prefecture: string;
  constituency: string;
  constituency_type: string;
  party: string;
  party_normalized: string;
  profile_url?: string;
  source_page: string;
  source: string;
  collected_at: string;
  
  // 詳細プロフィール情報
  age_info?: string;
  career?: string;
  occupation?: string;
  birthplace?: string;
  
  // 政策情報
  manifesto_summary?: string;
  policy_areas?: string[];
  
  // SNS・写真情報
  sns_accounts?: Record<string, string>;
  photo_url?: string;
  photo_alt?: string;
  websites?: Array<{url: string; title: string}>;
  official_website?: string;
}

interface ApiResponse {
  success: boolean;
  data: Candidate[];
  pagination: {
    total: number;
    limit: number;
    offset: number;
    hasMore: boolean;
  };
  filters: {
    query: string | null;
    party: string | null;
    prefecture: string | null;
  };
  metadata: {
    data_type: string;
    collection_method: string;
    total_candidates: number;
    generated_at: string;
    source_site: string;
    coverage: {
      constituency_types: number;
      parties: number;
      prefectures: number;
    };
  };
  statistics: {
    by_party: Record<string, number>;
    by_prefecture: Record<string, number>;
    by_constituency_type: Record<string, number>;
  };
}

export default function SangiinPage() {
  const [candidates, setCandidates] = useState<Candidate[]>([]);
  const [filteredCandidates, setFilteredCandidates] = useState<Candidate[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  
  // フィルター状態
  const [selectedParty, setSelectedParty] = useState<string>('');
  const [selectedPrefecture, setSelectedPrefecture] = useState<string>('');
  const [selectedConstituencyType, setSelectedConstituencyType] = useState<string>('');
  const [searchTerm, setSearchTerm] = useState('');

  const fetchCandidates = async () => {
    try {
      // SPA対応: 静的データファイルから直接読み込み（GitHub Pages対応）
      const basePath = process.env.NEXT_PUBLIC_BASE_PATH || '';
      const dataUrl = `${basePath}/data/sangiin_candidates/go2senkyo_optimized_latest.json`;
      
      const response = await fetch(dataUrl);
      
      if (!response.ok) {
        throw new Error(`参議院選候補者データの取得に失敗しました (HTTP ${response.status})`);
      }
      
      const result = await response.json();
      
      // データ構造の確認と取得
      const candidatesData = result.data || result.candidates || [];
      
      if (!Array.isArray(candidatesData)) {
        throw new Error('データ形式が正しくありません');
      }
      
      if (candidatesData.length === 0) {
        throw new Error('候補者データが見つかりません');
      }
      
      // go2senkyo_optimized_latest.jsonは既に品質が良いのでそのまま使用
      const uniqueCandidates = candidatesData;
      setCandidates(uniqueCandidates);
      setLoading(false);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : '不明なエラーが発生しました';
      
      // GitHub Pages でのデータ読み込み失敗の場合、代替手段を試行
      if (errorMessage.includes('404') || errorMessage.includes('Failed to fetch')) {
        try {
          // 代替パスでの試行
          const altResponse = await fetch('./data/sangiin_candidates/go2senkyo_optimized_latest.json');
          if (altResponse.ok) {
            const altResult = await altResponse.json();
            const altCandidatesData = altResult.data || altResult.candidates || [];
            if (Array.isArray(altCandidatesData) && altCandidatesData.length > 0) {
              setCandidates(altCandidatesData);
              setLoading(false);
              return;
            }
          }
        } catch (altErr) {
          // 代替手段も失敗した場合は元のエラーを表示
        }
      }
      
      setError(`データ読み込みエラー: ${errorMessage}`);
      setLoading(false);
    }
  };


  const filterCandidates = useCallback(() => {
    let filtered = [...candidates];

    // 政党フィルター
    if (selectedParty) {
      filtered = filtered.filter(candidate => candidate.party === selectedParty);
    }

    // 都道府県フィルター
    if (selectedPrefecture) {
      filtered = filtered.filter(candidate => candidate.prefecture === selectedPrefecture);
    }

    // 選挙区タイプフィルター
    if (selectedConstituencyType) {
      filtered = filtered.filter(candidate => candidate.constituency_type === selectedConstituencyType);
    }

    // 検索フィルター
    if (searchTerm) {
      const term = searchTerm.toLowerCase();
      filtered = filtered.filter(candidate => {
        const name = candidate.name.toLowerCase();
        const party = candidate.party.toLowerCase();
        const prefecture = candidate.prefecture.toLowerCase();
        const constituency = candidate.constituency.toLowerCase();
        
        // 政党名は完全一致または前方一致で検索（部分マッチを避ける）
        const partyMatch = party === term || party.startsWith(term);
        
        // その他のフィールドは部分マッチ
        const otherFieldsMatch = name.includes(term) ||
          prefecture.includes(term) ||
          constituency.includes(term);
        
        return partyMatch || otherFieldsMatch;
      });
    }

    setFilteredCandidates(filtered);
  }, [candidates, selectedParty, selectedPrefecture, selectedConstituencyType, searchTerm]);

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

  const getUniquePrefectures = () => {
    const prefectureOrder = [
      // 北海道
      '北海道',
      // 東北
      '青森県', '岩手県', '宮城県', '秋田県', '山形県', '福島県',
      // 関東
      '茨城県', '栃木県', '群馬県', '埼玉県', '千葉県', '東京都', '神奈川県',
      // 北陸・甲信越
      '新潟県', '富山県', '石川県', '福井県', '山梨県', '長野県',
      // 東海
      '岐阜県', '静岡県', '愛知県', '三重県',
      // 関西
      '滋賀県', '京都府', '大阪府', '兵庫県', '奈良県', '和歌山県',
      // 中国
      '鳥取県', '島根県', '岡山県', '広島県', '山口県',
      // 四国
      '徳島県', '香川県', '愛媛県', '高知県',
      // 九州・沖縄
      '福岡県', '佐賀県', '長崎県', '熊本県', '大分県', '宮崎県', '鹿児島県', '沖縄県'
    ];

    const availablePrefectures = Array.from(new Set(candidates.map(candidate => candidate.prefecture)));
    
    // 地理的順序に従って並び替え
    const sortedPrefectures = prefectureOrder.filter(pref => availablePrefectures.includes(pref));
    
    // 順序にない都道府県があれば最後に追加
    const unlisted = availablePrefectures.filter(pref => !prefectureOrder.includes(pref));
    
    return [...sortedPrefectures, ...unlisted.sort()];
  };

  const getConstituencyTypeLabel = (type: string) => {
    switch (type) {
      case 'single_member': return '参議院選挙区';
      case 'proportional': return '比例代表';
      case 'district': return '選挙区';
      case 'unknown': return '未分類';
      default: return type;
    }
  };

  const getUniqueConstituencyTypes = () => {
    const types = Array.from(new Set(candidates.map(candidate => candidate.constituency_type)));
    return types.sort();
  };

  const getPartyColor = (party: string) => {
    const colors: { [key: string]: string } = {
      '自由民主党': 'bg-red-100 text-red-800',
      '立憲民主党': 'bg-blue-100 text-blue-800',
      '日本維新の会': 'bg-orange-100 text-orange-800',
      '公明党': 'bg-yellow-100 text-yellow-800',
      '日本共産党': 'bg-red-100 text-red-700',
      '国民民主党': 'bg-green-100 text-green-800',
      'れいわ新選組': 'bg-purple-100 text-purple-800',
      '参政党': 'bg-indigo-100 text-indigo-800',
      '社会民主党': 'bg-pink-100 text-pink-800',
      '日本保守党（代表者：百田尚樹）': 'bg-blue-100 text-blue-700',
      '日本改革党': 'bg-teal-100 text-teal-800',
      '新党やまと': 'bg-emerald-100 text-emerald-800',
      '無所属': 'bg-gray-100 text-gray-700',
      '無所属連合': 'bg-gray-200 text-gray-800'
    };
    return colors[party] || 'bg-gray-100 text-gray-800';
  };

  if (loading) {
    return (
      <>
        <Header currentPage="sangiin" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
              <p className="text-gray-600">参議院選候補者データを読み込み中...</p>
            </div>
          </div>
        </div>
      </>
    );
  }

  if (error) {
    return (
      <>
        <Header currentPage="sangiin" />
        <div className="container mx-auto px-4 py-8 mt-16">
          <div className="bg-red-50 border border-red-200 rounded-lg p-6">
            <h2 className="text-lg font-semibold text-red-800 mb-2">エラーが発生しました</h2>
            <p className="text-red-600 mb-4">{error}</p>
            <div className="text-sm text-gray-600">
              <p>デバッグ情報:</p>
              <ul className="list-disc list-inside mt-2">
                <li>Candidates loaded: {candidates.length}</li>
                <li>Loading state: {loading.toString()}</li>
                <li>Console に詳細なログが出力されています</li>
              </ul>
            </div>
            <button 
              onClick={fetchCandidates}
              className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
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
      <Header currentPage="sangiin" />
      <div className="container mx-auto px-4 py-8 mt-16">
      {/* ヘッダー */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-8">
        <div className="flex items-center gap-3 mb-4">
          <Users className="h-8 w-8 text-blue-600" />
          <h1 className="text-3xl font-bold text-gray-900">参議院選2025 候補者一覧</h1>
        </div>
        <p className="text-gray-600 mb-4">
          2025年参議院選挙の候補者情報を都道府県・政党別に検索・表示できます。データはGo2senkyo.comから自動収集されています。
        </p>
        
        {/* 特設ページへのリンク */}
        <div className="flex flex-col sm:flex-row gap-4 mb-6">
          <Link
            href="/manifestos/llm"
            className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <BookOpen className="h-5 w-5 mr-2" />
            AI要約マニフェスト
          </Link>
          <Link
            href="/sangiin-comparison"
            className="inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Target className="h-5 w-5 mr-2" />
            参院選 政策対比表
          </Link>
        </div>
        
        <div className="flex flex-wrap gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Badge className="h-4 w-4" />
            <span>候補者数: {candidates.length}名</span>
          </div>
          <div className="flex items-center gap-1">
            <Calendar className="h-4 w-4" />
            <span>選挙年: 2025年</span>
          </div>
          <div className="flex items-center gap-1">
            <MapPin className="h-4 w-4" />
            <span>データソース: Go2senkyo.com</span>
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
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
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedParty}
              onChange={(e) => setSelectedParty(e.target.value)}
            >
              <option value="">すべての政党</option>
              {getUniqueParties().map(party => (
                <option key={party} value={party}>{party}</option>
              ))}
            </select>
          </div>

          {/* 都道府県フィルター */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              都道府県
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedPrefecture}
              onChange={(e) => setSelectedPrefecture(e.target.value)}
            >
              <option value="">すべての都道府県</option>
              {getUniquePrefectures().map(prefecture => (
                <option key={prefecture} value={prefecture}>{prefecture}</option>
              ))}
            </select>
          </div>

          {/* 選挙区タイプフィルター */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              選挙区タイプ
            </label>
            <select
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={selectedConstituencyType}
              onChange={(e) => setSelectedConstituencyType(e.target.value)}
            >
              <option value="">すべての選挙区</option>
              {getUniqueConstituencyTypes().map(type => (
                <option key={type} value={type}>{getConstituencyTypeLabel(type)}</option>
              ))}
            </select>
          </div>

        </div>

        {/* 検索結果件数 */}
        <div className="mt-4 text-sm text-gray-600">
          {filteredCandidates.length}名の候補者が見つかりました
        </div>
      </div>

      {/* 候補者一覧 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {filteredCandidates.map(candidate => (
          <div key={candidate.candidate_id} className="bg-white rounded-lg shadow-sm border hover:shadow-md transition-shadow">
            <div className="p-6">
              {/* 候補者基本情報 */}
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

              {/* 選挙区情報 */}
              <div className="space-y-2 mb-4">
                <div className="flex items-center gap-2 text-sm text-gray-600">
                  <MapPin className="h-4 w-4" />
                  <span>{candidate.prefecture} - {getConstituencyTypeLabel(candidate.constituency_type)}</span>
                </div>
                {candidate.age_info && (
                  <div className="flex items-center gap-2 text-sm text-gray-600">
                    <Badge className="h-4 w-4" />
                    <span>年齢: {candidate.age_info}歳</span>
                  </div>
                )}
                {candidate.occupation && (
                  <div className="text-sm text-gray-600">
                    <span>職業: {candidate.occupation}</span>
                  </div>
                )}
              </div>

              {/* 経歴情報 */}
              {candidate.career && (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1">経歴</p>
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {candidate.career.slice(0, 120)}...
                  </p>
                </div>
              )}

              {/* 公式サイト・関連リンク */}
              {candidate.websites && candidate.websites.length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-1">関連サイト</p>
                  <div className="space-y-1">
                    {candidate.websites.slice(0, 3).map((website, index) => (
                      <a
                        key={`${candidate.candidate_id}-website-${index}`} // ユニークキーに変更
                        href={website.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                      >
                        <ExternalLink className="h-3 w-3" />
                        <span className="truncate">{website.title}</span>
                      </a>
                    ))}
                  </div>
                </div>
              )}


              {/* SNSアカウント */}
              {candidate.sns_accounts && Object.keys(candidate.sns_accounts).length > 0 && (
                <div className="mb-4">
                  <p className="text-xs text-gray-500 mb-2">SNSアカウント</p>
                  <div className="flex flex-wrap gap-2">
                    {Object.entries(candidate.sns_accounts)
                      .filter(([platform, url]) => platform && url) // 空のキーやURLを除外
                      .map(([platform, url], index) => (
                      <a
                        key={`${candidate.candidate_id}-sns-${platform}-${index}`} // ユニークキーに変更
                        href={url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs bg-blue-50 text-blue-700 px-2 py-1 rounded hover:bg-blue-100"
                      >
                        {platform.charAt(0).toUpperCase() + platform.slice(1)}
                      </a>
                    ))}
                  </div>
                </div>
              )}

              {/* リンク */}
              <div className="flex flex-wrap gap-2">
                {candidate.profile_url && (
                  <a
                    href={candidate.profile_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-blue-600 hover:text-blue-800"
                  >
                    <ExternalLink className="h-3 w-3" />
                    プロフィール詳細
                  </a>
                )}
                {candidate.official_website && (
                  <a
                    href={candidate.official_website}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-1 text-xs text-green-600 hover:text-green-800"
                  >
                    <ExternalLink className="h-3 w-3" />
                    公式サイト
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* 検索結果なしの場合 */}
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

      {/* データが全くない場合 */}
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
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            データを再読み込み
          </button>
        </div>
      )}
      </div>
    </>
  );
}