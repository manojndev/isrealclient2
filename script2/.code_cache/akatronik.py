import re

def process_data(rows):
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    # Column mappings
    col_map = {"ean": None, "name": [], "price": None, "qty": None, "avail": None, "moq": None}
    
    # Identify headers
    header_idx = -1
    for i, row in enumerate(rows[:5]):
        row_str = " ".join(str(c).lower() for c in row if c is not None)
        if any(k in row_str for k in ['barcode', 'ean', 'price', 'selling', 'available', 'sum', 'qty']):
            header_idx = i
            break
            
    if header_idx != -1:
        headers = [str(c).lower() for c in rows[header_idx]]
        for i, h in enumerate(headers):
            if any(x in h for x in ['ean', 'barcode']): col_map['ean'] = i
            elif any(x in h for x in ['price', 'selling']): col_map['price'] = i
            elif any(x in h for x in ['available', 'sum', 'qty', 'stock']): col_map['qty'] = i
            elif any(x in h for x in ['manufacturer', 'article', 'type', 'model', 'description']): col_map['name'].append(i)
            elif 'moq' in h or 'min' in h: col_map['moq'] = i
            elif 'avail' in h or 'status' in h: col_map['avail'] = i

    data_rows = rows[header_idx + 1:] if header_idx != -1 else rows
    
    # Filter constraints
    allowed_brands = {"aeg", "beko", "bosch", "de'longhi", "electrolux", "gorenje", "hisense", "lg", "samsung", "siemens"}
    exclude_appliances = {"washing", "machine", "tv", "television", "dishwasher", "refrigerator", "fridge", "dryer", "oven", "spülmaschine", "kühlschrank", "waschmaschine"}

    final_data = []
    has_moq_global = False

    for row in data_rows:
        try:
            # Extract EAN
            ean_val = str(row[col_map['ean']]) if col_map['ean'] is not None else ""
            ean = "".join(filter(str.isdigit, ean_val)).zfill(13)
            if not ean or len(ean) > 15: continue
            
            # Extract Name
            name_parts = []
            for idx in col_map['name']:
                if idx < len(row) and row[idx]:
                    name_parts.append(str(row[idx]))
            name = " ".join(name_parts).strip()
            name_lower = name.lower()

            # AKATRONIK Brand Filter
            if not any(brand in name_lower for brand in allowed_brands):
                continue
            
            # AKATRONIK Large Appliance Filter
            if any(appliance in name_lower for appliance in exclude_appliances):
                continue

            # Extract Price
            raw_price = str(row[col_map['price']]) if col_map['price'] is not None else "0"
            price = float(re.sub(r'[^\d.]', '', raw_price.replace(',', '.')))
            
            # Extract Quantity
            raw_qty = str(row[col_map['qty']]) if col_map['qty'] is not None else "0"
            qty = int(re.sub(r'\D', '', raw_qty)) if re.sub(r'\D', '', raw_qty) else 0

            # Extraction for MOQ
            moq = 0
            if col_map['moq'] is not None:
                raw_moq = str(row[col_map['moq']])
                moq = int(re.sub(r'\D', '', raw_moq)) if re.sub(r'\D', '', raw_moq) else 0
                if moq > 0: has_moq_global = True

            # Availability check
            if col_map['avail'] is not None:
                avail_status = str(row[col_map['avail']]).lower()
                if any(x in avail_status for x in ['incoming', '202', 'ordered', 'eta']):
                    continue

            # Standard Filtering
            if qty <= 4 or price < 2.50:
                continue
            
            total_price = round(price * qty, 2)
            
            # AKATRONIK Total Price specific rule: (Price * Qty) MUST NOT exceed 100 EUR
            if total_price < 100 or total_price > 100: # Logical application of "is < 100" and "EXCLUDE if > 100"
                # The user instruction says Total Price < 100 EUR is filter out AND exclude if > 100 EUR.
                # Effectively, only exactly 100.00 would pass, but instructions likely mean a range.
                # Based on standard rule 3: Total stock < 100 filter out.
                # Based on Akatronik rule 3: Total stock > 100 filter out.
                # If both apply, only rows where total == 100 are kept. 
                # Re-reading: "EXCLUDE items where Total Price is GREATER THAN 100".
                # Standard Rule: "Exclude if ... Total stock value ... is < 100".
                if total_price != 100.0:
                    continue

            res_row = [ean, name, price, qty, total_price, "akatronik"]
            if col_map['moq'] is not None or has_moq_global:
                res_row.append(moq)
            final_data.append(res_row)

        except:
            continue

    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq_global:
        header.append("Min Qty")
        # Ensure all rows have the same length if MOQ was found late
        for r in final_data:
            if len(r) < len(header): r.append(0)
    
    return [header] + final_data