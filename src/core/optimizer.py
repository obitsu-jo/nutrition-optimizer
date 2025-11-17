import pulp
from itertools import combinations
import polars as pl
import os

def find_optimal_solution_iteratively(df_foods, df_constraints, base_output_path):
    """
    最適化問題を解き、失敗した場合は制約を1つずつ緩和して再試行するラッパー関数

    Args:
        df_foods (pl.DataFrame): 食品データのDataFrame
        df_constraints (pl.DataFrame): 栄養素制約のDataFrame
        base_output_path (str): 成功した場合の基本的な出力ファイルパス

    Returns:
        tuple: (pulp.LpProblem, pulp.LpStatus) or (None, pulp.LpStatus)
    """
    # --- Step 1: まずは全ての制約を使って試行 ---
    print("--- Step 1: 全ての制約を適用して最適化を試みます ---")
    prob, status = solve_optimization_problem(df_foods, df_constraints)

    # 修正点: pulp.LpStatus['Optimal'] -> pulp.LpStatusOptimal
    if status == pulp.LpStatusOptimal:
        print(">>> 成功: 全ての制約を満たす最適解が見つかりました。")
        save_results_to_csv(prob.variables(), df_foods, base_output_path, df_constraints)
        return prob, status

    print(">>> 失敗: 最適解が見つかりませんでした。制約の緩和を開始します。")

    # --- Step 2: 緩和する制約のリストを作成 ---
    all_possible_constraints = []
    for row in df_constraints.iter_rows(named=True):
        nutrient_id = row['nutrient_id']
        if row['lower'] is not None:
            all_possible_constraints.append(f"Min_{nutrient_id}")
        if row['upper'] is not None:
            all_possible_constraints.append(f"Max_{nutrient_id}")

    # --- Step 3: 制約を1つ、2つ、...と外しながら試行 ---
    for k in range(1, len(all_possible_constraints) + 1):
        print(f"\n--- Step {k+1}: {k}個の制約を無視して試行します ---")
        
        for constraints_to_ignore in combinations(all_possible_constraints, k):
            
            constraints_to_ignore = list(constraints_to_ignore)
            print(f"  - 無視する制約: {constraints_to_ignore}")
            
            prob, status = solve_optimization_problem(df_foods, df_constraints, constraints_to_ignore=constraints_to_ignore)

            # 修正点: pulp.LpStatus['Optimal'] -> pulp.LpStatusOptimal
            if status == pulp.LpStatusOptimal:
                print(f">>> 成功: {k}個の制約を無視して最適解が見つかりました。")
                
                removed_str = "_".join(constraints_to_ignore)
                output_dir = os.path.dirname(base_output_path)
                output_filename = f"results_without_{removed_str}.csv"
                output_path = os.path.join(output_dir, output_filename)
                
                save_results_to_csv(prob.variables(), df_foods, output_path, df_constraints)
                return prob, status

    # --- Step 4: 全ての試行が失敗 ---
    print("\n--- 全ての緩和策を試みましたが、最適解を見つけることができませんでした。 ---")
    # 修正点: pulp.LpStatus['Infeasible'] -> pulp.LpStatusInfeasible
    return None, pulp.LpStatusInfeasible

def solve_optimization_problem(df_foods, df_constraints, constraints_to_ignore=None):
    """
    与えられたデータと制約で最適化問題を解く汎用関数

    Args:
        df_foods (pl.DataFrame): 食品データのDataFrame
        df_constraints (pl.DataFrame): 栄養素制約のDataFrame
        constraints_to_ignore (list, optional): 無視する制約名のリスト (例: ['Min_energy', 'Max_vitamin_a'])

    Returns:
        tuple: (pulp.LpProblem, pulp.LpStatus) 最適化問題のオブジェクトとその結果ステータス
    """
    food_items = df_foods.to_dicts()

    if constraints_to_ignore is None:
        constraints_to_ignore = []

    prob = pulp.LpProblem("Diet_Optimization", pulp.LpMinimize)
    food_vars = pulp.LpVariable.dicts("food", [f["food_name"] for f in food_items], lowBound=0, cat='Continuous')
    prob += pulp.lpSum([food["cost"] * food_vars[food["food_name"]] for food in food_items]), "Total Cost"

    # 各食品の最小・最大摂取量の制約を追加
    for food in food_items:
        food_name = food["food_name"]
        
        # 'min' 列に有効な値があり、'amount'が0より大きい場合、下限制約を追加
        if food.get("min") is not None and food.get("amount") is not None and food["amount"] > 0:
            # 制約は「購入単位数」に対して設定する
            # (最小摂取量 / 単位あたりの量) で、必要な最小購入単位数を計算
            min_units = food["min"] / food["amount"]
            prob += food_vars[food_name] >= min_units, f"Min_amount_{food_name}"

        # 'max' 列に有効な値があり、'amount'が0より大きい場合、上限制約を追加
        if food.get("max") is not None and food.get("amount") is not None and food["amount"] > 0:
            # (最大摂取量 / 単位あたりの量) で、許容される最大購入単位数を計算
            max_units = food["max"] / food["amount"]
            prob += food_vars[food_name] <= max_units, f"Max_amount_{food_name}"

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
    prob.solve(pulp.PULP_CBC_CMD(msg=0))
    return prob, prob.status

def save_results_to_csv(prob_variables, df_foods: pl.DataFrame, output_path: str, df_constraints: pl.DataFrame):
    food_data_map = {f["food_name"]: f for f in df_foods.to_dicts()}
    results_data = []
    nutrient_columns = [col for col in df_foods.columns if col not in ["food_name", "amount", "min", "max", "unit", "cost"]]
    totals = {col: 0.0 for col in nutrient_columns}
    totals["cost"] = 0.0
    for var in prob_variables:
        if var.varValue > 0:
            food_name = var.name.replace("food_", "").replace("_", " ")
            num_units = var.varValue
            food_info = food_data_map[food_name]
            row_data = {
                "food_name": food_name,
                "cost": food_info["cost"] * num_units,
                "amount": f"{num_units * food_info['amount']:.2f}",
                "unit": food_info["unit"]
            }
            for nutrient in nutrient_columns:
                value = food_info[nutrient] * num_units
                row_data[nutrient] = value
                totals[nutrient] += value
            totals["cost"] += row_data["cost"]
            results_data.append(row_data)
    total_row = {"food_name": "total", "cost": totals["cost"], "amount": "", "unit": ""}
    for nutrient in nutrient_columns:
        total_row[nutrient] = totals[nutrient]
    results_data.append(total_row)
    df_results = pl.DataFrame(results_data)
    final_columns = ["food_name", "cost", "amount", "unit"] + nutrient_columns
    df_results = df_results.select(final_columns)

    list_lower = df_constraints.select(["nutrient_id", "lower"]).rows() # [(nutrient_id, lower)]
    add_data = {
        "food_name": "achievement_rate (%)",
        "cost": None,
        "amount": None,
        "unit": None
    }
    for nutrient_id, lower in list_lower:
        if lower is not None:
            achievement_rate = (totals[nutrient_id] / lower) * 100 if lower != 0 else None
            add_data[nutrient_id] = achievement_rate if achievement_rate is not None else None
            add_data[nutrient_id]
        else:
            add_data[nutrient_id] = None

    
    df_results = df_results.vstack(pl.DataFrame([add_data]))


    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_results.write_csv(output_path)
    print(f"\n結果がCSVファイルに出力されました: {output_path}")