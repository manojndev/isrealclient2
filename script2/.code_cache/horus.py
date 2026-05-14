import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val if val is not None else ""))
        if not s:
            return ""
        return s.zfill(13)

    def clean_price(val):
        if val is None or val == "":
            return None
        s = str(val).replace(' ', '').replace('€', '').replace('$', '')
        if ',' in s and '.' not in s:
            s = s.replace(',', '.')
        elif ',' in s and '.' in s:
            s = s.replace(',', '')
        try:
            return float(re.sub(r'[^\d.]', '', s))
        except (ValueError, TypeError):
            return None

    def clean_qty(val):
        if val is None or val == "":
            return None
        s = re.sub(r'[^\d]', '', str(val))
        try:
            return int(s)
        except (ValueError, TypeError):
            return None

    # Identify Column Indices
    header = [str(h).lower() if h is not None else "" for h in rows[0]]
    idx_ean = idx_name = idx_price = idx_qty = -1

    for i, h in enumerate(header):
        if 'ean' in h or 'barcode' in h:
            idx_ean = i
        elif 'description' in h or 'product' in h or 'article' in h or 'item' in h:
            idx_name = i
        elif 'price' in h or 'eur' in h or 'cost' in h:
            idx_price = i
        elif 'qty' in h or 'available' in h or 'stock' in h or 'quantity' in h:
            idx_qty = i

    # Fallback to inference
    if idx_ean == -1 or idx_name == -1 or idx_price == -1:
        sample = rows[1] if len(rows) > 1 else []
        for i, val in enumerate(sample):
            v_str = str(val)
            if idx_ean == -1 and re.match(r'^\d{12,14}$', v_str): idx_ean = i
            elif idx_name == -1 and len(v_str) > 15: idx_name = i
            elif idx_price == -1 and ('.' in v_str or ',' in v_str) and clean_price(val): idx_price = i

    exclude_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured|scooter', re.IGNORECASE)
    incoming_regex = re.compile(r'incoming|expected|delivery|ordered|date|\d{2}\.\d{2}', re.IGNORECASE)

    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    final_rows = [output_header]

    for i, row in enumerate(rows):
        if i == 0 and idx_ean != -1:  # Skip identified header
            continue
        if not any(row):
            continue

        # Extract Raw Values
        raw_ean = row[idx_ean] if idx_ean != -1 else ""
        raw_name = row[idx_name] if idx_name != -1 else ""
        raw_price = row[idx_price] if idx_price != -1 else None
        raw_qty = row[idx_qty] if idx_qty != -1 else None

        # Clean Values
        ean = clean_ean(raw_ean)
        name = str(raw_name).strip()
        price = clean_price(raw_price)
        qty = clean_qty(raw_qty)

        # 1. Basic Validity
        if not ean or len(ean) != 13:
            continue
        if price is None or qty is None:
            continue

        # 2. Filtering Rules
        if qty <= 4:
            continue
        if price < 2.50:
            continue
        
        total_price = price * qty
        if total_price < 100:
            continue

        # 3. Content Filtering
        if exclude_regex.search(name):
            continue

        # 4. Availability Filtering (Check all cells in row for incoming signals)
        is_incoming = False
        for cell in row:
            if cell and incoming_regex.search(str(cell)):
                is_incoming = True
                break
        if is_incoming:
            continue

        # Final Formatting
        final_rows.append([
            ean,
            name,
            price,
            qty,
            round(total_price, 2),
            "horus"
        ])

    return final_rows