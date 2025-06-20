'use client';

import { Legislator, HOUSE_LABELS, STATUS_LABELS } from '@/types/legislator';

interface LegislatorsListProps {
  legislators: Legislator[];
  isLoading: boolean;
}

export default function LegislatorsList({ legislators, isLoading }: LegislatorsListProps) {
  if (isLoading) {
    return (
      <div className="flex justify-center items-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        <span className="ml-3 text-gray-600">議員データを読み込み中...</span>
      </div>
    );
  }

  if (legislators.length === 0) {
    return (
      <div className="bg-gray-50 rounded-lg p-8 text-center">
        <p className="text-gray-500 text-lg">検索条件に該当する議員が見つかりませんでした。</p>
        <p className="text-gray-400 text-sm mt-2">フィルター条件を変更してお試しください。</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* 結果数表示 */}
      <div className="text-sm text-gray-600 mb-4">
        {legislators.length}件の議員が見つかりました
      </div>

      {/* 議員リスト */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {legislators.map((legislator) => (
          <div key={legislator.id} className="bg-white rounded-lg shadow-sm border border-gray-200 p-4 hover:shadow-md transition-shadow">
            {/* 議員名とステータス */}
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-semibold text-lg text-gray-900">
                {legislator.name}
              </h3>
              <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                legislator.status === 'active' 
                  ? 'bg-green-100 text-green-800' 
                  : 'bg-gray-100 text-gray-800'
              }`}>
                {STATUS_LABELS[legislator.status]}
              </span>
            </div>

            {/* 基本情報 */}
            <div className="space-y-2 text-sm">
              {/* 院・政党 */}
              <div className="flex items-center space-x-3">
                <span className={`px-2 py-1 rounded text-xs font-medium ${
                  legislator.house === 'shugiin' 
                    ? 'bg-red-100 text-red-800' 
                    : 'bg-purple-100 text-purple-800'
                }`}>
                  {HOUSE_LABELS[legislator.house]}
                </span>
                <span className="text-blue-600 font-medium">
                  {legislator.party}
                </span>
              </div>

              {/* 選挙区 */}
              <div className="text-gray-600">
                <span className="font-medium">選挙区:</span> {legislator.constituency}
                {legislator.region && (
                  <span className="text-gray-500"> ({legislator.region})</span>
                )}
              </div>

              {/* 初当選年・当選回数 */}
              <div className="text-gray-600">
                <span className="font-medium">初当選:</span> {legislator.electionYear}年
                {legislator.termCount && (
                  <span className="ml-2 text-blue-600">({legislator.termCount}期)</span>
                )}
              </div>

              {/* 役職 */}
              {legislator.positions && (
                <div className="text-gray-600 text-xs">
                  <span className="font-medium">役職:</span> {legislator.positions.length > 50 ? 
                    `${legislator.positions.substring(0, 50)}...` : 
                    legislator.positions
                  }
                </div>
              )}

              {/* 任期満了 */}
              {legislator.termEnd && (
                <div className="text-gray-500 text-xs">
                  任期満了: {legislator.termEnd}
                </div>
              )}

              {/* プロフィールリンク */}
              {legislator.profileUrl && (
                <div className="mt-2">
                  <a
                    href={legislator.profileUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-500 hover:text-blue-700 text-xs underline"
                  >
                    公式プロフィール →
                  </a>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}