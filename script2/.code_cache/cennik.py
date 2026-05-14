import re

def process_data(rows):
    """
    Expert data processing function for CENNIK (Makita-only) supplier data.
    """
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output_rows = [final_header]

    # Column Mapping Indicators
    col_ean = -1
    col_name = -1
    col_price = -1
    col_stock = -1
    col_incoming = -1
    
    # Identify the true header row (usually Row 1 in this format)
    header_found = False
    data_start_idx = 0
    
    for i, row in enumerate(rows):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if "ean" in row_str and "stock" in row_str:
            for idx, val in enumerate(row_str):
                if "ean" == val: col_ean = idx
                elif "name of product" == val: col_name = idx
                elif "net price eur" == val: col_price = idx
                elif "stock" == val: col_stock = idx
                elif "incoming stock" == val: col_incoming = idx
            data_start_idx = i + 1
            header_found = True
            break
            
    if not header_found:
        return output_rows

    # Regex for exclusions
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_regex = re.compile(r'scooter', re.IGNORECASE)
    makita_regex = re.compile(r'MAKITA', re.IGNORECASE)

    for i in range(data_start_idx, len(rows)):
        row = rows[i]
        if not row or len(row) <= max(col_ean, col_name, col_price, col_stock):
            continue

        try:
            # 1. Extraction & Cleaning
            raw_name = str(row[col_name] or "")
            raw_ean = str(row[col_ean] or "")
            raw_price = str(row[col_price] or "0")
            raw_stock = str(row[col_stock] or "0")
            raw_incoming = str(row[col_incoming] or "0") if col_incoming != -1 else "0"

            # Clean EAN: strictly 13-digit string
            ean_digits = re.sub(r'\D', '', raw_ean)
            ean = ean_digits.zfill(13)

            # Clean Name
            name = raw_name.strip()

            # Clean Price: float
            price_val = float(re.sub(r'[^-0-9.]', '', raw_price.replace(',', '.')))

            # Clean Quantity: integer
            qty_val = int(float(re.sub(r'[^-0-9.]', '', raw_stock.replace(',', '.'))))
            incoming_val = int(float(re.sub(r'[^-0-9.]', '', raw_incoming.replace(',', '.'))))

            # 2. Filtering Rules
            
            # STRICT CENNIK FILTER: Only MAKITA
            if not makita_regex.search(name):
                continue

            # Quantity check
            if qty_val <= 4:
                continue

            # Price check
            if price_val < 2.50:
                continue

            # Total Value check
            total_price = round(price_val * qty_val, 2)
            if total_price < 100:
                continue

            # Ready stock only (Exclude if stock represents incoming or if there's a delivery date)
            # In this dataset, we look at 'Stock' vs 'Incoming stock' and ETA columns
            eta_val = str(row[19]) if len(row) > 19 else "" # Estimated Time of Arrival
            if incoming_val > 0 and qty_val == 0: # Only incoming, no ready stock
                continue
            if eta_val.strip(): # Has a future date
                continue

            # Refurbished / Scooter check
            if refurb_regex.search(name) or scooter_regex.search(name):
                continue

            # 3. Final Row Assembly
            output_rows.append([
                ean,
                name,
                price_val,
                qty_val,
                total_price,
                "cennik"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return output_rows