# =============================
# TEST: Efepe Parser
# =============================

import sys
import os
from pathlib import Path
import logging

# 🔥 primero configurar path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# ahora sí importar
from services.matchers.parser_efepe import parse_efepe_csv

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_efepe_parser():
    """Prueba el parsing del CSV de Efepe"""
    
    # paths
    input_path = os.path.join(BASE_DIR, "ddbb", "efepeSinParsear.csv")
    output_path = os.path.join(BASE_DIR, "ddbb", "efepeParseado.csv")
    
    # Validar que exista el archivo
    if not Path(input_path).exists():
        logger.error(f"❌ Archivo no encontrado: {input_path}")
        logger.info("   Por favor, ejecuta primero: python testing/test_efepe.py")
        return

    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info("\n🚀 Iniciando Efepe Parser...\n")
    
    # Ejecutar parsing
    df = parse_efepe_csv(input_path, output_path)
    
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
        logger.info(f"✅ Archivo guardado en: {output_path}")
    else:
        logger.error("❌ No se extrajeron datos")


if __name__ == '__main__':
    test_efepe_parser()