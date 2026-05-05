import pandas as pd


def read_trusoni(file_path):
    all_data = []

    xls = pd.ExcelFile(file_path)

    for sheet_name in xls.sheet_names:
        df_raw = xls.parse(sheet_name, header=None)

        # 🔍 Buscar fila del header (CÓDIGO)
        header_row = None
        for i, row in df_raw.iterrows():
            if row.astype(str).str.contains("CÓDIGO", case=False).any():
                header_row = i
                break

        if header_row is None:
            continue

        # 🔥 EXTRAER TITULO (solo filas relevantes antes del header)
        titulo_partes = []

        for i in range(header_row - 1, -1, -1):
            row_values = df_raw.iloc[i].dropna().astype(str).tolist()

            if not row_values:
                if titulo_partes:
                    break
                continue

            titulo_partes = row_values + titulo_partes

        titulo = " ".join(titulo_partes)
        titulo = " ".join(titulo.split())

        # 📊 Leer tabla con header correcto
        df = xls.parse(sheet_name, header=header_row)

        # Normalizar columnas
        df.columns = [str(col).strip().upper() for col in df.columns]

        # Filtrar columnas necesarias
        cols_needed = ["CÓDIGO", "DESCRIPCIÓN", "PRECIO X 100"]
        df = df[[col for col in df.columns if col in cols_needed]]

        # Renombrar
        df = df.rename(columns={
            "CÓDIGO": "codigo",
            "DESCRIPCIÓN": "descripcion",
            "PRECIO X 100": "precio_100"
        })

        # Limpiar filas vacías
        df = df.dropna(subset=["codigo", "descripcion"])

        # Convertir precio
        df["precio_100"] = pd.to_numeric(df["precio_100"], errors="coerce")

        # 💰 Calcular precio unitario
        df["precio_unitario"] = df["precio_100"] / 100

        # 🧠 Construir descripción completa
        df["descripcion"] = titulo + " " + df["descripcion"].astype(str)

        df["descripcion"] = (
            df["descripcion"]
            .str.strip()
            .str.replace(r"\s+", " ", regex=True)
        )

        # Proveedor
        df["proveedor"] = "trusoni"

        # Columnas finales
        df = df[["codigo", "descripcion", "precio_unitario", "proveedor"]]

        all_data.append(df)

    # Unir todo
    if all_data:
        return pd.concat(all_data, ignore_index=True)
    else:
        return pd.DataFrame(columns=["codigo", "descripcion", "precio_unitario", "proveedor"])