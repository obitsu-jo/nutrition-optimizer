#!/usr/bin/env python3
"""
Step3: 最適化計算
制約条件と食品データを基に栄養最適化を実行する
"""

import os
import sys
import json
from datetime import datetime

# パスを追加
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(current_dir, 'core'))

from hybrid_data_loader import load_hybrid_data
from optimizer import create_optimization_model, solve_optimization

def check_prerequisites():
    """前提条件をチェック"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    foods_path = os.path.join(base_dir, 'data', 'input', 'foods.csv')
    nutrition_constraints_path = os.path.join(base_dir, 'data', 'input', 'nutrition_constraints.csv')
    calculation_info_path = os.path.join(base_dir, 'data', 'input', 'calculation_info.json')
    
    issues = []
    
    if not os.path.exists(foods_path):
        issues.append("foods.csv が見つかりません → src/step2_foods.py を実行してください")
    
    if not os.path.exists(nutrition_constraints_path):
        issues.append("nutrition_constraints.csv が見つかりません → src/step1_constraints.py を実行してください")
    
    if not os.path.exists(calculation_info_path):
        issues.append("calculation_info.json が見つかりません → src/step1_constraints.py を実行してください")
    
    if issues:
        print("=== 前提条件エラー ===")
        for issue in issues:
            print(issue)
        return False
    
    return True

def save_results(result, foods, constraints):
    """結果を保存"""
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    output_dir = os.path.join(base_dir, 'data', 'output')
    os.makedirs(output_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    result_file = os.path.join(output_dir, f"optimization_result_{timestamp}.json")
    
    # 結果データを整理
    output_data = {
        "timestamp": datetime.now().isoformat(),
        "status": result['status'],
        "optimal": result['optimal'],
        "total_cost_yen": result.get('total_cost', 0),
        "foods": result.get('foods', {}),
        "nutrition": result.get('nutrition', {}),
        "constraints_used": constraints,
        "foods_available": len(foods)
    }
    
    # JSONファイルに保存
    with open(result_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, ensure_ascii=False, indent=2)
    
    print(f"詳細結果を保存: {result_file}")

def main():
    """メイン処理"""
    print("=== Step3: 栄養最適化計算 ===\n")
    
    # 前提条件チェック
    if not check_prerequisites():
        return False
    
    # データファイルのパス
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    input_dir = os.path.join(base_dir, 'data', 'input')
    
    try:
        # ハイブリッド形式データ読み込み
        print("ハイブリッド形式データを読み込んでいます...")
        foods, constraints = load_hybrid_data(base_dir)
        
        # 最適化モデル作成
        print("最適化モデルを作成しています...")
        problem, food_vars = create_optimization_model(foods, constraints)
        
        # 最適化実行
        print("最適化を実行しています...\n")
        result = solve_optimization(problem, food_vars, foods, constraints)
        
        # 結果表示
        print("=" * 50)
        print("最適化結果")
        print("=" * 50)
        print(f"ステータス: {result['status']}")
        
        if result['optimal']:
            print(f"最小コスト: {result['total_cost']:.2f}円/日")
            
            print(f"\n推奨食品と摂取量:")
            for food_name, info in result['foods'].items():
                print(f"  • {food_name}")
                print(f"    摂取量: {info['units']:.2f} {info['unit_type']}")
                print(f"    コスト: {info['cost']:.2f}円")
            
            print(f"\n栄養成分（制約有効項目）:")
            
            # 制約から栄養素名とラベルを取得
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            constraints_path = os.path.join(base_dir, 'data', 'input', 'nutrition_constraints.csv')
            
            try:
                import pandas as pd
                constraints_df = pd.read_csv(constraints_path)
                nutrient_labels = dict(zip(constraints_df['nutrient_id'], constraints_df['nutrient_name']))
                nutrient_units = dict(zip(constraints_df['nutrient_id'], constraints_df['unit']))
            except:
                nutrient_labels = {}
                nutrient_units = {}
            
            for nutrient, value in result['nutrition'].items():
                # 栄養素名とラベルを取得
                label = nutrient_labels.get(nutrient, nutrient)
                unit = nutrient_units.get(nutrient, '')
                
                # 制約範囲と比較
                constraint = constraints.get('nutrition_constraints', {}).get(nutrient, {})
                min_val = constraint.get('min', '')
                max_val = constraint.get('max', '')
                
                # 範囲文字列を作成
                if min_val != '' and max_val != '':
                    range_str = f" (目標: {min_val}-{max_val})"
                elif min_val != '':
                    range_str = f" (最低: {min_val})"
                elif max_val != '':
                    range_str = f" (上限: {max_val})"
                else:
                    range_str = ""
                
                print(f"  • {label}: {value} {unit}{range_str}")
            
            
            # 結果保存
            save_results(result, foods, constraints)
            
            print(f"\n最適化が成功しました！")
            
        else:
            print("最適解が見つかりませんでした。")
            print("\n解決方法:")
            print("1. 制約条件を緩和する (src/step1_constraints.py)")
            print("2. より多くの食品を追加する (src/step2_foods.py)")
            print("3. 食品の摂取上限を増やす")
            
            return False
            
    except FileNotFoundError as e:
        print(f"ファイルが見つかりません: {e}")
        return False
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print(f"\n処理が完了しました。")
        else:
            sys.exit(1)
    except KeyboardInterrupt:
        print("\n\n操作が中断されました。")
        sys.exit(1)