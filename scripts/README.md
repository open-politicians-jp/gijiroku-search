# データ収集スクリプト

このディレクトリには、日本政治データ収集システムのPythonスクリプトが含まれています。

## ファイル構成

- `fetch_data.py` - メインデータ収集スクリプト（議事録、マニフェスト、議員データ）
- `fetch_speeches.py` - レガシー議事録取得スクリプト
- `requirements.txt` - Python依存関係
- `venv/` - Python仮想環境
- `README.md` - このファイル

## セットアップ

### 1. 仮想環境の有効化

```bash
cd scripts
source venv/bin/activate  # macOS/Linux
# または
venv\Scripts\activate.bat  # Windows
```

### 2. 依存関係のインストール

```bash
pip install -r requirements.txt
```

## スクリプトの実行

### メインデータ収集スクリプト

```bash
python fetch_data.py
```

このスクリプトは以下のデータを収集します：
- 📊 国会議事録データ（過去30日間、最大500件）
- 📋 政党マニフェストデータ（サンプル）
- 👥 議員データ（サンプル）
- 🏷️ 政党略称マッピング

### 出力先

すべてのデータは `../frontend/public/data/` ディレクトリに保存されます：
- `speeches_YYYYMMDD_HHMMSS.json`
- `manifestos_YYYYMMDD_HHMMSS.json`
- `legislators_YYYYMMDD_HHMMSS.json`
- `party_aliases.json`

## GitHub Actions での使用

このスクリプトは GitHub Actions の cron job での自動実行を想定して設計されています。

### 例: .github/workflows/data-collection.yml

```yaml
name: Data Collection
on:
  schedule:
    - cron: '0 3 * * *'  # 毎日3時に実行
  workflow_dispatch:  # 手動実行も可能

jobs:
  collect-data:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
          
      - name: Install dependencies
        run: |
          cd scripts
          pip install -r requirements.txt
          
      - name: Collect data
        run: |
          cd scripts
          python fetch_data.py
          
      - name: Commit and push changes
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add frontend/public/data/
          git commit -m "Update data: $(date)" || exit 0
          git push
```

## 政党略称対応

スクリプトは以下の政党略称に対応しています：

- 自由民主党 → 自民党、自民、LDP
- 立憲民主党 → 立憲、立民、CDP
- 公明党 → 公明、CGP
- 日本維新の会 → 維新、維新の会、大阪維新
- など...

## ログ

スクリプト実行時には詳細な進行状況とエラーログが出力されます。