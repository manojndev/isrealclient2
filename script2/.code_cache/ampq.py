import re

def process_data(rows):
    if not rows:
        return []

    # Final structure headers
    output_headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    # 1. Identify Column Indices
    # Default indices based on sample: QTY:0, MODEL:1, PN:2, EAN:3, PRICE:4, AVAIL:5
    idx_qty, idx_name, idx_ean, idx_price, idx_avail = -1, -1, -1, -1, -1
    
    # Try to find indices from header row
    header_row = [str(cell).upper().strip() for cell in rows[0]]
    for i, col in enumerate(header_row):
        if 'QTY' in col or 'QUANTITY' in col or 'AVAILABILITY' == col: # QTY or AVAIL might be mixed
            if idx_qty == -1: idx_qty = i
        if 'MODEL' in col or 'NAME' in col or 'DESCRIPTION' in col:
            idx_name = i
        if 'EAN' in col or 'BARCODE' in col:
            idx_ean = i
        if 'PRICE' in col:
            idx_price = i
        if 'AVAILABILITY' in col:
            idx_avail = i

    # Fallback to inference if headers were not clear (based on sample positions)
    if idx_qty == -1: idx_qty = 0
    if idx_name == -1: idx_name = 1
    if idx_ean == -1: idx_ean = 3
    if idx_price == -1: idx_price = 4
    if idx_avail == -1: idx_avail = 5

    processed_rows = [output_headers]
    
    # Regex for filtering
    refurb_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_pattern = re.compile(r'scooter', re.IGNORECASE)

    # Skip header row for processing
    data_rows = rows[1:] if idx_qty != -1 or idx_name != -1 else rows

    for row in data_rows:
        try:
            # --- Extract and Clean Data ---
            
            # Availability / Stock Status Filter
            avail_str = str(row[idx_avail]).lower() if idx_avail < len(row) else ""
            if "incoming" in avail_str or "days" in avail_str or "." in avail_str:
                continue
            if "in stock" not in avail_str and avail_str != "":
                # If there's text but it doesn't say in stock, and contains dates/incoming, skip
                if any(x in avail_str for x in ["incoming", "due", "backorder"]):
                    continue

            # Name
            name = str(row[idx_name]).strip()
            # Filter Refurbished/Scooters
            if refurb_pattern.search(name) or scooter_pattern.search(name):
                continue

            # Quantity
            qty_raw = str(row[idx_qty])
            qty_clean = re.sub(r'[^\d]', '', qty_raw)
            quantity = int(qty_clean) if qty_clean else 0
            if quantity <= 4:
                continue

            # Price
            price_raw = str(row[idx_price])
            price_clean = re.sub(r'[^\d.]', '', price_raw.replace(',', '.'))
            price = float(price_clean) if price_clean else 0.0
            if price < 2.50:
                continue

            # Total Stock Value Filter
            total_price = round(price * quantity, 2)
            if total_price < 100:
                continue

            # EAN
            ean_raw = str(row[idx_ean])
            ean_clean = re.sub(r'[^\d]', '', ean_raw)
            if not ean_clean or len(ean_clean) < 8: # Basic validation
                continue
            ean = ean_clean.zfill(13)

            # --- Construct Final Row ---
            # ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
            new_row = [
                ean,
                name,
                price,
                quantity,
                total_price,
                "ampq"
            ]
            processed_rows.append(new_row)

        except (ValueError, IndexError):
            continue

    return processed_rows