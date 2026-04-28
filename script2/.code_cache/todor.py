import re

def process_data(rows):
    final_header = ["EAN", "Name", "Price", "Stock/Quantity", "Total Price", "Supplier"]
    has_moq = False
    extracted_data = []

    # Regex patterns
    ean_pattern = re.compile(r'\b\d{8,13}\b')
    price_pattern = re.compile(r'(\d+(?:[.,]\d+)?)\s*(?:€|\$|EUR|USD)')
    stock_pattern = re.compile(r'(\d+)\s*(?:pcs|pieces|pzs|qty|quantity)', re.IGNORECASE)
    moq_pattern = re.compile(r'moq[:\s-]*(\d+)', re.IGNORECASE)

    # Keywords to exclude (incoming/future stock)
    exclude_keywords = ['incoming', 'delivery', 'estimated', 'expected', 'date', 'arrival', 'due']

    for row in rows:
        # Flatten row into a single string for parsing free-form text
        row_text = " ".join(str(cell) for cell in row if cell is not None)
        
        # Check for exclusion keywords
        if any(kw in row_text.lower() for kw in exclude_keywords):
            continue

        # Split row text if it contains multiple EANs (multiple products in one line)
        parts = re.split(r'(?=\b\d{13}\b)', row_text)
        sub_rows = [p.strip() for p in parts if p.strip()]

        for sub_row in sub_rows:
            # Extract EAN
            ean_match = ean_pattern.search(sub_row)
            if not ean_match:
                continue
            ean = ean_match.group().zfill(13)

            # Extract Price
            price_match = price_pattern.search(sub_row)
            if not price_match:
                # Fallback: look for digits followed by a dash or at end of string
                price_match = re.search(r'-\s*(\d+(?:[.,]\d+)?)', sub_row)
            
            if not price_match:
                continue
            
            try:
                price_str = price_match.group(1).replace(',', '.')
                price = float(price_str)
            except ValueError:
                continue

            if price < 2.50:
                continue

            # Extract Stock
            stock_match = stock_pattern.search(sub_row)
            if not stock_match:
                # Fallback: look for any integer that isn't the EAN or Price
                nums = re.findall(r'\b\d+\b', sub_row)
                potential_stock = [n for n in nums if n != ean_match.group() and n not in price_str]
                stock = int(potential_stock[0]) if potential_stock else 0
            else:
                stock = int(stock_match.group(1))

            if stock <= 4:
                continue

            # Total Value check
            total_price = round(price * stock, 2)
            if total_price < 100:
                continue

            # Extract Name
            # Remove EAN, Price, and Stock info from the string to isolate the name
            name = sub_row.replace(ean_match.group(), "")
            name = re.sub(r'\d+(?:[.,]\d+)?\s*(?:€|\$|EUR|USD)', '', name)
            name = re.sub(r'\d+\s*(?:pcs|pieces|pzs|qty|quantity)', '', name, flags=re.IGNORECASE)
            name = re.sub(r'-\s*\d+.*', '', name) # Clean up tails
            name = " ".join(name.split()).strip().strip('-').strip()

            # Extract MOQ
            moq_match = moq_pattern.search(sub_row)
            moq = int(moq_match.group(1)) if moq_match else None
            if moq is not None:
                has_moq = True

            extracted_data.append({
                "EAN": ean,
                "Name": name,
                "Price": price,
                "Stock/Quantity": stock,
                "Total Price": total_price,
                "Supplier": "todor",
                "Min Qty": moq
            })

    if has_moq:
        final_header.append("Min Qty")

    output = [final_header]
    for item in extracted_data:
        row_out = [
            item["EAN"],
            item["Name"],
            item["Price"],
            item["Stock/Quantity"],
            item["Total Price"],
            item["Supplier"]
        ]
        if has_moq:
            row_out.append(item["Min Qty"])
        output.append(row_out)

    return output