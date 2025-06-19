'use client';

import { ExternalLink, Github, Shield, Search, Database, Users } from 'lucide-react';

export default function AboutPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-8">
      {/* ページタイトル */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">このサイトについて</h1>
        <p className="text-gray-600">
          日本政治議事録検索システムの目的と使命について
        </p>
      </div>

      {/* メインメッセージ */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-16 h-16 bg-blue-100 rounded-full mb-4">
            <Search className="h-8 w-8 text-blue-600" />
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            政治をもっと身近に、もっと透明に
          </h2>
          <p className="text-gray-600 max-w-2xl mx-auto">
            国会議事録を誰でも簡単に検索できるオープンソースプラットフォームです。
            政治的判断を「感情」ではなく「発言と行動の記録」で行えるようサポートします。
          </p>
        </div>
      </div>

      {/* 特徴 */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-blue-100 rounded-lg mb-4">
            <Database className="h-6 w-6 text-blue-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">包括的なデータ</h3>
          <p className="text-gray-600 text-sm">
            国会議事録を網羅的に収集・整理し、検索可能な形で提供
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-green-100 rounded-lg mb-4">
            <Shield className="h-6 w-6 text-green-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">中立・非営利</h3>
          <p className="text-gray-600 text-sm">
            特定の政治的立場を取らず、客観的な情報提供に徹底
          </p>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 text-center">
          <div className="inline-flex items-center justify-center w-12 h-12 bg-purple-100 rounded-lg mb-4">
            <Users className="h-6 w-6 text-purple-600" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">オープンソース</h3>
          <p className="text-gray-600 text-sm">
            コミュニティ主導で透明性を保ち、誰でも改善に参加可能
          </p>
        </div>
      </div>

      {/* 目的 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🎯 目的</h2>
        <div className="space-y-4 text-gray-700">
          <p>
            国会（衆議院・参議院）の議事録を収集・検索・公開し、政党や議員の発言傾向・資産・政策を
            国民が簡単に把握できるOSSプラットフォームを構築します。
          </p>
          <p>
            中立・非営利・匿名性を重視し、将来的には都道府県・市区町村の地方議会議事録にも対応予定です。
          </p>
        </div>
      </div>

      {/* 技術仕様 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🔧 技術仕様</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">データ収集</h3>
            <ul className="text-gray-700 text-sm space-y-1">
              <li>• Python</li>
              <li>• 国会会議録検索API連携</li>
              <li>• 自動データ収集システム</li>
            </ul>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">フロントエンド</h3>
            <ul className="text-gray-700 text-sm space-y-1">
              <li>• Next.js + TypeScript</li>
              <li>• FlexSearch全文検索</li>
              <li>• レスポンシブデザイン</li>
            </ul>
          </div>
        </div>
      </div>

      {/* データソース */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">📊 データ収集元・情報源</h2>
        <div className="space-y-3">
          <div className="mb-4">
            <h3 className="font-semibold text-gray-900 mb-2">🏛️ 公式データソース（直接収集）</h3>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-gray-700">国会会議録検索API（国立国会図書館）</span>
            <a
              href="https://kokkai.ndl.go.jp/api.html"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
            >
              公式API
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-gray-700">衆議院公式サイト（質問主意書・提出法案）</span>
            <a
              href="https://www.shugiin.go.jp/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
            >
              公式サイト
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-gray-700">参議院公式サイト（質問主意書・提出法案）</span>
            <a
              href="https://www.sangiin.go.jp/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
            >
              公式サイト
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-gray-700">各政党公式サイト（マニフェスト）</span>
            <span className="text-gray-500 text-sm">7政党から直接収集</span>
          </div>
          
          <div className="mt-6 mb-4">
            <h3 className="font-semibold text-gray-900 mb-2">🔍 参考プロジェクト</h3>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-gray-700">衆議院議案データベース（スマートニュース）</span>
            <a
              href="https://smartnews-smri.github.io/house-of-representatives/"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
            >
              参考
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
          <div className="flex items-center justify-between py-2 border-b border-gray-100">
            <span className="text-gray-700">オープンポリティクス</span>
            <a
              href="https://search.openpolitics.or.jp/home"
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:text-blue-700 flex items-center gap-1 text-sm"
            >
              参考
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        </div>
      </div>

      {/* 透明性とオープンソース */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🌟 透明性とオープンソース</h2>
        <div className="space-y-4 text-gray-700">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">🔍 完全な透明性</h3>
            <p className="text-sm mb-2">
              すべてのデータ収集プロセス、処理ロジック、ソースコードを公開しています。
              どのようにデータが収集・処理されているかを誰でも確認でき、監査可能です。
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">🤝 コミュニティ主導</h3>
            <p className="text-sm mb-2">
              オープンソースソフトウェアとして開発され、誰でも改善提案や貢献ができます。
              特定の組織や個人に依存しない、コミュニティ主導の運営を行っています。
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">📊 データの信頼性</h3>
            <p className="text-sm mb-2">
              公式なデータソースからのみ収集し、データの加工や編集は行いません。
              収集元の情報も明示し、データの出典を常に明確にしています。
            </p>
          </div>
          <div className="flex items-center gap-4 pt-4">
            <a
              href="https://github.com/hironeko/new-jp-search"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-gray-900 text-white rounded-lg hover:bg-gray-800 transition-colors text-sm"
            >
              <Github className="h-4 w-4" />
              GitHub リポジトリ
            </a>
            <span className="text-sm text-gray-500">MIT License</span>
          </div>
        </div>
      </div>

      {/* プライバシー・中立性 */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">🛡️ 中立性とプライバシー</h2>
        <div className="space-y-4 text-gray-700">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">🔒 プライバシー保護</h3>
            <p className="text-sm mb-2">
              公式に公開されている議事録・文書のみを対象とし、個人のプライバシーに最大限配慮します。
              帰化歴等の機微な情報については、公式に明示的に公開されている場合のみ表示します。
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">🌐 オープンで公正な運営</h3>
            <p className="text-sm mb-2">
              すべてのプロセスを透明化し、特定の利益団体や組織の影響を受けない独立した運営を行います。
              国民の知る権利を支援し、民主主義の発展に貢献することを目指しています。
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">📝 情報の正確性</h3>
            <p className="text-sm">
              データの収集・処理過程を完全に公開し、いつでも検証可能な状態を維持します。
              誤りが発見された場合は迅速に修正し、修正履歴も透明に公開します。
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}