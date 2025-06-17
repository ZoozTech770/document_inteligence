#!/usr/bin/env python3
"""
Extract final table with custom column order and clean up temp files
Usage: python3 extract_final_table.py <tables.json> [--cleanup]
"""

import json
import sys
import os

def extract_final_table(json_file, cleanup=False):
    """Extract and reorder table, optionally cleaning up the input file"""
    
    # Read the input file
    with open(json_file, 'r', encoding='utf-8') as f:
        tables = json.load(f)
    
    if not tables:
        print("❌ No tables found in JSON file")
        return None
    
    table = tables[0]  # Use first table
    if not table['rows']:
        print("❌ No rows found in table")
        return None
    
    headers = table['rows'][0]
    print(f"📊 Original headers: {headers}")
    
    # Smart column detection
    id_col = None
    fname_col = None
    lname_col = None
    
    for i, header in enumerate(headers):
        h = header.lower().strip()
        if 'תז' in h or 'id' in h:
            id_col = i
        elif 'שם פרטי' in h or 'first' in h:
            fname_col = i
        elif 'שם משפחה' in h or 'last' in h or 'surname' in h:
            lname_col = i
    
    print(f"🔍 Found columns - ID: {id_col}, First Name: {fname_col}, Last Name: {lname_col}")
    
    # Create new column order: ID, First Name, Last Name, Others
    new_order = []
    if id_col is not None:
        new_order.append(id_col)
    if fname_col is not None:
        new_order.append(fname_col)
    if lname_col is not None:
        new_order.append(lname_col)
    
    # Add remaining columns
    for i in range(len(headers)):
        if i not in new_order:
            new_order.append(i)
    
    print(f"🔄 New column order: {[headers[i] for i in new_order]}")
    
    # Reorder all rows
    reordered_rows = []
    for row in table['rows']:
        new_row = [row[i] if i < len(row) else '' for i in new_order]
        reordered_rows.append(new_row)
    
    # Create final result
    result = {
        "table_index": 0,
        "row_count": table['row_count'],
        "column_count": table['column_count'],
        "rows": reordered_rows,
        "metadata": {
            "original_headers": headers,
            "reordered_headers": [headers[i] for i in new_order],
            "column_order": "ID → First Name → Last Name → Others",
            "processed_by": "extract_final_table.py"
        }
    }
    
    # Generate output filename
    if json_file.endswith('_tables.json'):
        output_file = json_file.replace('_tables.json', '_final_table.json')
    else:
        output_file = json_file.replace('.json', '_final_table.json')
    
    # Save result
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump([result], f, ensure_ascii=False, indent=2)
    
    print(f"💾 Final table saved to: {output_file}")
    
    # Clean up input file if requested
    if cleanup and json_file != output_file:
        print(f"🗑️  Removing input file: {json_file}")
        os.remove(json_file)
    
    return output_file, result

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 extract_final_table.py <tables.json> [--cleanup]")
        print("")
        print("Options:")
        print("  --cleanup    Remove the input JSON file after processing")
        print("")
        print("Example:")
        print("  python3 extract_final_table.py student_tables.json --cleanup")
        sys.exit(1)
    
    json_file = sys.argv[1]
    cleanup = '--cleanup' in sys.argv
    
    if not os.path.exists(json_file):
        print(f"❌ File not found: {json_file}")
        sys.exit(1)
    
    print(f"🚀 Processing: {json_file}")
    if cleanup:
        print("🧹 Cleanup mode: will remove input file after processing")
    
    result = extract_final_table(json_file, cleanup)
    
    if result:
        output_file, table_data = result
        print("")
        print("✅ Success!")
        print(f"📄 Final file: {output_file}")
        print("")
        print("📋 Preview (first 3 rows):")
        for i, row in enumerate(table_data['rows'][:3]):
            print(f"   Row {i}: {row}")
    else:
        print("❌ Processing failed")
        sys.exit(1)

