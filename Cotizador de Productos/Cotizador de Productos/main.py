# main.py
import logging
from services.pdf_reader import read_pdfcl
from services.processor import process_data
from services.sheets_service import upload_to_sheets
from services.providers import PROVIDERS
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_config():
    with open('config/settings.json') as f:
        return json.load(f)

def main():
    try:
        config = load_config()
        logger.info("Configuración cargada")
        
        # Leer PDFs usando estrategia de proveedores
        dfs = []
        for provider, reader in PROVIDERS.items():
            path = f"data/{provider}.pdf"
            logger.info(f"Leyendo {provider}...")
            df = reader.read(path)
            dfs.append(df)
        
        # Procesar
        logger.info("Procesando datos...")
        result = process_data(dfs, config)
        
        if result.empty:
            logger.warning("No hay resultados para subir")
            return
        
        logger.info(f"Resultados: {len(result)} productos")
        
        # Subir a Google Sheets
        logger.info("Subiendo a Google Sheets...")
        upload_to_sheets(result, config)
        
        logger.info("✅ Proceso completado exitosamente")
        
    except Exception as e:
        logger.error(f"❌ Error en main: {e}")
        raise

if __name__ == '__main__':
    main()


