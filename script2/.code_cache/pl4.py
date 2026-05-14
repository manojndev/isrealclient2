import re

def process_data(rows):
    if not rows:
        return []

    def is_ean(val):
        s = re.sub(r'\D', '', str(val))
        return len(s) >= 8 and len(s) <= 14 

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13)

    def clean_price(val):
        if val is None: return None
        s = str(val).replace('€', '').replace('$', '').strip()
        try:
            return float(s.replace(',', '.'))
        except ValueError:
            return None

    def clean_int(val):
        if val is None: return None
        s = re.sub(r'[^\d]', '', str(val))
        try:
            return int(s)
        except ValueError:
            return None

    # Identify indices
    header = rows[0]
    sample_data = rows[1:10]
    
    idx_ean = idx_brand = idx_art = idx_stock = idx_price = -1
    
    # Try header matching first
    for i, h in enumerate(header):
        h_str = str(h or "").lower()
        if "ean" in h_str: idx_ean = i
        elif "brand" in h_str: idx_brand = i
        elif "art" in h_str or "name" in h_str or "bezeichnung" in h_str: idx_art = i
        elif "stock" in h_str or "menge" in h_str or "lager" in h_str or "qty" in h_str: idx_stock = i
        elif "price" in h_str or "preis" in h_str: idx_price = i

    # Fallback to inference if headers were generic
    if idx_ean == -1:
        for r in sample_data:
            for i, col in enumerate(r):
                if is_ean(col): idx_ean = i; break
    
    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = [output_header]

    exclude_patterns = re.compile(r'refurbished|renewed|reconditioned|remanufactured|scooter', re.IGNORECASE)
    availability_patterns = re.compile(r'incoming|expected|delivery|availabl|soon', re.IGNORECASE)

    for row in rows:
        # Skip empty rows or header row
        if not any(row) or row == header:
            continue
            
        raw_ean = row[idx_ean] if idx_ean != -1 else None
        if not is_ean(raw_ean):
            continue

        ean = clean_ean(raw_ean)
        
        # Name construction
        brand = str(row[idx_brand] or "") if idx_brand != -1 else ""
        art = str(row[idx_art] or "") if idx_art != -1 else ""
        full_name = f"{brand} {art}".strip()
        
        # Filtering: Name-based
        if exclude_patterns.search(full_name):
            continue
            
        # Check all columns for availability/incoming status
        is_incoming = False
        for cell in row:
            if cell and availability_patterns.search(str(cell)):
                is_incoming = True
                break
        if is_incoming:
            continue

        price = clean_price(row[idx_price]) if idx_price != -1 else None
        stock = clean_int(row[idx_stock]) if idx_stock != -1 else None

        # Filtering: Logic-based
        if price is None or stock is None:
            continue
        if price < 2.50 or stock <= 4:
            continue
            
        total_price = round(price * stock, 2)
        if total_price < 100:
            continue

        processed_rows.append([
            ean,
            full_name,
            price,
            stock,
            total_price,
            "pl4"
        ])

    return processed_rows