# ファイルサイズ管理ガイド

## GitHubファイルサイズ制限対応

### 制限事項
- **単一ファイル制限**: 100MB（警告は50MB）
- **リポジトリ制限**: 1GB推奨、5GB上限
- **Push制限**: 2GB

### 現在の対応策

#### 1. データファイル分割システム
大きなデータファイルは自動的に分割：

- `speeches_2025_processed.json` (66MB) → 月別分割
- `speeches_2025_03.json` (26MB) → 週別分割  
- `speeches_2025_02.json` (22MB) → 週別分割
- `speeches_2025_04.json` (15MB) → 週別分割

#### 2. 分割ツール
```bash
cd scripts/uv-data-collection

# 大きなファイルを分割
uv run python split_large_files.py

# 月次ファイルをさらに分割
uv run python split_large_monthly.py
```

#### 3. ファイル命名規則
- **月別**: `speeches_YYYY_MM.json`
- **週別**: `speeches_YYYY_MM_wNN.json`
- **バックアップ**: `.original`, `.large_backup` (gitignore対象)

#### 4. 現在のファイルサイズ状況
```
speeches_2025_01.json      1.6MB ✅
speeches_2025_02_w01.json  4.1MB ✅
speeches_2025_02_w02.json  3.8MB ✅
speeches_2025_02_w03.json  3.4MB ✅
speeches_2025_02_w04.json  11MB  ⚠️
speeches_2025_03_w01.json  3.0MB ✅
speeches_2025_03_w02.json  9.1MB ✅
speeches_2025_03_w03.json  2.8MB ✅
speeches_2025_03_w04.json  10MB  ⚠️
speeches_2025_04_w01.json  4.7MB ✅
speeches_2025_04_w02.json  5.6MB ✅
speeches_2025_04_w03.json  3.4MB ✅
speeches_2025_04_w04.json  1.0MB ✅
speeches_2025_05.json      1.1MB ✅
speeches_2025_06.json      19KB  ✅
```

### 監視とメンテナンス

#### 1. 定期チェック
```bash
# 大きなファイルをチェック
find frontend/public/data -name "*.json" -size +10M

# ファイルサイズ一覧
ls -lh frontend/public/data/speeches/
```

#### 2. 新しいデータ追加時の注意
- 月次データが15MB を超えた場合は週別分割を検討
- 週次データが15MBを超えた場合は日別分割を検討

#### 3. 自動分割の改善案
- GitHub Actionsでファイルサイズチェック
- 制限超過時の自動分割トリガー
- プルリクエスト時のファイルサイズ検証

### 代替案（将来検討）

#### 1. Git LFS使用
- 大きなファイルを別管理
- 帯域幅制限に注意（月1GB）

#### 2. 外部ストレージ
- S3/CloudFlare R2等での管理
- CDN配信でパフォーマンス向上

#### 3. データベース移行
- JSON → PostgreSQL/MongoDB
- API経由でのデータ提供

### トラブルシューティング

#### Push時のエラー
```bash
# 大きなファイルが含まれている場合
git filter-branch --tree-filter 'rm -f large-file.json' HEAD

# または、ファイル分割後に再コミット
git reset --soft HEAD~1
# ファイル分割実行
git add .
git commit -m "データファイル分割対応"
```

## 継続的な監視

このドキュメントは定期的に更新し、ファイルサイズの増大を監視することが重要です。