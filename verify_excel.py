#!/usr/bin/env python3
"""
Verify Excel structure script
"""

import pandas as pd
import sys

def verify_excel(filename):
    try:
        df = pd.read_excel(filename)
        print(f"📊 Excel file: {filename}")
        print(f"📏 Dimensions: {df.shape[0]} rows × {df.shape[1]} columns")
        print(f"\n📋 Column names:")
        for i, col in enumerate(df.columns, 1):
            print(f"   {i}. {col}")
        
        print(f"\n🔍 First 5 rows:")
        print(df.head().to_string(index=False))
        
        # Check if we have the expected structure
        if 'Source File' in df.columns:
            unique_files = df['Source File'].nunique()
            print(f"\n📁 Number of source files: {unique_files}")
            
            # Check for expected columns (ID, name columns)
            id_cols = [col for col in df.columns if any(x in col.lower() for x in ['תז', 'id'])]
            name_cols = [col for col in df.columns if any(x in col.lower() for x in ['שם', 'name'])]
            
            print(f"🆔 ID columns found: {id_cols}")
            print(f"👤 Name columns found: {name_cols}")
            
        return True
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 verify_excel.py <excel_file>")
        sys.exit(1)
    
    verify_excel(sys.argv[1])

