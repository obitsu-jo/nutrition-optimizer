import pandas as pd

main_path = "/app/data/raw/20230428-mxt_kagsei-mext_00001_012.xlsx"
fat_path = "/app/data/raw/20230428-mxt_kagsei-mext_00001_032.xlsx"
#main_df = pd.read_excel(main_path, sheet_name=0, skiprows=2)

#print(main_df.iloc[8, :].to_list())
#print(main_df.iloc[9, :].to_list())

fat_df = pd.read_excel(fat_path, sheet_name=0, skiprows=2)
print(fat_df.iloc[1, :].to_list())