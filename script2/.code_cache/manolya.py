import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    header = rows[0]
    idx_map = {}

    # Identify column indices based on header names or data patterns
    for i, col in enumerate(header):
        col_name = str(col).lower()
        if 'ean' in col_name:
            idx_map['ean'] = i
        elif any(x in col_name for x in ['brand', 'manufacturer']):
            idx_map['brand'] = i
        elif any(x in col_name for x in ['art', 'description', 'model', 'name']):
            if 'brand' in idx_map and idx_map.get('name') is None:
                idx_map['name'] = i
            elif 'brand' not in idx_map:
                idx_map['name'] = i
        elif any(x in col_name for x in ['price', 'exw', 'cost']):
            idx_map['price'] = i
        elif any(x in col_name for x in ['stock', 'qty', 'quantity', 'availability']):
            idx_map['qty'] = i

    # Refurbished filter regex
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    
    # Ready stock only filter keywords (to exclude incoming)
    incoming_keywords = ['incoming', 'delivery', 'estimated', 'expected', 'transit', 'soon']

    final_rows = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    for row in rows[1:]:
        try:
            # 1. Quantity Extraction
            raw_qty = row[idx_map.get('qty', 3)]
            qty_str = str(raw_qty).strip()
            # Basic cleaning for quantity
            qty_clean = re.sub(r'[^\d]', '', qty_str)
            qty = int(qty_clean) if qty_clean else 0
            
            # Filter: Quantity <= 4
            if qty <= 4:
                continue

            # 2. Price Extraction
            raw_price = row[idx_map.get('price', 4)]
            price_str = str(raw_price).strip().replace(',', '.')
            price_clean = re.sub(r'[^\d.]', '', price_str)
            price = float(price_clean) if price_clean else 0.0
            
            # Filter: Price < 2.50
            if price < 2.50:
                continue

            # 3. EAN Extraction
            raw_ean = str(row[idx_map.get('ean', 2)]).strip()
            ean_clean = re.sub(r'\D', '', raw_ean)
            ean = ean_clean.zfill(13)

            # 4. Name Extraction (Brand + Art/Description)
            brand = str(row[idx_map.get('brand', 0)]).strip() if 'brand' in idx_map else ""
            main_name = str(row[idx_map.get('name', 1)]).strip() if 'name' in idx_map else ""
            
            if brand and brand.lower() not in main_name.lower():
                full_name = f"{brand} {main_name}".strip()
            else:
                full_name = main_name
            
            # Filter: Refurbished
            if refurb_regex.search(full_name):
                continue
                
            # Filter: Incoming Stock (Check all columns for date-like or incoming text)
            is_incoming = False
            for cell in row:
                cell_str = str(cell).lower()
                if any(k in cell_str for k in incoming_keywords):
                    # Check if it actually contains a date or is just a status
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # 5. Calculations
            total_price = price * qty
            
            # Filter: Total stock value < 100 EUR
            if total_price < 100:
                continue

            # Construct Final Row
            final_rows.append([
                ean,
                full_name,
                price,
                qty,
                round(total_price, 2),
                "manolya"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return final_rows