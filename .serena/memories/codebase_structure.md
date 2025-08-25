# コードベース構造

## ディレクトリ構成
```
nutrition-optimizer/
├── src/
│   ├── step1_constraints.py      # 栄養制約設定UI
│   ├── step2_foods.py           # 食品管理UI (検索・選択・価格設定)
│   ├── step3_optimize.py        # 最適化実行・結果表示
│   └── core/                    # コアエンジン
│       ├── nutrition_calculator.py     # 栄養制約計算
│       ├── food_helper.py             # 食品データベース
│       ├── fatty_acid_integrator.py   # 脂肪酸データ統合
│       ├── nutrition_constraint_mapper.py # 栄養素マッピング
│       ├── hybrid_data_loader.py      # ハイブリッドデータ読み込み
│       ├── optimizer.py               # 線形計画法エンジン
│       ├── nutrition_mapping.py       # MEXT成分表マッピング
│       └── data_loader.py             # 基本データ読み込み
├── data/
│   ├── raw/                     # MEXT食品成分表（Excel）
│   │   ├── 20230428-mxt_kagsei-mext_00001_012.xlsx  # 一般成分表
│   │   └── 20230428-mxt_kagsei-mext_00001_032.xlsx  # 脂肪酸成分表
│   ├── input/                   # 設定ファイル
│   │   ├── nutrition_constraints.csv   # 栄養制約設定
│   │   ├── foods.csv                  # 食品・価格データ
│   │   └── calculation_info.json      # 計算パラメータ
│   └── output/                  # 最適化結果
└── docs/                        # ドキュメント
    ├── mapping.md               # 栄養素マッピング詳細
    └── energy.md               # エネルギー計算説明
```

## 主要モジュール
- **step1-3**: ユーザーインターフェース（3ステップワークフロー）
- **core/optimizer.py**: 線形計画法の最適化エンジン
- **core/food_helper.py**: 食品検索・データベース機能
- **core/nutrition_calculator.py**: 栄養制約の計算ロジック
- **core/*_data_loader.py**: データ読み込み・統合機能
- **core/*_mapper.py**: 栄養素・食品のマッピング機能