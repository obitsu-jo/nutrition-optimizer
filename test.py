import pandas as pd

path = "/app/data/raw/20230428-mxt_kagsei-mext_00001_032.xlsx"
df = pd.read_excel(path)

# 表示オプションを設定して折り返しを防ぐ
pd.set_option('display.max_columns', None)  # 全列表示
pd.set_option('display.width', None)        # 幅制限なし
pd.set_option('display.max_colwidth', None) # 列幅制限なし
pd.set_option('display.expand_frame_repr', False)  # 折り返し無効

print(df.iloc[:10, :10])