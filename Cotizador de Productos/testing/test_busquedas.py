import sys
import os

# Path del proyecto
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.matchers.busqueda_service import (
    buscar_por_codigo,
    buscar_por_descripcion,
    buscar_general
)

path_mapeo = "ddbb/productos_mapeados_borroni.csv"

# Buscar por código
print("BUSQUEDA DEL CODIGO: >TUAAG2NC031Z")
print(buscar_por_codigo(">TUAAG2NC031Z", path_mapeo))

print("BUSQUEDA DE DESCRIPCIÓN: tuerca 1/4")
# Buscar por descripción
print(buscar_por_descripcion("tuerca 1/4", path_mapeo))
print(buscar_por_descripcion("tuerca 1/8", path_mapeo))