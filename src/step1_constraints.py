#!/usr/bin/env python3
"""
Step1: ハイブリッド形式対応制約条件設定
体重と活動レベルから日本人の食事摂取基準に基づいた栄養制約を自動計算
結果をCSV + JSON のハイブリッド形式で保存
"""

import json
import pandas as pd
import os
import sys
from datetime import datetime
from typing import Dict, Any

# パスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'core'))

from nutrition_calculator import NutritionCalculator

def get_user_profile():
    """ユーザープロフィールを対話式で取得"""
    print("=== 個人プロフィール設定 ===")
    print("「日本人の食事摂取基準」に基づいた栄養制約を計算します。")
    print("現在は18-29歳男性の基準に対応しています。\n")
    
    # 体重の入力
    while True:
        try:
            weight = float(input("体重を入力してください (kg): "))
            if weight <= 0 or weight > 300:
                print("ERROR: 適切な体重を入力してください (1-300kg)")
                continue
            break
        except ValueError:
            print("ERROR: 有効な数値を入力してください")
    
    # 身体活動レベルの選択
    print(f"\n身体活動レベルを選択してください:")
    print("1. 低い (1.50) - 座位中心の生活")  
    print("2. ふつう (1.75) - 座位中心だが歩行や立位での活動も含む")
    print("3. 高い (2.00) - 立位での活動が多い、またはスポーツなど")
    
    activity_mapping = {
        "1": "低い",
        "2": "ふつう", 
        "3": "高い"
    }
    
    while True:
        choice = input("番号を選択してください [2]: ").strip()
        if not choice:
            choice = "2"  # デフォルト
        
        if choice in activity_mapping:
            activity_level = activity_mapping[choice]
            break
        else:
            print("ERROR: 1, 2, 3のいずれかを入力してください")
    
    return weight, activity_level

def create_nutrition_constraints_csv(constraints: Dict[str, Any], output_dir: str) -> str:
    """栄養制約をCSV形式で保存"""
    
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
        'vitamin_b6': 'ビタミンB群',
        'vitamin_b12': 'ビタミンB群',
        'folate': 'ビタミンB群',
        'biotin': 'ビタミンB群',
        'n6_fatty_acid': '脂肪酸',
        'n3_fatty_acid': '脂肪酸',
        'fiber_total': '食物繊維',
        'retinol_activity_equiv': 'ビタミン',
        'vitamin_d': 'ビタミン',
        'alpha_tocopherol': 'ビタミン',
        'vitamin_k': 'ビタミン',
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
    
    # CSVデータを作成
    nutrition_data = []
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
    
    # DataFrameに変換してソート
    nutrition_df = pd.DataFrame(nutrition_data)
    nutrition_df = nutrition_df.sort_values(['category', 'nutrient_name'])
    
    # CSV保存
    csv_path = os.path.join(output_dir, 'nutrition_constraints.csv')
    nutrition_df.to_csv(csv_path, index=False, encoding='utf-8')
    
    return csv_path

def save_hybrid_constraints(calc_result: Dict[str, Any]):
    """ハイブリッド形式で制約条件を保存"""
    
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'data', 'input')
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. nutrition_constraints.csv を保存
    nutrition_csv_path = create_nutrition_constraints_csv(
        calc_result["nutrition_constraints"], 
        output_dir
    )
    
    # 2. calculation_info.json を保存
    calc_info = {
        "calculation_params": calc_result["calculation_params"],
        "generated_at": datetime.now().isoformat(),
        "version": "1.0",
        "description": "体重と活動レベルに基づく栄養制約の自動計算結果"
    }
    
    calc_info_path = os.path.join(output_dir, 'calculation_info.json')
    with open(calc_info_path, 'w', encoding='utf-8') as f:
        json.dump(calc_info, f, ensure_ascii=False, indent=2)
    
    return {
        "nutrition_constraints": nutrition_csv_path,
        "calculation_info": calc_info_path
    }

def main():
    """メイン処理"""
    print("=== Step1: ハイブリッド形式制約条件設定 ===")
    print("体重と活動レベルから科学的根拠に基づいた栄養制約を自動計算します。")
    print("結果はCSV + JSON のハイブリッド形式で保存されます。\n")
    
    try:
        # 栄養計算機を初期化
        calculator = NutritionCalculator()
        
        # ユーザープロフィールを取得
        weight, activity_level = get_user_profile()
        
        # 栄養制約を計算
        print(f"\n>>> 栄養制約を計算しています...")
        calc_result = calculator.calculate_all_constraints(weight, activity_level)
        
        # 計算結果を表示
        params = calc_result["calculation_params"]
        constraints = calc_result["nutrition_constraints"]
        
        print(f"\n" + "="*60)
        print("*** 栄養制約計算結果 ***")
        print("="*60)
        
        print(f"\n基本情報:")
        print(f"  体重: {params['weight']} kg")
        print(f"  身体活動レベル: {params['activity_level']}")
        print(f"  基礎代謝量: {params['bmr']} kcal/日")
        print(f"  推定エネルギー必要量: {params['energy_needs']} kcal/日")
        
        print(f"\n*** 栄養制約: {len(constraints)}項目 ***")
        
        # ハイブリッド形式で保存
        print(f"\n>>> ハイブリッド形式で保存しています...")
        file_paths = save_hybrid_constraints(calc_result)
        
        # 最終サマリー
        print("\n" + "="*60)
        print("完了: ハイブリッド形式制約条件設定完了")
        print("="*60)
        
        print(f"\n生成されたファイル:")
        print(f"  - {file_paths['nutrition_constraints']}")
        print(f"  - {file_paths['calculation_info']}")
        
        print(f"\n利点:")
        print("  - CSV形式: スプレッドシートで編集可能")
        print("  - カテゴリ別整理: 栄養素を分類して表示")
        print("  - enabled列: 個別の制約ON/OFF切り替え可能")
        print("  - JSON形式: 計算パラメータを保存")
        
        print(f"\n次のステップ:")
        print("1. CSVファイルを編集して制約を調整（オプション）")
        print("2. src/step2_foods.py で食品情報を設定（食品制約テンプレートも自動生成）")
        print("3. src/step3_optimize.py で最適化を実行")
        
        return True
        
    except KeyboardInterrupt:
        print("\n\n操作が中断されました。")
        return False
    except Exception as e:
        print(f"\nERROR: エラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)