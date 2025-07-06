# 🐍 データ収集スクリプト

日本政治議事録検索システムのPythonデータ収集スクリプト集

## 📁 ディレクトリ構成

```
scripts/
├── uv-data-collection/          # メインのUVプロジェクト
│   ├── daily_data_collection.py    # 毎日の議事録データ収集
│   ├── collect_questions_fixed.py  # 質問主意書収集
│   ├── collect_bills.py            # 提出法案収集
│   ├── collect_committee_news_enhanced.py # 委員会ニュース収集
│   ├── weekly_data_organizer.py    # 週次データ整理
│   ├── fix_questions_links.py      # リンク修正
│   ├── update_policy_summaries.py  # 政策要約JSON生成
│   ├── pyproject.toml               # UV設定ファイル
│   └── uv.lock                      # UV依存関係ロック
├── individual_manifesto_research.md # マニフェスト調査
└── README.md                        # このファイル
```

## 🚀 セットアップ（UV環境）

### 1. UV のインストール

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### 2. プロジェクトセットアップ

```bash
cd scripts/uv-data-collection
uv sync  # 依存関係のインストール
```

## 📊 データ収集の実行

### 毎日データ収集（推奨）

```bash
cd scripts/uv-data-collection

# 過去2ヶ月分の議事録を収集
uv run python daily_data_collection.py
```

### 個別データ収集

```bash
# 質問主意書収集
uv run python collect_questions_fixed.py

# 提出法案収集  
uv run python collect_bills.py

# 委員会ニュース収集（強化版）
uv run python collect_committee_news_enhanced.py

# 週次データ整理
uv run python weekly_data_organizer.py

# リンク修正（相対URL→絶対URL）
uv run python fix_questions_links.py

# 政策要約JSON生成
uv run python update_policy_summaries.py
```

## 📦 収集されるデータ

このシステムは以下のデータを自動収集・整理します：

### 📋 議事録データ (speeches/)
- **国会会議録検索API** からの議事録データ
- 過去2ヶ月分を毎日更新
- 発言者、政党、委員会、内容を構造化

### ❓ 質問主意書 (questions/)
- **質問主意書検索システム** からの質問・答弁データ
- HTML/PDFリンク付き
- 絶対URLで参照可能

### 📜 提出法案 (bills/)
- **国会提出法案データベース** からの法案情報
- ステータス・審議状況付き
- 衆参両院対応

### 📰 委員会ニュース (committee_news/)
- **各委員会公式サイト** からのニュース
- 全22委員会対応
- 強化版データ収集

### 🗂️ 週次データ (weekly/)
- 週単位でのデータ分類・管理
- CSV/JSON両形式で出力
- 長期トレンド分析対応

### 出力先ディレクトリ

すべてのデータは `../../frontend/public/data/` に保存されます：
```
frontend/public/data/
├── speeches/           # 議事録データ
├── questions/          # 質問主意書データ  
├── bills/              # 提出法案データ
├── committee_news/     # 委員会ニュース
├── weekly/             # 週次統合データ
└── policy_summaries.json # 政策要約統合データ
```

## 🔄 GitHub Actions での自動実行

システムは **GitHub Actions** で毎日自動実行されます：

### 🕒 自動実行スケジュール
- **毎日 3:00 JST**: 過去2ヶ月分のデータ収集
- **自動コミット**: 収集データを直接リポジトリにコミット
- **エラー通知**: 失敗時はGitHub Issuesで通知

### 📋 実行ワークフロー

現在のワークフロー設定（`.github/workflows/data-collection.yml`）：

```yaml
name: 📊 Daily Data Collection
on:
  schedule:
    - cron: '18 0 * * *'  # 毎日 3:18 JST (UTC+9)
  workflow_dispatch:     # 手動実行も可能

jobs:
  collect-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: 🐍 Setup Python & UV
        run: |
          curl -LsSf https://astral.sh/uv/install.sh | sh
          echo "$HOME/.cargo/bin" >> $GITHUB_PATH
          
      - name: 📊 Run Data Collection
        working-directory: scripts/uv-data-collection
        run: |
          uv sync
          uv run python daily_data_collection.py
          uv run python weekly_data_organizer.py
          
      - name: 💾 Commit Data Updates
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add frontend/public/data/
          git commit -m "📊 Daily data update: $(date '+%Y-%m-%d %H:%M JST')" || exit 0
          git push
```

## 🏷️ 政党正規化システム

データ収集時に政党名を自動正規化：

### 正規化ルール
- **自由民主党**: 自民党、自民、LDP → `自由民主党`  
- **立憲民主党**: 立憲、立民、CDP → `立憲民主党`
- **日本維新の会**: 維新、維新の会 → `日本維新の会`
- **公明党**: 公明、CGP → `公明党`
- **日本共産党**: 共産党、共産、JCP → `日本共産党`
- **国民民主党**: 国民、DPP → `国民民主党`
- **れいわ新選組**: れいわ → `れいわ新選組`

### エイリアス管理
政党エイリアスは `frontend/public/data/speeches/party_aliases.json` で管理されています。

## 🔧 技術仕様

### 依存関係管理
- **UV**: 高速なPythonパッケージ管理
- **Python 3.11+**: 最新のPython機能を活用
- **依存関係**: `pyproject.toml` で宣言的管理

### データ処理機能
- **IP偽装**: `fake-useragent` でUser-Agentローテーション
- **レート制限**: 1-3秒のランダム間隔でリクエスト
- **エラー処理**: 個別ファイル失敗でも全体処理継続
- **テキスト正規化**: 全角スペース削除、改行整理
- **リンク修正**: 相対URL → 絶対URL自動変換

## 📝 ログ・デバッグ

### 実行ログ
```bash
# 詳細ログ付きで実行
uv run python daily_data_collection.py --verbose

# 特定の国会回次のみ
uv run python collect_committee_news_enhanced.py --session 217

# 過去30日分のみ
uv run python collect_committee_news_enhanced.py --days 30
```

### トラブルシューティング
- **メモリ不足**: 大量データ処理時のメモリ使用量注意
- **ネットワークエラー**: レート制限・IP制限の回避設定
- **文字化け**: UTF-8エンコーディング確認