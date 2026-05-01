import pandas as pd
import re

# ---------------------------
# Utilidad
# ---------------------------
def limpiar_codigo(codigo):
    return str(codigo).strip().lstrip(">")


def normalizar(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).upper()
    texto = re.sub(r'[^A-Z0-9 ]', ' ', texto)
    texto = re.sub(r'\s+', ' ', texto).strip()
    return texto

# ---------------------------
# Obtener medida
# ---------------------------

def extraer_medida(texto):
    if texto is None:
        return None
    
    match = re.search(r'\b\d+/\d+\b', str(texto))
    return match.group(0) if match else None

# ---------------------------
# Buscar por código (exacto)
# ---------------------------
def buscar_por_codigo(codigo, path_csv):
    df = pd.read_csv(path_csv)

    codigo_busqueda = limpiar_codigo(codigo)

    resultado = df[
        df["codigo"].apply(lambda x: limpiar_codigo(x) == codigo_busqueda)
    ]

    return resultado


# ---------------------------
# Buscar por descripción
# ---------------------------
def buscar_por_descripcion(texto, path_csv):
    df = pd.read_csv(path_csv)

    texto_norm = normalizar(texto)
    medida_busqueda = extraer_medida(texto)

    resultados = df[
        df["descripcion_original"].apply(
            lambda x: all(p in normalizar(x) for p in texto_norm.split())
        )
    ]

    # Filtro de medida
    if medida_busqueda:
        resultados = resultados[
            resultados["descripcion_original"].apply(
                lambda x: medida_busqueda in str(x)
            )
        ]

    return resultados


# ---------------------------
# Búsqueda combinada (opcional)
# ---------------------------
def buscar_general(query, path_csv):
    # si parece código → buscar por código
    if any(char.isdigit() for char in query) and len(query) > 5:
        return buscar_por_codigo(query, path_csv)
    else:
        return buscar_por_descripcion(query, path_csv)