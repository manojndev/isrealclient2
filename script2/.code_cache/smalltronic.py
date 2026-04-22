import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # 1. Column Identification
    header_row = rows[0]
    col_map = {"ean": -1, "name": -1, "price": -1, "qty": -1, "avail": -1}

    for i, cell in enumerate(header_row):
        val = str(cell).lower()
        if "ean" in val:
            col_map["ean"] = i
        elif "name" in val or "item" in val or "model" in val:
            col_map["name"] = i
        elif "price" in val or "cost" in val:
            col_map["price"] = i
        elif "qty" in val or "sell" in val or "stock" in val or "quantity" in val:
            col_map["qty"] = i
        elif "eta" in val or "avail" in val or "status" in val:
            col_map["avail"] = i

    # Fallback to pattern matching if headers are non-standard
    if col_map["ean"] == -1:
        for i, cell in enumerate(rows[1] if len(rows) > 1 else []):
            s_val = re.sub(r'\D', '', str(cell))
            if len(s_val) >= 11: col_map["ean"] = i

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [final_header]

    for row in rows[1:]:
        try:
            # Availability check (Strict)
            if col_map["avail"] != -1:
                avail_status = str(row[col_map["avail"]]).lower()
                # Check for dates (e.g., 23.03) or "incoming"
                if "ready" not in avail_status and "stock" not in avail_status:
                    if re.search(r'\d{2}[./]\d{2}', avail_status) or "incoming" in avail_status:
                        continue
                if avail_status == "" or "out" in avail_status:
                    continue

            # Quantity Extraction
            raw_qty = str(row[col_map["qty"]]) if col_map["qty"] != -1 else "0"
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            qty = int(qty_clean) if qty_clean else 0
            if qty <= 4:
                continue

            # Price Extraction
            raw_price = str(row[col_map["price"]]) if col_map["price"] != -1 else "0"
            price_clean = raw_price.replace(',', '.').replace(' ', '')
            price_match = re.search(r'(\d+\.?\d*)', price_clean)
            if not price_match:
                continue
            price = float(price_match.group(1))
            if price < 2.50:
                continue

            # Total Stock Value calculation and filter
            total_price = round(price * qty, 2)
            if total_price < 100.0:
                continue

            # EAN Extraction (13-digit string)
            raw_ean = str(row[col_map["ean"]]) if col_map["ean"] != -1 else ""
            ean_clean = re.sub(r'\D', '', raw_ean)
            ean = ean_clean.zfill(13)

            # Name Extraction
            name = str(row[col_map["name"]]).strip() if col_map["name"] != -1 else ""

            # Supplier name constant
            supplier = "smalltronic"

            output.append([ean, name, price, qty, total_price, supplier])

        except (ValueError, IndexError):
            continue

    return output