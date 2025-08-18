"""
栄養成分のマッピング定義
"""

# 栄養成分のマッピング（列インデックス -> [日本語名, 英語識別子, 単位]）
NUTRITION_MAPPING = {
    3: ["食品名", "food_name", ""],
    4: ["廃棄率", "refuse", "%"],
    5: ["エネルギー_kJ", "energy_kj", "kJ"],
    6: ["エネルギー_kcal", "energy_kcal", "kcal"],
    7: ["水分", "water", "g"],
    8: ["たんぱく質_アミノ酸組成", "protein_amino", "g"],
    9: ["たんぱく質", "protein", "g"],
    10: ["脂質_脂肪酸組成", "fat_fatty_acid", "g"],
    11: ["コレステロール", "cholesterol", "mg"],
    12: ["脂質", "fat", "g"],
    13: ["炭水化物_利用可能", "carb_available_mono", "g"],
    15: ["炭水化物_利用可能_合計", "carb_available", "g"],
    16: ["食物繊維_不溶性", "fiber_insoluble", "g"],
    18: ["食物繊維_総量", "fiber_total", "g"],
    19: ["ポリフェノール", "polyphenol", "mg"],
    20: ["炭水化物_差し引き", "carb_diff", "g"],
    21: ["有機酸", "organic_acid", "g"],
    22: ["灰分", "ash", "g"],
    24: ["カリウム", "potassium", "mg"],
    25: ["カルシウム", "calcium", "mg"],
    26: ["マグネシウム", "magnesium", "mg"],
    27: ["リン", "phosphorus", "mg"],
    28: ["鉄", "iron", "mg"],
    29: ["亜鉛", "zinc", "mg"],
    30: ["銅", "copper", "mg"],
    31: ["マンガン", "manganese", "mg"],
    33: ["ヨウ素", "iodine", "μg"],
    34: ["セレン", "selenium", "μg"],
    35: ["クロム", "chromium", "μg"],
    36: ["モリブデン", "molybdenum", "μg"],
    37: ["レチノール", "retinol", "μg"],
    38: ["α-カロテン", "alpha_carotene", "μg"],
    39: ["β-カロテン", "beta_carotene", "μg"],
    40: ["β-クリプトキサンチン", "beta_cryptoxanthin", "μg"],
    41: ["β-カロテン当量", "beta_carotene_equiv", "μg"],
    42: ["レチノール活性当量", "retinol_activity_equiv", "μg"],
    43: ["ビタミンD", "vitamin_d", "μg"],
    44: ["α-トコフェロール", "alpha_tocopherol", "mg"],
    45: ["β-トコフェロール", "beta_tocopherol", "mg"],
    46: ["γ-トコフェロール", "gamma_tocopherol", "mg"],
    47: ["δ-トコフェロール", "delta_tocopherol", "mg"],
    48: ["ビタミンK", "vitamin_k", "μg"],
    49: ["チアミン", "thiamin", "mg"],
    50: ["リボフラビン", "riboflavin", "mg"],
    51: ["ナイアシン", "niacin", "mg"],
    52: ["ナイアシン当量", "niacin_equiv", "mg"],
    53: ["ビタミンB6", "vitamin_b6", "mg"],
    54: ["ビタミンB12", "vitamin_b12", "μg"],
    55: ["葉酸", "folate", "μg"],
    56: ["パントテン酸", "pantothenic_acid", "mg"],
    57: ["ビオチン", "biotin", "μg"],
    58: ["ビタミンC", "vitamin_c", "mg"],
    59: ["アルコール", "alcohol", "g"],
    60: ["食塩相当量", "salt_equiv", "g"]
}

# よく使われる栄養素のグループ
MACRONUTRIENTS = ["protein", "fat", "carb_available", "fiber_total"]
MINERALS = ["potassium", "calcium", "magnesium", "phosphorus", "iron", "zinc"]
VITAMINS = [
    "retinol_activity_equiv", "vitamin_d", "alpha_tocopherol", "vitamin_k",
    "thiamin", "riboflavin", "niacin", "vitamin_b6", "vitamin_b12", 
    "folate", "pantothenic_acid", "vitamin_c"
]

def get_column_name(col_index):
    """列インデックスから栄養成分名（英語）を取得"""
    if col_index in NUTRITION_MAPPING:
        return NUTRITION_MAPPING[col_index][1]
    return f"col_{col_index}"

def get_japanese_name(col_index):
    """列インデックスから栄養成分名（日本語）を取得"""
    if col_index in NUTRITION_MAPPING:
        return NUTRITION_MAPPING[col_index][0]
    return f"列{col_index}"

def get_unit(col_index):
    """列インデックスから単位を取得"""
    if col_index in NUTRITION_MAPPING:
        return NUTRITION_MAPPING[col_index][2]
    return ""