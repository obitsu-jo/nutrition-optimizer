#!/usr/bin/env python3
"""
脂肪酸データ統合モジュール
MEXT脂肪酸成分表（032.xlsx）からn-6系、n-3系脂肪酸データを抽出・計算し、
基本成分表データと統合する
"""

import pandas as pd
import os
from typing import Dict, Tuple, Optional

class FattyAcidIntegrator:
    def __init__(self):
        # プロジェクトルートディレクトリを取得
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.fatty_acid_path = os.path.join(self.base_dir, 'data', 'raw', '20230428-mxt_kagsei-mext_00001_032.xlsx')
        self.fatty_acid_data = None
        self.load_fatty_acid_data()
    
    def load_fatty_acid_data(self):
        """脂肪酸成分表データを読み込む"""
        try:
            # 表全体シートを使用、データは6行目から開始（0ベースで6行目）
            df = pd.read_excel(self.fatty_acid_path, sheet_name='表全体', header=None, skiprows=6)
            
            # 列の対応関係（実際のデータ構造に基づく）
            # 0: group_code, 1: food_code, 2: item_no, 3: food_name
            # 4: water, 5: triacylglycerol, 6: fat, 7: total_fatty_acid
            # 8: saturated_fat, 9: monounsaturated_fat, 10: polyunsaturated_fat
            # 11: n3_fatty_acid, 12: n6_fatty_acid
            
            # 必要な列を選択してカラム名を設定
            self.fatty_acid_data = df[[0, 1, 2, 3, 8, 10, 11, 12]].copy()
            self.fatty_acid_data.columns = [
                'group_code', 'food_code', 'item_no', 'food_name',
                'saturated_fat', 'polyunsaturated_fat', 'n3_fatty_acid', 'n6_fatty_acid'
            ]
            
            # 数値データのクリーニング
            for col in ['saturated_fat', 'polyunsaturated_fat', 'n3_fatty_acid', 'n6_fatty_acid']:
                self.fatty_acid_data[col] = self.fatty_acid_data[col].apply(self._clean_numeric_value)
            
            print(f"📊 脂肪酸データ: {len(self.fatty_acid_data)}件の食品データを読み込みました")
            
        except Exception as e:
            print(f"❌ 脂肪酸データの読み込みに失敗: {e}")
            self.fatty_acid_data = None
    
    def _clean_numeric_value(self, val):
        """数値データをクリーニング"""
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip()
        # 特殊記号を処理
        if val_str in ['*', '-', '(0)', 'Tr', 'tr', '']:
            return 0.0
        # 括弧を除去 "(1.23)" -> "1.23"
        val_str = val_str.replace('(', '').replace(')', '')
        try:
            return float(val_str)
        except (ValueError, TypeError):
            return 0.0
    
    def calculate_fatty_acids(self, food_name: str) -> Tuple[Optional[float], Optional[float]]:
        """
        食品名に基づいてn-3系、n-6系脂肪酸を取得
        改善されたマッチングロジック：完全一致 > 詳細一致 > 部分一致
        
        Args:
            food_name: 食品名（例: "こめ　［水稲穀粒］　精白米　うるち米"）
            
        Returns:
            Tuple[n3_fatty_acid, n6_fatty_acid] (g/100g)
        """
        if self.fatty_acid_data is None:
            return None, None
        
        try:
            # Step 1: 完全一致を優先
            exact_match = self.fatty_acid_data[
                self.fatty_acid_data['food_name'] == food_name
            ]
            
            if not exact_match.empty:
                match = exact_match.iloc[0]
                n3_value = match['n3_fatty_acid'] if pd.notna(match['n3_fatty_acid']) else 0.0
                n6_value = match['n6_fatty_acid'] if pd.notna(match['n6_fatty_acid']) else 0.0
                return n3_value, n6_value
            
            # Step 2: より多くのキーワードがマッチする食品を優先
            # 食品名からキーワードを抽出
            keywords = [word for word in food_name.replace('＜', '').replace('＞', '').replace('［', '').replace('］', '').split('　') if word.strip()]
            
            if len(keywords) >= 2:
                # 全キーワードを含む食品を検索
                matches = self.fatty_acid_data.copy()
                for keyword in keywords:
                    if keyword:
                        matches = matches[matches['food_name'].str.contains(keyword, na=False, case=False)]
                
                if not matches.empty:
                    # 最もキーワード数が多い食品を選択
                    best_match = matches.iloc[0]
                    n3_value = best_match['n3_fatty_acid'] if pd.notna(best_match['n3_fatty_acid']) else 0.0
                    n6_value = best_match['n6_fatty_acid'] if pd.notna(best_match['n6_fatty_acid']) else 0.0
                    return n3_value, n6_value
            
            # Step 3: 従来の部分一致検索（最後の手段）
            matches = self.fatty_acid_data[
                self.fatty_acid_data['food_name'].str.contains(food_name[:10], na=False, case=False)
            ]
            
            if matches.empty:
                # より簡単な名前で再検索
                simple_name = food_name.split('　')[0] if '　' in food_name else food_name[:5]
                matches = self.fatty_acid_data[
                    self.fatty_acid_data['food_name'].str.contains(simple_name, na=False, case=False)
                ]
            
            if not matches.empty:
                # 最初のマッチを使用
                match = matches.iloc[0]
                n3_value = match['n3_fatty_acid'] if pd.notna(match['n3_fatty_acid']) else 0.0
                n6_value = match['n6_fatty_acid'] if pd.notna(match['n6_fatty_acid']) else 0.0
                return n3_value, n6_value
            
            return 0.0, 0.0  # マッチしない場合は0を返す
            
        except Exception as e:
            print(f"⚠️ 脂肪酸計算エラー ({food_name}): {e}")
            return 0.0, 0.0
    
    def get_fatty_acid_mapping(self) -> Dict[str, Tuple[Optional[float], Optional[float]]]:
        """
        全食品の脂肪酸データマッピングを作成
        
        Returns:
            Dict[food_name, (n3_fatty_acid, n6_fatty_acid)]
        """
        if self.fatty_acid_data is None:
            return {}
        
        fatty_acid_mapping = {}
        
        # 実際のデータ処理ロジックをここに実装
        # 今は空のマッピングを返す（データ構造確認後に実装）
        
        return fatty_acid_mapping
    
    def inspect_data_structure(self):
        """データ構造を調査するためのヘルパーメソッド"""
        if self.fatty_acid_data is not None:
            print("=== 脂肪酸データ構造調査 ===")
            print(f"形状: {self.fatty_acid_data.shape}")
            print(f"最初の10行:")
            print(self.fatty_acid_data.iloc[:10, :15])
            print(f"\n列40-50の内容:")
            print(self.fatty_acid_data.iloc[:5, 40:50])

if __name__ == "__main__":
    # テスト実行
    integrator = FattyAcidIntegrator()
    integrator.inspect_data_structure()