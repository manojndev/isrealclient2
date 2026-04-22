import re

def process_data(rows):
    if not rows:
        return []

    # 1. Identify Headers and Column Indices
    # Expected columns: EAN, Name, Price, Quantity
    header_indices = {
        'ean': -1,
        'name': -1,
        'price': -1,
        'quantity': -1
    }

    # Analyze first row for headers
    first_row = [str(cell).strip().lower() for cell in rows[0]]
    
    for i, cell in enumerate(first_row):
        if 'ean' in cell:
            header_indices['ean'] = i
        elif 'desc' in cell or 'name' in cell:
            header_indices['name'] = i
        elif 'sales cost' in cell or 'price' in cell or 'cost' in cell:
            header_indices['price'] = i
        elif 'qav' in cell or 'qty' in cell or 'stock' in cell or 'quantity' in cell:
            header_indices['quantity'] = i

    # Fallback for missing headers using sample data patterns
    data_start_idx = 1
    if header_indices['ean'] == -1:
        # Check first data row to infer
        sample = rows[1] if len(rows) > 1 else rows[0]
        for i, val in enumerate(sample):
            val_str = str(val)
            if re.fullmatch(r'\d{10,13}', val_str):
                header_indices['ean'] = i
            elif isinstance(val, (int, float)) and val > 1000: # heuristic for EAN as number
                header_indices['ean'] = i
    
    # Final Output Header
    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = [output_header]

    # 2. Process Data Rows
    for row in rows[data_start_idx:]:
        try:
            # Extract EAN
            raw_ean = str(row[header_indices['ean']]) if header_indices['ean'] != -1 else ""
            clean_ean = re.sub(r'\D', '', raw_ean)
            if not clean_ean:
                continue
            clean_ean = clean_ean.zfill(13)

            # Extract Name
            name = str(row[header_indices['name']]) if header_indices['name'] != -1 else ""

            # Extract Price
            raw_price = str(row[header_indices['price']]) if header_indices['price'] != -1 else "0"
            clean_price_str = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            try:
                price = float(clean_price_str)
            except ValueError:
                continue

            # Extract Quantity
            raw_qty = str(row[header_indices['quantity']]) if header_indices['quantity'] != -1 else "0"
            clean_qty_str = re.sub(r'[^\d]', '', raw_qty)
            try:
                quantity = int(clean_qty_str)
            except ValueError:
                continue

            # 3. Filtering Rules
            # Rule: Quantity > 4
            if quantity <= 4:
                continue
            
            # Rule: Price < 2.50
            if price < 2.50:
                continue

            # Rule: Total stock value < 100
            total_price = price * quantity
            if total_price < 100:
                continue

            # Rule: Availability check (filter out incoming/dates)
            # Check all cells for keywords indicating non-ready stock
            is_invalid_stock = False
            for cell in row:
                cell_str = str(cell).lower()
                if any(k in cell_str for k in ["incoming", "delivery", "estimated", "expected", "backorder"]):
                    is_invalid_stock = True
                    break
            if is_invalid_stock:
                continue

            # 4. Construct Row
            new_row = [
                clean_ean,          # EAN (String)
                name,               # Name
                round(price, 2),    # Price (Float)
                quantity,           # Stock/Quantity (Int)
                round(total_price, 2), # Total Price (Float)
                "eurotronics"       # Supplier
            ]
            processed_rows.append(new_row)

        except (IndexError, ValueError):
            continue

    return processed_rows