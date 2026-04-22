import pdfplumber
import pandas as pd
import logging
from abc import ABC, abstractmethod
from pathlib import Path

logger = logging.getLogger(__name__)


class BaseReader(ABC):
    """
    Clase base abstracta para lectores de PDF específicos por proveedor.
    Define la interfaz común y funcionalidades compartidas.
    """

    def __init__(self, provider_name: str):
        self.provider_name = provider_name
        self.data = []

    @abstractmethod
    def parse_page(self, page, page_num: int) -> list:
        """
        Parsea una página del PDF y extrae los productos.

        Args:
            page: Página de pdfplumber
            page_num: Número de página

        Returns:
            Lista de diccionarios con datos de productos
        """
        pass

    def read(self, pdf_path: str) -> pd.DataFrame:
        """
        Lee un PDF y retorna DataFrame con los productos extraídos.

        Args:
            pdf_path: Ruta del archivo PDF

        Returns:
            DataFrame con estructura: provider, description, specification, price, finish, page
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            logger.error(f"Archivo no encontrado: {pdf_path}")
            return pd.DataFrame()

        try:
            logger.info(f"Leyendo {self.provider_name} desde {pdf_path}")

            with pdfplumber.open(pdf_path) as pdf:
                logger.info(f"Total de páginas: {len(pdf.pages)}")

                for page_num, page in enumerate(pdf.pages, 1):
                    try:
                        products = self.parse_page(page, page_num)
                        self.data.extend(products)
                    except Exception as e:
                        logger.warning(f"Error en página {page_num}: {e}")
                        continue

            if not self.data:
                logger.warning(f"No se extrajeron datos de {self.provider_name}")
                return pd.DataFrame()

            df = pd.DataFrame(self.data)
            logger.info(f"✅ Se extrajeron {len(df)} productos de {self.provider_name}")

            return df

        except Exception as e:
            logger.error(f"Error leyendo PDF de {self.provider_name}: {e}")
            return pd.DataFrame()

    def _clean_price(self, price_str) -> float:
        """Limpia y convierte string de precio a float"""
        try:
            if isinstance(price_str, (int, float)):
                return float(price_str)

            price_str = str(price_str).strip()
            price_str = price_str.replace(".", "").replace(",", ".")
            return float(price_str)
        except (ValueError, TypeError):
            return 0.0

    def _clean_text(self, text) -> str:
        """Limpia texto"""
        if text is None:
            return ""
        return str(text).strip()