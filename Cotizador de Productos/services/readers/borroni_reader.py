import re
import logging
from services.readers.base_reader import BaseReader

logger = logging.getLogger(__name__)


class BorroniReader(BaseReader):

    KEYWORDS = [
        "bulon", "tuercas", "arandelas", "tornillos",
        "varillas", "tirafondos", "remaches", "clavos",
        "alemites", "ganchos", "precintos", "tarugos",
        "rosca", "tuerca"
    ]

    def __init__(self):
        super().__init__(provider_name="Borroni")

    # =========================
    # PUBLIC
    # =========================
    def parse_page(self, page, page_num: int) -> list:
        products = []
        tables = page.extract_tables()

        if not tables:
            return products

        for table in tables:
            product_type = self._detect_product_type_for_table(page)

            if self._is_thread_table(table):
                products.extend(
                    self._parse_borroni_thread_table(table, page_num, product_type)
                )
            else:
                products.extend(
                    self._parse_generic_table(table, page_num, product_type)
                )

        return products

    # =========================
    # TYPE DETECTION
    # =========================
    def _detect_product_type_for_table(self, page):
        text = page.extract_text()
        if not text:
            return "PRODUCTO"

        lines = text.split("\n")

        candidates = []

        for line in lines:
            line_clean = line.strip()

            if len(line_clean) > 80:
                continue

            for word in self.KEYWORDS:
                if word.lower() in line_clean.lower():
                    candidates.append(line_clean.upper())

        if not candidates:
            return "PRODUCTO NO IDENTIFICADO"

        return max(candidates, key=len)

    # =========================
    # TABLE TYPE DETECTION
    # =========================
    def _is_thread_table(self, table):
        if not table or len(table) < 2:
            return False

        header = " ".join(
            [str(cell).lower() for cell in table[0] if cell]
        )

        return ("diam" in header or "pulg") and "hilo" in header

    # =========================
    # THREAD TABLE PARSER
    # =========================
    def _parse_borroni_thread_table(self, table, page_num, product_type):
        products = []

        if not table or len(table) < 2:
            return products

        header = [str(c).lower() for c in table[0]]

        def find_col(keys):
            for i, col in enumerate(header):
                if any(k in col for k in keys):
                    return i
            return None

        col_pulg = find_col(["pulg", "diam"])
        col_hilos = find_col(["hilo"])
        col_nat = find_col(["nat"])
        col_za = find_col(["za"])
        col_cant = find_col(["cant"])

        if col_pulg is None or col_hilos is None:
            return products

        for i, row in enumerate(table):
            if i == 0:
                continue

            try:
                row = [str(c).strip() if c else "" for c in row]

                pulgadas = row[col_pulg] if col_pulg < len(row) else ""
                hilos = row[col_hilos] if col_hilos < len(row) else ""

                if not re.match(r'\d+/\d+', pulgadas):
                    continue

                if not hilos.isdigit():
                    continue

                def to_float(val):
                    if not val or "REF" in val.upper():
                        return None
                    try:
                        return float(val.replace(",", "."))
                    except:
                        return None

                precio_nat = to_float(row[col_nat]) if col_nat is not None else None
                precio_za = to_float(row[col_za]) if col_za is not None else None

                cantidad = 1
                if col_cant is not None and col_cant < len(row):
                    cantidad = int(row[col_cant]) if row[col_cant].isdigit() else 1

                medida = f"{pulgadas}-UNC-{hilos}"

                base_desc = self._normalize_description(product_type)

                if precio_nat:
                    products.append({
                        "description": f"{base_desc} RD NAT",
                        "measure": medida,
                        "unit_price": round(precio_nat / cantidad, 4),
                        "normalized_description": base_desc
                    })

                if precio_za:
                    products.append({
                        "description": f"{base_desc} RD ZA",
                        "measure": medida,
                        "unit_price": round(precio_za / cantidad, 4),
                        "normalized_description": base_desc
                    })

            except Exception as e:
                logger.debug(f"Error fila thread: {e}")
                continue

        return products

    # =========================
    # GENERIC TABLE PARSER
    # =========================
    def _parse_generic_table(self, table, page_num, product_type):
        products = []

        for row in table:
            if not row:
                continue

            try:
                cleaned_row = [
                    self._clean_text(str(c)) for c in row if c
                ]

                if len(cleaned_row) < 2:
                    continue

                description = cleaned_row[0]

                if any(x in description.lower() for x in [
                    "medida", "mm", "codigo", "precio"
                ]):
                    continue

                price = None
                quantity = 1

                for cell in cleaned_row[1:]:

                    price_match = re.search(
                        r'^\$?\s*\d+[.,]\d{2,}$',
                        cell
                    )
                    if price_match:
                        price = float(
                            price_match.group().replace("$", "").replace(",", ".")
                        )

                    qty_match = re.fullmatch(r'\d+', cell.strip())
                    if qty_match:
                        quantity = int(qty_match.group())

                if price and price > 0:
                    base_desc = self._normalize_description(
                        f"{product_type} {description}"
                    )

                    products.append({
                        "description": base_desc,
                        "measure": self._extract_measure(description),
                        "unit_price": round(price / quantity, 4),
                        "normalized_description": base_desc
                    })

            except Exception as e:
                logger.debug(f"Error parse generic: {e}")
                continue

        return products

    # =========================
    # HELPERS
    # =========================
    def _extract_measure(self, text):
        text = text.upper()

        # -------------------------
        # 1. Casos estándar
        # -------------------------
        patterns = [
            r'\d+/\d+\s*X\s*\d+',   # 1/4 x 2
            r'\d+/\d+',             # 1/4
            r'M\d+',                # M6
            r'\d+\s*MM',            # 10 mm
        ]

        for p in patterns:
            match = re.search(p, text)
            if match:
                return match.group().replace(" ", "")

        # -------------------------
        # 2. 🔥 MÉTRICOS SIN M NI MM (EL FIX IMPORTANTE)
        # -------------------------
        if "METRIC" in text or "METRICA" in text:

            # agarramos números de 1 a 3 dígitos
            numbers = re.findall(r'\b\d{1,3}\b', text)

            if numbers:
                # tomamos el PRIMERO (en tu caso es correcto)
                return f"M{numbers[0]}"

        return None

    def _normalize_description(self, text):
        text = text.upper()
        text = re.sub(r'\s+', ' ', text)

        # eliminamos puntuación que molesta al matching
        text = text.replace(",", "")
        text = text.replace(".", "")

        return text.strip()