import sys
import os
from pathlib import Path
import pandas as pd

# Path base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Agregar src al path (ajustalo si tu estructura es distinta)
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.readers.trusoni_reader import read_trusoni


def test_trusoni_reader():
    input_path = os.path.join(BASE_DIR, "data", "trusoni.xlsx")
    output_path = os.path.join(BASE_DIR, "ddbb", "trusoniSinParsear.csv")

    # Ejecutar reader
    df = read_trusoni(input_path)

    # 🔍 Validaciones básicas
    assert df is not None, "El DataFrame es None"
    assert not df.empty, "El DataFrame está vacío"
    assert "codigo" in df.columns, "Falta columna codigo"
    assert "descripcion" in df.columns, "Falta columna descripcion"
    assert "precio_unitario" in df.columns, "Falta columna precio_unitario"

    # Crear carpeta si no existe
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Guardar CSV
    df.to_csv(output_path, index=False, encoding="utf-8")

    print(f"✅ CSV generado en: {output_path}")
    print(df.head())


if __name__ == "__main__":
    test_trusoni_reader()