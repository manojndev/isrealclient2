import re

def process_data(rows: list) -> list:
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_data = [final_header]
    
    idx_name = -1
    idx_ean = -1
    idx_price = -1
    idx_stock = -1
    
    # Locate the actual header row and indices
    start_row = 0
    for i, row in enumerate(rows):
        row_str = [str(c).upper() if c else "" for c in row]
        if 'MODELS' in row_str or 'EAN' in row_str or 'SELL PRICE' in row_str:
            start_row = i + 1
            for j, val in enumerate(row_str):
                if 'MODELS' in val or 'DESCRIPTION' in val: idx_name = j
                elif 'EAN' in val: idx_ean = j
                elif 'PRICE' in val: idx_price = j
                elif 'READY' in val or 'STOCK' in val: 
                    if idx_stock == -1: idx_stock = j
            break
            
    # Refurbished filter
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)

    for r in range(start_row, len(rows)):
        row = rows[r]
        if not row or len(row) < 3:
            continue
            
        try:
            # Extract Name
            name = str(row[idx_name]).strip() if idx_name != -1 else ""
            if not name or name == 'None' or refurb_regex.search(name):
                continue
            
            # Extract EAN
            raw_ean = str(row[idx_ean]).strip() if idx_ean != -1 else ""
            ean = "".join(filter(str.isdigit, raw_ean))
            if not ean:
                continue
            ean = ean.zfill(13)
            
            # Extract Price
            raw_price = str(row[idx_price]).strip() if idx_price != -1 else "0"
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            
            # Extract Quantity
            raw_qty = str(row[idx_stock]).strip() if idx_stock != -1 else "0"
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            qty = int(qty_clean) if qty_clean else 0
            
            # Filter Rules
            if qty <= 4:
                continue
            if price < 2.50:
                continue
            
            total_price = price * qty
            if total_price < 100:
                continue
                
            # Incoming check - Look for delivery times/incoming stock logic
            # Based on sample, Column 4 is "Incoming Stock" and 5 is "Delivery Time"
            # We strictly keep ready stock rows based on the 'Ready Stock' column usage.
            
            processed_data.append([
                ean,
                name,
                price,
                qty,
                round(total_price, 2),
                "smalltronics"
            ])
            
        except (ValueError, IndexError):
            continue

    return processed_data