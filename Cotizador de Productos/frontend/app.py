import streamlit as st
import pandas as pd
from busquedaDeMejorPrecioProductos import (
    cargarMasterCarel,
    cargarMatchers,
    buscarCoincidenciasDescripcion,
    generarCotizacion
)

st.title("Cotizador de Productos")

dfMaster = cargarMasterCarel()
matchers = cargarMatchers()

# Inicializar lista persistente
if "productos" not in st.session_state:
    st.session_state["productos"] = []

# Input de búsqueda
descripcion = st.text_input("Buscar producto")

# Solo definimos resultados si hay algo escrito
if descripcion:
    resultados = buscarCoincidenciasDescripcion(dfMaster, descripcion)

    if resultados.empty:
        st.warning("❌ Sin coincidencias")
    else:
        # Selector de producto
        opciones = resultados["descripcion"].tolist()
        seleccion = st.selectbox("Elegí el producto", opciones)

        cantidad = st.number_input("Cantidad", min_value=1, step=1)

        if st.button("Agregar producto"):
            fila = resultados[resultados["descripcion"] == seleccion].iloc[0]
            st.session_state["productos"].append({
                "codigo": fila["codigo"],
                "descripcion": fila["descripcion"],
                "cantidad": cantidad
            })
            st.success("✅ Producto agregado")

# Mostrar productos seleccionados
if st.session_state["productos"]:
    st.write("### Productos seleccionados")
    st.dataframe(pd.DataFrame(st.session_state["productos"]))

# Generar cotización
if st.button("Generar cotización"):
    if st.session_state["productos"]:
        resultado = generarCotizacion(st.session_state["productos"], matchers)
        st.write("### Cotización Final")
        st.dataframe(resultado)
    else:
        st.error("❌ No se agregaron productos")
