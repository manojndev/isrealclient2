import re

def process_data(rows):
    if not rows:
        return []

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_data = [final_header]
    
    col_map = {"ean": -1, "name": -1, "price": -1, "qty": -1}
    
    # Identify Header Row and Map Columns
    for i, row in enumerate(rows):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if "ean" in row_str or "description" in row_str:
            for idx, cell in enumerate(row_str):
                if "ean" in cell:
                    col_map["ean"] = idx
                elif "description" in cell or "artikel" in cell:
                    col_map["name"] = idx
                elif "price" in cell:
                    col_map["price"] = idx
                elif "stock" in cell or "qty" in cell:
                    col_map["qty"] = idx
            start_index = i + 1
            break
    else:
        # Fallback if no header text found
        col_map = {"name": 1, "ean": 2, "qty": 4, "price": 5}
        start_index = 0

    exclude_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured|scooter', re.IGNORECASE)

    for r_idx in range(start_index, len(rows)):
        row = rows[r_idx]
        if not row or len(row) <= max(col_map.values()):
            continue
            
        try:
            # 1. Name and Filtering
            name = str(row[col_map["name"]]).strip()
            if not name or name.lower() == "none" or exclude_pattern.search(name):
                continue
                
            # 2. EAN Cleaning
            ean_raw = re.sub(r'\D', '', str(row[col_map["ean"]]))
            if not ean_raw:
                continue
            ean = ean_raw.zfill(13)
            
            # 3. Price Cleaning
            price_raw = str(row[col_map["price"]]).replace('\xa0', '').strip()
            price_match = re.search(r'(\d+[\.,]\d+|\d+)', price_raw)
            if not price_match:
                continue
            price = float(price_match.group(1).replace(',', '.'))
            
            # 4. Quantity Cleaning
            qty_raw = str(row[col_map["qty"]])
            qty_clean = re.sub(r'[^\d]', '', qty_raw)
            qty = int(qty_clean) if qty_clean else 0
            
            # 5. Availability Check
            # Check row for "incoming" or date patterns to ensure ready stock
            row_content = " ".join(str(c) for c in row).lower()
            if any(term in row_content for term in ["incoming", "delivery", "expect"]):
                continue

            # Standard Processing Filters
            if qty <= 4:
                continue
            if price < 2.50:
                continue
                
            total_price = round(price * qty, 2)
            if total_price < 100:
                continue
                
            processed_data.append([
                ean,
                name,
                price,
                qty,
                total_price,
                "hifi"
            ])
            
        except (ValueError, IndexError, TypeError):
            continue

    return processed_data