import pandas as pd
import logging
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class BorroniReader:
    """
    Lector especializado para archivos Excel de Borroni.
    Lee múltiples hojas y normaliza los datos.
    """
    
    # Hojas esperadas en el Excel
    HOJAS_ESPERADAS = ['fijaciones', 'varillas', 'ale-clavos']
    
    # Campos esperados en todas las hojas
    CAMPOS_ESPERADOS = [
        'tipo de producto',
        'código de producto',
        'descripción',
        'unid. de medida',
        'cant. mínimo',
        'precio',
        'fecha de vigencia'
    ]
    
    def __init__(self):
        """Inicializa el reader"""
        self.datos_crudos = {}
        self.proveedor_nombre = "borroni"
    
    def read(self, excel_path: str) -> pd.DataFrame:
        """
        Lee el archivo Excel de Borroni y retorna un DataFrame unificado.
        
        Args:
            excel_path: Ruta al archivo .xlsx
            
        Returns:
            DataFrame con todos los productos sin parsear
        """
        
        excel_path = Path(excel_path)
        
        if not excel_path.exists():
            logger.error(f"❌ Archivo no encontrado: {excel_path}")
            return pd.DataFrame()
        
        logger.info(f"📂 Leyendo Excel: {excel_path}")
        
        try:
            # Leer todas las hojas
            excel_file = pd.ExcelFile(excel_path)
            hojas_disponibles = excel_file.sheet_names
            
            logger.info(f"   Hojas disponibles: {hojas_disponibles}")
            
            datos_consolidados = []
            
            # Procesar cada hoja esperada
            for hoja in self.HOJAS_ESPERADAS:
                if hoja.lower() in [h.lower() for h in hojas_disponibles]:
                    # Buscar la hoja (case-insensitive)
                    hoja_real = next(h for h in hojas_disponibles if h.lower() == hoja.lower())
                    
                    logger.info(f"\n📖 Procesando hoja: {hoja_real}")
                    
                    df_hoja = self._leer_hoja(excel_file, hoja_real)
                    
                    if not df_hoja.empty:
                        datos_consolidados.append(df_hoja)
                        logger.info(f"   ✅ {len(df_hoja)} productos extraídos")
                    else:
                        logger.warning(f"   ⚠️  Hoja vacía o sin datos válidos")
                else:
                    logger.warning(f"   ⚠️  Hoja no encontrada: {hoja}")
            
            if not datos_consolidados:
                logger.error("❌ No se extrajeron datos de ninguna hoja")
                return pd.DataFrame()
            
            # Consolidar todos los datos
            df_resultado = pd.concat(datos_consolidados, ignore_index=True)
            
            logger.info(f"\n✅ LECTURA COMPLETADA")
            logger.info(f"   Total de productos: {len(df_resultado)}")
            logger.info(f"   Columnas: {df_resultado.columns.tolist()}")
            
            # Estadísticas
            logger.info(f"\n📊 ESTADÍSTICAS:")
            logger.info(f"   Tipos de producto:")
            for tipo, count in df_resultado['tipo_de_producto'].value_counts().items():
                logger.info(f"      - {tipo}: {count}")
            
            logger.info(f"\n   Unidades de medida:")
            for unidad, count in df_resultado['unid_de_medida'].value_counts().items():
                logger.info(f"      - {unidad}: {count}")
            
            return df_resultado
        
        except Exception as e:
            logger.error(f"❌ Error al leer Excel: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def _leer_hoja(self, excel_file: pd.ExcelFile, nombre_hoja: str) -> pd.DataFrame:
        """
        Lee una hoja específica y la normaliza.
        
        Args:
            excel_file: Objeto ExcelFile
            nombre_hoja: Nombre de la hoja a leer
            
        Returns:
            DataFrame normalizado
        """
        
        try:
            # Leer la hoja
            df = pd.read_excel(excel_file, sheet_name=nombre_hoja)
            
            if df.empty:
                logger.warning(f"   Hoja vacía: {nombre_hoja}")
                return pd.DataFrame()
            
            # Normalizar nombres de columnas
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_').str.replace('.', '')
            
            logger.info(f"   Columnas encontradas: {df.columns.tolist()}")
            
            # Validar que tenga las columnas esperadas (flexiblemente)
            columnas_validas = self._mapear_columnas(df.columns.tolist())
            
            if not columnas_validas:
                logger.warning(f"   ⚠️  No se pudieron mapear las columnas")
                return pd.DataFrame()
            
            # Seleccionar solo las columnas válidas
            df = df[columnas_validas.values()].copy()
            
            # Renombrar a nombres estándar
            df.columns = columnas_validas.keys()
            
            # Limpiar datos
            df = self._limpiar_datos(df, nombre_hoja)
            
            return df
        
        except Exception as e:
            logger.error(f"   Error leyendo hoja {nombre_hoja}: {e}")
            return pd.DataFrame()
    
    def _mapear_columnas(self, columnas_actuales: List[str]) -> Dict[str, str]:
        """
        Mapea las columnas del Excel a nombres estándar.
        
        Args:
            columnas_actuales: Lista de nombres de columnas actuales
            
        Returns:
            Dict con {nombre_estándar: nombre_actual}
        """
        
        # Crear versión normalizada de las columnas actuales para búsqueda
        def normalizar_nombre(nombre):
            return (
                str(nombre)
                .lower()
                .strip()
                .replace('á', 'a')
                .replace('é', 'e')
                .replace('í', 'i')
                .replace('ó', 'o')
                .replace('ú', 'u')
                .replace(' ', '_')
                .replace('-', '_')
                .replace('.', '')
            )
        
        # Diccionario de posibles nombres de columnas normalizados
        mapeadores = {
            'tipo_de_producto': ['tipo_de_producto', 'tipo', 'product_type', 'tipo_prod'],
            'codigo_de_producto': ['codigo_de_producto', 'codigo', 'code', 'sku', 'product_code'],
            'descripcion': ['descripcion', 'description', 'desc'],
            'unid_de_medida': ['unid_de_medida', 'unidad', 'unit', 'u', 'unid', 'medida'],
            'cant_minimo': ['cant_minimo', 'cant_min', 'cantidad_minima', 'cantidad_minima', 'min_qty'],
            'precio': ['precio', 'price', 'precio_unitario', 'unit_price', 'pu'],
            'fecha_de_vigencia': ['fecha_de_vigencia', 'fecha', 'vigencia', 'date']
        }
        
        # Normalizar las columnas actuales
        columnas_norm = {normalizar_nombre(c): c for c in columnas_actuales}
        
        resultado = {}
        
        for nombre_std, posibles_nombres in mapeadores.items():
            for posible in posibles_nombres:
                if posible in columnas_norm:
                    resultado[nombre_std] = columnas_norm[posible]
                    break
        
        logger.info(f"   Mapeo de columnas: {resultado}")
        
        return resultado
    
    def _limpiar_datos(self, df: pd.DataFrame, nombre_hoja: str) -> pd.DataFrame:
        """
        Limpia y normaliza los datos de la hoja.
        
        Args:
            df: DataFrame con datos crudos
            nombre_hoja: Nombre de la hoja (para contexto)
            
        Returns:
            DataFrame limpio
        """
        
        df = df.copy()
        
        # Remover filas completamente vacías
        df = df.dropna(how='all')
        
        # Encontrar la columna de código (flexible)
        col_codigo = None
        for col in df.columns:
            if 'codigo' in col.lower():
                col_codigo = col
                break
        
        if col_codigo:
            # Remover filas donde el código está vacío
            df = df.dropna(subset=[col_codigo])
            df[col_codigo] = df[col_codigo].astype(str).str.strip()
        
        # Encontrar y limpiar descripción
        col_desc = None
        for col in df.columns:
            if 'descripc' in col.lower():
                col_desc = col
                break
        
        if col_desc:
            df[col_desc] = df[col_desc].astype(str).str.strip()
        
        # Encontrar y limpiar tipo
        col_tipo = None
        for col in df.columns:
            if 'tipo' in col.lower():
                col_tipo = col
                break
        
        if col_tipo:
            df[col_tipo] = df[col_tipo].astype(str).str.strip()
        
        # Encontrar y normalizar precio
        col_precio = None
        for col in df.columns:
            if 'precio' in col.lower():
                col_precio = col
                break
        
        if col_precio:
            df[col_precio] = pd.to_numeric(df[col_precio], errors='coerce')
            df = df.dropna(subset=[col_precio])
        
        # Encontrar y normalizar cantidad mínima
        col_cant = None
        for col in df.columns:
            if 'cant' in col.lower() or 'cantidad' in col.lower():
                col_cant = col
                break
        
        if col_cant:
            df[col_cant] = pd.to_numeric(df[col_cant], errors='coerce')
        
        # Encontrar unidad
        col_unid = None
        for col in df.columns:
            if 'unid' in col.lower():
                col_unid = col
                break
        
        if col_unid:
            df[col_unid] = df[col_unid].astype(str).str.strip()
        
        # Agregar información del proveedor
        df['proveedor'] = self.proveedor_nombre
        df['hoja_origen'] = nombre_hoja
        
        return df
    
    def read_and_save(self, excel_path: str, output_csv_path: str) -> pd.DataFrame:
        """
        Lee el Excel y guarda el resultado en CSV.
        
        Args:
            excel_path: Ruta al archivo Excel
            output_csv_path: Ruta donde guardar el CSV
            
        Returns:
            DataFrame leído
        """
        
        df = self.read(excel_path)
        
        if not df.empty:
            try:
                df.to_csv(output_csv_path, index=False, encoding='utf-8')
                logger.info(f"\n💾 CSV guardado en: {output_csv_path}")
            except Exception as e:
                logger.error(f"❌ Error al guardar CSV: {e}")
        
        return df