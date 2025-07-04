'use client';

import { useEffect, useState } from 'react';
import { FileText, Download, ExternalLink, Calendar, Filter, Search, BookOpen, Target } from 'lucide-react';
import { format, parseISO } from 'date-fns';
import Link from 'next/link';

interface Manifesto {
  party: string;
  title: string;
  year: number;
  category: string;
  content: string;
  url: string;
  pdf_url?: string;
  collected_at: string;
}

interface ManifestoData {
  metadata: {
    data_type: string;
    total_count: number;
    generated_at: string;
    source: string;
  };
  data: Manifesto[];
}

// GitHub Pages basePath対応 - コンポーネント外で定義
const getBasePath = (): string => {
  if (typeof window !== 'undefined') {
    // ブラウザ環境では現在のパスから推測
    const path = window.location.pathname;
    if (path.startsWith('/gijiroku-search/')) {
      return '/gijiroku-search';
    }
  }
  return process.env.GITHUB_PAGES === 'true' ? '/gijiroku-search' : '';
};

const getDataPath = (path: string): string => {
  const basePath = getBasePath();
  return `${basePath}${path}`;
};

// マニフェストファイルのフォールバック候補を動的生成
const generateManifestFiles = (): string[] => {
  const files = ['/data/manifestos/manifestos_latest.json'];
  
  // 過去7日分のファイル名パターンを生成（時刻は既知のパターン）
  const timePatterns = ['193602', '193501', '193406', '193135', '192440'];
  
  for (let i = 0; i < 7; i++) {
    const date = new Date();
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().slice(0, 10).replace(/-/g, '');
    
    timePatterns.forEach(time => {
      files.push(`/data/manifestos/manifestos_${dateStr}_${time}.json`);
    });
  }
  
  return files;
};

export default function ManifestosPage() {
  const [manifestos, setManifestos] = useState<Manifesto[]>([]);
  const [filteredManifestos, setFilteredManifestos] = useState<Manifesto[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedParty, setSelectedParty] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');

  useEffect(() => {
    const fetchManifestos = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // 動的にファイル候補を生成
        const filesToTry = generateManifestFiles().map(path => getDataPath(path));


        for (const filePath of filesToTry) {
          try {
            const response = await fetch(filePath);
            
            if (response.ok) {
              const data = await response.json();
              
              const manifestosData = Array.isArray(data) ? data : data.data || [];
              setManifestos(manifestosData);
              setFilteredManifestos(manifestosData);
              return;
            } else {
            }
          } catch (fileError) {
            console.error(`Error loading ${filePath}:`, fileError);
            continue;
          }
        }
        
        console.warn('No manifesto files could be loaded from any source');
        setManifestos([]);
        setFilteredManifestos([]);
      } catch (err) {
        console.error('Critical error loading manifestos:', err);
        setError(err instanceof Error ? err.message : 'マニフェストの取得に失敗しました');
      } finally {
        setLoading(false);
      }
    };

    fetchManifestos();
  }, []);

  useEffect(() => {
    let filtered = manifestos;

    // 政党フィルター
    if (selectedParty) {
      filtered = filtered.filter(m => m.party === selectedParty);
    }

    // カテゴリフィルター
    if (selectedCategory) {
      filtered = filtered.filter(m => m.category === selectedCategory);
    }

    // 検索フィルター
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(m => 
        m.title.toLowerCase().includes(query) ||
        m.content.toLowerCase().includes(query) ||
        m.party.toLowerCase().includes(query)
      );
    }

    setFilteredManifestos(filtered);
  }, [manifestos, selectedParty, selectedCategory, searchQuery]);

  const uniqueParties = Array.from(new Set(manifestos.map(m => m.party))).sort();
  const uniqueCategories = Array.from(new Set(manifestos.map(m => m.category))).sort();

  const formatDate = (dateString: string) => {
    try {
      return format(parseISO(dateString), 'yyyy年MM月dd日');
    } catch {
      return dateString;
    }
  };

  const truncateContent = (content: string, maxLength: number = 200) => {
    if (content.length <= maxLength) return content;
    return content.substring(0, maxLength) + '...';
  };

  const getPartySlug = (party: string) => {
    const slugs: { [key: string]: string } = {
      '自由民主党': 'jiyuminshuto',
      '公明党': 'komeito', 
      '立憲民主党': 'rikkenminshuto',
      '日本維新の会': 'nipponishin',
      '日本共産党': 'kyosanto',
      '国民民主党': 'kokuminminshuto',
      '参政党': 'sanseito'
    };
    return slugs[party] || party.toLowerCase().replace(/\s+/g, '');
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">マニフェストを読み込み中...</p>
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

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* ページタイトル */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">政党マニフェスト</h1>
        <p className="text-gray-600 mb-4">
          各政党の政策提言・マニフェストを検索・閲覧できます
        </p>
        
        {/* 特別ページへのリンク */}
        <div className="flex flex-col sm:flex-row gap-4 mt-4">
          <Link
            href="/manifestos/llm"
            className="inline-flex items-center justify-center px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            <BookOpen className="h-5 w-5 mr-2" />
            AI要約マニフェスト
          </Link>
          <Link
            href="/sangiin-comparison"
            className="inline-flex items-center justify-center px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
          >
            <Target className="h-5 w-5 mr-2" />
            参院選 政策対比表
          </Link>
        </div>
      </div>

      {/* フィルター・検索 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* 検索ボックス */}
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className="h-4 w-4 text-gray-400" />
            </div>
            <input
              type="text"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              placeholder="キーワード検索"
              className="w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* 政党フィルター */}
          <div>
            <select
              value={selectedParty}
              onChange={(e) => setSelectedParty(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">すべての政党</option>
              {uniqueParties.map(party => (
                <option key={party} value={party}>{party}</option>
              ))}
            </select>
          </div>

          {/* カテゴリフィルター */}
          <div>
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="">すべてのカテゴリ</option>
              {uniqueCategories.map(category => (
                <option key={category} value={category}>{category}</option>
              ))}
            </select>
          </div>

          {/* リセットボタン */}
          <div>
            <button
              onClick={() => {
                setSelectedParty('');
                setSelectedCategory('');
                setSearchQuery('');
              }}
              className="w-full px-4 py-2 text-sm font-medium text-gray-700 bg-gray-100 rounded-md hover:bg-gray-200 transition-colors"
            >
              フィルターをリセット
            </button>
          </div>
        </div>

        {/* 結果数表示 */}
        <div className="mt-4 text-sm text-gray-600">
          <span className="font-medium">{filteredManifestos.length}</span>件のマニフェストが見つかりました
        </div>
      </div>

      {/* マニフェスト一覧 */}
      {filteredManifestos.length === 0 ? (
        <div className="text-center py-12 bg-white rounded-lg shadow-sm">
          <FileText className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <p className="text-gray-600 text-lg">該当するマニフェストが見つかりませんでした</p>
          <p className="text-gray-500 mt-2">検索条件を変更してお試しください</p>
        </div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {filteredManifestos.map((manifesto, index) => (
            <div key={index} className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              {/* ヘッダー */}
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 mb-1">
                    {manifesto.title}
                  </h3>
                  <div className="flex items-center gap-4 text-sm text-gray-600">
                    <span className="font-medium text-blue-600">{manifesto.party}</span>
                    <span className="px-2 py-1 bg-gray-100 rounded text-xs">
                      {manifesto.category}
                    </span>
                    <span>{manifesto.year}年</span>
                  </div>
                </div>
                <FileText className="h-6 w-6 text-gray-400 flex-shrink-0" />
              </div>

              {/* 内容 */}
              <div className="mb-4">
                <p className="text-gray-800 leading-relaxed">
                  {truncateContent(manifesto.content)}
                </p>
              </div>

              {/* アクション */}
              <div className="pt-4 border-t border-gray-100">
                <div className="flex items-center justify-between mb-3">
                  <div className="text-xs text-gray-500">
                    <Calendar className="inline h-3 w-3 mr-1" />
                    {formatDate(manifesto.collected_at)}
                  </div>
                </div>
                
                <div className="flex flex-col gap-2">
                  <Link
                    href={`/manifestos/${getPartySlug(manifesto.party)}`}
                    className="inline-flex items-center justify-center gap-1 bg-blue-600 text-white hover:bg-blue-700 text-sm font-medium px-3 py-2 rounded"
                  >
                    <FileText className="h-4 w-4" />
                    AI要約詳細
                  </Link>
                  
                  <div className="flex items-center gap-2">
                    {manifesto.pdf_url && (
                      <a
                        href={manifesto.pdf_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center gap-1 text-red-600 hover:text-red-700 text-sm font-medium"
                      >
                        <Download className="h-4 w-4" />
                        PDF
                      </a>
                    )}
                    
                    <a
                      href={manifesto.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-1 text-blue-600 hover:text-blue-700 text-sm font-medium"
                    >
                      元ページ
                      <ExternalLink className="h-4 w-4" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}