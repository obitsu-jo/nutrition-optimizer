import pulp
import polars as pl
import os

# --- 定数設定 ---
NUTRIENT_CONSTRAINT_PATH = "/app/data/step1_constraints/test/nutrient_constraints.csv"
FOOD_NUTRIENT_DATA_PATH = "/app/data/step2_foods/test/food_nutrient_data.csv" 
OPTIMIZATION_RESULT_PATH = "/app/data/step3_result/test/diet_plan.csv"


def solve_optimization_problem(food_items, df_constraints, constraints_to_ignore=None):
    """
    与えられたデータと制約で最適化問題を解く汎用関数

    Args:
        food_items (list): 食品データの辞書のリスト
        df_constraints (pl.DataFrame): 栄養素制約のDataFrame
        constraints_to_ignore (list, optional): 無視する制約名のリスト (例: ['Min_energy', 'Max_vitamin_a'])

    Returns:
        tuple: (pulp.LpProblem, pulp.LpStatus) 最適化問題のオブジェクトとその結果ステータス
    """
    if constraints_to_ignore is None:
        constraints_to_ignore = []

    prob = pulp.LpProblem("Diet_Optimization", pulp.LpMinimize)
    food_vars = pulp.LpVariable.dicts("food", [f["food_name"] for f in food_items], lowBound=0, cat='Continuous')
    prob += pulp.lpSum([food["price"] * food_vars[food["food_name"]] for food in food_items]), "Total Cost"

    for row in df_constraints.iter_rows(named=True):
        nutrient_id = row['nutrient_id']
        if nutrient_id not in food_items[0]:
            continue

        total_nutrient = pulp.lpSum([food[nutrient_id] * food_vars[food["food_name"]] for food in food_items])
        
        min_constraint_name = f"Min_{nutrient_id}"
        if row['lower'] is not None and min_constraint_name not in constraints_to_ignore:
            prob += total_nutrient >= row['lower'], min_constraint_name
        
        max_constraint_name = f"Max_{nutrient_id}"
        if row['upper'] is not None and max_constraint_name not in constraints_to_ignore:
            prob += total_nutrient <= row['upper'], max_constraint_name

    # デバッグループ中はソルバーのメッセージを非表示にする
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return prob, prob.status


def debug_infeasible_problem(food_items, df_constraints):
    """
    実行不可能な問題の原因となっている可能性のある制約を特定する
    """
    print("\n--- 実行不可能(Infeasible)の原因分析を開始します ---")
    print("制約を1つずつ緩和して、解決可能になるか試します...")

    problematic_constraints = []
    
    # 全ての制約名のリストを作成
    all_constraints_to_test = []
    for row in df_constraints.iter_rows(named=True):
        if row['lower'] is not None:
            all_constraints_to_test.append(f"Min_{row['nutrient_id']}")
        if row['upper'] is not None:
            all_constraints_to_test.append(f"Max_{row['nutrient_id']}")

    # 各制約を1つだけ無視して計算を試す
    for constraint in all_constraints_to_test:
        _, status = solve_optimization_problem(food_items, df_constraints, constraints_to_ignore=[constraint])
        
        # もし最適解が見つかれば、無視した制約が原因の候補
        if pulp.LpStatus[status] == 'Optimal':
            problematic_constraints.append(constraint)

    if problematic_constraints:
        print("\n[分析結果] 以下の制約が原因である可能性が高いです:")
        for p_constraint in problematic_constraints:
            print(f"  - {p_constraint}")
        print("\nこれらの栄養素の目標値を見直すか、栄養を補える別の食品を追加してみてください。")
    else:
        print("\n[分析結果] 単一の制約緩和では解決しませんでした。")
        print("複数の制約の組み合わせが原因である可能性が高いです。")


def main():
    """
    栄養制約を満たしつつ、コストを最小化する食品の組み合わせを計算する
    """
    try:
        df_constraints = pl.read_csv(NUTRIENT_CONSTRAINT_PATH)
        df_foods = pl.read_csv(FOOD_NUTRIENT_DATA_PATH)
    except FileNotFoundError as e:
        print(f"エラー: ファイルが見つかりません。パスを確認してください: {e.filename}")
        return

    food_items = df_foods.to_dicts()

    # --- 最初の最適化計算 ---
    print("最適化計算を開始します...")
    prob, status = solve_optimization_problem(food_items, df_constraints)
    
    # --- 結果の表示 ---
    print("-" * 30)
    print(f"最適化結果: {pulp.LpStatus[status]}")
    print("-" * 30)

    if pulp.LpStatus[status] == 'Optimal':
        print(f"算出された最小コスト: {pulp.value(prob.objective):.2f} 円")
        print("\n摂取すべき食品と量:")
        
        food_data_map = {f["food_name"]: f for f in food_items}
        for var in prob.variables():
            if var.varValue > 0:
                food_name = var.name.replace("food_", "").replace("_", " ")
                food_info = food_data_map[food_name]
                print(f"- {food_name}: {var.varValue:.2f} x ({food_info['quantity']} {food_info['unit']})")

        save_results_to_csv(prob.variables(), df_foods, OPTIMIZATION_RESULT_PATH)

    elif pulp.LpStatus[status] == 'Infeasible':
        print("実行不可能: 制約を満たす解を見つけることができませんでした。")
        debug_infeasible_problem(food_items, df_constraints)

    else:
        print("最適解を見つけることができませんでした。")

def save_results_to_csv(prob_variables, df_foods: pl.DataFrame, output_path: str):
    food_data_map = {f["food_name"]: f for f in df_foods.to_dicts()}
    results_data = []
    nutrient_columns = [col for col in df_foods.columns if col not in ["food_name", "quantity", "unit", "price"]]
    totals = {col: 0.0 for col in nutrient_columns}
    totals["cost"] = 0.0
    for var in prob_variables:
        if var.varValue > 0:
            food_name = var.name.replace("food_", "").replace("_", " ")
            num_units = var.varValue
            food_info = food_data_map[food_name]
            row_data = {
                "food_name": food_name,
                "amount": f"{num_units:.2f} x ({food_info['quantity']} {food_info['unit']})",
                "cost": food_info["price"] * num_units
            }
            for nutrient in nutrient_columns:
                value = food_info[nutrient] * num_units
                row_data[nutrient] = value
                totals[nutrient] += value
            totals["cost"] += row_data["cost"]
            results_data.append(row_data)
    total_row = {"food_name": "--- TOTAL ---", "amount": "", "cost": totals["cost"]}
    for nutrient in nutrient_columns:
        total_row[nutrient] = totals[nutrient]
    results_data.append(total_row)
    df_results = pl.DataFrame(results_data)
    final_columns = ["food_name", "amount", "cost"] + nutrient_columns
    df_results = df_results.select(final_columns)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_results.write_csv(output_path)
    print(f"\n詳細な結果がCSVファイルに出力されました: {output_path}")


if __name__ == "__main__":
    main()