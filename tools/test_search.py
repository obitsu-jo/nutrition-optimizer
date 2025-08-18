#!/usr/bin/env python3
"""
食品検索のテストスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src', 'core'))

from food_helper import FoodCompositionDatabase

def test_search():
    db = FoodCompositionDatabase()
    
    test_keywords = ['米', '鶏', '卵', '牛乳', '豚']
    
    for keyword in test_keywords:
        print(f"\n=== '{keyword}'の検索結果 ===")
        matches = db.search_food(keyword)
        for i, match in enumerate(matches[:5]):
            calories = match.get('energy_kcal', 'N/A')
            protein = match.get('protein', 'N/A')
            fat = match.get('fat', 'N/A')
            carb = match.get('carb_available', 'N/A')
            print(f"{i+1}: {match['food_name']}")
            print(f"    エネルギー: {calories} kcal, たんぱく質: {protein} g, 脂質: {fat} g, 炭水化物: {carb} g")

if __name__ == "__main__":
    test_search()