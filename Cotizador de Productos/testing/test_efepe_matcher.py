# =============================
# TEST: Product Matcher (Efepe)
# =============================

import sys
import os
from pathlib import Path

# Agregar la carpeta raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.matchers.matcher import match_generico
import logging
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_matcher_efepe():
    """Prueba el matching genérico entre Carel y Efepe"""
    
    # Rutas
    carel_csv = "ddbb/carelParseado.csv"
    efepe_csv = "ddbb/efepeParseado.csv"
    output_dir = "ddbb/matchingFiles"
    output_file = f"{output_dir}/efepe_match.csv"
    
    # Validar que existan los archivos
    if not Path(carel_csv).exists():
        logger.error(f"❌ Archivo no encontrado: {carel_csv}")
        return
    
    if not Path(efepe_csv).exists():
        logger.error(f"❌ Archivo no encontrado: {efepe_csv}")
        return
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Ejecutar matching
    logger.info("\n🚀 Iniciando Match Engine (Genérico) - Efepe...\n")
    
    df_matches, df_sin_match = match_generico(
        master_path=carel_csv,
        proveedor_path=efepe_csv,
        output_path=output_file,
        proveedor_nombre="Efepe",
        umbral_minimo=60,
        peso_atributos=0.6,
        debug=False
    )
    
    # Análisis detallado
    if not df_matches.empty:
        logger.info(f"\n{'='*100}")
        logger.info("📊 ANÁLISIS DETALLADO DE MATCHES")
        logger.info(f"{'='*100}\n")
        
        # Distribución por tipo
        logger.info("📈 Matches por TIPO:")
        tipo_dist = df_matches.groupby('tipo_proveedor').size()
        for tipo, count in tipo_dist.items():
            logger.info(f"   - {tipo}: {count}")
        
        # Distribución por score
        logger.info(f"\n📊 Distribución de SCORES:")
        logger.info(f"   - Excelentes (90-100): {len(df_matches[df_matches['score_final'] >= 90])}")
        logger.info(f"   - Muy buenos (80-89): {len(df_matches[(df_matches['score_final'] >= 80) & (df_matches['score_final'] < 90)])}")
        logger.info(f"   - Buenos (70-79): {len(df_matches[(df_matches['score_final'] >= 70) & (df_matches['score_final'] < 80)])}")
        
        # Top 10 matches por score
        logger.info(f"\n{'─'*100}")
        logger.info("⭐ TOP 10 MATCHES (Mejor Score):")
        logger.info(f"{'─'*100}\n")
        
        top_matches = df_matches.nlargest(10, 'score_final')
        for idx, (_, row) in enumerate(top_matches.iterrows(), 1):
            logger.info(f"{idx}. Score: {row['score_final']:.1f} (Attr: {row['score_atributos']:.1f}, Desc: {row['score_descripcion']:.1f})")
            logger.info(f"   Carel:    {row['id_master']} - {row['tipo_master']} | Diam: {row['diametro_master']} Paso: {row['grado_master']}")
            logger.info(f"   Borroni:  {row['id_proveedor']} - {row['tipo_proveedor']} | Diam: {row['diametro_proveedor']} Paso: {row['largo_proveedor']}")
            logger.info(f"   Precio:   ${row['precio_unitario']}")
            logger.info("")
        
        # Matches mediocres
        mediocre = df_matches[(df_matches['score_final'] >= 70) & (df_matches['score_final'] < 80)]
        if not mediocre.empty:
            logger.info(f"{'─'*100}")
            logger.info(f"⚠️  MATCHES MEDIOCRES ({len(mediocre)} registros, Score 70-79):")
            logger.info(f"{'─'*100}\n")
            
            for idx, (_, row) in enumerate(mediocre.head(5).iterrows(), 1):
                logger.info(f"{idx}. Score: {row['score_final']:.1f}")
                logger.info(f"   Carel:    {row['id_master']} - {row['descripcion_master'][:60]}")
                logger.info(f"   Efepe:  {row['id_proveedor']} - {row['descripcion_proveedor'][:60]}")
                logger.info("")
    
    # Análisis de sin match
    if not df_sin_match.empty:
        logger.info(f"{'─'*100}")
        logger.info(f"❌ ANÁLISIS DE SIN MATCH ({len(df_sin_match)} registros)")
        logger.info(f"{'─'*100}\n")
        
        # Distribución por tipo
        logger.info("📊 Sin match por TIPO:")
        tipo_no_match = df_sin_match.groupby('tipo_proveedor').size()
        for tipo, count in tipo_no_match.items():
            logger.info(f"   - {tipo}: {count}")
        
        # Ejemplos
        logger.info(f"\n📋 EJEMPLOS (primeros 5):")
        for idx, (_, row) in enumerate(df_sin_match.head(5).iterrows(), 1):
            logger.info(f"\n{idx}. {row['id_proveedor']} - {row['tipo_proveedor']}")
            logger.info(f"   Descripción: {row['descripcion_proveedor'][:70]}")
            logger.info(f"   Score más cercano: {row['score_final']:.1f}")
    
    # Resumen final
    logger.info(f"\n{'='*100}")
    logger.info("✅ TEST COMPLETADO")
    logger.info(f"{'='*100}\n")
    logger.info(f"📊 RESUMEN:")
    logger.info(f"   - Matches encontrados: {len(df_matches)}")
    logger.info(f"   - Sin match: {len(df_sin_match)}")
    logger.info(f"   - Total procesados: {len(df_matches) + len(df_sin_match)}")
    if len(df_matches) + len(df_sin_match) > 0:
        tasa = (len(df_matches) / (len(df_matches) + len(df_sin_match)) * 100)
        logger.info(f"   - Tasa de éxito: {tasa:.1f}%\n")


if __name__ == '__main__':
    test_matcher_efepe()