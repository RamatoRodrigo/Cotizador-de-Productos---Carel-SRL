import sys
import os
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.matchers.parser_carel import parse_carel_listado

# Procesar
df = parse_carel_listado("ddbb/listadoProductos.csv", "ddbb/carel_parseado.csv")

print(df.head(20))