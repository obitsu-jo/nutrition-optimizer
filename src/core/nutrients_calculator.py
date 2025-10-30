from functools import cached_property
from typing import Literal, Optional
from dataclasses import dataclass
import polars as pl

@dataclass
class UserProfile:
    sex_code: Literal["M", "F"]  # "male" or "female"
    weight: float  # in kg
    height: float  # in cm
    age: int  # in years
    activity_level: float # low: 1.5, normal: 1.75, high: 2.0
    life_code: Literal["general", "pregnant_early", "pregnant_mid_late", "lactating"] = "general"

class NutrientsCalculator:
    MACRONUTRIENTS = ["energy", "protein", "saturated_fatty_acids", "n6_fatty_acids", "n3_fatty_acids", "carbohydrate"]
    MACRONUTRIENT_UNITS = ["kcal", "g", "g", "g", "g", "g"]
    EER_METHOD = "ganpule" # "harris_benedict" or "ganpule"

    AGE_BANDS_PATH = "/app/resources/age_bands.csv"
    REF_TYPES_PATH = "/app/resources/ref_types.csv"
    NUTRIENT_IDS_PATH = "/app/resources/nutrient_ids.csv"
    VALUES_DIR = "resources/values/"
    LIST_FILE_NAME = ["fiber", "fat_soluble_vitamins", "water_soluble_vitamins", "macrominerals", "microminerals"]

    def __init__(self, user: UserProfile, lower_ref_codes: list[str] = ["RDA", "AI", "DG_LOWER", "EAR"], upper_ref_codes: list[str] = ["UL", "DG_UPPER"]):
        self.sex_code = user.sex_code
        self.weight = user.weight
        self.height = user.height
        self.age = user.age
        self.activity_level = user.activity_level
        self.life_code = user.life_code
        self.lower_ref_codes = lower_ref_codes
        self.upper_ref_codes = upper_ref_codes

        if self.sex_code == "M":
            self.sex_id = 0
        elif self.sex_code == "F":
            self.sex_id = 1

    @cached_property
    def age_band_id(self) -> Optional[int]:
        """ユーザーの年齢からage_band_idを取得する"""
        df_age_bands = pl.read_csv(self.AGE_BANDS_PATH)
        band = df_age_bands.filter((pl.col("min_age") <= self.age) & (self.age < pl.col("max_age")))
        if not band.is_empty():
            return band.select(pl.col("age_band_id")).to_series()[0]
        raise ValueError("対応する年齢バンドが見つかりません。")

    @cached_property
    def nutrient_ids(self) -> list[str]:
        df_nutrient_ids = pl.read_csv(self.NUTRIENT_IDS_PATH)
        return df_nutrient_ids["nutrient_id"].to_list()

    @cached_property
    def dict_nutrient_unit(self) -> dict[str, str]:
        df_nutrient_ids = pl.read_csv(self.NUTRIENT_IDS_PATH)
        dict_nutrient_unit = {nutrient_id: df_nutrient_ids.filter(pl.col("nutrient_id") == nutrient_id)["unit"].to_list()[0] for nutrient_id in self.nutrient_ids}
        for nutrient_id, unit in zip(self.MACRONUTRIENTS, self.MACRONUTRIENT_UNITS):
            dict_nutrient_unit[nutrient_id] = unit
        return dict_nutrient_unit

    @cached_property
    def ref_codes(self) -> list[str]:
        df_ref_types = pl.read_csv(self.REF_TYPES_PATH)
        return df_ref_types.select(pl.col("ref_code")).to_series().to_list()

    @cached_property
    def df_values(self) -> pl.DataFrame:
        """
        UserProfileに基づいて必要なデータのみを抽出する
        """
        
        list_of_dfs = []
        for file_name in self.LIST_FILE_NAME:
            file_path = f"{self.VALUES_DIR}{file_name}.csv"
            try:
                # schema_overrides で 'factor' 列を浮動小数点型として指定
                df_tmp = pl.read_csv(
                    file_path, 
                    schema_overrides={'value': pl.Float64},
                )
                # コメント行を削除
                df_tmp = df_tmp.filter(~pl.col("nutrient_id").str.starts_with("#"))
                # sex_codeによってフィルタリング
                df_tmp = df_tmp.filter(pl.col("sex_code") == self.sex_code).drop("sex_code")
                # age_band_idによってフィルタリング
                df_tmp = df_tmp.filter(pl.col("age_band_id") == self.age_band_id).drop("age_band_id")
                # life_codeによってフィルタリング
                df_tmp = df_tmp.filter(pl.col("life_code") == self.life_code).drop("life_code")
                list_of_dfs.append(df_tmp)
            except Exception as e:
                print(f"Error reading {file_path}: {e}")
                # 必要に応じてエラー処理を追加
                
        # DataFrameのリストを一度に連結する
        if not list_of_dfs:
            return pl.DataFrame() # 空のDataFrameを返すか、エラーを発生させる
            
        df_values = pl.concat(list_of_dfs, how="vertical")
        return df_values

    def _bmr_harris_benedict(self) -> float:
        C = [66.4730, 655.0955]
        C_W = [13.7516, 9.5634]
        C_H = [5.0033, 1.8496]
        C_A = [6.7550, 4.6756]

        bmr = C[self.sex_id] + (C_W[self.sex_id] * self.weight) + (C_H[self.sex_id] * self.height) - (C_A[self.sex_id] * self.age)
        return bmr

    def _bmr_ganpule(self) -> float:
        C_W = [0.0481, 0.0481]
        C_H = [0.0234, 0.0234]
        C_A = [0.0138, 0.0138]
        C = [0.4235, 0.9708]

        bmr = (C_W[self.sex_id] * self.weight + C_H[self.sex_id] * self.height - C_A[self.sex_id] * self.age - C[self.sex_id]) * 1000 / 4.186
        return bmr

    @cached_property
    def eer(self) -> tuple[float, Optional[float]]:

        if self.EER_METHOD == "harris_benedict":
            bmr = self._bmr_harris_benedict()
        else:  # デフォルトはganpule
            bmr = self._bmr_ganpule()

        eer = bmr * self.activity_level
        return eer


    def get_protein(self, ref_code: str) -> tuple[float, Optional[float]]:
        C_W = 0.73 # 体重当たりのたんぱく質必要量 (g/kg)
        C_RDA = 1.25 # たんぱく質推奨量の補正係数
        if ref_code in self.lower_ref_codes:
            if ref_code == "RDA":
                return self.weight * C_W * C_RDA
            elif ref_code == "EAR":
                return self.weight * C_W
            else:
                return None
        else:
            return None

    def get_saturated_fatty_acids(self, ref_code: str) -> tuple[Optional[float], float]:
        C_E = 0.07  # エネルギー比率の上限
        if ref_code in self.upper_ref_codes:
                return (self.eer * C_E) / 9  # g単位に変換
        else:
            return None

    def get_n6_fatty_acids(self, ref_code: str) -> tuple[float, Optional[float]]:
        C_E = 0.04  # エネルギー比率の下限
        if ref_code in self.lower_ref_codes:
            return (self.eer * C_E) / 9 # g単位に変換
        else:
            return None

    def get_n3_fatty_acids(self, ref_code: str) -> tuple[float, Optional[float]]:
        C_E = 0.006  # エネルギー比率の下限
        if ref_code in self.lower_ref_codes:
            if self.eer is not None:
                return (self.eer * C_E) / 9 # g単位に変換
        else:
            return None

    def get_carbohydrate(self, ref_code: str) -> tuple[float, Optional[float]]:
        return None

    def get_nutrient_value_by_ref_code(self, nutrient_id: str, ref_code: str) -> float:
        """
        指定された栄養素の値を取得する
        """
        if nutrient_id == "energy":
            if ref_code in self.lower_ref_codes:
                return self.eer
            else:
                return None
        elif nutrient_id == "protein":
            return self.get_protein(ref_code)
        elif nutrient_id == "saturated_fatty_acids":
            return self.get_saturated_fatty_acids(ref_code)
        elif nutrient_id == "n6_fatty_acids":
            return self.get_n6_fatty_acids(ref_code)
        elif nutrient_id == "n3_fatty_acids":
            return self.get_n3_fatty_acids(ref_code)
        elif nutrient_id == "carbohydrate":
            return self.get_carbohydrate(ref_code)

        value = self.df_values.filter((pl.col("nutrient_id") == nutrient_id) & (pl.col("ref_code") == ref_code))["value"]
        if value.is_empty():
            return None
        return value[0]

    def get_nutrient_value_by_settings(self, nutrient_id: str):
        for lower_method in self.lower_ref_codes:
            lower_value = self.get_nutrient_value_by_ref_code(nutrient_id, lower_method)
            if lower_value is not None:
                break
        for upper_method in self.upper_ref_codes:
            upper_value = self.get_nutrient_value_by_ref_code(nutrient_id, upper_method)
            if upper_value is not None:
                break
        return lower_value, upper_value

    def get_dict_nutrient_value(self):
        all_nutrient_ids = self.MACRONUTRIENTS + self.nutrient_ids
        return {nutrient_id: self.get_nutrient_value_by_settings(nutrient_id) for nutrient_id in all_nutrient_ids}

    def save_to_csv(self, dict_nutrient_value, dict_nutrient_unit, output_path):
        """
        栄養素のデータをpolarsを使ってCSVファイルに保存する関数

        Args:
            dict_nutrient_value (dict): 栄養素のIDをキー、(下限値, 上限値)のタプルを値とする辞書
            dict_nutrient_unit (dict): 栄養素のIDをキー、単位を値とする辞書
            output_path (str): 出力先のCSVファイルパス
        """
        # データをpolars DataFrameに適した形式に変換
        data_for_df = []
        for key, (lower, upper) in dict_nutrient_value.items():
            data_for_df.append({
                "nutrient_id": key,
                "lower": lower,
                "upper": upper,
                "unit": dict_nutrient_unit.get(key, "")
            })

        # DataFrameの作成
        df = pl.DataFrame(data_for_df)

        # CSVファイルへの書き出し
        df.write_csv(output_path)

if __name__ == "__main__":
    # テストコード
    user = UserProfile(sex_code="M", weight=55, height=165, age=23, activity_level=1.75)
    nutrientsCalculator = NutrientsCalculator(user)
    dict_nutrient_value = nutrientsCalculator.get_dict_nutrient_value()
    dict_nutrient_unit = nutrientsCalculator.dict_nutrient_unit
    
    # CSVファイルへの保存
    output_path = "nutrients_polars.csv"
    nutrientsCalculator.save_to_csv(dict_nutrient_value, dict_nutrient_unit, output_path)