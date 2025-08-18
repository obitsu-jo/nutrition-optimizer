#!/usr/bin/env python3
"""
ハイブリッド形式（CSV + JSON）データローダー
"""

import pandas as pd
import json
import os
from typing import Dict, Any, Tuple

def load_hybrid_data(base_dir: str) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    ハイブリッド形式からデータを読み込む
    
    Args:
        base_dir: プロジェクトのベースディレクトリ
        
    Returns:
        Tuple[foods_df, constraints_dict]
    """
    
    input_dir = os.path.join(base_dir, 'data', 'input')
    
    # 1. 食品データを読み込み
    foods_path = os.path.join(input_dir, 'foods.csv')
    if not os.path.exists(foods_path):
        raise FileNotFoundError(f"foods.csvが見つかりません: {foods_path}")
    
    foods = pd.read_csv(foods_path)
    
    # enabled=Trueの食品のみをフィルタリング
    if 'enabled' in foods.columns:
        original_count = len(foods)
        foods = foods[foods['enabled'] == True].copy()
        print(f"📊 食品データ: {len(foods)}種類の食品を読み込みました (全{original_count}種類中の有効な食品)")
    else:
        print(f"📊 食品データ: {len(foods)}種類の食品を読み込みました")
    
    # 2. 栄養制約をCSVから読み込み
    nutrition_constraints_path = os.path.join(input_dir, 'nutrition_constraints.csv')
    nutrition_constraints = {}
    
    if os.path.exists(nutrition_constraints_path):
        nutrition_df = pd.read_csv(nutrition_constraints_path)
        
        # enabled=TRUEの制約のみを取得
        active_constraints = nutrition_df[nutrition_df['enabled'] == True].copy() if 'enabled' in nutrition_df.columns else nutrition_df
        
        for _, row in active_constraints.iterrows():
            constraint = {}
            
            # 最小値・最大値を設定
            if pd.notna(row['min_value']) and row['min_value'] != '':
                constraint['min'] = float(row['min_value'])
            if pd.notna(row['max_value']) and row['max_value'] != '':
                constraint['max'] = float(row['max_value'])
            
            # 単位を設定
            if pd.notna(row['unit']) and row['unit'] != '':
                constraint['unit'] = str(row['unit'])
            
            if constraint:  # 空でない場合のみ追加
                nutrition_constraints[row['nutrient_id']] = constraint
        
        print(f"🔬 栄養制約: {len(nutrition_constraints)}項目を読み込みました")
    else:
        print("⚠️  nutrition_constraints.csvが見つかりません")
    
    # 3. 食品制約をfoods.csvから読み込み（単位数ベース）
    food_constraints = {}
    
    # 現在のfoods DataFrameは既にenabled=Trueでフィルタ済み
    for _, row in foods.iterrows():
        constraint = {}
        
        # 最小単位数制約
        if 'min_units' in foods.columns:
            min_units_val = row['min_units']
            if pd.notna(min_units_val) and str(min_units_val).strip() != '' and float(min_units_val) > 0:
                constraint['min_units'] = float(min_units_val)
        
        # 最大単位数制約
        if 'max_units' in foods.columns:
            max_units_val = row['max_units']
            if pd.notna(max_units_val) and str(max_units_val).strip() != '' and float(max_units_val) > 0:
                constraint['max_units'] = float(max_units_val)
        
        # 制約がある場合のみ追加
        if constraint:
            food_constraints[row['food_name']] = constraint
    
    print(f"🍽️  食品制約: {len(food_constraints)}項目を読み込みました")
    
    # 4. 計算情報をJSONから読み込み
    calc_info_path = os.path.join(input_dir, 'calculation_info.json')
    calculation_info = {}
    
    if os.path.exists(calc_info_path):
        with open(calc_info_path, 'r', encoding='utf-8') as f:
            calculation_info = json.load(f)
        print(f"⚙️  計算情報を読み込みました")
    else:
        print("⚠️  calculation_info.jsonが見つかりません")
    
    # 5. 食品データのサンプル表示
    if not foods.empty:
        sample_foods = foods.head(3)
        print(f"\n📋 食品サンプル:")
        for _, food in sample_foods.iterrows():
            print(f"  • {food['food_name']}: {food.get('energy_kcal', 'N/A')} kcal, "
                  f"たんぱく質 {food.get('protein', 'N/A')} g")
        
        nutrition_cols = [col for col in foods.columns if col not in ['food_name', 'price_per_100g']]
        print(f"\n🔬 利用可能な栄養素データ: {len(nutrition_cols)}項目")
    
    # 6. 制約条件のサマリー表示
    if nutrition_constraints:
        print(f"\n📊 栄養制約サマリー:")
        
        # カテゴリ別に表示（CSVにカテゴリがある場合）
        if os.path.exists(nutrition_constraints_path):
            category_summary = nutrition_df[nutrition_df['enabled'] == True]['category'].value_counts() if 'enabled' in nutrition_df.columns else nutrition_df['category'].value_counts()
            for category, count in category_summary.head(5).items():
                print(f"  • {category}: {count}項目")
        
        # 主要制約を表示
        key_nutrients = ['energy_kcal', 'protein', 'fat', 'carb_available']
        for nutrient in key_nutrients:
            if nutrient in nutrition_constraints:
                constraint = nutrition_constraints[nutrient]
                min_val = constraint.get('min', 'N/A')
                max_val = constraint.get('max', 'N/A')
                unit = constraint.get('unit', '')
                print(f"  • {nutrient}: {min_val} - {max_val} {unit}")
    
    # 7. 制約辞書を作成
    constraints_dict = {
        "nutrition_constraints": nutrition_constraints,
        "food_constraints": food_constraints,
        "calculation_info": calculation_info
    }
    
    return foods, constraints_dict

def load_foods(filepath: str) -> pd.DataFrame:
    """食品データを読み込む（後方互換性のため）"""
    return pd.read_csv(filepath)

def load_constraints(filepath: str) -> Dict[str, Any]:
    """制約条件を読み込む（後方互換性のため）"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def load_data(foods_path: str, constraints_path: str = None) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    データを読み込む（後方互換性 + ハイブリッド対応）
    
    constraints_pathがNoneの場合、ハイブリッド形式を試行
    """
    
    # 食品データを読み込み
    foods = load_foods(foods_path)
    
    if constraints_path and os.path.exists(constraints_path):
        # 従来のJSON形式
        constraints = load_constraints(constraints_path)
        print(f"📊 従来形式で読み込み: 食品{len(foods)}種類")
    else:
        # ハイブリッド形式を試行
        base_dir = os.path.dirname(os.path.dirname(foods_path))
        try:
            _, constraints = load_hybrid_data(base_dir)
            print(f"📊 ハイブリッド形式で読み込み: 食品{len(foods)}種類")
        except Exception as e:
            print(f"⚠️  ハイブリッド形式の読み込みに失敗: {e}")
            constraints = {"nutrition_constraints": {}, "food_constraints": {}}
    
    return foods, constraints