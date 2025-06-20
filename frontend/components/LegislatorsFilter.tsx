'use client';

import { useState, useEffect } from 'react';
import { Search, Filter, Users, Building } from 'lucide-react';
import { LegislatorFilter, HOUSE_LABELS, STATUS_LABELS } from '@/types/legislator';
import { legislatorsLoader } from '@/lib/legislators-loader';

interface LegislatorsFilterProps {
  filter: LegislatorFilter;
  onFilterChange: (filter: LegislatorFilter) => void;
  houseCounts?: { shugiin: number; sangiin: number; total: number };
}

export default function LegislatorsFilter({ 
  filter, 
  onFilterChange,
  houseCounts 
}: LegislatorsFilterProps) {
  const [parties, setParties] = useState<string[]>([]);
  const [isExpanded, setIsExpanded] = useState(false);

  useEffect(() => {
    // 政党リストを読み込み
    legislatorsLoader.getUniqueParties().then(setParties);
  }, []);

  const handleSearchChange = (search: string) => {
    onFilterChange({ ...filter, search });
  };

  const handleHouseChange = (house: 'shugiin' | 'sangiin' | 'all') => {
    onFilterChange({ ...filter, house });
  };

  const handlePartyChange = (party: string) => {
    onFilterChange({ ...filter, party });
  };

  const handleStatusChange = (status: 'active' | 'inactive' | 'all') => {
    onFilterChange({ ...filter, status });
  };

  const clearFilters = () => {
    onFilterChange({ house: 'all', party: 'all', search: '', status: 'all' });
  };

  const hasActiveFilters = filter.house !== 'all' || filter.party !== 'all' || 
                          filter.search || filter.status !== 'all';

  return (
    <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 mb-6">
      {/* 検索バー */}
      <div className="relative mb-4">
        <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-5 h-5" />
        <input
          type="text"
          placeholder="議員名、政党、選挙区で検索..."
          value={filter.search || ''}
          onChange={(e) => handleSearchChange(e.target.value)}
          className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
        />
      </div>

      {/* 院別タブ */}
      <div className="flex flex-wrap gap-2 mb-4">
        <button
          onClick={() => handleHouseChange('all')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter.house === 'all'
              ? 'bg-blue-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Users className="inline-block w-4 h-4 mr-1" />
          全て {houseCounts && `(${houseCounts.total})`}
        </button>
        <button
          onClick={() => handleHouseChange('shugiin')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter.house === 'shugiin'
              ? 'bg-red-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Building className="inline-block w-4 h-4 mr-1" />
          {HOUSE_LABELS.shugiin} {houseCounts && `(${houseCounts.shugiin})`}
        </button>
        <button
          onClick={() => handleHouseChange('sangiin')}
          className={`px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
            filter.house === 'sangiin'
              ? 'bg-purple-500 text-white'
              : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
          }`}
        >
          <Building className="inline-block w-4 h-4 mr-1" />
          {HOUSE_LABELS.sangiin} {houseCounts && `(${houseCounts.sangiin})`}
        </button>
      </div>

      {/* 詳細フィルター */}
      <div className="border-t pt-4">
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="flex items-center text-sm text-gray-600 hover:text-gray-800 mb-3"
        >
          <Filter className="w-4 h-4 mr-2" />
          詳細フィルター
          <span className="ml-2 text-xs text-gray-400">
            {isExpanded ? '▲' : '▼'}
          </span>
        </button>

        {isExpanded && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 政党フィルター */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                政党
              </label>
              <select
                value={filter.party || 'all'}
                onChange={(e) => handlePartyChange(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="all">全ての政党</option>
                {parties.map((party) => (
                  <option key={party} value={party}>
                    {party}
                  </option>
                ))}
              </select>
            </div>

            {/* ステータスフィルター */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                在職状況
              </label>
              <select
                value={filter.status || 'all'}
                onChange={(e) => handleStatusChange(e.target.value as 'active' | 'inactive' | 'all')}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent text-sm"
              >
                <option value="all">全て</option>
                <option value="active">{STATUS_LABELS.active}</option>
                <option value="inactive">{STATUS_LABELS.inactive}</option>
              </select>
            </div>
          </div>
        )}
      </div>

      {/* フィルタークリア */}
      {hasActiveFilters && (
        <div className="border-t pt-3 mt-3">
          <button
            onClick={clearFilters}
            className="text-sm text-gray-500 hover:text-gray-700 underline"
          >
            フィルターをクリア
          </button>
        </div>
      )}
    </div>
  );
}