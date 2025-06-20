#!/usr/bin/env python3
"""
Test Excel Header Detection for specific file
"""

import pandas as pd
import json
from pathlib import Path
from column_normalizer import ColumnNormalizer

def test_excel_headers():
    # Load the specific file data from cache
    cache_file = Path("json_result/IMG-20240321-WA0015-06AVg000003jvdEMAQ-a542ee10_final_table.json")
    
    if not cache_file.exists():
        print(f"Cache file not found: {cache_file}")
        return
    
    print("Loading cached data...")
    with open(cache_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Extract table data
    table_data = data[0]['rows']
    
    # Create DataFrame
    df = pd.DataFrame(table_data[1:], columns=table_data[0])  # Skip first row, use as headers
    
    print(f"Original DataFrame shape: {df.shape}")
    print(f"Original columns: {list(df.columns)}")
    print(f"First few rows:")
    print(df.head(3))
    print()
    
    # Initialize normalizer
    normalizer = ColumnNormalizer()
    
    # Test the Excel header detection
    print("Testing Excel header detection...")
    df_fixed = normalizer.detect_and_fix_excel_headers(df)
    
    print(f"After Excel header fix - shape: {df_fixed.shape}")
    print(f"After Excel header fix - columns: {list(df_fixed.columns)}")
    print(f"First few rows after fix:")
    print(df_fixed.head(3))
    print()
    
    # Apply full normalization
    print("Applying full normalization...")
    df_normalized = normalizer.normalize_dataframe(df)
    
    print(f"Final DataFrame shape: {df_normalized.shape}")
    print(f"Final columns: {list(df_normalized.columns)}")
    print(f"First few rows final:")
    print(df_normalized.head(3))

if __name__ == "__main__":
    test_excel_headers()

