import re

def process_data(rows):
    header_row = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    result = [header_row]
    
    col_map = {}
    start_row_idx = 0
    
    # Identify the actual header row and map columns
    for i, row in enumerate(rows):
        row_str = [str(c).lower() if c is not None else "" for c in row]
        if 'ean' in row_str or ('item' in row_str and 'price' in " ".join(row_str)):
            for idx, val in enumerate(row_str):
                if 'ean' in val: col_map['ean'] = idx
                elif 'item' in val: col_map['name'] = idx
                elif 'price' in val: col_map['price'] = idx
                elif 'qty' in val or 'quantity' in val: col_map['qty'] = idx
                elif 'stock' in val: col_map['stock_status'] = idx
                elif 'manufacturer' in val: col_map['brand'] = idx
            start_row_idx = i + 1
            break

    # Regex patterns
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_regex = re.compile(r'scooter', re.IGNORECASE)
    appliance_regex = re.compile(r'washing machine|dryer|dishwasher|refrigerator|freezer|oven|hob|cooker|stove', re.IGNORECASE)
    num_only = re.compile(r'[^\d.]')

    for i in range(start_row_idx, len(rows)):
        row = rows[i]
        if not row or len(row) < 3:
            continue
            
        try:
            # 1. Name & Brand
            brand = str(row[col_map['brand']]) if 'brand' in col_map and row[col_map['brand']] else ""
            item_name = str(row[col_map['name']]) if 'name' in col_map and row[col_map['name']] else ""
            full_name = f"{brand} {item_name}".strip()
            
            if not item_name:
                continue

            # 2. Filters: Refurbished, Scooter, Appliances
            if refurb_regex.search(full_name) or scooter_regex.search(full_name) or appliance_regex.search(full_name):
                continue

            # 3. Stock Status Filter
            if 'stock_status' in col_map:
                status = str(row[col_map['stock_status']]).lower()
                # Only keep "ready" or empty (assuming available), exclude dates or incoming
                if any(kw in status for kw in ['incoming', 'delivery', '.', '202']):
                    continue
                if 'ready' not in status and status != "" and 'stock' not in status:
                    continue

            # 4. Quantity
            qty_val = row[col_map['qty']] if 'qty' in col_map else 0
            qty_str = "".join(filter(str.isdigit, str(qty_val)))
            quantity = int(qty_str) if qty_str else 0
            if quantity <= 4:
                continue

            # 5. Price
            price_val = row[col_map['price']] if 'price' in col_map else 0
            price_str = num_only.sub('', str(price_val).replace(',', '.'))
            price = float(price_str) if price_str else 0.0
            if price < 2.50:
                continue

            # 6. Total Stock Value
            total_price = price * quantity
            if total_price < 100:
                continue

            # 7. EAN
            ean_val = str(row[col_map['ean']]) if 'ean' in col_map else ""
            ean_clean = "".join(filter(str.isdigit, ean_val))
            if not ean_clean:
                continue
            ean = ean_clean.zfill(13)

            # Construct Row
            result.append([
                ean,
                full_name,
                float(price),
                int(quantity),
                float(round(total_price, 2)),
                "duna"
            ])

        except (ValueError, KeyError, IndexError):
            continue

    return result