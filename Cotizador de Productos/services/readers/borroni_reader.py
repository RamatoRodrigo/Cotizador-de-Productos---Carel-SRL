import re
import logging
from services.readers.base_reader import BaseReader

logger = logging.getLogger(__name__)


class BorroniReader(BaseReader):

    KEYWORDS = [
        "bulon", "tuercas", "arandelas", "tornillos",
        "varillas", "tirafondos", "remaches", "clavos",
        "alemites", "ganchos", "precintos", "tarugos"
    ]

    def __init__(self):
        super().__init__(provider_name="Borroni")

    def parse_page(self, page, page_num: int) -> list:
        products = []

        tables = page.extract_tables()

        if not tables:
            return products


        for table in tables:
            product_type = self._detect_product_type_for_table(page, table)

            if self._is_thread_table(table):
                products.extend(self._parse_borroni_thread_table(table, page_num, product_type))
            else:
                products.extend(self._parse_generic_table(table, page_num, product_type))

        return products

    def _is_thread_table(self, table):
        if not table or len(table) < 2:
            return False

        header = " ".join([str(cell) for cell in table[0] if cell])
        return "Diámetro" in header and "hilos" in header

    def _detect_product_type_for_table(self, page, table):
        text = page.extract_text()

        if not text:
            return "PRODUCTO"

        lines = text.split("\n")

        # Buscar TODAS las líneas que contienen keywords
        matches = []

        for i, line in enumerate(lines):
            line_clean = line.strip()

            for word in self.KEYWORDS:
                if word.lower() in line_clean.lower():
                    matches.append((i, line_clean.upper()))

        if not matches:
            return "PRODUCTO NO IDENTIFICADO"

        return matches[-1][1]

    def _parse_borroni_thread_table(self, table, page_num, product_type="PRODUCTO"):
        products = []

        for i, row in enumerate(table):
            if i < 4:
                continue

            try:
                row = [str(c).strip() if c else "" for c in row]

                if len(row) < 8:
                    continue

                pulgadas = row[0]
                hilos = row[2]
                precio_rd_nat = row[3]
                precio_rd_za = row[4]
                cantidad = row[7]

                if not re.match(r'\d+/\d+', pulgadas):
                    continue

                if not hilos.isdigit():
                    continue

                def to_float(val):
                    if not val or "REF" in val:
                        return None
                    return float(val.replace(",", "."))

                precio_nat = to_float(precio_rd_nat)
                precio_za = to_float(precio_rd_za)

                cantidad = int(cantidad) if cantidad.isdigit() else 1

                medida = f"{pulgadas}-UNC-{hilos}"

                if precio_nat:
                    products.append({
                        "description": f"{product_type} SAE1010 RD NAT {medida}",
                        "measure": medida,
                        "unit_price": round(precio_nat / cantidad, 4)
                    })

                if precio_za:
                    products.append({
                        "description": f"{product_type} SAE1010 RD ZA {medida}",
                        "measure": medida,
                        "unit_price": round(precio_za / cantidad, 4)
                    })

            except Exception as e:
                logger.debug(f"Error fila: {e}")
                continue

        return products

    def _parse_generic_table(self, table, page_num, product_type="PRODUCTO"):
        products = []

        for row in table:
            if not row:
                continue

            try:
                cleaned_row = [self._clean_text(str(c)) for c in row if c]

                if len(cleaned_row) < 2:
                    continue

                description = cleaned_row[0]

                if any(x in description.lower() for x in ["medida", "mm", "codigo", "precio"]):
                    continue

                price = None
                quantity = 1

                for cell in cleaned_row[1:]:
                    price_match = re.search(r'\d+[.,]\d+', cell)
                    if price_match:
                        price = float(price_match.group().replace(",", "."))

                    qty_match = re.fullmatch(r'\d+', cell.strip())
                    if qty_match:
                        quantity = int(qty_match.group())

                if price and price > 0:
                    products.append({
                        "description": f"{product_type} {description}",
                        "measure": self._extract_measure(description),
                        "unit_price": price / quantity
                    })

            except Exception as e:
                logger.debug(f"Error parseando fila: {e}")
                continue

        return products

    def _extract_measure(self, text):
        match = re.search(r'\d+/\d+(?:-\w+(?:\(?\d*\)?))?', text)
        return match.group() if match else None