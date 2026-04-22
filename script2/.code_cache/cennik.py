import re

def process_data(rows):
    if not rows:
        return []

    # Final headers structure
    header_out = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    ean_idx = -1
    name_idx = -1
    price_idx = -1
    qty_idx = -1
    producer_idx = -1
    eta_idx = -1
    moq_idx = -1

    # Locate the true header row (usually row 1 based on sample)
    data_start_idx = 0
    for i, row in enumerate(rows[:5]):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if 'ean' in row_str or 'product code' in row_str:
            data_start_idx = i + 1
            for idx, cell in enumerate(row_str):
                if 'ean' == cell: ean_idx = idx
                elif 'name of product' in cell: name_idx = idx
                elif 'net price eur' in cell: price_idx = idx
                elif 'stock' == cell: qty_idx = idx
                elif 'producer' in cell: producer_idx = idx
                elif 'estimated time of arrival' in cell or 'eta' in cell: eta_idx = idx
                elif 'moq' in cell or 'min qty' in cell: moq_idx = idx
            break

    # If header identification failed, fallback to indices from sample
    if ean_idx == -1: ean_idx = 12
    if name_idx == -1: name_idx = 3
    if price_idx == -1: price_idx = 6
    if qty_idx == -1: qty_idx = 10
    if producer_idx == -1: producer_idx = 2
    if eta_idx == -1: eta_idx = 19

    has_moq = moq_idx != -1
    if has_moq:
        header_out.append("Min Qty")

    final_rows = [header_out]

    for row in rows[data_start_idx:]:
        try:
            if not row or len(row) <= max(ean_idx, name_idx, price_idx, qty_idx):
                continue

            # 1. Availability / Incoming Filtering
            # Exclude if ETA is populated or if row explicitly mentions incoming/OnOrder patterns
            eta_val = str(row[eta_idx]).strip() if eta_idx != -1 else ""
            if eta_val and eta_val.lower() != 'none' and eta_val != '0':
                continue

            # 2. Extract and Clean Quantity
            raw_qty = str(row[qty_idx]).strip()
            qty_clean = "".join(filter(str.isdigit, raw_qty))
            quantity = int(qty_clean) if qty_clean else 0
            
            if quantity <= 4:
                continue

            # 3. Extract and Clean Price
            raw_price = str(row[price_idx]).strip()
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            
            if price < 2.50:
                continue

            # 4. Total Stock Value Filter
            total_price = price * quantity
            if total_price < 100.0:
                continue

            # 5. Extract and Clean EAN (13-digit string)
            raw_ean = str(row[ean_idx]).strip()
            ean_digits = "".join(filter(str.isdigit, raw_ean))
            if not ean_digits:
                continue
            ean_final = ean_digits.zfill(13)

            # 6. Name construction
            producer = str(row[producer_idx]).strip() if producer_idx != -1 else ""
            prod_name = str(row[name_idx]).strip()
            # Avoid repeating producer if already in name
            full_name = f"{producer} {prod_name}" if producer.lower() not in prod_name.lower() else prod_name

            # Construct row
            processed_row = [
                ean_final,
                full_name.strip(),
                price,
                quantity,
                round(total_price, 2),
                "cennik"
            ]

            if has_moq:
                raw_moq = str(row[moq_idx]).strip()
                moq_clean = "".join(filter(str.isdigit, raw_moq))
                processed_row.append(int(moq_clean) if moq_clean else 1)

            final_rows.append(processed_row)

        except (ValueError, IndexError):
            continue

    return final_rows