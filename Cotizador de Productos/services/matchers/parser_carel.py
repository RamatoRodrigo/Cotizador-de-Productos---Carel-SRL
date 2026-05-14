import pandas as pd
import re
import os
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -------------------------
# Helpers
# -------------------------

def normalizar(texto):
    """Normaliza texto para búsquedas"""
    return (
        str(texto)
        .lower()
        .replace(",", ".")
        .replace("(", " ")
        .replace(")", " ")
        .strip()
    )


def limpiar_codigo(codigo):
    """Limpia caracteres especiales del código"""
    return str(codigo).replace(">", "").strip()


def detectar_tipo(desc):
    """Detecta el tipo de producto basado en la descripción"""
    desc = desc.lower()

    # FIX: clavo duplicado removido (el segundo nunca se ejecutaba)
    if (
        "clavo" in desc or
        "clavos" in desc or
        "punta paris" in desc or
        "cabeza perdida" in desc or
        "cabeza chata" in desc or
        "cajonero" in desc
    ):
        return "clavo"
    if "drywall" in desc or "dry wall" in desc:
        return "tornillo_drywall"
    if "p/mad" in desc or "fix" in desc:
        return "tornillo_fix"
    if "bul" in desc or "bulón" in desc or "bulon" in desc:
        return "bulón"
    if "tuerca" in desc:
        return "tuerca"
    # FIX: "tor" reemplazado por \btor para evitar match en "motor", "doctor", etc.
    if re.search(r"\btor", desc) or "tornillo" in desc or "cabeza tanque" in desc:
        return "tornillo"
    if "pris" in desc or "prisionero" in desc:
        return "prisionero"
    if "tirafondo" in desc:
        return "tirafondo"
    if "arandela" in desc:
        return "arandela"
    if "espárrago" in desc or "esparrago" in desc:
        return "espárrago"
    if "perno" in desc:
        return "perno"
    if "varilla" in desc:
        return "varilla"
    if "remache" in desc:
        return "remache"
    if "pasador" in desc:
        return "pasador"
    if "chaveta" in desc:
        return "chaveta"
    if "tarugo" in desc:
        return "tarugo"
    if "abrazadera" in desc:
        return "abrazadera"
    if "grampyta" in desc or "pytones" in desc:
        return "grampas"
    if "pytones" in desc:
        return "pitones"

    return "otro"


def detectar_forma(desc):
    """Detecta la forma del producto (hexagonal, autofrenante, etc.)"""
    desc = desc.lower()

    formas = {
        'hexagonal': ['hexagonal', 'hex', 'hex.'],
        'autofrenante': ['autofr', 'autofrenante', 'autofren'],
        'allen': ['allen', 'allen cab', 'allen s/', 'allen s/c'],
        'mariposa': ['mariposa', 'butterfly'],
        'almenada': ['almenada', 'castillo'],
        'grower': ['grower'],
        'plana': ['plana', 'flat'],
        'fresada': ['fresada', 'fresa', 'countersunk'],
        'phillips': ['phillips', 'phil', 'cruz'],
        'pozi': ['pozi', 'pozidrive'],
        'redonda': ['redonda', 'round'],
        'cuadrada': ['cuadrada', 'square', 'c/cuad'],
        'pytones abiertos' : ['pytones abiertos', 'pyton abierto', 'pytones abierto'],
        'pytones cerrados' : ['pytones cerrados', 'pyton cerrado', 'pytones cerrad'],
        'pytones escuadra' : ['pytones escuadra'],
    }

    for forma, keywords in formas.items():
        for keyword in keywords:
            if keyword in desc:
                return forma

    return None


def detectar_acabado(desc):
    """Detecta el acabado/recubrimiento del producto"""
    desc = desc.lower()

    acabados = {
        'zinc': ['zinc', 'zincado', 'zincada'],
        'natural': ['nat', 'natural'],
        'bronce': ['bronce'],
        'niquelado': ['niquelado', 'niquel'],
        'cromado': ['cromado', 'cromo'],
        'dicro': ['dicro', 'dicromado'],
        'fosforado': ['fosf', 'fosforado'],
        'acero_inox': ['inox', 'acero inoxidable', 'stainless'],
    }

    for acabado, keywords in acabados.items():
        for keyword in keywords:
            if keyword in desc:
                return acabado

    return None


def detectar_sistema_rosca(desc):
    """Detecta el sistema de rosca (UNC, UNF, BSW, ISO, NC, etc.)"""
    desc = desc.lower()

    # FIX: usar \b para evitar falsos positivos ("nf" dentro de "infierno", etc.)
    sistemas = {
        'UNC': r'\bunc\b',
        'UNF': r'\bunf\b',
        'BSW': r'\bbsw\b',
        'BSP': r'\bbsp\b',
        'ISO': r'\biso\b',
        'NC':  r'\bnc\b',
        'NF':  r'\bnf\b',
        'WH':  r'\bwh\b',
        'METRICA': r'\bm[eé]tric[ao]\b',
        'WHITWORTH': r'\bwhitworth\b',
    }

    for nombre, patron in sistemas.items():
        if re.search(patron, desc):
            return nombre

    return None


def detectar_sistema(desc):
    """Detecta si es métrico o imperial"""
    desc = desc.lower()

    # Métrico primero: M8, M10, M12, etc.
    # Tiene prioridad porque "M12-1,75 ZINC" también tiene "nc" dentro de "zinc"
    if re.search(r"\bm\d+", desc):
        return "métrico"

    # Formato "número x número" sin barra → métrico
    if re.search(r"^\s*\d+\s*x\s*\d+", desc):
        return "métrico"

    # Usar \b (word boundary) para evitar falsos positivos
    if (re.search(r"\bunc\b", desc)
            or re.search(r"\bunf\b", desc)
            or re.search(r"\bbsw\b", desc)
            or re.search(r"\bnc\b", desc)
            or re.search(r"\bnf\b", desc)
            or re.search(r"\bwhitworth\b", desc)
            or re.search(r"\bwh\b", desc)
            or re.search(r"\d+/\d+", desc)):
        return "imperial"

    return "otro"


def detectar_grado(desc):
    """Detecta el grado de resistencia (8.8, 10.9, G2, G10, etc.)"""
    desc = desc.lower()

    # Grados alfanuméricos: G2, G5, G10, etc.
    match = re.search(r"\bg(\d+)\b", desc)
    if match:
        return f"G{match.group(1)}"

    # Grados numéricos: 8.8, 10.9, 12.9, etc.
    match = re.search(r"(\d+\.?\d*)\s*(?:grado|gr\.?|clase)", desc)
    if match:
        return match.group(1)

    # Búsqueda directa de patrones comunes
    grados = ["12.9", "10.9", "8.8", "5.8", "4.8", "4.6"]
    for grado in grados:
        if grado in desc:
            return grado

    return None


# -------------------------
# Parseo métrico
# -------------------------

import re

def parse_metrico(desc):
    """
    Parsea especificaciones métricas

    Ejemplos:
    M8x1.25
    M10-1.5
    M12x1.75
    M24-3-200
    M10-1,25-20
    M6x45
    M6 x 45
    4x30
    8x1.25x50
    6x25
    """

    desc_norm = normalizar(desc)

    diametro = None
    paso = None
    largo = None

    # =====================================================
    # M24-3-200 / M10-1,25-20
    # =====================================================

    match = re.search(
        r"m\s*(\d+)\s*[-x]\s*(\d+(?:[.,]\d+)?)\s*[-x]\s*(\d+)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = f"M{match.group(1)}"
        paso = match.group(2).replace(",", ".")
        largo = match.group(3)

        return diametro, paso, largo

    # =====================================================
    # M6x45 / M6 x 45
    # =====================================================

    match = re.search(
        r"m\s*(\d+)\s*x\s*(\d+)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = f"M{match.group(1)}"
        largo = match.group(2)

        return diametro, paso, largo

    # =====================================================
    # M8x1.25 o M8-1.25
    # =====================================================

    match = re.search(
        r"m\s*(\d+)\s*[-x]\s*(\d+(?:[.,]\d+)?)",
        desc_norm,
        re.IGNORECASE
    )

    if match:

        posible = float(match.group(2).replace(",", "."))

        # Si el segundo número es chico -> paso
        # Si es grande -> probablemente largo
        if posible < 5:
            diametro = f"M{match.group(1)}"
            paso = str(posible)

            return diametro, paso, largo

    # =====================================================
    # Solo M8 (sin paso)
    # =====================================================

    match = re.search(
        r"m\s*(\d+)(?:\s|$|[^\d])",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = f"M{match.group(1)}"

        return diametro, None, largo

    # =====================================================
    # 8x1.25x50
    # =====================================================

    match = re.search(
        r"(\d+)\s*x\s*(\d+(?:[.,]\d+)?)\s*x\s*(\d+(?:[.,]\d+)?)",
        desc_norm,
        re.IGNORECASE
    )

    if match:

        num1 = int(match.group(1))
        num2 = float(match.group(2).replace(",", "."))
        num3 = float(match.group(3).replace(",", "."))

        if num1 < 30:

            diametro = str(num1)

            if num2 < 5:
                paso = str(num2)
                largo = str(int(num3))
            else:
                paso = None
                largo = str(int(num2))

            return diametro, paso, largo

    # =====================================================
    # 4x30
    # =====================================================

    match = re.search(
        r"(\d+)\s*x\s*(\d+(?:[.,]\d+)?)",
        desc_norm,
        re.IGNORECASE
    )

    if match:

        num1 = int(match.group(1))
        num2 = float(match.group(2).replace(",", "."))

        if num1 < 30:

            if num2 < 5:
                diametro = str(num1)
                paso = str(num2)
            else:
                diametro = str(num1)
                largo = str(int(num2))

            return diametro, paso, largo

    return None, None, None


# -------------------------
# Parseo imperial
# -------------------------

def parse_imperial(desc):
    """
    Parsea especificaciones imperiales

    Ejemplos:
    1/4"-20
    5/16"UNC(32)
    3/8 x 2
    1.1/2-UNF(12)
    1/4-NC-1/2
    9/16-UNC-3
    3/8-UNF-7/8
    1/8-UNC(40)
    1 1/2-UNC(6)
    1 NAT

    Retorna:
    (diametro, paso, largo)
    """

    desc_norm = normalizar(desc)

    diametro = None
    paso = None
    largo = None

    # =====================================================
    # PATRON DE DIAMETRO
    #
    # Soporta:
    #   1 1/2
    #   1.1/2
    #   1/2
    #   1
    #
    # IMPORTANTE:
    # No permite capturar números pegados a letras
    # como G2, A2, CL8, etc.
    # =====================================================

    DIAM_PATTERN = r"(\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+|\d+)"

    PREFIX = r"(?<![a-z0-9])"

    # =====================================================
    # PATRON:
    # 1 1/2-UNC(6)
    # 9/16-UNC(12)
    # 5/16-UNF(24)
    # 1/8-UNC(40)
    #
    # El valor entre paréntesis es paso (TPI)
    # =====================================================

    match = re.search(
        PREFIX +
        DIAM_PATTERN +
        r"\s*[-]?\s*(?:unc|unf|nc|nf|wh)\s*\((\d+)\)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = match.group(1).strip()
        paso = match.group(2)
        return diametro, paso, largo

    # =====================================================
    # PATRON:
    # 9/16-UNC-3
    # 3/8-UNF-7/8
    # 1/4-NC-1/2
    #
    # El último valor es largo
    # =====================================================

    match = re.search(
        PREFIX +
        DIAM_PATTERN +
        r"\s*[-]\s*(?:unc|unf|nc|nf|wh)\s*[-]\s*"
        r"(\d+(?:\s+\d+/\d+|[.,]\d+/\d+|/\d+)?)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = match.group(1).strip()
        largo = match.group(2).strip()
        return diametro, paso, largo

    # =====================================================
    # PATRON:
    # 1/4-20
    # 3/8-16
    #
    # El segundo valor es paso
    # =====================================================

    match = re.search(
        PREFIX +
        r"(\d+(?:\.\d+)?/\d+)\s*[-]\s*(\d+)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = match.group(1).strip()
        paso = match.group(2).strip()
        return diametro, paso, largo

    # =====================================================
    # DIAMETRO + TIPO ROSCA
    #
    # Busca:
    # 1 1/2-UNC
    # 1/2-NC
    # 3/8 UNF
    #
    # Evita:
    # G2 1/2-UNC
    # A2-70
    # =====================================================

    match = re.search(
        PREFIX +
        DIAM_PATTERN +
        r"\s*[-]?\s*(?:unc|unf|nc|nf|wh)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        diametro = match.group(1).strip()

    # =====================================================
    # PATRON:
    # x 2
    # x 7/8
    # x 1 1/2
    # x 1.1/2
    #
    # Busca largo
    # =====================================================

    match = re.search(
        r"x\s*(\d+(?:\s+\d+/\d+|[.,]\d+/\d+|/\d+)?)",
        desc_norm,
        re.IGNORECASE
    )

    if match:
        largo = match.group(1).strip()

    # =====================================================
    # FALLBACK: diámetro sin rosca
    #
    # Casos:
    # ARANDELA GROWER 1 NAT
    # ARANDELA GROWER 1/8 NAT
    #
    # Evita:
    # códigos grandes
    # grados tipo G2
    # =====================================================

    if not diametro:

        for m in re.finditer(PREFIX + DIAM_PATTERN, desc_norm, re.IGNORECASE):

            candidato = m.group(1).strip()

            # Evita números grandes de códigos
            try:
                if "/" not in candidato and int(candidato) >= 100:
                    continue
            except ValueError:
                pass

            # Evita grados tipo G2
            inicio = m.start(1)

            if inicio > 0:
                anterior = desc_norm[inicio - 1]

                if anterior.isalpha():
                    continue

            diametro = candidato
            break

    return diametro, paso, largo

# -------------------------
# Parseo abrazaderas
# -------------------------
def parse_abrazadera(desc):
    # Ejemplo: "Abrazadera de Encastre Regulable 19-21"
    desc_norm = normalizar(desc)

    diametro = None
    largo = None
    forma = None

    # Buscamos el rango numérico (ej: 19-21 o incluso 9-11)
    match = re.search(r"(\d+-\d+)", desc_norm)

    if match:
        diametro = match.group(1) 

    return diametro, largo, forma

# -------------------------
# Parseo para grampas
# -------------------------

def parse_grampa(desc):
    # Ejemplo: "Grampyta PY 5  Bolsa x 750 (15 bolsitas x 50 unid) BLANCA"
    # Aseguramos que no rompa si viene en mayúsculas/minúsculas
    desc_norm = desc.upper() 

    diametro = None
    largo = None
    forma = None
    color = None

    # 1. Extraer la medida del cable (ej: "PY 5" o "PY5" o "Nº 5")
    # Busca la palabra PY seguida opcionalmente de espacios y un número (puede ser decimal como 5.5 o 6)
    match_medida = re.search(r"PY\s*(\d+(?:[.,]\d+)?)", desc_norm)
    if match_medida:
        diametro = match_medida.group(1)

    # 2. Extraer el color si viene al final o entre el texto
    if "BLANCA" in desc_norm or "BLANCO" in desc_norm:
        color = "Blanco"
    elif "NEGRA" in desc_norm or "NEGRO" in desc_norm:
        color = "Negro"
    elif "GRIS" in desc_norm:
        color = "Gris"

    # Asignamos el color a 'forma' o lo manejas como variable extra según tu BD
    forma = color 

    return diametro, largo, forma



# -------------------------
# Parseo para clavos
# -------------------------

def parse_clavo(desc):
    """
    Parsea clavos en distintos formatos

    Ejemplos:

    PUNTA PARIS ESPIR 2 1/2
    CABEZA CHATA 8/20
    CABEZA DE PLOMO ANILLADO 4,1 X 101,6
    PUNTA CAJONERO 12/32 MM
    """

    desc_norm = normalizar(desc)

    diametro = None
    largo = None
    forma = None

    # ==========================================
    # FORMAS / TIPOS
    # ==========================================

    if "punta paris" in desc_norm:
        forma = "punta paris"
    elif "cabeza perdida" in desc_norm:
        forma = "cabeza perdida"
    elif "cabeza chata" in desc_norm:
        forma = "cabeza chata"
    elif "cajonero" in desc_norm:
        forma = "cajonero"
    elif "anillado" in desc_norm:
        forma = "anillado"

    # ==========================================
    # FORMATO:
    # 4,1 x 101,6
    # 3.5 x 25
    # ==========================================

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)",
        desc_norm
    )

    if match:
        diametro = match.group(1).replace(",", ".")
        largo = match.group(2).replace(",", ".")

        if diametro.endswith(".0"):
            diametro = diametro[:-2]
        if largo.endswith(".0"):
            largo = largo[:-2]

        return diametro, None, largo, forma

    # ==========================================
    # FIX: este bloque estaba indentado dentro del if anterior
    # → nunca se ejecutaba. Ahora es un bloque independiente.
    #
    # FORMATO IMPERIAL:
    # 2 1/2
    # 1 1/4
    # ==========================================

    match = re.search(
        r"(\d+)\s+(\d+/\d+)",
        desc_norm
    )

    if match:
        entero = match.group(1)
        fraccion = match.group(2)
        largo = f"{entero}.{fraccion}"

        return diametro, None, largo, forma

    # ==========================================
    # FORMATO:
    # 8/20
    # 12/32
    #
    # diámetro / largo mm
    # ==========================================

    match = re.search(
        r"\b(\d+)\s*/\s*(\d+)\b",
        desc_norm
    )

    if match:
        diametro = match.group(1)
        largo = match.group(2)

        return diametro, None, largo, forma

    # ==========================================
    # SOLO FRACCION:
    # 3/4
    # ==========================================

    match = re.search(
        r"(\d+/\d+)",
        desc_norm
    )

    if match:
        largo = match.group(1)

        return diametro, None, largo, forma

    # ==========================================
    # SOLO ENTERO
    # ==========================================

    match = re.search(
        r"\b(\d+(?:[.,]\d+)?)\b",
        desc_norm
    )

    if match:
        largo = match.group(1).replace(",", ".")

    return diametro, None, largo, forma


# -------------------------
# Parseo para espacios
# -------------------------

def parse_con_espacios(desc):
    """
    Ejemplos:
    4 x 25
    5 x 40
    6x30
    3,5 x 40
    3.5 x 25
    """

    desc_norm = normalizar(desc)

    diametro = None
    largo = None

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)",
        desc_norm
    )

    if match:
        diametro = match.group(1).replace(",", ".")
        largo = match.group(2).replace(",", ".")

        if largo.endswith(".0"):
            largo = largo[:-2]
        if diametro.endswith(".0"):
            diametro = diametro[:-2]

    return diametro, None, largo


# -------------------------
# Parseo para tarugos
# -------------------------

def parse_tarugo(desc):
    """
    Ejemplos:
    Tarugos ESPYGA 5
    Tarugos PY PLUS 6 x 40 mm
    Abrazadera PY 5
    """

    desc_norm = normalizar(desc)

    diametro = None
    largo = None

    # ==========================================
    # 6 x 40
    # ==========================================

    match = re.search(
        r"(\d+(?:[.,]\d+)?)\s*[x×]\s*(\d+(?:[.,]\d+)?)",
        desc_norm
    )

    if match:
        diametro = match.group(1).replace(",", ".")
        largo = match.group(2).replace(",", ".")

        if diametro.endswith(".0"):
            diametro = diametro[:-2]
        if largo.endswith(".0"):
            largo = largo[:-2]

        return diametro, None, largo

    # ==========================================
    # Tarugo 5
    # ==========================================

    match = re.search(
        r"tarugos?\s+.*?(\d+(?:[.,]\d+)?)",
        desc_norm
    )

    if match:
        diametro = match.group(1).replace(",", ".")

    

    return diametro, None, largo


# -------------------------
# Validaciones
# -------------------------

def es_registro_valido(desc, codigo):
    """
    Valida si un registro es válido (no es basura)
    """
    desc = str(desc).strip() if pd.notna(desc) else ""
    codigo = str(codigo).strip() if pd.notna(codigo) else ""

    if not codigo or codigo == ">" or codigo == "nan":
        return False
    if not desc or desc == "" or desc == "nan":
        return False
    if desc.count("0") > 20 and len(desc.split(",")) > 10:
        return False

    return True


# -------------------------
# Parser principal
# -------------------------

def parse_carel_listado(input_path, output_path=None):
    """
    Parsea el archivo listadoProductos.csv de Carel

    Args:
        input_path: Ruta del archivo CSV
        output_path: Ruta para guardar el CSV procesado (opcional)

    Returns:
        DataFrame con productos parseados
    """

    try:
        logger.info(f"📖 Leyendo archivo: {input_path}")

        df = pd.read_csv(
            input_path,
            encoding="utf-8",
            sep=",",
            quotechar='"',
            engine="python"
        )

        logger.info(f"✅ Archivo cargado: {len(df)} productos encontrados")

        df.columns = df.columns.str.strip().str.lower()

        if "codigo" not in df.columns or "descripcion" not in df.columns:
            logger.error("❌ El archivo debe contener columnas 'Codigo' y 'Descripcion'")
            return pd.DataFrame()

        df = df[["codigo", "descripcion"]].copy()

        df["codigo"] = df["codigo"].astype(str).fillna("").str.strip()
        df["descripcion"] = df["descripcion"].astype(str).fillna("").str.strip()
        df["codigo"] = df["codigo"].apply(limpiar_codigo)

        logger.info("🔍 Validando registros...")

        df = df[df.apply(lambda row: es_registro_valido(row["descripcion"], row["codigo"]), axis=1)]

        logger.info(f"✅ Registros válidos: {len(df)}")
        logger.info("🔍 Parseando descripciones...")

        resultados = []

        for idx, row in df.iterrows():
            try:
                desc = str(row["descripcion"]).strip()
                codigo = str(row["codigo"]).strip()

                desc_norm = normalizar(desc)

                tipo = detectar_tipo(desc_norm)
                forma = detectar_forma(desc_norm)
                acabado = detectar_acabado(desc_norm)
                sistema_rosca = detectar_sistema_rosca(desc_norm)
                sistema = detectar_sistema(desc_norm)
                grado = detectar_grado(desc_norm)

                diametro = None
                paso = None
                largo = None

                if tipo == "clavo":
                    diametro, paso, largo, forma = parse_clavo(desc_norm)
                elif sistema == "métrico":
                    diametro, paso, largo = parse_metrico(desc_norm)
                elif sistema == "imperial":
                    diametro, paso, largo = parse_imperial(desc_norm)
                elif tipo in ["tornillo_fix", "tirafondo", "tornillo_drywall"]:
                    diametro, paso, largo = parse_con_espacios(desc_norm)
                elif tipo == "tarugo":
                    diametro, paso, largo = parse_tarugo(desc_norm)
                elif tipo == "grampas":
                    diametro, paso, largo = parse_grampa(desc_norm)
                # FIX: tipos con sistema "otro" que sí tienen formato métrico/imperial
                # son intentados con parse_con_espacios como fallback genérico
                elif tipo in ["tornillo", "tuerca", "bulón", "arandela",
                              "espárrago", "perno", "varilla", "prisionero",
                              "remache", "pasador", "chaveta"]:
                    diametro, paso, largo = parse_con_espacios(desc_norm)
                elif tipo == "abrazadera":
                    diametro, paso, largo = parse_abrazadera(desc_norm)

                resultados.append({
                    "codigo": codigo,
                    "tipo": tipo,
                    "forma": forma,
                    "diametro": diametro,
                    "paso": paso,
                    "largo": largo,
                    "grado": grado,
                    "sistema": sistema,
                    "sistema_rosca": sistema_rosca,
                    "acabado": acabado,
                    "descripcion": desc
                })

                if (idx + 1) % 100 == 0:
                    logger.info(f"   Procesados {idx + 1}/{len(df)} productos...")

            except Exception as e:
                logger.warning(f"   ⚠️  Error procesando fila {idx}: {e}")
                continue

        df_resultado = pd.DataFrame(resultados)

        logger.info(f"✅ Parseado completado: {len(df_resultado)} productos procesados")

        logger.info("\n📊 ESTADÍSTICAS DE PARSEO:")
        logger.info(f"   Productos parseados: {len(df_resultado[df_resultado['diametro'].notna()])}")
        logger.info(f"   Productos sin parsear: {len(df_resultado[df_resultado['diametro'].isna()])}")

        logger.info(f"\n   Tipos detectados:")
        for tipo, count in df_resultado['tipo'].value_counts().items():
            logger.info(f"      - {tipo}: {count}")

        logger.info(f"\n   Formas detectadas:")
        formas = df_resultado[df_resultado['forma'].notna()]['forma'].value_counts()
        if len(formas) > 0:
            for forma, count in formas.items():
                logger.info(f"      - {forma}: {count}")
        else:
            logger.info(f"      - (ninguna detectada)")

        logger.info(f"\n   Acabados detectados:")
        acabados = df_resultado[df_resultado['acabado'].notna()]['acabado'].value_counts()
        if len(acabados) > 0:
            for acabado, count in acabados.items():
                logger.info(f"      - {acabado}: {count}")
        else:
            logger.info(f"      - (ninguno detectado)")

        logger.info(f"\n   Sistemas detectados:")
        for sistema, count in df_resultado['sistema'].value_counts().items():
            logger.info(f"      - {sistema}: {count}")

        logger.info(f"\n   Grados detectados:")
        grados_count = df_resultado[df_resultado['grado'].notna()]['grado'].value_counts()
        if len(grados_count) > 0:
            for grado, count in grados_count.head(10).items():
                logger.info(f"      - {grado}: {count}")
        else:
            logger.info(f"      - (ninguno detectado)")

        sin_parsear = df_resultado[df_resultado['diametro'].isna()]
        if len(sin_parsear) > 0:
            logger.info(f"\n⚠️  Ejemplos de productos sin parsear ({len(sin_parsear)} total):")
            for _, row in sin_parsear.head(10).iterrows():
                logger.info(f"      {str(row['codigo'])[:15]:15} | {str(row['tipo'])[:12]:12} | {str(row['descripcion'])[:60]}")

        if output_path:
            df_resultado.to_csv(output_path, index=False, encoding="utf-8")
            logger.info(f"\n💾 Archivo guardado: {output_path}")

        return df_resultado

    except FileNotFoundError:
        logger.error(f"❌ Archivo no encontrado: {input_path}")
        return pd.DataFrame()
    except Exception as e:
        logger.error(f"❌ Error al procesar archivo: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return pd.DataFrame()