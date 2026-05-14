import re

def process_data(rows):
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [header]
    
    col_map = {
        'ean': -1,
        'name': -1,
        'brand': -1,
        'price': -1,
        'qty': -1,
        'stock_status': -1
    }

    # Identifying headers and starting processing from data rows
    data_start_idx = 0
    for i, row in enumerate(rows):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if 'ean' in row_str and 'price' in " ".join(row_str):
            for idx, val in enumerate(row_str):
                if 'ean' in val: col_map['ean'] = idx
                elif 'item' in val or 'description' in val: col_map['name'] = idx
                elif 'manufacturer' in val or 'brand' in val: col_map['brand'] = idx
                elif 'price' in val: col_map['price'] = idx
                elif 'qty' in val: col_map['qty'] = idx
                elif 'stock' in val: col_map['stock_status'] = idx
            data_start_idx = i + 1
            break

    # If no headers found, we can't reliably map columns based on sample structure
    if col_map['ean'] == -1:
        return output

    exclude_terms = [
        "washing machine", "dryer", "dishwasher", "refrigerator", 
        "freezer", "oven", "hob", "cooker", "stove", "scooter",
        "refurbished", "renewed", "reconditioned", "remanufactured"
    ]

    for i in range(data_start_idx, len(rows)):
        row = rows[i]
        if not row or len(row) <= max(col_map.values()):
            continue
            
        try:
            # EAN Cleaning
            raw_ean = str(row[col_map['ean']] or "")
            ean_digits = re.sub(r'\D', '', raw_ean)
            if not ean_digits: continue
            ean = ean_digits.zfill(13)
            
            # Name Construction
            brand = str(row[col_map['brand']] or "").strip()
            item = str(row[col_map['name']] or "").strip()
            full_name = f"{brand} {item}".strip()
            
            # Exclusion Filters
            name_lower = full_name.lower()
            if any(term in name_lower for term in exclude_terms):
                continue
            
            # Price Cleaning
            raw_price = str(row[col_map['price']] or "")
            price_match = re.search(r'(\d+[\.,]\d+|\d+)', raw_price)
            if not price_match: continue
            price = float(price_match.group(1).replace(',', '.'))
            if price < 2.50:
                continue
                
            # Quantity Cleaning
            raw_qty = str(row[col_map['qty']] or "0")
            qty_match = re.search(r'\d+', raw_qty)
            qty = int(qty_match.group(0)) if qty_match else 0
            if qty <= 4:
                continue

            # Availability / Stock Status Filter
            status = str(row[col_map['stock_status']] or "").lower()
            # Only keep "ready" or empty (assuming available) and exclude dates/incoming
            if any(term in status for term in ['incoming', 'expected', 'delivery']) or (status and 'ready' not in status):
                continue

            # Total Price Calculation
            total_price = round(price * qty, 2)
            if total_price < 100:
                continue

            output.append([
                ean,
                full_name,
                price,
                qty,
                total_price,
                "duna"
            ])
            
        except (ValueError, IndexError):
            continue

    return output