'use client';

import { useState, useEffect } from 'react';
import { Manifesto } from '@/types';
import { dataLoader } from '@/lib/data-loader';
import { Search, FileText, Users, Calendar, ExternalLink } from 'lucide-react';

export default function ManifestosPage() {
  const [manifestos, setManifestos] = useState<Manifesto[]>([]);
  const [filteredManifestos, setFilteredManifestos] = useState<Manifesto[]>([]);
  const [selectedParty, setSelectedParty] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // 政党リスト
  const parties = [
    '自由民主党',
    '立憲民主党', 
    '日本維新の会',
    '公明党',
    '日本共産党',
    '国民民主党',
    'れいわ新選組'
  ];

  useEffect(() => {
    loadManifestos();
  }, []);

  useEffect(() => {
    if (selectedParty) {
      const filtered = manifestos.filter(manifesto => 
        manifesto.party === selectedParty ||
        (manifesto.party_aliases && manifesto.party_aliases.includes(selectedParty))
      );
      setFilteredManifestos(filtered);
    } else {
      setFilteredManifestos(manifestos);
    }
  }, [selectedParty, manifestos]);

  const loadManifestos = async () => {
    try {
      setLoading(true);
      const data = await dataLoader.loadManifestos();
      setManifestos(data);
      setFilteredManifestos(data);
    } catch (err) {
      console.error('マニフェスト読み込みエラー:', err);
      setError('マニフェストデータの読み込みに失敗しました');
    } finally {
      setLoading(false);
    }
  };

  const handlePartyChange = (party: string) => {
    setSelectedParty(party);
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-16">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">マニフェストデータを読み込み中...</p>
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center py-16">
            <div className="text-red-500 mb-4">
              <FileText className="h-16 w-16 mx-auto" />
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">エラー</h2>
            <p className="text-gray-600">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">政党マニフェスト</h1>
          <p className="text-gray-600">各政党の政策・公約を確認できます</p>
        </div>

        {/* 政党選択 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center mb-4">
            <Users className="h-5 w-5 text-blue-600 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">政党選択</h2>
          </div>
          
          <div className="flex flex-wrap gap-2">
            <button
              onClick={() => handlePartyChange('')}
              className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                selectedParty === '' 
                  ? 'bg-blue-600 text-white' 
                  : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
              }`}
            >
              すべて
            </button>
            {parties.map((party) => (
              <button
                key={party}
                onClick={() => handlePartyChange(party)}
                className={`px-4 py-2 rounded-full text-sm font-medium transition-colors ${
                  selectedParty === party 
                    ? 'bg-blue-600 text-white' 
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                {party}
              </button>
            ))}
          </div>
        </div>

        {/* 結果表示 */}
        <div className="mb-4">
          <p className="text-sm text-gray-600">
            {selectedParty ? `${selectedParty}: ` : ''}
            {filteredManifestos.length}件のマニフェスト
          </p>
        </div>

        {/* マニフェスト一覧 */}
        <div className="space-y-4">
          {filteredManifestos.length === 0 ? (
            <div className="text-center py-16">
              <FileText className="h-16 w-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">マニフェストが見つかりません</h3>
              <p className="text-gray-600">選択した政党のマニフェストがありません。</p>
            </div>
          ) : (
            filteredManifestos.map((manifesto, index) => (
              <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">
                      {manifesto.title}
                    </h3>
                    <div className="flex items-center text-sm text-gray-600 space-x-4 mb-3">
                      <span className="flex items-center">
                        <Users className="h-4 w-4 mr-1" />
                        {manifesto.party}
                      </span>
                      <span className="flex items-center">
                        <Calendar className="h-4 w-4 mr-1" />
                        {manifesto.year}年
                      </span>
                      {manifesto.category && (
                        <span className="bg-blue-100 text-blue-800 px-2 py-1 rounded-full text-xs">
                          {manifesto.category}
                        </span>
                      )}
                    </div>
                  </div>
                </div>
                
                <div className="text-gray-700 mb-4">
                  <p className="line-clamp-3">
                    {manifesto.content.length > 200 
                      ? `${manifesto.content.substring(0, 200)}...` 
                      : manifesto.content
                    }
                  </p>
                </div>
                
                {manifesto.url && (
                  <div className="flex justify-end">
                    <a
                      href={manifesto.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center text-blue-600 hover:text-blue-800 text-sm font-medium"
                    >
                      詳細を見る
                      <ExternalLink className="h-4 w-4 ml-1" />
                    </a>
                  </div>
                )}
              </div>
            ))
          )}
        </div>
      </div>
    </div>
  );
}