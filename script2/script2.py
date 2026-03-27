from __future__ import annotations

from pathlib import Path

import pandas as pd
from openpyxl import load_workbook


BASE_DIR = Path(__file__).resolve().parent
OUTPUT_FILE = BASE_DIR / "output.xlsx"
DATABASE_FILE = BASE_DIR / "database.xlsx"
FINAL_OUTPUT_FILE = BASE_DIR / "finaloutput.xlsx"


def normalize_gtin(value: object) -> str:
	"""Normalize GTIN/EAN values to a 13-digit string for reliable matching."""
	if pd.isna(value):
		return ""

	text = str(value).strip()
	if not text:
		return ""

	if "." in text:
		text = text.split(".", 1)[0]

	digits = "".join(ch for ch in text if ch.isdigit())
	if not digits:
		return ""

	if len(digits) > 13:
		return digits[-13:]
	return digits.zfill(13)


def pick_column(df: pd.DataFrame, candidates: list[str]) -> str:
	normalized = {
		str(col).strip().lower().replace(" ", ""): col for col in df.columns
	}
	for candidate in candidates:
		key = candidate.strip().lower().replace(" ", "")
		if key in normalized:
			return normalized[key]
	raise KeyError(f"None of these columns were found: {candidates}")


def apply_text_format_to_barcode(path: Path) -> None:
	wb = load_workbook(path)
	for sheet_name in ["finaloutput", "new products"]:
		if sheet_name not in wb.sheetnames:
			continue
		ws = wb[sheet_name]
		for row in ws.iter_rows(min_row=2, min_col=1, max_col=1):
			row[0].number_format = "@"
	wb.save(path)


def main() -> None:
	output_df = pd.read_excel(OUTPUT_FILE, sheet_name="clean_output")
	db_df = pd.read_excel(DATABASE_FILE, sheet_name="DataBase")

	output_ean_col = pick_column(output_df, ["EAN", "barcode", "gtin"])
	output_name_col = pick_column(output_df, ["Name", "ProductTitle", "title"])
	output_price_col = pick_column(output_df, ["Price", "selling Price", "Selling price"])
	output_qty_col = pick_column(output_df, ["Stock/Quantity", "sum Available", "qty"])

	db_gtin_col = pick_column(db_df, ["Gtin", "GTIN", "EAN", "barcode"])
	db_hifi_col = pick_column(db_df, ["Hifi code", "Product code", "Unnamed: 1"])
	db_brand_col = pick_column(db_df, ["BrandName", "Brand", "Name"])
	db_title_col = pick_column(db_df, ["roductTitle", "ProductTitle", "Title"])
	db_hifi_price_col = pick_column(db_df, ["Selling price", "Selling price "])

	output_df["_ean13"] = output_df[output_ean_col].apply(normalize_gtin)
	db_df["_ean13"] = db_df[db_gtin_col].apply(normalize_gtin)

	db_lookup = db_df[
		["_ean13", db_hifi_col, db_brand_col, db_title_col, db_hifi_price_col]
	].drop_duplicates(subset=["_ean13"], keep="first")

	merged = output_df.merge(db_lookup, on="_ean13", how="left", indicator=True)

	merged["barcode"] = merged["_ean13"]
	merged["Hifi code"] = merged[db_hifi_col].fillna("")
	merged["Name"] = merged[db_brand_col].where(
		merged[db_brand_col].notna() & (merged[db_brand_col].astype(str).str.strip() != ""),
		merged[output_name_col],
	)
	merged["ProductTitle"] = merged[db_title_col].where(
		merged[db_title_col].notna() & (merged[db_title_col].astype(str).str.strip() != ""),
		merged[output_name_col],
	)
	merged["selling Price"] = merged[output_price_col]
	merged["sum Available"] = merged[output_qty_col]
	merged["Hifi price"] = merged[db_hifi_price_col].where(
		merged[db_hifi_price_col].notna(),
		merged[output_price_col],
	)

	final_df = merged[
		[
			"barcode",
			"Hifi code",
			"Name",
			"ProductTitle",
			"selling Price",
			"sum Available",
			"Hifi price",
		]
	].copy()

	unmatched = merged[merged["_merge"] == "left_only"].copy()
	new_products_df = unmatched[
		["barcode", output_name_col, output_price_col, output_qty_col, "Total Price", "Supplier"]
	].rename(
		columns={
			output_name_col: "Name",
			output_price_col: "Price",
			output_qty_col: "Stock/Quantity",
		}
	)

	with pd.ExcelWriter(FINAL_OUTPUT_FILE, engine="openpyxl") as writer:
		final_df.to_excel(writer, sheet_name="finaloutput", index=False)
		new_products_df.to_excel(writer, sheet_name="new products", index=False)

	apply_text_format_to_barcode(FINAL_OUTPUT_FILE)
	print(f"Created: {FINAL_OUTPUT_FILE}")


if __name__ == "__main__":
	main()
