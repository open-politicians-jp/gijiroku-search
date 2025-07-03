'use client';

import { useState } from 'react';
import { Search, Calendar, User, Users, Building } from 'lucide-react';
import { SearchParams } from '@/types';

interface SearchFormProps {
  onSearch: (params: SearchParams) => void;
  onSearchTypeChange?: () => void;
  loading?: boolean;
}

export default function SearchForm({ onSearch, onSearchTypeChange, loading = false }: SearchFormProps) {
  const [query, setQuery] = useState('');
  const [speaker, setSpeaker] = useState('');
  const [party, setParty] = useState('');
  const [committee, setCommittee] = useState('');
  const [dateFrom, setDateFrom] = useState('');
  const [dateTo, setDateTo] = useState('');
  const [searchType, setSearchType] = useState<'speeches' | 'committee_news' | 'bills' | 'questions'>('speeches');
  const [showAdvanced, setShowAdvanced] = useState(false);
  
  // 提出法案用フィールド
  const [billSubmitter, setBillSubmitter] = useState('');
  const [billStatus, setBillStatus] = useState('');
  
  // 質問主意書用フィールド
  const [questioner, setQuestioner] = useState('');
  const [sessionNumber, setSessionNumber] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const params: SearchParams = {
      q: query.trim() || undefined,
      speaker: searchType === 'speeches' ? speaker.trim() || undefined : undefined,
      party: searchType === 'speeches' ? party.trim() || undefined : undefined,
      committee: committee.trim() || undefined,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
      search_type: searchType,
      limit: searchType === 'speeches' ? 50 : 20,
      offset: 0,
      // 提出法案用パラメータ
      bill_submitter: searchType === 'bills' ? billSubmitter.trim() || undefined : undefined,
      bill_status: searchType === 'bills' ? billStatus.trim() || undefined : undefined,
      // 質問主意書用パラメータ
      questioner: searchType === 'questions' ? questioner.trim() || undefined : undefined,
      session_number: searchType === 'questions' ? sessionNumber.trim() || undefined : undefined
    };

    onSearch(params);
  };

  const handleSearchTypeChange = (newSearchType: 'speeches' | 'committee_news' | 'bills' | 'questions') => {
    setSearchType(newSearchType);
    onSearchTypeChange?.();
  };

  const handleReset = () => {
    setQuery('');
    setSpeaker('');
    setParty('');
    setCommittee('');
    setDateFrom('');
    setDateTo('');
    setBillSubmitter('');
    setBillStatus('');
    setQuestioner('');
    setSessionNumber('');
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
              onChange={(e) => handleSearchTypeChange(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
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
              onChange={(e) => handleSearchTypeChange(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
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
              onChange={(e) => handleSearchTypeChange(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
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
              onChange={(e) => handleSearchTypeChange(e.target.value as 'speeches' | 'committee_news' | 'bills' | 'questions')}
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
            
            {/* 議事録検索用フィールド */}
            {searchType === 'speeches' && (
              <>
                {/* 発言者 */}
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

                {/* 政党 */}
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
              </>
            )}

            {/* 提出法案検索用フィールド */}
            {searchType === 'bills' && (
              <>
                {/* 提出者 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <User className="inline h-4 w-4 mr-1" />
                    提出者
                  </label>
                  <input
                    type="text"
                    value={billSubmitter}
                    onChange={(e) => setBillSubmitter(e.target.value)}
                    placeholder="例：内閣、創新太郎君"
                    className="search-input"
                  />
                </div>

                {/* 審議状況 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Users className="inline h-4 w-4 mr-1" />
                    審議状況
                  </label>
                  <select
                    value={billStatus}
                    onChange={(e) => setBillStatus(e.target.value)}
                    className="search-input"
                  >
                    <option value="">すべての状況</option>
                    <option value="審議中">審議中</option>
                    <option value="可決">可決</option>
                    <option value="成立">成立</option>
                    <option value="否決">否決</option>
                    <option value="廃案">廃案</option>
                    <option value="継続審議">継続審議</option>
                  </select>
                </div>
              </>
            )}

            {/* 質問主意書検索用フィールド */}
            {searchType === 'questions' && (
              <>
                {/* 質問者 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <User className="inline h-4 w-4 mr-1" />
                    質問者
                  </label>
                  <input
                    type="text"
                    value={questioner}
                    onChange={(e) => setQuestioner(e.target.value)}
                    placeholder="例：創新太郎君"
                    className="search-input"
                  />
                </div>

                {/* 国会回次 */}
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Building className="inline h-4 w-4 mr-1" />
                    国会回次
                  </label>
                  <select
                    value={sessionNumber}
                    onChange={(e) => setSessionNumber(e.target.value)}
                    className="search-input"
                  >
                    <option value="">すべての回次</option>
                    <option value="217">第217回（臨時会）</option>
                    <option value="216">第216回（常会）</option>
                    <option value="215">第215回（臨時会）</option>
                    <option value="214">第214回（常会）</option>
                    <option value="213">第213回（臨時会）</option>
                  </select>
                </div>
              </>
            )}

            {/* 委員会（議事録・委員会ニュースのみ） */}
            {(searchType === 'speeches' || searchType === 'committee_news') && (
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Building className="inline h-4 w-4 mr-1" />
                  委員会
                </label>
                <select
                  value={committee}
                  onChange={(e) => setCommittee(e.target.value)}
                  className="search-input"
                >
                  <option value="">すべての委員会</option>
                  <optgroup label="常任委員会">
                    <option value="内閣委員会">内閣委員会</option>
                    <option value="総務委員会">総務委員会</option>
                    <option value="法務委員会">法務委員会</option>
                    <option value="外務委員会">外務委員会</option>
                    <option value="財務金融委員会">財務金融委員会</option>
                    <option value="文部科学委員会">文部科学委員会</option>
                    <option value="厚生労働委員会">厚生労働委員会</option>
                    <option value="農林水産委員会">農林水産委員会</option>
                    <option value="経済産業委員会">経済産業委員会</option>
                    <option value="国土交通委員会">国土交通委員会</option>
                    <option value="環境委員会">環境委員会</option>
                    <option value="安全保障委員会">安全保障委員会</option>
                    <option value="予算委員会">予算委員会</option>
                    <option value="決算行政監視委員会">決算行政監視委員会</option>
                    <option value="議院運営委員会">議院運営委員会</option>
                  </optgroup>
                  <optgroup label="特別委員会">
                    <option value="復興災害特別委員会">復興災害特別委員会</option>
                    <option value="政治改革特別委員会">政治改革特別委員会</option>
                    <option value="沖縄北方特別委員会">沖縄北方特別委員会</option>
                    <option value="拉致問題特別委員会">拉致問題特別委員会</option>
                    <option value="消費者特別委員会">消費者特別委員会</option>
                    <option value="原子力特別委員会">原子力特別委員会</option>
                    <option value="地方デジタル特別委員会">地方デジタル特別委員会</option>
                  </optgroup>
                  <optgroup label="調査会">
                    <option value="憲法調査会">憲法調査会</option>
                    <option value="科学技術・イノベーション調査会">科学技術・イノベーション調査会</option>
                  </optgroup>
                </select>
                
                {/* 院内検索リンク */}
                <div className="mt-2">
                  <a
                    href="https://www.shugiin.go.jp/internet/itdb_iinkai.nsf/html/iinkai/iin_j0000.htm"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <Building className="h-3 w-3" />
                    衆議院委員会情報（院内検索）
                  </a>
                </div>
              </div>
            )}

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
          </div>
        )}
      </form>
    </div>
  );
}