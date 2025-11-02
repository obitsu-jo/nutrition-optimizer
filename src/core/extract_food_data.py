import polars as pl

if __name__ == "__main__":
    FUNDAMENTAL_DATA_PATH = "/app/resources/step2/raw/20230428-mxt_kagsei-mext_00001_012.csv"
    FAT_DATA_PATH = "/app/resources/step2/raw/20230428-mxt_kagsei-mext_00001_032.csv"
    NUTRIENT_IDS_PATH = "/app/resources/nutrient_ids.csv"
    FOOD_NUTRIENT_DATA_PATH = "/app/resources/step2/template/food_nutrient_data.csv"


    df_fundamental = pl.read_csv(FUNDAMENTAL_DATA_PATH)
    units_fundamental = df_fundamental[0]
    labels_fundamental = df_fundamental.columns[1:]
    df_fundamental = df_fundamental[1:]
    df_fundamental = df_fundamental.with_columns(
        pl.col(labels_fundamental).cast(pl.Utf8)
        .str.replace_all(r"\(|\)", "")
        .str.replace_all("Tr", "")
        .str.replace_all(" ", "")
        .str.replace_all("†", "")
        .str.replace_all(r"\*", "")
        .str.replace_all("-", "")
        .cast(pl.Float64, strict=False)
        .fill_null(0)
    )
    df_fat = pl.read_csv(FAT_DATA_PATH)
    labels_fat = df_fat.columns[1:]
    df_fat = df_fat[1:]
    df_fat = df_fat.with_columns(
        pl.col(labels_fat).cast(pl.Utf8)
        .str.replace_all(r"\(|\)", "")
        .str.replace_all("Tr", "")
        .str.replace_all(" ", "")
        .str.replace_all("†", "")
        .str.replace_all(r"\*", "")
        .str.replace_all("-", "")
        .cast(pl.Float64, strict=False)
        .fill_null(0)
    )

    df_nutrient_ids = pl.read_csv(NUTRIENT_IDS_PATH)

    nutrient_ids = df_nutrient_ids["nutrient_id"].to_list()
    nutrient_names = df_nutrient_ids["nutrient_name"].to_list()
    nutrient_units = df_nutrient_ids["unit"].to_list()

    rename_map = dict(zip(nutrient_names, nutrient_ids))

    # df_fundamentalとdf_fatを食品名で結合
    df_merged = df_fundamental.join(df_fat, on="食品名", how="inner", suffix="_fat")
    df_final = df_merged.select(
    [pl.col("食品名").alias("food_name")] +
    [pl.col(name).alias(rename_map.get(name, name)) for name in nutrient_names]
    )

    # このデータはすべて100gあたりの値なので、quantityとunitの列を追加
    quantity_col = pl.lit(100).alias("quantity")
    unit_col = pl.lit("g").alias("unit")
    df_final = df_final.with_columns([quantity_col, unit_col])

    # 値段は空欄で追加
    price_col = pl.lit(None).cast(pl.Float64).alias("price")
    df_final = df_final.with_columns([price_col])

    df_final.write_csv(FOOD_NUTRIENT_DATA_PATH)
    print("食品栄養データの抽出と保存が完了しました。")
