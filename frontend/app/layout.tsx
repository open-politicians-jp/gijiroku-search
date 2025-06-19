import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  metadataBase: new URL('https://hironeko.github.io/new-jp-search'),
  title: '日本政治議事録検索',
  description: '国会議事録の横断検索システム - 政治をもっと身近に、もっと透明に',
  keywords: ['国会', '議事録', '検索', '政治', '日本', '議員', '政党'],
  authors: [{ name: 'JP-Search OSS Project' }],
  openGraph: {
    title: '日本政治議事録検索',
    description: '国会議事録の横断検索システム',
    type: 'website',
    locale: 'ja_JP',
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
  return (
    <html lang="ja">
      <body className="min-h-screen bg-gray-50">
        {children}
      </body>
    </html>
  )
}