import re

def process_data(rows):
    if not rows:
        return []

    # 1. Identify Column Indices
    # Header logic: Check first row for keywords, otherwise infer from data
    header = [str(cell).lower() for cell in rows[0]]
    idx_ean = -1
    idx_name = -1
    idx_price = -1
    idx_qty = -1
    idx_status = -1

    # Mapping based on header keywords
    for i, col in enumerate(header):
        if 'ean' in col: idx_ean = i
        elif 'model' in col or 'name' in col: idx_name = i
        elif 'price' in col: idx_price = i
        elif 'total' in col or 'qty' in col or 'quantity' in col: idx_qty = i
        elif 'eta' in col or 'status' in col or 'availability' in col: idx_status = i

    # Fallback: Infer from first data row if headers were unclear
    sample = rows[1] if len(rows) > 1 else rows[0]
    for i, val in enumerate(sample):
        val_str = str(val).strip()
        if idx_ean == -1 and val_str.isdigit() and len(val_str) >= 10: idx_ean = i
        if idx_price == -1 and ('€' in val_str or re.search(r'\d+[.,]\d{2}', val_str)): idx_price = i
        if idx_qty == -1 and isinstance(val, (int, float)): idx_qty = i
        if idx_name == -1 and len(val_str) > 15: idx_name = i

    # 2. Process Rows
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [final_header]
    
    # Skip header if it was indeed a header row
    start_row = 1 if idx_ean != -1 or idx_name != -1 else 0
    
    for row in rows[start_row:]:
        try:
            # Status Filter: Only 'ready' or 'available'
            if idx_status != -1:
                status = str(row[idx_status]).lower().strip()
                if status not in ['ready', 'available', 'in stock']:
                    continue

            # Extract and Clean EAN (13 digits, left-pad)
            raw_ean = re.sub(r'\D', '', str(row[idx_ean]))
            ean = raw_ean.zfill(13)
            if len(ean) != 13: continue

            # Extract Name
            name = str(row[idx_name]).strip()

            # Extract Price (Float)
            raw_price = str(row[idx_price]).replace(',', '.')
            price_match = re.search(r'(\d+(?:\.\d+)?)', raw_price)
            if not price_match: continue
            price = float(price_match.group(1))
            if price < 2.50: continue

            # Extract Quantity (Integer)
            raw_qty = str(row[idx_qty])
            qty_match = re.search(r'(\d+)', raw_qty)
            if not qty_match: continue
            qty = int(qty_match.group(1))
            
            # Filtering Rules
            if qty <= 4: continue
            
            total_price = round(price * qty, 2)
            if total_price < 100: continue

            # Construct Row
            output.append([
                ean,
                name,
                price,
                qty,
                total_price,
                "smaltronic"
            ])
            
        except (IndexError, ValueError, TypeError):
            continue

    return output