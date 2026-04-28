import re

def process_data(rows):
    if not rows:
        return []

    # 1. Identify Header Row and Mapping
    header_idx = -1
    for i, row in enumerate(rows[:10]):
        row_str = " ".join([str(c).lower() for c in row if c is not None])
        if "ean" in row_str and ("price" in row_str or "netto" in row_str):
            header_idx = i
            break
    
    if header_idx == -1:
        return []

    headers = [str(h).lower() if h else "" for h in rows[header_idx]]
    
    col_map = {
        "ean": -1,
        "name": -1,
        "brand": -1,
        "price": -1,
        "stock": -1,
        "moq": -1,
        "eta": -1,
        "incoming": -1
    }

    for i, h in enumerate(headers):
        if "ean" in h: col_map["ean"] = i
        elif "name of product" in h or "nazwa" in h: col_map["name"] = i
        elif "producer" in h or "producent" in h: col_map["brand"] = i
        elif "net price eur" in h: col_map["price"] = i # Prioritize EUR per rules
        elif col_map["price"] == -1 and ("net price" in h or "cena netto" in h): col_map["price"] = i
        elif "stock" in h or "stan" in h or "qty" in h: col_map["stock"] = i
        elif "moq" in h or "minimum order" in h: col_map["moq"] = i
        elif "estimated time of arrival" in h or "eta" in h: col_map["eta"] = i
        elif "incoming stock" in h: col_map["incoming"] = i

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = []
    found_moq = False

    # 2. Process Data Rows
    for row in rows[header_idx + 1:]:
        if not row or len(row) <= max(col_map.values()):
            continue

        # Extract Raw Values
        raw_ean = str(row[col_map["ean"]]) if col_map["ean"] != -1 else ""
        raw_name = str(row[col_map["name"]]) if col_map["name"] != -1 else ""
        raw_brand = str(row[col_map["brand"]]) if col_map["brand"] != -1 else ""
        raw_price = str(row[col_map["price"]]) if col_map["price"] != -1 else "0"
        raw_stock = str(row[col_map["stock"]]) if col_map["stock"] != -1 else "0"
        
        # Filtering: MAKITA only
        full_name = f"{raw_brand} {raw_name}".strip()
        if "makita" not in full_name.lower():
            continue

        # Availability/Strict Row Filtering
        eta = str(row[col_map["eta"]]).strip() if col_map["eta"] != -1 else ""
        incoming = str(row[col_map["incoming"]]).strip() if col_map["incoming"] != -1 else "0"
        if eta or (incoming != "0" and incoming != ""):
            continue

        # Clean EAN (13 digits)
        ean_clean = re.sub(r'\D', '', raw_ean)
        ean_clean = ean_clean.zfill(13) if ean_clean else ""
        if not ean_clean:
            continue

        # Clean Price (Float)
        price_clean = raw_price.replace(',', '.')
        price_clean = re.sub(r'[^\d.]', '', price_clean)
        try:
            price = float(price_clean)
        except ValueError:
            continue

        # Clean Quantity (Int)
        qty_clean = re.sub(r'\D', '', raw_stock)
        try:
            qty = int(qty_clean)
        except ValueError:
            continue

        # Standard Processing Filters
        if qty <= 4 or price < 2.50:
            continue
        
        total_price = round(price * qty, 2)
        if total_price < 100.0:
            continue

        # MOQ Extraction
        moq = 0
        if col_map["moq"] != -1:
            try:
                moq = int(re.sub(r'\D', '', str(row[col_map["moq"]])))
                if moq > 0: found_moq = True
            except ValueError:
                moq = 0

        # Build Output Row
        res_row = [ean_clean, full_name, price, qty, total_price, "cennik"]
        if col_map["moq"] != -1 or found_moq:
            res_row.append(moq)
        
        processed_rows.append(res_row)

    # 3. Finalize Output Structure
    if found_moq:
        final_header.append("Min Qty")
        # Ensure all rows have MOQ column
        for r in processed_rows:
            if len(r) == 6: r.append(0)
    else:
        # If MOQ index existed but no values found, strip the extra column
        processed_rows = [r[:6] for r in processed_rows]

    return [final_header] + processed_rows