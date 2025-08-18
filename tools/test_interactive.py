#!/usr/bin/env python3
"""
対話式食品データ作成の簡単テスト
"""

from src.food_helper import FoodCompositionDatabase
import pandas as pd
import os

def create_sample_foods():
    """サンプル食品データを作成"""
    db = FoodCompositionDatabase()
    
    # 手動で選択
    selected_foods = [
        {
            'keyword': '精白米',
            'price': 60
        },
        {
            'keyword': '鶏卵　全卵　生', 
            'price': 200  # 卵1個約50g想定なので100gで約200円
        },
        {
            'keyword': '牛乳',
            'price': 80   # 牛乳100mlで約80円
        }
    ]
    
    foods_list = []
    
    for item in selected_foods:
        matches = db.search_food(item['keyword'])
        if matches:
            selected = matches[0]  # 最初の結果を選択
            food_entry = selected.copy()
            food_entry['price_per_100g'] = item['price']
            foods_list.append(food_entry)
            print(f"追加: {selected['food_name']}")
    
    # CSVファイルを生成
    if foods_list:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        output_path = os.path.join(base_dir, 'data', 'input', 'foods.csv')
        df = pd.DataFrame(foods_list)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\n{len(foods_list)}件の食品データを{output_path}に保存しました。")
        print("\n生成されたデータ:")
        print(df.to_string(index=False))

if __name__ == "__main__":
    create_sample_foods()