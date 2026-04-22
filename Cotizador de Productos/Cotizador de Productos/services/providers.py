# services/providers.py
from abc import ABC, abstractmethod
import pdfplumber
import pandas as pd

class ProviderReader(ABC):
    """
    Interfaz abstracta para lectores de proveedores.
    Define el contrato que todos los lectores deben cumplir.
    """

    @abstractmethod
    def read(self, path: str) -> pd.DataFrame:
        """
        Lee un PDF de proveedor y retorna DataFrame.

        Args:
            path: Ruta del archivo PDF

        Returns:
            DataFrame con columnas: provider, product_type, description, 
            specification, price, finish, page
        """
        pass


# Importar implementaciones específicas
from services.readers.borroni_reader import BorroniReader


# Instancias de readers
PROVIDERS = {
    'borroni': BorroniReader(),
    # 'fleb': FlebReader(),        # Próximos
    # 'efepe': EfepeReader(),
    # 'bm': BMReader(),
}

class FlebReader(ProviderReader):
    def read(self, path):
        # Lógica específica para Fleb
        pass

class BorroniReader(ProviderReader):
    def read(self, path):
        # Lógica específica para Borroni
        pass

class EfepeReader(ProviderReader):
    def read(self, path):
        # Lógica específica para EFEPE
        pass

class BMReader(ProviderReader):
    def read(self, path):
        # Lógica específica para BM
        pass
