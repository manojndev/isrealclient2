import re

def process_data(rows):
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier", "Min Qty"]
    result = [header]
    
    # Global MOQ extraction from text
    global_moq = None
    for row in rows:
        for cell in row:
            if cell and isinstance(cell, str) and "MOQ of" in cell:
                moq_match = re.search(r'MOQ of (\d+)', cell)
                if moq_match:
                    global_moq = int(moq_match.group(1))
                    break

    col_map = {"name": -1, "price": -1, "ean": -1, "stock": -1}
    data_start = -1

    # Identify Table Header
    for i, row in enumerate(rows):
        row_str = [str(c).upper() if c is not None else "" for c in row]
        if "MODELS" in row_str or "SELL PRICE" in row_str:
            for idx, val in enumerate(row_str):
                if "MODEL" in val: col_map["name"] = idx
                elif "PRICE" in val: col_map["price"] = idx
                elif "EAN" in val: col_map["ean"] = idx
                elif "STOCK" in val or "READY" in val: col_map["stock"] = idx
            data_start = i + 1
            break

    if data_start == -1 or col_map["ean"] == -1:
        return [header]

    for i in range(data_start, len(rows)):
        row = rows[i]
        if not row or len(row) <= max(col_map.values()):
            continue

        try:
            # Name extraction
            name = str(row[col_map["name"]]).strip()
            if not name or name.lower() == "none":
                continue
            
            # Filtering: Refurbished and Scooter
            name_lower = name.lower()
            if any(x in name_lower for x in ["refurbished", "renewed", "reconditioned", "remanufactured"]):
                continue
            if re.search(r'scooter', name_lower):
                continue

            # Price extraction
            raw_price = str(row[col_map["price"]])
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            
            # EAN extraction
            raw_ean = str(row[col_map["ean"]])
            ean_clean = re.sub(r'\D', '', raw_ean)
            ean = ean_clean.zfill(13) if ean_clean else ""

            # Quantity extraction
            raw_qty = str(row[col_map["stock"]])
            qty_clean = re.sub(r'\D', '', raw_qty)
            qty = int(qty_clean) if qty_clean else 0

            # Filtering logic
            if qty <= 4:
                continue
            if price < 2.50:
                continue
            
            total_price = round(price * qty, 2)
            if total_price < 100:
                continue
            
            # Availability Check (Ready Stock check)
            # The sample shows 'Ready Stock' header; we only process if qty > 0 and no 'incoming' text
            if "incoming" in str(row[col_map["stock"]]).lower():
                continue

            result.append([
                ean,
                name,
                price,
                qty,
                total_price,
                "smalltronic",
                global_moq
            ])

        except (ValueError, IndexError):
            continue

    return result