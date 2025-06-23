'use client';

import { useState } from 'react';
import { Search, BarChart3, Info, FileText, Users, Bot, Menu, X } from 'lucide-react';
import Link from 'next/link';

interface HeaderProps {
  currentPage?: 'search' | 'stats' | 'about' | 'manifestos' | 'legislators' | 'summaries';
  onPageChange?: (page: 'search' | 'stats' | 'about' | 'manifestos' | 'legislators') => void;
}

export default function Header({ currentPage = 'search', onPageChange }: HeaderProps) {
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const navigationItems = [
    { key: 'search', icon: Search, label: '検索', href: '/' },
    { key: 'summaries', icon: Bot, label: '議会要約', href: '/summaries', badge: 'Beta' },
    { key: 'manifestos', icon: FileText, label: 'マニフェスト', onClick: () => onPageChange?.('manifestos') },
    { key: 'legislators', icon: Users, label: '議員一覧', href: '/legislators' },
    { key: 'stats', icon: BarChart3, label: '統計', onClick: () => onPageChange?.('stats') },
    { key: 'about', icon: Info, label: 'About', onClick: () => onPageChange?.('about') }
  ];

  const handleNavClick = (item: typeof navigationItems[0]) => {
    if (item.onClick) {
      item.onClick();
    }
    setIsMobileMenuOpen(false);
  };

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* ロゴ・タイトル */}
          <Link href="/" className="flex items-center gap-3 min-w-0 flex-1 sm:flex-initial hover:opacity-80 transition-opacity">
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
          </Link>

          {/* デスクトップナビゲーション */}
          <nav className="hidden md:flex items-center gap-2">
            {navigationItems.map((item) => {
              const Icon = item.icon;
              const isActive = currentPage === item.key;
              
              if (item.href) {
                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-4 w-4" />
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="text-xs bg-blue-600 text-white px-1 py-0.5 rounded">
                        {item.badge}
                      </span>
                    )}
                  </Link>
                );
              }
              
              return (
                <button
                  key={item.key}
                  onClick={() => handleNavClick(item)}
                  className={`flex items-center gap-2 px-3 py-2 rounded-md text-sm font-medium transition-colors ${
                    isActive
                      ? 'bg-blue-100 text-blue-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  <span>{item.label}</span>
                  {item.badge && (
                    <span className="text-xs bg-blue-600 text-white px-1 py-0.5 rounded">
                      {item.badge}
                    </span>
                  )}
                </button>
              );
            })}
          </nav>

          {/* モバイルメニューボタン */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-md text-gray-600 hover:text-gray-900 hover:bg-gray-100 transition-colors"
            aria-label="メニューを開く"
          >
            {isMobileMenuOpen ? (
              <X className="h-6 w-6" />
            ) : (
              <Menu className="h-6 w-6" />
            )}
          </button>
        </div>

        {/* モバイルメニュー */}
        {isMobileMenuOpen && (
          <div className="md:hidden border-t border-gray-200 py-4">
            <nav className="space-y-2">
              {navigationItems.map((item) => {
                const Icon = item.icon;
                const isActive = currentPage === item.key;
                
                if (item.href) {
                  return (
                    <Link
                      key={item.key}
                      href={item.href}
                      onClick={() => setIsMobileMenuOpen(false)}
                      className={`flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors ${
                        isActive
                          ? 'bg-blue-100 text-blue-700'
                          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                      }`}
                    >
                      <Icon className="h-5 w-5" />
                      <span>{item.label}</span>
                      {item.badge && (
                        <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded ml-auto">
                          {item.badge}
                        </span>
                      )}
                    </Link>
                  );
                }
                
                return (
                  <button
                    key={item.key}
                    onClick={() => handleNavClick(item)}
                    className={`w-full flex items-center gap-3 px-4 py-3 rounded-md text-sm font-medium transition-colors text-left ${
                      isActive
                        ? 'bg-blue-100 text-blue-700'
                        : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                    }`}
                  >
                    <Icon className="h-5 w-5" />
                    <span>{item.label}</span>
                    {item.badge && (
                      <span className="text-xs bg-blue-600 text-white px-2 py-1 rounded ml-auto">
                        {item.badge}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>
        )}
      </div>
    </header>
  );
}