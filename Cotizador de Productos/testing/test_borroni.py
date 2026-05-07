# =============================
# TEST: Borroni Excel Reader
# =============================

import sys
import os
from pathlib import Path

# Agregar la carpeta raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.readers.borroni_reader import BorroniReader
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


def test_borroni_excel():
    """Prueba la lectura del Excel de Borroni"""
    
    excel_path = "data/borroni.xlsx"
    output_csv = "ddbb/borroniSinParsear.csv"
    
    # Validar que exista el Excel
    if not Path(excel_path).exists():
        logger.error(f"❌ Archivo no encontrado: {excel_path}")
        logger.info("   Por favor, coloca el archivo en data/borroni.xlsx")
        return
    
    # Crear directorio de salida si no existe
    os.makedirs(os.path.dirname(output_csv), exist_ok=True)
    
    logger.info("\n🚀 Iniciando BorroniReader...\n")
    
    # Crear reader y ejecutar
    reader = BorroniReader()
    df = reader.read_and_save(excel_path, output_csv)
    
    if not df.empty:
        logger.info(f"\n{'='*100}")
        logger.info("📋 PRIMEROS 10 PRODUCTOS:")
        logger.info(f"{'='*100}\n")
        
        # Mostrar primeros 10
        print(df.head(10).to_string())
        
        logger.info(f"\n{'='*100}")
        logger.info("📊 INFORMACIÓN DEL DATASET:")
        logger.info(f"{'='*100}")
        logger.info(f"Total de filas: {len(df)}")
        logger.info(f"Columnas: {df.columns.tolist()}")
        logger.info(f"Tipos de datos:\n{df.dtypes}")
        
        logger.info(f"\n✅ Test completado exitosamente!")
    else:
        logger.error("❌ No se extrajeron datos")


if __name__ == '__main__':
    test_borroni_excel()