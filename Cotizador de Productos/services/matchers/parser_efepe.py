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
        .replace("  ", " ")
        .strip()
    )


def detectar_tipo(desc):
    """Detecta el tipo de producto basado en la descripción"""
    desc = desc.lower()

    if "bulón" in desc or "bulon" in desc:
        return "bulón"
    if "tuerca" in desc or "tca" in desc:
        return "tuerca"
    if "drywall" in desc:
        return "drywall"
    if "niple" in desc:
        return "niple"
    if "arandela" in desc:
        return "arandela"
    if "tarugo" in desc:
        return "tarugo"
    if "espárrago" in desc or "esparrago" in desc:
        return "espárrago"
    if "perno" in desc:
        return "perno"
    if "mecha" in desc:
        return "mecha"
    if "varilla" in desc:
        return "varilla"
    if "remache" in desc:
        return "remache"
    if "tela" in desc:
        return "tela"
    if "chaveta" in desc:
        return "chaveta"
    if (("tel" in desc and "poda" not in desc) or "tornillo" in desc or "dry" in desc or ("alas" in desc and "palas" not in desc) 
        or "tanque" in desc or "punta calada" in desc or "trompeta" in desc or ("phil" in desc and "destornillador" not in desc) 
        or "fix" in desc or "autoperforante" in desc or "chip" in desc):
        return "tornillo"

    return "otro"


def detectar_forma(desc):
    """Detecta la forma del producto (hexagonal, autofrenante, etc.)"""
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
        for keyw in keywords:
            if keyw in desc:
                return forma
    
    return None


def detectar_acabado(desc):
    """Detecta el acabado/recubrimiento del producto"""
    desc = desc.lower()
    
    acabados = {
        'zinc': ['zinc', 'zincado', 'zincada', 'zn'],
        'natural': ['nat', 'natural', 'na'],
        'bronce': ['bronce'],
        'niquelado': ['niquelado', 'niquel'],
        'cromado': ['cromado', 'cromo'],
        'dicro': ['dicro', 'dicromado'],
        'acero_inox': ['inox', 'acero inoxidable', 'stainless', 'a4', 'a2'],
        'galvanizado': ['galvanizado', 'galv', 'gv'],
        'pavonado': ['pavonado', 'pav'],
    }
    
    for acabado, keywords in acabados.items():
        for keyw in keywords:
            if keyw in desc:
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


def detectar_sistema(desc: str) -> str:
    desc = desc.lower()

    # ---------- IMPERIAL ----------
    
    # fracciones
    if re.search(r"\b\d+(?:\.\d+)?/\d+\b", desc):
        return "imperial"

    # UNC / UNF / BSW
    if re.search(r"\b(?:unc|unf|bsw|bsf)\b", desc):
        return "imperial"

    # formato 5/16-24
    if re.search(r"\b\d+(?:\.\d+)?/\d+\s*-\s*\d+\b", desc):
        return "imperial"

    # ---------- MÉTRICO ----------

    # grados métricos
    if re.search(r"\b(?:8\.8|10\.9|12\.9)\b", desc):
        return "métrico"

    # M8, M10, etc
    if re.search(r"\bm\d+\b", desc):
        return "métrico"

    # paso P1.25
    if re.search(r"\bp\s*\d+(?:\.\d+)?\b", desc):
        return "métrico"

    # milímetros explícitos
    if re.search(r"\d+(?:\.\d+)?\s*mm\b", desc):
        return "métrico"

    # 12x35
    if re.search(
        r"\b\d+(?:\.\d+)?\s*[x]\s*\d+(?:\.\d+)?\b",
        desc
    ):
        return "métrico"

    # ---------- FALLBACK ----------

    if re.search(r"\d", desc):
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

def parse_metrico(desc: str):
    desc = desc.upper().replace(",", ".")
    desc = re.sub(r"\s+", " ", desc)  # normalizar espacios
    
    # Caso M + número (ej: M8 x 20)
    match = re.search(r"\bM(\d+)\s*[Xx]\s*(\d+(?:\.\d+)?)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Caso con MM explícito (ej: 2.0 MM X 300MM)
    match = re.search(r"(\d+(?:\.\d+)?)\s*MM\s*[Xx]\s*(\d+(?:\.\d+)?)\s*MM", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Caso genérico con tres números separados por x (ej: 6 x 1.00 x 100)
    match = re.search(r"(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)", desc)
    if match:
        return match.group(1), match.group(2), match.group(3)

    # 🔹 Nuevo: dos números separados por x (ej: 14 x 3, 14x6)
    match = re.search(r"(\d+(?:\.\d+)?)\s*[Xx]\s*(\d+(?:\.\d+)?)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Caso número suelto (ej: Grower 6)
    match = re.search(r"\b(\d+(?:\.\d+)?)\b", desc)
    if match:
        return match.group(1), None, None

    return None, None, None




# -------------------------
# Parseo imperial
# -------------------------

def parse_imperial(desc: str):
    desc = desc.lower().replace(",", ".")
    
    # Fracción con paso (ej: 5/16 - 24)
    match = re.search(r"(\d+(?:\.\d+)?/\d+)\s*-\s*(\d+)", desc)
    if match:
        return match.group(1), match.group(2), None

    # Fracción x fracción (ej: 5/16 x 3/4)
    match = re.search(r"(\d+(?:\.\d+)?/\d+)\s*x\s*(\d+(?:\.\d+)?/\d+)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Fracción x número entero (ej: 5/16 x 110)
    match = re.search(r"(\d+(?:\.\d+)?/\d+)\s*x\s*(\d+)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Entero x fracción (ej: 08 x 1.1/4)
    match = re.search(r"(\d+)\s*x\s*(\d+(?:\.\d+)?/\d+)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # 🔹 Entero x entero (ej: 1 x 6)
    match = re.search(r"(\d+)\s*x\s*(\d+)", desc)
    if match:
        return match.group(1), None, match.group(2)

    # Fracción sola (ej: 3/8)
    match = re.search(r"(\d+(?:\.\d+)?/\d+)\b", desc)
    if match:
        return match.group(1), None, None

    return None, None, None

# -------------------------
# Parser de Efepe
# -------------------------

def parse_efepe_csv(input_path, output_path=None):
    """
    Parsea el archivo efepeSinParsear.csv
    
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
        cols_requeridas = ['codigo', 'descripcion', 'precio_unitario']
        if not all(col in df.columns for col in cols_requeridas):
            logger.error(f"❌ El archivo debe contener columnas: {cols_requeridas}")
            logger.info(f"   Columnas encontradas: {df.columns.tolist()}")
            return pd.DataFrame()
        
        # Convertir TODO a string PRIMERO
        df['codigo'] = df['codigo'].astype(str).fillna("").str.strip()
        df['descripcion'] = df['descripcion'].astype(str).fillna("").str.strip()
        df['precio_unitario'] = pd.to_numeric(df['precio_unitario'], errors='coerce')
        
        logger.info("🔍 Validando registros...")
        
        # Filtrar registros válidos (con código, descripción y precio)
        df = df[
            (df['codigo'] != "") & 
            (df['codigo'] != "nan") &
            (df['descripcion'] != "") & 
            (df['descripcion'] != "nan") &
            (df['precio_unitario'].notna())
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
                codigo = str(row['codigo']).strip()
                precio = row['precio_unitario']
                
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
                    "proveedor": "efepe",
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


# -------------------------
# Ejemplo de uso
# -------------------------

if __name__ == "__main__":
    input_file = "ddbb/efepeSinParsear.csv"
    output_file = "ddbb/efepeParseado.csv"
    
    if Path(input_file).exists():
        df = parse_efepe_csv(input_file, output_file)
        
        if not df.empty:
            print("\n" + "="*150)
            print("PRIMERAS 15 FILAS PARSEADAS:")
            print("="*150)
            print(df.head(15).to_string())
    else:
        logger.error(f"Archivo no encontrado: {input_file}")
        logger.info("Coloca el archivo 'efepeSinParsear.csv' en la carpeta 'ddbb/'")