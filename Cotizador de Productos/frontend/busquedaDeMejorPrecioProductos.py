# frontend/busquedaDeMejorPrecioProductos.py

import pandas as pd
import os

# ==========================================
# IMPORTAR BUSCADOR MASTER
# ==========================================

from busquedaDescripcionMaster import (
    buscarCoincidenciasDescripcion
)

# ==========================================
# CONFIG MARGENES
# ==========================================

MARGEN_1 = 0.28
MARGEN_2 = 0.36

# ==========================================
# CONFIG PROVEEDORES
# ==========================================

PROVEEDORES = {
    "Borroni": "borroni_match.csv",

    # FUTUROS
    "EFEPE": "efepe_match.csv",
    # "BM": "bm_match.csv",
    # "Fleb": "fleb_match.csv",
}

# ==========================================
# CARGAR MASTER CAREL
# ==========================================

def cargarMasterCarel():

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    path_master = os.path.join(
        BASE_DIR,
        "ddbb",
        "carelParseado.csv"
    )

    df = pd.read_csv(path_master)

    return df

# ==========================================
# CARGAR MATCHERS
# ==========================================

def cargarMatchers():

    BASE_DIR = os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )

    path_matching = os.path.join(
        BASE_DIR,
        "ddbb",
        "matchingFiles"
    )

    dataframes = {}

    for proveedor, archivo in PROVEEDORES.items():

        path_csv = os.path.join(
            path_matching,
            archivo
        )

        if not os.path.exists(path_csv):

            print(f"❌ No existe {archivo}")
            continue

        df = pd.read_csv(path_csv)

        dataframes[proveedor] = df

        print(f"✅ Matcher cargado: {proveedor}")

    return dataframes

# ==========================================
# BUSCAR PRODUCTOS EN MATCHER
# ==========================================

def buscarProductoMatcher(dfMatcher, codigoMaster):

    if "id_master" not in dfMatcher.columns:

        return pd.DataFrame()

    resultados = dfMatcher[

        dfMatcher["id_master"]
        .fillna("")
        .astype(str)
        .str.lower()

        == str(codigoMaster).lower()
    ]

    return resultados

# ==========================================
# OBTENER MEJOR PRECIO
# ==========================================

def obtenerMejorPrecio(resultadosPorProveedor):

    mejorPrecio = None
    mejorProveedor = None

    for proveedor, resultados in resultadosPorProveedor.items():

        if resultados.empty:
            continue

        # Ordenar por score_final
        if "score_final" in resultados.columns:

            resultados = resultados.sort_values(
                by="score_final",
                ascending=False
            )

        fila = resultados.iloc[0]

        if "precio_unitario" not in fila:
            continue

        precio = fila["precio_unitario"]

        if pd.isna(precio):
            continue

        if (
            mejorPrecio is None
            or precio < mejorPrecio
        ):

            mejorPrecio = precio
            mejorProveedor = proveedor

    return mejorProveedor, mejorPrecio

# ==========================================
# GENERAR COTIZACION
# ==========================================

def generarCotizacion(productosSeleccionados, matchers):

    salida = []

    for producto in productosSeleccionados:
        codigo = producto["codigo"]
        descripcion = producto["descripcion"]
        cantidad = producto["cantidad"]

        resultadosPorProveedor = {}
        for proveedor, dfMatcher in matchers.items():
            resultados = buscarProductoMatcher(dfMatcher, codigo)
            resultadosPorProveedor[proveedor] = resultados

        mejorProveedor, mejorPrecio = obtenerMejorPrecio(resultadosPorProveedor)

        if mejorPrecio is None:
            precio28 = precio36 = total28 = total36 = None
        else:
            precio28 = round(mejorPrecio * (1 + MARGEN_1), 2)
            precio36 = round(mejorPrecio * (1 + MARGEN_2), 2)
            total28 = round(precio28 * cantidad, 2)
            total36 = round(precio36 * cantidad, 2)

        # ==============================
        # ARMAR FILA DE SALIDA
        # ==============================
        fila = {
            "Descripcion pieza": descripcion,
            "Cantidad": cantidad,
        }

        # Insertar proveedores aquí
        for proveedor, resultados in resultadosPorProveedor.items():
            if resultados is None or resultados.empty:
                fila[f"{proveedor} ($/unidad)"] = None
            else:
                fila[f"{proveedor} ($/unidad)"] = resultados.iloc[0]["precio_unitario"]

        # Luego las columnas de sugerido y cálculos
        fila.update({
            "Proveedor sugerido": mejorProveedor,
            "Precio base": mejorPrecio,
            "Precio sugerido +28%": precio28,
            "Total +28%": total28,
            "Precio sugerido +36%": precio36,
            "Total +36%": total36
        })

        salida.append(fila)

    return pd.DataFrame(salida)


# ==========================================
# MAIN
# ==========================================

def main():

    os.system(
        "cls"
        if os.name == "nt"
        else "clear"
    )

    print("============= COTIZADOR =============\n")

    # ======================================
    # CARGAR ARCHIVOS
    # ======================================

    dfMaster = cargarMasterCarel()

    matchers = cargarMatchers()

    productosSeleccionados = []

    # ======================================
    # LOOP PRINCIPAL
    # ======================================

    while True:

        print("\n")

        descripcionBusqueda = input(
            "Ejemplo de busqueda: bulon hexagonal g2 1/2 x 7 zinc\n"
            "Buscar producto ('salir' para terminar): "
        ).strip()

        if descripcionBusqueda.lower() == "salir":
            break
        

        # ==================================
        # BUSCAR EN MASTER
        # ==================================

        resultados = buscarCoincidenciasDescripcion(
            dfMaster,
            descripcionBusqueda
        )

        if resultados.empty:

            print("\n❌ Sin coincidencias\n")
            continue

        resultados = resultados.reset_index(
            drop=True
        )

        # ==================================
        # MOSTRAR RESULTADOS
        # ==================================

        print("\n============= COINCIDENCIAS =============\n")

        for i, (_, fila) in enumerate(
            resultados.head(20).iterrows()
        ):

            print(
                f"[{i}] "
                f"{fila['descripcion']}"
            )

        print("\n")

        # ==================================
        # SELECCION USUARIO
        # ==================================
        entrada = input("Ingrese 'no' para cancelar o seleccione el número de producto que desea facturar: ").strip().lower()

        # 1. Verificamos primero si el usuario quiere salir
        if entrada == "no":
            print("Seleccion cancelada.")
            continue 

        try:
            seleccion = int(entrada)

        except:

            print("❌ Entrada no válida")
            continue

        if seleccion < 0 or seleccion >= len(resultados):

            print("❌ El índice ingresado es inválido")
            continue

        filaSeleccionada = (
            resultados.iloc[seleccion]
        )

        # ==================================
        # CANTIDAD
        # ==================================

        try:

            cantidad = int(
                input("Cantidad: ")
            )

        except:

            print("❌ Cantidad inválida")
            continue

        # ==================================
        # GUARDAR PRODUCTO
        # ==================================

        productosSeleccionados.append({

            "codigo":
                filaSeleccionada["codigo"],

            "descripcion":
                filaSeleccionada["descripcion"],

            "cantidad":
                cantidad
        })

        print("\n✅ Producto agregado")

    # ======================================
    # GENERAR COTIZACION FINAL
    # ======================================

    if len(productosSeleccionados) == 0:

        print("\n❌ No se agregaron productos")
        return

    resultado = generarCotizacion(
        productosSeleccionados,
        matchers
    )

    print(
        "\n============= COTIZACION FINAL =============\n"
    )

    print(
        resultado.to_string(index=False)
    )

# ==========================================
# ENTRYPOINT
# ==========================================

if __name__ == "__main__":
    main()