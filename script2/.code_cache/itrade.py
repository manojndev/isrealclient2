import re

def process_data(rows):
    if not rows:
        return []

    # Final headers
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = [header]

    # Mapping to store column indices
    col_map = {"qty": -1, "name": -1, "ean": -1, "price": -1}

    # Attempt to find header row and map indices
    start_row = 0
    for i, row in enumerate(rows[:5]):
        row_str = [str(cell).lower() if cell is not None else "" for cell in row]
        if 'ean' in row_str or 'article' in row_str or 'price' in row_str:
            for idx, val in enumerate(row_str):
                if 'qty' in val or 'quant' in val: col_map["qty"] = idx
                elif 'ean' in val or 'barcode' in val: col_map["ean"] = idx
                elif 'price' in val or 'preis' in val: col_map["price"] = idx
                elif 'article' in val or 'model' in val or 'name' in val: col_map["name"] = idx
            start_row = i + 1
            break
    
    # Fallback mapping based on sample structure if header not found
    if col_map["ean"] == -1:
        col_map = {"qty": 0, "name": 1, "ean": 2, "price": 3}
        start_row = 1

    exclude_regex = re.compile(r'scooter|refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)

    for i in range(start_row, len(rows)):
        row = rows[i]
        if not row or len(row) <= max(col_map.values()):
            continue

        try:
            # 1. Clean Name and check exclusions
            name = str(row[col_map["name"]]).strip()
            if exclude_regex.search(name):
                continue

            # 2. Clean EAN (Strictly 13 digits)
            ean_raw = re.sub(r'\D', '', str(row[col_map["ean"]]))
            if not ean_raw:
                continue
            ean = ean_raw.zfill(13)[-13:]

            # 3. Clean Price
            price_raw = str(row[col_map["price"]])
            price_clean = re.sub(r'[^\d.,]', '', price_raw).replace(',', '.')
            price = float(price_clean)
            if price < 2.50:
                continue

            # 4. Clean Quantity
            qty_raw = str(row[col_map["qty"]])
            qty_clean = re.sub(r'[^\d.]', '', qty_raw)
            qty = int(float(qty_clean)) if qty_clean else 0
            if qty <= 4:
                continue

            # 5. Availability check (General logic for 'incoming' etc)
            # Checking all cells in the row for availability keywords
            row_text = " ".join([str(c).lower() for c in row if c])
            if any(word in row_text for word in ["incoming", "delivery date", "estimated", "expected"]):
                continue

            # 6. Calculations
            total_price = round(price * qty, 2)
            if total_price < 100:
                continue

            # Output mapping
            processed_rows.append([
                ean,
                name,
                price,
                qty,
                total_price,
                "itrade"
            ])

        except (ValueError, TypeError, IndexError):
            continue

    return processed_rows