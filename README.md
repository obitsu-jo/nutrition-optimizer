# Nutrition Optimizer (栄養素最適化計算機)

摂取する栄養素の制約と使用する食材を設定し, 線形計画法によって値段が最も安くなる組みあわせを計算する.

## installation

vscodeのdevcontainer機能を使用する前提である.
リポジトリをクローンし, コンテナとして開くことで使用でる.

## 使用方法

1. 制約の設定

    `python -m src.step1_constraints -s {設定名1(任意の文字列)`
    を実行すると対話形式で推奨栄養素を設定することができ,
    `/app/data/step1_constraints/{設定名1}/`
    に`nutrient_constraints.csv`と`user_profile.json`が出力される.<br>
    `-u`をつけることで, `user_profile.json`を読み込んで制約を計算することができる.<br>
    出力された`nutrient_onstraints.csv`を形式を変えずに任意に書き換える.

2. 使用する食品の設定

    `python -m src.step2_foods -s {設定名2}`
    を実行すると対話形式で使用する食品を設定することができ, 
    `/app/data/step2_foods/{設定名2}/food_nutrient_data.csv`
    が出力される. また, ここで値段も設定する. この値段はすべてのデータで単位を揃える.<br>
    このデータは`/app/resources/step2/template/food_nutrient_data.csv`にあり, すべて100gごとの量になっていることに注意.<br>
    食品ごとに使用する量の上限と下限についても設定可能.<br>

3. 最適化の実行
    `python -m src.step3_optimize -s {設定名3} -s1 {設定名1} -s2 {設定名2}`
    を実行すると値段を最も安くするような組み合わせが
    `/app/data/step3_optimize/{設定名3}/results.csv`
    に出力される.