# 🇯🇵 日本政治議事録検索システム v2

Next.js 14 + Hono で構築されたTypeScript統一アーキテクチャ

## ✨ 新アーキテクチャの特徴

- **TypeScript統一**: フロントエンド・バックエンドを TypeScript で完結
- **軽量API**: Hono による高速APIルート
- **ファイルベースDB**: JSON ファイルによるシンプルなデータ管理
- **ゼロコンフィグ**: Docker不要、npm一つで起動

## 🚀 クイックスタート

```bash
# 依存関係をインストール
npm install

# 開発サーバー起動
npm run dev

# ブラウザでアクセス
open http://localhost:3000
```

## 📊 データ収集

```bash
# 最新データ取得
npm run fetch:latest

# 過去データ取得  
npm run fetch:history
```

## 🏗️ アーキテクチャ

```
├── app/
│   ├── api/[[...route]]/route.ts  # Hono API Routes
│   ├── page.tsx                   # メインページ
│   └── layout.tsx                 # レイアウト
├── lib/
│   ├── kokkai-api.ts             # 国会API クライアント
│   ├── data-manager.ts           # データ管理
│   ├── fetch-latest.ts           # 最新データ取得
│   └── fetch-history.ts          # 履歴データ取得
├── types/
│   └── index.ts                  # TypeScript 型定義
└── data/
    ├── daily/                    # 日次データ
    └── 2024/, 2025/             # 年次データ
```

## 📈 改善点

### 従来 (Python + Next.js)
- ❌ 複数言語混在
- ❌ Docker 必須
- ❌ 複雑なAPI連携
- ❌ 重厚なバックエンド

### 新版 (Next.js + Hono)
- ✅ TypeScript 統一
- ✅ ゼロコンフィグ
- ✅ シンプルなAPI
- ✅ 軽量・高速

## 🔄 マイグレーション

```bash
# 既存データをコピー
cp -r ../data ./

# 新システム起動
npm run dev
```