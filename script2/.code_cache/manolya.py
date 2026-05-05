import re
from typing import Any

def process_data(rows: list[list[Any]]) -> list[list[Any]]:
    if not rows:
        return []
    
    brand_idx = name_idx = ean_idx = price_idx = qty_idx = stock_idx = moq_idx = -1
    header_found = False
    
    output_rows = []
    has_moq = False
    
    refurb_regex = re.compile(r"\b(refurbished|renewed|reconditioned|remanufactured)\b", re.IGNORECASE)
    incoming_regex = re.compile(r"\b(incoming|eta|delivery|estimated|expected)\b", re.IGNORECASE)
    
    for i, row in enumerate(rows):
        if not row or all(x is None or str(x).strip() == '' for x in row):
            continue
            
        str_row = [str(x).lower().strip() if x is not None else "" for x in row]
        
        # Header Detection
        if not header_found:
            if any('price' in x or 'preis' in x or '€' in x for x in str_row) or any('ean' in x for x in str_row) or any('stock' in x or 'bestand' in x for x in str_row):
                header_found = True
                for j, val in enumerate(str_row):
                    if not val: continue
                    if 'ean' in val or 'barcode' in val: ean_idx = j
                    elif 'price' in val or 'preis' in val: price_idx = j
                    elif 'stock' in val or 'qty' in val or 'quantity' in val or 'bestand' in val: qty_idx = j
                    elif 'brand' in val or 'marke' in val or 'hersteller' in val or 'manufacturer' in val: brand_idx = j
                    elif 'art' == val or 'item' in val or 'name' in val or 'description' in val or 'artikel' in val or 'modell' in val: name_idx = j
                    elif 'min' in val and ('qty' in val or 'order' in val or 'moq' in val): moq_idx = j
                if moq_idx != -1: has_moq = True
                continue
                
        r_qty, r_price, r_ean, r_brand, r_moq, r_name = None, None, None, None, None, None
        
        if header_found:
            if 0 <= qty_idx < len(row): r_qty = row[qty_idx]
            if 0 <= price_idx < len(row): r_price = row[price_idx]
            if 0 <= ean_idx < len(row): r_ean = row[ean_idx]
            if 0 <= brand_idx < len(row): r_brand = row[brand_idx]
            if 0 <= name_idx < len(row): r_name = row[name_idx]
            if 0 <= moq_idx < len(row): r_moq = row[moq_idx]
        else:
            # Fallback for dynamic pattern matching if explicit headers are somewhat missing
            for val in row:
                if val is None: continue
                val_str = str(val).strip()
                if not val_str: continue
                
                if re.match(r'^\d{12,14}$', val_str) and r_ean is None:
                    r_ean = val_str
                elif re.match(r'^\+?\d+$', val_str) and len(val_str) < 6 and r_qty is None:
                    r_qty = val_str
                elif re.match(r'^[\d\s.,]+[€$£]?$', val_str) and any(c.isdigit() for c in val_str) and len(val_str) < 15 and r_price is None and val_str != r_ean:
                    r_price = val_str
                elif len(val_str) > 3 and not re.match(r'^[\d.,]+$', val_str):
                    if r_name is None: r_name = val_str
                    elif r_brand is None: r_brand = r_name; r_name = val_str
                    
        # Extract and Clean Quantity
        if r_qty is None: continue
        qty_str = re.sub(r'[^\d]', '', str(r_qty))
        if not qty_str: continue
        try:
            qty = int(qty_str)
        except ValueError:
            continue
        if qty <= 4: continue
        
        # Extract and Clean Price
        if r_price is None: continue
        price_str = str(r_price).replace('€', '').replace('$', '').replace('£', '').strip()
        # Clean numeric format handling
        if ',' in price_str and '.' in price_str:
            if price_str.rfind(',') > price_str.rfind('.'):
                price_str = price_str.replace('.', '').replace(',', '.')
            else:
                price_str = price_str.replace(',', '')
        elif ',' in price_str:
            price_str = price_str.replace(',', '.')
            
        price_str = re.sub(r'[^\d.]', '', price_str)
        if not price_str: continue
        try:
            price = float(price_str)
        except ValueError:
            continue
        if price < 2.50: continue
        
        # Total Price Filter
        total_price = round(price * qty, 2)
        if total_price < 100.0: continue
        
        # Extract and Clean EAN
        if r_ean is None: continue
        ean_str = re.sub(r'\D', '', str(r_ean))
        if not ean_str: continue
        ean = ean_str.zfill(13)
        
        # Extract Name
        brand_val = str(r_brand).strip() if r_brand is not None else ""
        name_val = str(r_name).strip() if r_name is not None else ""
        
        if brand_val and name_val:
            if brand_val.lower() not in name_val.lower():
                full_name = f"{brand_val} {name_val}".strip()
            else:
                full_name = name_val.strip()
        else:
            full_name = (name_val or brand_val).strip()
            
        full_name = re.sub(r'\s+', ' ', full_name)
        if not full_name: continue
        
        # Filters (Regex & Combinations)
        row_str_combined = " ".join([str(x) for x in row if x is not None])
        if incoming_regex.search(row_str_combined): continue
        if refurb_regex.search(full_name): continue
        if re.search(r'\b(out of stock)\b', row_str_combined, re.IGNORECASE): continue
        if re.search(r'\d{1,2}[./-]\d{1,2}', row_str_combined) and ('incoming' in row_str_combined.lower() or 'delivery' in row_str_combined.lower()): continue
        
        final_row = [ean, full_name, price, qty, total_price, "manolya"]
        
        # MOQ handling
        if has_moq:
            moq_val = 1
            if r_moq is not None:
                m_str = re.sub(r'\D', '', str(r_moq))
                if m_str: moq_val = int(m_str)
            final_row.append(moq_val)
            
        output_rows.append(final_row)
        
    headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq:
        headers.append("Min Qty")
        
    output_rows.insert(0, headers)
    
    return output_rows