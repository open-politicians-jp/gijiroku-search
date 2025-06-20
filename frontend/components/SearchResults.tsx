'use client';

import { Speech } from '@/types';
import { Calendar, User, Users, Building, ExternalLink } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import SpeakerLink from './SpeakerLink';

interface SearchResultsProps {
  speeches: Speech[];
  total: number;
  loading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
  currentOffset?: number;
  limit?: number;
}

export default function SearchResults({ 
  speeches, 
  total, 
  loading = false, 
  onLoadMore, 
  hasMore = false, 
  currentOffset = 0, 
  limit = 50 
}: SearchResultsProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">検索中...</p>
        </div>
      </div>
    );
  }

  if (speeches.length === 0) {
    return (
      <div className="max-w-4xl mx-auto mt-8">
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <p className="text-gray-600 text-lg">検索結果が見つかりませんでした</p>
          <p className="text-gray-500 mt-2">検索条件を変更してお試しください</p>
        </div>
      </div>
    );
  }

  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'yyyy年MM月dd日');
    } catch {
      return dateString;
    }
  };

  const truncateText = (text: string, maxLength: number = 100) => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const getHouseDisplay = (house: string) => {
    const houseMap: { [key: string]: string } = {
      '衆議院': '衆',
      '参議院': '参',
      'House of Representatives': '衆',
      'House of Councillors': '参'
    };
    return houseMap[house] || house;
  };

  return (
    <div className="max-w-4xl mx-auto mt-8">
      {/* 検索結果サマリー */}
      <div className="mb-6 text-sm text-gray-600">
        <span className="font-medium text-gray-900">{total.toLocaleString()}</span>件の議事録が見つかりました
      </div>

      {/* 検索結果リスト */}
      <div className="space-y-4">
        {speeches.map((speech) => (
          <div key={speech.id} className="search-card">
            {/* ヘッダー情報 */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-4 text-xs sm:text-sm text-gray-600">
              <div className="flex items-center gap-1">
                <Calendar className="h-3 w-3 sm:h-4 sm:w-4" />
                <span className="text-xs sm:text-sm">{formatDate(speech.date)}</span>
              </div>
              
              {speech.house && (
                <div className="flex items-center gap-1">
                  <Building className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span className="text-xs sm:text-sm">{getHouseDisplay(speech.house)}</span>
                </div>
              )}

              {speech.committee && (
                <div className="flex items-center gap-1 max-w-32 sm:max-w-none">
                  <Building className="h-3 w-3 sm:h-4 sm:w-4" />
                  <span className="text-xs sm:text-sm truncate" title={speech.committee}>
                    {speech.committee.length > 8 ? speech.committee.substring(0, 8) + '...' : speech.committee}
                  </span>
                </div>
              )}

              {speech.session && (
                <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                  第{speech.session}回
                </span>
              )}
            </div>

            {/* 発言者情報 */}
            <div className="flex flex-wrap items-center gap-2 sm:gap-4 mb-3">
              <div className="flex items-center gap-2">
                <User className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                <SpeakerLink 
                  speakerName={speech.speaker} 
                  className="font-medium text-gray-900 text-sm sm:text-base"
                />
              </div>
              
              {speech.party && (
                <div className="flex items-center gap-2">
                  <Users className="h-4 w-4 sm:h-5 sm:w-5 text-gray-400" />
                  <span className="text-gray-600 text-sm sm:text-base">
                    {speech.party.length > 6 ? speech.party.substring(0, 6) + '...' : speech.party}
                  </span>
                </div>
              )}
            </div>

            {/* 発言内容 */}
            <div className="mb-4">
              <p className="text-gray-800 leading-relaxed text-sm sm:text-base">
                {truncateText(speech.text)}
              </p>
            </div>

            {/* アクション */}
            <div className="flex items-center justify-between pt-4 border-t border-gray-100">
              <div className="text-xs text-gray-500">
                ID: {speech.id}
              </div>
              
              {speech.url && (
                <a
                  href={speech.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium"
                >
                  全文を読む
                  <ExternalLink className="h-4 w-4" />
                </a>
              )}
            </div>
          </div>
        ))}
      </div>

      {/* ページネーション */}
      {(hasMore || speeches.length < total) && (
        <div className="mt-8 text-center">
          <div className="mb-4">
            <p className="text-gray-600">
              {currentOffset + 1}〜{currentOffset + speeches.length}件 / {total.toLocaleString()}件を表示中
            </p>
          </div>
          
          {hasMore && onLoadMore && (
            <button
              onClick={(e) => {
                e.preventDefault();
                // 現在の位置を記録
                const currentScrollY = window.scrollY;
                
                onLoadMore();
                
                // 新しいコンテンツが読み込まれた後、元の位置に戻る
                setTimeout(() => {
                  window.scrollTo({
                    top: currentScrollY,
                    behavior: 'smooth'
                  });
                }, 100);
              }}
              disabled={loading}
              className="inline-flex items-center px-6 py-3 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  読み込み中...
                </>
              ) : (
                `さらに${Math.min(limit, total - currentOffset - speeches.length)}件を表示`
              )}
            </button>
          )}
          
          {!hasMore && speeches.length < total && (
            <p className="text-sm text-gray-500 mt-2">
              より多くの結果を表示するには、検索条件を絞り込んでください
            </p>
          )}
        </div>
      )}
    </div>
  );
}