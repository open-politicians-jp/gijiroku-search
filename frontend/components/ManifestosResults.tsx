'use client';

import { Manifesto } from '@/types';
import { ExternalLink, Calendar, User, Tag } from 'lucide-react';

interface ManifestosResultsProps {
  manifestos: Manifesto[];
  total: number;
  loading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export default function ManifestosResults({
  manifestos,
  total,
  loading = false,
  onLoadMore,
  hasMore = false
}: ManifestosResultsProps) {
  
  if (loading && manifestos.length === 0) {
    return (
      <div className="flex items-center justify-center py-8">
        <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        <span className="ml-2 text-gray-600">マニフェストを検索中...</span>
      </div>
    );
  }

  if (manifestos.length === 0) {
    return (
      <div className="text-center py-8 text-gray-500">
        <p>マニフェストが見つかりませんでした。</p>
        <p className="text-sm mt-2">検索条件を変更してお試しください。</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <h2 className="text-lg font-semibold text-gray-800">
          マニフェスト検索結果
        </h2>
        <span className="text-sm text-gray-600">
          {total.toLocaleString()}件のマニフェスト
        </span>
      </div>

      <div className="space-y-4">
        {manifestos.map((manifesto, index) => (
          <div
            key={`${manifesto.party}-${manifesto.year}-${index}`}
            className="bg-white rounded-lg border border-gray-200 p-6 hover:shadow-md transition-shadow"
          >
            {/* ヘッダー情報 */}
            <div className="flex flex-wrap items-start justify-between gap-4 mb-4">
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-medium text-gray-900 mb-2">
                  {manifesto.title}
                </h3>
                
                <div className="flex flex-wrap items-center gap-4 text-sm text-gray-600">
                  <div className="flex items-center gap-1">
                    <User className="w-4 h-4" />
                    <span className="font-medium text-blue-600">{manifesto.party}</span>
                  </div>
                  
                  <div className="flex items-center gap-1">
                    <Calendar className="w-4 h-4" />
                    <span>{manifesto.year}年</span>
                  </div>
                  
                  {manifesto.category && (
                    <div className="flex items-center gap-1">
                      <Tag className="w-4 h-4" />
                      <span>{manifesto.category}</span>
                    </div>
                  )}
                </div>
              </div>
              
              {manifesto.url && (
                <a
                  href={manifesto.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium whitespace-nowrap"
                >
                  <ExternalLink className="w-4 h-4" />
                  公式ページ
                </a>
              )}
            </div>

            {/* 内容プレビュー */}
            <div className="border-t border-gray-100 pt-4">
              <div className="text-gray-700 text-sm leading-relaxed">
                <p className="line-clamp-4">
                  {manifesto.content.length > 300 
                    ? `${manifesto.content.substring(0, 300)}...` 
                    : manifesto.content
                  }
                </p>
              </div>
            </div>

            {/* 政党エイリアス表示 */}
            {manifesto.party_aliases && manifesto.party_aliases.length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-100">
                <div className="flex flex-wrap gap-1">
                  <span className="text-xs text-gray-500">別名:</span>
                  {manifesto.party_aliases.map((alias, aliasIndex) => (
                    <span
                      key={aliasIndex}
                      className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded"
                    >
                      {alias}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* 収集日時 */}
            <div className="mt-3 pt-3 border-t border-gray-100 flex justify-between items-center text-xs text-gray-500">
              <span>
                収集日時: {new Date(manifesto.collected_at).toLocaleDateString('ja-JP')}
              </span>
            </div>
          </div>
        ))}
      </div>

      {/* 読み込みボタン */}
      {hasMore && (
        <div className="text-center pt-6">
          <button
            onClick={onLoadMore}
            disabled={loading}
            className="inline-flex items-center px-6 py-3 border border-gray-300 rounded-md shadow-sm bg-white text-gray-700 hover:bg-gray-50 disabled:bg-gray-100 disabled:cursor-not-allowed transition-colors"
          >
            {loading ? (
              <>
                <div className="inline-block animate-spin rounded-full h-4 w-4 border-b-2 border-gray-600 mr-2"></div>
                読み込み中...
              </>
            ) : (
              'さらに読み込む'
            )}
          </button>
        </div>
      )}
    </div>
  );
}