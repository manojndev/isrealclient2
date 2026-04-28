import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    def clean_ean(val):
        if val is None: return ""
        s = re.sub(r'\D', '', str(val))
        if not s: return ""
        return s.zfill(13)

    def clean_float(val):
        if val is None: return 0.0
        s = str(val).replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except ValueError:
            return 0.0

    def clean_int(val):
        if val is None: return 0
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except ValueError:
            return 0

    col_map = {"ean": None, "name": None, "price": None, "qty": None, "moq": None}
    header_row_idx = -1

    # Identify Header Row and Map Columns
    for i, row in enumerate(rows[:10]):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if any(key in " ".join(row_str) for key in ["ean", "description", "price", "stock", "ready"]):
            header_row_idx = i
            for idx, col_name in enumerate(row_str):
                if "ean" in col_name: col_map["ean"] = idx
                elif "description" in col_name or "model" in col_name: col_map["name"] = idx
                elif "cost" in col_name or "price" in col_name: col_map["price"] = idx
                elif "ready" in col_name or "stock" in col_name: col_map["qty"] = idx
                elif "moq" in col_name: col_map["moq"] = idx
            break

    # If no headers found, infer by data types from first few non-empty rows
    if col_map["ean"] is None or col_map["price"] is None:
        start = header_row_idx + 1 if header_row_idx != -1 else 0
        for i in range(start, min(len(rows), start + 5)):
            row = rows[i]
            if not any(row): continue
            for idx, cell in enumerate(row):
                val = str(cell) if cell is not None else ""
                if len(re.sub(r'\D', '', val)) >= 12 and col_map["ean"] is None: col_map["ean"] = idx
                elif "." in val and col_map["price"] is None: col_map["price"] = idx
                elif any(c.isalpha() for c in val) and len(val) > 10 and col_map["name"] is None: col_map["name"] = idx

    data_start = header_row_idx + 1 if header_row_idx != -1 else 0
    processed_data = []
    has_moq = False

    for row in rows[data_start:]:
        if not any(row) or len(row) <= max((v for v in col_map.values() if v is not None), default=0):
            continue

        ean = clean_ean(row[col_map["ean"]]) if col_map["ean"] is not None else ""
        name = str(row[col_map["name"]]).strip() if col_map["name"] is not None else ""
        price = clean_float(row[col_map["price"]]) if col_map["price"] is not None else 0.0
        qty = clean_int(row[col_map["qty"]]) if col_map["qty"] is not None else 0
        
        # Filtering
        if not ean or len(ean) > 15: continue
        if qty <= 4: continue
        if price < 2.50: continue
        
        total_price = round(price * qty, 2)
        if total_price < 100.0: continue

        # Construct Row
        new_row = [ean, name, price, qty, total_price, "eurotronics"]
        
        if col_map["moq"] is not None:
            moq_val = clean_int(row[col_map["moq"]])
            new_row.append(moq_val)
            has_moq = True
            
        processed_data.append(new_row)

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq:
        final_header.append("Min Qty")
        # Ensure all rows have MOQ column if at least one did
        for r in processed_data:
            if len(r) < 7: r.append(0)

    return [final_header] + processed_data