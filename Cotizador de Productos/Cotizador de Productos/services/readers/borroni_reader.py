import logging
from services.readers.base_reader import BaseReader

logger = logging.getLogger(__name__)


class BorroniReader(BaseReader):
    """
    Lector especializado para PDFs de Aceros Borroni S.A.
    
    Estructura esperada:
    - Varillas Roscadas (SAE, RD NAT, RD ZA, RI NAT)
    - Roscas Métricas
    - Tuercas Hexagonales
    - Tuercas Métricas
    - Tuercas Pesadas
    """

    def __init__(self):
        super().__init__(provider_name="Borroni")

    def parse_page(self, page, page_num: int) -> list:
        """Extrae tablas de la página y parsea productos"""
        products = []

        tables = page.extract_tables()

        if not tables:
            logger.debug(f"No se encontraron tablas en página {page_num}")
            return products

        for table_idx, table in enumerate(tables):
            if len(table) < 2:
                continue

            # Detectar tipo de tabla por headers
            table_type = self._detect_table_type(table)

            if table_type == "VARILLAS_ROSCADAS":
                products.extend(self._parse_varillas(table, page_num))
            elif table_type == "ROSCA_METRICA":
                products.extend(self._parse_rosca_metrica(table, page_num))
            elif table_type == "TUERCA_HEXAGONAL":
                products.extend(self._parse_tuerca_hexagonal(table, page_num))
            elif table_type == "TUERCA_METRICA":
                products.extend(self._parse_tuerca_metrica(table, page_num))
            elif table_type == "TUERCA_PESADA":
                products.extend(self._parse_tuerca_pesada(table, page_num))

        return products

    def _detect_table_type(self, table) -> str:
        """Detecta el tipo de tabla por sus headers"""
        headers_text = " ".join([str(cell).upper() for row in table[:2] for cell in row if cell])

        if "VARILLA" in headers_text or "ROSCADA" in headers_text:
            return "VARILLAS_ROSCADAS"
        elif "ROSCA METRICA" in headers_text or "ROSCA MÉTRICA" in headers_text:
            return "ROSCA_METRICA"
        elif "TUERCA HEXAGONAL" in headers_text:
            return "TUERCA_HEXAGONAL"
        elif "TUERCA METRICA" in headers_text or "TUERCA MÉTRICA" in headers_text:
            return "TUERCA_METRICA"
        elif "TUERCA PESADA" in headers_text:
            return "TUERCA_PESADA"

        return "UNKNOWN"

    def _parse_varillas(self, table, page_num) -> list:
        """Parsea tabla de Varillas Roscadas"""
        products = []

        # Saltar headers (primeras 2 filas)
        for row in table[2:]:
            if len(row) < 3 or not row[0]:
                continue

            try:
                diametro = self._clean_text(row[0])
                if not diametro or diametro.lower() in ["diámetro", "mm.", "pulgada"]:
                    continue

                # Parsear RD NAT (acero natural)
                if len(row) > 3 and row[2]:
                    price = self._clean_price(row[2])
                    if price > 0:
                        products.append({
                            "provider": self.provider_name,
                            "product_type": "VARILLA ROSCADA",
                            "description": f"Varilla Roscada {diametro}",
                            "specification": diametro,
                            "price": price,
                            "finish": "RD NAT",
                            "page": page_num,
                        })

                # Parsear RD ZA (zincada)
                if len(row) > 4 and row[3]:
                    price = self._clean_price(row[3])
                    if price > 0:
                        products.append({
                            "provider": self.provider_name,
                            "product_type": "VARILLA ROSCADA",
                            "description": f"Varilla Roscada {diametro} Zincada",
                            "specification": diametro,
                            "price": price,
                            "finish": "RD ZA",
                            "page": page_num,
                        })

            except Exception as e:
                logger.debug(f"Error parseando fila de varilla: {e}")
                continue

        return products

    def _parse_rosca_metrica(self, table, page_num) -> list:
        """Parsea tabla de Roscas Métricas"""
        products = []

        for row in table[2:]:
            if len(row) < 2 or not row[0]:
                continue

            try:
                medida = self._clean_text(row[0])
                if not medida or medida.lower() in ["medida", "mm.", "paso"]:
                    continue

                # Parsear PULIDA
                if len(row) > 2 and row[1]:
                    price = self._clean_price(row[1])
                    if price > 0:
                        products.append({
                            "provider": self.provider_name,
                            "product_type": "ROSCA METRICA",
                            "description": f"Rosca Métrica {medida}",
                            "specification": medida,
                            "price": price,
                            "finish": "PULIDA",
                            "page": page_num,
                        })

                # Parsear ZINCADA
                if len(row) > 3 and row[2]:
                    price = self._clean_price(row[2])
                    if price > 0:
                        products.append({
                            "provider": self.provider_name,
                            "product_type": "ROSCA METRICA",
                            "description": f"Rosca Métrica {medida} Zincada",
                            "specification": medida,
                            "price": price,
                            "finish": "ZINCADA",
                            "page": page_num,
                        })

            except Exception as e:
                logger.debug(f"Error parseando fila de rosca: {e}")
                continue

        return products

    def _parse_tuerca_hexagonal(self, table, page_num) -> list:
        """Parsea tabla de Tuercas Hexagonales"""
        products = []

        for row in table[2:]:
            if len(row) < 2 or not row[0]:
                continue

            try:
                medida = self._clean_text(row[0])
                if not medida or medida.lower() in ["medida", "mm.", "paso"]:
                    continue

                # Parsear PULIDA
                if len(row) > 2 and row[1]:
                    price = self._clean_price(row[1])
                    if price > 0:
                        products.append({
                            "provider": self.provider_name,
                            "product_type": "TUERCA HEXAGONAL",
                            "description": f"Tuerca Hexagonal {medida}",
                            "specification": medida,
                            "price": price,
                            "finish": "PULIDA",
                            "page": page_num,
                        })

                # Parsear ZINCADA
                if len(row) > 3 and row[2]:
                    price = self._clean_price(row[2])
                    if price > 0:
                        products.append({
                            "provider": self.provider_name,
                            "product_type": "TUERCA HEXAGONAL",
                            "description": f"Tuerca Hexagonal {medida} Zincada",
                            "specification": medida,
                            "price": price,
                            "finish": "ZINCADA",
                            "page": page_num,
                        })

            except Exception as e:
                logger.debug(f"Error parseando fila de tuerca: {e}")
                continue

        return products

    def _parse_tuerca_metrica(self, table, page_num) -> list:
        """Parsea tabla de Tuercas Métricas"""
        return self._parse_tuerca_hexagonal(table, page_num)  # Estructura similar

    def _parse_tuerca_pesada(self, table, page_num) -> list:
        """Parsea tabla de Tuercas Pesadas"""
        return self._parse_tuerca_hexagonal(table, page_num)  # Estructura similar
