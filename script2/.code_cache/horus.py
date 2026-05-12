import re

def process_data(rows):
    if not rows:
        return []

    # Target headers
    final_headers = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [final_headers]

    # Column Mapping (Inferred from Sample)
    # Row 0: ['EAN', 'Product Description', 'Qty Available', 'EUR Price', ...]
    idx_ean = 0
    idx_name = 1
    idx_qty = 2
    idx_price = 3

    # Regex patterns
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_regex = re.compile(r'scooter', re.IGNORECASE)
    incoming_regex = re.compile(r'incoming|expected|delivery|date|\d{2}\.\d{2}', re.IGNORECASE)

    # Process data rows
    for row in rows[1:]:
        if not row or len(row) < 4:
            continue

        try:
            # 1. Clean and Validate Name
            name = str(row[idx_name] or "").strip()
            if not name:
                continue
            
            # Filter Refurbished and Scooters
            if refurb_regex.search(name) or scooter_regex.search(name):
                continue

            # 2. Availability Filter
            # Check all cells in the row for "incoming" patterns to ensure only ready stock
            is_incoming = False
            for cell in row:
                if cell and incoming_regex.search(str(cell)):
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # 3. Clean Price
            raw_price = str(row[idx_price] or "0")
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            if price < 2.50:
                continue

            # 4. Clean Quantity
            raw_qty = str(row[idx_qty] or "0")
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            quantity = int(qty_clean) if qty_clean else 0
            if quantity <= 4:
                continue

            # 5. Total Stock Value Filter
            total_price = round(price * quantity, 2)
            if total_price < 100:
                continue

            # 6. Clean EAN
            raw_ean = str(row[idx_ean] or "")
            ean_digits = re.sub(r'[^\d]', '', raw_ean)
            if not ean_digits:
                continue
            ean = ean_digits.zfill(13)

            # Build row
            # ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
            output.append([
                ean,
                name,
                price,
                quantity,
                total_price,
                "horus"
            ])

        except (ValueError, IndexError):
            continue

    return output