#!/usr/bin/env python3
"""
栄養素必要量計算ライブラリ
体重と基本情報を基に科学的根拠のある栄養制約を算出
"""

import pandas as pd
import os
from typing import Dict, Tuple, Any

class NutritionCalculator:
    def __init__(self):
        """栄養素計算クラスの初期化"""
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.load_nutrition_standards()
    
    def load_nutrition_standards(self):
        """栄養基準データを読み込み"""
        try:
            csv_path = os.path.join(self.base_dir, 'docs', '18~29_men.csv')
            # すべての列を文字列として読み込み、後で数値変換
            self.standards = pd.read_csv(csv_path, encoding='utf-8', on_bad_lines='skip', dtype=str)
            print(f"栄養基準データを読み込みました: {len(self.standards)}項目")
        except Exception as e:
            print(f"栄養基準データの読み込みエラー: {e}")
            self.standards = pd.DataFrame()
    
    def calculate_bmr_and_energy(self, weight: float, activity_level: str = "ふつう") -> Tuple[float, float]:
        """基礎代謝量と推定エネルギー必要量を計算"""
        
        # 18-29歳男性の基礎代謝基準値
        BMR_STANDARD = 23.7  # kcal/kg/日
        
        # 身体活動レベル係数
        PAL_VALUES = {
            "低い": 1.50,      # 座位中心の生活
            "ふつう": 1.75,    # 座位中心だが歩行や立位での活動も含む
            "高い": 2.00       # 立位での活動が多い、またはスポーツなど
        }
        
        # 基礎代謝量の計算
        bmr = BMR_STANDARD * weight
        
        # 推定エネルギー必要量の計算
        pal = PAL_VALUES.get(activity_level, 1.75)
        energy_needs = bmr * pal
        
        return bmr, energy_needs
    
    def calculate_energy_dependent_nutrients(self, energy_kcal: float) -> Dict[str, Dict[str, float]]:
        """エネルギー依存栄養素を計算"""
        
        energy_dependent = {
            # PFC バランス栄養素
            "protein": {
                "min": energy_kcal * 0.13 / 4,  # 13%エネルギー ÷ 4kcal/g
                "max": energy_kcal * 0.20 / 4,  # 20%エネルギー ÷ 4kcal/g
                "unit": "g"
            },
            "fat": {
                "min": energy_kcal * 0.20 / 9,  # 20%エネルギー ÷ 9kcal/g
                "max": energy_kcal * 0.30 / 9,  # 30%エネルギー ÷ 9kcal/g
                "unit": "g"
            },
            "carb_available": {
                "min": energy_kcal * 0.50 / 4,  # 50%エネルギー ÷ 4kcal/g
                "max": energy_kcal * 0.65 / 4,  # 65%エネルギー ÷ 4kcal/g
                "unit": "g"
            },
            "saturated_fat": {
                "max": energy_kcal * 0.07 / 9,  # 7%エネルギー上限 ÷ 9kcal/g
                "unit": "g"
            },
            
            # エネルギー代謝関連ビタミン
            "thiamin": {  # ビタミンB1
                "min": energy_kcal * 0.54 / 1000,  # 0.54mg/1000kcal
                "unit": "mg"
            },
            "riboflavin": {  # ビタミンB2
                "min": energy_kcal * 0.62 / 1000,  # 0.62mg/1000kcal  
                "unit": "mg"
            },
            "niacin": {  # ナイアシン
                "min": energy_kcal * 5.8 / 1000,   # 5.8mgNE/1000kcal
                "unit": "mg"
            },
            "pantothenic_acid": {  # パントテン酸
                "min": energy_kcal * 1.9 / 1000,   # 1.9mg/1000kcal
                "unit": "mg"
            }
        }
        
        return energy_dependent
    
    def get_fixed_nutrients_from_csv(self) -> Dict[str, Dict[str, Any]]:
        """CSVから固定栄養素基準を取得"""
        fixed_nutrients = {}
        
        if self.standards.empty:
            return fixed_nutrients
        
        # CSVデータを処理
        for idx, row in self.standards.iterrows():
            try:
                # 確実に文字列に変換
                raw_nutrient = row['栄養素']
                if pd.isna(raw_nutrient):
                    continue  # NaNの場合はスキップ
                nutrient_name = str(raw_nutrient).strip()
                
                # 栄養素名を英語名にマッピング
                nutrient_mapping = {
                'ビタミンA': 'retinol_activity_equiv',
                'ビタミンD': 'vitamin_d', 
                'ビタミンE': 'alpha_tocopherol',
                'ビタミンK': 'vitamin_k',
                'ビタミンB₆': 'vitamin_b6',
                'ビタミンB₁₂': 'vitamin_b12',
                '葉酸': 'folate',
                'ビオチン': 'biotin',
                'ビタミンC': 'vitamin_c',
                'ナトリウム (食塩相当量)': 'salt_equiv',
                'カリウム': 'potassium',
                'カルシウム': 'calcium',
                'マグネシウム': 'magnesium',
                'リン': 'phosphorus',
                '鉄': 'iron',
                '亜鉛': 'zinc',
                '銅': 'copper',
                'マンガン': 'manganese',
                'ヨウ素': 'iodine',
                'セレン': 'selenium',
                'クロム': 'chromium',
                'モリブデン': 'molybdenum',
                '食物繊維': 'fiber_total',
                'n-6系脂肪酸': 'n6_fatty_acid',
                'n-3系脂肪酸': 'n3_fatty_acid'
                }
                
                en_name = nutrient_mapping.get(nutrient_name)
                if not en_name:
                    continue
                
                nutrient_data = {}
                
                # 各基準値を処理（全て文字列化）
                ear = str(row.get('推定平均必要量(EAR)', '')).strip() if pd.notna(row.get('推定平均必要量(EAR)', '')) else ''
                rda = str(row.get('推奨量(RDA)', '')).strip() if pd.notna(row.get('推奨量(RDA)', '')) else ''
                ai = str(row.get('目安量(AI)', '')).strip() if pd.notna(row.get('目安量(AI)', '')) else ''
                ul = str(row.get('耐容上限量(UL)', '')).strip() if pd.notna(row.get('耐容上限量(UL)', '')) else ''
                dg = str(row.get('目標量(DG)', '')).strip() if pd.notna(row.get('目標量(DG)', '')) else ''
                unit = str(row.get('単位', '')).strip() if pd.notna(row.get('単位', '')) else ''
                
                # 最小値を設定（EAR > RDA > AI の優先順位）
                if ear and ear not in ['', 'nan']:
                    ear_val = ear.replace(' 以上', '').strip()
                    if ear_val and ear_val != 'nan':
                        nutrient_data['min'] = float(ear_val)
                elif rda and rda not in ['', 'nan']:
                    rda_val = rda.replace(' 以上', '').strip()
                    if rda_val and rda_val != 'nan':
                        nutrient_data['min'] = float(rda_val)
                elif ai and ai not in ['', 'nan']:
                    ai_val = ai.replace(' 以上', '').strip()
                    if ai_val and ai_val != 'nan':
                        nutrient_data['min'] = float(ai_val)
                
                # 最大値を設定（UL）- 葉酸とマグネシウムはサプリメント用制限のため除外
                if ul and ul not in ['', 'nan'] and en_name not in ['folate', 'magnesium']:
                    ul_val = ul.replace(' 未満', '').strip()
                    if ul_val and ul_val != 'nan':
                        nutrient_data['max'] = float(ul_val)
                
                # 目標量がある場合の処理
                if dg and dg not in ['', 'nan']:
                    dg_str = dg.strip()
                    if '以上' in dg_str:
                        dg_val = dg_str.replace(' 以上', '').strip()
                        if dg_val and dg_val != 'nan':
                            nutrient_data['min'] = float(dg_val)
                    elif '未満' in dg_str:
                        # 葉酸とマグネシウムは目標量の上限も除外
                        if en_name not in ['folate', 'magnesium']:
                            dg_val = dg_str.replace(' 未満', '').strip()
                            if dg_val and dg_val != 'nan':
                                nutrient_data['max'] = float(dg_val)
                    else:
                        # 範囲指定がない場合は目標値として設定
                        if dg_str and dg_str != 'nan':
                            nutrient_data['target'] = float(dg_str)
                
                # 単位を設定
                unit_mapping = {
                    'g/日': 'g',
                    'mg/日': 'mg', 
                    'µg/日': 'μg',
                    'µgRAE/日': 'μgRAE',
                    'kcal/日': 'kcal'
                }
                nutrient_data['unit'] = unit_mapping.get(unit, unit.replace('/日', ''))
                
                if nutrient_data:  # 何らかのデータがある場合のみ追加
                    fixed_nutrients[en_name] = nutrient_data
                
            except Exception as e:
                continue
        
        return fixed_nutrients
    
    def calculate_all_constraints(self, weight: float, activity_level: str = "ふつう") -> Dict[str, Any]:
        """体重と活動レベルから全制約を計算"""
        
        # エネルギー必要量を計算
        bmr, energy_needs = self.calculate_bmr_and_energy(weight, activity_level)
        
        # エネルギー依存栄養素を計算
        energy_dependent = self.calculate_energy_dependent_nutrients(energy_needs)
        
        # 固定栄養素をCSVから取得
        fixed_nutrients = self.get_fixed_nutrients_from_csv()
        
        # 制約辞書を作成
        constraints = {
            "energy_kcal": {
                "min": round(energy_needs * 0.9),  # -10%
                "max": round(energy_needs * 1.1),  # +10%
                "unit": "kcal"
            }
        }
        
        # エネルギー依存栄養素を追加
        for nutrient, values in energy_dependent.items():
            constraint = {}
            if 'min' in values:
                constraint['min'] = round(values['min'], 2)
            if 'max' in values:
                constraint['max'] = round(values['max'], 2)
            constraint['unit'] = values['unit']
            constraints[nutrient] = constraint
        
        # 固定栄養素を追加
        constraints.update(fixed_nutrients)
        
        return {
            "calculation_params": {
                "weight": weight,
                "activity_level": activity_level,
                "bmr": round(bmr, 1),
                "energy_needs": round(energy_needs, 1)
            },
            "nutrition_constraints": constraints
        }