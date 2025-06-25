'use client';

import Header from '@/components/Header';
import StatsPage from '@/components/StatsPage';

export default function StatsPageWrapper() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="stats" />
      <main className="pt-16">
        <StatsPage />
      </main>
    </div>
  );
}