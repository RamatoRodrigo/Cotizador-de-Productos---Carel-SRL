import pandas as pd
import re
import logging
from pathlib import Path

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


def detectar_tipo(desc):
    """Detecta el tipo de producto basado en la descripción"""
    desc = desc.lower()

    # PUNTAS (debe ir antes que otros para evitar confusiones)
    if (
        "punta aguja" in desc or
        "punta paris" in desc or
        "punta espir" in desc or
        "punta cajonero" in desc or
        desc.startswith("pta ") or
        " pta " in desc
    ):
        return "punta"

    # CABEZAL/CABEZA (incluye "cabeza perdida", "cabeza chata")
    if (
        "cabeza de plomo" in desc or
        "cabeza perdida" in desc or
        "cabeza chata" in desc or
        "cabezal" in desc or
        "cab tanque" in desc or
        "cab " in desc  # Detecta abreviaturas "CAB..."
    ):
        return "cabezal"

    # BULONES
    if (
        "bulón" in desc or "bulon" in desc or
        desc.startswith("bu ") or " bu " in desc
    ):
        return "bulón"

    # TUERCAS
    if (
        "tuerca" in desc or
        desc.startswith("tu ") or " tu " in desc
    ):
        return "tuerca"

    # TORNILLOS DRYWALL (antes que tornillo genérico)
    if "drywall" in desc or "dry wall" in desc:
        return "tornillo_drywall"

    # TORNILLOS FIX
    if "fix" in desc:
        return "tornillo_fix"

    # TORNILLOS
    if (
        "tornillo" in desc or
        desc.startswith("to ") or " to " in desc
    ):
        return "tornillo"

    # ARANDELAS
    if (
        "arandela" in desc or "ale " in desc or " ale " in desc or
        desc.startswith("ara ") or " ara " in desc
    ):
        return "arandela"

    if "espárrago" in desc or "esparrago" in desc:
        return "espárrago"

    if "perno" in desc:
        return "perno"

    if "varilla" in desc or "vr " in desc:
        return "varilla"

    if "remache" in desc:
        return "remache"

    if "pasador" in desc:
        return "pasador"

    if "chaveta" in desc:
        return "chaveta"

    return "otro"


def detectar_forma(desc):
    """Detecta la forma del producto (hexagonal, autofrenante, phillips, etc.)"""
    desc = desc.lower()
    
    formas = {
        'hexagonal': ['hexagonal', 'hex', 'hex.'],
        'autofrenante': ['autofr', 'autofrenante', 'autofren'],
        'allen': ['allen', 'allen cab'],
        'mariposa': ['mariposa', 'butterfly'],
        'almenada': ['almenada', 'castillo'],
        'grower': ['grower'],
        'plana': ['plana', 'flat'],
        'fresada': ['fresada', 'fresa', 'countersunk'],
        'phillips': ['phillips', 'phil', 'cruz'],
        'pozi': ['pozi', 'pozidrive'],
        'redonda': ['redonda', 'round'],
        'cuadrada': ['cuadrada', 'square'],
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
        'zinc': ['zinc', 'zincado', 'zincada', 'za', 'zn', 'galvanizado', 'galv', 'gv'],
        'natural': ['nat', 'natural', 'natural', 'na', 'rd nat'],
        'bronce': ['bronce', 'br'],
        'niquelado': ['niquelado', 'niquel', 'ni'],
        'cromado': ['cromado', 'cromo', 'cr'],
        'dicro': ['dicro', 'dicromado', 'dc'],
        'acero_inox': ['inox', 'acero inoxidable', 'stainless', 'a4', 'a2'],
        'pavonado': ['pavonado', 'pav'],
        'plomo': ['plomo', 'pb'],
    }
    
    for acabado, keywords in acabados.items():
        for keyword in keywords:
            if keyword in desc:
                return acabado
    
    return None


def detectar_sistema_rosca(desc):
    """Detecta el sistema de rosca (UNC, UNF, BSW, ISO, etc.)"""
    desc = desc.lower()
    
    sistemas = ['unc', 'unf', 'bsw', 'bsp', 'iso', 'metrica', 'métrica', 'wh', 'whitworth']
    
    for sistema in sistemas:
        if sistema in desc:
            return sistema.upper()
    
    return None


def detectar_sistema(desc):
    """Detecta si es métrico o imperial"""
    desc = desc.lower()

    # Sistema imperial: 1/4", 5/16", UNC, UNF, BSW, etc.
    if "unc" in desc or "unf" in desc or "bsw" in desc or "whitworth" in desc or "wh" in desc or re.search(r"\d+/\d+", desc):
        return "imperial"

    # Sistema métrico: M8, M10, M12, etc.
    if re.search(r"\bm\d+", desc):
        return "métrico"
    
    # Si tiene formato "número x número" sin barra, probablemente métrico
    if re.search(r"^\s*\d+\s*x\s*\d+", desc):
        return "métrico"

    return "otro"


def detectar_grado(desc):
    """Detecta el grado de resistencia (8.8, 10.9, G2, etc.)"""
    desc = desc.lower()
    
    # Grados numéricos: 8.8, 10.9, 12.9, etc.
    match = re.search(r"(\d+\.?\d*)\s*(?:grado|gr\.?|clase)", desc)
    if match:
        return match.group(1)
    
    # Búsqueda directa de patrones comunes
    grados = ["12.9", "10.9", "8.8", "5.8", "4.8", "4.6"]
    for grado in grados:
        if grado in desc:
            return grado
    
    # Grados alfanuméricos: G2, G5, etc.
    match = re.search(r"[^a-z](g\d+)[^a-z]", f" {desc} ")
    if match:
        return match.group(1).upper()
    
    return None


# -------------------------
# Parseo métrico
# -------------------------

def parse_metrico(desc):
    """
    Parsea especificaciones métricas
    Ejemplos: M8x1.25, M10-1.5, M12x1.75, 4x30, 8x1.25x50, 4.5x25.0
    """
    desc_norm = normalizar(desc)
    
    diametro = None
    paso = None
    largo = None
    
    # M8x1.25 o M8-1.25
    match = re.search(r"m\s*(\d+)[-x](\d+\.?\d*)", desc_norm)
    if match:
        diametro = f"M{match.group(1)}"
        paso = match.group(2)
        return diametro, paso, largo
    
    # Solo M8 (sin paso)
    match = re.search(r"m\s*(\d+)(?:\s|$|[^\d])", desc_norm)
    if match:
        diametro = f"M{match.group(1)}"
        return diametro, paso, largo
    
    # Tres números: 8x1.25x50mm o 4.5x25.0x100
    match = re.search(r"(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)", desc_norm)
    if match:
        diametro = match.group(1)
        paso = match.group(2)
        largo = match.group(3)
        return diametro, paso, largo
    
    # Dos números: 4x30, 4.5x25.0
    match = re.search(r"(\d+\.?\d*)\s*x\s*(\d+\.?\d*)", desc_norm)
    if match:
        num1 = float(match.group(1))
        num2 = float(match.group(2))
        
        # Heurística: si el primer número es pequeño (1-30) y segundo es mayor, probablemente:
        # - num1 es diámetro, num2 es largo (si num2 > 10)
        # - num1 es diámetro, num2 es paso (si num2 < 10)
        if 1 <= num1 <= 30:
            if num2 > 10:
                diametro = str(num1)
                largo = str(int(num2) if num2 == int(num2) else num2)
            else:
                diametro = str(num1)
                paso = str(num2)
            return diametro, paso, largo
    
    return None, None, None



# -------------------------
# Parseo imperial
# -------------------------

def parse_imperial(desc):
    """
    Parsea especificaciones imperiales
    Ejemplos: 1/4"-20, 5/16"UNC(32), 3/8" x 2", 1,1/2-UNF(12), 8 X 1/2
    Retorna: (diámetro, paso, largo)
    """
    desc_norm = normalizar(desc)
    
    diametro = None
    paso = None
    largo = None
    
    # Buscar diámetro: 1/4, 5/16, 1.1/2 (con punto), 8 (número sin fracción)
    diametro_match = re.search(r"(\d+(?:\.\d+)?/\d+)", desc_norm)
    if diametro_match:
        diametro = diametro_match.group(1)
    else:
        # Si no hay fracción pero hay "x" (formato: 8 X 1/2), buscar el primer número
        diametro_match = re.search(r"^(\d+(?:\.\d+)?)\s*x", desc_norm)
        if diametro_match:
            diametro = diametro_match.group(1)
    
    # Paso: búsqueda de UNC(20), (20), -20, UNC20, WH-2, etc.
    paso_match = re.search(r"(?:unc|unf|bsw|wh)?\s*[-\.]?\s*\(?(\d+)\)?", desc_norm)
    if paso_match:
        paso = paso_match.group(1)
    
    # Largo: x 2", x 1.5", x 1/2, x 16mm, etc.
    largo_match = re.search(r"x\s*(\d+(?:\.\d+)?(?:/\d+)?)", desc_norm)
    if largo_match:
        largo = largo_match.group(1)
    
    return diametro, paso, largo


# -------------------------
# Parser de Borroni
# -------------------------

def parse_borroni_csv(input_path, output_path=None):
    """
    Parsea el archivo borroniSinParsear.csv
    
    Args:
        input_path: Ruta del archivo CSV sin parsear
        output_path: Ruta para guardar el CSV parseado (opcional)
    
    Returns:
        DataFrame con productos parseados
    """
    
    try:
        logger.info(f"📖 Leyendo archivo: {input_path}")
        
        # Leer CSV
        df = pd.read_csv(
            input_path,
            encoding="utf-8",
            sep=",",
            quotechar='"',
            engine="python"
        )
        
        logger.info(f"✅ Archivo cargado: {len(df)} productos encontrados")
        
        # Normalizar nombres de columnas
        df.columns = df.columns.str.strip().str.lower()
        
        # Validar que existan las columnas necesarias
        cols_requeridas = ['codigo_de_producto', 'descripcion', 'precio']
        if not all(col in df.columns for col in cols_requeridas):
            logger.error(f"❌ El archivo debe contener columnas: {cols_requeridas}")
            logger.info(f"   Columnas encontradas: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Convertir TODO a string PRIMERO
        df['codigo_de_producto'] = df['codigo_de_producto'].astype(str).fillna("").str.strip()
        df['descripcion'] = df['descripcion'].astype(str).fillna("").str.strip()
        df['precio'] = pd.to_numeric(df['precio'], errors='coerce')
        
        logger.info("🔍 Validando registros...")
        
        # Filtrar registros válidos (con código, descripción y precio)
        df = df[
            (df['codigo_de_producto'] != "") & 
            (df['codigo_de_producto'] != "nan") &
            (df['descripcion'] != "") & 
            (df['descripcion'] != "nan") &
            (df['precio'].notna())
        ]
        
        logger.info(f"✅ Registros válidos: {len(df)}")
        logger.info("🔍 Parseando descripciones...")
        
        # -------------------------
        # Aplicar lógica de parseo
        # -------------------------
        
        resultados = []
        
        for idx, row in df.iterrows():
            try:
                desc = str(row['descripcion']).strip()
                codigo = str(row['codigo_de_producto']).strip()
                precio = row['precio']
                
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
                
                if sistema == "métrico":
                    diametro, paso, largo = parse_metrico(desc_norm)
                
                elif sistema == "imperial":
                    diametro, paso, largo = parse_imperial(desc_norm)
                
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
                    "precio_unitario": precio,
                    "proveedor": "borroni",
                    "descripcion": desc
                })
                
                if (idx + 1) % 100 == 0:
                    logger.info(f"   Procesados {idx + 1}/{len(df)} productos...")
            
            except Exception as e:
                logger.warning(f"   ⚠️  Error procesando fila {idx}: {e}")
                continue
        
        # Crear DataFrame con resultados
        df_resultado = pd.DataFrame(resultados)
        
        logger.info(f"✅ Parseado completado: {len(df_resultado)} productos procesados")
        
        # Estadísticas
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
        
        logger.info(f"\n   Precio mínimo: ${df_resultado['precio_unitario'].min():.2f}")
        logger.info(f"   Precio máximo: ${df_resultado['precio_unitario'].max():.2f}")
        logger.info(f"   Precio promedio: ${df_resultado['precio_unitario'].mean():.2f}")
        
        # Mostrar ejemplos de productos que no se parsearon bien
        sin_parsear = df_resultado[df_resultado['diametro'].isna()]
        if len(sin_parsear) > 0:
            logger.info(f"\n⚠️  Ejemplos de productos sin parsear ({len(sin_parsear)} total):")
            for _, row in sin_parsear.head(10).iterrows():
                logger.info(f"      {str(row['codigo'])[:15]:15} | {str(row['tipo'])[:20]:20} | {str(row['descripcion'])[:60]}")
        
        # Guardar si se especifica output_path
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

