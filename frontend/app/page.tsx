'use client';

import { useState, useEffect } from 'react';
import Header from '@/components/Header';
import SearchForm from '@/components/SearchForm';
import SearchResults from '@/components/SearchResults';
import CommitteeNewsResults from '@/components/CommitteeNewsResults';
import BillsResults from '@/components/BillsResults';
import QuestionResults from '@/components/QuestionResults';
import LegislatorsPage from './legislators/page';
import { SearchParams, SearchResult, Stats, CommitteeNewsResult, BillsResult, QuestionsResult } from '@/types';
import { apiClient } from '@/lib/api';

export default function Home() {
  const [currentPage, setCurrentPage] = useState<'search' | 'legislators'>('search');
  const [searchResult, setSearchResult] = useState<SearchResult | null>(null);
  const [committeeNewsResult, setCommitteeNewsResult] = useState<CommitteeNewsResult | null>(null);
  const [billsResult, setBillsResult] = useState<BillsResult | null>(null);
  const [questionsResult, setQuestionsResult] = useState<QuestionsResult | null>(null);
  const [allSpeeches, setAllSpeeches] = useState<any[]>([]);
  const [currentSearchParams, setCurrentSearchParams] = useState<SearchParams | null>(null);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [footerStats, setFooterStats] = useState<Stats | null>(null);

  // フッター統計データの取得
  useEffect(() => {
    const fetchFooterStats = async () => {
      try {
        const stats = await apiClient.getStats();
        setFooterStats(stats);
      } catch (err) {
        console.warn('Failed to fetch footer stats:', err);
      }
    };
    fetchFooterStats();
  }, []);

  const handleSearch = async (params: SearchParams) => {
    try {
      setLoading(true);
      setError(null);
      
      // 統合検索（静的データローダー使用）
      const result = await apiClient.search(params);
      
      if (params.search_type === 'committee_news') {
        setCommitteeNewsResult(result);
        setSearchResult(null);
        setBillsResult(null);
        setQuestionsResult(null);
        setAllSpeeches([]);
      } else if (params.search_type === 'bills') {
        setBillsResult(result);
        setSearchResult(null);
        setCommitteeNewsResult(null);
        setQuestionsResult(null);
        setAllSpeeches([]);
      } else if (params.search_type === 'questions') {
        setQuestionsResult(result);
        setSearchResult(null);
        setCommitteeNewsResult(null);
        setBillsResult(null);
        setAllSpeeches([]);
      } else {
        // 議事録検索
        setSearchResult(result);
        setCommitteeNewsResult(null);
        setBillsResult(null);
        setQuestionsResult(null);
        setAllSpeeches(result.speeches);
      }
      
      setCurrentSearchParams(params);
    } catch (err) {
      setError(err instanceof Error ? err.message : '検索に失敗しました');
      setSearchResult(null);
      setCommitteeNewsResult(null);
      setBillsResult(null);
      setQuestionsResult(null);
      setAllSpeeches([]);
      setCurrentSearchParams(null);
    } finally {
      setLoading(false);
    }
  };

  const handleLoadMore = async () => {
    if (!currentSearchParams || !searchResult) return;
    
    try {
      setLoadingMore(true);
      const nextParams = {
        ...currentSearchParams,
        offset: (currentSearchParams.offset || 0) + (currentSearchParams.limit || 50)
      };
      
      const result = await apiClient.search(nextParams);
      
      // 既存の結果に新しい結果を追加
      const updatedSpeeches = [...allSpeeches, ...result.speeches];
      setAllSpeeches(updatedSpeeches);
      
      // SearchResultの更新
      setSearchResult({
        ...result,
        speeches: updatedSpeeches,
        offset: nextParams.offset || 0
      });
      
      setCurrentSearchParams(nextParams);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'さらに読み込みに失敗しました');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleSearchTypeChange = () => {
    setSearchResult(null);
    setCommitteeNewsResult(null);
    setBillsResult(null);
    setQuestionsResult(null);
    setAllSpeeches([]);
    setCurrentSearchParams(null);
    setError(null);
  };

  const handlePageChange = (page: 'search' | 'legislators') => {
    setCurrentPage(page);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage={currentPage} onPageChange={handlePageChange} />
      
      <main className="pt-16">
        {currentPage === 'search' && (
          <div className="py-8">
            <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
              {/* 検索フォーム */}
              <SearchForm onSearch={handleSearch} onSearchTypeChange={handleSearchTypeChange} loading={loading} />
              
              {/* エラー表示 */}
              {error && (
                <div className="max-w-4xl mx-auto mt-8">
                  <div className="bg-red-50 border border-red-200 rounded-lg p-6">
                    <p className="text-red-600">{error}</p>
                  </div>
                </div>
              )}
              
              {/* 検索結果 */}
              {searchResult && (
                <SearchResults
                  speeches={allSpeeches}
                  total={searchResult.total}
                  loading={loading || loadingMore}
                  onLoadMore={handleLoadMore}
                  hasMore={searchResult.has_more}
                  currentOffset={searchResult.offset}
                  limit={searchResult.limit}
                />
              )}
              
              {/* 委員会ニュース結果 */}
              {committeeNewsResult && (
                <CommitteeNewsResults
                  news={committeeNewsResult.news}
                  total={committeeNewsResult.total}
                  loading={loading}
                />
              )}
              
              {/* 法案検索結果 */}
              {billsResult && (
                <BillsResults
                  bills={billsResult.bills}
                  total={billsResult.total}
                  loading={loading}
                />
              )}
              
              {/* 質問主意書検索結果 */}
              {questionsResult && (
                <QuestionResults
                  questions={questionsResult.questions}
                  total={questionsResult.total}
                  loading={loading}
                />
              )}
              
              
              {/* 初期状態メッセージ */}
              {!searchResult && !committeeNewsResult && !billsResult && !questionsResult && !loading && !error && (
                <div className="max-w-4xl mx-auto mt-12 text-center">
                  <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12">
                    <h2 className="text-2xl font-bold text-gray-900 mb-4">
                      国会情報を包括検索
                    </h2>
                    <p className="text-gray-600 mb-6">
                      議事録検索：政策名、議員名、政党名、委員会名などで検索<br/>
                      委員会活動：最新の委員会開催情報、法案審議状況を検索<br/>
                      提出法案：法案タイトル、ステータス、提出者、審議状況を検索<br/>
                      質問主意書：国会議員の政府への質問と答弁を検索
                    </p>
                    <div className="text-sm text-gray-500 space-y-2">
                      <p>検索例：</p>
                      <div className="flex flex-wrap justify-center gap-2">
                        <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">創新太郎</span>
                        <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">デジタル改革</span>
                        <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">創新党</span>
                        <span className="px-3 py-1 bg-gray-100 rounded-full text-xs">環境政策</span>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
        
        {currentPage === 'legislators' && <LegislatorsPage />}
      </main>
      
      {/* フッター */}
      <footer className="bg-white border-t border-gray-200 mt-16">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          <div className="text-center text-sm text-gray-500">
            <p className="mb-2">
              このサイトは、国会会議録検索APIを利用して作成されたオープンソースプロジェクトです
            </p>
            <p>
              中立・非営利・透明性を重視し、政治情報へのアクセス向上を目指しています
            </p>
            {footerStats && (
              <p className="mt-2 text-xs">
                📊 {footerStats.total_speeches.toLocaleString()}件の議事録 | 🗓️ {footerStats.date_range.from}〜{footerStats.date_range.to} | ⚡ Next.js + JSON
              </p>
            )}
          </div>
        </div>
      </footer>
    </div>
  );
}