import os
import sys

# 🔥 primero configurar path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

# ahora sí importar
from services.matchers.parser_trusoni import parse_trusoni

# paths
input_path = os.path.join(BASE_DIR, "ddbb", "trusoniSinParsear.csv")
output_path = os.path.join(BASE_DIR, "ddbb", "trusoniParseado.csv")

# debug (opcional pero útil)
print("INPUT:", input_path, os.path.exists(input_path))
print("OUTPUT:", output_path)

parse_trusoni(input_path, output_path)