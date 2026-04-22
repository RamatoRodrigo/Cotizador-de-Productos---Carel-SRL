# =============================
# TEST: Borroni Reader
# =============================

import sys
import os
from pathlib import Path  # ← AGREGAR ESTA LÍNEA

# Agregar la carpeta raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.readers.borroni_reader import BorroniReader
from utils.helpers import clean_string
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_borroni():
    """Prueba la lectura del PDF de Borroni"""

    pdf_path = "data/borroni.pdf"

    if not Path(pdf_path).exists():
        logger.error(f"❌ Archivo no encontrado: {pdf_path}")
        logger.info("   Por favor, coloca el PDF de Borroni en data/borroni.pdf")
        return

    logger.info(f"🔍 Probando lectura de {pdf_path}...")

    reader = BorroniReader()
    df = reader.read(pdf_path)

    if df.empty:
        logger.error("❌ No se extrajeron datos")
        return

    logger.info(f"\n✅ EXTRACCIÓN EXITOSA")
    logger.info(f"   Total de productos: {len(df)}")
    logger.info(f"\n   Columnas: {df.columns.tolist()}")

    # Estadísticas por tipo de producto
    logger.info(f"\n📊 PRODUCTOS POR TIPO:")
    for product_type, count in df['product_type'].value_counts().items():
        logger.info(f"   - {product_type}: {count}")

    # Estadísticas por acabado
    logger.info(f"\n🎨 PRODUCTOS POR ACABADO:")
    for finish, count in df['finish'].value_counts().items():
        logger.info(f"   - {finish}: {count}")

    # Mostrar ejemplos
    logger.info(f"\n📋 EJEMPLOS DE PRODUCTOS:")
    logger.info(f"{df.head(5).to_string()}")

    # Guardar CSV
    output_file = "data/borroni_extracted.csv"
    df.to_csv(output_file, index=False)
    logger.info(f"\n✅ Datos guardados en {output_file}")


if __name__ == '__main__':
    test_borroni()