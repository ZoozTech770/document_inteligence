#!/usr/bin/env python3
"""
Test all files that failed table extraction to identify causes
"""

import pandas as pd
import json
import os
import subprocess
import sys

def test_failed_extractions():
    """Test all files that had extraction failures"""
    
    # Read the Excel file to get files with errors
    df = pd.read_excel('excel_results/ocr_results.xlsx')
    
    # Get files with "Table extraction failed" errors
    failed_extractions = df[df['Error'].str.contains('Table extraction failed', na=False)]
    
    print(f"Found {len(failed_extractions)} files with table extraction failures")
    print(f"Found {len(df[df['Error'] == 'No table data extracted'])} files with 'No table data extracted'")
    
    # Test a sample of failed extractions
    fixed_count = 0
    still_failing_count = 0
    no_table_count = 0
    
    failed_files = failed_extractions['Source File'].unique()
    
    print(f"\nTesting {min(20, len(failed_files))} failed extraction files...\n")
    
    for i, source_file in enumerate(failed_files[:20]):  # Test first 20
        print(f"Testing {i+1}/20: {source_file}")
        
        # Find the corresponding JSON file
        # Extract the hash from the error message in the same row
        error_msg = failed_extractions[failed_extractions['Source File'] == source_file]['Error'].iloc[0]
        
        # Extract JSON filename from error message
        if 'extract_final_table.py' in error_msg:
            # Parse: "Command '[path, 'extract_final_table.py', 'filename.json', '--cleanup']'"
            parts = error_msg.split("'")  
            if len(parts) >= 6:
                json_filename = parts[5]  # The filename is usually the 3rd argument
                json_path = f"json_result/{json_filename}"
            else:
                print(f"  ❓ Could not parse JSON filename from error: {error_msg}")
                continue
            
            if os.path.exists(json_path):
                # Try to run the extract script
                try:
                    result = subprocess.run([
                        'python3', 'extract_final_table.py', json_path
                    ], capture_output=True, text=True, timeout=30)
                    
                    if result.returncode == 0:
                        print(f"  ✅ FIXED: Now extracts successfully")
                        fixed_count += 1
                    else:
                        print(f"  ❌ Still failing: {result.stderr.strip()}")
                        still_failing_count += 1
                        
                except subprocess.TimeoutExpired:
                    print(f"  ⏰ Timeout")
                    still_failing_count += 1
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    still_failing_count += 1
            else:
                print(f"  ❓ JSON file not found: {json_path}")
                
        print()
    
    print("="*60)
    print(f"SUMMARY of tested files:")
    print(f"  Fixed (now working): {fixed_count}")
    print(f"  Still failing: {still_failing_count}")
    print(f"  Total tested: {fixed_count + still_failing_count}")
    
    # Now test some "No table data extracted" files to verify they truly have no tables
    print(f"\nNow testing files that reported 'No table data extracted'...")
    
    no_table_files = df[df['Error'] == 'No table data extracted']['Source File'].unique()
    
    verified_no_tables = 0
    actually_have_tables = 0
    
    print(f"Testing {min(10, len(no_table_files))} 'no table' files...\n")
    
    for i, source_file in enumerate(no_table_files[:10]):  # Test first 10
        print(f"Checking {i+1}/10: {source_file}")
        
        # Try to find the corresponding tables.json file
        # Remove .docx and find matching files
        base_name = source_file.replace('.docx', '').replace('.pdf', '').replace('.png', '').replace('.jpg', '')
        
        # Find matching JSON files
        matching_files = []
        for json_file in os.listdir('json_result'):
            if json_file.startswith(base_name) and json_file.endswith('_tables.json'):
                matching_files.append(json_file)
        
        if matching_files:
            json_path = f"json_result/{matching_files[0]}"
            try:
                with open(json_path, 'r', encoding='utf-8') as f:
                    tables_data = json.load(f)
                
                if isinstance(tables_data, dict) and tables_data.get('no_tables_detected'):
                    print(f"  ✅ VERIFIED: Truly has no tables")
                    verified_no_tables += 1
                elif isinstance(tables_data, list) and len(tables_data) == 0:
                    print(f"  ✅ VERIFIED: Empty tables array")
                    verified_no_tables += 1
                elif isinstance(tables_data, list) and len(tables_data) > 0:
                    print(f"  ❗ POTENTIAL ISSUE: Has {len(tables_data)} tables but reported no tables")
                    actually_have_tables += 1
                    # Show first few cells of first table
                    if tables_data[0].get('rows'):
                        first_row = tables_data[0]['rows'][0][:3]
                        print(f"    First row sample: {first_row}")
                else:
                    print(f"  ❓ Unexpected structure: {type(tables_data)}")
                    
            except Exception as e:
                print(f"  ❌ Error reading JSON: {e}")
        else:
            print(f"  ❓ No matching JSON file found")
            
        print()
    
    print("="*60)
    print(f"SUMMARY of 'no table' verification:")
    print(f"  Verified no tables: {verified_no_tables}")
    print(f"  Actually have tables: {actually_have_tables}")
    print(f"  Total checked: {verified_no_tables + actually_have_tables}")

if __name__ == "__main__":
    test_failed_extractions()

