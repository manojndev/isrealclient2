import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else ""

    def clean_float(val):
        if val is None or val == "": return 0.0
        s = str(val).replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except:
            return 0.0

    def clean_int(val):
        if val is None or val == "": return 0
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except:
            return 0

    col_map = {"ean": None, "name": None, "price": None, "qty": None, "moq": None, "avail": None}
    
    # Identify header index and map columns
    header_idx = -1
    for i, row in enumerate(rows[:5]):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if any(k in " ".join(row_str) for k in ["ean", "product", "price", "qty", "available"]):
            header_idx = i
            for idx, cell in enumerate(row_str):
                if "ean" in cell: col_map["ean"] = idx
                elif any(k in cell for k in ["product", "description", "name"]): col_map["name"] = idx
                elif "price" in cell or "eur" in cell or "cost" in cell: col_map["price"] = idx
                elif any(k in cell for k in ["qty", "available", "stock", "quant"]): col_map["qty"] = idx
                elif "moq" in cell or "min" in cell: col_map["moq"] = idx
                elif "avail" in cell or "status" in cell: col_map["avail"] = idx
            break

    # Heuristic fallback for column identification
    if col_map["ean"] is None or col_map["price"] is None:
        start_row = header_idx + 1 if header_idx != -1 else 0
        for i in range(start_row, min(len(rows), start_row + 3)):
            for idx, cell in enumerate(rows[i]):
                val = str(cell)
                if len(re.sub(r'\D', '', val)) >= 12: col_map["ean"] = idx
                elif any(c.isalpha() for c in val) and len(val) > 10: col_map["name"] = idx
                elif "." in val or (val.isdigit() and int(val) > 1000): col_map["price"] = idx # Price vs large Int
                elif val.isdigit(): col_map["qty"] = idx

    data_start = header_idx + 1 if header_idx != -1 else 0
    final_rows = []
    has_moq = False

    for row in rows[data_start:]:
        if not any(row) or len(row) <= max((v for v in col_map.values() if v is not None), default=0):
            continue

        # Extract availability and check for incoming stock signals
        avail_str = ""
        if col_map["avail"] is not None:
            avail_str = str(row[col_map["avail"]]).lower()
        
        # Check whole row for "incoming", "eta", etc.
        row_content = " ".join(str(c).lower() for c in row if c is not None)
        if any(k in row_content for k in ["incoming", "eta", "expected", "delivery date", "ordered"]):
            continue
        if any(k in avail_str for k in ["incoming", "backorder", "expected"]):
            continue

        ean = clean_ean(row[col_map["ean"]]) if col_map["ean"] is not None else ""
        name = str(row[col_map["name"]]).strip() if col_map["name"] is not None else ""
        price = clean_float(row[col_map["price"]]) if col_map["price"] is not None else 0.0
        qty = clean_int(row[col_map["qty"]]) if col_map["qty"] is not None else 0
        
        # Standard Filtering
        if len(ean) != 13 or qty <= 4 or price < 2.50:
            continue
        
        total_price = round(price * qty, 2)
        if total_price < 100.0:
            continue

        processed_row = [ean, name, price, qty, total_price, "horus"]
        
        # MOQ Extraction
        if col_map["moq"] is not None:
            moq_val = clean_int(row[col_map["moq"]])
            processed_row.append(moq_val)
            has_moq = True
            
        final_rows.append(processed_row)

    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq:
        header.append("Min Qty")
        # Align rows that might be missing the MOQ value
        for r in final_rows:
            if len(r) < 7: r.append(0)

    return [header] + final_rows