import sys
import os
from pathlib import Path
import pdfplumber
import csv

# Path del proyecto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.readers.borroni_reader import BorroniReader


def test_borroni_parser():
    pdf_path = "Cotizador de Productos/data/borroni.pdf"

    if not Path(pdf_path).exists():
        print(f"❌ Archivo no encontrado: {pdf_path}")
        return

    reader = BorroniReader()
    all_products = []

    with pdfplumber.open(pdf_path) as pdf:
        print(f"\n📄 Total páginas: {len(pdf.pages)}")

        for page_num, page in enumerate(pdf.pages, start=1):
            products = reader.parse_page(page, page_num)

            print(f"Página {page_num}: {len(products)} productos")

            # Mostrar algunos ejemplos
            for p in products[:2]:
                print(p)

            all_products.extend(products)

    print("\n======================")
    print(f"TOTAL PRODUCTOS: {len(all_products)}")

    # Guardar CSV
    output_path = "borroni_debug.csv"

    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["description", "measure", "unit_price"])
        writer.writeheader()
        writer.writerows(all_products)

    print(f"\n✅ CSV generado: {output_path}")


if __name__ == "__main__":
    test_borroni_parser()