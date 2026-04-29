import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # Helper to clean numeric values
    def clean_num(val):
        if val is None: return None
        s = str(val).strip()
        # Remove currency symbols and comma separators
        s = re.sub(r'[^\d.,-]', '', s)
        if not s: return None
        # Handle European decimal commas
        if ',' in s and '.' in s:
            s = s.replace(',', '')
        elif ',' in s:
            s = s.replace(',', '.')
        try:
            return float(s)
        except ValueError:
            return None

    # Identify column indices
    header = [str(c).upper().strip() for c in rows[0]]
    idx_map = {}
    
    # Try to find indices by header names
    for i, h in enumerate(header):
        if any(x in h for x in ['EAN', 'GTIN', 'BARCODE']): idx_map['ean'] = i
        elif any(x in h for x in ['MODEL', 'NAME', 'DESCRIPTION', 'PRODUCT']): idx_map['name'] = i
        elif any(x in h for x in ['PRICE', 'UNIT PRICE', 'COST']): idx_map['price'] = i
        elif any(x in h for x in ['QTY', 'AVAILABILITY', 'STOCK', 'QUANTITY', 'AMNT']): 
            # Differentiate between Stock count and Status text if possible
            val_sample = str(rows[1][i]).lower() if len(rows) > 1 else ""
            if any(char.isdigit() for char in val_sample):
                idx_map['qty'] = i
            else:
                idx_map['status'] = i

    # Fallback/Inference logic if headers failed
    if 'ean' not in idx_map or 'name' not in idx_map or 'price' not in idx_map:
        sample = rows[1] if len(rows) > 1 else rows[0]
        for i, val in enumerate(sample):
            s_val = str(val).strip()
            if re.match(r'^\d{10,15}$', s_val): idx_map['ean'] = i
            elif any(x in s_val.lower() for x in ['apple', 'samsung', 'iphone', 'gb']): idx_map['name'] = i
            elif '.' in s_val and clean_num(s_val) is not None: idx_map['price'] = i

    # Final Output Header
    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    final_data = [output_header]

    # Process Data Rows (skip header)
    for row in rows[1:]:
        try:
            # Extract basic fields
            raw_ean = str(row[idx_map.get('ean', 3)]).strip()
            ean = re.sub(r'\D', '', raw_ean).zfill(13)
            
            name = str(row[idx_map.get('name', 1)]).strip()
            
            price = clean_num(row[idx_map.get('price', 4)])
            qty = int(clean_num(row[idx_map.get('qty', 0)])) if idx_map.get('qty') is not None else 0
            
            # Check for Availability status text
            status_idx = idx_map.get('status')
            status_text = str(row[status_idx]).lower() if status_idx is not None else ""
            
            # Filtering Logic
            # 1. Refurbished filter
            forbidden = ['refurbished', 'renewed', 'reconditioned', 'remanufactured']
            if any(word in name.lower() for word in forbidden):
                continue
                
            # 2. Availability filter (only in stock)
            if "incoming" in status_text or "delivery" in status_text or "estimated" in status_text:
                continue
            if "out of stock" in status_text:
                continue
                
            # 3. Numeric constraints
            if qty <= 4:
                continue
            if price is None or price < 2.50:
                continue
                
            total_price = price * qty
            if total_price < 100:
                continue

            # Validated row construction
            final_data.append([
                ean,
                name,
                price,
                qty,
                round(total_price, 2),
                "ampq"
            ])
        except (ValueError, IndexError, TypeError):
            continue

    return final_data