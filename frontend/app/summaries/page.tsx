'use client';

import React, { useState, useEffect } from 'react';
import SummariesPage from '@/components/SummariesPage';
import Header from '@/components/Header';
import { SummariesClientLoader } from '@/lib/summaries-client-loader';
import { MeetingSummary } from '@/types';

export default function SummariesPageWrapper() {
  const [initialSummaries, setInitialSummaries] = useState<MeetingSummary[]>([]);
  const [houses, setHouses] = useState<string[]>([]);
  const [committees, setCommittees] = useState<string[]>([]);
  const [keywords, setKeywords] = useState<string[]>([]);
  const [stats, setStats] = useState<{
    total_summaries: number;
    total_meetings: number;
    houses: string[];
    committees: string[];
    keywords: string[];
    date_range: { from: string; to: string };
  }>({
    total_summaries: 0,
    total_meetings: 0,
    houses: [],
    committees: [],
    keywords: [],
    date_range: { from: '', to: '' }
  });
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const loadInitialData = async () => {
      try {
        const [summariesResult, housesData, committeesData, keywordsData, statsData] = await Promise.all([
          SummariesClientLoader.searchSummaries({ limit: 10, offset: 0 }),
          SummariesClientLoader.getAvailableHouses(),
          SummariesClientLoader.getAvailableCommittees(),
          SummariesClientLoader.getAvailableKeywords(),
          SummariesClientLoader.getSummaryStats()
        ]);

        setInitialSummaries(summariesResult.summaries);
        setHouses(housesData);
        setCommittees(committeesData);
        setKeywords(keywordsData);
        setStats(statsData);
      } catch (error) {
        console.error('Error loading initial data:', error);
      } finally {
        setIsLoading(false);
      }
    };

    loadInitialData();
  }, []);

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mb-4"></div>
          <p className="text-gray-600">議会要約データを読み込み中...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="summaries" />
      <main>
        <SummariesPage
          initialSummaries={initialSummaries}
          houses={houses}
          committees={committees}
          keywords={keywords}
          stats={stats}
        />
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
            <p className="mt-2 text-xs">
              🤖 AI要約機能はLlama3.2:3Bモデルを使用 | Beta版のため改善を継続中
            </p>
          </div>
        </div>
      </footer>
    </div>
  );
}