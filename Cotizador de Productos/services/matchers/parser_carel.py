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

    # Abreviaturas comunes
    if "bul" in desc or "bulón" in desc or "bulon" in desc:
        return "bulón"
    if "tor" in desc or "tornillo" in desc:
        return "tornillo"
    if "tuerca" in desc:
        return "tuerca"
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
    
    sistemas = ['unc', 'unf', 'bsw', 'bsp', 'iso', 'nc', 'nf', 'metrica', 'métrica', 'wh', 'whitworth']
    
    for sistema in sistemas:
        if sistema in desc:
            return sistema.upper()
    
    return None


def detectar_sistema(desc):
    """Detecta si es métrico o imperial"""
    desc = desc.lower()

    # Sistema imperial: 1/4", 5/16", UNC, UNF, BSW, NC, etc.
    if "unc" in desc or "unf" in desc or "bsw" in desc or "nc" in desc or "nf" in desc or "whitworth" in desc or "wh" in desc or re.search(r"\d+/\d+", desc):
        return "imperial"

    # Sistema métrico: M8, M10, M12, etc. o números simples como "4 x 30"
    if re.search(r"\bm\d+", desc):
        return "métrico"
    
    # Si tiene formato "número x número" sin barra, probablemente métrico
    if re.search(r"^\s*\d+\s*x\s*\d+", desc):
        return "métrico"

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

def parse_metrico(desc):
    """
    Parsea especificaciones métricas
    Ejemplos: M8x1.25, M10-1.5, M12x1.75, 4x30, 8x1.25x50, 6x25
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
        return diametro, None, largo
    
    # Números sin M: 4x30, 8x1.25x50mm (3 números)
    match = re.search(r"(\d+)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)", desc_norm)
    if match:
        num1 = int(match.group(1))
        num2 = float(match.group(2))
        num3 = float(match.group(3))
        
        # Si primer número es pequeño, probablemente es diámetro
        if num1 < 30:
            diametro = str(num1)
            # Si el segundo número es muy pequeño (< 5), es paso
            if num2 < 5:
                paso = str(num2)
                largo = str(int(num3))
            else:
                # Si el segundo es mayor, es largo
                paso = None
                largo = str(int(num2))
            return diametro, paso, largo
    
    # Números sin M: 4x30 (solo dos números)
    match = re.search(r"(\d+)\s*x\s*(\d+\.?\d*)", desc_norm)
    if match:
        num1 = int(match.group(1))
        num2 = float(match.group(2))
        
        # Si primer número es pequeño (1-30) probablemente es diámetro
        if num1 < 30:
            # Si el segundo número es muy pequeño (< 5), es paso
            if num2 < 5:
                diametro = str(num1)
                paso = str(num2)
            else:
                # Si es mayor, es largo
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
    Ejemplos: 1/4"-20, 5/16"UNC(32), 3/8" x 2", 1.1/2-UNF(12), 1.3/4-WH, 1/4-NC-1/2
    Retorna: (diámetro, paso, largo)
    """
    desc_norm = normalizar(desc)
    
    diametro = None
    paso = None
    largo = None
    
    # Buscar diámetro con fracciones: 1/4, 5/16, 1.1/2, 1.3/4, etc.
    diametro_match = re.search(r"(\d+(?:\.\d+)?/\d+)", desc_norm)
    if diametro_match:
        diametro = diametro_match.group(1)
    
    # NUEVOS PATRONES PARA PASO Y LARGO:
    
    # Patrón 1: "NC-paso-largo" o "UNC-paso-largo" (ej: 1/4-NC-1/2, 5/16-UNC-3/8)
    # Busca: sistema-número-número (donde el segundo número puede ser fracción)
    match = re.search(r"(?:unc|unf|nc|nf|wh)\s*[-.]?\s*(\d+)\s*[-.]?\s*(\d+(?:/\d+)?)", desc_norm)
    if match and diametro:
        paso = match.group(1)
        largo = match.group(2)
        return diametro, paso, largo
    
    # Patrón 2: "UNC(20)" o "(20)" o "-20" (paso sin largo)
    paso_match = re.search(r"(?:unc|unf|bsw|nc|nf|wh)?\s*[-.\s]?\(?(\d+)\)?", desc_norm)
    if paso_match and not largo:
        paso = paso_match.group(1)
    
    # Patrón 3: "x 2" o "x 1.1/2" o "x 1.3/4" (largo)
    largo_match = re.search(r"x\s*(\d+(?:\.\d+)?(?:/\d+)?)", desc_norm)
    if largo_match and not largo:
        largo = largo_match.group(1)
    
    return diametro, paso, largo


# -------------------------
# Validaciones
# -------------------------

def es_registro_valido(desc, codigo):
    """
    Valida si un registro es válido (no es basura)
    """
    # Convertir a string por seguridad
    desc = str(desc).strip() if pd.notna(desc) else ""
    codigo = str(codigo).strip() if pd.notna(codigo) else ""
    
    # Si el código está vacío o es solo ">"
    if not codigo or codigo == ">" or codigo == "nan":
        return False
    
    # Si la descripción está vacía
    if not desc or desc == "" or desc == "nan":
        return False
    
    # Si es un registro con muchos ceros (basura)
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
        if "codigo" not in df.columns or "descripcion" not in df.columns:
            logger.error("❌ El archivo debe contener columnas 'Codigo' y 'Descripcion'")
            return pd.DataFrame()
        
        # Quedarse solo con las columnas importantes
        df = df[["codigo", "descripcion"]].copy()
                
        # Convertir TODO a string PRIMERO
        df["codigo"] = df["codigo"].astype(str).fillna("").str.strip()
        df["descripcion"] = df["descripcion"].astype(str).fillna("").str.strip()

        # Limpiar datos
        df["codigo"] = df["codigo"].apply(limpiar_codigo)        
        logger.info("🔍 Validando registros...")
        
        # Filtrar registros válidos
        df = df[df.apply(lambda row: es_registro_valido(row["descripcion"], row["codigo"]), axis=1)]
        
        logger.info(f"✅ Registros válidos: {len(df)}")
        logger.info("🔍 Parseando descripciones...")
        
        # -------------------------
        # Aplicar lógica de parseo
        # -------------------------
        
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
        
        logger.info(f"\n   Grados detectados:")
        grados_count = df_resultado[df_resultado['grado'].notna()]['grado'].value_counts()
        if len(grados_count) > 0:
            for grado, count in grados_count.head(10).items():
                logger.info(f"      - {grado}: {count}")
        else:
            logger.info(f"      - (ninguno detectado)")
        
        # Mostrar ejemplos de productos que no se parsearon bien
        sin_parsear = df_resultado[df_resultado['diametro'].isna()]
        if len(sin_parsear) > 0:
            logger.info(f"\n⚠️  Ejemplos de productos sin parsear ({len(sin_parsear)} total):")
            for _, row in sin_parsear.head(10).iterrows():
                logger.info(f"      {str(row['codigo'])[:15]:15} | {str(row['tipo'])[:12]:12} | {str(row['descripcion'])[:60]}")
        
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