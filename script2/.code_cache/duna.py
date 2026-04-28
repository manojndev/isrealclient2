import re

def process_data(rows: list[list]) -> list[list]:
    if not rows:
        return []

    # Find the header row by looking for key columns
    header_idx = -1
    col_map = {}
    
    for i, row in enumerate(rows):
        if not row:
            continue
        row_lower = [str(c).lower().strip() if c is not None else "" for c in row]
        if any("ean" in c for c in row_lower) and any("price" in c for c in row_lower):
            header_idx = i
            for j, cell in enumerate(row_lower):
                if "ean" in cell:
                    col_map['ean'] = j
                elif "price" in cell:
                    col_map['price'] = j
                elif "qty" in cell or "quantity" in cell:
                    col_map['qty'] = j
                elif "manufacturer" in cell or "brand" in cell:
                    col_map['brand'] = j
                elif "item" in cell or "description" in cell or "name" in cell:
                    col_map['name'] = j
                elif "stock" in cell or "availability" in cell:
                    col_map['stock'] = j
            break

    if header_idx == -1 or 'ean' not in col_map or 'price' not in col_map:
        return []

    final_rows = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]
    
    appliance_keywords = [
        'washing machine', 'dryer', 'dishwasher', 'refrigerator', 
        'freezer', 'oven', 'hob', 'cooker', 'stove'
    ]
    incoming_keywords = ['incoming', 'delivery', 'estimated', 'expected']

    for row in rows[header_idx + 1:]:
        if not row or all(c is None for c in row):
            continue

        def get_val(key):
            idx = col_map.get(key, -1)
            if 0 <= idx < len(row) and row[idx] is not None:
                return str(row[idx]).strip()
            return ""

        ean_raw = get_val('ean')
        price_raw = get_val('price')
        qty_raw = get_val('qty')
        brand_raw = get_val('brand')
        name_raw = get_val('name')
        stock_raw = get_val('stock')

        # Clean EAN
        ean = re.sub(r'\D', '', ean_raw)
        if not ean:
            continue
        ean = ean.zfill(13)

        # Clean Name
        name_parts = []
        if brand_raw:
            name_parts.append(brand_raw)
        if name_raw:
            name_parts.append(name_raw)
        name = " ".join(name_parts).strip()
        if not name:
            continue

        # Strict Duna Filter: Exclude large appliances
        name_lower = name.lower()
        if any(kw in name_lower for kw in appliance_keywords):
            continue

        # Clean Price
        price_match = re.search(r'[\d\.]+', price_raw.replace(',', '.'))
        if not price_match:
            continue
        try:
            price = float(price_match.group(0))
        except ValueError:
            continue

        # Clean Quantity
        qty_match = re.search(r'\d+', qty_raw)
        if not qty_match:
            continue
        try:
            qty = int(qty_match.group(0))
        except ValueError:
            continue

        # Stock / Availability check
        row_str = " ".join([str(c).lower() for c in row if c is not None])
        if any(kw in row_str for kw in incoming_keywords):
            continue
        
        # If there's a specific stock column, ensure it signifies available stock
        # and explicitly exclude dates indicating incoming stock (e.g. 23.03)
        if 'stock' in col_map and stock_raw:
            stock_lower = stock_raw.lower()
            if re.search(r'\d{1,2}[\./-]\d{1,2}', stock_lower):
                continue
            if not any(kw in stock_lower for kw in ['ready', 'available', 'in stock', 'ok', 'yes', 'on stock']):
                # Strict enforcement to only keep ready/available items if stock column is populated
                continue

        # Filtering conditions
        if qty <= 4:
            continue
        if price < 2.50:
            continue
        
        total_price = round(price * qty, 2)
        if total_price < 100:
            continue

        final_rows.append([ean, name, price, qty, total_price, "duna"])

    return final_rows