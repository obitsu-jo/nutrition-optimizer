import pulp
import pandas as pd
from typing import Dict, Any

def create_optimization_model(foods: pd.DataFrame, constraints: Dict[str, Any]) -> pulp.LpProblem:
    """線形計画モデルを作成する（全栄養素対応）"""
    
    # 問題を定義（コスト最小化）
    problem = pulp.LpProblem("NutritionOptimization", pulp.LpMinimize)
    
    # 決定変数：各食品の摂取単位数
    food_vars = {}
    for _, row in foods.iterrows():
        food_name = row['food_name']
        food_vars[food_name] = pulp.LpVariable(
            f"units_{food_name}", 
            lowBound=0, 
            cat='Continuous'
        )
    
    # 目的関数：総コストの最小化（単位数×価格）
    total_cost = pulp.lpSum([
        food_vars[row['food_name']] * row['price']
        for _, row in foods.iterrows()
    ])
    problem += total_cost
    
    # 全栄養素制約を動的に追加
    nutrition_constraints = constraints['nutrition_constraints']
    
    for nutrient_name, constraint in nutrition_constraints.items():
        # 該当する栄養素列が食品データに存在するかチェック
        if nutrient_name in foods.columns:
            # 栄養素の総摂取量を計算（単位数ベース：単位数×栄養素値）
            total_nutrient = pulp.lpSum([
                food_vars[row['food_name']] * row[nutrient_name]
                for _, row in foods.iterrows()
                if pd.notna(row[nutrient_name])  # NaN値をスキップ
            ])
            
            # 制約を追加
            if 'min' in constraint:
                problem += total_nutrient >= constraint['min']
            if 'max' in constraint:
                problem += total_nutrient <= constraint['max']
            
            print(f"制約追加: {nutrient_name} ({constraint.get('min', 0)} - {constraint.get('max', '無制限')} {constraint.get('unit', '')})")
    
    # 食品摂取単位数制約（上限・下限）
    food_constraints = constraints['food_constraints']
    for food_name, limits in food_constraints.items():
        if food_name in food_vars:
            # 最小単位数制約
            if limits.get('min_units', 0) > 0:
                problem += food_vars[food_name] >= limits['min_units']
                print(f"食品制約追加: {food_name} >= {limits['min_units']}単位")
            # 最大単位数制約
            if limits.get('max_units', 0) > 0:
                problem += food_vars[food_name] <= limits['max_units']
                print(f"食品制約追加: {food_name} <= {limits['max_units']}単位")
    
    return problem, food_vars

def solve_optimization(problem: pulp.LpProblem, food_vars: Dict[str, pulp.LpVariable], foods: pd.DataFrame, constraints: Dict[str, Any] = None) -> Dict[str, Any]:
    """最適化問題を解く"""
    
    # デバッグ情報を出力
    print(f"最適化問題の詳細:")
    print(f"  • 変数数: {len(food_vars)}")
    print(f"  • 制約数: {len(problem.constraints)}")
    
    # 制約の厳しさを警告
    if len(food_vars) < 10:
        print(f"注意: 食品種類が少ない({len(food_vars)}種類)ため、制約を満たすのに非効率な組み合わせが必要になる可能性があります")
    
    # 求解
    status = problem.solve(pulp.PULP_CBC_CMD(msg=1))
    
    result = {
        'status': pulp.LpStatus[status],
        'optimal': status == pulp.LpStatusOptimal,
        'total_cost': 0,
        'foods': {},
        'nutrition': {}
    }
    
    if status == pulp.LpStatusOptimal:
        result['total_cost'] = pulp.value(problem.objective)
        
        # 各食品の最適摂取単位数
        for food_name, var in food_vars.items():
            units = pulp.value(var)
            if units > 0.001:  # 微小値は無視
                food_data = foods[foods['food_name'] == food_name].iloc[0]
                result['foods'][food_name] = {
                    'units': round(units, 2),
                    'unit_type': food_data['unit'],
                    'cost': round(units * food_data['price'], 2)
                }
        
        # 制約で有効な栄養素の摂取量を計算
        nutrition_results = {}
        
        if constraints and 'nutrition_constraints' in constraints:
            # 制約で有効になっている栄養素のみを計算
            for nutrient_name in constraints['nutrition_constraints'].keys():
                if nutrient_name in foods.columns:
                    total_nutrient = sum([
                        result['foods'].get(row['food_name'], {}).get('units', 0) * row[nutrient_name]
                        for _, row in foods.iterrows()
                        if pd.notna(row[nutrient_name])
                    ])
                    nutrition_results[nutrient_name] = round(total_nutrient, 2)
        
        result['nutrition'] = nutrition_results
    
    return result