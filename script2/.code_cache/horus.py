import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # Identify indices
    idx_ean = -1
    idx_name = -1
    idx_qty = -1
    idx_price = -1
    idx_avail = -1

    # Use first row to detect headers
    header_row = [str(cell).lower() if cell is not None else "" for cell in rows[0]]
    
    for i, cell in enumerate(header_row):
        if 'ean' in cell: idx_ean = i
        elif 'desc' in cell or 'product' in cell or 'name' in cell: idx_name = i
        elif 'qty' in cell or 'avail' in cell or 'stock' in cell:
            if 'price' not in cell: idx_qty = i
        elif 'price' in cell or 'eur' in cell: idx_price = i
        elif 'eta' in cell or 'status' in cell or 'delivery' in cell: idx_avail = i

    # Fallback to pattern detection if headers are missing
    if idx_ean == -1 or idx_name == -1 or idx_price == -1:
        sample = rows[min(1, len(rows)-1)]
        for i, cell in enumerate(sample):
            val = str(cell)
            if re.fullmatch(r'\d{12,13}', val): idx_ean = i
            elif any(c.isalpha() for c in val) and len(val) > 10: idx_name = i
            elif re.search(r'\d+[.,]\d+', val) or (val.isdigit() and int(val) > 100): idx_price = i

    result = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]
    
    # Process data rows
    for row in rows[1:]:
        try:
            # Basic data extraction
            raw_ean = str(row[idx_ean]) if idx_ean != -1 else ""
            raw_name = str(row[idx_name]) if idx_name != -1 else ""
            raw_qty = str(row[idx_qty]) if idx_qty != -1 else "0"
            raw_price = str(row[idx_price]) if idx_price != -1 else "0"
            
            # Availability Filtering
            if idx_avail != -1:
                avail_status = str(row[idx_avail]).lower()
                if any(kw in avail_status for kw in ['incoming', 'eta', 'delivery', 'expected']):
                    continue
                if re.search(r'\d{2}\.\d{2}', avail_status): # Date pattern
                    continue

            # Clean EAN
            ean_clean = "".join(filter(str.isdigit, raw_ean))
            if not ean_clean: continue
            ean = ean_clean.zfill(13)

            # Clean Price
            price_clean = raw_price.replace(',', '.').replace(' ', '')
            price_match = re.search(r'(\d+\.?\d*)', price_clean)
            if not price_match: continue
            price = float(price_match.group(1))
            
            # Clean Quantity
            qty_clean = "".join(filter(str.isdigit, raw_qty.split('.')[0]))
            qty = int(qty_clean) if qty_clean else 0

            # Filtering Rules
            if qty <= 4: continue
            if price < 2.50: continue
            
            total_price = round(price * qty, 2)
            if total_price < 100.0: continue

            # Construct row
            result.append([
                ean,
                raw_name.strip(),
                price,
                qty,
                total_price,
                "horus"
            ])
        except (IndexError, ValueError):
            continue

    return result