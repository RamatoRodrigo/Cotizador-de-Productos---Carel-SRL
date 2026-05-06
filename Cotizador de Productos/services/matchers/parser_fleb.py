import pandas as pd
import re
import os


# -------------------------
# Helpers
# -------------------------

def normalizar(texto):
    return (
        str(texto)
        .lower()
        .replace(",", ".")
        .replace("  ", " ")
        .strip()
    )

def detectar_tipo(desc):
    """Detecta el tipo de producto basado en la descripción"""
    desc = desc.lower()

    if "tca" in desc:
        return "tuerca"
    if "bulón" in desc or "bulon" in desc:
        return "bulón"
    if "tirafondo" in desc:
        return "tirafondo"
    if "arandela" in desc:
        return "arandela"
    if "punta" in desc:
        return "tornillo"
    if "varilla" in desc:
        return "varilla"
    if "electrodos" in desc:
        return "electrodo"

    return "otro"

import re

def detectar_sistema(desc: str) -> str:
    """Detecta si es métrico, imperial u otro según la descripción"""
    desc = desc.lower()

    # 🔹 Sistema imperial
    # Palabras clave UNC, UNF
    if "unc" in desc or "unf" in desc:
        return "imperial"
    # Fracciones con o sin comillas (1/4, 5/16, 3/8")
    if re.search(r"\d+/\d+(?:\s*\"|)", desc):
        return "imperial"

    # 🔹 Sistema métrico
    # Formato M seguido de número (M6, M8, M10)
    if re.search(r"\bm\d+", desc):
        return "métrico"
    # Números con unidad MM (2.0 MM, 300MM)
    if re.search(r"\d+(?:\.\d+)?\s*mm", desc):
        return "métrico"
    # Números sueltos (ej. "Grower 6", "Arandela 8")
    if re.search(r"\b\d+\b", desc):
        return "métrico"

    # 🔹 Otro
    return "otro"



# -------------------------
# Parseo métrico e imperial
# -------------------------

def parse_metrico(desc: str):
    desc = desc.upper().replace(",", ".")
    
    # Caso M + número (ej: M8 x 20)
    match = re.search(r"\bM(\d+)\s*x\s*(\d+(?:\.\d+)?)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Caso con MM explícito (ej: 2.0 MM X 300MM)
    match = re.search(r"(\d+(?:\.\d+)?)\s*MM\s*x\s*(\d+(?:\.\d+)?)\s*MM", desc)
    if match:
        return match.group(1), None, match.group(2)

    # 🔹 Caso genérico con tres números separados por x (ej: 6 x 1.00 x 100)
    match = re.search(r"(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)\s*x\s*(\d+(?:\.\d+)?)", desc)
    if match:
        return match.group(1), match.group(2), match.group(3)

    # Caso número suelto (ej: Grower 6)
    match = re.search(r"\b(\d+)\b", desc)
    if match:
        return match.group(1), None, None

    return None, None, None



def parse_imperial(desc: str):
    desc = desc.lower().replace(",", ".")
    
    # Caso fracción con paso (ej: 5/16 - 24)
    match = re.search(r"(\d+(?:/\d+)?)\s*-\s*(\d+)", desc)
    if match:
        return match.group(1), match.group(2), None

    # Caso fracción con largo (ej: 1/4 x 1/2)
    match = re.search(r"(\d+(?:/\d+)?)\s*x\s*(\d+(?:/\d+)?)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # 🔹 Nuevo caso: dos fracciones separadas por espacio (ej: 1/4 1/2)
    match = re.search(r"(\d+(?:/\d+)?)\s+(\d+(?:/\d+)?)", desc)
    if match:
        return match.group(1), None, match.group(2)

    return None, None, None




# -------------------------
# Parser principal
# -------------------------

def parse_fleb(input_path, output_path):

    df = pd.read_csv(
        input_path,
        header=None,
        names=["codigo", "descripcion", "precio_unitario", "proveedor"],
        encoding="utf-8"
    )

    resultados = []

    for _, row in df.iterrows():

        desc = normalizar(row["descripcion"])

        tipo = detectar_tipo(desc)
        sistema = detectar_sistema(desc)

        diametro = None
        paso = None
        largo = None

        if sistema == "metrico":
            diametro, paso, largo = parse_metrico(desc)
        else:
            diametro, paso, largo = parse_imperial(desc)

        grado = None

        resultados.append({
            "codigo": row["codigo"],
            "tipo": tipo,
            "diametro": diametro,
            "paso": paso,
            "largo": largo,
            "grado": grado,
            "sistema": sistema,
            "precio_unitario": row["precio_unitario"],
            "proveedor": row["proveedor"],
            "descripcion": row["descripcion"]
        })

    df_out = pd.DataFrame(resultados)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_out.to_csv(output_path, index=False, encoding="utf-8")

    print(f"✅ CSV parseado generado en: {output_path}")
    print(df_out.head())

    return df_out