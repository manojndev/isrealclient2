import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
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
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except ValueError:
            return None

    ean_idx = name_idx = price_idx = qty_idx = moq_idx = -1
    
    # Analyze headers
    header_candidates = rows[0]
    header_str = [str(c).lower() if c else "" for c in header_candidates]
    
    for i, col in enumerate(header_str):
        if any(x in col for x in ['ean', 'barcode', 'gtin']): ean_idx = i
        elif any(x in col for x in ['description', 'product', 'name', 'article']): name_idx = i
        elif any(x in col for x in ['price', 'eur', 'cost']): price_idx = i
        elif any(x in col for x in ['qty', 'available', 'stock', 'quantity']): qty_idx = i
        elif any(x in col for x in ['moq', 'min qty', 'minimum']): moq_idx = i

    # Fallback inference
    if ean_idx == -1 or name_idx == -1 or price_idx == -1 or qty_idx == -1:
        sample = rows[1] if len(rows) > 1 else rows[0]
        for i, val in enumerate(sample):
            val_s = str(val) if val is not None else ""
            digits = re.sub(r'\D', '', val_s)
            if ean_idx == -1 and len(digits) >= 12: ean_idx = i
            elif qty_idx == -1 and val_s.isdigit() and i != ean_idx: qty_idx = i
            elif price_idx == -1 and ('.' in val_s or val_s.replace('.0', '').isdigit()) and i not in [ean_idx, qty_idx]: price_idx = i
            elif name_idx == -1 and len(val_s) > 8: name_idx = i

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    has_moq_data = False
    temp_results = []

    exclude_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured', 'incoming', 'delivery', 'estimated', 'date']

    for i, row in enumerate(rows):
        # Skip header row if it matches keywords
        if i == 0 and any(x in str(row[0]).lower() for x in ['ean', 'qty', 'price']):
            continue

        if len(row) <= max(ean_idx, name_idx, price_idx, qty_idx):
            continue

        name = str(row[name_idx]) if name_idx != -1 else ""
        ean = clean_ean(row[ean_idx]) if ean_idx != -1 else ""
        price = clean_price(row[price_idx]) if price_idx != -1 else None
        qty = clean_qty(row[qty_idx]) if qty_idx != -1 else None
        
        # Validation and Filtering
        if not ean or not name or price is None or qty is None:
            continue
        
        name_lower = name.lower()
        if any(term in name_lower for term in exclude_terms):
            continue
            
        if qty <= 4 or price < 2.50:
            continue
            
        total_price = price * qty
        if total_price < 100:
            continue
            
        moq_val = None
        if moq_idx != -1 and moq_idx < len(row):
            moq_val = clean_qty(row[moq_idx])
            if moq_val is not None: has_moq_data = True

        temp_results.append({
            "data": [ean, name, price, qty, total_price, "horus"],
            "moq": moq_val
        })

    if has_moq_data:
        final_header.append("Min Qty")

    final_output = [final_header]
    for item in temp_results:
        row_data = item["data"]
        if has_moq_data:
            row_data.append(item["moq"] if item["moq"] is not None else 0)
        final_output.append(row_data)

    return final_output