import pandas as pd
import os
import re
from rapidfuzz import fuzz


# -------------------------
# Helpers
# -------------------------

def normalizar(texto):
    return (
        str(texto)
        .lower()
        .replace(",", ".")
        .replace("-", " ")
        .replace("x", " x ")
        .replace("  ", " ")
        .strip()
    )

def extraer_medidas(desc):
    desc = desc.lower().replace(",", ".")
    
    # formato tipo: 8 x 1.25 x 35
    match = re.search(r"(\d+)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+)", desc)
    if match:
        return match.group(1), match.group(3)

    # formato tipo: m8-1.25-35
    match = re.search(r"m\s*(\d+)[-x](\d+\.?\d*)[-x](\d+)", desc)
    if match:
        return match.group(1), match.group(3)

    return None, None


def tipo_producto(desc):
    desc = desc.lower()

    if "allen" in desc:
        return "allen"
    if "hexagonal" in desc or "bulon" in desc:
        return "hexagonal"

    return "otro"


def es_imperial(desc):
    desc = desc.lower()
    return "unc" in desc or "/" in desc


# -------------------------
# Matching principal
# -------------------------

def match_trusoni_vs_carel(trusoni_path, carel_path, output_path):

    df_trusoni = pd.read_csv(trusoni_path)
    df_carel = pd.read_csv(carel_path, encoding="utf-8")

    # 🔥 normalizar nombres de columnas
    df_carel.columns = df_carel.columns.str.strip().str.lower()

    # Normalizar
    df_trusoni["desc_norm"] = df_trusoni["descripcion"].apply(normalizar)
    df_carel["desc_norm"] = df_carel["descripcion"].apply(normalizar)

    df_trusoni["diametro"], df_trusoni["largo"] = zip(*df_trusoni["desc_norm"].apply(extraer_medidas))
    df_carel["diametro"], df_carel["largo"] = zip(*df_carel["desc_norm"].apply(extraer_medidas))

    # Tipo
    df_trusoni["tipo"] = df_trusoni["desc_norm"].apply(tipo_producto)
    df_carel["tipo"] = df_carel["desc_norm"].apply(tipo_producto)

    resultados = []

    for _, carel_row in df_carel.iterrows():

        desc_carel = carel_row["desc_norm"]

        tipo_carel = carel_row["tipo"]

        # Filtrar candidatos por tipo
        candidatos = df_trusoni.copy()

        # filtrar por diámetro si existe
        if carel_row["diametro"]:
            candidatos = candidatos[candidatos["diametro"] == carel_row["diametro"]]

        # filtrar por largo si existe
        if carel_row["largo"]:
            candidatos = candidatos[candidatos["largo"] == carel_row["largo"]]

        # fallback si se queda vacío
        if candidatos.empty:
            candidatos = df_trusoni

        if candidatos.empty:
            continue

        best_score = 0
        best_match = None

        for _, tr_row in candidatos.iterrows():
            score = fuzz.token_set_ratio(desc_carel, tr_row["desc_norm"])

            if score > best_score:
                best_score = score
                best_match = tr_row

        # umbral mínimo (ajustable)
        if best_match is not None and best_score > 60:
            resultados.append({
                "id_carel": carel_row["codigo"] if "codigo" in carel_row else carel_row.iloc[0],
                "descripcion_carel": carel_row["descripcion"],
                "codigo_trusoni": best_match["codigo"],
                "descripcion_trusoni": best_match["descripcion"],
                "precio_unitario": best_match["precio_unitario"],
                "score": best_score
            })

    df_result = pd.DataFrame(resultados)

    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    df_result.to_csv(output_path, index=False, encoding="utf-8")

    print(f"✅ Matches generados en: {output_path}")
    print(df_result.head())

    return df_result