import pandas as pd
import re

def read_fleb(file_path):
    # Leer hoja 1 y hoja 2
    df1 = pd.read_excel(file_path, sheet_name=0, header=3)
    df2 = pd.read_excel(file_path, sheet_name=1, header=3)

    # Normalizar nombres en ambas
    def normalize_cols(df):
        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
            .str.replace(r"\s+", " ", regex=True)
        )
        return df

    df1 = normalize_cols(df1)
    df2 = normalize_cols(df2)

    # Filtrar columnas necesarias
    cols_needed1 = ["FAMILIA", "CÓDIGO", "PRODUCTO", "$ (UNITARIO)"]
    cols_needed2 = ["CÓDIGO", "$ (UNITARIO)"]  # ejemplo: columna distinta en hoja 2

    df1 = df1[[c for c in df1.columns if c in cols_needed1]].copy()
    df2 = df2[[c for c in df2.columns if c in cols_needed2]].copy()

    # Renombrar
    df1 = df1.rename(columns={
        "FAMILIA": "familia",
        "CÓDIGO": "codigo",
        "PRODUCTO": "producto",
        "$ (UNITARIO)": "precio_granel"
    })
    df2 = df2.rename(columns={
        "CÓDIGO": "codigo",
        "$ (UNITARIO)": "precio_fraccionado"
    })

    # Merge por código (o por índice si están en el mismo orden)
    df = pd.merge(df1, df2, on="codigo", how="inner")

    # Limpiar
    df = df.dropna(subset=["codigo", "producto"])
    df["precio_granel"] = pd.to_numeric(df["precio_granel"], errors="coerce")
    df["precio_fraccionado"] = pd.to_numeric(df["precio_fraccionado"], errors="coerce")

    # Regex flexible para medidas
    medida_regex = r"(?:M?\d+(?:\.\d+)?(?:/\d+)?(?:\s*MM)?(?:\s*x\s*\d+(?:\.\d+)?(?:/\d+)?(?:\s*MM)?)*)"
    df["medidas"] = df["producto"].apply(
        lambda x: " ".join(re.findall(medida_regex, str(x).upper()))
    )

    # Descripción final
    df["descripcion"] = (
        df["familia"].astype(str).str.strip() + " " +
        df["medidas"].astype(str).str.strip() + " "
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    df["proveedor"] = "fleb"

    return df[["codigo", "descripcion", "precio_granel", "precio_fraccionado", "proveedor"]]
