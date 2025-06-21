# CLAUDE.md

このファイルは、このリポジトリでコードを扱う際にClaude Code (claude.ai/code) に対してガイダンスを提供します。

## プロジェクト概要

日本の政治議事録横断検索システム - 国会議事録を収集・検索・公開するOSSプラットフォーム

### 目的
- 国会（衆議院・参議院）の議事録を収集・検索・公開
- 政党や議員の発言傾向・政策を国民が簡単に把握できるシステム
- 中立・非営利・匿名性を重視したオープンソースプロジェクト
- リアルタイム政党マニフェストと統計の包括的表示

### 現在の実装状況
- ✅ GitHub Actions による毎日自動データ収集（過去2ヶ月分）
- ✅ 強化されたテキスト処理パイプライン（全角スペース除去等）
- ✅ 実際の政党マニフェストデータ収集（主要7政党）
- ✅ 統計API制限解除（全発言者・政党・委員会を上限なし表示）
- ✅ Next.js専用アーキテクチャ（Docker Compose廃止）
- ✅ 構造化ディレクトリ（speeches/, manifestos/, legislators/, questions/, bills/, committee_news/）
- ✅ データ日付ベースのファイル命名システム
- ✅ 委員会ニュース検索機能
- ✅ 提出法案検索機能（ステータス・審議状況付き）
- ✅ 質問主意書検索機能（HTML/PDFリンク付き）
- ✅ リンク修正システム（相対URL→絶対URL変換）
- ✅ 週次データ管理（週単位でのデータ分類）
- ✅ 請願・陳情データ収集
- ✅ 議員一覧機能（参議院データ統合）
- ✅ console.log削除・ESLintルール強化

## 開発コマンド

### フロントエンド（Next.js + TypeScript）
```bash
cd frontend

# 依存関係インストール
npm ci

# 開発サーバー起動
npm run dev

# ビルド
npm run build

# 本番環境起動
npm run start

# Lintチェック
npm run lint
```

### データ収集（Python + UV）
```bash
cd scripts/uv-data-collection

# UV環境セットアップ
uv sync

# 毎日データ収集（過去2ヶ月分）
uv run python daily_data_collection.py

# データ加工パイプライン
uv run python data_processing_pipeline.py

# 質問主意書収集
uv run python collect_questions_fixed.py

# 委員会ニュース収集
uv run python collect_committee_news.py

# 提出法案収集
uv run python collect_bills.py

# 週次データ整理
uv run python weekly_data_organizer.py

# リンク修正
uv run python fix_questions_links.py

# テスト実行
uv run python test_collection.py
```

### Python開発環境（Docker版）
```bash
# Dockerコンテナでの開発
docker run -it --rm \
  -v $(pwd):/workspace \
  -w /workspace/scripts/uv-data-collection \
  python:3.11-slim \
  bash -c "curl -LsSf https://astral.sh/uv/install.sh | sh && uv sync && uv run python daily_data_collection.py"
```

## アーキテクチャ

### 全体構成
- **フロントエンド**: Next.js + TypeScript (API Routes内蔵)
- **データ収集**: Python + UV + GitHub Actions
- **データストレージ**: JSONファイル形式でGitリポジトリに保存
- **自動化**: GitHub Actions + cron（毎日午前3時JST）
- **検索**: サーバーサイド検索（Next.js API Routes）

### 参考プロジェクト・データソース
- **スマートニュース議案DB**: 衆参議院の議案情報オープンデータ化の先駆事例
- **オープンポリティクス**: 政治情報横断検索の参考アーキテクチャ
- **国会会議録検索API**: 議事録データの公式提供源

### ディレクトリ構造
```
├── .github/workflows/      # GitHub Actions
│   ├── data-collection.yml # データ収集ワークフロー
│   └── data-processing.yml # データ加工ワークフロー
├── scripts/
│   └── uv-data-collection/ # Python データ収集スクリプト
│       ├── daily_data_collection.py      # 毎日データ収集
│       ├── data_processing_pipeline.py   # データ加工パイプライン
│       └── pyproject.toml                # UV設定
├── frontend/               # Next.jsフロントエンド
│   ├── app/               # App Router
│   │   └── api/          # APIエンドポイント
│   ├── components/        # Reactコンポーネント
│   ├── public/data/      # フロントエンド用データ
│   │   ├── speeches/     # 議事録データ
│   │   ├── manifestos/   # マニフェストデータ
│   │   ├── legislators/  # 議員データ
│   │   ├── questions/    # 質問主意書データ
│   │   ├── bills/        # 提出法案データ
│   │   ├── committee_news/ # 委員会ニュースデータ
│   │   ├── petitions/    # 請願・陳情データ
│   │   ├── weekly/       # 週次統合データ
│   │   └── analysis/     # 分析結果
│   └── types/            # TypeScript型定義
└── CLAUDE.md             # このファイル
```

### データフロー
1. **データ収集**: 各種公式サイト → Python収集スクリプト → frontend/public/data/
2. **週次整理**: weekly_data_organizer.py → frontend/public/data/weekly/
3. **リンク修正**: fix_questions_links.py → 絶対URLに変換
4. **API提供**: frontend/public/data/ → Next.js API Routes → フロントエンド
5. **自動化**: GitHub Actions → データ収集・加工 → Git commit

### API設計
- `GET /api/search`: 議事録検索（クエリ、発言者、政党、委員会、日付範囲）
- `GET /api/stats`: 統計情報（総数、政党別、発言者別）
- `GET /api/manifestos`: マニフェストデータ
- `GET /api/questions`: 質問主意書検索
- `GET /api/bills`: 提出法案検索
- `GET /api/committee-news`: 委員会ニュース検索

### 技術スタック
- **Frontend**: Next.js 14, TypeScript, Tailwind CSS, Lucide React
- **Data Collection**: Python 3.11, UV, requests, BeautifulSoup4, fake-useragent
- **Data Storage**: JSON形式、Git管理
- **CI/CD**: GitHub Actions
- **Deployment**: Vercel / Cloudflare Pages（予定）

## 最新リリース情報

- **バージョン**: v1.0.1
- **リリース日**: 2025-06-21
- **主な変更**: GitHub Actions自動リリース対応

## 最新リリース情報

- **バージョン**: v1.0.2
- **リリース日**: 2025-06-21
- **主な変更**: GitHub Actions自動リリース対応

## 最新リリース情報

- **バージョン**: v1.0.3
- **リリース日**: 2025-06-21
- **主な変更**: GitHub Actions自動リリース対応

## 開発ガイドライン

### データ収集
- 国会会議録検索API（https://kokkai.ndl.go.jp/api.html）を使用
- 毎日午前3時JST → GitHub Actions自動実行
- 過去2ヶ月分のデータを収集
- IP偽装・レート制限対応（1-3秒間隔）

### データ形式
```json
{
  "id": "議事録ID",
  "date": "YYYY-MM-DD",
  "session": "会期番号",
  "house": "衆議院/参議院",
  "committee": "委員会名",
  "speaker": "発言者名",
  "party": "政党名",
  "party_normalized": "正規化政党名",
  "party_aliases": ["略称配列"],
  "text": "発言内容",
  "url": "議事録URL",
  "created_at": "ISO8601日時"
}
```

### UI/UX原則
- モダンでシンプルなデザイン
- 老若男女が操作しやすいインターフェース
- レスポンシブ対応
- アクセシビリティ配慮

### 中立性・プライバシー配慮
- 特定の政治的立場を取らない
- 公開情報のみを扱う
- 帰化歴等の機微情報は明示的公開時のみ表示
- オープンソース・透明性重視

### コードクオリティ・ESLint設定
- **console.log禁止**: 本番コードでは使用不可（console.warn, console.errorは許可）
- **ESLintルール**: `"no-console": ["error", { "allow": ["warn", "error"] }]`
- **Lintチェック**: コミット前に必ず`npm run lint`を実行
- **ビルドテスト**: プロダクション動作を`npm run build`で確認

## データ収集・処理の標準ルール

### GitHub Actions自動化ルール
- **毎日実行**: 過去2ヶ月分のデータ収集（午前3時JST）
- **直接配置**: 収集データを直接frontend/public/data/に保存
- **ディレクトリ構造**: 
  - `frontend/public/data/speeches/` - 議事録データ
  - `frontend/public/data/questions/` - 質問主意書データ
  - `frontend/public/data/bills/` - 提出法案データ
  - `frontend/public/data/committee_news/` - 委員会ニュース
  - `frontend/public/data/weekly/` - 週次統合データ

### ファイル命名規則
- **議事録**: `speeches_YYYYMMDD_HHMMSS.json`
- **質問主意書**: `questions_YYYYMMDD_HHMMSS.json`
- **提出法案**: `bills_YYYYMMDD_HHMMSS.json`
- **委員会ニュース**: `committee_news_YYYYMMDD_HHMMSS.json`
- **週次データ**: `speeches_YYYY_wWW.json` (例: `speeches_2025_w24.json`)
- **最新ファイル**: `*_latest.json`

### テキスト処理標準
1. **全角・半角スペース統一** - 全角スペースは半角に変換
2. **連続スペース除去** - 複数の連続スペースは1つに統一
3. **改行整理** - 3回以上の連続改行は2回まで制限
4. **タブ文字除去** - タブは半角スペースに変換
5. **行頭・行末空白除去** - 各行の前後の不要な空白を削除
6. **日本語構造保持** - 自然な日本語改行は保持

### データ処理パイプライン
```bash
# 1. 議事録データ収集
uv run python daily_data_collection.py

# 2. 質問主意書収集
uv run python collect_questions_fixed.py

# 3. 提出法案収集
uv run python collect_bills.py

# 4. 委員会ニュース収集
uv run python collect_committee_news.py

# 5. 週次データ整理
uv run python weekly_data_organizer.py

# 6. リンク修正
uv run python fix_questions_links.py
```

### 運用方針
- **直接配置**: データは直接frontend/public/data/に保存
- **バックアップなし**: 不要なバックアップファイルは作成しない
- **ログ出力**: 処理状況を詳細にログ記録
- **エラー対応**: 個別ファイル失敗でも全体処理は継続
- **リンク修正**: 相対URLを絶対URLに自動変換

### ディレクトリ分類
- **speeches/**: 国会議事録データ
- **questions/**: 質問主意書データ（HTML/PDFリンク付き）
- **bills/**: 提出法案データ
- **committee_news/**: 委員会ニュースデータ
- **manifestos/**: 政党マニフェストデータ
- **legislators/**: 議員関連データ
- **weekly/**: 週次統合データ

### UV環境設定
- **Python**: 3.11使用
- **パッケージ管理**: uv使用
- **IP偽装**: fake-useragent + User-Agentローテーション
- **レート制限**: 1-3秒のランダム間隔

### API更新ルール
- 新データファイルは自動的に検索対象に追加
- `*_latest.json` を最新ファイルとして使用
- **統計API制限解除**: 全ての政党・発言者・委員会データを上限なしで表示
- **リンク修正**: 質問主意書・法案のURLは絶対URLで提供
- **週次統合**: 週単位でのデータアクセスも可能

### 政党マニフェストデータ
- **リアルタイム収集**: 主要7政党の公式サイトから自動収集
  - 自由民主党、立憲民主党、日本維新の会、公明党
  - 日本共産党、国民民主党、れいわ新選組
- **サンプルデータ排除**: 実際のマニフェストデータのみ使用
- **定期更新**: GitHub Actions による自動更新

### 開発環境選択肢
- **ローカル**: UV環境での直接実行
- **Docker**: Python公式イメージ + UV での実行
- **GitHub Actions**: 本番環境と同じ環境での自動実行

## 毎回適用すべき重要ルール

### データ収集・処理
1. **毎日自動実行**: GitHub Actions で午前3時JST実行
2. **2ヶ月分収集**: 過去2ヶ月分のデータ収集
3. **直接配置**: データは直接frontend/public/data/に保存
4. **ディレクトリ分類**: speeches/, questions/, bills/, committee_news/, manifestos/, legislators/, weekly/
5. **ファイル命名**: *_YYYYMMDD_HHMMSS.json 形式
6. **テキスト処理**: 全角スペース削除、連続改行制限、日本語構造保持
7. **統計制限解除**: API結果に上限を設けない（全データ表示）
8. **リンク修正**: 相対URLを絶対URLに自動変換
9. **週次統合**: 週単位でのデータ管理システム

### ドキュメント管理
10. **常時最新化**: README.md と CLAUDE.md を常に最新状態に保つ
11. **繰り返し指示回避**: 確立されたルールは CLAUDE.md に記録して再指示を防ぐ

### 開発方針
12. **Next.js専用**: Docker Compose 不使用、Next.js単体構成
13. **GitHub Actions**: 全自動化でローカル作業不要
14. **UV使用**: Python パッケージ管理は UV で統一
15. **バックアップなし**: 不要なバックアップファイルは作成しない
16. **console.log禁止**: 本番コードではconsole.logを使用しない（console.warn, console.errorは許可）

## 確立されたワークフロー

### 標準作業手順
**対応完了後は必ず以下の手順で進める:**

1. **ブランチ作成**: `git checkout -b feat/機能名` でブランチ作成
2. **作業実行**: 要求された機能・修正を実装
3. **動作確認**: ローカルでテスト・ビルド確認
4. **変更コミット**: `git add . && git commit -m "説明"`
5. **プッシュ**: `git push -u origin ブランチ名`
6. **PR作成**: `gh pr create` でプルリクエスト作成

**ワークフロー自動化**: 上記手順は一連の流れで自動実行する

### Git管理ルール
- **メインブランチ保護**: 直接pushせずPRワークフロー必須
- **ブランチ戦略**: 
  - `fix/` (bugラベル): mainから直接作成
  - `feat/`, `docs/`, `refactor/`: releaseブランチから作成、複数機能をまとめてリリース
- **ブランチ命名**: `feat/`, `fix/`, `docs/` プレフィックス使用
- **コミットメッセージ**: 日本語で分かりやすい説明
- **PR説明**: Summary, Test plan を含む構造化された説明

## 計画中の機能開発

### 1. 両院議員一覧システム
**概要**: 衆議院・参議院議員の包括的データベース
- **議員基本情報**: 氏名、所属政党、選挙区、当選回数
- **政治資金**: 収支報告書データとの連携
- **発言履歴**: 議事録データとの紐付け
- **検索・フィルタリング**: 政党別、地域別、期別絞り込み

### 2. 政治資金収支報告書検索システム
**概要**: 議員・政党の政治資金の透明化
- **収支データ**: 収入・支出の詳細情報
- **時系列分析**: 年度別・月別の資金動向
- **比較機能**: 議員間・政党間の資金比較
- **可視化**: グラフ・チャートによる資金流れの視覚化

### 3. スマートニュース連携
**概要**: 外部プラットフォームとの連携強化
- **記事リンク**: 関連ニュース記事への自動リンク
- **議案データベース**: スマートニュース議案DBとの連携
- **リアルタイム情報**: 最新政治動向の統合表示
- **ライセンス確認**: 使用許可の確認と適切な実装

### 4. データ統合ダッシュボード
**概要**: 全データソースの統合ビュー
- **議員プロフィール**: 発言・資金・ニュースの統合表示
- **政党分析**: 各政党の活動状況の包括的分析
- **トレンド分析**: 政治的な議論の動向把握
- **検索横断**: 全データソース対応の統合検索

### 5. 技術基盤強化
**概要**: システム拡張に向けた基盤整備
- **API拡張**: 新データソース対応のAPI設計
- **パフォーマンス**: 大容量データ処理の最適化
- **セキュリティ**: 政治情報の適切な取り扱い
- **監査ログ**: アクセス・操作の透明性確保