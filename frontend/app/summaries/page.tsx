import { Metadata } from 'next';
import { SummariesLoader } from '@/lib/summaries-loader';
import SummariesPage from '@/components/SummariesPage';
import Header from '@/components/Header';

export const metadata: Metadata = {
  title: '議会要約検索 (Beta) | 日本政治議事録横断検索',
  description: 'AI技術を活用した国会議事録の議会単位要約システム。重要な議論と決定事項を効率的に把握できます。',
  keywords: ['国会', '議事録', '要約', 'AI', '政治', '法案', '審議'],
};

export default async function SummariesPageWrapper() {
  const loader = new SummariesLoader();
  
  // 初期データ読み込み
  const [initialResult, houses, committees, keywords, stats] = await Promise.all([
    loader.searchSummaries({ limit: 10, offset: 0 }),
    loader.getAvailableHouses(),
    loader.getAvailableCommittees(),
    loader.getAvailableKeywords(),
    loader.getSummaryStats()
  ]);

  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="summaries" />
      <main>
        <SummariesPage
          initialSummaries={initialResult.summaries}
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