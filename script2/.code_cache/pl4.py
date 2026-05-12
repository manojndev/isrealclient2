import re

def process_data(rows):
    if not rows:
        return []

    # 1. Identify Column Indices
    # We look at the first few rows to determine which index corresponds to which data type
    header_indices = {"ean": None, "brand": None, "art": None, "price": None, "stock": None}
    
    # Check first row for keywords
    first_row = [str(c).lower() if c is not None else "" for c in rows[0]]
    for i, val in enumerate(first_row):
        if "ean" in val: header_indices["ean"] = i
        elif "brand" in val: header_indices["brand"] = i
        elif "art" in val or "product" in val: header_indices["art"] = i
        elif "price" in val or "€" in val: header_indices["price"] = i
        elif "stock" in val or "qty" in val or "menge" in val: header_indices["stock"] = i

    # Fallback/Validation logic for indices using sample data if header was messy
    def infer_indices(data_rows):
        inferred = {"ean": None, "brand": None, "art": None, "price": None, "stock": None}
        for row in data_rows[:20]:
            for i, cell in enumerate(row):
                if cell is None: continue
                s_cell = str(cell).strip()
                # EAN check (13 digits)
                if re.fullmatch(r'\d{12,14}', s_cell.replace('.0', '')):
                    inferred["ean"] = i
                # Price check (float with decimals)
                elif re.match(r'^\d+[.,]\d{2}$', s_cell):
                    inferred["price"] = i
        return inferred

    inferred = infer_indices(rows)
    for k, v in header_indices.items():
        if v is None: header_indices[k] = inferred[k]

    final_data = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]
    
    # Keywords for exclusion
    exclude_terms = ["refurbished", "renewed", "reconditioned", "remanufactured"]
    scooter_regex = re.compile(r'scooter', re.IGNORECASE)

    for idx, row in enumerate(rows):
        # Skip header or empty rows
        if not any(row) or idx == 0:
            continue
            
        try:
            # --- Extraction & Cleaning ---
            
            # EAN
            raw_ean = str(row[header_indices["ean"]]).split('.')[0] if header_indices["ean"] is not None else ""
            ean = "".join(filter(str.isdigit, raw_ean))
            if len(ean) < 13:
                ean = ean.zfill(13)
            elif len(ean) > 13:
                ean = ean[-13:]
            
            # Name (Brand + Art)
            brand = str(row[header_indices["brand"]] or "").strip()
            art = str(row[header_indices["art"]] or "").strip()
            full_name = f"{brand} {art}".strip()
            
            # Price
            raw_price = str(row[header_indices["price"]] or "0")
            clean_price = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(clean_price)
            
            # Quantity
            raw_qty = str(row[header_indices["stock"]] or "0")
            # Filter out strings like "incoming"
            if any(term in raw_qty.lower() for term in ["incoming", "delivery", "expected"]):
                continue
            qty_match = re.search(r'\d+', raw_qty)
            qty = int(qty_match.group()) if qty_match else 0
            
            # --- Filtering ---
            
            # Price/Qty constraints
            if qty <= 4 or price < 2.50:
                continue
            
            # Total Stock Value
            total_value = round(price * qty, 2)
            if total_value < 100:
                continue
            
            # Name based exclusions
            name_lower = full_name.lower()
            if any(term in name_lower for term in exclude_terms):
                continue
            if scooter_regex.search(name_lower):
                continue
            
            # --- Final Row Construction ---
            final_data.append([
                ean,
                full_name,
                price,
                qty,
                total_value,
                "pl4"
            ])
            
        except (ValueError, IndexError, TypeError):
            continue

    return final_data