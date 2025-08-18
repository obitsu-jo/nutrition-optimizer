#!/usr/bin/env python3
"""
食品データ生成ヘルパー
ユーザーが食品名と価格を入力すると、食品成分表から栄養データを自動取得してfoods.csvを生成
"""

import pandas as pd
import os
import json
from typing import Dict, List, Any
import sys
import os
# パスを追加してモジュールを読み込み
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from nutrition_mapping import NUTRITION_MAPPING, get_column_name
from fatty_acid_integrator import FattyAcidIntegrator
from nutrition_constraint_mapper import NutritionConstraintMapper

class FoodCompositionDatabase:
    def __init__(self):
        # プロジェクトルートディレクトリを取得 (/app/src/core -> /app)
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.excel_path = os.path.join(self.base_dir, 'data', 'raw', '20230428-mxt_kagsei-mext_00001_012.xlsx')
        self.food_data = None
        self.fatty_acid_integrator = FattyAcidIntegrator()
        self.constraint_mapper = NutritionConstraintMapper()
        self.load_composition_data()
    
    def load_composition_data(self):
        """食品成分表からすべての栄養素データを読み込む"""
        try:
            # 表全体シートを使用
            df = pd.read_excel(self.excel_path, sheet_name='表全体', header=None)
            
            # データは11行目から開始
            data_start_row = 11
            data_df = df.iloc[data_start_row:].copy()
            
            # 全栄養素データを読み込み
            nutrition_data = {}
            for col_index, (jp_name, en_name, unit) in NUTRITION_MAPPING.items():
                if col_index < len(data_df.columns):
                    nutrition_data[en_name] = data_df.iloc[:, col_index]
            
            self.food_data = pd.DataFrame(nutrition_data)
            
            # 食品名でNaNを除去
            self.food_data = self.food_data.dropna(subset=['food_name'])
            self.food_data['food_name'] = self.food_data['food_name'].astype(str).str.strip()
            
            # 数値データをクリーニング
            def clean_numeric(val):
                if pd.isna(val):
                    return None
                val_str = str(val).strip()
                # 特殊記号を処理
                if val_str in ['*', '-', '(0)', 'Tr', 'tr']:
                    return 0.0
                # 括弧を除去 "(11.3)" -> "11.3"
                val_str = val_str.replace('(', '').replace(')', '')
                try:
                    return float(val_str)
                except:
                    return None
            
            # 数値列のクリーニング（食品名以外）
            for col in self.food_data.columns:
                if col != 'food_name':
                    self.food_data[col] = self.food_data[col].apply(clean_numeric)
            
            # 基本的な栄養素（エネルギー、たんぱく質）が有効なデータのみ残す
            self.food_data = self.food_data[
                (self.food_data['energy_kcal'].notna()) & 
                (self.food_data['protein'].notna())
            ]
            
            print(f"食品成分データベース: {len(self.food_data)}件の食品データを読み込みました")
            print(f"栄養素項目数: {len([c for c in self.food_data.columns if c != 'food_name'])}項目")
            
        except Exception as e:
            print(f"食品成分表の読み込みエラー: {e}")
            self.food_data = pd.DataFrame()
    
    def search_food(self, food_name: str) -> List[Dict[str, Any]]:
        """食品名で検索（部分一致）"""
        if self.food_data is None or self.food_data.empty:
            return []
        
        # 部分一致で検索
        matches = self.food_data[
            self.food_data['food_name'].str.contains(food_name, na=False, case=False)
        ]
        
        results = []
        for _, row in matches.iterrows():
            try:
                # 全栄養素データを辞書として格納
                nutrition_data = {'food_name': row['food_name']}
                
                # 数値データを適切に丸める
                for col in self.food_data.columns:
                    if col != 'food_name' and pd.notna(row[col]):
                        val = row[col]
                        if val >= 100:  # 大きな値は小数点1桁
                            nutrition_data[col] = round(val, 1)
                        elif val >= 1:  # 中程度の値は小数点2桁
                            nutrition_data[col] = round(val, 2)
                        else:  # 小さな値は小数点3桁
                            nutrition_data[col] = round(val, 3)
                
                # 脂肪酸データを統合
                n3_fatty_acid, n6_fatty_acid = self.fatty_acid_integrator.calculate_fatty_acids(row['food_name'])
                nutrition_data['n3_fatty_acid'] = round(n3_fatty_acid, 3) if n3_fatty_acid is not None else 0.0
                nutrition_data['n6_fatty_acid'] = round(n6_fatty_acid, 3) if n6_fatty_acid is not None else 0.0
                
                # 34栄養制約に対応するデータのみを抽出
                mapped_nutrition_data = self.constraint_mapper.extract_mapped_nutrition_data(nutrition_data)
                
                results.append(mapped_nutrition_data)
            except Exception:
                continue
        
        return results

def interactive_food_input():
    """対話式で食品データを作成"""
    db = FoodCompositionDatabase()
    
    if db.food_data is None or db.food_data.empty:
        print("食品成分データベースの読み込みに失敗しました。")
        return
    
    foods_list = []
    
    print("=== 食品データ作成ヘルパー ===")
    print("食品名を入力すると、栄養データを自動で検索します。")
    print("'quit'で終了します。\n")
    
    while True:
        food_name_input = input("食品名を入力してください: ").strip()
        if food_name_input.lower() == 'quit':
            break
        
        if not food_name_input:
            continue
        
        # 食品を検索
        matches = db.search_food(food_name_input)
        
        if not matches:
            print(f"'{food_name_input}'に一致する食品が見つかりませんでした。")
            continue
        
        # 検索結果を表示
        print(f"\n'{food_name_input}'の検索結果:")
        for i, match in enumerate(matches[:10]):  # 上位10件まで表示
            calories = match.get('energy_kcal', 'N/A')
            protein = match.get('protein', 'N/A')
            fat = match.get('fat', 'N/A')
            carb = match.get('carb_available', 'N/A')
            print(f"{i+1}: {match['food_name']}")
            print(f"    エネルギー: {calories} kcal, たんぱく質: {protein} g, 脂質: {fat} g, 炭水化物: {carb} g")
        
        if len(matches) > 10:
            print(f"... 他{len(matches) - 10}件")
        
        # 選択
        try:
            choice = int(input("番号を選択してください (0でスキップ): "))
            if choice == 0:
                continue
            if 1 <= choice <= len(matches):
                selected = matches[choice - 1]
                
                # 価格を入力
                while True:
                    try:
                        price = float(input("100gあたりの価格（円）を入力してください: "))
                        break
                    except ValueError:
                        print("有効な数値を入力してください。")
                
                # リストに追加（全栄養素データ + 価格）
                food_entry = selected.copy()
                food_entry['price_per_100g'] = price
                foods_list.append(food_entry)
                print(f"'{selected['food_name']}'を追加しました。\\n")
            else:
                print("無効な番号です。")
        except ValueError:
            print("無効な入力です。")
    
    # CSVファイルを生成
    if foods_list:
        output_path = os.path.join(db.base_dir, 'data', 'input', 'foods.csv')
        df = pd.DataFrame(foods_list)
        df.to_csv(output_path, index=False, encoding='utf-8')
        print(f"\\n{len(foods_list)}件の食品データを{output_path}に保存しました。")
        print("\\n生成されたデータ:")
        print(df.to_string(index=False))
    else:
        print("食品データが追加されませんでした。")

if __name__ == "__main__":
    interactive_food_input()