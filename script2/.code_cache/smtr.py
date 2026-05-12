import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
        if val is None: return ""
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else ""

    def clean_float(val):
        if val is None: return None
        try:
            # Handle currency symbols and European/Standard decimal formats
            s = str(val).replace('€', '').replace('$', '').strip()
            # If multiple dots/commas exist, assume last one is decimal
            s = s.replace(',', '.')
            return float(re.sub(r'[^\d.]', '', s))
        except:
            return None

    def clean_int(val):
        if val is None: return None
        try:
            s = re.sub(r'\D', '', str(val))
            return int(s) if s else None
        except:
            return None

    # Global MOQ extraction from unstructured header text
    moq_val = None
    for row in rows[:12]:
        for cell in row:
            if cell and isinstance(cell, str) and 'MOQ' in cell:
                match = re.search(r'MOQ\s+(?:of\s+)?(\d+)', cell)
                if match:
                    moq_val = int(match.group(1))

    # Identify Table Header Index and Column Mapping
    header_idx = -1
    col_map = {"Name": -1, "Price": -1, "EAN": -1, "Qty": -1}
    
    for i, row in enumerate(rows):
        row_str = [str(c).upper() if c else "" for c in row]
        if "MODELS" in row_str or "EAN" in row_str or "SELL PRICE" in row_str:
            header_idx = i
            for j, cell in enumerate(row_str):
                if "MODELS" in cell or "NAME" in cell: col_map["Name"] = j
                elif "PRICE" in cell: col_map["Price"] = j
                elif "EAN" in cell: col_map["EAN"] = j
                elif "STOCK" in cell or "READY" in cell or "QTY" in cell: col_map["Qty"] = j
            break

    # Final structure definition
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if moq_val is not None:
        final_header.append("Min Qty")
    
    output = [final_header]
    start_row = header_idx + 1 if header_idx != -1 else 0

    for row in rows[start_row:]:
        if len(row) < 3: continue
        
        # Data Extraction
        raw_name = str(row[col_map["Name"]]) if col_map["Name"] != -1 else ""
        raw_price = row[col_map["Price"]] if col_map["Price"] != -1 else None
        raw_ean = row[col_map["EAN"]] if col_map["EAN"] != -1 else None
        raw_qty = row[col_map["Qty"]] if col_map["Qty"] != -1 else None

        # 1. Clean and Validate Data
        ean = clean_ean(raw_ean)
        if len(ean) != 13: continue
        
        name = raw_name.strip()
        name_l = name.lower()
        if not name: continue
        
        price = clean_float(raw_price)
        qty = clean_int(raw_qty)
        
        if price is None or qty is None: continue
        
        # 2. Filters
        if qty <= 4: continue
        if price < 2.50: continue
        
        total_price = round(price * qty, 2)
        if total_price < 100: continue
        
        # Strict Availability check
        is_unavailable = False
        for cell in row:
            if isinstance(cell, str):
                cl = cell.lower()
                if any(x in cl for x in ["incoming", "delivery", "expect", "week", "sold out"]):
                    is_unavailable = True
                    break
        if is_unavailable: continue

        # Product Type Filters
        if any(x in name_l for x in ["refurbished", "renewed", "reconditioned", "remanufactured"]):
            continue
        if re.search(r'scooter', name_l):
            continue

        # 3. Build Result Row
        res_row = [ean, name, price, qty, total_price, "smtr"]
        if moq_val is not None:
            res_row.append(moq_val)
            
        output.append(res_row)

    return output