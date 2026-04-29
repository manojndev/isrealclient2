import re

def process_data(rows: list) -> list:
    if not rows:
        return [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    header_row = rows[0]
    data_rows = rows[1:]

    # Indices for mapping
    idx_qty = -1
    idx_manuf = -1
    idx_type1 = -1
    idx_type2 = -1
    idx_ean = -1
    idx_price = -1

    # Heuristic identification based on sample or headers
    for i, col in enumerate(header_row):
        col_name = str(col).lower()
        if 'sum available' in col_name or 'qty' in col_name or 'available' in col_name:
            idx_qty = i
        elif 'manufacturer' in col_name or 'brand' in col_name:
            idx_manuf = i
        elif 'article type' in col_name or 'type1' in col_name or 'description' in col_name:
            idx_type1 = i
        elif 'type2' in col_name:
            idx_type2 = i
        elif 'barcode' in col_name or 'ean' in col_name:
            idx_ean = i
        elif 'price' in col_name:
            idx_price = i

    # Regex for big appliances (multilingual)
    appliances_pattern = re.compile(
        r"(wash(ing)?\s?machine|waschmaschine|wasmachine|lavadora|lavatrice|machine\s[àa]\slaver|maquina\sde\slavar|"
        r"dryer|secadora|secador|tumble|trockner|dishwasher|lavavajillas|lave\svaisselle|vaatwasser|lavastoviglie|"
        r"refrigerator|frigorifero|fridge|kühlschrank|koelkast|freezer|gefrierschrank|oven|backofen|forno|"
        r"television|televisor|fernseher|\btv\b|air\sconditioner|climatiseur|klimaanlage)",
        re.IGNORECASE
    )

    excluded_brands = {
        "aeg", "beko", "bosch", "de'longhi", "delonghi", "electrolux", 
        "gorenje", "hisense", "lg", "samsung", "siemens"
    }

    refurbished_terms = ["refurbished", "renewed", "reconditioned", "remanufactured"]

    result = [["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]]

    for row in data_rows:
        # 1. Extraction & Cleaning
        try:
            # Quantity
            raw_qty = str(row[idx_qty]) if idx_qty != -1 else "0"
            qty_clean = int(float(re.sub(r'[^\d.-]', '', raw_qty))) if any(c.isdigit() for c in raw_qty) else 0
            
            # Price
            raw_price = str(row[idx_price]) if idx_price != -1 else "0"
            price_clean = re.sub(r'[^\d.,]', '', raw_price).replace(',', '.')
            price = float(price_clean) if price_clean else 0.0
            
            # EAN
            raw_ean = str(row[idx_ean]) if idx_ean != -1 else ""
            ean = "".join(filter(str.isdigit, raw_ean)).zfill(13)
            
            # Name Construction
            manuf = str(row[idx_manuf]).strip() if idx_manuf != -1 and row[idx_manuf] else ""
            t1 = str(row[idx_type1]).strip() if idx_type1 != -1 and row[idx_type1] else ""
            t2 = str(row[idx_type2]).strip() if idx_type2 != -1 and row[idx_type2] else ""
            full_name = " ".join(filter(None, [manuf, t1, t2]))
            
            # Availability logic (Status check)
            availability_text = ""
            for cell in row:
                cell_str = str(cell).lower()
                if any(x in cell_str for x in ["incoming", "delivery", "estimated", "expected"]):
                    availability_text = cell_str
                    break
            
            # 2. Filtering
            if qty_clean <= 4: continue
            if price < 2.50: continue
            if availability_text: continue
            
            # Refurbished check
            name_lower = full_name.lower()
            if any(term in name_lower for term in refurbished_terms):
                continue
                
            # AKATRONIK Brand Filter
            if any(brand in name_lower for brand in excluded_brands):
                continue
                
            # AKATRONIK Big Appliances Filter
            if appliances_pattern.search(name_lower):
                continue

            # 3. Final Row Build
            total_price = price * qty_clean
            
            result.append([
                ean,
                full_name,
                price,
                qty_clean,
                round(total_price, 2),
                "akatronik"
            ])

        except (ValueError, IndexError, TypeError):
            continue

    return result