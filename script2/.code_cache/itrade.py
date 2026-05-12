import re

def process_data(rows):
    if not rows:
        return []

    # Final headers structure
    header_row = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    # Identify indices from Row 0
    idx_map = {"qty": 0, "name": 1, "ean": 2, "price": 3}
    
    # Optional logic to detect if headers are different, 
    # but based on sample they are consistently [QTY, article, EAN, price, '']
    first_row = [str(c).lower() for c in rows[0]]
    for i, col in enumerate(first_row):
        if 'ean' in col: idx_map['ean'] = i
        elif 'article' in col or 'description' in col: idx_map['name'] = i
        elif 'price' in col: idx_map['price'] = i
        elif 'qty' in col or 'quantity' in col: idx_map['qty'] = i

    # Regex patterns for filtering
    refurb_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_pattern = re.compile(r'scooter', re.IGNORECASE)
    date_pattern = re.compile(r'\d{2}\.\d{2}') # matches dates like 23.03

    processed_data = [header_row]
    
    # Start from index 1 to skip header
    for row in rows[1:]:
        if not row or len(row) <= max(idx_map.values()):
            continue
            
        try:
            # --- Name & Basic Filters ---
            name = str(row[idx_map['name']]).strip()
            if not name:
                continue
            if refurb_pattern.search(name) or scooter_pattern.search(name):
                continue
            
            # Check all columns for "incoming" or dates to satisfy availability rule
            is_incoming = False
            for cell in row:
                cell_str = str(cell).lower()
                if 'incoming' in cell_str or 'due' in cell_str or date_pattern.search(cell_str):
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # --- Price ---
            raw_price = str(row[idx_map['price']])
            # Extract digits and decimal point
            price_str = "".join(re.findall(r'[0-9.]+', raw_price.replace(',', '.')))
            price = float(price_str) if price_str else 0.0
            if price < 2.50:
                continue

            # --- Quantity ---
            raw_qty = str(row[idx_map['qty']])
            qty_str = "".join(re.findall(r'\d+', raw_qty.split('.')[0])) # handle 100.0
            quantity = int(qty_str) if qty_str else 0
            if quantity <= 4:
                continue

            # --- Total Value Calculation ---
            total_price = round(price * quantity, 2)
            if total_price < 100:
                continue

            # --- EAN ---
            raw_ean = str(row[idx_map['ean']])
            ean_clean = "".join(re.findall(r'\d+', raw_ean))
            if not ean_clean:
                continue
            ean = ean_clean.zfill(13)

            # --- Build Final Row ---
            processed_data.append([
                ean,
                name,
                price,
                quantity,
                total_price,
                "itrade"
            ])
            
        except (ValueError, IndexError):
            continue

    return processed_data