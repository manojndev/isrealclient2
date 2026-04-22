import re

def process_data(rows):
    if not rows:
        return []

    # Final headers
    headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    # Analyze columns to find indices
    ean_idx = -1
    name_idx = -1
    price_idx = -1
    qty_idx = -1
    avail_idx = -1
    
    # Sample first few rows to detect indices if headers are fuzzy
    # We look at the first row as potential header or data
    header_row = rows[0]
    
    for i, val in enumerate(header_row):
        val_str = str(val).upper().strip()
        if 'EAN' in val_str: ean_idx = i
        elif 'MODEL' in val_str or 'NAME' in val_str or 'DESCRIPTION' in val_str: name_idx = i
        elif 'PRICE' in val_str: price_idx = i
        elif 'QTY' in val_str or 'QUANTITY' in val_str: qty_idx = i
        elif 'AVAIL' in val_str or 'STOCK' in val_str: avail_idx = i

    # If indices not found by header text, infer from first data row
    sample_row = rows[1] if len(rows) > 1 else rows[0]
    for i, val in enumerate(sample_row):
        val_s = str(val).strip()
        if ean_idx == -1 and (val_s.isdigit() and len(val_s) >= 12): ean_idx = i
        if price_idx == -1 and re.match(r'^\d+([.,]\d+)?$', val_s.replace('$', '').replace('€', '').strip()): price_idx = i
        if qty_idx == -1 and val_s.isdigit() and len(val_s) < 6: qty_idx = i

    # If name still not found, take the longest string column
    if name_idx == -1:
        name_idx = 1 if len(sample_row) > 1 else 0

    processed_rows = [headers]
    
    # Start loop from 1 if 0 was a header, else 0
    start_row = 1 if any(isinstance(x, str) and not x.isdigit() for x in rows[0]) else 0

    for row in rows[start_row:]:
        try:
            # 1. Extraction & Cleaning
            # EAN
            raw_ean = str(row[ean_idx]).strip() if ean_idx < len(row) else ""
            clean_ean = "".join(filter(str.isdigit, raw_ean))
            if not clean_ean: continue
            clean_ean = clean_ean.zfill(13)
            
            # Name
            name = str(row[name_idx]).strip() if name_idx < len(row) else ""
            
            # Price
            raw_price = str(row[price_idx]).strip() if price_idx < len(row) else "0"
            clean_price_str = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(clean_price_str) if clean_price_str else 0.0
            
            # Quantity
            raw_qty = str(row[qty_idx]).strip() if qty_idx < len(row) else "0"
            clean_qty_str = "".join(filter(str.isdigit, raw_qty))
            quantity = int(clean_qty_str) if clean_qty_str else 0
            
            # Availability Check
            avail_text = str(row[avail_idx]).lower() if avail_idx != -1 and avail_idx < len(row) else ""
            # Exclude if indicates incoming/future dates
            if any(x in avail_text for x in ["incoming", "delivery", "expected", "202", "."]) and "in stock" not in avail_text:
                continue
            if "in stock" not in avail_text and avail_idx != -1:
                # If availability column exists but doesn't explicitly confirm stock, skip fuzzy ones
                if not any(word in avail_text for word in ["yes", "available", "(in stock)"]):
                    continue

            # 2. Filtering
            if quantity <= 4: continue
            if price < 2.50: continue
            
            total_price = price * quantity
            if total_price < 100: continue
            
            # 3. Output construction
            processed_rows.append([
                clean_ean,
                name,
                price,
                quantity,
                round(total_price, 2),
                "ampq"
            ])
            
        except (ValueError, IndexError):
            continue

    return processed_rows