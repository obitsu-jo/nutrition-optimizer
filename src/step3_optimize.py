import argparse
import json
import os
import polars as pl
from core.optimizer import *

def load_settings(args: argparse.Namespace):
    setting_name = args.setting_name
    output_dir = f"/app/data/step3_optimize/{setting_name}/"
    user_profile_path = os.path.join(output_dir, "user_profile.json")
    if os.path.exists(user_profile_path) and args.use_profile:
        print("設定ファイルが見つかりました。")
        with open(user_profile_path, "r") as f:
            profile_data = json.load(f)
            setting_name_1 = profile_data["setting_name_1"]
            setting_name_2 = profile_data["setting_name_2"]
    else:
        print("設定ファイルが見つかりません。コマンドライン引数から設定名を取得します。")
        if args.setting_name_1 is None or args.setting_name_2 is None:
            raise ValueError("設定名1および設定名2をコマンドライン引数で指定してください。")
        setting_name_1 = args.setting_name_1
        setting_name_2 = args.setting_name_2
        profile_data = {
            "setting_name_1": setting_name_1,
            "setting_name_2": setting_name_2
        }
        os.makedirs(output_dir, exist_ok=True)
        with open(user_profile_path, "w") as f:
            json.dump(profile_data, f, indent=4)
        print(f"設定ファイルを保存しました: {user_profile_path}")
    return setting_name, setting_name_1, setting_name_2

def load_data(setting_name_1: str, setting_name_2: str):
    setting_1_path = f"/app/data/step1_constraints/{setting_name_1}/nutrient_constraints.csv"
    setting_2_path = f"/app/data/step2_foods/{setting_name_2}/food_nutrient_data.csv"
    if not os.path.exists(setting_1_path):
        raise FileNotFoundError(f"設定1の制約条件ファイルが見つかりません: {setting_1_path}")
    if not os.path.exists(setting_2_path):
        raise FileNotFoundError(f"設定2の食品データファイルが見つかりません: {setting_2_path}")
    df_constraints = pl.read_csv(setting_1_path)
    df_foods = pl.read_csv(setting_2_path)
    return df_constraints, df_foods

def main(args: argparse.Namespace):
    setting_name, setting_name_1, setting_name_2 = load_settings(args)
    df_constraints, df_foods = load_data(setting_name_1, setting_name_2)

    # 基本となる出力パスを定義
    base_output_path = f"/app/data/step3_optimize/{setting_name}/results.csv"

    # 新しいラッパー関数を呼び出す
    prob, status = find_optimal_solution_iteratively(
        df_foods,
        df_constraints,
        base_output_path
    )

    # 最終的なステータスを表示
    if status == pulp.LpStatusOptimal:
        print("\n最適化プロセスが正常に完了しました。")
    else:
        print("\n最適化プロセスは実行可能な解を見つけることができませんでした。")

    


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--setting_name", type=str, required=True, help="設定名")
    parser.add_argument("-s1", "--setting_name_1", type=str, required=False, help="設定名1")
    parser.add_argument("-s2", "--setting_name_2", type=str, required=False, help="設定名2")
    parser.add_argument("-u", "--use_profile", action="store_true", help="ファイルから設定を読み込む場合に指定")
    args = parser.parse_args()

    main(args)
