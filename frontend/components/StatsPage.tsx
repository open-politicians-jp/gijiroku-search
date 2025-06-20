'use client';

import { useEffect, useState } from 'react';
import { Stats } from '@/types';
import { apiClient } from '@/lib/api';
import { BarChart3, Users, MessageSquare, Clock } from 'lucide-react';
import { format, parseISO } from 'date-fns';

export default function StatsPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        setLoading(true);
        setError(null);
        console.log('StatsPage: Starting to fetch stats...');
        
        const data = await apiClient.getStats();
        console.log('StatsPage: Received stats data:', {
          total_speeches: data.total_speeches,
          top_parties_count: data.top_parties ? data.top_parties.length : 0,
          top_speakers_count: data.top_speakers ? data.top_speakers.length : 0,
          top_committees_count: data.top_committees ? data.top_committees.length : 0,
          date_range: data.date_range,
          last_updated: data.last_updated
        });
        
        // データ検証
        if (!data || typeof data !== 'object') {
          throw new Error('無効な統計データを受信しました');
        }
        
        if (data.total_speeches === 0) {
          console.warn('StatsPage: Received stats with 0 speeches');
        }
        
        setStats(data);
      } catch (err) {
        console.error('StatsPage: Error fetching stats:', err);
        const errorMessage = err instanceof Error ? err.message : '統計情報の取得に失敗しました';
        setError(`統計データの読み込みエラー: ${errorMessage}`);
      } finally {
        setLoading(false);
      }
    };

    fetchStats();
  }, []);

  const formatLastUpdated = (dateString: string | null) => {
    if (!dateString) return '未更新';
    try {
      return format(parseISO(dateString), 'yyyy年MM月dd日 HH:mm');
    } catch {
      return dateString;
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">統計情報を読み込み中...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <p className="text-red-600">{error}</p>
        </div>
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <p className="text-gray-600">統計情報がありません</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* ページタイトル */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">統計情報</h1>
        <p className="text-gray-600">
          収集された議事録データの統計情報を表示しています
        </p>
      </div>

      {/* サマリー統計 */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <MessageSquare className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">総議事録数</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.total_speeches.toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-green-100 rounded-lg">
              <Users className="h-6 w-6 text-green-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">政党数</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.top_parties?.length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-blue-100 rounded-lg">
              <Users className="h-6 w-6 text-blue-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">発言者数</p>
              <p className="text-2xl font-bold text-gray-900">
                {stats.top_speakers?.length || 0}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <div className="p-2 bg-purple-100 rounded-lg">
              <Clock className="h-6 w-6 text-purple-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-600">最終更新</p>
              <p className="text-sm font-bold text-gray-900">
                {formatLastUpdated(stats.last_updated)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* 詳細統計 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* 政党別発言数 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-6">
            <BarChart3 className="h-5 w-5 text-gray-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">政党別発言数（上位10位）</h2>
          </div>
          
          <div className="space-y-3">
            {stats.top_parties && stats.top_parties.length > 0 ? stats.top_parties.slice(0, 10).map(([party, count], index) => {
              const maxCount = stats.top_parties[0]?.[1] || 1;
              const percentage = (count / maxCount) * 100;
              
              return (
                <div key={party} className="flex items-center">
                  <div className="w-4 text-sm text-gray-500 mr-2">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {party || '未分類'}
                      </span>
                      <span className="text-sm text-gray-600 ml-2">
                        {count.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            }) : (
              <p className="text-gray-500 text-sm">政党データがありません</p>
            )}
          </div>
        </div>

        {/* 発言者別発言数 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-6">
            <Users className="h-5 w-5 text-gray-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">発言者別発言数（上位10位）</h2>
          </div>
          
          <div className="space-y-3">
            {stats.top_speakers && stats.top_speakers.length > 0 ? stats.top_speakers.slice(0, 10).map(([speaker, count], index) => {
              const maxCount = stats.top_speakers[0]?.[1] || 1;
              const percentage = (count / maxCount) * 100;
              
              return (
                <div key={speaker} className="flex items-center">
                  <div className="w-4 text-sm text-gray-500 mr-2">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {speaker || '不明'}
                      </span>
                      <span className="text-sm text-gray-600 ml-2">
                        {count.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-green-600 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            }) : (
              <p className="text-gray-500 text-sm">発言者データがありません</p>
            )}
          </div>
        </div>

        {/* 委員会別発言数 */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center mb-6">
            <MessageSquare className="h-5 w-5 text-gray-400 mr-2" />
            <h2 className="text-lg font-semibold text-gray-900">委員会別発言数（上位10位）</h2>
          </div>
          
          <div className="space-y-3">
            {stats.top_committees && stats.top_committees.length > 0 ? stats.top_committees.slice(0, 10).map(([committee, count], index) => {
              const maxCount = stats.top_committees[0]?.[1] || 1;
              const percentage = (count / maxCount) * 100;
              
              return (
                <div key={committee} className="flex items-center">
                  <div className="w-4 text-sm text-gray-500 mr-2">
                    {index + 1}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-900 truncate">
                        {committee || '未分類'}
                      </span>
                      <span className="text-sm text-gray-600 ml-2">
                        {count.toLocaleString()}
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                </div>
              );
            }) : (
              <p className="text-gray-500 text-sm">委員会データがありません</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}