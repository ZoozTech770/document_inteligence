#!/usr/bin/env python3
"""
Repair Script for Problematic OCR Tables
Identifies and fixes transposed tables, then regenerates the Excel file
"""

import json
import os
import sys
from pathlib import Path
import pandas as pd
from extract_final_table import extract_final_table, is_likely_id
import subprocess

def is_excel_ui_row(row):
    """Check if a row contains Excel UI elements"""
    if not row:
        return False
    
    excel_ui_indicators = [
        'formula bar', 'selected', ':selected:', 'unselected', ':unselected:',
        'column_', 'row_', 'cell_', 'sheet', 'workbook'
    ]
    
    for cell in row:
        cell_str = str(cell).lower().strip()
        if any(indicator in cell_str for indicator in excel_ui_indicators):
            return True
        if ':selected:' in cell_str or ':unselected:' in cell_str:
            return True
    
    return False

def find_problematic_files():
    """Find cached JSON files that likely have transposed tables or Excel UI issues"""
    json_folder = Path("json_result")
    problematic_files = []
    
    print("🔍 Scanning cached files for problems...")
    
    for json_file in json_folder.glob("*_tables.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                tables = json.load(f)
            
            if not tables or not tables[0].get('rows'):
                continue
                
            rows = tables[0]['rows']
            first_row = rows[0] if len(rows) > 0 else []
            
            # Check for Excel UI issues
            has_excel_ui = is_excel_ui_row(first_row)
            
            # Check if first row contains IDs (suggesting transposed table)
            id_count = sum(1 for cell in first_row if is_likely_id(cell))
            
            if has_excel_ui:
                problematic_files.append((json_file, f"Excel UI elements"))
                print(f"  🚫 {json_file.name}: Contains Excel UI elements")
            elif id_count > 0:
                problematic_files.append((json_file, f"{id_count} IDs in header row"))
                print(f"  ⚠️  {json_file.name}: {id_count} IDs in header row")
                
        except Exception as e:
            print(f"  ❌ Error reading {json_file.name}: {e}")
    
    return problematic_files

def fix_problematic_file(json_file):
    """Fix a single problematic file"""
    print(f"\n🔧 Fixing: {json_file.name}")
    
    try:
        # Re-process the file with improved logic
        result = extract_final_table(str(json_file), cleanup=False)
        if result:
            print(f"  ✅ Fixed: {json_file.name}")
            return True
        else:
            print(f"  ❌ Failed to fix: {json_file.name}")
            return False
    except Exception as e:
        print(f"  ❌ Error fixing {json_file.name}: {e}")
        return False

def analyze_current_excel():
    """Analyze the current Excel file to identify issues"""
    print("\n📊 Analyzing current Excel file...")
    
    try:
        df = pd.read_excel('ocr_results.xlsx')
        
        # Find numeric column names (these are IDs that became headers)
        numeric_columns = []
        for col in df.columns:
            try:
                if str(col).replace('.', '').isdigit() and len(str(col)) > 6:
                    numeric_columns.append(col)
            except:
                pass
        
        print(f"  📈 Total rows: {len(df)}")
        print(f"  📊 Total columns: {len(df.columns)}")
        print(f"  ❌ Rows with empty ID: {df['ID'].isna().sum()}")
        print(f"  🔢 Numeric column names (should be IDs): {len(numeric_columns)}")
        
        if numeric_columns:
            print("     Problematic columns:")
            for col in numeric_columns[:5]:  # Show first 5
                count = df[col].notna().sum()
                print(f"       {col} ({count} values)")
        
        return len(numeric_columns) > 0
        
    except Exception as e:
        print(f"  ❌ Error analyzing Excel: {e}")
        return False

def regenerate_excel():
    """Regenerate the Excel file using fixed tables"""
    print("\n🔄 Regenerating Excel file with fixed data...")
    
    try:
        # Run the batch processor on already processed files
        # This will use the fixed cached results
        cmd = [sys.executable, 'batch_ocr_processor.py', '--limit', '50', '-o', 'fixed_ocr_results.xlsx']
        
        # We need to temporarily select the same files again
        # Let's create a simple script to do this automatically
        print("  🤖 Running automated reprocessing...")
        
        # This will use all the cached (now fixed) results
        result = subprocess.run(cmd, input="3\n", text=True, capture_output=True)
        
        if result.returncode == 0:
            print("  ✅ Successfully regenerated Excel file: fixed_ocr_results.xlsx")
            return True
        else:
            print(f"  ❌ Error regenerating Excel: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"  ❌ Error regenerating Excel: {e}")
        return False

def main():
    print("🛠️  TABLE REPAIR TOOL")
    print("=" * 50)
    
    # Step 1: Analyze current situation
    has_problems = analyze_current_excel()
    
    if not has_problems:
        print("\n✅ No obvious problems found in current Excel file!")
        return
    
    # Step 2: Find problematic cached files
    problematic_files = find_problematic_files()
    
    if not problematic_files:
        print("\n✅ No problematic cached files found!")
        return
    
    print(f"\n🎯 Found {len(problematic_files)} files to fix")
    
    # Step 3: Fix each problematic file
    fixed_count = 0
    for json_file, id_count in problematic_files:
        if fix_problematic_file(json_file):
            fixed_count += 1
    
    print(f"\n📈 Fixed {fixed_count} out of {len(problematic_files)} files")
    
    if fixed_count > 0:
        # Step 4: Regenerate Excel with fixed data
        if regenerate_excel():
            print("\n🎉 Repair completed successfully!")
            print("   📄 New file: fixed_ocr_results.xlsx")
            print("   📄 Original: ocr_results.xlsx (kept for comparison)")
        else:
            print("\n⚠️  Tables were fixed but Excel regeneration failed")
            print("   You can run the batch processor manually to regenerate")
    else:
        print("\n❌ No files were successfully fixed")

if __name__ == "__main__":
    main()

