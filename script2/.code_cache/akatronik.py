import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else None

    def clean_float(val):
        if val is None: return None
        try:
            s = str(val).replace('€', '').replace('$', '').strip()
            return float(s)
        except:
            return None

    def clean_int(val):
        if val is None: return None
        try:
            s = re.sub(r'[^\d]', '', str(val))
            return int(s) if s else None
        except:
            return None

    # Identify columns dynamically
    header = rows[0]
    sample_data = rows[1:6] if len(rows) > 1 else []
    
    col_map = {"stock": -1, "brand": -1, "name1": -1, "name2": -1, "ean": -1, "price": -1}
    
    # Try mapping by header names first
    for i, h in enumerate(header):
        h_lower = str(h).lower()
        if 'sum available' in h_lower: col_map["stock"] = i
        elif 'manufacturer' in h_lower: col_map["brand"] = i
        elif 'article type' in h_lower: col_map["name1"] = i
        elif 'type2' in h_lower: col_map["name2"] = i
        elif 'barcode' in h_lower or 'ean' in h_lower: col_map["ean"] = i
        elif 'price' in h_lower: col_map["price"] = i

    # Fallback/Validation with data patterns
    for row in sample_data:
        for i, val in enumerate(row):
            if col_map["ean"] == -1 and len(re.sub(r'\D', '', str(val))) >= 12: col_map["ean"] = i
            if col_map["price"] == -1 and isinstance(val, (float, int)) and i != col_map["stock"]: col_map["price"] = i

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed = [final_header]

    # Filters
    excluded_brands = {'aeg', 'beko', 'bosch', 'de\'longhi', 'delonghi', 'electrolux', 'gorenje', 'hisense', 'lg', 'samsung', 'siemens'}
    appliances_pattern = re.compile(
        r'washing\s?machine|washmachine|waschmaschine|wasmachine|lavadora|lavatrice|machine\s?a\s?laver|maquina\s?de\s?lavar|'
        r'dryer|secadora|dishwasher|lavavajillas|lave\s?vaisselle|refrigerator|frigorifero|fridge|freezer|'
        r'oven|tv\b|television|televisor|fernseher|air\s?conditioner|climatiseur|klimaanlage', 
        re.IGNORECASE
    )
    refurb_pattern = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)

    for row in rows[1:]:
        # Extract base values
        qty = clean_int(row[col_map["stock"]]) if col_map["stock"] != -1 else None
        price = clean_float(row[col_map["price"]]) if col_map["price"] != -1 else None
        ean = clean_ean(row[col_map["ean"]]) if col_map["ean"] != -1 else ""
        brand = str(row[col_map["brand"]]).strip() if col_map["brand"] != -1 else ""
        n1 = str(row[col_map["name1"]]).strip() if col_map["name1"] != -1 else ""
        n2 = str(row[col_map["name2"]]).strip() if (col_map["name2"] != -1 and row[col_map["name2"]] is not None) else ""
        
        full_name = f"{brand} {n1} {n2}".strip().replace('\xa0', ' ')
        full_name = ' '.join(full_name.split()) # Clean whitespaces

        # Validations
        if qty is None or qty <= 4: continue
        if price is None or price < 2.50: continue
        
        # Refurbished Filter
        if refurb_pattern.search(full_name): continue
        
        # Akatronik Specific Brand Filter
        if any(b in full_name.lower() for b in excluded_brands): continue
        
        # Akatronik Specific Appliance Filter
        if appliances_pattern.search(full_name): continue

        total_price = round(price * qty, 2)
        
        # Add row
        processed.append([
            ean,
            full_name,
            price,
            qty,
            total_price,
            "akatronik"
        ])

    return processed