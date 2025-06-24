'use client';

import Header from '@/components/Header';
import AboutPage from '@/components/AboutPage';

export default function AboutPageWrapper() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="about" />
      <main className="pt-16">
        <AboutPage />
      </main>
    </div>
  );
}