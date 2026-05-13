import pandas as pd
import os
import re
import unicodedata

TIPOS = [
    "tuerca",
    "tornillo",
    "bulon",
    "arandela",
    "esparrago",
    "varilla"
]

FORMAS = [
    "hexagonal",
    "allen",
    "tanque",
    "cilindrica"
]

GRADOS = [
    "g2",
    "g5",
    "g8"
]

ACABADOS = [
    "zinc",
    "inoxidable",
    "galvanizado",
    "negro",
    "dicro"
]

SISTEMAS_ROSCA = {
    "unc": ["unc", "nc"],
    "unf": ["unf", "nf"],
    "metrica": ["metrica", "m"]
}

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

def parsearBusqueda(texto):

    texto = normalizarTexto(texto)

    resultado = {}

    # =========================
    # TIPO
    # =========================

    for tipo in TIPOS:

        if tipo in texto:
            resultado["tipo"] = tipo
            break

    # =========================
    # GRADO
    # =========================

    for grado in GRADOS:

        if grado in texto:
            resultado["grado"] = grado
            break

    # =========================
    # ACABADO
    # =========================

    for acabado in ACABADOS:

        if acabado in texto:
            resultado["acabado"] = acabado
            break

    # =========================
    # FORMA
    # =========================

    for forma in FORMAS:

        if forma in texto:
            resultado["forma"] = forma
            break


    # =========================
    # SISTEMA ROSCA
    # =========================

    for canonico, aliases in SISTEMAS_ROSCA.items():

        for alias in aliases:

            if alias in texto:
                resultado["sistema_rosca"] = canonico
                break


    # =========================
    # DIAMETRO
    # =========================

    matchDiametro = re.search(r"\d+/\d+", texto)

    if matchDiametro:
        resultado["diametro"] = matchDiametro.group()

    return resultado


def buscarCoincidenciasDescripcion(df, textoBusqueda):

    atributos = parsearBusqueda(textoBusqueda)

    print("\nAtributos detectados:")
    print(atributos)

    resultados = df.copy()

    for columna, valor in atributos.items():

        if columna not in resultados.columns:
            continue

        resultados = resultados[
            resultados[columna]
            .fillna("")
            .astype(str)
            .apply(normalizarTexto)
            .str.contains(valor, na=False)
        ]

    return resultados


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

    df = pd.read_csv(path_csv)

    print("============= BUSCADOR CAREL =============")
    print("Escribí 'salir' para terminar.")
    print("Escribí 'limpiar' para limpiar pantalla.\n")

    while True:

        busqueda = input("Buscar: ").strip()

        # =========================
        # SALIR
        # =========================

        if busqueda.lower() in [
            "salir",
            "dejar de buscar"
        ]:

            print("Finalizando...")
            break

        # =========================
        # LIMPIAR
        # =========================

        if busqueda.lower() == "limpiar":

            os.system(
                "cls"
                if os.name == "nt"
                else "clear"
            )

            print("============= BUSCADOR CAREL =============")
            print("Escribí 'salir' para terminar.")
            print("Escribí 'limpiar' para limpiar pantalla.\n")

            continue

        # =========================
        # BUSQUEDA
        # =========================

        resultados = buscarCoincidenciasDescripcion(
            df,
            busqueda
        )

        print(f"\nMatches encontrados: {len(resultados)}\n")

        if resultados.empty:

            print("Sin coincidencias.\n")
            continue

        columnasMostrar = [
            "codigo",
            "tipo",
            "forma",
            "diametro",
            "paso",
            "largo",
            "grado",
            "sistema_rosca",
            "acabado",
            "descripcion"
        ]

        columnasExistentes = [
            col
            for col in columnasMostrar
            if col in resultados.columns
        ]

        print(
            resultados[columnasExistentes]
            .head(50)
            .to_string(index=False)
        )

        print("\n" + "=" * 100 + "\n")


if __name__ == "__main__":
    main()