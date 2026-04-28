import pandas as pd
import logging
from services.providers import PROVIDERS

logger = logging.getLogger(__name__)

def read_pdf(path: str, provider_name: str) -> pd.DataFrame:
    """
    Lee un PDF usando el reader específico del proveedor.

    Args:
        path: Ruta del archivo PDF
        provider_name: Nombre del proveedor (clave en PROVIDERS)

    Returns:
        DataFrame con datos extraídos del PDF
    """

    if provider_name.lower() not in PROVIDERS:
        logger.error(f"Proveedor no soportado: {provider_name}")
        logger.info(f"Proveedores disponibles: {list(PROVIDERS.keys())}")
        return pd.DataFrame()

    try:
        reader = PROVIDERS[provider_name.lower()]
        df = reader.read(path)

        if df.empty:
            logger.warning(f"No se extrajeron datos de {path}")
        else:
            logger.info(f"✅ {len(df)} productos leídos de {provider_name}")

        return df

    except Exception as e:
        logger.error(f"Error leyendo PDF de {provider_name}: {e}")
        return pd.DataFrame()