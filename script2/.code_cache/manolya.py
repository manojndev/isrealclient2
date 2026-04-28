import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    def clean_ean(val):
        if val is None: return ""
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else ""

    def clean_float(val):
        if val is None: return 0.0
        s = str(val).replace(',', '.')
        s = re.sub(r'[^\d.]', '', s)
        try:
            return float(s)
        except:
            return 0.0

    def clean_int(val):
        if val is None: return 0
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except:
            return 0

    # Column Mapping logic
    col_indices = {"ean": None, "brand": None, "art": None, "stock": None, "price": None, "moq": None}
    header_idx = -1

    for i, row in enumerate(rows[:5]):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if any(key in " ".join(row_str) for key in ["ean", "stock", "price", "brand"]):
            header_idx = i
            for idx, cell in enumerate(row_str):
                if "ean" in cell: col_indices["ean"] = idx
                elif "brand" in cell: col_indices["brand"] = idx
                elif "art" in cell or "model" in cell: col_indices["art"] = idx
                elif "stock" in cell or "qty" in cell or "menge" in cell: col_indices["stock"] = idx
                elif "price" in cell or "preis" in cell or "€" in cell: col_indices["price"] = idx
                elif "moq" in cell or "min" in cell: col_indices["moq"] = idx
            break

    # Data extraction loop
    processed_rows = []
    has_moq_global = False
    start_idx = header_idx + 1 if header_idx != -1 else 0

    for row in rows[start_idx:]:
        if not row or all(c is None for c in row):
            continue

        # Extract values based on indices or heuristic if header was missing
        raw_ean = row[col_indices["ean"]] if col_indices["ean"] is not None else ""
        raw_price = row[col_indices["price"]] if col_indices["price"] is not None else 0
        raw_stock = row[col_indices["stock"]] if col_indices["stock"] is not None else 0
        
        ean = clean_ean(raw_ean)
        price = clean_float(raw_price)
        qty = clean_int(raw_stock)

        # Name construction: Brand + Art
        brand = str(row[col_indices["brand"]]) if col_indices["brand"] is not None else ""
        art = str(row[col_indices["art"]]) if col_indices["art"] is not None else ""
        name = f"{brand} {art}".strip()

        # Availability/Strict Filtering (Ignore strings containing incoming dates)
        row_content_str = " ".join(str(c).lower() for c in row if c is not None)
        if any(x in row_content_str for x in ["incoming", "eta", "delivery", "expected"]):
            continue

        # Logic filtering
        if len(ean) != 13: continue
        if qty <= 4: continue
        if price < 2.50: continue
        
        total_price = round(price * qty, 2)
        if total_price < 100: continue

        # Result construction
        result_row = [ean, name, price, qty, total_price, "manolya"]
        
        if col_indices["moq"] is not None:
            moq = clean_int(row[col_indices["moq"]])
            result_row.append(moq)
            has_moq_global = True
            
        processed_rows.append(result_row)

    # Final Header
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq_global:
        header.append("Min Qty")
        # Ensure all rows have MOQ column if global flag set
        for r in processed_rows:
            if len(r) < 7: r.append(0)

    return [header] + processed_rows