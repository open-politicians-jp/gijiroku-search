'use client';

import { useState, useEffect } from 'react';
import { Users } from 'lucide-react';
import { Legislator, LegislatorFilter, LegislatorsData } from '@/types/legislator';
import { legislatorsLoader } from '@/lib/legislators-loader';
import LegislatorsFilter from '@/components/LegislatorsFilter';
import LegislatorsList from '@/components/LegislatorsList';
import Header from '@/components/Header';

export default function LegislatorsPage() {
  const [legislatorsData, setLegislatorsData] = useState<LegislatorsData | null>(null);
  const [filteredLegislators, setFilteredLegislators] = useState<Legislator[]>([]);
  const [filter, setFilter] = useState<LegislatorFilter>({
    house: 'all',
    party: 'all',
    search: '',
    status: 'all'
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [houseCounts, setHouseCounts] = useState<{ shugiin: number; sangiin: number; total: number }>();

  // データ読み込み
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [data, counts] = await Promise.all([
          legislatorsLoader.loadLegislators(),
          legislatorsLoader.getHouseCounts()
        ]);
        
        if (data) {
          setLegislatorsData(data);
        }
        if (counts) {
          setHouseCounts(counts);
        }
      } catch (err) {
        const errorMessage = '議員データの読み込みに失敗しました。しばらく時間をおいて再度お試しください。';
        console.warn('議員データの読み込みに失敗しました:', err);
        setError(errorMessage);
        
        // Fallback: Set empty data to prevent crashes with proper error state
        setLegislatorsData({
          metadata: {
            total_count: 0,
            last_updated: new Date().toISOString(),
            data_source: 'エラー時フォールバック',
            sangiin_count: 0,
            shugiin_count: 0
          },
          data: []
        });
        // Set empty house counts as fallback
        setHouseCounts({ shugiin: 0, sangiin: 0, total: 0 });
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  }, []);

  // フィルタリング処理
  useEffect(() => {
    if (!legislatorsData) return;

    const filtered = legislatorsLoader.filterLegislators(legislatorsData.data, filter);
    setFilteredLegislators(filtered);
  }, [legislatorsData, filter]);

  const handleFilterChange = (newFilter: LegislatorFilter) => {
    setFilter(newFilter);
  };

  const handleRetry = () => {
    const loadData = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const [data, counts] = await Promise.all([
          legislatorsLoader.loadLegislators(),
          legislatorsLoader.getHouseCounts()
        ]);
        
        if (data) {
          setLegislatorsData(data);
        }
        if (counts) {
          setHouseCounts(counts);
        }
      } catch (err) {
        const errorMessage = '議員データの読み込みに失敗しました。しばらく時間をおいて再度お試しください。';
        console.warn('議員データの読み込みに失敗しました:', err);
        setError(errorMessage);
      } finally {
        setIsLoading(false);
      }
    };

    loadData();
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="legislators" />
      <main className="py-8 pt-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* ヘッダー */}
        <div className="mb-8">
          <div className="flex items-center mb-4">
            <Users className="w-8 h-8 text-blue-500 mr-3" />
            <h1 className="text-3xl font-bold text-gray-900">国会議員一覧</h1>
          </div>
          <p className="text-gray-600">
            国会議員の基本情報を院別・政党別に検索できます。
          </p>
          
          {/* データ情報 */}
          {legislatorsData && legislatorsData.metadata && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-800">
                <p>
                  <span className="font-medium">データ更新日:</span>{' '}
                  {new Date(legislatorsData.metadata.last_updated).toLocaleDateString('ja-JP')}
                </p>
                <p>
                  <span className="font-medium">参議院議員数:</span>{' '}
                  {legislatorsData.metadata.sangiin_count || 0}名
                  {legislatorsData.metadata.shugiin_count !== undefined && (
                    <span>、衆議院議員数: {legislatorsData.metadata.shugiin_count}名</span>
                  )}
                </p>
                <p>
                  <span className="font-medium">データソース:</span>{' '}
                  <a 
                    href="https://smartnews-smri.github.io/house-of-councillors/" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 underline"
                  >
                    SmartNews Media Research Institute
                  </a>
                </p>
              </div>
            </div>
          )}

          {/* エラー表示 */}
          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="flex items-center">
                  <Users className="h-5 w-5 text-red-500 mr-2" />
                  <p className="text-red-700 text-sm">{error}</p>
                </div>
                <button
                  onClick={handleRetry}
                  disabled={isLoading}
                  className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 disabled:bg-gray-400 transition-colors"
                >
                  {isLoading ? '読み込み中...' : '再試行'}
                </button>
              </div>
            </div>
          )}
        </div>

        {/* フィルター */}
        <LegislatorsFilter
          filter={filter}
          onFilterChange={handleFilterChange}
          houseCounts={houseCounts}
        />

        {/* 議員一覧 */}
        <LegislatorsList
          legislators={filteredLegislators}
          isLoading={isLoading}
        />
        </div>
      </main>
    </div>
  );
}