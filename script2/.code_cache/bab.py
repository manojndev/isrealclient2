import re

def process_data(rows):
    if not rows:
        return []

    # Target headers and index variables
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    ean_idx = -1
    name_idx = -1
    price_idx = -1
    qty_idx = -1
    
    # Identify indices from the first potential header row
    for row in rows[:5]:
        row_str = [str(cell).lower() if cell is not None else "" for cell in row]
        if 'ean' in row_str or 'qty' in row_str or 'price' in row_str:
            for i, cell in enumerate(row_str):
                if 'ean' in cell: ean_idx = i
                elif 'name' in cell: name_idx = i
                elif 'price' in cell: price_idx = i
                elif 'qty' in cell or 'quantity' in cell: qty_idx = i
            if ean_idx != -1:
                break

    # Final data list
    processed_data = [final_header]
    
    for row in rows:
        # Skip header repetitions or empty rows
        row_str_check = [str(cell).lower() if cell is not None else "" for cell in row]
        if 'ean' in row_str_check or 'name' in row_str_check:
            continue
            
        try:
            # 1. Extraction
            raw_ean = str(row[ean_idx]) if ean_idx != -1 else ""
            raw_name = str(row[name_idx]) if name_idx != -1 else ""
            raw_price = str(row[price_idx]) if price_idx != -1 else "0"
            raw_qty = str(row[qty_idx]) if qty_idx != -1 else "0"
            
            # 2. Cleaning EAN: strictly 13-digit string, left-padded
            ean_digits = "".join(filter(str.isdigit, raw_ean))
            if not ean_digits:
                continue
            ean_clean = ean_digits.zfill(13)
            
            # 3. Cleaning Price: float
            price_str = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_str) if price_str else 0.0
            
            # 4. Cleaning Quantity: integer
            qty_digits = "".join(filter(str.isdigit, str(raw_qty).split('.')[0]))
            quantity = int(qty_digits) if qty_digits else 0
            
            # 5. Filtering Rules
            if quantity <= 4:
                continue
            if price < 2.50:
                continue
            
            total_price = price * quantity
            if total_price < 100.0:
                continue
            
            # Availability check (Strict)
            # Ensure no "incoming" or dates in cells that might indicate future stock
            is_incoming = False
            for cell in row:
                cell_s = str(cell).lower()
                if any(x in cell_s for x in ["incoming", "delivery", "expected", "eta"]):
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # 6. Formatting row
            processed_data.append([
                ean_clean,
                raw_name.strip(),
                price,
                quantity,
                round(total_price, 2),
                "bab"
            ])
            
        except (ValueError, IndexError):
            continue

    return processed_data