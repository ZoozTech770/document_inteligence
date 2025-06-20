#!/usr/bin/env python3
"""
Enhanced text pattern extraction for documents where Azure didn't detect tables
but the text contains structured data that can be parsed into tables
"""

import json
import os
import re
import sys
from collections import defaultdict
import pandas as pd

def detect_structured_patterns(text_content):
    """
    Detect structured patterns in text that could be converted to tables
    """
    patterns = {
        'list_with_id': {
            'pattern': r'(\d+)\s+([\u0590-\u05FF\s\w.-]+?)\s+([\d-]+)\s+(\d{7,10})',
            'headers': ['Row Number', 'Name', 'Phone', 'ID'],
            'description': 'Numbered list with Hebrew names, phone numbers, and ID numbers'
        },
        'name_phone_id': {
            'pattern': r'([\u0590-\u05FF\s\w.-]+?)\s+([\d-]+)\s+(\d{7,10})',
            'headers': ['Name', 'Phone', 'ID'],
            'description': 'Names with phone numbers and ID numbers'
        },
        'id_name_pattern': {
            'pattern': r'(\d{7,10})\s+([\u0590-\u05FF\s\w.-]+)',
            'headers': ['ID', 'Name'],
            'description': 'ID numbers followed by names'
        }
    }
    
    detected_patterns = []
    
    for pattern_name, pattern_info in patterns.items():
        matches = re.findall(pattern_info['pattern'], text_content, re.MULTILINE)
        if len(matches) >= 3:  # At least 3 matches to consider it a pattern
            detected_patterns.append({
                'name': pattern_name,
                'matches': matches,
                'count': len(matches),
                'headers': pattern_info['headers'],
                'description': pattern_info['description']
            })
    
    return detected_patterns

def convert_pattern_to_table(pattern_data):
    """Convert detected pattern to table format"""
    headers = pattern_data['headers']
    rows = [headers]  # Start with headers
    
    for match in pattern_data['matches']:
        if len(match) == len(headers):
            rows.append(list(match))
    
    return {
        'table_index': 0,
        'row_count': len(rows),
        'column_count': len(headers),
        'rows': rows,
        'metadata': {
            'pattern_type': pattern_data['name'],
            'description': pattern_data['description'],
            'extracted_from': 'text_pattern_analysis',
            'processed_by': 'enhance_text_extraction.py'
        }
    }

def process_no_table_files():
    """Process files that were marked as having no tables"""
    
    # Read the Excel file to get files with "No table data extracted"
    df = pd.read_excel('excel_results/ocr_results.xlsx')
    no_table_files = df[df['Error'] == 'No table data extracted']['Source File'].unique()
    
    print(f"Found {len(no_table_files)} files with 'No table data extracted'")
    print("Analyzing text content for structured patterns...\n")
    
    recovered_files = []
    
    for i, source_file in enumerate(no_table_files[:50]):  # Process first 50
        print(f"Processing {i+1}/50: {source_file}")
        
        # Find the corresponding OCR text file
        base_name = source_file.replace('.docx', '').replace('.pdf', '').replace('.png', '').replace('.jpg', '')
        
        # Find matching text files
        matching_text_files = []
        for txt_file in os.listdir('txt_result'):
            if txt_file.startswith(base_name) and txt_file.endswith('_ocr_results.txt'):
                matching_text_files.append(txt_file)
        
        if matching_text_files:
            txt_path = f"txt_result/{matching_text_files[0]}"
            try:
                with open(txt_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                # Extract only the document content (before analysis section)
                if "----Analyzing Read from page" in text_content:
                    document_content = text_content.split("----Analyzing Read from page")[0]
                else:
                    document_content = text_content
                
                # Remove "Document contains content:" prefix if present
                if "Document contains content:" in document_content:
                    document_content = document_content.split("Document contains content:")[1]
                
                # Detect patterns
                patterns = detect_structured_patterns(document_content.strip())
                
                if patterns:
                    # Use the pattern with the most matches
                    best_pattern = max(patterns, key=lambda x: x['count'])
                    print(f"  ✅ RECOVERED: Found {best_pattern['count']} rows using pattern '{best_pattern['name']}'")
                    print(f"     Description: {best_pattern['description']}")
                    
                    # Convert to table format
                    table_data = convert_pattern_to_table(best_pattern)
                    
                    # Generate output filename
                    hash_part = matching_text_files[0].split('-')[-1].replace('_ocr_results.txt', '')
                    output_file = f"json_result/{base_name}-{hash_part}_recovered_table.json"
                    
                    # Save the recovered table
                    with open(output_file, 'w', encoding='utf-8') as f:
                        json.dump([table_data], f, ensure_ascii=False, indent=2)
                    
                    recovered_files.append({
                        'source_file': source_file,
                        'output_file': output_file,
                        'pattern': best_pattern['name'],
                        'row_count': best_pattern['count'],
                        'headers': best_pattern['headers']
                    })
                    
                    print(f"     Saved to: {output_file}")
                else:
                    print(f"  ❌ No structured patterns detected")
                    
            except Exception as e:
                print(f"  ❌ Error reading text file: {e}")
        else:
            print(f"  ❓ No matching text file found")
        
        print()
    
    print("="*60)
    print(f"RECOVERY SUMMARY:")
    print(f"  Files processed: {min(50, len(no_table_files))}")
    print(f"  Tables recovered: {len(recovered_files)}")
    
    if recovered_files:
        print(f"\nRecovered files:")
        for file_info in recovered_files:
            print(f"  {file_info['source_file']}")
            print(f"    → {file_info['row_count']} rows with headers: {file_info['headers']}")
            print(f"    → Pattern: {file_info['pattern']}")
            print()
    
    return recovered_files

def run_extraction_on_recovered_files(recovered_files):
    """Run the final table extraction on recovered files"""
    print("Running final table extraction on recovered files...\n")
    
    successful_extractions = 0
    
    for file_info in recovered_files:
        print(f"Processing: {file_info['source_file']}")
        
        try:
            # Run the extract_final_table script
            import subprocess
            result = subprocess.run([
                'python3', 'extract_final_table.py', file_info['output_file']
            ], capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"  ✅ Successfully extracted final table")
                successful_extractions += 1
            else:
                print(f"  ❌ Final extraction failed: {result.stderr.strip()}")
                
        except Exception as e:
            print(f"  ❌ Error during final extraction: {e}")
    
    print(f"\nFinal extraction completed: {successful_extractions}/{len(recovered_files)} successful")

if __name__ == "__main__":
    print("Enhanced Text Pattern Extraction")
    print("="*50)
    
    recovered_files = process_no_table_files()
    
    if recovered_files:
        print(f"\nWould you like to run final table extraction on the {len(recovered_files)} recovered files? (y/n)")
        response = input().strip().lower()
        if response == 'y':
            run_extraction_on_recovered_files(recovered_files)
    else:
        print("No files were recovered with structured patterns.")

