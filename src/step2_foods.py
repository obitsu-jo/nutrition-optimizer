#!/usr/bin/env python3
"""
Step2: 食品情報設定（既存ファイル追加・編集対応版）
既存のfoods.csvを読み込んで食品を追加・編集・削除する
"""

import pandas as pd
import os
import sys
from core.nutrition_mapping import NUTRITION_MAPPING

# パスを追加
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'core'))

from food_helper import FoodCompositionDatabase

def load_existing_foods():
    """既存のfoods.csvを読み込み"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    foods_path = os.path.join(base_dir, 'data', 'input', 'foods.csv')
    
    if os.path.exists(foods_path):
        try:
            existing_df = pd.read_csv(foods_path)
            foods_list = existing_df.to_dict('records')
            print(f"読み込み: 既存のfoods.csvを読み込みました: {len(foods_list)}品目")
            return foods_list, foods_path
        except Exception as e:
            print(f"WARNING: 既存ファイル読み込みエラー: {e}")
            return [], foods_path
    else:
        print(">>> 新規foods.csvを作成します")
        return [], foods_path

def show_existing_foods(foods_list):
    """既存食品リストを表示"""
    if not foods_list:
        print("現在、登録済み食品はありません。")
        return
    
    print(f"\n=== 登録済み食品 ({len(foods_list)}品目) ===")
    for i, food in enumerate(foods_list, 1):
        name = food.get('名前', 'N/A')
        price = food.get('price', 'N/A')
        unit = food.get('unit', 'N/A')
        min_units = food.get('min_units', '')
        max_units = food.get('max_units', '')
        enabled = food.get('enabled', 'TRUE')
        status = "DISABLED" if enabled != 'TRUE' else "ENABLED"
        range_display = f"{min_units or '0'}-{max_units or '無制限'}単位"
        print(f"  {i:2d}. [{status}] {name}")
        print(f"      価格: {price}円/{unit}, 制限: {range_display}")

def add_new_food(foods_list, db):
    """新しい食品を追加"""
    food_name_input = input("\n追加する食品名を入力してください (back=戻る): ").strip()
    if food_name_input.lower() in ['back', '']:
        return False
    
    # 食品を検索
    matches = db.search_food(food_name_input)
    
    if not matches:
        print(f"'{food_name_input}'に一致する食品が見つかりませんでした。")
        return False
    
    # ページネーション付きで検索結果を表示
    page_size = 20
    current_page = 0
    total_pages = (len(matches) - 1) // page_size + 1
    
    while True:
        print(f"\n'{food_name_input}'の検索結果 (ページ {current_page + 1}/{total_pages}, 全{len(matches)}件):")
        
        start_idx = current_page * page_size
        end_idx = min(start_idx + page_size, len(matches))
        
        for i in range(start_idx, end_idx):
            match = matches[i]
            calories = match.get('エネルギー', 'N/A')
            protein = match.get('たんぱく質', 'N/A')
            fat = match.get('脂質', 'N/A')
            carb = match.get('炭水化物', 'N/A')
            print(f"  {i+1}. {match['名前']}")
            print(f"     エネルギー: {calories} kcal, たんぱく質: {protein} g, 脂質: {fat} g, 炭水化物: {carb} g")
        
        # ページナビゲーション
        nav_options = []
        if current_page > 0:
            nav_options.append("p: 前のページ")
        if current_page < total_pages - 1:
            nav_options.append("n: 次のページ")
        nav_options.extend(["番号: 食品を選択", "0: キャンセル"])
        
        print(f"\n操作: {', '.join(nav_options)}")
        user_input = input("選択してください: ").strip().lower()
        
        if user_input == '0':
            return False
        elif user_input == 'p' and current_page > 0:
            current_page -= 1
            continue
        elif user_input == 'n' and current_page < total_pages - 1:
            current_page += 1
            continue
        else:
            # 数値入力として処理
            try:
                choice = int(user_input)
                if 1 <= choice <= len(matches):
                    selected = matches[choice - 1]
                    break
                else:
                    print("無効な番号です。")
                    continue
            except ValueError:
                print("有効な入力をしてください。")
                continue
    
    # 既に選択済みかチェック
    existing_food = next((food for food in foods_list if food['名前'] == selected['名前']), None)
    if existing_food:
        overwrite = input(f"'{selected['名前']}'は既に登録済みです。上書きしますか？ (y/N): ").strip().lower()
        if overwrite != 'y':
            return False
        # 既存の価格・制約情報を保持
        selected['price'] = existing_food.get('price', 0)
        selected['unit'] = existing_food.get('unit', '100g')
        selected['min_units'] = existing_food.get('min_units', '')
        selected['max_units'] = existing_food.get('max_units', '')
        selected['enabled'] = existing_food.get('enabled', 'TRUE')
        # 既存エントリを削除
        foods_list[:] = [food for food in foods_list if food['名前'] != selected['名前']]
    else:
        # 価格と単位を入力
        while True:
            try:
                price = float(input(f"'{selected['名前']}'の価格（円）: "))
                if price < 0:
                    print("価格は0以上で入力してください。")
                    continue
                break
            except ValueError:
                print("有効な数値を入力してください。")
        
        # 単位を選択
        print("\n単位を選択してください:")
        unit_options = ['100g', '1個', '1本', '1枚', '1kg', '1袋', '1缶', '1パック']
        for i, unit_opt in enumerate(unit_options, 1):
            print(f"  {i}. {unit_opt}")
        print("  9. カスタム単位")
        
        while True:
            try:
                unit_choice = int(input("番号を選択してください: "))
                if 1 <= unit_choice <= 8:
                    unit = unit_options[unit_choice - 1]
                    break
                elif unit_choice == 9:
                    unit = input("カスタム単位を入力してください: ").strip()
                    if unit:
                        break
                    else:
                        print("単位を入力してください。")
                else:
                    print("有効な番号を選択してください。")
            except ValueError:
                print("有効な数値を入力してください。")
        
        # 制約情報を設定
        selected['price'] = price
        selected['unit'] = unit
        selected['min_units'] = ''  # 初期値として空文字（下限なし）
        selected['max_units'] = ''  # 初期値として空文字（上限なし）
        selected['enabled'] = 'TRUE'
    
    # リストに追加
    foods_list.append(selected)
    print(f"OK: '{selected['名前']}'を追加しました。")
    return True

def interactive_food_selection():
    """対話式で食品を選択し、価格を設定（既存ファイル追加方式）"""
    print("=== Step2: 食品情報設定（追加・編集モード） ===")
    print("既存のfoods.csvに食品を追加・編集します。")
    print("'quit'で終了して、foods.csvを保存します。\n")
    
    db = FoodCompositionDatabase()
    
    if db.food_data is None or db.food_data.empty:
        print("ERROR: 食品成分データベースの読み込みに失敗しました。")
        print("data/raw/食品成分表ファイルが存在することを確認してください。")
        return False
    
    # 既存データを読み込み
    foods_list, foods_path = load_existing_foods()
    
    # 既存食品を表示
    show_existing_foods(foods_list)
    
    while True:
        # メニュー表示
        print("\n" + "="*50)
        print("*** 操作メニュー ***")
        print("  add    : 新しい食品を追加")
        print("  list   : 登録済み食品を表示") 
        print("  quit   : 保存して終了")
        
        action = input("\n操作を選択してください: ").strip().lower()
        
        if action == 'quit':
            break
        elif action == 'list':
            show_existing_foods(foods_list)
            continue
        elif action == 'add':
            add_new_food(foods_list, db)
        else:
            print("ERROR: 無効な操作です。add/list/quit のいずれかを入力してください。")

    # CSVファイルを保存
    if foods_list:
        df = pd.DataFrame(foods_list)
        
        # nutrition_complete.csvと同じ列順序に並び替え
        try:
            # nutrition_complete.csvから正しい列順序を取得
            import os
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            complete_csv_path = os.path.join(base_dir, 'data', 'input', 'nutrition_complete.csv')
            complete_df = pd.read_csv(complete_csv_path, nrows=1)
            nutrition_columns = complete_df.columns.tolist()
            
            # 目標列順序：日本語栄養素列 + 価格情報列
            target_columns = nutrition_columns + ['price', 'unit', 'min_units', 'max_units', 'enabled']
            
            # 存在する列のみを選択して並び替え
            available_columns = [col for col in target_columns if col in df.columns]
            df_ordered = df[available_columns]
            
            print(f"列順序確認: {len(available_columns)}列 (最初の5列: {available_columns[:5]})")
            
        except Exception as e:
            print(f"WARNING: 列並び替えエラー: {e}")
            df_ordered = df
        
        df_ordered.to_csv(foods_path, index=False, encoding='utf-8')
        
        print(f"\n保存完了: {len(foods_list)}件の食品データを保存しました:")
        print(f"   {foods_path} (制約情報統合済み)")
        
        # サマリー表示
        print(f"\n=== 最終食品データサマリー ===")
        for food in foods_list:
            print(f"- {food['名前']}: {food.get('price', 'N/A')}円/{food.get('unit', 'N/A')}")
            print(f"  エネルギー: {food.get('エネルギー', 'N/A')} kcal, "
                  f"たんぱく質: {food.get('たんぱく質', 'N/A')} g")
        
        print(f"\n食品制約設定:")
        print("foods.csv ファイルの min_units, max_units列を編集して各食品の摂取単位数制限を設定してください。")
        print("min_units: 最小単位数（空=下限なし）, max_units: 最大単位数（空=上限なし）, enabled: TRUE/FALSE で有効/無効切り替え")
        
        print(f"\n次のステップ:")
        print("1. foods.csv の min_units, max_units, enabled列を編集して食品制約を設定（オプション）")
        print("2. src/step3_optimize.py で最適化を実行")
        
        return True
    else:
        print("食品が選択されませんでした。")
        return False

if __name__ == "__main__":
    try:
        interactive_food_selection()
    except KeyboardInterrupt:
        print("\n\n操作が中断されました。")
    except Exception as e:
        print(f"\nエラーが発生しました: {e}")
        sys.exit(1)