'use client';

import Header from '@/components/Header';
import AboutPage from '@/components/AboutPage';

export default function AboutPageWrapper() {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header currentPage="about" />
      <div className="container mx-auto px-4 py-8 pt-24">
        <AboutPage />
      </div>
    </div>
  );
}