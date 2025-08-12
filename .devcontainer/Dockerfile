# 1. ベースイメージの指定
FROM python:3.11-slim

# 2. システムパッケージの更新と、開発ツールおよびライブラリのインストール
RUN apt-get update && apt-get install -y \
    # 開発ツール
    git vim curl \
    # Node.js (claude-code用)
    nodejs npm \
    # Pygameが依存するライブラリ群
    libsdl2-dev libsdl2-image-dev libsdl2-mixer-dev libsdl2-ttf-dev libfreetype6-dev \
    # aptキャッシュのクリーンアップ
    && rm -rf /var/lib/apt/lists/*

# 3. Dev Container用のグループと非rootユーザー(vscode)を作成する
RUN groupadd -g 1000 vscode && \
    useradd -m -s /bin/bash -u 1000 -g vscode vscode

# 4. ユーザーをvscodeに切り替えて、ユーザー固有の設定を行う
USER vscode

# 5. vscodeユーザーのホームに、npmグローバルパッケージ用のディレクトリを作成し、
#    npmにその場所を使用するよう設定する
RUN mkdir -p /home/vscode/.npm-global && \
    npm config set prefix '/home/vscode/.npm-global'

# 6. 作成したディレクトリをPATH環境変数に追加する
#    これにより、グローバルインストールしたコマンドが直接実行できるようになる
ENV PATH="/home/vscode/.npm-global/bin:${PATH}"

# 7. claude-codeをグローバルインストールする（vscodeユーザーとして実行される）
RUN npm install -g @anthropic-ai/claude-code

# 8. ユーザーをrootに戻す（以降の命令で必要があれば）
USER root

# 9. 作業ディレクトリの設定と依存関係のインストール
WORKDIR /app
COPY --chown=vscode:vscode .devcontainer/requirements.txt .
RUN pip install uv && \
    pip install --no-cache-dir -r requirements.txt

COPY --chown=vscode:vscode . .

# 10. アプリケーションのデフォルト実行コマンド
CMD ["python", "src/main.py"]