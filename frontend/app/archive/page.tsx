'use client';

import Header from '@/components/Header';
import Link from 'next/link';
import { Archive, Calendar, ExternalLink, Building2, Users } from 'lucide-react';

export default function ArchivePage() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="archive" />
      <main className="pt-20">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Page header */}
          <div className="mb-8">
            <div className="flex items-center gap-3 mb-2">
              <Archive className="h-6 w-6 text-gray-700" />
              <h1 className="text-2xl font-bold text-gray-900">アーカイブ</h1>
            </div>
            <p className="text-gray-600">過去の選挙ページなどのアーカイブを掲載しています。</p>
          </div>

          {/* Archived items */}
          <div className="space-y-4">
            {/* 議員一覧（アーカイブ） */}
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Users className="h-4 w-4" />
                    <span>議員一覧（アーカイブ）</span>
                  </div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    2025/07/20参議院選までの議員一覧
                  </h2>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href="/archive/legislators?date=20250720"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                  >
                    開く
                  </Link>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-3">
                参議院選（2025/07/20）実施までの議員データの保存版です。
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
              <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
                <div>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mb-1">
                    <Building2 className="h-4 w-4" />
                    <span>選挙ページ（アーカイブ）</span>
                  </div>
                  <h2 className="text-lg font-semibold text-gray-900">
                    2025年 参議院選 候補者一覧
                  </h2>
                  <div className="flex items-center gap-2 text-sm text-gray-500 mt-1">
                    <Calendar className="h-4 w-4" />
                    <span>投開票日: 2025-07-20</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <Link
                    href="/sangiin"
                    className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 text-white text-sm rounded-md hover:bg-blue-700"
                  >
                    開く
                  </Link>
                  <a
                    href="https://www.sangiin.go.jp/"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                  >
                    参議院公式サイト
                    <ExternalLink className="h-4 w-4" />
                  </a>
                </div>
              </div>
              <p className="text-sm text-gray-600 mt-3">
                本ページは過去選挙の記録として公開を継続しています。データは当時の収集元に基づきます。
              </p>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
