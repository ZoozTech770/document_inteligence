#!/usr/bin/env python3
"""
Batch OCR Processor for Multiple PDF Files
Processes all PDF files in 'files' directory and outputs to Excel
"""

import os
import sys
import json
import argparse
import subprocess
from pathlib import Path
import pandas as pd
from typing import List, Dict, Any
from datetime import datetime
import re
from column_normalizer import ColumnNormalizer

def is_likely_data(value):
    """Examine value to determine if it looks like data rather than a header"""
    if not value:
        return False
    
    value_str = str(value).strip()
    
    # Check for date patterns (common data that becomes column headers)
    if re.match(r'\d{1,2}/\d{1,2}/\d{2,4}', value_str):  # MM/DD/YYYY or DD/MM/YYYY
        return True
    if re.match(r'\d{4}-\d{2}-\d{2}', value_str):  # YYYY-MM-DD
        return True
    if re.match(r'\d{1,2}\.\d{1,2}\.\d{2,4}', value_str):  # DD.MM.YYYY
        return True
    
    # Check for ID numbers (should not be column headers)
    if re.match(r'^\d{7,12}$', value_str):  # 7-12 digit numbers (IDs)
        return True
    
    # Check for phone numbers
    if re.match(r'^\d{3}-\d{3}-\d{4}$', value_str) or re.match(r'^\d{10}$', value_str):
        return True
    
    # Check for multiple Hebrew/English names (like "ליאל גניש ואוהד שמח")
    hebrew_words = re.findall(r'[\u0590-\u05FF]+', value_str)
    if len(hebrew_words) >= 3:  # Multiple Hebrew names
        return True
    
    # Check for "ו" (Hebrew "and") which suggests multiple names
    if 'ו' in value_str and len(hebrew_words) >= 2:
        return True
    
    # Check for very long text (more than 25 characters) - likely content
    if len(value_str) > 25:
        return True
    
    # Check for common data separators like "|" or "," with meaningful content
    if ('|' in value_str or ',' in value_str) and len(value_str) > 8:
        return True
    
    # Check for common OCR artifacts that are clearly not headers
    ocr_artifacts = ['V(PINVIS', 'Nd DOIS', 'Good Neutral', ':selected:', ':unselected:']
    if any(artifact in value_str for artifact in ocr_artifacts):
        return True
    
    return False

def clean_and_normalize_headers(headers):
    """Logic for filtering and normalizing headers by excluding likely data rows"""
    valid_headers = []
    
    for header in headers:
        if not header or is_likely_data(header):
            # Replace invalid headers with generic column names
            valid_headers.append('')  # Will be handled later as Column_N
        else:
            # Clean and normalize valid header
            header_str = str(header).strip()
            
            # Remove common OCR artifacts from valid headers
            header_str = re.sub(r':selected:', '', header_str)
            header_str = re.sub(r':unselected:', '', header_str)
            header_str = re.sub(r'\n+', ' ', header_str)
            header_str = re.sub(r'\s+', ' ', header_str)
            header_str = header_str.strip()
            
            valid_headers.append(header_str if header_str else '')
    
    return valid_headers

def find_folders_in_directory(directory: str) -> List[Path]:
    """Find all folders in the given directory"""
    base_path = Path(directory)
    folders = []
    
    # Add root directory if it contains files
    root_files = [f for f in base_path.iterdir() if f.is_file() and is_supported_file(f)]
    if root_files:
        folders.append(base_path)
    
    # Add subdirectories that contain supported files
    for item in base_path.iterdir():
        if item.is_dir():
            # Check if this folder or any subfolder contains supported files
            supported_files = list(item.rglob('*'))
            supported_files = [f for f in supported_files if f.is_file() and is_supported_file(f)]
            if supported_files:
                folders.append(item)
    
    return sorted(folders)

def is_supported_file(file_path: Path) -> bool:
    """Check if file is supported by Azure Document Intelligence"""
    supported_extensions = {
        '.pdf', '.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif',
        '.html', '.htm', '.docx', '.pptx', '.xlsx'
    }
    
    # Check file extension
    if file_path.suffix.lower() not in supported_extensions:
        return False
    
    # Exclude error files and obvious junk
    filename = file_path.name.lower()
    
    # Skip error files
    if '_error.txt' in filename or 'error' in filename:
        return False
    
    # Skip system files
    if filename.startswith('.') or filename.startswith('~'):
        return False
    
    # Skip temp files
    if 'temp' in filename or 'tmp' in filename:
        return False
    
    # Skip files that are clearly not documents
    if any(skip in filename for skip in ['___all_errors', 'backup', 'copy']):
        return False
    
    return True

def find_files_in_folders(folders: List[Path]) -> List[Path]:
    """Find all supported files in the selected folders"""
    all_files = []
    for folder in folders:
        for file_path in folder.rglob('*'):
            if file_path.is_file() and is_supported_file(file_path):
                all_files.append(file_path)
    return sorted(all_files)

def display_folders_for_selection(folders: List[Path], base_dir: Path) -> List[Path]:
    """Display folders and let user select which ones to process"""
    if not folders:
        print("No folders with supported files found in directory.")
        return []
    
    print("\nFound folders with supported files:")
    print("=" * 60)
    
    for i, folder_path in enumerate(folders, 1):
        rel_path = folder_path.relative_to(base_dir.parent) if folder_path != base_dir else folder_path.name
        
        # Count files in this folder
        file_count = len([f for f in folder_path.rglob('*') if f.is_file() and is_supported_file(f)])
        
        print(f"{i:2d}. {rel_path} ({file_count} files)")
    
    print("\nSelection options:")
    print("- Enter specific numbers (e.g., 1,3,5)")
    print("- Enter range (e.g., 1-5)")
    print("- Enter 'all' to process all folders")
    print("- Press Enter to exit")
    
    selection = input("\nYour selection: ").strip()
    
    if not selection:
        return []
    
    if selection.lower() == 'all':
        return folders
    
    selected_folders = []
    
    # Parse selection
    try:
        parts = selection.split(',')
        for part in parts:
            part = part.strip()
            if '-' in part:
                # Range selection
                start, end = map(int, part.split('-'))
                for i in range(start, end + 1):
                    if 1 <= i <= len(folders):
                        selected_folders.append(folders[i - 1])
            else:
                # Individual selection
                i = int(part)
                if 1 <= i <= len(folders):
                    selected_folders.append(folders[i - 1])
    except ValueError:
        print("Invalid selection format. Please try again.")
        return []
    
    return list(set(selected_folders))  # Remove duplicates

def create_result_folders():
    """Create result folders if they don't exist"""
    json_folder = Path("json_result")
    txt_folder = Path("txt_result")
    excel_folder = Path("excel_results")
    temp_folder = Path("temp_results")
    error_folder = Path("error_files")
    
    json_folder.mkdir(exist_ok=True)
    txt_folder.mkdir(exist_ok=True)
    excel_folder.mkdir(exist_ok=True)
    temp_folder.mkdir(exist_ok=True)
    error_folder.mkdir(exist_ok=True)
    
    return json_folder, txt_folder, excel_folder, temp_folder, error_folder

def get_file_hash(file_path):
    """Generate a hash for the file to create unique identifier"""
    import hashlib
    hasher = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def check_cached_results(file_path: Path, json_folder: Path, txt_folder: Path):
    """Check if we already have cached results for this file"""
    base_name = file_path.stem
    file_hash = get_file_hash(file_path)
    hash_suffix = file_hash[:8]
    
    # First check temp_results directory with simple naming
    temp_folder = Path("temp_results")
    if temp_folder.exists():
        temp_json = temp_folder / f"{base_name}_tables.json"
        temp_txt = temp_folder / f"{base_name}_ocr_results.txt"
        
        if temp_json.exists():
            # Found in temp_results, create a dummy final file path
            temp_final = temp_folder / f"{base_name}_final_table.json"
            return temp_json, temp_txt, temp_final, file_hash
    
    # Fallback: Look for existing files with hash pattern in cache folders
    json_pattern = f"{base_name}-{hash_suffix}_tables.json"
    txt_pattern = f"{base_name}-{hash_suffix}_ocr_results.txt"
    final_pattern = f"{base_name}-{hash_suffix}_final_table.json"
    
    json_file = json_folder / json_pattern
    txt_file = txt_folder / txt_pattern
    final_file = json_folder / final_pattern
    
    if json_file.exists() and txt_file.exists():
        return json_file, txt_file, final_file, file_hash
    
    return None, None, None, file_hash

def move_error_file(file_path: Path, error_folder: Path, error_message: str):
    """Move a problematic file to the error_files directory"""
    try:
        # Create target path in error_files directory
        error_file_path = error_folder / file_path.name
        
        # If file already exists in error_files, create a unique name
        counter = 1
        original_stem = file_path.stem
        original_suffix = file_path.suffix
        
        while error_file_path.exists():
            error_file_path = error_folder / f"{original_stem}_{counter}{original_suffix}"
            counter += 1
        
        # Move the file
        import shutil
        shutil.move(str(file_path), str(error_file_path))
        
        # Create an error log file alongside the moved file
        error_log_path = error_file_path.with_suffix(error_file_path.suffix + '.error.txt')
        with open(error_log_path, 'w', encoding='utf-8') as f:
            f.write(f"Error processing file: {file_path.name}\n")
            f.write(f"Error message: {error_message}\n")
            f.write(f"Moved on: {datetime.now().isoformat()}\n")
            f.write(f"Original path: {file_path}\n")
        
        print(f"  📁 Moved problematic file to: {error_file_path}")
        print(f"  📝 Created error log: {error_log_path.name}")
        
        return True
        
    except Exception as e:
        print(f"  ⚠️  Failed to move error file {file_path.name}: {e}")
        return False

def should_move_to_error_files(error_message: str) -> bool:
    """Determine if a file should be moved to error_files based on the error message"""
    # Define error patterns that indicate problematic files that should be moved
    error_patterns_to_move = [
        "Target: 0",  # The specific error mentioned by user
        "Document Intelligence service error",
        "Authentication failed",
        "Service quota exceeded",
        "Document format not supported",
        "File is corrupted",
        "Unable to process document",
        "Invalid file format",
        "Document too large",
        "Unsupported document type"
    ]
    
    # Check if the error message contains any of these patterns
    error_lower = error_message.lower()
    for pattern in error_patterns_to_move:
        if pattern.lower() in error_lower:
            return True
    
    return False

def process_single_file(file_path: Path) -> Dict[str, Any]:
    """Process a single file and return extracted data with caching support"""
    print(f"Processing: {file_path.name}")
    
    # Additional validation
    if not file_path.exists():
        return {'filename': file_path.name, 'error': 'File does not exist'}
    
    # Check file size (skip very large files that might cause issues)
    file_size_mb = file_path.stat().st_size / (1024 * 1024)
    if file_size_mb > 100:  # 100 MB limit
        print(f"Skipping {file_path.name} - file too large ({file_size_mb:.1f} MB)")
        return {'filename': file_path.name, 'error': f'File too large ({file_size_mb:.1f} MB)'}
    
    # Create result folders
    json_folder, txt_folder, excel_folder, temp_folder, error_folder = create_result_folders()
    
    # Check for cached results first
    cached_json, cached_txt, cached_final, file_hash = check_cached_results(file_path, json_folder, txt_folder)
    
    base_name = file_path.stem
    hash_suffix = file_hash[:8]
    
    if cached_json and cached_txt:
        print(f"  ✅ Using cached results (hash: {hash_suffix})")
        
        # Check if we have a cached final table as well
        if cached_final and cached_final.exists():
            try:
                with open(cached_final, 'r', encoding='utf-8') as f:
                    table_data = json.load(f)
                
                # Check if this is a "no table data" cache entry
                if (len(table_data) == 1 and 
                    table_data[0].get('metadata', {}).get('no_table_data', False)):
                    print(f"  📋 Using cached 'no table' result (hash: {hash_suffix})")
                    return {
                        'filename': file_path.name,
                        'error': 'No table data extracted',
                        'cached': True
                    }
                
                return {
                    'filename': file_path.name,
                    'table_data': table_data,
                    'rows_count': len(table_data),
                    'cached': True
                }
            except Exception as e:
                print(f"  ⚠️  Error reading cached final table, will reprocess: {e}")
        
        # Load and process cached table data directly
        try:
            with open(cached_json, 'r', encoding='utf-8') as f:
                cached_table_data = json.load(f)
            
            # Check if this is temp_results format (direct array) or old format (nested)
            if isinstance(cached_table_data, list) and len(cached_table_data) > 0:
                # temp_results format - direct array of table objects
                if all('cells' in table for table in cached_table_data):
                    # Convert temp_results format to final table format
                    final_table_data = []
                    for table in cached_table_data:
                        rows = []
                        max_row = max(cell['row_index'] for cell in table['cells']) + 1
                        max_col = max(cell['column_index'] for cell in table['cells']) + 1
                        
                        # Create empty grid
                        grid = [[''] * max_col for _ in range(max_row)]
                        
                        # Fill grid with cell content
                        for cell in table['cells']:
                            row_idx = cell['row_index']
                            col_idx = cell['column_index']
                            content = cell.get('content', '').strip()
                            grid[row_idx][col_idx] = content
                        
                        # Convert grid to rows
                        rows = [row for row in grid if any(cell.strip() for cell in row)]
                        
                        final_table_data.append({
                            'table_index': table.get('table_index', 0),
                            'row_count': len(rows),
                            'column_count': max_col,
                            'rows': rows
                        })
                    
                    return {
                        'filename': file_path.name,
                        'table_data': final_table_data,
                        'rows_count': sum(len(table['rows']) for table in final_table_data),
                        'cached': True
                    }
                else:
                    # Already in final format
                    return {
                        'filename': file_path.name,
                        'table_data': cached_table_data,
                        'rows_count': sum(len(table.get('rows', [])) for table in cached_table_data),
                        'cached': True
                    }
            
            else:
                # Empty or "no tables" result
                print(f"  📋 Using cached 'no table' result (hash: {hash_suffix})")
                return {
                    'filename': file_path.name,
                    'error': 'No table data extracted',
                    'cached': True
                }
                
        except Exception as e:
            print(f"  ⚠️  Error reading cached table data: {e}")
            # Fall back to normal processing
            pass
        
        # Copy cached files to temp directory for processing (fallback)
        import shutil
        current_json = temp_folder / f"{base_name}_tables.json"
        current_txt = temp_folder / f"{base_name}_ocr_results.txt"
        
        if not cached_json.name.startswith(base_name):
            # Copy from temp_results to standard location
            if cached_json.exists():
                shutil.copy2(cached_json, current_json)
            if cached_txt and cached_txt.exists():
                shutil.copy2(cached_txt, current_txt)
        
    else:
        print(f"  🔄 Running OCR analysis (hash: {hash_suffix})")
        
        # Run OCR on the file
        cmd = [sys.executable, 'sample_analyze_read.py', str(file_path), '--json']
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            if result.returncode != 0:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                # Extract the actual error message, skip SSL warnings
                error_lines = [line for line in error_msg.split('\n') if line.strip() and not line.startswith('  warnings.warn')]
                if error_lines:
                    # Get the last meaningful error line
                    actual_error = error_lines[-1] if error_lines else error_msg
                else:
                    actual_error = "Process failed without specific error message"
                
                print(f"  ❌ Error processing {file_path.name}: {actual_error}")
                
                # Check if this error type should cause the file to be moved to error_files
                if should_move_to_error_files(actual_error):
                    print(f"  🚨 Moving problematic file due to error: {actual_error}")
                    moved = move_error_file(file_path, error_folder, actual_error)
                    if moved:
                        return {
                            'filename': file_path.name, 
                            'error': f'File moved to error_files: {actual_error}',
                            'moved_to_error_files': True
                        }
                
                return {'filename': file_path.name, 'error': actual_error}
        except subprocess.TimeoutExpired:
            timeout_error = 'Processing timeout (exceeded 5 minutes)'
            print(f"  ⏰ Timeout processing {file_path.name}")
            
            # Move timeout files to error_files as they often indicate problematic files
            print(f"  🚨 Moving timeout file to error_files")
            moved = move_error_file(file_path, error_folder, timeout_error)
            if moved:
                return {
                    'filename': file_path.name, 
                    'error': f'File moved to error_files: {timeout_error}',
                    'moved_to_error_files': True
                }
            
            return {'filename': file_path.name, 'error': timeout_error}
        except Exception as e:
            unexpected_error = f'Unexpected error: {str(e)}'
            print(f"  ❌ Unexpected error processing {file_path.name}: {str(e)}")
            
            # Check if this is a serious error that should move the file
            serious_errors = ['permission denied', 'file not found', 'access denied', 'corrupt', 'invalid']
            if any(serious in str(e).lower() for serious in serious_errors):
                print(f"  🚨 Moving problematic file due to serious error")
                moved = move_error_file(file_path, error_folder, unexpected_error)
                if moved:
                    return {
                        'filename': file_path.name, 
                        'error': f'File moved to error_files: {unexpected_error}',
                        'moved_to_error_files': True
                    }
            
            return {'filename': file_path.name, 'error': unexpected_error}
    
    # Extract table data (files are created in current directory, but we'll move them to temp)
    json_file = Path(f"{base_name}_tables.json")
    final_json = Path(f"{base_name}_final_table.json")
    
    if json_file.exists():
        cmd = [sys.executable, 'extract_final_table.py', str(json_file), '--cleanup']
        try:
            subprocess.run(cmd, check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            print(f"  ❌ Error extracting table from {file_path.name}: {e}")
            return {'filename': file_path.name, 'error': f'Table extraction failed: {e}'}
    
    # Read the final table data
    if final_json.exists():
        try:
            with open(final_json, 'r', encoding='utf-8') as f:
                table_data = json.load(f)
            
            # Save final table to cache if not from cache
            if not (cached_json and cached_txt):
                cached_final_name = f"{base_name}-{hash_suffix}_final_table.json"
                import shutil
                shutil.copy2(final_json, json_folder / cached_final_name)
                print(f"  💾 Cached final table: {cached_final_name}")
            
            # Clean up temporary files
            ocr_results_file = Path(f"{base_name}_ocr_results.txt")
            for temp_file in [json_file, final_json, ocr_results_file]:
                if temp_file.exists():
                    temp_file.unlink()
            
            return {
                'filename': file_path.name,
                'table_data': table_data,
                'rows_count': len(table_data),
                'cached': cached_json and cached_txt
            }
        except Exception as e:
            print(f"  ❌ Error reading table data from {file_path.name}: {e}")
            return {'filename': file_path.name, 'error': f'Failed to read table data: {e}'}
    else:
        print(f"  ⚠️  No table data found for {file_path.name}")
        
        # Cache the "no table data" result to avoid future API calls
        if not (cached_json and cached_txt):
            import shutil
            
            # Cache the OCR results (both JSON and TXT) so cache detection works
            try:
                ocr_results_file = Path(f"{base_name}_ocr_results.txt")
                
                # Cache the JSON file if it exists (even if no tables)
                if json_file.exists():
                    cached_json_name = f"{base_name}-{hash_suffix}_tables.json"
                    shutil.copy2(json_file, json_folder / cached_json_name)
                else:
                    # Create an empty tables file so cache detection works next time
                    cached_json_name = f"{base_name}-{hash_suffix}_tables.json"
                    empty_tables = {"tables": [], "no_tables_detected": True}
                    with open(json_folder / cached_json_name, 'w', encoding='utf-8') as f:
                        json.dump(empty_tables, f, ensure_ascii=False, indent=2)
                
                # Cache the TXT file if it exists
                if ocr_results_file.exists():
                    cached_txt_name = f"{base_name}-{hash_suffix}_ocr_results.txt"
                    shutil.copy2(ocr_results_file, txt_folder / cached_txt_name)
                
                # Create the "no table" final result cache
                cached_final_name = f"{base_name}-{hash_suffix}_final_table.json"
                no_table_result = [{
                    "table_index": 0,
                    "row_count": 0,
                    "column_count": 0,
                    "rows": [],
                    "metadata": {
                        "no_table_data": True,
                        "processed_by": "batch_ocr_processor.py",
                        "timestamp": str(datetime.now())
                    }
                }]
                
                with open(json_folder / cached_final_name, 'w', encoding='utf-8') as f:
                    json.dump(no_table_result, f, ensure_ascii=False, indent=2)
                
                print(f"  💾 Cached 'no table' result: {cached_final_name}")
                
            except Exception as e:
                print(f"  ⚠️  Could not cache 'no table' result: {e}")
        
        # Clean up temporary files
        ocr_results_file = Path(f"{base_name}_ocr_results.txt")
        for temp_file in [json_file, ocr_results_file]:
            if temp_file.exists():
                temp_file.unlink()
        
        return {'filename': file_path.name, 'error': 'No table data extracted'}

def create_excel_output(processed_files: List[Dict], output_file: str):
    """Create Excel file with all extracted data"""
    all_rows = []
    
    for file_data in processed_files:
        filename = file_data['filename']
        
        if 'error' in file_data:
            # Add error row
            all_rows.append({
                'Source File': filename,
                'Error': file_data['error']
            })
        elif 'table_data' in file_data:
            table_data = file_data['table_data']
            
            if not table_data:
                # No data found
                all_rows.append({
                    'Source File': filename,
                    'Error': 'No table data found'
                })
            else:
                # Extract individual rows from the table data
                # table_data is expected to be a list with table info
                for table_info in table_data:
                    if 'rows' in table_info and table_info['rows']:
                        rows = table_info['rows']
                        
                        # Detect if the first row contains data instead of headers
                        import re
                        
                        def is_id_like(value):
                            """Check if a value looks like an ID"""
                            if not value:
                                return False
                            val_str = str(value).strip()
                            # Check for Israeli ID patterns (9 digits with optional spaces/separators)
                            if re.match(r'^\d{2,3}\s*\d{5,6}$', val_str):  # e.g., "255 87932"
                                return True
                            if re.match(r'^\d{9}$', val_str):  # e.g., "123456789"
                                return True
                            if re.match(r'^\d{8,10}$', val_str):  # 8-10 digit IDs
                                return True
                            return False
                        
                        def has_header_like_content(row):
                            """Check if a row contains header-like content"""
                            header_words = ['id', 'name', 'שם', 'ת.ז', 'תז', 'ת״ז', 'מספר', 'זהות', 'first', 'last', 'תפקיד', 'position']
                            for val in row:
                                if val:
                                    val_str = str(val).strip().lower()
                                    for word in header_words:
                                        if word in val_str:
                                            return True
                            return False
                        
                        # Skip header row (first row) and process data rows
                        if len(rows) > 1:
                            first_row = rows[0]
                            
                            # Check if first row contains ID data instead of headers
                            first_row_has_ids = any(is_id_like(val) for val in first_row)
                            first_row_has_headers = has_header_like_content(first_row)
                            
                            # If first row has IDs but no clear headers, treat all rows as data
                            if first_row_has_ids and not first_row_has_headers:
                                print(f"  🔄 Detected ID data in first row of {filename}, treating all rows as data")
                                headers = [f'Column_{i+1}' for i in range(len(first_row))]
                                data_rows = rows  # All rows are data
                            else:
                                headers = rows[0]  # First row contains headers
                                data_rows = rows[1:]  # Remaining rows contain data
                            
                            # Check if this file has Excel column names that need fixing
                            excel_columns = [chr(i) for i in range(ord('A'), ord('Z')+1)]  # A-Z
                            excel_col_count = sum(1 for h in headers if str(h).strip() in excel_columns)
                            
                            # If more than 50% are Excel columns and we have data, check first data row for real headers
                            if (excel_col_count > len(headers) * 0.5 and len(headers) > 2 and 
                                len(data_rows) > 0 and not first_row_has_ids):
                                
                                first_data_row = data_rows[0]
                                # Count meaningful headers in first data row
                                meaningful_headers = 0
                                import re
                                for val in first_data_row:
                                    if val and str(val).strip():
                                        val_str = str(val).strip()
                                        if re.search(r'[\u0590-\u05FFa-zA-Z]', val_str) and len(val_str) > 1:
                                            meaningful_headers += 1
                                
                                # If first data row looks like headers, use it
                                if meaningful_headers >= len(headers) * 0.6:
                                    print(f"  🔄 Detected Excel headers in {filename}, using first data row as headers")
                                    
                                    # Use first data row as headers
                                    real_headers = []
                                    for val in first_data_row:
                                        if val and str(val).strip():
                                            # Clean the header name
                                            header_name = str(val).strip()
                                            # Remove common artifacts
                                            header_name = re.sub(r'[^\w\u0590-\u05FF\s\.\-]', '', header_name)
                                            header_name = ' '.join(header_name.split())
                                            real_headers.append(header_name)
                                        else:
                                            real_headers.append('')
                                    
                                    headers = real_headers
                                    data_rows = data_rows[1:]  # Skip the row we used as headers
                            
                            # Filter and normalize headers
                            filtered_headers = clean_and_normalize_headers(headers)
                            for data_row in data_rows:
                                row_data = {'Source File': filename}
                                
                                # Map each cell to its corresponding filtered header
                                for i, cell_value in enumerate(data_row):
                                    if i < len(filtered_headers):
                                        header = filtered_headers[i]
                                        if header:  # Only include valid headers
                                            row_data[header] = cell_value
                                    else:
                                        # Handle extra columns without headers
                                        row_data[f'Column_{i+1}'] = cell_value
                                
                                all_rows.append(row_data)
    
    if not all_rows:
        print("No data to export.")
        return
    
    # Create DataFrame and export to Excel
    df = pd.DataFrame(all_rows)
    
    # Reorder columns to put 'Source File' first
    cols = ['Source File'] + [col for col in df.columns if col != 'Source File']
    df = df[cols]
    
    # Apply column normalization before exporting
    print("\nApplying column normalization...")
    normalizer = ColumnNormalizer()
    df_normalized = normalizer.normalize_dataframe(df)
    
    # Export to Excel
    excel_folder = Path('excel_results')
    excel_output_path = excel_folder / Path(output_file)
    with pd.ExcelWriter(excel_output_path, engine='openpyxl') as writer:
        df_normalized.to_excel(writer, sheet_name='OCR Results', index=False)
        
        # Auto-adjust column widths
        worksheet = writer.sheets['OCR Results']
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = min(max_length + 2, 50)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    print(f"\nResults exported to: {excel_output_path}")
    print(f"Total rows processed: {len(all_rows)}")
    print(f"Normalized columns: {len(df_normalized.columns)}")
    
    # Summary statistics
    files_with_data = sum(1 for f in processed_files if 'table_data' in f and f['table_data'])
    files_with_errors = sum(1 for f in processed_files if 'error' in f)
    
    print(f"Files successfully processed: {files_with_data}")
    print(f"Files with errors: {files_with_errors}")
    
    # Show final column structure
    print(f"\nFinal normalized columns:")
    for i, col in enumerate(df_normalized.columns, 1):
        non_null_count = df_normalized[col].notna().sum()
        print(f"  {i:2d}. {col} ({non_null_count} values)")

def main():
    parser = argparse.ArgumentParser(description='Batch OCR processor for multiple file types')
    parser.add_argument('-o', '--output', default='ocr_results.xlsx', 
                       help='Output Excel file (default: ocr_results.xlsx)')
    parser.add_argument('--files-dir', default='files',
                       help='Directory containing files (default: files)')
    parser.add_argument('--limit', type=int, default=None,
                       help='Limit number of files to process (for testing)')
    
    args = parser.parse_args()
    
    # Check if files directory exists
    files_dir = Path(args.files_dir)
    if not files_dir.exists():
        print(f"Error: Directory '{args.files_dir}' does not exist.")
        print(f"Please create the directory and add your files.")
        return
    
    # Find all folders with supported files
    folders = find_folders_in_directory(args.files_dir)
    
    if not folders:
        print(f"No folders with supported files found in '{args.files_dir}' directory.")
        return
    
    # Let user select folders to process
    selected_folders = display_folders_for_selection(folders, files_dir)
    
    if not selected_folders:
        print("No folders selected. Exiting.")
        return
    
    # Get all files from selected folders
    all_files = find_files_in_folders(selected_folders)
    
    if not all_files:
        print("No supported files found in selected folders.")
        return
    
    # Apply file limit if specified
    if args.limit and args.limit < len(all_files):
        selected_files = all_files[:args.limit]
        print(f"\n🔢 File limit applied: Processing {len(selected_files)} out of {len(all_files)} total files")
    else:
        selected_files = all_files
    
    print(f"\nProcessing {len(selected_files)} files from {len(selected_folders)} folders...")
    if args.limit:
        print(f"File limit: {args.limit} (for testing)")
    print("=" * 70)
    
    # Process each selected file
    processed_files = []
    cached_count = 0
    api_calls_count = 0
    
    for i, file_path in enumerate(selected_files, 1):
        print(f"\n[{i}/{len(selected_files)}] Processing: {file_path.name}")
        result = process_single_file(file_path)
        processed_files.append(result)
        
        # Track cache usage
        if result.get('cached', False):
            cached_count += 1
        elif 'error' not in result:
            api_calls_count += 1
    
    # Print cache statistics
    print("\n" + "=" * 70)
    print("📊 PROCESSING SUMMARY")
    print("=" * 70)
    print(f"Total files processed: {len(selected_files)}")
    print(f"Files from cache: {cached_count} (saved {cached_count} API calls!)")
    print(f"New API calls made: {api_calls_count}")
    print(f"Cost savings: {(cached_count / len(selected_files)) * 100:.1f}% reduction in API usage")
    
    # Create Excel output
    print("\nCreating Excel output...")
    create_excel_output(processed_files, args.output)

if __name__ == '__main__':
    main()

