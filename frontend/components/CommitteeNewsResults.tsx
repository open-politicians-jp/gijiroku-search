'use client';

import { ExternalLink, Calendar, Building, Tag } from 'lucide-react';
import { CommitteeNews } from '@/types';

interface CommitteeNewsResultsProps {
  news: CommitteeNews[];
  total: number;
  loading?: boolean;
  hasMore?: boolean;
  loadingMore?: boolean;
  onLoadMore?: () => void;
}

export default function CommitteeNewsResults({ 
  news, 
  total, 
  loading = false, 
  hasMore = false,
  loadingMore = false,
  onLoadMore 
}: CommitteeNewsResultsProps) {
  if (loading) {
    return (
      <div className="max-w-4xl mx-auto px-4">
        <div className="animate-pulse space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="h-4 bg-gray-200 rounded w-3/4 mb-3"></div>
              <div className="h-3 bg-gray-200 rounded w-1/2 mb-2"></div>
              <div className="h-3 bg-gray-200 rounded w-1/4"></div>
            </div>
          ))}
        </div>
      </div>
    );
  }

  if (news.length === 0) {
    return (
      <div className="max-w-4xl mx-auto px-4 text-center py-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
          <p className="text-gray-500">検索条件に一致する委員会ニュースが見つかりませんでした。</p>
          <p className="text-sm text-gray-400 mt-2">
            検索キーワードや条件を変更してお試しください。
          </p>
        </div>
      </div>
    );
  }

  const formatDate = (dateStr: string | null) => {
    if (!dateStr) return '';
    try {
      return new Date(dateStr).toLocaleDateString('ja-JP');
    } catch {
      return dateStr;
    }
  };

  const formatCollectedDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('ja-JP', {
        year: 'numeric',
        month: 'numeric',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
      });
    } catch {
      return dateStr;
    }
  };

  const getNewsTypeColor = (newsType: string) => {
    switch (newsType) {
      case '委員会開催':
        return 'bg-blue-100 text-blue-800';
      case '採決結果':
        return 'bg-green-100 text-green-800';
      case '質疑応答':
        return 'bg-yellow-100 text-yellow-800';
      case '法案関連':
        return 'bg-purple-100 text-purple-800';
      case '参考人招致':
        return 'bg-indigo-100 text-indigo-800';
      case '現地調査':
        return 'bg-orange-100 text-orange-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4">
      {/* 検索結果ヘッダー */}
      <div className="mb-6">
        <h2 className="text-xl font-bold text-gray-900 mb-2">
          委員会ニュース検索結果
        </h2>
        <p className="text-gray-600">
          {total}件の委員会ニュースが見つかりました
        </p>
      </div>

      {/* ニュース一覧 */}
      <div className="space-y-4">
        {news.map((item, index) => (
          <div
            key={`${item.url}-${index}`}
            className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            {/* ニュースタイトル */}
            <div className="mb-3">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-lg font-semibold text-gray-900 hover:text-blue-600 transition-colors flex items-start gap-2"
              >
                <span className="flex-1">{item.title}</span>
                <ExternalLink className="h-4 w-4 mt-1 flex-shrink-0 text-gray-400" />
              </a>
            </div>

            {/* メタ情報 */}
            <div className="flex flex-wrap items-center gap-4 text-sm text-gray-500 mb-3">
              {/* 委員会 */}
              <div className="flex items-center gap-1">
                <Building className="h-4 w-4" />
                <span>{item.committee}</span>
              </div>

              {/* ニュースタイプ */}
              <div className="flex items-center gap-1">
                <Tag className="h-4 w-4" />
                <span className={`px-2 py-1 rounded-full text-xs font-medium ${getNewsTypeColor(item.news_type)}`}>
                  {item.news_type}
                </span>
              </div>

              {/* 日付 */}
              {item.date && (
                <div className="flex items-center gap-1">
                  <Calendar className="h-4 w-4" />
                  <span>{formatDate(item.date)}</span>
                </div>
              )}
            </div>

            {/* ニュース内容プレビュー */}
            {item.content && (
              <div className="mb-3">
                <p className="text-gray-700 text-sm line-clamp-3">
                  {item.content.substring(0, 200)}
                  {item.content.length > 200 ? '...' : ''}
                </p>
              </div>
            )}

            {/* フッター情報 */}
            <div className="flex items-center justify-between text-xs text-gray-400 pt-2 border-t border-gray-100">
              <span>
                {item.year}年第{item.week}週のニュース
              </span>
              <span>
                収集日時: {formatCollectedDate(item.collected_at)}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* もっと読み込むボタン */}
      {hasMore && (
        <div className="mt-8 text-center">
          <button
            onClick={onLoadMore}
            disabled={loadingMore}
            className="bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loadingMore ? '読み込み中...' : 'もっと読み込む'}
          </button>
          <p className="text-sm text-gray-500 mt-2">
            {news.length}件 / {total}件を表示中
          </p>
        </div>
      )}
      
      {/* 全件表示済みの場合 */}
      {!hasMore && news.length > 0 && (
        <div className="mt-8 text-center">
          <p className="text-sm text-gray-500">
            全{total}件を表示済み
          </p>
        </div>
      )}
    </div>
  );
}