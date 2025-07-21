# Cloudflare D1 セットアップガイド

## 1. Cloudflare Dashboard設定

### D1データベース作成
```bash
# Cloudflare D1データベースを作成
npx wrangler d1 create gijiroku-search-db

# 出力例:
# Created database 'gijiroku-search-db' (xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)
# 
# Add the following to your wrangler.toml:
# [[d1_databases]]
# binding = "DB"
# database_name = "gijiroku-search-db"
# database_id = "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
```

### プレビュー用データベース作成
```bash
# プレビュー環境用のD1データベース
npx wrangler d1 create gijiroku-search-db-preview
```

### スキーマ適用
```bash
# 本番データベースにスキーマを適用
npx wrangler d1 execute gijiroku-search-db --file=schema.sql

# プレビューデータベースにスキーマを適用
npx wrangler d1 execute gijiroku-search-db-preview --file=schema.sql
```

## 2. データ移行

### 移行SQLファイル生成
```bash
# データ移行スクリプト実行
cd /path/to/worktrees/cloudflare-d1-migration
node scripts/migrate-to-d1.js

# 出力: d1-migration/complete_migration.sql
```

### D1データベースにデータ投入
```bash
# 本番データベースにデータ投入
npx wrangler d1 execute gijiroku-search-db --file=d1-migration/complete_migration.sql

# プレビューデータベースにデータ投入（必要に応じて）
npx wrangler d1 execute gijiroku-search-db-preview --file=d1-migration/complete_migration.sql
```

## 3. Cloudflare Pages設定

### Pages プロジェクト作成
1. Cloudflare Dashboard → Pages
2. "Create a project" → "Connect to Git"
3. GitHubリポジトリを選択: `open-politicians-jp/gijiroku-search`
4. ブランチ: `feature/cloudflare-d1-migration`

### ビルド設定
- **Build command**: `cd frontend && npm ci && npm run build`
- **Build output directory**: `frontend/out`
- **Root directory**: `/` (デフォルト)

### 環境変数設定
Pages プロジェクト → Settings → Environment variables:

**Production環境:**
- `NODE_ENV`: `production`
- `NEXT_PUBLIC_API_BASE_URL`: `https://your-project.pages.dev`

**Preview環境:**
- `NODE_ENV`: `preview`
- `NEXT_PUBLIC_API_BASE_URL`: `https://preview.your-project.pages.dev`

### D1バインディング設定
Pages プロジェクト → Settings → Functions:

**Production:**
- Variable name: `DB`
- D1 database: `gijiroku-search-db`

**Preview:**
- Variable name: `DB`
- D1 database: `gijiroku-search-db-preview`

## 4. カスタムドメイン設定（オプション）

### ドメイン追加
1. Pages プロジェクト → Custom domains
2. `Add custom domain`
3. ドメイン名入力（例: `gijiroku-search.example.com`）
4. DNS設定確認

### SSL/TLS設定
- Cloudflare → SSL/TLS → Overview
- 暗号化モード: "Full (strict)" 推奨

## 5. 動作確認

### API エンドポイントテスト
```bash
# 統計API
curl https://your-project.pages.dev/api/stats

# 検索API
curl "https://your-project.pages.dev/api/search?q=税制改革&limit=5"

# マニフェストAPI
curl https://your-project.pages.dev/api/manifestos

# 質問主意書API
curl "https://your-project.pages.dev/api/questions?limit=5"
```

### フロントエンド動作確認
1. https://your-project.pages.dev にアクセス
2. 検索機能のテスト
3. 各ページの表示確認
4. パフォーマンス確認

## 6. モニタリング設定

### Analytics有効化
1. Pages プロジェクト → Analytics
2. Web Analytics有効化

### ログ確認
```bash
# Pages Functions ログ確認
npx wrangler pages deployment tail --project-name=your-project

# D1データベースクエリ実行（デバッグ用）
npx wrangler d1 execute gijiroku-search-db --command="SELECT COUNT(*) FROM speeches"
```

## 7. パフォーマンス最適化

### キャッシュ設定
```typescript
// API Routeでのキャッシュヘッダー例
return NextResponse.json(data, {
  headers: {
    'Cache-Control': 's-maxage=3600, stale-while-revalidate=86400',
    'CDN-Cache-Control': 'max-age=3600'
  }
});
```

### D1クエリ最適化
- インデックス活用の確認
- EXPLAIN QUERY PLANでクエリプラン確認
- 大量データクエリの分割実行

## 8. 本番移行

### DNS切り替え（既存ドメインがある場合）
1. TTL短縮（事前準備）
2. Cloudflare DNS設定
3. 動作確認後にTTL復元

### モニタリング強化
- エラー率監視
- レスポンス時間監視
- D1データベース使用量監視

## トラブルシューティング

### よくある問題
1. **D1バインディングエラー**: 環境変数とwrangler.tomlの設定確認
2. **CORS エラー**: _middleware.tsの設定確認
3. **ビルドエラー**: Node.jsバージョンとnpmキャッシュクリア

### デバッグコマンド
```bash
# ローカル開発サーバー（D1接続）
npx wrangler pages dev frontend/out --d1 DB=gijiroku-search-db

# D1データベース状態確認
npx wrangler d1 info gijiroku-search-db
```