import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
        if val is None: return ""
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else ""

    def clean_price(val):
        if val is None: return None
        # Handle string and numeric inputs
        s = str(val).replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except ValueError:
            return None

    def clean_qty(val):
        if val is None: return None
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except ValueError:
            return None

    # Column Mapping
    ean_idx = name_idx = price_idx = qty_idx = prod_idx = incoming_idx = -1
    
    # Search for the header row (skipping potential disclaimer rows)
    header_found_idx = 0
    for i, row in enumerate(rows[:5]):
        row_str = [str(c).lower() for c in row if c]
        if any('ean' in s or 'product code' in s or 'net price' in s for s in row_str):
            header_found_idx = i
            for idx, col in enumerate(row_str):
                if 'ean' in col: ean_idx = idx
                elif 'name of product' in col: name_idx = idx
                elif 'net price eur' in col: price_idx = idx
                elif 'stock' == col: qty_idx = idx
                elif 'producer' in col: prod_idx = idx
                elif 'incoming stock' in col: incoming_idx = idx
            break

    # Final result construction
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [final_header]
    
    exclude_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured', 'incoming', 'delivery', 'estimated']

    for i, row in enumerate(rows):
        # Skip header and rows before it
        if i <= header_found_idx:
            continue
        
        # Safe extraction
        name = str(row[name_idx]) if name_idx != -1 and name_idx < len(row) else ""
        producer = str(row[prod_idx]) if prod_idx != -1 and prod_idx < len(row) else ""
        full_name = f"{producer} {name}".strip() if producer.lower() not in name.lower() else name
        
        # STRICT CENNIK FILTER: MAKITA only
        if 'makita' not in full_name.lower():
            continue
            
        ean = clean_ean(row[ean_idx]) if ean_idx != -1 and ean_idx < len(row) else ""
        price = clean_price(row[price_idx]) if price_idx != -1 and price_idx < len(row) else None
        qty = clean_qty(row[qty_idx]) if qty_idx != -1 and qty_idx < len(row) else None
        incoming = clean_qty(row[incoming_idx]) if incoming_idx != -1 and incoming_idx < len(row) else 0

        # Validations
        if not ean or not name or price is None or qty is None:
            continue
        
        # Exclude refurbished etc
        name_lower = full_name.lower()
        if any(term in name_lower for term in exclude_terms):
            continue
        
        # Standard Numeric Filters
        if qty <= 4 or price < 2.50:
            continue
            
        total_price = round(price * qty, 2)
        if total_price < 100:
            continue
            
        # Add to output
        output.append([
            ean,
            full_name,
            price,
            qty,
            total_price,
            "cennik"
        ])

    return output