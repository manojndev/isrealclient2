import re

def process_data(rows):
    """
    Expert Python data processing assistant.
    Parses unstructured list-of-lists (likely from a TXT/Email source) into structured data.
    """
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    output = [final_header]
    
    # Flatten the rows into a list of strings for easier context-aware parsing
    flat_lines = []
    for row in rows:
        line = " ".join([str(item) for item in row if item is not None])
        if line.strip():
            flat_lines.append(line.strip())

    # Regular Expressions
    ean_pattern = re.compile(r'\b\d{10,13}\b')
    price_pattern = re.compile(r'(\d+(?:[.,]\d{1,2})?)\s*[€$]')
    qty_pattern = re.compile(r'(\d+)\s*(?:pcs|units|qty|x|stk)', re.IGNORECASE)
    exclusion_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured|scooter', re.IGNORECASE)
    incoming_pattern = re.compile(r'incoming|expected|delivery|eta|\d{2}\.\d{2}', re.IGNORECASE)

    current_product = {"ean": None, "name": [], "price": None, "qty": None}
    
    products = []

    for line in flat_lines:
        # Check for incoming stock/logistics - skip these blocks or invalidate current
        if incoming_pattern.search(line):
            continue

        # Extract EAN
        found_ean = ean_pattern.search(line)
        # Extract Price
        found_price = price_pattern.search(line)
        # Extract Quantity
        found_qty = qty_pattern.search(line)
        
        # Heuristic: If we find a new EAN and we already have some info, the previous product is likely finished
        if found_ean and (current_product["ean"] or current_product["price"]):
            products.append(current_product)
            current_product = {"ean": None, "name": [], "price": None, "qty": None}

        if found_ean:
            current_product["ean"] = found_ean.group().zfill(13)
        
        if found_price:
            p_str = found_price.group(1).replace(',', '.')
            try:
                current_product["price"] = float(p_str)
            except ValueError:
                pass
        
        if found_qty:
            try:
                current_product["qty"] = int(found_qty.group(1))
            except ValueError:
                pass
        elif not found_price and not found_ean:
            # If line is just a number without symbols, it might be Qty or Price based on context
            parts = line.split()
            for part in parts:
                if part.isdigit() and len(part) < 6:
                    val = int(part)
                    if current_product["qty"] is None:
                        current_product["qty"] = val
                elif re.match(r'^\d+[.,]\d{2}$', part):
                    if current_product["price"] is None:
                        try:
                            current_product["price"] = float(part.replace(',', '.'))
                        except: pass

        # Name extraction: capture lines that aren't purely numeric or logistical
        if not found_ean and not found_price and not incoming_pattern.search(line):
            # Clean non-product text from name
            clean_line = re.sub(r'\d+pcs|qty|units', '', line, flags=re.I).strip()
            if clean_line:
                current_product["name"].append(clean_line)

    # Append last
    if current_product["ean"] or current_product["price"]:
        products.append(current_product)

    # Validation and Filtering
    for p in products:
        name = " ".join(p["name"]).strip()
        ean = p["ean"] if p["ean"] else ""
        price = p["price"] if p["price"] is not None else 0.0
        qty = p["qty"] if p["qty"] is not None else 0
        
        # Missing data inference (if qty or price was in a list-style row 2)
        if qty == 0 or price == 0.0:
            continue
            
        # Filters
        if qty <= 4:
            continue
        if price < 2.50:
            continue
        
        total_price = round(price * qty, 2)
        if total_price < 100.0:
            continue
            
        if exclusion_pattern.search(name):
            continue
            
        # Name cleanup (remove EAN if it ended up in the name)
        name = name.replace(ean, "").strip() if ean else name
        
        output.append([
            ean,
            name,
            price,
            qty,
            total_price,
            "bab"
        ])

    return output