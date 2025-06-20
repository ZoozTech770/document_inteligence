#!/usr/bin/env python3
"""
Extract final table with custom column order and clean up temp files
Usage: python3 extract_final_table.py <tables.json> [--cleanup]
"""

import json
import sys
import os
import re

def is_excel_ui_row(row):
    """Check if a row contains Excel UI elements that shouldn't be headers"""
    if not row:
        return False
    
    excel_ui_indicators = [
        'formula bar', 'selected', ':selected:', 'unselected', ':unselected:',
        'column_', 'row_', 'cell_', 'sheet', 'workbook'
    ]
    
    # Check for Excel column names (A, B, C, D, etc.)
    excel_columns = [chr(i) for i in range(ord('A'), ord('Z')+1)]  # A-Z
    
    for cell in row:
        cell_str = str(cell).lower().strip()
        
        # Check for Excel UI elements
        if any(indicator in cell_str for indicator in excel_ui_indicators):
            return True
            
        # Check for single letter columns (A, B, C, etc.)
        if cell_str in [col.lower() for col in excel_columns]:
            return True
            
        # Check for Excel UI patterns like "First Name\n:selected:"
        if ':selected:' in cell_str or ':unselected:' in cell_str:
            return True
    
    return False

def is_header_row(row):
    """Determine if a row looks like headers or data"""
    if not row:
        return False
    
    # First check if this is an Excel UI row (definitely not headers)
    if is_excel_ui_row(row):
        return False
    
    # Check for common header patterns
    header_indicators = [
        'id', 'תז', 'ת.ז', 'מספר', 'first', 'last', 'שם פרטי', 'שם משפחה', 
        'name', 'employee', 'עובד', 'חתימה', 'signature'
    ]
    
    valid_headers = 0
    for cell in row:
        cell_str = str(cell).lower().strip()
        if any(indicator in cell_str for indicator in header_indicators):
            valid_headers += 1
        elif cell_str and len(cell_str) > 8 and cell_str.isdigit():
            # Long numeric values are likely data, not headers
            return False
    
    # If most cells look like headers, it's probably a header row
    return valid_headers >= max(1, len(row) // 2)

def is_likely_id(value):
    """Check if a value looks like an ID"""
    if not value:
        return False
    val_str = str(value).strip()
    
    # Check for Israeli ID patterns (9 digits with optional spaces/separators)
    import re
    if re.match(r'^\d{2,3}\s*\d{5,6}$', val_str):  # e.g., "255 87932"
        return True
    if re.match(r'^\d{9}$', val_str):  # e.g., "123456789"
        return True
    if re.match(r'^\d{8,10}$', val_str):  # 8-10 digit IDs
        return True
    
    # Fallback to original logic
    val_str = val_str.replace('-', '').replace('/', '').replace(' ', '')
    return val_str.isdigit() and len(val_str) >= 6

def contains_embedded_id(text):
    """Check if text contains an embedded ID (name + ID number)"""
    if not text:
        return False
    text_str = str(text).strip()
    # Look for patterns like "הכהן קרנר 314905662" (name followed by ID)
    import re
    # Pattern: Hebrew/English text followed by a 9+ digit number
    pattern = r'[\u0590-\u05FFa-zA-Z\s]+\d{8,}'
    return bool(re.search(pattern, text_str))

def detect_table_structure(rows):
    """Analyze table structure to find the best header row and data organization"""
    if not rows or len(rows) < 2:
        return 0, []
    
    best_header_row = 0
    
    # Check for column count mismatch between header and data rows
    header_cols = len(rows[0])
    data_cols = len(rows[1]) if len(rows) > 1 else header_cols
    
    if header_cols != data_cols and len(rows) > 2:
        print(f"⚠️  Column mismatch detected: Header={header_cols} cols, Data={data_cols} cols")
        
        # If data rows have more columns than header, the table structure is wrong
        if data_cols > header_cols:
            print(f"🔧 Data rows have more columns - reconstructing header row")
            
            # Check if first row contains embedded ID data (should be treated as data, not header)
            # Use module-level function
            first_row_has_embedded_ids = any(contains_embedded_id(val) for val in rows[0])
            
            if first_row_has_embedded_ids:
                print(f"🔄 First row contains embedded IDs, treating as data: {rows[0]}")
                # Pad the first row to match data column count
                padded_first_row = list(rows[0])
                while len(padded_first_row) < data_cols:
                    padded_first_row.append('')  # Add empty columns
                
                # Insert this as a data row after creating proper headers
                all_data_rows = [padded_first_row] + rows[1:]
            else:
                all_data_rows = rows[1:]
            
            # Analyze all data to create proper headers
            corrected_headers = []
            
            for col_idx in range(data_cols):
                # Check what type of data is in this column across multiple rows
                id_count = 0
                text_count = 0
                empty_count = 0
                
                for row in all_data_rows[:6]:  # Check first 6 data rows
                    if col_idx < len(row):
                        cell = row[col_idx]
                        if not cell or str(cell).strip() == '':
                            empty_count += 1
                        elif is_likely_id(cell):
                            id_count += 1
                        elif str(cell).strip() and not str(cell).isdigit():
                            text_count += 1
                
                # Assign header based on data pattern
                if id_count >= 3:  # Most values are IDs
                    corrected_headers.append('ID')
                elif empty_count >= 3:  # Most values are empty
                    corrected_headers.append('')
                elif text_count >= 3:  # Most values are text
                    if col_idx == 0:  # First text column is usually first name
                        corrected_headers.append('First Name')
                    elif 'First Name' in corrected_headers:  # Second text column is usually last name
                        corrected_headers.append('Last Name')
                    else:
                        corrected_headers.append('Name')
                else:
                    corrected_headers.append(f'Column_{col_idx+1}')
            
            print(f"🔨 Corrected headers: {corrected_headers}")
            print(f"📊 Total data rows including recovered: {len(all_data_rows)}")
            
            # Rebuild the rows array with corrected headers and all data
            rows[:] = [corrected_headers] + all_data_rows
            return 0, corrected_headers
    
    # Check if first row contains ID data instead of headers
    first_row = rows[0]
    first_row_has_ids = any(is_likely_id(val) for val in first_row)
    
    # Also check if first row has header-like content
    def has_header_like_content(row):
        """Check if a row contains header-like content"""
        header_words = ['id', 'name', 'שם', 'ת.ז', 'תז', 'ת״ז', 'מספר', 'זהות', 'first', 'last', 'תפקיד', 'position', 'משפחה', 'מגורים']
        for val in row:
            if val:
                val_str = str(val).strip().lower()
                for word in header_words:
                    if word in val_str:
                        return True
        return False
    
    
    def is_title_or_metadata_row(row, max_cols):
        """Check if row appears to be a title/metadata rather than table headers"""
        if not row:
            return False
        
        # If row has significantly fewer columns than expected, it might be a title
        non_empty_count = sum(1 for val in row if val and str(val).strip())
        if non_empty_count <= 1 and len(row) < max_cols:
            return True
        
        # Check for common title/metadata patterns
        title_patterns = [
            r'[\u05d8][\u05f4\u05f3]\d+',  # Hebrew abbreviation + number (like ט׳2)
            r'\w+\s+\w+\s+\w+',  # 3+ words (likely a name or title)
            r'\d{1,2}\.\d{1,2}\.\d{2,4}',  # Date pattern
        ]
        
        for val in row:
            if val and str(val).strip():
                val_str = str(val).strip()
                for pattern in title_patterns:
                    if re.match(pattern, val_str):
                        return True
        
        return False
    
    # Find the expected column count by looking at the most common row length
    if len(rows) > 3:
        row_lengths = [len(row) for row in rows[1:]]
        from collections import Counter
        most_common_length = Counter(row_lengths).most_common(1)[0][0]
        print(f"📊 Expected column count based on data rows: {most_common_length}")
    else:
        most_common_length = len(rows[1]) if len(rows) > 1 else len(rows[0])
    
    # Check if any cell in first row contains embedded IDs
    first_row_has_embedded_ids = any(contains_embedded_id(val) for val in first_row)
    first_row_has_headers = has_header_like_content(first_row)
    first_row_is_title = is_title_or_metadata_row(first_row, most_common_length)
    
    # Check for column count mismatch (suggests first row is incomplete data, not headers)
    if len(rows) > 1:
        first_row_cols = len(first_row)
        
        print(f"📊 Column analysis: First row={first_row_cols} cols, Expected={most_common_length} cols")
        print(f"🔍 First row analysis: has_headers={first_row_has_headers}, is_title={first_row_is_title}, has_ids={first_row_has_ids}")
        
        # If first row appears to be a title/metadata row, look for real headers in subsequent rows
        if first_row_is_title or (first_row_cols < most_common_length and not first_row_has_headers):
            print(f"🔄 First row appears to be title/metadata, searching for real headers...")
            
            # Look for the actual header row in the next few rows
            for i in range(1, min(5, len(rows))):
                candidate_row = rows[i]
                if (len(candidate_row) >= most_common_length and 
                    has_header_like_content(candidate_row) and
                    not any(is_likely_id(val) for val in candidate_row)):
                    
                    print(f"✅ Found real headers in row {i}: {candidate_row}")
                    return i, candidate_row
            
            # If no clear headers found, create synthetic headers based on column count
            print(f"🔨 No clear headers found, creating synthetic headers for {most_common_length} columns")
            synthetic_headers = []
            for col_idx in range(most_common_length):
                if col_idx == 0:
                    synthetic_headers.append('Row Number')
                elif col_idx == 1:
                    synthetic_headers.append('Last Name')
                elif col_idx == 2:
                    synthetic_headers.append('First Name')
                elif col_idx == 3:
                    synthetic_headers.append('Address')
                elif col_idx == 4:
                    synthetic_headers.append('ID')
                else:
                    synthetic_headers.append(f'Column_{col_idx+1}')
            
            return 0, synthetic_headers  # Use row 0 but with synthetic headers
        
        # If first row has fewer columns than data rows AND contains embedded IDs, it's likely data
        if (first_row_cols < most_common_length and first_row_has_embedded_ids):
            print(f"🔄 First row appears to be incomplete data (embedded IDs + column mismatch): {first_row}")
            return -1, first_row  # Signal transposed table
    
    # If first row has IDs but no clear headers, treat all rows as data
    if (first_row_has_ids or first_row_has_embedded_ids) and not first_row_has_headers:
        print(f"🔄 Detected ID data in first row, treating all rows as data: {first_row}")
        return -1, first_row  # Signal transposed table
    
    # First, check if early rows contain Excel UI elements
    excel_ui_rows = []
    for i in range(min(3, len(rows))):
        if is_excel_ui_row(rows[i]):
            excel_ui_rows.append(i)
            print(f"🚫 Row {i} contains Excel UI elements: {rows[i][:2]}...")
    
    # Skip Excel UI rows and find the best header
    for i in range(min(5, len(rows))):
        if i not in excel_ui_rows and is_header_row(rows[i]):
            best_header_row = i
            print(f"✅ Found proper headers in row {i}: {rows[i]}")
            break
        elif i not in excel_ui_rows:
            # If it's not a UI row but also not clearly headers,
            # check if it contains mostly text (potential headers)
            text_cells = sum(1 for cell in rows[i] if str(cell).strip() and not str(cell).isdigit())
            if text_cells >= len(rows[i]) // 2:  # Most cells are text
                best_header_row = i
                print(f"📝 Using row {i} as headers (mostly text): {rows[i]}")
                break
    
    # If no clear headers found, check if table is transposed
    # (first row contains data that should be headers)
    first_row = rows[0]
    if len(first_row) > 0:
        # Check if first column contains IDs (suggesting transposed table)
        first_col_ids = 0
        for row in rows[1:6]:  # Check first 5 data rows
            if len(row) > 0 and is_likely_id(row[0]):
                first_col_ids += 1
        
        # If most first column values are IDs, table might be correct
        if first_col_ids >= min(3, len(rows) - 1):
            print("🔍 Table appears to have correct structure (IDs in first column)")
        else:
            # Check if table is transposed (headers are actually first row data)
            numeric_in_headers = sum(1 for cell in first_row if is_likely_id(cell))
            if numeric_in_headers > 0:
                print(f"⚠️  Detected transposed table: {numeric_in_headers} IDs in header row")
                # For transposed tables, we need special handling
                return -1, first_row  # Signal transposed table
    
    return best_header_row, rows[best_header_row] if best_header_row < len(rows) else []

def handle_transposed_table(table, json_file, cleanup=False):
    """Handle tables where first row contains data that became column headers"""
    print("🔧 Fixing transposed table structure...")
    
    # For transposed tables, we need to create proper structure
    # The 'rows' might be incorrectly structured
    all_rows = table['rows']
    
    # Try to detect if we have a simple case where we just need to 
    # treat the first row as data instead of headers
    if len(all_rows) >= 2:
        # Check if this looks like a simple case
        first_row = all_rows[0]
        
        # Create a synthetic header based on common patterns
        new_headers = []
        data_rows = []
        
        # Analyze first row to create appropriate headers
        for i, cell in enumerate(first_row):
            if is_likely_id(cell):
                new_headers.append('ID')
            elif i == len(first_row) - 1:  # Last column
                new_headers.append('Other')
            elif any(char.isalpha() for char in str(cell)):
                new_headers.append('Name')
            else:
                new_headers.append(f'Column_{i+1}')
        
        # Include all rows as data (no header row)
        data_rows = all_rows
        
        print(f"🔨 Created synthetic headers: {new_headers}")
        print(f"📊 Data rows: {len(data_rows)}")
        
        # Create the corrected table structure
        corrected_table = {
            'table_index': 0,
            'row_count': len(data_rows) + 1,  # +1 for header
            'column_count': len(new_headers),
            'rows': [new_headers] + data_rows,
            'metadata': {
                'original_headers': first_row,
                'corrected_headers': new_headers,
                'column_order': 'ID → Name → Others',
                'processed_by': 'extract_final_table.py (transposed fix)',
                'note': 'Table was transposed - first row data became headers'
            }
        }
        
        # Now process normally
        return process_corrected_table(corrected_table, json_file, cleanup)
    
    return None

def process_corrected_table(table, json_file, cleanup=False):
    """Process a corrected table structure"""
    rows = table['rows']
    headers = rows[0]  # First row is headers
    data_rows = rows[1:]  # Rest are data
    
    print(f"📊 Processing corrected table with headers: {headers}")
    
    # Smart column detection
    id_col = None
    name_col = None
    
    for i, header in enumerate(headers):
        h = str(header).lower().strip()
        if 'id' in h or 'תז' in h:
            id_col = i
        elif 'name' in h or 'שם' in h:
            name_col = i
    
    # If no clear ID column found, find the column with most ID-like values
    if id_col is None:
        for col_idx in range(len(headers)):
            id_count = 0
            for row in data_rows[:5]:  # Check first 5 rows
                if col_idx < len(row) and is_likely_id(row[col_idx]):
                    id_count += 1
            if id_count >= 3:  # Most values look like IDs
                id_col = col_idx
                headers[col_idx] = 'ID'  # Fix header
                break
    
    # Create new column order
    new_order = []
    if id_col is not None:
        new_order.append(id_col)
    
    # Add other columns
    for i in range(len(headers)):
        if i not in new_order:
            new_order.append(i)
    
    print(f"🔄 Column order: {[headers[i] for i in new_order]}")
    
    # Reorder all rows
    reordered_rows = [[headers[i] for i in new_order]]  # Header row
    for row in data_rows:
        new_row = [row[i] if i < len(row) else '' for i in new_order]
        reordered_rows.append(new_row)
    
    # Create final result
    result = {
        "table_index": 0,
        "row_count": len(reordered_rows),
        "column_count": len(headers),
        "rows": reordered_rows,
        "metadata": {
            "original_headers": table['metadata']['original_headers'],
            "reordered_headers": [headers[i] for i in new_order],
            "column_order": "ID → Others",
            "processed_by": "extract_final_table.py (corrected)",
            "correction_applied": True
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
    
    print(f"💾 Corrected table saved to: {output_file}")
    
    # Clean up input file if requested
    if cleanup and json_file != output_file:
        print(f"🗑️  Removing input file: {json_file}")
        os.remove(json_file)
    
    return output_file, result

def detect_collapsed_table_structure(table):
    """Detect if table structure has collapsed into a single cell"""
    if not table or not table.get('rows'):
        return False
    
    rows = table['rows']
    
    # Check if we have very few columns but very long content in first column
    if len(rows) > 0 and len(rows[0]) <= 2:  # Only 1-2 columns
        first_cell = rows[0][0] if rows[0] else ""
        
        # If first cell contains multiple lines that look like table data
        if isinstance(first_cell, str) and '\n' in first_cell:
            lines = first_cell.split('\n')
            
            # Look for patterns suggesting this should be a multi-column table
            # Pattern 1: ID numbers followed by names
            id_pattern_count = 0
            for line in lines:
                line = line.strip()
                if re.match(r'^\d{7,10}$', line):  # Line is just an ID number
                    id_pattern_count += 1
            
            # If we have many ID patterns, this is likely a collapsed table
            if id_pattern_count >= 5:
                print(f"🔍 Detected collapsed table structure: {id_pattern_count} ID patterns found")
                return True
    
    return False

def repair_collapsed_table_structure(table):
    """Repair a collapsed table structure by parsing the content"""
    print("🔧 REPAIRING COLLAPSED TABLE STRUCTURE")
    print("=" * 50)
    
    rows = table['rows']
    repaired_rows = []
    
    for row_idx, row in enumerate(rows):
        if not row or not row[0]:
            continue
            
        content = str(row[0]).strip()
        if not content:
            continue
            
        print(f"\n📝 Processing row {row_idx + 1} with {len(content)} characters")
        
        # Split content into lines
        lines = [line.strip() for line in content.split('\n') if line.strip()]
        
        if not lines:
            continue
            
        # Find header patterns
        header_start = None
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['ת.ז', 'id', 'שם פרטי', 'שם משפחה', 'first', 'last']):
                header_start = i
                break
        
        if header_start is not None:
            print(f"  📋 Found headers starting at line {header_start + 1}")
            
            # Look for the header pattern: ת.ז, שם פרטי, שם משפחה
            header_lines = []
            data_start = header_start
            
            # Collect header lines
            for i in range(header_start, min(header_start + 5, len(lines))):
                line = lines[i]
                if any(keyword in line.lower() for keyword in ['ת.ז', 'id', 'שם פרטי', 'שם משפחה', 'first', 'last']):
                    header_lines.append(line)
                    data_start = i + 1
                elif re.match(r'^\d{7,10}$', line):  # Hit an ID number - data starts here
                    break
                else:
                    data_start = i + 1
            
            # Create headers
            if len(header_lines) >= 3:
                headers = header_lines[:3]  # Take first 3 as ת.ז, שם פרטי, שם משפחה
            else:
                headers = ['ID', 'First Name', 'Last Name']  # Default headers
            
            print(f"  🏷️  Headers: {headers}")
            
            # Parse data rows
            data_lines = lines[data_start:]
            parsed_data = []
            
            i = 0
            while i < len(data_lines):
                # Look for ID pattern
                if i < len(data_lines) and re.match(r'^\d{7,10}$', data_lines[i]):
                    id_num = data_lines[i]
                    first_name = data_lines[i + 1] if i + 1 < len(data_lines) else ''
                    last_name = data_lines[i + 2] if i + 2 < len(data_lines) else ''
                    
                    # Skip row number if present
                    next_idx = i + 3
                    if (next_idx < len(data_lines) and 
                        data_lines[next_idx].isdigit() and 
                        len(data_lines[next_idx]) <= 2):
                        next_idx += 1  # Skip row number
                    
                    parsed_data.append([id_num, first_name, last_name])
                    print(f"    👤 {id_num} | {first_name} | {last_name}")
                    
                    i = next_idx
                else:
                    i += 1
            
            print(f"  ✅ Parsed {len(parsed_data)} data rows")
            
            # Add headers and data to repaired rows
            if not repaired_rows:  # First time, add headers
                repaired_rows.append(headers)
            
            repaired_rows.extend(parsed_data)
        
        else:
            print(f"  ⚠️  No clear headers found, treating as data continuation")
            
            # Try to parse as continuation of data
            lines = [line.strip() for line in content.split('\n') if line.strip()]
            
            parsed_data = []
            i = 0
            while i < len(lines):
                if i < len(lines) and re.match(r'^\d{7,10}$', lines[i]):
                    id_num = lines[i]
                    first_name = lines[i + 1] if i + 1 < len(lines) else ''
                    last_name = lines[i + 2] if i + 2 < len(lines) else ''
                    
                    # Skip row number if present
                    next_idx = i + 3
                    if (next_idx < len(lines) and 
                        lines[next_idx].isdigit() and 
                        len(lines[next_idx]) <= 2):
                        next_idx += 1
                    
                    parsed_data.append([id_num, first_name, last_name])
                    i = next_idx
                else:
                    i += 1
            
            repaired_rows.extend(parsed_data)
            print(f"  ✅ Parsed {len(parsed_data)} additional data rows")
    
    if repaired_rows:
        # Create the repaired table structure
        repaired_table = {
            'table_index': 0,
            'row_count': len(repaired_rows),
            'column_count': 3,  # ID, First Name, Last Name
            'rows': repaired_rows,
            'metadata': {
                'repair_applied': True,
                'repair_type': 'collapsed_structure',
                'original_structure': f"{table.get('row_count', 0)} rows x {table.get('column_count', 0)} cols",
                'repaired_structure': f"{len(repaired_rows)} rows x 3 cols",
                'data_rows_extracted': len(repaired_rows) - 1 if len(repaired_rows) > 1 else 0
            }
        }
        
        print(f"\n✅ REPAIR COMPLETE:")
        print(f"  Original: {table.get('row_count', 0)} rows x {table.get('column_count', 0)} cols")
        print(f"  Repaired: {len(repaired_rows)} rows x 3 cols")
        print(f"  Data rows: {len(repaired_rows) - 1 if len(repaired_rows) > 1 else 0}")
        
        return repaired_table
    
    return None

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
    
    # Check if table structure has collapsed and needs repair
    if detect_collapsed_table_structure(table):
        repaired_table = repair_collapsed_table_structure(table)
        if repaired_table:
            table = repaired_table  # Use the repaired table
        else:
            print("⚠️  Failed to repair collapsed table structure")
    
    # Analyze table structure
    header_row_idx, headers = detect_table_structure(table['rows'])
    
    if header_row_idx == -1:
        print("🔄 Handling transposed table - converting data back to proper format")
        # Handle transposed table where first row is actually data
        return handle_transposed_table(table, json_file, cleanup)
    
    print(f"📊 Using row {header_row_idx} as headers: {headers}")
    
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

