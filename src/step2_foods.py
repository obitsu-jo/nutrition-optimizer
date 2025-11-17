import argparse
import polars as pl
import os

def load_food_nutrient_data():
    TEMPLATE_FOOD_NUTRIENT_DATA_PATH = "/app/resources/step2/template/food_nutrient_data.csv"
    CUSTOM_FOOD_NUTRIENT_DATA_DIR = "/app/resources/step2/custom/"
    df_input = pl.read_csv(TEMPLATE_FOOD_NUTRIENT_DATA_PATH)
    # 食品名とunitはstr、それ以外はfloat64にキャスト
    df_input = df_input.with_columns(
        pl.col("food_name").cast(pl.Utf8),
        pl.col("unit").cast(pl.Utf8)
    )
    for col_name in df_input.columns:
        if col_name not in ["food_name", "unit"]:
            df_input = df_input.with_columns(
                pl.col(col_name).cast(pl.Float64, strict=False)
            )
    
    n_custom_data = len(os.listdir(CUSTOM_FOOD_NUTRIENT_DATA_DIR))
    # 食品名が重複する場合、カスタムデータを優先
    if n_custom_data > 0:
        for filename in os.listdir(CUSTOM_FOOD_NUTRIENT_DATA_DIR):
            if filename.endswith(".csv"):
                custom_data_path = os.path.join(CUSTOM_FOOD_NUTRIENT_DATA_DIR, filename)
                df_custom = pl.read_csv(custom_data_path)
                df_custom = df_custom.with_columns(
                    pl.col("food_name").cast(pl.Utf8),
                    pl.col("unit").cast(pl.Utf8)
                )
                for col_name in df_custom.columns:
                    if col_name not in ["food_name", "unit"]:
                        df_custom = df_custom.with_columns(
                            pl.col(col_name).cast(pl.Float64, strict=False)
                        )
                df_input = df_input.filter(~pl.col("food_name").is_in(df_custom["food_name"]))
                df_input = pl.concat([df_input, df_custom])
    return df_input

def main(args: argparse.Namespace):

    df_input = load_food_nutrient_data()

    output_path = f"/app/data/step2_foods/{args.setting_name}/food_nutrient_data.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path):
        df_output = pl.read_csv(output_path, schema=df_input.schema)
    else:
        df_output = pl.DataFrame(schema=df_input.schema)
    

    while True:
        print("\n食品名を入力してください (終了するには 'exit' と入力):")
        food_name = input().strip()
        if food_name.lower() == 'exit':
            if df_output.is_empty():
                print("食品が一つも追加されていません。終了します。")
            else:
                df_output.write_csv(output_path)
                print(f"選択した食品データが保存されました: {output_path}")
            break

        # まず完全一致で検索
        df_food = df_input.filter(pl.col("food_name") == food_name)
        
        # 完全一致しなかった場合、部分一致検索を行う
        if df_food.is_empty():
            print(f"食品名 '{food_name}' は存在しません。部分一致で検索します...")
            
            # 部分一致する候補を検索
            df_search_results = df_input.filter(pl.col("food_name").str.contains(food_name))
            
            if df_search_results.is_empty():
                print(f"'{food_name}' を含む食品は見つかりませんでした。")
                continue # 次の入力を待つ
            
            # 候補を番号付きで表示
            print("----------------------------------------")
            food_name_list = df_search_results["food_name"].to_list()
            for i, name in enumerate(food_name_list, 1):
                print(f"{i}: {name}")
            print("----------------------------------------")
            
            # ユーザーに番号を選ばせる
            while True:
                choice_input = input("追加する食品の番号を入力してください (キャンセルは 'c'): ").strip().lower()
                
                if choice_input == 'c':
                    df_food = None # キャンセルされたことを示す
                    break
                
                try:
                    choice_index = int(choice_input) - 1
                    if 0 <= choice_index < len(food_name_list):
                        selected_name = food_name_list[choice_index]
                        df_food = df_input.filter(pl.col("food_name") == selected_name)
                        print(f"'{selected_name}' を選択しました。")
                        break
                    else:
                        print(f"無効な番号です。1から{len(food_name_list)}の間で入力してください。")
                except ValueError:
                    print("無効な入力です。番号または 'c' を入力してください。")

        # キャンセルされた場合は次のループへ
        if df_food is None or df_food.is_empty():
            print("キャンセルされました。")
            continue
        
        df_food_completed = df_food.clone() # 元のデータを変更しないようにコピー
        
        for col_name in df_food_completed.columns:
            # food_nameはチェック不要
            if col_name == "food_name":
                continue

            if col_name == "min" or col_name == "max":
                continue

            # Polarsでは .is_null() で欠損値を判定
            if df_food_completed.select(pl.col(col_name).is_null()).item():
                
                col_type = df_food_completed.schema[col_name] # 列のデータ型を取得

                while True:
                    user_input = input(f"-> '{col_name}' の値を入力してください: ").strip()
                    
                    # データ型に応じて変換を試みる
                    # 食品名やunitは文字列型として扱う
                    if col_type == pl.Utf8:
                        value = user_input
                    else:
                        try:
                            value = float(user_input)
                        except ValueError:
                            print(f"無効な入力です。'{col_name}' には数値を入力してください。")
                            continue
                    # 入力が成功したらDataFrameを更新してループを抜ける
                    df_food_completed = df_food_completed.with_columns(
                        pl.lit(value).cast(col_type).alias(col_name)
                    )
                    break
        
        # 完成したデータを元の変数に戻す
        df_food = df_food_completed

        # 選択された食品名を取得
        selected_food_name = df_food["food_name"][0]
        
        # 既に追加されているかチェック
        if df_output.filter(pl.col("food_name") == selected_food_name).is_empty() is False:
            print(f"食品名 '{selected_food_name}' は既に追加されています。上書きしますか？ (y/n):")
            while True:
                choice = input().strip().lower()
                if choice == 'y':
                    df_output = df_output.filter(pl.col("food_name") != selected_food_name)
                    df_output = pl.concat([df_output, df_food])
                    print(f"食品名 '{selected_food_name}' を上書きしました。")
                    break
                elif choice == 'n':
                    print("上書きをキャンセルしました。")
                    break
                else:
                    print("無効な選択です。yまたはnを入力してください。")
        else:
            df_output = pl.concat([df_output, df_food])
            print(f"食品名 '{selected_food_name}' を追加しました。")



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--setting_name", type=str, required=True, help="設定名")

    args = parser.parse_args()
    main(args)