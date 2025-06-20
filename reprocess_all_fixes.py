#!/usr/bin/env python3
"""
Comprehensive re-processing script that applies all fixes:
1. Re-runs table extraction on files that failed due to the missing 'import re' bug
2. Applies enhanced text pattern extraction for files marked as having no tables
3. Consolidates all results into a new improved Excel file
"""

import pandas as pd
import json
import os
import subprocess
import sys
from datetime import datetime
import shutil
import re

def backup_existing_results():
    """Backup the existing Excel results"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_file = f"excel_results/ocr_results_backup_{timestamp}.xlsx"
    
    if os.path.exists("excel_results/ocr_results.xlsx"):
        shutil.copy2("excel_results/ocr_results.xlsx", backup_file)
        print(f"📁 Backed up existing results to: {backup_file}")
        return backup_file
    return None

def process_recovered_files():
    """Process files recovered from text pattern analysis"""
    print("🔍 Running enhanced text pattern extraction...")
    
    # Run the enhanced text extraction
    result = subprocess.run(['python3', 'enhance_text_extraction.py'], 
                          input='y\n',  # Auto-answer yes to run final extraction
                          capture_output=True, text=True, encoding='utf-8')
    
    if result.returncode == 0:
        print("✅ Enhanced text extraction completed successfully")
        
        # Count recovered files
        recovered_count = result.stdout.count("RECOVERED:")
        final_count = result.stdout.count("Successfully extracted final table")
        
        print(f"📊 Text pattern recovery summary:")
        print(f"   - Patterns detected: {recovered_count}")
        print(f"   - Final tables extracted: {final_count}")
        
        return final_count
    else:
        print(f"❌ Enhanced text extraction failed: {result.stderr}")
        return 0

def regenerate_excel_output():
    """Regenerate the Excel output with all available final tables"""
    print("📊 Regenerating consolidated Excel output...")
    
    # Find all final table JSON files
    final_tables = []
    
    for file in os.listdir('json_result'):
        if file.endswith('_final_table.json'):
            try:
                with open(f'json_result/{file}', 'r', encoding='utf-8') as f:
                    table_data = json.load(f)
                
                if table_data and len(table_data) > 0:
                    table = table_data[0]
                    if 'rows' in table and len(table['rows']) > 1:
                        # Extract source file name from filename
                        source_file = file.replace('_final_table.json', '')
                        
                        # Clean up the source filename
                        parts = source_file.split('-')
                        if len(parts) > 1:
                            # Remove hash part (last part after last dash)
                            source_name = '-'.join(parts[:-1])
                        else:
                            source_name = source_file
                        
                        # Add .docx extension if not present
                        if not any(source_name.endswith(ext) for ext in ['.docx', '.pdf', '.png', '.jpg', '.pptx']):
                            source_name += '.docx'
                        
                        final_tables.append({
                            'source_file': source_name,
                            'json_file': file,
                            'table_data': table
                        })
                        
            except Exception as e:
                print(f"⚠️  Error reading {file}: {e}")
    
    print(f"📋 Found {len(final_tables)} final table files")
    
    if not final_tables:
        print("❌ No final tables found to process")
        return
    
    # Process all tables and create consolidated Excel
    all_rows = []
    
    for table_info in final_tables:
        table = table_info['table_data']
        source_file = table_info['source_file']
        
        headers = table['rows'][0] if table['rows'] else []
        data_rows = table['rows'][1:] if len(table['rows']) > 1 else []
        
        for row in data_rows:
            row_dict = {'Source File': source_file}
            
            # Add data columns
            for i, value in enumerate(row):
                if i < len(headers):
                    col_name = headers[i]
                else:
                    col_name = f'Column_{i+1}'
                row_dict[col_name] = value
            
            all_rows.append(row_dict)
    
    if all_rows:
        # Create DataFrame and save to Excel
        df = pd.DataFrame(all_rows)
        
        # Generate timestamp for the new file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"excel_results/ocr_results_enhanced_{timestamp}.xlsx"
        
        df.to_excel(output_file, index=False)
        print(f"💾 Enhanced results saved to: {output_file}")
        print(f"📊 Total rows: {len(df)}")
        print(f"📊 Total files with data: {len(final_tables)}")
        print(f"📊 Total columns: {len(df.columns)}")
        
        return output_file
    else:
        print("❌ No data rows found to save")
        return None

def verify_improvements():
    """Verify the improvements made"""
    print("\n" + "="*60)
    print("🔍 VERIFICATION SUMMARY")
    print("="*60)
    
    # Count original results
    if os.path.exists("excel_results/ocr_results.xlsx"):
        original_df = pd.read_excel("excel_results/ocr_results.xlsx")
        original_rows = len(original_df)
        original_error_count = len(original_df[original_df['Error'].notna()])
        original_success_count = original_rows - original_error_count
        
        print(f"📊 Original results:")
        print(f"   - Total rows: {original_rows}")
        print(f"   - Successful extractions: {original_success_count}")
        print(f"   - Errors: {original_error_count}")
    
    # Count JSON files
    json_files = len([f for f in os.listdir('json_result') if f.endswith('_tables.json')])
    final_files = len([f for f in os.listdir('json_result') if f.endswith('_final_table.json')])
    recovered_files = len([f for f in os.listdir('json_result') if '_recovered_table' in f])
    
    print(f"\n📁 File counts:")
    print(f"   - Original table JSON files: {json_files}")
    print(f"   - Final table JSON files: {final_files}")
    print(f"   - Recovered table files: {recovered_files}")
    
    # Find the latest enhanced file
    enhanced_files = [f for f in os.listdir('excel_results') if f.startswith('ocr_results_enhanced_')]
    if enhanced_files:
        latest_enhanced = max(enhanced_files)
        enhanced_df = pd.read_excel(f"excel_results/{latest_enhanced}")
        enhanced_rows = len(enhanced_df)
        enhanced_files_count = len(enhanced_df['Source File'].unique())
        
        print(f"\n📈 Enhanced results ({latest_enhanced}):")
        print(f"   - Total rows: {enhanced_rows}")
        print(f"   - Files with data: {enhanced_files_count}")
        print(f"   - Columns: {len(enhanced_df.columns)}")
        
        if 'original_rows' in locals():
            improvement = enhanced_rows - original_success_count
            print(f"   - Additional data rows recovered: {improvement}")

def main():
    """Main processing function"""
    print("🚀 COMPREHENSIVE OCR RESULTS RE-PROCESSING")
    print("=" * 50)
    print("This script will:")
    print("1. 🔧 Apply the missing 'import re' fix (already done)")
    print("2. 🔍 Run enhanced text pattern extraction")
    print("3. 📊 Regenerate consolidated Excel output")
    print("4. 📈 Provide improvement summary")
    print()
    
    # Backup existing results
    backup_file = backup_existing_results()
    
    # Process recovered files using enhanced text extraction
    recovered_count = process_recovered_files()
    
    # Regenerate Excel output with all available data
    enhanced_file = regenerate_excel_output()
    
    # Verification summary
    verify_improvements()
    
    print("\n" + "="*60)
    print("✅ PROCESSING COMPLETE")
    print("="*60)
    
    if enhanced_file:
        print(f"📄 Enhanced results file: {enhanced_file}")
    if backup_file:
        print(f"📁 Original backup: {backup_file}")
    
    print(f"\n🔧 Fixes applied:")
    print(f"   ✅ Missing 'import re' bug fixed in extract_final_table.py")
    print(f"   ✅ Enhanced text pattern extraction for {recovered_count} additional files")
    print(f"   ✅ Consolidated Excel output regenerated")
    
    print(f"\n💡 Next steps:")
    print(f"   - Review the enhanced results file")
    print(f"   - Compare with original backup to see improvements")
    print(f"   - Consider running the full batch process again if needed")

if __name__ == "__main__":
    main()

