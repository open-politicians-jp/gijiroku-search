# Git Worktree 並列作業ガイド

## 🌳 Worktree環境概要

複数のissueを並列で作業するためのgit worktree環境をセットアップしました。

## 📁 ディレクトリ構造

```
new-jp-search/                    # メインリポジトリ（現在: fix/github-actions-errors）
├── frontend/
├── scripts/
└── CLAUDE.md

../worktrees/                     # 並列作業用ディレクトリ
├── issue-4-api-routes/          # Issue #4: APIルート実装
├── issue-6-bills-links/         # Issue #6: 法案リンク修正
└── issue-7-radio-clear/         # Issue #7: ラジオボタン初期化
```

## 🎯 各Issue別作業環境

### Issue #4: APIルート実装 (feat/issue-4-api-routes)
```bash
cd ../worktrees/issue-4-api-routes
# APIエンドポイント作成 (3-4時間の大作業)
# - frontend/app/api/bills/route.ts
# - frontend/app/api/questions/route.ts  
# - frontend/app/api/committee-news/route.ts
# - frontend/app/api/search/route.ts
# - frontend/app/api/stats/route.ts
```

### Issue #6: 法案リンク修正 (feat/issue-6-bills-links)
```bash
cd ../worktrees/issue-6-bills-links
# 審議経過リンクの404エラー修正
# - frontend/public/data/bills/ のデータクリーニング
# - scripts/uv-data-collection/ のURL生成修正
```

### Issue #7: ラジオボタン初期化 (feat/issue-7-radio-clear)
```bash
cd ../worktrees/issue-7-radio-clear
# UI改善: 検索タイプ切り替え時の結果クリア
# - frontend/components/SearchForm.tsx
# - frontend/app/page.tsx
```

## 🔧 作業コマンド

### 特定のissueで作業開始
```bash
# Issue #7（最も軽い作業）から開始する場合
cd ../worktrees/issue-7-radio-clear

# ブランチ確認
git branch
# → * feat/issue-7-radio-clear

# 作業実行
# ...

# コミット・プッシュ
git add .
git commit -m "🔄 ラジオボタン切り替え時に検索結果をクリア"
git push -u origin feat/issue-7-radio-clear

# PR作成
gh pr create --title "🔄 ラジオボタン切り替え時に検索結果をクリア" --body "Issue #7対応..."
```

### 別のissueに切り替え
```bash
# Issue #6に切り替え
cd ../worktrees/issue-6-bills-links

# ブランチ確認
git branch
# → * feat/issue-6-bills-links

# 作業続行...
```

### メインリポジトリでの確認
```bash
# メインに戻る
cd /Users/hironeko/Work/private/new-jp-search

# 全worktreeの状況確認
git worktree list

# 全ブランチの状況
git branch -a
```

## 🚀 推奨作業順序

### 1. Issue #7（軽い作業、30分）
- UI改善のため影響範囲が限定的
- 他のissueと競合しにくい
- 成功体験として最初に完了

### 2. Issue #6（中程度、1-2時間）
- データクリーニングとURL修正
- スクリプト修正が主体
- フロントエンドへの影響少

### 3. Issue #4（重い作業、3-4時間）
- 大規模なAPI実装
- 他の修正完了後に着手
- 十分な時間を確保

## ⚠️ 注意事項

### データファイルの競合
各worktreeで`frontend/public/data/`を変更する場合は注意が必要：
- Issue #6: bills/のデータ修正
- Issue #4: 全データファイル読み込み

### 依存関係
- Issue #4は他のissue完了後に着手推奨
- Issue #6、#7は並列実行可能

### クリーンアップ
```bash
# 作業完了後のworktree削除
git worktree remove ../worktrees/issue-7-radio-clear
git branch -d feat/issue-7-radio-clear  # ローカルブランチ削除
```

## 🔄 同期とマージ

### 最新のmainから作業開始
```bash
cd ../worktrees/issue-7-radio-clear
git fetch origin
git rebase origin/main  # 必要に応じて
```

### PR作成とマージ後の同期
```bash
# PR #5がマージされた後
cd ../worktrees/issue-6-bills-links
git fetch origin
git rebase origin/main  # 最新の変更を取り込み
```

## 📝 作業ログ

- ✅ **Worktree環境構築完了** (2025-06-20)
- [ ] Issue #7: ラジオボタン初期化
- [ ] Issue #6: 法案リンク修正  
- [ ] Issue #4: APIルート実装

これで効率的な並列開発が可能になりました！