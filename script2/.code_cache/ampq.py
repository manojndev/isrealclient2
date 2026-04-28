import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else None

    def clean_float(val):
        if val is None: return None
        s = str(val).replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except:
            return None

    def clean_int(val):
        if val is None: return None
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except:
            return None

    # Identify columns
    header_idx = -1
    for i, row in enumerate(rows[:5]):
        row_str = " ".join(str(c).lower() for c in row)
        if any(k in row_str for k in ['ean', 'price', 'qty', 'model', 'sku']):
            header_idx = i
            break
    
    data_start = header_idx + 1 if header_idx != -1 else 0
    sample_rows = rows[data_start:data_start + 10]
    
    col_map = {"ean": None, "name": None, "price": None, "qty": None, "moq": None, "avail": None}
    num_cols = len(rows[data_start]) if data_start < len(rows) else 0

    if header_idx != -1:
        h_row = [str(c).lower() for c in rows[header_idx]]
        for i, val in enumerate(h_row):
            if 'ean' in val: col_map['ean'] = i
            elif 'price' in val or 'unit' in val: col_map['price'] = i
            elif 'qty' in val or 'stock' in val or 'quant' in val: col_map['qty'] = i
            elif 'model' in val or 'name' in val or 'desc' in val: col_map['name'] = i
            elif 'moq' in val or 'min' in val: col_map['moq'] = i
            elif 'avail' in val or 'status' in val: col_map['avail'] = i

    # Fallback inference
    for i in range(num_cols):
        vals = [str(r[i]) for r in sample_rows if i < len(r)]
        if col_map['ean'] is None and any(len(re.sub(r'\D', '', v)) >= 10 for v in vals):
            col_map['ean'] = i
        elif col_map['qty'] is None and all(re.match(r'^\d+$', v.strip()) for v in vals if v.strip()):
            col_map['qty'] = i
        elif col_map['price'] is None and any(re.search(r'\d', v) for v in vals):
            if any('€' in v or '$' in v or '.' in v or ',' in v for v in vals):
                col_map['price'] = i

    final_rows = []
    has_moq_col = col_map['moq'] is not None
    
    for row in rows[data_start:]:
        if not row or len(row) < 2: continue
        
        # Check Availability
        if col_map['avail'] is not None:
            avail_val = str(row[col_map['avail']]).lower()
            if any(k in avail_val for k in ['incoming', 'delivery', 'eta', 'expected', 'ordered']):
                continue
        
        # Extract fields
        raw_ean = row[col_map['ean']] if col_map['ean'] is not None else ""
        raw_name = row[col_map['name']] if col_map['name'] is not None else ""
        raw_price = row[col_map['price']] if col_map['price'] is not None else None
        raw_qty = row[col_map['qty']] if col_map['qty'] is not None else None
        
        ean = clean_ean(raw_ean)
        name = str(raw_name).strip()
        price = clean_float(raw_price)
        qty = clean_int(raw_qty)
        
        if not ean or not price or not qty: continue
        if qty <= 4 or price < 2.50: continue
        
        total_price = round(price * qty, 2)
        if total_price < 100: continue
        
        processed_row = [ean, name, price, qty, total_price, "ampq"]
        
        if has_moq_col:
            moq = clean_int(row[col_map['moq']]) or 0
            processed_row.append(moq)
            
        final_rows.append(processed_row)

    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq_col:
        header.append("Min Qty")
        
    return [header] + final_rows