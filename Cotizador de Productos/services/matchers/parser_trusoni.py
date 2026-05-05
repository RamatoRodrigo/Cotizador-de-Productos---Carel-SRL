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
    if "allen" in desc:
        return "allen"
    return "otro"


def detectar_sistema(desc):
    if "/" in desc or "-" in desc:
        return "imperial"
    return "metrico"


# -------------------------
# Parseo métrico
# -------------------------

def parse_metrico(desc):
    match = re.search(r"(\d+)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+)", desc)
    if match:
        return match.group(1), match.group(2), match.group(3)
    return None, None, None


# -------------------------
# Parseo imperial
# -------------------------

def parse_imperial(desc):
    desc = desc.lower().replace(",", ".")

    match = re.search(
        r"(\d+(?:/\d+)?)\s*-\s*(\d+)\s*x\s*(\d+(?:/\d+)?)",
        desc
    )

    if match:
        diametro = match.group(1)
        paso = match.group(2)
        largo = match.group(3)
        return diametro, paso, largo

    return None, None, None


# -------------------------
# Extraer grado
# -------------------------

def extraer_grado(desc):
    match = re.search(r"(8\.8|10\.9|12\.9)", desc)
    return match.group(1) if match else None


# -------------------------
# Parser principal
# -------------------------

def parse_trusoni(input_path, output_path):

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

        grado = extraer_grado(desc)

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