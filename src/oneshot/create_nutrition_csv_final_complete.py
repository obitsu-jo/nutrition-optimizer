#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
from pathlib import Path

def create_nutrition_csv_final_complete():
    """
    メインデータと3つの脂肪酸ファイルを統合して、34項目完全なCSVを作成
    """
    # ファイルパス
    main_data_path = Path("/app/data/raw/20230428-mxt_kagsei-mext_00001_012.xlsx")
    fatty_acid_paths = [
        Path(f"/app/data/raw/20230428-mxt_kagsei-mext_00001_03{i}.xlsx") 
        for i in range(2, 5)
    ]
    
    print("=== メインデータの読み込み ===")
    # メインデータの読み込み
    main_df = pd.read_excel(main_data_path, sheet_name=0, skiprows=2)
    
    # 食品名と各栄養素のマッピング（test.logの成分識別子に基づき修正）
    nutrient_mapping = {
        'エネルギー': 6,      # ENERC_KCAL (kcal)
        'ビタミンA': 42,      # VITA_RAE
        'ビタミンC': 58,      # VITC
        'ビタミンD': 43,      # VITD
        'ビタミンE': 44,      # TOCPHA
        'ビタミンK': 48,      # VITK
        'ナイアシン': 52,     # NE (ナイアシン当量)
        'パントテン酸': 56,   # PANTAC
        'ビオチン': 57,       # BIOT
        'ビタミンB₁': 49,     # THIA
        'ビタミンB₁₂': 54,    # VITB12
        'ビタミンB₂': 50,     # RIBF
        'ビタミンB₆': 53,     # VITB6A
        '葉酸': 55,          # FOL
        'カリウム': 24,       # K
        'カルシウム': 25,     # CA
        'クロム': 35,        # CR
        'セレン': 34,        # SE
        'マグネシウム': 26,   # MG
        'マンガン': 31,      # MN
        'モリブデン': 36,     # MO
        'ヨウ素': 33,        # ID
        'リン': 27,          # P
        '亜鉛': 29,          # ZN
        '鉄': 28,            # FE
        '銅': 30,            # CU
        '食塩相当量': 60,     # NACL_EQ
        'たんぱく質': 8,      # PROTCAA (アミノ酸組成による)
        '炭水化物': 13,       # CHOAVLM (利用可能炭水化物単糖当量)
        '脂質': 12,          # FAT-
        '食物繊維': 18       # FIB-
    }
    
    print("=== 脂肪酸データの読み込みと統合 ===")
    # 脂肪酸データの読み込み
    fatty_acid_data = {}
    
    for i, path in enumerate(fatty_acid_paths):
        if path.exists():
            print(f"読み込み中: {path.name}")
            fatty_df = pd.read_excel(path, sheet_name=0, skiprows=2)
            fatty_header = fatty_df.iloc[0, :].tolist()
            
            # 必要な脂肪酸列を日本語名で探す
            fatty_cols = {}
            for j, header in enumerate(fatty_header):
                if pd.notna(header):
                    header_str = str(header).strip().replace('\n', '')
                    if header_str == '飽和脂肪酸':
                        fatty_cols['飽和脂肪酸'] = j
                    elif 'n-3系多価不飽和脂肪酸' in header_str:
                        fatty_cols['n-3系脂肪酸'] = j
                    elif 'n-6系多価不飽和脂肪酸' in header_str:
                        fatty_cols['n-6系脂肪酸'] = j
            
            print(f"  見つかった列: {fatty_cols}")
            
            # データ行を取得（2行目以降）
            fatty_data_rows = fatty_df.iloc[1:].copy()
            
            # 食品名列は3番目
            food_names = fatty_data_rows.iloc[:, 3]
            
            # 各脂肪酸データを辞書に格納
            for fatty_name, col_idx in fatty_cols.items():
                if fatty_name not in fatty_acid_data:
                    fatty_acid_data[fatty_name] = {}
                
                fatty_values = fatty_data_rows.iloc[:, col_idx]
                
                for food_name, value in zip(food_names, fatty_values):
                    if pd.notna(food_name):
                        food_key = str(food_name).strip()
                        if food_key not in fatty_acid_data[fatty_name]:
                            fatty_acid_data[fatty_name][food_key] = value
    
    print(f"脂肪酸データ統計:")
    for fatty_name, data_dict in fatty_acid_data.items():
        print(f"  {fatty_name}: {len(data_dict)}件")
    
    print("\n=== メインデータの処理 ===")
    # メインデータから実際のデータ行を抽出（2行目以降）
    data_rows = main_df.iloc[1:].copy()
    
    # 結果用データフレーム作成
    result_df = pd.DataFrame()
    result_df['名前'] = data_rows.iloc[:, 3]  # 食品名列
    
    # 34項目の栄養素リスト（nutrition_constraints.csvの順序）とメタデータ
    target_nutrients = [
        'エネルギー', 'ビタミンA', 'ビタミンC', 'ビタミンD', 'ビタミンE', 'ビタミンK',
        'ナイアシン', 'パントテン酸', 'ビオチン', 'ビタミンB₁', 'ビタミンB₁₂', 'ビタミンB₂',
        'ビタミンB₆', '葉酸', 'カリウム', 'カルシウム', 'クロム', 'セレン', 'マグネシウム',
        'マンガン', 'モリブデン', 'ヨウ素', 'リン', '亜鉛', '鉄', '銅', '食塩相当量',
        'たんぱく質', '炭水化物', '脂質', 'n-3系脂肪酸', 'n-6系脂肪酸', '飽和脂肪酸', '食物繊維'
    ]
    
    # 栄養素メタデータ（識別子と単位）
    nutrient_metadata = {
        'エネルギー': {'id': 'energy_kcal', 'unit': 'kcal', 'component_id': 'ENERC_KCAL'},
        'ビタミンA': {'id': 'retinol_activity_equiv', 'unit': 'μgRAE', 'component_id': 'VITA_RAE'},
        'ビタミンC': {'id': 'vitamin_c', 'unit': 'mg', 'component_id': 'VITC'},
        'ビタミンD': {'id': 'vitamin_d', 'unit': 'μg', 'component_id': 'VITD'},
        'ビタミンE': {'id': 'alpha_tocopherol', 'unit': 'mg', 'component_id': 'TOCPHA'},
        'ビタミンK': {'id': 'vitamin_k', 'unit': 'μg', 'component_id': 'VITK'},
        'ナイアシン': {'id': 'niacin', 'unit': 'mg', 'component_id': 'NE'},
        'パントテン酸': {'id': 'pantothenic_acid', 'unit': 'mg', 'component_id': 'PANTAC'},
        'ビオチン': {'id': 'biotin', 'unit': 'μg', 'component_id': 'BIOT'},
        'ビタミンB₁': {'id': 'thiamin', 'unit': 'mg', 'component_id': 'THIA'},
        'ビタミンB₁₂': {'id': 'vitamin_b12', 'unit': 'μg', 'component_id': 'VITB12'},
        'ビタミンB₂': {'id': 'riboflavin', 'unit': 'mg', 'component_id': 'RIBF'},
        'ビタミンB₆': {'id': 'vitamin_b6', 'unit': 'mg', 'component_id': 'VITB6A'},
        '葉酸': {'id': 'folate', 'unit': 'μg', 'component_id': 'FOL'},
        'カリウム': {'id': 'potassium', 'unit': 'mg', 'component_id': 'K'},
        'カルシウム': {'id': 'calcium', 'unit': 'mg', 'component_id': 'CA'},
        'クロム': {'id': 'chromium', 'unit': 'μg', 'component_id': 'CR'},
        'セレン': {'id': 'selenium', 'unit': 'μg', 'component_id': 'SE'},
        'マグネシウム': {'id': 'magnesium', 'unit': 'mg', 'component_id': 'MG'},
        'マンガン': {'id': 'manganese', 'unit': 'mg', 'component_id': 'MN'},
        'モリブデン': {'id': 'molybdenum', 'unit': 'μg', 'component_id': 'MO'},
        'ヨウ素': {'id': 'iodine', 'unit': 'μg', 'component_id': 'ID'},
        'リン': {'id': 'phosphorus', 'unit': 'mg', 'component_id': 'P'},
        '亜鉛': {'id': 'zinc', 'unit': 'mg', 'component_id': 'ZN'},
        '鉄': {'id': 'iron', 'unit': 'mg', 'component_id': 'FE'},
        '銅': {'id': 'copper', 'unit': 'mg', 'component_id': 'CU'},
        '食塩相当量': {'id': 'salt_equiv', 'unit': 'g', 'component_id': 'NACL_EQ'},
        'たんぱく質': {'id': 'protein', 'unit': 'g', 'component_id': 'PROTCAA'},
        '炭水化物': {'id': 'carb_available', 'unit': 'g', 'component_id': 'CHOAVLM'},
        '脂質': {'id': 'fat', 'unit': 'g', 'component_id': 'FAT-'},
        'n-3系脂肪酸': {'id': 'n3_fatty_acid', 'unit': 'g', 'component_id': 'FAPUN3'},
        'n-6系脂肪酸': {'id': 'n6_fatty_acid', 'unit': 'g', 'component_id': 'FAPUN6'},
        '飽和脂肪酸': {'id': 'saturated_fat', 'unit': 'g', 'component_id': 'FASAT'},
        '食物繊維': {'id': 'fiber_total', 'unit': 'g', 'component_id': 'FIB-'}
    }
    
    # 各栄養素のデータを取得
    for nutrient in target_nutrients:
        if nutrient in nutrient_mapping:
            # メインデータから取得
            col_index = nutrient_mapping[nutrient]
            result_df[nutrient] = data_rows.iloc[:, col_index]
        elif nutrient in fatty_acid_data:
            # 脂肪酸データから取得
            print(f"脂肪酸データから {nutrient} をマッピング中...")
            fatty_values = []
            for food_name in result_df['名前']:
                food_key = str(food_name).strip() if pd.notna(food_name) else ""
                if food_key in fatty_acid_data[nutrient]:
                    fatty_values.append(fatty_acid_data[nutrient][food_key])
                else:
                    fatty_values.append(np.nan)
            result_df[nutrient] = fatty_values
        else:
            result_df[nutrient] = np.nan
    
    print("\n=== データクリーニング ===")
    # 有効なデータ行のみ抽出
    valid_mask = (
        result_df['名前'].notna() & 
        (result_df['名前'].astype(str).str.strip() != '') & 
        (result_df['名前'].astype(str) != 'nan')
    )
    result_df_clean = result_df[valid_mask].copy()
    
    # ヘッダー行を除外
    header_keywords = ['単位', '成分識別子', '食　品　群', '食品群']
    for keyword in header_keywords:
        mask = ~result_df_clean['名前'].astype(str).str.contains(keyword, na=False)
        result_df_clean = result_df_clean[mask]
    
    print(f"有効データの形状: {result_df_clean.shape}")
    
    # 出力
    output_path = Path("/app/oneshot/nutrition_complete_34items.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # メタデータ行（識別子と単位）を作成
    id_row = ['nutrient_id'] + [nutrient_metadata.get(nutrient, {}).get('id', '') for nutrient in target_nutrients]
    unit_row = ['unit'] + [nutrient_metadata.get(nutrient, {}).get('unit', '') for nutrient in target_nutrients]
    component_row = ['component_id'] + [nutrient_metadata.get(nutrient, {}).get('component_id', '') for nutrient in target_nutrients]
    
    # シンプルなCSVファイルを書き込み（ヘッダー + データ行のみ）
    with open(output_path, 'w', encoding='utf-8') as f:
        # ヘッダー行のみ
        f.write('名前,' + ','.join(target_nutrients) + '\n')
        
        # データ行
        for _, row in result_df_clean.iterrows():
            values = [str(row['名前'])]
            for nutrient in target_nutrients:
                value = row[nutrient]
                values.append(str(value) if pd.notna(value) else '')
            f.write(','.join(values) + '\n')
    
    print(f"シンプルなCSVファイルを保存しました: {output_path}")
    print("ヘッダー行 + データ行のみのシンプル構造です")
    
    # サンプルデータの表示
    print("\n=== 作成されたCSVのサンプル（最初の3行） ===")
    print(result_df_clean.head(3))
    
    # データの統計
    print("\n=== データ統計 ===")
    non_null_counts = result_df_clean.count()
    complete_nutrients = 0
    missing_nutrients = []
    
    for col, count in non_null_counts.items():
        if col != '名前':
            print(f"  {col}: {count}")
            if count > 1000:  # 十分なデータがある
                complete_nutrients += 1
            else:
                missing_nutrients.append(col)
    
    print(f"\n完全にデータが取得できた栄養素: {complete_nutrients}/34項目")
    if missing_nutrients:
        print(f"不足している栄養素: {missing_nutrients}")
    
    return result_df_clean

if __name__ == "__main__":
    result = create_nutrition_csv_final_complete()
    if result is not None:
        print("\n処理が正常に完了しました")
        print("34項目の栄養素データを含むCSVファイルが作成されました。")
    else:
        print("\n処理中にエラーが発生しました")