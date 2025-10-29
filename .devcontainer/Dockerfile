# 1. ベースイメージの指定
FROM python:3.11-slim

# 2. システムパッケージの更新と、開発ツールおよびライブラリのインストール
RUN apt-get update && apt-get install -y \
    # 開発ツール
    git vim curl tree \
    # Pygameが依存するライブラリ群
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev \
    # aptキャッシュのクリーンアップ
    && rm -rf /var/lib/apt/lists/*

# 3. Dev Container用のグループと非rootユーザー(vscode)を作成する
RUN groupadd -g 1000 vscode && \
    useradd -m -s /bin/bash -u 1000 -g vscode vscode

# 4. 作業ディレクトリの設定と依存関係のインストール
WORKDIR /app
COPY --chown=vscode:vscode .devcontainer/requirements.txt .
RUN pip install uv && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=vscode:vscode . .

# 10. アプリケーションのデフォルト実行コマンド
CMD ["python", "src/main.py"]