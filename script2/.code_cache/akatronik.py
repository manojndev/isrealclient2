import re

def process_data(rows):
    if not rows:
        return []

    def clean_ean(val):
        s = re.sub(r'\D', '', str(val))
        return s.zfill(13) if s else ""

    def clean_price(val):
        if val is None: return 0.0
        s = str(val).replace('€', '').replace('$', '').replace(',', '.').strip()
        try:
            return float(re.sub(r'[^\d.]', '', s))
        except:
            return 0.0

    def clean_qty(val):
        if val is None: return 0
        s = re.sub(r'\D', '', str(val))
        try:
            return int(s)
        except:
            return 0

    # Column Mapping
    ean_idx = name_idx = price_idx = qty_idx = brand_idx = moq_idx = -1
    
    header_row = rows[0]
    header_str = [str(c).lower() for c in header_row]
    
    for i, col in enumerate(header_str):
        if any(x in col for x in ['barcode', 'ean', 'gtin']): ean_idx = i
        elif any(x in col for x in ['article type', 'description', 'name']): name_idx = i
        elif any(x in col for x in ['price', 'selling']): price_idx = i
        elif any(x in col for x in ['available', 'qty', 'stock', 'sum']): qty_idx = i
        elif any(x in col for x in ['manufacturer', 'brand']): brand_idx = i
        elif 'moq' in col or 'min' in col: moq_idx = i

    # Akatronik specific rules
    allowed_brands = {'AEG', 'BEKO', 'BOSCH', "DE'LONGHI", 'ELECTROLUX', 'GORENJE', 'HISENSE', 'LG', 'SAMSUNG', 'SIEMENS'}
    
    big_appliances = [
        'washing machine', 'washmachine', 'waschmaschine', 'wasmachine', 'lavadora', 'lavatrice', 
        'machine a laver', 'maquina de lavar', 'dryer', 'secadora', 'dishwasher', 'lavavajillas', 
        'lave vaisselle', 'refrigerator', 'frigorifero', 'fridge', 'freezer', 'oven', 'tv', 
        'television', 'televisor', 'fernseher', 'air conditioner', 'climatiseur', 'klimaanlage'
    ]
    appliance_regex = re.compile(r'\b(' + '|'.join(big_appliances) + r')\b', re.IGNORECASE)
    exclude_terms = ['refurbished', 'renewed', 'reconditioned', 'remanufactured', 'incoming', 'delivery', 'estimated']

    processed_rows = []
    has_moq = False
    
    for i, row in enumerate(rows):
        if i == 0 and ean_idx != -1: continue # Skip header
        if len(row) < 3: continue

        # Extract values
        raw_ean = row[ean_idx] if ean_idx != -1 else ""
        raw_name = str(row[name_idx]) if name_idx != -1 else ""
        raw_brand = str(row[brand_idx]) if brand_idx != -1 else ""
        raw_price = row[price_idx] if price_idx != -1 else 0
        raw_qty = row[qty_idx] if qty_idx != -1 else 0
        
        full_name = f"{raw_brand} {raw_name}".strip()
        ean = clean_ean(raw_ean)
        price = clean_price(raw_price)
        qty = clean_qty(raw_qty)
        
        # Akatronik Brand Filter
        brand_match = any(b.lower() in full_name.lower() for b in allowed_brands)
        if not brand_match:
            continue

        # Exclusion Filters
        name_lower = full_name.lower()
        if any(term in name_lower for term in exclude_terms):
            continue
        if appliance_regex.search(name_lower):
            continue
            
        # Basic Requirements
        if qty <= 4 or price < 2.50 or not ean:
            continue
            
        total_price = round(price * qty, 2)
        
        entry = [ean, full_name, price, qty, total_price, "akatronik"]
        
        if moq_idx != -1:
            has_moq = True
            moq_val = clean_qty(row[moq_idx])
            entry.append(moq_val)
            
        processed_rows.append(entry)

    # Prepare Final Header
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    if has_moq:
        final_header.append("Min Qty")
        
    return [final_header] + processed_rows