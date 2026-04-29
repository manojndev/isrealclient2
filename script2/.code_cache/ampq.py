import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else None

    def clean_price(val):
        if val is None: return None
        s = str(val).replace('€', '').replace('$', '').replace(',', '').strip()
        try:
            return float(s)
        except ValueError:
            return None

    def clean_qty(val):
        if val is None: return None
        s = re.sub(r'[^0-9]', '', str(val))
        try:
            return int(s)
        except ValueError:
            return None

    # Identify Column Indices
    ean_idx = name_idx = price_idx = qty_idx = avail_idx = moq_idx = -1
    
    # Try to find headers in the first 2 rows
    for r_idx in range(min(2, len(rows))):
        row_str = [str(c).upper() for c in rows[r_idx]]
        for i, col in enumerate(row_str):
            if any(x in col for x in ['EAN', 'GTIN', 'BARCODE']): ean_idx = i
            elif any(x in col for x in ['MODEL', 'NAME', 'DESCRIPTION', 'PRODUCT']): name_idx = i
            elif any(x in col for x in ['PRICE', 'UNIT COST']): price_idx = i
            elif any(x in col for x in ['QTY', 'STOCK', 'QUANTITY', 'AMOUNT']): qty_idx = i
            elif any(x in col for x in ['AVAIL', 'STATUS']): avail_idx = i
            elif 'MOQ' in col or 'MIN' in col: moq_idx = i

    # Fallback inference based on data if headers failed
    sample_row = rows[1] if len(rows) > 1 else rows[0]
    for i, val in enumerate(sample_row):
        val_s = str(val)
        if ean_idx == -1 and len(re.sub(r'\D', '', val_s)) >= 10: ean_idx = i
        if qty_idx == -1 and val_s.isdigit() and int(val_s) < 1000 and i != ean_idx: qty_idx = i
        if price_idx == -1 and ('.' in val_s or val_s.isdigit()) and i not in [ean_idx, qty_idx]: price_idx = i
        if name_idx == -1 and len(val_s) > 10 and i not in [ean_idx, price_idx]: name_idx = i

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if moq_idx != -1:
        final_header.append("Min Qty")
    
    result = [final_header]
    exclude_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured']
    not_in_stock_terms = ['incoming', 'delivery', 'estimated', 'backorder', 'soon']

    for i, row in enumerate(rows):
        # Skip header if it looks like one
        if i == 0 and any(isinstance(c, str) and c.upper() in ['EAN', 'QTY', 'PRICE'] for c in row):
            continue
            
        if len(row) <= max(ean_idx, name_idx, price_idx, qty_idx):
            continue

        name = str(row[name_idx]) if name_idx != -1 else ""
        ean = clean_ean(row[ean_idx]) if ean_idx != -1 else None
        price = clean_price(row[price_idx]) if price_idx != -1 else None
        qty = clean_qty(row[qty_idx]) if qty_idx != -1 else None
        avail = str(row[avail_idx]).lower() if avail_idx != -1 else ""
        
        # Validation & Filtering
        if not ean or not name or price is None or qty is None:
            continue
        
        if qty <= 4:
            continue
        if price < 2.50:
            continue
        
        total_price = price * qty
        if total_price < 100:
            continue
            
        name_lower = name.lower()
        if any(term in name_lower for term in exclude_terms):
            continue
        
        # Availability Check
        if any(term in avail for term in not_in_stock_terms) or any(term in name_lower for term in not_in_stock_terms):
            continue
        
        clean_row = [ean, name, price, qty, total_price, "ampq"]
        
        if moq_idx != -1:
            moq = clean_qty(row[moq_idx])
            clean_row.append(moq if moq is not None else 0)
            
        result.append(clean_row)

    return result