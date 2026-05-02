import sys
from pathlib import Path
import pdfplumber
import csv

# ---------------------------
# Base del proyecto
# ---------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# Agregar raíz al path
sys.path.insert(0, str(BASE_DIR))

# Imports del proyecto
from services.readers.borroni_reader import BorroniReader

# ---------------------------
# Paths
# ---------------------------
pdf_path = BASE_DIR / "data" / "borroni.pdf"
output_path = BASE_DIR / "ddbb" / "borroni.csv"

# Crear carpeta si no existe
output_path.parent.mkdir(parents=True, exist_ok=True)


def test_borroni_parser():
    if not pdf_path.exists():
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
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["description", "measure", "unit_price"]
        )
        writer.writeheader()
        writer.writerows(all_products)

    print(f"\n✅ CSV generado: {output_path}")


if __name__ == "__main__":
    test_borroni_parser()