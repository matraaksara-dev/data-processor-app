import pandas as pd
import os

file_path = r"D:\1.1.1.1 PT SEDUHLUR INDO GROUP\merempah-app\dataanalytics\ZV64 IMT 2024 new.XLSX"
output_dir = r"D:\1.1.1.1 PT SEDUHLUR INDO GROUP\merempah-app\dataanalytics\split_csvs"

os.makedirs(output_dir, exist_ok=True)

print("Reading Excel file...")
xls = pd.read_excel(file_path, sheet_name=None, engine='openpyxl')

for sheet_name, df in xls.items():
    safe_name = "".join(c for c in sheet_name if c.isalnum() or c in (' ', '_', '-')).strip()
    out_file = os.path.join(output_dir, f"{safe_name}.csv")
    df.to_csv(out_file, index=False)
    print(f"Exported sheet '{sheet_name}' to '{safe_name}.csv'")

print("Done!")
