import re
with open('finalscript.py', 'r') as f:
    content = f.read()

# Replace USER_PROMPT_TEMPLATE
old_prompt = """USER_PROMPT_TEMPLATE = \"\"\"Sample raw rows (first {sample_count} rows of the file):
{sample_rows}

Standard Processing Guidelines:
1. Identify and Format Columns: Ensure the final output has EXACTLY these columns in this order: "EAN", "Name", "Price", and "Stock/Quantity".
2. Missing or Bad Headers: Handle data where the first row is not a clear header. Look at the data types (e.g., 13-digit numbers are EAN, strings are Name, floats are Price, integers are Stock/Quantity) if a real header is missing.
3. Fix EAN Formatting: Ensure EAN column entries are EXACTLY 13-character strings (pad with leading zeros if necessary).
4. Product Names: Use the Name column. If a brand/manufacturer is provided in a separate column or missing, merge it into the product Name.
5. Quantity Filter: Filter OUT (delete) any rows where Stock/Quantity <= 4.
6. Price Filter: Filter OUT (delete) any rows where Price < 2.50.
7. Supplier/Brand Filter: Filter OUT large appliances. Example brands to drop: Beko, Bosch.

User specific request:
{instruction}

Generate the full `def process_data(rows: list[list[Any]]) -> list[list[Any]]:` Python code block:
\"\"\""""

new_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pnew_pns:
1. Identify and Format Columns: Ensure the final output has EXACTLY these columns in this order: "EAN", "Name", "Price", "Stock/Quantity", "Total Price" (which is Price * Stock/Quantity), and "Supplier" (which must be exactly "{supplier_name}" for every row).
2. Missing or Bad Headers: Handle data where the first row is not a clear header. Look at the data types (e.g., 13-digit numbers are EAN, strings are Name, floats are Price, integers are Stock/Quantity) if a real header is missing.
3. Fix EAN Formatting: Ensure EAN column entries are EXACTLY 13-character strings (pad with leading zeros if necessary).
4. Product Names: Use the Name column. If a brand/manufacturer is provided in a separate column or missing, merge it into the product Name.
5. Quantity Filter: Filter OUT (delete) any rows where Stock/Quantity <= 4.
6. Price Filter: Filter OUT (delete) any rows where Price < 2.30.
7. Total Filter: Filter OUT any rows where Total Price <= 100.
8. Supplier/Brand Filter: Filter OUT large appliances. Example bra8. Supplier/Brand Filter: Filter OUT large appliances. Example bra8. Supplier/Brand Filter: Filter OUT large appliances. Example bra8. Supplier/Brand Filter: Filter OUT large appliances. Example bra8. S   content = content.replace(old_prompt, new_prompt)

with open('finalscript.py', 'w') as f:
    f.write(content)
