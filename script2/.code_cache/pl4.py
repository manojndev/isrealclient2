import re
from typing import Any

def process_data(rows: list[list[Any]]) -> list[list[Any]]:
    if not rows:
        return []

    # Helper function to clean text
    def clean_str(val: Any) -> str:
        if val is None:
            return ""
        return str(val).strip()

    # Identify headers dynamically
    headers = [clean_str(x).lower() for x in rows[0]]
    
    brand_idx, name_idx, ean_idx, stock_idx, price_idx, moq_idx = -1, -1, -1, -1, -1, -1
    
    for i, h in enumerate(headers):
        if any(kw in h for kw in ['brand', 'marke', 'hersteller', 'manufacturer']): brand_idx = i
        elif any(kw in h for kw in ['art', 'name', 'desc', 'artikel', 'product']): name_idx = i
        elif any(kw in h for kw in ['ean', 'barcode', 'gtin']): ean_idx = i
        elif any(kw in h for kw in ['stock', 'qty', 'quantity', 'menge', 'bestand']): stock_idx = i
        elif any(kw in h for kw in ['price', 'preis', 'cost', '€']): price_idx = i
        elif any(kw in h for kw in ['moq', 'min', 'minimum']): moq_idx = i

    # Fallback to inference by sample data column indices if headers are totally ambiguous
    if ean_idx == -1: ean_idx = 2
    if stock_idx == -1: stock_idx = 3
    if price_idx == -1: price_idx = 4
    if brand_idx == -1: brand_idx = 0
    if name_idx == -1: name_idx = 1

    # Output headers
    out_headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if moq_idx != -1:
        out_headers.append("Min Qty")
        
    output_data = [out_headers]

    # Pre-compile Regex Patterns
    incoming_pattern = re.compile(r'(?i)(incoming|delivery|expected|estimated|transit|available\s*(from|ab)|verfügbar\s*ab|lieferdatum|ankunft|restock|backorder|out of stock)')
    date_pattern = re.compile(r'\d{1,2}[\./-]\d{1,2}([\./-]\d{2,4})?')
    refurb_pattern = re.compile(r'(?i)(refurbished|renewed|reconditioned|remanufactured)')
    scooter_pattern = re.compile(r'(?i)scooter')

    for row in rows[1:]:
        if not row or all(cell is None or str(cell).strip() == "" for cell in row):
            continue

        # Check for incoming stock / dates across all columns
        skip_row = False
        for cell in row:
            cell_str = clean_str(cell)
            if incoming_pattern.search(cell_str):
                skip_row = True
                break
            # Look for dates if they look like an incoming notation, though purely standalone numbers might be dimensions.
            # We strictly exclude if delivery terms are found.
        if skip_row:
            continue

        # Extract Raw Values
        raw_brand = clean_str(row[brand_idx]) if brand_idx != -1 and brand_idx < len(row) else ""
        raw_name = clean_str(row[name_idx]) if name_idx != -1 and name_idx < len(row) else ""
        raw_ean = clean_str(row[ean_idx]) if ean_idx < len(row) else ""
        raw_stock = clean_str(row[stock_idx]) if stock_idx < len(row) else ""
        raw_price = clean_str(row[price_idx]) if price_idx < len(row) else ""

        # Process EAN
        ean = re.sub(r'\D', '', raw_ean)
        if not ean:
            continue
        if len(ean) > 13:
            ean = ean[-13:]
        ean = ean.zfill(13)

        # Process Name
        if raw_brand and raw_brand.lower() not in raw_name.lower():
            full_name = f"{raw_brand} {raw_name}".strip()
        else:
            full_name = raw_name

        if refurb_pattern.search(full_name) or scooter_pattern.search(full_name):
            continue

        # Process Price
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

        # Process Stock
        stock_str = re.sub(r'[^\d\-]', '', raw_stock)
        try:
            stock = int(stock_str)
        except ValueError:
            continue

        if stock <= 4:
            continue

        # Total Value Calculation
        total_price = round(price * stock, 2)
        if total_price < 100.0:
            continue

        # Assemble Output Row
        out_row = [ean, full_name, price, stock, total_price, "pl4"]
        
        # Process MOQ if present
        if moq_idx != -1 and moq_idx < len(row):
            raw_moq = clean_str(row[moq_idx])
            moq_match = re.search(r'(\d+)', raw_moq)
            moq = int(moq_match.group(1)) if moq_match else 1
            out_row.append(moq)

        output_data.append(out_row)

    return output_data