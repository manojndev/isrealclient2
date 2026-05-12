import re

def process_data(rows):
    if not rows:
        return []

    # Final headers
    output_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    
    # 1. Column Identification
    # Sample structure: 0:sum Available, 1:manufacturer, 2:article Type, 3:Type2, 4:barcode, 5:selling Price
    idx_qty = 0
    idx_brand = 1
    idx_desc = 2
    idx_extra = 3
    idx_ean = 4
    idx_price = 5

    # Regex for standard filters
    refurb_regex = re.compile(r'refurbished|renewed|reconditioned|remanufactured', re.IGNORECASE)
    scooter_regex = re.compile(r'scooter', re.IGNORECASE)
    
    # AKATRONIK Brand Filter
    forbidden_brands = ['AEG', 'BEKO', 'BOSCH', "DE'LONGHI", 'ELECTROLUX', 'GORENJE', 'HISENSE', 'LG', 'SAMSUNG', 'SIEMENS']
    
    # AKATRONIK Appliance Filter (Multilingual / Accent Insensitive variations handled by basic strings)
    appliances = [
        'washing machine', 'washmachine', 'waschmaschine', 'wasmachine', 'lavadora', 'lavatrice', 
        'machine a laver', 'maquina de lavar', 'dryer', 'secadora', 'dishwasher', 'lavavajillas', 
        'lave vaisselle', 'refrigerator', 'frigorifero', 'fridge', 'freezer', 'oven', 'tv', 
        'television', 'televisor', 'fernseher', 'air conditioner', 'climatiseur', 'klimaanlage'
    ]
    appliance_regex = re.compile('|'.join(appliances), re.IGNORECASE)

    processed_data = [output_header]

    # Skip header row
    for row in rows[1:]:
        try:
            # Basic data extraction
            raw_qty = str(row[idx_qty]) if idx_qty < len(row) else "0"
            raw_brand = str(row[idx_brand]) if idx_brand < len(row) else ""
            raw_desc = str(row[idx_desc]) if idx_desc < len(row) else ""
            raw_type2 = str(row[idx_extra]) if idx_extra < len(row) and row[idx_extra] else ""
            raw_ean = str(row[idx_ean]) if idx_ean < len(row) else ""
            raw_price = str(row[idx_price]) if idx_price < len(row) else "0"

            # Clean Name
            full_name = f"{raw_brand} {raw_desc} {raw_type2}".strip()
            
            # --- Filters ---
            # 1. Brand Filter
            brand_upper = raw_brand.upper()
            if any(fb in brand_upper for fb in forbidden_brands) or any(fb in full_name.upper() for fb in forbidden_brands):
                continue
            
            # 2. Appliance Filter
            if appliance_regex.search(full_name):
                continue

            # 3. Refurbished / Scooter Filter
            if refurb_regex.search(full_name) or scooter_regex.search(full_name):
                continue

            # 4. Quantity Cleaning & Filter
            qty_clean = re.sub(r'[^\d]', '', raw_qty)
            quantity = int(qty_clean) if qty_clean else 0
            if quantity <= 4:
                continue

            # 5. Price Cleaning & Filter
            price_clean = re.sub(r'[^\d.]', '', raw_price.replace(',', '.'))
            price = float(price_clean) if price_clean else 0.0
            if price < 2.50:
                continue
            
            # Total price calculation (Note: No 100 EUR filter for AKATRONIK per rules)
            total_price = round(price * quantity, 2)

            # 6. EAN Cleaning
            ean_clean = re.sub(r'[^\d]', '', raw_ean)
            if not ean_clean:
                continue
            ean = ean_clean.zfill(13)

            # Build final row
            final_row = [
                ean,
                full_name,
                price,
                quantity,
                total_price,
                "akatronik"
            ]
            processed_data.append(final_row)

        except (ValueError, IndexError):
            continue

    return processed_data