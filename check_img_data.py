#!/usr/bin/env python3

import pandas as pd

# Read the Excel file
df = pd.read_excel('test_img_final_fix.xlsx')

# Check if the IMG file is in the data
img_rows = df[df['Source File'].str.contains('IMG-20240321-WA0015', na=False)]

print(f"Total rows in Excel: {len(df)}")
print(f"Rows from IMG-20240321-WA0015: {len(img_rows)}")

if len(img_rows) > 0:
    print(f"\nFirst few rows from IMG file:")
    print(img_rows.head())
    
    print(f"\nColumns with data from IMG file:")
    for col in df.columns:
        img_col_data = img_rows[col].dropna()
        if len(img_col_data) > 0:
            print(f"  {col}: {len(img_col_data)} values")
else:
    print("❌ No data from IMG-20240321-WA0015 found in final Excel!")

