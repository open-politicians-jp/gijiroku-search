# ディレクトリ構成設計（2025年6月現在）

## 現在のディレクトリ構成

```
├── .claude/                          # Claude Code学習・開発記録
│   ├── learnings/                   # 技術的発見・学習内容
│   ├── development-notes/           # 開発プロセス記録
│   └── directory-structure.md       # このファイル
├── scripts/uv-data-collection/      # Python データ収集スクリプト
│   ├── daily_data_collection.py    # 議事録収集
│   ├── collect_questions_fixed.py  # 質問主意書収集
│   ├── collect_bills_fixed.py      # 提出法案収集
│   ├── collect_committee_news_fixed.py # 委員会ニュース収集
│   ├── collect_real_manifestos.py  # マニフェスト収集
│   ├── fix_questions_links.py      # リンク修正
│   ├── weekly_data_organizer.py    # 週次データ整理
│   ├── test_collection.py          # テスト
│   └── pyproject.toml              # UV設定
└── frontend/                       # Next.jsフロントエンド
    ├── public/data/                # フロントエンド用データ（直接配置）
    │   ├── speeches/               # 議事録データ
    │   ├── questions/              # 質問主意書データ（HTML/PDFリンク付き）
    │   ├── bills/                  # 提出法案データ
    │   ├── committee_news/         # 委員会ニュースデータ
    │   ├── manifestos/             # 政党マニフェストデータ
    │   ├── legislators/            # 議員データ
    │   ├── petitions/              # 請願・陳情データ
    │   └── weekly/                 # 週次統合データ
    │       └── 2025/               # 年別週次データ
    ├── components/                 # Reactコンポーネント
    │   ├── SearchForm.tsx
    │   ├── SearchResults.tsx
    │   ├── QuestionResults.tsx     # 質問主意書検索結果
    │   ├── BillsResults.tsx        # 提出法案検索結果
    │   ├── CommitteeNewsResults.tsx # 委員会ニュース検索結果
    │   ├── AboutPage.tsx           # Aboutページ
    │   └── StatsPage.tsx           # 統計ページ
    └── app/api/                    # APIエンドポイント
        ├── search/                 # 議事録検索
        ├── questions/              # 質問主意書検索
        ├── bills/                  # 提出法案検索
        ├── committee-news/         # 委員会ニュース検索
        └── stats/                  # 統計情報
```

## ファイル命名規則（現在）

### 収集データファイル
- `speeches_YYYYMMDD_HHMMSS.json` - 議事録データ
- `questions_YYYYMMDD_HHMMSS.json` - 質問主意書データ
- `bills_YYYYMMDD_HHMMSS.json` - 提出法案データ
- `committee_news_YYYYMMDD_HHMMSS.json` - 委員会ニュースデータ
- `manifestos_YYYYMMDD_HHMMSS.json` - マニフェストデータ

### 最新ファイル
- `*_latest.json` - 各カテゴリの最新データ

### 週次統合ファイル
- `speeches_YYYY_wWW.json` - 週次議事録データ（例: speeches_2025_w24.json）
- `bills_YYYY_wWW.json` - 週次法案データ
- `questions_YYYY_wWW.json` - 週次質問主意書データ

## データ管理の原則（更新）

1. **直接配置**: データは`frontend/public/data/`に直接保存
2. **バックアップなし**: 不要なバックアップファイルは作成しない
3. **リンク修正**: 相対URLを絶対URLに自動変換
4. **週次統合**: 週単位でのデータ管理とアクセス
5. **GitHub版管理**: Git履歴による版管理のみ

## 実装された機能

### データ収集
- ✅ 議事録データ収集（国会会議録検索API）
- ✅ 質問主意書収集（衆議院・参議院公式サイト）
- ✅ 提出法案収集（各院公式サイト）
- ✅ 委員会ニュース収集（公式サイト）
- ✅ マニフェスト収集（政党公式サイト）

### データ処理
- ✅ リンク修正システム（相対→絶対URL変換）
- ✅ 週次データ整理
- ✅ テキスト正規化処理

### フロントエンド機能
- ✅ 議事録検索
- ✅ 質問主意書検索（HTML/PDFリンク付き）
- ✅ 提出法案検索
- ✅ 委員会ニュース検索
- ✅ 統計情報表示