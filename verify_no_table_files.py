#!/usr/bin/env python3

import pandas as pd
import json
import subprocess
import sys
from pathlib import Path
import os

def find_error_files_from_excel():
    """Find files that had errors from the Excel output"""
    excel_file = "excel_results/ocr_results.xlsx"
    
    if not os.path.exists(excel_file):
        print(f"❌ Excel file not found: {excel_file}")
        return []
    
    try:
        # Read the Excel file
        df = pd.read_excel(excel_file)
        
        # Find rows with errors
        error_rows = df[df['Error'].notna()]
        error_files = error_rows['Source File'].tolist()
        
        print(f"📊 Found {len(error_files)} files with errors in Excel:")
        for i, file in enumerate(error_files[:10]):  # Show first 10
            print(f"  {i+1}. {file}")
        if len(error_files) > 10:
            print(f"  ... and {len(error_files) - 10} more")
        
        return error_files
        
    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return []

def find_cached_no_table_files():
    """Find files that were cached as having no table data"""
    json_folder = Path("json_result")
    no_table_files = []
    
    if not json_folder.exists():
        print("❌ json_result folder not found")
        return []
    
    # Look for final_table.json files with no_table_data metadata
    for json_file in json_folder.glob("*_final_table.json"):
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Check if this indicates no table data
            if (isinstance(data, list) and len(data) > 0 and 
                data[0].get('metadata', {}).get('no_table_data', False)):
                # Extract original filename from cached filename
                cache_name = json_file.stem
                # Remove the hash suffix and _final_table
                original_name = cache_name.split('-')[0]  # This is rough, but should work for most
                no_table_files.append((original_name, str(json_file)))
                
        except Exception as e:
            print(f"⚠️  Error reading {json_file}: {e}")
    
    print(f"📋 Found {len(no_table_files)} cached 'no table' files:")
    for i, (file, cache) in enumerate(no_table_files[:10]):
        print(f"  {i+1}. {file}")
    
    return no_table_files

def re_analyze_file(file_path):
    """Re-analyze a file using the OCR script"""
    if not os.path.exists(file_path):
        return None, f"File not found: {file_path}"
    
    print(f"🔍 Re-analyzing: {os.path.basename(file_path)}")
    
    # Run OCR analysis
    cmd = [sys.executable, 'sample_analyze_read.py', file_path, '--json']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            error_msg = result.stderr.strip() if result.stderr else "Unknown error"
            return None, f"OCR failed: {error_msg}"
        
        # Check if JSON file was created
        base_name = Path(file_path).stem
        json_file = Path(f"{base_name}_tables.json")
        
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Clean up
                json_file.unlink()
                ocr_file = Path(f"{base_name}_ocr_results.txt")
                if ocr_file.exists():
                    ocr_file.unlink()
                
                # Check if tables were found
                if 'tables' in data and len(data['tables']) > 0:
                    return data['tables'], None
                else:
                    return None, "No tables detected by OCR"
                    
            except Exception as e:
                return None, f"Error reading OCR results: {e}"
        else:
            return None, "No OCR output file generated"
            
    except subprocess.TimeoutExpired:
        return None, "OCR timeout"
    except Exception as e:
        return None, f"Unexpected error: {e}"

def main():
    print("🔍 VERIFYING FILES MARKED AS 'NO TABLE DATA'")
    print("=" * 60)
    
    # Get files that had errors from Excel
    error_files = find_error_files_from_excel()
    
    # Get files that were cached as having no table data
    cached_no_table_files = find_cached_no_table_files()
    
    # Combine and deduplicate
    all_problem_files = set(error_files)
    for file, _ in cached_no_table_files:
        all_problem_files.add(file)
    
    print(f"\n📝 Total unique files to verify: {len(all_problem_files)}")
    
    # Ask user which files to re-verify
    print("\nOptions:")
    print("1. Re-verify all files")
    print("2. Re-verify first 10 files")
    print("3. Re-verify specific files")
    print("4. Exit")
    
    choice = input("\nEnter your choice (1-4): ").strip()
    
    files_to_verify = []
    
    if choice == "1":
        files_to_verify = list(all_problem_files)
    elif choice == "2":
        files_to_verify = list(all_problem_files)[:10]
    elif choice == "3":
        print("\nEnter file numbers to verify (comma-separated):")
        file_list = list(all_problem_files)
        for i, file in enumerate(file_list, 1):
            print(f"  {i}. {file}")
        
        try:
            selected = input("\nNumbers: ").strip()
            if selected:
                indices = [int(x.strip()) - 1 for x in selected.split(',')]
                files_to_verify = [file_list[i] for i in indices if 0 <= i < len(file_list)]
        except ValueError:
            print("❌ Invalid input")
            return
    elif choice == "4":
        return
    else:
        print("❌ Invalid choice")
        return
    
    if not files_to_verify:
        print("❌ No files selected for verification")
        return
    
    print(f"\n🔄 Re-verifying {len(files_to_verify)} files...")
    print("=" * 60)
    
    results = []
    
    for i, filename in enumerate(files_to_verify, 1):
        print(f"\n[{i}/{len(files_to_verify)}] Checking: {filename}")
        
        # Find the actual file path
        possible_paths = [
            f"files/תמונות/{filename}",
            f"files/PDF/{filename}",
            f"files/וורד/{filename}",
            f"files/קבצי אינטרנט/{filename}",
        ]
        
        file_path = None
        for path in possible_paths:
            if os.path.exists(path):
                file_path = path
                break
        
        if not file_path:
            print(f"  ❌ File not found in any expected location")
            results.append({
                'filename': filename,
                'status': 'file_not_found',
                'message': 'File not found in expected locations'
            })
            continue
        
        # Re-analyze the file
        tables, error = re_analyze_file(file_path)
        
        if error:
            print(f"  ❌ {error}")
            results.append({
                'filename': filename,
                'status': 'error',
                'message': error
            })
        elif tables:
            print(f"  ✅ FOUND TABLES! ({len(tables)} table(s))")
            # Show summary of found tables
            for j, table in enumerate(tables):
                row_count = len(table.get('cells', []))
                print(f"    Table {j+1}: {row_count} cells")
            
            results.append({
                'filename': filename,
                'status': 'tables_found',
                'table_count': len(tables),
                'message': f'Found {len(tables)} table(s)'
            })
        else:
            print(f"  ✅ Confirmed: No tables detected")
            results.append({
                'filename': filename,
                'status': 'no_tables_confirmed',
                'message': 'No tables detected (confirmed)'
            })
    
    # Summary
    print(f"\n📊 VERIFICATION SUMMARY")
    print("=" * 60)
    
    found_tables = [r for r in results if r['status'] == 'tables_found']
    confirmed_no_tables = [r for r in results if r['status'] == 'no_tables_confirmed']
    errors = [r for r in results if r['status'] == 'error']
    not_found = [r for r in results if r['status'] == 'file_not_found']
    
    print(f"✅ Files where tables were FOUND: {len(found_tables)}")
    if found_tables:
        for result in found_tables:
            print(f"  • {result['filename']} - {result['message']}")
    
    print(f"\n✅ Files confirmed to have no tables: {len(confirmed_no_tables)}")
    print(f"❌ Files with errors: {len(errors)}")
    print(f"❓ Files not found: {len(not_found)}")
    
    if found_tables:
        print(f"\n🎉 DISCOVERY: {len(found_tables)} files originally marked as 'no table' actually contain tables!")
        print("These files should be reprocessed to extract their table data.")
        
        # Ask if user wants to reprocess these files
        reprocess = input(f"\nWould you like to reprocess these {len(found_tables)} files now? (y/n): ").strip().lower()
        if reprocess == 'y':
            print("\n🔄 Reprocessing files with discovered tables...")
            for result in found_tables:
                filename = result['filename']
                print(f"\nReprocessing: {filename}")
                # Here you could call the batch processor on just these files
                # For now, just show the command they should run
                print(f"  Command: python batch_ocr_processor.py (select files with {filename})")

if __name__ == "__main__":
    main()

