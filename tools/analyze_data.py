#!/usr/bin/env python3
"""
食品成分表の構造を分析するスクリプト
"""

import pandas as pd
import os

def analyze_excel_file():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    excel_path = os.path.join(base_dir, 'data', 'raw', '20230428-mxt_kagsei-mext_00001_012.xlsx')
    
    try:
        # Excelファイルのシート一覧を確認
        xl_file = pd.ExcelFile(excel_path)
        print("シート一覧:")
        for i, sheet in enumerate(xl_file.sheet_names):
            print(f"{i}: {sheet}")
        
        # 表全体シートを詳しく確認
        sheet_name = "表全体"
        print(f"\n=== シート: {sheet_name} 詳細分析 ===")
        
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        print(f"形状: {df.shape}")
        print("最初の15行の最初の10列:")
        for i in range(15):
            if i < len(df):
                row_data = df.iloc[i, 0:10].tolist()
                row_str = [str(val)[:15] if pd.notna(val) else 'NaN' for val in row_data]
                print(f"行{i}: {row_str}")
        
        # ヘッダー行（行1）の全列を確認
        print("\n=== ヘッダー行（行1）全体 ===")
        headers = df.iloc[1].tolist()
        for i, header in enumerate(headers):
            if pd.notna(header):
                print(f"列{i}: {header}")
        
        # 成分識別子行（行10）も確認
        print("\n=== 成分識別子行（行10）===")
        identifiers = df.iloc[10].tolist()
        for i, identifier in enumerate(identifiers):
            if pd.notna(identifier):
                print(f"列{i}: {identifier}")
        
        # サンプルデータも確認
        print("\n=== サンプルデータ（行11） ===")
        sample_data = df.iloc[11].tolist()
        for i, val in enumerate(sample_data[:20]):
            if pd.notna(val):
                print(f"列{i}: {val}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    analyze_excel_file()