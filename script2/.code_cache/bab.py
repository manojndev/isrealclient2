import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    col_map = {"ean": None, "name": None, "price": None, "qty": None, "moq": None, "avail": None}
    header_idx = -1

    # 1. Identify Header Row and Map Columns
    for i, row in enumerate(rows[:10]):
        # Convert row to lower-case string for keyword matching
        row_str = [str(c).lower() if c is not None else "" for c in row]
        combined = " ".join(row_str)
        
        # Check for core keywords
        if any(key in combined for key in ["ean", "price", "stock", "qty", "name", "sku"]):
            header_idx = i
            for idx, cell in enumerate(row_str):
                if "ean" in cell: col_map["ean"] = idx
                elif any(x in cell for x in ["name", "description", "product"]): col_map["name"] = idx
                elif "price" in cell or "euro" in cell: col_map["price"] = idx
                elif any(x in cell for x in ["stock", "free stock", "qty", "quantity"]): col_map["qty"] = idx
                elif "moq" in cell or "min" in cell: col_map["moq"] = idx
                elif any(x in cell for x in ["avail", "status", "delivery"]): col_map["avail"] = idx
            break

    # 2. Heuristic Column Inference if Header search failed
    if col_map["ean"] is None or col_map["price"] is None:
        start_search = header_idx + 1 if header_idx != -1 else 0
        for i in range(start_search, min(len(rows), start_search + 5)):
            for idx, cell in enumerate(rows[i]):
                val = str(cell) if cell is not None else ""
                digits = re.sub(r'\D', '', val)
                if len(digits) >= 12 and col_map["ean"] is None: col_map["ean"] = idx
                elif ('.' in val or (val.isdigit() and int(val) > 100)) and col_map["price"] is None: col_map["price"] = idx
                elif len(val) > 15 and col_map["name"] is None: col_map["name"] = idx

    data_start = header_idx + 1 if header_idx != -1 else 0
    final_rows = []
    has_moq_data = False

    # 3. Process Data Rows
    for row in rows[data_start:]:
        if not any(row): continue
        
        # Extract Availability info to filter out non-stock
        avail_text = ""
        if col_map["avail"] is not None and col_map["avail"] < len(row):
            avail_text = str(row[col_map["avail"]]).lower()
        
        # Whole row check for incoming signals
        row_content = " ".join(str(c).lower() for c in row if c is not None)
        if any(term in row_content for term in ["incoming", "eta", "expected", "delivery", "ordered", "2026"]):
            # If the text also contains "stock" or "ready", it might be a header or status. 
            # We strictly exclude if it implies a future date or "incoming" status.
            if "incoming" in avail_text or re.search(r'\d{2}\.\d{2}', row_content):
                continue

        # Extract Fields
        try:
            ean_raw = str(row[col_map["ean"]]) if col_map["ean"] is not None else ""
            ean = "".join(filter(str.isdigit, ean_raw)).zfill(13)
            
            name = str(row[col_map["name"]]).strip() if col_map["name"] is not None else ""
            
            price_raw = str(row[col_map["price"]]) if col_map["price"] is not None else "0"
            price = float(re.sub(r'[^\d.]', '', price_raw.replace(',', '.')))
            
            qty_raw = str(row[col_map["qty"]]) if col_map["qty"] is not None else "0"
            qty = int(re.sub(r'\D', '', qty_raw))
        except (ValueError, IndexError):
            continue

        # Filtering Rules
        if qty <= 4: continue
        if price < 2.50: continue
        total_price = round(price * qty, 2)
        if total_price < 100.0: continue
        if len(ean) > 15: continue # Basic EAN sanity check

        # Build Row
        entry = [ean, name, price, qty, total_price, "bab"]
        
        # Handle MOQ
        if col_map["moq"] is not None and col_map["moq"] < len(row):
            moq_val = re.sub(r'\D', '', str(row[col_map["moq"]]))
            entry.append(int(moq_val) if moq_val else 0)
            has_moq_data = True
            
        final_rows.append(entry)

    # 4. Finalize Header and Structure
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq_data:
        header.append("Min Qty")
        # Ensure all rows have MOQ column
        for r in final_rows:
            if len(r) < 7: r.append(0)
    else:
        # If MOQ column was mapped but no data kept, truncate
        final_rows = [r[:6] for r in final_rows]

    return [header] + final_rows