import pandas as pd
import pdfplumber
import re
from collections import defaultdict

def construir_diccionario_qxkg(pdf_path):
    dicc = {}
    patron_medida = re.compile(r"^\d+/\d+$")  # fracciones tipo 1/8, 5/32, etc.
    patron_qxkg = re.compile(r"^\d{3,4}$")    # QxKg: 3–4 dígitos

    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            tablas = page.extract_tables()
            tabla_medidas = [t for t in tablas if any(patron_medida.match((fila[0] or "").strip()) for fila in t if fila)]
            tabla_qxkg = [t for t in tablas if any(patron_qxkg.match((fila[0] or "").strip()) for fila in t if fila)]

            if not tabla_medidas or not tabla_qxkg:
                continue

            # emparejar por índice
            for fila_medida, fila_qxkg in zip(tabla_medidas[0], tabla_qxkg[0]):
                medida = fila_medida[0]
                qxkg = fila_qxkg[0]
                if medida and qxkg and qxkg.isdigit():
                    txt_upper = page.extract_text().upper()
                    producto = "ARANDELAS PLANAS BRONCE" if "BRONCE" in txt_upper else "ARANDELAS PLANAS ZINCADAS"
                    dicc[(producto, medida.strip().upper())] = int(qxkg)
    return dicc

def read_efepe(file_path, pdf_path=None):
    df_raw = pd.read_excel(file_path, header=2)

    # Normalizar nombres
    df_raw.columns = (
        df_raw.columns
        .str.strip()
        .str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )

    # Filtrar columnas necesarias
    cols_needed = ["SKU","DESCRIPCIÓN DEL ARTÍCULO", "UNIDAD DE MEDIDA (UM)",
                "LISTA POR UNIDAD", "LISTA POR UM"]
    df = df_raw[[c for c in df_raw.columns if c in cols_needed]].copy()

    # Renombrar
    df = df.rename(columns={
        "SKU": "codigo",
        "DESCRIPCIÓN DEL ARTÍCULO": "descripcion",
        "UNIDAD DE MEDIDA (UM)": "unidad"
    })

    # Convertir a numérico y combinar
    df["LISTA POR UNIDAD"] = pd.to_numeric(df["LISTA POR UNIDAD"], errors="coerce")
    df["LISTA POR UM"] = pd.to_numeric(df["LISTA POR UM"], errors="coerce")
    df["precio_unitario"] = df["LISTA POR UNIDAD"].fillna(df["LISTA POR UM"])

    df["proveedor"] = "efepe"


    # Quitar códigos iniciales tipo "123456 - "
    df["descripcion"] = df["descripcion"].str.replace(r"^\d+\s*-\s*", "", regex=True)

    # Extraer medidas con regex vectorizado
    df["medida"] = df["descripcion"].str.extract(r"(\d+(?:\.\d+)?(?:/\d+)?)")

    # Caso especial: productos por kilo
    if pdf_path is not None:
        dicc_qxkg = construir_diccionario_qxkg(pdf_path)
        print(list(dicc_qxkg.items())[:5])


        for row in df.itertuples(index=True):
            if str(row.unidad).upper() == "KILOGRAMOS":
                desc = " ".join(row.descripcion.upper().split())
                producto = None

                if any(x in desc for x in ["ARANDELA PLANA DR", "ARANDELA PLANA ZN", "ARANDELA PLANA CHAPISTA"]):
                    producto = "ARANDELAS PLANAS ZINCADAS"
                elif "ARANDELA PLANA BRONCE" in desc:
                    producto = "ARANDELAS PLANAS BRONCE"

                if producto and row.medida:
                    # Normalizar medida (ej: "12 mm" → "12")
                    medida_norm = str(row.medida).replace("MM", "").strip()
                    qxkg = dicc_qxkg.get((producto, medida_norm))

                    if qxkg and pd.notna(row.precio_unitario):
                        df.at[row.Index, "precio_unitario"] = row.precio_unitario / qxkg
                    # Si no hay qxkg, no pisar el precio



    return df[["codigo", "descripcion", "precio_unitario", "proveedor"]]


