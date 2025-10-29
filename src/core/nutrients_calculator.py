from functools import cached_property
from typing import Literal, Optional
from dataclasses import dataclass
import pandas as pd

@dataclass
class UserProfile:
    sex: Literal["M", "F"]  # "male" or "female"
    weight: float  # in kg
    height: float  # in cm
    age: int  # in years
    activity_level: float # low: 1.5, normal: 1.75, high: 2.0
    life_stage: Literal["general", "pregnant_early", "pregnant_mid_late", "lactating"] = "general"

class NutrientsCalculator:
    """
    エネルギー産生栄養素以外の栄養素の必要量計算機
    各メソッドは 下限値, 上限値 のタプルを返す設計とする
    例: return lower_value, upper_value
    """

    AGE_BANDS_PATH = "/app/resources/age_bands.csv"
    VALUES_DIR = "resources/values/"

    def __init__(self, user: UserProfile, lower_methods: list[str] = ["RDA", "AI", "Dg_LOWER", "EAR"], upper_methods: list[str] = ["UL", "DG_UPPER"], eer_method: Literal["harris_benedict", "ganpule"] = "ganpule"):
        self.sex = user.sex
        self.weight = user.weight
        self.height = user.height
        self.age = user.age
        self.activity_level = user.activity_level
        self.life_stage = user.life_stage
        self.lower_methods = lower_methods
        self.upper_methods = upper_methods
        self.eer_method = eer_method

        if self.sex == "M":
            self.sex_id = 0
        elif self.sex == "F":
            self.sex_id = 1


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
        if self.eer_method == "harris_benedict":
            bmr = self._bmr_harris_benedict()
        else:  # デフォルトはganpule
            bmr = self._bmr_ganpule()

        eer = bmr * self.activity_level
        return eer, None

    @cached_property
    def protein(self) -> tuple[float, Optional[float]]:
        C_W = 0.73 # 体重当たりのたんぱく質必要量 (g/kg)
        C_RDA = 1.25 # たんぱく質推奨量の補正係数
        for lower_method in self.lower_methods:
            if lower_method == "RDA":
                return self.weight * C_W * C_RDA, None
            if lower_method == "EAR":
                return self.weight * C_W, None
            
        raise ValueError("対応する下限値算出方法が見つかりません。")
        
    @cached_property
    def saturated_fatty_acids(self) -> tuple[Optional[float], float]:
        C_E = 0.07  # エネルギー比率の上限
        return None, (self.eer[0] * C_E) / 9  # g単位に変換
    
    @cached_property
    def n6_fatty_acids(self) -> tuple[float, Optional[float]]:
        C_E = 0.04  # エネルギー比率の下限
        return (self.eer[0] * C_E) / 9, None  # g単位に変換

    @cached_property
    def n3_fatty_acids(self) -> tuple[float, Optional[float]]:
        C_E = 0.006  # エネルギー比率の下限
        return (self.eer[0] * C_E) / 9, None  # g単位に変換
    
    @cached_property
    def carbohydrate(self) -> tuple[float, Optional[float]]:
        return None, None  # 制約なし

    @cached_property
    def age_band_id(self) -> Optional[int]:
        """ユーザーの年齢からage_band_idを取得する"""
        df_age_bands = pd.read_csv(self.AGE_BANDS_PATH)
        band = df_age_bands[
            (self.age >= df_age_bands["min_age"]) & 
            (self.age < df_age_bands["max_age"])
        ]
        if not band.empty:
            return band.iloc[0]["age_band_id"]
        raise ValueError("対応する年齢帯が見つかりません。")

if __name__ == "__main__":
    # テストコード
    user = UserProfile(sex="M", weight=55, height=165, age=23, activity_level=1.75)
    nutrientsCalculator = NutrientsCalculator(user)
    print("EER:", nutrientsCalculator.eer[0])
    print("Protein:", nutrientsCalculator.protein[0])
