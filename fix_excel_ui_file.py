#!/usr/bin/env python3
"""
Specific fix for files with Excel UI elements
This handles the case where row 0 has headers with Excel UI elements like ":selected:"
"""

import json
import sys
from pathlib import Path

def clean_excel_header(header):
    """Clean Excel UI elements from header text"""
    if not header:
        return header
    
    # Remove Excel UI elements
    cleaned = str(header)
    cleaned = cleaned.replace('\n:selected:', '')
    cleaned = cleaned.replace('\n:unselected:', '')
    cleaned = cleaned.replace(':selected:', '')
    cleaned = cleaned.replace(':unselected:', '')
    cleaned = cleaned.strip()
    
    return cleaned

def is_excel_formula_bar_row(row):
    """Check if this row contains Formula Bar or other Excel UI elements"""
    if not row:
        return False
    
    for cell in row:
        cell_str = str(cell).lower().strip()
        if 'formula bar' in cell_str:
            return True
    
    return False

def fix_excel_ui_table(json_file):
    """Fix the specific Excel UI table issue"""
    
    # Read the original table
    with open(json_file, 'r', encoding='utf-8') as f:
        tables = json.load(f)
    
    if not tables:
        print("❌ No tables found")
        return None
    
    table = tables[0]
    rows = table['rows']
    
    print("🔍 ANALYZING TABLE STRUCTURE:")
    for i, row in enumerate(rows[:3]):
        print(f"  Row {i}: {row}")
    
    # Check if row 0 has Excel UI elements but valid headers
    if len(rows) > 0:
        row0 = rows[0]
        cleaned_headers = [clean_excel_header(h) for h in row0]
        
        # Check if cleaned headers look like real headers
        real_headers = any(h.lower() in ['first name', 'last name', 'i.d.', 'id', 'name'] 
                          for h in cleaned_headers if h)
        
        if real_headers:
            print("✅ Found real headers in row 0 (after cleaning)")
            print(f"   Original: {row0}")
            print(f"   Cleaned:  {cleaned_headers}")
            
            # Find the first data row (skip Excel UI rows)
            data_start_row = 1
            for i in range(1, min(len(rows), 3)):
                if is_excel_formula_bar_row(rows[i]):
                    print(f"🚫 Skipping Excel UI row {i}: {rows[i][:2]}...")
                    data_start_row = i + 1
                else:
                    break
            
            print(f"📊 Data starts from row {data_start_row}")
            
            # Create corrected table
            corrected_rows = [cleaned_headers] + rows[data_start_row:]
            
            # Analyze the structure to fix column mapping
            # Looking at the pattern: First Name, Last Name, ID
            # But the data seems to be: First Name, Empty, Last Name, ID
            
            # Check a few data rows to understand the pattern
            print("🔍 ANALYZING DATA PATTERN:")
            for i, row in enumerate(rows[data_start_row:data_start_row+3]):
                print(f"   Data row {i}: {row}")
            
            # It looks like:
            # Headers: ["First Name", "Last Name", "I.D."]  (3 columns)
            # Data:    ["Dov", "", "Mendelovich", "23846223"]  (4 columns)
            # This suggests the table structure is misaligned
            
            # Let's reconstruct based on the pattern we see:
            # Column 0: First Name (Dov, Eyal, etc.)
            # Column 1: (empty)
            # Column 2: Last Name (Mendelovich, Zellerkraut, etc.)  
            # Column 3: ID (23846223, 337666549, etc.)
            
            new_headers = ["First Name", "Middle", "Last Name", "ID"]
            new_rows = [new_headers] + rows[data_start_row:]
            
            result = {
                "table_index": 0,
                "row_count": len(new_rows),
                "column_count": len(new_headers),
                "rows": new_rows,
                "metadata": {
                    "original_headers": row0,
                    "cleaned_headers": cleaned_headers,
                    "corrected_headers": new_headers,
                    "column_order": "First Name → Middle → Last Name → ID",
                    "processed_by": "fix_excel_ui_file.py",
                    "note": "Fixed Excel UI elements and corrected column structure"
                }
            }
            
            # Save the corrected version
            output_file = json_file.replace('_tables.json', '_final_table.json')
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump([result], f, ensure_ascii=False, indent=2)
            
            print(f"💾 Corrected table saved to: {output_file}")
            
            # Show preview
            print("\n📋 CORRECTED STRUCTURE:")
            for i, row in enumerate(new_rows[:5]):
                print(f"   Row {i}: {row}")
            
            return output_file
    
    return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 fix_excel_ui_file.py <tables.json>")
        sys.exit(1)
    
    json_file = sys.argv[1]
    if not Path(json_file).exists():
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    print(f"🛠️  Fixing Excel UI issues in: {json_file}")
    result = fix_excel_ui_table(json_file)
    
    if result:
        print("✅ Successfully fixed Excel UI table!")
    else:
        print("❌ Failed to fix table")

