import re

def process_data(rows: list) -> list:
    """
    Processes product data rows to extract EAN, Name, Price, and Stock.
    Applies strict filtering and formatting rules for the smartcom1 supplier.
    """
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [final_header]
    
    col_map = {"ean": -1, "name": -1, "price": -1, "qty": -1, "moq": -1}
    data_start_idx = 0
    
    # 1. Identify Header and Column Mapping
    for i, row in enumerate(rows):
        # Skip empty rows
        if not row or all(c is None or str(c).strip() == "" for c in row):
            continue
            
        row_str = [str(c).upper().strip() for c in row if c is not None]
        
        # Check for header keywords
        if "EAN" in row_str or "PRICE" in row_str or "MODEL" in row_str:
            for j, cell in enumerate(row):
                if cell is None: continue
                c_str = str(cell).upper().strip()
                if "EAN" in c_str: col_map["ean"] = j
                elif "MODEL" in c_str or "DESCRIPTION" in c_str: col_map["name"] = j
                elif "PRICE" in c_str: col_map["price"] = j
                elif "QTY" in c_str or "STOCK" in c_str or "QUANTITY" in c_str: col_map["qty"] = j
                elif "MOQ" in c_str or "MIN" in c_str: col_map["moq"] = j
            data_start_idx = i + 1
            break
            
    # 2. Dynamic Inference (if no header found)
    if col_map["ean"] == -1 or col_map["price"] == -1:
        for i, row in enumerate(rows):
            if not row or len(row) < 3: continue
            for j, cell in enumerate(row):
                val = str(cell or "").strip()
                if len(re.sub(r'\D', '', val)) == 13: col_map["ean"] = j
                elif any(x in val.lower() for x in ["petzl", "apple", "samsung"]): col_map["name"] = j
                elif "." in val and re.match(r'^\d+\.\d+$', val): col_map["price"] = j
                elif val.isdigit() and int(val) < 10000: col_map["qty"] = j
            if col_map["ean"] != -1:
                data_start_idx = i
                break

    # Patterns
    exclude_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured|scooter', re.I)
    incoming_regex = re.compile(r'incoming|delivery|expected|date|\d{2}\.\d{2}', re.I)
    
    has_moq = col_map["moq"] != -1
    if has_moq:
        final_header.append("Min Qty")

    # 3. Process Rows
    for i in range(data_start_idx, len(rows)):
        row = rows[i]
        if not row or len(row) <= max(col_map["ean"], col_map["price"], col_map["qty"]):
            continue
            
        try:
            # Name extraction and exclusion
            name = str(row[col_map["name"]] if col_map["name"] != -1 else "")
            if exclude_regex.search(name):
                continue
                
            # Availability / Incoming Check
            row_text = " ".join(str(c) for c in row if c is not None)
            if incoming_regex.search(row_text) and not re.search(r'ready|in stock', row_text, re.I):
                continue

            # Price Cleaning
            raw_price = str(row[col_map["price"]] or "0")
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean)
            if price < 2.50:
                continue
                
            # Quantity Cleaning
            raw_qty = str(row[col_map["qty"]] or "0")
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            qty = int(qty_clean) if qty_clean else 0
            if qty <= 4:
                continue
                
            # Total Value Calculation
            total_price = price * qty
            if total_price < 100:
                continue
                
            # EAN Cleaning
            raw_ean = str(row[col_map["ean"]] or "")
            ean = re.sub(r'\D', '', raw_ean).zfill(13)
            if len(ean) != 13:
                continue
                
            # Prepare result row
            res_row = [ean, name.strip(), price, qty, round(total_price, 2), "smartcom1"]
            
            if has_moq:
                raw_moq = str(row[col_map["moq"]] or "1")
                moq = int(re.sub(r'\D', '', raw_moq)) if re.search(r'\d', raw_moq) else 1
                res_row.append(moq)
                
            output.append(res_row)
            
        except (ValueError, IndexError):
            continue
            
    return output