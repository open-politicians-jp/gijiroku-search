# GitHub Pages セットアップガイド

## GitHub Pages デプロイ手順

### 1. リポジトリ設定

1. **GitHubリポジトリ** → **Settings** → **Pages**
2. **Source**: `GitHub Actions` を選択
3. **Custom domain** (オプション): カスタムドメインがある場合は設定

### 2. 必要なファイル

以下のファイルが準備済みです：

#### ✅ Next.js設定
- `frontend/next.config.js` - 静的エクスポート設定
- `frontend/public/.nojekyll` - Jekyllのビルドを無効化
- `frontend/public/CNAME` - カスタムドメイン設定用（コメントアウト済み）

#### ✅ GitHub Actions
- `.github/workflows/deploy-github-pages.yml` - デプロイワークフロー

#### ✅ プロジェクト管理
- `.github/CODEOWNERS` - コードレビュー設定
- `.github/pull_request_template.md` - PR テンプレート

### 3. デプロイワークフロー

#### 自動デプロイ
- **mainブランチへのpush時**: 自動デプロイ
- **Pull Request時**: ビルドテストのみ

#### 手動デプロイ
1. GitHubリポジトリ → **Actions**
2. **Deploy to GitHub Pages** を選択
3. **Run workflow** をクリック

### 4. ビルド内容

#### 含まれるもの
- Next.js アプリケーション（静的ファイル）
- 既存のデータファイル（議事録、質問主意書、法案等）
- 検索機能（クライアントサイド）

#### 含まれないもの
- サーバーサイド機能（API Routes は静的生成）
- リアルタイムデータ更新
- Python データ収集スクリプト

### 5. パフォーマンス最適化

#### Next.js最適化
```javascript
// next.config.js
{
  output: 'export',           // 静的エクスポート
  trailingSlash: true,        // GitHub Pages用
  images: { unoptimized: true }, // 画像最適化無効
  compress: true              // gzip圧縮
}
```

#### キャッシュ戦略
- Next.js ビルドキャッシュ
- npm依存関係キャッシュ
- 静的アセットの長期キャッシュ

### 6. URL構造

#### 本番URL
```
https://[username].github.io/[repository-name]/
```

#### ページ構造
```
/                    # トップページ（検索）
/about              # このサイトについて
/stats              # 統計情報
/data/*             # 静的データファイル
```

### 7. カスタムドメイン設定（オプション）

#### CNAMEファイル更新
```bash
# frontend/public/CNAME
your-domain.com
```

#### DNS設定
```
Type: CNAME
Name: www (or @)
Value: [username].github.io
```

### 8. SSL/HTTPS

GitHub Pagesは自動的にHTTPS対応：
- `*.github.io` ドメイン: 自動SSL
- カスタムドメイン: Let's Encrypt証明書

### 9. 監視とメンテナンス

#### デプロイ状況確認
1. **Actions** タブでビルド・デプロイ状況を確認
2. **Environments** でデプロイ履歴を確認

#### トラブルシューティング
- ビルドエラー: Actions ログを確認
- 404エラー: `trailingSlash: true` 設定を確認
- アセット読み込みエラー: `basePath` 設定を確認

### 10. データ更新戦略

#### 現在の方式
- 静的データファイルをリポジトリにコミット
- ビルド時にデータを含めて配信

#### 将来の改善案
- 外部API からのデータ取得
- CDN経由での配信最適化
- 差分更新システム

## 注意事項

### ファイルサイズ制限
- 単一ファイル: 100MB未満（現在最大11MB）
- リポジトリ全体: 1GB推奨

### 更新頻度
- GitHub Actions: 月2,000分まで無料
- Pages ビルド: 月10回まで推奨

### セキュリティ
- 機密情報は含めない
- 環境変数は使用不可（静的サイト）
- HTTPS強制設定推奨