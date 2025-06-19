# GitHub Actions ワークフロー

このディレクトリには、日本政治データ検索システムの自動化ワークフローが含まれています。

## ワークフロー概要

### 1. 📊 data-collection.yml
**目的**: 政治データの自動収集
- **実行タイミング**: 毎日午前3時（JST）/ 手動実行
- **処理内容**:
  - 国会議事録データの取得（過去30日間、最大500件）
  - 政党マニフェストデータの更新
  - 議員データの更新
  - フロントエンドのビルドテスト
  - データファイルのコミット・プッシュ

### 2. 🔧 ci.yml
**目的**: コード品質とビルドの継続的インテグレーション
- **実行タイミング**: main/developブランチへのプッシュ、プルリクエスト
- **処理内容**:
  - フロントエンド: 型チェック、ビルドテスト
  - Python スクリプト: インポートテスト、設定検証
  - 統合テスト: API接続テスト

### 3. 🚀 deploy.yml
**目的**: 本番環境への自動デプロイ
- **実行タイミング**: mainブランチへのプッシュ / 手動実行
- **処理内容**:
  - フロントエンドのビルド
  - Vercel または GitHub Pages へのデプロイ

## 環境変数とシークレット

### データ収集ワークフロー用
- `MAX_RECORDS`: 取得する議事録の最大件数（デフォルト: 500）
- `DAYS_BACK`: 過去何日分のデータを取得するか（デフォルト: 30）

### デプロイワークフロー用（オプション）
- `VERCEL_TOKEN`: Vercel デプロイトークン
- `VERCEL_ORG_ID`: Vercel 組織ID
- `VERCEL_PROJECT_ID`: Vercel プロジェクトID

## セットアップ手順

### 1. リポジトリ設定
```bash
# GitHub Actions の有効化（自動的に有効になります）
git add .github/
git commit -m "Add GitHub Actions workflows"
git push
```

### 2. シークレットの設定（Vercel使用の場合）
1. GitHub リポジトリの Settings → Secrets and variables → Actions
2. 以下のシークレットを追加:
   - `VERCEL_TOKEN`
   - `VERCEL_ORG_ID`
   - `VERCEL_PROJECT_ID`

### 3. 初回手動実行
1. GitHub の Actions タブに移動
2. "🗂️ Data Collection" ワークフローを選択
3. "Run workflow" で手動実行

## ワークフロー監視

### 成功時の動作
- ✅ データ収集: 新しい JSON ファイルが `frontend/public/data/` に作成
- ✅ CI: 全テストが通過
- ✅ デプロイ: 新しいバージョンが公開

### 失敗時の対応
1. **データ収集失敗**:
   - 国会API のステータス確認
   - ネットワーク接続の確認
   - Python 依存関係の確認

2. **CI失敗**:
   - TypeScript エラーの修正
   - ESLint エラーの修正
   - ビルドエラーの修正

3. **デプロイ失敗**:
   - ビルド成果物の確認
   - デプロイ設定の確認
   - シークレットの設定確認

## カスタマイズ

### データ収集頻度の変更
`data-collection.yml` の cron 式を修正:
```yaml
schedule:
  - cron: '0 18 * * *'  # 毎日18:00 UTC（日本時間3:00）
  - cron: '0 6 18 * *'  # 毎週18日の6:00 UTC
```

### 取得データ量の変更
ワークフロー実行時にパラメータを指定:
- `max_records`: 最大議事録件数
- `days_back`: 過去何日分

### 通知設定
失敗時の通知を追加する場合:
```yaml
- name: 📧 Notify on failure
  if: failure()
  uses: 8398a7/action-slack@v3
  with:
    status: failure
    webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## データ管理

### アーティファクト
- データファイルは30日間保持されます
- 手動ダウンロード可能

### ストレージ
- 各データファイルは数MB程度
- 1年間で約1-2GB の想定

## トラブルシューティング

### よくある問題

1. **Python 依存関係エラー**
   ```
   解決策: scripts/requirements.txt を更新
   ```

2. **Next.js ビルドエラー**
   ```
   解決策: 型定義の修正、コンパイルエラーの解決
   ```

3. **API レート制限**
   ```
   解決策: fetch_data.py の sleep 時間を調整
   ```

### ログの確認
1. GitHub の Actions タブ
2. 実行したワークフローをクリック
3. 各ステップのログを確認