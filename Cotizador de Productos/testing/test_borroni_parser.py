# =============================
# TEST: Borroni Parser
# =============================

import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.matchers.parser_borroni import parse_borroni_csv
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_borroni_parser():
    """Prueba el parsing del CSV de Borroni"""
    
    input_csv = "ddbb/borroniSinParsear.csv"
    output_csv = "ddbb/borroniParseado.csv"
    
    # Validar que exista el archivo
    if not Path(input_csv).exists():
        logger.error(f"❌ Archivo no encontrado: {input_csv}")
        logger.info("   Por favor, ejecuta primero: python testing/test_borroni_excel.py")
        return
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    logger.info("\n🚀 Iniciando Borroni Parser...\n")
    
    # Ejecutar parsing
    df = parse_borroni_csv(input_csv, output_csv)
    
    if not df.empty:
        logger.info(f"\n{'='*150}")
        logger.info("📋 PRIMEROS 20 PRODUCTOS PARSEADOS:")
        logger.info(f"{'='*150}\n")
        
        # Mostrar primeros 20
        pd_options = __import__('pandas').set_option
        pd_options('display.max_columns', None)
        pd_options('display.max_colwidth', None)
        pd_options('display.width', None)
        
        print(df.head(20).to_string())
        
        logger.info(f"\n{'='*150}")
        logger.info("📊 INFORMACIÓN DEL DATASET:")
        logger.info(f"{'='*150}")
        logger.info(f"Total de filas: {len(df)}")
        logger.info(f"Columnas: {df.columns.tolist()}")
        
        logger.info(f"\n✅ Test completado exitosamente!")
        logger.info(f"✅ Archivo guardado en: {output_csv}")
    else:
        logger.error("❌ No se extrajeron datos")


if __name__ == '__main__':
    test_borroni_parser()