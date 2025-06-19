# ブランチ保護設定ガイド

## mainブランチ保護設定

以下の設定をGitHubのリポジトリ設定で行ってください：

### 1. ブランチ保護ルールの作成
1. GitHubリポジトリ → Settings → Branches
2. "Add rule" をクリック
3. Branch name pattern: `main`

### 2. 推奨設定

#### 必須設定
- ✅ **Require a pull request before merging**
  - Required number of reviewers: 1
  - ✅ Dismiss stale PR approvals when new commits are pushed
  - ✅ Require review from code owners

#### セキュリティ設定
- ✅ **Require status checks to pass before merging**
  - ✅ Require branches to be up to date before merging
  - 必要に応じてCIチェックを追加

#### 管理者設定
- ✅ **Restrict pushes that create files larger than 100MB**
- ✅ **Include administrators** (推奨: 管理者も同じルールに従う)

#### マージ設定
- ✅ **Allow merge commits**
- ✅ **Allow squash merging**
- ✅ **Allow rebase merging**

### 3. コードオーナー設定の有効化

`.github/CODEOWNERS` ファイルが作成済みです。
このファイルにより、すべての変更に対して @hironeko の承認が必要になります。

### 4. 設定後の動作

1. **Pull Request作成時**: 自動的に @hironeko がレビュワーとして指定
2. **マージ時**: コードオーナーの承認が必須
3. **直接push**: mainブランチへの直接pushは禁止

## 緊急時の対応

管理者は必要に応じてブランチ保護ルールを一時的にバイパスできますが、
通常時は同じルールに従うことを推奨します。

## 設定確認手順

1. テスト用ブランチを作成
2. 軽微な変更をコミット
3. Pull Request作成
4. レビュー・マージプロセスを確認