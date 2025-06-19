'use client';

import { useState } from 'react';
import { Search, Calendar, User, Users, Building } from 'lucide-react';
import { SearchParams } from '@/types';

interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
  loading?: boolean;
}

export default function SearchForm({ onSearch, loading = false }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [speaker, setSpeaker] = useState('');
  const [party, setParty] = useState('');
  const [committee, setCommittee] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [includeMeetingInfo, setIncludeMeetingInfo] = useState(false);
  const [searchType, setSearchType] = useState<'speeches' | 'committee_news' | 'bills' | 'questions'>('speeches');
  const [showAdvanced, setShowAdvanced] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const params: SearchParams = {
      q: query.trim() || undefined,
      speaker: searchType === 'speeches' ? speaker.trim() || undefined : undefined,
      party: searchType === 'speeches' ? party.trim() || undefined : undefined,
      committee: committee.trim() || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      include_meeting_info: searchType === 'speeches' ? includeMeetingInfo : undefined,
      search_type: searchType,
      limit: searchType === 'speeches' ? 50 : 20,
      offset: 0
    };

    onSearch(params);
  };

  const handleReset = () => {
    setQuery('');
    setSpeaker('');
    setParty('');
    setCommittee('');
    setDateFrom('');
    setDateTo('');
    setShowAdvanced(false);
  };

  return (
    <div className="search-card max-w-4xl mx-auto">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* 検索タイプ選択 */}
        <div className="flex flex-wrap gap-4 mb-4">
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="searchType"
              value="speeches"
              checked={searchType === 'speeches'}
              onChange={(e) => setSearchType(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700">議事録</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="searchType"
              value="committee_news"
              checked={searchType === 'committee_news'}
              onChange={(e) => setSearchType(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700">委員会活動</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="searchType"
              value="bills"
              checked={searchType === 'bills'}
              onChange={(e) => setSearchType(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700">提出法案</span>
          </label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="radio"
              name="searchType"
              value="questions"
              checked={searchType === 'questions'}
              onChange={(e) => setSearchType(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
              className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 focus:ring-blue-500 focus:ring-2"
            />
            <span className="text-sm font-medium text-gray-700">質問主意書</span>
          </label>
        </div>

        {/* メイン検索ボックス */}
        <div className="relative">
          <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
            <Search className="h-5 w-5 text-gray-400" />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder={
              searchType === 'speeches' ? "議事録を検索（例：デジタル改革、社会保障制度、環境政策）" :
              searchType === 'committee_news' ? "委員会ニュースを検索（例：法案審議、委員会開催）" :
              searchType === 'bills' ? "提出法案を検索（例：デジタル庁設置法、環境基本法改正案）" :
              "質問主意書を検索（例：年金制度、外交政策、エネルギー問題）"
            }
            className="search-input pl-10"
          />
        </div>

        {/* 詳細検索トグル */}
        <div className="flex items-center justify-between">
          <button
            type="button"
            onClick={() => setShowAdvanced(!showAdvanced)}
            className="text-blue-600 hover:text-blue-700 text-sm font-medium"
          >
            {showAdvanced ? '詳細検索を閉じる' : '詳細検索を開く'}
          </button>
          
          <div className="flex gap-3">
            <button
              type="button"
              onClick={handleReset}
              className="filter-button"
            >
              リセット
            </button>
            <button
              type="submit"
              disabled={loading}
              className="search-button disabled:bg-gray-400"
            >
              {loading ? '検索中...' : '検索'}
            </button>
          </div>
        </div>

        {/* 詳細検索フィールド */}
        {showAdvanced && (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 pt-4 border-t border-gray-200">
            {/* 発言者（議事録検索のみ） */}
            {searchType === 'speeches' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <User className="inline h-4 w-4 mr-1" />
                  発言者
                </label>
                <input
                  type="text"
                  value={speaker}
                  onChange={(e) => setSpeaker(e.target.value)}
                  placeholder="例：創新太郎"
                  className="search-input"
                />
              </div>
            )}

            {/* 政党（議事録検索のみ） */}
            {searchType === 'speeches' && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Users className="inline h-4 w-4 mr-1" />
                  政党
                </label>
                <input
                  type="text"
                  value={party}
                  onChange={(e) => setParty(e.target.value)}
                  placeholder="例：創新党、自民、立民"
                  className="search-input"
                />
              </div>
            )}

            {/* 委員会 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Building className="inline h-4 w-4 mr-1" />
                委員会
              </label>
              <input
                type="text"
                value={committee}
                onChange={(e) => setCommittee(e.target.value)}
                placeholder={
                  searchType === 'speeches' ? "例：政治改革特別委員会" :
                  searchType === 'committee_news' ? "例：内閣委員会、予算委員会" :
                  "例：内閣委員会、法務委員会"
                }
                className="search-input"
              />
            </div>

            {/* 開始日 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="inline h-4 w-4 mr-1" />
                開始日
              </label>
              <input
                type="date"
                value={dateFrom}
                onChange={(e) => setDateFrom(e.target.value)}
                className="search-input"
              />
            </div>

            {/* 終了日 */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                <Calendar className="inline h-4 w-4 mr-1" />
                終了日
              </label>
              <input
                type="date"
                value={dateTo}
                onChange={(e) => setDateTo(e.target.value)}
                className="search-input"
              />
            </div>
            
            {/* 会議録情報を含める（議事録検索のみ） */}
            {searchType === 'speeches' && (
              <div className="col-span-2">
                <label className="flex items-center gap-2 text-sm text-gray-700 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={includeMeetingInfo}
                    onChange={(e) => setIncludeMeetingInfo(e.target.checked)}
                    className="w-4 h-4 text-blue-600 bg-gray-100 border-gray-300 rounded focus:ring-blue-500 focus:ring-2"
                  />
                  会議録情報を含める（委員名簿、出席者リスト等）
                </label>
              </div>
            )}
          </div>
        )}
      </form>
    </div>
  );
}