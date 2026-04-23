import re
import logging
from services.readers.base_reader import BaseReader

logger = logging.getLogger(__name__)


class BorroniReader(BaseReader):

    def __init__(self):
        super().__init__(provider_name="Borroni")

    def parse_page(self, page, page_num: int) -> list:
        products = []

        tables = page.extract_tables()

        if not tables:
            return products

        for table in tables:
            products.extend(self._parse_generic_table(table, page_num))

        return products

    def _parse_generic_table(self, table, page_num):
        products = []

        for row in table:
            if not row:
                continue

            try:
                # Limpiar celdas
                cleaned_row = [self._clean_text(str(c)) for c in row if c]

                if len(cleaned_row) < 2:
                    continue

                # Detectar descripción
                description = cleaned_row[0]

                if any(x in description.lower() for x in ["medida", "mm", "codigo", "precio"]):
                    continue

                price = None
                quantity = 1

                for cell in cleaned_row[1:]:
                    price_match = re.search(r'\d+[.,]?\d*', cell)
                    if price_match:
                        price = float(price_match.group().replace(",", "."))

                    qty_match = re.search(r'\b\d+\b', cell)
                    if qty_match:
                        quantity = int(qty_match.group())

                if price and price > 0:
                    unit_price = price / quantity

                    products.append({
                        "provider": self.provider_name,
                        "product_type": "GENERIC",
                        "description": description,
                        "specification": description,
                        "price": unit_price,
                        "raw_price": price,
                        "quantity": quantity,
                        "page": page_num,
                    })

            except Exception as e:
                logger.debug(f"Error parseando fila: {e}")
                continue

        return products