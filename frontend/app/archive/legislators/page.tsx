'use client';

import { useEffect, useMemo, useState } from 'react';
import Header from '@/components/Header';
import { Users, History } from 'lucide-react';
import { Legislator, LegislatorsData, LegislatorFilter } from '@/types/legislator';
import { legislatorsLoader } from '@/lib/legislators-loader';
import LegislatorsFilter from '@/components/LegislatorsFilter';
import LegislatorsList from '@/components/LegislatorsList';
import { useSearchParams } from 'next/navigation';

export default function ArchivedLegislatorsPage() {
  const [data, setData] = useState<LegislatorsData | null>(null);
  const [filtered, setFiltered] = useState<Legislator[]>([]);
  const [filter, setFilter] = useState<LegislatorFilter>({
    house: 'sangiin',
    party: 'all',
    search: '',
    status: 'all',
  });
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const searchParams = useSearchParams();
  const archiveDate = useMemo(() => searchParams.get('date') || '20250720', [searchParams]);
  const archiveDateDisplay = useMemo(() => {
    if (/^\d{8}$/.test(archiveDate)) {
      return `${archiveDate.slice(0,4)}/${archiveDate.slice(4,6)}/${archiveDate.slice(6,8)}`;
    }
    return archiveDate;
  }, [archiveDate]);

  useEffect(() => {
    const run = async () => {
      try {
        setIsLoading(true);
        setError(null);
        const archived = await legislatorsLoader.loadArchivedSangiinLegislators(archiveDate);
        setData(archived);
      } catch (e) {
        setError('アーカイブ議員データの読み込みに失敗しました');
      } finally {
        setIsLoading(false);
      }
    };
    run();
  }, [archiveDate]);

  useEffect(() => {
    if (!data) return;
    const list = legislatorsLoader.filterLegislators(data.data, filter);
    setFiltered(list);
  }, [data, filter]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="archive" />
      <main className="py-8 pt-24">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* タイトル */}
          <div className="mb-6">
            <div className="flex items-center gap-2 mb-2">
              <History className="h-6 w-6 text-gray-600" />
              <h1 className="text-2xl font-bold text-gray-900">{archiveDateDisplay} 参議院選までの議員一覧（アーカイブ）</h1>
            </div>
            <p className="text-gray-600">選挙実施までの参議院議員データを保存しています。</p>
            {data && (
              <div className="mt-3 p-3 bg-blue-50 rounded text-sm text-blue-900">
                <span className="font-medium">件数:</span> 参議院 {data.metadata.sangiin_count || 0} 名
              </div>
            )}
          </div>

          {/* エラー */}
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-700">{error}</div>
          )}

          {/* フィルタ */}
          <LegislatorsFilter
            filter={filter}
            onFilterChange={setFilter}
            houseCounts={{ shugiin: 0, sangiin: data?.metadata.sangiin_count || 0, total: data?.metadata.sangiin_count || 0 }}
          />

          {/* 一覧 */}
          <LegislatorsList legislators={filtered} isLoading={isLoading} />
        </div>
      </main>
    </div>
  );
}
