import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    header = [str(cell).lower().strip() for cell in rows[0]]
    
    # Identify indices
    idx_ean = -1
    idx_name = -1
    idx_price = -1
    idx_qty = -1

    # Try mapping by header names
    for i, col in enumerate(header):
        if 'ean' in col or 'barcode' in col:
            idx_ean = i
        elif 'article' in col or 'name' in col or 'description' in col:
            idx_name = i
        elif 'price' in col or 'cost' in col:
            idx_price = i
        elif 'qty' in col or 'stock' in col or 'quantity' in col:
            idx_qty = i

    # Fallback/Validation by data pattern if header mapping is incomplete
    if idx_ean == -1 or idx_name == -1 or idx_price == -1:
        sample_row = rows[1] if len(rows) > 1 else rows[0]
        for i, val in enumerate(sample_row):
            s_val = str(val).strip()
            if re.search(r'\d{12,13}', s_val) and idx_ean == -1:
                idx_ean = i
            elif any(word in s_val.lower() for word in ['apple', 'amazon', 'samsung']) and idx_name == -1:
                idx_name = i
            elif (isinstance(val, (int, float)) or '.' in s_val) and idx_price == -1:
                idx_price = i

    clean_rows = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]
    
    refurb_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured']
    incoming_terms = ['incoming', 'delivery', 'estimated', 'expected', 'transit', 'weeks']

    for row in rows[1:]:
        try:
            # 1. Extraction
            raw_ean = str(row[idx_ean]).strip() if idx_ean != -1 else ""
            raw_name = str(row[idx_name]).strip() if idx_name != -1 else ""
            raw_price = row[idx_price] if idx_price != -1 else 0
            raw_qty = row[idx_qty] if idx_qty != -1 else 0

            # 2. Cleaning EAN
            ean = "".join(filter(str.isdigit, raw_ean))
            if not ean: continue
            ean = ean.zfill(13)

            # 3. Cleaning Price
            price_str = str(raw_price).replace(',', '.').strip()
            price_val = float(re.sub(r'[^\d.]', '', price_str)) if any(c.isdigit() for c in price_str) else 0.0
            
            # 4. Cleaning Quantity
            qty_str = str(raw_qty).strip()
            qty_val = int(float(re.sub(r'[^\d.]', '', qty_str))) if any(c.isdigit() for c in qty_str) else 0

            # 5. Name & Filtering
            name_lower = raw_name.lower()
            
            # Refurbished Filter
            if any(term in name_lower for term in refurb_terms):
                continue
            
            # Incoming/Ready Stock Filter (check all columns for any mention of incoming dates)
            is_incoming = False
            for cell in row:
                cell_s = str(cell).lower()
                if any(term in cell_s for term in incoming_terms):
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # Standard constraints
            if qty_val <= 4:
                continue
            if price_val < 2.50:
                continue
                
            total_price = price_val * qty_val
            if total_price < 100:
                continue

            # Final check: Price * Qty must be numeric
            clean_rows.append([
                ean,
                raw_name,
                price_val,
                qty_val,
                round(total_price, 2),
                "itrade"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return clean_rows