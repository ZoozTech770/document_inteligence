#!/usr/bin/env python3

import pandas as pd
import json
import os
import hashlib
from pathlib import Path

def get_file_hash(filepath):
    """Calculate MD5 hash of file content"""
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        return hashlib.md5(content).hexdigest()[:8]
    except:
        return None

def analyze_excel_errors():
    """Analyze Excel file for 'No table data extracted' errors and check JSON cache"""
    
    # Read Excel file
    excel_path = "excel_results/ocr_results.xlsx"
    if not os.path.exists(excel_path):
        print(f"❌ Excel file not found: {excel_path}")
        return
    
    df = pd.read_excel(excel_path)
    print(f"📊 Total rows in Excel: {len(df)}")
    
    # Filter rows with 'No table data extracted' in Error column
    error_rows = df[df['Error'].str.contains('No table data extracted', na=False)]
    print(f"🔍 Found {len(error_rows)} rows with 'No table data extracted'")
    
    if len(error_rows) == 0:
        print("✅ No 'No table data extracted' errors found!")
        return
    
    cache_dir = Path("temp_results")
    checked_count = 0
    found_data_count = 0
    
    print("\n🔍 Checking JSON cache files for these errors...")
    print("=" * 80)
    
    for idx, row in error_rows.head(20).iterrows():  # Check first 20 errors
        source_file = row['Source File']
        print(f"\n📄 Checking: {source_file}")
        
        # Find JSON cache file by filename pattern
        # Files are stored as: filename_tables.json
        base_name = source_file.replace('.jpg', '').replace('.jpeg', '').replace('.png', '').replace('.gif', '')
        json_file = cache_dir / f"{base_name}_tables.json"
        
        if not json_file.exists():
            print(f"   ❌ Cache file not found: {json_file}")
            continue
        
        checked_count += 1
        
        # Read and analyze JSON cache
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            print(f"   ✅ Cache file found: {json_file}")
            
            # Check data structure - it could be a list of tables or nested structure
            if isinstance(cache_data, list) and len(cache_data) > 0:
                # Direct list of tables
                tables = cache_data
                print(f"   🎯 FOUND TABLES: {len(tables)} table(s) in cache!")
                found_data_count += 1
                
                # Show table details
                for i, table in enumerate(tables):
                    rows = table.get('row_count', 0)
                    cols = table.get('column_count', 0)
                    cells = len(table.get('cells', []))
                    print(f"      Table {i+1}: {rows}x{cols} ({cells} cells)")
                    
                    # Show first few cells with content
                    if cells > 0:
                        content_cells = []
                        for cell in table.get('cells', [])[:10]:
                            content = cell.get('content', '').strip()
                            if content:
                                content_cells.append(content)
                        
                        if content_cells:
                            print(f"         Sample content: {', '.join(content_cells[:5])}")
                        else:
                            print(f"         All cells appear empty")
            
            elif isinstance(cache_data, dict):
                # Nested structure - check for analyzeResult
                analyzeResult = cache_data.get('analyzeResult', {})
                tables = analyzeResult.get('tables', [])
                
                if tables:
                    print(f"   🎯 FOUND TABLES: {len(tables)} table(s) in cache!")
                    found_data_count += 1
                    
                    # Show table details
                    for i, table in enumerate(tables):
                        rows = table.get('rowCount', 0)
                        cols = table.get('columnCount', 0)
                        cells = len(table.get('cells', []))
                        print(f"      Table {i+1}: {rows}x{cols} ({cells} cells)")
                        
                        # Show first few cells
                        if cells > 0:
                            first_cells = table.get('cells', [])[:3]
                            for cell in first_cells:
                                content = cell.get('content', '').strip()
                                if content:
                                    print(f"         Cell: '{content}'")
                else:
                    print(f"   ℹ️  No tables found in cache (confirmed)")
                    
                    # Check if there's any text content
                    pages = analyzeResult.get('pages', [])
                    total_lines = sum(len(page.get('lines', [])) for page in pages)
                    print(f"      Text lines found: {total_lines}")
            
            else:
                print(f"   ℹ️  Unexpected data structure in cache")
                
        except Exception as e:
            print(f"   ❌ Error reading cache: {e}")
    
    print("\n" + "=" * 80)
    print(f"📊 SUMMARY:")
    print(f"   Files checked: {checked_count}")
    print(f"   Files with missed table data: {found_data_count}")
    
    if found_data_count > 0:
        print(f"\n⚠️  FOUND {found_data_count} files with table data that wasn't extracted!")
        print("   This suggests the table extraction logic may need improvement.")
    else:
        print(f"\n✅ All 'No table data extracted' errors are accurate.")

if __name__ == "__main__":
    analyze_excel_errors()

