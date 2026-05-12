import re

def process_data(rows):
    if not rows:
        return []

    # Final headers
    header_row = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    # Identify indices
    idx_ean = -1
    idx_name = -1
    idx_price = -1
    idx_qty = -1
    
    # Try to find headers from the first row
    first_row = [str(cell).lower() if cell is not None else "" for cell in rows[0]]
    for i, cell in enumerate(first_row):
        if 'ean' in cell:
            idx_ean = i
        elif 'description' in cell or 'model' in cell:
            idx_name = i
        elif 'price' in cell or 'cost' in cell:
            idx_price = i
        elif 'ready stock' in cell or 'qty' in cell or 'quantity' in cell:
            # Prefer 'ready stock' for available items based on guidelines
            if 'ready' in cell or idx_qty == -1:
                idx_qty = i

    # Fallback to inference if headers weren't clear
    if idx_ean == -1: idx_ean = 6
    if idx_name == -1: idx_name = 2
    if idx_price == -1: idx_price = 4
    if idx_qty == -1: idx_qty = 3

    processed = [header_row]
    
    # Filtering patterns
    refurb_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_pattern = re.compile(r'scooter', re.IGNORECASE)

    for row in rows[1:]:
        # Skip empty rows or rows with no data
        if not row or all(cell is None for cell in row):
            continue
            
        try:
            # 1. Clean Name
            name = str(row[idx_name]).strip() if row[idx_name] else ""
            if not name:
                continue
            
            # Filter Refurbished and Scooters
            if refurb_pattern.search(name) or scooter_pattern.search(name):
                continue

            # 2. Clean Quantity (Stock)
            # Only consider "Ready Stock" based on specific sample rules
            raw_qty = str(row[idx_qty]) if row[idx_qty] is not None else "0"
            qty_clean = "".join(filter(str.isdigit, raw_qty))
            quantity = int(qty_clean) if qty_clean else 0
            
            # Rule: Quantity <= 4 invalid
            if quantity <= 4:
                continue

            # 3. Clean Price
            raw_price = str(row[idx_price]) if row[idx_price] is not None else "0"
            # Remove non-numeric except dot/comma
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            
            # Rule: Price < 2.50 invalid
            if price < 2.50:
                continue

            # 4. Total Stock Value Filter
            total_price = round(price * quantity, 2)
            if total_price < 100:
                continue

            # 5. Clean EAN
            raw_ean = str(row[idx_ean]) if row[idx_ean] is not None else ""
            ean_digits = "".join(filter(str.isdigit, raw_ean))
            if not ean_digits:
                continue
            ean = ean_digits.zfill(13)

            # Build final row
            processed.append([
                ean,
                name,
                price,
                quantity,
                total_price,
                "eurotronics"
            ])

        except (ValueError, IndexError):
            continue

    return processed