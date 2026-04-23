# =============================
# TEST: Borroni Reader
# =============================

import sys
import os
from pathlib import Path

# Agregar la carpeta raíz del proyecto al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.readers.borroni_reader import BorroniReader
from utils.helpers import clean_string
import pandas as pd
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_borroni():
    import pdfplumber

    pdf_path = "Cotizador de Productos/data/borroni.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return

    print(f"\n🔍 MOSTRANDO TABLAS DE: {pdf_path}")

    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            print(f"\n============================")
            print(f"📄 PÁGINA {page_num}")
            print(f"============================")

            tables = page.extract_tables()

            if not tables:
                print("❌ No se encontraron tablas")
                continue

            print(f"🔢 Tablas encontradas: {len(tables)}")

            for t_idx, table in enumerate(tables):
                print(f"\n--- TABLA {t_idx + 1} ---")

                for row_idx, row in enumerate(table):
                    print(f"{row_idx:02d} | {row}")

if __name__ == '__main__':
    test_borroni()