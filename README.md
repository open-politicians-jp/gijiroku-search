# 🇯🇵 日本政治議事録検索システム

国会議事録を横断検索できるオープンソースプラットフォーム

## 🎯 プロジェクトの目的

政治をもっと身近に、もっと透明に。

このプロジェクトは、国会（衆議院・参議院）の議事録を収集・検索・公開し、政党や議員の発言傾向・政策を国民が簡単に把握できるオープンソースプラットフォームです。

### 特徴

- ✅ **包括的なデータ**: 国会議事録を網羅的に収集・整理
- 🛡️ **中立・非営利**: 特定の政治的立場を取らず、客観的な情報提供に徹底
- 🌟 **オープンソース**: コミュニティ主導で透明性を保持
- 🔍 **高性能検索**: 発言者、政党、委員会、日付での詳細検索
- 📱 **レスポンシブ対応**: スマートフォンからPC まで対応

## 🚀 クイックスタート

### Next.js フロントエンド（推奨）

```bash
# リポジトリのクローン
git clone <repository-url>
cd new-jp-search

# フロントエンドセットアップ
cd frontend
npm ci
npm run dev

# ブラウザでアクセス
open http://localhost:3000
```

### データ収集（開発者向け）

```bash
# Python UV環境でのデータ収集
cd scripts/uv-data-collection
uv sync
uv run python daily_data_collection.py
```

### GitHub Pages デプロイ

```bash
# 静的ビルド（SPA対応）
cd frontend
npm run build

# outディレクトリが生成され、GitHub Pagesにデプロイ可能
```

## 📊 データ収集

### 自動収集（GitHub Actions）

- **毎日 3:00 JST**: 過去2ヶ月分の議事録を自動取得
- **収集後自動実行**: データ加工・テキストクリーニング
- **リアルタイム更新**: 政党マニフェストを定期更新

### 手動収集（開発者向け）

```bash
cd scripts/uv-data-collection

# 毎日データ収集（過去2ヶ月分）
uv run python daily_data_collection.py

# データ加工パイプライン
uv run python data_processing_pipeline.py

# 政党マニフェスト収集
uv run python collect_real_manifestos.py
```

## 🏗️ アーキテクチャ

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │  GitHub Actions │    │  Data Sources   │
│   (Next.js)     │───▶│  Data Pipeline  │───▶│  国会議事録API   │
│                 │    │                 │    │  政党公式サイト  │
│ • 検索UI        │    │ • 毎日データ収集 │    │                 │
│ • 統計表示      │    │ • テキスト加工   │    │ • 議事録データ   │
│ • API Routes    │    │ • 自動デプロイ   │    │ • マニフェスト   │
│ • レスポンシブ   │    │ • JSON配置      │    │ • 自動収集      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ 技術スタック

### フロントエンド
- **Next.js 14**: React フレームワーク（App Router）
- **TypeScript**: 型安全性
- **Tailwind CSS**: ユーティリティファーストCSS
- **Lucide React**: アイコンライブラリ
- **API Routes**: 内蔵バックエンド

### データ収集・処理
- **Python 3.11**: データ収集言語
- **UV**: Python パッケージマネージャー
- **BeautifulSoup4**: HTMLパース
- **Requests + fake-useragent**: IP偽装対応HTTP
- **GitHub Actions**: 自動データ収集

### データ
- **JSON形式**: 構造化データストレージ
- **Git管理**: バージョン管理・バックアップ
- **ディレクトリ分類**: speeches/, manifestos/, analysis/

### インフラ・DevOps
- **GitHub Actions**: CI/CD 自動化
- **Docker**: Python開発環境
- **GitHub Pages**: 静的サイトデプロイ（SPA対応）
- **Vercel/Cloudflare**: 代替デプロイ環境

## 📁 プロジェクト構造

```
├── .github/workflows/           # GitHub Actions
│   ├── data-collection.yml     # データ収集ワークフロー
│   └── data-processing.yml     # データ加工ワークフロー
├── scripts/
│   └── uv-data-collection/     # Python データ収集
│       ├── daily_data_collection.py    # 毎日データ収集
│       ├── data_processing_pipeline.py # データ加工
│       ├── collect_real_manifestos.py  # 政党マニフェスト
│       └── pyproject.toml              # UV設定
├── frontend/                   # Next.js フロントエンド
│   ├── app/                   # App Router
│   │   └── api/              # API エンドポイント
│   ├── components/           # React コンポーネント
│   ├── public/data/         # フロントエンド用データ
│   │   ├── speeches/        # 議事録データ
│   │   ├── manifestos/      # マニフェストデータ
│   │   └── legislators/     # 議員データ
│   └── types/              # TypeScript 型定義
├── data/                   # データストレージ
│   ├── raw/               # 生データ
│   ├── processed/         # 加工済みデータ
│   └── backup/            # バックアップ
└── CLAUDE.md             # 開発者ガイド
```

## 🤝 コントリビューション

このプロジェクトはオープンソースです。改善提案、バグ報告、機能追加のプルリクエストを歓迎します。

### 開発への参加方法

1. このリポジトリをフォーク
2. 機能ブランチを作成 (`git checkout -b feature/amazing-feature`)
3. 変更をコミット (`git commit -m 'Add some amazing feature'`)
4. ブランチにプッシュ (`git push origin feature/amazing-feature`)
5. プルリクエストを作成

### コントリビューションガイドライン

- 中立性を保つ：特定の政治的立場を取らない
- プライバシー配慮：公開情報のみを扱う
- オープンソース精神：透明性と協調を重視

## 📜 ライセンス

MIT License - 詳細は [LICENSE](LICENSE) ファイルを参照

## 📈 機能

### 現在の機能
- **議事録検索**: 発言者、政党、委員会、キーワード検索
- **統計表示**: 発言数、政党別・議員別ランキング（上限なし）
- **マニフェスト**: 主要7政党の最新政策（自民、立民、維新、公明、共産、国民、れいわ）
- **レスポンシブUI**: スマートフォン・タブレット・PC対応
- **自動データ更新**: GitHub Actions による毎日自動収集

### 今後の機能
- **AI分析**: 議員発言傾向の自動分析
- **可視化**: グラフ・チャートによる統計表示
- **通知機能**: 特定議員・政党の発言アラート
- **比較機能**: 政党間・議員間の発言比較

## 🔗 関連リンク

### データソース
- [国会会議録検索API](https://kokkai.ndl.go.jp/api.html) - メインデータソース

### 参考リソース・類似プロジェクト
- [衆議院議案データベース（スマートニュース）](https://smartnews-smri.github.io/house-of-representatives/) - 議案情報のオープンデータ化
- [参議院データベース（スマートニュース）](https://smartnews-smri.github.io/house-of-councillors/) - 参議院関連情報の構造化
- [オープンポリティクス](https://search.openpolitics.or.jp/home) - 政治情報の横断検索プラットフォーム

### 開発・運用
- [開発者ガイド](CLAUDE.md) - 技術仕様・開発環境

## 💬 サポート

質問や提案がありましたら、GitHub Issues でお気軽にお聞かせください。

---

**政治をもっと身近に、もっと透明に** 🇯🇵