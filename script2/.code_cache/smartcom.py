import re

def process_data(rows):
    """
    Parses unstructured product data from a list of lists, extracting EAN, Name, 
    Price, and Stock into a standardized format.
    """
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = []
    has_moq = False
    temp_results = []

    # Regex patterns for unstructured text extraction
    ean_pattern = re.compile(r'\b\d{8,13}\b')
    price_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s?[€$£]')
    qty_pattern = re.compile(r'(\d+)\s?(?:pcs|qty|stock|@)', re.IGNORECASE)
    moq_pattern = re.compile(r'moq[:\s-]*(\d+)', re.IGNORECASE)
    
    # Flatten rows if they come in as single-element lists containing long strings
    flat_lines = []
    for r in rows:
        if not r: continue
        line = " ".join(str(cell) for cell in r if cell is not None)
        # Split line if it contains multiple EANs (multiple products on one line)
        parts = re.split(r'(?=\b\d{12,13}\b)', line)
        for p in parts:
            if p.strip():
                flat_lines.append(p.strip())

    for line in flat_lines:
        # Filter out non-product lines
        low_line = line.lower()
        exclude_keywords = ['incoming', 'delivery', 'eta', 'expected', 'estimated', 'payment', 'logistics']
        if any(word in low_line for word in exclude_keywords):
            continue
            
        # Extract EAN
        ean_match = ean_pattern.search(line)
        if not ean_match:
            continue
        ean = ean_match.group(0).zfill(13)
        
        # Extract Price
        # Look for pattern like "1175€" or "@ 1175"
        price = 0.0
        p_match = price_pattern.search(line)
        if p_match:
            price = float(p_match.group(1).replace(',', '.'))
        else:
            # Fallback: look for digits after '@'
            at_match = re.search(r'@\s*(\d+(?:[.,]\d+)?)', line)
            if at_match:
                price = float(at_match.group(1).replace(',', '.'))

        # Extract Quantity
        quantity = 0
        q_match = qty_pattern.search(line)
        if q_match:
            quantity = int(q_match.group(1))
        else:
            # Fallback: find integers near "pcs" or stand-alone integers that aren't the price/EAN
            nums = re.findall(r'\b(\d+)\b', line.replace(ean, ''))
            for n in nums:
                val = int(n)
                if 1 < val < 10000 and val != int(price): # Heuristic
                    quantity = val
                    break

        # Extract MOQ
        moq = None
        m_match = moq_pattern.search(line)
        if m_match:
            moq = int(m_match.group(1))
            has_moq = True

        # Extract Name
        # Remove known identifiers to isolate the product name
        name = line
        name = re.sub(ean_pattern, '', name)
        name = re.sub(r'(\d+(?:[.,]\d+)?)\s?[€$£]', '', name)
        name = re.sub(r'\d+\s?(?:pcs|qty|stock|@)', '', name, flags=re.IGNORECASE)
        name = re.sub(r'P/N:\s*\S+', '', name)
        name = re.sub(r'EAN:\s*', '', name)
        name = re.sub(r'\s+', ' ', name).strip()
        
        # Business Logic Filtering
        if quantity <= 4:
            continue
        if price < 2.50:
            continue
        total_price = round(price * quantity, 2)
        if total_price < 100:
            continue

        item = [ean, name, price, quantity, total_price, "smartcom"]
        if moq is not None:
            item.append(moq)
        else:
            item.append(0) # Placeholder for MOQ
        
        temp_results.append(item)

    # Finalize Header
    if has_moq:
        final_header.append("Min Qty")
    
    output = [final_header]
    for item in temp_results:
        if has_moq:
            output.append(item)
        else:
            output.append(item[:6]) # Strip the MOQ placeholder if no MOQ found in whole set

    return output