import re

def process_data(rows):
    final_data = []
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    has_moq = False
    temp_results = []

    # Regex patterns
    ean_pattern = re.compile(r'\b(\d{8,13})\b')
    price_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s?[€$£]')
    qty_pattern = re.compile(r'(\d+)\s?(?:pcs|qty|stock|@)', re.IGNORECASE)
    moq_pattern = re.compile(r'moq[:\s-]*(\d+)', re.IGNORECASE)
    
    # Exclusion keywords
    exclude_keywords = ['incoming', 'delivery', 'estimated', 'refurbished', 'renewed', 'reconditioned', 'remanufactured']

    for row in rows:
        # Join list into a single string for free-form parsing
        line = " ".join(str(cell) for cell in row if cell).strip()
        if not line:
            continue
            
        # Filter out metadata lines or non-ready stock lines
        line_lower = line.lower()
        if any(word in line_lower for word in exclude_keywords):
            continue
        
        # Extract EAN
        ean_match = ean_pattern.search(line)
        if not ean_match:
            continue
        ean_raw = ean_match.group(1)
        ean = ean_raw.zfill(13)
        
        # Extract Price
        price_match = price_pattern.search(line)
        if not price_match:
            # Fallback: look for @ 1175
            price_match = re.search(r'@\s*(\d+(?:[.,]\d+)?)', line)
            
        if not price_match:
            continue
            
        price_val = float(price_match.group(1).replace(',', '.'))
        if price_val < 2.50:
            continue

        # Extract Quantity
        qty_match = qty_pattern.search(line)
        if not qty_match:
            # Fallback: find number before "pcs" or after "stock"
            qty_match = re.search(r'(\d+)\s*pcs', line_lower)
            
        if not qty_match:
            continue
            
        qty_val = int(qty_match.group(1))
        if qty_val <= 4:
            continue

        # Total Value Check
        total_price = round(price_val * qty_val, 2)
        if total_price < 100:
            continue

        # Extract Name
        # Clean name by removing extracted bits (EAN, Price, Qty patterns)
        name_clean = line
        name_clean = re.sub(r'\b\d{8,13}\b', '', name_clean) # Remove EAN
        name_clean = re.sub(r'EAN:', '', name_clean, flags=re.I)
        name_clean = re.sub(r'P/N:\s*\S+', '', name_clean, flags=re.I)
        name_clean = re.sub(r'\d+\s*pcs', '', name_clean, flags=re.I)
        name_clean = re.sub(r'@\s*\d+.*', '', name_clean)
        name_clean = re.sub(r'\s+', ' ', name_clean).strip()
        
        # Extract MOQ
        moq_match = moq_pattern.search(line)
        moq_val = int(moq_match.group(1)) if moq_match else None
        if moq_val:
            has_moq = True

        temp_results.append({
            "EAN": ean,
            "Name": name_clean,
            "Price": price_val,
            "Quantity": qty_val,
            "Total": total_price,
            "Supplier": "smartcom",
            "MOQ": moq_val
        })

    # Construct final list
    if has_moq:
        header.append("Min Qty")
    
    output = [header]
    for item in temp_results:
        row_out = [
            item["EAN"],
            item["Name"],
            item["Price"],
            item["Quantity"],
            item["Total"],
            item["Supplier"]
        ]
        if has_moq:
            row_out.append(item["MOQ"])
        output.append(row_out)

    return output