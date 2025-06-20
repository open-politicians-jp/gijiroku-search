'use client';

import { useState, useEffect } from 'react';
import { Users } from 'lucide-react';
import { Legislator, LegislatorFilter, LegislatorsData } from '@/types/legislator';
import { legislatorsLoader } from '@/lib/legislators-loader';
import LegislatorsFilter from '@/components/LegislatorsFilter';
import LegislatorsList from '@/components/LegislatorsList';

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
  const [houseCounts, setHouseCounts] = useState<{ shugiin: number; sangiin: number; total: number }>();

  // データ読み込み
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      try {
        const [data, counts] = await Promise.all([
          legislatorsLoader.loadLegislators(),
          legislatorsLoader.getHouseCounts()
        ]);
        
        setLegislatorsData(data);
        setHouseCounts(counts);
      } catch (error) {
        console.error('Error loading legislators data:', error);
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

  return (
    <div className="py-8">
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
          {legislatorsData && (
            <div className="mt-4 p-4 bg-blue-50 rounded-lg">
              <div className="text-sm text-blue-800">
                <p>
                  <span className="font-medium">データ更新日:</span>{' '}
                  {new Date(legislatorsData.metadata.last_updated).toLocaleDateString('ja-JP')}
                </p>
                <p>
                  <span className="font-medium">データソース:</span>{' '}
                  {legislatorsData.metadata.data_source === 'mock_csv_data' ? 'サンプルデータ' : legislatorsData.metadata.data_source}
                </p>
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
    </div>
  );
}