import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else ""

    def clean_float(val):
        if val is None or val == '': return 0.0
        s = str(val).replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except:
            return 0.0

    def clean_int(val):
        if val is None or val == '': return 0
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except:
            return 0

    col_map = {"ean": None, "name": None, "price": None, "qty": None, "moq": None, "avail": None}
    
    # Identify header row and map columns
    header_idx = -1
    for i, row in enumerate(rows[:10]):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if any(key in " ".join(row_str) for key in ["ean", "article", "price", "qty", "stock"]):
            header_idx = i
            for idx, col_name in enumerate(row_str):
                if "ean" in col_name: col_map["ean"] = idx
                elif any(x in col_name for x in ["article", "description", "name", "model"]): col_map["name"] = idx
                elif "price" in col_name or "preis" in col_name: col_map["price"] = idx
                elif any(x in col_name for x in ["qty", "stock", "menge", "stk"]): col_map["qty"] = idx
                elif "moq" in col_name or "min" in col_name: col_map["moq"] = idx
                elif "avail" in col_name or "status" in col_name: col_map["avail"] = idx
            break

    # Heuristic inference if headers are missing
    if col_map["ean"] is None or col_map["price"] is None:
        start = header_idx + 1 if header_idx != -1 else 0
        for i in range(start, min(len(rows), start + 5)):
            row = rows[i]
            if not any(row): continue
            for idx, cell in enumerate(row):
                val = str(cell) if cell is not None else ""
                digits = re.sub(r'\D', '', val)
                if len(digits) >= 12 and col_map["ean"] is None: col_map["ean"] = idx
                elif any(x in val.lower() for x in ["amazon", "samsung", "apple", "generation"]) and col_map["name"] is None: col_map["name"] = idx
                elif "." in val and col_map["price"] is None: col_map["price"] = idx
                elif val.isdigit() and col_map["qty"] is None: col_map["qty"] = idx

    data_start = header_idx + 1 if header_idx != -1 else 0
    final_rows = []
    has_moq = False

    for row in rows[data_start:]:
        if not any(row) or len(row) <= max((v for v in col_map.values() if v is not None), default=0):
            continue

        # Availability/Incoming filter
        row_content = " ".join(str(c).lower() for c in row if c is not None)
        if any(term in row_content for term in ["incoming", "eta", "delivery", "expected", "ordered", "on order"]):
            continue
        if col_map["avail"] is not None:
            avail_val = str(row[col_map["avail"]]).lower()
            if any(term in avail_val for term in ["incoming", "backorder", "expected"]):
                continue

        ean = clean_ean(row[col_map["ean"]]) if col_map["ean"] is not None else ""
        name = str(row[col_map["name"]]).strip() if col_map["name"] is not None else ""
        price = clean_float(row[col_map["price"]]) if col_map["price"] is not None else 0.0
        qty = clean_int(row[col_map["qty"]]) if col_map["qty"] is not None else 0
        
        # Validation and Filtering
        if len(ean) < 8 or not name or price < 2.50 or qty <= 4:
            continue
        
        total_price = round(price * qty, 2)
        if total_price < 100.0:
            continue

        processed_row = [ean, name, price, qty, total_price, "itrade"]
        
        if col_map["moq"] is not None:
            moq_val = clean_int(row[col_map["moq"]])
            processed_row.append(moq_val)
            has_moq = True
            
        final_rows.append(processed_row)

    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq:
        header.append("Min Qty")
        # Ensure consistency for rows where MOQ might be missing
        for r in final_rows:
            if len(r) < 7: r.append(0)

    return [header] + final_rows