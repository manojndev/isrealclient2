import re

with open('finalscript.py', 'r') as f:
    text = f.read()

# Let's target the exact prompt text replacement using regex
pattern = re.compile(r'USER_PROMPT_TEMPLATE = """.*?Python code block:\n"""', re.DOTALL)
replacement = """USER_PROMPT_TEMPLATE = \"\"\"Sample raw rows (first {sample_count} rows of the file):
{sample_rows}

Standard Processing Guidelines:
1. Identify and Format Columns: Ensure the final output has EXACTLY these columns in this exact order: "EAN", "Name", "Price", "Stock/Quantity", "Total Price" (which is Price * Stock/Quantity), and "Supplier" (which must be exactly "{supplier_name}" for every single valid item row).
2. Missing or Bad Headers: Handle data where the first row is not a clear header. Look at the data types (e.g., 13-digit numbers are EAN, strings are Name, floats are Price, integers are Stock/Quantity) if a real header is missing.
3. Fix EAN Formatting: Ensure EAN column entries are EXACTLY 13-character strings (pad with leading zeros i3. Fix EAN Formatting: Ensures3. Fix Ee Name column. If a brand/manufacturer is provided in a separate column or missing, merge it into the product Name.
5. Quantity Filter: Filter OUT (delete) any rows where Stock/Quantity <= 4.
6. Price Filter: Filter OUT (delete) any rows where Price < 2.50.
7. Supplier/Brand Filter: Filter OUT large appliances. Example brands to drop: Beko, Bosch.

User specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser specifiUser snput", default="input.xlsx", help="Input file (.xlsx/.xlsm/.csv)")',
                    'p.add_argument("--input-folder", default="input", help="Folder containing .xlsx/.csv files")')

# Replace format_prompt arguments to accept supp# Replace format_prompt arguments to accept supp# Replace format_prompt arguments to accept supp# Replace format_prompt arguments to accept supp# Replace format_prompt arguments to accept supp# Replace format_prompt arguments to accept supp# Replace format_prstruction,',
                    'instruction=instruction,\n        supplier_name=supplier_name,\n    ')

# Update run_pipeline signature and logic
run_pipeline_old = """def run_pipeline(args: argparse.Namespace):
    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path = Path(a    input_path =args.output_format)
        return
        
    if not args.instruction and not args.code_file and not args.interactive:
        args.instruction = input("\\nEnter any specific instructions (or press Enter to just apply standard rules): ").strip()

    sample_rows = raw_data[:15]
    prompt = format_prompt(sample_rows, args.instruction)

    if args.print_prompts:
        print("\\n===== SYSTEM PROMPT =====\\n")
        print(SYSTEM_PR        print(SYSTEM_PR        print(SYSTEM_PR        print(SYSTEM_PR        print(SYSTEM_
    python_code = ""

    if args.code_file:    if args.code_file:    if args.ode_file).read_text(encoding="utf-8")
    elif args.interactive:
        python_code = extract_code_from_pasted_input()
    else:  # Default to Gemini if no other mode is specified
        print("Generating processing script via Gemini...")
        python_code = asyncio.run(generate_code_with_gemini(SYSTEM_PROMPT, prompt, args))
        if args.save_code_file:
            save_path = Path(args.save_code_file)
            save_path.p            parents=True            save_path.p            parents=True            save_path.p     f-            save_path.p            parents=True            save_path.p            parents=True            save_path.p     f- se ValueError("No python code generated or provided.")

    print("\\nExecuting dynamically generated script on the full dataset...")
    # Create execution namespace
                                                                                                                 rocess_data")
        if n        if n        if n        if n        if n        if n        if n        if n        ta        if n        if n  
        processed_data = process_func(raw_data)
        
    except Exception as e:
        print("=== Generated Cod        print("=== Generated Cod        print("=== Generat==        print("=== Generated Cod        print("=== Generated Cod        print("=== Gener {        print("=== Generated Cessed_data, Path(args.output), args.output_format)
                                                                                                                                                                                                                                                                                                               s.input_folder)
    if not input_folder.exists() or not input_folder.is_dir():
        print(f"Input folder not found: {input_folder}. Creating it now... Please add files and run again.")
        input_folder.mkdir(parents=True, exist_ok=True)
        return

    if not args.instruction and not args.code_file and not args.interactive:
        args.instruction = input("\\nEnter any specific instructions (or press Enter to just a        args.instruction strip()

    all_files = [f for f in input_folder.iterdir() if f.suffix.lower() in {'.xlsx', '.xls', '.csv'}]
    if not all_files:
        print(f"No excel/csv files found in {input_folder}")
        return

    master_output = []
    headers = None

    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    for file_    fe     for file_    for file_    for file_    for file_    for f           
        sample_rows = raw_data[:15]
        prompt = format_prompt(sample_rows, args.instruction, supplier_name)

        if args.print_prompts:
            print("\\n===== SYSTEM PROMPT =====\\n")
            print(SYSTEM_PROMPT)
            print("\\n===== USER PROMPT =====\\n")
            print(prompt)
            continue

        python_code = ""

        if args.code_file:
            python_code = Path(args.code_file).read_text(encoding="utf-8")
        elif args.interactive:
            python_code = extract_code_from_pasted_input()
        else:
            print(f"Generating custom code via Gemini for '{supplier_name}'...")
            python_code = asyncio.run(generate_code_with_gemini(SYSTEM_PROMPT, prompt, args))
            if args.save_code_file:
                save_path = Path(f"{args.save_code_file}_{supplier_name}.py")
                save_path.parent.mkdir(parents=True, exist_ok=True)
                save_path.write_text(python_code, encoding="utf-8")

        if not python_code.strip():
            print(f"Skipping {file_path.name} - no python code generated.")
            continue

        exec_globals = {}
        try:
            exec(python_code, exec_globals)
            process_func = exec_globals.get("process_data")
            if not process_func:
                raise KeyError("The generated code did not define a `process_data` function.")
                
            processed_data = process_func(raw_data)
            
            if not processed_data:
                continue

            current_headers = processed_data[0]
            if headers is None:
                headers = current_headers
                master_output.append(headers)

            master_output.extend(processed_data[1:])
            print(f"-> Extracted {len(processed_data) - 1} valid rows for {supplier_name}.")
            
        except Exception as e:
            print("=== Generated Code Failed ===")
            print(python_code)
            print("============================")
            print(f"Error executing generated code for {file_path.name}: {e}")

    if master_output and len(master_output) > 1:
        export_data_raw(maste        export_data_raw(maste        exporormat)
        print(f"\\n=== Final Pipeline Summary ===")
        print(f"- Processed files: {len(all_files)}")
        print(f"- Total output rows (excluding header): {len(master_output) - 1}")
        pri        pri        pri        pri        priutput}")
    else:
                               uccessfully matched or processed across files.")"""

text = text.replace(run_pipeline_old, run_pipeline_new)

with open('finalscript.py', 'w') as f:
    f.write(text)

