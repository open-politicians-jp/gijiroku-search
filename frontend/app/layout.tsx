import type { Metadata } from 'next'
import './globals.css'
import GoogleAnalytics from '@/components/GoogleAnalytics'

export const metadata: Metadata = {
  metadataBase: new URL('https://open-politicians-jp.github.io/gijiroku-search'),
  title: {
    default: '日本政治議事録検索',
    template: '%s | 日本政治議事録検索',
  },
  description: '国会議事録の横断検索システム - 政治をもっと身近に、もっと透明に',
  keywords: ['国会', '議事録', '検索', '政治', '日本', '議員', '政党'],
  authors: [{ name: 'JP-Search OSS Project' }],
  openGraph: {
    title: '日本政治議事録検索',
    description: '国会議事録の横断検索システム',
    type: 'website',
    locale: 'ja_JP',
    url: '/',
    siteName: '日本政治議事録検索',
  },
  twitter: {
    card: 'summary',
    title: '日本政治議事録検索',
    description: '国会議事録の横断検索システム',
  },
  robots: {
    index: true,
    follow: true,
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const jsonLd = {
    '@context': 'https://schema.org',
    '@type': 'WebSite',
    name: '日本政治議事録検索',
    url: 'https://open-politicians-jp.github.io/gijiroku-search',
    inLanguage: 'ja-JP',
    potentialAction: {
      '@type': 'SearchAction',
      target: 'https://open-politicians-jp.github.io/gijiroku-search/?q={search_term_string}',
      'query-input': 'required name=search_term_string',
    },
  };

  return (
    <html lang="ja">
      <body className="min-h-screen bg-gray-50">
        <GoogleAnalytics />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(jsonLd) }}
        />
        {children}
      </body>
    </html>
  )
}
