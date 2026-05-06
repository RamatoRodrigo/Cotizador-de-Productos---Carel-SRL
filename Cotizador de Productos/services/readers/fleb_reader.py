import re
import pandas as pd

def read_fleb(file_path):
    df_raw = pd.read_excel(file_path, header=3)

    # Normalizar nombres
    df_raw.columns = (
        df_raw.columns
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Filtrar columnas necesarias
    cols_needed = ["FAMILIA", "CÓDIGO", "PRODUCTO", "$ (UNITARIO)"]
    df = df_raw[[c for c in df_raw.columns if c in cols_needed]].copy()

    # Renombrar
    df = df.rename(columns={
        "FAMILIA": "familia",
        "CÓDIGO": "codigo",
        "PRODUCTO": "producto",
        "$ (UNITARIO)": "precio_unitario"
    })


    print(df_raw.columns)

    df = df.dropna(subset=["codigo", "producto"])
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")

    # 🔍 Regex flexible para medidas
    medida_regex = r"(?:M?\d+(?:\.\d+)?(?:/\d+)?(?:\s*MM)?(?:\s*x\s*\d+(?:\.\d+)?(?:/\d+)?(?:\s*MM)?)*)"

    df["medidas"] = df["producto"].apply(
        lambda x: " ".join(re.findall(medida_regex, str(x).upper()))
    )

    # 🧠 Construir descripción final
    df["descripcion"] = (
        df["familia"].astype(str).str.strip() + " " +
        df["medidas"].astype(str).str.strip() + " "
    ).str.replace(r"\s+", " ", regex=True).str.strip()

    df["proveedor"] = "fleb"

    return df[["codigo", "descripcion", "precio_unitario", "proveedor"]]
