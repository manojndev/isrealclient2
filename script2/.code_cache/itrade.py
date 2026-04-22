import re

def process_data(rows):
    if not rows:
        return []

    # Final headers
    header_out = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    ean_idx = -1
    name_idx = -1
    price_idx = -1
    qty_idx = -1
    moq_idx = -1
    avail_idx = -1

    # Analyze potential header row (row 0)
    first_row = [str(x).upper() if x is not None else "" for x in rows[0]]
    for i, col in enumerate(first_row):
        if 'EAN' in col: ean_idx = i
        elif any(x in col for x in ['ARTICLE', 'PRODUCT', 'MODEL', 'DESCRIPTION', 'NAME']): name_idx = i
        elif 'PRICE' in col or 'EUR' in col: price_idx = i
        elif 'QTY' in col or 'QUANTITY' in col or 'STÜCK' in col: qty_idx = i
        elif 'MOQ' in col or 'MIN' in col: moq_idx = i
        elif 'AVAIL' in col or 'STOCK' in col or 'STATUS' in col: avail_idx = i

    # Data pattern fallback for inference
    if len(rows) > 1:
        sample = rows[1]
        for i, val in enumerate(sample):
            if val is None: continue
            s_val = str(val).strip()
            # EAN usually 12-13 digits
            if ean_idx == -1 and s_val.isdigit() and len(s_val) >= 12: ean_idx = i
            # Price usually has decimals or is a float
            elif price_idx == -1 and (isinstance(val, float) or ('.' in s_val and s_val.replace('.', '').isdigit())):
                if i != ean_idx: price_idx = i
            # Qty usually integer
            elif qty_idx == -1 and (isinstance(val, (int, float)) or s_val.isdigit()) and i not in [ean_idx, price_idx]:
                qty_idx = i

    # Detect if MOQ column exists
    has_moq = moq_idx != -1
    if has_moq:
        header_out.append("Min Qty")

    final_data = [header_out]
    
    # Skip header row if identified
    start_row = 1 if ean_idx != -1 or name_idx != -1 or 'QTY' in first_row else 0

    for row in rows[start_row:]:
        try:
            # Availability Filtering (Strict)
            if avail_idx != -1 and avail_idx < len(row):
                status = str(row[avail_idx]).lower()
                if any(x in status for x in ["incoming", "delivery", "expected", "202", "nachschub"]):
                    if "in stock" not in status:
                        continue

            # EAN Cleaning
            raw_ean = str(row[ean_idx]).strip() if ean_idx < len(row) and row[ean_idx] is not None else ""
            ean_clean = "".join(filter(str.isdigit, raw_ean))
            if not ean_clean: continue
            ean_final = ean_clean.zfill(13)

            # Name Cleaning
            name_final = str(row[name_idx]).strip() if name_idx < len(row) and row[name_idx] is not None else ""
            if not name_final: continue

            # Price Cleaning
            raw_price = str(row[price_idx]) if price_idx < len(row) and row[price_idx] is not None else "0"
            price_str = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price_final = float(price_str) if price_str else 0.0

            # Quantity Cleaning
            raw_qty = str(row[qty_idx]) if qty_idx < len(row) and row[qty_idx] is not None else "0"
            qty_str = "".join(filter(str.isdigit, raw_qty.split('.')[0])) # Handle 110.0 cases
            qty_final = int(qty_str) if qty_str else 0

            # Filtering Rules
            if qty_final <= 4: continue
            if price_final < 2.50: continue
            
            total_price = price_final * qty_final
            if total_price < 100.0: continue

            # Construct Row
            processed_row = [
                ean_final,
                name_final,
                price_final,
                qty_final,
                round(total_price, 2),
                "itrade"
            ]

            if has_moq:
                raw_moq = str(row[moq_idx]) if moq_idx < len(row) and row[moq_idx] is not None else "1"
                moq_clean = "".join(filter(str.isdigit, raw_moq))
                processed_row.append(int(moq_clean) if moq_clean else 1)

            final_data.append(processed_row)

        except (ValueError, IndexError):
            continue

    return final_data