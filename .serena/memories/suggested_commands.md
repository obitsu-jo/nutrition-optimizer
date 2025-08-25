# 推奨コマンド

## メイン実行コマンド
```bash
# 3ステップでの実行
python src/step1_constraints.py    # 栄養制約設定
python src/step2_foods.py         # 食品選択・価格設定
python src/step3_optimize.py      # 最適化実行
```

## 必要パッケージのインストール
```bash
pip install pandas pulp openpyxl
```

## デバッグ用コマンド
```bash
# 詳細ログを有効化
export NUTRITION_DEBUG=1
python src/step3_optimize.py
```

## データファイル関連
```bash
# 入力データの確認
ls data/input/
cat data/input/nutrition_constraints.csv
cat data/input/foods.csv

# 出力データの確認
ls data/output/
```

## 開発・テスト用コマンド
```bash
# Pythonのバージョン確認
python --version

# インストール済みパッケージ確認
pip list | grep -E "(pandas|pulp|openpyxl)"

# プロジェクトルートから各ステップを実行
cd /app
python src/step1_constraints.py
python src/step2_foods.py
python src/step3_optimize.py
```

## 一般的なLinuxコマンド
```bash
ls          # ファイル・ディレクトリ一覧
cd          # ディレクトリ移動
cat         # ファイル内容表示
grep        # 文字列検索
find        # ファイル検索
git         # gitコマンド
```

注意: このプロジェクトには requirements.txt、setup.py、pyproject.toml などの依存関係管理ファイルは存在しない。