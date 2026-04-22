import re

def process_data(rows: list[list]) -> list[list]:
    if not rows:
        return []

    # Final headers structure
    header_out = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    ean_idx = -1
    name_idx = -1
    qty_idx = -1
    price_idx = -1
    moq_idx = -1
    avail_idx = -1

    # Heuristic to find column indices
    # We examine the first row and potentially the second to identify columns
    first_row = [str(x).upper() if x is not None else "" for x in rows[0]]
    
    for i, col in enumerate(first_row):
        if 'EAN' in col: ean_idx = i
        elif 'DESC' in col or 'PRODUCT' in col or 'MODEL' in col: name_idx = i
        elif 'QTY' in col or 'AVAIL' in col or 'STOCK' in col: 
            if 'DATE' in col or 'INCOMING' in col: avail_idx = i
            else: qty_idx = i
        elif 'PRICE' in col or 'EUR' in col or 'COST' in col: price_idx = i
        elif 'MOQ' in col or 'MIN' in col: moq_idx = i

    # Fallback to data pattern recognition if headers are missing or ambiguous
    if len(rows) > 1:
        sample = rows[1]
        for i, val in enumerate(sample):
            if val is None: continue
            s_val = str(val).strip()
            if ean_idx == -1 and s_val.isdigit() and len(s_val) >= 12: ean_idx = i
            elif qty_idx == -1 and s_val.isdigit() and len(s_val) < 6: qty_idx = i
            elif price_idx == -1 and re.search(r'\d', s_val) and ('.' in s_val or ',' in s_val or float(s_val.replace(',', '.')) > 0):
                if i != ean_idx and i != qty_idx: price_idx = i

    # If Name still not found, try to find the longest string
    if name_idx == -1:
        max_len = 0
        for i, val in enumerate(rows[1] if len(rows) > 1 else rows[0]):
            if isinstance(val, str) and len(val) > max_len:
                max_len = len(val)
                name_idx = i

    has_moq = moq_idx != -1
    if has_moq:
        header_out.append("Min Qty")

    result = [header_out]
    
    # Process data rows
    start_idx = 1 if ean_idx != -1 or name_idx != -1 else 0
    for row in rows[start_idx:]:
        try:
            # Extract EAN
            raw_ean = str(row[ean_idx]).strip() if ean_idx < len(row) and row[ean_idx] is not None else ""
            ean_clean = "".join(filter(str.isdigit, raw_ean))
            if not ean_clean: continue
            ean_final = ean_clean.zfill(13)

            # Extract Name
            name_final = str(row[name_idx]).strip() if name_idx < len(row) and row[name_idx] is not None else ""
            if not name_final: continue

            # Extract Price
            raw_price = str(row[price_idx]) if price_idx < len(row) and row[price_idx] is not None else "0"
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price_final = float(price_clean) if price_clean else 0.0

            # Extract Quantity
            raw_qty = str(row[qty_idx]) if qty_idx < len(row) and row[qty_idx] is not None else "0"
            qty_clean = "".join(filter(str.isdigit, raw_qty))
            qty_final = int(qty_clean) if qty_clean else 0

            # Availability/Incoming Check
            is_invalid_stock = False
            if avail_idx != -1 and avail_idx < len(row) and row[avail_idx]:
                avail_val = str(row[avail_idx]).lower()
                if any(x in avail_val for x in ["incoming", "expected", ".", "202"]):
                    is_invalid_stock = True
            
            # Standard Filtering
            if is_invalid_stock: continue
            if qty_final <= 4: continue
            if price_final < 2.50: continue
            
            total_val = price_final * qty_final
            if total_val < 100.0: continue

            # Build processed row
            new_row = [
                ean_final,
                name_final,
                price_final,
                qty_final,
                round(total_val, 2),
                "abox"
            ]

            if has_moq:
                raw_moq = str(row[moq_idx]) if moq_idx < len(row) and row[moq_idx] is not None else "1"
                moq_clean = "".join(filter(str.isdigit, raw_moq))
                new_row.append(int(moq_clean) if moq_clean else 1)

            result.append(new_row)

        except (ValueError, IndexError):
            continue

    return result