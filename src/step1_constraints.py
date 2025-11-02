#!/usr/bin/env python3
"""
Step1: ハイブリッド形式対応制約条件設定
体重と活動レベルから日本人の食事摂取基準に基づいた栄養制約を自動計算
結果をCSV + JSON のハイブリッド形式で保存
"""

import json
import os
import sys
from datetime import datetime
from typing import Dict, Any
import argparse

from core.nutrients_calculator import UserProfile, NutrientsCalculator

def main(args: argparse.Namespace):
    """メイン処理"""
    print("=== Step1: 制約条件設定 ===")

    setting_name = args.setting_name
    output_dir = f"/app/data/step1_constraints/{setting_name}/"
    user_profile_path = os.path.join(output_dir, "user_profile.json")
    nutrient_constraints_path = os.path.join(output_dir, "nutrient_constraints.csv")
    if os.path.exists(user_profile_path) and args.use_profile:
        print("設定ファイルが見つかりました。")
        with open(user_profile_path, "r") as f:
            profile_data = json.load(f)
        user_profile = UserProfile(
            sex_code=profile_data["sex_code"],
            weight=profile_data["weight"],
            height=profile_data["height"],
            age=profile_data["age"],
            activity_level=profile_data["activity_level"],
            life_code=profile_data["life_code"]
        )
    else:
        print("ユーザープロファイルを新規作成します。")

    
        print("性別コードを入力してください (M/F):")
        while True:
            sex_code = input().strip().upper()
            if sex_code not in ['M', 'F']:
                print("無効な性別コードです。MまたはFを入力してください。")
                continue
            break

        print("体重を入力してください (kg):")
        while True:
            try:
                weight = float(input().strip())
                if weight <= 0:
                    raise ValueError
                break
            except ValueError:
                print("無効な体重です。正の数を入力してください。")

        print("身長を入力してください (cm):")
        while True:
            try:
                height = float(input().strip())
                if height <= 0:
                    raise ValueError
                break
            except ValueError:
                print("無効な身長です。正の数を入力してください。")

        print("年齢を入力してください (歳):")
        while True:
            try:
                age = float(input().strip())
                if age <= 0:
                    raise ValueError
                break
            except ValueError:
                print("無効な年齢です。正の数を入力してください。")
        
        print("活動レベルを入力してください (例: 1.2, 1.55, 1.75):")
        while True:
            try:
                activity_level = float(input().strip())
                if activity_level <= 0:
                    raise ValueError
                break
            except ValueError:
                print("無効な活動レベルです。正の数を入力してください。")

        print("ライフステージコードを選択してください")
        print("1: 標準")
        print("2: 妊娠初期")
        print("3: 妊娠中期・後期")
        print("4: 授乳中")
        while True:
            life_stage_input = int(input().strip())
            if life_stage_input == 1:
                life_code = "general"
                break
            elif life_stage_input == 2:
                life_code = "pregnant_early"
                break
            elif life_stage_input == 3:
                life_code = "pregnant_mid_late"
                break
            elif life_stage_input == 4:
                life_code = "lactating"
                break
            else:
                print("無効な選択です。1から4の数字を入力してください。")

        user_profile = UserProfile(sex_code, weight, height, age, activity_level, life_code)

    calculator = NutrientsCalculator(user_profile)
    os.makedirs(output_dir, exist_ok=True)
    calculator.save_nutrient_values_to_csv(nutrient_constraints_path)
    calculator.save_user_profile_to_json(user_profile_path)
    print(f"制約条件が保存されました: {nutrient_constraints_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--setting_name", type=str, required=True, help="設定名")
    parser.add_argument("-u", "--use_profile", action="store_true", help="ファイルから設定を読み込む場合に指定")
    args = parser.parse_args()

    main(args)