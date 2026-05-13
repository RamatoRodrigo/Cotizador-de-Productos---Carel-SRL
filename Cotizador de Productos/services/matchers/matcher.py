import pandas as pd
import os
import re
from rapidfuzz import fuzz


# -------------------------
# Helpers
# -------------------------

def normalizar(texto):
    return (
        str(texto)
        .lower()
        .replace(",", ".")
        .replace("-", " ")
        .replace("x", " x ")
        .replace("  ", " ")
        .strip()
    )


def get_value(row, key, default=""):
    """Helper para obtener valor de una Series de pandas de forma segura"""
    try:
        value = row.get(key) if hasattr(row, 'get') else row[key]
        return value if pd.notna(value) else default
    except (KeyError, TypeError):
        return default


def calcular_score_atributos(row_master, row_proveedor):
    """
    Calcula score basado en atributos coincidentes
    """
    score = 0
    weight = 0
    
    # TIPO (peso: 30%)
    tipo_master = get_value(row_master, "tipo")
    tipo_prov = get_value(row_proveedor, "tipo")
    if tipo_master and tipo_prov:
        weight += 30
        if str(tipo_master).lower() == str(tipo_prov).lower():
            score += 30
    
    # FORMA (peso: 15%)
    forma_master = get_value(row_master, "forma")
    forma_prov = get_value(row_proveedor, "forma")
    if forma_master and forma_prov:
        weight += 15
        if str(forma_master).lower() == str(forma_prov).lower():
            score += 15
    
    # DIAMETRO (peso: 20%)
    diam_master = get_value(row_master, "diametro")
    diam_prov = get_value(row_proveedor, "diametro")
    if diam_master and diam_prov:
        weight += 20
        if str(diam_master).lower() == str(diam_prov).lower():
            score += 20
    
    # LARGO (peso: 15%)
    largo_master = get_value(row_master, "largo")
    largo_prov = get_value(row_proveedor, "largo")
    if largo_master and largo_prov:
        weight += 15
        if str(largo_master).lower() == str(largo_prov).lower():
            score += 15
    
    # GRADO (peso: 10%)
    grado_master = get_value(row_master, "grado")
    grado_prov = get_value(row_proveedor, "grado")
    if grado_master and grado_prov:
        weight += 10
        if str(grado_master).lower() == str(grado_prov).lower():
            score += 10
    
    # ACABADO (peso: 10%)
    acabado_master = get_value(row_master, "acabado")
    acabado_prov = get_value(row_proveedor, "acabado")
    if acabado_master and acabado_prov:
        weight += 10
        if str(acabado_master).lower() == str(acabado_prov).lower():
            score += 10
    
    # Normalizar a 0-100
    if weight > 0:
        return (score / weight) * 100
    
    return 0


def calcular_score_descripcion(desc_master, desc_proveedor):
    """
    Calcula score de similitud entre descripciones usando fuzzy matching
    """
    desc_master_norm = normalizar(str(desc_master))
    desc_proveedor_norm = normalizar(str(desc_proveedor))
    
    # Token set ratio da mejor resultado para descripciones largas
    return fuzz.token_set_ratio(desc_master_norm, desc_proveedor_norm)


def calcular_score_final(score_atributos, score_desc, peso_atributos=0.6):
    """
    Combina score de atributos y descripción
    peso_atributos: importancia de los atributos vs descripción (0-1)
    """
    return (score_atributos * peso_atributos) + (score_desc * (1 - peso_atributos))


# -------------------------
# Matcher principal
# -------------------------

def match_generico(master_path, proveedor_path, output_path, proveedor_nombre="proveedor", 
                   umbral_minimo=70, peso_atributos=0.6, debug=False, max_candidatos=50):
    """
    Matcher genérico para todos los proveedores (OPTIMIZADO)
    
    Args:
        master_path: CSV del catálogo master (Carel)
        proveedor_path: CSV del proveedor a matchear
        output_path: Ruta para guardar resultados
        proveedor_nombre: Nombre del proveedor
        umbral_minimo: Score mínimo para considerar un match válido
        peso_atributos: Peso de atributos vs descripción (0.6 = 60% atributos, 40% desc)
        debug: Mostrar detalles del matching
        max_candidatos: Máximo de candidatos a evaluar (para optimizar velocidad)
    """
    
    print(f"📖 Cargando archivos...")
    df_master = pd.read_csv(master_path, encoding="utf-8")
    df_proveedor = pd.read_csv(proveedor_path, encoding="utf-8")
    
    # Normalizar nombres de columnas
    df_master.columns = df_master.columns.str.strip().str.lower()
    df_proveedor.columns = df_proveedor.columns.str.strip().str.lower()
    
    print(f"✅ Master cargado: {len(df_master)} registros")
    print(f"✅ Proveedor ({proveedor_nombre}) cargado: {len(df_proveedor)} registros")
    
    resultados = []
    sin_match = []
    
    print(f"\n🔍 Matcheando...")
    
    for idx, row_prov in df_proveedor.iterrows():
        
        # Mostrar progreso cada 50 registros
        if (idx + 1) % 50 == 0:
            print(f"   Procesados {idx + 1}/{len(df_proveedor)}...")
        
        tipo_prov = str(get_value(row_prov, "tipo", "otro")).lower()
        diametro_prov = get_value(row_prov, "diametro")
        largo_prov = get_value(row_prov, "largo")
        
        # Filtrar candidatos por tipo (es lo más importante)
        candidatos = df_master.copy()
        
        if tipo_prov != "otro":
            candidatos = candidatos[
                candidatos["tipo"].fillna("otro").astype(str).str.lower() == tipo_prov
            ]
        
        # Filtro secundario por diámetro si existe
        if diametro_prov and diametro_prov != "":
            candidatos_diam = candidatos[
                candidatos["diametro"].fillna("").astype(str).str.lower() == 
                str(diametro_prov).lower()
            ]
            if not candidatos_diam.empty:
                candidatos = candidatos_diam
        
        # Filtro secundario por largo si existe
        if largo_prov and largo_prov != "":
            candidatos_largo = candidatos[
                candidatos["largo"].fillna("").astype(str).str.lower() == 
                str(largo_prov).lower()
            ]
            if not candidatos_largo.empty:
                candidatos = candidatos_largo
        
        # Si no hay candidatos, usar todos del master del mismo tipo
        if candidatos.empty and tipo_prov != "otro":
            candidatos = df_master[
                df_master["tipo"].fillna("otro").astype(str).str.lower() == tipo_prov
            ]
        
        # Si aún no hay candidatos, usar todo el master
        if candidatos.empty:
            candidatos = df_master
        
        # ⚡ OPTIMIZACIÓN: Limitar candidatos a evaluar
        if len(candidatos) > max_candidatos:
            # Priorizar por similitud de descripción rápida
            desc_prov = str(get_value(row_prov, "descripcion", ""))
            candidatos["desc_sim"] = candidatos["descripcion"].fillna("").astype(str).apply(
                lambda x: fuzz.token_sort_ratio(normalizar(x), normalizar(desc_prov))
            )
            candidatos = candidatos.nlargest(max_candidatos, "desc_sim")
            candidatos = candidatos.drop(columns=["desc_sim"])
        
        best_score_attr = 0
        best_score_desc = 0
        best_score_final = 0
        best_match = None
        
        # Evaluar todos los candidatos
        for _, row_master in candidatos.iterrows():
            
            # Score por atributos
            score_attr = calcular_score_atributos(row_master, row_prov)
            
            # Score por descripción
            desc_master = str(get_value(row_master, "descripcion", ""))
            desc_prov = str(get_value(row_prov, "descripcion", ""))
            score_desc = calcular_score_descripcion(desc_master, desc_prov)
            
            # Score final
            score_final = calcular_score_final(score_attr, score_desc, peso_atributos)
            
            if score_final > best_score_final:
                best_score_final = score_final
                best_score_attr = score_attr
                best_score_desc = score_desc
                best_match = row_master
        
        # Guardar resultado si cumple umbral
        if best_match is not None and best_score_final >= umbral_minimo:
            
            resultado = {
                "id_master": get_value(best_match, "codigo", ""),
                "descripcion_master": get_value(best_match, "descripcion", ""),
                "tipo_master": get_value(best_match, "tipo", ""),
                "diametro_master": get_value(best_match, "diametro", ""),
                "largo_master": get_value(best_match, "largo", ""),
                "grado_master": get_value(best_match, "grado", ""),
                "acabado_master": get_value(best_match, "acabado", ""),
                "id_proveedor": get_value(row_prov, "codigo", ""),
                "descripcion_proveedor": get_value(row_prov, "descripcion", ""),
                "tipo_proveedor": get_value(row_prov, "tipo", ""),
                "diametro_proveedor": get_value(row_prov, "diametro", ""),
                "largo_proveedor": get_value(row_prov, "largo", ""),
                "precio_unitario": get_value(row_prov, "precio_unitario", ""),
                "proveedor": proveedor_nombre,
                "score_atributos": round(best_score_attr, 2),
                "score_descripcion": round(best_score_desc, 2),
                "score_final": round(best_score_final, 2)
            }
            
            resultados.append(resultado)
            
            if debug and idx < 5:
                print(f"\n✅ {idx+1}. Score: {best_score_final:.1f}")
                print(f"   Master: {get_value(best_match, 'codigo')} - {get_value(best_match, 'tipo')}")
                print(f"   Prov:   {get_value(row_prov, 'codigo')} - {get_value(row_prov, 'tipo')}")
        
        else:
            sin_match.append({
                "id_proveedor": get_value(row_prov, "codigo", ""),
                "descripcion_proveedor": get_value(row_prov, "descripcion", ""),
                "tipo_proveedor": get_value(row_prov, "tipo", ""),
                "score_final": round(best_score_final, 2) if best_match is not None else 0,
                "proveedor": proveedor_nombre
            })
            
            if debug and idx < 5:
                score_display = best_score_final if best_match is not None else 0
                print(f"\n❌ {idx+1}. Sin match válido (score: {score_display:.1f})")
                print(f"   Prov: {get_value(row_prov, 'codigo')} - {get_value(row_prov, 'tipo')}")
    
    # Crear DataFrames
    df_result = pd.DataFrame(resultados)
    df_sin_match = pd.DataFrame(sin_match)
    
    # Guardar resultados
    os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)
    
    df_result.to_csv(output_path, index=False, encoding="utf-8")
    
    # Guardar registros sin match
    sin_match_path = output_path.replace(".csv", "_sin_match.csv")
    df_sin_match.to_csv(sin_match_path, index=False, encoding="utf-8")
    
    # Estadísticas
    print(f"\n{'='*100}")
    print(f"📊 RESULTADOS DEL MATCHING ({proveedor_nombre})")
    print(f"{'='*100}")
    print(f"✅ Matches encontrados: {len(df_result)}")
    print(f"❌ Sin match: {len(df_sin_match)}")
    tasa_matching = (len(df_result) / len(df_proveedor) * 100) if len(df_proveedor) > 0 else 0
    print(f"📈 Tasa de matching: {tasa_matching:.1f}%")
    
    if not df_result.empty:
        print(f"\n📊 Score promedio de matches: {df_result['score_final'].mean():.1f}")
        print(f"   - Score atributos: {df_result['score_atributos'].mean():.1f}")
        print(f"   - Score descripción: {df_result['score_descripcion'].mean():.1f}")
    
    print(f"\n💾 Resultados guardados en: {output_path}")
    print(f"💾 Sin matches en: {sin_match_path}")
    print(f"{'='*100}\n")
    
    # Mostrar ejemplos
    if not df_result.empty:
        print("📋 EJEMPLOS DE MATCHES (primeros 10):")
        print(df_result[[
            "id_proveedor", "tipo_proveedor", "diametro_proveedor", "largo_proveedor",
            "id_master", "tipo_master", "score_final"
        ]].head(10).to_string(index=False))
    
    if not df_sin_match.empty:
        print("\n⚠️  EJEMPLOS SIN MATCH (primeros 10):")
        print(df_sin_match[[
            "id_proveedor", "tipo_proveedor", "descripcion_proveedor", "score_final"
        ]].head(10).to_string(index=False))
    
    return df_result, df_sin_match


# -------------------------
# Ejemplo de uso
# -------------------------

if __name__ == "__main__":
    
    # Matchear Trusoni vs Carel Master
    df_matches, df_sin_match = match_generico(
        master_path="ddbb/carelParseado.csv",
        proveedor_path="ddbb/trusoniParseado.csv",
        output_path="ddbb/matches_trusoni_vs_carel.csv",
        proveedor_nombre="trusoni",
        umbral_minimo=70,
        peso_atributos=0.6,
        debug=True
    )