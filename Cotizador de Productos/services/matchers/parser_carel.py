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

    if "tuerca" in desc:
        return "tuerca"
    if "bulón" in desc or "bulon" in desc:
        return "bulón"
    if "tornillo" in desc:
        return "tornillo"
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

    return "otro"


def detectar_sistema(desc):
    """Detecta si es métrico o imperial"""
    desc = desc.lower()

    # Sistema imperial: 1/4", 5/16", UNC, etc.
    if "unc" in desc or "unf" in desc or re.search(r"\d+/\d+\"", desc):
        return "imperial"

    # Sistema métrico: M8, M10, M12, etc.
    if re.search(r"\bm\d+", desc):  # M seguido de número
        return "métrico"

    return "otro"


def detectar_grado(desc):
    """Detecta el grado de resistencia (8.8, 10.9, etc.)"""
    desc = desc.lower()
    
    match = re.search(r"(\d+\.?\d*)\s*(?:grado|gr\.?|clase)", desc)
    if match:
        return match.group(1)
    
    # Búsqueda directa de patrones comunes
    grados = ["8.8", "10.9", "12.9", "5.8", "4.6", "4.8"]
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
    Ejemplos: M8x1.25, M10-1.5, M12x1.75
    """
    desc_norm = normalizar(desc)
    
    # M8x1.25 o M8-1.25
    match = re.search(r"m\s*(\d+)[-x](\d+\.?\d*)", desc_norm)
    if match:
        diametro = f"M{match.group(1)}"
        paso = match.group(2)
        return diametro, paso
    
    # Solo M8 (sin paso)
    match = re.search(r"m\s*(\d+)", desc_norm)
    if match:
        diametro = f"M{match.group(1)}"
        return diametro, None
    
    return None, None


# -------------------------
# Parseo imperial
# -------------------------

def parse_imperial(desc):
    """
    Parsea especificaciones imperiales
    Ejemplos: 1/4"-20, 5/16"UNC(32), 3/8" x 2"
    Retorna: (diámetro, paso, largo)
    """
    desc_norm = normalizar(desc)
    
    # Diámetro tipo 5/32"
    diametro_match = re.search(r"(\d+/\d+)\"?", desc_norm)
    diametro = diametro_match.group(1) if diametro_match else None
    
    # Paso dentro de UNC(32), (32) o -20
    paso_match = re.search(r"(?:unc|unf)?\s*\(?(\d+)\)?", desc_norm)
    paso = paso_match.group(1) if paso_match else None
    
    # Largo opcional (para bulones): x 2" o x 2.5"
    largo_match = re.search(r"x\s*(\d+(?:\.\d+)?(?:/\d+)?)", desc_norm)
    largo = largo_match.group(1) if largo_match else None
    
    return diametro, paso, largo


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
        
        # Limpiar datos
        df["codigo"] = df["codigo"].astype(str).apply(limpiar_codigo)
        df["descripcion"] = df["descripcion"].astype(str)
        
        logger.info("🔍 Parseando descripciones...")
        
        # -------------------------
        # Aplicar lógica de parseo
        # -------------------------
        
        resultados = []
        
        for idx, row in df.iterrows():
            desc = row["descripcion"]
            desc_norm = normalizar(desc)
            
            tipo = detectar_tipo(desc_norm)
            sistema = detectar_sistema(desc_norm)
            grado = detectar_grado(desc_norm)
            
            diametro = None
            paso = None
            largo = None
            
            if sistema == "métrico":
                diametro, paso = parse_metrico(desc_norm)
            
            elif sistema == "imperial":
                diametro, paso, largo = parse_imperial(desc_norm)
            
            resultados.append({
                "codigo": row["codigo"],
                "tipo": tipo,
                "diametro": diametro,
                "paso": paso,
                "largo": largo,
                "grado": grado,
                "sistema": sistema,
                "descripcion": desc
            })
            
            if (idx + 1) % 100 == 0:
                logger.info(f"   Procesados {idx + 1}/{len(df)} productos...")
        
        # Crear DataFrame con resultados
        df_resultado = pd.DataFrame(resultados)
        
        logger.info(f"✅ Parseado completado: {len(df_resultado)} productos procesados")
        
        # Estadísticas
        logger.info("\n📊 ESTADÍSTICAS:")
        logger.info(f"   Tipos detectados: {df_resultado['tipo'].nunique()}")
        logger.info(f"   Sistemas detectados:")
        for sistema, count in df_resultado['sistema'].value_counts().items():
            logger.info(f"      - {sistema}: {count}")
        
        logger.info(f"\n   Productos sin parsear:")
        sin_parsear = df_resultado[df_resultado['diametro'].isna()]
        logger.info(f"      - Total: {len(sin_parsear)}")
        if len(sin_parsear) > 0 and len(sin_parsear) <= 10:
            logger.info(f"      Ejemplos:")
            for _, row in sin_parsear.head(5).iterrows():
                logger.info(f"         {row['codigo']}: {row['descripcion']}")
        
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
    # Ejemplo: procesar listadoProductos.csv
    input_file = "data/listadoProductos.csv"
    output_file = "data/listadoProductos_parseado.csv"
    
    if os.path.exists(input_file):
        df = parse_carel_listado(input_file, output_file)
        
        if not df.empty:
            print("\n" + "="*80)
            print("PRIMERAS 10 FILAS PARSEADAS:")
            print("="*80)
            print(df.head(10).to_string())
    else:
        logger.error(f"Archivo no encontrado: {input_file}")
        logger.info("Coloca el archivo 'listadoProductos.csv' en la carpeta 'data/'")
