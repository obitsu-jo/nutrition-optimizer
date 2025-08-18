import pandas as pd

path = "/app/data/raw/20230428-mxt_kagsei-mext_00001_032.xlsx"
df = pd.read_excel(path)
names = pd.Series(df.iloc[2:, 3])
targets = names[names.str.contains("むね")] # とりむね->1582
result = df.iloc[[2, 1581, 1582], [3,  8, 11, 12]]
pd.set_option('display.max_columns', None)  # 全列表示
pd.set_option('display.width', None)        # 幅制限なし
pd.set_option('display.max_colwidth', None) # 列幅制限なし
pd.set_option('display.expand_frame_repr', False)  # 折り返し無効

print(targets)
print()
print(result)