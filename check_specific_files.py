#!/usr/bin/env python3

import subprocess
import sys
from pathlib import Path
import json
import os

def check_file(file_path):
    """Check a specific file for tables"""
    if not os.path.exists(file_path):
        return f"❌ File not found: {file_path}"
    
    print(f"🔍 Analyzing: {os.path.basename(file_path)}")
    
    # Run OCR analysis
    cmd = [sys.executable, 'sample_analyze_read.py', file_path, '--json']
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        if result.returncode != 0:
            return f"❌ OCR failed: {result.stderr.strip()}"
        
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
                    table_count = len(data['tables'])
                    total_cells = sum(len(table.get('cells', [])) for table in data['tables'])
                    return f"✅ FOUND {table_count} table(s) with {total_cells} total cells!"
                else:
                    return "✅ Confirmed: No tables detected"
                    
            except Exception as e:
                return f"❌ Error reading results: {e}"
        else:
            return "✅ Confirmed: No tables detected"
            
    except subprocess.TimeoutExpired:
        return "❌ Timeout during analysis"
    except Exception as e:
        return f"❌ Unexpected error: {e}"

def main():
    print("🔍 CHECKING SPECIFIC FILES FOR HIDDEN TABLES")
    print("=" * 60)
    
    # List of specific files that were marked as having no tables
    # These are the files we saw in the processing output
    test_files = [
        "files/תמונות/12.9-06AVg00000BpcLJMAZ.png",
        "files/תמונות/16.9-06AVg00000BySfsMAF.png", 
        "files/תמונות/20.2.24 הבינ'ל ת'א-06AVg000002MfzSMAS.jpg",
        "files/תמונות/27.8-06AVg00000B3CbLMAV.png",
        "files/תמונות/WhatsApp Image 2024-02-15 at 12.45.01-06AVg000002NIpbMAG.jpeg",
        "files/תמונות/26.2.24 ראשית בנות תל אביב- הסעה-06AVg000002ikysMAA.jpg",
        "files/תמונות/WhatsApp Image 2024-02-19 at 09.19.23-06AVg000002U2V3MAK.jpeg",
        "files/תמונות/WhatsApp Image 2024-02-26 at 13.39.12-06AVg000002p9jLMAQ.jpeg",
        "files/תמונות/WhatsApp Image 2024-02-28 at 14.41.47-06AVg000002qBhWMAU.jpeg",
        "files/תמונות/WhatsApp Image 2024-03-04 at 12.12.27-06AVg0000031d49MAA.jpeg"
    ]
    
    print(f"Testing {len(test_files)} files that were marked as having no tables...\n")
    
    found_tables = []
    confirmed_no_tables = []
    errors = []
    
    for i, file_path in enumerate(test_files, 1):
        print(f"[{i}/{len(test_files)}] {os.path.basename(file_path)}")
        result = check_file(file_path)
        print(f"  {result}")
        
        if "FOUND" in result:
            found_tables.append(file_path)
        elif "Confirmed" in result:
            confirmed_no_tables.append(file_path)
        else:
            errors.append((file_path, result))
        
        print()
    
    # Summary
    print("=" * 60)
    print("📊 SUMMARY")
    print("=" * 60)
    print(f"✅ Files with NEWLY DISCOVERED tables: {len(found_tables)}")
    if found_tables:
        for file_path in found_tables:
            print(f"  • {os.path.basename(file_path)}")
    
    print(f"\n✅ Files confirmed to have no tables: {len(confirmed_no_tables)}")
    print(f"❌ Files with errors: {len(errors)}")
    
    if found_tables:
        print(f"\n🎉 DISCOVERY: Found tables in {len(found_tables)} files that were previously marked as having no tables!")
        print("These files should be reprocessed through the batch system.")
    else:
        print(f"\n✅ VERIFICATION COMPLETE: All tested files confirmed to have no table data.")
        print("The 'no table' cache results appear to be accurate.")

if __name__ == "__main__":
    main()

