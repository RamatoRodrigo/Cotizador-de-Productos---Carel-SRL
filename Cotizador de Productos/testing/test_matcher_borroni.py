import sys
import os

# ---------------------------
# FIX PATHS (CLAVE)
# ---------------------------
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.matchers.matcher_borroni_service import generar_mapeo, buscar_por_codigo


# ---------------------------
# BASE DIR
# ---------------------------
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

path_productos = os.path.join(BASE_DIR, "ddbb", "listadoProductos.csv")
path_borroni = os.path.join(BASE_DIR, "ddbb", "borroni.csv")
output_path = os.path.join(BASE_DIR, "ddbb", "productos_mapeados_borroni.csv")


# ---------------------------
# TEST
# ---------------------------
if __name__ == "__main__":
    generar_mapeo(path_productos, path_borroni, output_path)

    buscar_por_codigo("TUAAG2NC047Z", output_path)