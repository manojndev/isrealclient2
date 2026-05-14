import re

def process_data(rows):
    if not rows:
        return []

    # Final headers
    header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    processed_rows = [header]
    
    # Indices for the input data based on sample
    # 0: QTY, 1: MODEL, 2: PN, 3: EAN, 4: PRICE, 5: AVAILABILITY
    
    for row in rows:
        # Skip potential header row if it contains keywords
        if any(isinstance(val, str) and 'EAN' in val.upper() for val in row):
            continue
            
        try:
            # 1. Extract and Clean Quantity
            qty_raw = str(row[0]).strip()
            qty_clean = int(re.sub(r'[^\d]', '', qty_raw)) if qty_raw else 0
            
            # 2. Extract and Clean Name
            name = str(row[1]).strip()
            
            # 3. Extract and Clean EAN
            ean_raw = str(row[3]).strip()
            ean_clean = re.sub(r'[^\d]', '', ean_raw)
            if ean_clean:
                ean_clean = ean_clean.zfill(13)
            else:
                ean_clean = ""
                
            # 4. Extract and Clean Price
            price_raw = str(row[4]).strip()
            price_clean = float(re.sub(r'[^-0-9.]', '', price_raw.replace(',', '.')))
            
            # 5. Extract Availability
            avail = str(row[5]).lower() if len(row) > 5 else ""

            # --- Filtering Rules ---
            
            # Exclusion: Quantity <= 4
            if qty_clean <= 4:
                continue
                
            # Exclusion: Price < 2.50
            if price_clean < 2.50:
                continue
                
            # Exclusion: Total stock value < 100
            total_price = round(price_clean * qty_clean, 2)
            if total_price < 100:
                continue
                
            # Exclusion: Only "in stock" allowed
            # Exclude if contains incoming or date patterns
            if "stock" not in avail or any(x in avail for x in ["incoming", "delivery", "expected"]):
                continue
            
            # Exclusion: Refurbished / Scooter
            name_lower = name.lower()
            refurb_terms = ["refurbished", "renewed", "reconditioned", "remanufactured"]
            if any(term in name_lower for term in refurb_terms):
                continue
            
            if re.search(r'scooter', name_lower):
                continue
            
            # Final Validation for EAN
            if len(ean_clean) != 13:
                continue

            # Append valid row
            processed_rows.append([
                ean_clean,
                name,
                price_clean,
                qty_clean,
                total_price,
                "ampq"
            ])

        except (ValueError, IndexError):
            continue

    return processed_rows