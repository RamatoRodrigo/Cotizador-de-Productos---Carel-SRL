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
    
    if "allen" in desc or "din 912" in desc:
        return "tornillo_allen"
    if "hexagonal" in desc or "hex" in desc or "din 933" in desc:
        return "tornillo_hexagonal"
    if "autofr" in desc or "autofrenante" in desc:
        return "tornillo_autofrenante"
    if "drywall" in desc or "dry wall" in desc:
        return "tornillo_drywall"
    if "tuerca" in desc:
        return "tuerca"
    if "arandela" in desc or "ale " in desc:
        return "arandela"
    if "bulón" in desc or "bulon" in desc:
        return "bulón"
    
    return "tornillo"


def detectar_forma(desc):
    """Detecta la forma del producto"""
    desc = desc.lower()
    
    if "cilindrica" in desc or "cil " in desc:
        return "cilindrica"
    if "conica" in desc or "cónica" in desc:
        return "conica"
    if "plana" in desc or "flat" in desc:
        return "plana"
    if "almenada" in desc or "castillo" in desc:
        return "almenada"
    
    return None


def detectar_sistema(desc):
    """Detecta si es métrico o imperial"""
    desc = desc.lower()
    
    if "/" in desc or "unc" in desc or "unf" in desc or "bsw" in desc:
        return "imperial"
    if re.search(r"\bm\d+", desc):
        return "metrico"
    
    return "metrico"


def detectar_acabado(desc):
    """Detecta el acabado del producto"""
    desc = desc.lower()
    
    if "zinc" in desc or "zincado" in desc:
        return "zinc"
    if "inox" in desc or "acero inoxidable" in desc or "a2" in desc or "a4" in desc:
        return "acero_inox"
    if "natural" in desc or "nat" in desc:
        return "natural"
    if "pavonado" in desc or "pav" in desc:
        return "pavonado"
    
    return None


# -------------------------
# Parseo métrico
# -------------------------

def parse_metrico(desc):
    """
    Parsea especificaciones métricas
    Ejemplos: 4 x 0.70 x 16, 3 x 0,50 x 30
    """
    desc_norm = normalizar(desc)
    
    diametro = None
    paso = None
    largo = None
    
    # Formato: número x número x número (ej: 4 x 0.70 x 16 o 3 x 0,50 x 30)
    match = re.search(r"(\d+\.?\d*)\s*x\s*(\d+\.?\d*)\s*x\s*(\d+\.?\d*)", desc_norm)
    if match:
        diametro = match.group(1)
        paso = match.group(2)
        largo = match.group(3)
        return diametro, paso, largo
    
    # Formato M8x1.25
    match = re.search(r"m\s*(\d+)[-x](\d+\.?\d*)", desc_norm)
    if match:
        diametro = f"M{match.group(1)}"
        paso = match.group(2)
        return diametro, paso, largo
    
    # Solo M8
    match = re.search(r"m\s*(\d+)(?:\s|$|[^\d])", desc_norm)
    if match:
        diametro = f"M{match.group(1)}"
        return diametro, paso, largo
    
    # Dos números: 4x30
    match = re.search(r"(\d+\.?\d*)\s*x\s*(\d+\.?\d*)", desc_norm)
    if match:
        num1 = float(match.group(1))
        num2 = float(match.group(2))
        
        if num1 <= 30:
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
    """Parsea especificaciones imperiales"""
    desc_norm = normalizar(desc)
    
    diametro = None
    paso = None
    largo = None
    
    # 1/4"-20 x 3/4"
    match = re.search(r"(\d+(?:/\d+)?)\s*[-x]\s*(\d+)\s*x\s*(\d+(?:/\d+)?)", desc_norm)
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
    """Extrae el grado de resistencia"""
    desc_norm = normalizar(desc)
    
    # Buscar "CALIDAD 12.9" o similar
    match = re.search(r"calidad\s+(\d+\.?\d*)", desc_norm)
    if match:
        return match.group(1)
    
    # Búsqueda directa de grados comunes
    grados = ["12.9", "10.9", "8.8", "5.8", "4.8", "4.6"]
    for grado in grados:
        if grado in desc_norm:
            return grado
    
    return None


# -------------------------
# Parser principal
# -------------------------

def parse_trusoni(input_path, output_path):
    """
    Parsea archivo Trusoni
    Estructura del CSV: codigo, descripcion, [campos vacíos], precio, proveedor, ...
    """

    # Leer sin headers para identificar la estructura
    df_raw = pd.read_csv(input_path, header=None, encoding="utf-8")
    
    # Identificar columnas relevantes
    # Estructura típica: col0=codigo, col1=descripcion, col3=precio, col4=proveedor
    resultados = []

    for idx, row in df_raw.iterrows():
        try:
            codigo = str(row[0]).strip() if pd.notna(row[0]) else ""
            descripcion = str(row[1]).strip() if pd.notna(row[1]) else ""
            precio = row[3] if pd.notna(row[3]) else None
            
            if not codigo or not descripcion or precio is None:
                continue
            
            desc_norm = normalizar(descripcion)
            
            # Detectar atributos
            tipo = detectar_tipo(desc_norm)
            forma = detectar_forma(desc_norm)
            acabado = detectar_acabado(desc_norm)
            sistema = detectar_sistema(desc_norm)
            grado = extraer_grado(desc_norm)
            
            # Parsear dimensiones
            diametro = None
            paso = None
            largo = None
            
            if sistema == "metrico":
                diametro, paso, largo = parse_metrico(desc_norm)
            else:
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
                "acabado": acabado,
                "precio_unitario": precio,
                "proveedor": "trusoni",
                "descripcion": descripcion
            })
        
        except Exception as e:
            print(f"⚠️ Error en fila {idx}: {e}")
            continue

    df_out = pd.DataFrame(resultados)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_out.to_csv(output_path, index=False, encoding="utf-8")

    print(f"✅ CSV parseado generado en: {output_path}")
    print(f"📊 Total procesados: {len(df_out)}")
    print("\n" + "="*150)
    print(df_out.head(15).to_string())
    print("="*150)

    return df_out