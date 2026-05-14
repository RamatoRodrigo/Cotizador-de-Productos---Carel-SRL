import pandas as pd
import os
import re
import unicodedata
from tabulate import tabulate

# =========================================================
# EJEMPLOS DE BUSQUEDAS
# =========================================================
"""
bulon hexagonal m6 x 45 g8 zinc
tirafondo 1/4 x 2
tuerca unf inoxidable
prisionero allen m8
remache pop
tarugo fisher
bulon hexagonal g2 1/2 x 7 zinc
arandela grower
"""
# =========================================================
# DICCIONARIOS
# =========================================================

TIPOS = {
    "clavo": [
        "clavo",
        "clavos",
        "punta paris",
        "cabeza perdida",
        "cabeza chata",
        "cajonero"
    ],

    "tornillo_drywall": [
        "drywall",
        "dry wall"
    ],

    "tornillo_fix": [
        "p/mad",
        "fix"
    ],

    "bulón": [
        "bulon",
        "bulón",
        "bul "
    ],

    "tuerca": [
        "tuerca"
    ],

    "tornillo": [
        "tornillo",
        "cabeza tanque"
    ],

    "prisionero": [
        "prisionero",
        "pris"
    ],

    "tirafondo": [
        "tirafondo"
    ],

    "arandela": [
        "arandela"
    ],

    "espárrago": [
        "esparrago",
        "espárrago"
    ],

    "perno": [
        "perno"
    ],

    "varilla": [
        "varilla"
    ],

    "remache": [
        "remache"
    ],

    "pasador": [
        "pasador"
    ],

    "chaveta": [
        "chaveta"
    ],

    "tarugo": [
        "tarugo"
    ],

    "abrazadera": [
        "abrazadera"
    ],

    "grampas": [
        "grampa",
        "grampas"
    ],

    "pitones": [
        "piton",
        "pitones",
        "pytones"
    ]
}

FORMAS = [
    "hexagonal",
    "allen",
    "tanque",
    "cilindrica",
    "gota",
    "t2",
    "philips",
    "phillips",
    "ranurada",
    "flange",
    "copa"
]

GRADOS = [
    "g2",
    "g5",
    "g8",
    "4.6",
    "5.6",
    "8.8",
    "10.9",
    "12.9"
]

ACABADOS = [
    "zinc",
    "zincado",
    "galvanizado",
    "negro",
    "dacro",
    "dicro",
    "inoxidable",
    "natural",
    "latonado",
    "fosfatizado"
]

SISTEMAS_ROSCA = {
    "unc": ["unc", "nc"],
    "unf": ["unf", "nf"],
    "whitworth": ["wh", "bsw"],
    "metrica": ["metrica", "metrica"]
}

# =========================================================
# NORMALIZAR
# =========================================================

def normalizarTexto(texto):

    texto = str(texto).lower()

    texto = unicodedata.normalize(
        'NFKD',
        texto
    ).encode(
        'ascii',
        'ignore'
    ).decode(
        'utf-8'
    )

    return texto


# =========================================================
# PARSEAR BUSQUEDA
# =========================================================

def parsearBusqueda(texto):

    texto = normalizarTexto(texto)

    resultado = {}

    # =====================================================
    # TIPO
    # =====================================================

    for tipo, aliases in TIPOS.items():

        encontrado = False

        for alias in aliases:

            if alias in texto:
                resultado["tipo"] = tipo
                encontrado = True
                break

        if encontrado:
            break

    # Detecta "tor" aislado
    if "tipo" not in resultado:

        if (
            re.search(r"\btor\b", texto)
            or re.search(r"\btorn\b", texto)
        ):
            resultado["tipo"] = "tornillo"

    # =====================================================
    # GRADO
    # =====================================================

    for grado in GRADOS:

        if grado in texto:
            resultado["grado"] = grado
            break

    # =====================================================
    # ACABADO
    # =====================================================

    for acabado in ACABADOS:

        if acabado in texto:
            resultado["acabado"] = acabado
            break

    # =====================================================
    # FORMA
    # =====================================================

    for forma in FORMAS:

        if forma in texto:
            resultado["forma"] = forma
            break

    # =====================================================
    # SISTEMA ROSCA
    # =====================================================

    for canonico, aliases in SISTEMAS_ROSCA.items():

        for alias in aliases:

            if re.search(rf"\b{re.escape(alias)}\b", texto):

                resultado["sistema_rosca"] = canonico
                break

    # =====================================================
    # DIAMETRO METRICO
    # M6 / M8 / M10
    # =====================================================

    match = re.search(r"\bm\s*(\d+)\b", texto)

    if match:

        resultado["diametro"] = f"M{match.group(1)}"

    else:

        # =================================================
        # DIAMETRO IMPERIAL
        #
        # Soporta:
        # 1/2
        # 3/8
        # 1 1/2
        # 1.1/2
        #
        # Evita:
        # G2
        # G5
        # G8
        # =================================================

        candidatos = re.finditer(

            r"(?<![a-z0-9])"
            r"(\d+\s+\d+/\d+|\d+[.,]\d+/\d+|\d+/\d+|\d+)"
            r"(?![a-z0-9])",

            texto
        )

        for match in candidatos:

            candidato = (
                match.group(1)
                .replace(",", ".")
                .strip()
            )

            # Ignora enteros solos
            # para evitar G2/G5/G8
            if re.fullmatch(r"\d+", candidato):
                continue

            resultado["diametro"] = candidato
            break

    # =====================================================
    # LARGO
    # x45 / x 45
    # =====================================================

    match = re.search(r"x\s*(\d+)", texto)

    if match:
        resultado["largo"] = match.group(1)

    return resultado


# =========================================================
# BUSCAR
# =========================================================

def buscarCoincidenciasDescripcion(df, textoBusqueda):

    atributos = parsearBusqueda(textoBusqueda)

    print("\nAtributos detectados:")
    print(atributos)

    resultados = df.copy()

    for columna, valor in atributos.items():

        if columna not in resultados.columns:
            continue

        valor_normalizado = normalizarTexto(valor)

        resultados = resultados[
            resultados[columna]
            .fillna("")
            .astype(str)
            .apply(normalizarTexto)
            .str.contains(
                re.escape(valor_normalizado),
                na=False
            )
        ]

    return resultados

# =========================================================
# MAIN
# =========================================================

def main():

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    path_csv = os.path.join(
        BASE_DIR,
        "ddbb",
        "carelParseado.csv"
    )

    if not os.path.exists(path_csv):

        print(f"\nNo se encontró el archivo:\n{path_csv}\n")
        return

    # =====================================================
    # CARGA CSV
    # =====================================================

    df = pd.read_csv(
        path_csv,
        dtype=str
    ).fillna("")

    print("\n============= BUSCADOR CAREL =============")
    print("Escribí 'salir' para terminar.")
    print("Escribí 'limpiar' para limpiar pantalla.\n")

    # =====================================================
    # LOOP PRINCIPAL
    # =====================================================

    while True:

        try:

            busqueda = input("Buscar: ").strip()

        except KeyboardInterrupt:

            print("\nFinalizando...")
            break

        # =================================================
        # VALIDACION
        # =================================================

        if not busqueda:
            continue

        comando = busqueda.lower()

        # =================================================
        # SALIR
        # =================================================

        if comando in [
            "salir",
            "exit",
            "quit",
            "dejar de buscar"
        ]:

            print("\nFinalizando...")
            break

        # =================================================
        # LIMPIAR
        # =================================================

        if comando == "limpiar":

            os.system(
                "cls"
                if os.name == "nt"
                else "clear"
            )

            print("\n============= BUSCADOR CAREL =============")
            print("Escribí 'salir' para terminar.")
            print("Escribí 'limpiar' para limpiar pantalla.\n")

            continue

        # =================================================
        # BUSQUEDA
        # =================================================

        resultados = buscarCoincidenciasDescripcion(
            df,
            busqueda
        )

        print(f"\nMatches encontrados: {len(resultados)}\n")

        if resultados.empty:

            print("Sin coincidencias.\n")
            print("=" * 120)
            continue

        # =================================================
        # COLUMNAS A MOSTRAR
        # =================================================

        columnasMostrar = [
            "codigo",
            "tipo",
            "forma",
            "diametro",
            "paso",
            "largo",
            "grado",
            "sistema",
            "sistema_rosca",
            "acabado",
            "descripcion"
        ]

        columnasExistentes = [
            col
            for col in columnasMostrar
            if col in resultados.columns
        ]

        # =================================================
        # OUTPUT
        # =================================================

        mostrar = (
            resultados[columnasExistentes]
            .head(50)
            .copy()
        )

        print(
            tabulate(
                mostrar,
                headers="keys",
                tablefmt="fancy_grid",
                showindex=False
            )
        )

        if len(resultados) > 50:

            print(
                f"\nMostrando primeros 50 de "
                f"{len(resultados)} resultados."
            )

        print("\n" + "=" * 120 + "\n")


# =========================================================
# ENTRYPOINT
# =========================================================

if __name__ == "__main__":
    main()
