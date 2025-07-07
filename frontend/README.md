# 🇯🇵 日本政治議事録検索システム - フロントエンド

Next.js 14 + TypeScript で構築された政治議事録横断検索システムのフロントエンド

## ✨ 特徴

- **Next.js 14 App Router**: 最新のNext.jsアーキテクチャ
- **TypeScript**: 型安全なコード
- **静的サイト生成**: GitHub Pages対応
- **レスポンシブデザイン**: Tailwind CSS使用
- **検索機能**: 議事録・法案・質問主意書・委員会ニュースの横断検索
- **政策要約**: 22政党のLLM要約ページ（動的URL参照）

## 🚀 開発環境

```bash
# 依存関係インストール
npm ci

# 開発サーバー起動
npm run dev

# ブラウザでアクセス
open http://localhost:3000
```

## 🏗️ ビルド・デプロイ

```bash
# 本番ビルド
npm run build

# 静的サイト生成
npm run build && npm run export

# ローカル本番環境テスト
npm run start
```

## 📁 ディレクトリ構造

```
├── app/                    # Next.js App Router
│   ├── manifestos/        # マニフェスト関連
│   │   ├── llm/          # 22政党LLM要約ページ
│   │   │   ├── jiyuminshuto/      # 自由民主党
│   │   │   ├── rikkenminshuto/    # 立憲民主党
│   │   │   ├── team-mirai/        # チームみらい
│   │   │   └── ...                # その他19政党
│   │   └── page.tsx      # マニフェスト一覧
│   ├── sangiin/          # 参議院関連
│   ├── sangiin-comparison/ # 参議院対比
│   ├── summaries/        # 要約ページ
│   ├── legislators/      # 議員ページ
│   ├── about/           # アバウトページ
│   ├── page.tsx         # メインページ
│   ├── layout.tsx       # レイアウト
│   └── globals.css      # グローバルスタイル
├── components/          # Reactコンポーネント
│   ├── Header.tsx       # ヘッダー
│   ├── SearchForm.tsx   # 検索フォーム
│   ├── SearchResults.tsx # 検索結果
│   ├── PolicyReferences.tsx # 政策参照コンポーネント
│   └── ...
├── lib/                   # ライブラリ
│   ├── api.ts            # API関数
│   ├── data-loader.ts    # データローダー
│   └── legislators-linker.ts # 議員リンカー
├── types/                 # TypeScript型定義
│   └── index.ts
├── public/               # 静的ファイル
│   └── data/            # データファイル
│       ├── speeches/    # 議事録データ
│       ├── bills/       # 法案データ
│       ├── questions/   # 質問主意書データ
│       ├── committee_news/ # 委員会ニュース
│       ├── manifestos/  # マニフェストデータ
│       ├── legislators/ # 議員データ
│       ├── petitions/   # 請願・陳情データ
│       ├── summaries/   # 要約データ
│       ├── weekly/      # 週次データ
│       └── policy_summaries.json # 政策要約統合データ
└── next.config.js        # Next.js設定
```

## 🔧 技術スタック

- **フレームワーク**: Next.js 14
- **言語**: TypeScript 
- **スタイリング**: Tailwind CSS
- **UIライブラリ**: Lucide React (アイコン)
- **デプロイ**: GitHub Pages (静的サイト)

## 📊 データ構造

### 議事録データ (speeches)
```typescript
interface SpeechRecord {
  id: string
  date: string
  session: string
  house: string
  committee: string
  speaker: string
  party: string
  text: string
  url: string
}
```

### 法案データ (bills)
```typescript
interface BillRecord {
  id: string
  title: string
  bill_number: string
  submission_date: string
  status: string
  house: string
  submitter: string
  url: string
}
```

### 政策要約データ (policy_summaries)
```typescript
interface PolicySummaryData {
  generated_at: string
  description: string
  parties: PartyPolicy[]
  total_parties: number
  has_url_references: boolean
}

interface PartyPolicy {
  name: string
  categories: PolicyCategory[]
  party_references?: PolicyReference[]
}

interface PolicyReference {
  url: string
  description: string
  source_type: string
  reliability: string
}
```

## 🌐 デプロイメント

### GitHub Pages
- **URL**: `https://open-politicians-jp.github.io/gijiroku-search`
- **自動デプロイ**: mainブランチpush時
- **静的サイト**: Next.js static export使用

### GitHub Actions
- **デプロイワークフロー**: `.github/workflows/deploy-github-pages.yml`
- **データ収集**: `.github/workflows/data-collection.yml` (毎日3時JST)

## 🔍 検索機能

### 対応データ
- **議事録**: 国会での発言内容
- **法案**: 提出法案の詳細（ステータス・審議状況付き）
- **質問主意書**: 質問と答弁（HTML/PDFリンク付き）
- **委員会ニュース**: 全22委員会の活動情報
- **マニフェスト**: 政党政策資料（動的URL参照）
- **政策要約**: 22政党のLLM要約（出典URL統合）
- **請願・陳情**: 国民からの請願・陳情データ
- **議員情報**: 衆参議員の詳細情報

### 検索方式
- **全文検索**: タイトル・内容での検索
- **フィルタ機能**: 政党・議員・委員会・日付範囲
- **統計表示**: データ件数・傾向分析

## 🎯 パフォーマンス最適化

- **静的サイト生成**: 高速なページ読み込み
- **データファイル分割**: 大きなデータセットの最適化
- **画像最適化**: Next.js Image Optimization
- **キャッシュ活用**: GitHub Actions caching

## 🔐 セキュリティ

- **静的サイト**: サーバー攻撃リスクなし
- **公開情報のみ**: 機密情報は含まない
- **HTTPS**: GitHub Pages標準対応

## 📱 レスポンシブ対応

- **デスクトップ**: フル機能
- **タブレット**: 最適化されたレイアウト
- **モバイル**: タッチ操作対応

## 🛠️ 開発ガイドライン

### コーディング規約
- **TypeScript**: 型安全性を重視
- **ESLint**: コード品質チェック
- **Prettier**: コードフォーマット統一

### コンポーネント設計
- **関数コンポーネント**: React Hooks使用
- **再利用可能**: モジュラー設計
- **アクセシビリティ**: WCAG準拠

## 🧪 テスト

```bash
# 型チェック
npm run type-check

# Lint
npm run lint

# ビルドテスト
npm run build
```

## 📄 ライセンス

MIT License - 詳細は[LICENSE](../LICENSE)を参照

## 🤝 貢献

- **Issue報告**: GitHub Issues
- **Pull Request**: 歓迎
- **ドキュメント改善**: README・コメント

## 📞 サポート

- **プロジェクト**: [GitHub Repository](https://github.com/open-politicians-jp/gijiroku-search)
- **ドキュメント**: [CLAUDE.md](../CLAUDE.md)
- **デプロイ**: [GitHub Pages](https://open-politicians-jp.github.io/gijiroku-search)