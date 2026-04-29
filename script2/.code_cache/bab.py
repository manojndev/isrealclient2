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
        s = str(val).replace(',', '.').strip()
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except ValueError:
            return None

    def clean_qty(val):
        if val is None: return None
        s = str(val).lower()
        if 'incoming' in s or 'delivery' in s or 'estimated' in s:
            return -1
        s = re.sub(r'\D', '', s)
        try:
            return int(s)
        except ValueError:
            return None

    # Column Mapping
    ean_idx = name_idx = price_idx = qty_idx = brand_idx = moq_idx = -1
    
    # Try to find header row (usually index 0)
    header_found = False
    for i, row in enumerate(rows[:3]):
        row_str = [str(c).lower() if c else "" for c in row]
        if any(x in row_str for x in ['ean', 'sku', 'price', 'qty']):
            header_found = True
            for idx, col in enumerate(row_str):
                if 'ean' in col: ean_idx = idx
                elif any(x in col for x in ['name', 'description', 'article']): name_idx = idx
                elif any(x in col for x in ['price', 'euro', 'cost']): price_idx = idx
                elif any(x in col for x in ['stock', 'qty', 'quantity', 'free']): qty_idx = idx
                elif 'brand' in col: brand_idx = idx
                elif 'moq' in col or 'min' in col: moq_idx = idx
            header_row_count = i + 1
            break

    # Fallback inference if headers are missing or unclear
    if not header_found or ean_idx == -1 or price_idx == -1:
        sample = rows[1] if len(rows) > 1 else rows[0]
        for i, val in enumerate(sample):
            val_s = str(val)
            if ean_idx == -1 and len(re.sub(r'\D', '', val_s)) >= 12: ean_idx = i
            elif qty_idx == -1 and val_s.isdigit() and i != ean_idx: qty_idx = i
            elif price_idx == -1 and ('.' in val_s or ',' in val_s) and i not in [ean_idx, qty_idx]: price_idx = i
            elif name_idx == -1 and len(val_s) > 10: name_idx = i
        header_row_count = 1 if header_found else 0

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    has_moq_col = moq_idx != -1
    if has_moq_col:
        final_header.append("Min Qty")

    processed_rows = [final_header]
    exclude_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured']

    for i, row in enumerate(rows):
        if i < header_row_count:
            continue

        if len(row) <= max(ean_idx, name_idx, price_idx, qty_idx):
            continue

        # Extraction
        brand = str(row[brand_idx]) if brand_idx != -1 else ""
        raw_name = str(row[name_idx]) if name_idx != -1 else ""
        name = f"{brand} {raw_name}".strip() if brand and brand.lower() not in raw_name.lower() else raw_name
        
        ean = clean_ean(row[ean_idx])
        price = clean_price(row[price_idx])
        qty = clean_qty(row[qty_idx])
        
        # Validation & Filters
        if not ean or not name or price is None or qty is None:
            continue
        
        # Availability Check (clean_qty returns -1 for incoming stock)
        if qty <= 4:
            continue
            
        # Price Filter
        if price < 2.50:
            continue
            
        # Condition Filter
        name_lower = name.lower()
        if any(term in name_lower for term in exclude_terms):
            continue
            
        # Total Value Filter
        total_price = round(price * qty, 2)
        if total_price < 100:
            continue
            
        # Final formatting
        res_row = [ean, name, price, qty, total_price, "bab"]
        
        if has_moq_col:
            moq_val = clean_qty(row[moq_idx])
            res_row.append(moq_val if (moq_val is not None and moq_val > 0) else 1)
            
        processed_rows.append(res_row)

    return processed_rows