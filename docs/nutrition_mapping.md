# 栄養素マッピング情報

このドキュメントは、日本語栄養素名と技術的識別子の対応関係を記載しています。

## Component ID マッピング

| 日本語栄養素名 | Component ID | 英語ID | 単位 | 備考 |
|---|---|---|---|---|
| エネルギー | ENERC_KCAL | energy_kcal | kcal | カロリー |
| たんぱく質 | PROTCAA | protein | g | アミノ酸組成による |
| 脂質 | FAT- | fat | g | 脂質総量 |
| 炭水化物 | CHOAVLM | carb_available | g | 利用可能炭水化物（単糖当量） |
| 食物繊維 | FIB- | fiber_total | g | 総食物繊維 |
| ビタミンA | VITA_RAE | retinol_activity_equiv | μgRAE | レチノール活性当量 |
| ビタミンB₁ | THIA | thiamin | mg | チアミン |
| ビタミンB₂ | RIBF | riboflavin | mg | リボフラビン |
| ナイアシン | NE | niacin | mg | ナイアシン当量 |
| パントテン酸 | PANTAC | pantothenic_acid | mg | パントテン酸 |
| ビオチン | BIOT | biotin | μg | ビオチン |
| ビタミンB₆ | VITB6A | vitamin_b6 | mg | ビタミンB₆ |
| ビタミンB₁₂ | VITB12 | vitamin_b12 | μg | ビタミンB₁₂ |
| 葉酸 | FOL | folate | μg | 葉酸 |
| ビタミンC | VITC | vitamin_c | mg | アスコルビン酸 |
| ビタミンD | VITD | vitamin_d | μg | ビタミンD |
| ビタミンE | TOCPHA | alpha_tocopherol | mg | α-トコフェロール |
| ビタミンK | VITK | vitamin_k | μg | ビタミンK |
| カリウム | K | potassium | mg | カリウム |
| カルシウム | CA | calcium | mg | カルシウム |
| マグネシウム | MG | magnesium | mg | マグネシウム |
| リン | P | phosphorus | mg | リン |
| 鉄 | FE | iron | mg | 鉄 |
| 亜鉛 | ZN | zinc | mg | 亜鉛 |
| 銅 | CU | copper | mg | 銅 |
| マンガン | MN | manganese | mg | マンガン |
| ヨウ素 | ID | iodine | μg | ヨウ素 |
| セレン | SE | selenium | μg | セレン |
| クロム | CR | chromium | μg | クロム |
| モリブデン | MO | molybdenum | μg | モリブデン |
| 食塩相当量 | NACL_EQ | salt_equiv | g | 食塩相当量 |
| n-3系脂肪酸 | FAPUN3 | n3_fatty_acid | g | n-3系多価不飽和脂肪酸 |
| n-6系脂肪酸 | FAPUN6 | n6_fatty_acid | g | n-6系多価不飽和脂肪酸 |
| 飽和脂肪酸 | FASAT | saturated_fat | g | 飽和脂肪酸 |

## データソース

- **メインデータ**: `/app/data/raw/20230428-mxt_kagsei-mext_00001_012.xlsx`（表全体シート）
- **脂肪酸データ**: 
  - `/app/data/raw/20230428-mxt_kagsei-mext_00001_032.xlsx`
  - `/app/data/raw/20230428-mxt_kagsei-mext_00001_033.xlsx`
  - `/app/data/raw/20230428-mxt_kagsei-mext_00001_034.xlsx`

## 注意事項

1. **エネルギー**: kcal（キロカロリー）を使用。kJ（キロジュール）ではない。
2. **たんぱく質**: アミノ酸組成によるたんぱく質を使用。
3. **炭水化物**: 利用可能炭水化物（単糖当量）を使用。
4. **ナイアシン**: ナイアシン当量（NE）を使用。
5. **脂肪酸**: 脂肪酸専用ファイルから統合したデータを使用。

## システム内でのデータ統一

すべてのCSVファイル（`nutrition_constraints.csv`, `foods.csv`）および処理において、**日本語栄養素名**を統一キーとして使用しています。英語IDやComponent IDは技術的な参照情報としてのみ利用します。