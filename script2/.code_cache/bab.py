import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    header = rows[0]
    idx_map = {}
    
    # Identify indices
    for i, col in enumerate(header):
        c = str(col).lower()
        if 'ean' in c:
            idx_map['ean'] = i
        elif 'name' in c or 'description' in c:
            idx_map['name'] = i
        elif 'brand' in c or 'manufacturer' in c:
            idx_map['brand'] = i
        elif 'price' in c or 'euro' in c:
            idx_map['price'] = i
        elif 'stock' in c or 'qty' in c or 'free' in c:
            idx_map['qty'] = i

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    result = [final_header]

    refurb_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured']
    incoming_terms = ['incoming', 'delivery', 'estimated', 'expected', 'transit', 'soon']

    for row in rows[1:]:
        try:
            # 1. Quantity Cleaning
            raw_qty = row[idx_map.get('qty', 5)]
            qty_str = str(raw_qty).strip()
            qty_clean = re.sub(r'[^\d]', '', qty_str)
            qty = int(qty_clean) if qty_clean else 0
            if qty <= 4:
                continue

            # 2. Price Cleaning
            raw_price = row[idx_map.get('price', 6)]
            price_str = str(raw_price).replace(',', '.').strip()
            price_clean = re.sub(r'[^\d.]', '', price_str)
            price = float(price_clean) if price_clean else 0.0
            if price < 2.50:
                continue

            # 3. EAN Cleaning (Strict 13 digits)
            raw_ean = str(row[idx_map.get('ean', 3)]).strip()
            ean_clean = re.sub(r'\D', '', raw_ean)
            if not ean_clean:
                continue
            ean = ean_clean.zfill(13)

            # 4. Name Construction & Refurbished Filter
            brand = str(row[idx_map.get('brand', 1)]).strip() if 'brand' in idx_map else ""
            desc = str(row[idx_map.get('name', 4)]).strip()
            
            # Combine Brand and Name if brand not already in name
            if brand and brand.lower() not in desc.lower():
                full_name = f"{brand} {desc}"
            else:
                full_name = desc
                
            if any(term in full_name.lower() for term in refurb_terms):
                continue

            # 5. Availability/Incoming Filter
            is_incoming = False
            for cell in row:
                cell_str = str(cell).lower()
                if any(term in cell_str for term in incoming_terms):
                    is_incoming = True
                    break
            if is_incoming:
                continue

            # 6. Calculations & Value Filter
            total_price = price * qty
            if total_price < 100:
                continue

            result.append([
                ean,
                full_name,
                price,
                qty,
                round(total_price, 2),
                "bab"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return result