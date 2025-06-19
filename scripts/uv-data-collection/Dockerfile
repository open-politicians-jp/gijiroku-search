# Python UV環境でのデータ収集用Dockerファイル
FROM python:3.11-slim

# 作業ディレクトリ設定
WORKDIR /app

# システムパッケージ更新
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# UV インストール
RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:$PATH"

# プロジェクトファイルをコピー
COPY pyproject.toml uv.lock ./

# UV環境セットアップ
RUN uv sync --frozen

# ソースコードをコピー
COPY . .

# 実行権限付与
RUN chmod +x *.py

# デフォルトコマンド
CMD ["uv", "run", "python", "daily_data_collection.py"]