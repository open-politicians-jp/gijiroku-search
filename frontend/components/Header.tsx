'use client';

import { Search, BarChart3, Info, FileText } from 'lucide-react';

interface HeaderProps {
  currentPage?: 'search' | 'stats' | 'about' | 'manifestos';
  onPageChange?: (page: 'search' | 'stats' | 'about' | 'manifestos') => void;
}

export default function Header({ currentPage = 'search', onPageChange }: HeaderProps) {
  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* ロゴ・タイトル */}
          <div className="flex items-center gap-3 min-w-0 flex-1 sm:flex-initial">
            <div className="h-8 w-8 bg-blue-600 rounded-lg flex items-center justify-center flex-shrink-0">
              <Search className="h-5 w-5 text-white" />
            </div>
            <div className="min-w-0">
              <h1 className="text-lg sm:text-xl font-bold text-gray-900 truncate">
                日本政治議事録検索
              </h1>
              <p className="text-xs text-gray-500 hidden sm:block">
                国会議事録の横断検索システム
              </p>
            </div>
          </div>

          {/* ナビゲーション */}
          {onPageChange && (
            <nav className="flex items-center gap-1 sm:gap-6">
              <button
                onClick={() => onPageChange('search')}
                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  currentPage === 'search'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Search className="h-4 w-4" />
                <span className="hidden sm:inline">検索</span>
              </button>
              
              <button
                onClick={() => onPageChange('manifestos')}
                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  currentPage === 'manifestos'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <FileText className="h-4 w-4" />
                <span className="hidden sm:inline">マニフェスト</span>
              </button>
              
              <button
                onClick={() => onPageChange('stats')}
                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  currentPage === 'stats'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <BarChart3 className="h-4 w-4" />
                <span className="hidden sm:inline">統計</span>
              </button>
              
              <button
                onClick={() => onPageChange('about')}
                className={`flex items-center gap-1 sm:gap-2 px-2 sm:px-3 py-2 rounded-md text-xs sm:text-sm font-medium transition-colors ${
                  currentPage === 'about'
                    ? 'bg-blue-100 text-blue-700'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                }`}
              >
                <Info className="h-4 w-4" />
                <span className="hidden sm:inline">About</span>
              </button>
            </nav>
          )}
        </div>
      </div>
    </header>
  );
}