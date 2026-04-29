import re

def process_data(rows: list) -> list:
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # Column Mapping
    header = [str(cell).lower() if cell is not None else "" for cell in rows[0]]
    idx_ean = -1
    idx_name = -1
    idx_qty = -1
    idx_price = -1

    for i, col in enumerate(header):
        if 'ean' in col: idx_ean = i
        elif 'description' in col or 'name' in col: idx_name = i
        elif 'qty' in col or 'stock' in col: idx_qty = i
        elif 'price' in col or 'cost' in col: idx_price = i

    # Fallback inference if headers are missing
    if -1 in [idx_ean, idx_name, idx_qty, idx_price]:
        sample = rows[1] if len(rows) > 1 else rows[0]
        for i, val in enumerate(sample):
            s_val = str(val)
            if re.search(r'\d{12,13}', s_val) and idx_ean == -1: idx_ean = i
            elif any(x in s_val.lower() for x in ['bosch', 'dyson', 'delonghi']) and idx_name == -1: idx_name = i
            elif isinstance(val, (int, float)) or (s_val.replace('.', '').isdigit()):
                if idx_qty == -1: idx_qty = i
                elif idx_price == -1: idx_price = i

    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    result = [output_header]

    refurb_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured']
    incoming_terms = ['incoming', 'delivery', 'estimated', 'expected', 'transit', 'weeks']

    for row in rows[1:]:
        try:
            # 1. Extract Name & Filter Refurbished
            name = str(row[idx_name]).strip() if idx_name != -1 else ""
            if any(term in name.lower() for term in refurb_terms):
                continue

            # 2. Extract EAN (Strict 13-digit)
            raw_ean = str(row[idx_ean]).strip() if idx_ean != -1 else ""
            # Handle cases with multiple EANs separated by comma
            first_ean = raw_ean.split(',')[0].strip()
            ean_clean = re.sub(r'\D', '', first_ean)
            if not ean_clean:
                continue
            ean = ean_clean.zfill(13)

            # 3. Extract Price
            raw_price = str(row[idx_price]).strip() if idx_price != -1 else "0"
            price_clean = re.sub(r'[^\d.]', '', raw_price.replace(',', '.'))
            price = float(price_clean) if price_clean else 0.0

            # 4. Extract Quantity
            raw_qty = str(row[idx_qty]).strip() if idx_qty != -1 else "0"
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            qty = int(qty_clean) if qty_clean else 0

            # 5. Availability check (Search entire row for incoming status)
            is_incoming = False
            for cell in row:
                cell_s = str(cell).lower()
                if any(term in cell_s for term in incoming_terms):
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # 6. Filtering Rules
            if qty <= 4:
                continue
            if price < 2.50:
                continue
            
            total_price = price * qty
            if total_price < 100:
                continue

            # 7. Final Row Construction
            result.append([
                ean,
                name,
                price,
                qty,
                round(total_price, 2),
                "horus"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return result