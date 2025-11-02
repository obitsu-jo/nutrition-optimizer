from functools import cached_property
from typing import Literal, Optional
from dataclasses import dataclass
import polars as pl
import json

@dataclass
class UserProfile:
    sex_code: Literal["M", "F"]  # "male" or "female"
    weight: float  # in kg
    height: float  # in cm
    age: int  # in years
    activity_level: float # low: 1.5, normal: 1.75, high: 2.0
    life_code: Literal["general", "pregnant_early", "pregnant_mid_late", "lactating"] = "general"

class NutrientsCalculator:
    EER_METHOD = "ganpule" # "harris_benedict" or "ganpule"

    AGE_BANDS_PATH = "/app/resources/step1/age_bands.csv"
    REF_TYPES_PATH = "/app/resources/step1/ref_types.csv"
    NUTRIENT_IDS_PATH = "/app/resources/nutrient_ids.csv"
    VALUES_DIR = "resources/step1/values/"
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
                df_tmp = df_tmp.filter(pl.col("life_code").is_in([self.life_code, "general"]))
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

        value = self.df_values.filter((pl.col("nutrient_id") == nutrient_id) & (pl.col("ref_code") == ref_code) & (pl.col("life_code") == self.life_code))["value"]
        if value.is_empty():
            value = self.df_values.filter((pl.col("nutrient_id") == nutrient_id) & (pl.col("ref_code") == ref_code) & (pl.col("life_code") == "general"))["value"]
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

    @cached_property
    def dict_nutrient_value(self):
        all_nutrient_ids = self.nutrient_ids
        return {nutrient_id: self.get_nutrient_value_by_settings(nutrient_id) for nutrient_id in all_nutrient_ids}

    def save_nutrient_values_to_csv(self, output_path: str, dict_nutrient_value: dict[str, tuple[Optional[float], Optional[float]]] = None, dict_nutrient_unit: dict[str, str] = None):
        if dict_nutrient_value is None:
            dict_nutrient_value = self.dict_nutrient_value
        if dict_nutrient_unit is None:
            dict_nutrient_unit = self.dict_nutrient_unit
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

    def save_user_profile_to_json(self, output_path: str):
        data = {
            "sex_code": self.sex_code,
            "weight": self.weight,
            "height": self.height,
            "age": self.age,
            "activity_level": self.activity_level,
            "life_code": self.life_code
        }
        with open(output_path, "w") as f:
            json.dump(data, f)

if __name__ == "__main__":
    # テストコード
    user = UserProfile(sex_code="F", weight=55, height=165, age=27, activity_level=1.75, life_code="pregnant_mid_late")
    nutrientsCalculator = NutrientsCalculator(user)
    nutrientsCalculator.save_nutrient_values_to_csv("test_nutrient_values.csv")