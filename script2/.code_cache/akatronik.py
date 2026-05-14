import re

def process_data(rows):
    if not rows:
        return []

    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_data = [final_header]
    
    # Identify indices
    # Based on sample: 0: Qty, 1: Brand, 2: Name, 4: EAN, 5: Price
    idx_qty = 0
    idx_brand = 1
    idx_name = 2
    idx_ean = 4
    idx_price = 5

    # Regex for big appliances (multilingual)
    appliances_pattern = re.compile(
        r"washing\s?machine|washmaschine|waschmaschine|wasmachine|lavadora|lavatrice|machine\s?a\s?laver|"
        r"maquina\s?de\s?lavar|dryer|secadora|dishwasher|lavavajillas|lave\s?vaisselle|refrigerator|"
        r"frigorifero|fridge|freezer|oven|tv|television|televisor|fernseher|air\s?conditioner|"
        r"climatiseur|klimaanlage", 
        re.IGNORECASE
    )
    
    excluded_brands = {
        "aeg", "beko", "bosch", "de'longhi", "electrolux", 
        "gorenje", "hisense", "lg", "samsung", "siemens"
    }

    refurbished_terms = ["refurbished", "renewed", "reconditioned", "remanufactured"]

    for i, row in enumerate(rows):
        # Skip header row if it contains keywords
        if i == 0 and any(isinstance(x, str) and 'barcode' in x.lower() for x in row):
            continue
            
        try:
            # 1. Extract Quantity
            raw_qty = str(row[idx_qty]) if row[idx_qty] is not None else "0"
            qty = int(float(re.sub(r'[^\d.]', '', raw_qty)))
            
            # 2. Extract Price
            raw_price = str(row[idx_price]) if row[idx_price] is not None else "0"
            price = float(re.sub(r'[^\d.]', '', raw_price.replace(',', '.')))
            
            # 3. Extract EAN
            raw_ean = str(row[idx_ean]) if row[idx_ean] is not None else ""
            ean = re.sub(r'\D', '', raw_ean).zfill(13)
            
            # 4. Extract and Build Name
            brand = str(row[idx_brand]).strip() if row[idx_brand] else ""
            model_name = str(row[idx_name]).strip() if row[idx_name] else ""
            full_name = f"{brand} {model_name}".strip()
            name_lower = full_name.lower()

            # --- Filtering Rules ---
            
            # Quantity Filter
            if qty <= 4:
                continue
                
            # Price Filter
            if price < 2.50:
                continue

            # AKATRONIK Brand Filter
            if any(eb in name_lower for eb in excluded_brands):
                continue
            
            # AKATRONIK Big Appliance Filter
            if appliances_pattern.search(name_lower):
                continue
            
            # Refurbished Filter
            if any(term in name_lower for term in refurbished_terms):
                continue
            
            # Scooter Filter
            if re.search(r'scooter', name_lower, re.IGNORECASE):
                continue

            # Calculation
            total_price = round(price * qty, 2)
            
            # Append valid row
            processed_data.append([
                ean,
                full_name,
                price,
                qty,
                total_price,
                "akatronik"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return processed_data