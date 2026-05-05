# =============================
# TEST: Product Matcher
# =============================

import sys
import os
from pathlib import Path

# Agregar la carpeta raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.matchers import MatchEngine
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_matcher():
    """Prueba el matching entre Carel y proveedores"""
    
    # Rutas
    carel_csv = "ddbb/carel_parseado.csv"
    trusoni_csv = "ddbb/trusoni.csv"
    output_dir = "ddbb/matchingsFiles"
    
    # Validar que existan los archivos
    if not Path(carel_csv).exists():
        logger.error(f"❌ Archivo no encontrado: {carel_csv}")
        return
    
    if not Path(trusoni_csv).exists():
        logger.error(f"❌ Archivo no encontrado: {trusoni_csv}")
        return
    
    # Crear directorio de salida si no existe
    os.makedirs(output_dir, exist_ok=True)
    
    # Crear engine
    logger.info("\n🚀 Iniciando Match Engine...\n")
    engine = MatchEngine(threshold=0.7)
    
    # Ejecutar matching
    result_df = engine.match_provider(
        carel_csv=carel_csv,
        provider_csv=trusoni_csv,
        provider_name="Trusoni",
        output_path=f"{output_dir}/trusoni_match.csv"
    )
    
    # Mostrar resultados
    if not result_df.empty:
        logger.info(f"\n{'='*80}")
        logger.info("📋 EJEMPLOS DE PRODUCTOS MATCHEADOS:")
        logger.info(f"{'='*80}\n")
        
        # Mostrar algunos exactos
        exact_matches = result_df[result_df['match_type'] == 'exact'].head(3)
        if not exact_matches.empty:
            logger.info("✅ EXACT MATCHES:")
            for _, row in exact_matches.iterrows():
                logger.info(f"\n   Carel: {row['carel_codigo']} - {row['carel_tipo']} {row['carel_diametro']}x{row['carel_paso']}")
                logger.info(f"   Match: {row['match_codigo']} - Precio: ${row['match_precio_unitario']}")
                logger.info(f"   Score: {row['match_score']}")
        
        # Mostrar algunos parciales
        partial_matches = result_df[result_df['match_type'] == 'partial'].head(3)
        if not partial_matches.empty:
            logger.info(f"\n{'─'*80}")
            logger.info("⚠️  PARTIAL MATCHES:")
            for _, row in partial_matches.iterrows():
                logger.info(f"\n   Carel: {row['carel_codigo']} - {row['carel_tipo']} {row['carel_diametro']}x{row['carel_paso']}")
                logger.info(f"   Match: {row['match_codigo']} - Precio: ${row['match_precio_unitario']}")
                logger.info(f"   Score: {row['match_score']}")
                logger.info(f"   Notas: {row['notas']}")
        
        # Mostrar algunos sin match
        no_matches = result_df[result_df['match_type'] == 'no_match'].head(3)
        if not no_matches.empty:
            logger.info(f"\n{'─'*80}")
            logger.info("❌ SIN COINCIDENCIA:")
            for _, row in no_matches.iterrows():
                logger.info(f"\n   Carel: {row['carel_codigo']} - {row['carel_tipo']} {row['carel_diametro']}x{row['carel_paso']}x{row['carel_largo']}")
        
        logger.info(f"\n{'='*80}\n")
    
    logger.info("✅ Test completado!")


if __name__ == '__main__':
    test_matcher()