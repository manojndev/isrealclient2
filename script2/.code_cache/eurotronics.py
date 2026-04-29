import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # Identify indices based on the first row or data patterns
    header = [str(cell).lower() if cell else "" for cell in rows[0]]
    
    idx_ean = -1
    idx_name = -1
    idx_price = -1
    idx_qty = -1
    idx_transit = -1

    for i, col in enumerate(header):
        if 'ean' in col: idx_ean = i
        elif 'description' in col or 'model' in col: idx_name = i
        elif 'price' in col or 'cost' in col: idx_price = i
        elif 'ready stock' in col or 'qty' in col and 'transit' not in col: idx_qty = i
        elif 'transit' in col: idx_transit = i

    # Fallback inference if headers are messy
    if idx_ean == -1 or idx_name == -1 or idx_price == -1:
        for i, cell in enumerate(rows[1] if len(rows) > 1 else []):
            s_cell = str(cell)
            if re.fullmatch(r'\d{10,13}', s_cell): idx_ean = i
            elif any(c.isalpha() for c in s_cell) and len(s_cell) > 10: idx_name = i
            elif isinstance(cell, (int, float)) or (s_cell.replace('.', '').isdigit()):
                if idx_price == -1: idx_price = i

    output = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]
    
    # Refurbished filter keywords
    refurb_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)

    for row in rows[1:]:
        # Skip empty or null rows
        if not any(row):
            continue
            
        try:
            # 1. Extract and Clean EAN
            raw_ean = str(row[idx_ean]) if idx_ean != -1 else ""
            clean_ean = "".join(filter(str.isdigit, raw_ean))
            if not clean_ean: continue
            ean = clean_ean.zfill(13)

            # 2. Extract Name
            name = str(row[idx_name]).strip() if idx_name != -1 else ""
            if refurb_pattern.search(name):
                continue

            # 3. Extract and Clean Price
            raw_price = str(row[idx_price]) if idx_price != -1 else "0"
            price_str = re.sub(r'[^\d.]', '', raw_price.replace(',', '.'))
            price = float(price_str) if price_str else 0.0
            if price < 2.50:
                continue

            # 4. Extract and Clean Quantity
            # Note: We only take 'ready stock'. We ignore 'transit' or 'incoming'
            raw_qty = str(row[idx_qty]) if idx_qty != -1 else "0"
            qty_str = re.sub(r'[^\d]', '', raw_qty)
            qty = int(qty_str) if qty_str else 0
            
            # Strict Availability Check: check other columns for "incoming" or dates
            is_incoming = False
            for cell in row:
                cell_s = str(cell).lower()
                if "incoming" in cell_s or "delivery" in cell_s or "expected" in cell_s:
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # Filter rules
            if qty <= 4:
                continue
                
            total_price = price * qty
            if total_price < 100:
                continue

            # Append valid row
            output.append([
                ean,
                name,
                price,
                qty,
                round(total_price, 2),
                "eurotronics"
            ])

        except (ValueError, IndexError):
            continue

    return output