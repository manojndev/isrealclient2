import re

def process_data(rows):
    if not rows:
        return []

    # 1. Identify MOQ from header text (Rows 0-10)
    moq_value = None
    for row in rows[:11]:
        text = " ".join([str(cell) for cell in row if cell])
        moq_match = re.search(r'MOQ\s*(?:of)?\s*(\d+)', text, re.IGNORECASE)
        if moq_match:
            moq_value = int(moq_match.group(1))
            break

    # 2. Find Header Row and Map Columns
    header_idx = -1
    col_map = {}
    
    for i, row in enumerate(rows):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if 'ean' in row_str or 'sell price' in row_str or 'models' in row_str:
            header_idx = i
            for j, val in enumerate(row_str):
                if 'ean' in val: col_map['ean'] = j
                elif 'model' in val or 'name' in val: col_map['name'] = j
                elif 'price' in val: col_map['price'] = j
                elif 'ready stock' in val: col_map['stock'] = j
            break
            
    if header_idx == -1:
        return []

    # 3. Process Data Rows
    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if moq_value is not None:
        output_header.append("Min Qty")
    
    processed_rows = [output_header]
    
    for row in rows[header_idx + 1:]:
        # Skip empty rows or rows that don't have enough columns
        if not row or len(row) <= max(col_map.values(), default=0):
            continue
            
        try:
            # Extract Raw Values
            raw_ean = str(row[col_map['ean']]) if 'ean' in col_map else ""
            raw_name = str(row[col_map['name']]) if 'name' in col_map else ""
            raw_price = str(row[col_map['price']]) if 'price' in col_map else ""
            raw_stock = row[col_map['stock']] if 'stock' in col_map else 0

            # Data Cleaning - EAN
            ean_clean = re.sub(r'\D', '', raw_ean)
            if ean_clean:
                ean_clean = ean_clean.zfill(13)
            else:
                continue

            # Data Cleaning - Price
            price_clean = str(raw_price).replace(',', '.')
            price_match = re.search(r'(\d+\.?\d*)', price_clean)
            if not price_match:
                continue
            price_val = float(price_match.group(1))

            # Data Cleaning - Quantity
            if isinstance(raw_stock, (int, float)):
                stock_val = int(raw_stock)
            else:
                stock_match = re.search(r'(\d+)', str(raw_stock))
                stock_val = int(stock_match.group(1)) if stock_match else 0

            # Filtering Rules
            if stock_val <= 4:
                continue
            if price_val < 2.50:
                continue
            
            total_price = round(price_val * stock_val, 2)
            if total_price < 100:
                continue

            # Final Row Assembly
            final_row = [
                ean_clean,
                raw_name.strip(),
                price_val,
                stock_val,
                total_price,
                "smtr"
            ]
            if moq_value is not None:
                final_row.append(moq_value)
                
            processed_rows.append(final_row)
            
        except (ValueError, TypeError, IndexError):
            continue

    return processed_rows