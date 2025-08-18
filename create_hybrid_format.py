#!/usr/bin/env python3
"""
ハイブリッド形式（CSV + JSON）のサンプルを作成
"""

import json
import pandas as pd
import os
import sys

# パスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'src', 'core'))

from nutrition_calculator import NutritionCalculator

def create_hybrid_format():
    """ハイブリッド形式のサンプルを作成"""
    print("=== ハイブリッド形式サンプル作成 ===")
    
    calculator = NutritionCalculator()
    
    # テストパラメータ
    weight = 70.0
    activity_level = "ふつう"
    
    # 制約を計算
    calc_result = calculator.calculate_all_constraints(weight, activity_level)
    
    # 1. nutrition_constraints.csv を作成
    nutrition_data = []
    
    # カテゴリマッピング
    category_mapping = {
        'energy_kcal': 'エネルギー',
        'protein': '主要栄養素',
        'fat': '主要栄養素', 
        'carb_available': '主要栄養素',
        'saturated_fat': '脂質',
        'thiamin': 'ビタミンB群',
        'riboflavin': 'ビタミンB群',
        'niacin': 'ビタミンB群',
        'pantothenic_acid': 'ビタミンB群',
        'n6_fatty_acid': '脂肪酸',
        'n3_fatty_acid': '脂肪酸',
        'fiber_total': '食物繊維',
        'retinol_activity_equiv': 'ビタミン',
        'vitamin_d': 'ビタミン',
        'alpha_tocopherol': 'ビタミン',
        'vitamin_k': 'ビタミン',
        'vitamin_b6': 'ビタミンB群',
        'vitamin_b12': 'ビタミンB群',
        'folate': 'ビタミンB群',
        'biotin': 'ビタミンB群',
        'vitamin_c': 'ビタミン',
        'salt_equiv': 'ミネラル',
        'potassium': 'ミネラル',
        'calcium': 'ミネラル',
        'magnesium': 'ミネラル',
        'phosphorus': 'ミネラル',
        'iron': 'ミネラル',
        'zinc': 'ミネラル',
        'copper': 'ミネラル',
        'manganese': 'ミネラル',
        'iodine': 'ミネラル',
        'selenium': 'ミネラル',
        'chromium': 'ミネラル',
        'molybdenum': 'ミネラル'
    }
    
    # 日本語名マッピング
    japanese_names = {
        'energy_kcal': 'エネルギー',
        'protein': 'たんぱく質',
        'fat': '脂質',
        'carb_available': '炭水化物',
        'saturated_fat': '飽和脂肪酸',
        'thiamin': 'ビタミンB₁',
        'riboflavin': 'ビタミンB₂',
        'niacin': 'ナイアシン',
        'pantothenic_acid': 'パントテン酸',
        'n6_fatty_acid': 'n-6系脂肪酸',
        'n3_fatty_acid': 'n-3系脂肪酸',
        'fiber_total': '食物繊維',
        'retinol_activity_equiv': 'ビタミンA',
        'vitamin_d': 'ビタミンD',
        'alpha_tocopherol': 'ビタミンE',
        'vitamin_k': 'ビタミンK',
        'vitamin_b6': 'ビタミンB₆',
        'vitamin_b12': 'ビタミンB₁₂',
        'folate': '葉酸',
        'biotin': 'ビオチン',
        'vitamin_c': 'ビタミンC',
        'salt_equiv': '食塩相当量',
        'potassium': 'カリウム',
        'calcium': 'カルシウム',
        'magnesium': 'マグネシウム',
        'phosphorus': 'リン',
        'iron': '鉄',
        'zinc': '亜鉛',
        'copper': '銅',
        'manganese': 'マンガン',
        'iodine': 'ヨウ素',
        'selenium': 'セレン',
        'chromium': 'クロム',
        'molybdenum': 'モリブデン'
    }
    
    constraints = calc_result["nutrition_constraints"]
    
    for nutrient, constraint in constraints.items():
        nutrition_data.append({
            'nutrient_id': nutrient,
            'nutrient_name': japanese_names.get(nutrient, nutrient),
            'category': category_mapping.get(nutrient, 'その他'),
            'min_value': constraint.get('min', ''),
            'max_value': constraint.get('max', ''),
            'unit': constraint.get('unit', ''),
            'enabled': 'TRUE'
        })
    
    # DataFrameに変換してCSV保存
    nutrition_df = pd.DataFrame(nutrition_data)
    nutrition_df = nutrition_df.sort_values(['category', 'nutrient_name'])
    
    nutrition_csv_path = 'data/input/nutrition_constraints.csv'
    os.makedirs(os.path.dirname(nutrition_csv_path), exist_ok=True)
    nutrition_df.to_csv(nutrition_csv_path, index=False, encoding='utf-8')
    
    # 2. calculation_info.json を作成
    calc_info = {
        "calculation_params": calc_result["calculation_params"],
        "generated_at": "2024-01-15T10:30:00Z",
        "version": "1.0"
    }
    
    calc_info_path = 'data/input/calculation_info.json'
    with open(calc_info_path, 'w', encoding='utf-8') as f:
        json.dump(calc_info, f, ensure_ascii=False, indent=2)
    
    # 3. food_constraints.csv を作成（サンプル）
    food_data = [
        {'food_name': '米', 'max_grams': 600, 'enabled': 'TRUE'},
        {'food_name': '鶏卵', 'max_grams': 300, 'enabled': 'TRUE'},
        {'food_name': '牛乳', 'max_grams': 500, 'enabled': 'TRUE'}
    ]
    
    food_df = pd.DataFrame(food_data)
    food_csv_path = 'data/input/food_constraints.csv'
    food_df.to_csv(food_csv_path, index=False, encoding='utf-8')
    
    # 結果表示
    print(f"✅ ハイブリッド形式ファイルを生成しました:")
    print(f"   📊 {nutrition_csv_path} ({len(nutrition_df)}項目)")
    print(f"   ⚙️  {calc_info_path}")
    print(f"   🍽️  {food_csv_path} ({len(food_df)}項目)")
    
    print(f"\n📋 nutrition_constraints.csv の内容（上位10項目）:")
    print(nutrition_df.head(10).to_string(index=False))
    
    print(f"\n📋 カテゴリ別項目数:")
    category_counts = nutrition_df['category'].value_counts()
    for category, count in category_counts.items():
        print(f"   {category}: {count}項目")

if __name__ == "__main__":
    create_hybrid_format()