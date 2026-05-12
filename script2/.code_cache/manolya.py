import re

def process_data(rows):
    if not rows:
        return []

    # Final headers structure
    output_headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    # Identify indices
    idx_brand = -1
    idx_art = -1
    idx_ean = -1
    idx_stock = -1
    idx_price = -1

    # Attempt to find headers in the first few rows
    for i, row in enumerate(rows[:5]):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if "ean" in row_str or "stock" in row_str or "price" in " ".join(row_str):
            for j, val in enumerate(row_str):
                if "brand" in val: idx_brand = j
                elif "art" in val: idx_art = j
                elif "ean" in val: idx_ean = j
                elif "stock" in val: idx_stock = j
                elif "price" in val: idx_price = j
            data_start_idx = i + 1
            break
    else:
        # Inference fallback based on sample data if no clear header row found
        idx_brand, idx_art, idx_ean, idx_stock, idx_price = 0, 1, 2, 3, 4
        data_start_idx = 0

    processed_data = [output_headers]
    
    # Regex patterns
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_regex = re.compile(r'scooter', re.IGNORECASE)

    for row in rows[data_start_idx:]:
        # Skip empty rows
        if not row or all(c is None for c in row):
            continue
            
        try:
            # 1. Quantity Cleaning
            raw_qty = str(row[idx_stock]) if idx_stock < len(row) and row[idx_stock] is not None else "0"
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            quantity = int(qty_clean) if qty_clean else 0
            
            # Rule: Quantity <= 4 invalid
            if quantity <= 4:
                continue

            # 2. Price Cleaning
            raw_price = str(row[idx_price]) if idx_price < len(row) and row[idx_price] is not None else "0"
            price_clean = re.sub(r'[^\d,.]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            
            # Rule: Price < 2.50 invalid
            if price < 2.50:
                continue

            # Rule: Total stock value < 100 EUR invalid
            total_price = round(price * quantity, 2)
            if total_price < 100:
                continue

            # 3. Name Construction
            brand = str(row[idx_brand]).strip() if idx_brand < len(row) and row[idx_brand] else ""
            art = str(row[idx_art]).strip() if idx_art < len(row) and row[idx_art] else ""
            full_name = f"{brand} {art}".strip()
            
            # Rules: Filter Refurbished and Scooters
            if refurb_regex.search(full_name) or scooter_regex.search(full_name):
                continue

            # 4. EAN Cleaning
            raw_ean = str(row[idx_ean]) if idx_ean < len(row) and row[idx_ean] is not None else ""
            ean_clean = re.sub(r'[^\d]', '', raw_ean)
            if not ean_clean:
                continue
            ean = ean_clean.zfill(13)

            # Construct final row
            processed_data.append([
                ean,
                full_name,
                price,
                quantity,
                total_price,
                "manolya"
            ])

        except (ValueError, IndexError):
            continue

    return processed_data