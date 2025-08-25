#!/usr/bin/env python3
"""
栄養制約マッピングモジュール
step1で生成されたnutrition_constraints.csvの34栄養素に対応する
MEXT食品成分表の列データを抽出・変換する
"""

import pandas as pd
import os
from typing import Dict, List, Any

class NutritionConstraintMapper:
    def __init__(self):
        """mapping.mdに基づく栄養素マッピング"""
        # step1制約ID → MEXT成分表列名のマッピング
        self.constraint_to_mext_mapping = {
            # エネルギー・主要栄養素
            'energy_kcal': 'energy_kcal',  # 直接使用
            'protein': 'protein',  # 直接使用
            'fat': 'fat',  # 直接使用
            'carb_available': 'carb_available',  # 直接使用（利用可能炭水化物）
            'fiber_total': 'fiber_total',  # 直接使用
            
            # ビタミン
            'retinol_activity_equiv': 'retinol_activity_equiv',  # 【最重要】レチノール活性当量
            'vitamin_d': 'vitamin_d',  # 直接使用
            'alpha_tocopherol': 'alpha_tocopherol',  # 【重要】α-トコフェロールのみ
            'vitamin_k': 'vitamin_k',  # 直接使用
            'thiamin': 'thiamin',  # ビタミンB₁
            'riboflavin': 'riboflavin',  # ビタミンB₂
            'niacin': 'niacin',  # 【修正】ナイアシン（計算前の基本値）
            'vitamin_b6': 'vitamin_b6',  # 直接使用
            'vitamin_b12': 'vitamin_b12',  # 直接使用
            'folate': 'folate',  # 葉酸
            'pantothenic_acid': 'pantothenic_acid',  # パントテン酸
            'biotin': 'biotin',  # ビオチン
            'vitamin_c': 'vitamin_c',  # 直接使用
            
            # ミネラル
            'potassium': 'potassium',  # カリウム
            'calcium': 'calcium',  # カルシウム
            'magnesium': 'magnesium',  # マグネシウム
            'phosphorus': 'phosphorus',  # リン
            'iron': 'iron',  # 鉄
            'zinc': 'zinc',  # 亜鉛
            'copper': 'copper',  # 銅
            'manganese': 'manganese',  # マンガン
            'iodine': 'iodine',  # ヨウ素
            'selenium': 'selenium',  # セレン
            'chromium': 'chromium',  # クロム
            'molybdenum': 'molybdenum',  # モリブデン
            'salt_equiv': 'salt_equiv',  # 食塩相当量（ナトリウム）
            
            # 脂肪酸（統合データから取得）
            'n3_fatty_acid': 'n3_fatty_acid',  # 脂肪酸統合モジュールから
            'n6_fatty_acid': 'n6_fatty_acid',  # 脂肪酸統合モジュールから
            'saturated_fat': 'saturated_fat',  # 飽和脂肪酸
        }
        
        self.load_constraint_list()
    
    def load_constraint_list(self):
        """nutrition_constraints.csvから全制約リストを読み込み（enabledに関係なく全項目）"""
        try:
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            constraints_path = os.path.join(base_dir, 'data', 'input', 'nutrition_constraints.csv')
            
            if os.path.exists(constraints_path):
                df = pd.read_csv(constraints_path)
                # enabledに関係なく全制約を取得（foods.csvには全34項目を記載）
                self.active_nutrient_ids = df['nutrient_id'].tolist()
                enabled_count = len(df[df['enabled'] == True]) if 'enabled' in df.columns else len(df)
                print(f"全栄養制約: {len(self.active_nutrient_ids)}項目（有効: {enabled_count}項目）")
            else:
                print("nutrition_constraints.csvが見つかりません")
                self.active_nutrient_ids = []
                
        except Exception as e:
            print(f"制約リスト読み込みエラー: {e}")
            self.active_nutrient_ids = []
    
    def extract_mapped_nutrition_data(self, full_nutrition_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        全栄養素データから34制約に対応するデータのみを抽出
        
        Args:
            full_nutrition_data: 全栄養素データ（53項目）
            
        Returns:
            制約対応栄養素データ（34項目 + 価格 + 制約）
        """
        mapped_data = {'food_name': full_nutrition_data['food_name']}
        
        # 有効な栄養制約に対応するデータのみを抽出
        for constraint_id in self.active_nutrient_ids:
            mext_column = self.constraint_to_mext_mapping.get(constraint_id)
            
            if mext_column and mext_column in full_nutrition_data:
                mapped_data[constraint_id] = full_nutrition_data[mext_column]
            else:
                # 対応するMEXTデータがない場合は0を設定
                mapped_data[constraint_id] = 0.0
                # デバッグ用：脂肪酸以外で実際に不足している項目のみ警告
                if not hasattr(self, '_warned_mappings'):
                    self._warned_mappings = set()
                if (constraint_id not in self._warned_mappings and 
                    constraint_id not in ['n3_fatty_acid', 'n6_fatty_acid', 'saturated_fat'] and
                    mext_column is not None):  # マッピング定義があるのにデータがない場合のみ
                    print(f"マッピング不可: {constraint_id} -> {mext_column} (データに存在しない)")
                    self._warned_mappings.add(constraint_id)
        
        return mapped_data
    
    def get_constraint_column_order(self) -> List[str]:
        """CSVの列順序を取得（名前 + 日本語栄養素列順 + 価格・制約情報）"""
        # nutrition_complete.csvと同じ列順序を使用
        try:
            import pandas as pd
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            complete_csv_path = os.path.join(base_dir, 'data', 'input', 'nutrition_complete.csv')
            complete_df = pd.read_csv(complete_csv_path, nrows=1)
            nutrition_columns = complete_df.columns.tolist()
            columns = nutrition_columns + ['price', 'unit', 'min_units', 'max_units', 'enabled']
            return columns
        except Exception:
            # フォールバック: 旧形式
            columns = ['名前'] + self.active_nutrient_ids + ['price', 'unit', 'min_units', 'max_units', 'enabled']
            return columns

if __name__ == "__main__":
    # テスト実行
    mapper = NutritionConstraintMapper()
    print("制約マッピング:", len(mapper.active_nutrient_ids), "項目")
    print("列順序:", mapper.get_constraint_column_order()[:10])  # 最初の10列