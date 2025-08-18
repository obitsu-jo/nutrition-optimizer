import pandas as pd
import json
from typing import Dict, Any, Tuple
from nutrition_mapping import NUTRITION_MAPPING, get_japanese_name

def load_foods(filepath: str) -> pd.DataFrame:
    """食品データを読み込む"""
    return pd.read_csv(filepath)

def load_constraints(filepath: str) -> Dict[str, Any]:
    """制約条件を読み込む"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_data(foods_path: str, constraints_path: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """全てのデータを読み込む"""
    foods = load_foods(foods_path)
    constraints = load_constraints(constraints_path)
    
    print(f"食品データ: {len(foods)}種類の食品を読み込みました")
    
    # 基本的な栄養情報を表示
    if not foods.empty:
        sample_foods = foods.head(3)
        print("\n食品サンプル:")
        for _, food in sample_foods.iterrows():
            print(f"- {food['food_name']}: {food.get('energy_kcal', 'N/A')} kcal, "
                  f"たんぱく質 {food.get('protein', 'N/A')} g, "
                  f"脂質 {food.get('fat', 'N/A')} g, "
                  f"炭水化物 {food.get('carb_available', 'N/A')} g")
        
        # 利用可能な栄養素列を表示
        nutrition_cols = [col for col in foods.columns if col not in ['food_name', 'price_per_100g']]
        print(f"\n利用可能な栄養素データ: {len(nutrition_cols)}項目")
    
    print(f"\n制約条件:")
    for nutrient, constraint in constraints.get('nutrition_constraints', {}).items():
        min_val = constraint.get('min', 'N/A')
        max_val = constraint.get('max', 'N/A')
        print(f"- {nutrient}: {min_val} - {max_val}")
    
    return foods, constraints