import pandas as pd
import os

file_path = 'k:/Luciana/dashboard-financeiro/importacao-contas.xlsx'

if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit()

try:
    xl = pd.ExcelFile(file_path)
    print(f"Sheets: {xl.sheet_names}")
    
    for sheet in xl.sheet_names:
        print(f"\n--- Sheet: {sheet} ---")
        df = pd.read_excel(file_path, sheet_name=sheet)
        print(f"Columns: {list(df.columns)}")
        print("First 5 rows:")
        print(df.head().to_string())
        
        # Check for ID and CONTA
        if 'ID' in df.columns:
            print(f"\nIDs found in {sheet}: {df['ID'].unique()[:10]} ...")
        else:
            print(f"\nWARNING: 'ID' column missing in {sheet}")

except Exception as e:
    print(f"Error reading file: {e}")
