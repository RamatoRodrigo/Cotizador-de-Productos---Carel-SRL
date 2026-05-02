import pandas as pd
import re
from difflib import SequenceMatcher
from difflib import get_close_matches


# ---------------------------
# Normalizar texto
# ---------------------------
def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper()
    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

# ---------------------------
# Detectar el tipo de medida
# ---------------------------
def detectar_tipo_medida(texto):
    texto = str(texto).upper()

    if re.search(r'\b\d+\s*x\s*\d+\b', texto):
        return "MM_LARGO"

    if re.search(r'\bM\d+\b', texto):
        return "METRICO"

    if re.search(r'\b\d+/\d+\b', texto):
        return "IMPERIAL"

    return "OTRO"


# ---------------------------
# Extraer medida segun Tipo
# ---------------------------
def extraer_medida(texto):
    texto = str(texto).upper()

    # 1. imperial
    match = re.search(r'\b\d+/\d+\b', texto)
    if match:
        return match.group(0)

    # 2. métrico
    match = re.search(r'\bM\d+\b', texto)
    if match:
        return match.group(0)

    # 3. tipo 6 x 120
    match = re.search(r'\b\d+\s*x\s*\d+\b', texto)
    if match:
        return match.group(0)

    return None


# ---------------------------
# Detectar tipo de producto
# ---------------------------
def detectar_tipo_producto(texto):
    texto = str(texto).upper()

    if "BULON" in texto:
        return "BULON"

    if "VARILLA" in texto:
        return "VARILLA"

    if "TORNILLO" in texto or "TOR " in texto:
        return "TORNILLO"

    # 🔥 solo TUERCA si NO es "SIN TUERCA"
    if "TUERCA" in texto and "SIN TUERCA" not in texto:
        return "TUERCA"

    return "OTRO"

# ---------------------------
# Buscar mejor match
# ---------------------------
def similitud(a, b):
    return SequenceMatcher(None, a, b).ratio()


def mejor_match(descripcion, lista_descripciones, umbral=0.65):
    desc_norm = normalizar(descripcion)

    tipo_producto = detectar_tipo_producto(descripcion)
    tipo_medida = detectar_tipo_medida(descripcion)

    mejor_candidato = None
    mejor_score = 0

    for candidato in lista_descripciones:
        candidato_norm = normalizar(candidato)

        # filtro por tipo producto
        if detectar_tipo_producto(candidato) != tipo_producto:
            continue

        # filtro por tipo medida
        if detectar_tipo_medida(candidato) != tipo_medida:
            continue

        score = similitud(desc_norm, candidato_norm)

        # opcional: boost por misma medida
        if extraer_medida(descripcion) == extraer_medida(candidato):
            score += 0.1

        if score > mejor_score:
            mejor_score = score
            mejor_candidato = candidato

    if mejor_score >= umbral:
        return mejor_candidato, round(mejor_score, 3)

    return None, 0




# ---------------------------
# Generar mapeo completo
# ---------------------------
def generar_mapeo(path_productos, path_borroni, output_path):
    print("📥 Cargando archivos...")

    df_productos = pd.read_csv(
        path_productos,
        header=None,
        encoding="latin1"
    )
    df_borroni = pd.read_csv(path_borroni)

    lista_borroni = df_borroni.iloc[:, 0].tolist()

    resultados = []

    print("🔍 Generando mapeo...")

    for _, row in df_productos.iterrows():
        codigo = str(row[0]).strip()
        descripcion = row[1]

        if pd.isna(descripcion):
            descripcion = ""

        match, score = mejor_match(descripcion, lista_borroni)

        resultados.append({
            "codigo": codigo,
            "descripcion_original": descripcion,
            "descripcion_borroni": match if match else "",
            "score": score,
            "estado": "MATCH" if match else "SIN_MATCH"
        })

    df_final = pd.DataFrame(resultados)

    print("💾 Guardando resultado...")
    df_final.to_csv(output_path, index=False)

    print("✅ Mapeo generado correctamente")
    return df_final

# ---------------------------
# Buscar por código
# ---------------------------
def buscar_por_codigo(codigo, path_mapeo):
    df = pd.read_csv(path_mapeo)

    codigo = codigo.lstrip(">")

    resultado = df[df["codigo"] == codigo]

    if resultado.empty:
        print("❌ No se encontró el código")
    else:
        print("✅ Resultado encontrado:")
        print(resultado)

    return resultado
