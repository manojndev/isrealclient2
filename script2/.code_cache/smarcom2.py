import re

def process_data(rows):
    """
    Expert Python data processing function for smartcom2 datasets.
    """
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # 1. Identify Column Indices
    idx_map = {"ean": -1, "name": -1, "price": -1, "qty": -1, "moq": -1}
    
    # Analyze first row for headers
    first_row = [str(c).lower().strip() if c is not None else "" for c in rows[0]]
    for i, cell in enumerate(first_row):
        if 'ean' in cell: idx_map["ean"] = i
        elif 'model' in cell or 'description' in cell or 'name' in cell: idx_map["name"] = i
        elif 'price' in cell or 'preis' in cell: idx_map["price"] = i
        elif 'qty' in cell or 'stock' in cell or 'quantity' in cell or 'bestand' in cell: idx_map["qty"] = i
        elif 'moq' in cell or 'minimal' in cell: idx_map["moq"] = i

    # Fallback to pattern inference if headers are missing
    if idx_map["ean"] == -1 or idx_map["price"] == -1:
        sample = rows[0] if len(rows) > 0 else []
        for i, cell in enumerate(sample):
            val = str(cell)
            if re.match(r'^\d{12,14}$', val): idx_map["ean"] = i
            elif any(x in val.lower() for x in ["victorinox", "apple", "samsung"]): idx_map["name"] = i
            elif re.search(r'\d+\.\d+', val): idx_map["price"] = i
            elif val.isdigit(): idx_map["qty"] = i

    # Define return header
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    has_moq_source = idx_map["moq"] != -1
    if has_moq_source:
        final_header.append("Min Qty")

    processed_rows = [final_header]
    
    # Regex for exclusions
    refurb_pat = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_pat = re.compile(r'scooter', re.IGNORECASE)
    incoming_pat = re.compile(r'incoming|zulauf|delivery|expected|\d{2}\.\d{2}', re.IGNORECASE)

    # 2. Process Data
    # Skip header row if it was identified as such
    start_idx = 1 if idx_map["ean"] != -1 else 0

    for r_idx in range(start_idx, len(rows)):
        row = rows[r_idx]
        if not row or all(c is None for c in row):
            continue

        try:
            # Name extraction & filtering
            raw_name = str(row[idx_map["name"]]) if idx_map["name"] != -1 else ""
            if refurb_pat.search(raw_name) or scooter_pat.search(raw_name):
                continue
            
            # Stock filtering for incoming dates
            row_str = " ".join(str(c) for c in row if c is not None).lower()
            if incoming_pat.search(row_str) and not re.search(r'ready|in stock', row_str):
                continue

            # Price Cleaning
            p_val = str(row[idx_map["price"]]) if idx_map["price"] != -1 else "0"
            p_clean = re.sub(r'[^\d.,]', '', p_val).replace(',', '.')
            price = float(p_clean)
            if price < 2.50:
                continue

            # Quantity Cleaning
            q_val = str(row[idx_map["qty"]]) if idx_map["qty"] != -1 else "0"
            qty = int(float(re.sub(r'[^\d.]', '', q_val))) if re.search(r'\d', q_val) else 0
            if qty <= 4:
                continue

            # Total Value Filter
            total_price = round(price * qty, 2)
            if total_price < 100.0:
                continue

            # EAN Cleaning
            ean_val = str(row[idx_map["ean"]]) if idx_map["ean"] != -1 else ""
            ean = "".join(filter(str.isdigit, ean_val)).zfill(13)
            if len(ean) != 13:
                continue

            # Final Row Construction
            new_row = [ean, raw_name.strip(), price, qty, total_price, "smarcom2"]
            
            if has_moq_source:
                m_val = str(row[idx_map["moq"]]) if row[idx_map["moq"]] is not None else "1"
                moq = int(float(re.sub(r'[^\d.]', '', m_val))) if re.search(r'\d', m_val) else 1
                new_row.append(moq)

            processed_rows.append(new_row)

        except (ValueError, IndexError, ZeroDivisionError):
            continue

    return processed_rows