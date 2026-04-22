import re

def process_data(rows):
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = [header]
    
    col_map = {
        "ean": -1,
        "name": -1,
        "manufacturer": -1,
        "price": -1,
        "qty": -1,
        "stock_status": -1
    }

    # Find the real header row and identify column indices
    data_start_idx = 0
    for r_idx, row in enumerate(rows):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if "ean" in row_str and ("price" in " ".join(row_str) or "qty" in row_str):
            data_start_idx = r_idx + 1
            for c_idx, cell in enumerate(row_str):
                if "ean" in cell: col_map["ean"] = c_idx
                elif "item" in cell or "product" in cell: col_map["name"] = c_idx
                elif "manufacturer" in cell or "brand" in cell: col_map["manufacturer"] = c_idx
                elif "price" in cell: col_map["price"] = c_idx
                elif "qty" in cell or "quantity" in cell: col_map["qty"] = c_idx
                elif "stock" in cell or "availability" in cell: col_map["stock_status"] = c_idx
            break

    # Filtering keywords for large appliances
    excluded_keywords = ["washing machine", "dryer", "dishwasher", "refrigerator", "freezer", "oven", "hob", "cooker", "stove"]

    for row in rows[data_start_idx:]:
        if not row or len(row) <= max(col_map.values()):
            continue

        # Extract and Clean EAN
        ean_val = str(row[col_map["ean"]]) if col_map["ean"] != -1 else ""
        ean_clean = "".join(filter(str.isdigit, ean_val))
        if not ean_clean:
            continue
        ean_final = ean_clean.zfill(13)

        # Extract and Clean Name
        brand = str(row[col_map["manufacturer"]]).strip() if col_map["manufacturer"] != -1 and row[col_map["manufacturer"]] else ""
        item_name = str(row[col_map["name"]]).strip() if col_map["name"] != -1 and row[col_map["name"]] else ""
        full_name = f"{brand} {item_name}".strip()
        
        # DUNA Filter: Large Appliances
        name_lower = full_name.lower()
        if any(kw in name_lower for kw in excluded_keywords):
            continue

        # Extract and Clean Price
        try:
            raw_price = str(row[col_map["price"]]) if col_map["price"] != -1 else "0"
            price_clean = re.sub(r'[^\d.]', '', raw_price.replace(',', '.'))
            price_val = float(price_clean)
        except (ValueError, TypeError):
            continue

        # Extract and Clean Quantity
        try:
            raw_qty = str(row[col_map["qty"]]) if col_map["qty"] != -1 else "0"
            qty_clean = "".join(filter(str.isdigit, raw_qty))
            qty_val = int(qty_clean)
        except (ValueError, TypeError):
            continue

        # Stock Availability Filter
        if col_map["stock_status"] != -1:
            status = str(row[col_map["stock_status"]]).lower()
            # If it contains digits but isn't just a number, it's likely a date (incoming)
            if any(char.isdigit() for char in status) and "." in status:
                continue
            if "ready" not in status and "in stock" not in status and status != "":
                if "incoming" in status or "expected" in status:
                    continue

        # Standard Filtering Rules
        if qty_val <= 4:
            continue
        if price_val < 2.50:
            continue
        
        total_price = price_val * qty_val
        if total_price < 100.0:
            continue

        processed_rows.append([
            ean_final,
            full_name,
            price_val,
            qty_val,
            total_price,
            "duna"
        ])

    return processed_rows