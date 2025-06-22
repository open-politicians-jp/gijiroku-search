'use client';

import React, { useState, useEffect } from 'react';
import { Search, Filter, Calendar, Building, Users, FileText, Clock, Tag } from 'lucide-react';
import { MeetingSummary, SummarySearchParams } from '@/types';

interface SummariesPageProps {
  initialSummaries: MeetingSummary[];
  houses: string[];
  committees: string[];
  keywords: string[];
  stats: any;
}

interface SummaryCardProps {
  summary: MeetingSummary;
}

const SummaryCard: React.FC<SummaryCardProps> = ({ summary }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  
  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString('ja-JP', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    });
  };

  const parseStructuredSummary = (text: string) => {
    const sections = {
      overview: '',
      discussions: [] as string[],
      decisions: '',
      participants: '',
      notes: ''
    };

    const lines = text.split('\n');
    let currentSection = '';

    for (const line of lines) {
      if (line.includes('【会議概要】')) {
        currentSection = 'overview';
      } else if (line.includes('【主要な議論・審議内容】')) {
        currentSection = 'discussions';
      } else if (line.includes('【決定事項・結論】')) {
        currentSection = 'decisions';
      } else if (line.includes('【発言者・政党】')) {
        currentSection = 'participants';
      } else if (line.includes('【備考】')) {
        currentSection = 'notes';
      } else if (line.trim() && !line.includes('以下は')) {
        if (currentSection === 'overview' && line.trim()) {
          sections.overview += line.trim() + ' ';
        } else if (currentSection === 'discussions' && line.match(/^\d+\./)) {
          sections.discussions.push(line.trim());
        } else if (currentSection === 'decisions' && line.trim()) {
          sections.decisions += line.trim() + ' ';
        } else if (currentSection === 'participants' && line.trim()) {
          sections.participants += line.trim() + ' ';
        } else if (currentSection === 'notes' && line.trim()) {
          sections.notes += line.trim() + ' ';
        }
      }
    }

    return sections;
  };

  const parsedSummary = parseStructuredSummary(summary.summary.text);

  return (
    <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6 hover:shadow-lg transition-shadow">
      <div className="flex justify-between items-start mb-4">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900 mb-2">
            {summary.meeting_info.house} {summary.meeting_info.committee}
          </h3>
          <div className="flex items-center space-x-4 text-sm text-gray-600 mb-3">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              {formatDate(summary.meeting_info.date)}
            </div>
            <div className="flex items-center">
              <Building className="h-4 w-4 mr-1" />
              第{summary.meeting_info.session}回国会
            </div>
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-1" />
              {summary.metadata.speakers_count}名発言
            </div>
            <div className="flex items-center">
              <FileText className="h-4 w-4 mr-1" />
              {summary.metadata.speech_count}発言
            </div>
          </div>
        </div>
        <div className="flex items-center space-x-2 text-xs text-gray-500">
          <Clock className="h-3 w-3" />
          <span>{new Date(summary.metadata.generated_at).toLocaleDateString('ja-JP')}</span>
        </div>
      </div>

      {/* 要約概要 */}
      {parsedSummary.overview && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">会議概要</h4>
          <p className="text-gray-700 text-sm leading-relaxed">
            {parsedSummary.overview.trim()}
          </p>
        </div>
      )}

      {/* 主要議論（展開時のみ） */}
      {isExpanded && parsedSummary.discussions.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">主要な議論・審議内容</h4>
          <ul className="text-sm text-gray-700 space-y-1">
            {parsedSummary.discussions.map((discussion, index) => (
              <li key={index} className="leading-relaxed">{discussion}</li>
            ))}
          </ul>
        </div>
      )}

      {/* 決定事項（展開時のみ） */}
      {isExpanded && parsedSummary.decisions && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">決定事項・結論</h4>
          <p className="text-gray-700 text-sm leading-relaxed">
            {parsedSummary.decisions.trim()}
          </p>
        </div>
      )}

      {/* キーワード */}
      {summary.summary.keywords.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2 flex items-center">
            <Tag className="h-4 w-4 mr-1" />
            キーワード
          </h4>
          <div className="flex flex-wrap gap-2">
            {summary.summary.keywords.map((keyword, index) => (
              <span
                key={index}
                className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded-full"
              >
                {keyword}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 参加者情報（展開時のみ） */}
      {isExpanded && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">参加者</h4>
          <div className="text-sm text-gray-700">
            <div className="mb-2">
              <strong>発言者:</strong> {summary.participants.speakers.join(', ')}
            </div>
            <div>
              <strong>政党:</strong> {summary.participants.parties.join(', ')}
            </div>
          </div>
        </div>
      )}

      {/* 議事録リンク（展開時のみ） */}
      {isExpanded && summary.speeches_references.length > 0 && (
        <div className="mb-4">
          <h4 className="font-medium text-gray-900 mb-2">関連議事録</h4>
          <div className="max-h-32 overflow-y-auto">
            {summary.speeches_references.slice(0, 5).map((ref, index) => (
              <a
                key={index}
                href={ref.url}
                target="_blank"
                rel="noopener noreferrer"
                className="block text-sm text-blue-600 hover:text-blue-800 hover:underline mb-1"
              >
                {ref.speaker}の発言 →
              </a>
            ))}
            {summary.speeches_references.length > 5 && (
              <p className="text-xs text-gray-500">他{summary.speeches_references.length - 5}件</p>
            )}
          </div>
        </div>
      )}

      {/* 展開ボタン */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full mt-4 px-4 py-2 text-sm text-blue-600 bg-blue-50 hover:bg-blue-100 rounded-md transition-colors"
      >
        {isExpanded ? '詳細を閉じる' : '詳細を表示'}
      </button>
    </div>
  );
};

const SummariesPage: React.FC<SummariesPageProps> = ({
  initialSummaries,
  houses,
  committees,
  keywords,
  stats
}) => {
  const [summaries, setSummaries] = useState<MeetingSummary[]>(initialSummaries);
  const [searchParams, setSearchParams] = useState<SummarySearchParams>({});
  const [isLoading, setIsLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const handleSearch = async (newParams: SummarySearchParams) => {
    setIsLoading(true);
    try {
      // 静的エクスポート対応: クライアントサイドローダーを使用
      const { SummariesClientLoader } = await import('@/lib/summaries-client-loader');
      const result = await SummariesClientLoader.searchSummaries(newParams);
      setSummaries(result.summaries);
      setSearchParams(newParams);
    } catch (error) {
      console.error('検索エラー:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      {/* ヘッダー */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          議会要約検索 <span className="text-sm font-normal text-blue-600 bg-blue-100 px-2 py-1 rounded">Beta</span>
        </h1>
        <p className="text-gray-600">
          国会議事録をAIが議会単位で要約しています。重要な議論と決定事項を効率的に把握できます。
        </p>
      </div>

      {/* 統計情報 */}
      <div className="bg-blue-50 rounded-lg p-4 mb-6">
        <h2 className="font-semibold text-blue-900 mb-2">要約統計</h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div>
            <span className="text-blue-700 font-medium">要約済み議会:</span>
            <span className="ml-2 text-blue-900">{stats.total_summaries}議会</span>
          </div>
          <div>
            <span className="text-blue-700 font-medium">対象院:</span>
            <span className="ml-2 text-blue-900">{stats.houses.join(', ')}</span>
          </div>
          <div>
            <span className="text-blue-700 font-medium">委員会数:</span>
            <span className="ml-2 text-blue-900">{stats.committees.length}委員会</span>
          </div>
          <div>
            <span className="text-blue-700 font-medium">期間:</span>
            <span className="ml-2 text-blue-900">
              {stats.date_range.from} 〜 {stats.date_range.to}
            </span>
          </div>
        </div>
      </div>

      {/* 検索フォーム */}
      <div className="bg-white rounded-lg shadow-md border p-6 mb-6">
        <div className="flex items-center space-x-4 mb-4">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
            <input
              type="text"
              placeholder="要約内容、委員会名、キーワードで検索..."
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              value={searchParams.q || ''}
              onChange={(e) => handleSearch({ ...searchParams, q: e.target.value, offset: 0 })}
            />
          </div>
          <button
            onClick={() => setShowFilters(!showFilters)}
            className="flex items-center px-4 py-2 text-gray-700 bg-gray-100 hover:bg-gray-200 rounded-md transition-colors"
          >
            <Filter className="h-4 w-4 mr-2" />
            フィルター
          </button>
        </div>

        {/* フィルター */}
        {showFilters && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-4 border-t">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">院</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                value={searchParams.house || ''}
                onChange={(e) => handleSearch({ ...searchParams, house: e.target.value, offset: 0 })}
              >
                <option value="">すべて</option>
                {houses.map(house => (
                  <option key={house} value={house}>{house}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">委員会</label>
              <select
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                value={searchParams.committee || ''}
                onChange={(e) => handleSearch({ ...searchParams, committee: e.target.value, offset: 0 })}
              >
                <option value="">すべて</option>
                {committees.map(committee => (
                  <option key={committee} value={committee}>{committee}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">日付範囲</label>
              <div className="flex space-x-2">
                <input
                  type="date"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  value={searchParams.date_from || ''}
                  onChange={(e) => handleSearch({ ...searchParams, date_from: e.target.value, offset: 0 })}
                />
                <input
                  type="date"
                  className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                  value={searchParams.date_to || ''}
                  onChange={(e) => handleSearch({ ...searchParams, date_to: e.target.value, offset: 0 })}
                />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 検索結果 */}
      <div className="space-y-6">
        {isLoading ? (
          <div className="text-center py-8">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            <p className="mt-2 text-gray-600">検索中...</p>
          </div>
        ) : summaries.length > 0 ? (
          summaries.map((summary, index) => (
            <SummaryCard key={summary.metadata.meeting_key} summary={summary} />
          ))
        ) : (
          <div className="text-center py-8 text-gray-500">
            <FileText className="h-12 w-12 mx-auto mb-4 text-gray-300" />
            <p>該当する議会要約が見つかりませんでした。</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default SummariesPage;