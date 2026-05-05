import re
import unicodedata
from typing import Any

def process_data(rows: list[list[Any]]) -> list[list[Any]]:
    if not rows:
        return []

    def clean_str(val: Any) -> str:
        if val is None:
            return ""
        return str(val).strip()

    def remove_accents(input_str: str) -> str:
        nfkd_form = unicodedata.normalize('NFKD', input_str)
        return u"".join([c for c in nfkd_form if not unicodedata.combining(c)])

    # Identify headers dynamically
    headers = [clean_str(x).lower() for x in rows[0]]
    
    brand_idx, name_idx, ean_idx, stock_idx, price_idx, moq_idx = -1, -1, -1, -1, -1, -1
    
    for i, h in enumerate(headers):
        if not h: continue
        if any(kw in h for kw in ['manufacturer', 'brand', 'marke', 'hersteller']):
            brand_idx = i
        elif any(kw in h for kw in ['article type', 'name', 'desc', 'artikel', 'product', 'item', 'title']):
            name_idx = i
        elif any(kw in h for kw in ['barcode', 'ean', 'gtin']):
            ean_idx = i
        elif any(kw in h for kw in ['sum available', 'stock', 'qty', 'quantity', 'menge', 'bestand']):
            stock_idx = i
        elif any(kw in h for kw in ['selling price', 'price', 'preis', 'cost', '€']):
            price_idx = i
        elif any(kw in h for kw in ['moq', 'min', 'minimum']):
            moq_idx = i

    # Fallback based on sample
    if ean_idx == -1: ean_idx = 4
    if stock_idx == -1: stock_idx = 0
    if price_idx == -1: price_idx = 5
    if brand_idx == -1: brand_idx = 1
    if name_idx == -1: name_idx = 2

    out_headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if moq_idx != -1:
        out_headers.append("Min Qty")
        
    output_data = [out_headers]

    # Pre-compile Regex Patterns
    incoming_pattern = re.compile(r'(?i)(incoming|delivery|expected|estimated|transit|available\s*(from|ab)|verfügbar\s*ab|lieferdatum|ankunft|restock|backorder|out of stock)')
    refurb_scooter_pattern = re.compile(r'(?i)(refurbished|renewed|reconditioned|remanufactured|scooter)')
    
    # AKATRONIK specific filters
    akatronik_brands = re.compile(r'(?i)\b(AEG|BEKO|BOSCH|De\'?Longhi|ELECTROLUX|Gorenje|Hisense|LG|SAMSUNG|Siemens)\b')
    akatronik_appliances = re.compile(r'(?i)\b(washing\s*machine|washmachine|waschmaschine|wasmachine|lavadora|lavatrice|machine\s*a\s*laver|maquina\s*de\s*lavar|dryer|secadora|dishwasher|lavavajillas|lave\s*vaisselle|refrigerator|frigorifero|fridge|freezer|oven|tv|television|televisor|fernseher|air\s*conditioner|climatiseur|klimaanlage)\b')

    for row in rows[1:]:
        if not row or all(cell is None or clean_str(cell) == "" for cell in row):
            continue

        # Check for incoming stock / dates across all columns
        skip_row = False
        for cell in row:
            if incoming_pattern.search(clean_str(cell)):
                skip_row = True
                break
        if skip_row:
            continue

        raw_brand = clean_str(row[brand_idx]) if brand_idx != -1 and brand_idx < len(row) else ""
        raw_name = clean_str(row[name_idx]) if name_idx != -1 and name_idx < len(row) else ""
        raw_ean = clean_str(row[ean_idx]) if ean_idx != -1 and ean_idx < len(row) else ""
        raw_stock = clean_str(row[stock_idx]) if stock_idx != -1 and stock_idx < len(row) else ""
        raw_price = clean_str(row[price_idx]) if price_idx != -1 and price_idx < len(row) else ""

        # EAN
        ean = re.sub(r'\D', '', raw_ean)
        if not ean:
            continue
        if len(ean) > 13:
            ean = ean[-13:]
        ean = ean.zfill(13)

        # Name
        if raw_brand and raw_brand.lower() not in raw_name.lower():
            full_name = f"{raw_brand} {raw_name}".strip()
        else:
            full_name = raw_name

        # Filtering Name based rules
        normalized_name = remove_accents(full_name)
        if refurb_scooter_pattern.search(full_name):
            continue
        if akatronik_brands.search(normalized_name) or akatronik_appliances.search(normalized_name):
            continue

        # Price
        price_str = re.sub(r'[^\d,\.-]', '', raw_price)
        if ',' in price_str and '.' in price_str:
            price_str = price_str.replace(',', '')
        elif ',' in price_str:
            price_str = price_str.replace(',', '.')
            
        try:
            price = float(price_str)
        except ValueError:
            continue

        if price < 2.50:
            continue

        # Stock
        stock_str = re.sub(r'[^\d\-]', '', raw_stock)
        try:
            stock = int(stock_str)
        except ValueError:
            continue

        if stock <= 4:
            continue

        # Total Value Calculation
        total_price = round(price * stock, 2)
        
        # NOTE: 100 EUR filter is explicitly skipped for AKATRONIK

        out_row = [ean, full_name, price, stock, total_price, "akatronik"]
        
        if moq_idx != -1 and moq_idx < len(row):
            raw_moq = clean_str(row[moq_idx])
            moq_match = re.search(r'(\d+)', raw_moq)
            moq = int(moq_match.group(1)) if moq_match else 1
            out_row.append(moq)

        output_data.append(out_row)

    return output_data